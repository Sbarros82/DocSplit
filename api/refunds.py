"""Cálculo e execução de reembolsos DocSplit."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from api.payment import create_refund, extract_fee_brl, get_payment

logger = logging.getLogger(__name__)

# Meios em que a política desconta a taxa da operadora do valor devolvido.
FEE_DEDUCT_METHODS = frozenset(
    {
        "credit_card",
        "debit_card",
        "ticket",  # boleto
        "visa",
        "master",
        "elo",
        "amex",
        "hipercard",
        "bolbradesco",
        "pec",
    }
)

FEE_DEDUCT_TYPES = frozenset({"credit_card", "debit_card", "ticket"})


def _method_deducts_fee(payment_method: str | None, payment_type: str | None = None) -> bool:
    method = (payment_method or "").lower()
    ptype = (payment_type or "").lower()
    if method in FEE_DEDUCT_METHODS or ptype in FEE_DEDUCT_TYPES:
        return True
    if "credit" in method or "debit" in method or "boleto" in method or method == "ticket":
        return True
    return False


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_refund_preview(tx: dict[str, Any], user: dict[str, Any], mp_payment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monta prévia de reembolso conforme a política DocSplit."""
    amount = _as_float(tx.get("amount_brl"))
    credits_mb = int(tx.get("credits_mb") or 0)
    already_refunded_amount = _as_float(tx.get("refunded_amount_brl"))
    already_refunded_credits = int(tx.get("refunded_credits_mb") or 0)
    fee_stored = _as_float(tx.get("fee_brl"))

    fee = fee_stored
    payment_method = str(tx.get("payment_method") or "")
    payment_type = None
    mp_status = None

    if mp_payment:
        fee = extract_fee_brl(mp_payment) if extract_fee_brl(mp_payment) > 0 else fee_stored
        payment_method = str(mp_payment.get("payment_method_id") or payment_method)
        payment_type = str(mp_payment.get("payment_type_id") or "")
        mp_status = str(mp_payment.get("status") or "")

    deduct_fee = _method_deducts_fee(payment_method, payment_type)
    # PIX / transferências: devolve o valor pago (taxa não é descontada na política).
    max_refundable_money = round(amount - fee, 2) if deduct_fee else round(amount, 2)
    max_refundable_money = max(0.0, max_refundable_money - already_refunded_amount)

    available_mb = max(0, int(user.get("total_credits_mb") or 0) - int(user.get("used_credits_mb") or 0))
    remaining_pack_credits = max(0, credits_mb - already_refunded_credits)
    credits_to_claw = min(available_mb, remaining_pack_credits)

    ratio = (credits_to_claw / credits_mb) if credits_mb > 0 else 0.0
    # Valor proporcional aos créditos ainda disponíveis do pacote.
    refund_amount = round(max_refundable_money * ratio, 2) if remaining_pack_credits else 0.0
    if credits_to_claw == remaining_pack_credits and remaining_pack_credits > 0:
        refund_amount = round(max_refundable_money, 2)

    is_invoice = payment_method.lower() in {"invoice", "manual", "faturado"} or str(
        (tx.get("payment_id") or "")
    ).startswith("invoice_")

    reasons: list[str] = []
    status = str(tx.get("payment_status") or "")
    if status not in {"approved", "partially_refunded"}:
        reasons.append("Pagamento não está aprovado.")
    if remaining_pack_credits <= 0 or already_refunded_amount >= amount:
        reasons.append("Transação já reembolsada.")
    if credits_to_claw <= 0:
        reasons.append("Sem créditos disponíveis na conta para estornar (pacote já usado).")
    if not is_invoice and refund_amount <= 0:
        reasons.append("Valor reembolsável zerado.")
    if mp_status and mp_status not in {"approved"}:
        reasons.append(f"Status no Mercado Pago: {mp_status}.")

    can_refund = len(reasons) == 0

    return {
        "transaction_id": tx.get("id"),
        "payment_id": tx.get("payment_id"),
        "payment_method": payment_method,
        "payment_type": payment_type,
        "amount_brl": amount,
        "fee_brl": round(fee, 2),
        "deduct_fee": deduct_fee,
        "already_refunded_amount_brl": already_refunded_amount,
        "already_refunded_credits_mb": already_refunded_credits,
        "available_mb": available_mb,
        "credits_mb": credits_mb,
        "credits_to_claw_mb": credits_to_claw,
        "refund_amount_brl": refund_amount if not is_invoice else 0.0,
        "is_invoice": is_invoice,
        "mp_money_refund": not is_invoice and refund_amount > 0,
        "can_refund": can_refund,
        "block_reasons": reasons,
        "policy_note": (
            "Cartão/boleto/débito: devolve valor pago menos taxa da operadora, "
            "proporcional aos créditos ainda disponíveis. PIX: devolve o valor pago "
            "(sem descontar taxa). Faturado: só estorna créditos; dinheiro fora do MP."
        ),
    }


