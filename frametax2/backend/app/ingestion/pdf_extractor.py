"""
pdf_extractor.py

Extracts raw text from PDF files using pypdf.
Returns raw text for downstream LLM extraction or rule parsing.
No LLM calls here — pure file I/O.
"""
from __future__ import annotations

import io
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PDFExtractionResult:
    filename: str
    page_count: int
    word_count: int
    raw_text: str
    pages: list[str]  # per-page text
    extraction_method: str = "pypdf"


def extract_text_from_pdf(
    file_path: str | Path,
    max_pages: int = 100,
) -> PDFExtractionResult:
    """
    Extract text from a PDF file.
    Requires pypdf: pip install pypdf
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf is required: pip install pypdf")

    path = Path(file_path)
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        pages.append(page.extract_text() or "")

    raw_text = "\n\n".join(pages)
    word_count = len(raw_text.split())

    return PDFExtractionResult(
        filename=path.name,
        page_count=len(reader.pages),
        word_count=word_count,
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
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf is required: pip install pypdf")

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        pages.append(page.extract_text() or "")

    raw_text = "\n\n".join(pages)

    return PDFExtractionResult(
        filename=filename,
        page_count=len(reader.pages),
        word_count=len(raw_text.split()),
        raw_text=raw_text,
        pages=pages,
    )
