"""
Canonical structural classification -- the ONE mapping from a candidate's real, persisted trace fields
(structural_family / structure_type / candidate_status / rejection_reason_class / conditional_scenario) to
its backend-owned, mutually exclusive structural classification.

GD-2 correction (Globe data contract remediation, 2026-09-20, operator directive following the Codex Globe
data contract delta audit): this logic previously lived ONLY inside canonical_production_view.py as
serve-time projection logic -- correct in its OUTPUT, but not itself part of the canonical persisted
contract, and not the same value retention (candidate_retention.py) or aggregation
(candidate_aggregation.py) used for their own family/type bucketing. This module is now the single
source of truth, imported by:

  * app/services/canonical_evaluation.py -- computed ONCE per candidate, at the same centralized
    `_BulkEvaluationWriter._route()` call site every candidate already passes through exactly once, and
    STAMPED onto `calculation_trace_json["structural_classification"]` before the candidate is persisted
    (retained detail row or aggregate representative) -- so the classification is itself part of the
    canonical persisted contract, not solely re-derived at serve time. That same stamped value is also
    what bounded retention's per-family lane and aggregation's per-family dominator reconciliation key on
    (see `Held.family` / `candidate_group_identity`'s `structural_classification` field), so retention,
    aggregation and the served view all consume the exact same canonical family value.

  * app/services/canonical_production_view.py -- serves the persisted `structural_classification` field
    directly when present; falls back to calling `classify_structure()` live only for the small number of
    historical rows generated before this field existed (the same graceful-degradation precedent already
    used throughout this module for structure_type/selected_incentive_usd/etc.).
"""
from __future__ import annotations

#: P1-CLASS-001 (Codex global optimizer audit): "Add one backend-owned, mutually exclusive
#: classification for every emitted structure. Do not require UI inference." The ten values below are
#: the full, closed contract: every structure this backend ever emits resolves to EXACTLY one, derived
#: here from fields already persisted on the SAME candidate -- never a new signal, never left for a
#: frontend consumer to infer from structure_type + relationship_types + candidate_status combinations
#: on its own.
CLASS_SINGLE_JURISDICTION = "SINGLE_JURISDICTION"
CLASS_OFFICIAL_COPRODUCTION = "OFFICIAL_COPRODUCTION"
CLASS_HYBRID_ANCHOR_COMPONENT = "HYBRID_ANCHOR_COMPONENT"
CLASS_STACKED_PROGRAMS = "STACKED_PROGRAMS"
CLASS_COMBINED_COPRO_HYBRID_STACK = "COMBINED_COPRO_HYBRID_STACK"
#: GD-2: the delta audit's own required family list distinguishes "multi-principal / multilateral" from
#: the pair/component/multi-component combined-hybrid families above -- structural_family=
#: "combined_multilateral_coproduction_stack" (>=2 simultaneous principal-production legs under one real
#: multilateral treaty mechanism, e.g. Eurimages) is its own canonical value, never folded into
#: COMBINED_COPRO_HYBRID_STACK.
CLASS_MULTI_PRINCIPAL_MULTILATERAL = "MULTI_PRINCIPAL_MULTILATERAL"
CLASS_CONDITIONAL_USER_FACT_REQUIRED = "CONDITIONAL_USER_FACT_REQUIRED"
CLASS_RULE_DATA_INCOMPLETE = "RULE_DATA_INCOMPLETE"
CLASS_AUTHORITY_LOCKED = "AUTHORITY_LOCKED"
CLASS_REJECTED_FOR_PROJECT = "REJECTED_FOR_PROJECT"

STRUCTURE_CLASSIFICATIONS: tuple[str, ...] = (
    CLASS_SINGLE_JURISDICTION,
    CLASS_OFFICIAL_COPRODUCTION,
    CLASS_HYBRID_ANCHOR_COMPONENT,
    CLASS_STACKED_PROGRAMS,
    CLASS_COMBINED_COPRO_HYBRID_STACK,
    CLASS_MULTI_PRINCIPAL_MULTILATERAL,
    CLASS_CONDITIONAL_USER_FACT_REQUIRED,
    CLASS_RULE_DATA_INCOMPLETE,
    CLASS_AUTHORITY_LOCKED,
    CLASS_REJECTED_FOR_PROJECT,
)

