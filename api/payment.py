"""
Módulo de integração com Mercado Pago.
"""

import os
import mercadopago
from typing import Literal

# Configurar SDK
MP_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MP_PUBLIC_KEY = os.environ.get("MERCADOPAGO_PUBLIC_KEY", "")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None

# Pacotes de créditos
CREDIT_PACKAGES = {
    "basic": {"price_brl": 5.0, "credits_mb": 50, "label": "Básico"},
    "plus": {"price_brl": 15.0, "credits_mb": 200, "label": "Plus (Bônus 33%)"},
    "pro": {"price_brl": 30.0, "credits_mb": 500, "label": "Pro (Bônus 67%)"},
    "premium": {"price_brl": 50.0, "credits_mb": 1000, "label": "Premium (Bônus 100%)"},
}


def create_preference(
    user_id: str,
    package_id: Literal["basic", "plus", "pro", "premium"],
    user_email: str,
    success_url: str,
    failure_url: str,
    pending_url: str,
) -> dict:
    """
    Cria uma preferência de pagamento no Mercado Pago.
    
    Returns:
        {
            "id": "preference_id",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect...",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout..."
        }
    """
    if not sdk:
        raise ValueError("Mercado Pago não configurado (MERCADOPAGO_ACCESS_TOKEN ausente)")
    
    package = CREDIT_PACKAGES.get(package_id)
    if not package:
        raise ValueError(f"Pacote inválido: {package_id}")
    
    preference_data = {
        "items": [
            {
                "title": f"DocSplit — {package['label']}",
                "description": f"{package['credits_mb']} MB de créditos (válido por 90 dias)",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": package["price_brl"],
            }
        ],
        "payer": {
            "email": user_email,
        },
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        "auto_return": "approved",
        "metadata": {
            "user_id": user_id,
            "package_id": package_id,
            "credits_mb": package["credits_mb"],
        },
        "statement_descriptor": "DOCSPLIT",
        "external_reference": f"user_{user_id}_pkg_{package_id}",
    }
    
    preference_response = sdk.preference().create(preference_data)
    
    if preference_response["status"] != 201:
        raise Exception(f"Erro ao criar preferência: {preference_response}")
    
    return preference_response["response"]


def get_payment(payment_id: str) -> dict:
    """Busca informações de um pagamento."""
    if not sdk:
        raise ValueError("Mercado Pago não configurado")
    
    payment_response = sdk.payment().get(payment_id)
    
    if payment_response["status"] != 200:
        raise Exception(f"Erro ao buscar pagamento: {payment_response}")
    
    return payment_response["response"]


def create_refund(payment_id: str, amount: float | None = None) -> dict:
    """Cria reembolso total ou parcial no Mercado Pago.

    Se amount for None, reembolsa o valor integral restante.
    """
    if not MP_ACCESS_TOKEN:
        raise ValueError("Mercado Pago não configurado")

    import uuid

    import httpx

    body: dict[str, float] = {}
    if amount is not None:
        body["amount"] = round(float(amount), 2)

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    response = httpx.post(
        f"https://api.mercadopago.com/v1/payments/{payment_id}/refunds",
        headers=headers,
        json=body if body else None,
        timeout=30.0,
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Erro ao criar reembolso: {response.status_code} {response.text}")
    return response.json()


def extract_fee_brl(payment: dict) -> float:
    """Soma as taxas do coletor (Mercado Pago) no pagamento."""
    total = 0.0
    for fee in payment.get("fee_details") or []:
        try:
            if str(fee.get("fee_payer") or "collector") == "collector":
                total += float(fee.get("amount") or 0)
        except (TypeError, ValueError):
            continue
    if total <= 0:
        details = payment.get("transaction_details") or {}
        try:
            net = float(details.get("net_received_amount") or 0)
            amount = float(payment.get("transaction_amount") or 0)
            if amount > 0 and net >= 0 and net <= amount:
                total = round(amount - net, 2)
        except (TypeError, ValueError):
            pass
    return round(total, 2)


def is_configured() -> bool:
    """Verifica se as credenciais do Mercado Pago estão configuradas."""
    return bool(MP_ACCESS_TOKEN and MP_PUBLIC_KEY)
