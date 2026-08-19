"""
Rotas de pagamento e checkout.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Literal
import os

from api.auth import CurrentUser, get_optional_user
from .payment import create_preference, CREDIT_PACKAGES, is_configured as mp_configured

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
    user: CurrentUser | None = Depends(get_optional_user),
):
    """
    Cria um checkout do Mercado Pago.
    
    Retorna URL para redirecionar o usuário ao pagamento.
    """
    user_id = user.user_id if user else body.user_id
    user_email = body.user_email or (user.email if user else "")
    if not user_id:
        raise HTTPException(401, "Faça login para continuar.")

    if not mp_configured():
        raise HTTPException(
            status_code=503,
            detail="Pagamentos temporariamente indisponíveis (Mercado Pago não configurado)"
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
        
        # Retornar init_point (URL de pagamento)
        # Em produção usar init_point, em sandbox usar sandbox_init_point
        is_test = "TEST" in os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
        checkout_url = preference["sandbox_init_point"] if is_test else preference["init_point"]
        
        return {
            "checkout_url": checkout_url,
            "preference_id": preference["id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def mercadopago_webhook(request: Request):
    """
    Webhook do Mercado Pago.
    
    IMPORTANTE: Este endpoint é chamado pelo Mercado Pago quando o status
    de um pagamento muda. Configure a URL no painel do Mercado Pago:
    https://www.mercadopago.com.br/developers/panel/notifications/webhooks
    
    URL do webhook: https://seu-backend.railway.app/api/payment/webhook
    
    NOTA: Na produção, use a Edge Function do Supabase para processar
    o webhook (mais confiável que FastAPI em serverless).
    """
    body = await request.json()
    
    # Log para debug
    print(f"Webhook Mercado Pago recebido: {body}")
    
    # O processamento real está na Edge Function do Supabase
    # (supabase/functions/handle-mercadopago-webhook)
    # Este endpoint apenas confirma o recebimento
    
    return {"status": "received"}
