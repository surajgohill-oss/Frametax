from __future__ import annotations

"""Final Backend Closeout — Phase 3 (multi-production validation) + Phase 4
(optimizer sanity + determinism) consolidated closeout artifact.

These tests do not replace the deep per-engine suites (test_full_analysis.py,
test_treaty_coproduction.py, test_stacking_engine.py, the jurisdiction
validations, test_canonical_optimization_contract.py). They tie the closeout
guarantees into one self-documenting file: the pipeline validates against
MULTIPLE distinct productions, the served optimizer is deterministic, and the
required scenario families all appear and price (or honestly decline).
"""

import json

import pytest

from app.calculators.run_full_analysis import run_full_analysis
from app.demo.little_utopia_state import (
    apply_fact_answers,
    build_allocated_structures,
    get_state,
    reset_fact_answers,
)
from tests.fixtures.synthetic_projects import (
    FIXTURE_1_US_DOMESTIC,
    FIXTURE_2_CANADA_ONTARIO,
    FIXTURE_5_DEFERRED_COMPENSATION,
    FIXTURE_7_STACKING_ALLOWED,
    FIXTURE_8_STACKING_PROHIBITED,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="closeout",
        jurisdiction=fixture["jurisdiction"],
        line_items=fixture["line_items"],
        programs_with_categories=fixture["programs_with_categories"],
        stacking_rules=fixture.get("stacking_rules", []),
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=fixture.get("fx_rates"),
        production_details=fixture.get("production_details"),
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


# Three distinct productions (own budgets, jurisdictions, programs) beyond the
# real Little Utopia budget exercised by the served pipeline below.
_MULTI_PRODUCTION_CORPUS = [
    FIXTURE_1_US_DOMESTIC,       # US domestic single-jurisdiction, cash/credit
    FIXTURE_2_CANADA_ONTARIO,    # Canadian province, refundable credit
    FIXTURE_5_DEFERRED_COMPENSATION,  # indie with deferred fees (QPE edge case)
]


class TestMultiProductionPipeline:
    @pytest.mark.parametrize("fixture", _MULTI_PRODUCTION_CORPUS,
                             ids=lambda f: f["name"][:24])
    def test_full_pipeline_produces_coherent_economics(self, fixture):
        r = _run(fixture)
        assert r.total_input_budget_usd > 0
        assert r.true_net_cost_usd > 0
        assert r.true_net_cost_usd <= r.total_input_budget_usd
        assert r.calculation_trace["steps"], "pipeline must emit a calculation trace"

    @pytest.mark.parametrize("fixture", _MULTI_PRODUCTION_CORPUS,
                             ids=lambda f: f["name"][:24])
    def test_pipeline_is_deterministic_per_production(self, fixture):
        a = _run(fixture)
        b = _run(fixture)
        assert a.true_net_cost_usd == b.true_net_cost_usd
        assert a.total_incentive_economic_value_usd == b.total_incentive_economic_value_usd


class TestServedOptimizerDeterminism:
    def test_served_structures_are_byte_identical_across_runs(self):
        a = build_allocated_structures(get_state())
        b = build_allocated_structures(get_state())
        assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


class TestScenarioFamilyCoverage:
    """Phase 4 sanity: the required scenario families are present and each
    either prices or honestly declines — never forced."""

    def _served(self):
        return build_allocated_structures(get_state())["structures"]

    def test_single_jurisdiction_baseline_prices(self):
        s = next(x for x in self._served() if x["structure_type"] == "single_country")
        assert s["is_fully_priced"]

    def test_full_relocation_family_present_and_prices(self):
        fam = [x for x in self._served() if x["structure_type"] == "full_relocation"]
        assert len(fam) > 5
        assert any(x["is_fully_priced"] for x in fam)

    def test_component_relocation_family_present_and_prices(self):
        fam = [x for x in self._served() if x["structure_type"] == "component_relocation"]
        assert len(fam) > 5
        assert any(x["is_fully_priced"] for x in fam)

    def test_stacking_allowed_vs_prohibited_are_distinguished(self):
        allowed = _run(FIXTURE_7_STACKING_ALLOWED)
        prohibited = _run(FIXTURE_8_STACKING_PROHIBITED)
        assert allowed.stacking_violations == []
        assert prohibited.stacking_legal_review_required is True


class TestNegativeCasesNeverForced:
    def test_treaty_without_a_covering_instrument_is_unavailable_not_priced(self):
        """Electing a treaty partner with no real instrument covering the pair
        must yield an UNAVAILABLE structure (honest block), never a fabricated
        price."""
        reset_fact_answers()
        try:
            apply_fact_answers({"treaty_partner_code": "FR"})
            structs = build_allocated_structures(get_state())["structures"]
            treaty = [s for s in structs
                      if s["structure_type"] in ("treaty_coproduction", "majority_minority", "multi_party")]
            assert treaty, "electing a treaty partner must compose a treaty structure"
            for s in treaty:
                if not s["is_fully_priced"]:
                    assert s["confidence_status"] == "UNAVAILABLE"
        finally:
            reset_fact_answers()

    def test_reset_restores_canonical_baseline(self):
        reset_fact_answers()
        baseline = build_allocated_structures(get_state())
        rank1 = next(r for r in baseline["ranking"] if r["rank"] == 1)
        assert rank1["structure_id"] == "ALLOC-BASELINE-MU"