def execute_refund(
    *,
    tx: dict[str, Any],
    user: dict[str, Any],
    admin_id: str | None,
    note: str | None = None,
    force_credits_only: bool = False,
) -> dict[str, Any]:
    """Executa reembolso: estorna créditos e, se aplicável, devolve no Mercado Pago."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    payment_id = str(tx.get("payment_id") or "")
    is_invoice = payment_id.startswith("invoice_") or str(tx.get("payment_method") or "").lower() == "invoice"

    mp_payment = None
    if not is_invoice and payment_id.isdigit():
        mp_payment = get_payment(payment_id)

    preview = build_refund_preview(tx, user, mp_payment)
    if not preview["can_refund"]:
        raise ValueError("; ".join(preview["block_reasons"]) or "Reembolso não permitido")

    credits_to_claw = int(preview["credits_to_claw_mb"])
    refund_amount = float(preview["refund_amount_brl"])
    fee = float(preview["fee_brl"])
    mp_refund_id = None

    if preview["mp_money_refund"] and not force_credits_only:
        refund = create_refund(payment_id, refund_amount)
        mp_refund_id = str(refund.get("id") or "")

    now = datetime.now(timezone.utc)
    new_total = max(0, int(user.get("total_credits_mb") or 0) - credits_to_claw)
    sb.table("users").update({"total_credits_mb": new_total}).eq("id", user["id"]).execute()

    new_refunded_amount = round(_as_float(tx.get("refunded_amount_brl")) + refund_amount, 2)
    new_refunded_credits = int(tx.get("refunded_credits_mb") or 0) + credits_to_claw
    pack_credits = int(tx.get("credits_mb") or 0)
    if new_refunded_credits >= pack_credits:
        new_status = "refunded"
    else:
        new_status = "partially_refunded"

    meta = dict(tx.get("payment_metadata") or {})
    meta["last_refund"] = {
        "at": now.isoformat(),
        "amount_brl": refund_amount,
        "credits_mb": credits_to_claw,
        "fee_brl": fee,
        "mp_refund_id": mp_refund_id,
        "by": admin_id,
        "note": note,
    }

    sb.table("transactions").update(
        {
            "payment_status": new_status,
            "fee_brl": fee,
            "net_amount_brl": round(_as_float(tx.get("amount_brl")) - fee, 2),
            "refunded_amount_brl": new_refunded_amount,
            "refunded_credits_mb": new_refunded_credits,
            "refunded_at": now.isoformat(),
            "refund_note": note,
            "payment_metadata": meta,
        }
    ).eq("id", tx["id"]).execute()

    grant_res = (
        sb.table("refund_requests")
        .insert(
            {
                "transaction_id": tx["id"],
                "user_id": user["id"],
                "requested_by": admin_id,
                "status": "completed",
                "amount_brl": refund_amount,
                "fee_brl": fee,
                "credits_mb": credits_to_claw,
                "mp_refund_id": mp_refund_id,
                "note": note,
            }
        )
        .execute()
    )

    logger.info(
        "Reembolso ok tx=%s user=%s amount=%s credits=%s mp_refund=%s",
        tx.get("id"),
        user.get("id"),
        refund_amount,
        credits_to_claw,
        mp_refund_id,
    )

    return {
        "success": True,
        "preview": preview,
        "payment_status": new_status,
        "refund_amount_brl": refund_amount,
        "credits_clawed_mb": credits_to_claw,
        "mp_refund_id": mp_refund_id,
        "user_available_mb": max(0, new_total - int(user.get("used_credits_mb") or 0)),
        "refund_request_id": (grant_res.data or [{}])[0].get("id"),
        "invoice_manual_money": is_invoice,
    }