#: GD-2: the structural generator's real, persisted `structural_family` trace values that map to
#: COMBINED_COPRO_HYBRID_STACK -- the pair, single-component, and multi-component combined co-production
#: variants all persist the broad `structure_type="hybrid"`, so `structure_type` alone cannot distinguish
#: them from an ordinary (non-treaty) component hybrid. One canonical enum/mapping, never derived from
#: display text.
COMBINED_COPRO_STRUCTURAL_FAMILIES = frozenset({
    "combined_coproduction_pair_stack",
    "combined_coproduction_component_stack",
    "combined_coproduction_multi_component_stack",
})

#: GD-4: the canonical classifications a PRICED candidate can ever resolve to (excludes the
#: unpriced/blocked/conditional classes, which never compete for a "best priced candidate" family slot) --
#: the fixed key set the served `top_by_structural_family` block is pre-seeded with, so an available-but-
#: absent family serves an honest empty list rather than a missing key.
PRICED_STRUCTURE_FAMILIES: tuple[str, ...] = (
    CLASS_SINGLE_JURISDICTION,
    CLASS_STACKED_PROGRAMS,
    CLASS_HYBRID_ANCHOR_COMPONENT,
    CLASS_OFFICIAL_COPRODUCTION,
    CLASS_COMBINED_COPRO_HYBRID_STACK,
    CLASS_MULTI_PRINCIPAL_MULTILATERAL,
)


def classify_structure(trace: dict, structure_type: str, is_priced: bool) -> str:
    """The canonical derivation. Checked in a fail-closed order (most severe / most specific first,
    generic fallback last) -- unresolved/blocked states always win over a structure_type-based guess:

    1. RULE_DATA_INCOMPLETE  -- an unresolved named-rule gap (a rejection explicitly classed this way,
       or the analogous scenario status).
    2. AUTHORITY_LOCKED      -- authority coverage fails closed (never a priceability question at all).
    3. CONDITIONAL_USER_FACT_REQUIRED -- registry presence is real but a real project fact (ownership
       share, cultural test, ...) is missing; disclosed, never fabricated-eligible.
    4. REJECTED_FOR_PROJECT  -- any other real, explicit rejection (minimum spend, statutory conditions,
       qualification hard-fail).
    5. Priced structures resolve by real composition, most-combined first:
       MULTI_PRINCIPAL_MULTILATERAL > COMBINED_COPRO_HYBRID_STACK > OFFICIAL_COPRODUCTION >
       HYBRID_ANCHOR_COMPONENT > STACKED_PROGRAMS > SINGLE_JURISDICTION (the last also covers
       full_relocation -- a single jurisdiction, just not the production's original one).

    GD-2: every combined/ordinary hybrid family persists the same broad `structure_type="hybrid"`, so
    `structure_type` alone previously fell through to the generic SINGLE_JURISDICTION default for all of
    them. The real, persisted `structural_family` trace value (never display text, never re-derived) is
    the primary signal for every hybrid structure_type.
    """
    candidate_status = trace.get("candidate_status")
    rejection_reason_class = trace.get("rejection_reason_class")
    conditional_scenario = trace.get("conditional_scenario") or {}

    if (
        candidate_status == "RULE_DATA_INCOMPLETE"
        or rejection_reason_class == "RULE_DATA_INCOMPLETE"
        or conditional_scenario.get("status") == "RULE_DATA_INCOMPLETE"
    ):
        return CLASS_RULE_DATA_INCOMPLETE
    if candidate_status == "UNPRICEABLE_AUTHORITY_INSUFFICIENT":
        return CLASS_AUTHORITY_LOCKED
    if candidate_status == "CO_PRO_OPPORTUNITY" or candidate_status == "QUALIFICATION_UNRESOLVED":
        return CLASS_CONDITIONAL_USER_FACT_REQUIRED
    if not is_priced:
        return CLASS_REJECTED_FOR_PROJECT

    structural_family = trace.get("structural_family")
    discovery_classification = trace.get("discovery_classification")
    if structural_family == "combined_multilateral_coproduction_stack":
        return CLASS_MULTI_PRINCIPAL_MULTILATERAL
    if (
        structural_family in COMBINED_COPRO_STRUCTURAL_FAMILIES
        or discovery_classification == "combined_coproduction_component_stack"
    ):
        return CLASS_COMBINED_COPRO_HYBRID_STACK
    if structure_type == "treaty_coproduction":
        return CLASS_OFFICIAL_COPRODUCTION
    if structure_type == "component_relocation" or structural_family == "ordinary_component_hybrid":
        return CLASS_HYBRID_ANCHOR_COMPONENT
    if structure_type == "multi_program":
        return CLASS_STACKED_PROGRAMS
    return CLASS_SINGLE_JURISDICTION
