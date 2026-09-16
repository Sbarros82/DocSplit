"""DocSplit Rápido: upload → Pix por página → libera ZIP + WhatsApp."""

from __future__ import annotations

import logging
import os
import secrets
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from api.express_pricing import (
    EXPRESS_MAX_FILE_MB,
    quote_express,
    normalize_whatsapp,
)
from api.express_storage import (
    download_express_file,
    upload_express_file,
)
from api.payment import create_express_preference, is_configured as mp_configured

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/express", tags=["Express"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://docsplit-app.vercel.app")
API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL") or os.environ.get("BACKEND_PUBLIC_URL") or "https://docsplit.fly.dev"
SUPPORT_WHATSAPP = os.environ.get("SUPPORT_WHATSAPP", "5582982218199")


def _sb():
    from src.pdf_splitter.supabase_client import get_supabase

    return get_supabase()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _public_status(row: dict[str, Any]) -> dict[str, Any]:
    token = row["token"]
    download_token = row.get("download_token")
    status = row.get("status") or "awaiting_payment"
    download_url = None
    page_url = f"{FRONTEND_URL}/rapido/{token}"
    if status == "completed" and download_token:
        download_url = f"{API_PUBLIC_URL}/api/express/{token}/download?key={download_token}"
        page_url = f"{FRONTEND_URL}/rapido/{token}?key={download_token}"
    return {
        "token": token,
        "status": status,
        "pages_count": row.get("pages_count"),
        "amount_brl": float(row.get("amount_brl") or 0),
        "price_per_page_brl": float(row.get("price_per_page_brl") or 0),
        "file_size_mb": float(row.get("file_size_mb") or 0),
        "original_filename": row.get("original_filename"),
        "whatsapp": row.get("whatsapp"),
        "payment_status": row.get("payment_status"),
        "download_ready": bool(download_url),
        "download_url": download_url,
        "page_url": page_url,
        "whatsapp_share_url": row.get("whatsapp_share_url"),
        "error_message": row.get("error_message"),
        "expires_at": row.get("expires_at"),
        "pricing": {
            "min_brl": 2.0,
            "le_50": 0.50,
            "gt_50": 0.25,
            "max_file_mb": EXPRESS_MAX_FILE_MB,
        },
    }


def build_whatsapp_share(download_link: str, filename: str, whatsapp: str) -> str:
    """Link wa.me para o cliente abrir o WhatsApp com o download pronto."""
    text = (
        f"DocSplit — seu PDF separado está pronto.\n"
        f"Arquivo: {filename}\n"
        f"Baixar: {download_link}"
    )
    # Abre conversa com o número informado já com a mensagem (cliente pode encaminhar/salvar).
    return f"https://wa.me/{whatsapp}?text={quote(text)}"


