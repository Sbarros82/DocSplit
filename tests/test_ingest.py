"""Testes para o módulo de ingestão."""

import pytest
from pathlib import Path
from src.pdf_splitter.ingest import ingest_pdf


def test_ingest_pdf_returns_pages(sample_pdf: Path, temp_output_dir: Path):
    """Testa que ingest_pdf retorna lista de Pages."""
    pages = ingest_pdf(sample_pdf, temp_output_dir)
    
    assert isinstance(pages, list)
    assert len(pages) > 0
    
    # Verificar estrutura de cada Page
    for page in pages:
        assert page.page_number >= 1
        # Imagem só é gerada quando a página precisa de OCR
        if page.image_path:
            assert Path(page.image_path).exists()


def test_ingest_pdf_file_not_found():
    """Testa erro ao tentar abrir PDF inexistente."""
    with pytest.raises(FileNotFoundError):
        ingest_pdf("arquivo_que_nao_existe.pdf", "/tmp")


# TODO: adicionar mais testes quando módulo for implementado
