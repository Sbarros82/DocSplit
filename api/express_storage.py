"""Storage e helpers do DocSplit Rápido (pay-per-page)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.pdf_splitter.supabase_client import get_supabase

_BUCKET = "signing-docs"


def upload_express_file(storage_path: str, data: bytes, content_type: str = "application/pdf") -> str:
    """Envia arquivo ao storage (prefixo express/)."""
    sb = get_supabase()
    sb.storage.from_(_BUCKET).upload(
        storage_path,
        data,
        {"content-type": content_type, "upsert": "true"},
    )
    return storage_path


def download_express_file(storage_path: str) -> bytes:
    """Baixa arquivo do storage."""
    sb = get_supabase()
    return sb.storage.from_(_BUCKET).download(storage_path)


def save_express_file_to_temp(storage_path: str, suffix: str = ".pdf") -> Path:
    """Baixa do storage para arquivo temporário."""
    data = download_express_file(storage_path)
    tmp = Path(tempfile.gettempdir()) / f"docsplit_express_{storage_path.replace('/', '_')}{suffix}"
    tmp.write_bytes(data)
    return tmp
