"""
production_recommendation_engine.py

Phase 7D of CineGlobe: the Production Optimization Recommendation Engine.

Phase 7A (opportunity_discovery.py) answers "what candidate optimization
paths exist worldwide?". Phase 7B/7C (global_scenario_ranker.py,
production_structure_composer.py) answer "which combinations form a
coherent, prices structure, and how do they rank?". This module answers
the question a producer actually asked: "what should I change?" — a
ranked list of concrete, gated ActionRecommendations, not a restatement
of what already exists.

This is synthesis only. This module:

- discovers nothing new: every Recommendation is derived from an
  Opportunity already present in the OpportunityCollection, a
  ProductionStructureCandidate already composed by Phase 7C, or a
  QualificationTestResult already scored by cultural_test_rules.py /
  evaluate_qualification_tests.py.
- computes no new dollar figures: estimated_value_usd is always either
  None, an existing Opportunity's own estimated_upside_usd, or a plain
  subtraction of two already-computed CaseResult.net_production_cost_usd
  figures (both produced by the same build_risk_cases() call the
  composer already made). This module never calls build_risk_cases()
  itself and never invents a dollar figure no other engine already
  computed.
- never mutates: every function here reads its inputs and returns new
  Recommendation objects. No Opportunity, ProductionStructureCandidate,
  CompositionResult, JurisdictionGraph, or EvidenceGraph is ever written
  to. A Recommendation is a suggestion the producer or counsel must
  explicitly accept (see the lifecycle/gate functions below) — it can
  never programmatically apply itself to a candidate.
- never fabricates authority: authority_reference always points at an
  object an existing engine already produced — an Evidence Graph
  graph_rule_id/graph_absence_id, an LAAE acquisition_task_ref, or (for
  cultural-test recommendations, which have no Evidence Graph linkage in
  this codebase) the exact cultural_test_rules.py rule table entry the
  recommendation is drawn from. Nothing here performs legal research or
  invents a citation.
- gates creative recommendations structurally, not by convention: a
  Recommendation with category=CREATIVE cannot be constructed without
  creative_impact, qualification_rationale, trade_off_framing, an
  evidence_reference, an authority_reference, and requires_producer_approval
  set True — see Recommendation.__post_init__. Creative recommendations
  are never generated for a passing cultural test — this module never
  proposes changing a creative decision "for its own sake", only where
  an actual, already-computed qualification gap exists.
- never silently suppresses an unknown: a cultural test the caller marks
  relevant but supplies no (or incomplete) production_details for
  produces a REQUIRED_INPUT recommendation listing exactly which
  cultural_test_rules.py input_keys are missing — never a silent skip,
  never an assumed pass or fail.

Out of scope for this phase (see docs/roadmap): script/production-package
parsing (Phase 7E), the Learning Engine, the UI, the API. This module
takes already-extracted structured inputs (OpportunityCollection,
CompositionResult, a caller-supplied cultural_test_inputs dict) — it does
not extract them from anything.

Deterministic throughout: fixed iteration over sorted/ranked structures,
no wall-clock, no randomness. The same inputs produce byte-identical
Recommendation ids and ordering on every run.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional

from app.calculators import cultural_test_rules as ctr
from app.data import cultural_qualification_model as cqm
from app.calculators.evaluate_qualification_tests import QualificationTestResult
from app.calculators.legal_authority_acquisition import (
    DEFAULT_ACQUISITION_EFFORT,
    compute_priority_score,
)
from app.calculators.levers import Lever, derive_levers, is_lever_recommended
from app.calculators.opportunity_discovery import (
    Opportunity,
    OpportunityCollection,
    OpportunityType,
)
from app.calculators.optimization_engine import CONFIDENCE_WEIGHTS, RiskCase
from app.calculators.production_structure_composer import (
    CompositionResult,
    ProductionStructureCandidate,
)
from app.calculators.qualification_model import AccountQualification, QualificationConfidence

PRODUCTION_RECOMMENDATION_ENGINE_VERSION = "1.0.0"

# Policy constant: cultural-test-driven CREATIVE recommendations always
# require counsel sign-off in addition to producer sign-off, because they
# touch a legal qualification determination, not merely an operational
# choice. Named explicitly (matching the codebase's convention of naming
# policy constants rather than burying magic booleans) so the rule is
# auditable and can be revisited in one place.
CREATIVE_RECOMMENDATIONS_REQUIRE_COUNSEL = True

# Complexity -> acquisition-style effort mapping, same 1.0/2.0/3.0 scale
# legal_authority_acquisition.EFFORT_BY_CONNECTOR_CLASS already uses.
# This is a ranking input, never a cost estimate.
EFFORT_BY_COMPLEXITY: dict[str, float] = {
    "LOW": 1.0,
    "MEDIUM": 2.0,
    "HIGH": 3.0,
    "UNKNOWN": 2.0,
}

RECOMMENDATION_PASSES: tuple[str, ...] = (
    "grey_area",
    "evidence_acquisition",
    "structuring",
    "treaty_stacking_normalization_reinvestment",
    "candidate_comparison",
    "cultural",
    "dedupe",
    "rank",
)


class RecommendationCategory(str, enum.Enum):
    FINANCIAL = "financial"
    STRUCTURAL = "structural"
    CREATIVE = "creative"
    REQUIRED_INPUT = "required_input"


class RecommendationStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"


def _confidence_gap(confidence: QualificationConfidence) -> float:
    """Complement of optimization_engine.CONFIDENCE_WEIGHTS — reuses the
    existing HIGH/MEDIUM/LOW/NOT_APPLICABLE weight table rather than
    inventing a second confidence scale."""
    return round(1.0 - CONFIDENCE_WEIGHTS[confidence], 4)


@dataclass
class Recommendation:
    """
    One producer-facing, gated suggestion: what to change, why, what it's
    worth (only if an existing engine already computed that), and what
    approval it needs before anything happens. Structurally incapable of
    representing a self-applying change — there is no method on this
    object or anywhere in this module that mutates an Opportunity,
    ProductionStructureCandidate, or CompositionResult.
    """
    recommendation_id: str
    category: RecommendationCategory
    subtype: str
    title: str
    description: str
    specific_actions: tuple[str, ...]
    jurisdiction_codes: tuple[str, ...] = ()
    estimated_value_usd: Optional[float] = None
    confidence: QualificationConfidence = QualificationConfidence.LOW
    candidate_id: Optional[str] = None
    opportunity_ids: tuple[str, ...] = ()
    evidence_reference: tuple[str, ...] = ()
    authority_reference: tuple[str, ...] = ()
    requires_producer_approval: bool = True
    requires_counsel_approval: bool = False
    creative_impact: Optional[str] = None
    qualification_rationale: Optional[str] = None
    trade_off_framing: Optional[str] = None
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    producer_approved_by: Optional[str] = None
    counsel_approved_by: Optional[str] = None
    superseded_by: Optional[str] = None
    notes: str = ""
    source_ref: str = ""
    attributes: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category == RecommendationCategory.CREATIVE:
            missing = [
                name for name, value in (
                    ("creative_impact", self.creative_impact),
                    ("qualification_rationale", self.qualification_rationale),
                    ("trade_off_framing", self.trade_off_framing),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    f"{self.recommendation_id}: CREATIVE recommendations require "
                    f"{', '.join(missing)}."
                )
            if not self.evidence_reference:
                raise ValueError(
                    f"{self.recommendation_id}: CREATIVE recommendations require an evidence_reference."
                )
            if not self.authority_reference:
                raise ValueError(
                    f"{self.recommendation_id}: CREATIVE recommendations require an authority_reference."
                )
            if not self.requires_producer_approval:
                raise ValueError(
                    f"{self.recommendation_id}: CREATIVE recommendations must require producer approval."
                )
        if self.category == RecommendationCategory.REQUIRED_INPUT:
            if not self.attributes.get("required_fields"):
                raise ValueError(
                    f"{self.recommendation_id}: REQUIRED_INPUT recommendations must list "
                    "attributes['required_fields']."
                )

    @property
    def recommendation_rank_score(self) -> float:
        """Same (value x confidence_gap) / effort formula LAAE and
        Opportunity.discovery_rank_score already use — no new ranking
        math, just reused against this object's own fields."""
        gap = self.attributes.get("confidence_gap", 1.0)
        effort = self.attributes.get("implementation_effort", DEFAULT_ACQUISITION_EFFORT)
        return compute_priority_score(self.estimated_value_usd, gap, effort)

    @property
    def is_fully_approved(self) -> bool:
        if self.producer_approved_by is None:
            return False
        if self.requires_counsel_approval and self.counsel_approved_by is None:
            return False
        return True


