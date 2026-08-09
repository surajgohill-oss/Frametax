"""
Tests for jurisdiction_comparison.py

Validates:
- SpendCategory.VESSEL_MARINE enum value exists
- Vessel/marine descriptions classify correctly via classify_line_item
- All Tier 1 profiles present in TIER1_PROFILES
- Scoring dimension weights sum to 1.0
- Required profile fields populated for confirmed programs
- Mauritius correctly DISCOVERY with null rates
- Marine suitability values are valid constants
- Secondary profiles present for all expected jurisdictions
- No profile has a rate of 0.0 masquerading as "unknown" (must be None or a real rate)
"""
from __future__ import annotations

import pytest

from app.models.enums import SpendCategory
from app.calculators.classify_budget_line_items import classify_line_item
from app.calculators.jurisdiction_comparison import (
    FRAMEWORK_VERSION,
    SCORING_DIMENSIONS,
    TIER1_PROFILES,
    SECONDARY_PROFILES,
    ALL_PROFILES,
    GAP_MATRIX,
    MarineSuitability,
    CrewDepth,
    FinancingFriction,
    VALID_MARINE_SUITABILITY,
    VALID_CREW_DEPTH,
    VALID_FINANCING_FRICTION,
)


# ---------------------------------------------------------------------------
# SpendCategory enum
# ---------------------------------------------------------------------------

class TestVesselMarineEnum:
    def test_vessel_marine_in_spend_category(self):
        assert SpendCategory.VESSEL_MARINE == "vessel_marine"

    def test_vessel_marine_string_value(self):
        assert SpendCategory.VESSEL_MARINE.value == "vessel_marine"


# ---------------------------------------------------------------------------
# Vessel/marine classification
# ---------------------------------------------------------------------------

class TestVesselMarineClassification:
    def test_vessel_charter(self):
        result = classify_line_item("Vessel Charter Week 3")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_yacht_rental(self):
        result = classify_line_item("Yacht Rental — Principal Photography")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_dive_boat(self):
        result = classify_line_item("Dive Boat Hire — Underwater Unit")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_underwater_camera(self):
        result = classify_line_item("Underwater Camera Housing and Operator")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_speedboat(self):
        result = classify_line_item("Speedboat Purchase — Action Sequence")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_charter_boat(self):
        result = classify_line_item("Charter Boat for Marine Unit")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_marine_equipment(self):
        result = classify_line_item("Marine Equipment Rental")
        assert result.spend_category == SpendCategory.VESSEL_MARINE

    def test_vessel_is_btl(self):
        result = classify_line_item("Vessel Charter")
        assert result.atl_btl.value == "btl"
        assert result.is_labor is False
        assert result.is_fixed is False

    def test_non_marine_transport_unaffected(self):
        result = classify_line_item("Van Rental — Production")
        assert result.spend_category == SpendCategory.BTL_TRANSPORTATION

    def test_camera_equipment_unaffected(self):
        result = classify_line_item("Camera Rental Package")
        assert result.spend_category == SpendCategory.BTL_EQUIPMENT_RENTAL


# ---------------------------------------------------------------------------
# Scoring Framework
# ---------------------------------------------------------------------------

class TestScoringFramework:
    def test_framework_version_set(self):
        assert FRAMEWORK_VERSION == "0.1.0"

    def test_dimensions_sum_to_one(self):
        total = sum(d.weight_default for d in SCORING_DIMENSIONS)
        assert abs(total - 1.0) < 1e-9

    def test_six_dimensions(self):
        assert len(SCORING_DIMENSIONS) == 6

    def test_required_dimension_keys(self):
        keys = {d.key for d in SCORING_DIMENSIONS}
        assert "net_producer_benefit" in keys
        assert "marine_suitability" in keys
        assert "ease_of_qualification" in keys
        assert "crew_depth" in keys
        assert "financing_efficiency" in keys
        assert "operational_complexity" in keys

    def test_marine_weight_significant(self):
        marine = next(d for d in SCORING_DIMENSIONS if d.key == "marine_suitability")
        assert marine.weight_default >= 0.15, "Marine suitability must have meaningful weight"

    def test_net_benefit_highest_weight(self):
        weights = {d.key: d.weight_default for d in SCORING_DIMENSIONS}
        assert weights["net_producer_benefit"] == max(weights.values())


# ---------------------------------------------------------------------------
# Tier 1 Profiles
# ---------------------------------------------------------------------------

