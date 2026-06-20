"""
Tests for mediterranean_comparison.py and incentive_guide_parser.py

Covers:
- Per-jurisdiction QPE qualification rules (flag overrides)
- Little Utopia run through all four Tier 1 jurisdictions
- Comparison matrix structure and known values
- Gap summary completeness
- Ranking by net producer benefit
- Incentive guide parser extraction
"""
from __future__ import annotations

import pytest

from app.calculators.mediterranean_comparison import (
    COMPARISON_VERSION,
    TIER1_PROGRAMS,
    COMPARISON_MATRIX,
    COMPARISON_DIMENSIONS,
    _jur_flags,
    _apply_jur_rules,
    run_tier1_comparison,
    rank_by_net_benefit,
    build_gap_summary,
)
from app.calculators.qpe_calculator import QPEAccount, get_scenario
from tests.fixtures.little_utopia_sanitized import ACCOUNTS

TIER1_CODES = {"MU", "MT", "GR", "CY"}


# ---------------------------------------------------------------------------
# Program configuration
# ---------------------------------------------------------------------------

class TestTierOnePrograms:
    def test_all_tier1_codes_present(self):
        assert set(TIER1_PROGRAMS.keys()) == TIER1_CODES

    def test_mauritius_rate_35(self):
        assert TIER1_PROGRAMS["MU"].base_rate == 0.35
        assert TIER1_PROGRAMS["MU"].rate_verified is False

    def test_malta_base_25_max_40(self):
        assert TIER1_PROGRAMS["MT"].base_rate == 0.25
        assert TIER1_PROGRAMS["MT"].max_rate == 0.40

    def test_greece_40_flat(self):
        assert TIER1_PROGRAMS["GR"].base_rate == 0.40
        assert TIER1_PROGRAMS["GR"].max_rate == 0.40

    def test_cyprus_35_discovery(self):
        assert TIER1_PROGRAMS["CY"].base_rate == 0.35
        assert TIER1_PROGRAMS["CY"].confidence_tier == "DISCOVERY"

    def test_no_rate_verified(self):
        for code, prog in TIER1_PROGRAMS.items():
            assert prog.rate_verified is False, (
                f"{code}: rate_verified must remain False until statute text reviewed"
            )

    def test_malta_lowest_delay(self):
        delays = {code: p.finance_delay_weeks for code, p in TIER1_PROGRAMS.items()}
        assert delays["MT"] < delays["GR"], "Malta should have lower finance delay than Greece"
        assert delays["MT"] < delays["MU"], "Malta should have lower finance delay than Mauritius"


# ---------------------------------------------------------------------------
# Jurisdiction QPE flag rules
# ---------------------------------------------------------------------------

def _acct(code: str, dept: str, c: bool, b: bool, o: bool, **kw) -> QPEAccount:
    return QPEAccount(
        account_code=code,
        description=code,
        department=dept,
        amount_usd=100.0,
        conservative_qualifies=c,
        base_qualifies=b,
        optimistic_qualifies=o,
        **kw,
    )


