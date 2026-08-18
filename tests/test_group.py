"""Testes para o módulo de agrupamento — espelha o lote de 46 páginas / 34 documentos."""

from src.pdf_splitter.schemas import ClassificationResult
from src.pdf_splitter.group import group_pages, should_group
from src.pdf_splitter.rules import apply_rules, detect_continuation, extract_cnpj


def _c(
    page: int,
    doc_type: str,
    supplier: str | None = None,
    confidence: float = 0.95,
    is_continuation: bool = False,
    cnpj: str | None = None,
) -> ClassificationResult:
    return ClassificationResult(
        page_number=page,
        doc_type=doc_type,
        supplier=supplier,
        confidence=confidence,
        source="rule",
        matched_pattern=doc_type,
        is_continuation=is_continuation,
        cnpj=cnpj,
    )


def _ranges(groups) -> list[tuple[int, int, str]]:
    return [(g.start_page, g.end_page, g.doc_type) for g in groups]


def test_group_pages_same_type_and_supplier():
    classifications = [
        _c(1, "pix_comprovante", "Maria Silva"),
        _c(2, "pix_comprovante", "Maria Silva"),
    ]
    groups = group_pages(classifications)
    assert len(groups) == 2
    assert groups[0].start_page == 1
    assert groups[1].start_page == 2


def test_group_pages_different_types_create_separate_groups():
    groups = group_pages([
        _c(1, "pix_comprovante", "A"),
        _c(2, "darf"),
    ])
    assert len(groups) == 2


def test_two_pix_never_merge_even_without_supplier():
    groups = group_pages([
        _c(1, "pix_comprovante"),
        _c(2, "pix_comprovante"),
    ])
    assert _ranges(groups) == [(1, 1, "pix_comprovante"), (2, 2, "pix_comprovante")]


def test_continuation_2_de_2_attaches_unknown_page():
    groups = group_pages([
        _c(1, "boleto_outros_bancos", "Consorcio Honda"),
        _c(2, "desconhecido", confidence=0.0, is_continuation=True),
    ])
    assert len(groups) == 1
    assert groups[0].start_page == 1
    assert groups[0].end_page == 2
    assert groups[0].doc_type == "boleto_outros_bancos"


def test_two_darfs_stay_separate():
    groups = group_pages([
        _c(1, "darf"),
        _c(2, "darf"),
    ])
    assert len(groups) == 2


def test_viasat_comprovante_fatura_nfe_bundle():
    groups = group_pages([
        _c(1, "viasat_fatura", "Viasat", cnpj="14796606000190"),
        _c(2, "viasat_fatura", "Viasat"),
        _c(3, "nfe", "Viasat Brasil"),
        _c(4, "cupom_fiscal", "Mercado Divino"),
    ])
    assert _ranges(groups) == [
        (1, 3, "viasat_fatura"),
        (4, 4, "cupom_fiscal"),
    ]


def test_viasat_does_not_swallow_following_unrelated_nfe():
    groups = group_pages([
        _c(1, "viasat_fatura", "Viasat"),
        _c(2, "nfe", "Viasat"),
        _c(3, "nfe", "Oeste Representacoes"),
    ])
    assert _ranges(groups) == [
        (1, 2, "viasat_fatura"),
        (3, 3, "nfe"),
    ]


def test_premix_comprovante_boleto_nfe_bundle():
    groups = group_pages([
        _c(1, "comprovante_pagamento", "Manufaturacao"),
        _c(2, "recibo_pagador", "Premix"),
        _c(3, "nfe", "Premix"),
        _c(4, "pix_comprovante", "Paulo"),
    ])
    assert _ranges(groups) == [
        (1, 3, "nfe"),
        (4, 4, "pix_comprovante"),
    ]
    # Preferimos o tipo boleto se existir no pacote
    groups_b = group_pages([
        _c(1, "comprovante_pagamento", "Premix"),
        _c(2, "boleto_outros_bancos", "Premix"),
        _c(3, "nfe", "Premix"),
    ])
    assert groups_b[0].doc_type == "boleto_outros_bancos"
    assert groups_b[0].end_page == 3


def test_oeste_comprovante_and_recibo_stay_separate_without_nfe():
    groups = group_pages([
        _c(1, "comprovante_pagamento", "Oeste"),
        _c(2, "recibo_pagador", "Oeste Representacoes"),
        _c(3, "comprovante_pagamento", "Pm Maceio"),
    ])
    assert len(groups) == 3


def test_energy_comprovante_stays_separate_from_danfe():
    groups = group_pages([
        _c(1, "comprovante_pagamento", "Coelba"),
        _c(2, "conta_energia", "Neoenergia"),
        _c(3, "conta_energia", "Neoenergia"),
    ])
    assert _ranges(groups) == [
        (1, 1, "comprovante_pagamento"),
        (2, 3, "conta_energia"),
    ]