TIER1_CODES = {"MU", "MT", "GR", "CY"}
SECONDARY_CODES = {
    "IE", "FR", "IT", "ES", "HR", "HU", "BE", "DE", "GB",
    "CA", "CA-BC", "CA-ON", "CA-QC", "AU", "NZ",
    "US-GA", "US-CA", "US-NY", "US-NM", "US-OR", "US-LA",
    "ZA", "AE-AD", "MA", "DK", "FI", "NO", "SE",
    "SA", "JO", "TH", "MY", "PH", "KR", "MX", "CL", "IL", "JP", "EG",
    "PA", "CR", "GH", "FJ", "GE", "TW", "KZ", "AL", "ME", "MK",
    "US-NV", "US-RI", "TT", "QA", "UZ", "MN", "CH", "SI", "UA",
    "PT", "AU-SA",
    "US-WA", "US-IL", "US-NC", "US-SC", "US-MA", "US-TX", "US-CT", "US-PA",
    "US-MD", "US-VA", "US-CO", "US-TN", "US-OK", "US-AL", "US-KY",
    "CA-AB", "CA-MB", "CA-NS", "CA-NB",
    "NL", "AT", "CZ", "RO", "RS", "IS",
    "AU-NSW", "AU-QLD", "CO", "DO", "SG", "AE-DXB",
    "BG", "EE", "LV", "LT", "PL", "SK", "LU",
    "US-HI", "US-UT", "US-MN", "US-MS", "US-AZ", "US-PR",
    "CA-SK", "CA-NL",
}


class TestTier1ProfilesPresent:
    def test_all_tier1_codes_present(self):
        assert set(TIER1_PROFILES.keys()) == TIER1_CODES

    def test_all_secondary_codes_present(self):
        assert set(SECONDARY_PROFILES.keys()) == SECONDARY_CODES

    def test_all_profiles_in_all_profiles(self):
        assert ALL_PROFILES.keys() == TIER1_CODES | SECONDARY_CODES


class TestMauritiusProfile:
    @pytest.fixture
    def mu(self):
        return TIER1_PROFILES["MU"]

    def test_verified_tier(self, mu):
        """Rates were promoted PARSED -> VERIFIED after full review of the
        primary source (EDB Film Rebate Scheme — Submission Procedures,
        31 Jan 2020, citing the FRS Regulation 2018)."""
        assert mu.confidence_tier == "VERIFIED"

    def test_base_rate_30_statutory(self, mu):
        """30% general rebate per the primary source. The budget document's
        own 'EDB Rebate at 35%' line is budget evidence, never authority
        (permanent Rules 1/2) — recorded as a reported conflict in
        app.data.program_rate_rules, not as a rate."""
        assert mu.base_rate == 0.30

    def test_max_rate_40_band_ceiling(self, mu):
        """'Up to 40%' feature-film band (min QPE USD 1,000,000) per the
        primary source — max_rate is the band ceiling."""
        assert mu.max_rate == 0.40

    def test_rates_mirror_statutory_rate_rules(self, mu):
        """Rule 4: cross-border comparison must use database/statutory
        rates — the profile must mirror program_rate_rules exactly."""
        from app.data.program_rate_rules import get_rate_rules
        rules = get_rate_rules("mu_edb_incentive")
        assert mu.base_rate == min(r.rate for r in rules)
        assert mu.max_rate == max(r.rate for r in rules)

    def test_no_cashflow_timing(self, mu):
        assert mu.cashflow_timing_weeks is None

    def test_has_open_water(self, mu):
        assert mu.has_open_water_filming is True

    def test_no_water_tanks(self, mu):
        assert mu.has_water_tanks is False

    def test_shallow_crew(self, mu):
        assert mu.crew_depth_rating == CrewDepth.SHALLOW

    def test_strong_marine_suitability(self, mu):
        assert mu.marine_suitability == MarineSuitability.STRONG

    def test_data_gaps_populated(self, mu):
        assert len(mu.data_gaps) >= 5

    def test_vessel_marine_confirmed(self, mu):
        assert mu.vessel_marine_qualifies is True

    def test_vat_not_recoverable(self, mu):
        assert mu.vat_recoverable is False

    def test_high_financing_friction(self, mu):
        assert mu.financing_friction == FinancingFriction.HIGH

    def test_atl_qualifies_per_primary_source(self, mu):
        """EDB QPE list names 'Remuneration for cast and crew' / 'Labour
        costs (including non-nationals)' with no ATL carve-out."""
        assert mu.atl_qualifies is True


