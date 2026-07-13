"""
test_opportunity_discovery.py

Targeted tests for Phase 7A — the Global Opportunity Discovery Engine
(opportunity_discovery.py). Covers all seven discovery passes,
determinism, duplicate suppression, traceability (graph + authority
references), LAAE task-reference integration, optimizer compatibility,
and non-mutation of every consumed engine.
"""
from __future__ import annotations

import pytest

from app.calculators import jurisdiction_comparison as jc
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import (
    tasks_from_grey_areas,
    tasks_from_jurisdiction_graph_unknowns,
)
from app.calculators.optimization_engine import RiskCase, build_risk_cases
from app.calculators.qualification_model import (
    GreyAreaStatus,
    QualificationConfidence,
    ReinvestmentCategory,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
)

from app.calculators.opportunity_discovery import (
    MATERIAL_RATE_ADVANTAGE,
    OPPORTUNITY_DISCOVERY_VERSION,
    Opportunity,
    OpportunityCollection,
    OpportunityType,
    dedupe_opportunities,
    discover_all_opportunities,
    discover_grey_area_opportunities,
    discover_jurisdiction_opportunities,
    discover_normalization_opportunities,
    discover_reinvestment_opportunities,
    discover_stacking_opportunities,
    discover_structuring_opportunities,
    discover_treaty_opportunities,
    opportunities_to_structuring_paths,
    rank_opportunities,
)

MU_RATE = 0.40


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


@pytest.fixture(scope="module")
def collection(graph):
    return discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert OPPORTUNITY_DISCOVERY_VERSION == "1.0.0"

    def test_seven_opportunity_types(self):
        assert len(OpportunityType) == 7
        assert {t.value for t in OpportunityType} == {
            "jurisdiction", "treaty", "stacking", "structuring",
            "reinvestment", "normalization", "grey_area",
        }

    def test_all_seven_passes_run(self, collection):
        assert len(collection.passes_run) == 7
        types_present = {o.opportunity_type for o in collection.opportunities}
        assert types_present == set(OpportunityType)


# ── Pass 1: jurisdiction discovery ───────────────────────────────────────────

class TestJurisdictionDiscovery:
    def test_materially_stronger_jurisdictions_found(self):
        opps = discover_jurisdiction_opportunities("MU")
        relocations = [o for o in opps if o.subtype == "relocation_candidate"]
        codes = {o.jurisdiction_codes[1] for o in relocations}
        # MU statutory max is 0.40 (EDB 'up to 40%' feature-film band), so
        # only ES (0.50) clears the +0.05 materiality threshold. BE/GR/IT/MT
        # at 0.40 are NOT stronger — the prior expectation of all five
        # existed only because the profile carried the budget-evidenced
        # 0.35, which is never authority (permanent Rules 1/2/4).
        assert codes == {"ES"}

    def test_rate_delta_carried_not_dollar_upside_invented(self):
        opps = discover_jurisdiction_opportunities("MU")
        for o in opps:
            if o.subtype == "relocation_candidate":
                assert o.estimated_upside_usd is None  # no spend basis — no invented figure
                assert o.attributes["rate_delta"] >= MATERIAL_RATE_ADVANTAGE

    def test_comparable_jurisdictions_are_tier1(self):
        opps = discover_jurisdiction_opportunities("MU")
        comparables = {o.jurisdiction_codes[1] for o in opps if o.subtype == "comparable_jurisdiction"}
        assert comparables == {"CY", "GR", "MT"}  # Tier 1 minus the baseline itself

    def test_none_rate_never_treated_as_advantage(self):
        # A baseline with unknown rate produces no relocation candidates at all.
        profiles = dict(jc.ALL_PROFILES)
        import dataclasses
        profiles["MU"] = dataclasses.replace(profiles["MU"], max_rate=None)
        opps = discover_jurisdiction_opportunities("MU", profiles)
        assert not any(o.subtype == "relocation_candidate" for o in opps)


# ── Pass 2: treaty discovery ─────────────────────────────────────────────────