@dataclass
class RecommendationSet:
    baseline_jurisdiction: str
    passes_run: tuple[str, ...]
    recommendations: list[Recommendation]

    def of_category(self, category: RecommendationCategory) -> list[Recommendation]:
        return [r for r in self.recommendations if r.category == category]


# ── Lifecycle / gates (7D-4) ─────────────────────────────────────────────────

def record_producer_approval(rec: Recommendation, approved_by: str, notes: str = "") -> Recommendation:
    """Mutates rec in place and returns it — same pattern as
    approve_staged_authority()/approve_recommendation-style lifecycle
    objects elsewhere in this codebase. Never touches anything but the
    Recommendation itself: accepting a recommendation is not the same as
    applying it to a candidate, and this module has no code path that
    does the latter."""
    if rec.status in (RecommendationStatus.REJECTED, RecommendationStatus.SUPERSEDED):
        raise ValueError(f"{rec.recommendation_id} is {rec.status.value} — cannot approve.")
    rec.producer_approved_by = approved_by
    if notes:
        rec.notes = notes
    if rec.is_fully_approved:
        rec.status = RecommendationStatus.ACCEPTED
    return rec


def record_counsel_approval(rec: Recommendation, approved_by: str, notes: str = "") -> Recommendation:
    if rec.status in (RecommendationStatus.REJECTED, RecommendationStatus.SUPERSEDED):
        raise ValueError(f"{rec.recommendation_id} is {rec.status.value} — cannot approve.")
    if not rec.requires_counsel_approval:
        raise ValueError(f"{rec.recommendation_id} does not require counsel approval.")
    rec.counsel_approved_by = approved_by
    if notes:
        rec.notes = notes
    if rec.is_fully_approved:
        rec.status = RecommendationStatus.ACCEPTED
    return rec


