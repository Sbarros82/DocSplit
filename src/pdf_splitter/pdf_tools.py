"""Ferramentas utilitárias de PDF usadas pela Central de PDF do DocSplit."""
from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader, PdfWriter
import fitz


def merge_pdfs(paths: list[str | Path], output: str | Path) -> Path:
    if not paths:
        raise ValueError("Informe pelo menos um PDF.")
    writer = PdfWriter()
    for path in paths:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as fh:
        writer.write(fh)
    return dest


def split_pdf(path: str | Path, output_dir: str | Path, ranges: list[tuple[int, int]] | None = None) -> list[Path]:
    reader = PdfReader(str(path))
    total = len(reader.pages)
    if not total:
        raise ValueError("O PDF não contém páginas.")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ranges = ranges or [(i, i) for i in range(1, total + 1)]
    result: list[Path] = []
    for index, (start, end) in enumerate(ranges, 1):
        if start < 1 or end < start or end > total:
            raise ValueError(f"Intervalo inválido: {start}-{end}.")
        writer = PdfWriter()
        for page_no in range(start - 1, end):
            writer.add_page(reader.pages[page_no])
        dest = output / f"pagina_{start:04d}_{end:04d}.pdf"
        with dest.open("wb") as fh:
            writer.write(fh)
        result.append(dest)
    return result


def rotate_pdf(path: str | Path, output: str | Path, degrees: int = 90) -> Path:
    if degrees not in (90, 180, 270):
        raise ValueError("A rotação deve ser 90, 180 ou 270 graus.")
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)
    dest = Path(output)
    with dest.open("wb") as fh:
        writer.write(fh)
    return dest


def delete_pages(path: str | Path, output: str | Path, pages: list[int]) -> Path:
    reader = PdfReader(str(path))
    remove = set(pages)
    if any(p < 1 or p > len(reader.pages) for p in remove):
        raise ValueError("Uma ou mais páginas são inválidas.")
    if len(remove) >= len(reader.pages):
        raise ValueError("Não é possível remover todas as páginas.")
    writer = PdfWriter()
    for number, page in enumerate(reader.pages, 1):
        if number not in remove:
            writer.add_page(page)
    dest = Path(output)
    with dest.open("wb") as fh:
        writer.write(fh)
    return dest


def compress_pdf(path: str | Path, output: str | Path) -> Path:
    """Regrava o PDF com limpeza de objetos; não faz rasterização destrutiva."""
    doc = fitz.open(str(path))
    dest = Path(output)
    try:
        doc.save(str(dest), garbage=4, deflate=True, clean=True)
    finally:
        doc.close()
    return dest


def pdf_info(path: str | Path) -> dict:
    reader = PdfReader(str(path))
    meta = reader.metadata or {}
    return {
        "pages": len(reader.pages),
        "title": meta.title,
        "author": meta.author,
        "subject": meta.subject,
        "creator": meta.creator,
        "producer": meta.producer,
    }
