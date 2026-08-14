"""Testes para o módulo de exportação."""

import pytest
from pathlib import Path
from src.pdf_splitter.export import validate_groups_coverage
from src.pdf_splitter.schemas import DocumentGroup


def test_validate_groups_coverage_valid():
    """Testa validação com cobertura completa e correta."""
    groups = [
        DocumentGroup(doc_type="pix", supplier=None, start_page=1, end_page=2, needs_review=False),
        DocumentGroup(doc_type="nfe", supplier="Empresa X", start_page=3, end_page=5, needs_review=False),
    ]
    
    # Não deve levantar exceção
    # TODO: implementar quando módulo estiver pronto
    # validate_groups_coverage(groups, total_pages=5)
    pass


def test_validate_groups_coverage_missing_pages():
    """Testa validação com páginas faltando."""
    groups = [
        DocumentGroup(doc_type="pix", supplier=None, start_page=1, end_page=2, needs_review=False),
        DocumentGroup(doc_type="nfe", supplier="Empresa X", start_page=4, end_page=5, needs_review=False),
        # Página 3 está faltando!
    ]
    
    # TODO: implementar quando módulo estiver pronto
    # with pytest.raises(ValueError, match="gap"):
    #     validate_groups_coverage(groups, total_pages=5)
    pass


# TODO: adicionar mais testes
