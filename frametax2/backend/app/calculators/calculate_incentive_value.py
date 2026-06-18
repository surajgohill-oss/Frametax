"""
calculate_incentive_value.py

Deterministically computes the economic value of a single incentive program
given qualifying spend, the program's base rate, uplifts, and program type.

No LLM calls. All math is explicit and traceable.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import ProgramType

ENGINE_VERSION = "0.1.0"


@dataclass
class IncentiveValueResult:
    program_id: str
    program_slug: str
    program_type: str
    qualifying_spend_usd: float
    base_rate: float
    base_credit_usd: float
    uplifts_applied: list[dict]      # [{name, rate, basis_usd, credit_usd}]
    total_credit_usd: float
    effective_rate: float
    is_refundable: bool | None
    is_transferable: bool | None
    transferable_value_pct: float | None
    economic_value_usd: float        # cash economic value after transfer discount
    cap_applied: bool
    cap_limit_usd: float | None
    notes: list[str]
    engine_version: str = ENGINE_VERSION


def calculate_incentive_value(
    qualifying_spend_usd: float,
    program: dict,
    uplifts: list[dict],
    production_details: dict | None = None,
    vfx_spend_usd: float = 0.0,
    music_spend_usd: float = 0.0,
    annual_cap_usd: float | None = None,
) -> IncentiveValueResult:
    """
    program: IncentiveProgram-shaped dict
    uplifts: list of ProgramUplift-shaped dicts
    production_details: dict for evaluating uplift conditions
    """
    production_details = production_details or {}
    notes: list[str] = []

    base_rate = float(program.get("base_rate") or 0.0)
    base_credit = qualifying_spend_usd * base_rate

    # Apply uplifts
    uplifts_applied: list[dict] = []
    uplift_total = 0.0

    for uplift in uplifts:
        additional_rate = float(uplift.get("additional_rate") or 0.0)
        applies_to = uplift.get("applies_to", "same_qualifying_spend")
        condition_type = uplift.get("condition_type", "")
        condition_threshold = uplift.get("condition_threshold")
        condition_text = uplift.get("condition_text", "")

        # Check if condition is met
        condition_met = _evaluate_uplift_condition(
            condition_type=condition_type,
            condition_threshold=condition_threshold,
            condition_text=condition_text,
            production_details=production_details,
        )

        if not condition_met:
            continue

        # Determine basis for uplift
        if applies_to == "vfx_spend_only":
            basis = vfx_spend_usd
        elif applies_to == "music_spend_only":
            basis = music_spend_usd
        else:
            basis = qualifying_spend_usd

        credit_usd = basis * additional_rate
        uplift_total += credit_usd

        uplifts_applied.append({
            "name": uplift.get("name", "Uplift"),
            "rate": additional_rate,
            "basis_usd": basis,
            "credit_usd": credit_usd,
            "condition_type": condition_type,
        })

    total_credit = base_credit + uplift_total

    # Apply annual cap
    cap_applied = False
    cap_limit = annual_cap_usd
    if cap_limit is not None and total_credit > cap_limit:
        total_credit = cap_limit
        cap_applied = True
        notes.append(f"Credit capped at program annual limit ${cap_limit:,.0f}")

    effective_rate = total_credit / qualifying_spend_usd if qualifying_spend_usd > 0 else 0.0

    # Compute economic value (accounts for transfer discount on non-refundable transferable credits)
    is_refundable = program.get("is_refundable")
    is_transferable = program.get("is_transferable")
    transferable_pct = float(program.get("transferable_value_pct") or 1.0)

    if is_refundable:
        economic_value = total_credit  # Full cash value
    elif is_transferable:
        economic_value = total_credit * transferable_pct
        if transferable_pct < 1.0:
            notes.append(
                f"Non-refundable credit transferred at {transferable_pct:.0%} — "
                f"economic value ${economic_value:,.0f}"
            )
    else:
        economic_value = total_credit  # Used against tax liability (assume usable)
        notes.append("Non-refundable, non-transferable credit — assumes tax liability sufficient")

    if program.get("is_competitive"):
        notes.append(
            "WARNING: This program has competitive allocation — "
            "credit is not guaranteed even if qualified"
        )

    return IncentiveValueResult(
        program_id=str(program.get("id", "")),
        program_slug=program.get("slug", ""),
        program_type=program.get("program_type", ""),
        qualifying_spend_usd=qualifying_spend_usd,
        base_rate=base_rate,
        base_credit_usd=base_credit,
        uplifts_applied=uplifts_applied,
        total_credit_usd=total_credit,
        effective_rate=effective_rate,
        is_refundable=is_refundable,
        is_transferable=is_transferable,
        transferable_value_pct=float(program.get("transferable_value_pct") or 1.0),
        economic_value_usd=economic_value,
        cap_applied=cap_applied,
        cap_limit_usd=cap_limit,
        notes=notes,
    )


def _evaluate_uplift_condition(
    condition_type: str,
    condition_threshold: float | None,
    condition_text: str,
    production_details: dict,
) -> bool:
    """Evaluate whether an uplift condition is satisfied."""
    if condition_type == "uses_logo":
        return bool(production_details.get("uses_georgia_logo"))
    if condition_type == "shooting_location":
        return production_details.get("shooting_location", "") == condition_text
    if condition_type == "spend_category_pct":
        key = condition_text or "vfx_pct"
        val = float(production_details.get(key) or 0.0)
        return val >= float(condition_threshold or 0.0)
    if condition_type == "labor_pct":
        val = float(production_details.get("local_labor_pct") or 0.0)
        return val >= float(condition_threshold or 0.0)
    if condition_type == "budget_under":
        total = float(production_details.get("total_budget_usd") or 0.0)
        return total <= float(condition_threshold or 0.0)
    if condition_type == "is_independent":
        return bool(production_details.get("is_independent_film"))
    # Default: treat as true if no specific evaluation defined
    return True
