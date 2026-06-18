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
    """Parse a monetary string like '$1,250,000' or '1.25M' to float."""
    if not s:
        return None
    s = s.strip().replace(",", "")
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
        return value
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
