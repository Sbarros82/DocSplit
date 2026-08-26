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


def unlock_pdf(path: str | Path, output: str | Path, password: str) -> Path:
    """Remove a proteção de um PDF usando a senha informada pelo usuário."""
    if not password:
        raise ValueError("Informe a senha do PDF.")
    dest = Path(output)
    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PDF: {exc}") from exc
    try:
        if doc.is_encrypted:
            auth = doc.authenticate(password)
            if not auth:
                raise ValueError("Senha incorreta ou insuficiente para desbloquear o PDF.")
        try:
            doc.save(str(dest), encryption=fitz.PDF_ENCRYPT_NONE, garbage=4, deflate=True)
        except Exception:
            # Fallback para versões sem a constante PDF_ENCRYPT_NONE
            doc.save(str(dest), garbage=4, deflate=True)
    finally:
        doc.close()
    return dest


def extract_text_markdown(path: str | Path, output: str | Path) -> Path:
    """Extrai o texto do PDF para um arquivo Markdown (uma seção por página)."""
    doc = fitz.open(str(path))
    dest = Path(output)
    lines: list[str] = [f"# Texto extraído — {Path(path).name}", ""]
    try:
        for index, page in enumerate(doc, 1):
            text = (page.get_text("text") or "").strip()
            lines.append(f"## Página {index}")
            lines.append("")
            lines.append(text if text else "*(sem texto nativo nesta página)*")
            lines.append("")
    finally:
        doc.close()
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def ocr_searchable_pdf(path: str | Path, output: str | Path, language: str = "por") -> Path:
    """Gera um PDF pesquisável com camada de texto via OCR (Tesseract)."""
    try:
        import io

        import pytesseract
        from PIL import Image
        from pytesseract import Output
    except ImportError as exc:
        raise ValueError("OCR indisponível neste ambiente (pytesseract/Pillow).") from exc

    from src.pdf_splitter.ocr import is_ocr_available

    if not is_ocr_available():
        raise ValueError("Tesseract OCR não está disponível no servidor.")

    src = fitz.open(str(path))
    out = fitz.open()
    dest = Path(output)
    try:
        for page in src:
            matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            new_page = out.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=pix.tobytes("png"))
            try:
                data = pytesseract.image_to_data(img, lang=language, output_type=Output.DICT)
            except Exception:
                data = pytesseract.image_to_data(img, lang="eng", output_type=Output.DICT)
            sx = page.rect.width / max(pix.width, 1)
            sy = page.rect.height / max(pix.height, 1)
            n = len(data.get("text") or [])
            for i in range(n):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue
                conf = data.get("conf", ["-1"])[i]
                try:
                    if float(conf) < 40:
                        continue
                except (TypeError, ValueError):
                    pass
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                fontsize = max(6.0, min(h * sy * 0.85, 28.0))
                # render_mode=3: texto invisível (selecionável/pesquisável)
                new_page.insert_text(
                    (x * sx, (y + h) * sy),
                    text,
                    fontsize=fontsize,
                    render_mode=3,
                )
        out.save(str(dest), garbage=4, deflate=True)
    finally:
        src.close()
        out.close()
    return dest


