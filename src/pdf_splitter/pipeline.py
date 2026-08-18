"""
Módulo orquestrador do pipeline completo.

Responsabilidade:
- Coordenar execução de todos os estágios em ordem
- Expor função única run_pipeline() para uso em CLI e interface web
- Gerenciar logging e progresso
- Tratar erros de forma centralizada
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
    Executa pipeline completo de separacao de documentos.

    Entrada: PDF de entrada, diretorio de saida
    Saida: list[ExportedFile] + arquivos gerados em disco
    """
    input_pdf = Path(input_pdf)
    output_dir = Path(output_dir)

    logger.info("Iniciando pipeline: %s -> %s", input_pdf, output_dir)

    report_progress("Validando entrada...", 0, 7, progress_callback)
    validate_input(input_pdf)
    setup_output_directory(output_dir)

    ocr_available = ocr.is_ocr_available()
    report_progress("Extraindo paginas do PDF...", 1, 7, progress_callback)
    pages = ingest.ingest_pdf(input_pdf, output_dir, render_images=ocr_available)
    logger.info("Ingestao: %s paginas extraidas (OCR disponivel: %s)", len(pages), ocr_available)

    report_progress("Executando OCR nas paginas...", 2, 7, progress_callback)
    if enable_preprocessing is None:
        enable_preprocessing = settings.enable_preprocessing
    pages_with_text = ocr.batch_ocr(pages, use_preprocessing=enable_preprocessing)
    logger.info("OCR: %s paginas processadas", sum(1 for p in pages_with_text if p.ocr_text))

    report_progress("Classificando tipos de documento...", 3, 7, progress_callback)
    classifications = classify.classify_pages(pages_with_text)
    logger.info("Classificacao: %s paginas classificadas", len(classifications))

    report_progress("Agrupando paginas em documentos...", 4, 7, progress_callback)
    groups = group.group_pages(classifications)
    logger.info("Agrupamento: %s documentos identificados", len(groups))

    report_progress("Gerando PDFs separados...", 5, 7, progress_callback)
    exported_files = export.export_documents(
        input_pdf,
        groups,
        output_dir,
        create_zip=create_zip,
    )
    logger.info("Exportacao: %s arquivos gerados", len(exported_files))

    report_progress("Gerando relatorio indice...", 6, 7, progress_callback)
    index_path = output_dir / "index.xlsx"
    index_report.generate_index_report(exported_files, index_path, format="xlsx")
    logger.info("Indice: %s", index_path)

    report_progress("Pipeline concluido!", 7, 7, progress_callback)
    logger.info("Pipeline concluido: %s documentos", len(exported_files))

    return exported_files


def validate_input(pdf_path: Path) -> None:
    """Valida o PDF de entrada. Levanta FileNotFoundError ou ValueError."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf_path}")

    if not pdf_path.is_file():
        raise ValueError(f"Caminho nao e um arquivo: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Arquivo deve ser PDF: {pdf_path}")

    try:
        import fitz

        reader = fitz.open(str(pdf_path))
        try:
            if reader.page_count == 0:
                raise ValueError(f"PDF nao contem paginas: {pdf_path}")
            logger.info("PDF valido: %s paginas", reader.page_count)
        finally:
            reader.close()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("PDF invalido ou corrompido: %s (%s)" % (pdf_path, exc)) from exc


def setup_output_directory(output_dir: Path) -> None:
    """Cria o diretorio de saida se nao existir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Diretorio de saida: %s", output_dir)


def report_progress(
    message: str,
    current: int,
    total: int,
    callback: Optional[Callable[[str, int, int], None]],
) -> None:
    """Reporta progresso via callback e logger."""
    logger.info("[%s/%s] %s", current, total, message)
    if callback:
        callback(message, current, total)
