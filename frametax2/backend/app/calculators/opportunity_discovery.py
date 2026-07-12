"""
opportunity_discovery.py

Phase 7A of CineGlobe: the Global Opportunity Discovery Engine.

The optimizer's question changes from "how do we optimize this production
in Mauritius?" to "given a production, what legally supportable structure
anywhere in the modeled world could reduce risk-adjusted Net Production
Cost?" — and this module is the reasoning layer that answers the
discovery half of that question. It consumes every engine already built
(jurisdiction_comparison, treaty_engine, jurisdiction_graph,
qualification_model, levers, legal_authority_acquisition) and emits
candidate Opportunity objects.

What discovery does NOT do — enforced structurally, not by convention:

- It never calculates incentives. Estimated-upside figures are carried
  over from values other engines already computed (a Lever's
  upside_incentive_usd, a GreyAreaItem's amount x rate — the same formula
  qualification_model already applies), or left None when no existing
  figure exists. No new QPE/incentive math is introduced here.
- It never changes qualification: qualification_model's register builders
  are read, never written.
- It never performs legal research: unknown authority becomes an
  AcquisitionTask *reference* (matching legal_authority_acquisition.py's
  deterministic task-id scheme) so the LAAE docket — not an assumption —
  is the follow-up. Opportunities blocked on evidence are emitted with
  requires_evidence=True, never silently discarded and never silently
  included as if proven.
- It never mutates: JurisdictionGraph, EvidenceGraph, the treaty
  registries, and the reinvestment registry are inputs. This module has
  no import of optimization_engine.py (verified by test), and the
  existing optimizer consumes Opportunity collections only through the
  explicit opportunities_to_structuring_paths() bridge — its own inputs
  and outputs are unchanged.

Every pass is deterministic: fixed iteration over sorted keys, no
wall-clock, no randomness, no network. Two runs with the same inputs
produce byte-identical output in identical order.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators import jurisdiction_comparison as jc
from app.calculators import treaty_engine as te
from app.calculators.jurisdiction_graph import (
    JurisdictionGraph,
    NodeType,
    RelationshipType,
    build_jurisdiction_graph,
    get_program_unknowns,
)
from app.calculators.legal_authority_acquisition import compute_priority_score
from app.calculators.levers import Lever, derive_levers, lever_to_structuring_path
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationConfidence,
    ReinvestmentCategory,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
)
from app.calculators.structuring_paths import StructuringPath

OPPORTUNITY_DISCOVERY_VERSION = "1.0.0"

# A candidate jurisdiction's max_rate must exceed the baseline's by at
# least this much (in rate points) to count as "materially stronger".
# Policy constant, not a per-jurisdiction fact.
MATERIAL_RATE_ADVANTAGE = 0.05

# A candidate's payroll burden must undercut the baseline's by at least
# this much (in rate points) before a labor-normalization opportunity is
# worth surfacing.
MATERIAL_PAYROLL_ADVANTAGE = 0.05

# A candidate's payout timing must beat the baseline's by at least this
# many weeks before a fund-timing opportunity is emitted.
MATERIAL_TIMING_ADVANTAGE_WEEKS = 8


class OpportunityType(str, enum.Enum):
    JURISDICTION = "jurisdiction"
    TREATY = "treaty"
    STACKING = "stacking"
    STRUCTURING = "structuring"
    REINVESTMENT = "reinvestment"
    NORMALIZATION = "normalization"
    GREY_AREA = "grey_area"


@dataclass
class Opportunity:
    """
    One candidate optimization path. Fully traceable: source_ref names the
    exact object the pass derived it from; graph_refs point at
    JurisdictionGraph node ids; graph_rule_id / graph_absence_id point at
    Evidence Graph objects (same convention as GreyAreaItem and Lever);
    acquisition_task_refs use legal_authority_acquisition.py's
    deterministic TASK-… id scheme so an unresolved authority gap resolves
    to a real docket entry, not an assumption.

    estimated_upside_usd / estimated_downside_usd / implementation_cost_usd
    are Optional: None means "no existing engine has computed this figure"
    — discovery never invents one.

    authority_score is Optional[float]. Discovery does not run the Phase 2
    scorer; the only value it ever sets itself is the hard 0.0 for
    opportunities whose terminus is an absence of authority, mirroring
    (not recomputing) authority_score.py's frozen rule that absence never
    manufactures confidence. Anything else stays None until a caller
    scores it against a populated EvidenceGraph.
    """
    opportunity_id: str
    opportunity_type: OpportunityType
    subtype: str
    description: str
    jurisdiction_codes: tuple[str, ...]
    affected_accounts: tuple[str, ...] = ()
    estimated_upside_usd: Optional[float] = None
    estimated_downside_usd: Optional[float] = None
    implementation_cost_usd: Optional[float] = None
    complexity: str = "UNKNOWN"  # "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
    confidence: QualificationConfidence = QualificationConfidence.LOW
    authority_score: Optional[float] = None
    required_evidence: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    blocking_requirements: tuple[str, ...] = ()
    dependent_opportunity_ids: tuple[str, ...] = ()
    graph_refs: tuple[str, ...] = ()
    graph_rule_id: Optional[str] = None
    graph_absence_id: Optional[str] = None
    acquisition_task_refs: tuple[str, ...] = ()
    requires_evidence: bool = False
    source_ref: str = ""
    attributes: dict = field(default_factory=dict)

    @property
    def discovery_rank_score(self) -> float:
        """Deterministic ranking input: known upside weighted by how much
        of it is already evidenced. Reuses LAAE's prioritization formula —
        (value x confidence gap) / effort — with gap/effort carried in
        attributes when a pass sets them, defaulting to a plain upside
        sort otherwise. No new scoring math."""
        gap = self.attributes.get("confidence_gap", 1.0)
        effort = self.attributes.get("research_effort", 1.0)
        return compute_priority_score(self.estimated_upside_usd, gap, effort)


@dataclass
class OpportunityCollection:
    """What discover_all_opportunities() returns: the deduplicated,
    deterministically ordered union of every pass's output, plus a record
    of which passes ran. This is the object the (unchanged) optimizer
    receives as an additional input."""
    baseline_jurisdiction: str
    passes_run: tuple[str, ...]
    opportunities: list[Opportunity]

    def of_type(self, opportunity_type: OpportunityType) -> list[Opportunity]:
        return [o for o in self.opportunities if o.opportunity_type == opportunity_type]


# ── Pass 1: Jurisdiction opportunities ───────────────────────────────────────

def discover_jurisdiction_opportunities(
    baseline_code: str,
    profiles: Optional[dict[str, "jc.JurisdictionIncentiveProfile"]] = None,
    movable_spend_usd: Optional[float] = None,
) -> list[Opportunity]:
    """
    Compares the baseline jurisdiction against every other modeled
    profile. Emits:

    - "stronger_incentive" / "relocation_candidate" where a candidate's
      max_rate is KNOWN and exceeds the baseline's KNOWN max_rate by
      MATERIAL_RATE_ADVANTAGE. A None rate on either side means no
      comparison is made — an unverified rate is never treated as a real
      advantage (or a real disadvantage).
    - "comparable_jurisdiction" for the existing Tier 1 comparison set
      (jurisdiction_comparison.TIER1_PROFILES), mirroring the
      COMPARABLE_TO edges Phase 5A wired — not a new comparison theory.

    By default (movable_spend_usd=None) no dollar upside is estimated:
    the rate delta is known but the production's relocatable spend basis
    is not an input, and discovery does not invent one. When a caller
    supplies the production's own real movable-spend figure (the same
    number production_package_intelligence.py already computes as
    HINT-MOVABLE-SPEND — routable VFX/music/sound/post/creative-fee
    spend not physically tied to the shoot location), a relocation
    candidate's estimated_upside_usd becomes rate_delta * movable_spend
    — the two real numbers this docstring already said were needed,
    finally combined. Still None whenever either input is missing, so
    "no data" is never confused with "zero opportunity".
    """
    profiles = profiles if profiles is not None else jc.ALL_PROFILES
    baseline = profiles.get(baseline_code)
    opportunities: list[Opportunity] = []

    for code in sorted(profiles.keys()):
        if code == baseline_code:
            continue
        candidate = profiles[code]
        if (
            baseline is not None
            and baseline.max_rate is not None
            and candidate.max_rate is not None
            and candidate.max_rate - baseline.max_rate >= MATERIAL_RATE_ADVANTAGE
        ):
            rate_delta = round(candidate.max_rate - baseline.max_rate, 4)
            upside = (
                round(rate_delta * movable_spend_usd, 2)
                if movable_spend_usd is not None else None
            )
            opportunities.append(Opportunity(
                opportunity_id=f"OPP-JUR-RELOCATE-{baseline_code}-{code}",
                opportunity_type=OpportunityType.JURISDICTION,
                subtype="relocation_candidate",
                description=(
                    f"{candidate.jurisdiction_name} ({candidate.program_name}) offers max rate "
                    f"{candidate.max_rate:.0%} vs {baseline_code} baseline {baseline.max_rate:.0%}."
                ),
                jurisdiction_codes=(baseline_code, code),
                complexity="HIGH",
                confidence=(
                    QualificationConfidence.MEDIUM
                    if candidate.confidence_tier == "PARSED"
                    else QualificationConfidence.LOW
                ),
                blocking_requirements=tuple(sorted(candidate.data_gaps)),
                graph_refs=(f"country:{code}", f"program:{candidate.program_slug}"),
                source_ref=f"jurisdiction_comparison.ALL_PROFILES[{code}]",
                estimated_upside_usd=upside,
                attributes={
                    "rate_delta": rate_delta,
                    "candidate_confidence_tier": candidate.confidence_tier,
                    **({"movable_spend_basis_usd": movable_spend_usd} if upside is not None else {}),
                },
            ))

    for code in sorted(jc.TIER1_PROFILES.keys()):
        if code == baseline_code or code not in profiles:
            continue
        candidate = profiles[code]
        opportunities.append(Opportunity(
            opportunity_id=f"OPP-JUR-COMPARE-{baseline_code}-{code}",
            opportunity_type=OpportunityType.JURISDICTION,
            subtype="comparable_jurisdiction",
            description=f"{candidate.jurisdiction_name} is in the established Tier 1 comparison set with {baseline_code}.",
            jurisdiction_codes=(baseline_code, code),
            complexity="MEDIUM",
            confidence=QualificationConfidence.MEDIUM,
            graph_refs=(f"country:{baseline_code}", f"country:{code}"),
            source_ref="jurisdiction_comparison.TIER1_PROFILES",
        ))

    return opportunities


# ── Pass 2: Treaty opportunities ─────────────────────────────────────────────

def discover_treaty_opportunities(country_codes: list[str]) -> list[Opportunity]:
    """
    For the given production-relevant countries, reads treaty_engine's
    registries through its public getters. Emits:

    - "bilateral_coproduction" for each in-scope country pair with a
      registered bilateral treaty;
    - "nationality_unlock" for each such treaty's majority/minority unlock
      slugs (the incentive programs a co-production structure would open);
    - "multilateral_membership" per country per multilateral instrument it
      belongs to (Eurimages / European Convention / Ibermedia);
    - "treaty_composition_path" for in-scope pairs with NO bilateral
      treaty where both countries are European Convention signatories —
      the Convention substitutes as the co-production framework.

    A country with no treaty presence at all (Mauritius today) yields
    nothing from this pass — treaty absence is already a first-class fact
    in the Jurisdiction Graph (treaty_availability, ABSENT-and-checked)
    and an LAAE docket task; fabricating a treaty opportunity here would
    violate the no-invented-facts rule.
    """
    codes = sorted({c.upper() for c in country_codes})
    opportunities: list[Opportunity] = []

    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            treaty = te.get_bilateral_treaty(a, b)
            if treaty is not None:
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-TREATY-BILATERAL-{treaty.treaty_slug}",
                    opportunity_type=OpportunityType.TREATY,
                    subtype="bilateral_coproduction",
                    description=(
                        f"Bilateral co-production treaty '{treaty.treaty_slug}' between {a} and {b} "
                        f"(majority ≥{treaty.majority_min_pct:.0f}%, minority ≥{treaty.minority_min_pct:.0f}%)."
                    ),
                    jurisdiction_codes=(a, b),
                    complexity="HIGH",
                    confidence=(
                        QualificationConfidence.MEDIUM
                        if treaty.confidence_tier == "PARSED"
                        else QualificationConfidence.LOW
                    ),
                    blocking_requirements=(
                        ("Cultural test required.",) if treaty.cultural_test_required else ()
                    ),
                    required_approvals=("Competent authority co-production approval in both countries.",),
                    graph_refs=(f"treaty:{treaty.treaty_slug}",),
                    source_ref=f"treaty_engine._BILATERAL[{treaty.treaty_slug}]",
                    attributes={"confidence_tier": treaty.confidence_tier},
                ))
                unlock_slugs = sorted(set(treaty.majority_unlocks) | set(treaty.minority_unlocks))
                for slug in unlock_slugs:
                    opportunities.append(Opportunity(
                        opportunity_id=f"OPP-TREATY-UNLOCK-{treaty.treaty_slug}-{slug}",
                        opportunity_type=OpportunityType.TREATY,
                        subtype="nationality_unlock",
                        description=(
                            f"Qualifying under '{treaty.treaty_slug}' unlocks national-treatment access "
                            f"to incentive program '{slug}'."
                        ),
                        jurisdiction_codes=(a, b),
                        complexity="HIGH",
                        confidence=QualificationConfidence.LOW,
                        dependent_opportunity_ids=(f"OPP-TREATY-BILATERAL-{treaty.treaty_slug}",),
                        graph_refs=(f"treaty:{treaty.treaty_slug}",),
                        source_ref=f"treaty_engine._BILATERAL[{treaty.treaty_slug}].unlocks",
                        attributes={"unlocked_slug": slug},
                    ))
            elif te.is_european_convention_signatory(a) and te.is_european_convention_signatory(b):
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-TREATY-COMPOSE-{a}-{b}",
                    opportunity_type=OpportunityType.TREATY,
                    subtype="treaty_composition_path",
                    description=(
                        f"No bilateral treaty between {a} and {b}, but both are European Convention "
                        "signatories — the Convention provides the co-production framework."
                    ),
                    jurisdiction_codes=(a, b),
                    complexity="HIGH",
                    confidence=QualificationConfidence.LOW,
                    graph_refs=("treaty:european_convention",),
                    source_ref="treaty_engine._MULTILATERAL[european_convention]",
                ))

    membership_checks = (
        ("eurimages", te.is_eurimages_member),
        ("european_convention", te.is_european_convention_signatory),
        ("ibermedia", te.is_ibermedia_member),
    )
    for code in codes:
        for slug, checker in membership_checks:
            if checker(code):
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-TREATY-MULTI-{slug}-{code}",
                    opportunity_type=OpportunityType.TREATY,
                    subtype="multilateral_membership",
                    description=f"{code} is a member/signatory of '{slug}' — multilateral co-production and fund access.",
                    jurisdiction_codes=(code,),
                    complexity="HIGH",
                    confidence=QualificationConfidence.MEDIUM,
                    graph_refs=(f"treaty:{slug}",),
                    source_ref=f"treaty_engine._MULTILATERAL[{slug}]",
                ))

    return opportunities


# ── Pass 3: Stacking opportunities ───────────────────────────────────────────

def discover_stacking_opportunities(graph: JurisdictionGraph) -> list[Opportunity]:
    """
    Reads the Jurisdiction Graph only. Two honest sources:

    - STACKS_WITH edges, if any exist, become KNOWN stacking
      opportunities. (None exist in today's graph — the pass handles them
      generically for when Phase 5's data grows.)
    - Every program's stacking_rule fact node with status ABSENT/UNKNOWN
      becomes an evidence-required stacking opportunity carrying the
      matching LAAE AcquisitionTask reference (TASK-<node_id>, the exact
      id tasks_from_jurisdiction_graph_unknowns() generates). Unknown
      stackability is never asserted in either direction — it routes to
      the docket, per "unknown stacking becomes Grey Area".

    Nothing is fabricated: no national/regional/municipal/fund stack is
    emitted as combinable unless the graph actually carries the edge.
    """
    opportunities: list[Opportunity] = []

    for rel in graph.relationships_of_type(RelationshipType.STACKS_WITH):
        source = graph.get_node(rel.source_id)
        target = graph.get_node(rel.target_id)
        opportunities.append(Opportunity(
            opportunity_id=f"OPP-STACK-KNOWN-{rel.source_id}-{rel.target_id}",
            opportunity_type=OpportunityType.STACKING,
            subtype="known_stack",
            description=f"'{source.name}' stacks with '{target.name}' per Jurisdiction Graph.",
            jurisdiction_codes=tuple(sorted(filter(None, {
                source.attributes.get("jurisdiction_code"),
                target.attributes.get("jurisdiction_code"),
            }))),
            confidence=QualificationConfidence.MEDIUM,
            graph_refs=(rel.source_id, rel.target_id),
            graph_rule_id=rel.evidence.graph_rule_id,
            source_ref="jurisdiction_graph.STACKS_WITH",
        ))

    for program in sorted(graph.nodes_of_type(NodeType.NATIONAL_PROGRAM), key=lambda n: n.node_id):
        code = program.attributes.get("jurisdiction_code", "")
        for node in sorted(get_program_unknowns(graph, program.node_id), key=lambda n: n.node_id):
            if node.attributes.get("kind") != "stacking_rule":
                continue
            opportunities.append(Opportunity(
                opportunity_id=f"OPP-STACK-UNKNOWN-{program.attributes.get('program_slug', program.node_id)}",
                opportunity_type=OpportunityType.STACKING,
                subtype="stacking_unknown",
                description=(
                    f"Stacking rules for {program.name} are {node.attributes.get('status')} — "
                    "combinability with regional/municipal/fund support is an open evidence question, "
                    "not a determination in either direction."
                ),
                jurisdiction_codes=(code,),
                confidence=QualificationConfidence.LOW,
                authority_score=0.0,  # absence terminus — mirrors the frozen absence rule
                requires_evidence=True,
                required_evidence=("Program stacking/cumulation rule from primary or official guidance.",),
                graph_refs=(program.node_id, node.node_id),
                acquisition_task_refs=(f"TASK-{node.node_id}",),
                source_ref=node.node_id,
                attributes={"fact_status": node.attributes.get("status")},
            ))

    return opportunities


# ── Pass 4: Structuring opportunities ────────────────────────────────────────

# Deterministic keyword → routing-category classifier for lever mechanisms.
# Classification only — it adds no new structuring theory; an opportunity
# is emitted only when an underlying Lever (existing evidence model)
# exists. Order matters: first match wins, so the tuple is fixed.
_ROUTING_CLASSIFIERS: tuple[tuple[str, str], ...] = (
    ("spv", "spv_routing"),
    ("employer of record", "employer_of_record"),
    ("payroll", "payroll_routing"),
    ("loan-out", "entity_routing"),
    ("entity", "entity_routing"),
    ("vendor", "vendor_routing"),
    ("facility", "facility_routing"),
    ("service", "service_routing"),
)


def _classify_routing(mechanism: str) -> str:
    text = mechanism.lower()
    for keyword, category in _ROUTING_CLASSIFIERS:
        if keyword in text:
            return category
    return "general_structuring"


def discover_structuring_opportunities(
    register: list[AccountQualification],
    rate: float,
    jurisdiction_code: str = "MU",
) -> list[Opportunity]:
    """
    Generalizes StructuringPath by wrapping the existing Lever pipeline
    (levers.derive_levers -> structuring_paths.derive_structuring_paths,
    both unchanged). Every emitted opportunity corresponds 1:1 to a Lever
    the existing evidence model already supports — no SPV/EoR/vendor/
    entity/payroll/facility/service route is invented; those categories
    exist here only as a deterministic classification of each lever's
    own mechanism text.
    """
    levers: list[Lever] = derive_levers(register, rate=rate, jurisdiction_code=jurisdiction_code)
    opportunities: list[Opportunity] = []
    for lever in levers:
        opportunities.append(Opportunity(
            opportunity_id=f"OPP-STRUCT-{lever.lever_id}",
            opportunity_type=OpportunityType.STRUCTURING,
            subtype=_classify_routing(lever.mechanism),
            description=lever.description,
            jurisdiction_codes=(lever.jurisdiction_code,),
            affected_accounts=lever.affected_accounts,
            estimated_upside_usd=lever.upside_incentive_usd,
            implementation_cost_usd=lever.implementation_cost_usd,
            complexity=lever.complexity,
            confidence=lever.confidence,
            required_evidence=lever.required_documents,
            graph_refs=(f"lever:{lever.lever_id}",),
            graph_rule_id=lever.graph_rule_id,
            graph_absence_id=lever.graph_absence_id,
            source_ref=f"levers.derive_levers[{lever.lever_id}]",
            attributes={"mechanism": lever.mechanism, "lever_type": lever.lever_type.value},
        ))
    return opportunities


# ── Pass 5: Reinvestment opportunities ───────────────────────────────────────

def discover_reinvestment_opportunities(country_codes: list[str]) -> list[Opportunity]:
    """
    Consumes ReinvestmentProfile per jurisdiction. The category mapping is
    the point of this pass:

    - UNKNOWN -> an Opportunity requiring evidence, carrying the LAAE
      task reference (TASK-reinvestment:<code>). "We have not looked" is
      an open opportunity, never an assumed unavailability.
    - NOT_PERMITTED -> no opportunity, and not silently: that is an
      authority-backed determination, so this pass records nothing to
      pursue (the determination itself lives in the registry/graph).
    - Any other category (PERMITTED, VENDOR_REINVESTMENT, …) -> a known
      reinvestment opportunity citing the registry's own evidence text.
    """
    opportunities: list[Opportunity] = []
    for code in sorted({c.upper() for c in country_codes}):
        profile = get_reinvestment_profile(code)
        if profile.category == ReinvestmentCategory.NOT_PERMITTED:
            continue
        if profile.category == ReinvestmentCategory.UNKNOWN:
            opportunities.append(Opportunity(
                opportunity_id=f"OPP-REINVEST-UNKNOWN-{code}",
                opportunity_type=OpportunityType.REINVESTMENT,
                subtype="reinvestment_unknown",
                description=(
                    f"Reinvestment treatment in {code} is UNKNOWN (absence of authority, not a "
                    "prohibition) — an open opportunity pending evidence."
                ),
                jurisdiction_codes=(code,),
                confidence=QualificationConfidence.LOW,
                authority_score=0.0,
                requires_evidence=True,
                required_evidence=("Reinvestment / vendor-credit / equity-substitution provision from official guidance.",),
                graph_refs=(f"reinvestment:{code}",),
                acquisition_task_refs=(f"TASK-reinvestment:{code}",),
                source_ref=f"qualification_model.get_reinvestment_profile({code})",
                attributes={"category": profile.category.value},
            ))
        else:
            opportunities.append(Opportunity(
                opportunity_id=f"OPP-REINVEST-KNOWN-{code}",
                opportunity_type=OpportunityType.REINVESTMENT,
                subtype=f"reinvestment_{profile.category.value}",
                description=f"Reinvestment in {code}: {profile.category.value} per registry evidence.",
                jurisdiction_codes=(code,),
                confidence=QualificationConfidence.MEDIUM,
                required_approvals=(
                    ("Government approval.",)
                    if profile.category == ReinvestmentCategory.GOVERNMENT_APPROVAL_REQUIRED
                    else ()
                ),
                graph_refs=(f"reinvestment:{code}",),
                source_ref=f"qualification_model.REINVESTMENT_REGISTRY[{code}]",
                attributes={"category": profile.category.value, "evidence": profile.evidence},
            ))
    return opportunities


# ── Pass 6: Normalization opportunities (NPC-only) ───────────────────────────

def discover_normalization_opportunities(
    baseline_code: str,
    profiles: Optional[dict[str, "jc.JurisdictionIncentiveProfile"]] = None,
    graph: Optional[JurisdictionGraph] = None,
) -> list[Opportunity]:
    """
    NPC-side opportunities only — nothing here touches QPE qualification.
    Sources, all existing model fields:

    - fund/payout timing: candidate cashflow_timing_weeks materially
      faster than the baseline's (both KNOWN; a None on either side means
      no comparison — the baseline's own unknown payout timing is already
      an UNKNOWN fact node and LAAE task, not something to guess at).
    - labor normalization: candidate payroll_burden_pct materially below
      the baseline's (both KNOWN).
    - VAT recovery: candidate vat_recoverable is True where the
      baseline's is False — a real NPC lever on any relocated spend.
    - application timing: every program's application_timing_deadline
      fact is ABSENT in today's source data; each becomes an
      evidence-required timing opportunity with its LAAE task reference.

    Cross-jurisdiction normalization opportunities are marked dependent
    on the corresponding Pass 1 relocation opportunity where one exists —
    they only pay off if spend actually moves.
    """
    profiles = profiles if profiles is not None else jc.ALL_PROFILES
    baseline = profiles.get(baseline_code)
    opportunities: list[Opportunity] = []

    stronger_rate_codes = {
        o.jurisdiction_codes[1]
        for o in discover_jurisdiction_opportunities(baseline_code, profiles)
        if o.subtype == "relocation_candidate"
    }

    def _dependency(code: str) -> tuple[str, ...]:
        if code in stronger_rate_codes:
            return (f"OPP-JUR-RELOCATE-{baseline_code}-{code}",)
        return ()

    if baseline is not None:
        for code in sorted(profiles.keys()):
            if code == baseline_code:
                continue
            candidate = profiles[code]
            if (
                baseline.cashflow_timing_weeks is not None
                and candidate.cashflow_timing_weeks is not None
                and baseline.cashflow_timing_weeks - candidate.cashflow_timing_weeks >= MATERIAL_TIMING_ADVANTAGE_WEEKS
            ):
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-NORM-TIMING-{baseline_code}-{code}",
                    opportunity_type=OpportunityType.NORMALIZATION,
                    subtype="fund_timing",
                    description=(
                        f"{candidate.jurisdiction_name} pays out in ~{candidate.cashflow_timing_weeks} weeks vs "
                        f"~{baseline.cashflow_timing_weeks} for {baseline_code} — financing-cost reduction on NPC."
                    ),
                    jurisdiction_codes=(baseline_code, code),
                    complexity="MEDIUM",
                    confidence=QualificationConfidence.LOW,
                    dependent_opportunity_ids=_dependency(code),
                    graph_refs=(f"restriction:{candidate.program_slug}:payout_timing",),
                    source_ref=f"jurisdiction_comparison.ALL_PROFILES[{code}].cashflow_timing_weeks",
                    attributes={"weeks_saved": baseline.cashflow_timing_weeks - candidate.cashflow_timing_weeks},
                ))
            if (
                baseline.payroll_burden_pct is not None
                and candidate.payroll_burden_pct is not None
                and baseline.payroll_burden_pct - candidate.payroll_burden_pct >= MATERIAL_PAYROLL_ADVANTAGE
            ):
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-NORM-LABOR-{baseline_code}-{code}",
                    opportunity_type=OpportunityType.NORMALIZATION,
                    subtype="labor_normalization",
                    description=(
                        f"{candidate.jurisdiction_name} payroll burden ~{candidate.payroll_burden_pct:.0%} vs "
                        f"~{baseline.payroll_burden_pct:.0%} for {baseline_code} — net labor cost normalization."
                    ),
                    jurisdiction_codes=(baseline_code, code),
                    complexity="MEDIUM",
                    confidence=QualificationConfidence.LOW,
                    dependent_opportunity_ids=_dependency(code),
                    graph_refs=(f"program:{candidate.program_slug}",),
                    source_ref=f"jurisdiction_comparison.ALL_PROFILES[{code}].payroll_burden_pct",
                    attributes={"payroll_delta": round(baseline.payroll_burden_pct - candidate.payroll_burden_pct, 4)},
                ))
            if baseline.vat_recoverable is False and candidate.vat_recoverable is True:
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-NORM-VAT-{baseline_code}-{code}",
                    opportunity_type=OpportunityType.NORMALIZATION,
                    subtype="vat_recovery",
                    description=(
                        f"VAT is recoverable in {candidate.jurisdiction_name} but not in {baseline_code} — "
                        "NPC reduction on any spend routed there."
                    ),
                    jurisdiction_codes=(baseline_code, code),
                    complexity="LOW",
                    confidence=QualificationConfidence.LOW,
                    dependent_opportunity_ids=_dependency(code),
                    graph_refs=(f"program:{candidate.program_slug}",),
                    source_ref=f"jurisdiction_comparison.ALL_PROFILES[{code}].vat_recoverable",
                    attributes={"candidate_vat_rate_pct": candidate.vat_rate_pct},
                ))

    if graph is not None:
        for program in sorted(graph.nodes_of_type(NodeType.NATIONAL_PROGRAM), key=lambda n: n.node_id):
            code = program.attributes.get("jurisdiction_code", "")
            for node in sorted(get_program_unknowns(graph, program.node_id), key=lambda n: n.node_id):
                if node.attributes.get("kind") != "application_timing_deadline":
                    continue
                opportunities.append(Opportunity(
                    opportunity_id=f"OPP-NORM-APPTIMING-{program.attributes.get('program_slug', program.node_id)}",
                    opportunity_type=OpportunityType.NORMALIZATION,
                    subtype="application_timing_unknown",
                    description=(
                        f"Application timing/deadline for {program.name} is not modeled — a calendar-planning "
                        "opportunity or risk pending evidence."
                    ),
                    jurisdiction_codes=(code,),
                    confidence=QualificationConfidence.LOW,
                    authority_score=0.0,
                    requires_evidence=True,
                    required_evidence=("Program application window / deadline from official guidance.",),
                    graph_refs=(program.node_id, node.node_id),
                    acquisition_task_refs=(f"TASK-{node.node_id}",),
                    source_ref=node.node_id,
                    attributes={"fact_status": node.attributes.get("status")},
                ))

    return opportunities


# ── Pass 7: Grey Area opportunities ──────────────────────────────────────────

# Fixed research-effort constant for grey-area ranking — same scale as
# LAAE's EFFORT_BY_CONNECTOR_CLASS (grey areas route to tax-authority
# guidance, effort 2.0). Kept as a named constant so ranking inputs are
# explicit, not buried.
GREY_AREA_RESEARCH_EFFORT = 2.0


def discover_grey_area_opportunities(
    grey_areas: list[GreyAreaItem],
    rate: float,
) -> list[Opportunity]:
    """
    Every OPEN GreyAreaItem becomes a quantified opportunity. The upside
    figure is amount_usd x rate — the exact formula
    build_little_utopia_qualification_register() already applies to
    grey-area accounts (incentive_upside_usd), not a new calculation.
    Ranking inputs (confidence gap = 1.0 for an open item, research
    effort constant) feed discovery_rank_score via LAAE's own
    prioritization formula.
    """
    opportunities: list[Opportunity] = []
    for ga in grey_areas:
        if ga.status != GreyAreaStatus.OPEN:
            continue
        opportunities.append(Opportunity(
            opportunity_id=f"OPP-GREY-{ga.item_id}",
            opportunity_type=OpportunityType.GREY_AREA,
            subtype="grey_area_resolution",
            description=f"Resolving '{ga.item_id}' could swing QPE on ${ga.amount_usd:,.0f}: {ga.resolving_evidence}",
            jurisdiction_codes=(ga.jurisdiction_code,),
            affected_accounts=ga.account_codes,
            estimated_upside_usd=round(ga.amount_usd * rate, 2),
            estimated_downside_usd=0.0,  # an OPEN grey area books nothing today; resolution cannot reduce booked value
            confidence=QualificationConfidence.LOW,
            authority_score=0.0,
            requires_evidence=True,
            required_evidence=(ga.resolving_evidence,),
            graph_absence_id=ga.graph_absence_id,
            graph_rule_id=ga.graph_rule_id,
            acquisition_task_refs=(f"TASK-{ga.item_id}",),
            source_ref=ga.item_id,
            attributes={
                "amount_usd": ga.amount_usd,
                "off_budget": ga.off_budget,
                "confidence_gap": 1.0,
                "research_effort": GREY_AREA_RESEARCH_EFFORT,
            },
        ))
    return opportunities


# ── Dedup / ranking / top-level ──────────────────────────────────────────────

def dedupe_opportunities(opportunities: list[Opportunity]) -> list[Opportunity]:
    """First occurrence wins, order preserved — duplicate suppression is
    by opportunity_id, which every pass constructs deterministically from
    its source object's identity."""
    seen: set[str] = set()
    unique: list[Opportunity] = []
    for opp in opportunities:
        if opp.opportunity_id in seen:
            continue
        seen.add(opp.opportunity_id)
        unique.append(opp)
    return unique


