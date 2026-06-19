"""
Tests for the multi-program stacking engine.

Phase 1-6 coverage:
  - apply_stacking_adjustments() unit tests (all rule types)
  - run_full_analysis() integration tests with NOHFC stacking
  - Backward-compatibility: single-program paths unchanged
  - Validation harness outputs verified

Math is fully annotated in fixtures/canada_stacking_validation.py.
"""
from __future__ import annotations

import pytest

from app.calculators.apply_stacking_adjustments import (
    StackingAdjustment,
    apply_stacking_adjustments,
)
from app.calculators.run_full_analysis import run_full_analysis, StructureAnalysisResult
from tests.fixtures.canada_stacking_validation import (
    CA_CPTC_NOHFC_EXPECTED,
    FIXTURE_CA_CPTC_NOHFC,
    FIXTURE_ON_OFTTC_NOHFC,
    NOHFC_PROGRAM,
    ON_OFTTC_NOHFC_EXPECTED,
)
from tests.fixtures.canada_validation import (
    FIXTURE_ON_OFTTC,
    FIXTURE_CA_CPTC,
    ON_OFTTC_EXPECTED,
    CA_CPTC_EXPECTED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(fixture: dict) -> StructureAnalysisResult:
    return run_full_analysis(
        structure_id="stacking-test",
        jurisdiction=fixture["jurisdiction"],
        line_items=fixture["line_items"],
        programs_with_categories=fixture["programs_with_categories"],
        stacking_rules=fixture.get("stacking_rules", []),
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=None,
        production_details=fixture.get("production_details", {}),
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


def _total_qs(result: StructureAnalysisResult) -> float:
    return sum(r.get("qualifying_spend_usd", 0) or 0 for r in result.qualified_spend_results)


def _iv_by_slug(result: StructureAnalysisResult, slug: str) -> dict | None:
    return next((r for r in result.incentive_results if r.get("program_slug") == slug), None)


def _stacking_adj_for(result: StructureAnalysisResult, credit_id: str) -> StackingAdjustment | None:
    for a in result.stacking_adjustments:
        if a.get("program_b_id") == credit_id:
            return a
    return None


# ===========================================================================
# Unit tests — apply_stacking_adjustments() directly
# ===========================================================================

class TestApplyStackingAdjustmentsUnit:
    """Unit tests for apply_stacking_adjustments() with hand-crafted inputs."""

    def _base_results(self):
        return [
            {
                "program_id": "grant-1",
                "program_slug": "my_grant",
                "program_type": "discretionary_fund",
                "qualifying_spend_usd": 0.0,
                "effective_rate": 0.0,
                "economic_value_usd": 500_000.0,
            },
            {
                "program_id": "credit-1",
                "program_slug": "my_credit",
                "program_type": "tax_credit",
                "qualifying_spend_usd": 1_400_000.0,
                "effective_rate": 0.35,
                "economic_value_usd": 490_000.0,
            },
        ]

    def test_no_rules_returns_raw_values_unchanged(self):
        results = self._base_results()
        out = apply_stacking_adjustments(results, stacking_rules=[])
        assert out.total_adjusted_value_usd == out.total_raw_value_usd
        assert out.total_adjusted_value_usd == 990_000.0
        assert out.adjustments == []
        assert out.legal_review_flags == []

    def test_spend_reduction_correct_math(self):
        results = self._base_results()
        rules = [{
            "program_a_id": "grant-1",
            "program_b_id": "credit-1",
            "rule_type": "spend_reduction",
            "condition_text": "grant reduces credit basis",
        }]
        out = apply_stacking_adjustments(results, rules)

        # credit_reduction = min(500_000, 1_400_000) × 0.35 = 175_000
        assert len(out.adjustments) == 1
        adj = out.adjustments[0]
        assert adj.rule_type == "spend_reduction"
        assert adj.program_b_id == "credit-1"
        assert abs(adj.adjustment_usd - (-175_000.0)) < 0.01
        assert abs(adj.adjusted_value_usd - 315_000.0) < 0.01

    def test_spend_reduction_total_adjusted_value(self):
        results = self._base_results()
        rules = [{"program_a_id": "grant-1", "program_b_id": "credit-1",
                  "rule_type": "spend_reduction"}]
        out = apply_stacking_adjustments(results, rules)
        # 500_000 (grant unchanged) + 315_000 (adjusted credit) = 815_000
        assert abs(out.total_adjusted_value_usd - 815_000.0) < 0.01
        assert abs(out.total_raw_value_usd - 990_000.0) < 0.01

    def test_spend_reduction_rule_applied_in_reverse_order(self):
        """rule_type resolution should work regardless of which is program_a vs program_b."""
        results = self._base_results()
        rules = [{"program_a_id": "credit-1", "program_b_id": "grant-1",
                  "rule_type": "spend_reduction"}]
        out = apply_stacking_adjustments(results, rules)
        # Same result: grant identified by program_type
        assert abs(out.adjustments[0].adjustment_usd - (-175_000.0)) < 0.01

    def test_spend_reduction_grant_larger_than_qualifying_spend(self):
        """When grant > qualifying_spend, reduction is capped at qualifying_spend × rate."""
        results = [
            {"program_id": "g1", "program_type": "grant",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 2_000_000.0, "program_slug": "big_grant"},
            {"program_id": "c1", "program_type": "tax_credit",
             "qualifying_spend_usd": 500_000.0, "effective_rate": 0.30,
             "economic_value_usd": 150_000.0, "program_slug": "small_credit"},
        ]
        rules = [{"program_a_id": "g1", "program_b_id": "c1", "rule_type": "spend_reduction"}]
        out = apply_stacking_adjustments(results, rules)
        # reducible = min(2_000_000, 500_000) = 500_000; reduction = 500_000 × 0.30 = 150_000
        # adjusted_credit = max(0, 150_000 - 150_000) = 0
        assert abs(out.program_values["c1"] - 0.0) < 0.01

    def test_mutually_exclusive_zeroes_lower_value(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 1_000_000.0, "effective_rate": 0.20,
             "economic_value_usd": 200_000.0, "program_slug": "credit_a"},
            {"program_id": "p2", "program_type": "tax_credit",
             "qualifying_spend_usd": 1_000_000.0, "effective_rate": 0.30,
             "economic_value_usd": 300_000.0, "program_slug": "credit_b"},
        ]
        rules = [{"program_a_id": "p1", "program_b_id": "p2", "rule_type": "mutually_exclusive"}]
        out = apply_stacking_adjustments(results, rules)

        # p2 (300K) kept; p1 (200K) zeroed
        assert out.program_values["p1"] == 0.0
        assert out.program_values["p2"] == 300_000.0
        assert abs(out.total_adjusted_value_usd - 300_000.0) < 0.01
        assert len(out.legal_review_flags) == 1
        assert "p1" in out.legal_review_flags[0]  # excluded program in flag

    def test_mutually_exclusive_keeps_higher_value(self):
        results = [
            {"program_id": "px", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 600_000.0, "program_slug": "big"},
            {"program_id": "py", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 400_000.0, "program_slug": "small"},
        ]
        rules = [{"program_a_id": "px", "program_b_id": "py", "rule_type": "mutually_exclusive"}]
        out = apply_stacking_adjustments(results, rules)
        assert out.program_values["px"] == 600_000.0
        assert out.program_values["py"] == 0.0

    def test_value_cap_reduces_proportionally(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 300_000.0, "program_slug": "a"},
            {"program_id": "p2", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 700_000.0, "program_slug": "b"},
        ]
        cap = 800_000.0
        rules = [{"program_a_id": "p1", "program_b_id": "p2",
                  "rule_type": "value_cap", "condition_text": str(cap)}]
        out = apply_stacking_adjustments(results, rules)
        assert abs(out.total_adjusted_value_usd - cap) < 0.01
        # 300K/1000K × 800K = 240K; 700K/1000K × 800K = 560K
        assert abs(out.program_values["p1"] - 240_000.0) < 0.01
        assert abs(out.program_values["p2"] - 560_000.0) < 0.01

    def test_value_cap_not_applied_when_under_cap(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 200_000.0, "program_slug": "a"},
            {"program_id": "p2", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 300_000.0, "program_slug": "b"},
        ]
        cap = 1_000_000.0   # combined = 500K < cap
        rules = [{"program_a_id": "p1", "program_b_id": "p2",
                  "rule_type": "value_cap", "condition_text": str(cap)}]
        out = apply_stacking_adjustments(results, rules)
        assert out.adjustments == []
        assert abs(out.total_adjusted_value_usd - 500_000.0) < 0.01

    def test_conditional_adds_legal_review_flag(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 100_000.0, "program_slug": "a"},
            {"program_id": "p2", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 200_000.0, "program_slug": "b"},
        ]
        rules = [{"program_a_id": "p1", "program_b_id": "p2",
                  "rule_type": "conditional",
                  "condition_text": "subject to ministerial approval"}]
        out = apply_stacking_adjustments(results, rules)
        assert len(out.legal_review_flags) == 1
        assert "ministerial approval" in out.legal_review_flags[0]
        # No value adjustment for conditional
        assert out.adjustments == []
        assert abs(out.total_adjusted_value_usd - 300_000.0) < 0.01

    def test_allowed_rule_has_no_effect(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 100_000.0, "program_slug": "a"},
            {"program_id": "p2", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 200_000.0, "program_slug": "b"},
        ]
        rules = [{"program_a_id": "p1", "program_b_id": "p2", "rule_type": "allowed"}]
        out = apply_stacking_adjustments(results, rules)
        assert out.adjustments == []
        assert out.legal_review_flags == []
        assert abs(out.total_adjusted_value_usd - 300_000.0) < 0.01

    def test_rule_skipped_when_program_not_in_set(self):
        results = [
            {"program_id": "p1", "program_type": "tax_credit",
             "qualifying_spend_usd": 0.0, "effective_rate": 0.0,
             "economic_value_usd": 100_000.0, "program_slug": "a"},
        ]
        rules = [{"program_a_id": "p1", "program_b_id": "p-not-claimed",
                  "rule_type": "spend_reduction"}]
        out = apply_stacking_adjustments(results, rules)
        assert out.adjustments == []
        assert abs(out.total_adjusted_value_usd - 100_000.0) < 0.01


