"""
budget_parser.py

Parses budget documents (CSV, XLSX, or pre-extracted text) into structured line items.
Step 1: structural parsing (row extraction, amount normalization) — deterministic.
Step 2: LLM extraction pass (optional, for PDF/free-text budgets) — marked as LLM-assisted.
Step 3: classification (calls classify_budget_line_items) — deterministic.

LLM calls are isolated to step 2. Steps 1 and 3 are always deterministic.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.calculators.classify_budget_line_items import classify_line_item


@dataclass
class ParsedLineItem:
    description: str
    department: str | None
    amount_raw: str | None
    amount_usd: float | None
    currency_code: str
    source_row: int | None
    source_page: int | None
    is_llm_extracted: bool = False
    extraction_confidence: float | None = None
    llm_extracted_raw: dict | None = None


@dataclass
class BudgetParseResult:
    filename: str
    currency_code: str
    total_budget_raw: float | None
    origin_note: str | None
    line_items: list[ParsedLineItem]
    parse_warnings: list[str] = field(default_factory=list)
    line_count: int = 0


_AMOUNT_RE = re.compile(r"[\$£€]?\s*([\d,]+(?:\.\d{0,2})?)\s*([KkMm]?)")


def _parse_amount(s: str) -> float | None:
    """Parse a monetary string like '$1,250,000' or '1.25M' or '(150,000)' to float."""
    if not s:
        return None
    s = s.strip()
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    s = s.replace(",", "")
    m = _AMOUNT_RE.search(s)
    if not m:
        return None
    try:
        value = float(m.group(1))
        suffix = (m.group(2) or "").upper()
        if suffix == "K":
            value *= 1_000
        elif suffix == "M":
            value *= 1_000_000
        return -value if negative else value
    except (ValueError, AttributeError):
        return None


def parse_budget_csv(
    content: str | bytes,
    filename: str = "budget.csv",
    currency_code: str = "USD",
    description_col: str = "description",
    amount_col: str = "amount",
    department_col: str | None = "department",
) -> BudgetParseResult:
    """
    Parse a CSV budget file.
    Expects at minimum: description, amount columns.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    items: list[ParsedLineItem] = []
    warnings: list[str] = []

    # Case-insensitive column matching
    fieldnames = [f.lower().strip() for f in (reader.fieldnames or [])]

    def find_col(name: str) -> str | None:
        for f in (reader.fieldnames or []):
            if f.lower().strip() == name.lower():
                return f
        return None

    desc_col = find_col(description_col)
    amt_col = find_col(amount_col)
    dept_col = find_col(department_col) if department_col else None

    if not desc_col or not amt_col:
        warnings.append(f"Could not find required columns '{description_col}'/'{amount_col}'")
        return BudgetParseResult(
            filename=filename,
            currency_code=currency_code,
            total_budget_raw=None,
            origin_note=None,
            line_items=[],
            parse_warnings=warnings,
        )

    total = 0.0
    for row_num, row in enumerate(reader, start=2):
        desc = str(row.get(desc_col, "")).strip()
        amount_str = str(row.get(amt_col, "")).strip()
        dept = str(row.get(dept_col, "")).strip() if dept_col else None

        if not desc:
            continue

        amount = _parse_amount(amount_str)
        if amount is not None:
            total += amount

        items.append(ParsedLineItem(
            description=desc,
            department=dept or None,
            amount_raw=amount_str,
            amount_usd=amount,
            currency_code=currency_code,
            source_row=row_num,
            source_page=None,
        ))

    return BudgetParseResult(
        filename=filename,
        currency_code=currency_code,
        total_budget_raw=total if items else None,
        origin_note=None,
        line_items=items,
        parse_warnings=warnings,
        line_count=len(items),
    )


