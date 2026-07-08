"""
test_inkind_contribution.py

Targeted tests for the in-kind contribution treatment model.
Covers all five QPE scenarios, factory function, budget modification
opportunities, and MU vs Malta post comparison.
"""
import pytest

from app.calculators.inkind_contribution import (
    CALCULATOR_VERSION,
    INTERNATIONAL_PRECEDENTS,
    AuditRisk,
    BudgetModificationOpportunity,
    ContributionType,
    InKindContribution,
    InKindImpactResult,
    PostJurisdictionComparison,
    QPEScenario,
    QualifyingTreatment,
    SourceConfidence,
    analyse_inkind_contribution,
    build_lu_budget_modifications,
    compare_mu_vs_malta_post,
    make_post_inkind_contribution,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def free_service() -> InKindContribution:
    """Fully-free in-kind service (cash_paid=$0, FMV=$625K)."""
    return InKindContribution(
        contribution_type=ContributionType.IN_KIND_SERVICE,
        description="MU post-production services",
        face_value_usd=625_000,
        cash_paid_usd=0.0,
        fair_market_value_usd=625_000,
        qualifying_treatment=QualifyingTreatment.UNKNOWN,
        requires_invoice=True,
        requires_payment_proof=False,
        requires_fmv_support=True,
        requires_related_party_disclosure=True,
        source_confidence=SourceConfidence.UNKNOWN,
    )


@pytest.fixture
def partial_cash_service() -> InKindContribution:
    """Discounted service where some cash was paid."""
    return InKindContribution(
        contribution_type=ContributionType.VENDOR_DISCOUNT,
        description="Discounted sound studio",
        face_value_usd=100_000,
        cash_paid_usd=60_000,
        fair_market_value_usd=100_000,
        qualifying_treatment=QualifyingTreatment.UNKNOWN,
        requires_invoice=True,
        requires_payment_proof=True,
        requires_fmv_support=False,
        requires_related_party_disclosure=False,
        source_confidence=SourceConfidence.LOW,
    )


@pytest.fixture
def lu_base_qpe() -> float:
    return 2_500_000.0


@pytest.fixture
def mu_rate() -> float:
    return 0.35


# ── InKindContribution properties ─────────────────────────────────────────────

class TestInKindContributionProperties:
    def test_discount_usd_fully_free(self, free_service):
        assert free_service.discount_usd == 625_000.0

    def test_discount_usd_partial(self, partial_cash_service):
        assert partial_cash_service.discount_usd == 40_000.0

    def test_is_fully_free_true(self, free_service):
        assert free_service.is_fully_free is True

    def test_is_fully_free_false(self, partial_cash_service):
        assert partial_cash_service.is_fully_free is False

    def test_discount_usd_no_discount(self):
        c = InKindContribution(
            contribution_type=ContributionType.CASH_REINVESTMENT,
            description="cash at full rate",
            face_value_usd=50_000,
            cash_paid_usd=50_000,
            fair_market_value_usd=50_000,
            qualifying_treatment=QualifyingTreatment.QUALIFIES_AT_CASH_PAID,
            requires_invoice=True,
            requires_payment_proof=True,
            requires_fmv_support=False,
            requires_related_party_disclosure=False,
            source_confidence=SourceConfidence.MEDIUM,
        )
        assert c.discount_usd == 0.0


# ── analyse_inkind_contribution — five scenarios ───────────────────────────────

class TestAnalyseInkindContribution:
    def test_returns_five_scenarios(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert len(result.scenarios) == 5

    def test_scenario_ids(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        ids = [s.scenario_id for s in result.scenarios]
        assert ids == ["A", "B", "C", "D", "E"]

    def test_recommended_scenario_always_e(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert result.recommended_scenario == "E"

    def test_edb_ruling_required(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert result.edb_ruling_required is True

    def test_international_precedents_populated(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert len(result.international_precedents) >= 6
        # Mauritius entry must be present
        assert any("Mauritius" in p for p in result.international_precedents)

    def test_required_edb_questions_non_empty(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert len(result.required_edb_questions) >= 5

    def test_documentation_checklist_non_empty(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        assert len(result.documentation_checklist) >= 3

    # Scenario A — Excluded
    def test_scenario_a_excluded_qpe_zero(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        a = next(s for s in result.scenarios if s.scenario_id == "A")
        assert a.qpe_amount_usd == 0.0
        assert a.rebate_impact_usd == 0.0
        assert a.treatment == QualifyingTreatment.EXCLUDED
        assert a.audit_risk == AuditRisk.LOW

    # Scenario B — Cash paid only ($0 for fully free)
    def test_scenario_b_cash_paid_zero_for_free_service(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        b = next(s for s in result.scenarios if s.scenario_id == "B")
        assert b.qpe_amount_usd == 0.0
        assert b.rebate_impact_usd == 0.0
        assert b.treatment == QualifyingTreatment.QUALIFIES_AT_CASH_PAID
        assert b.audit_risk == AuditRisk.LOW

    def test_scenario_b_cash_paid_partial(self, partial_cash_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(partial_cash_service, mu_rate, lu_base_qpe)
        b = next(s for s in result.scenarios if s.scenario_id == "B")
        assert b.qpe_amount_usd == 60_000.0
        assert abs(b.rebate_impact_usd - 60_000 * mu_rate) < 0.01
        assert b.audit_risk == AuditRisk.MEDIUM

    # Scenario C — FMV
    def test_scenario_c_fmv(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        c = next(s for s in result.scenarios if s.scenario_id == "C")
        assert c.qpe_amount_usd == 625_000.0
        assert abs(c.rebate_impact_usd - 625_000 * mu_rate) < 0.01
        assert c.treatment == QualifyingTreatment.QUALIFIES_AT_FMV
        assert c.audit_risk == AuditRisk.HIGH

    def test_scenario_c_requires_edb_question(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        c = next(s for s in result.scenarios if s.scenario_id == "C")
        assert any("EDB" in q for q in c.edb_questions)

    # Scenario D — Reduces QPE
    def test_scenario_d_reduces_qpe(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        d = next(s for s in result.scenarios if s.scenario_id == "D")
        # qpe_amount is negative (reduction)
        assert d.qpe_amount_usd == -625_000.0
        # rebate_impact is negative (reduces rebate)
        assert d.rebate_impact_usd < 0
        assert d.treatment == QualifyingTreatment.REDUCES_QPE

    def test_scenario_d_rebate_impact_matches_reduction(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        d = next(s for s in result.scenarios if s.scenario_id == "D")
        expected = (lu_base_qpe - 625_000) * mu_rate - lu_base_qpe * mu_rate
        assert abs(d.rebate_impact_usd - expected) < 0.01

    def test_scenario_d_qpe_floor_zero(self, mu_rate):
        """When FMV > base QPE the adjusted QPE floors at zero."""
        tiny_qpe = 100_000.0
        large_inkind = InKindContribution(
            contribution_type=ContributionType.GOVERNMENT_GRANT,
            description="large govt grant",
            face_value_usd=500_000,
            cash_paid_usd=0.0,
            fair_market_value_usd=500_000,
            qualifying_treatment=QualifyingTreatment.UNKNOWN,
            requires_invoice=False,
            requires_payment_proof=False,
            requires_fmv_support=True,
            requires_related_party_disclosure=False,
            source_confidence=SourceConfidence.LOW,
        )
        result = analyse_inkind_contribution(large_inkind, mu_rate, tiny_qpe)
        d = next(s for s in result.scenarios if s.scenario_id == "D")
        # Adjusted QPE = max(0, 100K - 500K) = 0
        expected_rebate_impact = 0.0 * mu_rate - tiny_qpe * mu_rate  # -35000
        assert abs(d.rebate_impact_usd - expected_rebate_impact) < 0.01

    # Scenario E — Unknown
    def test_scenario_e_unknown_treatment(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        e = next(s for s in result.scenarios if s.scenario_id == "E")
        assert e.treatment == QualifyingTreatment.UNKNOWN
        assert e.qpe_amount_usd == 0.0
        assert e.rebate_impact_usd == 0.0
        assert e.audit_risk == AuditRisk.CRITICAL

    def test_scenario_e_has_edb_questions(self, free_service, mu_rate, lu_base_qpe):
        result = analyse_inkind_contribution(free_service, mu_rate, lu_base_qpe)
        e = next(s for s in result.scenarios if s.scenario_id == "E")
        assert len(e.edb_questions) >= 4


# ── make_post_inkind_contribution factory ────────────────────────────────────

class TestMakePostInkindContribution:
    def test_base_values(self):
        c = make_post_inkind_contribution(625_000)
        assert c.face_value_usd == 625_000
        assert c.cash_paid_usd == 0.0
        assert c.fair_market_value_usd == 625_000
        assert c.contribution_type == ContributionType.IN_KIND_SERVICE
        assert c.qualifying_treatment == QualifyingTreatment.UNKNOWN
        assert c.source_confidence == SourceConfidence.UNKNOWN

    def test_requires_flags(self):
        c = make_post_inkind_contribution(500_000)
        assert c.requires_invoice is True
        assert c.requires_payment_proof is False
        assert c.requires_fmv_support is True
        assert c.requires_related_party_disclosure is True

    def test_low_range(self):
        c = make_post_inkind_contribution(500_000, "LU post low scenario")
        assert c.face_value_usd == 500_000
        assert c.is_fully_free is True
        assert c.discount_usd == 500_000

    def test_high_range(self):
        c = make_post_inkind_contribution(750_000)
        assert c.fair_market_value_usd == 750_000

    def test_custom_description(self):
        c = make_post_inkind_contribution(625_000, "Custom post deal")
        assert c.description == "Custom post deal"


# ── build_lu_budget_modifications ────────────────────────────────────────────

class TestBuildLuBudgetModifications:
    def test_without_edb_confirmations(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=False)
        # Should NOT include post-production opportunities
        codes = [o.account_code for o in opps]
        assert "54-00" not in codes
        assert "51-00" not in codes

    def test_with_edb_post_confirmation(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=True)
        codes = [o.account_code for o in opps]
        # Post accounts should be present
        assert "54-00" in codes
        assert "51-00" in codes
        assert "52-00" in codes
        assert "53-00" in codes

    def test_marine_always_present(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=False)
        codes = [o.account_code for o in opps]
        assert "31-00" in codes
        assert "32-00" in codes
        assert "34-00" in codes

    def test_incremental_rebate_calculation(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=False)
        for o in opps:
            expected = o.candidate_additional_usd * 0.35
            assert abs(o.incremental_rebate_at_rate - expected) < 0.01

    def test_no_edb_items_have_low_risk(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=False)
        no_edb = [o for o in opps if not o.depends_on_edb_confirmation]
        for o in no_edb:
            assert o.audit_risk == AuditRisk.LOW

    def test_accommodation_excluded_when_confirmed(self):
        opps = build_lu_budget_modifications(
            0.35, edb_confirms_accommodation=True, edb_confirms_post_as_qpe=False
        )
        codes = [o.account_code for o in opps]
        assert "37-00" not in codes
        assert "38-00" not in codes

    def test_accommodation_included_when_not_confirmed(self):
        opps = build_lu_budget_modifications(
            0.35, edb_confirms_accommodation=False, edb_confirms_post_as_qpe=False
        )
        codes = [o.account_code for o in opps]
        assert "37-00" in codes
        assert "38-00" in codes

    def test_total_incremental_rebate_reasonable(self):
        opps = build_lu_budget_modifications(0.35, edb_confirms_post_as_qpe=True)
        total_candidate = sum(o.candidate_additional_usd for o in opps)
        total_rebate = sum(o.incremental_rebate_at_rate for o in opps)
        assert total_candidate > 0
        assert abs(total_rebate - total_candidate * 0.35) < 1.0


# ── compare_mu_vs_malta_post ──────────────────────────────────────────────────

class TestCompareMuVsMaltaPost:
    """Verify MU 100% vs MU+Malta post comparison across each treatment scenario."""

    MU_BASE_QPE = 2_500_000.0
    INKIND_FMV  = 625_000.0
    MU_RATE     = 0.35
    MALTA_RATE  = 0.40

    def _get_scenario(self, result: InKindImpactResult, sid: str) -> QPEScenario:
        return next(s for s in result.scenarios if s.scenario_id == sid)

    def _analyse(self, inkind_fmv: float = None) -> InKindImpactResult:
        fmv = inkind_fmv or self.INKIND_FMV
        contrib = make_post_inkind_contribution(fmv)
        return analyse_inkind_contribution(contrib, self.MU_RATE, self.MU_BASE_QPE)

    def test_scenario_a_mu_wins(self):
        result = self._analyse()
        scenario = self._get_scenario(result, "A")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        assert cmp.winner == "MU_100_PCT"
        assert cmp.margin > 0

    def test_scenario_b_mu_wins_free_service(self):
        """With $0 cash paid, B is same as A — free service still value to MU."""
        result = self._analyse()
        scenario = self._get_scenario(result, "B")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        assert cmp.winner == "MU_100_PCT"

    def test_scenario_c_fmv_check_computations(self):
        """Scenario C: FMV qualifies — MU QPE includes $625K, service value = $0."""
        result = self._analyse()
        scenario = self._get_scenario(result, "C")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        # MU QPE should be base + FMV
        assert cmp.mu_qpe_with_inkind == self.MU_BASE_QPE + self.INKIND_FMV
        # Service value $0 when counted in QPE
        assert cmp.mu_inkind_service_value == 0.0
        # MU rebate = (2.5M + 625K) × 0.35 = 1,093,750
        assert abs(cmp.mu_rebate - (self.MU_BASE_QPE + self.INKIND_FMV) * self.MU_RATE) < 0.01

    def test_scenario_d_reduces_qpe_check(self):
        """Scenario D: QPE reduced by FMV — MU rebate falls but in-kind still has service value."""
        result = self._analyse()
        scenario = self._get_scenario(result, "D")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        # MU QPE should be base - FMV = 1,875,000
        assert cmp.mu_qpe_with_inkind == self.MU_BASE_QPE - self.INKIND_FMV
        # Still get the free service
        assert cmp.mu_inkind_service_value == self.INKIND_FMV

    def test_scenario_e_mu_wins(self):
        """Scenario E (unknown): modeled conservatively as excluded — MU still wins."""
        result = self._analyse()
        scenario = self._get_scenario(result, "E")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        assert cmp.winner == "MU_100_PCT"

    def test_malta_figures_consistent(self):
        """Malta side should include lost in-kind value and overhead."""
        result = self._analyse()
        scenario = self._get_scenario(result, "A")
        cmp = compare_mu_vs_malta_post(
            scenario, self.INKIND_FMV, self.MU_BASE_QPE,
            malta_overhead=23_000,
        )
        assert cmp.malta_inkind_lost == self.INKIND_FMV
        assert cmp.malta_overhead == 23_000

    def test_margin_is_absolute_difference(self):
        """Margin equals abs(mu_net - malta_net)."""
        result = self._analyse()
        scenario = self._get_scenario(result, "A")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        assert abs(cmp.margin - abs(cmp.mu_net_value - cmp.malta_net_value)) < 0.01

    def test_malta_post_qpe_is_total_scope(self):
        """Malta post QPE = budgeted post ($363K) + in-kind FMV ($625K) = $988K."""
        result = self._analyse()
        scenario = self._get_scenario(result, "A")
        cmp = compare_mu_vs_malta_post(
            scenario, self.INKIND_FMV, self.MU_BASE_QPE,
            post_in_budget=363_000,
        )
        assert cmp.malta_post_qpe == 363_000 + self.INKIND_FMV

    def test_mu_wins_across_low_base_high_ranges(self):
        """MU 100% should win across all three in-kind valuation ranges (Scenario A)."""
        for fmv in [500_000, 625_000, 750_000]:
            result = self._analyse(fmv)
            scenario = self._get_scenario(result, "A")
            cmp = compare_mu_vs_malta_post(scenario, fmv, self.MU_BASE_QPE)
            assert cmp.winner == "MU_100_PCT", f"MU lost at FMV=${fmv:,}"

    def test_scenario_c_mu_still_wins_even_with_fmv_in_qpe(self):
        """
        Even if EDB says FMV qualifies (best case for MU QPE),
        MU 100% should still beat MU + Malta post because the free service
        value is replaced by rebate AND Malta takes on overhead + in-kind cash cost.
        """
        result = self._analyse()
        scenario = self._get_scenario(result, "C")
        cmp = compare_mu_vs_malta_post(scenario, self.INKIND_FMV, self.MU_BASE_QPE, mu_rate=self.MU_RATE)
        # Under scenario C MU rebate goes UP (more QPE), Malta still loses in-kind
        assert cmp.winner == "MU_100_PCT"


# ── Module-level constants ────────────────────────────────────────────────────

class TestModuleConstants:
    def test_calculator_version(self):
        assert CALCULATOR_VERSION == "1.0.0"

    def test_international_precedents_count(self):
        assert len(INTERNATIONAL_PRECEDENTS) == 7

    def test_mauritius_precedent_unknown(self):
        mu_entry = next(p for p in INTERNATIONAL_PRECEDENTS if "Mauritius" in p)
        assert "UNKNOWN" in mu_entry

    def test_all_enum_values(self):
        assert len(ContributionType) == 6
        assert len(QualifyingTreatment) == 5
        assert len(AuditRisk) == 4
        assert len(SourceConfidence) == 4