class TestJurFlagRules:
    # ── Universal exclusions ───────────────────────────────────────────────

    def test_memo_line_excluded_all_jurs(self):
        acc = _acct("44-00", "Production", True, True, True, is_memo_line=True)
        for jur in TIER1_CODES:
            assert _jur_flags(acc, jur) == (False, False, False), f"{jur}: memo must be excluded"

    def test_other_dept_excluded_all_jurs(self):
        acc = _acct("60-00", "Other", False, False, False)
        for jur in TIER1_CODES:
            assert _jur_flags(acc, jur) == (False, False, False)

    def test_post_dept_excluded_all_jurs(self):
        acc = _acct("51-00", "Post Production", False, False, False)
        for jur in TIER1_CODES:
            assert _jur_flags(acc, jur) == (False, False, False)

    def test_travel_excluded_all_jurs(self):
        acc = _acct("39-00", "Production", False, False, False)
        for jur in TIER1_CODES:
            assert _jur_flags(acc, jur) == (False, False, False)

    # ── Malta ──────────────────────────────────────────────────────────────

    def test_malta_atl_all_true(self):
        for code in ("10-00", "11-00", "12-00", "13-00"):
            acc = _acct(code, "Above The Line", False, False, True)
            assert _jur_flags(acc, "MT") == (True, True, True), (
                f"MT: {code} ATL should qualify all scenarios"
            )

    def test_malta_btl_all_true(self):
        acc = _acct("20-00", "Production", True, True, True)
        assert _jur_flags(acc, "MT") == (True, True, True)

    def test_malta_frogsquad_qualifies_all(self):
        frogsquad = next(a for a in ACCOUNTS if a.account_code == "33-00")
        c, b, o = _jur_flags(frogsquad, "MT")
        assert c and b and o, "Malta: Frogsquad qualifies all scenarios (no routing issue)"

    def test_malta_accommodation_qualifies_all(self):
        hod = next(a for a in ACCOUNTS if a.account_code == "37-00")
        c, b, o = _jur_flags(hod, "MT")
        assert c and b and o, "Malta: HOD accommodation qualifies all scenarios"

    # ── Greece ─────────────────────────────────────────────────────────────

    def test_greece_atl_story_base_plus(self):
        acc = _acct("10-00", "Above The Line", False, False, True)
        assert _jur_flags(acc, "GR") == (False, True, True)

    def test_greece_atl_director_base_plus(self):
        acc = _acct("11-00", "Above The Line", False, False, True)
        assert _jur_flags(acc, "GR") == (False, True, True)

    def test_greece_cast_optimistic_only(self):
        acc = _acct("13-00", "Above The Line", False, False, False)
        assert _jur_flags(acc, "GR") == (False, False, True)

    def test_greece_frogsquad_base_plus(self):
        frogsquad = next(a for a in ACCOUNTS if a.account_code == "33-00")
        assert _jur_flags(frogsquad, "GR") == (False, True, True)

    def test_greece_clear_btl_conservative(self):
        vessel = next(a for a in ACCOUNTS if a.account_code == "31-00")
        c, b, o = _jur_flags(vessel, "GR")
        assert c and b and o

    # ── Cyprus ─────────────────────────────────────────────────────────────

    def test_cyprus_atl_optimistic_only(self):
        acc = _acct("11-00", "Above The Line", False, False, True)
        assert _jur_flags(acc, "CY") == (False, False, True)

    def test_cyprus_cast_excluded_all(self):
        acc = _acct("13-00", "Above The Line", False, False, False)
        assert _jur_flags(acc, "CY") == (False, False, False)

    def test_cyprus_frogsquad_base_plus(self):
        frogsquad = next(a for a in ACCOUNTS if a.account_code == "33-00")
        assert _jur_flags(frogsquad, "CY") == (False, True, True)

    def test_cyprus_accommodation_base_plus(self):
        hod = next(a for a in ACCOUNTS if a.account_code == "37-00")
        assert _jur_flags(hod, "CY") == (False, True, True)

    def test_cyprus_vessel_charter_conservative(self):
        vessel = next(a for a in ACCOUNTS if a.account_code == "31-00")
        c, b, o = _jur_flags(vessel, "CY")
        assert c and b and o


# ---------------------------------------------------------------------------
# Little Utopia — run through all four jurisdictions
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def comparison():
    return run_tier1_comparison(ACCOUNTS)


