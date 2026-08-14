"""
Módulo de exportação de PDFs individuais.

Responsabilidade:
- Ler PDF original
- Para cada DocumentGroup, extrair páginas e gerar arquivo PDF separado
- Salvar arquivos na pasta de saída com nomes gerados por naming.py
- Opcionalmente gerar arquivo ZIP com todos os PDFs
- VALIDAR que soma de páginas == total do PDF original

Entrada: PDF original, list[DocumentGroup], pasta de saída
Saída: list[ExportedFile]
"""

from pathlib import Path
import zipfile
from pypdf import PdfReader, PdfWriter
from .schemas import DocumentGroup, ExportedFile
from . import naming


def export_documents(
    original_pdf_path: str | Path,
    groups: list[DocumentGroup],
    output_dir: str | Path,
    create_zip: bool = True,
) -> list[ExportedFile]:
    """
    Exporta grupos de páginas como PDFs individuais.
    
    Args:
        original_pdf_path: Caminho do PDF original
        groups: Lista de DocumentGroup a exportar
        output_dir: Diretório de saída
        create_zip: Se True, cria arquivo ZIP com todos os PDFs
        
    Returns:
        Lista de ExportedFile com informações dos arquivos gerados
        
    Validações obrigatórias:
    - Soma de páginas de todos os grupos DEVE ser igual ao total do PDF original
    - Não pode haver páginas duplicadas entre grupos
    - Não pode haver gaps (páginas faltando)
    
    Se validação falhar:
    - Levanta ValueError com mensagem clara
    - NÃO gera saída parcial/incompleta
    
    Comportamento:
    - Cria output_dir se não existir
    - Sobrescreve arquivos existentes
    - Gera ZIP opcional com nome baseado no PDF original
    """
    original_pdf_path = Path(original_pdf_path)
    output_dir = Path(output_dir)
    
    # Criar diretório de saída
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Abrir PDF original
    reader = PdfReader(str(original_pdf_path))
    total_pages = len(reader.pages)
    
    # Validar cobertura de grupos
    validate_groups_coverage(groups, total_pages)
    
    # Resetar contadores de naming
    naming.reset_naming_counters()
    
    # Exportar cada grupo
    exported_files = []
    for i, group in enumerate(groups, start=1):
        # Gerar nome de arquivo
        filename = naming.generate_filename(group, i)
        output_path = output_dir / filename
        
        # Extrair páginas e criar PDF
        create_pdf_from_pages(
            reader,
            group.start_page,
            group.end_page,
            output_path,
        )
        
        # Criar registro de arquivo exportado
        exported_file = ExportedFile(
            filename=filename,
            doc_type=group.doc_type,
            supplier=group.supplier,
            start_page=group.start_page,
            end_page=group.end_page,
            output_path=str(output_path),
            needs_review=group.needs_review,
        )
        exported_files.append(exported_file)
        
        print(f"Exportado: {filename} (páginas {group.start_page}-{group.end_page})")
    
    # Criar ZIP se solicitado
    if create_zip:
        zip_path = create_zip_archive(
            exported_files,
            output_dir,
            zip_name=f"{original_pdf_path.stem}_separados.zip",
        )
        print(f"\nZIP criado: {zip_path}")
    
    return exported_files


def validate_groups_coverage(
    groups: list[DocumentGroup],
    total_pages: int,
) -> None:
    """
    Valida que os grupos cobrem todas as páginas sem duplicação/omissão.
    
    Args:
        groups: Lista de DocumentGroup
        total_pages: Total de páginas no PDF original
        
    Raises:
        ValueError: Se houver problema de cobertura
        
    Verificações:
    - Soma de páginas == total_pages
    - Sem overlaps (mesma página em dois grupos)
    - Sem gaps (página faltando)
    """
    if not groups:
        raise ValueError("Nenhum grupo de documentos fornecido")
    
    # Criar conjunto de todas as páginas cobertas
    covered_pages = set()
    
    for group in groups:
        # Validar range do grupo
        if group.start_page > group.end_page:
            raise ValueError(
                f"Grupo inválido: start_page ({group.start_page}) > end_page ({group.end_page})"
            )
        
        # Adicionar páginas do grupo
        for page_num in range(group.start_page, group.end_page + 1):
            if page_num in covered_pages:
                raise ValueError(
                    f"Página {page_num} aparece em mais de um grupo (overlap)"
                )
            covered_pages.add(page_num)
    
    # Verificar se todas as páginas foram cobertas
    expected_pages = set(range(1, total_pages + 1))
    
    if covered_pages != expected_pages:
        missing = expected_pages - covered_pages
        extra = covered_pages - expected_pages
        
        error_parts = []
        if missing:
            error_parts.append(f"Páginas faltando: {sorted(missing)}")
        if extra:
            error_parts.append(f"Páginas extras: {sorted(extra)}")
        
        raise ValueError(
            f"Cobertura de páginas inválida. " + "; ".join(error_parts)
        )
    
    print(f"Validacao OK: {len(covered_pages)} paginas cobertas corretamente")


def create_pdf_from_pages(
    reader: PdfReader,
    start_page: int,
    end_page: int,
    output_path: Path,
) -> None:
    """
    Cria um PDF contendo apenas as páginas especificadas.
    
    Args:
        reader: PdfReader do PDF original
        start_page: Primeira página a incluir (1-indexed)
        end_page: Última página a incluir (1-indexed, inclusive)
        output_path: Caminho do arquivo de saída
    """
    writer = PdfWriter()
    
    # Adicionar páginas (converter de 1-indexed para 0-indexed)
    for page_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_num])
    
    # Salvar PDF
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)


def create_zip_archive(
    exported_files: list[ExportedFile],
    output_dir: Path,
    zip_name: str = "documentos_separados.zip",
) -> Path:
    """
    Cria arquivo ZIP contendo todos os PDFs exportados.
    
    Args:
        exported_files: Lista de arquivos exportados
        output_dir: Diretório base
        zip_name: Nome do arquivo ZIP
        
    Returns:
        Caminho do arquivo ZIP criado
    """
    zip_path = output_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for exported_file in exported_files:
            file_path = Path(exported_file.output_path)
            if file_path.exists():
                # Adicionar ao ZIP com apenas o nome do arquivo (sem caminho completo)
                zipf.write(file_path, file_path.name)
    
    return zip_path
