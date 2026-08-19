"""
API web do Separador Inteligente de Documentos.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.routes_payment import router as payment_router
from api.routes_pdf_tools import router as pdf_tools_router

IS_VERCEL = bool(os.environ.get("VERCEL"))
IS_RAILWAY = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID"))
IS_FLYIO = bool(os.environ.get("FLY_APP_NAME"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "").lower()

if not ENVIRONMENT:
    if IS_VERCEL:
        MAX_UPLOAD_BYTES, MAX_PAGES, ENVIRONMENT = 4 * 1024 * 1024, 20, "vercel"
    elif IS_RAILWAY:
        MAX_UPLOAD_BYTES, MAX_PAGES, ENVIRONMENT = 50 * 1024 * 1024, 200, "railway"
    elif IS_FLYIO:
        MAX_UPLOAD_BYTES, MAX_PAGES, ENVIRONMENT = 100 * 1024 * 1024, 500, "production"
    else:
        MAX_UPLOAD_BYTES, MAX_PAGES, ENVIRONMENT = 100 * 1024 * 1024, 500, "local"
else:
    MAX_UPLOAD_BYTES, MAX_PAGES = 100 * 1024 * 1024, 500

app = FastAPI(title="DocSplit — Separador Inteligente de Documentos", version="0.5.0", docs_url=None if IS_VERCEL else "/api/docs", redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(payment_router)
app.include_router(pdf_tools_router)


def _ocr_available() -> bool:
    try:
        from src.pdf_splitter.ocr import is_ocr_available
        return is_ocr_available()
    except Exception:
        return False


def _llm_available() -> bool:
    try:
        from src.pdf_splitter.llm_classify import is_configured
        return is_configured()
    except Exception:
        return False


_JOBS: dict[str, Path] = {}
_EDIT_SESSIONS: dict[str, Path] = {}
_EDIT_NAMES: dict[str, str] = {}


@app.get("/api/download/{job_id}")
@app.get("/download/{job_id}")
def download_zip(job_id: str):
    path = _JOBS.get(job_id)
    if not path or not path.exists():
        raise HTTPException(404, "Arquivo não encontrado ou expirado. Processe de novo.")
    return FileResponse(path=str(path), media_type="application/zip", filename=path.name)


@app.get("/api/health")
@app.get("/health")
def health() -> dict:
    return {
        "status": "ok", "version": "0.5.0", "environment": ENVIRONMENT,
        "ocr_available": _ocr_available(), "llm_available": _llm_available(),
        "supabase_connected": bool(os.environ.get("SUPABASE_URL")),
        "payments_enabled": bool(os.environ.get("MERCADOPAGO_ACCESS_TOKEN")),
        "max_upload_mb": MAX_UPLOAD_BYTES / (1024 * 1024), "max_pages": MAX_PAGES,
        "pdf_tools": ["merge", "split", "rotate", "delete-pages", "compress"],
    }


@app.post("/api/process")
@app.post("/process")
async def process_pdf(file: UploadFile = File(...)) -> dict:
    from src.pdf_splitter.pipeline import run_pipeline
    from src.pdf_splitter.index_report import format_page_range, get_readable_doc_type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo PDF válido.")
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "O arquivo enviado está vazio.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Arquivo excede o limite de {MAX_UPLOAD_BYTES / (1024 * 1024):.0f} MB deste ambiente.")
    try:
        import fitz
        doc = fitz.open(stream=contents, filetype="pdf")
        page_count = doc.page_count
        doc.close()
    except Exception as e:
        raise HTTPException(400, f"PDF inválido ou corrompido: {e}") from e
    if page_count == 0:
        raise HTTPException(400, "O PDF não contém páginas.")
    if page_count > MAX_PAGES:
        raise HTTPException(413, f"Este PDF tem {page_count} páginas; o limite deste ambiente é {MAX_PAGES}.")
    safe_stem = Path(file.filename).stem.replace(" ", "_") or "documento"
    work_dir = Path(tempfile.mkdtemp(prefix="pdf_splitter_"))
    try:
        input_pdf = work_dir / f"{safe_stem}.pdf"
        input_pdf.write_bytes(contents)
        output_dir = work_dir / "output"
        try:
            exported_files = run_pipeline(input_pdf=input_pdf, output_dir=output_dir, create_zip=True)
        except (ValueError, FileNotFoundError) as e:
            raise HTTPException(400, str(e)) from e
        zip_path = output_dir / f"{safe_stem}_separados.zip"
        if not zip_path.exists():
            raise HTTPException(500, "Falha ao gerar o arquivo ZIP.")
        index_path = output_dir / "index.xlsx"
        if index_path.exists():
            with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_STORED) as zipf:
                if "index.xlsx" not in zipf.namelist():
                    zipf.write(index_path, "index.xlsx")
        job_id = uuid.uuid4().hex
        stored_zip = Path(tempfile.gettempdir()) / f"{safe_stem}_{job_id}.zip"
        shutil.copy2(zip_path, stored_zip)
        _JOBS[job_id] = stored_zip
        documents = [{"filename": f.filename, "doc_type": f.doc_type, "doc_type_label": get_readable_doc_type(f.doc_type), "supplier": f.supplier, "pages": format_page_range(f.start_page, f.end_page), "page_count": f.end_page - f.start_page + 1, "needs_review": f.needs_review} for f in exported_files]
        payload = {"success": True, "documents": documents, "stats": {"total_documents": len(documents), "total_pages": sum(d["page_count"] for d in documents), "needs_review": sum(1 for d in documents if d["needs_review"]), "ocr_used": _ocr_available()}, "zip_filename": f"{safe_stem}_separados.zip", "download_id": job_id}
        if IS_VERCEL:
            import base64
            payload["zip_base64"] = base64.b64encode(stored_zip.read_bytes()).decode("ascii")
        return payload
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


class EditCorrectionIn(BaseModel):
    page_number: int = Field(..., ge=1)
    x0: float
    y0: float
    x1: float
    y1: float
    text: str = Field(..., min_length=1, max_length=2000)
    fontsize: float | None = Field(None, gt=4, lt=72)

class ApplyEditsIn(BaseModel):
    corrections: list[EditCorrectionIn]

class InspectRegionIn(BaseModel):
    page_number: int = Field(..., ge=1)
    x0: float
    y0: float
    x1: float
    y1: float


def _edit_pdf_path(session_id: str) -> Path:
    path = _EDIT_SESSIONS.get(session_id)
    if not path or not path.exists():
        raise HTTPException(404, "Sessao de edicao expirada. Envie o PDF novamente.")
    return path


@app.post("/api/edit/session")
async def edit_open(file: UploadFile = File(...)) -> dict:
    from src.pdf_splitter.edit import page_geometries
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo PDF valido.")
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "O arquivo enviado esta vazio.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Arquivo excede {MAX_UPLOAD_BYTES / (1024 * 1024):.0f} MB.")
    try:
        import fitz
        doc = fitz.open(stream=contents, filetype="pdf")
        page_count = doc.page_count
        doc.close()
    except Exception as e:
        raise HTTPException(400, f"PDF invalido ou corrompido: {e}") from e
    if page_count == 0:
        raise HTTPException(400, "O PDF nao contem paginas.")
    if page_count > MAX_PAGES:
        raise HTTPException(413, f"Este PDF tem {page_count} paginas; o limite e {MAX_PAGES}.")
    session_id = uuid.uuid4().hex
    safe_stem = Path(file.filename).stem.replace(" ", "_") or "documento"
    stored = Path(tempfile.gettempdir()) / f"docsplit_edit_{session_id}.pdf"
    stored.write_bytes(contents)
    _EDIT_SESSIONS[session_id] = stored
    _EDIT_NAMES[session_id] = f"{safe_stem}_corrigido.pdf"
    return {"success": True, "session_id": session_id, "filename": file.filename, "page_count": page_count, "pages": page_geometries(stored), "note": "Clique numa linha de texto para troca-la."}

@app.get("/api/edit/session/{session_id}/page/{page_number}")
def edit_preview(session_id: str, page_number: int):
    from src.pdf_splitter.edit import render_page_preview
    try:
        jpeg = render_page_preview(_edit_pdf_path(session_id), page_number)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return Response(content=jpeg, media_type="image/jpeg")

@app.post("/api/edit/session/{session_id}/inspect")
def edit_inspect(session_id: str, body: InspectRegionIn) -> dict:
    from src.pdf_splitter.edit import inspect_region
    try:
        hit = inspect_region(_edit_pdf_path(session_id), body.page_number, body.x0, body.y0, body.x1, body.y1)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"success": True, **hit}

@app.post("/api/edit/session/{session_id}/apply")
def edit_apply(session_id: str, body: ApplyEditsIn) -> dict:
    from src.pdf_splitter.edit import OverlayCorrection, apply_overlays
    path = _edit_pdf_path(session_id)
    corrections = [OverlayCorrection(**item.model_dump()) for item in body.corrections]
    try:
        apply_overlays(path, corrections)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"success": True, "applied": len(corrections)}

@app.get("/api/edit/session/{session_id}/download")
def edit_download(session_id: str):
    path = _edit_pdf_path(session_id)
    return FileResponse(path=str(path), media_type="application/pdf", filename=_EDIT_NAMES.get(session_id, "documento_corrigido.pdf"))

if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    public_dir = ROOT_DIR / "public"
    if public_dir.exists():
        app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
