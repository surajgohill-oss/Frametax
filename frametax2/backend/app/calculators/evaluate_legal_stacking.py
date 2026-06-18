"""
evaluate_legal_stacking.py

Checks a proposed set of incentive programs for legal stacking violations.
Returns ALLOWED / PROHIBITED / CONDITIONAL decisions with full trace.

No LLM calls. Decisions are rule-table lookups only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.enums import StackingRuleType

ENGINE_VERSION = "0.1.0"


@dataclass
class StackingDecision:
    program_a_id: str
    program_b_id: str
    rule_type: StackingRuleType
    condition_text: str | None
    statutory_reference: str | None
    confidence_tier: str
    notes: str | None


@dataclass
class StackingEvaluationResult:
    claimed_program_ids: list[str]
    decisions: list[StackingDecision]
    violations: list[StackingDecision]     # PROHIBITED decisions
    conditionals: list[StackingDecision]   # CONDITIONAL decisions requiring review
    legal_review_required: bool
    engine_version: str = ENGINE_VERSION


def evaluate_legal_stacking(
    claimed_program_ids: list[str],
    stacking_rules: list[dict[str, Any]],
) -> StackingEvaluationResult:
    """
    Evaluate stacking rules for a proposed set of programs.

    claimed_program_ids: list of program UUIDs or slugs
    stacking_rules: list of LegalStackingRule-shaped dicts:
        {program_a_id, program_b_id, rule_type, condition_text,
         statutory_reference, confidence_tier, notes}
    """
    id_set = set(str(pid) for pid in claimed_program_ids)
    decisions: list[StackingDecision] = []
    violations: list[StackingDecision] = []
    conditionals: list[StackingDecision] = []

    for rule in stacking_rules:
        a_id = str(rule["program_a_id"])
        b_id = str(rule["program_b_id"])

        # Stacking rules are bidirectional
        if not ((a_id in id_set and b_id in id_set)):
            continue

        rule_type = StackingRuleType(rule["rule_type"])
        decision = StackingDecision(
            program_a_id=a_id,
            program_b_id=b_id,
            rule_type=rule_type,
            condition_text=rule.get("condition_text"),
            statutory_reference=rule.get("statutory_reference"),
            confidence_tier=rule.get("confidence_tier", "DISCOVERY"),
            notes=rule.get("notes"),
        )
        decisions.append(decision)

        if rule_type == StackingRuleType.PROHIBITED:
            violations.append(decision)
        elif rule_type == StackingRuleType.CONDITIONAL:
            conditionals.append(decision)

    legal_review_required = bool(violations) or bool(conditionals)

    return StackingEvaluationResult(
        claimed_program_ids=claimed_program_ids,
        decisions=decisions,
        violations=violations,
        conditionals=conditionals,
        legal_review_required=legal_review_required,
    )
