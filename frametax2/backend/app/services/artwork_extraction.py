"""
artwork_extraction.py — Phase F: candidate cover-art extraction from a
deck/lookbook/screenplay's own first page/slide. Never generative, never
OCR/semantic — this only ever picks the single largest embedded raster
image on the relevant page and returns its ORIGINAL bytes untouched.

Two independent extractors, one per source container:
  - `extract_pdf_cover`  — PyMuPDF: the largest-by-page-area embedded
    image on page 1, extracted at its original encoding (no re-render).
  - `extract_pptx_cover` — a .pptx is a zip archive; the largest embedded
    image referenced by slide 1's own relationships.

Both apply the same two rejection gates, calibrated against the real MTS
corpus (see Phase F notes): a page-coverage/size floor to reject small
logos, decorative bullets, and chart/table pages, so only a genuine
full-bleed cover photo or illustration is ever returned. `None` means "no
legitimate candidate on this page" — never a low-quality fallback.
"""
from __future__ import annotations

import posixpath
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import fitz

# A logo/bullet/decorative element is rejected outright below this pixel
# area — calibrated against real corpus data (logos found at 194x194 /
# 280x196 / 300x168, areas 37k–61k; real cover photos found at 1456x840 /
# 2500x1368, areas 1.2M–3.4M). Area rather than width/height separately,
# since a PDF's native-embedded image can be portrait-oriented even when
# the page transform stretches it to fill a landscape page (e.g. a
# 453x828 JPXDecode image scaled to cover a 1280x700 page) — checking
# width and height independently would wrongly reject that legitimate case.
MIN_AREA = 500 * 350

# Browser-renderable encodings we pass through untouched. Anything else
# PyMuPDF might extract (JPXDecode/JPEG2000 is common in print-quality
# PDFs — a real case in this corpus) is converted to PNG so the stored
# candidate can actually be displayed as an <img>, never left in a format
# most browsers can't decode.
_WEB_SAFE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}


def _ensure_web_safe(data: bytes, ext: str) -> tuple[bytes, str]:
    if ext.lower() in _WEB_SAFE_EXTS:
        return data, ext.lower()
    pix = fitz.Pixmap(data)
    if pix.colorspace is None:  # a mask/alpha-only plane, not a displayable image
        pix = fitz.Pixmap(fitz.csRGB, pix)
    elif pix.colorspace.n not in (1, 3):  # CMYK etc. — normalize to RGB for PNG
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return pix.tobytes("png"), "png"
# Fraction of the PDF page's own area the single largest image must cover
# to count as a real cover photo rather than an incidental small graphic
# (a genuine screenplay title-page logo measured at 0.09; real covers
# measured at 0.83–1.00).
MIN_PAGE_COVERAGE = 0.20


@dataclass(frozen=True)
class ExtractedImage:
    data: bytes
    ext: str  # "jpg" | "jpeg" | "png" | ... — the image's own original encoding
    width: int | None
    height: int | None


def extract_pdf_cover(path: Path) -> ExtractedImage | None:
    """Largest embedded image on page 1, only if it plausibly IS the
    cover — no OCR, no page rendering, no text inspection. A screenplay's
    ordinary text-only title page (zero embedded images, or only a tiny
    logo) correctly returns None."""
    doc = fitz.open(path)
    try:
        if doc.page_count == 0:
            return None
        page = doc[0]
        rect = page.rect
        page_area = rect.width * rect.height
        if page_area <= 0:
            return None

        best_xref, best_area = None, 0.0
        for info in page.get_image_info(xrefs=True):
            bbox = fitz.Rect(info["bbox"]) & rect
            area = bbox.width * bbox.height
            if area > best_area:
                best_area, best_xref = area, info.get("xref")
        if not best_xref or (best_area / page_area) < MIN_PAGE_COVERAGE:
            return None

        extracted = doc.extract_image(best_xref)
        w, h = extracted.get("width"), extracted.get("height")
        if w and h and (w * h) < MIN_AREA:
            return None
        data, ext = _ensure_web_safe(extracted["image"], extracted["ext"])
        return ExtractedImage(data=data, ext=ext, width=w, height=h)
    finally:
        doc.close()


