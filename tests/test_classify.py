"""Testes para o módulo de classificação."""

from src.pdf_splitter.rules import apply_rules, normalize_text, looks_like_spreadsheet


def test_normalize_text_removes_accents():
    assert normalize_text("São José") == "sao jose"
    assert "darf" in normalize_text("DARF - Receita Federal")


def test_apply_rules_detects_pix():
    text = """
    Comprovante de Transferência PIX
    Nome do beneficiário: MARIA DA SILVA
    CPF: 123.456.789-00
    Valor: R$ 1.500,00
    """
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "pix_comprovante"
    assert result.confidence >= 0.9
    assert result.supplier and "MARIA" in result.supplier.upper()


def test_apply_rules_detects_nfe():
    text = "DANFE Documento Auxiliar da Nota Fiscal Eletrônica NF-e Razão Social: PREMIX LTDA"
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "nfe"


def test_apply_rules_viasat_on_bank_receipt():
    text = (
        "Identificacao no extrato PAG TIT BANCO 033 "
        "Nome do beneficiario Viasat Brasil Servicos de Comunicacoes "
        "valor pago R$ 309,00"
    )
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "viasat_fatura"


def test_relacao_bases_not_folha():
    text = "Calculo: Folha Mensal Competencia 07/2025 RELACAO DE BASES DO INSS Codigo Nome do empregado"
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "relacao_bases_inss"


def test_spreadsheet_heuristic():
    noisy = " ".join(["ej", "a", "5", "|"] * 80)
    assert looks_like_spreadsheet(noisy)
    assert not looks_like_spreadsheet("Comprovante de Transferencia PIX nome do favorecido JOAO")