# ─── Film budget account-number format ────────────────────────────────────────
# Movie Magic / EP-style budgets use one of two account-code conventions:
#   "XX-00" hyphenated (e.g. "10-00")   — _ACCT_CODE_HYPHEN_RE
#   bare 4-digit (e.g. "1000", "8300")  — _ACCT_CODE_BARE_RE
# A single combined pattern drives both the top-sheet and detail-page passes
# so either convention is recognized without a production-specific branch.
_ACCT_CODE_HYPHEN_RE = r"\d{2}-\d{2}"
_ACCT_CODE_BARE_RE = r"\d{4}"
_ACCT_CODE_ANY_RE = re.compile(rf"^({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})$")
_ACCT_CODE_INLINE_RE = re.compile(rf"^({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})\s+(.+)$")
# "Account Total for XX-00" or "Account Total for 1000"
_ACCT_TOTAL_LINE_RE = re.compile(
    rf"^Account Total for ({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})\s*$"
)
# Section sentinels (ATL / BTL) — used to tag department
_ATL_SENTINEL_RE = re.compile(
    r"Total Above.The.Line|Above.The.Line", re.IGNORECASE
)
_BTL_SECTION_RE = re.compile(
    r"Total Production|Total Post Production|Total Other", re.IGNORECASE
)
_GRAND_TOTAL_RE = re.compile(r"^Grand Total\s*$", re.IGNORECASE)

# Lines that must never contribute to parsed spend totals:
# rebate/credit/net-total rows are budget assumptions, not gross spend.
_REBATE_EXCLUSION_RE = re.compile(
    r"edb\s+rebate|tax\s+credit|net\s+total|rebate\s+at\s+\d|incentive\s+rebate"
    r"|credit\s+at\s+\d|tax\s+rebate\s+at|film\s+rebate|incentive\s+line",
    re.IGNORECASE,
)

# Pure group-subtotal / grand-summary sentinel lines on the top sheet — these
# aggregate other accounts already being summed individually and must never
# be registered as their own leaf account (would double-count spend).
_GROUP_SUBTOTAL_RE = re.compile(
    r"^(ABOVE THE LINE|BELOW THE LINE.*|VISUAL EFFECTS|MUSIC"
    r"|Total Above.The.Line|Total Below.The.Line|Total Above and Below.The.Line)\s*$",
    re.IGNORECASE,
)


def _is_film_budget_format(text: str) -> bool:
    """Return True if text looks like a film budget with account codes
    (either hyphenated "XX-00" or bare 4-digit "1000" convention)."""
    has_bare_4digit_topsheet = (
        "Acct#" in text and "Category Description" in text
        and bool(re.search(rf"^{_ACCT_CODE_BARE_RE}$", text, re.MULTILINE))
    )
    return bool(
        re.search(rf"Account Total for ({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})", text)
        or re.search(rf"({_ACCT_CODE_HYPHEN_RE})\s{{2,}}[A-Z]", text)
        or has_bare_4digit_topsheet
    )


def _acct_code_match(line: str) -> re.Match | None:
    """Match a bare account-code line in either convention: 'XX-00' or 4-digit."""
    return _ACCT_CODE_ANY_RE.match(line)


def _acct_code_inline_match(line: str) -> re.Match | None:
    """Match 'CODE  DESCRIPTION' on one line, either convention."""
    return _ACCT_CODE_INLINE_RE.match(line)


