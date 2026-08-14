"""
Módulo orquestrador do pipeline completo.

Responsabilidade:
- Coordenar execução de todos os estágios em ordem
- Expor função única run_pipeline() para uso em CLI e interface web
- Gerenciar logging e progresso
- Tratar erros de forma centralizada

Pipeline:
1. ingest → extrai páginas + texto nativo
2. preprocess → melhora imagens (opcional)
3. ocr → extrai texto por OCR quando necessário
4. classify → identifica tipo de cada página
5. group → agrupa páginas em documentos
6. export → gera PDFs individuais
7. index_report → gera planilha resumo

Entrada: PDF de entrada, diretório de saída
Saída: list[ExportedFile] + arquivos gerados em disco
"""

from pathlib import Path
import logging
from typing import Callable, Optional
from .schemas import ExportedFile
from .config import settings
from . import (
    ingest,
    ocr,
    classify,
    group,
    export,
    index_report,
)


logger = logging.getLogger(__name__)


def run_pipeline(
    input_pdf: str | Path,
    output_dir: str | Path,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    create_zip: bool = True,
    enable_preprocessing: bool = None,
) -> list[ExportedFile]:
    """
    Executa pipeline completo de separação de documentos.
    
    Args:
        input_pdf: Caminho do PDF de entrada
        output_dir: Diretório de saída para arquivos gerados
        progress_callback: Função opcional para reportar progresso (mensagem, atual, total)
        create_zip: Se True, cria ZIP com todos os PDFs
        enable_preprocessing: Se None, usa configuração de settings
        
    Returns:
        Lista de ExportedFile com informações dos documentos gerados
        
    Arquivos gerados em output_dir:
    - Um PDF por documento identificado
    - index.xlsx (ou index.csv) com resumo
    - documentos_separados.zip (opcional)
    - Subpasta "images/" com páginas renderizadas
    
    Em caso de erro:
    - Levanta exceção com mensagem clara
    - Não gera saída parcial (all-or-nothing)
    
    Observações:
    - Cria output_dir se não existir
    - Reseta contadores de naming entre execuções
    - Valida entrada antes de começar processamento
    """
    input_pdf = Path(input_pdf)
    output_dir = Path(output_dir)
    
    logger.info(f"Iniciando pipeline: {input_pdf} → {output_dir}")
    
    # Etapa 0: Validações
    report_progress("Validando entrada...", 0, 7, progress_callback)
    validate_input(input_pdf)
    setup_output_directory(output_dir)
    
    # Etapa 1: Ingestão
    # Só renderiza imagens se o OCR estiver disponível neste ambiente —
    # sem Tesseract (ex: Vercel) as imagens não seriam usadas.
    ocr_available = ocr.is_ocr_available()
    report_progress("Extraindo páginas do PDF...", 1, 7, progress_callback)
    pages = ingest.ingest_pdf(input_pdf, output_dir, render_images=ocr_available)
    logger.info(f"Ingestão: {len(pages)} páginas extraídas (OCR disponível: {ocr_available})")
    
    # Etapa 2: OCR
    report_progress("Executando OCR nas páginas...", 2, 7, progress_callback)
    if enable_preprocessing is None:
        enable_preprocessing = settings.enable_preprocessing
    pages_with_text = ocr.batch_ocr(pages, use_preprocessing=enable_preprocessing)
    logger.info(f"OCR: {sum(1 for p in pages_with_text if p.ocr_text)} páginas processadas")
    
    # Etapa 3: Classificação
    report_progress("Classificando tipos de documento...", 3, 7, progress_callback)
    classifications = classify.classify_pages(pages_with_text)
    logger.info(f"Classificação: {len(classifications)} páginas classificadas")
    
    # Etapa 4: Agrupamento
    report_progress("Agrupando páginas em documentos...", 4, 7, progress_callback)
    groups = group.group_pages(classifications)
    logger.info(f"Agrupamento: {len(groups)} documentos identificados")
    
    # Etapa 5: Exportação
    report_progress("Gerando PDFs separados...", 5, 7, progress_callback)
    exported_files = export.export_documents(
        input_pdf,
        groups,
        output_dir,
        create_zip=create_zip,
    )
    logger.info(f"Exportação: {len(exported_files)} arquivos gerados")
    
    # Etapa 6: Índice
    report_progress("Gerando relatório índice...", 6, 7, progress_callback)
    index_path = output_dir / "index.xlsx"
    index_report.generate_index_report(exported_files, index_path, format="xlsx")
    logger.info(f"Índice: {index_path}")
    
    # Finalizado
    report_progress("Pipeline concluído!", 7, 7, progress_callback)
    logger.info(f"Pipeline concluído com sucesso: {len(exported_files)} documentos")
    
    return exported_files


def validate_input(pdf_path: Path) -> None:
    """
    Valida arquivo de entrada antes de processar.
    
    Verificações:
    - Arquivo existe
    - É um PDF válido
    - Tem ao menos uma página
    - Não está corrompido
    
    Raises:
        FileNotFoundError: Se arquivo não existir
        ValueError: Se arquivo inválido
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Caminho não é um arquivo: {pdf_path}")
    
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"Arquivo não é PDF: {pdf_path}")
    
    # Tentar abrir para verificar se está corrompido
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        if len(reader.pages) == 0:
            raise ValueError(f"PDF não contém páginas: {pdf_path}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"PDF inválido ou corrompido: {pdf_path} ({e})")
    
    logger.info(f"✓ PDF válido: {len(reader.pages)} páginas")


def setup_output_directory(output_dir: Path) -> None:
    """
    Prepara diretório de saída.
    
    - Cria diretório se não existir
    - A subpasta "images/" é criada sob demanda pelo ingest.py
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Diretório de saída: {output_dir}")


def report_progress(
    message: str,
    current: int,
    total: int,
    callback: Optional[Callable[[str, int, int], None]],
) -> None:
    """
    Reporta progresso via callback e logger.
    
    Args:
        message: Mensagem descritiva da etapa atual
        current: Progresso atual
        total: Total de itens
        callback: Função de callback opcional
    """
    logger.info(f"[{current}/{total}] {message}")
    if callback:
        callback(message, current, total)
