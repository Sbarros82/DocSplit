"""
Módulo de OCR (Reconhecimento Óptico de Caracteres).

Responsabilidade:
- Executar OCR em páginas que não têm texto nativo confiável
- Preencher o campo ocr_text do objeto Page
- Usar Tesseract configurado para português

Entrada: Page com image_path preenchido
Saída: mesma Page com ocr_text preenchido

Só roda OCR se native_text for None ou muito curto (< N caracteres configurável).
"""

import os
import shutil
from pathlib import Path
from .schemas import Page
from .config import settings

# Dependências opcionais: o sistema degrada graciosamente sem OCR
# (ex: em ambientes serverless como a Vercel, onde o binário Tesseract
# não está disponível — nesse caso apenas o texto nativo do PDF é usado).
try:
    import pytesseract
    from PIL import Image
    _PYTESSERACT_INSTALLED = True
except ImportError:
    _PYTESSERACT_INSTALLED = False

_ocr_available: bool | None = None

# Caminhos comuns de instalação do Tesseract no Windows
# (usados quando o binário não está no PATH da sessão)
_WINDOWS_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(os.environ.get("LOCALAPPDATA", "C:")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
]


def _configure_tesseract_cmd() -> None:
    """Aponta o pytesseract para o binário Tesseract, mesmo fora do PATH."""
    if shutil.which("tesseract"):
        return  # já está no PATH
    for candidate in _WINDOWS_TESSERACT_PATHS:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def _configure_tessdata() -> None:
    """
    Configura TESSDATA_PREFIX quando os dados do idioma configurado
    existem em um diretório alternativo (ex: instalação do Tesseract
    sem o pacote de português).
    
    Ordem de busca:
    1. Variável de ambiente PDF_SPLITTER_TESSDATA
    2. %LOCALAPPDATA%/pdf_splitter/tessdata
    3. Nada (usa o tessdata padrão da instalação)
    """
    if os.environ.get("TESSDATA_PREFIX"):
        return  # já configurado pelo usuário
    
    lang_file = f"{settings.ocr_language}.traineddata"
    
    custom = os.environ.get("PDF_SPLITTER_TESSDATA")
    if custom and (Path(custom) / lang_file).exists():
        os.environ["TESSDATA_PREFIX"] = str(custom)
        return
    
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "pdf_splitter" / "tessdata"
    if (local / lang_file).exists():
        os.environ["TESSDATA_PREFIX"] = str(local)


def is_ocr_available() -> bool:
    """
    Verifica se o OCR está disponível neste ambiente.
    
    Returns:
        True se o pacote pytesseract E o binário Tesseract estiverem
        instalados e funcionais. O resultado é cacheado.
    """
    global _ocr_available
    if _ocr_available is not None:
        return _ocr_available
    
    if not _PYTESSERACT_INSTALLED:
        _ocr_available = False
        return False
    
    try:
        _configure_tesseract_cmd()
        _configure_tessdata()
        pytesseract.get_tesseract_version()
        _ocr_available = True
    except Exception:
        _ocr_available = False
    
    return _ocr_available


def extract_text_ocr(page: Page, use_preprocessing: bool = None) -> Page:
    """
    Executa OCR em uma página e preenche o campo ocr_text.
    
    Args:
        page: Objeto Page com image_path preenchido
        use_preprocessing: Se True, pré-processa imagem antes do OCR (None usa settings)
        
    Returns:
        Mesma Page com ocr_text preenchido
        
    Comportamento:
    - Só executa OCR se native_text for None ou tiver menos de
      settings.min_native_text_length caracteres
    - Usa Tesseract com idioma configurado em settings.ocr_language
    - Em caso de erro, preenche ocr_text com string vazia e continua
      (não quebra o pipeline)
      
    Observações:
    - Tesseract deve estar instalado no sistema
    - Qualidade do OCR depende da qualidade da imagem
    - Considere rodar preprocess.py antes para melhor resultado
    """
    # Verificar se OCR é necessário
    if page.native_text and len(page.native_text) >= settings.min_native_text_length:
        # Texto nativo já é suficiente, não precisa OCR
        page.ocr_text = None
        return page
    
    if not is_ocr_available():
        # Ambiente sem Tesseract: seguir apenas com texto nativo
        page.ocr_text = ""
        return page
    
    if not page.image_path or not Path(page.image_path).exists():
        # Sem imagem, não pode fazer OCR
        page.ocr_text = ""
        return page
    
    # Decidir se deve usar pré-processamento
    if use_preprocessing is None:
        use_preprocessing = settings.enable_preprocessing
    
    try:
        # Pré-processar imagem se habilitado
        if use_preprocessing:
            from .preprocess import preprocess_image
            processed_image_path = preprocess_image(page.image_path)
            image_to_ocr = Image.open(processed_image_path)
        else:
            image_to_ocr = Image.open(page.image_path)
        
        # Executar OCR com Tesseract
        # OEM 3 = LSTM, PSM 1 = segmentação automática com detecção de orientação
        text = pytesseract.image_to_string(
            image_to_ocr,
            lang=settings.ocr_language,
            config='--oem 3 --psm 6',
        )
        
        page.ocr_text = text.strip()
        
    except Exception as e:
        # Em caso de erro, não quebra o pipeline
        # Página será marcada para revisão manual depois
        page.ocr_text = ""
        print(f"Aviso: Erro ao executar OCR na página {page.page_number}: {e}")
    
    return page


def batch_ocr(pages: list[Page], use_preprocessing: bool = None) -> list[Page]:
    """
    Executa OCR em lote em múltiplas páginas.
    
    Args:
        pages: Lista de objetos Page
        use_preprocessing: Se True, pré-processa imagens antes do OCR (None usa settings)
        
    Returns:
        Lista de Pages com ocr_text preenchido quando necessário
        
    Otimização: processa apenas páginas que realmente precisam de OCR,
    em paralelo (Tesseract roda em processo separado).
    """
    if not is_ocr_available():
        needing = sum(
            1 for p in pages
            if not p.native_text or len(p.native_text) < settings.min_native_text_length
        )
        if needing:
            print(
                f"Aviso: OCR indisponível neste ambiente (Tesseract não encontrado). "
                f"{needing} página(s) sem texto nativo suficiente seguirão para revisão manual."
            )
        return pages

    to_ocr = [
        p for p in pages
        if not p.native_text or len(p.native_text) < settings.min_native_text_length
    ]
    if not to_ocr:
        return pages

    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Sem isso, cada Tesseract usa vários núcleos OpenMP e 4 workers
    # brigam pela CPU — fica mais lento, não mais rápido.
    os.environ.setdefault("OMP_THREAD_LIMIT", "1")

    workers = min(4, os.cpu_count() or 2, len(to_ocr))
    print(f"OCR: {len(to_ocr)} página(s) em paralelo ({workers} workers)")

    def _run(page: Page) -> Page:
        return extract_text_ocr(page, use_preprocessing=use_preprocessing)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_run, page) for page in to_ocr]
        for fut in as_completed(futures):
            fut.result()
            done += 1
            if done == 1 or done % 5 == 0 or done == len(to_ocr):
                print(f"OCR: {done}/{len(to_ocr)} páginas")

    return pages


def get_text(page: Page) -> str:
    """
    Obtém o melhor texto disponível de uma página.
    
    Prioridade: ocr_text > native_text > string vazia
    
    Returns:
        Texto da página (nunca None, pode ser string vazia)
    """
    if page.ocr_text:
        return page.ocr_text
    if page.native_text:
        return page.native_text
    return ""
