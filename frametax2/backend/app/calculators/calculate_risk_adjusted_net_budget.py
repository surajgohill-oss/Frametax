"""
calculate_risk_adjusted_net_budget.py

Applies risk discounts to the true net budget based on:
- confidence tier of program rules (DISCOVERY = high risk)
- is_competitive flag (CA-style programs may not allocate)
- qualification gaps (partial qualification)
- unverified BTL rate multipliers
- currency risk exposure

Returns a risk-adjusted net budget for conservative comparison.
"""
from __future__ import annotations

from dataclasses import dataclass

ENGINE_VERSION = "0.1.0"

# Risk discount factors by confidence tier
RISK_DISCOUNTS = {
    "VERIFIED": 0.0,      # No discount
    "PARSED": 0.08,        # 8% discount on incentive value
    "DISCOVERY": 0.25,    # 25% discount — rules may be wrong
}

COMPETITIVE_DISCOUNT = 0.30   # 30% discount if program is competitive
PARTIAL_QUAL_DISCOUNT = 0.40  # 40% discount if major qualification gap flagged


@dataclass
class RiskAdjustedResult:
    true_net_cost_usd: float
    risk_adjusted_net_cost_usd: float
    risk_adjustments: list[dict]   # [{factor, description, reduction_usd}]
    overall_risk_level: str        # "low" | "medium" | "high"
    engine_version: str = ENGINE_VERSION


def calculate_risk_adjusted_net(
    true_net_cost_usd: float,
    total_incentive_value_usd: float,
    program_results: list[dict],
    has_qualification_gaps: bool = False,
    btl_rates_confidence: str = "DISCOVERY",
) -> RiskAdjustedResult:
    """
    program_results: list of calculate_incentive_value output dicts, each with:
        {program_id, total_credit_usd, confidence_tier, is_competitive}
    """
    adjustments: list[dict] = []
    risk_reduction = 0.0

    for prog in program_results:
        credit = float(prog.get("total_credit_usd") or 0.0)
        confidence = prog.get("confidence_tier", "DISCOVERY")
        is_competitive = bool(prog.get("is_competitive", False))
        slug = prog.get("program_slug", prog.get("program_id", "unknown"))

        discount = RISK_DISCOUNTS.get(confidence, RISK_DISCOUNTS["DISCOVERY"])

        if is_competitive:
            discount = max(discount, COMPETITIVE_DISCOUNT)
            adjustments.append({
                "factor": "competitive_program",
                "description": f"{slug}: competitive allocation — credit not guaranteed",
                "reduction_usd": credit * COMPETITIVE_DISCOUNT,
            })

        if discount > 0:
            reduction = credit * discount
            risk_reduction += reduction
            if not is_competitive:
                adjustments.append({
                    "factor": f"confidence_{confidence.lower()}",
                    "description": f"{slug}: {confidence} tier — {discount:.0%} risk discount applied",
                    "reduction_usd": reduction,
                })

    if has_qualification_gaps:
        gap_reduction = total_incentive_value_usd * PARTIAL_QUAL_DISCOUNT
        risk_reduction += gap_reduction
        adjustments.append({
            "factor": "qualification_gaps",
            "description": "One or more qualification gaps flagged — partial qualification risk",
            "reduction_usd": gap_reduction,
        })

    risk_adjusted_net = true_net_cost_usd + risk_reduction

    # Assess overall risk level
    if risk_reduction == 0:
        risk_level = "low"
    elif risk_reduction < total_incentive_value_usd * 0.15:
        risk_level = "medium"
    else:
        risk_level = "high"

    return RiskAdjustedResult(
        true_net_cost_usd=true_net_cost_usd,
        risk_adjusted_net_cost_usd=risk_adjusted_net,
        risk_adjustments=adjustments,
        overall_risk_level=risk_level,
    )
