"""Testes do serviço de correção visual (overlay)."""

from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from api.index import app
from src.pdf_splitter.edit import OverlayCorrection, apply_overlays, page_geometries


def _make_pdf(path: Path, pages: int = 1) -> None:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=400, height=600)
        page.insert_text((50, 80), f"VALOR ERRADO {i + 1}", fontsize=14)
    doc.save(str(path))
    doc.close()


def test_overlay_keeps_page_count_and_size(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    _make_pdf(src, pages=2)
    before = fitz.open(str(src))
    sizes = [tuple(p.rect) for p in before]
    count = before.page_count
    before.close()

    apply_overlays(
        src,
        [
            OverlayCorrection(
                page_number=1,
                x0=40,
                y0=60,
                x1=250,
                y1=100,
                text="VALOR CERTO",
                fontsize=12,
            )
        ],
    )

    after = fitz.open(str(src))
    try:
        assert after.page_count == count
        assert [tuple(p.rect) for p in after] == sizes
    finally:
        after.close()


def test_replaces_only_selected_line(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)
    page.insert_text((50, 80), "VALOR ERRADO", fontsize=14)
    page.insert_text((50, 200), "LINHA INTACTA", fontsize=14)
    doc.save(str(src))
    doc.close()

    apply_overlays(
        src,
        [
            OverlayCorrection(
                page_number=1,
                x0=45,
                y0=65,
                x1=220,
                y1=95,
                text="VALOR CERTO",
                fontsize=14,
            )
        ],
    )
    after = fitz.open(str(src))
    try:
        text = after[0].get_text().replace("\xa0", " ")
        assert "VALOR CERTO" in text
        assert "LINHA INTACTA" in text
        assert "VALOR ERRADO" not in text
    finally:
        after.close()


def test_replaces_portuguese_accents_without_tofu(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)
    page.insert_text((50, 80), "JOSE SANTOS CUNHA", fontsize=14)
    doc.save(str(src))
    doc.close()

    apply_overlays(
        src,
        [
            OverlayCorrection(
                page_number=1,
                x0=45,
                y0=65,
                x1=280,
                y1=95,
                text="José Santos Cunha",
                fontsize=14,
            )
        ],
    )
    after = fitz.open(str(src))
    try:
        text = after[0].get_text().replace("\xa0", " ")
        assert "José Santos Cunha" in text
        assert "\ufffd" not in text
    finally:
        after.close()


def test_match_visual_size_tracks_original_width() -> None:
    from src.pdf_splitter.edit import _match_visual_size, _writable_font

    font = _writable_font("", False, False)
    original = "JOSE SANTOS CUNHA"
    bbox = fitz.Rect(0, 0, 120, 20)
    size = _match_visual_size(font, original, bbox, 13.8)
    drawn = font.text_length(original, fontsize=size)
    assert abs(drawn - 120) < 2


def test_inspect_finds_line(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    _make_pdf(src, pages=1)
    client = TestClient(app)
    with src.open("rb") as fh:
        resp = client.post("/api/edit/session", files={"file": ("nota.pdf", fh, "application/pdf")})
    session = resp.json()["session_id"]
    hit = client.post(
        f"/api/edit/session/{session}/inspect",
        json={"page_number": 1, "x0": 50, "y0": 70, "x1": 180, "y1": 90},
    )
    assert hit.status_code == 200, hit.text
    data = hit.json()
    assert data["mode"] == "text"
    assert "VALOR ERRADO" in data["original"]
    assert data.get("font") or data.get("font_label")
    src = tmp_path / "doc.pdf"
    _make_pdf(src, pages=2)
    geos = page_geometries(src)
    assert len(geos) == 2
    assert geos[0]["page_number"] == 1
    assert geos[0]["width"] == 400
    assert geos[0]["height"] == 600


def test_edit_api_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    _make_pdf(src, pages=1)
    client = TestClient(app)
    with src.open("rb") as fh:
        resp = client.post("/api/edit/session", files={"file": ("nota.pdf", fh, "application/pdf")})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    session = data["session_id"]
    assert data["page_count"] == 1

    preview = client.get(f"/api/edit/session/{session}/page/1")
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/")

    apply = client.post(
        f"/api/edit/session/{session}/apply",
        json={
            "corrections": [
                {
                    "page_number": 1,
                    "x0": 40,
                    "y0": 60,
                    "x1": 250,
                    "y1": 100,
                    "text": "OK",
                    "fontsize": 12,
                }
            ]
        },
    )
    assert apply.status_code == 200, apply.text

    download = client.get(f"/api/edit/session/{session}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    doc = fitz.open(stream=download.content, filetype="pdf")
    try:
        assert doc.page_count == 1
        assert tuple(doc[0].rect) == (0.0, 0.0, 400.0, 600.0)
    finally:
        doc.close()
