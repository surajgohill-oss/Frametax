"""
test_movie_magic_budget_parser.py

Targeted tests for the real Movie Magic Budgeting 4-digit account-code
format (as opposed to the pre-existing "XX-00" hyphenated convention
_parse_film_budget already covered). Synthetic fixtures mirror the exact
structure discovered in the real Little Utopia budget PDF: a top-sheet
summary (Acct# / Category Description / Page / Orig / Total / Var) plus
detail pages carrying "Account Total for CODE" lines and per-line-item
rate/unit arithmetic underneath each account.

No real PDF file is required for these — the fixtures are format-
representative synthetic text, portable to any CI environment. A
separate, conditionally-skipped test locks in the specific real-file
reconciliation finding (a $2 source-document rounding variance) for
local verification when the actual downloaded PDF is present.
"""
from __future__ import annotations

import os

import pytest

from app.ingestion.budget_parser import (
    _is_film_budget_format,
    parse_budget_from_text,
)


def _pages(*page_texts: str) -> list[str]:
    return list(page_texts)


# A minimal but structurally faithful two-account top sheet + two detail
# pages, mirroring the real document's exact line-by-line layout.
_TOP_SHEET = """Acct#
Category Description
Page
Orig
Total
Var
1000
DEVELOPMENT
1
$0
$0
$0
1100
SCRIPT
1
$5,050
$5,050
$0
1400
CAST
2
$136,115
$136,115
$0
ABOVE THE LINE
$141,165
$141,165
$0
2000
PRODUCTION STAFF
8
$321,594
$321,594
$0
BELOW THE LINE - PRODUCTION
$321,594
$321,594
$0
8100
Insurance : 1.2%
$5,489
$5,489
$0
Total Above-The-Line
$141,165
$141,165
$0
Total Below-The-Line
$321,594
$321,594
$0
Grand Total
$468,248
$468,248
$0
9001
EDB Rebate at 35%
$(163,887) $(163,887)
$0
Net Total
$304,361
$304,361
$0
"""

_DETAIL_PAGE_1 = """Acct#
Description
Amt
Units
X
Rate
Sub T
Orig
Total
Var
1000  DEVELOPMENT
1001
DEVELOPMENT COSTS
Development Costs
Subtotal
$0
Total
$0
$0
$0
1099
Total Fringes
$0
$0
$0
Account Total for 1000
$0
$0
1100  SCRIPT
1101
WRITERS
WRITER
Subtotal
$5,050
Total
$5,050
$5,050
$0
1199
Total Fringes
$0
$0
$0
Account Total for 1100
$5,050
$0
Jun 3, 2025                                                                                  Page 1
"""

_DETAIL_PAGE_2 = """Acct#
Description
Amt
Units
X
Rate
Sub T
Orig
Total
Var
1400  CAST
1401
PRINCIPAL PLAYERS
Weekly fee buyout
CAST: FRANK
Global Deal
Subtotal
$136,115
Total
$136,115
$136,115
$0
1499
Total Fringes
$0
$0
$0
Account Total for 1400
$136,115
$0
Jun 3, 2025                                                                                  Page 2
"""

_DETAIL_PAGE_3 = """Acct#
Description
Amt
Units
X
Rate
Sub T
Orig
Total
Var
2000  PRODUCTION STAFF
2001
PRODUCTION MANAGER
Production Manager
Prep
7 Wee...
1
0
0
Subtotal
$321,594
Total
$321,594
$321,594
$0
2099
Total Fringes
$0
$0
$0
Account Total for 2000
$321,594
$0
Jun 3, 2025                                                                                  Page 3
"""


def _full_text_and_pages() -> tuple[str, list[str]]:
    pages = _pages(_TOP_SHEET, _DETAIL_PAGE_1, _DETAIL_PAGE_2, _DETAIL_PAGE_3)
    return "\n\n".join(pages), pages


