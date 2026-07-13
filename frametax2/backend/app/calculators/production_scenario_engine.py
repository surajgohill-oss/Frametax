"""
production_scenario_engine.py

Phase 7 closeout, Part F: the Scenario Engine.

"What if we moved VFX to Canada?" "What if we structured this as a
co-production?" These are exactly the questions production_structure_
composer.py's extra_jurisdiction_sets parameter and opportunity_
discovery.py's STRUCTURING opportunities already answer — the composer
generalizes a production to a SET of jurisdictions and prices every
composition it can; the discovery engine already classifies structuring
levers by routing category (spv_routing, employer_of_record, ...) via
its own _ROUTING_CLASSIFIERS. Nothing currently gives a caller a named,
comparable way to ask for one specific variation and see how it prices
against the baseline.

This module:

- performs no new composition or pricing. Every jurisdiction-shaped
  scenario (move VFX/post/music/sound/payroll/marine work, create a
  co-production) is translated into an extra_jurisdiction_sets argument
  and passed straight into the EXISTING
  production_structure_composer.compose_production_structures() — the
  exact same function Phase 7C already exposes, called with the exact
  same discipline any other caller uses it with. This module has no
  build_risk_cases() call of its own.
- performs no new discovery. Every non-jurisdiction-shaped scenario
  (create an SPV, shift spend/schedule/financing timing) is answered by
  filtering the OpportunityCollection the caller already built via
  opportunity_discovery.discover_all_opportunities() for the routing
  category/subtype that scenario names — the same STRUCTURING
  opportunities Phase 7A already classified, never reclassified here.
- reuses production_recommendation_engine for the "so what should I
  actually do about it" half: a ScenarioResult exposes the delta in
  Risk-Adjusted NPC (read from two already-computed CaseResult objects,
  the same subtraction Phase 7D's candidate-savings recommendation
  already performs) and, when the caller opts in, the ranked
  Recommendation objects for the scenario's own composition result
  by calling generate_production_recommendations() directly — never a
  parallel recommendation model.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from app.calculators.opportunity_discovery import Opportunity, OpportunityCollection, OpportunityType
from app.calculators.optimization_engine import RiskCase
from app.calculators.production_recommendation_engine import RecommendationSet, generate_production_recommendations
from app.calculators.production_structure_composer import (
    CompositionResult,
    ProductionStructureCandidate,
    compose_production_structures,
)
from app.calculators.jurisdiction_graph import JurisdictionGraph
from app.calculators.qualification_model import AccountQualification, GreyAreaItem

PRODUCTION_SCENARIO_ENGINE_VERSION = "1.0.0"


class ScenarioKind(str, enum.Enum):
    MOVE_VFX = "move_vfx"
    MOVE_POST = "move_post"
    MOVE_MUSIC = "move_music"
    MOVE_SOUND = "move_sound"
    MOVE_PAYROLL = "move_payroll"
    MOVE_MARINE = "move_marine"
    CREATE_SPV = "create_spv"
    CREATE_COPRODUCTION = "create_coproduction"
    SHIFT_SPEND = "shift_spend"
    SHIFT_SCHEDULE = "shift_schedule"
    SHIFT_FINANCING_TIMING = "shift_financing_timing"


# Jurisdiction-shaped scenarios: answered entirely by re-composing with
# an additional candidate jurisdiction set via the EXISTING composer.
_JURISDICTION_SHAPED_KINDS: frozenset[ScenarioKind] = frozenset({
    ScenarioKind.MOVE_VFX, ScenarioKind.MOVE_POST, ScenarioKind.MOVE_MUSIC,
    ScenarioKind.MOVE_SOUND, ScenarioKind.MOVE_PAYROLL, ScenarioKind.MOVE_MARINE,
    ScenarioKind.CREATE_COPRODUCTION,
})

# Non-jurisdiction-shaped scenarios: answered by filtering already-
# discovered STRUCTURING opportunities for the matching routing category
# opportunity_discovery._ROUTING_CLASSIFIERS already assigns. MOVE_PAYROLL
# is intentionally jurisdiction-shaped only (see _JURISDICTION_SHAPED_KINDS
# above, checked first in run_scenario) — "move payroll to X" is a
# location decision; a caller wanting payroll_routing-classified
# STRUCTURING opportunities specifically can already filter
# collection.of_type(OpportunityType.STRUCTURING) directly.
_STRUCTURING_SUBTYPE_BY_KIND: dict[ScenarioKind, str] = {
    ScenarioKind.CREATE_SPV: "spv_routing",
}


@dataclass(frozen=True)
class ProductionScenario:
    scenario_id: str
    kind: ScenarioKind
    description: str
    target_jurisdiction: Optional[str] = None  # required for jurisdiction-shaped kinds


@dataclass
class ScenarioResult:
    scenario: ProductionScenario
    baseline_candidate_id: Optional[str]
    scenario_candidate_id: Optional[str]
    baseline_risk_adjusted_npc_usd: Optional[float]
    scenario_risk_adjusted_npc_usd: Optional[float]
    delta_usd: Optional[float]  # positive = scenario is cheaper than baseline
    relevant_structuring_opportunities: tuple[Opportunity, ...]
    composition_result: Optional[CompositionResult]
    recommendations: Optional[RecommendationSet]
    notes: str = ""


def _baseline_candidate(result: CompositionResult) -> Optional[ProductionStructureCandidate]:
    return next(
        (c for c in result.candidates if c.participating_jurisdictions == (result.baseline_jurisdiction,)),
        None,
    )


def _run_jurisdiction_shaped_scenario(
    scenario: ProductionScenario,
    collection: OpportunityCollection,
    graph: JurisdictionGraph,
    register: Optional[list[AccountQualification]],
    gross_budget_usd: Optional[float],
    rate: Optional[float],
    grey_areas: Optional[list[GreyAreaItem]],
    include_recommendations: bool,
    delay_weeks: int = 0,
    bridge_rate: float = 0.0,
) -> ScenarioResult:
    if not scenario.target_jurisdiction:
        return ScenarioResult(
            scenario=scenario, baseline_candidate_id=None, scenario_candidate_id=None,
            baseline_risk_adjusted_npc_usd=None, scenario_risk_adjusted_npc_usd=None, delta_usd=None,
            relevant_structuring_opportunities=(), composition_result=None, recommendations=None,
            notes=f"{scenario.kind.value} requires a target_jurisdiction — none supplied.",
        )

    target = scenario.target_jurisdiction.upper()
    baseline_code = collection.baseline_jurisdiction
    extra_set = (baseline_code, target) if target != baseline_code else (baseline_code,)

    result = compose_production_structures(
        collection, graph, register=register, gross_budget_usd=gross_budget_usd, rate=rate,
        grey_areas=grey_areas, extra_jurisdiction_sets=[extra_set],
        delay_weeks=delay_weeks, bridge_rate=bridge_rate,
    )
    baseline = _baseline_candidate(result)
    scenario_candidate = next(
        (c for c in result.candidates if set(c.participating_jurisdictions) == set(extra_set)),
        None,
    )

    baseline_npc = baseline.npc(RiskCase.RISK_ADJUSTED) if baseline and baseline.is_fully_priced else None
    scenario_npc = scenario_candidate.npc(RiskCase.RISK_ADJUSTED) if scenario_candidate and scenario_candidate.is_fully_priced else None
    delta = round(baseline_npc - scenario_npc, 2) if baseline_npc is not None and scenario_npc is not None else None

    recommendations = (
        generate_production_recommendations(collection, composition_result=result, register=register, rate=rate, jurisdiction_code=baseline_code)
        if include_recommendations else None
    )

    return ScenarioResult(
        scenario=scenario,
        baseline_candidate_id=baseline.candidate_id if baseline else None,
        scenario_candidate_id=scenario_candidate.candidate_id if scenario_candidate else None,
        baseline_risk_adjusted_npc_usd=baseline_npc,
        scenario_risk_adjusted_npc_usd=scenario_npc,
        delta_usd=delta,
        relevant_structuring_opportunities=(),
        composition_result=result,
        recommendations=recommendations,
        notes="" if scenario_candidate is not None else "Scenario jurisdiction set did not compose into a candidate.",
    )


def _run_structuring_shaped_scenario(
    scenario: ProductionScenario,
    collection: OpportunityCollection,
) -> ScenarioResult:
    subtype = _STRUCTURING_SUBTYPE_BY_KIND.get(scenario.kind)
    relevant = tuple(
        o for o in collection.of_type(OpportunityType.STRUCTURING)
        if subtype is None or o.subtype == subtype
    )
    return ScenarioResult(
        scenario=scenario, baseline_candidate_id=None, scenario_candidate_id=None,
        baseline_risk_adjusted_npc_usd=None, scenario_risk_adjusted_npc_usd=None, delta_usd=None,
        relevant_structuring_opportunities=relevant, composition_result=None, recommendations=None,
        notes=(
            f"No STRUCTURING opportunities with subtype '{subtype}' were discovered."
            if subtype and not relevant else ""
        ),
    )


def run_scenario(
    scenario: ProductionScenario,
    collection: OpportunityCollection,
    graph: Optional[JurisdictionGraph] = None,
    register: Optional[list[AccountQualification]] = None,
    gross_budget_usd: Optional[float] = None,
    rate: Optional[float] = None,
    grey_areas: Optional[list[GreyAreaItem]] = None,
    include_recommendations: bool = False,
    delay_weeks: int = 0,
    bridge_rate: float = 0.0,
) -> ScenarioResult:
    """
    Top-level Part F entry point. Jurisdiction-shaped scenarios
    (MOVE_VFX/POST/MUSIC/SOUND/MARINE, CREATE_COPRODUCTION) require graph
    (and register/gross_budget_usd/rate to be priced — otherwise the
    scenario composes but stays honestly unpriced, same discipline as
    compose_production_structures itself). SHIFT_SPEND/SHIFT_SCHEDULE/
    SHIFT_FINANCING_TIMING have no existing engine representation to
    reuse (no calculator models schedule or financing-timing facts yet)
    and return a not-yet-supported ScenarioResult rather than fabricate
    one.
    """
    if scenario.kind in _JURISDICTION_SHAPED_KINDS:
        if graph is None:
            return ScenarioResult(
                scenario=scenario, baseline_candidate_id=None, scenario_candidate_id=None,
                baseline_risk_adjusted_npc_usd=None, scenario_risk_adjusted_npc_usd=None, delta_usd=None,
                relevant_structuring_opportunities=(), composition_result=None, recommendations=None,
                notes=f"{scenario.kind.value} requires a JurisdictionGraph — none supplied.",
            )
        return _run_jurisdiction_shaped_scenario(
            scenario, collection, graph, register, gross_budget_usd, rate, grey_areas, include_recommendations,
            delay_weeks=delay_weeks, bridge_rate=bridge_rate,
        )
    if scenario.kind in _STRUCTURING_SUBTYPE_BY_KIND or scenario.kind == ScenarioKind.CREATE_SPV:
        return _run_structuring_shaped_scenario(scenario, collection)

    return ScenarioResult(
        scenario=scenario, baseline_candidate_id=None, scenario_candidate_id=None,
        baseline_risk_adjusted_npc_usd=None, scenario_risk_adjusted_npc_usd=None, delta_usd=None,
        relevant_structuring_opportunities=(), composition_result=None, recommendations=None,
        notes=(
            f"{scenario.kind.value} has no existing engine representation to reuse yet "
            "(schedule/financing-timing modeling is out of scope for Phase 7) — not fabricated."
        ),
    )
