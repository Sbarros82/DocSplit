"""
API web do Separador Inteligente de Documentos.

- Local: `python api/index.py` ou `run_local.ps1`
- Vercel: exporta o ASGI `app` (sem Mangum — o runtime Python da Vercel
  fala ASGI nativo; um `handler` Mangum faz a função crashar).
"""

from __future__ import annotations

import base64
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

IS_VERCEL = bool(os.environ.get("VERCEL"))
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 if IS_VERCEL else 100 * 1024 * 1024
MAX_PAGES = 20 if IS_VERCEL else 500

app = FastAPI(
    title="DocSplit — Separador Inteligente de Documentos",
    description="Separa PDFs com múltiplos documentos em arquivos individuais organizados.",
    version="0.3.1",
    docs_url=None if IS_VERCEL else "/api/docs",
    redoc_url=None,
)

app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ocr_available() -> bool:
    """OCR é opcional: na Vercel o Tesseract não existe."""
    try:
        from src.pdf_splitter.ocr import is_ocr_available

        return is_ocr_available()
    except Exception:
        return False


@app.get("/api/health")
@app.get("/health")
def health() -> dict:
    """Status do serviço. Não importa o pipeline pesado — precisa responder sempre."""
    return {
        "status": "ok",
        "version": "0.3.1",
        "environment": "vercel" if IS_VERCEL else "local",
        "ocr_available": _ocr_available(),
        "max_upload_mb": MAX_UPLOAD_BYTES / (1024 * 1024),
        "max_pages": MAX_PAGES,
    }


@app.post("/api/process")
@app.post("/process")
async def process_pdf(file: UploadFile = File(...)) -> dict:
    """Recebe um PDF, executa o pipeline e devolve ZIP em base64 + índice JSON."""
    from src.pdf_splitter.pipeline import run_pipeline
    from src.pdf_splitter.index_report import format_page_range, get_readable_doc_type

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
        import fitz

        doc = fitz.open(stream=contents, filetype="pdf")
        try:
            page_count = doc.page_count
        finally:
            doc.close()
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

        return {
            "success": True,
            "documents": documents,
            "stats": {
                "total_documents": len(documents),
                "total_pages": sum(d["page_count"] for d in documents),
                "needs_review": sum(1 for d in documents if d["needs_review"]),
                "ocr_used": _ocr_available(),
            },
            "zip_filename": f"{safe_stem}_separados.zip",
            "zip_base64": base64.b64encode(zip_bytes).decode("ascii"),
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles

    public_dir = ROOT_DIR / "public"
    if public_dir.exists():
        app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=True)
