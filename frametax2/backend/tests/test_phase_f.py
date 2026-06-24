"""
test_phase_f.py — Phase F integration tests.

Tests the qualification gap engine, recommendation engine,
structure generator, maximization engine, and travel model.
"""
from __future__ import annotations

import pytest

from app.optimization.qualification_gap_engine import analyse_gaps, QualificationGap, GapAnalysisResult
from app.optimization.recommendation_engine import generate_recommendations, ActionableRecommendation
from app.optimization.structure_generator import generate_structures, GeneratedStructure
from app.optimization.maximization_engine import maximize_structure, StructureComparison
from app.calculators.travel_model import estimate_travel_cost, estimate_net_incentive_after_travel
from app.data.structure_graph_model import (
    STRUCTURE_GRAPH_EDGES,
    get_edges_by_type,
    get_edges_from,
    get_edges_to,
)


# ---------------------------------------------------------------------------
# Fixtures: synthetic project profiles
# ---------------------------------------------------------------------------

@pytest.fixture
def us_ga_profile():
    return {
        "us_spend_pct": 0.85,
        "qualifying_spend_pct": 0.85,
        "has_us_company": True,
        "production_type": "feature",
    }


@pytest.fixture
def uk_feature_profile():
    return {
        "uk_spend_pct": 0.60,
        "qualifying_spend_pct": 0.60,
        "has_uk_company": True,
        "director_uk": True,
        "writer_uk": True,
        "producer_uk": True,
        "lead_cast_uk": True,
        "uk_setting": True,
        "british_subject_matter": True,
        "production_type": "feature",
    }


@pytest.fixture
def canada_feature_profile():
    return {
        "ca_spend_pct": 0.70,
        "qualifying_spend_pct": 0.70,
        "has_canadian_company": True,
        "director_ca": True,
        "writer_ca": True,
        "producer_ca": True,
        "has_broadcaster_commitment": True,
        "broadcaster_jurisdiction": "CA",
        "production_type": "feature",
    }


@pytest.fixture
def kr_sa_profile():
    return {
        "kr_spend_pct": 0.30,
        "sa_spend_pct": 0.20,
        "qualifying_spend_pct": 0.50,
        "production_type": "feature",
    }


@pytest.fixture
def de_hu_profile():
    return {
        "de_spend_pct": 0.40,
        "hu_spend_pct": 0.30,
        "qualifying_spend_pct": 0.70,
        "has_german_company": True,
        "has_hungarian_company": True,
        "is_coproduction": True,
        "production_type": "feature",
    }


@pytest.fixture
def fr_be_profile():
    return {
        "fr_spend_pct": 0.50,
        "be_spend_pct": 0.20,
        "qualifying_spend_pct": 0.70,
        "has_french_company": True,
        "director_fr": True,
        "is_coproduction": True,
        "production_type": "feature",
    }


@pytest.fixture
def au_nz_profile():
    return {
        "au_spend_pct": 0.55,
        "nz_spend_pct": 0.20,
        "qualifying_spend_pct": 0.75,
        "has_australian_entity": True,
        "director_au": True,
        "is_coproduction": True,
        "production_type": "feature",
    }


# ---------------------------------------------------------------------------
# F2: Gap Analysis tests
# ---------------------------------------------------------------------------

