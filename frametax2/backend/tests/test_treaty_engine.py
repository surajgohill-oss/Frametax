"""
test_treaty_engine.py — Phase E2: treaty & co-production engine tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.calculators.treaty_engine import (
    MultilateralEligibilityResult,
    TreatyData,
    TreatyEligibilityResult,
    evaluate_bilateral_eligibility,
    evaluate_eurimages_eligibility,
    evaluate_european_convention_eligibility,
    evaluate_ibermedia_eligibility,
    get_available_bilateral_treaties,
    get_bilateral_treaty,
    is_eurimages_member,
    is_ibermedia_member,
    validate_spend_allocation,
)


# ---------------------------------------------------------------------------
# Bilateral treaty lookup
# ---------------------------------------------------------------------------

class TestBilateralTreatyLookup:
    def test_uk_ca_treaty_exists(self):
        t = get_bilateral_treaty("GB", "CA")
        assert t is not None
        assert t.treaty_slug == "uk-ca-bilateral"

    def test_ca_uk_treaty_symmetric(self):
        t = get_bilateral_treaty("CA", "GB")
        assert t is not None
        assert t.treaty_slug == "uk-ca-bilateral"

    def test_uk_ie_treaty_exists(self):
        t = get_bilateral_treaty("GB", "IE")
        assert t is not None
        assert t.treaty_slug == "uk-ie-bilateral"

    def test_fr_de_treaty_exists(self):
        t = get_bilateral_treaty("FR", "DE")
        assert t is not None
        assert t.treaty_slug == "fr-de-bilateral"

    def test_ca_fr_treaty_exists(self):
        t = get_bilateral_treaty("CA", "FR")
        assert t is not None
        assert t.treaty_slug == "ca-fr-bilateral"

    def test_nonexistent_treaty_returns_none(self):
        assert get_bilateral_treaty("US", "RU") is None

    def test_case_insensitive_lookup(self):
        t = get_bilateral_treaty("gb", "ca")
        assert t is not None

    def test_uk_unlocks_avec(self):
        t = get_bilateral_treaty("GB", "CA")
        assert "uk_avec" in t.majority_unlocks or "uk_avec" in t.minority_unlocks

    def test_ca_unlocks_cptc(self):
        t = get_bilateral_treaty("GB", "CA")
        assert "ca_federal_cptc" in t.majority_unlocks or "ca_federal_cptc" in t.minority_unlocks

    def test_uk_ie_unlocks_section_481(self):
        t = get_bilateral_treaty("GB", "IE")
        assert "ie_section_481" in t.majority_unlocks or "ie_section_481" in t.minority_unlocks

    def test_au_de_treaty_exists(self):
        assert get_bilateral_treaty("AU", "DE") is not None

    def test_fr_be_treaty_exists(self):
        assert get_bilateral_treaty("FR", "BE") is not None

    def test_get_available_treaties_for_gb(self):
        treaties = get_available_bilateral_treaties("GB")
        slugs = [t.treaty_slug for t in treaties]
        assert "uk-ca-bilateral" in slugs
        assert "uk-au-bilateral" in slugs
        assert "uk-fr-bilateral" in slugs
        assert "uk-ie-bilateral" in slugs
        assert len(treaties) >= 5


# ---------------------------------------------------------------------------
# Bilateral eligibility evaluation
# ---------------------------------------------------------------------------

class TestBilateralEligibility:
    def test_uk_ca_majority_uk_eligible(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 60.0, 40.0)
        assert result.is_eligible is True

    def test_uk_ca_majority_ca_eligible(self):
        result = evaluate_bilateral_eligibility("CA", "GB", 60.0, 40.0)
        assert result.is_eligible is True

    def test_uk_ca_majority_too_low_ineligible(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 25.0, 75.0)
        assert result.is_eligible is False
        assert result.passes_majority_min is False

    def test_uk_ca_minority_too_low_ineligible(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 85.0, 15.0)
        assert result.is_eligible is False
        assert result.passes_minority_min is False

    def test_uk_ca_minority_too_high_ineligible(self):
        # UK-CA treaty: minority_max_pct = 70
        result = evaluate_bilateral_eligibility("GB", "CA", 25.0, 75.0)
        assert result.is_eligible is False

    def test_uk_ca_exact_minimum_eligible(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 80.0, 20.0)
        assert result.is_eligible is True
        assert result.passes_majority_min is True
        assert result.passes_minority_min is True

    def test_uk_ie_no_cultural_test_required(self):
        result = evaluate_bilateral_eligibility("GB", "IE", 60.0, 40.0)
        assert result.is_eligible is True
        assert result.cultural_test_required is False

    def test_fr_de_cultural_test_required(self):
        result = evaluate_bilateral_eligibility("FR", "DE", 60.0, 40.0)
        assert result.cultural_test_required is True

    def test_fr_de_cultural_test_failed_ineligible(self):
        result = evaluate_bilateral_eligibility("FR", "DE", 60.0, 40.0,
                                                cultural_test_passed=False)
        assert result.is_eligible is False
        assert any("cultural test" in r.lower() for r in result.disqualification_reasons)

    def test_fr_de_cultural_test_warned_when_unknown(self):
        result = evaluate_bilateral_eligibility("FR", "DE", 60.0, 40.0,
                                                cultural_test_passed=None)
        assert any("cultural test" in w.lower() for w in result.warnings)

    def test_nonexistent_treaty_returns_ineligible(self):
        result = evaluate_bilateral_eligibility("US", "RU", 60.0, 40.0)
        assert result.is_eligible is False
        assert result.treaty is None
        assert len(result.disqualification_reasons) > 0

    def test_eligible_result_has_unlocked_slugs(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 60.0, 40.0)
        assert result.is_eligible is True
        # Majority (GB) should unlock AVEC; minority (CA) should unlock CPTC
        assert len(result.unlocked_majority_slugs) > 0 or len(result.unlocked_minority_slugs) > 0

    def test_ineligible_result_has_no_unlocked_slugs(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 5.0, 95.0)
        assert result.is_eligible is False
        assert result.unlocked_majority_slugs == []
        assert result.unlocked_minority_slugs == []

    def test_confidence_tier_propagated(self):
        result = evaluate_bilateral_eligibility("GB", "CA", 60.0, 40.0)
        assert result.confidence_tier == "PARSED"


# ---------------------------------------------------------------------------
# Spend allocation validation
# ---------------------------------------------------------------------------

class TestSpendAllocationValidation:
    def test_valid_allocation_passes(self):
        treaty = get_bilateral_treaty("GB", "CA")
        ok, violations = validate_spend_allocation(
            total_budget=10_000_000,
            majority_spend=7_000_000,
            minority_spend=3_000_000,
            treaty=treaty,
        )
        assert ok is True
        assert violations == []

    def test_majority_spend_too_low_fails(self):
        treaty = get_bilateral_treaty("GB", "CA")
        ok, violations = validate_spend_allocation(
            total_budget=10_000_000,
            majority_spend=2_000_000,
            minority_spend=8_000_000,
            treaty=treaty,
        )
        assert ok is False
        assert any("majority" in v.lower() for v in violations)

    def test_zero_budget_fails(self):
        treaty = get_bilateral_treaty("GB", "CA")
        ok, violations = validate_spend_allocation(0, 0, 0, treaty)
        assert ok is False


# ---------------------------------------------------------------------------
# Eurimages eligibility
# ---------------------------------------------------------------------------

class TestEurimagesEligibility:
    def test_three_member_countries_eligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR", "DE"],
            {"GB": 40.0, "FR": 35.0, "DE": 25.0},
        )
        assert result.is_eligible is True

    def test_two_countries_ineligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR"],
            {"GB": 60.0, "FR": 40.0},
        )
        assert result.is_eligible is False
        assert result.min_countries_met is False

    def test_non_member_country_ineligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR", "US"],
            {"GB": 40.0, "FR": 35.0, "US": 25.0},
        )
        assert result.is_eligible is False
        assert result.all_are_members is False
        assert "US" in result.non_member_countries

    def test_below_minimum_pct_ineligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR", "DE"],
            {"GB": 80.0, "FR": 15.0, "DE": 5.0},
        )
        assert result.is_eligible is False
        assert result.all_above_min is False

    def test_eurimages_fund_unlocked_when_eligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR", "DE"],
            {"GB": 40.0, "FR": 35.0, "DE": 25.0},
        )
        assert result.is_eligible is True
        assert "eu_eurimages" in result.unlocked_fund_slugs

    def test_eurimages_fund_not_unlocked_when_ineligible(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR"],
            {"GB": 60.0, "FR": 40.0},
        )
        assert "eu_eurimages" not in result.unlocked_fund_slugs

    def test_gb_is_eurimages_member(self):
        assert is_eurimages_member("GB") is True

    def test_de_is_eurimages_member(self):
        assert is_eurimages_member("DE") is True

    def test_us_is_not_eurimages_member(self):
        assert is_eurimages_member("US") is False

    def test_cultural_test_warning_present(self):
        result = evaluate_eurimages_eligibility(
            ["GB", "FR", "DE"],
            {"GB": 40.0, "FR": 35.0, "DE": 25.0},
        )
        assert any("cultural" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Ibermedia eligibility
# ---------------------------------------------------------------------------

class TestIbermediaEligibility:
    def test_es_br_eligible(self):
        result = evaluate_ibermedia_eligibility(
            ["ES", "BR"],
            {"ES": 60.0, "BR": 40.0},
        )
        assert result.is_eligible is True

    def test_us_ineligible_non_member(self):
        result = evaluate_ibermedia_eligibility(
            ["ES", "US"],
            {"ES": 70.0, "US": 30.0},
        )
        assert result.is_eligible is False
        assert "US" in result.non_member_countries

    def test_minority_below_10pct_ineligible(self):
        result = evaluate_ibermedia_eligibility(
            ["ES", "BR", "MX"],
            {"ES": 85.0, "BR": 10.0, "MX": 5.0},
        )
        assert result.is_eligible is False
        assert result.all_above_min is False

    def test_ibermedia_fund_unlocked(self):
        result = evaluate_ibermedia_eligibility(
            ["ES", "BR"],
            {"ES": 60.0, "BR": 40.0},
        )
        assert "ibermedia_programme" in result.unlocked_fund_slugs

    def test_es_is_ibermedia_member(self):
        assert is_ibermedia_member("ES") is True

    def test_br_is_ibermedia_member(self):
        assert is_ibermedia_member("BR") is True

    def test_gb_is_not_ibermedia_member(self):
        assert is_ibermedia_member("GB") is False


# ---------------------------------------------------------------------------
# European Convention eligibility
# ---------------------------------------------------------------------------

class TestEuropeanConventionEligibility:
    def test_bilateral_uk_fr_eligible(self):
        result = evaluate_european_convention_eligibility(
            ["GB", "FR"],
            {"GB": 60.0, "FR": 40.0},
        )
        assert result.is_eligible is True

    def test_majority_below_30pct_ineligible(self):
        result = evaluate_european_convention_eligibility(
            ["GB", "FR"],
            {"GB": 25.0, "FR": 75.0},
        )
        assert result.is_eligible is False

    def test_majority_above_70pct_ineligible_bilateral(self):
        result = evaluate_european_convention_eligibility(
            ["GB", "FR"],
            {"GB": 75.0, "FR": 25.0},
        )
        assert result.is_eligible is False

    def test_non_signatory_ineligible(self):
        result = evaluate_european_convention_eligibility(
            ["GB", "US"],
            {"GB": 60.0, "US": 40.0},
        )
        assert result.is_eligible is False
        assert "US" in result.non_member_countries

    def test_trilateral_eligible(self):
        result = evaluate_european_convention_eligibility(
            ["GB", "FR", "DE"],
            {"GB": 50.0, "FR": 30.0, "DE": 20.0},
        )
        assert result.is_eligible is True