class TestFourDigitFormatDetection:
    def test_bare_4digit_topsheet_detected(self):
        text, _ = _full_text_and_pages()
        assert _is_film_budget_format(text) is True

    def test_non_budget_text_not_detected(self):
        assert _is_film_budget_format("Just a regular document with a year 2025 in it.") is False

    def test_lone_4digit_number_without_topsheet_markers_not_detected(self):
        """A bare 4-digit number (e.g. a year) alone must not trigger
        film-budget detection without the Acct#/Category Description
        top-sheet markers — otherwise any document mentioning a year on
        its own line would be misdetected."""
        assert _is_film_budget_format("Meeting notes\n2025\nEnd of notes") is False


class TestFourDigitAccountRecognition:
    def test_all_leaf_accounts_recognized(self):
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        codes = {li.description.split()[0] for li in result.line_items}
        assert codes == {"1000", "1100", "1400", "2000", "8100"}

    def test_account_names_preserved(self):
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        by_code = {li.description.split()[0]: li.description for li in result.line_items}
        assert "SCRIPT" in by_code["1100"]
        assert "CAST" in by_code["1400"]

    def test_detail_page_overrides_amount_and_page_provenance(self):
        """Account Total for CODE on a detail page must override the
        top-sheet amount and record the real pymupdf page index."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        by_code = {li.description.split()[0]: li for li in result.line_items}
        assert by_code["1100"].amount_usd == 5_050.0
        assert by_code["1100"].source_page == 2  # detail page 2 (0-indexed pages[1] -> enumerate start=1)
        assert by_code["2000"].source_page == 4


class TestNumericTokenMisreadPrevention:
    def test_page_number_never_becomes_amount(self):
        """The bare '1' / '2' page-reference tokens on the top sheet must
        never be captured as a dollar amount."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        amounts = [li.amount_usd for li in result.line_items]
        assert 1.0 not in amounts
        assert 2.0 not in amounts

    def test_percentage_label_amount_still_captured_correctly(self):
        """'Insurance : 1.2%' must not have its percentage misread as the
        amount — the actual dollar figure ($5,489) must be captured."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        by_code = {li.description.split()[0]: li for li in result.line_items}
        assert by_code["8100"].amount_usd == 5_489.0

    def test_subaccount_codes_never_become_leaf_accounts(self):
        """1001, 1099, 1101, 1199, etc. (detail-page subaccounts and fringe
        lines) must never appear as their own top-level parsed accounts —
        only the 4 real top-sheet accounts (1000/1100/1400/2000) plus 8100."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        codes = {li.description.split()[0] for li in result.line_items}
        assert "1001" not in codes
        assert "1099" not in codes
        assert "1101" not in codes
        assert "2001" not in codes
        assert len(result.line_items) == 5  # exactly the 5 real accounts, no phantoms


class TestRebateAndGroupSubtotalExclusion:
    def test_rebate_line_excluded(self):
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        codes = {li.description.split()[0] for li in result.line_items}
        assert "9001" not in codes

    def test_rebate_amount_never_summed(self):
        """A rebate is a negative/credit line — if it leaked in, it would
        corrupt the gross total by over $150K in this fixture."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        total = sum(li.amount_usd for li in result.line_items)
        assert total == pytest.approx(468_248.0, abs=0.01)

    def test_group_subtotal_lines_not_double_counted(self):
        """'ABOVE THE LINE', 'BELOW THE LINE - PRODUCTION', 'Total
        Above-The-Line', 'Total Below-The-Line', 'Grand Total' must never
        appear as their own leaf accounts."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        descriptions = " ".join(li.description for li in result.line_items)
        for forbidden in ("ABOVE THE LINE", "BELOW THE LINE - PRODUCTION",
                           "Total Above-The-Line", "Total Below-The-Line", "Grand Total"):
            assert forbidden not in descriptions


