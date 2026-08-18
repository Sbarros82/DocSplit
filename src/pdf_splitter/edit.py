"""
Serviço de correção pontual de PDF.

Troca só o texto da linha escolhida (redação de glifos, sem pintar
retângulo e sem apagar bordas/imagens). Página escaneada sem texto
nativo usa um tapa da cor do fundo, só na caixa do trecho.
"""

from __future__ import annotations

from pathlib import Path

import fitz
from pydantic import BaseModel, Field


class OverlayCorrection(BaseModel):
    """Correção em coordenadas PDF (pontos, origem no topo-esquerdo)."""

    page_number: int = Field(..., ge=1, description="Página 1-indexed")
    x0: float
    y0: float
    x1: float
    y1: float
    text: str = Field(..., min_length=1, max_length=2000)
    fontsize: float | None = Field(None, gt=4, lt=72)


def apply_overlays(
    pdf_path: str | Path,
    corrections: list[OverlayCorrection],
    output_path: str | Path | None = None,
) -> Path:
    """
    Aplica correções pontuais no PDF.

    Entrada: caminho do PDF e lista de OverlayCorrection.
    Saída: caminho do PDF gravado.

    Não altera o tamanho das páginas. Só remove o texto da linha
    escolhida; vetores e imagens permanecem.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf_path}")
    if not corrections:
        raise ValueError("Informe ao menos uma correcao.")

    dest = Path(output_path) if output_path else pdf_path
    doc = fitz.open(str(pdf_path))
    try:
        _apply_on_document(doc, corrections)
        _save_preserving_structure(doc, pdf_path, dest)
    finally:
        if not doc.is_closed:
            doc.close()
    return dest


def inspect_region(
    pdf_path: str | Path,
    page_number: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> dict:
    """
    Descobre a linha de texto sob a seleção (para encaixar o recorte na UI).

    Entrada: PDF, página e retângulo em pontos.
    Saída: dict com mode, original, bbox e fontsize.
    """
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Pagina {page_number} inexistente (total {doc.page_count}).")
        page = doc[page_number - 1]
        rect = _selection_rect(x0, y0, x1, y1, page.rect)
        hit = _pick_line(page, rect)
        if hit:
            font = _writable_font(hit["font"], hit["bold"], hit["italic"])
            render_size = _match_visual_size(font, hit["text"], hit["bbox"], hit["size"])
            return {
                "mode": "text",
                "original": hit["text"],
                "fontsize": round(render_size, 1),
                "fontsize_pdf": round(hit["size"], 1),
                "font": hit["font"],
                "font_label": hit["font_label"],
                "bold": hit["bold"],
                "italic": hit["italic"],
                "bbox": _bbox_dict(hit["bbox"]),
            }
        return {
            "mode": "image",
            "original": "",
            "fontsize": max(8.0, min(14.0, rect.height * 0.7)),
            "font": None,
            "font_label": "sem texto nativo",
            "bold": False,
            "italic": False,
            "bbox": _bbox_dict(rect),
        }
    finally:
        doc.close()


def page_geometries(pdf_path: str | Path) -> list[dict]:
    """Devolve largura/altura em pontos de cada página."""
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))
    try:
        pages = []
        for i, page in enumerate(doc, start=1):
            rect = page.rect
            pages.append({
                "page_number": i,
                "width": float(rect.width),
                "height": float(rect.height),
            })
        return pages
    finally:
        doc.close()


def render_page_preview(
    pdf_path: str | Path,
    page_number: int,
    dpi: int = 130,
) -> bytes:
    """Renderiza uma página como JPEG para a tela de edição."""
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Pagina {page_number} inexistente (total {doc.page_count}).")
        page = doc[page_number - 1]
        zoom = dpi / 72
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        try:
            return pixmap.tobytes("jpeg")
        except TypeError:
            return pixmap.tobytes("jpg")
    finally:
        doc.close()


def _apply_on_document(doc: fitz.Document, corrections: list[OverlayCorrection]) -> None:
    original_sizes = [tuple(page.rect) for page in doc]
    for item in corrections:
        if item.page_number > doc.page_count:
            raise ValueError(
                f"Pagina {item.page_number} inexistente (total {doc.page_count})."
            )
        page = doc[item.page_number - 1]
        rect = _selection_rect(item.x0, item.y0, item.x1, item.y1, page.rect)
        hit = _pick_line(page, rect)
        new_text = item.text.strip()
        if hit:
            _replace_text_line(page, hit, new_text, item.fontsize)
        else:
            _patch_image_region(page, rect, new_text, item.fontsize)

    for i, page in enumerate(doc):
        if tuple(page.rect) != original_sizes[i]:
            raise ValueError("A correcao alterou o tamanho da pagina — operacao abortada.")


def _replace_text_line(
    page: fitz.Page,
    hit: dict,
    new_text: str,
    fontsize: float | None,
) -> None:
    """Remove só os glifos da linha e escreve o texto novo no mesmo ponto-base."""
    for span_rect in hit["span_rects"]:
        page.add_redact_annot(span_rect, fill=None, cross_out=False)
    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
        text=fitz.PDF_REDACT_TEXT_REMOVE,
    )
    size = fontsize or hit["size"]
    _insert_unicode_text(
        page,
        hit["origin"],
        new_text,
        size,
        hit["color"],
        pdf_font=hit.get("font") or "",
        bold=bool(hit.get("bold")),
        italic=bool(hit.get("italic")),
        bbox=hit["bbox"],
        original_text=hit.get("text") or "",
    )


def _patch_image_region(
    page: fitz.Page,
    rect: fitz.Rect,
    new_text: str,
    fontsize: float | None,
) -> None:
    """Página sem texto nativo: tapa só a caixa, na cor do fundo amostrado."""
    if rect.width * rect.height > 0.08 * page.rect.width * page.rect.height:
        raise ValueError(
            "Nesta pagina nao ha texto selecionavel. Marque so o trecho pequeno a corrigir."
        )
    fill = _sample_background(page, rect)
    page.draw_rect(rect, color=fill, fill=fill, width=0)
    size = fontsize or max(8.0, min(16.0, rect.height * 0.65))
    _insert_unicode_text(
        page,
        (rect.x0 + 1, rect.y0 + size),
        new_text,
        size,
        (0, 0, 0),
        bbox=rect,
    )


def _pick_line(page: fitz.Page, rect: fitz.Rect) -> dict | None:
    """Escolhe UMA linha de texto (a de maior sobreposição) — nunca a tabela inteira."""
    lines = _extract_lines(page)
    if not lines:
        return None
    point = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
    tiny = rect.width < 8 and rect.height < 8

    best: dict | None = None
    best_score = 0.0
    for line in lines:
        inter = line["bbox"] & rect
        if tiny:
            if line["bbox"].contains(point):
                dist = abs(line["bbox"].y0 + line["bbox"].height / 2 - point.y)
                score = 1000.0 - dist
            else:
                dist = abs(line["bbox"].y0 + line["bbox"].height / 2 - point.y)
                if dist > 18:
                    continue
                score = 100.0 - dist
        else:
            if inter.is_empty:
                continue
            score = inter.width * inter.height
        if score > best_score:
            best_score = score
            best = line
    return best


def _extract_lines(page: fitz.Page) -> list[dict]:
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
    lines: list[dict] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if (s.get("text") or "").strip()]
            if not spans:
                continue
            bbox = fitz.Rect(line["bbox"])
            first = spans[0]
            origin = first.get("origin") or (bbox.x0, bbox.y1 - 1)
            color_int = int(first.get("color") or 0)
            flags = int(first.get("flags") or 0)
            raw_font = str(first.get("font") or "")
            lines.append({
                "text": "".join(s.get("text", "") for s in spans).strip(),
                "bbox": bbox,
                "span_rects": [fitz.Rect(s["bbox"]) for s in spans],
                "size": float(first.get("size") or 11),
                "origin": (float(origin[0]), float(origin[1])),
                "color": _rgb(color_int),
                "font": raw_font,
                "font_label": _font_label(raw_font, flags),
                "bold": bool(flags & 16),
                "italic": bool(flags & 2),
            })
    return lines


def _clean_font_name(raw: str) -> str:
    """Tira prefixo de subset (ABCDEF+Roboto-Regular → Roboto-Regular)."""
    name = (raw or "").strip()
    if "+" in name:
        name = name.split("+", 1)[1]
    return name or "desconhecida"


def _font_label(raw: str, flags: int) -> str:
    """Nome legível da fonte, com peso se o PDF marcar negrito/itálico."""
    name = _clean_font_name(raw).replace("-", " ").replace("_", " ")
    extras = []
    if flags & 16 and "bold" not in name.lower():
        extras.append("negrito")
    if flags & 2 and "italic" not in name.lower() and "oblique" not in name.lower():
        extras.append("italico")
    if extras:
        return f"{name} ({', '.join(extras)})"
    return name


def _insert_unicode_text(
    page: fitz.Page,
    origin: tuple[float, float],
    text: str,
    fontsize: float,
    color: tuple[float, float, float],
    pdf_font: str = "",
    bold: bool = False,
    italic: bool = False,
    bbox: fitz.Rect | None = None,
    original_text: str = "",
) -> None:
    """
    Escreve com o mesmo tamanho visual da linha original.

    O pt do PDF (ex.: 13,8) não bate com Calibri/Arial. O tamanho é
    calculado para o texto original ocupar a mesma largura da caixa.
    """
    path = _pick_system_font(pdf_font, bold, italic)
    font = fitz.Font(fontfile=str(path)) if path else _writable_font(pdf_font, bold, italic)
    size = _match_visual_size(font, original_text or text, bbox, fontsize)
    writer = fitz.TextWriter(page.rect, color=color)
    writer.append(origin, text, font=font, fontsize=size)
    writer.write_text(page)


def _match_visual_size(
    font: fitz.Font,
    original_text: str,
    bbox: fitz.Rect | None,
    fallback: float,
) -> float:
    """
    Tamanho em que a fonte de reposição desenha o texto original
    com a mesma largura da linha no PDF.
    """
    size = max(6.0, fallback)
    orig = (original_text or "").strip()
    if orig and bbox is not None and bbox.width > 2:
        try:
            unit = font.text_length(orig, fontsize=1.0)
        except Exception:
            unit = 0.0
        if unit > 0:
            size = bbox.width / unit
    if bbox is not None and bbox.height > 2:
        size = min(size, bbox.height * 0.78)
    return max(6.0, size)


def _writable_font(pdf_font: str, bold: bool, italic: bool) -> fitz.Font:
    path = _pick_system_font(pdf_font, bold, italic)
    if path:
        return fitz.Font(fontfile=str(path))
    for builtin in ("notos", "cjk", "helv"):
        try:
            return fitz.Font(builtin)
        except Exception:
            continue
    return fitz.Font("helv")


def _pick_system_font(pdf_font: str, bold: bool, italic: bool) -> Path | None:
    """Escolhe um TTF completo do Windows parecido com a fonte do PDF."""
    import os

    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if not fonts_dir.is_dir():
        return None
    name = _clean_font_name(pdf_font).lower()
    if "bold" in name:
        bold = True
    if "italic" in name or "oblique" in name:
        italic = True
    serif = any(k in name for k in ("times", "georgia", "garamond", "cambria")) and "sans" not in name
    ordered = _font_files(bold, italic, serif=serif)
    for filename in ordered:
        path = fonts_dir / filename
        if path.exists():
            return path
    return None


def _font_files(bold: bool, italic: bool, serif: bool) -> list[str]:
    if serif:
        if bold and italic:
            return ["timesbi.ttf", "timesbd.ttf", "times.ttf"]
        if bold:
            return ["timesbd.ttf", "times.ttf"]
        if italic:
            return ["timesi.ttf", "times.ttf"]
        return ["times.ttf", "georgia.ttf"]
    if bold and italic:
        return ["arialbi.ttf", "calibriz.ttf", "arialbd.ttf", "arial.ttf"]
    if bold:
        return ["arialbd.ttf", "calibrib.ttf", "segoeuib.ttf", "arial.ttf"]
    if italic:
        return ["ariali.ttf", "calibrii.ttf", "arial.ttf"]
    return ["calibri.ttf", "arial.ttf", "segoeui.ttf", "tahoma.ttf"]


def _rgb(color: int) -> tuple[float, float, float]:
    return (
        ((color >> 16) & 255) / 255.0,
        ((color >> 8) & 255) / 255.0,
        (color & 255) / 255.0,
    )


def _sample_background(page: fitz.Page, rect: fitz.Rect) -> tuple[float, float, float]:
    clip = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
    clip = clip & page.rect
    pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(1, 1), alpha=False)
    samples = pix.samples
    n = pix.n
    if not samples or n < 3:
        return (1.0, 1.0, 1.0)
    # média dos pixels da borda (evita pegar a tinta do texto no centro)
    w, h = pix.width, pix.height
    acc = [0, 0, 0]
    count = 0
    for y in (0, h - 1):
        for x in range(w):
            i = (y * w + x) * n
            acc[0] += samples[i]
            acc[1] += samples[i + 1]
            acc[2] += samples[i + 2]
            count += 1
    for x in (0, w - 1):
        for y in range(h):
            i = (y * w + x) * n
            acc[0] += samples[i]
            acc[1] += samples[i + 1]
            acc[2] += samples[i + 2]
            count += 1
    if count == 0:
        return (1.0, 1.0, 1.0)
    return (acc[0] / count / 255.0, acc[1] / count / 255.0, acc[2] / count / 255.0)


def _selection_rect(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    page_rect: fitz.Rect,
) -> fitz.Rect:
    rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    if rect.width < 2 and rect.height < 2:
        pad = 3
        rect = fitz.Rect(rect.x0 - pad, rect.y0 - pad, rect.x1 + pad, rect.y1 + pad)
    rect = rect & page_rect
    if rect.is_empty:
        raise ValueError("A area selecionada e invalida.")
    return rect


def _bbox_dict(rect: fitz.Rect) -> dict:
    return {
        "x0": float(rect.x0),
        "y0": float(rect.y0),
        "x1": float(rect.x1),
        "y1": float(rect.y1),
    }


def _save_preserving_structure(
    doc: fitz.Document,
    source: Path,
    dest: Path,
) -> None:
    """Grava incrementalmente quando possível; senão copia sem garbage collection."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    same_file = dest.resolve() == source.resolve()
    if same_file:
        try:
            doc.saveIncr()
            return
        except Exception:
            tmp = dest.with_name(dest.stem + ".edit-tmp.pdf")
            doc.save(str(tmp), garbage=0, deflate=False)
            doc.close()
            dest.unlink(missing_ok=True)
            tmp.replace(dest)
            return
    doc.save(str(dest), garbage=0, deflate=False)
