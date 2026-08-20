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

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware

from api.auth import CurrentUser, get_current_user
from api.credits import (
    check_can_process,
    consume_after_process,
    get_client_ip,
    try_complete_job,
    try_create_job,
    try_fail_job,
)
from api.routes_payment import router as payment_router
from api.routes_pdf_tools import router as pdf_tools_router
from api.routes_pdf_advanced import router as pdf_advanced_router
from api.routes_admin import router as admin_router
from api.routes_blog import router as blog_router
from api.version import get_app_version

APP_VERSION = get_app_version()

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

app = FastAPI(title="DocSplit — Separador Inteligente de Documentos", version=APP_VERSION, docs_url=None if IS_VERCEL else "/api/docs", redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.include_router(payment_router)
app.include_router(pdf_tools_router)
app.include_router(pdf_advanced_router)
app.include_router(admin_router)
app.include_router(blog_router)


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


_JOBS: dict[str, tuple[Path, str]] = {}
_EDIT_SESSIONS: dict[str, Path] = {}
_EDIT_NAMES: dict[str, str] = {}
_EDIT_OWNERS: dict[str, str] = {}


@app.get("/api/download/{job_id}")
@app.get("/download/{job_id}")
def download_zip(job_id: str, user: CurrentUser = Depends(get_current_user)):
    item = _JOBS.get(job_id)
    if not item or not item[0].exists():
        raise HTTPException(404, "Arquivo não encontrado ou expirado. Processe de novo.")
    path, owner_id = item
    if owner_id != user.user_id:
        raise HTTPException(404, "Arquivo não encontrado ou expirado. Processe de novo.")
    return FileResponse(path=str(path), media_type="application/zip", filename=path.name)


@app.get("/api/health")
@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "ocr_available": _ocr_available(),
        "llm_available": _llm_available(),
        "supabase_connected": bool(os.environ.get("SUPABASE_URL")),
        "payments_enabled": bool(os.environ.get("MERCADOPAGO_ACCESS_TOKEN")),
        "max_upload_mb": MAX_UPLOAD_BYTES / (1024 * 1024),
        "max_pages": MAX_PAGES,
        "pdf_tools": [
            "merge",
            "split",
            "rotate",
            "delete-pages",
            "compress",
            "reorder",
            "pdf-to-images",
            "images-to-pdf",
            "watermark",
            "number-pages",
            "metadata",
            "protect",
        ],
    }


def _run_pipeline_sync(contents: bytes, safe_stem: str, user_id: str):
    """Run the OCR pipeline in a separate thread to avoid blocking the event loop."""
    from src.pdf_splitter.pipeline import run_pipeline
    from src.pdf_splitter.index_report import format_page_range, get_readable_doc_type

    work_dir = Path(tempfile.mkdtemp(prefix="pdf_splitter_"))
    try:
        input_pdf = work_dir / f"{safe_stem}.pdf"
        input_pdf.write_bytes(contents)
        output_dir = work_dir / "output"

        exported_files = run_pipeline(input_pdf=input_pdf, output_dir=output_dir, create_zip=True)

        zip_path = output_dir / f"{safe_stem}_separados.zip"
        if not zip_path.exists():
            raise RuntimeError("Falha ao gerar o arquivo ZIP.")

        index_path = output_dir / "index.xlsx"
        if index_path.exists():
            with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_STORED) as zipf:
                if "index.xlsx" not in zipf.namelist():
                    zipf.write(index_path, "index.xlsx")

        job_id = uuid.uuid4().hex
        stored_zip = Path(tempfile.gettempdir()) / f"{safe_stem}_{job_id}.zip"
        shutil.copy2(zip_path, stored_zip)
        _JOBS[job_id] = (stored_zip, user_id)

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
            "download_id": job_id,
            "stored_zip": stored_zip,
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