def _parse_film_budget(
    pages: list[str],
    filename: str,
    currency_code: str,
) -> BudgetParseResult:
    """
    Parse a film budget PDF whose text was extracted page-by-page. Recognizes
    both Movie Magic account-code conventions: hyphenated "XX-00" and bare
    4-digit ("1000"). Format-specific, not production-specific — no account
    code, description, or amount is ever hard-coded.

    Two passes:
      1. Top-sheet pass (first page(s) with "Acct#" header): extract each
         account's code, description, page reference (provenance), and total.
      2. Detail-page pass (remaining pages): extract "Account Total for CODE"
         lines as the authoritative per-account amounts, overriding the
         top-sheet if present, and capturing the exact PDF page as provenance.

    Group-subtotal / grand-summary sentinel lines (e.g. "ABOVE THE LINE",
    "BELOW THE LINE - PRODUCTION", "Total Below-The-Line") are never
    registered as leaf accounts — they aggregate accounts already counted
    individually and including them would double-count spend. Rebate/credit/
    net-total lines (e.g. "EDB Rebate at 35%", "Net Total") are excluded from
    every pass — they are budget assumptions about the incentive, not spend.

    ATL / BTL grouping is inferred from the account-code range convention
    (a documented Movie Magic Budgeting numbering standard, not tied to any
    one production): 1000s=ATL, 2000-4999=Production, 5000s=Post,
    6000-7999=Other, 8000s=Insurance/Bond/Contingency (top-level, non-BTL).
    """
    acct_totals: dict[str, tuple[str, float, int | None]] = {}  # key -> (desc, amount, page_ref)
    _acct_seen: dict[str, int] = {}  # acct_code -> count (for dedup of shared codes)
    grand_total: float | None = None
    warnings: list[str] = []

    top_sheet_pages = [
        p for p in pages if "Acct#" in p and "Category Description" in p
    ]
    for top_sheet_page in top_sheet_pages:
        lines = [l.strip() for l in top_sheet_page.splitlines() if l.strip()]
        try:
            start = lines.index("Total") + 1  # skip header row tokens
        except ValueError:
            start = 0
        i = start

        def _register(acct: str, desc: str, amt: float, page_ref: int | None) -> None:
            if _REBATE_EXCLUSION_RE.search(desc):
                return  # rebate/credit/net-total — never counted as spend
            n = _acct_seen.get(acct, 0) + 1
            _acct_seen[acct] = n
            key = acct if n == 1 else f"{acct}_{n}"
            acct_totals[key] = (desc, amt, page_ref)

        while i < len(lines):
            line = lines[i]
            # Rebate/credit/net-total lines are budget assumptions — skip entirely
            if _REBATE_EXCLUSION_RE.search(line):
                i += 1
                continue
            m_inline = _acct_code_inline_match(line)
            m_bare = _acct_code_match(line)

            if m_inline:
                acct = m_inline.group(1)
                desc = m_inline.group(2).strip()
                if i + 1 < len(lines):
                    next1 = lines[i + 1]
                    if re.match(r"^\d{1,2}$", next1) and i + 2 < len(lines):
                        page_ref = int(next1)
                        amt = _parse_amount(lines[i + 2])
                        if amt is not None:
                            _register(acct, desc, amt, page_ref)
                        i += 3
                    else:
                        amt = _parse_amount(next1)
                        if amt is not None:
                            _register(acct, desc, amt, None)
                        i += 2
                else:
                    i += 1
            elif m_bare:
                acct = m_bare.group(1)
                if i + 2 < len(lines):
                    desc = lines[i + 1]
                    maybe_page = lines[i + 2]
                    if re.match(r"^\d{1,2}$", maybe_page) and i + 3 < len(lines):
                        page_ref = int(maybe_page)
                        amt = _parse_amount(lines[i + 3])
                        if amt is not None:
                            _register(acct, desc, amt, page_ref)
                        i += 4
                    else:
                        amt = _parse_amount(maybe_page)
                        if amt is not None:
                            _register(acct, desc, amt, None)
                        i += 3
                else:
                    i += 1
            elif _GRAND_TOTAL_RE.match(line):
                if i + 1 < len(lines):
                    grand_total = _parse_amount(lines[i + 1])
                i += 2
            elif _GROUP_SUBTOTAL_RE.match(line):
                # Group-subtotal sentinel (e.g. "ABOVE THE LINE", "BELOW THE
                # LINE - PRODUCTION") — aggregates accounts already counted
                # individually; never registered as its own leaf account.
                i += 1
            else:
                i += 1

    # Pass 2: detail pages — "Account Total for CODE\nAMOUNT" overrides
    # top-sheet, and the enumerated pymupdf page index becomes the account's
    # provenance (the exact PDF page the detail was read from).
    for page_idx, page in enumerate(pages, start=1):
        lines = [l.strip() for l in page.splitlines() if l.strip()]
        for j, line in enumerate(lines):
            if _ACCT_TOTAL_LINE_RE.match(line):
                m = re.search(rf"({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})", line)
                acct = m.group(1)
                if j + 1 < len(lines):
                    amt = _parse_amount(lines[j + 1])
                    if amt is not None and acct in acct_totals:
                        # Update amount + page provenance, keep description
                        desc = acct_totals[acct][0]
                        acct_totals[acct] = (desc, amt, page_idx)
            if _GRAND_TOTAL_RE.match(line) and grand_total is None:
                if j + 1 < len(lines):
                    grand_total = _parse_amount(lines[j + 1])

    if not acct_totals:
        warnings.append("Film budget format detected but no account totals found")
        return BudgetParseResult(
            filename=filename,
            currency_code=currency_code,
            total_budget_raw=None,
            origin_note="film budget — no accounts extracted",
            line_items=[],
            parse_warnings=warnings,
            line_count=0,
        )

    # ATL / BTL assignment: infer from account code ranges (Movie Magic
    # Budgeting numbering convention — general to the format, not this
    # production). Hyphenated "XX-00" codes use the original 10/20/50/60/70
    # tier boundaries; bare 4-digit codes use the 1000/2000/5000/6000/8000
    # tier boundaries evident in this document's own top-sheet groupings
    # (ABOVE THE LINE / BELOW THE LINE - PRODUCTION / - POST / - OTHER).
    def _dept_for_acct(acct: str) -> str:
        if "-" in acct:
            prefix = int(acct.split("-")[0])
            if prefix < 20:
                return "Above The Line"
            if prefix < 50:
                return "Production"
            if prefix < 60:
                return "Post Production"
            if prefix < 70:
                return "Other"
            return "Below The Line"
        prefix = int(acct)
        if prefix < 2000:
            return "Above The Line"
        if prefix < 5000:
            return "Production"
        if prefix < 6000:
            return "Post Production"
        if prefix < 8000:
            return "Other"
        return "Below The Line"

    def _base_acct(key: str) -> str:
        # key may have a dedup suffix like "85-00_2" or "8300_2" — strip it.
        return re.match(rf"({_ACCT_CODE_HYPHEN_RE}|{_ACCT_CODE_BARE_RE})", key).group(1)

    items: list[ParsedLineItem] = []
    for row_num, (key, (desc, amt, page_ref)) in enumerate(sorted(acct_totals.items())):
        base_acct = _base_acct(key)
        items.append(ParsedLineItem(
            description=f"{base_acct} {desc}",
            department=_dept_for_acct(base_acct),
            amount_raw=str(amt),
            amount_usd=amt,
            currency_code=currency_code,
            source_row=row_num,
            source_page=page_ref,
        ))

    computed_total = sum(i.amount_usd for i in items if i.amount_usd)
    return BudgetParseResult(
        filename=filename,
        currency_code=currency_code,
        total_budget_raw=grand_total or computed_total,
        origin_note="parsed from film budget PDF (account-code format)",
        line_items=items,
        parse_warnings=warnings,
        line_count=len(items),
    )