def test_duam_two_pages_group():
    groups = group_pages([
        _c(1, "comprovante_pagamento", "Pm Maceio"),
        _c(2, "imposto_municipal", "Maceio"),
        _c(3, "imposto_municipal", "Maceio"),
    ])
    assert _ranges(groups) == [
        (1, 1, "comprovante_pagamento"),
        (2, 3, "imposto_municipal"),
    ]


def test_fgts_guia_and_detalhe_stay_separate():
    groups = group_pages([
        _c(1, "fgts_guia"),
        _c(2, "fgts_detalhe"),
    ])
    assert len(groups) == 2


def test_scan_lote_expected_34_documents():
    """Classificações do lote SCAN0000 alinhadas ao ZIP de referência (34 arquivos)."""
    pages = [
        _c(1, "planilha_movimento_caixa"),
        _c(2, "viasat_fatura", "Viasat"),
        _c(3, "viasat_fatura", "Viasat"),
        _c(4, "viasat_fatura", "Viasat"),
        _c(5, "nfe", "Viasat"),
        _c(6, "cupom_fiscal", "Mercado Divino"),
        _c(7, "pix_comprovante", "Agromaquinas"),
        _c(8, "boleto_outros_bancos", "Honda"),
        _c(9, "desconhecido", is_continuation=True),
        _c(10, "pix_comprovante", "Artur"),
        _c(11, "pix_qrcode_comprovante", "Joao Marcos"),
        _c(12, "pix_comprovante", "Joao Guedes"),
        _c(13, "pix_comprovante", "Geneci"),
        _c(14, "folha_pagamento"),
        _c(15, "pix_comprovante", "Gilvan"),
        _c(16, "nfe", "GP do Nascimento"),
        _c(17, "comprovante_pagamento", "Coelba"),
        _c(18, "conta_energia", "Neoenergia"),
        _c(19, "conta_energia", "Neoenergia"),
        _c(20, "folha_pagamento"),
        _c(21, "boleto_outros_bancos", "Honda"),
        _c(22, "desconhecido", is_continuation=True),
        _c(23, "darf"),
        _c(24, "darf"),
        _c(25, "relacao_bases_inss"),
        _c(26, "pix_qrcode_comprovante", "CEF"),
        _c(27, "fgts_guia"),
        _c(28, "fgts_detalhe"),
        _c(29, "boleto_outros_bancos", "Honda"),
        _c(30, "desconhecido", is_continuation=True),
        _c(31, "comprovante_pagamento", "Oeste"),
        _c(32, "recibo_pagador", "Oeste"),
        _c(33, "comprovante_pagamento", "Pm Maceio"),
        _c(34, "imposto_municipal", "Maceio"),
        _c(35, "imposto_municipal", "Maceio"),
        _c(36, "nfe", "Agromaquinas"),
        _c(37, "comprovante_pagamento", "Sefaz"),
        _c(38, "ipva"),
        _c(39, "comprovante_pagamento", "Premix"),
        _c(40, "recibo_pagador", "Premix"),
        _c(41, "nfe", "Premix"),
        _c(42, "pix_comprovante", "Paulo"),
        _c(43, "viasat_fatura", "Viasat"),
        _c(44, "viasat_fatura", "Viasat"),
        _c(45, "nfe", "Viasat"),
        _c(46, "nfe", "Oeste"),
    ]
    groups = group_pages(pages)
    assert sum(g.end_page - g.start_page + 1 for g in groups) == 46
    assert len(groups) == 34
    assert groups[1].start_page == 2 and groups[1].end_page == 5
    assert groups[30].start_page == 39 and groups[30].end_page == 41


def test_detect_continuation_2de2():
    assert detect_continuation("2de2 Data do pagamento: 05/08/2025")
    assert detect_continuation("Página 2 de 2 autenticacao")
    assert not detect_continuation("1 de 2 comprovante de pagamento outros bancos")
    assert not detect_continuation("Pagamento em 05/08/2025 valor 100")


def test_apply_rules_does_not_call_duam_a_darf():
    text = "PREFEITURA DE MACEIO DOCUMENTO DE ARRECADACAO GUIA DAM TAXA DE FUNCIONAMENTO"
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "imposto_municipal"


def test_apply_rules_ipva_not_darf():
    text = "GOVERNO DO ESTADO DE ALAGOAS IPVA Parcelado DAR / CB DOCUMENTO DE ARRECADACAO"
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "ipva"


def test_apply_rules_pix_favorecido():
    text = "Comprovante de transferencia Pix por chave nome do favorecido JOAO DA SILVA GUEDES"
    result = apply_rules(text, 1)
    assert result is not None
    assert result.doc_type == "pix_comprovante"
    assert result.supplier and "JOAO" in result.supplier.upper()


def test_extract_cnpj():
    assert extract_cnpj("CNPJ 14.796.606/0001-90 Viasat") == "14796606000190"


def test_should_group_continuation():
    prev = _c(1, "boleto_outros_bancos", "Honda")
    curr = _c(2, "desconhecido", is_continuation=True)
    assert should_group(curr, prev) is True
