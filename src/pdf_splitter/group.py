"""
Módulo de agrupamento de páginas em documentos.

Responsabilidade:
- Analisar lista de ClassificationResult (na ordem das páginas)
- Decidir quais páginas consecutivas formam um único documento
- Retornar lista de DocumentGroup

Entrada: list[ClassificationResult] (ordenados por page_number)
Saída: list[DocumentGroup]

Regras (prioridade):
1. Continuação explícita ("2 de 2", is_continuation) → mesmo grupo
2. PIX, cupom, planilha, folha e DARF são avulsos (não grudam no vizinho)
3. Mesmo tipo multi-página (fatura, DANFE, DUAM) com fornecedor compatível
4. Pacote Viasat: comprovante + fatura + NF consecutivos
5. Pacote comercial: comprovante/boleto + NF imediatamente depois
   (ex: Premix). Comprovante + recibo SEM NF na sequência ficam separados
   (ex: Oeste Representações).
"""

from __future__ import annotations

from .config import settings
from .rules import cnpj_base
from .schemas import ClassificationResult, DocumentGroup


PIX_TYPES = {"pix_comprovante", "pix_qrcode_comprovante"}
SINGLETON_TYPES = PIX_TYPES | {
    "planilha_movimento_caixa",
    "folha_pagamento",
    "relacao_bases_inss",
    "darf",
    "fgts_detalhe",
    "cupom_fiscal",
}
MULTIPAGE_TYPES = {
    "viasat_fatura",
    "conta_energia",
    "nfe",
    "imposto_municipal",
    "boleto_outros_bancos",
    "fgts_guia",
}
BOLETO_CHAIN_TYPES = {
    "comprovante_pagamento",
    "boleto_outros_bancos",
    "recibo_pagador",
}
TAX_TYPES = {
    "darf",
    "ipva",
    "imposto_municipal",
    "conta_energia",
    "fgts_guia",
    "fgts_detalhe",
    "folha_pagamento",
    "relacao_bases_inss",
}
TYPE_PRIORITY = [
    "viasat_fatura",
    "boleto_outros_bancos",
    "nfe",
    "conta_energia",
    "imposto_municipal",
    "ipva",
    "fgts_guia",
    "recibo_pagador",
    "comprovante_pagamento",
    "darf",
    "pix_comprovante",
    "pix_qrcode_comprovante",
]


def group_pages(classifications: list[ClassificationResult]) -> list[DocumentGroup]:
    """
    Agrupa páginas consecutivas em documentos.

    Entrada: classificações na ordem do PDF.
    Saída: um DocumentGroup por documento. Toda página entra em algum grupo.
    """
    if not classifications:
        return []

    items = sorted(classifications, key=lambda c: c.page_number)
    groups: list[DocumentGroup] = []
    i = 0
    n = len(items)

    while i < n:
        end = i
        while end + 1 < n and _should_attach(items, i, end + 1):
            end += 1
        groups.append(_build_group(items[i : end + 1]))
        i = end + 1

    print(f"\nAgrupamento: {len(items)} paginas -> {len(groups)} documentos")
    return groups


def _should_attach(items: list[ClassificationResult], start: int, nxt: int) -> bool:
    """Decide se a página `nxt` entra no grupo que começa em `start`."""
    current = items[nxt]
    previous = items[nxt - 1]
    group = items[start:nxt]

    if current.is_continuation or _is_back_of_bill(current, previous):
        return True

    if previous.doc_type in PIX_TYPES or current.doc_type in PIX_TYPES:
        return False

    if current.doc_type in SINGLETON_TYPES or previous.doc_type in SINGLETON_TYPES:
        return False

    if _is_viasat(previous) or _is_viasat(current) or any(_is_viasat(p) for p in group):
        if _is_viasat(current):
            return True
        # A NF da Viasat vem logo após a fatura; a NF do próximo fornecedor não.
        if current.doc_type == "nfe" and not any(p.doc_type == "nfe" for p in group):
            return True
        return False

    if (
        current.doc_type == previous.doc_type
        and current.doc_type in MULTIPAGE_TYPES
        and _suppliers_compatible(current, previous)
    ):
        return True

    # Pacote boleto + NF (Premix). Comprovante + recibo só grudam se a NF vem já na sequência.
    if current.doc_type == "nfe":
        if any(p.doc_type in BOLETO_CHAIN_TYPES for p in group):
            return True
        if previous.doc_type in BOLETO_CHAIN_TYPES:
            return True

    if current.doc_type in {"boleto_outros_bancos", "recibo_pagador"}:
        if previous.doc_type == "comprovante_pagamento" and current.doc_type not in TAX_TYPES:
            lookahead = items[nxt + 1] if nxt + 1 < len(items) else None
            return lookahead is not None and lookahead.doc_type == "nfe"

    return False


def _is_viasat(item: ClassificationResult) -> bool:
    if item.doc_type == "viasat_fatura":
        return True
    blob = f"{item.supplier or ''} {item.matched_pattern or ''}".lower()
    return "viasat" in blob


def _is_back_of_bill(current: ClassificationResult, previous: ClassificationResult) -> bool:
    """Verso de fatura de energia / DUAM costuma vir como desconhecido ou mesmo tipo."""
    if previous.doc_type in {"conta_energia", "imposto_municipal"} and current.doc_type in {
        previous.doc_type,
        "desconhecido",
    }:
        if current.confidence < 0.5 or current.doc_type == previous.doc_type:
            return _suppliers_compatible(current, previous) or current.doc_type == "desconhecido"
    return False


def _suppliers_compatible(a: ClassificationResult, b: ClassificationResult) -> bool:
    if cnpj_base(a.cnpj) and cnpj_base(a.cnpj) == cnpj_base(b.cnpj):
        return True
    sa = _norm_supplier(a.supplier)
    sb = _norm_supplier(b.supplier)
    if sa and sb:
        return sa == sb or sa in sb or sb in sa
    return True


def _norm_supplier(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.lower().split())


def _build_group(pages: list[ClassificationResult]) -> DocumentGroup:
    doc_type = _pick_doc_type(pages)
    supplier = _pick_supplier(pages)
    needs_review = any(
        p.confidence < settings.classification_confidence_threshold or p.doc_type == "desconhecido"
        for p in pages
    )
    return DocumentGroup(
        doc_type=doc_type,
        supplier=supplier,
        start_page=pages[0].page_number,
        end_page=pages[-1].page_number,
        needs_review=needs_review,
    )


def _pick_doc_type(pages: list[ClassificationResult]) -> str:
    types = [p.doc_type for p in pages if p.doc_type != "desconhecido"]
    if not types:
        return "desconhecido"
    for preferred in TYPE_PRIORITY:
        if preferred in types:
            return preferred
    return types[0]


def _pick_supplier(pages: list[ClassificationResult]) -> str | None:
    names = [p.supplier for p in pages if p.supplier]
    if not names:
        return None
    return max(names, key=len)


def should_group(
    current: ClassificationResult,
    previous: ClassificationResult,
) -> bool:
    """
    Compatibilidade com testes antigos: decide par a par, sem look-ahead.

    Para o pacote boleto+NF use group_pages(), que enxerga a página seguinte.
    """
    return _should_attach([previous, current], 0, 1)