class TestTreatyDiscovery:
    def test_bilateral_pairs_in_scope_found(self):
        opps = discover_treaty_opportunities(sorted(jc.ALL_PROFILES.keys()))
        bilateral = {o.opportunity_id for o in opps if o.subtype == "bilateral_coproduction"}
        assert bilateral == {
            "OPP-TREATY-BILATERAL-fr-be-bilateral",
            "OPP-TREATY-BILATERAL-fr-de-bilateral",
        }

    def test_nationality_unlocks_depend_on_their_treaty(self):
        opps = discover_treaty_opportunities(["FR", "BE"])
        unlocks = [o for o in opps if o.subtype == "nationality_unlock"]
        assert unlocks
        for o in unlocks:
            assert o.dependent_opportunity_ids == ("OPP-TREATY-BILATERAL-fr-be-bilateral",)

    def test_multilateral_memberships_found(self):
        opps = discover_treaty_opportunities(["FR", "ES", "MU"])
        multi = {(o.jurisdiction_codes[0], o.graph_refs[0]) for o in opps if o.subtype == "multilateral_membership"}
        assert ("ES", "treaty:ibermedia") in multi
        assert ("FR", "treaty:eurimages") in multi
        assert not any(code == "MU" for code, _ in multi)

    def test_composition_path_when_no_bilateral_but_both_convention(self):
        opps = discover_treaty_opportunities(["GR", "IT"])  # no GR-IT bilateral in registry
        composed = [o for o in opps if o.subtype == "treaty_composition_path"]
        assert len(composed) == 1
        assert composed[0].jurisdiction_codes == ("GR", "IT")

    def test_mauritius_treaty_absence_yields_nothing_fabricated(self):
        opps = discover_treaty_opportunities(["MU"])
        assert opps == []  # honest absence — the gap lives in the graph and the LAAE docket


# ── Pass 3: stacking discovery ───────────────────────────────────────────────

class TestStackingDiscovery:
    def test_unknown_stacking_becomes_evidence_required_opportunity(self, graph):
        opps = discover_stacking_opportunities(graph)
        unknowns = [o for o in opps if o.subtype == "stacking_unknown"]
        assert len(unknowns) == len(jc.ALL_PROFILES)  # one per program, all ABSENT today
        for o in unknowns:
            assert o.requires_evidence is True
            assert o.confidence == QualificationConfidence.LOW

    def test_no_fabricated_stackability(self, graph):
        opps = discover_stacking_opportunities(graph)
        # No STACKS_WITH edge exists in today's graph, so no known stack may appear.
        assert not any(o.subtype == "known_stack" for o in opps)

    def test_stacking_unknown_carries_laae_task_reference(self, graph):
        opps = discover_stacking_opportunities(graph)
        laae_task_ids = {t.task_id for t in tasks_from_jurisdiction_graph_unknowns(graph)}
        for o in opps:
            if o.subtype == "stacking_unknown":
                assert len(o.acquisition_task_refs) == 1
                assert o.acquisition_task_refs[0] in laae_task_ids


# ── Pass 4: structuring discovery ────────────────────────────────────────────

class TestStructuringDiscovery:
    def test_one_opportunity_per_existing_lever(self):
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        opps = discover_structuring_opportunities(register, rate=MU_RATE)
        assert len(opps) == 3
        accounts = {o.affected_accounts[0] for o in opps}
        assert accounts == {"21-00", "23-00", "42-00"}

    def test_upside_carried_from_lever_not_recomputed(self):
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        opps = discover_structuring_opportunities(register, rate=MU_RATE)
        by_account = {o.affected_accounts[0]: o for o in opps}
        assert by_account["21-00"].estimated_upside_usd == pytest.approx(38_000.0)
        assert by_account["23-00"].estimated_upside_usd == pytest.approx(26_000.0)
        assert by_account["42-00"].estimated_upside_usd == pytest.approx(19_200.0)

    def test_routing_classification_is_deterministic(self):
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        first = [o.subtype for o in discover_structuring_opportunities(register, rate=MU_RATE)]
        second = [o.subtype for o in discover_structuring_opportunities(register, rate=MU_RATE)]
        assert first == second


# ── Pass 5: reinvestment discovery ───────────────────────────────────────────

class TestReinvestmentDiscovery:
    def test_unknown_becomes_opportunity_requiring_evidence(self):
        opps = discover_reinvestment_opportunities(["MU"])
        assert len(opps) == 1
        o = opps[0]
        assert o.subtype == "reinvestment_unknown"
        assert o.requires_evidence is True
        assert o.acquisition_task_refs == ("TASK-reinvestment:MU",)

    def test_unknown_is_not_assumed_unavailable(self):
        # The registry says UNKNOWN, and discovery must emit an opportunity —
        # the exact opposite of treating it as NOT_PERMITTED.
        assert get_reinvestment_profile("MU").category == ReinvestmentCategory.UNKNOWN
        opps = discover_reinvestment_opportunities(["MU"])
        assert opps  # not silently dropped

    def test_every_modeled_jurisdiction_covered(self):
        codes = sorted(jc.ALL_PROFILES.keys())
        opps = discover_reinvestment_opportunities(codes)
        assert {o.jurisdiction_codes[0] for o in opps} == set(codes)  # all UNKNOWN today, none NOT_PERMITTED


