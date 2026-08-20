"""Versão única do produto DocSplit."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Lê VERSION na raiz do repositório (fallback 0.7.0)."""
    candidates = [
        Path(__file__).resolve().parents[1] / "VERSION",
        Path.cwd() / "VERSION",
    ]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
        except OSError:
            continue
    return "0.7.0"