_REDACT_PATTERNS: list[tuple[str, str]] = [
    ("cpf", r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    ("cnpj", r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ("phone", r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4,5}-?\d{4}\b"),
    ("money", r"\bR\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?\b"),
]
_KNOWN_KIND_NAMES = {name for name, _ in _REDACT_PATTERNS}


def _normalize_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _term_variants(term: str) -> list[str]:
    """Gera variantes de busca (com/sem pontuação) para CPF/CNPJ e termos livres."""
    raw = term.strip()
    if not raw:
        return []
    variants = {raw}
    digits = _normalize_digits(raw)
    if len(digits) == 11:  # CPF
        variants.add(digits)
        variants.add(f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}")
        variants.add(f"{digits[:3]}{digits[3:6]}{digits[6:9]}{digits[9:]}")
    elif len(digits) == 14:  # CNPJ
        variants.add(digits)
        variants.add(
            f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        )
    return [v for v in variants if v]


def _ocr_page_matches(page: "fitz.Page", patterns: list, terms: list[str], language: str = "por") -> list:
    """Localiza retângulos via OCR quando o PDF é scan (sem texto nativo)."""
    import io
    import re

    try:
        import pytesseract
        from PIL import Image
        from pytesseract import Output
    except ImportError:
        return []

    from src.pdf_splitter.ocr import is_ocr_available

    if not is_ocr_available():
        return []

    matrix = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    try:
        data = pytesseract.image_to_data(img, lang=language, output_type=Output.DICT)
    except Exception:
        data = pytesseract.image_to_data(img, lang="eng", output_type=Output.DICT)

    sx = page.rect.width / max(pix.width, 1)
    sy = page.rect.height / max(pix.height, 1)
    n = len(data.get("text") or [])
    words: list[tuple[str, fitz.Rect]] = []
    full_parts: list[str] = []
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        rect = fitz.Rect(x * sx, y * sy, (x + w) * sx, (y + h) * sy)
        words.append((text, rect))
        full_parts.append(text)
    full_text = " ".join(full_parts)
    hits: list[fitz.Rect] = []

    # Termos explícitos (e variantes)
    for term in terms:
        for variant in _term_variants(term):
            for word, rect in words:
                if variant.lower() in word.lower() or _normalize_digits(variant) and _normalize_digits(variant) == _normalize_digits(word):
                    hits.append(rect)
            # Janela de 1–3 palavras (ex.: CPF quebrado em tokens OCR)
            for i in range(len(words)):
                for span in range(1, 4):
                    chunk = " ".join(w for w, _ in words[i : i + span])
                    compact = chunk.replace(" ", "")
                    if variant.lower() in chunk.lower() or variant.replace(".", "").replace("-", "").replace("/", "") in compact.replace(".", "").replace("-", "").replace("/", ""):
                        union = words[i][1]
                        for _, r in words[i + 1 : i + span]:
                            union |= r
                        hits.append(union)

    # Padrões regex no texto OCR concatenado + mapear para boxes por dígitos
    for pattern in patterns:
        for match in pattern.finditer(full_text):
            snippet = match.group(0)
            target_digits = _normalize_digits(snippet)
            if not target_digits:
                continue
            for i in range(len(words)):
                for span in range(1, 5):
                    chunk_words = words[i : i + span]
                    chunk = "".join(w for w, _ in chunk_words)
                    if _normalize_digits(chunk) == target_digits:
                        union = chunk_words[0][1]
                        for _, r in chunk_words[1:]:
                            union |= r
                        hits.append(union)
                        break
    return hits


def redact_sensitive(
    path: str | Path,
    output: str | Path,
    kinds: list[str] | None = None,
    extra_terms: list[str] | None = None,
) -> Path:
    """Tarja dados sensíveis (CPF, CNPJ, e-mail, telefone, valores) e termos extras.

    Aceita PDF com texto nativo ou scan (usa OCR como fallback).
    Valores que parecem CPF/CNPJ enviados em `kinds` são tratados como termos.
    """
    import re

    raw_kinds = [k.strip() for k in (kinds or []) if k and k.strip()]
    selected: set[str] = set()
    migrated_terms: list[str] = []
    for item in raw_kinds:
        lower = item.lower()
        if lower in _KNOWN_KIND_NAMES:
            selected.add(lower)
        else:
            # Usuário colou CPF/nome no campo de tipos — trata como termo
            migrated_terms.append(item)
    if not selected and not migrated_terms and not extra_terms:
        selected = set(_KNOWN_KIND_NAMES)
    elif not selected and (migrated_terms or extra_terms):
        # Se só veio termo livre, ainda aplica padrões padrão de CPF/CNPJ etc.
        selected = set(_KNOWN_KIND_NAMES)

    patterns = [re.compile(pat, re.IGNORECASE) for name, pat in _REDACT_PATTERNS if name in selected]
    terms = [t.strip() for t in (extra_terms or []) if t and t.strip()]
    terms.extend(migrated_terms)
    # Dedup preservando ordem
    seen: set[str] = set()
    uniq_terms: list[str] = []
    for t in terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            uniq_terms.append(t)
    terms = uniq_terms

    doc = fitz.open(str(path))
    dest = Path(output)
    hits = 0
    try:
        for page in doc:
            text = page.get_text("text") or ""
            page_hits = 0

            for pattern in patterns:
                for match in pattern.finditer(text):
                    snippet = match.group(0)
                    for variant in _term_variants(snippet):
                        for rect in page.search_for(variant):
                            page.add_redact_annot(rect, fill=(0, 0, 0))
                            page_hits += 1

            for term in terms:
                for variant in _term_variants(term):
                    for rect in page.search_for(variant):
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                        page_hits += 1

            # Scan / pouco texto nativo → OCR
            if page_hits == 0 and len(text.strip()) < 40:
                for rect in _ocr_page_matches(page, patterns, terms):
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    page_hits += 1

            if page_hits:
                page.apply_redactions()
                hits += page_hits

        if hits == 0:
            raise ValueError(
                "Nenhum dado sensível encontrado para tarjar. "
                "Se o PDF for imagem/scan, o OCR pode falhar — "
                "coloque o CPF/nome em «Termos a tarjar» e tente de novo."
            )
        doc.save(str(dest), garbage=4, deflate=True)
    finally:
        doc.close()
    return dest


def add_signature_stamp(
    path: str | Path,
    output: str | Path,
    label: str,
    image_path: str | Path | None = None,
    page_number: int = -1,
) -> Path:
    """Adiciona carimbo/assinatura (texto e/ou imagem) na página indicada (-1 = última)."""
    if not label.strip() and not image_path:
        raise ValueError("Informe o nome da assinatura ou envie uma imagem.")
    doc = fitz.open(str(path))
    dest = Path(output)
    try:
        if not len(doc):
            raise ValueError("O PDF não contém páginas.")
        idx = len(doc) - 1 if page_number < 0 else page_number - 1
        if idx < 0 or idx >= len(doc):
            raise ValueError("Número de página inválido.")
        page = doc[idx]
        rect = page.rect
        box = fitz.Rect(rect.x1 - 220, rect.y1 - 110, rect.x1 - 24, rect.y1 - 24)
        if image_path:
            page.insert_image(box, filename=str(image_path), keep_proportion=True)
        else:
            page.draw_rect(box, color=(0.1, 0.1, 0.1), width=1)
            page.insert_textbox(
                fitz.Rect(box.x0 + 8, box.y0 + 8, box.x1 - 8, box.y1 - 8),
                f"Assinado por\n{label.strip()}",
                fontsize=11,
                align=0,
                color=(0.1, 0.1, 0.1),
            )
        doc.save(str(dest), garbage=4, deflate=True)
    finally:
        doc.close()
    return dest


def pdf_info(path: str | Path) -> dict:
    reader = PdfReader(str(path)); meta = reader.metadata or {}
    return {"pages": len(reader.pages), "title": meta.title, "author": meta.author, "subject": meta.subject, "creator": meta.creator, "producer": meta.producer}
