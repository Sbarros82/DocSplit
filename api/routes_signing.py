"""Rotas de assinatura por link (vários destinatários) e histórico."""

from __future__ import annotations

import json
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response

from api.auth import CurrentUser, get_current_user
from api.credits import ToolQuota, get_client_ip
from api.routes_pdf_advanced import _log_signature_event, _save, _tmp
from api.signing_storage import download_signing_file, save_signing_file_to_temp, upload_signing_file
from src.pdf_splitter.pdf_tools import add_signature_stamp

router = APIRouter(prefix="/api/signing", tags=["Signing"])

_SITE_URL = "https://docsplit-app.vercel.app"
_MAX_SIGNERS = 10


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


def _auto_positions(count: int, base_y: float = 0.78) -> list[tuple[float, float]]:
    """Distribui carimbos na horizontal (última linha da página)."""
    if count <= 0:
        return []
    box_w = 0.28
    gap = 0.03
    total = count * box_w + max(0, count - 1) * gap
    start_x = max(0.02, (1.0 - total) / 2)
    return [(start_x + i * (box_w + gap), base_y) for i in range(count)]


def _valid_email(email: str) -> bool:
    email = email.strip().lower()
    return bool(email) and "@" in email and "." in email.split("@")[-1]


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


def _get_recipient_by_token(token: str) -> dict:
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signing_recipients")
        .select("*")
        .eq("token", token)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(404, "Link de assinatura não encontrado.")
    return rows[0]


def _get_recipients_for_request(request_id: str) -> list[dict]:
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signing_recipients")
        .select("*")
        .eq("request_id", request_id)
        .order("sign_order")
        .execute()
    )
    return response.data or []


def _resolve_token(token: str) -> tuple[str, dict | None, dict]:
    """Retorna (mode, recipient|None, request). mode: legacy | recipient."""
    try:
        recipient = _get_recipient_by_token(token)
        request = _get_request_by_id(str(recipient["request_id"]))
        return "recipient", recipient, request
    except HTTPException:
        pass
    request = _get_request_by_token(token)
    return "legacy", None, request


