"""
Configuração compartilhada para testes pytest.

Define fixtures comuns usadas em múltiplos testes.
"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Retorna o diretório de fixtures de teste."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf(fixtures_dir: Path) -> Path:
    """Retorna caminho do PDF de exemplo para testes."""
    # TODO: adicionar PDF de exemplo anonimizado em tests/fixtures/
    pdf_path = fixtures_dir / "sample_documents.pdf"
    if not pdf_path.exists():
        pytest.skip(f"PDF de exemplo não encontrado: {pdf_path}")
    return pdf_path


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Cria diretório temporário para saída de testes."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
