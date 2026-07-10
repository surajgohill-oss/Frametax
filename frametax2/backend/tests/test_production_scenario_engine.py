"""
test_production_scenario_engine.py

Targeted tests for Phase 7 closeout, Part F — the Scenario Engine.
Covers jurisdiction-shaped scenarios (real re-composition through the
existing composer, no new pricing math), structuring-shaped scenarios
(filtering already-discovered opportunities, no new discovery),
unsupported scenario kinds (honest non-fabrication), determinism,
non-mutation, and Little Utopia compatibility.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.opportunity_discovery import OpportunityType, discover_all_opportunities
from app.calculators.optimization_engine import RiskCase, build_risk_cases
from app.calculators.opportunity_discovery import opportunities_to_structuring_paths
from app.calculators.qualification_model import build_little_utopia_grey_areas, build_little_utopia_qualification_register

from app.calculators.production_scenario_engine import (
    PRODUCTION_SCENARIO_ENGINE_VERSION,
    ProductionScenario,
    ScenarioKind,
    run_scenario,
)

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


@pytest.fixture(scope="module")
def collection(graph):
    return discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)


@pytest.fixture()
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def target_jurisdiction(collection):
    codes = sorted({c for o in collection.opportunities for c in o.jurisdiction_codes if c != "MU"})
    assert codes, "expected at least one non-MU jurisdiction in the modeled world"
    return codes[0]


class TestJurisdictionShapedScenarios:
    def test_move_vfx_recomposes_via_existing_composer(self, collection, graph, register, grey_areas, target_jurisdiction):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert result.composition_result is not None
        assert result.baseline_candidate_id == "PSC-MU"
        assert result.scenario_candidate_id == f"PSC-MU-{target_jurisdiction}"

    def test_missing_target_jurisdiction_does_not_fabricate(self, collection, graph):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx")
        result = run_scenario(scenario, collection, graph=graph)
        assert result.composition_result is None
        assert "target_jurisdiction" in result.notes

    def test_missing_graph_does_not_fabricate(self, collection):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction="FR")
        result = run_scenario(scenario, collection, graph=None)
        assert result.composition_result is None
        assert "JurisdictionGraph" in result.notes

    def test_delta_is_none_when_scenario_candidate_not_fully_priced(self, collection, graph, register, grey_areas, target_jurisdiction):
        """Only MU has a register in this codebase — a relocation
        candidate has no register, so its NPC must stay unpriced, never
        estimated."""
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_POST, description="move post", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert result.scenario_risk_adjusted_npc_usd is None
        assert result.delta_usd is None

    def test_baseline_npc_matches_direct_optimizer_call(self, collection, graph, register, grey_areas, target_jurisdiction):
        """Proves the scenario's baseline pricing is exactly what a
        direct build_risk_cases() call produces — no new math."""
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_MUSIC, description="move music", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)

        baseline = next(c for c in result.composition_result.candidates if c.candidate_id == "PSC-MU")
        paths = opportunities_to_structuring_paths(
            [o for o in collection.opportunities if o.opportunity_id in baseline.included_opportunity_ids],
            register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        direct = build_risk_cases(
            register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, delay_weeks=39, bridge_rate=0.08, jurisdiction_code="MU",
        )
        assert result.baseline_risk_adjusted_npc_usd == direct.cases[RiskCase.RISK_ADJUSTED].net_production_cost_usd

    def test_create_coproduction_is_jurisdiction_shaped(self, collection, graph, register, grey_areas, target_jurisdiction):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.CREATE_COPRODUCTION, description="coprod", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert result.composition_result is not None

    def test_include_recommendations_reuses_recommendation_engine(self, collection, graph, register, grey_areas, target_jurisdiction):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, include_recommendations=True)
        assert result.recommendations is not None
        assert len(result.recommendations.recommendations) > 0

    def test_recommendations_omitted_by_default(self, collection, graph, register, grey_areas, target_jurisdiction):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction=target_jurisdiction)
        result = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert result.recommendations is None


class TestStructuringShapedScenarios:
    def test_create_spv_filters_existing_spv_routing_opportunities(self, collection):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.CREATE_SPV, description="create spv")
        result = run_scenario(scenario, collection)
        assert result.composition_result is None
        expected = [o for o in collection.of_type(OpportunityType.STRUCTURING) if o.subtype == "spv_routing"]
        assert len(result.relevant_structuring_opportunities) == len(expected)
        assert result.relevant_structuring_opportunities == tuple(expected)

    def test_never_reclassifies_opportunities_only_filters(self, collection):
        """Every returned opportunity must be an object already present
        in the OpportunityCollection — never a new/modified one."""
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.CREATE_SPV, description="create spv")
        result = run_scenario(scenario, collection)
        collection_ids = {o.opportunity_id for o in collection.opportunities}
        assert all(o.opportunity_id in collection_ids for o in result.relevant_structuring_opportunities)


class TestUnsupportedScenarios:
    def test_shift_spend_reports_not_yet_supported_honestly(self, collection):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.SHIFT_SPEND, description="shift spend")
        result = run_scenario(scenario, collection)
        assert result.composition_result is None
        assert result.relevant_structuring_opportunities == ()
        assert "not fabricated" in result.notes

    def test_shift_schedule_reports_not_yet_supported(self, collection):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.SHIFT_SCHEDULE, description="shift schedule")
        result = run_scenario(scenario, collection)
        assert result.delta_usd is None
        assert result.notes

    def test_shift_financing_timing_reports_not_yet_supported(self, collection):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.SHIFT_FINANCING_TIMING, description="shift financing")
        result = run_scenario(scenario, collection)
        assert result.delta_usd is None
        assert result.notes


class TestDeterminismAndNonMutation:
    def test_two_runs_produce_identical_result(self, collection, graph, register, grey_areas, target_jurisdiction):
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction=target_jurisdiction)
        r1 = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        r2 = run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert r1.delta_usd == r2.delta_usd
        assert r1.scenario_candidate_id == r2.scenario_candidate_id

    def test_does_not_mutate_collection_or_register(self, collection, graph, register, grey_areas, target_jurisdiction):
        before_opp_ids = [o.opportunity_id for o in collection.opportunities]
        before_register = copy.deepcopy(register)
        scenario = ProductionScenario(scenario_id="S1", kind=ScenarioKind.MOVE_VFX, description="move vfx", target_jurisdiction=target_jurisdiction)
        run_scenario(scenario, collection, graph=graph, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert [o.opportunity_id for o in collection.opportunities] == before_opp_ids
        assert register == before_register

    def test_version_constant_present(self):
        assert PRODUCTION_SCENARIO_ENGINE_VERSION
