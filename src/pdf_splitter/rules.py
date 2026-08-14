"""
Dicionário de regras de classificação de documentos.

Responsabilidade:
- Definir padrões (regex/palavras-chave) para cada tipo de documento
- Aplicar regras sobre o texto extraído
- Retornar tipo de documento + confiança quando houver match

Baseado em docs/05_regras_classificacao.md
"""

import re
from dataclasses import dataclass
from typing import Pattern
from .schemas import ClassificationResult


@dataclass
class Rule:
    """Define uma regra de classificação de documento."""
    
    doc_type: str
    patterns: list[str]  # Lista de strings ou regex para buscar
    supplier_pattern: str | None = None  # Regex para extrair fornecedor
    confidence: float = 0.9
    is_regex: bool = False  # Se True, patterns são tratados como regex


# Dicionário de regras baseado em documentos financeiros brasileiros
# Ver docs/05_regras_classificacao.md para detalhes
RULES: list[Rule] = [
    # Planilhas
    Rule(
        doc_type="planilha_movimento_caixa",
        patterns=["movimento de caixa", "entrada/saída", "movimento diário"],
        confidence=0.85,
    ),
    
    # Comprovantes PIX
    Rule(
        doc_type="pix_comprovante",
        patterns=[
            "comprovante de transferência",
            "pix por chave",
            "pix por dados da conta",
            "transferência pix",
        ],
        supplier_pattern=r"(?:Nome do beneficiário|Favorecido):\s*(.+?)(?:\n|$)",
        confidence=0.95,
    ),
    
    Rule(
        doc_type="pix_qrcode_comprovante",
        patterns=["qr code pix", "pagamento via qr code"],
        supplier_pattern=r"(?:Nome do beneficiário|Favorecido):\s*(.+?)(?:\n|$)",
        confidence=0.95,
    ),
    
    # Padrão genérico de comprovante — confiança baixa de propósito
    # (aparece em vários tipos de documento; regras mais específicas vencem)
    Rule(
        doc_type="pix_qrcode_comprovante",
        patterns=["comprovante de pagamento"],
        supplier_pattern=r"(?:Nome do beneficiário|Favorecido):\s*(.+?)(?:\n|$)",
        confidence=0.6,
    ),
    
    # Boletos
    Rule(
        doc_type="boleto_outros_bancos",
        patterns=["comprovante de pagamento outros bancos", "pagamento de boleto"],
        supplier_pattern=r"(?:Beneficiário|Favorecido):\s*(.+?)(?:\n|$)",
        confidence=0.9,
    ),
    
    # Impostos federais
    Rule(
        doc_type="darf",
        patterns=["documento de arrecadação", "darf", "receita federal", "secretaria da receita federal"],
        confidence=0.95,
    ),
    
    # FGTS
    Rule(
        doc_type="fgts_guia",
        patterns=["gfd", "guia do fgts digital", "fgts digital", "guia de recolhimento do fgts"],
        confidence=0.95,
    ),
    
    # Folha de pagamento
    Rule(
        doc_type="folha_pagamento",
        patterns=["extrato mensal", "folha mensal", "folha de pagamento", "demonstrativo de pagamento"],
        confidence=0.85,
    ),
    
    # Notas fiscais eletrônicas
    Rule(
        doc_type="nfe",
        patterns=["nf-e", "danfe", "documento auxiliar da nota fiscal eletrônica", "nota fiscal eletrônica"],
        supplier_pattern=r"(?:Razão Social|Nome/Razão Social):\s*(.+?)(?:\n|CNPJ)",
        confidence=0.95,
    ),
    
    # Conta de energia (verificar antes da regra genérica de NF-e)
    Rule(
        doc_type="conta_energia",
        patterns=["neoenergia", "coelba", "energia elétrica", "consumo de energia", "conta de energia"],
        supplier_pattern=r"(neoenergia|coelba|celpe|cosern)",
        confidence=0.95,
    ),
    
    # Faturas de serviços específicos
    Rule(
        doc_type="viasat_fatura",
        patterns=["viasat", "viasat brasil serviços de comunicações", "viasat brasil"],
        supplier_pattern=r"viasat",
        confidence=0.95,
    ),
    
    # Impostos municipais
    Rule(
        doc_type="imposto_municipal",
        patterns=["prefeitura de", "duam", "documento único de arrecadação municipal", "issqn"],
        supplier_pattern=r"prefeitura (?:municipal )?de (.+?)(?:\n|$)",
        confidence=0.9,
    ),
    
    # IPVA
    Rule(
        doc_type="ipva",
        patterns=["ipva", "imposto sobre propriedade de veículos", "dar/cb"],
        confidence=0.95,
    ),
]


def normalize_text(text: str) -> str:
    """
    Normaliza texto para matching robusto.
    
    Remove acentos, converte para lowercase, colapsa espaços múltiplos.
    Essencial para lidar com OCR imperfeito de documentos brasileiros.
    """
    import unicodedata
    
    # Lowercase
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    
    # Colapsar espaços múltiplos e quebras de linha
    text = ' '.join(text.split())
    
    return text


def apply_rules(text: str, page_number: int = 0) -> ClassificationResult | None:
    """
    Aplica regras de classificação sobre o texto de uma página.
    
    Args:
        text: Texto extraído da página (native_text ou ocr_text)
        page_number: Número da página (para incluir no resultado)
        
    Returns:
        ClassificationResult se alguma regra bater, None caso contrário
        
    Comportamento:
    - Normaliza o texto antes de aplicar patterns
    - Retorna o primeiro match com maior confiança
    - Se encontrar supplier_pattern, tenta extrair o fornecedor
    - Marca source="rule" e inclui matched_pattern para depuração
    """
    if not text or not text.strip():
        return None
    
    normalized = normalize_text(text)
    
    # Avaliar todas as regras e escolher o melhor match:
    # maior confiança primeiro; em empate, o padrão mais longo (mais
    # específico) vence — evita que padrões genéricos "roubem" o match.
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
    
    # Tentar extrair fornecedor
    supplier = None
    if rule.supplier_pattern:
        supplier = extract_supplier(text, rule.supplier_pattern)
    
    return ClassificationResult(
        page_number=page_number,
        doc_type=rule.doc_type,
        supplier=supplier,
        confidence=rule.confidence,
        source="rule",
        matched_pattern=pattern,
    )


def extract_supplier(text: str, pattern: str) -> str | None:
    """
    Extrai nome do fornecedor/beneficiário usando regex.
    
    Args:
        text: Texto do documento
        pattern: Regex pattern para extração
        
    Returns:
        Nome do fornecedor normalizado ou None
    """
    try:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match and match.groups():
            supplier = match.group(1).strip()
            # Limpar e normalizar
            supplier = ' '.join(supplier.split())  # Colapsar espaços
            return supplier if supplier else None
    except Exception:
        pass
    
    return None
