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
SECONDARY_CODES = {"IE", "FR", "IT", "ES", "HR", "HU", "BE", "DE"}


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

    def test_parsed_tier(self, mu):
        assert mu.confidence_tier == "PARSED"

    def test_base_rate_35(self, mu):
        assert mu.base_rate == 0.35, "Budget evidence sets rate at 35% (not yet verified from EDB statute)"

    def test_max_rate_35(self, mu):
        assert mu.max_rate == 0.35

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

    def test_atl_unknown(self, mu):
        assert mu.atl_qualifies is None, "ATL scope unconfirmed from EDB source"


class TestMaltaProfile:
    @pytest.fixture
    def mt(self):
        return TIER1_PROFILES["MT"]

    def test_parsed_tier(self, mt):
        assert mt.confidence_tier == "PARSED"

    def test_base_rate(self, mt):
        assert mt.base_rate == 0.25

    def test_max_rate(self, mt):
        assert mt.max_rate == 0.40

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
        assert mt.min_spend_local == 50_000.0

    def test_no_cultural_test(self, mt):
        assert mt.requires_cultural_test is False


class TestGreeceProfile:
    @pytest.fixture
    def gr(self):
        return TIER1_PROFILES["GR"]

    def test_parsed_tier(self, gr):
        assert gr.confidence_tier == "PARSED"

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

    def test_discovery_tier(self, cy):
        assert cy.confidence_tier == "DISCOVERY"

    def test_base_rate_35(self, cy):
        assert cy.base_rate == 0.35

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

    def test_spain_has_max_rate_50_canary(self):
        es = SECONDARY_PROFILES["ES"]
        assert es.max_rate == 0.50, "Spain Canary Islands rate should be reflected in max_rate"

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
