"""
Teste de ponta a ponta da API.

Gera um PDF sintético com 5 páginas simulando documentos brasileiros
misturados e o envia ao endpoint /api/process usando o TestClient.
"""

import base64
import io
import zipfile

import fitz
from fastapi.testclient import TestClient

from api.index import app


PAGES = [
    # (conteúdo simulado de cada página)
    "MOVIMENTO DE CAIXA\nEntrada/Saída do mês de julho\nSaldo inicial: R$ 10.000,00",
    "Comprovante de Transferência\nPIX por chave\nNome do beneficiário: MARIA DA SILVA\nValor: R$ 1.500,00",
    "Comprovante de Pagamento Outros Bancos\nBeneficiário: VIVO S.A.\nPágina 1 de 2\nValor: R$ 289,90",
    "Comprovante de Pagamento Outros Bancos\nBeneficiário: VIVO S.A.\nPágina 2 de 2\nAutenticação mecânica",
    "DARF\nDocumento de Arrecadação\nReceita Federal\nCódigo: 0220\nValor: R$ 3.412,55",
]


def build_test_pdf() -> bytes:
    """Cria um PDF em memória com as páginas de teste."""
    doc = fitz.open()
    for content in PAGES:
        page = doc.new_page()
        page.insert_text((72, 100), content, fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def main() -> None:
    client = TestClient(app)

    # Health check
    health = client.get("/api/health").json()
    print(f"Health: {health}")

    # Processar PDF de teste
    pdf_bytes = build_test_pdf()
    resp = client.post(
        "/api/process",
        files={"file": ("comprovantes_teste.pdf", pdf_bytes, "application/pdf")},
    )
    print(f"\nStatus HTTP: {resp.status_code}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    print(f"Estatísticas: {data['stats']}")
    print("\nDocumentos identificados:")
    for doc in data["documents"]:
        review = " [REVISAR]" if doc["needs_review"] else ""
        print(f"  - {doc['filename']} | {doc['doc_type_label']} | "
              f"{doc['supplier'] or 'sem fornecedor'} | págs {doc['pages']}{review}")

    # Verificar conteúdo do ZIP
    zip_bytes = base64.b64decode(data["zip_base64"])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
    print(f"\nConteúdo do ZIP ({len(names)} arquivos):")
    for name in names:
        print(f"  - {name}")

    # Validações
    assert data["stats"]["total_pages"] == len(PAGES), "Páginas perdidas!"
    assert "index.xlsx" in names, "Índice Excel ausente do ZIP!"
    print("\n[OK] Teste de ponta a ponta passou!")


if __name__ == "__main__":
    main()
