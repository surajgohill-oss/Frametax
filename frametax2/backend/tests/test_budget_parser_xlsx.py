"""
test_budget_parser_xlsx.py

Backend-wiring self-audit, Section A (2026-09-17): before this pass, EVERY
XLSX upload was silently mis-handled two different ways depending on which
real API path it went through:

  - POST /projects/{id}/budgets/import (app/api/v1/budgets.py) explicitly
    claims to accept ".csv"/".xlsx", but handed the raw XLSX bytes straight
    to parse_budget_csv(), which does `.decode("utf-8-sig", errors="replace")`
    -- an XLSX file's real content is a ZIP/binary payload, not text, so
    this silently produced garbage/near-empty output, never an error.
  - The real commit/ingestion path (material_routing.py::_route_budget)
    had NO ".xlsx" branch at all -- an XLSX budget committed through
    POST /candidates/{id}/commit fell into the generic text-fallback
    branch, which returns None for a suffix it doesn't recognize, leaving
    the project permanently, silently unrouted.

Both are now fixed by a genuine parse_budget_xlsx() (openpyxl-based). These
tests exercise the parser directly -- no DB, no server, portable to any CI
environment, matching this module's own existing testing convention for
parse_budget_csv/parse_budget_from_text.
"""
from __future__ import annotations

import io

from app.ingestion.budget_parser import parse_budget_xlsx


def _make_xlsx(rows: list[list], header: list[str] | None = None) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header or ["description", "amount", "department"])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_genuine_numeric_cells_parse_exactly_not_via_text_heuristic():
    """A real spreadsheet numeric cell (openpyxl's native int/float type)
    must be read directly as that exact number -- never re-stringified and
    run back through the text-amount heuristic, which exists only for a
    cell that legitimately holds a formatted string like "$1,250,000"."""
    content = _make_xlsx([
        ["1000 PRODUCER FEE", 125_000, "Above the Line"],
        ["2000 CAMERA PACKAGE", 87_500.50, "Production"],
    ])
    result = parse_budget_xlsx(content, filename="budget.xlsx")
    assert result.parse_warnings == []
    assert len(result.line_items) == 2
    assert result.line_items[0].amount_usd == 125_000.0
    assert result.line_items[1].amount_usd == 87_500.50
    assert result.total_budget_raw == 212_500.50


def test_string_formatted_amount_cell_still_parses_via_heuristic():
    """A cell holding a formatted string amount (not a native number) still
    resolves correctly through the same _parse_amount() heuristic
    parse_budget_csv already uses -- the two parsers share amount parsing,
    they differ only in how they read cells vs. CSV rows."""
    content = _make_xlsx([["3000 LOCATION FEES", "$45,000.00", "Production"]])
    result = parse_budget_xlsx(content, filename="budget.xlsx")
    assert result.line_items[0].amount_usd == 45_000.0


def test_xlsx_is_never_decoded_as_text():
    """The real, confirmed-live defect this fix replaces: handing raw XLSX
    bytes to parse_budget_csv's utf-8-sig decode + csv.DictReader is not
    merely wrong output -- reproduced live, it actually raises an
    UNHANDLED csv.Error ("new-line character seen in unquoted field") for
    a real multi-row workbook, which would 500 the whole POST /budgets/
    import request rather than degrade gracefully. Confirm the GENUINE
    parser recovers the real rows correctly, and document that the OLD
    code path is not just imprecise but can crash outright."""
    import pytest

    from app.ingestion.budget_parser import parse_budget_csv

    content = _make_xlsx([
        ["1000 PRODUCER FEE", 125_000, "Above the Line"],
        ["2000 CAMERA PACKAGE", 87_500, "Production"],
        ["3000 LOCATION FEES", 45_000, "Production"],
    ])

    genuine = parse_budget_xlsx(content, filename="budget.xlsx")
    assert len(genuine.line_items) == 3
    assert genuine.total_budget_raw == 257_500.0

    with pytest.raises(Exception):
        parse_budget_csv(content, filename="budget.xlsx")


def test_missing_required_columns_reports_explicitly():
    content = _make_xlsx(
        [["some value", 100]],
        header=["notes", "value"],
    )
    result = parse_budget_xlsx(content, filename="budget.xlsx")
    assert result.line_items == []
    assert result.parse_warnings


def test_empty_worksheet_reports_explicitly():
    import openpyxl

    wb = openpyxl.Workbook()
    buf = io.BytesIO()
    wb.save(buf)
    result = parse_budget_xlsx(buf.getvalue(), filename="budget.xlsx")
    assert result.line_items == []
    assert result.parse_warnings


def test_corrupt_workbook_reports_explicitly_never_crashes():
    result = parse_budget_xlsx(b"not a real xlsx file", filename="budget.xlsx")
    assert result.line_items == []
    assert result.parse_warnings
    assert result.total_budget_raw is None


def test_blank_description_rows_are_skipped_not_counted():
    content = _make_xlsx([
        ["1000 PRODUCER FEE", 50_000, "ATL"],
        [None, 25_000, "ATL"],  # a stray amount with no description -- skip
        ["2000 CAMERA", 30_000, "Production"],
    ])
    result = parse_budget_xlsx(content, filename="budget.xlsx")
    assert len(result.line_items) == 2
    assert result.total_budget_raw == 80_000.0
