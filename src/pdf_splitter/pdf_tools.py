"""Ferramentas utilitárias de PDF usadas pela Central de PDF do DocSplit."""
from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader, PdfWriter
import fitz


def merge_pdfs(paths: list[str | Path], output: str | Path) -> Path:
    if not paths: raise ValueError("Informe pelo menos um PDF.")
    writer = PdfWriter()
    for path in paths:
        for page in PdfReader(str(path)).pages: writer.add_page(page)
    dest = Path(output); dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as fh: writer.write(fh)
    return dest


def split_pdf(path: str | Path, output_dir: str | Path, ranges: list[tuple[int, int]] | None = None) -> list[Path]:
    reader = PdfReader(str(path)); total = len(reader.pages)
    if not total: raise ValueError("O PDF não contém páginas.")
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    ranges = ranges or [(i, i) for i in range(1, total + 1)]
    result = []
    for start, end in ranges:
        if start < 1 or end < start or end > total: raise ValueError(f"Intervalo inválido: {start}-{end}.")
        writer = PdfWriter()
        for page_no in range(start - 1, end): writer.add_page(reader.pages[page_no])
        dest = output / f"pagina_{start:04d}_{end:04d}.pdf"
        with dest.open("wb") as fh: writer.write(fh)
        result.append(dest)
    return result


def rotate_pdf(path: str | Path, output: str | Path, degrees: int = 90) -> Path:
    if degrees not in (90, 180, 270): raise ValueError("A rotação deve ser 90, 180 ou 270 graus.")
    reader = PdfReader(str(path)); writer = PdfWriter()
    for page in reader.pages: page.rotate(degrees); writer.add_page(page)
    dest = Path(output)
    with dest.open("wb") as fh: writer.write(fh)
    return dest


def delete_pages(path: str | Path, output: str | Path, pages: list[int]) -> Path:
    reader = PdfReader(str(path)); remove = set(pages)
    if any(p < 1 or p > len(reader.pages) for p in remove): raise ValueError("Uma ou mais páginas são inválidas.")
    if len(remove) >= len(reader.pages): raise ValueError("Não é possível remover todas as páginas.")
    writer = PdfWriter()
    for number, page in enumerate(reader.pages, 1):
        if number not in remove: writer.add_page(page)
    dest = Path(output)
    with dest.open("wb") as fh: writer.write(fh)
    return dest


def reorder_pdf(path: str | Path, output: str | Path, order: list[int]) -> Path:
    reader = PdfReader(str(path)); total = len(reader.pages)
    if sorted(order) != list(range(1, total + 1)): raise ValueError(f"A ordem deve conter exatamente as páginas 1 a {total}, sem repetição.")
    writer = PdfWriter()
    for number in order: writer.add_page(reader.pages[number - 1])
    dest = Path(output)
    with dest.open("wb") as fh: writer.write(fh)
    return dest


def compress_pdf(path: str | Path, output: str | Path) -> Path:
    doc = fitz.open(str(path)); dest = Path(output)
    try: doc.save(str(dest), garbage=4, deflate=True, clean=True)
    finally: doc.close()
    return dest


def pdf_to_images(path: str | Path, output_dir: str | Path, dpi: int = 150) -> list[Path]:
    if dpi < 72 or dpi > 300: raise ValueError("DPI deve ficar entre 72 e 300.")
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True); files = []
    doc = fitz.open(str(path))
    try:
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        for index, page in enumerate(doc, 1):
            dest = output / f"pagina_{index:04d}.png"
            page.get_pixmap(matrix=matrix, alpha=False).save(str(dest)); files.append(dest)
    finally: doc.close()
    return files


def images_to_pdf(paths: list[str | Path], output: str | Path) -> Path:
    if not paths: raise ValueError("Selecione pelo menos uma imagem.")
    doc = fitz.open(); dest = Path(output)
    try:
        for path in paths:
            img = fitz.Pixmap(str(path))
            page = doc.new_page(width=img.width, height=img.height)
            page.insert_image(page.rect, pixmap=img)
        doc.save(str(dest))
    finally: doc.close()
    return dest


def add_watermark(path: str | Path, output: str | Path, text: str, opacity: float = 0.25) -> Path:
    if not text.strip(): raise ValueError("Informe o texto da marca d'água.")
    doc = fitz.open(str(path)); dest = Path(output); opacity = max(.05, min(1, opacity))
    try:
        for page in doc:
            r = page.rect
            page.insert_textbox(fitz.Rect(r.x0 + 30, r.y0 + r.height*.42, r.x1 - 30, r.y0 + r.height*.58), text, fontsize=min(r.width/8, 60), align=1, color=(.35,.35,.35), fill_opacity=opacity)
        doc.save(str(dest), garbage=4, deflate=True)
    finally: doc.close()
    return dest


def number_pages(path: str | Path, output: str | Path, position: str = "bottom-right") -> Path:
    doc = fitz.open(str(path)); dest = Path(output)
    try:
        for index, page in enumerate(doc, 1):
            r = page.rect
            x = r.x0 + 24 if position == "bottom-left" else ((r.x0+r.x1)/2 if position == "bottom-center" else r.x1-48)
            page.insert_text((x, r.y1-18), str(index), fontsize=10, color=(.2,.2,.2))
        doc.save(str(dest), garbage=4, deflate=True)
    finally: doc.close()
    return dest


def set_metadata(path: str | Path, output: str | Path, title: str = "", author: str = "", subject: str = "") -> Path:
    doc = fitz.open(str(path)); dest = Path(output)
    try:
        meta = doc.metadata
        if title: meta["title"] = title
        if author: meta["author"] = author
        if subject: meta["subject"] = subject
        doc.set_metadata(meta); doc.save(str(dest), garbage=4, deflate=True)
    finally: doc.close()
    return dest


def protect_pdf(path: str | Path, output: str | Path, password: str) -> Path:
    if len(password) < 4: raise ValueError("A senha deve ter pelo menos 4 caracteres.")
    reader = PdfReader(str(path)); writer = PdfWriter()
    for page in reader.pages: writer.add_page(page)
    writer.encrypt(password)
    dest = Path(output)
    with dest.open("wb") as fh: writer.write(fh)
    return dest


def pdf_info(path: str | Path) -> dict:
    reader = PdfReader(str(path)); meta = reader.metadata or {}
    return {"pages": len(reader.pages), "title": meta.title, "author": meta.author, "subject": meta.subject, "creator": meta.creator, "producer": meta.producer}
