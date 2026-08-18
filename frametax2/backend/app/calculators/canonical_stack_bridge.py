"""
canonical_stack_bridge.py

Canonical multi-program stack-pricing bridge — Existing Optimizer/Stacker
Reconnection (see docs/validation/CODEX_EXISTING_OPTIMIZER_LINEAGE_TRACE.md).

Reuses the EXISTING, engine-agnostic stacking calculators
(apply_stacking_adjustments.py, evaluate_legal_stacking.py) against
CURRENT canonical per-program pricing (produced by
canonical_evaluation._price_candidate / allocation_pricing.
price_allocated_structure), instead of the superseded run_full_analysis
(ENGINE_VERSION 0.1.0) path that generate_structure_scenarios.py's
combinatorics currently depend on. No pricing formula is duplicated here
— every incentive value consumed below was already computed by the same
canonical pricing kernel every single-program candidate uses.

Scope, deliberately conservative for this pass: PAIRWISE combinations
only (exactly two programs sharing one jurisdiction — "Multiple programs
in one jurisdiction" / "Federal + provincial/state" from the lineage
trace). Every program in a pair is already independently allocated 100%
to that one jurisdiction (single_country/full_relocation structures never
split accounts across jurisdictions), so combining them requires no new
account allocation — only combining already-computed incentive values
under the existing stacking rule engine.

Rule loading is intentionally conservative: only pairs with an EXPLICIT
named entry in app.optimization.stacking_rules._SLUG_PAIR_RULES are
consulted. That table's own evaluate_pair() step 4 default-allows any
unmatched pair for the legacy app.optimization.optimizer consumer — this
bridge NEVER uses that fallback. An unmatched pair is left ungenerated,
never silently priced as compatible. This is Codex's own instruction:
"unknown/mismatched pairs remain gated... do not use default-allowance
as authority" / "Program visibility alone must not be reported as
stacking."

N-way (3+) program combinations via generate_structure_scenarios'
itertools.combinations are NOT reconnected in this pass — that would
additionally require every pairwise sub-combination to carry named
coverage before a 3-program result could be trusted, which the current
_SLUG_PAIR_RULES table does not yet guarantee for any known triple. This
is an explicit, disclosed scope limit (INTENTIONALLY_DEFERRED), not a
new design decision — see the capability ledger.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators.apply_stacking_adjustments import apply_stacking_adjustments
from app.calculators.evaluate_legal_stacking import evaluate_legal_stacking
from app.optimization.stacking_rules import _SLUG_PAIR_RULES


@dataclass
class StackCandidate:
    """One already-canonically-priced single-program candidate eligible to
    be combined into a multi-program structure. Every field is read
    straight off the existing per-program pricing pass — no new
    economics computed here."""
    program_slug: str
    jurisdiction_code: str
    selected_incentive_usd: float
    effective_rate: float
    qualifying_spend_usd: float
    incentive_type: str          # DoctrineRecord.incentive_type


@dataclass
class MultiProgramStackResult:
    jurisdiction_code: str
    program_slugs: list[str]
    rule_type: str
    condition_text: str | None
    raw_incentive_usd: float
    adjusted_incentive_usd: float
    stacking_reduction_usd: float
    per_program_adjusted_usd: dict[str, float]
    adjustments: list[dict] = field(default_factory=list)
    legal_review_required: bool = False
    violations: list[dict] = field(default_factory=list)
    conditionals: list[dict] = field(default_factory=list)
    disclosed_limitations: list[str] = field(default_factory=list)


def load_named_pair_rule(slug_a: str, slug_b: str) -> dict | None:
    """The canonical rule/slug loading adapter (lineage-trace roadmap step
    2 / integration piece (c)). _SLUG_PAIR_RULES is already keyed by
    CURRENT canonical program_slug strings for the pairs this reconnection
    targets (confirmed live DoctrineRecord.program_slug values:
    ca_federal_cptc, ca_bc_pstc, on_ofttc) — no alias reconciliation is
    performed here; a slug that only exists in the table under a stale
    spelling (e.g. legacy "on_opstc" vs canonical "ca_on_opstc") simply
    will not match and the pair stays ungenerated, which is the correct,
    safe outcome rather than a silent guess.
    """
    entry = _SLUG_PAIR_RULES.get(frozenset({slug_a, slug_b}))
    if entry is None:
        return None
    return {
        "program_a_id": slug_a,
        "program_b_id": slug_b,
        "rule_type": entry["rule_type"],
        "condition_text": entry.get("condition_text"),
        "statutory_reference": None,
        "confidence_tier": "VERIFIED",
        "notes": "app.optimization.stacking_rules._SLUG_PAIR_RULES (named pair)",
    }


def eligible_for_combination(code_a: str, code_b: str) -> bool:
    """Two candidates may be considered for a combined structure only if
    they represent the SAME physical shoot jurisdiction: either the exact
    same jurisdiction_code (multiple independent programs at one
    jurisdiction — e.g. CA-ON's on_ofttc + ca_on_opstc), or one of them is
    the bare top-level country code (a national/federal program, which
    applies alongside any of its own provinces/states) paired with a
    provincial/state code under that SAME country (e.g. "CA" federal
    CPTC + "CA-BC" provincial PSTC). Two DIFFERENT provinces/states
    (e.g. "CA-BC" + "CA-ON") are never combinable — a production cannot
    simultaneously shoot in both under one structure. This mirrors the
    same country-prefix structural test app.optimization.stacking_rules.
    _is_government_assistance_in_jurisdiction already uses for its own
    (different, static-fallback) grant/credit check.
    """
    if code_a == code_b:
        return True
    country_a, country_b = code_a.split("-")[0], code_b.split("-")[0]
    if country_a != country_b:
        return False
    return code_a == country_a or code_b == country_b


def price_program_pair_stack(
    candidate_a: StackCandidate, candidate_b: StackCandidate,
) -> MultiProgramStackResult | None:
    """
    The canonical multi-program stack-pricing bridge for exactly two
    programs. Returns None if the pair has no explicit named rule in
    _SLUG_PAIR_RULES (nothing safe to combine — Codex: visibility alone
    is not proof of stacking) or if the two candidates do not represent
    the same physical shoot jurisdiction (see eligible_for_combination).
    """
    if not eligible_for_combination(candidate_a.jurisdiction_code, candidate_b.jurisdiction_code):
        return None

    rule = load_named_pair_rule(candidate_a.program_slug, candidate_b.program_slug)
    if rule is None:
        return None

    incentive_results = [
        {
            "program_id": c.program_slug,
            "economic_value_usd": c.selected_incentive_usd,
            "effective_rate": c.effective_rate,
            "program_type": c.incentive_type,
            "qualifying_spend_usd": c.qualifying_spend_usd,
        }
        for c in (candidate_a, candidate_b)
    ]

    adj_result = apply_stacking_adjustments(incentive_results, [rule])
    legal = evaluate_legal_stacking(
        claimed_program_ids=[candidate_a.program_slug, candidate_b.program_slug],
        stacking_rules=[rule],
    )

    disclosed_limitations: list[str] = []
    if rule["rule_type"] == "spend_reduction" and not adj_result.adjustments:
        # apply_stacking_adjustments._apply_spend_reduction only recognizes
        # a "grant"/"regional_fund"/"discretionary_fund" program_type as the
        # reducing side (see app/calculators/apply_stacking_adjustments.py
        # _GRANT_TYPES). The named on_ofttc+ca_federal_cptc and
        # qc_film_production+ca_federal_cptc rules describe a TAX CREDIT
        # that is itself government assistance reducing another tax
        # credit's qualifying-spend basis — a case that generic reused
        # heuristic cannot resolve without a program_type it wasn't
        # designed to see. Disclosed here rather than silently reported as
        # "no stacking impact": adjusted_incentive_usd above is the RAW
        # (unreduced) sum, not confirmed net of this statutory deduction.
        disclosed_limitations.append(
            f"Statutory rule found ({rule['condition_text']}) but the reused "
            "spend_reduction calculator only recognizes grant/regional_fund/"
            "discretionary_fund program types as the reducing side; neither "
            f"{candidate_a.program_slug} nor {candidate_b.program_slug} is "
            "typed that way, so no reduction was applied. This combination's "
            "adjusted_incentive_usd is therefore the unreduced sum, not a "
            "verified net figure — legal/economic review required before "
            "this combination is treated as priced."
        )

    return MultiProgramStackResult(
        # The more specific (provincial/state) code is the reported anchor
        # jurisdiction for a federal+provincial pair — that is where the
        # production actually shoots; the bare country code is never a
        # real shoot location on its own. Equal codes (same-jurisdiction
        # multi-program case) pick either, since they're identical.
        jurisdiction_code=max(
            candidate_a.jurisdiction_code, candidate_b.jurisdiction_code, key=len,
        ),
        program_slugs=[candidate_a.program_slug, candidate_b.program_slug],
        rule_type=rule["rule_type"],
        condition_text=rule["condition_text"],
        raw_incentive_usd=adj_result.total_raw_value_usd,
        adjusted_incentive_usd=adj_result.total_adjusted_value_usd,
        stacking_reduction_usd=max(
            0.0, adj_result.total_raw_value_usd - adj_result.total_adjusted_value_usd
        ),
        per_program_adjusted_usd=adj_result.program_values,
        adjustments=[
            {
                "program_a_id": a.program_a_id,
                "program_b_id": a.program_b_id,
                "rule_type": a.rule_type,
                "description": a.description,
                "original_value_usd": a.original_value_usd,
                "adjustment_usd": a.adjustment_usd,
                "adjusted_value_usd": a.adjusted_value_usd,
            }
            for a in adj_result.adjustments
        ],
        legal_review_required=legal.legal_review_required,
        violations=[
            {
                "program_a_id": v.program_a_id, "program_b_id": v.program_b_id,
                "rule_type": v.rule_type.value, "condition_text": v.condition_text,
            }
            for v in legal.violations
        ],
        conditionals=[
            {
                "program_a_id": c.program_a_id, "program_b_id": c.program_b_id,
                "rule_type": c.rule_type.value, "condition_text": c.condition_text,
            }
            for c in legal.conditionals
        ],
        disclosed_limitations=disclosed_limitations,
    )