@app.post("/api/process")
@app.post("/process")
async def process_pdf(
    request: Request,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    import asyncio
    import time

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo PDF válido.")
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "O arquivo enviado está vazio.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Arquivo excede o limite de {MAX_UPLOAD_BYTES/(1024*1024):.0f} MB deste ambiente.")
    file_size_mb = max(round(len(contents) / (1024 * 1024), 2), 0.01)
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

    client_ip = get_client_ip(request)
    billing_mode = check_can_process(user.user_id, file_size_mb, page_count, client_ip)
    db_job_id = try_create_job(
        user_id=user.user_id,
        filename=file.filename,
        file_size_mb=file_size_mb,
        pages_count=page_count,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    safe_stem = Path(file.filename).stem.replace(" ", "_") or "documento"
    started = time.monotonic()

    try:
        result = await asyncio.to_thread(_run_pipeline_sync, contents, safe_stem, user.user_id)
    except (ValueError, FileNotFoundError) as e:
        try_fail_job(db_job_id, str(e))
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        try_fail_job(db_job_id, str(e))
        raise HTTPException(500, str(e)) from e
    except Exception as e:
        try_fail_job(db_job_id, str(e))
        raise

    credits_used = consume_after_process(
        user.user_id,
        file_size_mb,
        billing_mode,
        client_ip=client_ip,
        email=user.email,
    )
    stats = result.get("stats") or {}
    try_complete_job(
        db_job_id,
        documents_count=int(stats.get("total_documents") or 0),
        processing_time_seconds=int(time.monotonic() - started),
        used_ocr=bool(stats.get("ocr_used")),
    )

    if IS_VERCEL:
        import base64
        stored_zip = result.pop("stored_zip")
        result["zip_base64"] = base64.b64encode(stored_zip.read_bytes()).decode("ascii")
    else:
        result.pop("stored_zip", None)

    result["total_pages"] = stats.get("total_pages", page_count)
    result["documents_count"] = stats.get("total_documents", 0)
    result["credits_used"] = credits_used
    result["billing_mode"] = billing_mode
    return result


class EditCorrectionIn(BaseModel):
    page_number:int=Field(...,ge=1); x0:float; y0:float; x1:float; y1:float; text:str=Field(...,min_length=1,max_length=2000); fontsize:float|None=Field(None,gt=4,lt=72)
class ApplyEditsIn(BaseModel): corrections:list[EditCorrectionIn]
class InspectRegionIn(BaseModel): page_number:int=Field(...,ge=1); x0:float; y0:float; x1:float; y1:float

def _edit_pdf_path(session_id: str, user: CurrentUser) -> Path:
    path=_EDIT_SESSIONS.get(session_id)
    if not path or not path.exists(): raise HTTPException(404,"Sessao de edicao expirada. Envie o PDF novamente.")
    owner=_EDIT_OWNERS.get(session_id)
    if owner != user.user_id: raise HTTPException(404,"Sessao de edicao expirada. Envie o PDF novamente.")
    return path

@app.post("/api/edit/session")
async def edit_open(file:UploadFile=File(...), user: CurrentUser = Depends(get_current_user)) -> dict:
    from src.pdf_splitter.edit import page_geometries
    if not file.filename or not file.filename.lower().endswith(".pdf"): raise HTTPException(400,"Envie um arquivo PDF valido.")
    contents=await file.read()
    if not contents: raise HTTPException(400,"O arquivo enviado esta vazio.")
    if len(contents)>MAX_UPLOAD_BYTES: raise HTTPException(413,f"Arquivo excede {MAX_UPLOAD_BYTES/(1024*1024):.0f} MB.")
    try:
        import fitz
        doc=fitz.open(stream=contents,filetype="pdf"); page_count=doc.page_count; doc.close()
    except Exception as e: raise HTTPException(400,f"PDF invalido ou corrompido: {e}") from e
    if page_count==0: raise HTTPException(400,"O PDF nao contem paginas.")
    if page_count>MAX_PAGES: raise HTTPException(413,f"Este PDF tem {page_count} paginas; o limite e {MAX_PAGES}.")
    session_id=uuid.uuid4().hex; safe_stem=Path(file.filename).stem.replace(" ","_") or "documento"; stored=Path(tempfile.gettempdir())/f"docsplit_edit_{session_id}.pdf"; stored.write_bytes(contents); _EDIT_SESSIONS[session_id]=stored; _EDIT_NAMES[session_id]=f"{safe_stem}_corrigido.pdf"; _EDIT_OWNERS[session_id]=user.user_id
    return {"success":True,"session_id":session_id,"filename":file.filename,"page_count":page_count,"pages":page_geometries(stored),"note":"Clique numa linha de texto para troca-la."}

@app.get("/api/edit/session/{session_id}/page/{page_number}")
def edit_preview(session_id:str,page_number:int, user: CurrentUser = Depends(get_current_user)):
    from src.pdf_splitter.edit import render_page_preview
    try: jpeg=render_page_preview(_edit_pdf_path(session_id, user),page_number)
    except ValueError as e: raise HTTPException(400,str(e)) from e
    return Response(content=jpeg,media_type="image/jpeg")

@app.post("/api/edit/session/{session_id}/inspect")
def edit_inspect(session_id:str,body:InspectRegionIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    from src.pdf_splitter.edit import inspect_region
    try: hit=inspect_region(_edit_pdf_path(session_id, user),body.page_number,body.x0,body.y0,body.x1,body.y1)
    except ValueError as e: raise HTTPException(400,str(e)) from e
    return {"success":True,**hit}

@app.post("/api/edit/session/{session_id}/apply")
def edit_apply(session_id:str,body:ApplyEditsIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    from src.pdf_splitter.edit import OverlayCorrection,apply_overlays
    path=_edit_pdf_path(session_id, user); corrections=[OverlayCorrection(**item.model_dump()) for item in body.corrections]
    try: apply_overlays(path,corrections)
    except ValueError as e: raise HTTPException(400,str(e)) from e
    return {"success":True,"applied":len(corrections)}

@app.get("/api/edit/session/{session_id}/download")
def edit_download(session_id:str, user: CurrentUser = Depends(get_current_user)):
    path=_edit_pdf_path(session_id, user); return FileResponse(path=str(path),media_type="application/pdf",filename=_EDIT_NAMES.get(session_id,"documento_corrigido.pdf"))

if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    public_dir=ROOT_DIR/"public"
    if public_dir.exists(): app.mount("/",StaticFiles(directory=str(public_dir),html=True),name="frontend")
if __name__=="__main__":
    import uvicorn
    uvicorn.run("api.index:app",host="0.0.0.0",port=8000,reload=True)