def reject_recommendation(rec: Recommendation, rejected_by: str, reason: str) -> Recommendation:
    rec.status = RecommendationStatus.REJECTED
    rec.notes = reason
    return rec


def defer_recommendation(rec: Recommendation, deferred_by: str, reason: str) -> Recommendation:
    if rec.status == RecommendationStatus.ACCEPTED:
        raise ValueError(f"{rec.recommendation_id} is already accepted — cannot defer.")
    rec.status = RecommendationStatus.DEFERRED
    rec.notes = reason
    return rec


def supersede_recommendation(rec: Recommendation, superseded_by: str) -> Recommendation:
    rec.status = RecommendationStatus.SUPERSEDED
    rec.superseded_by = superseded_by
    return rec


# ── 7D-2: Financial recommendations ──────────────────────────────────────────

def generate_grey_area_recommendations(collection: OpportunityCollection) -> list[Recommendation]:
    """One FINANCIAL recommendation per OPEN grey-area Opportunity. The
    dollar figure is the Opportunity's own estimated_upside_usd (amount x
    rate — qualification_model's existing formula), never recomputed.
    Counsel approval is required, mirroring optimization_engine's own
    rule that a grey-area AssumptionOverride requires approver_role ==
    'counsel'."""
    recs: list[Recommendation] = []
    for opp in collection.of_type(OpportunityType.GREY_AREA):
        recs.append(Recommendation(
            recommendation_id=f"REC-GREY-{opp.opportunity_id}",
            category=RecommendationCategory.FINANCIAL,
            subtype="grey_area_resolution",
            title=f"Resolve grey area: {opp.opportunity_id}",
            description=opp.description,
            specific_actions=(
                f"Pursue LAAE acquisition task(s) {', '.join(opp.acquisition_task_refs) or 'n/a'} "
                "to resolve this grey area before booking its value.",
            ),
            jurisdiction_codes=opp.jurisdiction_codes,
            estimated_value_usd=opp.estimated_upside_usd,
            confidence=opp.confidence,
            opportunity_ids=(opp.opportunity_id,),
            evidence_reference=opp.required_evidence,
            authority_reference=opp.acquisition_task_refs or (
                (opp.graph_absence_id,) if opp.graph_absence_id else ()
            ),
            requires_counsel_approval=True,
            source_ref=opp.source_ref,
            attributes={
                "confidence_gap": opp.attributes.get("confidence_gap", 1.0),
                "implementation_effort": opp.attributes.get("research_effort", DEFAULT_ACQUISITION_EFFORT),
            },
        ))
    return recs


def generate_evidence_acquisition_recommendations(collection: OpportunityCollection) -> list[Recommendation]:
    """One FINANCIAL recommendation per requires_evidence Opportunity that
    is NOT a grey area (those are covered above). Covers stacking_unknown,
    reinvestment_unknown, application_timing_unknown, and any future
    requires_evidence subtype uniformly — no new logic per subtype."""
    recs: list[Recommendation] = []
    for opp in collection.opportunities:
        if not opp.requires_evidence or opp.opportunity_type == OpportunityType.GREY_AREA:
            continue
        recs.append(Recommendation(
            recommendation_id=f"REC-EVID-{opp.opportunity_id}",
            category=RecommendationCategory.FINANCIAL,
            subtype="evidence_acquisition",
            title=f"Acquire evidence: {opp.subtype.replace('_', ' ')}",
            description=opp.description,
            specific_actions=(
                f"Pursue LAAE acquisition task(s) {', '.join(opp.acquisition_task_refs) or 'n/a'}.",
            ),
            jurisdiction_codes=opp.jurisdiction_codes,
            estimated_value_usd=opp.estimated_upside_usd,
            confidence=opp.confidence,
            opportunity_ids=(opp.opportunity_id,),
            evidence_reference=opp.required_evidence,
            authority_reference=opp.acquisition_task_refs,
            requires_counsel_approval=(opp.authority_score == 0.0),
            source_ref=opp.source_ref,
            attributes={
                "confidence_gap": opp.attributes.get("confidence_gap", 1.0),
                "implementation_effort": DEFAULT_ACQUISITION_EFFORT,
            },
        ))
    return recs


# ── 7D-2: Structural recommendations ─────────────────────────────────────────

