"""
test_production_economics.py

Tests for the deterministic production economics calculator and contribution fixtures.
"""
from __future__ import annotations

import pytest

from app.calculators.production_economics import (
    ContributionInput,
    ProductionEconomicsResult,
    calculate_production_economics,
)
from tests.fixtures.contribution_fixtures import (
    ALL_FIXTURES,
    EXPECTED_CASH_BUDGET,
    EXPECTED_CONDITIONAL_EXPOSURE,
    EXPECTED_CONTRIBUTION_VALUE,
    EXPECTED_INCENTIVE_QUALIFYING,
    EXPECTED_REPLACEMENT_COST,
    EXPECTED_UNCERTAIN,
    FIXTURE_GROSS_BUDGET_USD,
    deferred_producer_fee,
    equipment_sponsorship,
    free_facility_use,
    government_grant,
    vendor_equity_post_deal,
)


# ---------------------------------------------------------------------------
# Fixture integrity
# ---------------------------------------------------------------------------

class TestFixtureIntegrity:
    def test_all_fixtures_length(self):
        assert len(ALL_FIXTURES) == 5

    def test_fixture_types(self):
        types = {c.contribution_type for c in ALL_FIXTURES}
        assert types == {"equity", "deferred", "government_support", "in_kind", "sponsorship"}

    def test_no_cash_contributions(self):
        cash = [c for c in ALL_FIXTURES if c.contribution_type == "cash"]
        assert cash == []

    def test_vendor_equity_fmv_less_than_amount(self):
        assert vendor_equity_post_deal.fair_market_value < vendor_equity_post_deal.amount

    def test_vendor_equity_is_conditional(self):
        assert vendor_equity_post_deal.is_conditional is True

    def test_deferred_fee_full_value(self):
        assert deferred_producer_fee.amount == deferred_producer_fee.fair_market_value

    def test_deferred_qualifies_for_incentive(self):
        assert deferred_producer_fee.qualifies_for_incentive is True

    def test_government_grant_is_conditional(self):
        assert government_grant.is_conditional is True

    def test_government_grant_does_not_qualify(self):
        assert government_grant.qualifies_for_incentive is False

    def test_free_facility_amount_zero(self):
        assert free_facility_use.amount == 0.0

    def test_free_facility_fmv_positive(self):
        assert free_facility_use.effective_fmv() == 45_000.0

    def test_free_facility_incentive_unknown(self):
        assert free_facility_use.qualifies_for_incentive is None

    def test_equipment_sponsorship_incentive_unknown(self):
        assert equipment_sponsorship.qualifies_for_incentive is None

    def test_equipment_sponsorship_no_jurisdiction(self):
        assert equipment_sponsorship.jurisdiction_code is None

    def test_expected_contribution_value_constant(self):
        assert EXPECTED_CONTRIBUTION_VALUE == 345_000.0

    def test_expected_replacement_cost_constant(self):
        assert EXPECTED_REPLACEMENT_COST == 405_000.0

    def test_expected_incentive_qualifying_constant(self):
        assert EXPECTED_INCENTIVE_QUALIFYING == 125_000.0

    def test_expected_uncertain_constant(self):
        assert EXPECTED_UNCERTAIN == 80_000.0

    def test_expected_conditional_constant(self):
        assert EXPECTED_CONDITIONAL_EXPOSURE == 140_000.0


# ---------------------------------------------------------------------------
# ContributionInput helpers
# ---------------------------------------------------------------------------

class TestContributionInputHelpers:
    def test_effective_fmv_uses_fair_market_value(self):
        c = ContributionInput("equity", "Test", 100.0, fair_market_value=60.0)
        assert c.effective_fmv() == 60.0

    def test_effective_fmv_falls_back_to_amount(self):
        c = ContributionInput("in_kind", "Test", 75.0)
        assert c.effective_fmv() == 75.0

    def test_effective_replacement_cost_explicit(self):
        c = ContributionInput("in_kind", "Test", 0.0, fair_market_value=50.0,
                              replacement_cost=55.0)
        assert c.effective_replacement_cost() == 55.0

    def test_effective_replacement_cost_falls_back_to_fmv(self):
        c = ContributionInput("in_kind", "Test", 0.0, fair_market_value=50.0)
        assert c.effective_replacement_cost() == 50.0

    def test_effective_replacement_cost_chain_fallback(self):
        # No FMV, no RC → falls back amount → FMV → RC
        c = ContributionInput("in_kind", "Test", 40.0)
        assert c.effective_replacement_cost() == 40.0


# ---------------------------------------------------------------------------
# Calculator — simple cases
# ---------------------------------------------------------------------------