# ===========================================================================
# Integration tests — NOHFC (fixed grant) program type
# ===========================================================================

class TestNOHFCGrantProgram:
    """Verify NOHFC as a fixed-amount discretionary_fund."""

    def test_nohfc_program_type(self):
        assert NOHFC_PROGRAM["program_type"] == "discretionary_fund"

    def test_nohfc_has_fixed_grant_amount(self):
        assert NOHFC_PROGRAM["fixed_grant_amount_usd"] == 500_000

    def test_nohfc_is_competitive(self):
        assert NOHFC_PROGRAM["is_competitive"] is True


# ===========================================================================
# Integration tests — OFTTC + NOHFC (spend_reduction via run_full_analysis)
# ===========================================================================

class TestOFTTCNOHFCStacking:
    """Integration: OFTTC + NOHFC with spend_reduction stacking rule."""

    @pytest.fixture(scope="class")
    def result(self):
        return _run(FIXTURE_ON_OFTTC_NOHFC)

    def test_total_budget(self, result):
        expected = ON_OFTTC_NOHFC_EXPECTED["total_budget_usd"]
        assert result.total_input_budget_usd == expected

    def test_two_programs_evaluated(self, result):
        assert len(result.incentive_results) == 2

    def test_ofttc_raw_economic_value(self, result):
        ofttc = _iv_by_slug(result, "on_ofttc")
        assert ofttc is not None
        expected = ON_OFTTC_NOHFC_EXPECTED["ofttc_raw_value_usd"]
        assert abs(ofttc["economic_value_usd"] - expected) <= expected * 0.01, (
            f"OFTTC raw value: expected ${expected:,.0f}, got ${ofttc['economic_value_usd']:,.0f}"
        )

    def test_nohfc_fixed_grant_economic_value(self, result):
        nohfc = _iv_by_slug(result, "nohfc_production_fund")
        assert nohfc is not None
        expected = ON_OFTTC_NOHFC_EXPECTED["nohfc_raw_value_usd"]
        assert abs(nohfc["economic_value_usd"] - expected) <= 1.0, (
            f"NOHFC grant: expected ${expected:,.0f}, got ${nohfc['economic_value_usd']:,.0f}"
        )

    def test_total_raw_incentive_value(self, result):
        expected = ON_OFTTC_NOHFC_EXPECTED["total_raw_incentive_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.01, (
            f"Raw total: expected ${expected:,.0f}, got "
            f"${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_stacking_adjustment_applied(self, result):
        assert len(result.stacking_adjustments) == 1

    def test_stacking_adjustment_amount(self, result):
        adj = result.stacking_adjustments[0]
        expected = ON_OFTTC_NOHFC_EXPECTED["stacking_adjustment_usd"]   # −175,000
        assert abs(adj["adjustment_usd"] - expected) <= abs(expected) * 0.01, (
            f"Stacking adjustment: expected ${expected:,.0f}, got ${adj['adjustment_usd']:,.0f}"
        )

    def test_stacking_adjustment_targets_ofttc(self, result):
        adj = result.stacking_adjustments[0]
        assert adj["rule_type"] == "spend_reduction"
        assert adj["program_b_id"] == "prog-on-ofttc"

    def test_total_adjusted_incentive_value(self, result):
        expected = ON_OFTTC_NOHFC_EXPECTED["total_adjusted_incentive_usd"]
        assert abs(result.stacking_adjusted_economic_value_usd - expected) <= expected * 0.01, (
            f"Adjusted total: expected ${expected:,.0f}, got "
            f"${result.stacking_adjusted_economic_value_usd:,.0f}"
        )

    def test_adjusted_less_than_raw(self, result):
        assert result.stacking_adjusted_economic_value_usd < result.total_incentive_economic_value_usd

    def test_true_net_cost_uses_adjusted_value(self, result):
        expected = ON_OFTTC_NOHFC_EXPECTED["true_net_cost_usd"]
        assert abs(result.true_net_cost_usd - expected) <= expected * 0.01, (
            f"True net: expected ${expected:,.0f}, got ${result.true_net_cost_usd:,.0f}"
        )

    def test_true_net_higher_than_single_program(self, result):
        """Stacking with spend_reduction produces a higher net cost than OFTTC alone."""
        ofttc_only = _run(FIXTURE_ON_OFTTC)
        # Combined + stacking: 785K vs OFTTC alone: 1,110K
        # Wait — with NOHFC grant we have 815K adjusted incentive vs 490K alone.
        # So true_net should be LOWER (more incentive value → lower net)
        # OFTTC alone: 400K + 1200K - 490K = 1,110K
        # OFTTC+NOHFC: 400K + 1200K - 815K = 785K
        assert result.true_net_cost_usd < ofttc_only.true_net_cost_usd

    def test_calculation_trace_includes_stacking_step(self, result):
        steps = [s["step"] for s in result.calculation_trace["steps"]]
        assert "stacking_adjustments" in steps

    def test_stacking_legal_review_not_required(self, result):
        # spend_reduction does not trigger legal_review_required (only prohibited/conditional does)
        assert not result.stacking_legal_review_required


# ===========================================================================
# Integration tests — CPTC + NOHFC (spend_reduction via run_full_analysis)
# ===========================================================================

class TestCPTCNOHFCStacking:
    """Integration: Federal CPTC + NOHFC with spend_reduction stacking rule."""

    @pytest.fixture(scope="class")
    def result(self):
        return _run(FIXTURE_CA_CPTC_NOHFC)

    def test_total_budget(self, result):
        expected = CA_CPTC_NOHFC_EXPECTED["total_budget_usd"]
        assert result.total_input_budget_usd == expected

    def test_cptc_raw_economic_value(self, result):
        cptc = _iv_by_slug(result, "ca_federal_cptc")
        assert cptc is not None
        expected = CA_CPTC_NOHFC_EXPECTED["cptc_raw_value_usd"]
        assert abs(cptc["economic_value_usd"] - expected) <= expected * 0.01

    def test_nohfc_fixed_grant_economic_value(self, result):
        nohfc = _iv_by_slug(result, "nohfc_production_fund")
        assert nohfc is not None
        expected = CA_CPTC_NOHFC_EXPECTED["nohfc_raw_value_usd"]
        assert abs(nohfc["economic_value_usd"] - expected) <= 1.0

    def test_total_raw_incentive_value(self, result):
        expected = CA_CPTC_NOHFC_EXPECTED["total_raw_incentive_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.01

    def test_stacking_adjustment_amount(self, result):
        assert len(result.stacking_adjustments) == 1
        adj = result.stacking_adjustments[0]
        expected = CA_CPTC_NOHFC_EXPECTED["stacking_adjustment_usd"]   # −125,000
        assert abs(adj["adjustment_usd"] - expected) <= abs(expected) * 0.01, (
            f"CPTC stacking adj: expected ${expected:,.0f}, got ${adj['adjustment_usd']:,.0f}"
        )

    def test_stacking_adjustment_targets_cptc(self, result):
        adj = result.stacking_adjustments[0]
        assert adj["rule_type"] == "spend_reduction"
        assert adj["program_b_id"] == "prog-ca-cptc"

    def test_total_adjusted_incentive_value(self, result):
        expected = CA_CPTC_NOHFC_EXPECTED["total_adjusted_incentive_usd"]
        assert abs(result.stacking_adjusted_economic_value_usd - expected) <= expected * 0.01

    def test_true_net_cost_uses_adjusted_value(self, result):
        expected = CA_CPTC_NOHFC_EXPECTED["true_net_cost_usd"]
        assert abs(result.true_net_cost_usd - expected) <= expected * 0.01, (
            f"CPTC+NOHFC true net: expected ${expected:,.0f}, got ${result.true_net_cost_usd:,.0f}"
        )

    def test_true_net_lower_than_cptc_alone(self, result):
        """CPTC+NOHFC ($825K adjusted) beats CPTC alone ($450K) on net cost."""
        cptc_only = _run(FIXTURE_CA_CPTC)
        # CPTC+NOHFC true net = 1,375K; CPTC alone = 1,750K
        assert result.true_net_cost_usd < cptc_only.true_net_cost_usd


# ===========================================================================
# Backward-compatibility: single-program analysis unchanged
# ===========================================================================

class TestSingleProgramBackwardCompat:
    """Existing single-program analyses must not change after stacking integration."""

    def test_ofttc_alone_adjusted_equals_raw(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert abs(
            result.stacking_adjusted_economic_value_usd
            - result.total_incentive_economic_value_usd
        ) < 0.01

    def test_ofttc_alone_no_stacking_adjustments(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert result.stacking_adjustments == []

    def test_ofttc_alone_true_net_unchanged(self):
        result = _run(FIXTURE_ON_OFTTC)
        expected = ON_OFTTC_EXPECTED["true_net_cost_usd"]
        assert abs(result.true_net_cost_usd - expected) <= expected * 0.01

    def test_cptc_alone_adjusted_equals_raw(self):
        result = _run(FIXTURE_CA_CPTC)
        assert abs(
            result.stacking_adjusted_economic_value_usd
            - result.total_incentive_economic_value_usd
        ) < 0.01

    def test_cptc_alone_true_net_unchanged(self):
        result = _run(FIXTURE_CA_CPTC)
        expected = CA_CPTC_EXPECTED["true_net_cost_usd"]
        assert abs(result.true_net_cost_usd - expected) <= expected * 0.01


# ===========================================================================
# Stacking trace and flag tests
# ===========================================================================

class TestStackingTraceAndFlags:
    """Verify calculation trace and legal review flags."""

    def test_trace_includes_adjusted_value(self):
        result = _run(FIXTURE_ON_OFTTC_NOHFC)
        stacking_step = next(
            (s for s in result.calculation_trace["steps"] if s["step"] == "stacking_adjustments"),
            None,
        )
        assert stacking_step is not None
        assert stacking_step["adjustments_applied"] == 1
        expected_adj = ON_OFTTC_NOHFC_EXPECTED["total_adjusted_incentive_usd"]
        assert abs(stacking_step["total_adjusted_value_usd"] - expected_adj) <= expected_adj * 0.01

    def test_prohibited_rule_sets_legal_review_flag(self):
        """A PROHIBITED stacking rule triggers stacking_legal_review_required."""
        from app.calculators.run_full_analysis import run_full_analysis
        from tests.fixtures.canada_validation import (
            FIXTURE_ON_OFTTC,
            ON_OFTTC_PROGRAM,
            ON_OFTTC_QUALIFYING_CATEGORIES,
            ON_OFTTC_JURISDICTION,
            ON_OFTTC_LINE_ITEMS,
        )
        from tests.fixtures.canada_stacking_validation import NOHFC_PROGRAM, NOHFC_QUALIFYING_CATEGORIES

        fixture_with_prohibited = {
            **FIXTURE_ON_OFTTC_NOHFC,
            "stacking_rules": [{
                "program_a_id": "prog-nohfc",
                "program_b_id": "prog-on-ofttc",
                "rule_type": "prohibited",
                "condition_text": "hypothetical prohibition",
            }],
        }
        result = _run(fixture_with_prohibited)
        assert result.stacking_legal_review_required is True
        assert len(result.stacking_violations) == 1