def generate_structuring_recommendations(
    collection: OpportunityCollection,
    register: list[AccountQualification],
    rate: float,
    jurisdiction_code: str = "MU",
) -> list[Recommendation]:
    """
    One STRUCTURAL recommendation per STRUCTURING opportunity whose
    underlying Lever clears levers.is_lever_recommended() — the existing
    upside/cost >= 3x + confidence >= MEDIUM threshold, called directly
    rather than reimplemented. Levers below threshold are surfaced by
    Phase 7A already; this layer only recommends what's actually worth
    doing.
    """
    levers_by_id: dict[str, Lever] = {
        lever.lever_id: lever
        for lever in derive_levers(register, rate=rate, jurisdiction_code=jurisdiction_code)
    }
    recs: list[Recommendation] = []
    for opp in collection.of_type(OpportunityType.STRUCTURING):
        lever_id = opp.opportunity_id.removeprefix("OPP-STRUCT-")
        lever = levers_by_id.get(lever_id)
        if lever is None or not is_lever_recommended(lever):
            continue
        recs.append(Recommendation(
            recommendation_id=f"REC-STRUCT-{lever_id}",
            category=RecommendationCategory.STRUCTURAL,
            subtype=opp.subtype,
            title=f"Structure via {opp.attributes.get('mechanism', opp.subtype)}",
            description=opp.description,
            specific_actions=(f"Execute structuring mechanism: {lever.mechanism}.",),
            jurisdiction_codes=opp.jurisdiction_codes,
            estimated_value_usd=lever.upside_incentive_usd,
            confidence=lever.confidence,
            opportunity_ids=(opp.opportunity_id,),
            evidence_reference=lever.required_documents,
            authority_reference=(
                (lever.graph_rule_id,) if lever.graph_rule_id else
                ((lever.graph_absence_id,) if lever.graph_absence_id else ())
            ),
            requires_counsel_approval=False,
            source_ref=opp.source_ref,
            attributes={
                "confidence_gap": _confidence_gap(lever.confidence),
                "implementation_effort": EFFORT_BY_COMPLEXITY.get(lever.complexity, EFFORT_BY_COMPLEXITY["UNKNOWN"]),
            },
        ))
    return recs


# subtype key ("opportunity_type:subtype") -> recommendation title. Fixed,
# explicit lookup — classification only, mirrors opportunity_discovery's
# own _ROUTING_CLASSIFIERS discipline. A subtype not in this table is not
# recommended (it stays visible at the Opportunity level, Phase 7A's job,
# not restated here).
_STRUCTURAL_OPPORTUNITY_TITLES: dict[str, str] = {
    "treaty:bilateral_coproduction": "Pursue bilateral co-production treaty structure",
    "treaty:treaty_composition_path": "Pursue European Convention co-production composition",
    "treaty:nationality_unlock": "Utilize treaty co-production status to unlock program access",
    "treaty:multilateral_membership": "Confirm multilateral treaty/fund membership access",
    "stacking:known_stack": "Combine known-stackable incentive programs",
    "normalization:fund_timing": "Route financing through faster-paying jurisdiction",
    "normalization:labor_normalization": "Normalize payroll routing for lower labor burden",
    "normalization:vat_recovery": "Route recoverable-VAT spend to reduce NPC",
}


def generate_treaty_stacking_reinvestment_normalization_recommendations(
    collection: OpportunityCollection,
) -> list[Recommendation]:
    """STRUCTURAL recommendations for treaty, known-stack, known-category
    reinvestment, and normalization opportunities. No new economics: the
    dollar value is whatever the underlying opportunity already carries
    (usually None for these types — discovery never invented one either),
    and every qualitative fact (rate delta, weeks saved, payroll delta,
    VAT rate) is carried forward from the opportunity's own attributes,
    not recomputed."""
    recs: list[Recommendation] = []
    for opp in collection.opportunities:
        key = f"{opp.opportunity_type.value}:{opp.subtype}"
        title = _STRUCTURAL_OPPORTUNITY_TITLES.get(key)
        is_known_reinvestment = (
            opp.opportunity_type == OpportunityType.REINVESTMENT
            and opp.subtype.startswith("reinvestment_")
            and opp.subtype != "reinvestment_unknown"
        )
        if title is None and not is_known_reinvestment:
            continue
        if title is None:
            title = "Utilize known reinvestment channel"
        actions = tuple(f"Obtain approval: {a}." for a in opp.required_approvals) or (
            f"Confirm and execute: {opp.subtype.replace('_', ' ')}.",
        )
        recs.append(Recommendation(
            recommendation_id=f"REC-{opp.opportunity_id}",
            category=RecommendationCategory.STRUCTURAL,
            subtype=opp.subtype,
            title=title,
            description=opp.description,
            specific_actions=actions,
            jurisdiction_codes=opp.jurisdiction_codes,
            estimated_value_usd=opp.estimated_upside_usd,
            confidence=opp.confidence,
            opportunity_ids=(opp.opportunity_id,),
            evidence_reference=opp.blocking_requirements,
            authority_reference=(
                opp.graph_refs
                or ((opp.graph_rule_id,) if opp.graph_rule_id else ())
            ),
            requires_counsel_approval=bool(opp.required_approvals),
            source_ref=opp.source_ref,
            attributes={
                "confidence_gap": _confidence_gap(opp.confidence),
                "implementation_effort": EFFORT_BY_COMPLEXITY.get(opp.complexity, EFFORT_BY_COMPLEXITY["UNKNOWN"]),
                **opp.attributes,
            },
        ))
    return recs


