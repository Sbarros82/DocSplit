"""
Classificação via LLM (fallback) usando OpenRouter.

Só é chamado quando as regras não classificam com confiança suficiente.
Erros de API não quebram o pipeline: a página fica como desconhecido.
"""

from __future__ import annotations

import json
import re
from typing import Optional

import httpx

from .config import settings
from .schemas import ClassificationResult

SYSTEM_PROMPT = """Você classifica páginas de documentos financeiros/administrativos
brasileiros (boletos, comprovantes PIX, notas fiscais, guias de imposto,
folha de pagamento, etc.).

Responda APENAS em JSON, sem texto adicional, no formato:
{
  "doc_type": "<tipo_curto_em_snake_case>",
  "supplier": "<nome do fornecedor/beneficiário ou null>",
  "confidence": <número de 0.0 a 1.0>,
  "is_continuation": <true/false>,
  "reasoning": "<explicação em uma frase curta>"
}

Use preferencialmente um destes doc_type:
planilha_movimento_caixa, pix_comprovante, pix_qrcode_comprovante,
boleto_outros_bancos, darf, fgts_guia, folha_pagamento, nfe, conta_energia,
viasat_fatura, imposto_municipal, ipva, desconhecido.

"is_continuation": true se esta página parece ser a continuação do mesmo
documento da página anterior (ex: "página 2 de 2", mesmo CNPJ, mesmo
beneficiário sem cabeçalho novo).

Se não conseguir identificar o tipo com razoável certeza, use
"doc_type": "desconhecido" e "confidence" baixo (< 0.5).
"""


def is_configured() -> bool:
    """True se a chave OpenRouter está definida."""
    return bool(settings.openrouter_api_key.strip())


def classify_page(
    text: str,
    page_number: int,
    previous_doc_type: Optional[str] = None,
    previous_supplier: Optional[str] = None,
) -> ClassificationResult:
    """
    Classifica uma página via OpenRouter.

    Em caso de erro de API ou JSON inválido, devolve doc_type="desconhecido"
    com confidence=0.0 (a página segue no lote com needs_review).
    """
    if not is_configured():
        return _unknown(page_number)

    payload = {
        "model": settings.openrouter_model,
        "temperature": 0,
        "max_tokens": 350,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_classification_prompt(
                    text, page_number, previous_doc_type, previous_supplier
                ),
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Sbarros82/DocSplit",
        "X-Title": "DocSplit",
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        return parse_llm_response(content, page_number)
    except Exception as e:
        print(f"Aviso: OpenRouter falhou na página {page_number}: {e}")
        return _unknown(page_number)


def build_classification_prompt(
    text: str,
    page_number: int,
    previous_doc_type: Optional[str] = None,
    previous_supplier: Optional[str] = None,
) -> str:
    """Monta o prompt de usuário (docs/07_prompts_llm.md)."""
    excerpt = (text or "").strip()[:6000]
    return (
        f"Texto extraído da página {page_number}:\n"
        f'"""\n{excerpt}\n"""\n\n'
        f"Tipo de documento da página anterior (se houver): {previous_doc_type or 'nenhum'}\n"
        f"Fornecedor da página anterior (se houver): {previous_supplier or 'nenhum'}\n"
    )


def parse_llm_response(response_text: str, page_number: int) -> ClassificationResult:
    """Interpreta o JSON do modelo; formato inválido vira revisão manual."""
    try:
        parsed = _extract_json(response_text)
        doc_type = str(parsed.get("doc_type") or "desconhecido").strip() or "desconhecido"
        supplier = parsed.get("supplier")
        if supplier is not None:
            supplier = str(supplier).strip() or None
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        return ClassificationResult(
            page_number=page_number,
            doc_type=doc_type,
            supplier=supplier,
            confidence=confidence,
            source="llm",
            matched_pattern=str(parsed.get("reasoning") or "")[:200] or None,
        )
    except Exception:
        return _unknown(page_number)


def _extract_json(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _unknown(page_number: int) -> ClassificationResult:
    return ClassificationResult(
        page_number=page_number,
        doc_type="desconhecido",
        supplier=None,
        confidence=0.0,
        source="llm",
        matched_pattern=None,
    )
