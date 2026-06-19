"""
apply_stacking_adjustments.py

Applies stacking interaction rules to a set of computed incentive results.

Supported rule types:
  spend_reduction   — a grant reduces the qualifying spend basis of a downstream credit
  value_cap         — combined value of two programs may not exceed a stated cap
  mutually_exclusive — only the higher-value program can be claimed; lower is zeroed
  conditional       — legal review required; no automatic value adjustment
  allowed           — programs combine without restriction; no adjustment

No LLM calls. All math is deterministic and traceable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ENGINE_VERSION = "0.1.0"

_GRANT_TYPES = {"grant", "regional_fund", "discretionary_fund"}


@dataclass
class StackingAdjustment:
    program_a_id: str
    program_b_id: str
    rule_type: str
    description: str
    original_value_usd: float
    adjustment_usd: float        # negative = reduction
    adjusted_value_usd: float


@dataclass
class StackingAdjustmentResult:
    program_values: dict[str, float]   # program_id → post-adjustment economic value
    raw_values: dict[str, float]       # program_id → pre-adjustment economic value
    adjustments: list[StackingAdjustment]
    total_raw_value_usd: float
    total_adjusted_value_usd: float
    legal_review_flags: list[str]
    engine_version: str = ENGINE_VERSION


def apply_stacking_adjustments(
    incentive_results: list[dict[str, Any]],
    stacking_rules: list[dict[str, Any]],
) -> StackingAdjustmentResult:
    """
    Apply stacking interaction rules to a set of computed incentive results.

    incentive_results: list of IncentiveValueResult.__dict__ copies, each with:
        program_id, economic_value_usd, effective_rate, program_type,
        qualifying_spend_usd
    stacking_rules: list of LegalStackingRule dicts with:
        program_a_id, program_b_id, rule_type, condition_text
    """
    results_by_id: dict[str, dict] = {
        str(r["program_id"]): r for r in incentive_results
    }
    id_set = set(results_by_id.keys())

    raw_values: dict[str, float] = {
        pid: float(r["economic_value_usd"])
        for pid, r in results_by_id.items()
    }
    program_values = dict(raw_values)

    adjustments: list[StackingAdjustment] = []
    legal_review_flags: list[str] = []

    for rule in stacking_rules:
        a_id = str(rule["program_a_id"])
        b_id = str(rule["program_b_id"])

        if a_id not in id_set or b_id not in id_set:
            continue

        rule_type = str(rule.get("rule_type", ""))

        if rule_type == "spend_reduction":
            _apply_spend_reduction(
                a_id, b_id, results_by_id, program_values, adjustments,
            )
        elif rule_type == "value_cap":
            _apply_value_cap(
                a_id, b_id, rule, program_values, adjustments, legal_review_flags,
            )
        elif rule_type == "mutually_exclusive":
            _apply_mutually_exclusive(
                a_id, b_id, program_values, adjustments, legal_review_flags,
            )
        elif rule_type == "conditional":
            legal_review_flags.append(
                f"Stacking of programs {a_id} and {b_id} requires legal review: "
                f"{rule.get('condition_text') or 'see statutory reference'}"
            )
        # allowed → no adjustment

    return StackingAdjustmentResult(
        program_values=program_values,
        raw_values=raw_values,
        adjustments=adjustments,
        total_raw_value_usd=sum(raw_values.values()),
        total_adjusted_value_usd=sum(program_values.values()),
        legal_review_flags=legal_review_flags,
    )


def _apply_spend_reduction(
    a_id: str,
    b_id: str,
    results_by_id: dict[str, dict],
    program_values: dict[str, float],
    adjustments: list[StackingAdjustment],
) -> None:
    """
    spend_reduction: a grant/fund reduces the qualifying spend basis of a credit.

    credit_reduction = min(grant_amount, credit_qualifying_spend) × credit_effective_rate
    """
    r_a = results_by_id[a_id]
    r_b = results_by_id[b_id]

    if r_a.get("program_type", "") in _GRANT_TYPES:
        grant_id, grant_r = a_id, r_a
        credit_id, credit_r = b_id, r_b
    elif r_b.get("program_type", "") in _GRANT_TYPES:
        grant_id, grant_r = b_id, r_b
        credit_id, credit_r = a_id, r_a
    else:
        # Both credits — cannot determine direction; no adjustment
        return

    grant_amount = float(grant_r["economic_value_usd"])
    credit_qualifying_spend = float(credit_r.get("qualifying_spend_usd", 0.0))
    credit_effective_rate = float(credit_r.get("effective_rate", 0.0))

    reducible_spend = min(grant_amount, credit_qualifying_spend)
    credit_reduction = reducible_spend * credit_effective_rate

    original = program_values[credit_id]
    adjusted = max(0.0, original - credit_reduction)
    program_values[credit_id] = adjusted

    adjustments.append(StackingAdjustment(
        program_a_id=grant_id,
        program_b_id=credit_id,
        rule_type="spend_reduction",
        description=(
            f"Grant ${grant_amount:,.0f} reduces credit qualifying spend by "
            f"${reducible_spend:,.0f}; credit reduction = "
            f"${reducible_spend:,.0f} × {credit_effective_rate:.1%} = ${credit_reduction:,.0f}"
        ),
        original_value_usd=original,
        adjustment_usd=-credit_reduction,
        adjusted_value_usd=adjusted,
    ))


def _apply_value_cap(
    a_id: str,
    b_id: str,
    rule: dict,
    program_values: dict[str, float],
    adjustments: list[StackingAdjustment],
    legal_review_flags: list[str],
) -> None:
    """
    value_cap: combined value of both programs ≤ cap encoded in condition_text.
    Excess is reduced proportionally across both programs.
    """
    combined = program_values[a_id] + program_values[b_id]
    try:
        cap = float(rule.get("condition_text") or 0)
    except (ValueError, TypeError):
        legal_review_flags.append(
            f"value_cap rule between {a_id} and {b_id}: cap not parseable from "
            f"condition_text='{rule.get('condition_text')}' — legal review required"
        )
        return

    if cap <= 0 or combined <= cap:
        return

    factor = cap / combined
    for pid in (a_id, b_id):
        original = program_values[pid]
        adjusted = original * factor
        program_values[pid] = adjusted
        adjustments.append(StackingAdjustment(
            program_a_id=a_id,
            program_b_id=b_id,
            rule_type="value_cap",
            description=(
                f"Combined value ${combined:,.0f} exceeds cap ${cap:,.0f}; "
                f"program {pid} reduced proportionally ({(1-factor):.1%} reduction)"
            ),
            original_value_usd=original,
            adjustment_usd=-(original - adjusted),
            adjusted_value_usd=adjusted,
        ))


def _apply_mutually_exclusive(
    a_id: str,
    b_id: str,
    program_values: dict[str, float],
    adjustments: list[StackingAdjustment],
    legal_review_flags: list[str],
) -> None:
    """
    mutually_exclusive: only the higher-value program can be claimed.
    The lower-value program is zeroed out.
    """
    val_a = program_values[a_id]
    val_b = program_values[b_id]

    if val_a >= val_b:
        zeroed_id, kept_id = b_id, a_id
    else:
        zeroed_id, kept_id = a_id, b_id

    original = program_values[zeroed_id]
    program_values[zeroed_id] = 0.0

    legal_review_flags.append(
        f"Programs {a_id} and {b_id} are mutually exclusive. "
        f"Retained: {kept_id} (${program_values[kept_id]:,.0f}); "
        f"excluded: {zeroed_id} (${original:,.0f} zeroed)."
    )
    adjustments.append(StackingAdjustment(
        program_a_id=a_id,
        program_b_id=b_id,
        rule_type="mutually_exclusive",
        description=f"Mutually exclusive — {zeroed_id} excluded in favour of {kept_id}",
        original_value_usd=original,
        adjustment_usd=-original,
        adjusted_value_usd=0.0,
    ))
