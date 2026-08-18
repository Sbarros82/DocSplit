"""
Dicionário de regras de classificação de documentos.

Responsabilidade:
- Definir padrões (regex/palavras-chave) para cada tipo de documento
- Aplicar regras sobre o texto extraído
- Retornar tipo de documento + confiança quando houver match

Baseado em docs/05_regras_classificacao.md
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .schemas import ClassificationResult


@dataclass
class Rule:
    """Define uma regra de classificação de documento."""

    doc_type: str
    patterns: list[str]
    supplier_pattern: str | None = None
    confidence: float = 0.9
    is_regex: bool = False


# Ordem não importa: o match vencedor é o de maior confiança e, em
# empate, o padrão mais longo (mais específico).
RULES: list[Rule] = [
    Rule(
        doc_type="planilha_movimento_caixa",
        patterns=["movimento de caixa", "entrada/saida", "movimento diario"],
        confidence=0.9,
    ),
    Rule(
        doc_type="pix_comprovante",
        patterns=[
            "comprovante de transferencia",
            "pix por chave",
            "pix por dados da conta",
            "transferencia pix",
            "pix realizado",
        ],
        supplier_pattern=(
            r"(?:nome do (?:benefici[aáà]rio|favorecido)|nome favorecido|favorecido)"
            r"\s*:?\s*(.+?)(?:\n|cpf|cnpj|chave|institui|$)"
        ),
        confidence=0.95,
    ),
    Rule(
        doc_type="pix_qrcode_comprovante",
        patterns=["qr code pix", "qrcode pix", "pagamento via qr code", "qr code pix"],
        supplier_pattern=(
            r"(?:nome do (?:benefici[aáà]rio|favorecido)|nome favorecido|favorecido)"
            r"\s*:?\s*(.+?)(?:\n|cpf|cnpj|chave|institui|$)"
        ),
        confidence=0.95,
    ),
    Rule(
        doc_type="boleto_outros_bancos",
        patterns=[
            "comprovante de pagamento outros bancos",
            "pagamento de boleto",
            "pagamento outros bancos",
        ],
        supplier_pattern=(
            r"(?:benefici[aáà]rio|favorecido|razao social do benefici[aáà]rio)"
            r"\s*:?\s*(.+?)(?:\n|cpf|cnpj|$)"
        ),
        confidence=0.9,
    ),
    Rule(
        doc_type="recibo_pagador",
        patterns=[
            "recibo do pagador",
            "recibo de pagador",
            "comprovante de beneficiario",
        ],
        supplier_pattern=(
            r"(?:benefici[aáà]rio|cedente)\s*:?\s*(.+?)(?:\n|cnpj|cpf|$)"
        ),
        confidence=0.9,
    ),
    # DARF: NÃO usar "documento de arrecadação" — DUAM e DAR/CB IPVA
    # também trazem essa frase e roubavam a classificação.
    Rule(
        doc_type="darf",
        patterns=["darf", "receita federal", "secretaria da receita federal"],
        confidence=0.95,
    ),
    Rule(
        doc_type="fgts_detalhe",
        patterns=["detalhe da guia", "detalhe da guia emitida", "relacao de trabalhadores"],
        confidence=0.95,
    ),
    Rule(
        doc_type="fgts_guia",
        patterns=["gfd", "guia do fgts digital", "fgts digital", "guia de recolhimento do fgts"],
        confidence=0.95,
    ),
    Rule(
        doc_type="relacao_bases_inss",
        patterns=["relacao de bases do inss", "relacao de bases", "bases do inss"],
        confidence=0.95,
    ),
    Rule(
        doc_type="folha_pagamento",
        patterns=["extrato mensal", "folha mensal", "folha de pagamento", "demonstrativo de pagamento"],
        confidence=0.9,
    ),
    Rule(
        doc_type="nfe",
        patterns=[
            "nf-e",
            "danfe",
            "documento auxiliar da nota fiscal",
            "nota fiscal eletronica",
        ],
        supplier_pattern=r"(?:razao social|nome/razao social)\s*:?\s*(.+?)(?:\n|cnpj|$)",
        confidence=0.95,
    ),
    Rule(
        doc_type="conta_energia",
        patterns=["neoenergia", "coelba", "energia eletrica", "conta de energia", "aneel"],
        supplier_pattern=r"(neoenergia|coelba|celpe|cosern)",
        confidence=0.95,
    ),
    Rule(
        doc_type="viasat_fatura",
        patterns=["viasat", "viasat brasil"],
        supplier_pattern=r"(viasat(?: brasil)?(?: servicos de comunica[cç]oes?)?)",
        confidence=0.95,
    ),
    Rule(
        doc_type="imposto_municipal",
        patterns=[
            "prefeitura de",
            "prefeitura de maceio",
            "duam",
            "guia dam",
            "documento unico de arrecadacao municipal",
            "taxa de funcion",
            "issqn",
        ],
        supplier_pattern=r"prefeitura (?:municipal )?de (.+?)(?:\n|$)",
        confidence=0.92,
    ),
    Rule(
        doc_type="ipva",
        patterns=["ipva parcelado", "ipva", "dar/cb", "dar / cb"],
        confidence=0.96,
    ),
    Rule(
        doc_type="cupom_fiscal",
        patterns=["transacao aprovada", "cupom controle", "cupom fiscal"],
        supplier_pattern=r"(mercado .+?)(?:\n|cnpj|$)",
        confidence=0.85,
    ),
    Rule(
        doc_type="comprovante_pagamento",
        patterns=[
            "pagamento realizado",
            "valor pago via boleto",
            "comprovante de pagamento titulos",
            "identificacao no extrato",
            "comprovante de pagamento",
        ],
        supplier_pattern=(
            r"(?:nome do benefici[aáà]rio|razao social do benefici[aáà]rio|"
            r"valor pago via boleto para)\s*:?\s*(.+?)(?:\n|cpf|cnpj|$)"
        ),
        confidence=0.8,
    ),
]


_CNPJ_RE = re.compile(
    r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})"
)
_PAGE_OF_RE = re.compile(
    r"(?:pagina|folha|pag\.?)\s*(\d+)\s*(?:de|/)\s*(\d+)",
    re.IGNORECASE,
)
_N_DE_M_RE = re.compile(
    r"\b(\d{1,2})\s*de\s*(\d{1,2})\b",
    re.IGNORECASE,
)
_NDE_M_RE = re.compile(r"\b(\d{1,2})de(\d{1,2})\b", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """
    Normaliza texto para matching robusto.

    Lowercase, remove acentos, colapsa espaços. Essencial para OCR
    malformado de documentos brasileiros.
    """
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("ASCII")
    text = " ".join(text.split())
    return text


def extract_cnpj(text: str) -> str | None:
    """
    Extrai o primeiro CNPJ do texto e devolve 14 dígitos, ou None.

    Aceita grafia com ou sem pontuação (OCR costuma misturar).
    """
    if not text:
        return None
    for match in _CNPJ_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(1))
        if len(digits) == 14 and digits != "0" * 14:
            return digits
    return None


def cnpj_base(cnpj: str | None) -> str | None:
    """Raiz do CNPJ (8 primeiros dígitos), para comparar matriz e filial."""
    if not cnpj:
        return None
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) >= 8:
        return digits[:8]
    return None


def parse_page_x_of_y(text: str) -> tuple[int, int] | None:
    """
    Detecta '1 de 2', '2de2', 'página 2/3'.

    Ignora totais maiores que 8 (evita datas e números de documento).
    """
    if not text:
        return None
    normalized = normalize_text(text)
    for regex in (_PAGE_OF_RE, _N_DE_M_RE, _NDE_M_RE):
        match = regex.search(normalized)
        if not match:
            continue
        current = int(match.group(1))
        total = int(match.group(2))
        if 1 <= current <= total <= 8:
            return current, total
    return None


def detect_continuation(text: str) -> bool:
    """
    True se o texto indica continuação da página anterior.

    '2 de 2' / '2de2' / 'continuação'. '1 de 2' é início, não continuação.
    """
    if not text:
        return False
    normalized = normalize_text(text)
    if "continuacao" in normalized:
        return True
    parsed = parse_page_x_of_y(text)
    if parsed and parsed[0] >= 2:
        return True
    return False


def looks_like_spreadsheet(text: str) -> bool:
    """Heurística para planilha fotografada cujo OCR vira grade de letras."""
    if not text or len(text) < 400:
        return False
    tokens = text.split()
    if len(tokens) < 40:
        return False
    short = sum(1 for t in tokens if len(t) <= 2)
    return (short / len(tokens)) > 0.55


def apply_rules(text: str, page_number: int = 0) -> ClassificationResult | None:
    """
    Aplica regras de classificação sobre o texto de uma página.

    Entrada: texto extraído e número da página.
    Saída: ClassificationResult se alguma regra bater, None caso contrário.
    Em empate de confiança, vence o padrão mais longo (mais específico).
    """
    if not text or not text.strip():
        return None

    normalized = normalize_text(text)
    best: tuple[float, int, Rule, str] | None = None

    for rule in RULES:
        for pattern in rule.patterns:
            pattern_normalized = normalize_text(pattern)
            if rule.is_regex:
                found = re.search(pattern_normalized, normalized, re.IGNORECASE) is not None
            else:
                found = pattern_normalized in normalized
            if found:
                score = (rule.confidence, len(pattern_normalized))
                if best is None or score > (best[0], best[1]):
                    best = (rule.confidence, len(pattern_normalized), rule, pattern)

    if best is None:
        return None

    _, _, rule, pattern = best
    supplier = None
    if rule.supplier_pattern:
        supplier = extract_supplier(text, rule.supplier_pattern)
        if supplier is None:
            supplier = extract_supplier(normalized, rule.supplier_pattern)

    return ClassificationResult(
        page_number=page_number,
        doc_type=rule.doc_type,
        supplier=_clean_supplier(supplier),
        confidence=rule.confidence,
        source="rule",
        matched_pattern=pattern,
        is_continuation=detect_continuation(text),
        cnpj=extract_cnpj(text),
    )


def extract_supplier(text: str, pattern: str) -> str | None:
    """Extrai nome do fornecedor/beneficiário usando regex. None se não achar."""
    try:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match and match.groups():
            supplier = match.group(1).strip()
            supplier = " ".join(supplier.split())
            supplier = supplier.strip(" :-")
            return supplier if supplier else None
    except re.error:
        return None
    return None


def _clean_supplier(supplier: str | None) -> str | None:
    if not supplier:
        return None
    supplier = re.sub(r"\s+", " ", supplier).strip(" :-.,")
    if len(supplier) > 60:
        supplier = supplier[:60].rsplit(" ", 1)[0]
    if len(supplier) < 3:
        return None
    return supplier