def generate_candidate_recommendations(result: CompositionResult) -> list[Recommendation]:
    """
    Two STRUCTURAL/FINANCIAL views over Phase 7C's already-composed,
    already-priced candidates — no new composition, no new pricing:

    - a FINANCIAL 'structure_savings' recommendation for every fully-priced
      non-baseline candidate whose Risk-Adjusted NPC is strictly lower than
      the fully-priced baseline's — the value is a plain subtraction of
      two CaseResult.net_production_cost_usd figures the composer already
      computed via one build_risk_cases() call each.
    - a STRUCTURAL 'resolve_structure_constraints' recommendation for any
      candidate (baseline included) carrying unresolved StructureConstraints
      — surfacing what's already visible on the candidate, never resolving
      it here.
    """
    recs: list[Recommendation] = []
    baseline = next(
        (c for c in result.candidates if c.participating_jurisdictions == (result.baseline_jurisdiction,)),
        None,
    )

    if baseline is not None and baseline.is_fully_priced:
        baseline_npc = baseline.npc(RiskCase.RISK_ADJUSTED)
        for candidate in result.candidates:
            if candidate.candidate_id == baseline.candidate_id or not candidate.is_fully_priced:
                continue
            candidate_npc = candidate.npc(RiskCase.RISK_ADJUSTED)
            delta = round(baseline_npc - candidate_npc, 2)
            if delta <= 0:
                continue
            recs.append(Recommendation(
                recommendation_id=f"REC-CANDIDATE-SAVINGS-{candidate.candidate_id}",
                category=RecommendationCategory.FINANCIAL,
                subtype="structure_savings",
                title=f"Consider structure '{candidate.label}'",
                description=(
                    f"Structure '{candidate.label}' prices ${delta:,.2f} lower Risk-Adjusted "
                    f"Net Production Cost than the '{baseline.label}' baseline."
                ),
                specific_actions=(f"Evaluate feasibility of composing production across {candidate.label}.",),
                jurisdiction_codes=candidate.participating_jurisdictions,
                estimated_value_usd=delta,
                confidence=QualificationConfidence.MEDIUM,
                candidate_id=candidate.candidate_id,
                opportunity_ids=candidate.included_opportunity_ids,
                evidence_reference=(),
                authority_reference=candidate.evidence_graph_refs,
                requires_counsel_approval=bool(candidate.required_approvals),
                source_ref=candidate.candidate_id,
                attributes={
                    "confidence_gap": round(candidate.unknown_pct, 4),
                    "implementation_effort": DEFAULT_ACQUISITION_EFFORT,
                },
            ))

    for candidate in result.candidates:
        if not candidate.constraints:
            continue
        recs.append(Recommendation(
            recommendation_id=f"REC-CANDIDATE-CONSTRAINTS-{candidate.candidate_id}",
            category=RecommendationCategory.STRUCTURAL,
            subtype="resolve_structure_constraints",
            title=f"Resolve open constraints on '{candidate.label}'",
            description=(
                f"Structure '{candidate.label}' carries {len(candidate.constraints)} unresolved "
                "constraint(s) blocking full pricing/commitment."
            ),
            specific_actions=tuple(f"{c.kind}: {c.description}" for c in candidate.constraints),
            jurisdiction_codes=candidate.participating_jurisdictions,
            estimated_value_usd=None,
            confidence=QualificationConfidence.LOW,
            candidate_id=candidate.candidate_id,
            opportunity_ids=candidate.included_opportunity_ids,
            evidence_reference=tuple(c.description for c in candidate.constraints),
            authority_reference=tuple(
                t for c in candidate.constraints for t in c.acquisition_task_refs
            ) or candidate.evidence_graph_refs,
            requires_counsel_approval=any(c.kind in ("authority", "stacking_unknown") for c in candidate.constraints),
            source_ref=candidate.candidate_id,
            attributes={
                "confidence_gap": round(candidate.unknown_pct, 4) if candidate.unknown_pct else 1.0,
                "implementation_effort": DEFAULT_ACQUISITION_EFFORT,
            },
        ))
    return recs


# ── 7D-6: Cultural-test recommendation hooks ─────────────────────────────────

