"""
test_production_structure_composer.py

Targeted tests for Phase 7C — the Multi-Jurisdiction Production Structure
Composer (production_structure_composer.py). Covers single- and
multi-jurisdiction composition, treaty/stack/fund composition,
dependency/approval/authority preservation, duplicate elimination,
dominance pruning, determinism, double-counting prevention, graph
traceability, sparse-data honesty, partial priceability, optimizer
compatibility, and non-mutation of every consumed object.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.global_scenario_ranker import ClaimLedger
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.opportunity_discovery import (
    Opportunity,
    OpportunityCollection,
    OpportunityType,
    discover_all_opportunities,
)
from app.calculators.optimization_engine import CaseResult, RiskCase
from app.calculators.qualification_model import (
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)

from app.calculators.production_structure_composer import (
    COMPOSITION_PASSES,
    PRODUCTION_STRUCTURE_COMPOSER_VERSION,
    CompositionResult,
    IncentiveClaim,
    JurisdictionSegment,
    ProductionStructureCandidate,
    StackComposition,
    StructureConstraint,
    StructureSegment,
    TreatyComposition,
    compose_production_structures,
    eliminate_duplicates,
    prune_dominated,
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
def result(collection, graph, register, grey_areas):
    return compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )


def _mu_candidate(result: CompositionResult) -> ProductionStructureCandidate:
    return next(c for c in result.candidates if c.candidate_id == "PSC-MU")


def _priced_candidate(candidate_id: str, npcs: dict[RiskCase, float]) -> ProductionStructureCandidate:
    """Synthetic fully-priced candidate for dominance-pruning tests."""
    cases = {
        case: CaseResult(
            case=case, qpe_usd=0.0, incentive_usd=0.0, finance_cost_usd=0.0,
            net_benefit_usd=0.0, net_production_cost_usd=npc,
            included_codes=(), excluded_codes=(),
        )
        for case, npc in npcs.items()
    }
    return ProductionStructureCandidate(
        candidate_id=candidate_id, label=candidate_id,
        jurisdiction_segments=(JurisdictionSegment("MU", "mu_edb_incentive", "country:MU", "program:mu_edb_incentive", True),),
        treaty_compositions=(), stack_compositions=(), fund_graph_refs=(),
        incentive_claims=(), included_opportunity_ids=(), excluded_opportunity_ids=(),
        exclusion_reasons={}, grey_area_opportunity_ids=(), evidence_graph_refs=(),
        required_approvals=(), required_acquisition_task_refs=(), constraints=(),
        claim_ledger=ClaimLedger(), cases=cases, priceable_pct=1.0, unknown_pct=0.0,
    )


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert PRODUCTION_STRUCTURE_COMPOSER_VERSION == "1.0.0"

    def test_ten_composition_passes(self):
        assert len(COMPOSITION_PASSES) == 10

    def test_public_model_types_exist(self):
        for cls in (ProductionStructureCandidate, StructureSegment, JurisdictionSegment,
                    IncentiveClaim, TreatyComposition, StackComposition,
                    StructureConstraint, CompositionResult):
            assert cls is not None


# ── Single- / multi-jurisdiction composition ─────────────────────────────────

class TestJurisdictionComposition:
    def test_single_jurisdiction_baseline_candidate(self, result):
        mu = _mu_candidate(result)
        assert mu.participating_jurisdictions == ("MU",)
        assert mu.jurisdiction_segments[0].has_register is True
        assert mu.jurisdiction_segments[0].program_slug == "mu_edb_incentive"

    def test_multi_jurisdiction_candidates_from_discovered_partners(self, result, collection):
        # Invariant-based (not a hardcoded set, per the Worldwide
        # Jurisdiction Population phase's high-throughput testing
        # discipline): partners = exactly the union of relocation
        # candidates and comparable jurisdictions the discovery layer
        # itself found (collection fixture) — the composer must compose
        # what discovery discovered, no more, no less.
        pair_ids = {c.candidate_id for c in result.candidates if len(c.participating_jurisdictions) == 2}
        partner_codes = {
            o.jurisdiction_codes[1] for o in collection.opportunities
            if o.subtype in ("relocation_candidate", "comparable_jurisdiction")
        }
        expected = {f"PSC-MU-{code}" for code in partner_codes}
        assert pair_ids == expected

    def test_extra_jurisdiction_sets_composable(self, collection, graph):
        res = compose_production_structures(
            collection, graph, extra_jurisdiction_sets=[("GR", "IT", "ES")],
        )
        assert any(c.candidate_id == "PSC-ES-GR-IT" for c in res.candidates)

    def test_no_combinatorial_enumeration(self, result):
        # Every candidate traces to baseline-alone, a discovered pair, or an
        # explicit caller request — no uninvited triples/quads appear.
        assert all(len(c.participating_jurisdictions) <= 2 for c in result.candidates)


# ── Treaty composition ────────────────────────────────────────────────────────

class TestTreatyComposition:
    def test_mu_pairs_have_no_invented_treaty(self, result):
        for c in result.candidates:
            if len(c.participating_jurisdictions) == 2:
                assert c.treaty_compositions == ()  # MU has no treaty with anyone — none fabricated
                assert any(k.kind == "treaty_absence" for k in c.constraints)

    def test_bilateral_treaty_attached_when_registered(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="FR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("FR", "BE")])
        fr_be = next(c for c in res.candidates if set(c.participating_jurisdictions) == {"FR", "BE"})
        slugs = {t.treaty_slug for t in fr_be.treaty_compositions}
        assert "fr-be-bilateral" in slugs
        bilateral = next(t for t in fr_be.treaty_compositions if t.treaty_slug == "fr-be-bilateral")
        assert bilateral.kind == "bilateral"
        assert bilateral.graph_ref == "treaty:fr-be-bilateral"

    def test_convention_composition_when_no_bilateral(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="GR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("GR", "IT")])
        gr_it = next(c for c in res.candidates if c.candidate_id == "PSC-GR-IT")
        conventions = [t for t in gr_it.treaty_compositions if t.treaty_slug == "european_convention"]
        assert len(conventions) == 1
        assert conventions[0].kind == "convention_composition"

    def test_repeated_convention_collapsed_across_triple(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="GR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("GR", "IT", "ES")])
        triple = next(c for c in res.candidates if c.candidate_id == "PSC-ES-GR-IT")
        conventions = [t for t in triple.treaty_compositions if t.treaty_slug == "european_convention"]
        assert len(conventions) == 1
        assert conventions[0].jurisdiction_codes == ("ES", "GR", "IT")


# ── Stack composition ─────────────────────────────────────────────────────────

class TestStackComposition:
    def test_stacking_unknown_becomes_constraint_not_stack(self, result):
        mu = _mu_candidate(result)
        assert mu.stack_compositions == ()  # no STACKS_WITH evidence exists today
        stack_constraints = [c for c in mu.constraints if c.kind == "stacking_unknown"]
        assert len(stack_constraints) == 1  # MU program's unknown stacking rule
        assert stack_constraints[0].acquisition_task_refs  # routed to LAAE, not assumed

    def test_known_stack_composes_when_evidence_exists(self, graph):
        a = Opportunity(
            opportunity_id="OPP-A", opportunity_type=OpportunityType.STRUCTURING, subtype="s",
            description="a", jurisdiction_codes=("MU",), affected_accounts=("21-00",),
            graph_refs=("lever:A",),
        )
        b = Opportunity(
            opportunity_id="OPP-B", opportunity_type=OpportunityType.STRUCTURING, subtype="s",
            description="b", jurisdiction_codes=("MU",), affected_accounts=("21-00",),
            graph_refs=("lever:B",),
        )
        known = Opportunity(
            opportunity_id="OPP-STACK", opportunity_type=OpportunityType.STACKING,
            subtype="known_stack", description="k", jurisdiction_codes=("MU",),
            graph_refs=("lever:A", "lever:B"), graph_rule_id="RULE-STACK",
        )
        collection = OpportunityCollection(
            baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b, known],
        )
        res = compose_production_structures(collection, graph)
        mu = next(c for c in res.candidates if c.candidate_id == "PSC-MU")
        assert len(mu.stack_compositions) == 1
        assert mu.stack_compositions[0].graph_rule_id == "RULE-STACK"
        # And the STACKS_WITH evidence allowed both claims on 21-00 to book.
        assert {"OPP-A", "OPP-B"}.issubset(set(mu.included_opportunity_ids))


# ── Fund composition ──────────────────────────────────────────────────────────

class TestFundComposition:
    def test_eurimages_fund_requires_three_member_countries(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="GR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(
            collection, graph, extra_jurisdiction_sets=[("GR", "IT"), ("GR", "IT", "ES")],
        )
        pair = next(c for c in res.candidates if c.candidate_id == "PSC-GR-IT")
        triple = next(c for c in res.candidates if c.candidate_id == "PSC-ES-GR-IT")
        assert pair.fund_graph_refs == ()          # 2 < min_coproducer_countries (3)
        assert triple.fund_graph_refs == ("fund:eu_eurimages",)

    def test_no_fund_when_any_participant_is_non_member(self, result):
        for c in result.candidates:  # every candidate includes MU, a non-member
            assert c.fund_graph_refs == ()

    def test_fund_refs_resolve_in_graph(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="GR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("GR", "IT", "ES")])
        triple = next(c for c in res.candidates if c.candidate_id == "PSC-ES-GR-IT")
        for ref in triple.fund_graph_refs:
            assert graph.has_node(ref)


# ── Dependency / approval / authority preservation ───────────────────────────

class TestConstraintPreservation:
    def test_dependency_preserved(self, graph):
        # Retargeted twice now (Executable Jurisdiction Model Completion
        # phase — see docs/architecture/CAPABILITY_LEDGER.md's jurisdiction
        # population log). Originally MU-ES: broken when Spain's Art. 36.2
        # rate was corrected from an unverified 30%/50% to the confirmed
        # 25% marginal rate, dropping it below MU's 40% ceiling. Then
        # FR-BE: broken AGAIN when France's own TRIP rate was corrected
        # from an unverified flat 30% to the confirmed 30%/40%-VFX-ceiling
        # band (cnc.fr), which closed FR's materiality gap against BE's
        # own 40% ceiling. DE-MT is used now specifically because DE's
        # profile is still DISCOVERY-tier and untouched by this phase's
        # corrections so far — if DE is corrected in a future jurisdiction
        # pass and this breaks a third time, that is expected and should
        # be fixed the same way, not treated as a regression.
        collection = discover_all_opportunities(baseline_jurisdiction="DE", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("DE", "MT")])
        de_mt = next(c for c in res.candidates if c.candidate_id == "PSC-DE-MT")
        assert "OPP-JUR-RELOCATE-DE-MT" in de_mt.included_opportunity_ids
        assert "OPP-NORM-LABOR-DE-MT" in de_mt.included_opportunity_ids
        # In the baseline-only candidate the dependency cannot resolve, and the
        # dependent is excluded with the reason recorded — never silently included.
        de = next(c for c in res.candidates if c.candidate_id == "PSC-DE")
        assert "OPP-NORM-LABOR-DE-MT" not in de.included_opportunity_ids

    def test_approval_requirements_preserved(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="FR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("FR", "BE")])
        fr_be = next(c for c in res.candidates if set(c.participating_jurisdictions) == {"FR", "BE"})
        assert any("Competent authority" in a for a in fr_be.required_approvals)
        assert any(c.kind == "approval" for c in fr_be.constraints)

    def test_authority_absence_preserved_as_constraint(self, result):
        mu = _mu_candidate(result)
        authority_constraints = [c for c in mu.constraints if c.kind == "authority"]
        assert authority_constraints  # grey areas / unknowns carry score 0.0 termini
        for c in authority_constraints:
            assert c.opportunity_id is not None

    def test_acquisition_task_refs_aggregated(self, result):
        mu = _mu_candidate(result)
        assert "TASK-GA-LEGAL-ACCOUNTING-SPLIT" in mu.required_acquisition_task_refs
        assert "TASK-reinvestment:MU" in mu.required_acquisition_task_refs

    def test_grey_areas_and_evidence_refs_exposed(self, result):
        mu = _mu_candidate(result)
        assert set(mu.grey_area_opportunity_ids) == {"OPP-GREY-GA-LEGAL-ACCOUNTING-SPLIT", "OPP-GREY-GA-INKIND-FMV"}
        assert "ABS-LEGAL-ACCOUNTING-SPLIT" in mu.evidence_graph_refs
        assert "ABS-INKIND-FMV" in mu.evidence_graph_refs


# ── Duplicate elimination ─────────────────────────────────────────────────────

class TestDuplicateElimination:
    def test_identical_structures_deduplicated(self, collection, graph, register, grey_areas):
        # Supplying the baseline set again explicitly must not yield two
        # identical candidates.
        res = compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas, extra_jurisdiction_sets=[("MU",)],
        )
        mu_candidates = [c for c in res.candidates if c.participating_jurisdictions == ("MU",)]
        assert len(mu_candidates) == 1

    def test_eliminate_duplicates_records_reason(self):
        a = _priced_candidate("PSC-A", {c: 100.0 for c in RiskCase})
        b = _priced_candidate("PSC-A2", {c: 100.0 for c in RiskCase})
        survivors, pruned = eliminate_duplicates([a, b])
        assert len(survivors) == 1
        assert "Duplicate of 'PSC-A'" in pruned["PSC-A2"]


# ── Dominance pruning ─────────────────────────────────────────────────────────

class TestDominancePruning:
    def test_strictly_dominated_candidate_pruned(self):
        better = _priced_candidate("PSC-BETTER", {c: 1_000.0 for c in RiskCase})
        worse = _priced_candidate("PSC-WORSE", {c: 2_000.0 for c in RiskCase})
        survivors, pruned = prune_dominated([better, worse])
        assert [c.candidate_id for c in survivors] == ["PSC-BETTER"]
        assert "Strictly dominated by 'PSC-BETTER'" in pruned["PSC-WORSE"]

    def test_equal_in_one_case_defeats_dominance(self):
        a = _priced_candidate("PSC-A", {
            RiskCase.CONSERVATIVE: 1_000.0, RiskCase.BASE: 1_000.0,
            RiskCase.OPTIMISTIC: 1_000.0, RiskCase.RISK_ADJUSTED: 1_500.0,
        })
        b = _priced_candidate("PSC-B", {
            RiskCase.CONSERVATIVE: 2_000.0, RiskCase.BASE: 2_000.0,
            RiskCase.OPTIMISTIC: 2_000.0, RiskCase.RISK_ADJUSTED: 1_500.0,  # ties on RA
        })
        survivors, pruned = prune_dominated([a, b])
        assert len(survivors) == 2  # tie in any case ⇒ both survive
        assert pruned == {}

    def test_unpriced_candidates_never_pruned_by_dominance(self, result, collection):
        # Real data: pairs are partially priced (0.5), so none can be
        # dominance-compared, and none may vanish. Invariant-based count:
        # baseline + one pair per discovered relocation/comparable partner
        # (see test_multi_jurisdiction_candidates_from_discovered_partners).
        assert not result.pruned
        partner_codes = {
            o.jurisdiction_codes[1] for o in collection.opportunities
            if o.subtype in ("relocation_candidate", "comparable_jurisdiction")
        }
        assert len(result.candidates) == 1 + len(partner_codes)

    def test_partially_priced_never_dominates_or_is_dominated(self):
        priced = _priced_candidate("PSC-PRICED", {c: 1.0 for c in RiskCase})
        partial = _priced_candidate("PSC-PARTIAL", {c: 99_999.0 for c in RiskCase})
        partial.priceable_pct = 0.5  # cases exist but structure is partially priced
        survivors, pruned = prune_dominated([priced, partial])
        assert len(survivors) == 2
        assert pruned == {}


# ── Double counting / claims ─────────────────────────────────────────────────

class TestNoDoubleCounting:
    def test_each_account_claimed_once(self, result):
        mu = _mu_candidate(result)
        keys = [c.claim_key for c in mu.incentive_claims]
        assert len(keys) == len(set(keys))

    def test_claims_carry_program_slug(self, result):
        mu = _mu_candidate(result)
        for claim in mu.incentive_claims:
            assert claim.program_slug == "mu_edb_incentive"

    def test_conflicting_synthetic_claims_blocked(self, graph):
        a = Opportunity(
            opportunity_id="OPP-A", opportunity_type=OpportunityType.STRUCTURING, subtype="s",
            description="a", jurisdiction_codes=("MU",), affected_accounts=("21-00",),
        )
        b = Opportunity(
            opportunity_id="OPP-B", opportunity_type=OpportunityType.STRUCTURING, subtype="s",
            description="b", jurisdiction_codes=("MU",), affected_accounts=("21-00",),
        )
        collection = OpportunityCollection(baseline_jurisdiction="MU", passes_run=(), opportunities=[a, b])
        res = compose_production_structures(collection, graph)
        mu = next(c for c in res.candidates if c.candidate_id == "PSC-MU")
        booked = set(mu.included_opportunity_ids) & {"OPP-A", "OPP-B"}
        assert len(booked) == 1
        excluded = ({"OPP-A", "OPP-B"} - booked).pop()
        assert "Claim conflict" in mu.exclusion_reasons[excluded]


# ── Graph traceability ────────────────────────────────────────────────────────

class TestGraphTraceability:
    def test_jurisdiction_segments_resolve_in_graph(self, result, graph):
        for c in result.candidates:
            for seg in c.jurisdiction_segments:
                assert graph.has_node(seg.country_graph_ref)
                assert graph.has_node(seg.program_graph_ref)

    def test_treaty_refs_resolve_in_graph(self, graph):
        collection = discover_all_opportunities(baseline_jurisdiction="FR", mu_rate=MU_RATE, graph=graph)
        res = compose_production_structures(collection, graph, extra_jurisdiction_sets=[("FR", "BE")])
        for c in res.candidates:
            for t in c.treaty_compositions:
                assert graph.has_node(t.graph_ref)


# ── Sparse data / partial priceability ────────────────────────────────────────

class TestPartialPriceability:
    def test_baseline_fully_priceable(self, result):
        mu = _mu_candidate(result)
        assert mu.priceable_pct == 1.0
        assert mu.is_fully_priced

    def test_pair_half_priceable(self, result):
        pair = next(c for c in result.candidates if c.candidate_id == "PSC-MU-GR")
        assert pair.priceable_pct == 0.5
        assert not pair.is_fully_priced
        assert pair.cases is not None  # the MU portion is still priced

    def test_unknown_pct_reflects_evidence_gated_share(self, result):
        mu = _mu_candidate(result)
        assert 0.0 < mu.unknown_pct < 1.0

    def test_no_pricing_inputs_means_no_cases_not_invented_ones(self, collection, graph):
        res = compose_production_structures(collection, graph)  # no register/budget/rate
        for c in res.candidates:
            assert c.cases is None
            assert c.priceable_pct == 0.0


# ── Optimizer compatibility / four cases ──────────────────────────────────────

class TestOptimizerCompatibility:
    def test_all_four_cases_present_when_priced(self, result):
        mu = _mu_candidate(result)
        assert set(mu.cases.keys()) == {
            RiskCase.CONSERVATIVE, RiskCase.BASE, RiskCase.OPTIMISTIC, RiskCase.RISK_ADJUSTED,
        }

    def test_little_utopia_conservative_unchanged(self, result):
        mu = _mu_candidate(result)
        cons = mu.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_104_357.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_241_742.8, abs=1.0)

    def test_composer_does_not_import_private_optimizer_names(self):
        import ast
        import inspect
        import app.calculators.production_structure_composer as psc

        tree = ast.parse(inspect.getsource(psc))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "app.calculators.optimization_engine":
                assert all(not alias.name.startswith("_") for alias in node.names)


# ── Determinism / non-mutation ────────────────────────────────────────────────

class TestDeterminismAndNonMutation:
    def test_repeated_composition_identical(self, collection, graph, register, grey_areas):
        r1 = compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas,
        )
        r2 = compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas,
        )
        assert [c.candidate_id for c in r1.candidates] == [c.candidate_id for c in r2.candidates]
        assert [c.included_opportunity_ids for c in r1.candidates] == [c.included_opportunity_ids for c in r2.candidates]
        assert [c.npc(RiskCase.RISK_ADJUSTED) for c in r1.candidates] == [c.npc(RiskCase.RISK_ADJUSTED) for c in r2.candidates]

    def test_no_mutation_of_collection(self, collection, graph, register, grey_areas):
        before = [o.opportunity_id for o in collection.opportunities]
        compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas,
        )
        assert [o.opportunity_id for o in collection.opportunities] == before

    def test_no_mutation_of_graph(self, collection, graph, register, grey_areas):
        nodes, rels = len(graph.nodes), len(graph.relationships)
        compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas,
        )
        assert (len(graph.nodes), len(graph.relationships)) == (nodes, rels)

    def test_no_mutation_of_register_or_grey_areas(self, collection, graph, register, grey_areas):
        reg_snapshot = copy.deepcopy(register)
        grey_snapshot = copy.deepcopy(grey_areas)
        compose_production_structures(
            collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
            rate=MU_RATE, grey_areas=grey_areas,
        )
        assert register == reg_snapshot
        assert grey_areas == grey_snapshot
