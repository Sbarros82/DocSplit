"""API da Central de PDF do DocSplit."""
from __future__ import annotations

import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from api.auth import CurrentUser, get_current_user
from api.credits import ToolQuota, get_client_ip, get_tool_usage
from src.pdf_splitter.pdf_tools import compress_pdf, delete_pages, merge_pdfs, rotate_pdf, split_pdf

router = APIRouter(prefix="/api/pdf", tags=["PDF Tools"])
_JOBS: dict[str, tuple[Path, str, str, str]] = {}


def _tmp(suffix: str = ".pdf") -> Path:
    return Path(tempfile.gettempdir()) / f"docsplit_{uuid.uuid4().hex}{suffix}"


async def _save_upload(file: UploadFile) -> Path:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie apenas arquivos PDF.")
    path = _tmp()
    with path.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    return path


def _store(path: Path, filename: str, user_id: str, media_type: str = "application/pdf") -> str:
    job = uuid.uuid4().hex
    stored = _tmp(path.suffix or ".bin")
    shutil.copy2(path, stored)
    _JOBS[job] = (stored, filename, media_type, user_id)
    return job


@router.get("/usage")
def pdf_tool_usage(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    """Retorna usos restantes das ferramentas PDF no dia."""
    return get_tool_usage(user, get_client_ip(request))


@router.get("/download/{job_id}")
def download(job_id: str, user: CurrentUser = Depends(get_current_user)):
    item = _JOBS.get(job_id)
    if not item or not item[0].exists():
        raise HTTPException(404, "Arquivo nÃ£o encontrado ou expirado.")
    path, filename, media_type, owner_id = item
    if owner_id != user.user_id:
        raise HTTPException(404, "Arquivo nÃ£o encontrado ou expirado.")
    return FileResponse(path, media_type=media_type, filename=filename)


@router.post("/merge")
async def merge(
    request: Request,
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    quota = ToolQuota(user, request)
    if len(files) < 2:
        raise HTTPException(400, "Selecione pelo menos dois PDFs.")
    paths = [await _save_upload(f) for f in files]
    try:
        output = _tmp()
        merge_pdfs(paths, output)
        job_id = _store(output, "pdf_mesclado.pdf", user.user_id)
        quota.consume()
        return {"success": True, "download_id": job_id, "filename": "pdf_mesclado.pdf"}
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


@router.post("/split")
async def split(
    request: Request,
    file: UploadFile = File(...),
    ranges: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
):
    quota = ToolQuota(user, request)
    path = await _save_upload(file)
    output_dir = Path(tempfile.mkdtemp(prefix="docsplit_split_"))
    try:
        parsed = None
        if ranges:
            parsed = []
            for item in ranges.split(","):
                parts = item.strip().split("-")
                start, end = int(parts[0]), int(parts[-1])
                parsed.append((start, end))
        files = split_pdf(path, output_dir, parsed)
        zip_path = _tmp(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in files:
                zf.write(item, item.name)
        job_id = _store(zip_path, "pdf_separado.zip", user.user_id, "application/zip")
        quota.consume()
        return {"success": True, "download_id": job_id, "filename": "pdf_separado.zip"}
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)
        shutil.rmtree(output_dir, ignore_errors=True)


@router.post("/rotate")
async def rotate(
    request: Request,
    file: UploadFile = File(...),
    degrees: int = Form(90),
    user: CurrentUser = Depends(get_current_user),
):
    quota = ToolQuota(user, request)
    path = await _save_upload(file)
    try:
        output = _tmp()
        rotate_pdf(path, output, degrees)
        job_id = _store(output, "pdf_girado.pdf", user.user_id)
        quota.consume()
        return {"success": True, "download_id": job_id, "filename": "pdf_girado.pdf"}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)


@router.post("/delete-pages")
async def remove_pages(
    request: Request,
    file: UploadFile = File(...),
    pages: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
):
    quota = ToolQuota(user, request)
    path = await _save_upload(file)
    try:
        selected = [int(x.strip()) for x in pages.split(",") if x.strip()]
        output = _tmp()
        delete_pages(path, output, selected)
        job_id = _store(output, "pdf_paginas_removidas.pdf", user.user_id)
        quota.consume()
        return {"success": True, "download_id": job_id, "filename": "pdf_paginas_removidas.pdf"}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)


@router.post("/compress")
async def compress(
    request: Request,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    quota = ToolQuota(user, request)
    path = await _save_upload(file)
    try:
        output = _tmp()
        compress_pdf(path, output)
        job_id = _store(output, "pdf_comprimido.pdf", user.user_id)
        quota.consume()
        return {"success": True, "download_id": job_id, "filename": "pdf_comprimido.pdf"}
    finally:
        path.unlink(missing_ok=True)