_TEXT_ROW_RE = re.compile(
    r"^(?P<dept>[A-Z][A-Z &/\-]{1,30})?\s*"
    r"(?P<desc>[A-Za-z][A-Za-z0-9 &/()\-,'.]{2,60})\s+"
    r"(?P<amount>[\$£€]?\s*[\d,]+(?:\.\d{0,2})?\s*[KkMm]?)\s*$"
)

_DEPT_HEADER_RE = re.compile(
    r"^(?P<dept>[A-Z][A-Z &/\-]{2,40})\s*$"
)

_TOTAL_KEYWORD_RE = re.compile(
    r"\b(total|subtotal|grand\s+total|budget\s+total)\b",
    re.IGNORECASE,
)


def parse_budget_from_text(
    text: str,
    filename: str = "budget.pdf",
    currency_code: str = "USD",
    pages: list[str] | None = None,
) -> BudgetParseResult:
    """
    Parse budget line items from free-form extracted PDF text.

    Handles common film budget export formats (Movie Magic, AICP, generic
    tabular). Rows are matched heuristically — lines with a recognisable
    monetary amount and a description are captured. Department headers
    (ALL-CAPS labels without an amount) carry forward to subsequent rows.

    No LLM calls. Results may be less complete than CSV parsing; use
    classify_parsed_items() to tag ATL/BTL categories afterwards.

    Automatically detects film-budget account-code format (Movie Magic / EP-style)
    and delegates to _parse_film_budget for accurate extraction.

    `pages`: pass the caller's own per-page text list when available (e.g.
    PDFExtractionResult.pages) so real page boundaries drive top-sheet vs.
    detail-page detection. Without it, page breaks are guessed by splitting
    `text` on form-feed (\\x0c) — which pymupdf-based extraction does NOT
    emit (it joins pages with "\\n\\n"), so that fallback degrades to
    treating the entire document as one page. For any multi-page film
    budget, passing `pages` is required for correct account-total scoping —
    without real page boundaries, every subaccount code on every detail
    page gets scanned as if it were a top-sheet row.
    """
    # Prefer the caller's real per-page list; \x0c-splitting is a fallback
    # only for callers that never had page boundaries to begin with.
    pages = pages if pages is not None else text.split("\x0c")

    # Dispatch to specialized parser for account-code film budgets
    if _is_film_budget_format(text):
        return _parse_film_budget(pages, filename, currency_code)

    items: list[ParsedLineItem] = []
    warnings: list[str] = []
    current_dept: str | None = None
    total_budget: float | None = None
    row_num = 0

    for page_num, page_text in enumerate(pages, start=1):
        for line in page_text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Skip rebate/credit/net-total lines — budget assumptions, not gross spend
            if _REBATE_EXCLUSION_RE.search(line):
                continue

            # Detect total-budget sentinel lines (skip, capture value if present)
            if _TOTAL_KEYWORD_RE.search(line):
                amt = _parse_amount_from_line(line)
                if amt is not None and total_budget is None:
                    total_budget = amt
                continue

            # Detect ALL-CAPS department headers (no amount on the line)
            if _DEPT_HEADER_RE.match(line) and _parse_amount_from_line(line) is None:
                current_dept = line.strip().title()
                continue

            # Try to parse a line that contains at least a description + amount
            parsed = _parse_text_line(line, row_num, page_num, current_dept, currency_code)
            if parsed is not None:
                items.append(parsed)
                row_num += 1

    if not items:
        warnings.append(
            "No line items could be parsed from text — format may require manual review"
        )

    computed_total = sum(i.amount_usd for i in items if i.amount_usd is not None)

    return BudgetParseResult(
        filename=filename,
        currency_code=currency_code,
        total_budget_raw=total_budget or (computed_total if items else None),
        origin_note="parsed from PDF text",
        line_items=items,
        parse_warnings=warnings,
        line_count=len(items),
    )


