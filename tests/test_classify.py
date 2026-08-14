"""Testes para o módulo de classificação."""

import pytest
from src.pdf_splitter.rules import apply_rules, normalize_text


def test_normalize_text_removes_accents():
    """Testa normalização de texto."""
    # TODO: implementar quando módulo estiver pronto
    # assert normalize_text("São José") == "sao jose"
    # assert normalize_text("DARF - Receita Federal") == "darf - receita federal"
    pass


def test_apply_rules_detects_pix():
    """Testa detecção de comprovante PIX."""
    text = """
    Comprovante de Transferência PIX
    Nome do beneficiário: MARIA DA SILVA
    CPF: 123.456.789-00
    Valor: R$ 1.500,00
    """
    
    # TODO: implementar quando módulo estiver pronto
    # result = apply_rules(text)
    # assert result is not None
    # assert result.doc_type == "pix_comprovante"
    # assert result.confidence >= 0.9
    pass


def test_apply_rules_detects_nfe():
    """Testa detecção de nota fiscal eletrônica."""
    # TODO: implementar
    pass


# TODO: adicionar mais testes de regras