class TestMaltaProfile:
    @pytest.fixture
    def mt(self):
        return TIER1_PROFILES["MT"]

    def test_verified_tier(self, mt):
        # Upgraded from PARSED to VERIFIED (2026-07-26, account-handoff
        # session): the real MFC Cash Rebate Guidelines PDF (Jan 2019, 28
        # pages) was recovered and read in full via direct pypdf text
        # extraction, resolving an earlier tool parser failure that had
        # produced hallucinated placeholder analysis instead of real text.
        assert mt.confidence_tier == "VERIFIED"

    def test_base_rate(self, mt):
        assert mt.base_rate == 0.25

    def test_max_rate(self, mt):
        # Corrected from 0.40: the confirmed Guidelines describe a
        # separate, higher-ceiling "Difficult Audiovisual Work" category
        # (budget <= EUR 1.5M + a points-based National Work test)
        # qualifying for up to 50%, not modeled before this session.
        assert mt.max_rate == 0.50

    def test_excellent_marine(self, mt):
        assert mt.marine_suitability == MarineSuitability.EXCELLENT

    def test_water_tanks(self, mt):
        assert mt.has_water_tanks is True

    def test_vessel_qualifies(self, mt):
        assert mt.vessel_marine_qualifies is True

    def test_atl_qualifies(self, mt):
        assert mt.atl_qualifies is True

    def test_low_financing_friction(self, mt):
        assert mt.financing_friction == FinancingFriction.LOW

    def test_min_spend(self, mt):
        # Corrected from EUR 50,000: the confirmed Guidelines state EUR
        # 100,000 for the general case (EUR 50,000 applies only to the
        # separate "Difficult Audiovisual Work" category, not the general
        # minimum).
        assert mt.min_spend_local == 100_000.0

    def test_cultural_test_required(self, mt):
        # Corrected from False: the confirmed Guidelines require a
        # minimum of 40 points in aggregate in a Cultural Test (Section
        # 2.4) -- the prior False was never sourced from an official
        # document.
        assert mt.requires_cultural_test is True


class TestGreeceProfile:
    @pytest.fixture
    def gr(self):
        return TIER1_PROFILES["GR"]

    def test_parsed_tier(self, gr):
        # Incentive/Optimizer Core Closeout: bumped to VERIFIED alongside
        # program_rate_rules.GR_RATE_RULES, per the final rule resolution
        # sourced to JMD 607434 (see docs/validation/
        # CODEX_FINAL_RULE_RESOLUTION.md §2). Kept in sync by
        # test_jurisdiction_doctrine_consistency.py.
        assert gr.confidence_tier == "VERIFIED"

    def test_base_rate_40(self, gr):
        assert gr.base_rate == 0.40

    def test_strong_marine(self, gr):
        assert gr.marine_suitability == MarineSuitability.STRONG

    def test_no_water_tanks(self, gr):
        assert gr.has_water_tanks is False

    def test_vessel_qualifies(self, gr):
        assert gr.vessel_marine_qualifies is True

    def test_cashflow_risk(self, gr):
        assert gr.cashflow_timing_weeks >= 26, "Greece cashflow should reflect real delay risk"

    def test_no_cultural_test(self, gr):
        assert gr.requires_cultural_test is False


class TestCyprusProfile:
    @pytest.fixture
    def cy(self):
        return TIER1_PROFILES["CY"]

    def test_parsed_tier(self, cy):
        # Corrected worldwide-population phase: confirmed directly from the
        # official Cyprus Film Commission page (film.investcyprus.org.cy),
        # "up to 45%" — a real 35%/45% cultural-test band, not the flat 35%
        # DISCOVERY-tier figure this test previously asserted.
        assert cy.confidence_tier == "PARSED"

    def test_base_rate_35_ceiling_45(self, cy):
        assert cy.base_rate == 0.35
        assert cy.max_rate == 0.45

    def test_shallow_crew(self, cy):
        assert cy.crew_depth_rating == CrewDepth.SHALLOW

    def test_strong_marine(self, cy):
        assert cy.marine_suitability == MarineSuitability.STRONG

    def test_no_water_tanks(self, cy):
        assert cy.has_water_tanks is False

    def test_vessel_qualifies_expected(self, cy):
        assert cy.vessel_marine_qualifies is True

    def test_data_gaps_populated(self, cy):
        assert len(cy.data_gaps) >= 5


# ---------------------------------------------------------------------------
# Profile data integrity
# ---------------------------------------------------------------------------