# test_slug -> (rule table, score function, deficit function). Every entry
# is imported directly from cultural_test_rules.py — no scoring logic is
# reimplemented here.
CULTURAL_TEST_REGISTRY: dict[str, dict[str, Any]] = {
    "uk_bfi_cultural_test": {
        "rules": ctr.UK_BFI_RULES, "score_fn": ctr.score_uk_bfi_test, "deficit_fn": ctr.get_uk_bfi_deficit,
    },
    "fr_cnc_cultural_test": {
        "rules": ctr.FR_CNC_RULES, "score_fn": ctr.score_fr_cnc_cultural_test, "deficit_fn": ctr.get_fr_cnc_deficit,
    },
    "ie_section_481_test": {
        "rules": ctr.IE_SECTION_481_RULES, "score_fn": ctr.score_ie_section_481_test, "deficit_fn": ctr.get_ie_section_481_deficit,
    },
    "eu_eurimages_test": {
        "rules": ctr.EU_EURIMAGES_RULES, "score_fn": ctr.score_eu_eurimages_test, "deficit_fn": ctr.get_eu_eurimages_deficit,
    },
    "ibermedia_test": {
        "rules": ctr.IBERMEDIA_RULES, "score_fn": ctr.score_ibermedia_test, "deficit_fn": ctr.get_ibermedia_deficit,
    },
    "ca_content_test": {
        "rules": ctr.CA_CONTENT_RULES, "score_fn": ctr.score_ca_content_test, "deficit_fn": ctr.get_ca_content_deficit,
    },
    "au_content_test": {
        "rules": ctr.AU_CONTENT_RULES, "score_fn": ctr.score_au_content_test, "deficit_fn": ctr.get_au_content_deficit,
    },
    "eu_european_convention_test": {
        "rules": ctr.EU_EUROPEAN_CONVENTION_RULES,
        "score_fn": ctr.score_eu_european_convention_test,
        "deficit_fn": ctr.get_eu_european_convention_deficit,
    },
}

# Deterministic, deliberately conservative classifier: only input_keys
# that name an individual creative role's nationality/origin or the
# work's own creative content (language, subject, script/rights, music)
# are treated as CREATIVE. Entity/company residency, spend thresholds,
# co-production share/concentration caps, and production-type gates are
# STRUCTURAL or FINANCIAL — they describe how the production is set up
# or financed, not who makes it or what it is about. Classification
# only, same discipline as opportunity_discovery._ROUTING_CLASSIFIERS —
# it adds no new legal theory, and under-classifying (leaving something
# out of this list) is the safe direction: it becomes a required-input-
# style structural gap note in specific_actions instead of a creative
# suggestion, never the reverse.
_CREATIVE_INPUT_KEY_PREFIXES: tuple[str, ...] = (
    "director_", "writer_", "lead_actor_", "lead_performer_",
    "second_lead_", "supporting_cast_", "dop_", "art_director_",
    "composer_", "editor_",
)
_CREATIVE_INPUT_KEYS_EXACT: frozenset[str] = frozenset({
    "producer_french",
    "producer_australian",
    "producer_british",
    "french_language_or_subject",
    "australian_script_or_rights",
    "australian_music",
    "director_or_writer_from_signatory_state",
})


def _is_creative_input_key(input_key: str) -> bool:
    if input_key in _CREATIVE_INPUT_KEYS_EXACT:
        return True
    return any(input_key.startswith(prefix) for prefix in _CREATIVE_INPUT_KEY_PREFIXES)


def _missing_input_keys(rules: list[dict], production_details: dict[str, Any]) -> list[str]:
    """Keys the rule table requires that are simply absent from
    production_details — distinct from present-but-False, matching this
    codebase's 'unknown must never collapse to excluded' discipline."""
    return sorted({r["input_key"] for r in rules if r["input_key"] not in production_details})


# Cultural-test slug (cultural_test_rules.py / CULTURAL_TEST_REGISTRY) ->
# the corresponding real incentive-PROGRAM slug in
# cultural_qualification_model.py, which is where hard eligibility gates
# (status == "required") actually live. Only programs where a clear 1:1
# correspondence exists are mapped — never invented for a program this
# codebase has no gate data for.
_GATE_PROGRAM_SLUGS: dict[str, str] = {
    "uk_bfi_cultural_test": "uk_avec",
    "fr_cnc_cultural_test": "fr_cnc_production",
    "ca_content_test": "ca_federal_cptc",
    "ie_section_481_test": "ie_section_481",
    "au_content_test": "au_producer_offset",
}


