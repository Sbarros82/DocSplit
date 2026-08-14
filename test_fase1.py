"""
Script de teste para Fase 1: Ingestão + OCR

Teste rápido antes de ter testes automatizados completos.
"""

from pathlib import Path
from src.pdf_splitter.ingest import ingest_pdf
from src.pdf_splitter.ocr import batch_ocr, get_text


def test_fase1():
    """Testa ingestão e OCR de um PDF."""
    
    print("=" * 60)
    print("TESTE FASE 1 - Ingestão + OCR")
    print("=" * 60)
    
    # Verificar se há PDF de teste
    input_dir = Path("data/input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ Nenhum PDF encontrado em data/input/")
        print("Coloque um PDF de teste em data/input/ e execute novamente.")
        return
    
    test_pdf = pdf_files[0]
    print(f"\n📄 PDF de teste: {test_pdf.name}")
    
    output_dir = Path("data/output") / "test_fase1"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Passo 1: Ingestão
    print("\n[1/2] Executando ingestão...")
    try:
        pages = ingest_pdf(test_pdf, output_dir)
        print(f"✓ {len(pages)} páginas extraídas")
        
        # Mostrar amostra de texto nativo
        native_count = sum(1 for p in pages if p.native_text)
        print(f"  - {native_count} páginas com texto nativo")
        print(f"  - {len(pages) - native_count} páginas sem texto nativo (precisam OCR)")
        
    except Exception as e:
        print(f"❌ Erro na ingestão: {e}")
        return
    
    # Passo 2: OCR
    print("\n[2/2] Executando OCR...")
    try:
        pages_with_ocr = batch_ocr(pages)
        print(f"✓ OCR concluído")
        
        # Estatísticas
        ocr_count = sum(1 for p in pages_with_ocr if p.ocr_text)
        print(f"  - {ocr_count} páginas processadas com OCR")
        
    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return
    
    # Mostrar amostra do texto extraído
    print("\n" + "=" * 60)
    print("AMOSTRA DE TEXTO EXTRAÍDO (primeiras 3 páginas)")
    print("=" * 60)
    
    for page in pages_with_ocr[:3]:
        text = get_text(page)
        source = "OCR" if page.ocr_text else "Nativo"
        
        print(f"\nPágina {page.page_number} (fonte: {source}):")
        print("-" * 60)
        if text:
            # Mostrar primeiras 300 caracteres
            preview = text[:300].replace('\n', ' ')
            if len(text) > 300:
                preview += "..."
            print(preview)
        else:
            print("(sem texto extraído)")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✓ Total de páginas processadas: {len(pages_with_ocr)}")
    print(f"✓ Imagens salvas em: {output_dir / 'images'}")
    print(f"✓ Páginas com texto: {sum(1 for p in pages_with_ocr if get_text(p))}")
    print(f"✓ Páginas vazias: {sum(1 for p in pages_with_ocr if not get_text(p))}")
    
    print("\n✅ FASE 1 COMPLETA!")
    print("\nPróximo passo: Fase 2 - Regras de Classificação")


if __name__ == '__main__':
    test_fase1()