def _parse_amount_from_line(line: str) -> float | None:
    """Return the first parseable monetary amount found anywhere in the line."""
    # Match amounts like $1,250,000 or 1,250,000.00 or 1.25M
    m = re.search(
        r"[\$£€]?\s*([\d,]{1,15}(?:\.\d{0,2})?)\s*([KkMm]?)\b",
        line,
    )
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        value = float(raw)
    except ValueError:
        return None
    suffix = (m.group(2) or "").upper()
    if suffix == "K":
        value *= 1_000
    elif suffix == "M":
        value *= 1_000_000
    # Ignore suspiciously small numbers (page numbers, line numbers)
    if value < 10:
        return None
    return value


def _parse_text_line(
    line: str,
    row_num: int,
    page_num: int,
    current_dept: str | None,
    currency_code: str,
) -> ParsedLineItem | None:
    """
    Attempt to extract a (description, amount) pair from one text line.
    Returns None if the line doesn't look like a budget row.
    """
    amount = _parse_amount_from_line(line)
    if amount is None:
        return None

    # Remove the amount portion to get the description remainder
    desc = re.sub(
        r"[\$£€]?\s*[\d,]{1,15}(?:\.\d{0,2})?\s*[KkMm]?\b",
        "",
        line,
    ).strip(" \t|,-")

    # Heuristic: description must be at least 3 chars and not purely numeric
    if len(desc) < 3 or re.match(r"^\d+$", desc):
        return None

    return ParsedLineItem(
        description=desc,
        department=current_dept,
        amount_raw=line,
        amount_usd=amount,
        currency_code=currency_code,
        source_row=row_num,
        source_page=page_num,
    )


def classify_parsed_items(result: BudgetParseResult) -> BudgetParseResult:
    """
    Run deterministic classification on all parsed line items.
    Returns a new result with classification fields populated.
    """
    for item in result.line_items:
        cls = classify_line_item(item.description, item.department)
        # Attach classification results as dynamic attributes for downstream use
        item.__dict__.update({
            "atl_btl": cls.atl_btl.value,
            "spend_category": cls.spend_category.value,
            "is_fixed": cls.is_fixed,
            "is_labor": cls.is_labor,
            "compensation_type": cls.compensation_type.value,
            "classification_rule": cls.rule_matched,
        })
    return result
