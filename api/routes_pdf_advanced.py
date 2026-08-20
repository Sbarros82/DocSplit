from __future__ import annotations

import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from api.auth import CurrentUser, get_current_user
from api.credits import ToolQuota
from src.pdf_splitter.pdf_tools import (
    add_watermark,
    images_to_pdf,
    number_pages,
    pdf_to_images,
    protect_pdf,
    reorder_pdf,
    set_metadata,
)

router = APIRouter(prefix="/api/pdf", tags=["PDF Advanced"])

_JOBS: dict[str, tuple[Path, str, str, str]] = {}


def _tmp(suffix: str = ".pdf") -> Path:
    return Path(tempfile.gettempdir()) / f"docsplit_{uuid.uuid4().hex}{suffix}"


async def _save(file: UploadFile, images: bool = False) -> Path:
    """Save uploaded file to temp location after validating extension."""
    allowed = (".jpg", ".jpeg", ".png", ".webp") if images else (".pdf",)
    if not file.filename or not file.filename.lower().endswith(allowed):
        raise HTTPException(400, "Tipo de arquivo não permitido.")
    p = _tmp(Path(file.filename).suffix.lower())
    with p.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return p


def _store(p: Path, name: str, user_id: str, media: str = "application/pdf") -> dict:
    """Store processed file and return download info."""
    job_id = uuid.uuid4().hex
    stored = _tmp(p.suffix or ".bin")
    shutil.copy2(p, stored)
    _JOBS[job_id] = (stored, name, media, user_id)
    return {
        "success": True,
        "download_id": job_id,
        "download_url": f"/api/pdf/advanced-download/{job_id}",
        "filename": name,
    }


@router.get("/advanced-download/{job_id}")
def download(job_id: str, user: CurrentUser = Depends(get_current_user)):
    """Download a previously processed file by job ID."""
    item = _JOBS.get(job_id)
    if not item or not item[0].exists():
        raise HTTPException(404, "Arquivo não encontrado ou expirado.")
    path, name, media, owner_id = item
    if owner_id != user.user_id:
        raise HTTPException(404, "Arquivo não encontrado ou expirado.")
    return FileResponse(path, media_type=media, filename=name)


@router.post("/reorder")
async def reorder(
    request: Request,
    file: UploadFile = File(...),
    order: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Reorder PDF pages. Order is a comma-separated list of page numbers."""
    quota = ToolQuota(user)
    p = await _save(file)
    try:
        out = _tmp()
        page_order = [int(x.strip()) for x in order.split(",") if x.strip()]
        reorder_pdf(p, out, page_order)
        result = _store(out, "pdf_reordenado.pdf", user.user_id)
        quota.consume()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        p.unlink(missing_ok=True)


@router.post("/pdf-to-images")
async def pdf_to_images_api(
    request: Request,
    file: UploadFile = File(...),
    dpi: int = Form(150),
    user: CurrentUser = Depends(get_current_user),
):
    """Convert PDF pages to images, returned as a ZIP archive."""
    quota = ToolQuota(user)
    p = await _save(file)
    img_dir = Path(tempfile.mkdtemp(prefix="docsplit_img_"))
    try:
        files = pdf_to_images(p, img_dir, dpi)
        z = _tmp(".zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in files:
                zf.write(item, item.name)
        result = _store(z, "pdf_imagens.zip", user.user_id, "application/zip")
        quota.consume()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        p.unlink(missing_ok=True)
        shutil.rmtree(img_dir, ignore_errors=True)


@router.post("/images-to-pdf")
async def images_to_pdf_api(
    request: Request,
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Convert multiple images into a single PDF."""
    quota = ToolQuota(user)
    paths = [await _save(f, True) for f in files]
    try:
        out = _tmp()
        images_to_pdf(paths, out)
        result = _store(out, "imagens.pdf", user.user_id)
        quota.consume()
        return result
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


@router.post("/watermark")
async def watermark(
    request: Request,
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.25),
    user: CurrentUser = Depends(get_current_user),
):
    """Add a text watermark to all pages of a PDF."""
    quota = ToolQuota(user)
    p = await _save(file)
    try:
        out = _tmp()
        add_watermark(p, out, text, opacity)
        result = _store(out, "pdf_marca_dagua.pdf", user.user_id)
        quota.consume()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        p.unlink(missing_ok=True)


@router.post("/number-pages")
async def number(
    request: Request,
    file: UploadFile = File(...),
    position: str = Form("bottom-right"),
    user: CurrentUser = Depends(get_current_user),
):
    """Add page numbers to a PDF at the specified position."""
    quota = ToolQuota(user)
    p = await _save(file)
    try:
        out = _tmp()
        number_pages(p, out, position)
        result = _store(out, "pdf_numerado.pdf", user.user_id)
        quota.consume()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        p.unlink(missing_ok=True)


@router.post("/metadata")
async def metadata(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
    subject: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
):
    """Set PDF metadata (title, author, subject)."""
    quota = ToolQuota(user)
    p = await _save(file)
    try:
        out = _tmp()
        set_metadata(p, out, title, author, subject)
        result = _store(out, "pdf_metadados.pdf", user.user_id)
        quota.consume()
        return result
    finally:
        p.unlink(missing_ok=True)


@router.post("/protect")
async def protect(
    request: Request,
    file: UploadFile = File(...),
    password: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Protect a PDF with a password."""
    quota = ToolQuota(user)
    p = await _save(file)
    try:
        out = _tmp()
        protect_pdf(p, out, password)
        result = _store(out, "pdf_protegido.pdf", user.user_id)
        quota.consume()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        p.unlink(missing_ok=True)
