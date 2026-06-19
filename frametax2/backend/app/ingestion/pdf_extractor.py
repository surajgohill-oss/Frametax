"""
pdf_extractor.py

Extracts raw text from PDF files using pymupdf (fitz).
Returns raw text for downstream parsing or rule extraction.
No LLM calls — pure file I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PDFExtractionResult:
    filename: str
    page_count: int
    word_count: int
    raw_text: str
    pages: list[str]  # per-page text
    extraction_method: str = "pymupdf"


def extract_text_from_pdf(
    file_path: str | Path,
    max_pages: int = 100,
) -> PDFExtractionResult:
    """
    Extract text from a PDF file using pymupdf.
    Requires pymupdf: pip install pymupdf
    """
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        raise RuntimeError("pymupdf is required: pip install pymupdf")

    path = Path(file_path)
    doc = fitz.open(str(path))
    pages: list[str] = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pages.append(page.get_text() or "")
    doc.close()

    raw_text = "\n\n".join(pages)
    return PDFExtractionResult(
        filename=path.name,
        page_count=len(pages),
        word_count=len(raw_text.split()),
        raw_text=raw_text,
        pages=pages,
    )


def extract_text_from_bytes(
    content: bytes,
    filename: str,
    max_pages: int = 100,
) -> PDFExtractionResult:
    """Extract text from PDF bytes (for uploaded files)."""
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        raise RuntimeError("pymupdf is required: pip install pymupdf")

    doc = fitz.open(stream=content, filetype="pdf")
    pages: list[str] = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pages.append(page.get_text() or "")
    doc.close()

    raw_text = "\n\n".join(pages)
    return PDFExtractionResult(
        filename=filename,
        page_count=len(pages),
        word_count=len(raw_text.split()),
        raw_text=raw_text,
        pages=pages,
    )
