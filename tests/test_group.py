"""Testes para o módulo de agrupamento."""

import pytest
from src.pdf_splitter.schemas import ClassificationResult, DocumentGroup
from src.pdf_splitter.group import group_pages, should_group


def test_group_pages_same_type_and_supplier():
    """Testa que páginas consecutivas com mesmo tipo e fornecedor são agrupadas."""
    classifications = [
        ClassificationResult(
            page_number=1,
            doc_type="pix_comprovante",
            supplier="Maria Silva",
            confidence=0.95,
            source="rule",
            matched_pattern="pix",
        ),
        ClassificationResult(
            page_number=2,
            doc_type="pix_comprovante",
            supplier="Maria Silva",
            confidence=0.95,
            source="rule",
            matched_pattern="pix",
        ),
    ]
    
    # TODO: implementar quando módulo estiver pronto
    # groups = group_pages(classifications)
    # assert len(groups) == 1
    # assert groups[0].start_page == 1
    # assert groups[0].end_page == 2
    pass


def test_group_pages_different_types_create_separate_groups():
    """Testa que tipos diferentes criam grupos separados."""
    # TODO: implementar
    pass


# TODO: adicionar mais testes
