"""Precificação do DocSplit Rápido (cobrança por página)."""

from __future__ import annotations

from dataclasses import dataclass

PRICE_PER_PAGE_LE_50 = 0.50
PRICE_PER_PAGE_GT_50 = 0.25
MIN_AMOUNT_BRL = 2.00
EXPRESS_MAX_FILE_MB = 25.0
EXPRESS_MAX_PAGES = 500


@dataclass(frozen=True)
class ExpressQuote:
    """Cotação de um job expresso."""

    pages: int
    price_per_page_brl: float
    amount_brl: float
    file_size_mb: float


def price_per_page(pages: int) -> float:
    """Retorna o valor por página conforme a faixa do documento."""
    if pages <= 0:
        raise ValueError("O PDF precisa ter ao menos 1 página.")
    if pages <= 50:
        return PRICE_PER_PAGE_LE_50
    return PRICE_PER_PAGE_GT_50


def quote_express(pages: int, file_size_mb: float) -> ExpressQuote:
    """Calcula o valor a cobrar (mínimo R$ 2,00).

    Regras:
    - até 50 páginas: R$ 0,50/página
    - acima de 50 páginas: R$ 0,25/página (todas as páginas)
    - mínimo: R$ 2,00
    """
    if pages <= 0:
        raise ValueError("O PDF precisa ter ao menos 1 página.")
    if pages > EXPRESS_MAX_PAGES:
        raise ValueError(f"Máximo de {EXPRESS_MAX_PAGES} páginas neste fluxo.")
    if file_size_mb > EXPRESS_MAX_FILE_MB:
        raise ValueError(
            f"Arquivo acima de {EXPRESS_MAX_FILE_MB:.0f} MB. "
            "Comprima o PDF antes (limite do WhatsApp)."
        )
    per_page = price_per_page(pages)
    raw = round(pages * per_page, 2)
    amount = max(MIN_AMOUNT_BRL, raw)
    return ExpressQuote(
        pages=pages,
        price_per_page_brl=per_page,
        amount_brl=round(amount, 2),
        file_size_mb=round(float(file_size_mb), 2),
    )


def normalize_whatsapp(raw: str) -> str:
    """Normaliza telefone BR para dígitos com DDI 55 quando possível."""
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if not digits:
        raise ValueError("Informe um WhatsApp válido com DDD.")
    if len(digits) < 10:
        raise ValueError("WhatsApp incompleto. Use DDD + número.")
    if digits.startswith("55") and len(digits) >= 12:
        return digits
    if len(digits) in {10, 11}:
        return "55" + digits
    if len(digits) >= 12:
        return digits
    raise ValueError("WhatsApp inválido. Ex.: 82999999999")
