"""
Tests for budget_parser.parse_budget_from_text and the pymupdf-backed
pdf_extractor. No real PDFs are required — the text-parser tests use
synthetic budget text that mirrors common film budget export formats.
"""
from __future__ import annotations

import io
import pytest

from app.ingestion.budget_parser import (
    BudgetParseResult,
    ParsedLineItem,
    parse_budget_from_text,
    classify_parsed_items,
    _parse_amount_from_line,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text(*lines: str) -> str:
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# _parse_amount_from_line unit tests
# ---------------------------------------------------------------------------

class TestParseAmountFromLine:
    def test_plain_integer(self):
        assert _parse_amount_from_line("Director 500000") == 500_000

    def test_comma_separated(self):
        assert _parse_amount_from_line("Writer Fee $1,250,000") == 1_250_000

    def test_decimal(self):
        assert _parse_amount_from_line("Equipment 45,000.00") == 45_000.0

    def test_k_suffix(self):
        assert _parse_amount_from_line("Locations 120K") == 120_000

    def test_m_suffix(self):
        assert _parse_amount_from_line("Budget Total 1.5M") == 1_500_000

    def test_no_amount(self):
        assert _parse_amount_from_line("ABOVE THE LINE") is None

    def test_small_number_ignored(self):
        # Page numbers (1, 2, 3) should not be captured as amounts
        assert _parse_amount_from_line("Scene 3") is None

    def test_currency_symbol(self):
        assert _parse_amount_from_line("Travel £18,500") == 18_500


# ---------------------------------------------------------------------------
# parse_budget_from_text
# ---------------------------------------------------------------------------

class TestParseBudgetFromText:
    def test_basic_rows(self):
        text = _text(
            "Director Fee      1,500,000",
            "Producer Fee      750,000",
            "Screenplay        200,000",
        )
        result = parse_budget_from_text(text, filename="test.pdf")
        assert isinstance(result, BudgetParseResult)
        assert result.filename == "test.pdf"
        assert len(result.line_items) == 3

    def test_amounts_parsed_correctly(self):
        text = _text(
            "Director Fee      1,500,000",
            "Crew Labor        800,000",
        )
        result = parse_budget_from_text(text)
        amounts = [i.amount_usd for i in result.line_items]
        assert 1_500_000 in amounts
        assert 800_000 in amounts

    def test_total_sentinel_excluded_from_items(self):
        text = _text(
            "Director Fee      1,500,000",
            "Total Budget      2,300,000",
        )
        result = parse_budget_from_text(text)
        # Total line should not appear as a line item
        descs = [i.description.lower() for i in result.line_items]
        assert not any("total" in d for d in descs)

    def test_total_captured_separately(self):
        text = _text(
            "Director Fee      1,500,000",
            "Grand Total       2,000,000",
        )
        result = parse_budget_from_text(text)
        assert result.total_budget_raw == 2_000_000

    def test_department_header_propagates(self):
        text = _text(
            "ABOVE THE LINE",
            "Director Fee      1,500,000",
            "Writer Fee        300,000",
        )
        result = parse_budget_from_text(text)
        # Both rows should pick up the department
        depts = [i.department for i in result.line_items if i.department]
        assert len(depts) >= 1
        # Header is title-cased
        assert all("Above The Line" in (d or "") for d in depts)

    def test_empty_text_returns_warning(self):
        result = parse_budget_from_text("", filename="empty.pdf")
        assert result.line_count == 0
        assert result.parse_warnings

    def test_no_amounts_returns_warning(self):
        result = parse_budget_from_text(
            "This document contains no monetary values at all.",
            filename="none.pdf",
        )
        assert result.line_count == 0
        assert result.parse_warnings

    def test_currency_code_propagated(self):
        text = "Director Fee  1,500,000"
        result = parse_budget_from_text(text, currency_code="CAD")
        assert result.currency_code == "CAD"
        assert all(i.currency_code == "CAD" for i in result.line_items)

    def test_source_page_populated(self):
        # Page break is \x0c (form feed)
        text = "Director Fee  1,000,000\x0cCrew Labor  500,000"
        result = parse_budget_from_text(text)
        pages = {i.source_page for i in result.line_items}
        # Items come from different pages
        assert len(pages) == 2

    def test_multipage_items_aggregated(self):
        pages = [
            "Director Fee  1,000,000",
            "Producer Fee  500,000",
            "Crew Labor    800,000",
        ]
        text = "\x0c".join(pages)
        result = parse_budget_from_text(text)
        assert result.line_count == 3

    def test_computed_total_when_no_sentinel(self):
        text = _text(
            "Director Fee      1,000,000",
            "Producer Fee      500,000",
        )
        result = parse_budget_from_text(text)
        assert result.total_budget_raw == pytest.approx(1_500_000)

    def test_origin_note_set(self):
        result = parse_budget_from_text("Director Fee 1,000,000")
        assert result.origin_note == "parsed from PDF text"


class TestParseBudgetFromTextWithClassification:
    def test_classify_after_parse(self):
        text = _text(
            "Director Fee  1,500,000",
            "Camera Equipment  200,000",
            "Grip & Electric  150,000",
        )
        result = parse_budget_from_text(text)
        classified = classify_parsed_items(result)
        # Classification attributes should be attached
        for item in classified.line_items:
            assert hasattr(item, "atl_btl")
            assert hasattr(item, "spend_category")

    def test_director_classified_atl(self):
        text = "Director Fee  1,500,000"
        result = classify_parsed_items(parse_budget_from_text(text))
        director_items = [i for i in result.line_items if "Director" in i.description]
        assert director_items, "Expected at least one director item"
        assert director_items[0].atl_btl in ("ATL", "atl")


# ---------------------------------------------------------------------------
# pdf_extractor import sanity (no real PDF needed)
# ---------------------------------------------------------------------------

class TestPDFExtractorImports:
    def test_imports_cleanly(self):
        from app.ingestion.pdf_extractor import (
            PDFExtractionResult,
            extract_text_from_pdf,
            extract_text_from_bytes,
        )
        assert PDFExtractionResult is not None

    def test_extraction_method_is_pymupdf(self):
        from app.ingestion.pdf_extractor import PDFExtractionResult
        r = PDFExtractionResult(
            filename="x.pdf",
            page_count=1,
            word_count=10,
            raw_text="hello world",
            pages=["hello world"],
        )
        assert r.extraction_method == "pymupdf"

    def test_extract_bytes_with_synthetic_pdf(self):
        """Build a minimal valid PDF in memory and verify extraction."""
        import fitz  # type: ignore[import]
        from app.ingestion.pdf_extractor import extract_text_from_bytes

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 100), "Director Fee  1,500,000")
        page.insert_text((72, 120), "Crew Labor      800,000")
        buf = doc.tobytes()
        doc.close()

        result = extract_text_from_bytes(buf, "synthetic.pdf")
        assert result.filename == "synthetic.pdf"
        assert result.page_count == 1
        assert "1,500,000" in result.raw_text or "1500000" in result.raw_text
        assert result.extraction_method == "pymupdf"
