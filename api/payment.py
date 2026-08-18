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


def is_configured() -> bool:
    """Verifica se as credenciais do Mercado Pago estão configuradas."""
    return bool(MP_ACCESS_TOKEN and MP_PUBLIC_KEY)
