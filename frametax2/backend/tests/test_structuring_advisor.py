"""
test_structuring_advisor.py

Targeted tests for the Producer Structuring Advisor.
"""
import pytest

from app.calculators.structuring_advisor import (
    ADVISOR_VERSION,
    AuditRisk,
    ImplementationDifficulty,
    LittleUtopiaParams,
    RecommendationConfidence,
    StructuringAdvisoryResult,
    StructuringRecommendation,
    TimeHorizon,
    TransactionType,
    build_structuring_advisory,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def result() -> StructuringAdvisoryResult:
    return build_structuring_advisory()


@pytest.fixture(scope="module")
def params() -> LittleUtopiaParams:
    return LittleUtopiaParams()


@pytest.fixture(scope="module")
def recs(result) -> list[StructuringRecommendation]:
    return result.recommendations


def _get_rec(recs: list[StructuringRecommendation], rid: str) -> StructuringRecommendation:
    matches = [r for r in recs if r.recommendation_id == rid]
    assert matches, f"Recommendation {rid} not found"
    return matches[0]


# ── Advisory result structure ─────────────────────────────────────────────────

class TestAdvisoryResultStructure:
    def test_has_eleven_recommendations(self, recs):
        assert len(recs) == 11

    def test_advisor_version(self, result):
        assert result.advisor_version == ADVISOR_VERSION

    def test_jurisdiction(self, result):
        assert result.jurisdiction_code == "MU"

    def test_program_rate(self, result):
        assert result.program_rate == 0.35

    def test_production_title(self, result):
        assert "Little Utopia" in result.production_title

    def test_all_recommendation_ids_unique(self, recs):
        ids = [r.recommendation_id for r in recs]
        assert len(ids) == len(set(ids))

    def test_edb_questions_non_empty(self, result):
        assert len(result.edb_questions) >= 4

    def test_edb_questions_are_unique(self, result):
        assert len(result.edb_questions) == len(set(result.edb_questions))


# ── Aggregate financials ──────────────────────────────────────────────────────

class TestAggregateFinancials:
    def test_immediate_uplift_positive(self, result):
        assert result.total_immediate_rebate_uplift > 0

    def test_edb_conditional_uplift_positive(self, result):
        assert result.total_edb_conditional_rebate_uplift > 0

    def test_total_potential_uplift_equals_sum(self, result):
        expected = (
            result.total_immediate_rebate_uplift
            + result.total_medium_term_rebate_uplift
            + result.total_edb_conditional_rebate_uplift
        )
        assert abs(result.total_potential_rebate_uplift - expected) < 0.01

    def test_marine_and_crew_in_immediate_uplift(self, result):
        # R-06 ($39,200) + R-07 ($36,750) = $75,950 at minimum in immediate
        assert result.total_immediate_rebate_uplift >= 75_000

    def test_edb_conditional_includes_inkind(self, result, params):
        # In-kind FMV uplift alone: $625K × 35% = $218,750
        assert result.total_edb_conditional_rebate_uplift >= 218_750


# ── Recommendation sorting ────────────────────────────────────────────────────

class TestRecommendationSorting:
    def test_immediate_before_edb_first(self, recs):
        horizon_order = {
            TimeHorizon.IMMEDIATE: 0,
            TimeHorizon.EDB_FIRST: 1,
            TimeHorizon.MEDIUM_TERM: 2,
            TimeHorizon.LONG_TERM: 3,
        }
        for i in range(len(recs) - 1):
            a = horizon_order[recs[i].time_horizon]
            b = horizon_order[recs[i + 1].time_horizon]
            assert a <= b, (
                f"Horizon ordering violated at [{i}]={recs[i].recommendation_id} "
                f"(horizon={recs[i].time_horizon}) → [{i+1}]={recs[i+1].recommendation_id} "
                f"(horizon={recs[i+1].time_horizon})"
            )

    def test_within_same_horizon_sorted_by_roi(self, recs):
        """Within each horizon group, items should be sorted by rebate_impact descending."""
        horizon_order = {
            TimeHorizon.IMMEDIATE: 0,
            TimeHorizon.EDB_FIRST: 1,
            TimeHorizon.MEDIUM_TERM: 2,
            TimeHorizon.LONG_TERM: 3,
        }
        from itertools import groupby
        for horizon, group in groupby(recs, key=lambda r: r.time_horizon):
            group_list = list(group)
            for i in range(len(group_list) - 1):
                assert group_list[i].rebate_impact_usd >= group_list[i + 1].rebate_impact_usd, (
                    f"ROI ordering violated within {horizon}: "
                    f"{group_list[i].recommendation_id}=${group_list[i].rebate_impact_usd} "
                    f"before {group_list[i+1].recommendation_id}=${group_list[i+1].rebate_impact_usd}"
                )


# ── Individual recommendations ────────────────────────────────────────────────

class TestR01FrogsquadSPV:
    def test_recommendation_exists(self, recs):
        _get_rec(recs, "R-01")

    def test_transaction_type(self, recs):
        r = _get_rec(recs, "R-01")
        assert r.transaction_type == TransactionType.SPV_ROUTING

    def test_horizon_immediate(self, recs):
        r = _get_rec(recs, "R-01")
        assert r.time_horizon == TimeHorizon.IMMEDIATE

    def test_qpe_delta_matches_frogsquad_amount(self, recs, params):
        r = _get_rec(recs, "R-01")
        assert abs(r.qualification_impact_usd - params.frogsquad_usd) < 0.01

    def test_rebate_delta_matches_rate(self, recs, params):
        r = _get_rec(recs, "R-01")
        expected = params.frogsquad_usd * params.mu_rebate_rate
        assert abs(r.rebate_impact_usd - expected) < 0.01

    def test_requires_interpretation(self, recs):
        r = _get_rec(recs, "R-01")
        assert r.requires_official_interpretation is True
        assert r.interpretation_body == "Mauritius EDB"

    def test_confidence_industry_standard(self, recs):
        r = _get_rec(recs, "R-01")
        assert r.confidence == RecommendationConfidence.INDUSTRY_STANDARD

    def test_documentation_not_empty(self, recs):
        r = _get_rec(recs, "R-01")
        assert len(r.required_documentation) >= 3


class TestR02HodAccommodation:
    def test_horizon_edb_first(self, recs):
        r = _get_rec(recs, "R-02")
        assert r.time_horizon == TimeHorizon.EDB_FIRST

    def test_qpe_matches_hod_accom(self, recs, params):
        r = _get_rec(recs, "R-02")
        assert abs(r.qualification_impact_usd - params.hod_accom_usd) < 0.01

    def test_rebate_at_rate(self, recs, params):
        r = _get_rec(recs, "R-02")
        expected = params.hod_accom_usd * params.mu_rebate_rate
        assert abs(r.rebate_impact_usd - expected) < 0.01

    def test_confidence_requires_interpretation(self, recs):
        r = _get_rec(recs, "R-02")
        assert r.confidence == RecommendationConfidence.REQUIRES_INTERPRETATION

    def test_edb_question_about_accommodation(self, recs):
        r = _get_rec(recs, "R-02")
        assert r.interpretation_question is not None
        assert "accommodation" in r.interpretation_question.lower()


class TestR03PerDiem:
    def test_horizon_edb_first(self, recs):
        r = _get_rec(recs, "R-03")
        assert r.time_horizon == TimeHorizon.EDB_FIRST

    def test_qpe_matches_perdiem(self, recs, params):
        r = _get_rec(recs, "R-03")
        assert abs(r.qualification_impact_usd - params.local_perdiem_usd) < 0.01

    def test_confidence_requires_interpretation(self, recs):
        r = _get_rec(recs, "R-03")
        assert r.confidence == RecommendationConfidence.REQUIRES_INTERPRETATION

    def test_edb_question_about_perdiem(self, recs):
        r = _get_rec(recs, "R-03")
        assert r.interpretation_question is not None
        assert "per diem" in r.interpretation_question.lower()


class TestR04DeferredPayment:
    def test_is_fallback_structure(self, recs):
        """R-04 is the fallback if R-05 (FMV ruling) fails."""
        r = _get_rec(recs, "R-04")
        assert r.transaction_type == TransactionType.DEFERRED_PAYMENT

    def test_qpe_matches_inkind_base(self, recs, params):
        r = _get_rec(recs, "R-04")
        assert abs(r.qualification_impact_usd - params.inkind_base_usd) < 0.01

    def test_high_audit_risk(self, recs):
        r = _get_rec(recs, "R-04")
        assert r.audit_risk == AuditRisk.HIGH

    def test_requires_interpretation(self, recs):
        r = _get_rec(recs, "R-04")
        assert r.requires_official_interpretation is True


class TestR05InkindFMVRuling:
    def test_is_edb_ruling_request(self, recs):
        r = _get_rec(recs, "R-05")
        assert r.transaction_type == TransactionType.EDB_RULING_REQUEST

    def test_confidence_unknown(self, recs):
        r = _get_rec(recs, "R-05")
        assert r.confidence == RecommendationConfidence.UNKNOWN

    def test_is_in_unknown_items(self, result):
        assert any("In-kind" in item for item in result.unknown_items)

    def test_audit_risk_critical_without_ruling(self, recs):
        r = _get_rec(recs, "R-05")
        assert r.audit_risk == AuditRisk.CRITICAL

    def test_rebate_upside_matches_fmv(self, recs, params):
        r = _get_rec(recs, "R-05")
        expected = params.inkind_base_usd * params.mu_rebate_rate
        assert abs(r.rebate_impact_usd - expected) < 0.01

    def test_edb_question_covers_four_scenarios(self, recs):
        r = _get_rec(recs, "R-05")
        q = r.interpretation_question
        assert "(a)" in q
        assert "(b)" in q
        assert "(c)" in q
        assert "(d)" in q


class TestR06MarineExpansion:
    def test_explicitly_permitted(self, recs):
        r = _get_rec(recs, "R-06")
        assert r.confidence == RecommendationConfidence.EXPLICITLY_PERMITTED

    def test_no_edb_required(self, recs):
        r = _get_rec(recs, "R-06")
        assert r.requires_official_interpretation is False

    def test_low_audit_risk(self, recs):
        r = _get_rec(recs, "R-06")
        assert r.audit_risk == AuditRisk.LOW

    def test_rebate_delta_at_35pct(self, recs, params):
        r = _get_rec(recs, "R-06")
        expected = r.qualification_impact_usd * params.mu_rebate_rate
        assert abs(r.rebate_impact_usd - expected) < 0.01

    def test_immediate_horizon(self, recs):
        r = _get_rec(recs, "R-06")
        assert r.time_horizon == TimeHorizon.IMMEDIATE


class TestR07LocalCrew:
    def test_explicitly_permitted(self, recs):
        r = _get_rec(recs, "R-07")
        assert r.confidence == RecommendationConfidence.EXPLICITLY_PERMITTED

    def test_no_edb_required(self, recs):
        r = _get_rec(recs, "R-07")
        assert r.requires_official_interpretation is False

    def test_low_audit_risk(self, recs):
        r = _get_rec(recs, "R-07")
        assert r.audit_risk == AuditRisk.LOW

    def test_immediate_horizon(self, recs):
        r = _get_rec(recs, "R-07")
        assert r.time_horizon == TimeHorizon.IMMEDIATE


class TestR10RelatedPartyDisclosure:
    def test_zero_financial_impact(self, recs):
        """R-10 is protective — no direct rebate but must be implemented."""
        r = _get_rec(recs, "R-10")
        assert r.financial_impact_usd == 0.0
        assert r.rebate_impact_usd == 0.0

    def test_explicitly_permitted(self, recs):
        r = _get_rec(recs, "R-10")
        assert r.confidence == RecommendationConfidence.EXPLICITLY_PERMITTED

    def test_no_edb_interpretation_required(self, recs):
        r = _get_rec(recs, "R-10")
        assert r.requires_official_interpretation is False

    def test_is_in_immediate_horizon(self, recs):
        r = _get_rec(recs, "R-10")
        assert r.time_horizon == TimeHorizon.IMMEDIATE


class TestR11PreProductionMeeting:
    def test_highest_financial_impact_in_immediate(self, recs):
        """R-11 umbrella action should have the highest financial_impact among immediates."""
        immediate = [r for r in recs if r.time_horizon == TimeHorizon.IMMEDIATE]
        r11 = _get_rec(recs, "R-11")
        max_impact = max(r.financial_impact_usd for r in immediate)
        assert r11.financial_impact_usd == max_impact

    def test_low_difficulty(self, recs):
        r = _get_rec(recs, "R-11")
        assert r.implementation_difficulty == ImplementationDifficulty.LOW

    def test_low_audit_risk(self, recs):
        r = _get_rec(recs, "R-11")
        assert r.audit_risk == AuditRisk.LOW

    def test_industry_standard_confidence(self, recs):
        r = _get_rec(recs, "R-11")
        assert r.confidence == RecommendationConfidence.INDUSTRY_STANDARD


# ── Little Utopia params ──────────────────────────────────────────────────────

class TestLittleUtopiaParams:
    def test_default_mu_rate(self):
        p = LittleUtopiaParams()
        assert p.mu_rebate_rate == 0.35

    def test_default_inkind_base(self):
        p = LittleUtopiaParams()
        assert p.inkind_base_usd == 625_000

    def test_team_nationalities(self):
        p = LittleUtopiaParams()
        assert p.writer_nationality == "GB"
        assert p.director_nationality == "AU"
        assert p.lead_nationality == "GB"
        assert "GB" in p.producer_nationalities
        assert "CA" in p.producer_nationalities
        assert "US" in p.producer_nationalities

    def test_custom_params_flow_through(self):
        p = LittleUtopiaParams(mu_rebate_rate=0.40)
        result = build_structuring_advisory(p)
        assert result.program_rate == 0.40
        # R-06 marine rebate should scale with new rate
        r6 = next(r for r in result.recommendations if r.recommendation_id == "R-06")
        expected = r6.qualification_impact_usd * 0.40
        assert abs(r6.rebate_impact_usd - expected) < 0.01


# ── Module constants ──────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_advisor_version(self):
        assert ADVISOR_VERSION == "1.0.0"

    def test_transaction_type_count(self):
        assert len(TransactionType) >= 15

    def test_recommendation_confidence_count(self):
        assert len(RecommendationConfidence) == 4

    def test_time_horizon_count(self):
        assert len(TimeHorizon) == 4
