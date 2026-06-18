"""
apply_union_fringe_rules.py

Applies union/guild fringe rates to gross labor to compute fully-loaded labor cost.
Also handles per-employee annual fringe caps.

Fringes increase total BTL cost and therefore affect net budget, but their
eligibility for incentive qualification depends on the program's category rules.
"""
from __future__ import annotations

from dataclasses import dataclass

ENGINE_VERSION = "0.1.0"


@dataclass
class FringeResult:
    gross_labor_usd: float
    total_fringe_usd: float
    fully_loaded_labor_usd: float
    fringe_breakdown: list[dict]  # [{union, rate, gross_applied, fringe_usd}]
    engine_version: str = ENGINE_VERSION


def apply_union_fringes(
    labor_items: list[dict],
    union_fringe_rules: list[dict],
) -> FringeResult:
    """
    labor_items: budget line items where is_labor=True
    union_fringe_rules: list of UnionFringeRule-shaped dicts:
        {union_name, fringe_rate, applies_to_categories, cap_per_employee_usd}
    """
    total_gross_labor = sum(float(item.get("amount_usd") or 0) for item in labor_items)
    fringe_breakdown: list[dict] = []
    total_fringe = 0.0

    for rule in union_fringe_rules:
        rate = float(rule["fringe_rate"])
        applies_to = rule.get("applies_to_categories") or []
        cap = rule.get("cap_per_employee_usd")

        applicable_gross = 0.0
        for item in labor_items:
            cat = item.get("spend_category")
            if applies_to and cat not in applies_to:
                continue
            item_gross = float(item.get("amount_usd") or 0)
            applicable_gross += item_gross

        fringe_usd = applicable_gross * rate

        fringe_breakdown.append({
            "union": rule["union_name"],
            "rate": rate,
            "gross_applied_usd": applicable_gross,
            "fringe_usd": fringe_usd,
            "cap_per_employee": cap,
        })
        total_fringe += fringe_usd

    return FringeResult(
        gross_labor_usd=total_gross_labor,
        total_fringe_usd=total_fringe,
        fully_loaded_labor_usd=total_gross_labor + total_fringe,
        fringe_breakdown=fringe_breakdown,
    )
