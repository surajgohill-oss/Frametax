"""
apply_caps_floors_exclusions.py

Applies program-level caps, ATL caps, per-person caps, and other exclusion rules.
Called after calculate_qualified_spend, before calculate_incentive_value.
"""
from __future__ import annotations

from dataclasses import dataclass

ENGINE_VERSION = "0.1.0"


@dataclass
class CapsResult:
    input_qualifying_spend_usd: float
    adjusted_qualifying_spend_usd: float
    adjustments: list[dict]  # [{type, description, reduction_usd}]
    engine_version: str = ENGINE_VERSION


def apply_caps_and_exclusions(
    qualifying_spend_usd: float,
    total_budget_usd: float,
    atl_spend_usd: float,
    atl_cap_pct: float | None = None,
    individual_salary_cap_usd: float | None = None,
    individual_high_earners: list[dict] | None = None,
    program_annual_cap_usd: float | None = None,
) -> CapsResult:
    """
    Apply all caps in order:
    1. ATL cap (e.g. max % of budget that ATL can represent in qualifying spend)
    2. Individual salary caps (excess over cap excluded)
    3. Program annual cap

    Returns adjusted qualifying spend and trace of each adjustment.
    """
    adjustments: list[dict] = []
    current = float(qualifying_spend_usd)

    # 1. ATL cap
    if atl_cap_pct is not None and total_budget_usd > 0:
        max_atl_qualifying = total_budget_usd * atl_cap_pct
        if atl_spend_usd > max_atl_qualifying:
            excess = atl_spend_usd - max_atl_qualifying
            current -= excess
            adjustments.append({
                "type": "atl_cap",
                "description": f"ATL capped at {atl_cap_pct:.0%} of total budget",
                "reduction_usd": excess,
            })

    # 2. Individual salary caps
    if individual_salary_cap_usd and individual_high_earners:
        for person in individual_high_earners:
            salary = float(person.get("amount_usd", 0))
            if salary > individual_salary_cap_usd:
                excess = salary - individual_salary_cap_usd
                current -= excess
                adjustments.append({
                    "type": "individual_salary_cap",
                    "description": f"{person.get('name', 'Individual')} salary capped at ${individual_salary_cap_usd:,.0f}",
                    "reduction_usd": excess,
                })

    # 3. Program annual cap
    if program_annual_cap_usd is not None and current > program_annual_cap_usd:
        excess = current - program_annual_cap_usd
        adjustments.append({
            "type": "program_annual_cap",
            "description": f"Program annual cap ${program_annual_cap_usd:,.0f} applied",
            "reduction_usd": excess,
        })
        current = program_annual_cap_usd

    current = max(current, 0.0)

    return CapsResult(
        input_qualifying_spend_usd=qualifying_spend_usd,
        adjusted_qualifying_spend_usd=current,
        adjustments=adjustments,
    )
