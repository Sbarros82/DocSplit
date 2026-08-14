"""
Teste de OCR com PDF escaneado.

Cria um PDF cujas páginas são apenas imagens (simulando um scan,
sem texto nativo) e verifica que o OCR extrai o texto e o pipeline
classifica corretamente.
"""

import tempfile
from pathlib import Path

import fitz

from src.pdf_splitter.ocr import is_ocr_available
from src.pdf_splitter.pipeline import run_pipeline


def build_scanned_pdf(path: Path) -> None:
    """Gera um PDF de 2 páginas contendo apenas imagens de texto."""
    contents = [
        "Comprovante de Transferencia\nPIX por chave\nNome do beneficiario: JOSE PEREIRA\nValor: R$ 750,00",
        "DARF\nDocumento de Arrecadacao\nReceita Federal\nValor: R$ 1.200,00",
    ]
    
    final = fitz.open()
    for content in contents:
        # Renderizar página de texto como imagem
        tmp = fitz.open()
        page = tmp.new_page()
        page.insert_text((72, 100), content, fontsize=16)
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        tmp.close()
        
        # Inserir a imagem em uma página nova (sem camada de texto)
        out_page = final.new_page()
        out_page.insert_image(out_page.rect, stream=img_bytes)
    
    final.save(str(path))
    final.close()


def main() -> None:
    print(f"OCR disponivel: {is_ocr_available()}")
    assert is_ocr_available(), "Tesseract nao foi detectado!"
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pdf_path = tmp_path / "scan_teste.pdf"
        build_scanned_pdf(pdf_path)
        
        exported = run_pipeline(pdf_path, tmp_path / "out", create_zip=False)
        
        print("\nResultado:")
        for f in exported:
            review = " [REVISAR]" if f.needs_review else ""
            print(f"  - {f.filename} | {f.doc_type} | {f.supplier or 'sem fornecedor'}{review}")
        
        doc_types = {f.doc_type for f in exported}
        assert "pix_comprovante" in doc_types, f"PIX nao reconhecido via OCR: {doc_types}"
        assert "darf" in doc_types, f"DARF nao reconhecido via OCR: {doc_types}"
    
    print("\n[OK] OCR funcionando: paginas escaneadas classificadas corretamente!")


if __name__ == "__main__":
    main()