# ── Pass 6: normalization discovery ──────────────────────────────────────────

class TestNormalizationDiscovery:
    def test_vat_recovery_opportunities_from_existing_fields(self):
        opps = discover_normalization_opportunities("MU")
        vat = [o for o in opps if o.subtype == "vat_recovery"]
        # MU vat_recoverable=False; every other modeled jurisdiction is True.
        assert len(vat) == len(jc.ALL_PROFILES) - 1

    def test_no_timing_comparison_against_unknown_baseline(self):
        # MU's cashflow_timing_weeks is None — no fund-timing comparison may be made.
        opps = discover_normalization_opportunities("MU")
        assert not any(o.subtype == "fund_timing" for o in opps)

    def test_timing_comparison_when_baseline_known(self):
        # Greece pays out in ~39 weeks; Ireland in ~12 — a real timing opportunity.
        opps = discover_normalization_opportunities("GR")
        timing = {o.jurisdiction_codes[1] for o in opps if o.subtype == "fund_timing"}
        assert "IE" in timing

    def test_labor_normalization_uses_known_payroll_burdens(self):
        # France's 45% burden vs many lower-burden candidates.
        opps = discover_normalization_opportunities("FR")
        labor = {o.jurisdiction_codes[1] for o in opps if o.subtype == "labor_normalization"}
        assert "CY" in labor and "MU" in labor

    def test_application_timing_unknowns_route_to_laae(self, graph):
        opps = discover_normalization_opportunities("MU", graph=graph)
        app_timing = [o for o in opps if o.subtype == "application_timing_unknown"]
        assert len(app_timing) == len(jc.ALL_PROFILES)
        laae_task_ids = {t.task_id for t in tasks_from_jurisdiction_graph_unknowns(graph)}
        for o in app_timing:
            assert o.acquisition_task_refs[0] in laae_task_ids

    def test_cross_jurisdiction_normalization_depends_on_relocation(self):
        opps = discover_normalization_opportunities("MU")
        vat_to_es = next(o for o in opps if o.opportunity_id == "OPP-NORM-VAT-MU-ES")
        assert vat_to_es.dependent_opportunity_ids == ("OPP-JUR-RELOCATE-MU-ES",)


# ── Pass 7: grey area discovery ──────────────────────────────────────────────

class TestGreyAreaDiscovery:
    def test_every_open_grey_area_becomes_quantified_opportunity(self):
        opps = discover_grey_area_opportunities(build_little_utopia_grey_areas(), rate=MU_RATE)
        assert len(opps) == 2
        by_ref = {o.source_ref: o for o in opps}
        assert by_ref["GA-LEGAL-ACCOUNTING-SPLIT"].estimated_upside_usd == pytest.approx(113_000.0 * MU_RATE)

    def test_resolved_grey_area_not_re_emitted(self):
        areas = build_little_utopia_grey_areas()
        areas[0].status = GreyAreaStatus.RESOLVED_INCLUDE
        opps = discover_grey_area_opportunities(areas, rate=MU_RATE)
        assert [o.source_ref for o in opps] == ["GA-INKIND-FMV"]

    def test_grey_area_carries_authority_and_task_references(self):
        opps = discover_grey_area_opportunities(build_little_utopia_grey_areas(), rate=MU_RATE)
        laae_task_ids = {t.task_id for t in tasks_from_grey_areas(build_little_utopia_grey_areas())}
        for o in opps:
            assert o.graph_absence_id is not None       # Evidence Graph reference
            assert o.authority_score == 0.0             # absence never manufactures confidence
            assert o.acquisition_task_refs[0] in laae_task_ids

    def test_grey_areas_rank_by_financial_swing(self):
        opps = rank_opportunities(discover_grey_area_opportunities(build_little_utopia_grey_areas(), rate=MU_RATE))
        swings = [o.estimated_upside_usd for o in opps]
        assert swings == sorted(swings, reverse=True)


# ── Determinism & duplicate suppression ──────────────────────────────────────

