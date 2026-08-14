"""
Módulo de geração de relatório/índice.

Responsabilidade:
- Gerar planilha CSV/XLSX com índice de todos os documentos exportados
- Incluir informações úteis: nome arquivo, tipo, fornecedor, páginas, revisão manual
- Facilitar auditoria e localização de documentos

Entrada: list[ExportedFile]
Saída: arquivo CSV ou XLSX
"""

from pathlib import Path
import pandas as pd
from .schemas import ExportedFile


def generate_index_report(
    exported_files: list[ExportedFile],
    output_path: str | Path = None,
    format: str = "xlsx",
) -> Path:
    """
    Gera relatório/índice dos documentos exportados.
    
    Args:
        exported_files: Lista de ExportedFile
        output_path: Caminho do arquivo de saída (None para auto-gerar)
        format: Formato do relatório ("csv" ou "xlsx")
        
    Returns:
        Caminho do arquivo gerado
        
    Colunas do relatório:
    - Número: ordem sequencial
    - Arquivo: nome do arquivo PDF gerado
    - Tipo de Documento: tipo legível do documento
    - Fornecedor/Beneficiário: nome identificado (ou "N/A")
    - Páginas Originais: range de páginas do PDF original (ex: "8-9")
    - Total de Páginas: número de páginas do documento
    - Precisa Revisão: "Sim" ou "Não"
    
    Observações:
    - Formato XLSX é mais amigável para usuário final
    - CSV é útil para processamento automatizado
    """
    if output_path is None:
        output_path = Path("index." + format)
    else:
        output_path = Path(output_path)
    
    # Preparar dados
    data = []
    for i, file in enumerate(exported_files, start=1):
        data.append({
            'Número': i,
            'Arquivo': file.filename,
            'Tipo de Documento': get_readable_doc_type(file.doc_type),
            'Fornecedor/Beneficiário': file.supplier or "N/A",
            'Páginas Originais': format_page_range(file.start_page, file.end_page),
            'Total de Páginas': file.end_page - file.start_page + 1,
            'Precisa Revisão': "Sim" if file.needs_review else "Não",
        })
    
    # Criar DataFrame
    df = pd.DataFrame(data)
    
    # Salvar em formato apropriado
    if format.lower() == 'xlsx':
        df.to_excel(output_path, index=False, engine='openpyxl')
    elif format.lower() == 'csv':
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    else:
        raise ValueError(f"Formato não suportado: {format}. Use 'xlsx' ou 'csv'")
    
    print(f"\nÍndice gerado: {output_path}")
    return output_path


def format_page_range(start_page: int, end_page: int) -> str:
    """
    Formata range de páginas para exibição.
    
    Exemplos:
    - (5, 5) → "5"
    - (8, 10) → "8-10"
    """
    if start_page == end_page:
        return str(start_page)
    return f"{start_page}-{end_page}"


def get_readable_doc_type(doc_type: str) -> str:
    """
    Converte doc_type interno para nome legível.
    
    Exemplos:
    - "pix_comprovante" → "Comprovante PIX"
    - "viasat_fatura" → "Fatura Viasat"
    - "nfe" → "Nota Fiscal Eletrônica (NF-e)"
    """
    # Mapeamento de tipos conhecidos
    mappings = {
        'pix_comprovante': 'Comprovante PIX',
        'pix_qrcode_comprovante': 'Comprovante PIX (QR Code)',
        'boleto_outros_bancos': 'Boleto (Outros Bancos)',
        'darf': 'DARF (Receita Federal)',
        'fgts_guia': 'Guia FGTS',
        'folha_pagamento': 'Folha de Pagamento',
        'nfe': 'Nota Fiscal Eletrônica (NF-e)',
        'conta_energia': 'Conta de Energia',
        'viasat_fatura': 'Fatura Viasat',
        'imposto_municipal': 'Imposto Municipal',
        'ipva': 'IPVA',
        'planilha_movimento_caixa': 'Planilha - Movimento de Caixa',
        'desconhecido': 'Documento Não Classificado',
    }
    
    # Tentar mapeamento direto
    if doc_type in mappings:
        return mappings[doc_type]
    
    # Fallback: capitalizar e substituir underscores
    return doc_type.replace('_', ' ').title()