def _get_job_by_token(token: str) -> dict[str, Any]:
    rows = (
        _sb()
        .table("express_jobs")
        .select("*")
        .eq("token", token)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(404, "Pedido não encontrado.")
    return rows[0]


@router.get("/pricing")
def express_pricing():
    """Regras públicas de preço do fluxo rápido."""
    return {
        "min_brl": 2.0,
        "price_per_page_le_50": 0.50,
        "price_per_page_gt_50": 0.25,
        "max_file_mb": EXPRESS_MAX_FILE_MB,
        "examples": [
            {"pages": 10, "amount_brl": 5.0},
            {"pages": 50, "amount_brl": 25.0},
            {"pages": 80, "amount_brl": 20.0},
        ],
    }


@router.post("/create")
async def create_express_job(
    file: UploadFile = File(...),
    whatsapp: str = Form(...),
    email: str = Form(""),
):
    """Recebe PDF + WhatsApp, cotiza e devolve checkout Mercado Pago."""
    if not mp_configured():
        raise HTTPException(503, "Pagamentos temporariamente indisponíveis.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo PDF.")

    try:
        phone = normalize_whatsapp(whatsapp)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    contents = await file.read()
    if not contents:
        raise HTTPException(400, "Arquivo vazio.")

    size_mb = round(len(contents) / (1024 * 1024), 2)
    try:
        import fitz

        doc = fitz.open(stream=contents, filetype="pdf")
        pages = int(doc.page_count)
        doc.close()
    except Exception as exc:
        raise HTTPException(400, f"PDF inválido: {exc}") from exc

    try:
        quote = quote_express(pages, size_mb)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    token = secrets.token_urlsafe(16)
    storage_path = f"express/{token}/original.pdf"
    try:
        upload_express_file(storage_path, contents)
    except Exception as exc:
        logger.exception("Falha upload express")
        raise HTTPException(500, f"Falha ao salvar arquivo: {exc}") from exc

    expires_at = (_now() + timedelta(days=2)).isoformat()
    row = {
        "token": token,
        "status": "awaiting_payment",
        "whatsapp": phone,
        "email": (email or "").strip() or None,
        "original_filename": file.filename,
        "storage_path": storage_path,
        "pages_count": quote.pages,
        "file_size_mb": quote.file_size_mb,
        "amount_brl": quote.amount_brl,
        "price_per_page_brl": quote.price_per_page_brl,
        "expires_at": expires_at,
        "updated_at": _now().isoformat(),
    }
    inserted = _sb().table("express_jobs").insert(row).execute()
    job = (inserted.data or [row])[0]

    success_url = f"{FRONTEND_URL}/rapido/{token}?paid=1"
    failure_url = f"{FRONTEND_URL}/rapido/{token}?paid=0"
    pending_url = f"{FRONTEND_URL}/rapido/{token}?paid=pending"

    try:
        preference = create_express_preference(
            job_token=token,
            amount_brl=quote.amount_brl,
            pages=quote.pages,
            filename=file.filename,
            payer_email=(email or "").strip() or None,
            success_url=success_url,
            failure_url=failure_url,
            pending_url=pending_url,
        )
    except Exception as exc:
        _sb().table("express_jobs").update(
            {"status": "error", "error_message": str(exc)}
        ).eq("token", token).execute()
        raise HTTPException(500, f"Falha ao criar pagamento: {exc}") from exc

    preference_id = preference.get("id")
    _sb().table("express_jobs").update(
        {"preference_id": preference_id, "updated_at": _now().isoformat()}
    ).eq("token", token).execute()

    is_test = "TEST" in os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
    checkout_url = preference.get("sandbox_init_point") if is_test else preference.get("init_point")

    return {
        "success": True,
        "token": token,
        "checkout_url": checkout_url,
        "preference_id": preference_id,
        "quote": {
            "pages": quote.pages,
            "price_per_page_brl": quote.price_per_page_brl,
            "amount_brl": quote.amount_brl,
            "file_size_mb": quote.file_size_mb,
        },
        "status_url": f"{FRONTEND_URL}/rapido/{token}",
        "job": _public_status({**job, "preference_id": preference_id}),
    }


@router.get("/{token}")
def get_express_job(token: str):
    """Status público do pedido."""
    return _public_status(_get_job_by_token(token))


@router.post("/{token}/sync")
def sync_express_job(token: str, background_tasks: BackgroundTasks, payment_id: str | None = None):
    """Fallback: consulta pagamento no MP e processa (quando webhook atrasa)."""
    row = _get_job_by_token(token)
    if row.get("status") == "completed":
        return _public_status(row)

    from api.payment_fulfillment import fulfill_mercadopago_payment

    pid = payment_id or row.get("payment_id")
    if not pid:
        # Tenta via external_reference não disponível aqui; só status
        return _public_status(row)

    result = fulfill_mercadopago_payment(str(pid))
    row = _get_job_by_token(token)
    if row.get("status") == "paid":
        background_tasks.add_task(process_express_job, token)
    return {"fulfillment": result, "job": _public_status(row)}


@router.get("/{token}/download")
def download_express_result(token: str, key: str):
    """Download do ZIP separado (requer download_token)."""
    row = _get_job_by_token(token)
    if row.get("status") != "completed":
        raise HTTPException(400, "Arquivo ainda não está pronto.")
    if not key or key != row.get("download_token"):
        raise HTTPException(403, "Link de download inválido.")
    result_path = row.get("result_storage_path")
    if not result_path:
        raise HTTPException(404, "Resultado não encontrado.")
    try:
        data = download_express_file(result_path)
    except Exception as exc:
        raise HTTPException(404, "Arquivo expirado ou indisponível.") from exc
    name = (row.get("original_filename") or "documento.pdf").replace(".pdf", "_separados.zip")
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


def mark_express_paid(token: str, payment_id: str, payment_status: str) -> dict[str, Any]:
    """Marca job como pago (idempotente)."""
    sb = _sb()
    row = _get_job_by_token(token)
    if row.get("status") in {"paid", "processing", "completed"}:
        return row
    update = {
        "status": "paid",
        "payment_id": payment_id,
        "payment_status": payment_status,
        "paid_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
    }
    sb.table("express_jobs").update(update).eq("token", token).execute()
    return {**row, **update}


def process_express_job(token: str) -> None:
    """Processa o Separador e libera download + link WhatsApp."""
    sb = _sb()
    try:
        row = _get_job_by_token(token)
    except HTTPException:
        return

    if row.get("status") == "completed":
        return
    if row.get("status") not in {"paid", "processing", "awaiting_payment"}:
        # awaiting_payment só processa se já tiver payment_id (pago)
        if not row.get("payment_id"):
            return

    sb.table("express_jobs").update(
        {"status": "processing", "updated_at": _now().isoformat()}
    ).eq("token", token).execute()

    work_dir = Path(tempfile.mkdtemp(prefix="express_"))
    try:
        from api.index import _run_pipeline_sync

        original = download_express_file(row["storage_path"])
        safe_stem = Path(row.get("original_filename") or "documento").stem.replace(" ", "_") or "documento"
        result = _run_pipeline_sync(original, safe_stem, user_id=f"express:{token}")
        zip_path = Path(result["stored_zip"])
        result_storage = f"express/{token}/result.zip"
        upload_express_file(result_storage, zip_path.read_bytes(), "application/zip")

        download_token = secrets.token_urlsafe(18)
        download_link = f"{API_PUBLIC_URL}/api/express/{token}/download?key={download_token}"
        share = build_whatsapp_share(
            download_link,
            row.get("original_filename") or "documento.pdf",
            str(row.get("whatsapp") or SUPPORT_WHATSAPP),
        )
        sb.table("express_jobs").update(
            {
                "status": "completed",
                "result_storage_path": result_storage,
                "download_token": download_token,
                "whatsapp_share_url": share,
                "completed_at": _now().isoformat(),
                "updated_at": _now().isoformat(),
                "error_message": None,
            }
        ).eq("token", token).execute()
        _notify_whatsapp_optional(
            str(row.get("whatsapp") or ""),
            download_link,
            row.get("original_filename") or "documento.pdf",
        )
        logger.info("Express job completed token=%s", token)
    except Exception as exc:
        logger.exception("Express job failed token=%s", token)
        sb.table("express_jobs").update(
            {
                "status": "error",
                "error_message": str(exc)[:500],
                "updated_at": _now().isoformat(),
            }
        ).eq("token", token).execute()
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _notify_whatsapp_optional(whatsapp: str, download_link: str, filename: str) -> None:
    """Envia mensagem via Cloud API se configurada; senão só loga."""
    token = os.environ.get("WHATSAPP_TOKEN") or os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_id or not whatsapp:
        return
    try:
        import httpx

        text = (
            f"DocSplit: seu PDF *{filename}* está separado.\n"
            f"Baixe aqui: {download_link}"
        )
        httpx.post(
            f"https://graph.facebook.com/v20.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": whatsapp,
                "type": "text",
                "text": {"body": text},
            },
            timeout=20.0,
        )
    except Exception as exc:
        logger.warning("WhatsApp Cloud API falhou: %s", exc)