class TestCalculatorSimple:
    def test_empty_contributions_zero_totals(self):
        result = calculate_production_economics([], gross_budget_usd=100_000.0)
        assert result.cash_budget == 0.0
        assert result.contribution_value == 0.0
        assert result.effective_production_value == 0.0
        assert result.replacement_cost_exposure == 0.0

    def test_empty_contributions_full_unfunded_gap(self):
        result = calculate_production_economics([], gross_budget_usd=100_000.0)
        assert result.unfunded_gap_usd == 100_000.0

    def test_zero_gross_budget_warns(self):
        result = calculate_production_economics([], gross_budget_usd=0.0)
        assert any("zero or negative" in w for w in result.warnings)
        assert result.cash_coverage_pct == 0.0
        assert result.total_coverage_pct == 0.0

    def test_single_cash_contribution(self):
        c = ContributionInput("cash", "Investor A", 500_000.0)
        result = calculate_production_economics([c], 1_000_000.0)
        assert result.cash_budget == 500_000.0
        assert result.contribution_value == 500_000.0
        assert result.effective_production_value == 500_000.0
        assert result.cash_coverage_pct == pytest.approx(0.5, abs=1e-6)

    def test_single_deferred_contribution(self):
        c = ContributionInput("deferred", "Producer", 100_000.0)
        result = calculate_production_economics([c], 1_000_000.0)
        assert result.deferred_total == 100_000.0
        assert result.cash_budget == 0.0
        assert result.effective_production_value == 100_000.0

    def test_single_equity_with_discount(self):
        c = ContributionInput("equity", "Post House", 100_000.0, fair_market_value=60_000.0)
        result = calculate_production_economics([c], 500_000.0)
        assert result.equity_total_fmv == 60_000.0
        # Adjustment trace should include discount record
        discount_records = [a for a in result.adjustment_trace
                            if a.field_adjusted == "equity_discount"]
        assert len(discount_records) == 1
        assert discount_records[0].original_value == 100_000.0
        assert discount_records[0].adjusted_value == 60_000.0

    def test_unknown_type_is_skipped_with_warning(self):
        c = ContributionInput("mystery_type", "Unknown", 50_000.0)
        result = calculate_production_economics([c], 100_000.0)
        assert result.contribution_value == 0.0
        assert any("mystery_type" in w for w in result.warnings)

    def test_qualifies_true_adds_to_incentive_total(self):
        c = ContributionInput("deferred", "Producer", 80_000.0, qualifies_for_incentive=True)
        result = calculate_production_economics([c], 200_000.0)
        assert result.incentive_qualifying_total == 80_000.0

    def test_qualifies_none_adds_to_uncertain(self):
        c = ContributionInput("in_kind", "Resort", 0.0, fair_market_value=40_000.0,
                              qualifies_for_incentive=None)
        result = calculate_production_economics([c], 100_000.0)
        assert result.incentive_qualifying_uncertain == 40_000.0
        assert any("uncertain" in w for w in result.warnings)

    def test_qualifies_false_adds_to_neither(self):
        c = ContributionInput("government_support", "MFDC", 50_000.0,
                              qualifies_for_incentive=False)
        result = calculate_production_economics([c], 100_000.0)
        assert result.incentive_qualifying_total == 0.0
        assert result.incentive_qualifying_uncertain == 0.0

    def test_conditional_adds_to_conditional_exposure(self):
        c = ContributionInput("equity", "Post", 100_000.0, fair_market_value=70_000.0,
                              is_conditional=True)
        result = calculate_production_economics([c], 200_000.0)
        assert result.conditional_exposure_usd == 70_000.0

    def test_conditional_trace_record(self):
        c = ContributionInput("equity", "Post", 100_000.0, is_conditional=True)
        result = calculate_production_economics([c], 200_000.0)
        cond_records = [a for a in result.adjustment_trace
                        if a.field_adjusted == "conditional_flag"]
        assert len(cond_records) == 1

    def test_jurisdiction_bucketing(self):
        c1 = ContributionInput("deferred", "P1", 50_000.0, jurisdiction_code="MU")
        c2 = ContributionInput("in_kind", "P2", 0.0, fair_market_value=30_000.0,
                               jurisdiction_code="MT")
        c3 = ContributionInput("sponsorship", "P3", 20_000.0)
        result = calculate_production_economics([c1, c2, c3], 200_000.0)
        assert result.normalized_budget_by_jurisdiction["MU"] == 50_000.0
        assert result.normalized_budget_by_jurisdiction["MT"] == 30_000.0
        assert result.normalized_budget_by_jurisdiction["UNASSIGNED"] == 20_000.0

    def test_replacement_cost_accumulated(self):
        c = ContributionInput("equity", "Post", 100_000.0, fair_market_value=70_000.0,
                              replacement_cost=100_000.0)
        result = calculate_production_economics([c], 200_000.0)
        assert result.replacement_cost_exposure == 100_000.0

    def test_unfunded_gap_never_negative(self):
        c = ContributionInput("cash", "Investor", 2_000_000.0)
        result = calculate_production_economics([c], 1_000_000.0)
        assert result.unfunded_gap_usd == 0.0

    def test_calculator_version_present(self):
        result = calculate_production_economics([], 100_000.0)
        assert result.calculator_version == "0.1.0"


# ---------------------------------------------------------------------------
# Full fixture integration
# ---------------------------------------------------------------------------