def extract_pptx_cover(path: Path) -> ExtractedImage | None:
    """Largest (by pixel area) image referenced by slide 1's own
    relationships — a deck's title-slide background/hero photo, not a
    randomly-chosen embedded image from anywhere in the deck."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        rels_path = "ppt/slides/_rels/slide1.xml.rels"
        if rels_path not in names:
            return None
        root = ET.fromstring(z.read(rels_path))

        best: ExtractedImage | None = None
        best_area = 0
        for rel_el in root:
            target = rel_el.get("Target") or ""
            if "media" not in target:
                continue
            full = posixpath.normpath(posixpath.join("ppt/slides", target))
            if full not in names:
                continue
            data = z.read(full)
            try:
                pix = fitz.Pixmap(data)
                w, h = pix.width, pix.height
            except Exception:
                continue
            area = w * h
            if area <= best_area or area < MIN_AREA:
                continue
            ext = Path(full).suffix.lstrip(".").lower() or "jpg"
            data, ext = _ensure_web_safe(data, ext)
            best, best_area = ExtractedImage(data=data, ext=ext, width=w, height=h), area
        return best


def extract_cover_image(path: Path) -> ExtractedImage | None:
    """Dispatch by extension. Any other file type (budgets, xlsx, legal
    docs) is never a candidate source — returns None immediately."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf_cover(path)
    if ext == ".pptx":
        return extract_pptx_cover(path)
    return None


# A page whose non-white pixel coverage falls below this is "mostly blank
# page with sparse ink" — a plain screenplay title page or a financial
# table/topsheet — never a composed cover. Calibrated against real
# examples: screenplay title pages measured at 0.005–0.013; budget/
# topsheet pages (grid lines + numbers) at 0.14–0.19; a thin, mostly-
# white deck-cover title treatment at 0.037; genuine designed deck covers
# (color field / photo background) measured at 0.79–0.99. The threshold
# sits well above the budget/topsheet band so those are never mistaken
# for a cover, and well below the real-cover band.
MIN_NONWHITE_RATIO = 0.30
_WHITE_THRESHOLD = 235  # per-channel; pixels lighter than this count as "white"


def render_pdf_page_as_candidate(path: Path, page_index: int = 0) -> ExtractedImage | None:
    """Tier 3 fallback — used only when extract_pdf_cover() found no
    embedded raster image candidate. A composed deck/look-book cover can
    be built entirely from vector shapes, gradients, and typography with
    no embedded photo at all; that page IS the artwork. Renders the whole
    page as a flat image and evaluates its own visual richness (not
    content/OCR) to reject plain text pages and financial tables — see
    MIN_NONWHITE_RATIO. Callers are responsible for only invoking this for
    deck/lookbook categories, never screenplay/budget/legal (rejecting a
    plain screenplay title page or a budget topsheet by CATEGORY is a
    stronger, cheaper guarantee than trying to detect it visually alone)."""
    doc = fitz.open(path)
    try:
        if page_index >= doc.page_count:
            return None
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        if pix.width * pix.height == 0:
            return None

        samples = pix.samples
        stride = pix.n
        total = pix.width * pix.height
        step = max(1, total // 20000)  # sample for speed on large pages
        nonwhite, sampled = 0, 0
        for i in range(0, total, step):
            off = i * stride
            px = samples[off:off + min(3, stride)]
            if len(px) < 3:
                continue
            r, g, b = px[0], px[1], px[2]
            if not (r > _WHITE_THRESHOLD and g > _WHITE_THRESHOLD and b > _WHITE_THRESHOLD):
                nonwhite += 1
            sampled += 1
        ratio = nonwhite / sampled if sampled else 0.0
        if ratio < MIN_NONWHITE_RATIO:
            return None

        return ExtractedImage(data=pix.tobytes("png"), ext="png", width=pix.width, height=pix.height)
    finally:
        doc.close()