def generate_eligibility_gate_recommendations(
    role_known_codes: dict[str, tuple[str, ...]],
    relevant_test_slugs: tuple[str, ...],
    treaty_partner_code: str | None = None,
) -> list[Recommendation]:
    """
    THRESHOLD QUALIFICATION (runs conceptually BEFORE any points system):
    for every relevant test slug with a mapped incentive-program gate
    table, evaluate cultural_qualification_model.evaluate_program_
    eligibility(). A definitively FAILED required gate (a known fact
    contradicts a hard requirement — e.g. the director's only known
    nationality/residency is not Canadian/treaty, but ca_federal_cptc
    requires exactly that) produces ONE evidence-linked recommendation
    stating the production is categorically ineligible for that program
    regardless of any points score. INDETERMINATE gates (nobody on file
    for that role yet, or an EU/treaty-partner requirement this codebase
    cannot verify) are never reported as failures — 'unknown' never
    collapses to 'excluded' here either."""
    recs: list[Recommendation] = []
    for slug in sorted(set(relevant_test_slugs)):
        program_slug = _GATE_PROGRAM_SLUGS.get(slug)
        if program_slug is None:
            continue
        result = cqm.evaluate_program_eligibility(program_slug, role_known_codes, treaty_partner_code)
        if not result.has_failure:
            continue
        failed = [c for c in result.checks if c.status == cqm.GateStatus.FAILED]
        recs.append(Recommendation(
            recommendation_id=f"REC-ELIGIBILITY-GATE-{slug}",
            category=RecommendationCategory.CREATIVE,
            subtype="eligibility_gate_failed",
            title=f"Ineligible for {program_slug.replace('_', ' ')}: hard requirement not met",
            description=(
                f"'{program_slug}' has {len(failed)} unmet REQUIRED eligibility gate(s) — "
                f"the production cannot qualify for this program regardless of any cultural-"
                f"test points score, until these are resolved."
            ),
            specific_actions=tuple(
                f"{c.role}: {c.notes}" for c in failed
            ),
            confidence=QualificationConfidence.HIGH,
            evidence_reference=tuple(c.notes for c in failed),
            authority_reference=tuple(f"cultural_qualification_model.{program_slug}[{c.role}]" for c in failed),
            requires_producer_approval=True,
            requires_counsel_approval=CREATIVE_RECOMMENDATIONS_REQUIRE_COUNSEL,
            creative_impact=(
                f"Would require replacing or re-attaching the {'/'.join(c.role for c in failed)} "
                f"role with a national/resident/entity of the required jurisdiction."
            ),
            qualification_rationale=(
                f"Threshold eligibility gate (checked before any points system): "
                + "; ".join(c.notes for c in failed)
            ),
            trade_off_framing=(
                "This is a HARD eligibility requirement, not a scoring optimization — no amount "
                "of additional points elsewhere can offset a failed required gate for this program."
            ),
            source_ref=f"cultural_qualification_model.get_requirements({program_slug!r})",
            attributes={"program_slug": program_slug, "failed_roles": tuple(c.role for c in failed),
                        "confidence_gap": 0.0, "implementation_effort": 1.0},
        ))
    return recs


def generate_cultural_recommendations(
    cultural_test_inputs: dict[str, dict[str, Any]],
    relevant_test_slugs: tuple[str, ...],
) -> list[Recommendation]:
    """
    For each test_slug the caller has explicitly marked relevant to this
    production (a producer/counsel determination — this module never
    infers which cultural tests apply to a treaty or jurisdiction, since
    no existing engine carries that mapping):

    - if required input_keys are missing from cultural_test_inputs[slug]
      (or the slug has no entry at all), emit one REQUIRED_INPUT
      recommendation naming exactly which fields are needed. Never
      silently skipped, never assumed.
    - otherwise, score the test via its own existing score_fn. A passing
      test yields nothing — no recommendation is generated to change a
      creative decision that isn't blocking anything. A failing test
      yields one CREATIVE recommendation per failed, creative-classified
      criterion (via the existing deficit_fn / criterion_results, never
      reimplemented), each carrying its own creative_impact,
      qualification_rationale, and trade_off_framing.
    """
    recs: list[Recommendation] = []
    for slug in sorted(set(relevant_test_slugs)):
        entry = CULTURAL_TEST_REGISTRY.get(slug)
        if entry is None:
            continue
        details = cultural_test_inputs.get(slug)
        missing = _missing_input_keys(entry["rules"], details or {})
        if missing:
            recs.append(Recommendation(
                recommendation_id=f"REC-REQUIRED-INPUT-{slug}",
                category=RecommendationCategory.REQUIRED_INPUT,
                subtype="cultural_test_missing_inputs",
                title=f"Provide production details for {slug.replace('_', ' ')}",
                description=(
                    f"Cultural test '{slug}' cannot be evaluated — "
                    f"{len(missing)} required field(s) not yet supplied."
                ),
                specific_actions=tuple(f"Supply value for '{key}'." for key in missing),
                confidence=QualificationConfidence.NOT_APPLICABLE,
                evidence_reference=(),
                authority_reference=(f"cultural_test_rules.{slug}",),
                requires_producer_approval=True,
                requires_counsel_approval=False,
                source_ref=f"cultural_test_rules.CULTURAL_TEST_REGISTRY[{slug}]",
                attributes={"required_fields": tuple(missing), "confidence_gap": 1.0, "implementation_effort": 1.0},
            ))
            continue

        result: QualificationTestResult = entry["score_fn"](details)
        if result.passes_overall and result.passes_section_minimums:
            continue

        for cr in result.criterion_results:
            if cr.passed or not _is_creative_input_key(cr.input_key):
                continue
            recs.append(Recommendation(
                recommendation_id=f"REC-CULTURAL-{slug}-{cr.criterion_code}",
                category=RecommendationCategory.CREATIVE,
                subtype="cultural_test_gap",
                title=f"Consider: {cr.description}",
                description=(
                    f"'{slug}' scored {result.total_score}/{result.total_available} "
                    f"(minimum {result.minimum_required}); criterion {cr.criterion_code} "
                    f"({cr.description}) is unmet."
                ),
                specific_actions=(f"Review whether {cr.description.lower()} is achievable for this production.",),
                estimated_value_usd=None,
                confidence=QualificationConfidence.LOW,
                evidence_reference=(cr.description,),
                authority_reference=(f"cultural_test_rules.{slug}[{cr.criterion_code}]",),
                requires_producer_approval=True,
                requires_counsel_approval=CREATIVE_RECOMMENDATIONS_REQUIRE_COUNSEL,
                creative_impact=(
                    f"Would require a casting/crewing/creative decision affecting {cr.input_key.replace('_', ' ')}."
                ),
                qualification_rationale=(
                    f"{cr.criterion_code} ({cr.section}): {cr.scoring_rule} — "
                    f"currently {cr.awarded_points}/{cr.max_points} points; "
                    f"test requires >= {result.minimum_required}/{result.total_available} to pass."
                ),
                trade_off_framing=(
                    "This changes a creative attribution, not merely an operational structure — "
                    "the producer must weigh the qualification benefit against the creative "
                    "cost before deciding; incentive value alone is never sufficient justification."
                ),
                source_ref=f"cultural_test_rules.{slug}",
                attributes={"confidence_gap": 1.0, "implementation_effort": 1.0, "test_slug": slug},
            ))
    return recs


