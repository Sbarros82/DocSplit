"""
API web do Separador Inteligente de Documentos.

Serve como:
- Função serverless na Vercel (ASGI `app` + handler Mangum)
- Servidor local via `python api/index.py` ou o script `run_local.ps1`

Endpoints (registrados com e sem prefixo /api, para funcionar
tanto no uvicorn local quanto no rewrite da Vercel):
- GET  /api/health   → status do serviço e capacidades do ambiente
- POST /api/process  → recebe um PDF, executa o pipeline e devolve
                       os documentos separados (ZIP em base64 + índice JSON)
"""

from __future__ import annotations

import base64
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

# Garantir que o pacote src/ seja importável (raiz do repositório)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pdf_splitter.pipeline import run_pipeline
from src.pdf_splitter.index_report import format_page_range, get_readable_doc_type
from src.pdf_splitter.ocr import is_ocr_available

IS_VERCEL = bool(os.environ.get("VERCEL"))

# Limite de upload: a Vercel limita o corpo da resposta (~4.5 MB no plano Hobby);
# localmente aceitamos arquivos bem maiores.
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 if IS_VERCEL else 100 * 1024 * 1024
MAX_PAGES = 20 if IS_VERCEL else 500

app = FastAPI(
    title="DocSplit — Separador Inteligente de Documentos",
    description="Separa PDFs com múltiplos documentos em arquivos individuais organizados.",
    version="0.3.0",
    docs_url="/api/docs" if not IS_VERCEL else None,
    redoc_url=None,
)

app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


def _count_pdf_pages(pdf_bytes: bytes) -> int:
    """Conta páginas de um PDF em memória sem gravar em disco."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


@router.get("/health")
def health() -> dict:
    """Status do serviço e capacidades do ambiente atual."""
    return {
        "status": "ok",
        "version": "0.3.0",
        "environment": "vercel" if IS_VERCEL else "local",
        "ocr_available": is_ocr_available(),
        "max_upload_mb": MAX_UPLOAD_BYTES / (1024 * 1024),
        "max_pages": MAX_PAGES,
    }


@router.post("/process")
async def process_pdf(file: UploadFile = File(...)) -> dict:
    """
    Processa um PDF: separa em documentos individuais.

    Retorna JSON com:
    - documents: lista de documentos identificados
    - stats: totais do processamento
    - zip_base64: arquivo ZIP com os PDFs separados + índice Excel
    - zip_filename: nome sugerido para o download
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF válido.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")
    if len(contents) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"Arquivo excede o limite de {limit_mb:.0f} MB deste ambiente. "
                "Localmente o limite é 100 MB; na Vercel (Hobby) o teto é ~4 MB."
            ),
        )

    try:
        page_count = _count_pdf_pages(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF inválido ou corrompido: {e}") from e

    if page_count == 0:
        raise HTTPException(status_code=400, detail="O PDF não contém páginas.")
    if page_count > MAX_PAGES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Este PDF tem {page_count} páginas; o limite deste ambiente é {MAX_PAGES}. "
                "Para lotes maiores, rode localmente (`run_local.ps1`)."
            ),
        )

    safe_stem = Path(file.filename).stem.replace(" ", "_") or "documento"
    work_dir = Path(tempfile.mkdtemp(prefix="pdf_splitter_"))
    try:
        input_pdf = work_dir / f"{safe_stem}.pdf"
        input_pdf.write_bytes(contents)
        output_dir = work_dir / "output"

        try:
            exported_files = run_pipeline(
                input_pdf=input_pdf,
                output_dir=output_dir,
                create_zip=True,
            )
        except (ValueError, FileNotFoundError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        zip_path = output_dir / f"{safe_stem}_separados.zip"
        if not zip_path.exists():
            raise HTTPException(status_code=500, detail="Falha ao gerar o arquivo ZIP.")

        index_path = output_dir / "index.xlsx"
        if index_path.exists():
            with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as zipf:
                if "index.xlsx" not in zipf.namelist():
                    zipf.write(index_path, "index.xlsx")

        zip_bytes = zip_path.read_bytes()

        documents = [
            {
                "filename": f.filename,
                "doc_type": f.doc_type,
                "doc_type_label": get_readable_doc_type(f.doc_type),
                "supplier": f.supplier,
                "pages": format_page_range(f.start_page, f.end_page),
                "page_count": f.end_page - f.start_page + 1,
                "needs_review": f.needs_review,
            }
            for f in exported_files
        ]

        total_pages = sum(d["page_count"] for d in documents)

        return {
            "success": True,
            "documents": documents,
            "stats": {
                "total_documents": len(documents),
                "total_pages": total_pages,
                "needs_review": sum(1 for d in documents if d["needs_review"]),
                "ocr_used": is_ocr_available(),
            },
            "zip_filename": f"{safe_stem}_separados.zip",
            "zip_base64": base64.b64encode(zip_bytes).decode("ascii"),
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


# Prefixo /api (uvicorn local e rewrite da Vercel com path original)
app.include_router(router, prefix="/api")
# Sem prefixo — cobre o caso em que a Vercel entrega o path já reescrito
app.include_router(router, prefix="")


@app.exception_handler(Exception)
async def unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
    """Evita stack trace cru no cliente; detalhe vai para os logs."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno ao processar o documento. Tente novamente."},
    )


# Localmente o FastAPI também serve o frontend estático da pasta public/.
# Na Vercel a plataforma serve public/ e apenas /api/* chega aqui.
if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles

    public_dir = ROOT_DIR / "public"
    if public_dir.exists():
        app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="frontend")


# Handler ASGI para runtimes que esperam Mangum (além do `app` nativo da Vercel)
try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=True)
