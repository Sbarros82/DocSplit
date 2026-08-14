"""Testes para o módulo de OCR."""

import pytest
from src.pdf_splitter.schemas import Page
from src.pdf_splitter.ocr import extract_text_ocr, batch_ocr


def test_extract_text_ocr_skips_if_native_text_exists():
    """Testa que OCR não roda se já houver texto nativo suficiente."""
    page = Page(
        page_number=1,
        native_text="Este é um texto nativo com mais de 50 caracteres para não precisar de OCR",
        ocr_text=None,
        image_path="/tmp/test.png",
    )
    
    # TODO: implementar teste quando módulo estiver pronto
    # result = extract_text_ocr(page)
    # assert result.ocr_text is None  # não deve rodar OCR


def test_batch_ocr_processes_multiple_pages():
    """Testa processamento em lote de OCR."""
    # TODO: implementar quando módulo estiver pronto
    pass


# TODO: adicionar mais testes
