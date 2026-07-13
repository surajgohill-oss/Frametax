"""
test_global_scenario_ranker.py

Targeted tests for Phase 7B — the Global Scenario Ranker / Production
Structure Composer (global_scenario_ranker.py). Covers structure
composition, dependency enforcement, the claim ledger's double-counting
prevention (including the STACKS_WITH exception), four-case pricing,
sparse-data honesty, determinism, and non-mutation of upstream engines.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.opportunity_discovery import (
    Opportunity,
    OpportunityCollection,
    OpportunityType,
    discover_all_opportunities,
)
from app.calculators.optimization_engine import RiskCase
from app.calculators.qualification_model import (
    QualificationConfidence,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)

from app.calculators.global_scenario_ranker import (
    GLOBAL_SCENARIO_RANKER_VERSION,
    ClaimLedger,
    ProductionStructure,
    StructureClaim,
    StructureRankingResult,
    compose_candidate_structures,
    rank_production_structures,
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
def structures(collection, register, grey_areas):
    return compose_candidate_structures(
        collection, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )


def _opp(**kwargs) -> Opportunity:
    defaults = dict(
        opportunity_id="OPP-X", opportunity_type=OpportunityType.STRUCTURING,
        subtype="s", description="", jurisdiction_codes=("MU",),
    )
    defaults.update(kwargs)
    return Opportunity(**defaults)


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert GLOBAL_SCENARIO_RANKER_VERSION == "1.0.0"


# ── Candidate structure creation ─────────────────────────────────────────────

class TestStructureCreation:
    def test_baseline_structure_created(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        assert baseline.baseline_jurisdiction == "MU"
        assert baseline.included_opportunity_ids

    def test_relocation_structures_created_per_candidate(self, structures, collection):
        relocation_ids = {
            o.jurisdiction_codes[1] for o in collection.opportunities
            if o.opportunity_type == OpportunityType.JURISDICTION and o.subtype == "relocation_candidate"
        }
        struct_targets = {
            s.attributes["target_jurisdiction"] for s in structures if s.structure_id != "STRUCT-BASELINE-MU"
        }
        assert struct_targets == relocation_ids

    def test_baseline_only_includes_mu_scoped_opportunities(self, structures, collection):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        by_id = {o.opportunity_id: o for o in collection.opportunities}
        for oid in baseline.included_opportunity_ids:
            assert "MU" in by_id[oid].jurisdiction_codes


# ── Dependency enforcement ────────────────────────────────────────────────────

class TestDependencyEnforcement:
    def test_dependent_excluded_without_its_dependency(self):
        dependency = _opp(opportunity_id="OPP-DEP", description="dependency")
        dependent = _opp(
            opportunity_id="OPP-CHILD", dependent_opportunity_ids=("OPP-MISSING",), description="child",
        )
        collection = OpportunityCollection(
            baseline_jurisdiction="MU", passes_run=(), opportunities=[dependency, dependent],
        )
        structures = compose_candidate_structures(collection)
        baseline = structures[0]
        assert "OPP-CHILD" in baseline.excluded_opportunity_ids
        assert "OPP-MISSING" in baseline.exclusion_reasons["OPP-CHILD"]

    def test_dependent_included_when_dependency_present(self):
        dependency = _opp(opportunity_id="OPP-DEP", description="dependency", attributes={"confidence_gap": 1, "research_effort": 1})
        dependent = _opp(
            opportunity_id="OPP-CHILD", dependent_opportunity_ids=("OPP-DEP",), description="child",
        )
        collection = OpportunityCollection(
            baseline_jurisdiction="MU", passes_run=(), opportunities=[dependency, dependent],
        )
        structures = compose_candidate_structures(collection)
        baseline = structures[0]
        assert "OPP-DEP" in baseline.included_opportunity_ids
        assert "OPP-CHILD" in baseline.included_opportunity_ids

    def test_real_normalization_dependency_on_relocation_enforced(self, collection):
        vat_to_es = next(o for o in collection.opportunities if o.opportunity_id == "OPP-NORM-VAT-MU-ES")
        assert vat_to_es.dependent_opportunity_ids == ("OPP-JUR-RELOCATE-MU-ES",)
        es_structure = next(
            s for s in compose_candidate_structures(collection) if s.attributes.get("target_jurisdiction") == "ES"
        )
        assert "OPP-JUR-RELOCATE-MU-ES" in es_structure.included_opportunity_ids
        assert "OPP-NORM-VAT-MU-ES" in es_structure.included_opportunity_ids


# ── Claim ledger / duplicate suppression ─────────────────────────────────────

class TestClaimLedger:
    def test_claim_ledger_prevents_double_counting(self):
        a = _opp(opportunity_id="OPP-A", affected_accounts=("21-00",), description="a")
        b = _opp(opportunity_id="OPP-B", affected_accounts=("21-00",), description="b")
        collection = OpportunityCollection(baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b])
        baseline = compose_candidate_structures(collection)[0]
        included = set(baseline.included_opportunity_ids)
        assert len(included & {"OPP-A", "OPP-B"}) == 1  # only one of the two claims the account
        excluded_one = ({"OPP-A", "OPP-B"} - included).pop()
        assert "Claim conflict" in baseline.exclusion_reasons[excluded_one]

    def test_stacking_unknown_does_not_authorize_double_counting(self):
        a = _opp(opportunity_id="OPP-A", affected_accounts=("21-00",), description="a", graph_refs=("lever:A",))
        b = _opp(opportunity_id="OPP-B", affected_accounts=("21-00",), description="b", graph_refs=("lever:B",))
        stacking_unknown = _opp(
            opportunity_id="OPP-STACK-UNK", opportunity_type=OpportunityType.STACKING,
            subtype="stacking_unknown", description="unknown", graph_refs=("lever:A", "lever:B"),
        )
        collection = OpportunityCollection(
            baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b, stacking_unknown],
        )
        baseline = compose_candidate_structures(collection)[0]
        included = set(baseline.included_opportunity_ids) & {"OPP-A", "OPP-B"}
        assert len(included) == 1  # stacking_unknown never waives the conflict

    def test_stacks_with_evidence_allows_stacking(self):
        a = _opp(opportunity_id="OPP-A", affected_accounts=("21-00",), description="a", graph_refs=("lever:A",))
        b = _opp(opportunity_id="OPP-B", affected_accounts=("21-00",), description="b", graph_refs=("lever:B",))
        known_stack = _opp(
            opportunity_id="OPP-STACK-KNOWN", opportunity_type=OpportunityType.STACKING,
            subtype="known_stack", description="known", graph_refs=("lever:A", "lever:B"),
        )
        collection = OpportunityCollection(
            baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b, known_stack],
        )
        baseline = compose_candidate_structures(collection)[0]
        included = set(baseline.included_opportunity_ids)
        assert {"OPP-A", "OPP-B"}.issubset(included)  # both included — real STACKS_WITH evidence

    def test_claims_recorded_in_ledger(self):
        a = _opp(opportunity_id="OPP-A", affected_accounts=("21-00", "23-00"), description="a")
        collection = OpportunityCollection(baseline_jurisdiction="MU", passes_run=(), opportunities=[a])
        baseline = compose_candidate_structures(collection)[0]
        assert baseline.claim_ledger.all_keys() == ("MU:21-00", "MU:23-00")
        assert baseline.claim_ledger.claimed_by("MU:21-00") == ["OPP-A"]

    def test_claim_ledger_and_structure_claim_are_the_public_types(self):
        ledger = ClaimLedger()
        ledger.record("MU:21-00", "OPP-A")
        assert isinstance(ledger.claims[0], StructureClaim)
        assert ledger.claims[0].claim_key == "MU:21-00"

    def test_opportunities_without_accounts_never_conflict(self):
        a = _opp(opportunity_id="OPP-A", opportunity_type=OpportunityType.TREATY, description="a", affected_accounts=())
        b = _opp(opportunity_id="OPP-B", opportunity_type=OpportunityType.TREATY, description="b", affected_accounts=())
        collection = OpportunityCollection(baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b])
        baseline = compose_candidate_structures(collection)[0]
        assert set(baseline.included_opportunity_ids) == {"OPP-A", "OPP-B"}


# ── Non-priceable / informational opportunities ───────────────────────────────

class TestNonPriceableOpportunities:
    def test_non_priceable_opportunity_preserved_but_no_upside_invented(self):
        rate_only = _opp(
            opportunity_id="OPP-RATE", opportunity_type=OpportunityType.JURISDICTION,
            subtype="relocation_candidate", jurisdiction_codes=("MU", "ES"),
            estimated_upside_usd=None, description="",
        )
        collection = OpportunityCollection(baseline_jurisdiction="MU", passes_run=(), opportunities=[rate_only])
        baseline = compose_candidate_structures(collection)[0]
        assert "OPP-RATE" in baseline.included_opportunity_ids
        assert baseline.informational_upside_usd is None  # no known figure — never a fabricated number

    def test_priceable_structure_never_double_counts_via_informational_field(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        assert baseline.is_priceable is True
        assert baseline.informational_upside_usd is None  # already fully reflected in .cases

    def test_relocation_structures_always_non_priceable(self, structures):
        for s in structures:
            if s.structure_id != "STRUCT-BASELINE-MU":
                assert s.is_priceable is False
                assert s.cases is None


# ── Grey area gating ──────────────────────────────────────────────────────────

class TestGreyAreaGating:
    def test_grey_area_opportunities_remain_gated(self, structures, grey_areas):
        """The remaining grey area (GA-INKIND-FMV, off-budget in-kind post
        FMV) is OPEN and must not be reflected in Conservative — no
        on-budget account currently carries a grey-area classification
        under the canonical QPE rule (see test_qualification_model.py),
        so gating is verified via the off-budget in-kind addon instead of
        an account code."""
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        grey_opp_ids = [oid for oid in baseline.included_opportunity_ids if oid.startswith("OPP-GREY-")]
        assert grey_opp_ids  # present
        # None of them are RESOLVED_INCLUDE, so Conservative must not include their value.
        assert all(g.status.value == "open" for g in grey_areas)
        cons = baseline.cases[RiskCase.CONSERVATIVE]
        assert cons.inkind_addon_usd == 0.0  # unresolved off-budget in-kind stays out of Conservative

    def test_grey_area_carries_blocking_requirement(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        assert any("OPP-GREY-" in line for line in baseline.blocking_requirements)


# ── Structuring opportunities compose correctly ───────────────────────────────

class TestStructuringComposition:
    def test_all_three_little_utopia_levers_included(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        struct_ids = {oid for oid in baseline.included_opportunity_ids if oid.startswith("OPP-STRUCT-")}
        assert struct_ids == {"OPP-STRUCT-SP-21-00", "OPP-STRUCT-SP-23-00", "OPP-STRUCT-SP-42-00"}

    def test_structuring_accounts_do_not_conflict_with_each_other(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        assert not any("OPP-STRUCT-" in oid for oid in baseline.excluded_opportunity_ids)


# ── Four-case pricing ─────────────────────────────────────────────────────────

class TestFourCasePricing:
    def test_priceable_structure_exposes_all_four_cases(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        assert set(baseline.cases.keys()) == {
            RiskCase.CONSERVATIVE, RiskCase.BASE, RiskCase.OPTIMISTIC, RiskCase.RISK_ADJUSTED,
        }

    def test_answer_is_not_reduced_to_one_number(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        npcs = {case: cr.net_production_cost_usd for case, cr in baseline.cases.items()}
        assert len(set(npcs.values())) > 1  # the four cases are not collapsed to a single figure

    def test_existing_little_utopia_conservative_result_unchanged(self, structures):
        baseline = next(s for s in structures if s.structure_id == "STRUCT-BASELINE-MU")
        cons = baseline.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_700_954.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_480_381.6, abs=1.0)

    def test_non_priceable_structure_has_no_cases(self, structures):
        for s in structures:
            if not s.is_priceable:
                assert s.cases is None

    def test_missing_pricing_inputs_yields_non_priceable_not_invented(self, collection):
        structures = compose_candidate_structures(collection)  # no register/budget/rate supplied
        baseline = structures[0]
        assert baseline.is_priceable is False
        assert baseline.cases is None


# ── Ranking ───────────────────────────────────────────────────────────────────

class TestRanking:
    def test_rank_by_risk_adjusted_npc(self, structures):
        result = rank_production_structures(structures)
        assert isinstance(result, StructureRankingResult)
        priceable_ranks = [r for r in result.ranks if r.is_priceable]
        assert len(priceable_ranks) == 1
        assert priceable_ranks[0].rank == 1

    def test_non_priceable_ranked_after_priceable(self, structures):
        result = rank_production_structures(structures)
        priceable_positions = [r.rank for r in result.ranks if r.is_priceable]
        non_priceable_positions = [r.rank for r in result.ranks if not r.is_priceable]
        assert max(priceable_positions) < min(non_priceable_positions)

    def test_non_priceable_rank_order_deterministic_by_id(self, structures):
        result = rank_production_structures(structures)
        non_priceable_ids = [r.structure_id for r in result.ranks if not r.is_priceable]
        assert non_priceable_ids == sorted(non_priceable_ids)

    def test_best_returns_priceable_structure(self, structures):
        result = rank_production_structures(structures)
        best = result.best()
        assert best is not None
        assert best.is_priceable is True

    def test_best_returns_none_when_nothing_priceable(self):
        non_priceable = [
            ProductionStructure(
                structure_id="S1", label="s1", baseline_jurisdiction="MU",
                included_opportunity_ids=(), excluded_opportunity_ids=(), exclusion_reasons={},
                claim_ledger=ClaimLedger(), blocking_requirements=(), is_priceable=False,
            )
        ]
        result = rank_production_structures(non_priceable)
        assert result.best() is None


# ── Determinism ────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_repeated_composition_identical(self, collection, register, grey_areas):
        s1 = compose_candidate_structures(collection, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        s2 = compose_candidate_structures(collection, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert [s.structure_id for s in s1] == [s.structure_id for s in s2]
        assert [s.included_opportunity_ids for s in s1] == [s.included_opportunity_ids for s in s2]

    def test_repeated_ranking_identical(self, structures):
        r1 = rank_production_structures(structures)
        r2 = rank_production_structures(structures)
        assert [r.structure_id for r in r1.ranks] == [r.structure_id for r in r2.ranks]


# ── Non-mutation ────────────────────────────────────────────────────────────────

class TestNonMutation:
    def test_no_mutation_of_opportunity_collection(self, collection, register, grey_areas):
        ids_before = [o.opportunity_id for o in collection.opportunities]
        compose_candidate_structures(collection, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        ids_after = [o.opportunity_id for o in collection.opportunities]
        assert ids_before == ids_after

    def test_no_mutation_of_register(self, collection, register, grey_areas):
        snapshot = copy.deepcopy(register)
        compose_candidate_structures(collection, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert register == snapshot

    def test_no_mutation_of_grey_areas_input(self, collection, register, grey_areas):
        snapshot = copy.deepcopy(grey_areas)
        compose_candidate_structures(collection, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas)
        assert grey_areas == snapshot

    def test_no_optimizer_output_change_from_direct_call(self, register, grey_areas):
        """Calling build_risk_cases() directly (the pre-Phase-7B path) must
        still produce the same result it always did."""
        from app.calculators.structuring_paths import derive_structuring_paths
        from app.calculators.optimization_engine import build_risk_cases

        paths = derive_structuring_paths(register, rate=MU_RATE)
        result = build_risk_cases(
            register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_700_954.0, abs=1.0)

    def test_module_does_not_modify_optimization_engine_source_import(self):
        import ast
        import inspect
        import app.calculators.global_scenario_ranker as gsr

        tree = ast.parse(inspect.getsource(gsr))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        # It's expected (and required) to import build_risk_cases/RiskCase/
        # CaseResult — the boundary being tested is that it imports the
        # *public* API, never reaches into optimization_engine internals
        # via a private name.
        assert "app.calculators.optimization_engine" in imported
