"""Rotas de assinatura por link (1 destinatário) e histórico."""

from __future__ import annotations

import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response

from api.auth import CurrentUser, get_current_user
from api.credits import ToolQuota, get_client_ip
from api.routes_pdf_advanced import _log_signature_event, _save, _tmp
from api.signing_storage import download_signing_file, save_signing_file_to_temp, upload_signing_file
from src.pdf_splitter.pdf_tools import add_signature_stamp

router = APIRouter(prefix="/api/signing", tags=["Signing"])

_SITE_URL = "https://doc-split-beta.vercel.app"


def _parse_page(raw: str) -> int:
    value = (raw or "").strip().lower()
    if value in {"", "-1", "ultima", "última", "last", "final"}:
        return -1
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(400, "Página inválida.") from exc


def _parse_ratio(raw: str, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(raw or default)))
    except ValueError as exc:
        raise HTTPException(400, "Posição inválida.") from exc


def _get_request_by_token(token: str) -> dict:
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signing_requests")
        .select("*")
        .eq("token", token)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(404, "Link de assinatura não encontrado.")
    return rows[0]


def _ensure_pending(row: dict) -> None:
    if row.get("status") == "signed":
        raise HTTPException(410, "Este documento já foi assinado.")
    expires = row.get("expires_at")
    if expires:
        try:
            exp_dt = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
            if exp_dt < datetime.now(timezone.utc):
                raise HTTPException(410, "Este link de assinatura expirou.")
        except HTTPException:
            raise
        except Exception:
            pass


@router.post("/create")
async def create_signing_request(
    request: Request,
    file: UploadFile = File(...),
    recipient_email: str = Form(...),
    recipient_name: str = Form(""),
    owner_message: str = Form(""),
    page_number: str = Form("-1"),
    x_ratio: str = Form("0.62"),
    y_ratio: str = Form("0.78"),
    user: CurrentUser = Depends(get_current_user),
):
    """Cria link para 1 pessoa assinar o PDF (válido por 7 dias)."""
    email = recipient_email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Informe um e-mail válido do destinatário.")
    quota = ToolQuota(user, request)
    p = await _save(file)
    token = secrets.token_urlsafe(24)
    storage_path = f"{user.user_id}/{token}/original.pdf"
    try:
        upload_signing_file(storage_path, p.read_bytes())
        from src.pdf_splitter.supabase_client import get_supabase

        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        row = {
            "token": token,
            "owner_user_id": user.user_id,
            "recipient_email": email,
            "recipient_name": recipient_name.strip(),
            "owner_message": owner_message.strip(),
            "page_number": _parse_page(page_number),
            "pos_x": _parse_ratio(x_ratio, 0.62),
            "pos_y": _parse_ratio(y_ratio, 0.78),
            "storage_path": storage_path,
            "original_filename": file.filename or "documento.pdf",
            "expires_at": expires_at,
        }
        inserted = get_supabase().table("signing_requests").insert(row).execute()
        req_id = (inserted.data or [{}])[0].get("id")
        _log_signature_event(
            user.user_id,
            event_type="link_sent",
            filename=file.filename or "documento.pdf",
            signer_name=recipient_name.strip() or email,
            stamp_info={"recipient_email": email},
            signing_request_id=str(req_id) if req_id else None,
        )
        quota.consume()
        link = f"{_SITE_URL}/assinatura.html?token={token}"
        return {
            "success": True,
            "token": token,
            "link": link,
            "expires_at": expires_at,
            "recipient_email": email,
        }
    finally:
        p.unlink(missing_ok=True)


@router.get("/requests")
def list_signing_requests(user: CurrentUser = Depends(get_current_user)):
    """Lista solicitações de assinatura do usuário."""
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signing_requests")
        .select(
            "id,token,recipient_email,recipient_name,status,original_filename,created_at,expires_at,signed_at,owner_message"
        )
        .eq("owner_user_id", user.user_id)
        .order("created_at", desc=True)
        .limit(30)
        .execute()
    )
    return {"items": response.data or []}


@router.get("/events")
def list_signature_events(user: CurrentUser = Depends(get_current_user)):
    """Histórico de carimbos e assinaturas do usuário."""
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signature_events")
        .select("id,event_type,filename,signer_name,stamp_info,created_at")
        .eq("user_id", user.user_id)
        .order("created_at", desc=True)
        .limit(30)
        .execute()
    )
    return {"items": response.data or []}


@router.get("/public/{token}")
def get_public_signing_request(token: str):
    """Dados públicos da solicitação (sem exigir login)."""
    row = _get_request_by_token(token)
    _ensure_pending(row)
    return {
        "token": token,
        "status": row.get("status"),
        "recipient_email": row.get("recipient_email"),
        "recipient_name": row.get("recipient_name") or "",
        "owner_message": row.get("owner_message") or "",
        "original_filename": row.get("original_filename") or "documento.pdf",
        "page_number": row.get("page_number", -1),
        "pos_x": row.get("pos_x", 0.62),
        "pos_y": row.get("pos_y", 0.78),
        "expires_at": row.get("expires_at"),
    }


