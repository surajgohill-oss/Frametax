"""
test_production_constraint_engine.py

Targeted tests for Phase 7 closeout, Part E — the Production Constraint
Engine. Covers checkable vs. unverifiable constraint kinds, hard vs. soft
violation semantics, non-mutation of ProductionStructureCandidate
objects, determinism, and Little Utopia compatibility (real composed
candidates, no optimizer math touched).
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.opportunity_discovery import discover_all_opportunities
from app.calculators.optimization_engine import RiskCase
from app.calculators.production_structure_composer import compose_production_structures
from app.calculators.qualification_model import build_little_utopia_grey_areas, build_little_utopia_qualification_register

from app.calculators.production_constraint_engine import (
    PRODUCTION_CONSTRAINT_ENGINE_VERSION,
    ConstraintKind,
    ProductionConstraint,
    build_constraint_set,
    check_candidate_against_constraints,
    filter_candidates_by_constraints,
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
def composition_result(collection, graph, register, grey_areas):
    return compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )


@pytest.fixture()
def baseline_candidate(composition_result):
    return next(c for c in composition_result.candidates if c.participating_jurisdictions == ("MU",))


class TestConstraintSet:
    def test_build_constraint_set_sorts_deterministically(self):
        cs = build_constraint_set([
            ProductionConstraint(constraint_id="C2", kind=ConstraintKind.DIRECTOR_FIXED, value="Jane"),
            ProductionConstraint(constraint_id="C1", kind=ConstraintKind.WRITER_FIXED, value="John"),
        ])
        assert [c.constraint_id for c in cs.constraints] == ["C1", "C2"]

    def test_of_kind_filters(self):
        cs = build_constraint_set([
            ProductionConstraint(constraint_id="C1", kind=ConstraintKind.DIRECTOR_FIXED, value="Jane"),
            ProductionConstraint(constraint_id="C2", kind=ConstraintKind.WRITER_FIXED, value="John"),
        ])
        assert len(cs.of_kind(ConstraintKind.DIRECTOR_FIXED)) == 1

    def test_empty_constraint_set(self):
        cs = build_constraint_set()
        assert cs.constraints == ()

    def test_version_constant_present(self):
        assert PRODUCTION_CONSTRAINT_ENGINE_VERSION


class TestJurisdictionRequiredConstraint:
    def test_satisfied_constraint_is_compatible(self, baseline_candidate):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU")])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is True
        assert result.violated_constraint_ids == ()

    def test_violated_hard_constraint_reported(self, baseline_candidate):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="ZZ", hard=True)])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is False
        assert "C1" in result.violated_constraint_ids
        assert "C1" in result.reasons

    def test_violated_soft_constraint_does_not_block_compatibility(self, baseline_candidate):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="ZZ", hard=False)])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is True
        assert result.violated_constraint_ids == ()
        assert "C1" in result.reasons  # still recorded, just non-blocking

    def test_case_insensitive_jurisdiction_code(self, baseline_candidate):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="mu")])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is True


class TestBudgetCeilingConstraint:
    def test_within_ceiling_is_compatible(self, baseline_candidate):
        npc = baseline_candidate.npc(RiskCase.RISK_ADJUSTED)
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.BUDGET_CEILING, value=str(npc + 1_000_000))])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is True

    def test_exceeding_ceiling_violates(self, baseline_candidate):
        npc = baseline_candidate.npc(RiskCase.RISK_ADJUSTED)
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.BUDGET_CEILING, value=str(npc - 1))])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is False

    def test_unpriced_candidate_is_unverifiable_not_assumed_compliant(self, composition_result):
        unpriced = next((c for c in composition_result.candidates if not c.is_fully_priced), None)
        if unpriced is None:
            pytest.skip("no unpriced candidate in this composition result")
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.BUDGET_CEILING, value="1000000")])
        result = check_candidate_against_constraints(unpriced, cs)
        assert "C1" in result.unverifiable_constraint_ids
        assert result.compatible is True  # unverifiable is never treated as violated

    def test_malformed_value_is_unverifiable(self, baseline_candidate):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.BUDGET_CEILING, value="not-a-number")])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert "C1" in result.unverifiable_constraint_ids


class TestUnverifiableConstraintKinds:
    def test_unchecked_kinds_report_unverifiable_never_violated(self, baseline_candidate):
        cs = build_constraint_set([
            ProductionConstraint(constraint_id="C1", kind=ConstraintKind.DIRECTOR_FIXED, value="Jane"),
            ProductionConstraint(constraint_id="C2", kind=ConstraintKind.LOCAL_HIRE_REQUIRED, value="true"),
            ProductionConstraint(constraint_id="C3", kind=ConstraintKind.UNION_REQUIRED, value="true"),
        ])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert result.compatible is True
        assert set(result.unverifiable_constraint_ids) == {"C1", "C2", "C3"}
        assert result.violated_constraint_ids == ()

    def test_never_fabricates_a_check_it_cannot_perform(self, baseline_candidate):
        """Reason text must say it couldn't be checked, never assert
        compliance."""
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.REQUIRED_DISTRIBUTOR, value="Acme")])
        result = check_candidate_against_constraints(baseline_candidate, cs)
        assert "cannot be checked" in result.reasons["C1"]


class TestFilterCandidatesByConstraints:
    def test_returns_all_candidates_when_no_constraints_violated(self, composition_result):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU")])
        compatible, results = filter_candidates_by_constraints(composition_result.candidates, cs)
        assert len(compatible) == len(composition_result.candidates)
        assert len(results) == len(composition_result.candidates)

    def test_excludes_candidates_violating_hard_constraint(self, composition_result):
        non_mu_only_candidates = [c for c in composition_result.candidates if "ZZ" not in c.participating_jurisdictions]
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="ZZ", hard=True)])
        compatible, results = filter_candidates_by_constraints(composition_result.candidates, cs)
        assert compatible == []

    def test_does_not_mutate_candidates(self, composition_result):
        before = copy.deepcopy(composition_result.candidates)
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU")])
        filter_candidates_by_constraints(composition_result.candidates, cs)
        assert composition_result.candidates == before

    def test_preserves_original_order(self, composition_result):
        cs = build_constraint_set()
        compatible, _ = filter_candidates_by_constraints(composition_result.candidates, cs)
        assert [c.candidate_id for c in compatible] == [c.candidate_id for c in composition_result.candidates]

    def test_deterministic_across_runs(self, composition_result):
        cs = build_constraint_set([ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU")])
        c1, r1 = filter_candidates_by_constraints(composition_result.candidates, cs)
        c2, r2 = filter_candidates_by_constraints(composition_result.candidates, cs)
        assert [c.candidate_id for c in c1] == [c.candidate_id for c in c2]
        assert [r.compatible for r in r1] == [r.compatible for r in r2]


class TestOptimizerMathUntouched:
    def test_candidate_npc_unchanged_after_constraint_checks(self, baseline_candidate):
        """Constraint checking must be strictly read-only against
        pricing — this proves it never recomputes or perturbs NPC."""
        before = {case: baseline_candidate.npc(case) for case in RiskCase}
        cs = build_constraint_set([
            ProductionConstraint(constraint_id="C1", kind=ConstraintKind.BUDGET_CEILING, value="5000000"),
            ProductionConstraint(constraint_id="C2", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU"),
        ])
        check_candidate_against_constraints(baseline_candidate, cs)
        after = {case: baseline_candidate.npc(case) for case in RiskCase}
        assert before == after
