"""
Módulo de ingestão de PDF.

Responsabilidade:
- Abrir PDF de entrada
- Extrair texto nativo de cada página
- Renderizar páginas como imagem (para OCR), quando solicitado
- Retornar lista de objetos Page com image_path e native_text preenchidos

Entrada: caminho do PDF
Saída: list[Page]

Implementação com PyMuPDF (fitz): não requer Poppler nem outros binários
de sistema, o que permite rodar tanto localmente quanto em ambientes
serverless (ex: Vercel).
"""

from pathlib import Path
import fitz  # PyMuPDF
from .schemas import Page
from .config import settings


def ingest_pdf(
    pdf_path: str | Path,
    output_dir: str | Path,
    render_images: bool = True,
    dpi: int | None = None,
) -> list[Page]:
    """
    Abre um PDF e extrai páginas como imagens + texto nativo.
    
    Args:
        pdf_path: Caminho do arquivo PDF de entrada
        output_dir: Diretório onde salvar as imagens renderizadas
        render_images: Se False, não renderiza imagens (útil quando OCR
            está indisponível — ex: ambiente serverless — e apenas o texto
            nativo será usado). Muito mais rápido.
        dpi: Resolução de renderização das imagens (300 recomendado para OCR)
        
    Returns:
        Lista de objetos Page, um por página do PDF, com:
        - page_number preenchido (1-indexed)
        - native_text preenchido quando o PDF tem texto selecionável
        - image_path preenchido com o caminho da imagem renderizada
          (None se render_images=False)
        - ocr_text ainda None (será preenchido pelo módulo ocr.py)
        
    Raises:
        FileNotFoundError: Se o PDF não existir
        ValueError: Se o arquivo não for PDF ou não tiver páginas
        
    Observações:
    - Documentos escaneados podem estar tortos ou com má qualidade
    - Texto nativo de PDFs escaneados costuma ser vazio (precisa OCR)
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    dpi = dpi if dpi is not None else settings.ocr_dpi
    
    # Validar entrada
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise ValueError(f"Arquivo deve ser PDF: {pdf_path}")
    
    images_dir = output_dir / "images"
    if render_images:
        images_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(str(pdf_path))
    try:
        total_pages = doc.page_count
        
        if total_pages == 0:
            raise ValueError(f"PDF não contém páginas: {pdf_path}")
        
        pages: list[Page] = []
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        min_len = settings.min_native_text_length
        
        for page_index in range(total_pages):
            pdf_page = doc[page_index]
            page_number = page_index + 1
            
            try:
                native_text = (pdf_page.get_text() or "").strip()
            except Exception:
                native_text = ""
            
            # Só renderiza página que realmente precisa de OCR
            image_path: str | None = None
            needs_ocr = (not native_text) or (len(native_text) < min_len)
            if render_images and needs_ocr:
                pixmap = pdf_page.get_pixmap(
                    matrix=matrix,
                    colorspace=fitz.csGRAY,
                    alpha=False,
                )
                image_file = images_dir / f"page_{page_number:04d}.jpg"
                try:
                    pixmap.save(str(image_file), jpg_quality=72)
                except TypeError:
                    pixmap.save(str(image_file))
                image_path = str(image_file)
            
            pages.append(Page(
                page_number=page_number,
                native_text=native_text if native_text else None,
                ocr_text=None,
                image_path=image_path,
            ))
        
        return pages
    finally:
        doc.close()
