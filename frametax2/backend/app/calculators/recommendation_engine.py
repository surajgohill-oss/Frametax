"""
recommendation_engine.py

Phase 7D-1 through 7D-4 of CineGlobe: the Production Optimization
Recommendation Engine (core).

Every engine through Phase 7C answers "what is possible?" (Opportunity
Discovery), "what combinations are internally consistent?" (Production
Structure Composer), or "what does each combination cost?" (the
Optimizer / Global Scenario Ranker). This module answers the question a
producer actually asks: "what should I change?"

A Recommendation is not a new fact — it is an existing Opportunity (or a
small dependency-linked group of them) reframed as an addressable,
ranked, gated *action*: who must approve it, what evidence it still
needs, how reversible it is, and — where an existing engine can compute
it — what accepting it does to risk-adjusted Net Production Cost.

Scope of this phase (7D-1..7D-4 only):

- FINANCIAL and STRUCTURAL domain generation only. PRODUCTION and
  CREATIVE domains exist in the type system (RecommendationDomain,
  RecommendationType, CreativeElement, CreativeImpact) for forward
  compatibility, but no generator emits them yet — deferred to 7D-5/7D-6
  once production-plan/script inputs and broader cultural-test coverage
  exist.
- The creative guardrail is implemented and enforced at construction
  time even though nothing generates CREATIVE recommendations yet: a
  CREATIVE-domain Recommendation cannot be constructed without an
  explicit trade-off statement, a non-NOT_APPLICABLE creative impact, at
  least PRODUCER approval, a confidence, and an Evidence Graph reference.
  This is deliberate — the guardrail must exist and be testable before
  any code path can produce a creative recommendation, not bolted on
  after 7D-6 ships.

What this module does NOT do:

- It performs no legal research and writes nothing to the Evidence
  Graph, the Jurisdiction Graph, LAAE's docket, or any registry — it
  only *references* existing graph nodes, rule/absence ids, and
  AcquisitionTask ids by their existing deterministic naming.
- It invents no dollar figures. estimated_upside_usd /
  estimated_downside_usd / npc_impact are copied from what an existing
  engine already computed (an Opportunity's own upside, or a fresh
  build_risk_cases() call via price_recommendations()) — never derived
  by ad hoc arithmetic on top of that.
- It does not modify optimization_engine.py, opportunity_discovery.py,
  global_scenario_ranker.py, production_structure_composer.py,
  authority_score.py, or evidence_graph.py. price_recommendations() only
  *calls* build_risk_cases() with the same inputs any other caller would
  supply.
- Accepting a Recommendation (status -> ACCEPTED) does not, by itself,
  execute anything against the optimizer, the Composer, or the Evidence
  Graph. It only records that the producer/counsel decision was made;
  translating an ACCEPTED recommendation into an AssumptionOverride or a
  Composer input is future (post-7D) wiring.

Deterministic throughout: recommendation ids are derived directly from
their source opportunity id (REC-<opportunity_id>), so generation,
dependency resolution, and ranking are all reproducible given the same
OpportunityCollection.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators.opportunity_discovery import Opportunity, OpportunityCollection, OpportunityType
from app.calculators.optimization_engine import (
    CONFIDENCE_WEIGHTS,
    AssumptionOverride,
    RiskCase,
    build_risk_cases,
)
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationConfidence,
)
from app.calculators.structuring_paths import StructuringPath

RECOMMENDATION_ENGINE_VERSION = "1.0.0"


# ── Enums ─────────────────────────────────────────────────────────────────

class RecommendationDomain(str, enum.Enum):
    FINANCIAL = "financial"
    STRUCTURAL = "structural"
    PRODUCTION = "production"    # 7D-5, not generated yet
    CREATIVE = "creative"        # 7D-6, not generated yet


class RecommendationType(str, enum.Enum):
    # FINANCIAL
    CLAIM_INCENTIVE = "claim_incentive"
    RESOLVE_GREY_AREA = "resolve_grey_area"
    PURSUE_REINVESTMENT = "pursue_reinvestment"
    NORMALIZE_TIMING = "normalize_timing"
    NORMALIZE_LABOR_COST = "normalize_labor_cost"
    NORMALIZE_VAT_RECOVERY = "normalize_vat_recovery"
    APPLY_FOR_FUND = "apply_for_fund"
    # STRUCTURAL
    EXECUTE_STRUCTURING_LEVER = "execute_structuring_lever"
    ADOPT_TREATY_STRUCTURE = "adopt_treaty_structure"
    PURSUE_STACKING = "pursue_stacking"
    FORM_SPV = "form_spv"
    ENGAGE_EMPLOYER_OF_RECORD = "engage_employer_of_record"
    REROUTE_VENDOR = "reroute_vendor"
    REROUTE_PAYROLL = "reroute_payroll"
    # PRODUCTION — reserved for 7D-5, no generator emits these yet
    RELOCATE_PRINCIPAL_PHOTOGRAPHY = "relocate_principal_photography"
    RELOCATE_POST_PRODUCTION = "relocate_post_production"
    RELOCATE_VFX = "relocate_vfx"
    RELOCATE_SOUND_MIX = "relocate_sound_mix"
    RELOCATE_MUSIC_RECORDING = "relocate_music_recording"
    RELOCATE_MARINE_WORK = "relocate_marine_work"
    SPLIT_SECOND_UNIT = "split_second_unit"
    SHIFT_SCHEDULE = "shift_schedule"
    # CREATIVE — reserved for 7D-6, no generator emits these yet
    KEY_TALENT_NATIONALITY = "key_talent_nationality"
    CULTURAL_TEST_POINTS = "cultural_test_points"
    LANGUAGE_ELECTION = "language_election"
    SETTING_ELECTION = "setting_election"
    SOURCE_MATERIAL_ELECTION = "source_material_election"
    LOCAL_CULTURAL_CONTRIBUTION = "local_cultural_contribution"


class RecommendationStatus(str, enum.Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    SUPERSEDED = "superseded"


class CreativeElement(str, enum.Enum):
    """Reserved for 7D-6 generation — usable today only to construct a
    guardrail-compliant CREATIVE recommendation by hand (e.g. in tests)."""
    LEAD_ACTOR = "lead_actor"
    DIRECTOR = "director"
    WRITER = "writer"
    PRODUCER = "producer"
    DEPARTMENT_HEAD = "department_head"
    LANGUAGE = "language"
    SETTING = "setting"
    SOURCE_MATERIAL = "source_material"
    SUBJECT_MATTER = "subject_matter"
    LOCAL_CULTURAL_CONTRIBUTION = "local_cultural_contribution"


class CreativeImpact(str, enum.Enum):
    NOT_APPLICABLE = "not_applicable"
    OPTIONAL = "optional"
    MATERIAL = "material"
    HIGH_IMPACT = "high_impact"


class ApprovalGate(str, enum.Enum):
    NONE = "none"
    PRODUCER = "producer"
    COUNSEL = "counsel"
    PRODUCER_AND_COUNSEL = "producer_and_counsel"


# Ordering for "at least PRODUCER" comparisons. PRODUCER and COUNSEL are
# peer tiers (either alone satisfies "at least one gate"); only NONE is
# below both and only PRODUCER_AND_COUNSEL is above both.
_APPROVAL_GATE_ORDER: dict[ApprovalGate, int] = {
    ApprovalGate.NONE: 0,
    ApprovalGate.PRODUCER: 1,
    ApprovalGate.COUNSEL: 1,
    ApprovalGate.PRODUCER_AND_COUNSEL: 2,
}

_REQUIRED_APPROVER_ROLES: dict[ApprovalGate, frozenset] = {
    ApprovalGate.NONE: frozenset(),
    ApprovalGate.PRODUCER: frozenset({"producer"}),
    ApprovalGate.COUNSEL: frozenset({"counsel"}),
    ApprovalGate.PRODUCER_AND_COUNSEL: frozenset({"producer", "counsel"}),
}


class Reversibility(str, enum.Enum):
    REVERSIBLE = "reversible"
    COSTLY_TO_REVERSE = "costly_to_reverse"
    IRREVERSIBLE = "irreversible"


class RecommendationTier(str, enum.Enum):
    ACTIONABLE = "actionable"
    GATED = "gated"
    INFORMATIONAL = "informational"


# ── Recommendation object ────────────────────────────────────────────────

@dataclass
class Recommendation:
    """
    One ranked, addressable action. Non-creative recommendations leave
    every creative field at its default and are otherwise unconstrained;
    CREATIVE-domain recommendations are validated at construction time
    against the guardrail in __post_init__ — see module docstring.
    """
    recommendation_id: str
    recommendation_type: RecommendationType
    domain: RecommendationDomain
    headline: str
    detail: str
    affected_budget_lines: tuple[str, ...] = ()
    affected_creative_elements: tuple[CreativeElement, ...] = ()
    affected_jurisdictions: tuple[str, ...] = ()
    structure_impact: tuple[str, ...] = ()  # ProductionStructureCandidate ids, or ("NEW_CANDIDATE",)
    estimated_upside_usd: Optional[float] = None
    estimated_downside_usd: Optional[float] = None
    implementation_cost_usd: Optional[float] = None
    npc_impact: Optional[dict[RiskCase, float]] = None  # positive = NPC improves if accepted
    confidence: QualificationConfidence = QualificationConfidence.LOW
    authority_score: Optional[float] = None
    required_evidence: tuple[str, ...] = ()
    graph_rule_id: Optional[str] = None
    graph_absence_id: Optional[str] = None
    acquisition_task_refs: tuple[str, ...] = ()
    approval_gate: ApprovalGate = ApprovalGate.NONE
    creative_impact: CreativeImpact = CreativeImpact.NOT_APPLICABLE
    reversibility: Reversibility = Reversibility.REVERSIBLE
    schedule_impact_weeks: Optional[int] = None
    source_opportunity_ids: tuple[str, ...] = ()
    dependent_recommendation_ids: tuple[str, ...] = ()
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    attributes: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            raise ValueError("recommendation_id is required.")
        if self.domain != RecommendationDomain.CREATIVE:
            if self.creative_impact != CreativeImpact.NOT_APPLICABLE:
                raise ValueError(
                    f"Recommendation '{self.recommendation_id}': creative_impact may only be "
                    "set on CREATIVE-domain recommendations."
                )
            if self.affected_creative_elements:
                raise ValueError(
                    f"Recommendation '{self.recommendation_id}': affected_creative_elements may "
                    "only be set on CREATIVE-domain recommendations."
                )
        else:
            self._validate_creative_guardrail()

    def _validate_creative_guardrail(self) -> None:
        """
        Enforced even though no generator emits CREATIVE recommendations
        yet (7D-6 is deferred): the guardrail is part of the object model,
        not an afterthought bolted on once generation exists. A CREATIVE
        recommendation is unconstructible unless it states the trade-off
        explicitly, names a real creative impact, gates on at least
        PRODUCER approval, carries a confidence, and traces to the
        Evidence Graph (a rule or an absence — never neither).
        """
        rid = self.recommendation_id
        if self.creative_impact == CreativeImpact.NOT_APPLICABLE:
            raise ValueError(
                f"CREATIVE recommendation '{rid}' requires creative_impact other than NOT_APPLICABLE."
            )
        if _APPROVAL_GATE_ORDER[self.approval_gate] < _APPROVAL_GATE_ORDER[ApprovalGate.PRODUCER]:
            raise ValueError(
                f"CREATIVE recommendation '{rid}' requires approval_gate of at least PRODUCER."
            )
        if not (self.graph_rule_id or self.graph_absence_id):
            raise ValueError(
                f"CREATIVE recommendation '{rid}' requires an Evidence Graph reference "
                "(graph_rule_id or graph_absence_id) — a creative trade-off must trace to "
                "real authority, not an assumption."
            )
        if not self.required_evidence:
            raise ValueError(
                f"CREATIVE recommendation '{rid}' requires a stated qualification reason — "
                "required_evidence must name what test/treaty provision this serves."
            )
        if self.confidence is None:
            raise ValueError(f"CREATIVE recommendation '{rid}' requires an explicit confidence.")
        headline_and_detail = f"{self.headline} {self.detail}".lower()
        if "trade-off" not in headline_and_detail:
            raise ValueError(
                f"CREATIVE recommendation '{rid}' must state the trade-off explicitly "
                "(headline or detail must contain 'trade-off') — a creative change may "
                "never be framed as being for incentive purposes alone."
            )


# ── Ranked result ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RankedRecommendation:
    recommendation_id: str
    tier: RecommendationTier
    score: float
    rank: int


@dataclass
class RecommendationRankingResult:
    recommendations: list[Recommendation]  # ordered: ACTIONABLE, then GATED, then INFORMATIONAL
    ranked: list[RankedRecommendation]

    def by_tier(self, tier: RecommendationTier) -> list[Recommendation]:
        ids = {r.recommendation_id for r in self.ranked if r.tier == tier}
        return [r for r in self.recommendations if r.recommendation_id in ids]


# ── Generation: FINANCIAL ────────────────────────────────────────────────

_NORMALIZATION_TYPE_BY_SUBTYPE: dict[str, RecommendationType] = {
    "fund_timing": RecommendationType.NORMALIZE_TIMING,
    "labor_normalization": RecommendationType.NORMALIZE_LABOR_COST,
    "vat_recovery": RecommendationType.NORMALIZE_VAT_RECOVERY,
    "application_timing_unknown": RecommendationType.NORMALIZE_TIMING,
}

_NORMALIZATION_GATE_BY_SUBTYPE: dict[str, ApprovalGate] = {
    "fund_timing": ApprovalGate.PRODUCER,
    "labor_normalization": ApprovalGate.PRODUCER,
    "vat_recovery": ApprovalGate.PRODUCER,
    "application_timing_unknown": ApprovalGate.PRODUCER,
}


def _financial_from_grey_area(opp: Opportunity) -> Recommendation:
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=RecommendationType.RESOLVE_GREY_AREA,
        domain=RecommendationDomain.FINANCIAL,
        headline=f"Resolve grey area: {opp.opportunity_id}",
        detail=opp.description,
        affected_budget_lines=opp.affected_accounts,
        affected_jurisdictions=opp.jurisdiction_codes,
        estimated_upside_usd=opp.estimated_upside_usd,
        estimated_downside_usd=opp.estimated_downside_usd,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=ApprovalGate.COUNSEL,
        reversibility=Reversibility.REVERSIBLE,
        source_opportunity_ids=(opp.opportunity_id,),
    )


def _financial_from_reinvestment(opp: Opportunity) -> Recommendation:
    is_unknown = opp.subtype == "reinvestment_unknown"
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=RecommendationType.PURSUE_REINVESTMENT,
        domain=RecommendationDomain.FINANCIAL,
        headline=(
            f"Investigate reinvestment treatment in {opp.jurisdiction_codes[0]}"
            if is_unknown else
            f"Pursue reinvestment structure in {opp.jurisdiction_codes[0]}"
        ),
        detail=opp.description,
        affected_jurisdictions=opp.jurisdiction_codes,
        estimated_upside_usd=opp.estimated_upside_usd,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=ApprovalGate.COUNSEL if is_unknown else ApprovalGate.PRODUCER,
        reversibility=Reversibility.REVERSIBLE,
        source_opportunity_ids=(opp.opportunity_id,),
    )


def _financial_from_normalization(opp: Opportunity, opp_id_generated: set[str]) -> Optional[Recommendation]:
    rec_type = _NORMALIZATION_TYPE_BY_SUBTYPE.get(opp.subtype)
    if rec_type is None:
        return None
    dependent_ids = tuple(
        f"REC-{d}" for d in opp.dependent_opportunity_ids if f"REC-{d}" in opp_id_generated
    )
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=rec_type,
        domain=RecommendationDomain.FINANCIAL,
        headline=f"Normalize NPC via {opp.subtype.replace('_', ' ')}",
        detail=opp.description,
        affected_jurisdictions=opp.jurisdiction_codes,
        estimated_upside_usd=opp.estimated_upside_usd,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=_NORMALIZATION_GATE_BY_SUBTYPE.get(opp.subtype, ApprovalGate.PRODUCER),
        reversibility=Reversibility.REVERSIBLE,
        source_opportunity_ids=(opp.opportunity_id,),
        dependent_recommendation_ids=dependent_ids,
        attributes=dict(opp.attributes),
    )


def generate_financial_recommendations(collection: OpportunityCollection) -> list[Recommendation]:
    """
    One Recommendation per source Opportunity — grey areas, reinvestment
    (known and unknown), and normalization (fund timing, labor, VAT
    recovery, application-timing unknowns). Nothing is invented: every
    field traces to the source Opportunity's own data. Dependency links
    (e.g. a VAT-recovery normalization depending on a relocation) are
    only preserved when the depended-on opportunity was itself turned
    into a recommendation in this same call.
    """
    generated: list[Recommendation] = []
    for opp in sorted(collection.opportunities, key=lambda o: o.opportunity_id):
        if opp.opportunity_type == OpportunityType.GREY_AREA:
            generated.append(_financial_from_grey_area(opp))
        elif opp.opportunity_type == OpportunityType.REINVESTMENT:
            generated.append(_financial_from_reinvestment(opp))

    generated_ids = {r.recommendation_id for r in generated}
    for opp in sorted(collection.opportunities, key=lambda o: o.opportunity_id):
        if opp.opportunity_type == OpportunityType.NORMALIZATION:
            rec = _financial_from_normalization(opp, generated_ids)
            if rec is not None:
                generated.append(rec)
                generated_ids.add(rec.recommendation_id)

    return generated


# ── Generation: STRUCTURAL ───────────────────────────────────────────────

_STRUCTURING_SUBTYPE_TO_REC_TYPE: dict[str, RecommendationType] = {
    "spv_routing": RecommendationType.FORM_SPV,
    "employer_of_record": RecommendationType.ENGAGE_EMPLOYER_OF_RECORD,
    "payroll_routing": RecommendationType.REROUTE_PAYROLL,
    "vendor_routing": RecommendationType.REROUTE_VENDOR,
}

_REVERSIBILITY_BY_COMPLEXITY: dict[str, Reversibility] = {
    "LOW": Reversibility.REVERSIBLE,
    "MEDIUM": Reversibility.COSTLY_TO_REVERSE,
    "HIGH": Reversibility.IRREVERSIBLE,
    "UNKNOWN": Reversibility.COSTLY_TO_REVERSE,
}


def _structural_from_structuring(opp: Opportunity) -> Recommendation:
    rec_type = _STRUCTURING_SUBTYPE_TO_REC_TYPE.get(opp.subtype, RecommendationType.EXECUTE_STRUCTURING_LEVER)
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=rec_type,
        domain=RecommendationDomain.STRUCTURAL,
        headline=f"Execute structuring lever on {', '.join(opp.affected_accounts) or 'unspecified account'}",
        detail=opp.description,
        affected_budget_lines=opp.affected_accounts,
        affected_jurisdictions=opp.jurisdiction_codes,
        estimated_upside_usd=opp.estimated_upside_usd,
        implementation_cost_usd=opp.implementation_cost_usd,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=ApprovalGate.PRODUCER,
        reversibility=_REVERSIBILITY_BY_COMPLEXITY.get(opp.complexity, Reversibility.COSTLY_TO_REVERSE),
        source_opportunity_ids=(opp.opportunity_id,),
    )


def _structural_from_treaty(opp: Opportunity, opp_id_generated: set[str]) -> Recommendation:
    dependent_ids = tuple(
        f"REC-{d}" for d in opp.dependent_opportunity_ids if f"REC-{d}" in opp_id_generated
    )
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=RecommendationType.ADOPT_TREATY_STRUCTURE,
        domain=RecommendationDomain.STRUCTURAL,
        headline=f"Adopt treaty structure: {opp.subtype.replace('_', ' ')}",
        detail=opp.description,
        affected_jurisdictions=opp.jurisdiction_codes,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=ApprovalGate.COUNSEL,
        reversibility=Reversibility.IRREVERSIBLE,
        source_opportunity_ids=(opp.opportunity_id,),
        dependent_recommendation_ids=dependent_ids,
    )


def _structural_from_stacking(opp: Opportunity) -> Recommendation:
    is_known = opp.subtype == "known_stack"
    return Recommendation(
        recommendation_id=f"REC-{opp.opportunity_id}",
        recommendation_type=RecommendationType.PURSUE_STACKING,
        domain=RecommendationDomain.STRUCTURAL,
        headline=(
            "Combine known-compatible incentive programs"
            if is_known else
            "Investigate stacking eligibility (not yet established)"
        ),
        detail=opp.description,
        affected_jurisdictions=opp.jurisdiction_codes,
        confidence=opp.confidence,
        authority_score=opp.authority_score,
        required_evidence=opp.required_evidence,
        graph_rule_id=opp.graph_rule_id,
        graph_absence_id=opp.graph_absence_id,
        acquisition_task_refs=opp.acquisition_task_refs,
        approval_gate=ApprovalGate.PRODUCER if is_known else ApprovalGate.COUNSEL,
        reversibility=Reversibility.REVERSIBLE,
        source_opportunity_ids=(opp.opportunity_id,),
    )


def generate_structural_recommendations(collection: OpportunityCollection) -> list[Recommendation]:
    """
    One Recommendation per source Opportunity — structuring levers (SPV /
    EoR / vendor / payroll / general, per Discovery's own routing
    classification), treaty compositions (bilateral, nationality unlocks,
    multilateral memberships, convention-composition paths), and stacking
    (known — real STACKS_WITH evidence — and unknown, which is framed as
    "investigate," never "combine"). Never invents stackability, treaties,
    or routing beyond what Discovery already found.
    """
    generated: list[Recommendation] = []
    for opp in sorted(collection.opportunities, key=lambda o: o.opportunity_id):
        if opp.opportunity_type == OpportunityType.STRUCTURING:
            generated.append(_structural_from_structuring(opp))
        elif opp.opportunity_type == OpportunityType.STACKING:
            generated.append(_structural_from_stacking(opp))

    generated_ids = {r.recommendation_id for r in generated}
    for opp in sorted(collection.opportunities, key=lambda o: o.opportunity_id):
        if opp.opportunity_type == OpportunityType.TREATY:
            rec = _structural_from_treaty(opp, generated_ids)
            generated.append(rec)
            generated_ids.add(rec.recommendation_id)

    return generated


def generate_recommendations(collection: OpportunityCollection) -> list[Recommendation]:
    """Top-level 7D-1..7D-4 generator: FINANCIAL + STRUCTURAL only.
    PRODUCTION and CREATIVE generation is deferred (7D-5 / 7D-6)."""
    return generate_financial_recommendations(collection) + generate_structural_recommendations(collection)


# ── Pricing (7D core: structuring levers + grey areas only) ─────────────

def price_recommendations(
    recommendations: list[Recommendation],
    register: list[AccountQualification],
    gross_budget_usd: float,
    rate: float,
    all_structuring_paths: list[StructuringPath],
    all_grey_areas: list[GreyAreaItem],
    delay_weeks: int = 39,
    bridge_rate: float = 0.08,
    jurisdiction_code: str = "MU",
) -> None:
    """
    Sets npc_impact (delta per risk case; positive = NPC improves) on
    recommendations whose source opportunity has a clean, existing
    acceptance mechanism to diff against: a structuring lever (accepted =
    the matching StructuringPath overridden to EXECUTED) or a grey area
    (accepted = the matching GreyAreaItem overridden to RESOLVED_INCLUDE).
    Both overrides reuse optimization_engine.AssumptionOverride and its
    existing validation exactly as any direct caller of build_risk_cases
    would — no new override logic is introduced here.

    Every other recommendation (reinvestment, normalization, treaty,
    stacking) is left with npc_impact=None: there is no existing,
    unambiguous "accept this" toggle for those in the current optimizer
    model, so the ranking formula falls back to their estimated_upside_usd
    as informational support only, never as a booked NPC figure.

    Mutates the passed-in Recommendation objects' npc_impact field in
    place; does not mutate register, all_structuring_paths, or
    all_grey_areas — build_risk_cases() deep-copies both before applying
    any override.
    """
    baseline = build_risk_cases(
        register=register, gross_budget_usd=gross_budget_usd, rate=rate,
        structuring_paths=all_structuring_paths, grey_areas=all_grey_areas,
        delay_weeks=delay_weeks, bridge_rate=bridge_rate, jurisdiction_code=jurisdiction_code,
    ).cases

    path_ids = {p.path_id for p in all_structuring_paths}
    grey_ids = {g.item_id for g in all_grey_areas}
    open_grey_ids = {g.item_id for g in all_grey_areas if g.status == GreyAreaStatus.OPEN}

    for rec in recommendations:
        if len(rec.source_opportunity_ids) != 1:
            continue
        source_id = rec.source_opportunity_ids[0]

        if rec.domain == RecommendationDomain.STRUCTURAL and source_id.startswith("OPP-STRUCT-"):
            lever_id = source_id.removeprefix("OPP-STRUCT-")
            if lever_id not in path_ids:
                continue
            accepted = build_risk_cases(
                register=register, gross_budget_usd=gross_budget_usd, rate=rate,
                structuring_paths=all_structuring_paths, grey_areas=all_grey_areas,
                delay_weeks=delay_weeks, bridge_rate=bridge_rate, jurisdiction_code=jurisdiction_code,
                overrides=[AssumptionOverride(
                    item_id=lever_id, item_type="structuring_path", to_status="executed",
                    approver_role="producer", evidence="Pricing preview — not an actual filing.",
                )],
            ).cases
            rec.npc_impact = {
                case: round(baseline[case].net_production_cost_usd - accepted[case].net_production_cost_usd, 2)
                for case in RiskCase
            }

        elif rec.recommendation_type == RecommendationType.RESOLVE_GREY_AREA and source_id.startswith("OPP-GREY-"):
            grey_item_id = source_id.removeprefix("OPP-GREY-")
            if grey_item_id not in open_grey_ids:
                continue
            accepted = build_risk_cases(
                register=register, gross_budget_usd=gross_budget_usd, rate=rate,
                structuring_paths=all_structuring_paths, grey_areas=all_grey_areas,
                delay_weeks=delay_weeks, bridge_rate=bridge_rate, jurisdiction_code=jurisdiction_code,
                overrides=[AssumptionOverride(
                    item_id=grey_item_id, item_type="grey_area", to_status="resolved_include",
                    approver_role="counsel", evidence="Pricing preview — not an actual ruling.",
                )],
            ).cases
            rec.npc_impact = {
                case: round(baseline[case].net_production_cost_usd - accepted[case].net_production_cost_usd, 2)
                for case in RiskCase
            }


# ── Ranking ───────────────────────────────────────────────────────────────

DEFAULT_PRODUCTION_WEEKS = 12.0

_CERTAINTY_BY_CONFIDENCE: dict[QualificationConfidence, float] = {
    QualificationConfidence.HIGH: 1.0,
    QualificationConfidence.MEDIUM: 0.75,
    QualificationConfidence.LOW: 0.4,
    QualificationConfidence.NOT_APPLICABLE: 0.4,
}

_REVERSIBILITY_FACTOR: dict[Reversibility, float] = {
    Reversibility.REVERSIBLE: 1.0,
    Reversibility.COSTLY_TO_REVERSE: 0.85,
    Reversibility.IRREVERSIBLE: 0.7,
}

_APPROVAL_BURDEN: dict[ApprovalGate, float] = {
    ApprovalGate.NONE: 0.0,
    ApprovalGate.PRODUCER: 0.25,
    ApprovalGate.COUNSEL: 0.5,
    ApprovalGate.PRODUCER_AND_COUNSEL: 0.75,
}

AUTHORITY_SCORE_HIGH_THRESHOLD = 75.0
AUTHORITY_SCORE_MEDIUM_THRESHOLD = 40.0


def classify_tier(rec: Recommendation) -> RecommendationTier:
    """
    ACTIONABLE   — npc_impact is priced AND no outstanding LAAE task /
                   absence-terminus blocks it.
    GATED        — npc_impact is priced but blocked on an acquisition
                   task or an absence-of-authority terminus (authority
                   score 0.0).
    INFORMATIONAL — no npc_impact exists (nothing to price it against
                   yet); estimated_upside_usd, if any, is informational
                   support only, never a ranked NPC figure.
    """
    if rec.npc_impact is None:
        return RecommendationTier.INFORMATIONAL
    if rec.acquisition_task_refs or rec.authority_score == 0.0:
        return RecommendationTier.GATED
    return RecommendationTier.ACTIONABLE


def _certainty_factor(rec: Recommendation) -> float:
    if rec.authority_score == 0.0:
        return 0.25
    if rec.authority_score is not None:
        if rec.authority_score >= AUTHORITY_SCORE_HIGH_THRESHOLD:
            return 1.0
        if rec.authority_score >= AUTHORITY_SCORE_MEDIUM_THRESHOLD:
            return 0.75
        return 0.4
    return _CERTAINTY_BY_CONFIDENCE[rec.confidence]


def _friction_factor(rec: Recommendation, production_weeks: float) -> float:
    schedule_term = (rec.schedule_impact_weeks or 0) / production_weeks if production_weeks else 0.0
    return 1.0 / (1.0 + _APPROVAL_BURDEN[rec.approval_gate] + schedule_term)


def score_recommendation(rec: Recommendation, production_weeks: float = DEFAULT_PRODUCTION_WEEKS) -> float:
    """
    Stage-2 score. Only meaningful for priced (ACTIONABLE/GATED)
    recommendations — informational recommendations always score 0.0 and
    are ordered purely by id, never mixed into the priced ranking by
    score alone (see rank_recommendations' tier partition).
    """
    if rec.npc_impact is None:
        return 0.0
    ra_improvement = rec.npc_impact[RiskCase.RISK_ADJUSTED]
    confidence_weight = CONFIDENCE_WEIGHTS[rec.confidence]
    raw = (ra_improvement * confidence_weight) - (rec.implementation_cost_usd or 0.0)
    return raw * _certainty_factor(rec) * _REVERSIBILITY_FACTOR[rec.reversibility] * _friction_factor(rec, production_weeks)


def rank_recommendations(
    recommendations: list[Recommendation],
    production_weeks: float = DEFAULT_PRODUCTION_WEEKS,
) -> RecommendationRankingResult:
    """
    Two-stage, deterministic: partition into ACTIONABLE / GATED /
    INFORMATIONAL (never blended), each tier internally sorted by score
    descending with recommendation_id as the tie-break. Informational
    recommendations are always ordered after every priced recommendation,
    structurally — not merely because their score happens to be low.
    """
    tiers = {rec.recommendation_id: classify_tier(rec) for rec in recommendations}
    scores = {rec.recommendation_id: score_recommendation(rec, production_weeks) for rec in recommendations}

    def _tier_group(tier: RecommendationTier) -> list[Recommendation]:
        group = [r for r in recommendations if tiers[r.recommendation_id] == tier]
        if tier == RecommendationTier.INFORMATIONAL:
            return sorted(group, key=lambda r: r.recommendation_id)
        return sorted(group, key=lambda r: (-scores[r.recommendation_id], r.recommendation_id))

    ordered = (
        _tier_group(RecommendationTier.ACTIONABLE)
        + _tier_group(RecommendationTier.GATED)
        + _tier_group(RecommendationTier.INFORMATIONAL)
    )
    ranked = [
        RankedRecommendation(
            recommendation_id=r.recommendation_id, tier=tiers[r.recommendation_id],
            score=scores[r.recommendation_id], rank=i,
        )
        for i, r in enumerate(ordered, start=1)
    ]
    return RecommendationRankingResult(recommendations=ordered, ranked=ranked)


# ── Lifecycle ─────────────────────────────────────────────────────────────

def submit_for_review(rec: Recommendation) -> Recommendation:
    if rec.status != RecommendationStatus.PROPOSED:
        raise ValueError(f"Recommendation '{rec.recommendation_id}' is not PROPOSED — cannot submit for review.")
    rec.status = RecommendationStatus.UNDER_REVIEW
    return rec


def accept_recommendation(rec: Recommendation, approver_roles: frozenset) -> Recommendation:
    """
    Rejects acceptance of a GATED recommendation (outstanding LAAE
    task / absence terminus) and of one whose approval_gate is not fully
    satisfied by approver_roles. Accepting never touches the optimizer,
    the Composer, or the Evidence Graph — it only records the decision.
    """
    if rec.status not in (RecommendationStatus.PROPOSED, RecommendationStatus.UNDER_REVIEW):
        raise ValueError(f"Recommendation '{rec.recommendation_id}' cannot be accepted from status '{rec.status.value}'.")
    tier = classify_tier(rec)
    if tier == RecommendationTier.GATED:
        raise ValueError(
            f"Recommendation '{rec.recommendation_id}' is GATED — outstanding evidence/authority "
            f"(acquisition tasks: {rec.acquisition_task_refs or 'none'}) must resolve before acceptance."
        )
    required = _REQUIRED_APPROVER_ROLES[rec.approval_gate]
    missing = required - set(approver_roles)
    if missing:
        raise ValueError(
            f"Recommendation '{rec.recommendation_id}' requires approval from {sorted(required)}; "
            f"missing {sorted(missing)}."
        )
    rec.status = RecommendationStatus.ACCEPTED
    return rec


def decline_recommendation(rec: Recommendation, reason: str = "") -> Recommendation:
    """Declined recommendations are retained (status flips, the object is
    never removed from any caller-held list) — a declined recommendation
    remains inspectable and re-proposable context, not deleted history."""
    rec.status = RecommendationStatus.DECLINED
    rec.attributes = {**rec.attributes, "decline_reason": reason}
    return rec


def supersede_recommendation(rec: Recommendation, superseded_by: str = "") -> Recommendation:
    rec.status = RecommendationStatus.SUPERSEDED
    rec.attributes = {**rec.attributes, "superseded_by": superseded_by}
    return rec
