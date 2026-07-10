"""
ui_presentation.py

Phase 8 bridge: presentation adapters only.

Every function in this file does exactly one thing — take an object an
existing engine already produced and reshape it into a flatter,
JSON/UI-friendly structure. Nothing here computes a new value, applies a
new threshold, or makes a new determination. If a function in this file
ever needs an `if` statement to decide a fact (not just to handle a
missing/None case for display), that is a sign the logic belongs in the
engine that owns it, not here.

Why this file exists: three shapes recur across the Phase 4-8 engines
that are correct and necessary internally but awkward for a UI/JSON
consumer without a translation step —

1. Enum-keyed dicts. `ProductionStructureCandidate.cases` and
   `OptimizationResult.cases` are `dict[RiskCase, CaseResult]` — enum
   keys don't round-trip through standard JSON. `case_dict_to_display()`
   converts to `dict[str, CaseResult]` keyed by `RiskCase.value`, no
   other change.
2. Nested attribute facts. `PersonProfile.nationality`,
   `EntityProfile.registered_jurisdiction`, `LocationRecord.jurisdiction`,
   and `CrewMovement.home_base` / `destination_jurisdiction` are all
   `AttributeFact` — a small object a UI would otherwise have to unpack
   three different ways (state, confidence, discovery sources) at every
   call site. `attribute_fact_to_display()` flattens it once.
3. Object-valued evidence chains. `EvidenceGraph.trace_rule()` returns
   `list[dict]` where the dict VALUES are dataclass instances
   (Evidence, Citation, AuthoritySource, DocumentVersion, Document) —
   correct for Python-side tracing, not directly serializable.
   `evidence_chain_to_display()` flattens each link to primitive fields.

A fourth helper, `group_recommendations_by_category()`, does no
flattening — it only groups an already-ranked
list[Recommendation] by category, which the Recommendation Center
(Phase 8 data map) needs and RecommendationSet.of_category() already
supports one category at a time. This is "group related fields," not a
ranking or filtering decision — order within each group is preserved
exactly as generate_production_recommendations() already produced it.

None of these functions import anything write-capable (no EvidenceGraph
mutation, no LAAE commit, no optimizer call). They are pure, read-only,
and safe to call as many times as a UI needs without side effects.
"""
from __future__ import annotations

from typing import Any, Optional

from app.calculators.evidence_graph import AuthorityTier
from app.calculators.optimization_engine import CaseResult, RiskCase
from app.calculators.production_package_intelligence import AttributeFact, FactKnowledgeState
from app.calculators.production_recommendation_engine import Recommendation, RecommendationCategory

UI_PRESENTATION_VERSION = "1.0.0"


def case_dict_to_display(cases: Optional[dict[RiskCase, CaseResult]]) -> dict[str, dict[str, Any]]:
    """dict[RiskCase, CaseResult] -> dict[str, dict] keyed by
    RiskCase.value ('conservative' | 'base' | 'optimistic' |
    'risk_adjusted'), each CaseResult reshaped via its own field names —
    no field is renamed, computed, or dropped. None input (an unpriced
    candidate) returns an empty dict, never a fabricated case."""
    if not cases:
        return {}
    return {
        case.value: {
            "case": result.case.value,
            "qpe_usd": result.qpe_usd,
            "incentive_usd": result.incentive_usd,
            "finance_cost_usd": result.finance_cost_usd,
            "net_benefit_usd": result.net_benefit_usd,
            "net_production_cost_usd": result.net_production_cost_usd,
            "included_codes": list(result.included_codes),
            "excluded_codes": list(result.excluded_codes),
            "inkind_addon_usd": result.inkind_addon_usd,
            "reconciles": result.reconciles,
        }
        for case, result in cases.items()
    }


def attribute_fact_to_display(fact: AttributeFact) -> dict[str, Any]:
    """AttributeFact -> a flat dict a form/badge component can render
    without knowing the FactKnowledgeState enum. is_known /
    needs_verification are the exact state check the object already
    exposes (state == KNOWN, state == VERIFICATION_REQUIRED) — not a new
    classification."""
    return {
        "value": fact.value,
        "is_known": fact.state == FactKnowledgeState.KNOWN,
        "needs_verification": fact.state == FactKnowledgeState.VERIFICATION_REQUIRED,
        "state": fact.state.value,
        "confidence": fact.confidence.value,
        "is_actionable": fact.is_actionable,
        "discovery_sources": [s.value for s in fact.possible_discovery_sources],
        "notes": fact.notes,
    }


def evidence_chain_to_display(chain: list[dict]) -> list[dict[str, Any]]:
    """EvidenceGraph.trace_rule()'s list[dict] of dataclass instances ->
    a list of plain-field dicts, one per Evidence -> Citation ->
    AuthoritySource -> DocumentVersion -> Document link, in the exact
    order trace_rule() returned them (the graph's own evidence_ids
    order — never resorted here)."""
    display: list[dict[str, Any]] = []
    for link in chain:
        source = link["authority_source"]
        version = link["document_version"]
        document = link["document"]
        citation = link["citation"]
        evidence = link["evidence"]
        display.append({
            "evidence_id": evidence.evidence_id,
            "description": evidence.description,
            "supports_inclusion": evidence.supports_inclusion,
            "citation_pinpoint": citation.pinpoint,
            "citation_text": citation.citation_text,
            "authority_source_title": source.title,
            "authority_tier": source.tier.name,
            "authority_tier_rank": source.tier.value,
            "binding_force": source.binding_force.value,
            "authority_body": source.authority_body,
            "document_title": document.title,
            "document_source_url": document.source_url,
            "document_version_label": version.version_label,
            "retrieved_date": version.retrieved_date,
            "effective_date": version.effective_date,
            "publication_date": version.publication_date,
            "superseded": link["superseded"],
        })
    return display


# Display labels for AuthorityTier — the same 14 tiers evidence_graph.py
# already defines, only reformatted from ALL_CAPS_ENUM_NAMES to a label a
# UI can show directly. No tier is added, removed, or reordered.
AUTHORITY_TIER_LABELS: dict[AuthorityTier, str] = {
    tier: tier.name.replace("_", " ").title() for tier in AuthorityTier
}


def group_recommendations_by_category(
    recommendations: list[Recommendation],
) -> dict[str, list[Recommendation]]:
    """Groups an already-ranked recommendation list by category —
    RecommendationSet.of_category() already does this one category at a
    time; this returns all four groups in one call for a tabbed
    Recommendation Center view. Within-group order is exactly the input
    order (already ranked by generate_production_recommendations());
    this function performs no re-ranking."""
    grouped: dict[str, list[Recommendation]] = {c.value: [] for c in RecommendationCategory}
    for rec in recommendations:
        grouped[rec.category.value].append(rec)
    return grouped