class TestLittleUtopiaComparison:
    def test_all_jurisdictions_present(self, comparison):
        assert set(comparison.keys()) == TIER1_CODES

    def test_gross_budget_same_all_jurs(self, comparison):
        gross_values = {code: r.qpe_result.gross_budget_usd for code, r in comparison.items()}
        # All four share the same accounts; gross should be the same non-memo total
        values = list(gross_values.values())
        assert max(values) - min(values) < 1.0, (
            f"Gross budget must be identical across jurisdictions: {gross_values}"
        )

    # ── QPE ordering ───────────────────────────────────────────────────────

    def test_malta_qpe_highest_conservative(self, comparison):
        mt_c = get_scenario(comparison["MT"].qpe_result, "conservative").qpe_usd
        mu_c = get_scenario(comparison["MU"].qpe_result, "conservative").qpe_usd
        cy_c = get_scenario(comparison["CY"].qpe_result, "conservative").qpe_usd
        assert mt_c > mu_c, "Malta conservative QPE must exceed Mauritius (all BTL qualifies in MT)"
        assert mt_c > cy_c, "Malta conservative QPE must exceed Cyprus (cleaner qualification)"

    def test_malta_qpe_equal_all_scenarios(self, comparison):
        mt = comparison["MT"].qpe_result
        c = get_scenario(mt, "conservative").qpe_usd
        b = get_scenario(mt, "base").qpe_usd
        o = get_scenario(mt, "optimistic").qpe_usd
        assert c == b == o, "Malta: C/B/O must be equal (all ATL+BTL qualifies from conservative)"

    def test_greece_base_greater_than_conservative(self, comparison):
        gr = comparison["GR"].qpe_result
        c = get_scenario(gr, "conservative").qpe_usd
        b = get_scenario(gr, "base").qpe_usd
        assert b > c, "Greece base adds ATL (excl. cast) + Frogsquad"

    def test_greece_optimistic_adds_cast(self, comparison):
        gr = comparison["GR"].qpe_result
        b = get_scenario(gr, "base").qpe_usd
        o = get_scenario(gr, "optimistic").qpe_usd
        assert o > b
        cast_amount = next(a.amount_usd for a in ACCOUNTS if a.account_code == "13-00")
        assert abs((o - b) - cast_amount) < 1.0

    def test_mauritius_has_lowest_conservative_qpe(self, comparison):
        conservatives = {code: get_scenario(r.qpe_result, "conservative").qpe_usd
                        for code, r in comparison.items()}
        assert conservatives["MU"] <= min(conservatives.values()) + 1.0, (
            "Mauritius should have the lowest or equal-lowest conservative QPE "
            "(most restrictive qualification rules)"
        )

    # ── Rebate amounts ─────────────────────────────────────────────────────

    def test_malta_rebate_uses_max_rate_40(self, comparison):
        assert abs(comparison["MT"].rebate_max -
                   get_scenario(comparison["MT"].qpe_result, "base").qpe_usd * 0.40) < 1.0

    def test_greece_rebate_at_40pct(self, comparison):
        gr = comparison["GR"]
        expected = get_scenario(gr.qpe_result, "base").qpe_usd * 0.40
        assert abs(gr.rebate_max - expected) < 1.0

    def test_cyprus_rebate_at_35pct(self, comparison):
        cy = comparison["CY"]
        expected = get_scenario(cy.qpe_result, "base").qpe_usd * 0.35
        assert abs(cy.rebate_max - expected) < 1.0

    # ── Finance cost ───────────────────────────────────────────────────────

    def test_malta_lowest_finance_cost(self, comparison):
        assert comparison["MT"].finance_cost_base < comparison["GR"].finance_cost_base, (
            "Malta 20-week delay must produce lower finance cost than Greece 39-week delay"
        )
        assert comparison["MT"].finance_cost_base < comparison["MU"].finance_cost_base

    # ── Net benefit ────────────────────────────────────────────────────────

    def test_malta_net_benefit_positive(self, comparison):
        assert comparison["MT"].net_benefit_base > 0

    def test_greece_net_benefit_positive(self, comparison):
        assert comparison["GR"].net_benefit_base > 0

    def test_net_benefit_pct_in_range(self, comparison):
        for code, r in comparison.items():
            assert 0 < r.net_benefit_pct < 1.0, (
                f"{code}: net_benefit_pct {r.net_benefit_pct:.3f} out of range"
            )

    def test_malta_highest_net_benefit(self, comparison):
        ranked = rank_by_net_benefit(comparison)
        assert ranked[0][0] == "MT", (
            f"Malta should rank highest (40% rate, lowest delay); got {ranked[0][0]}"
        )

    def test_mauritius_lowest_or_second_lowest(self, comparison):
        ranked = rank_by_net_benefit(comparison)
        codes_ranked = [c for c, _ in ranked]
        mu_rank = codes_ranked.index("MU")
        assert mu_rank >= 2, (
            f"Mauritius should rank 3rd or 4th (unknown rate, high friction); ranked {mu_rank+1}"
        )

    def test_ranking_has_four_entries(self, comparison):
        ranked = rank_by_net_benefit(comparison)
        assert len(ranked) == 4


# ---------------------------------------------------------------------------
# Comparison matrix
# ---------------------------------------------------------------------------

class TestComparisonMatrix:
    def test_all_tier1_codes_in_matrix(self):
        assert set(COMPARISON_MATRIX.keys()) == TIER1_CODES

    @pytest.mark.parametrize("code", list(TIER1_CODES))
    def test_all_dimensions_present(self, code):
        missing = set(COMPARISON_DIMENSIONS) - set(COMPARISON_MATRIX[code].keys())
        assert not missing, f"{code}: missing dimensions {missing}"

    def test_malta_atl_confirmed(self):
        assert COMPARISON_MATRIX["MT"]["atl_treatment"] is True

    def test_malta_marine_confirmed(self):
        assert COMPARISON_MATRIX["MT"]["marine_vessel_treatment"] is True

    def test_greece_atl_confirmed(self):
        assert COMPARISON_MATRIX["GR"]["atl_treatment"] is True

    def test_mauritius_atl_unknown(self):
        assert COMPARISON_MATRIX["MU"]["atl_treatment"] is None

    def test_mauritius_marine_confirmed(self):
        assert COMPARISON_MATRIX["MU"]["marine_vessel_treatment"] is True

    def test_mauritius_vat_non_recoverable(self):
        assert "non_recoverable" in str(COMPARISON_MATRIX["MU"]["vat_treatment"])

    def test_eu_jurisdictions_vat_recoverable(self):
        for code in ("MT", "GR", "CY"):
            assert "recoverable" in str(COMPARISON_MATRIX[code]["vat_treatment"]), (
                f"{code}: EU jurisdiction should have recoverable VAT"
            )

    @pytest.mark.parametrize("code", list(TIER1_CODES))
    def test_insurance_excluded(self, code):
        assert COMPARISON_MATRIX[code]["insurance_treatment"] is False

    @pytest.mark.parametrize("code", list(TIER1_CODES))
    def test_contingency_excluded(self, code):
        assert COMPARISON_MATRIX[code]["contingency_treatment"] is False