def rank_opportunities(opportunities: list[Opportunity]) -> list[Opportunity]:
    """Deterministic: primary sort on discovery_rank_score (descending),
    ties broken by opportunity_id — never by insertion order or hash."""
    return sorted(opportunities, key=lambda o: (-o.discovery_rank_score, o.opportunity_id))


def discover_all_opportunities(
    baseline_jurisdiction: str = "MU",
    mu_rate: float = 0.40,
    graph: Optional[JurisdictionGraph] = None,
    movable_spend_usd: Optional[float] = None,
    register: Optional[list[AccountQualification]] = None,
    grey_areas: Optional[list[GreyAreaItem]] = None,
) -> OpportunityCollection:
    """
    Runs all seven passes over the currently modeled world (ALL_PROFILES'
    jurisdictions), dedupes, and returns a deterministically ordered
    collection.

    register / grey_areas (Engine Integration Phase 1): the caller's
    CURRENT qualification register and grey-area list — a facts-changed
    or legally-resolved register produces correspondingly changed
    structuring/grey-area opportunities for the baseline jurisdiction,
    whatever that jurisdiction is. When omitted, Pass 4/Pass 7 fall back
    to the one populated register in the codebase (Little Utopia / MU)
    for an MU baseline, and honestly contribute nothing for any other
    baseline rather than fabricate a register — byte-identical to prior
    behavior.

    movable_spend_usd, when supplied, is forwarded to Pass 1 so a
    relocation candidate's rate advantage can be combined with the
    production's own real routable-spend figure into a real
    estimated_upside_usd (see discover_jurisdiction_opportunities). Left
    None by default — no behavior change for any caller that doesn't
    pass it.
    """
    graph = graph if graph is not None else build_jurisdiction_graph(mu_rate=mu_rate)
    codes = sorted(jc.ALL_PROFILES.keys())

    if register is None and baseline_jurisdiction == "MU":
        register = build_little_utopia_qualification_register(mu_rate=mu_rate)
    if grey_areas is None and baseline_jurisdiction == "MU":
        grey_areas = build_little_utopia_grey_areas()

    all_opportunities: list[Opportunity] = []
    all_opportunities += discover_jurisdiction_opportunities(baseline_jurisdiction, movable_spend_usd=movable_spend_usd)
    all_opportunities += discover_treaty_opportunities(codes)
    all_opportunities += discover_stacking_opportunities(graph)
    if register is not None:
        all_opportunities += discover_structuring_opportunities(
            register, rate=mu_rate, jurisdiction_code=baseline_jurisdiction,
        )
    if grey_areas is not None:
        all_opportunities += discover_grey_area_opportunities(grey_areas, rate=mu_rate)
    all_opportunities += discover_reinvestment_opportunities(codes)
    all_opportunities += discover_normalization_opportunities(baseline_jurisdiction, graph=graph)

    return OpportunityCollection(
        baseline_jurisdiction=baseline_jurisdiction,
        passes_run=(
            "jurisdiction", "treaty", "stacking", "structuring",
            "reinvestment", "normalization", "grey_area",
        ),
        opportunities=rank_opportunities(dedupe_opportunities(all_opportunities)),
    )


