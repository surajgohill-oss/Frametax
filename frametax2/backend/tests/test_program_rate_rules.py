"""
test_program_rate_rules.py

The permanent rate-authority rules:

  1. Budget documents are never authoritative for incentive rates.
  2. Budget-embedded incentive percentages are ignored for calculation.
  3. Rates come only from the rate database + cited statutory authority.
  4. Cross-border comparison uses database/statutory rates only.
  5. On database-vs-budget disagreement: database wins, conflict reported.

Grounded in the EDB "Film Rebate Scheme — Submission Procedures"
(31 Jan 2020, citing the FRS Regulation 2018): 30% general rebate;
"up to 40%" for feature films with minimum QPE of USD 1,000,000.
"""
from __future__ import annotations

import pytest

from app.data.program_rate_rules import (
    MU_BUDGET_EVIDENCED_RATES,
    MU_RATE_RULES,
    MU_UNVERIFIED_CLAIMS,
    get_rate_rules,
    resolve_program_rate,
)


class TestStatutoryTiers:
    def test_two_mu_tiers_verified_with_citations(self):
        rules = get_rate_rules("mu_edb_incentive")
        assert {r.rate for r in rules} == {0.30, 0.40}
        for r in rules:
            assert r.confidence_tier == "VERIFIED"
            assert "Submission Procedures" in r.citation
            assert r.source_ref == "EDB-2020-Submission-Procedures"

    def test_40_tier_is_a_band_ceiling_with_verbatim_quote(self):
        tier40 = next(r for r in MU_RATE_RULES if r.rate == 0.40)
        assert tier40.is_band_ceiling is True
        quotes = " ".join(c.quote for c in tier40.conditions)
        assert "Up to 40% rebate" in quotes
        assert "minimum QPE of USD 1,000,000" in quotes

    def test_30_tier_is_not_a_band(self):
        tier30 = next(r for r in MU_RATE_RULES if r.rate == 0.30)
        assert tier30.is_band_ceiling is False


class TestResolution:
    def test_feature_film_over_1m_resolves_to_40_ceiling_with_30_floor(self):
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", qpe_usd=2_846_357.0)
        assert rr is not None
        assert rr.modeled_rate == 0.40
        assert rr.floor_rate == 0.30
        assert rr.is_band_ceiling is True
        assert rr.tier_id == "mu_frs_40_feature"

    def test_feature_film_under_1m_resolves_to_30(self):
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", qpe_usd=800_000.0)
        assert rr.modeled_rate == 0.30
        assert rr.is_band_ceiling is False

    def test_unknown_qpe_is_not_satisfied(self):
        """Unknown is never treated as meeting a threshold."""
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", qpe_usd=None)
        assert rr is None

    def test_unmodeled_program_returns_none_never_invents(self):
        assert resolve_program_rate("zz_unknown_program", "feature_film", 5_000_000.0) is None

    def test_discretionary_band_condition_is_never_pre_satisfied(self):
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", 2_000_000.0)
        band = next(c for c in rr.conditions_evaluated if c.condition_id == "mu40-band-discretion")
        assert band.satisfied is None  # authority discretion — cannot be claimed in advance


class TestBudgetRatesAreNeverAuthority:
    def test_budget_evidenced_35_exists_as_data_only(self):
        """Rule 1/2: the budget's 35% is recorded (so Rule 5 can report it),
        and appears in NO RateRule."""
        assert any(b.rate == 0.35 for b in MU_BUDGET_EVIDENCED_RATES)
        assert all(r.rate != 0.35 for r in MU_RATE_RULES)

    def test_resolution_never_returns_the_budget_rate(self):
        for qpe in (50_000.0, 150_000.0, 999_999.0, 1_000_000.0, 5_000_000.0):
            rr = resolve_program_rate("mu_edb_incentive", "feature_film", qpe)
            if rr is not None:
                assert rr.modeled_rate != 0.35

    def test_conflict_reported_database_wins(self):
        """Rule 5: the 0.35 budget figure surfaces as a reported conflict
        against the resolved statutory rate."""
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", 2_846_357.0)
        assert rr.conflicts, "budget-vs-database conflict must be reported"
        conflict = rr.conflicts[0]
        assert conflict.source_kind == "budget_document"
        assert conflict.claimed_rate == 0.35
        assert conflict.database_rate == 0.40
        assert "ignored" in conflict.resolution.lower()


class TestUnverifiedSecondaryClaims:
    def test_90pct_filming_claim_disclosed_not_applied(self):
        """The '90% of filming in Mauritius' condition appears only on a
        trade site with no cited regulation — it must be disclosed as
        unverified and must NOT exist as a RateCondition."""
        claims = " ".join(u.claim for u in MU_UNVERIFIED_CLAIMS)
        assert "90%" in claims
        for rule in MU_RATE_RULES:
            for cond in rule.conditions:
                assert "90%" not in cond.quote
                assert "90%" not in cond.description

    def test_resolution_carries_the_unverified_claims(self):
        rr = resolve_program_rate("mu_edb_incentive", "feature_film", 2_000_000.0)
        assert len(rr.unverified_claims) >= 1
        # Incentive/Optimizer Core Closeout: the 90%-local-filming claim
        # was RESOLVED (rejected — it belongs to a separate 2023/24 Budget
        # double-deduction measure, not the Film Rebate Scheme uplift; see
        # docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §1.1) and its
        # verification_status updated accordingly; the OTHER logged claim
        # (foreign cast/crew remuneration cap) remains genuinely
        # unresolved ("NOT FOUND"). Both states are legitimate — assert
        # each claim is one or the other, not that every claim is still
        # an open "NOT FOUND".
        for u in rr.unverified_claims:
            assert "NOT FOUND" in u.verification_status or "RESOLVED" in u.verification_status


class TestCrossModuleMirror:
    def test_jurisdiction_profile_mirrors_rate_database(self):
        """Rule 4: the comparison profile used by cross-border discovery
        must carry the statutory rates, not the budget-evidenced one."""
        from app.calculators.jurisdiction_comparison import TIER1_PROFILES
        mu = TIER1_PROFILES["MU"]
        rules = get_rate_rules("mu_edb_incentive")
        assert mu.base_rate == min(r.rate for r in rules) == 0.30
        assert mu.max_rate == max(r.rate for r in rules) == 0.40

    def test_demo_state_pipeline_rate_matches_resolver(self):
        from app.demo.little_utopia_state import get_state
        s = get_state()
        assert s.rate_resolution is not None
        assert s.rate_resolution.modeled_rate == s.rate
        assert s.rate_warnings == []
        assert s.rate_resolution.conflicts  # budget 0.35 conflict is reported