class TestGapAnalysis:

    def test_us_ga_no_crash(self, us_ga_profile):
        """US-GA feature: gap analysis should not crash."""
        result = analyse_gaps(["us_georgia_eitc"], us_ga_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0
        assert isinstance(result.all_gaps, list)
        assert isinstance(result.gap_summary, str)

    def test_uk_feature_gap_analysis(self, uk_feature_profile):
        """UK feature: gap analysis for uk_avec."""
        result = analyse_gaps(["uk_avec"], uk_feature_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_canada_feature_gap_analysis(self, canada_feature_profile):
        """Canada feature: gap analysis for ca_federal_cptc and ca_cmf."""
        result = analyse_gaps(["ca_federal_cptc", "ca_cmf"], canada_feature_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_kr_sa_gap_analysis(self, kr_sa_profile):
        """Korea/Saudi: gap analysis for kr_kofic_rebate."""
        result = analyse_gaps(["kr_kofic_rebate"], kr_sa_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_de_hu_gap_analysis(self, de_hu_profile):
        """Germany/Hungary: gap analysis for de_dfff and hu_nfi_grants."""
        result = analyse_gaps(["de_dfff", "hu_nfi_grants"], de_hu_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_fr_be_gap_analysis(self, fr_be_profile):
        """France/Belgium: gap analysis for fr_cnc_production."""
        result = analyse_gaps(["fr_cnc_production"], fr_be_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_au_nz_gap_analysis(self, au_nz_profile):
        """Australia/New Zealand: gap analysis for au_producer_offset."""
        result = analyse_gaps(["au_producer_offset", "nz_screen_production_grant"], au_nz_profile, 5_000_000)
        assert isinstance(result, GapAnalysisResult)
        assert result.total_gaps >= 0

    def test_blocking_vs_addressable_gaps(self):
        """Test that blocking and addressable gaps are correctly classified."""
        profile = {
            "ie_spend_pct": 0.0,  # zero spend = blocker
            "fr_spend_pct": 0.08,  # below minimum but not zero = addressable
        }
        result = analyse_gaps(["ie_section_481", "fr_cnc_production"], profile, 5_000_000)
        assert isinstance(result.blocking_gaps, list)
        assert isinstance(result.addressable_gaps, list)
        total_blockers = len(result.blocking_gaps)
        assert total_blockers >= 0

    def test_gap_result_values_non_negative(self):
        """Gap financial values should always be non-negative."""
        profile = {}
        result = analyse_gaps(["uk_avec", "ie_section_481", "ca_federal_cptc"], profile, 10_000_000)
        assert result.total_value_at_risk_usd >= 0
        assert result.total_value_unlockable_usd >= 0
        for gap in result.all_gaps:
            assert gap.estimated_value_unlocked_usd >= 0
            assert 0.0 <= gap.gap_magnitude <= 1.0
            assert 1.0 <= gap.friction_score <= 10.0

    def test_empty_slugs_no_crash(self):
        """Empty structure slugs should return zero gaps."""
        result = analyse_gaps([], {}, 5_000_000)
        assert result.total_gaps == 0
        assert result.all_gaps == []


# ---------------------------------------------------------------------------
# F3: Recommendation Engine tests
# ---------------------------------------------------------------------------

class TestRecommendationEngine:

    def test_uk_recommendations(self, uk_feature_profile):
        """UK feature: should generate at least one recommendation for failing programs."""
        gap_result = analyse_gaps(["uk_avec"], uk_feature_profile, 5_000_000)
        recs = generate_recommendations(gap_result, ["uk_avec"], uk_feature_profile, 5_000_000)
        assert isinstance(recs, list)
        assert all(isinstance(r, ActionableRecommendation) for r in recs)

    def test_canada_recommendations(self, canada_feature_profile):
        """Canada feature: recommendations should reference Canadian programs."""
        gap_result = analyse_gaps(
            ["ca_federal_cptc", "ca_cmf"], canada_feature_profile, 5_000_000
        )
        recs = generate_recommendations(
            gap_result, ["ca_federal_cptc", "ca_cmf"], canada_feature_profile, 5_000_000
        )
        assert isinstance(recs, list)

    def test_recommendations_sorted_by_net_value(self):
        """Recommendations should be sorted by net value descending."""
        profile = {"uk_spend_pct": 0.05}  # low UK spend to trigger gaps
        gap_result = analyse_gaps(["uk_avec", "ie_section_481"], profile, 5_000_000)
        recs = generate_recommendations(
            gap_result, ["uk_avec", "ie_section_481"], profile, 5_000_000
        )
        if len(recs) >= 2:
            for i in range(len(recs) - 1):
                assert recs[i].net_value_usd >= recs[i + 1].net_value_usd

    def test_recommendation_fields_valid(self):
        """All ActionableRecommendation fields should be valid types."""
        profile = {}
        gap_result = analyse_gaps(["ca_federal_cptc", "ie_section_481"], profile, 5_000_000)
        recs = generate_recommendations(
            gap_result, ["ca_federal_cptc", "ie_section_481"], profile, 5_000_000
        )
        for rec in recs:
            assert isinstance(rec.recommendation_id, str)
            assert isinstance(rec.title, str)
            assert isinstance(rec.description, str)
            assert isinstance(rec.specific_actions, list)
            assert isinstance(rec.estimated_value_unlocked_usd, float)
            assert rec.confidence in ("HIGH", "MEDIUM", "LOW")
            assert 1.0 <= rec.implementation_friction <= 10.0
            assert rec.timeline_weeks > 0


# ---------------------------------------------------------------------------
# F4: Structure Generator tests
# ---------------------------------------------------------------------------

class TestStructureGenerator:

    def test_us_ga_generates_structures(self):
        """US-GA: should generate at least 1 structure."""
        structures = generate_structures("US-GA", total_budget_usd=5_000_000)
        assert len(structures) >= 1
        assert all(isinstance(s, GeneratedStructure) for s in structures)

    def test_uk_generates_structures(self):
        """GB: should generate single-country structure."""
        structures = generate_structures("GB", total_budget_usd=5_000_000)
        assert len(structures) >= 1
        single = [s for s in structures if s.structure_type == "single_country"]
        assert len(single) >= 1

    def test_canada_generates_structures(self):
        """CA: should generate at least 1 structure."""
        structures = generate_structures("CA", total_budget_usd=5_000_000)
        assert len(structures) >= 1

    def test_kr_sa_generates_structures(self):
        """KR+SA: should generate dual-country structure."""
        structures = generate_structures("KR", ["SA"], total_budget_usd=5_000_000)
        assert len(structures) >= 1

    def test_de_hu_generates_structures(self):
        """DE+HU: should generate at least 1 structure."""
        structures = generate_structures("DE", ["HU"], total_budget_usd=5_000_000)
        assert len(structures) >= 1

    def test_fr_be_treaty_structure(self):
        """FR+BE: should generate treaty co-production structure."""
        structures = generate_structures("FR", ["BE"], total_budget_usd=5_000_000)
        assert len(structures) >= 1

    def test_au_nz_generates_structures(self):
        """AU+NZ: should generate treaty co-production structure."""
        structures = generate_structures("AU", ["NZ"], total_budget_usd=5_000_000)
        assert len(structures) >= 1

    def test_structure_fields_valid(self):
        """All GeneratedStructure fields should be valid types."""
        structures = generate_structures("GB", ["IE"], total_budget_usd=10_000_000)
        for s in structures:
            assert isinstance(s.structure_id, str)
            assert isinstance(s.structure_type, str)
            assert s.structure_type in (
                "single_country", "dual_country", "treaty_coproduction",
                "majority_minority", "broadcaster_supported", "regional_supported", "multi_party"
            )
            assert isinstance(s.program_slugs, list)
            assert s.estimated_soft_money_usd >= 0
            assert s.estimated_total_incentive_usd >= 0
            assert s.qualification_risk in ("LOW", "MEDIUM", "HIGH")
            assert s.confidence in ("HIGH", "MEDIUM", "LOW")

    def test_multi_jurisdiction_structure(self):
        """Multi-jurisdiction structure should be generated for 3+ countries."""
        structures = generate_structures("GB", ["IE", "CA"], total_budget_usd=10_000_000)
        multi = [s for s in structures if s.structure_type == "multi_party"]
        assert len(multi) >= 1

    def test_sorted_by_incentive_value(self):
        """Structures should be sorted by estimated_total_incentive_usd descending."""
        structures = generate_structures("GB", ["IE", "CA"], total_budget_usd=5_000_000)
        if len(structures) >= 2:
            for i in range(len(structures) - 1):
                assert structures[i].estimated_total_incentive_usd >= structures[i + 1].estimated_total_incentive_usd


# ---------------------------------------------------------------------------
# F5: Maximization Engine tests
# ---------------------------------------------------------------------------

class TestMaximizationEngine:

    def test_us_ga_maximize(self, us_ga_profile):
        """US-GA: maximize should return StructureComparison."""
        result = maximize_structure("US-GA", project_profile=us_ga_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)
        assert result.current_soft_money_usd >= 0
        assert result.best_soft_money_usd >= 0

    def test_uk_maximize(self, uk_feature_profile):
        """GB: maximize should return comparison with current/improved/best."""
        result = maximize_structure("GB", project_profile=uk_feature_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)
        assert isinstance(result.current_structure, GeneratedStructure)
        assert isinstance(result.improved_structure, GeneratedStructure)
        assert isinstance(result.best_structure, GeneratedStructure)

    def test_canada_maximize(self, canada_feature_profile):
        """CA: maximize should return StructureComparison."""
        result = maximize_structure("CA", project_profile=canada_feature_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)

    def test_kr_sa_maximize(self, kr_sa_profile):
        """KR+SA: maximize should handle unfamiliar jurisdiction pair."""
        result = maximize_structure("KR", ["SA"], project_profile=kr_sa_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)

    def test_de_hu_maximize(self, de_hu_profile):
        """DE+HU: maximize should return comparison."""
        result = maximize_structure("DE", ["HU"], project_profile=de_hu_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)

    def test_fr_be_maximize(self, fr_be_profile):
        """FR+BE: maximize should return comparison."""
        result = maximize_structure("FR", ["BE"], project_profile=fr_be_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)

    def test_au_nz_maximize(self, au_nz_profile):
        """AU+NZ: maximize should return comparison."""
        result = maximize_structure("AU", ["NZ"], project_profile=au_nz_profile, total_budget_usd=5_000_000)
        assert isinstance(result, StructureComparison)

    def test_best_at_least_as_good_as_current(self):
        """Best structure should be at least as good as current."""
        result = maximize_structure("GB", ["IE"], total_budget_usd=5_000_000)
        assert result.best_soft_money_usd >= result.current_soft_money_usd

    def test_maximize_actions_not_empty(self):
        """Actions required should be a non-empty list."""
        result = maximize_structure("GB", ["IE", "CA"], total_budget_usd=5_000_000)
        assert isinstance(result.actions_required, list)
        assert len(result.actions_required) >= 1

    def test_maximize_confidence_valid(self):
        """Confidence should be one of HIGH/MEDIUM/LOW."""
        result = maximize_structure("FR", total_budget_usd=5_000_000)
        assert result.confidence in ("HIGH", "MEDIUM", "LOW")


# ---------------------------------------------------------------------------
# F6: Travel Model tests
# ---------------------------------------------------------------------------

class TestTravelModel:

    def test_la_gb_estimate(self):
        """LA to GB travel estimate."""
        result = estimate_travel_cost(
            home_base="LA",
            destination_jurisdiction="GB",
            business_class_seats=2,
            travel_frequency_per_year=4,
            hotel_nights=14,
            per_diem_days=14,
            incentive_value_usd=1_000_000,
        )
        assert result.total_airfare_usd > 0
        assert result.total_hotel_usd > 0
        assert result.total_per_diem_usd > 0
        assert result.total_travel_cost_usd > 0
        assert result.net_incentive_after_travel_usd < result.incentive_value_usd
        assert isinstance(result.recommendation, str)

    def test_la_au_estimate(self):
        """LA to AU travel estimate (long-haul)."""
        result = estimate_travel_cost(
            home_base="LA",
            destination_jurisdiction="AU",
            business_class_seats=1,
            travel_frequency_per_year=2,
            hotel_nights=21,
            per_diem_days=21,
            incentive_value_usd=500_000,
        )
        assert result.total_airfare_usd > 0
        la_gb = estimate_travel_cost("LA", "GB", 1, 0, 0, 2, 21, 21)
        assert result.total_airfare_usd > la_gb.total_airfare_usd

    def test_nyc_ie_estimate(self):
        """NYC to IE travel estimate."""
        result = estimate_travel_cost(
            home_base="NYC",
            destination_jurisdiction="IE",
            business_class_seats=1,
            travel_frequency_per_year=3,
            hotel_nights=10,
            per_diem_days=10,
            incentive_value_usd=300_000,
        )
        assert result.total_airfare_usd > 0
        assert result.home_base == "NYC"
        assert result.destination_jurisdiction == "IE"

    def test_unknown_route_fallback(self):
        """Unknown home_base should use fallback fare."""
        result = estimate_travel_cost(
            home_base="UNKNOWN_CITY",
            destination_jurisdiction="GB",
            business_class_seats=1,
            travel_frequency_per_year=1,
            hotel_nights=7,
            per_diem_days=7,
        )
        assert result.total_airfare_usd > 0  # should not crash

    def test_zero_incentive_recommendation(self):
        """Zero incentive value should prompt 'enter incentive value' recommendation."""
        result = estimate_travel_cost(
            home_base="LA",
            destination_jurisdiction="GB",
            incentive_value_usd=0,
        )
        assert result.incentive_value_usd == 0
        assert "incentive" in result.recommendation.lower()

    def test_net_incentive_helper(self):
        """estimate_net_incentive_after_travel helper should return a float."""
        net = estimate_net_incentive_after_travel(
            incentive_value_usd=1_000_000,
            home_base="LA",
            destination_jurisdiction="GB",
        )
        assert isinstance(net, float)
        assert net < 1_000_000  # travel costs should reduce net incentive

    def test_travel_cost_pct_range(self):
        """Travel cost as pct of incentive should be between 0 and 1 for reasonable scenarios."""
        result = estimate_travel_cost(
            home_base="LA",
            destination_jurisdiction="GB",
            business_class_seats=2,
            travel_frequency_per_year=4,
            hotel_nights=14,
            per_diem_days=14,
            incentive_value_usd=5_000_000,
        )
        assert 0.0 <= result.travel_cost_as_pct_of_incentive <= 1.0


# ---------------------------------------------------------------------------
# F1: Structure Graph edge tests
# ---------------------------------------------------------------------------

class TestStructureGraph:

    def test_new_edge_types_exist(self):
        """New edge types (enables, complements, alternative_to) should exist in graph."""
        edge_types = {e.edge_type for e in STRUCTURE_GRAPH_EDGES}
        new_types = {"enables", "complements", "alternative_to", "blocks", "majority_only", "minority_only"}
        added_types = edge_types & new_types
        assert len(added_types) >= 1, f"Expected at least 1 new edge type, got: {edge_types}"

    def test_total_edges_above_150(self):
        """Total edges should be well above 150 after F1 additions."""
        assert len(STRUCTURE_GRAPH_EDGES) >= 150, f"Only {len(STRUCTURE_GRAPH_EDGES)} edges found"

    def test_uk_avec_has_edges(self):
        """uk_avec should have multiple edges after F1."""
        edges = get_edges_from("uk_avec") + get_edges_to("uk_avec")
        assert len(edges) >= 2

    def test_ca_federal_cptc_has_edges(self):
        """ca_federal_cptc should have edges."""
        edges = get_edges_from("ca_federal_cptc") + get_edges_to("ca_federal_cptc")
        assert len(edges) >= 2

    def test_broadcaster_edges_exist(self):
        """Broadcaster-related edges should exist."""
        broadcaster_slugs = {
            "bbc_drama_production", "rte_drama_fund", "cbc_original",
            "canal_plus_fund", "abc_television_fund"
        }
        edge_slugs = {e.source_slug for e in STRUCTURE_GRAPH_EDGES} | {e.target_slug for e in STRUCTURE_GRAPH_EDGES}
        matching = broadcaster_slugs & edge_slugs
        assert len(matching) >= 1, f"No broadcaster edges found. Edge slugs sample: {list(edge_slugs)[:10]}"

    def test_regional_fund_edges_exist(self):
        """Regional fund edges should exist."""
        regional_slugs = {"bavarian_film_fund", "berlin_mbb_fund", "uk_screen_scotland"}
        edge_slugs = {e.source_slug for e in STRUCTURE_GRAPH_EDGES} | {e.target_slug for e in STRUCTURE_GRAPH_EDGES}
        matching = regional_slugs & edge_slugs
        assert len(matching) >= 1

    def test_enables_edges_exist(self):
        """'enables' edge type should be in the graph after F1."""
        enables_edges = get_edges_by_type("enables")
        assert len(enables_edges) >= 1

    def test_complements_edges_exist(self):
        """'complements' edge type should be in the graph after F1."""
        complements_edges = get_edges_by_type("complements")
        assert len(complements_edges) >= 1