# ── Optimizer bridge (optimizer itself unchanged) ────────────────────────────

def opportunities_to_structuring_paths(
    opportunities: list[Opportunity],
    register: Optional[list[AccountQualification]] = None,
    rate: float = 0.40,
    jurisdiction_code: str = "MU",
) -> list[StructuringPath]:
    """
    The one integration point with the existing optimizer:
    OpportunityType.STRUCTURING opportunities convert back to the
    StructuringPath objects build_risk_cases() already consumes,
    round-tripping through the existing Lever machinery rather than
    reconstructing paths by hand. Non-structuring opportunities are
    skipped (they have no StructuringPath representation) — the optimizer
    is never handed anything it wasn't already built to accept, and its
    own code is not modified.

    A STRUCTURING opportunity's source lever id is embedded in its
    opportunity_id (OPP-STRUCT-<lever_id>); levers regenerate
    deterministically from the register, and only those the opportunity
    collection actually carries are converted.
    """
    wanted_lever_ids = {
        opp.opportunity_id.removeprefix("OPP-STRUCT-")
        for opp in opportunities
        if opp.opportunity_type == OpportunityType.STRUCTURING
    }
    if not wanted_lever_ids:
        return []
    if register is None:
        register = build_little_utopia_qualification_register(mu_rate=rate)
    paths_by_id = {
        lever.lever_id: lever_to_structuring_path(lever)
        for lever in derive_levers(register, rate=rate, jurisdiction_code=jurisdiction_code)
        if lever.lever_id in wanted_lever_ids
    }
    return [paths_by_id[lid] for lid in sorted(paths_by_id.keys())]
