"""
Rotas de pagamento e checkout.
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

from api.auth import CurrentUser, get_current_user
from api.payment import CREDIT_PACKAGES, create_preference, is_configured as mp_configured
from api.payment_fulfillment import (
    extract_payment_id_from_webhook,
    fulfill_mercadopago_payment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


class CreateCheckoutRequest(BaseModel):
    user_email: EmailStr
    package_id: Literal["basic", "plus", "pro", "premium"]
    user_id: str | None = None


@router.get("/packages")
def list_packages():
    """Lista pacotes de créditos disponíveis."""
    return {
        "packages": [
            {
                "id": pid,
                **pkg,
                "price_formatted": f"R$ {pkg['price_brl']:.2f}",
                "credits_formatted": f"{pkg['credits_mb']} MB",
            }
            for pid, pkg in CREDIT_PACKAGES.items()
        ]
    }


@router.post("/create-checkout")
async def create_checkout(
    body: CreateCheckoutRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Cria um checkout do Mercado Pago.

    Retorna URL para redirecionar o usuário ao pagamento.
    """
    user_id = user.user_id
    user_email = body.user_email or user.email or ""
    if not user_id:
        raise HTTPException(401, "Faça login para continuar.")

    if not mp_configured():
        raise HTTPException(
            status_code=503,
            detail="Pagamentos temporariamente indisponíveis (Mercado Pago não configurado)",
        )

    try:
        preference = create_preference(
            user_id=user_id,
            package_id=body.package_id,
            user_email=user_email,
            success_url=f"{FRONTEND_URL}/payment/success",
            failure_url=f"{FRONTEND_URL}/payment/failure",
            pending_url=f"{FRONTEND_URL}/payment/pending",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    is_test = "TEST" in os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
    checkout_url = preference["sandbox_init_point"] if is_test else preference["init_point"]

    return {
        "checkout_url": checkout_url,
        "preference_id": preference["id"],
    }


@router.post("/webhook")
@router.get("/webhook")
async def mercadopago_webhook(request: Request):
    """Recebe notificações do Mercado Pago e libera créditos quando aprovado.

    Endpoint público (sem JWT). Sempre responde 200 para evitar retries infinitos
    em erros de negócio; falhas de infraestrutura ainda podem retornar 5xx.
    """
    body: dict | None = None
    try:
        if request.method == "POST":
            body = await request.json()
    except Exception:
        body = None

    query = {k: str(v) for k, v in request.query_params.items()}
    payment_id = extract_payment_id_from_webhook(body, query)

    logger.info("Webhook Mercado Pago: method=%s payment_id=%s body=%s query=%s",
                request.method, payment_id, body, query)

    if not payment_id:
        return {"status": "ignored", "reason": "no_payment_id"}

    try:
        result = fulfill_mercadopago_payment(payment_id)
        return {"status": "ok", **result}
    except Exception as exc:
        logger.exception("Falha ao processar webhook payment_id=%s", payment_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/confirm/{payment_id}")
def confirm_payment(
    payment_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Consulta o pagamento no MP e libera créditos (fallback do webhook)."""
    if not mp_configured():
        raise HTTPException(503, "Mercado Pago não configurado")

    try:
        result = fulfill_mercadopago_payment(payment_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar pagamento: {exc}") from exc

    if result.get("error") == "missing_user_id":
        raise HTTPException(400, "Pagamento sem referência de usuário")

    if result.get("user_id") and result["user_id"] != user.user_id:
        from api.credits import _is_admin_account

        if not _is_admin_account(user):
            raise HTTPException(403, "Este pagamento não pertence à sua conta")

    return result
