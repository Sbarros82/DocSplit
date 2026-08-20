"""Libera créditos a partir de pagamentos do Mercado Pago (webhook/sync)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from api.payment import CREDIT_PACKAGES, get_payment

logger = logging.getLogger(__name__)

_AMOUNT_TO_CREDITS: dict[int, int] = {
    int(pkg["price_brl"]): int(pkg["credits_mb"]) for pkg in CREDIT_PACKAGES.values()
}

_EXT_REF_RE = re.compile(
    r"^user_(?P<user_id>[0-9a-fA-F-]{36})_pkg_(?P<package_id>basic|plus|pro|premium)$"
)


def _parse_user_and_package(payment: dict[str, Any]) -> tuple[str | None, str | None, int]:
    """Extrai user_id, package_id e credits_mb do pagamento MP."""
    metadata = payment.get("metadata") or {}
    user_id = metadata.get("user_id") or None
    package_id = metadata.get("package_id") or None
    credits_raw = metadata.get("credits_mb")

    if not user_id or not package_id:
        match = _EXT_REF_RE.match(str(payment.get("external_reference") or ""))
        if match:
            user_id = user_id or match.group("user_id")
            package_id = package_id or match.group("package_id")

    credits_mb: int | None = None
    if credits_raw is not None:
        try:
            credits_mb = int(credits_raw)
        except (TypeError, ValueError):
            credits_mb = None

    if credits_mb is None and package_id and package_id in CREDIT_PACKAGES:
        credits_mb = int(CREDIT_PACKAGES[package_id]["credits_mb"])

    if credits_mb is None:
        amount = payment.get("transaction_amount")
        try:
            amount_rounded = int(round(float(amount)))
        except (TypeError, ValueError):
            amount_rounded = 0
        credits_mb = _AMOUNT_TO_CREDITS.get(amount_rounded, max(0, amount_rounded * 10))

    return user_id, package_id, int(credits_mb)


def fulfill_mercadopago_payment(payment_id: str) -> dict[str, Any]:
    """Busca o pagamento no MP e libera créditos se estiver aprovado.

    Idempotente: se a transação já estiver approved, não soma créditos de novo.
    """
    payment = get_payment(str(payment_id))
    return apply_mercadopago_payment(payment)


def apply_mercadopago_payment(payment: dict[str, Any]) -> dict[str, Any]:
    """Aplica o resultado de um pagamento já carregado do Mercado Pago."""
    from src.pdf_splitter.supabase_client import get_supabase

    payment_id = str(payment["id"])
    status = str(payment.get("status") or "unknown")
    user_id, package_id, credits_mb = _parse_user_and_package(payment)

    if not user_id:
        logger.error("Pagamento %s sem user_id no metadata/external_reference", payment_id)
        return {
            "ok": False,
            "payment_id": payment_id,
            "status": status,
            "error": "missing_user_id",
        }

    sb = get_supabase()
    existing = (
        sb.table("transactions")
        .select("id,payment_status,credits_mb")
        .eq("payment_id", payment_id)
        .limit(1)
        .execute()
    )
    row = (existing.data or [None])[0]

    if row and row.get("payment_status") == "approved":
        return {
            "ok": True,
            "payment_id": payment_id,
            "status": "approved",
            "user_id": user_id,
            "credits_mb": int(row.get("credits_mb") or credits_mb),
            "already_credited": True,
        }

    amount = float(payment.get("transaction_amount") or 0)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=90)
    method = str(
        payment.get("payment_type_id")
        or payment.get("payment_method_id")
        or "mercadopago"
    )

    payload = {
        "user_id": user_id,
        "amount_brl": amount,
        "credits_mb": credits_mb,
        "payment_method": method,
        "payment_id": payment_id,
        "payment_status": status,
        "expires_at": expires_at.isoformat(),
        "approved_at": now.isoformat() if status == "approved" else None,
        "payment_metadata": {
            "package_id": package_id,
            "mp_status": status,
            "mp_status_detail": payment.get("status_detail"),
            "source": "mercadopago_fulfillment",
        },
    }

    if row:
        sb.table("transactions").update(payload).eq("payment_id", payment_id).execute()
    else:
        sb.table("transactions").insert(payload).execute()

    credited = False
    available_mb = None
    if status == "approved" and credits_mb > 0:
        user_resp = (
            sb.table("users")
            .select("total_credits_mb,used_credits_mb")
            .eq("id", user_id)
            .single()
            .execute()
        )
        user = user_resp.data or {}
        new_total = int(user.get("total_credits_mb") or 0) + credits_mb
        sb.table("users").update({"total_credits_mb": new_total}).eq("id", user_id).execute()
        credited = True
        available_mb = max(0, new_total - int(user.get("used_credits_mb") or 0))
        logger.info(
            "Créditos liberados: payment=%s user=%s +%sMB total=%s",
            payment_id,
            user_id,
            credits_mb,
            new_total,
        )

    return {
        "ok": True,
        "payment_id": payment_id,
        "status": status,
        "user_id": user_id,
        "credits_mb": credits_mb,
        "credited": credited,
        "already_credited": False,
        "available_mb": available_mb,
    }


def extract_payment_id_from_webhook(body: dict[str, Any] | None, query: dict[str, str]) -> str | None:
    """Extrai o ID do pagamento dos formatos de notificação do Mercado Pago."""
    data = body or {}
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    candidates = [
        nested.get("id") if nested else None,
        data.get("id"),
        data.get("data.id"),
        query.get("data.id"),
        query.get("id"),
        query.get("payment_id"),
    ]
    topic = str(data.get("type") or data.get("topic") or query.get("topic") or query.get("type") or "")
    for raw in candidates:
        if raw is None or raw == "":
            continue
        text = str(raw).strip()
        if text.isdigit():
            if topic and "merchant_order" in topic.lower():
                continue
            return text
    return None