def _get_request_by_id(request_id: str) -> dict:
    from src.pdf_splitter.supabase_client import get_supabase

    response = (
        get_supabase()
        .table("signing_requests")
        .select("*")
        .eq("id", request_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(404, "Solicitação não encontrada.")
    return rows[0]


def _check_expired(row: dict) -> None:
    expires = row.get("expires_at")
    if not expires:
        return
    try:
        exp_dt = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
        if exp_dt < datetime.now(timezone.utc):
            raise HTTPException(410, "Este link de assinatura expirou.")
    except HTTPException:
        raise
    except Exception:
        return


def _current_pdf_path(request: dict) -> str:
    return str(request.get("signed_storage_path") or request["storage_path"])


def _signed_count(recipients: list[dict]) -> int:
    return sum(1 for r in recipients if r.get("status") == "signed")


def _request_progress(request: dict) -> dict[str, Any]:
    recipients = _get_recipients_for_request(str(request["id"]))
    total = len(recipients)
    signed = _signed_count(recipients)
    if total == 0:
        status = request.get("status")
        return {
            "total_signers": 1,
            "signed_count": 1 if status in {"signed", "completed"} else 0,
            "recipients": [],
        }
    return {
        "total_signers": total,
        "signed_count": signed,
        "recipients": recipients,
    }


def _parse_recipients(
    recipients_json: str,
    recipient_email: str,
    recipient_name: str,
    page_number: int,
    base_y: float,
) -> list[dict]:
    """Monta lista de signatários a partir do JSON ou campos legados."""
    parsed: list[dict] = []
    if recipients_json.strip():
        try:
            raw = json.loads(recipients_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "Lista de signatários inválida.") from exc
        if not isinstance(raw, list):
            raise HTTPException(400, "Lista de signatários inválida.")
        for item in raw:
            if not isinstance(item, dict):
                continue
            email = str(item.get("email") or "").strip().lower()
            if not _valid_email(email):
                continue
            parsed.append(
                {
                    "email": email,
                    "name": str(item.get("name") or "").strip(),
                    "pos_x": _parse_ratio(str(item.get("pos_x", "")), 0.62),
                    "pos_y": _parse_ratio(str(item.get("pos_y", "")), base_y),
                }
            )
    elif _valid_email(recipient_email):
        parsed.append(
            {
                "email": recipient_email.strip().lower(),
                "name": recipient_name.strip(),
                "pos_x": 0.62,
                "pos_y": base_y,
            }
        )

    if not parsed:
        raise HTTPException(400, "Informe pelo menos um e-mail de signatário válido.")
    if len(parsed) > _MAX_SIGNERS:
        raise HTTPException(400, f"Máximo de {_MAX_SIGNERS} signatários por documento.")

    positions = _auto_positions(len(parsed), base_y)
    for idx, person in enumerate(parsed):
        if "pos_x" not in person or person.get("pos_x") == 0.62:
            person["pos_x"], person["pos_y"] = positions[idx]
        person["page_number"] = page_number
        person["sign_order"] = idx + 1
    return parsed


@router.post("/create")
async def create_signing_request(
    request: Request,
    file: UploadFile = File(...),
    recipient_email: str = Form(""),
    recipient_name: str = Form(""),
    recipients_json: str = Form(""),
    owner_message: str = Form(""),
    page_number: str = Form("-1"),
    x_ratio: str = Form("0.62"),
    y_ratio: str = Form("0.78"),
    user: CurrentUser = Depends(get_current_user),
):
    """Cria links para várias pessoas assinarem o PDF (válido por 7 dias)."""
    quota = ToolQuota(user, request)
    p = await _save(file)
    request_token = secrets.token_urlsafe(24)
    storage_path = f"{user.user_id}/{request_token}/original.pdf"
    page_int = _parse_page(page_number)
    base_y = _parse_ratio(y_ratio, 0.78)
    signers = _parse_recipients(recipients_json, recipient_email, recipient_name, page_int, base_y)
    try:
        upload_signing_file(storage_path, p.read_bytes())
        from src.pdf_splitter.supabase_client import get_supabase

        sb = get_supabase()
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        first = signers[0]
        row = {
            "token": request_token,
            "owner_user_id": user.user_id,
            "recipient_email": first["email"],
            "recipient_name": first["name"],
            "owner_message": owner_message.strip(),
            "page_number": page_int,
            "pos_x": first["pos_x"],
            "pos_y": first["pos_y"],
            "storage_path": storage_path,
            "original_filename": file.filename or "documento.pdf",
            "expires_at": expires_at,
            "status": "pending",
        }
        inserted = sb.table("signing_requests").insert(row).execute()
        req_row = (inserted.data or [{}])[0]
        req_id = str(req_row.get("id"))

        recipient_links: list[dict] = []
        for person in signers:
            token = secrets.token_urlsafe(24)
            sb.table("signing_recipients").insert(
                {
                    "request_id": req_id,
                    "token": token,
                    "email": person["email"],
                    "name": person["name"],
                    "sign_order": person["sign_order"],
                    "page_number": person["page_number"],
                    "pos_x": person["pos_x"],
                    "pos_y": person["pos_y"],
                }
            ).execute()
            recipient_links.append(
                {
                    "email": person["email"],
                    "name": person["name"],
                    "token": token,
                    "link": f"{_SITE_URL}/assinatura.html?token={token}",
                    "sign_order": person["sign_order"],
                }
            )

        _log_signature_event(
            user.user_id,
            event_type="link_sent",
            filename=file.filename or "documento.pdf",
            signer_name=f"{len(signers)} signatário(s)",
            stamp_info={"recipients": [p["email"] for p in signers]},
            signing_request_id=req_id,
        )
        quota.consume()
        return {
            "success": True,
            "token": request_token,
            "link": recipient_links[0]["link"] if len(recipient_links) == 1 else None,
            "recipients": recipient_links,
            "total_signers": len(recipient_links),
            "expires_at": expires_at,
            "recipient_email": first["email"],
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
    items = []
    for row in response.data or []:
        progress = _request_progress(row)
        recipients = progress["recipients"]
        items.append(
            {
                **row,
                "total_signers": progress["total_signers"],
                "signed_count": progress["signed_count"],
                "recipients": [
                    {
                        "email": r.get("email"),
                        "name": r.get("name"),
                        "status": r.get("status"),
                        "token": r.get("token"),
                        "link": f"{_SITE_URL}/assinatura.html?token={r.get('token')}",
                        "signed_at": r.get("signed_at"),
                    }
                    for r in recipients
                ],
            }
        )
    return {"items": items}


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
    mode, recipient, row = _resolve_token(token)
    _check_expired(row)
    progress = _request_progress(row)
    total = progress["total_signers"]
    signed = progress["signed_count"]

    if mode == "recipient" and recipient:
        if recipient.get("status") == "signed":
            return {
                "token": token,
                "status": "signed",
                "recipient_email": recipient.get("email"),
                "recipient_name": recipient.get("name") or "",
                "owner_message": row.get("owner_message") or "",
                "original_filename": row.get("original_filename") or "documento.pdf",
                "page_number": recipient.get("page_number", -1),
                "pos_x": recipient.get("pos_x", 0.62),
                "pos_y": recipient.get("pos_y", 0.78),
                "expires_at": row.get("expires_at"),
                "total_signers": total,
                "signed_count": signed,
                "sign_order": recipient.get("sign_order"),
                "already_signed": True,
            }
        return {
            "token": token,
            "status": row.get("status"),
            "recipient_email": recipient.get("email"),
            "recipient_name": recipient.get("name") or "",
            "owner_message": row.get("owner_message") or "",
            "original_filename": row.get("original_filename") or "documento.pdf",
            "page_number": recipient.get("page_number", -1),
            "pos_x": recipient.get("pos_x", 0.62),
            "pos_y": recipient.get("pos_y", 0.78),
            "expires_at": row.get("expires_at"),
            "total_signers": total,
            "signed_count": signed,
            "sign_order": recipient.get("sign_order"),
            "already_signed": False,
        }

    if row.get("status") in {"signed", "completed"}:
        raise HTTPException(410, "Este documento já foi totalmente assinado.")
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
        "total_signers": 1,
        "signed_count": 1 if row.get("status") in {"signed", "completed"} else 0,
        "sign_order": 1,
        "already_signed": row.get("status") in {"signed", "completed"},
    }


@router.get("/public/{token}/pdf")
def download_public_pdf(token: str):
    """PDF atual para visualização (inclui assinaturas já feitas)."""
    mode, recipient, row = _resolve_token(token)
    _check_expired(row)
    if mode == "recipient" and recipient and recipient.get("status") == "signed":
        pass
    elif mode == "legacy" and row.get("status") in {"signed", "completed"}:
        raise HTTPException(410, "Este documento já foi assinado.")
    try:
        data = download_signing_file(_current_pdf_path(row))
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
    """Destinatário aplica carimbo profissional."""
    mode, recipient, row = _resolve_token(token)
    _check_expired(row)

    if mode == "recipient" and recipient:
        if recipient.get("status") == "signed":
            raise HTTPException(410, "Você já assinou este documento.")
        page_int = int(recipient.get("page_number") or -1)
        x_pos = _parse_ratio(x_ratio, float(recipient.get("pos_x") or 0.62))
        y_pos = _parse_ratio(y_ratio, float(recipient.get("pos_y") or 0.78))
    else:
        if row.get("status") in {"signed", "completed"}:
            raise HTTPException(410, "Este documento já foi assinado.")
        page_int = int(row.get("page_number") or -1)
        x_pos = _parse_ratio(x_ratio, float(row.get("pos_x") or 0.62))
        y_pos = _parse_ratio(y_ratio, float(row.get("pos_y") or 0.78))

    if not label.strip() and not (stamp and stamp.filename):
        raise HTTPException(400, "Informe o nome ou envie imagem da assinatura.")

    stamp_path: Path | None = None
    local_pdf: Path | None = None
    out: Path | None = None
    signed_path = f"{row['owner_user_id']}/{row['token']}/signed.pdf"
    try:
        local_pdf = save_signing_file_to_temp(_current_pdf_path(row))
        if stamp and stamp.filename:
            stamp_path = await _save(stamp, images=True)
        out = _tmp()
        add_signature_stamp(
            local_pdf,
            out,
            label=label,
            image_path=stamp_path,
            page_number=page_int,
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

        sb = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        ip = get_client_ip(request)

        if mode == "recipient" and recipient:
            sb.table("signing_recipients").update(
                {
                    "status": "signed",
                    "signer_info": signer_info,
                    "signed_at": now,
                    "signer_ip": ip,
                    "pos_x": x_pos,
                    "pos_y": y_pos,
                }
            ).eq("token", token).execute()
            recipients = _get_recipients_for_request(str(row["id"]))
            signed = _signed_count(recipients)
            total = len(recipients)
            new_status = "completed" if signed >= total else "partial"
        else:
            new_status = "signed"
            recipients = []

        update_row: dict[str, Any] = {
            "signed_storage_path": signed_path,
            "signer_info": signer_info,
            "signer_ip": ip,
            "pos_x": x_pos,
            "pos_y": y_pos,
        }
        if new_status in {"signed", "completed"}:
            update_row["signed_at"] = now
        update_row["status"] = new_status
        sb.table("signing_requests").update(update_row).eq("id", row["id"]).execute()

        _log_signature_event(
            str(row["owner_user_id"]),
            event_type="link_signed",
            filename=row.get("original_filename") or "documento.pdf",
            signer_name=label.strip(),
            stamp_info=signer_info,
            signing_request_id=str(row.get("id")) if row.get("id") else None,
        )
        progress = _request_progress({**row, "id": row["id"], "status": new_status})
        return {
            "success": True,
            "download_url": f"/api/signing/public/{token}/signed",
            "filename": "documento_assinado.pdf",
            "signed_count": progress["signed_count"],
            "total_signers": progress["total_signers"],
            "completed": new_status in {"signed", "completed"},
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
    """PDF com as assinaturas já aplicadas."""
    mode, recipient, row = _resolve_token(token)
    if not row.get("signed_storage_path"):
        raise HTTPException(400, "Nenhuma assinatura registrada ainda.")
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
    """Dono baixa o PDF (parcial ou completo)."""
    row = _get_request_by_token(token)
    if row.get("owner_user_id") != user.user_id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if not row.get("signed_storage_path"):
        raise HTTPException(400, "Nenhuma assinatura registrada ainda.")
    try:
        data = download_signing_file(row["signed_storage_path"])
    except Exception as exc:
        raise HTTPException(404, "Arquivo assinado não encontrado.") from exc
    name = (row.get("original_filename") or "documento.pdf").replace(".pdf", "_assinado.pdf")
    tmp = Path(tempfile.gettempdir()) / f"docsplit_dl_{token}.pdf"
    tmp.write_bytes(data)
    return FileResponse(tmp, media_type="application/pdf", filename=name)