class TestTaxIncentiveNettingLineExclusion:
    """Fresh Project Economic Fidelity: a producer's own projected-
    incentive netting line (e.g. "9998 - Tax Incentive 25%* BTL (No
    Disc)" ahead of a stated "Net total") is the same self-referential
    rebate-assumption category as "EDB Rebate at 35%"/"tax credit" —
    never real spend, must never enter QPE/allocation as a negative BTL
    account. Real regression: Lips Like Sugar's actual source budget
    carries exactly this line, previously mis-parsed as spend and
    subtracted from every candidate jurisdiction's QPE."""

    def _text_and_pages(self):
        top_sheet = _TOP_SHEET.replace(
            "9001\nEDB Rebate at 35%",
            "9998\nTax Incentive 25%* BTL  (No Disc)",
        )
        assert "9998" in top_sheet and "9001" not in top_sheet
        pages = _pages(top_sheet, _DETAIL_PAGE_1, _DETAIL_PAGE_2, _DETAIL_PAGE_3)
        return "\n\n".join(pages), pages

    def test_tax_incentive_netting_line_excluded(self):
        text, pages = self._text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        codes = {li.description.split()[0] for li in result.line_items}
        assert "9998" not in codes

    def test_tax_incentive_netting_amount_never_summed(self):
        text, pages = self._text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        total = sum(li.amount_usd for li in result.line_items)
        assert total == pytest.approx(468_248.0, abs=0.01)


class TestExactReconciliation:
    def test_clean_synthetic_budget_reconciles_exactly(self):
        """When the source data has no internal rounding inconsistency,
        the parser's computed sum must equal the document's own stated
        Grand Total exactly."""
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        computed = sum(li.amount_usd for li in result.line_items)
        assert computed == result.total_budget_raw == 468_248.0

    def test_grand_total_captured_from_document_text(self):
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        assert result.total_budget_raw == 468_248.0


class TestPageBoundaryFix:
    """Regression test for the pre-existing bug: parse_budget_from_text's
    \\x0c-split fallback never matches pymupdf's "\\n\\n"-joined page text,
    collapsing a multi-page document into one giant "page" and causing
    every detail-page subaccount code to be scanned as a top-sheet row."""

    def test_without_pages_param_falls_back_to_single_page_and_misparses(self):
        text, _ = _full_text_and_pages()
        # No pages= passed -> \x0c split degenerates to one page since
        # pymupdf-style text never contains real form-feed characters.
        result = parse_budget_from_text(text, filename="test.pdf")
        codes = {li.description.split()[0] for li in result.line_items}
        # Without real page boundaries, subaccount codes like 1001/2001
        # leak in as phantom top-level accounts.
        assert "1001" in codes or "2001" in codes or len(result.line_items) > 5

    def test_with_pages_param_parses_correctly(self):
        text, pages = _full_text_and_pages()
        result = parse_budget_from_text(text, filename="test.pdf", pages=pages)
        assert len(result.line_items) == 5


class TestRealLittleUtopiaBudgetPDF:
    """Locks in the exact, precisely-diagnosed reconciliation finding
    against the real production PDF when it is present locally. Skipped
    everywhere else (the file is not part of the repository)."""

    PDF_PATH = os.path.expanduser(
        "~/Downloads/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf"
    )

    @pytest.mark.skipif(not os.path.exists(PDF_PATH), reason="real budget PDF not present locally")
    def test_real_budget_reconciliation_variance_is_exactly_two_dollars(self):
        """Documented, dual-source-corroborated finding: the source PDF's
        own 'BELOW THE LINE - PRODUCTION' and 'Total Above and Below-The-
        Line' subtotal lines are each $1 short of the sum of their own
        constituent leaf accounts (independent per-account rounding in
        the source spreadsheet, not a parser defect) — total $2 variance
        against the stated $4,364,393 Grand Total. This test intentionally
        asserts the variance, not exact equality — per instruction, no
        balancing entry may be fabricated to force reconciliation."""
        from app.ingestion.pdf_extractor import extract_text_from_pdf

        ex = extract_text_from_pdf(self.PDF_PATH)
        result = parse_budget_from_text(ex.raw_text, filename=ex.filename, pages=ex.pages)

        assert len(result.line_items) == 44
        computed = sum(li.amount_usd for li in result.line_items)
        assert result.total_budget_raw == 4_364_393.0  # document's own stated Grand Total
        assert computed == 4_364_395.0  # sum of the 44 leaf accounts as printed
        assert computed - result.total_budget_raw == 2.0  # the unresolved source-document variance