class TestFixtureIntegration:
    @pytest.fixture(scope="class")
    def result(self) -> ProductionEconomicsResult:
        return calculate_production_economics(ALL_FIXTURES, FIXTURE_GROSS_BUDGET_USD)

    def test_cash_budget_zero(self, result):
        assert result.cash_budget == EXPECTED_CASH_BUDGET

    def test_contribution_value(self, result):
        assert result.contribution_value == EXPECTED_CONTRIBUTION_VALUE

    def test_effective_production_value(self, result):
        # All contributions are non-cash, so effective_production_value = contribution_value
        assert result.effective_production_value == EXPECTED_CONTRIBUTION_VALUE

    def test_replacement_cost_exposure(self, result):
        assert result.replacement_cost_exposure == EXPECTED_REPLACEMENT_COST

    def test_incentive_qualifying_total(self, result):
        assert result.incentive_qualifying_total == EXPECTED_INCENTIVE_QUALIFYING

    def test_incentive_qualifying_uncertain(self, result):
        assert result.incentive_qualifying_uncertain == EXPECTED_UNCERTAIN

    def test_conditional_exposure(self, result):
        assert result.conditional_exposure_usd == EXPECTED_CONDITIONAL_EXPOSURE

    def test_unfunded_gap(self, result):
        expected_gap = FIXTURE_GROSS_BUDGET_USD - EXPECTED_CONTRIBUTION_VALUE
        assert result.unfunded_gap_usd == pytest.approx(expected_gap, abs=0.01)

    def test_unfunded_gap_positive(self, result):
        assert result.unfunded_gap_usd > 0

    def test_unfunded_gap_warning(self, result):
        assert any("Unfunded gap" in w for w in result.warnings)

    def test_per_type_deferred(self, result):
        assert result.deferred_total == 125_000.0

    def test_per_type_equity_fmv(self, result):
        assert result.equity_total_fmv == 90_000.0   # FMV, not face value

    def test_per_type_in_kind(self, result):
        assert result.in_kind_total_fmv == 45_000.0

    def test_per_type_sponsorship(self, result):
        assert result.sponsorship_total == 35_000.0

    def test_per_type_government_support(self, result):
        assert result.government_support_total == 50_000.0

    def test_per_type_vendor_financing_zero(self, result):
        assert result.vendor_financing_total == 0.0

    def test_jurisdiction_mu_total(self, result):
        # deferred(125K) + grant(50K) + facility(45K) = 220K
        assert result.normalized_budget_by_jurisdiction["MU"] == 220_000.0

    def test_jurisdiction_mt_total(self, result):
        # equity FMV(90K)
        assert result.normalized_budget_by_jurisdiction["MT"] == 90_000.0

    def test_jurisdiction_unassigned(self, result):
        # equipment sponsorship — no jurisdiction
        assert result.normalized_budget_by_jurisdiction["UNASSIGNED"] == 35_000.0

    def test_cash_coverage_zero(self, result):
        assert result.cash_coverage_pct == 0.0

    def test_total_coverage_pct(self, result):
        expected = EXPECTED_CONTRIBUTION_VALUE / FIXTURE_GROSS_BUDGET_USD
        assert result.total_coverage_pct == pytest.approx(expected, abs=1e-5)

    def test_adjustment_trace_has_equity_discount(self, result):
        discount = [a for a in result.adjustment_trace
                    if a.field_adjusted == "equity_discount"]
        assert len(discount) == 1
        assert discount[0].provider == "Chromatic Post Ltd"

    def test_adjustment_trace_has_conditional_records(self, result):
        cond = [a for a in result.adjustment_trace
                if a.field_adjusted == "conditional_flag"]
        # vendor_equity and government_grant are conditional
        assert len(cond) == 2
        providers = {a.provider for a in cond}
        assert "Chromatic Post Ltd" in providers
        assert "Mauritius Film Development Corporation (MFDC)" in providers

    def test_warnings_include_uncertainty_flags(self, result):
        uncertain_warnings = [w for w in result.warnings if "uncertain" in w.lower()]
        assert len(uncertain_warnings) == 2  # facility + sponsorship

    def test_gross_budget_stored(self, result):
        assert result.gross_budget_usd == FIXTURE_GROSS_BUDGET_USD

    def test_result_is_typed(self, result):
        assert isinstance(result, ProductionEconomicsResult)


# ---------------------------------------------------------------------------
# Vendor finance type
# ---------------------------------------------------------------------------

class TestVendorFinancing:
    def test_vendor_financing_adds_to_total(self):
        c = ContributionInput("vendor_financing", "Gap Lender", 200_000.0)
        result = calculate_production_economics([c], 500_000.0)
        assert result.vendor_financing_total == 200_000.0
        assert result.effective_production_value == 200_000.0

    def test_vendor_financing_fmv_fallback(self):
        c = ContributionInput("vendor_financing", "Gap Lender", 200_000.0)
        assert c.effective_fmv() == 200_000.0