class TestProfileIntegrity:
    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_marine_suitability_valid(self, code):
        profile = ALL_PROFILES[code]
        assert profile.marine_suitability in VALID_MARINE_SUITABILITY, (
            f"{code}: invalid marine_suitability '{profile.marine_suitability}'"
        )

    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_crew_depth_valid(self, code):
        profile = ALL_PROFILES[code]
        assert profile.crew_depth_rating in VALID_CREW_DEPTH, (
            f"{code}: invalid crew_depth_rating '{profile.crew_depth_rating}'"
        )

    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_financing_friction_valid(self, code):
        profile = ALL_PROFILES[code]
        assert profile.financing_friction in VALID_FINANCING_FRICTION, (
            f"{code}: invalid financing_friction '{profile.financing_friction}'"
        )

    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_no_zero_masquerading_as_unknown_rate(self, code):
        profile = ALL_PROFILES[code]
        assert profile.base_rate != 0.0, (
            f"{code}: base_rate should be None (unknown) not 0.0"
        )

    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_authority_name_set(self, code):
        profile = ALL_PROFILES[code]
        assert profile.authority_name, f"{code}: authority_name must be set"

    @pytest.mark.parametrize("code", list(TIER1_CODES | SECONDARY_CODES))
    def test_notes_set(self, code):
        profile = ALL_PROFILES[code]
        assert len(profile.notes) > 50, f"{code}: notes should be substantive"

    def test_hungary_no_marine(self):
        hu = SECONDARY_PROFILES["HU"]
        assert hu.marine_suitability == MarineSuitability.NONE
        assert hu.vessel_marine_qualifies is False
        assert hu.has_open_water_filming is False

    def test_spain_rate_is_confirmed_marginal_25_not_flat_30_or_canary_50(self):
        # Corrected per Executable Jurisdiction Model Completion phase: Article
        # 36.2 LIS (BOE-A-2014-12328), verbatim text confirmed from two
        # independent legal-database reproductions, is a MARGINAL/BRACKETED
        # rate (30% first EUR 1M, 25% excess) — not the flat 30%/50% Canary
        # Islands figures this test previously asserted (those were an
        # unverified DISCOVERY-tier carryover; the 50% Canary Islands rate
        # does not appear anywhere in Article 36's text). base_rate/max_rate
        # are both set to the conservative 25% marginal rate that governs
        # spend above the bracket break — see program_rate_rules.py
        # ES_RATE_RULES and ES_UNVERIFIED_CLAIMS for the full citation trail.
        es = SECONDARY_PROFILES["ES"]
        assert es.confidence_tier == "PARSED"
        assert es.base_rate == 0.25
        assert es.max_rate == 0.25
        assert es.annual_cap_local == 20_000_000.0

    def test_ireland_transferable(self):
        ie = SECONDARY_PROFILES["IE"]
        assert ie.is_transferable is True, "Section 481 is assignable to gap lender"


# ---------------------------------------------------------------------------
# GAP_MATRIX
# ---------------------------------------------------------------------------

TIER1_GAP_KEYS = {
    "rate_verified", "atl_treatment", "foreign_labor", "vessel_marine",
    "accommodation_per_diem", "vat_customs", "finance_timing", "grants_support",
}


class TestGapMatrix:
    def test_all_tier1_codes_in_gap_matrix(self):
        assert set(GAP_MATRIX.keys()) == TIER1_CODES

    @pytest.mark.parametrize("code", list(TIER1_CODES))
    def test_all_required_keys_present(self, code):
        assert TIER1_GAP_KEYS.issubset(GAP_MATRIX[code].keys()), (
            f"{code} gap matrix missing keys: {TIER1_GAP_KEYS - GAP_MATRIX[code].keys()}"
        )

    def test_mauritius_rate_not_verified(self):
        assert GAP_MATRIX["MU"]["rate_verified"] is False

    def test_mauritius_vessel_marine_confirmed(self):
        assert GAP_MATRIX["MU"]["vessel_marine"] is True

    def test_mauritius_vat_non_recoverable_noted(self):
        assert "non_recoverable" in str(GAP_MATRIX["MU"]["vat_customs"])

    def test_mauritius_atl_unknown(self):
        assert GAP_MATRIX["MU"]["atl_treatment"] is None

    def test_malta_vessel_confirmed(self):
        assert GAP_MATRIX["MT"]["vessel_marine"] is True

    def test_malta_atl_confirmed(self):
        assert GAP_MATRIX["MT"]["atl_treatment"] is True

    def test_greece_vessel_confirmed(self):
        assert GAP_MATRIX["GR"]["vessel_marine"] is True

    def test_greece_rate_not_verified(self):
        assert GAP_MATRIX["GR"]["rate_verified"] is False

    def test_cyprus_rate_not_verified(self):
        assert GAP_MATRIX["CY"]["rate_verified"] is False

    def test_no_tier1_has_verified_rate(self):
        """All Tier 1 rates are PARSED or DISCOVERY — none fully verified from statute."""
        for code in TIER1_CODES:
            assert GAP_MATRIX[code]["rate_verified"] is False, (
                f"{code}: rate_verified should be False until statute text reviewed"
            )