class TestDeterminismAndDedup:
    def test_two_full_runs_are_identical(self, graph):
        c1 = discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)
        c2 = discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)
        assert [o.opportunity_id for o in c1.opportunities] == [o.opportunity_id for o in c2.opportunities]
        assert [o.discovery_rank_score for o in c1.opportunities] == [o.discovery_rank_score for o in c2.opportunities]

    def test_opportunity_ids_unique_in_collection(self, collection):
        ids = [o.opportunity_id for o in collection.opportunities]
        assert len(ids) == len(set(ids))

    def test_dedupe_suppresses_duplicates_keeping_first(self):
        a = Opportunity(
            opportunity_id="OPP-X", opportunity_type=OpportunityType.JURISDICTION,
            subtype="s", description="first", jurisdiction_codes=("MU",),
        )
        b = Opportunity(
            opportunity_id="OPP-X", opportunity_type=OpportunityType.JURISDICTION,
            subtype="s", description="second", jurisdiction_codes=("MU",),
        )
        deduped = dedupe_opportunities([a, b])
        assert len(deduped) == 1
        assert deduped[0].description == "first"

    def test_ranking_ties_break_on_id_not_insertion_order(self):
        a = Opportunity(opportunity_id="OPP-B", opportunity_type=OpportunityType.TREATY,
                        subtype="s", description="", jurisdiction_codes=())
        b = Opportunity(opportunity_id="OPP-A", opportunity_type=OpportunityType.TREATY,
                        subtype="s", description="", jurisdiction_codes=())
        assert [o.opportunity_id for o in rank_opportunities([a, b])] == ["OPP-A", "OPP-B"]


# ── Traceability ─────────────────────────────────────────────────────────────

class TestTraceability:
    def test_every_opportunity_has_source_ref(self, collection):
        assert all(o.source_ref for o in collection.opportunities)

    def test_graph_refs_resolve_to_real_graph_nodes(self, collection, graph):
        for o in collection.opportunities:
            for ref in o.graph_refs:
                assert graph.has_node(ref), f"{o.opportunity_id} references unknown graph node '{ref}'"

    def test_evidence_required_opportunities_carry_task_refs(self, collection):
        for o in collection.opportunities:
            if o.requires_evidence:
                assert o.acquisition_task_refs or o.graph_absence_id, (
                    f"{o.opportunity_id} requires evidence but references neither an "
                    "acquisition task nor an absence node — a silent gap."
                )

    def test_grey_area_absence_ids_resolve_in_evidence_graph(self, collection):
        from app.calculators.qualification_model import build_little_utopia_evidence_graph
        eg = build_little_utopia_evidence_graph()
        for o in collection.of_type(OpportunityType.GREY_AREA):
            assert eg.get_absence_of_authority(o.graph_absence_id) is not None


# ── Optimizer compatibility & non-mutation ───────────────────────────────────

class TestOptimizerCompatibility:
    def test_structuring_opportunities_convert_to_paths_optimizer_accepts(self, collection):
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        paths = opportunities_to_structuring_paths(
            collection.opportunities, register=register, rate=MU_RATE,
        )
        assert [p.path_id for p in paths] == ["SP-21-00", "SP-23-00", "SP-42-00"]
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=MU_RATE,
            structuring_paths=paths,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(2_846_357.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_138_542.8, abs=1.0)

    def test_no_optimizer_output_change_from_discovery_existing(self):
        # Baseline behavior — optimizer consuming its own derive path —
        # must be identical whether or not discovery ever ran.
        from app.calculators.structuring_paths import derive_structuring_paths
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        paths = derive_structuring_paths(register, rate=MU_RATE)
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=MU_RATE,
            structuring_paths=paths,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(2_846_357.0, abs=1.0)

    def test_discovery_module_imports_no_optimizer(self):
        import ast
        import inspect
        import app.calculators.opportunity_discovery as od

        tree = ast.parse(inspect.getsource(od))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any("optimization_engine" in m for m in imported)

    def test_discovery_does_not_mutate_jurisdiction_graph(self, graph):
        nodes_before = len(graph.nodes)
        rels_before = len(graph.relationships)
        discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)
        assert len(graph.nodes) == nodes_before
        assert len(graph.relationships) == rels_before

    def test_discovery_does_not_mutate_source_registries(self):
        profiles_before = {code: p.max_rate for code, p in jc.ALL_PROFILES.items()}
        grey_before = [(g.item_id, g.status) for g in build_little_utopia_grey_areas()]
        discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE)
        assert {code: p.max_rate for code, p in jc.ALL_PROFILES.items()} == profiles_before
        assert [(g.item_id, g.status) for g in build_little_utopia_grey_areas()] == grey_before

    def test_collection_is_ranked_output(self, collection):
        scores = [o.discovery_rank_score for o in collection.opportunities]
        assert scores == sorted(scores, reverse=True)
        # Quantified grey-area swings outrank everything unquantified.
        assert collection.opportunities[0].opportunity_type == OpportunityType.GREY_AREA
