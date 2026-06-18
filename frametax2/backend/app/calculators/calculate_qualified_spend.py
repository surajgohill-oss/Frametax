"""
calculate_qualified_spend.py

Deterministically computes qualifying spend for a program given:
- classified budget line items
- qualifying_spend_categories rules for the program
- jurisdiction_spend_pct (user-provided assumption: what fraction of budget is spent in jurisdiction)
- any program-level spend caps (e.g. UK 80% cap)

Returns a trace-ready breakdown by category.
"""
from __future__ import annotations

from dataclasses import dataclass, field

ENGINE_VERSION = "0.1.0"


@dataclass
class QualifyingSpendResult:
    program_id: str
    program_slug: str
    total_qualifying_usd: float
    total_qualifying_capped_usd: float   # after any program cap
    cap_applied: bool
    cap_description: str | None
    category_breakdown: dict[str, float]  # spend_category -> qualifying USD
    excluded_categories: dict[str, float]  # spend_category -> excluded USD (with reason)
    jurisdiction_spend_pct_assumed: float
    engine_version: str = ENGINE_VERSION


def calculate_qualified_spend(
    line_items: list[dict],
    qualifying_categories: list[dict],
    jurisdiction_spend_pct: float,
    program_id: str,
    program_slug: str,
    spend_cap_pct: float | None = None,
    total_budget_usd: float | None = None,
) -> QualifyingSpendResult:
    """
    line_items: classified budget line items (output of classify_budget_line_items)
    qualifying_categories: list of QualifyingSpendCategory-shaped dicts:
        {spend_category, qualifies, jurisdiction_spend_only}
    jurisdiction_spend_pct: fraction of budget assumed to be spent IN jurisdiction (0.0-1.0)
    spend_cap_pct: optional cap as % of total_budget (e.g. 0.80 for UK 80% rule)
    """
    if not (0.0 <= jurisdiction_spend_pct <= 1.0):
        raise ValueError(f"jurisdiction_spend_pct must be 0.0-1.0, got {jurisdiction_spend_pct}")

    # Build lookup: category -> (qualifies, jurisdiction_spend_only)
    cat_rules: dict[str, tuple[bool, bool]] = {}
    for cat in qualifying_categories:
        cat_rules[cat["spend_category"]] = (
            bool(cat["qualifies"]),
            bool(cat.get("jurisdiction_spend_only", True)),
        )

    category_breakdown: dict[str, float] = {}
    excluded_categories: dict[str, float] = {}
    total_qualifying = 0.0

    for item in line_items:
        spend_cat = item.get("spend_category")
        amount_usd = float(item.get("amount_usd") or item.get("cash_amount_usd") or 0.0)
        if amount_usd <= 0 or not spend_cat:
            continue

        qualifies, jurisdiction_only = cat_rules.get(spend_cat, (False, True))

        if not qualifies:
            excluded_categories[spend_cat] = excluded_categories.get(spend_cat, 0.0) + amount_usd
            continue

        if jurisdiction_only:
            qualifying_amount = amount_usd * jurisdiction_spend_pct
        else:
            qualifying_amount = amount_usd

        category_breakdown[spend_cat] = category_breakdown.get(spend_cat, 0.0) + qualifying_amount
        total_qualifying += qualifying_amount

    # Apply program-level spend cap
    cap_applied = False
    cap_description = None
    total_qualifying_capped = total_qualifying

    if spend_cap_pct is not None and total_budget_usd is not None and total_budget_usd > 0:
        max_qualifying = total_budget_usd * spend_cap_pct
        if total_qualifying > max_qualifying:
            total_qualifying_capped = max_qualifying
            cap_applied = True
            cap_description = (
                f"Program cap: qualifying spend capped at {spend_cap_pct:.0%} "
                f"of total budget (${max_qualifying:,.0f})"
            )

    return QualifyingSpendResult(
        program_id=program_id,
        program_slug=program_slug,
        total_qualifying_usd=total_qualifying,
        total_qualifying_capped_usd=total_qualifying_capped,
        cap_applied=cap_applied,
        cap_description=cap_description,
        category_breakdown=category_breakdown,
        excluded_categories=excluded_categories,
        jurisdiction_spend_pct_assumed=jurisdiction_spend_pct,
    )