# ── Dedup / ranking / top-level ──────────────────────────────────────────────

def dedupe_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    seen: set[str] = set()
    unique: list[Recommendation] = []
    for rec in recommendations:
        if rec.recommendation_id in seen:
            continue
        seen.add(rec.recommendation_id)
        unique.append(rec)
    return unique


def rank_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    """Deterministic: primary sort on recommendation_rank_score
    (descending), ties broken by recommendation_id — same discipline as
    opportunity_discovery.rank_opportunities()."""
    return sorted(recommendations, key=lambda r: (-r.recommendation_rank_score, r.recommendation_id))


def generate_production_recommendations(
    collection: OpportunityCollection,
    composition_result: Optional[CompositionResult] = None,
    register: Optional[list[AccountQualification]] = None,
    rate: Optional[float] = None,
    jurisdiction_code: str = "MU",
    cultural_test_inputs: Optional[dict[str, dict[str, Any]]] = None,
    relevant_cultural_test_slugs: tuple[str, ...] = (),
    role_known_codes: Optional[dict[str, tuple[str, ...]]] = None,
    treaty_partner_code: Optional[str] = None,
) -> RecommendationSet:
    """
    Top-level Phase 7D entry point. register/rate are required to derive
    Levers for structuring recommendations (the same optional-input
    discipline compose_production_structures/build_risk_cases already
    use — omit them and structuring recommendations are honestly skipped
    rather than guessed at). composition_result is optional; when absent,
    candidate-comparison recommendations are skipped. cultural_test_inputs/
    relevant_cultural_test_slugs are optional; when relevant_cultural_test_slugs
    is empty, no cultural or required-input recommendations are generated
    at all (this module never infers which tests apply). role_known_codes
    (from production_package_intelligence.production_package_to_role_
    known_codes) drives the THRESHOLD eligibility-gate check, which runs
    before and independent of the points-based cultural recommendations —
    omit it and gate recommendations are honestly skipped, never guessed.
    """
    recs: list[Recommendation] = []
    recs += generate_grey_area_recommendations(collection)
    recs += generate_evidence_acquisition_recommendations(collection)
    if register is not None and rate is not None:
        recs += generate_structuring_recommendations(collection, register=register, rate=rate, jurisdiction_code=jurisdiction_code)
    recs += generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
    if composition_result is not None:
        recs += generate_candidate_recommendations(composition_result)
    if relevant_cultural_test_slugs and role_known_codes is not None:
        recs += generate_eligibility_gate_recommendations(
            role_known_codes, relevant_cultural_test_slugs, treaty_partner_code,
        )
    if relevant_cultural_test_slugs:
        recs += generate_cultural_recommendations(cultural_test_inputs or {}, relevant_cultural_test_slugs)

    return RecommendationSet(
        baseline_jurisdiction=collection.baseline_jurisdiction,
        passes_run=RECOMMENDATION_PASSES,
        recommendations=rank_recommendations(dedupe_recommendations(recs)),
    )


# ── Public re-exports (Phase 7 closeout) ──────────────────────────────────────
# Purely additive aliases — zero behavior change to anything above. Exposed so
# creative_qualification_engine.py can reuse this module's exact creative-
# attribute classification instead of maintaining a second copy ("one source
# of truth" — see production_package_intelligence.py's Part D docstring).
CREATIVE_INPUT_KEY_PREFIXES = _CREATIVE_INPUT_KEY_PREFIXES
CREATIVE_INPUT_KEYS_EXACT = _CREATIVE_INPUT_KEYS_EXACT
is_creative_input_key = _is_creative_input_key