# ---------------------------------------------------------------------------
# Gap summary
# ---------------------------------------------------------------------------

class TestGapSummary:
    @pytest.fixture(autouse=True)
    def gaps(self, comparison):
        self._gaps = build_gap_summary(comparison)

    def test_all_jurs_have_gaps(self):
        for code in TIER1_CODES:
            assert len(self._gaps[code]) > 0, f"{code}: should have at least one gap"

    def test_mauritius_has_most_gaps(self):
        mu_count = len(self._gaps["MU"])
        mt_count = len(self._gaps["MT"])
        assert mu_count >= mt_count, "Mauritius should have at least as many gaps as Malta"

    def test_rate_verified_gap_present_all_jurs(self):
        for code in TIER1_CODES:
            rate_gaps = [g for g in self._gaps[code] if "rate" in g.lower() and "verif" in g.lower()]
            assert rate_gaps, f"{code}: gap summary must include rate not verified"

    def test_mauritius_payment_timing_gap(self):
        timing_gaps = [g for g in self._gaps["MU"] if "payment_timing" in g or "timing" in g.lower()]
        assert timing_gaps, "Mauritius: payment_timing should appear in gaps"

    def test_mauritius_atl_gap(self):
        atl_gaps = [g for g in self._gaps["MU"] if "atl" in g.lower()]
        assert atl_gaps, "Mauritius: ATL treatment should be in gaps"


# ---------------------------------------------------------------------------
# Incentive guide parser
# ---------------------------------------------------------------------------

class TestIncentiveGuideParser:
    def test_rate_extraction_single(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "The programme provides a 40% cash rebate on qualifying expenditure."
        result = parse_incentive_guide(text, "Test Guide", "GR")
        assert result.base_rate == pytest.approx(0.40)
        assert result.is_cash_rebate is True

    def test_rate_extraction_range(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = (
            "A 25% cash rebate is available. "
            "With all uplifts, productions may receive up to 40% cash rebate."
        )
        result = parse_incentive_guide(text, "Malta Guide", "MT")
        assert result.base_rate == pytest.approx(0.25)
        assert result.max_rate == pytest.approx(0.40)

    def test_atl_qualify_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Director fees are eligible qualifying expenditure."
        result = parse_incentive_guide(text, "Guide", "MT")
        assert result.atl_qualifies is True

    def test_marine_qualify_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Vessel charter costs are eligible for the cash rebate."
        result = parse_incentive_guide(text, "Guide", "MT")
        assert result.vessel_marine_qualifies is True

    def test_accommodation_qualify_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Accommodation costs qualify as eligible expenditure."
        result = parse_incentive_guide(text, "Guide", "GR")
        assert result.accommodation_qualifies is True

    def test_refundable_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "The rebate is fully refundable to non-resident productions."
        result = parse_incentive_guide(text, "Guide", "MT")
        assert result.is_refundable is True

    def test_min_spend_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Minimum qualifying spend of EUR 50,000 is required."
        result = parse_incentive_guide(text, "Guide", "MT")
        assert result.min_spend_local == pytest.approx(50_000.0)

    def test_cultural_test_detected(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Productions must pass the cultural test administered by the authority."
        result = parse_incentive_guide(text, "Guide", "IE")
        assert result.requires_cultural_test is True

    def test_empty_text_returns_nones(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        result = parse_incentive_guide("", "Empty", "MU")
        assert result.base_rate is None
        assert result.atl_qualifies is None
        assert result.vessel_marine_qualifies is None
        assert result.confidence_tier == "DISCOVERY"

    def test_jurisdiction_code_preserved(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        result = parse_incentive_guide("40% cash rebate", "Guide", "GR")
        assert result.jurisdiction_code == "GR"

    def test_weeks_extraction(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Payment is typically made within 20 weeks of audit submission."
        result = parse_incentive_guide(text, "Guide", "MT")
        assert result.cashflow_timing_weeks == 20

    def test_working_days_converted_to_weeks(self):
        from app.ingestion.incentive_guide_parser import parse_incentive_guide
        text = "Processed within 60 working days of submission."
        result = parse_incentive_guide(text, "Guide", "MT")
        # 60 days / 7 = ~8-9 weeks
        assert result.cashflow_timing_weeks is not None
        assert 8 <= result.cashflow_timing_weeks <= 10