@router.get("/public/{token}/pdf")
def download_public_pdf(token: str):
    """PDF original para visualização pelo destinatário."""
    row = _get_request_by_token(token)
    _ensure_pending(row)
    try:
        data = download_signing_file(row["storage_path"])
    except Exception as exc:
        raise HTTPException(404, "Arquivo não encontrado.") from exc
    filename = row.get("original_filename") or "documento.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/public/{token}/complete")
async def complete_public_signing(
    token: str,
    request: Request,
    label: str = Form(""),
    role: str = Form(""),
    company: str = Form(""),
    document_id: str = Form(""),
    custom_line: str = Form(""),
    date_label: str = Form(""),
    x_ratio: str = Form(""),
    y_ratio: str = Form(""),
    stamp: UploadFile | None = File(default=None),
):
    """Destinatário aplica carimbo profissional e conclui a assinatura."""
    row = _get_request_by_token(token)
    _ensure_pending(row)
    if not label.strip() and not (stamp and stamp.filename):
        raise HTTPException(400, "Informe o nome ou envie imagem da assinatura.")
    stamp_path: Path | None = None
    local_pdf: Path | None = None
    out: Path | None = None
    signed_path = f"{row['owner_user_id']}/{token}/signed.pdf"
    try:
        local_pdf = save_signing_file_to_temp(row["storage_path"])
        if stamp and stamp.filename:
            stamp_path = await _save(stamp, images=True)
        out = _tmp()
        x_pos = _parse_ratio(x_ratio, float(row.get("pos_x") or 0.62))
        y_pos = _parse_ratio(y_ratio, float(row.get("pos_y") or 0.78))
        add_signature_stamp(
            local_pdf,
            out,
            label=label,
            image_path=stamp_path,
            page_number=int(row.get("page_number") or -1),
            role=role,
            company=company,
            document_id=document_id,
            custom_line=custom_line,
            date_label=date_label,
            x_ratio=x_pos,
            y_ratio=y_pos,
        )
        upload_signing_file(signed_path, out.read_bytes())
        signer_info = {
            "name": label.strip(),
            "role": role.strip(),
            "company": company.strip(),
            "document_id": document_id.strip(),
            "custom_line": custom_line.strip(),
        }
        from src.pdf_splitter.supabase_client import get_supabase

        get_supabase().table("signing_requests").update(
            {
                "status": "signed",
                "signed_storage_path": signed_path,
                "signed_at": datetime.now(timezone.utc).isoformat(),
                "signer_info": signer_info,
                "signer_ip": get_client_ip(request),
                "pos_x": x_pos,
                "pos_y": y_pos,
            }
        ).eq("token", token).execute()
        _log_signature_event(
            str(row["owner_user_id"]),
            event_type="link_signed",
            filename=row.get("original_filename") or "documento.pdf",
            signer_name=label.strip(),
            stamp_info=signer_info,
            signing_request_id=str(row.get("id")) if row.get("id") else None,
        )
        return {
            "success": True,
            "download_url": f"/api/signing/public/{token}/signed",
            "filename": "documento_assinado.pdf",
        }
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        if stamp_path:
            stamp_path.unlink(missing_ok=True)
        if local_pdf:
            local_pdf.unlink(missing_ok=True)
        if out:
            out.unlink(missing_ok=True)


@router.get("/public/{token}/signed")
def download_public_signed(token: str):
    """PDF assinado — disponível após conclusão (link com token)."""
    row = _get_request_by_token(token)
    if row.get("status") != "signed" or not row.get("signed_storage_path"):
        raise HTTPException(400, "Documento ainda não foi assinado.")
    try:
        data = download_signing_file(row["signed_storage_path"])
    except Exception as exc:
        raise HTTPException(404, "Arquivo assinado não encontrado.") from exc
    filename = (row.get("original_filename") or "documento.pdf").replace(".pdf", "_assinado.pdf")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download/{token}")
def download_signed_by_token(token: str, user: CurrentUser = Depends(get_current_user)):
    """Dono baixa o PDF assinado pelo token da solicitação."""
    row = _get_request_by_token(token)
    if row.get("owner_user_id") != user.user_id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if row.get("status") != "signed" or not row.get("signed_storage_path"):
        raise HTTPException(400, "Documento ainda não foi assinado.")
    try:
        data = download_signing_file(row["signed_storage_path"])
    except Exception as exc:
        raise HTTPException(404, "Arquivo assinado não encontrado.") from exc
    name = (row.get("original_filename") or "documento.pdf").replace(".pdf", "_assinado.pdf")
    tmp = Path(tempfile.gettempdir()) / f"docsplit_dl_{token}.pdf"
    tmp.write_bytes(data)
    return FileResponse(tmp, media_type="application/pdf", filename=name)
