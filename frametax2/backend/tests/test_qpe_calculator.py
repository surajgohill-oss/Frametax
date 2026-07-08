"""
Tests for qpe_calculator.py and the Little Utopia sanitized fixture.

Covers:
- QPEAccount validation (scenario flag ordering)
- calculate_qpe: scenario QPE sums, rebate amounts, finance costs
- GAP_MATRIX structure
- Fixture structural integrity: gross total, ATL total, marine cluster
- Rebate exclusion in budget parser
"""
from __future__ import annotations

import pytest

from app.calculators.qpe_calculator import (
    CALCULATOR_VERSION,
    QPEAccount,
    calculate_qpe,
    get_scenario,
)
from tests.fixtures.little_utopia_sanitized import (
    ACCOUNTS,
    GROSS_BUDGET_USD,
    ATL_TOTAL_USD,
    MARINE_CLUSTER_USD,
    QPE_CONSERVATIVE_TARGET,
    QPE_BASE_TARGET,
    QPE_OPTIMISTIC_TARGET,
    computed_gross_budget,
    computed_non_memo_budget,
    computed_marine_cluster,
    computed_qpe,
    get_atl_accounts,
    get_marine_accounts,
    get_non_memo_accounts,
)


# ---------------------------------------------------------------------------
# Fixture structural integrity
# ---------------------------------------------------------------------------

class TestFixtureStructure:
    def test_accounts_not_empty(self):
        assert len(ACCOUNTS) >= 30

    def test_gross_budget_matches_constant(self):
        computed = computed_gross_budget()
        assert abs(computed - GROSS_BUDGET_USD) < 1.0, (
            f"computed gross {computed:.2f} != GROSS_BUDGET_USD {GROSS_BUDGET_USD:.2f}; "
            f"includes memo lines"
        )

    def test_atl_total_matches_constant(self):
        computed = sum(a.amount_usd for a in get_atl_accounts())
        assert abs(computed - ATL_TOTAL_USD) < 1.0, (
            f"computed ATL {computed:.2f} != ATL_TOTAL_USD {ATL_TOTAL_USD:.2f}"
        )

    def test_marine_cluster_matches_constant(self):
        computed = computed_marine_cluster()
        assert abs(computed - MARINE_CLUSTER_USD) < 1.0, (
            f"computed marine {computed:.2f} != MARINE_CLUSTER_USD {MARINE_CLUSTER_USD:.2f}"
        )

    def test_marine_accounts_count(self):
        marine = get_marine_accounts()
        assert len(marine) >= 4, "Expect at least 4 marine accounts (vessel, safety, Frogsquad, equipment)"

    def test_memo_lines_excluded_from_gross(self):
        memo_sum = sum(a.amount_usd for a in ACCOUNTS if a.is_memo_line)
        non_memo_sum = computed_gross_budget()
        total_including_memo = memo_sum + non_memo_sum
        assert total_including_memo > GROSS_BUDGET_USD or memo_sum == 0, (
            "Memo lines should be in addition to or zero vs gross budget"
        )

    def test_scenario_flag_ordering(self):
        for acc in get_non_memo_accounts():
            if acc.conservative_qualifies:
                assert acc.base_qualifies, (
                    f"{acc.account_code}: conservative=True requires base=True"
                )
            if acc.base_qualifies:
                assert acc.optimistic_qualifies, (
                    f"{acc.account_code}: base=True requires optimistic=True"
                )

    def test_atl_all_excluded_conservative(self):
        for acc in get_atl_accounts():
            assert not acc.conservative_qualifies, (
                f"{acc.account_code}: ATL should not qualify conservatively"
            )
            assert not acc.base_qualifies, (
                f"{acc.account_code}: ATL should not qualify in base scenario"
            )

    def test_vessel_charter_always_qualifies(self):
        vessel = next(a for a in ACCOUNTS if a.account_code == "31-00")
        assert vessel.conservative_qualifies
        assert vessel.base_qualifies
        assert vessel.optimistic_qualifies
        assert vessel.is_marine

    def test_frogsquad_base_not_conservative(self):
        frogsquad = next(a for a in ACCOUNTS if a.account_code == "33-00")
        assert not frogsquad.conservative_qualifies
        assert frogsquad.base_qualifies
        assert frogsquad.is_marine

    def test_international_travel_excluded_all(self):
        travel = next(a for a in ACCOUNTS if a.account_code == "39-00")
        assert not travel.conservative_qualifies
        assert not travel.base_qualifies
        assert not travel.optimistic_qualifies

    def test_vat_memo_line(self):
        vat = next(a for a in ACCOUNTS if a.account_code == "44-00")
        assert vat.is_memo_line
        assert not vat.conservative_qualifies
        assert not vat.base_qualifies
        assert not vat.optimistic_qualifies

    def test_finance_costs_zero(self):
        finance = next(a for a in ACCOUNTS if a.account_code == "82-00")
        assert finance.amount_usd == 0.0

    def test_conservative_qpe_less_than_base(self):
        c = computed_qpe("conservative")
        b = computed_qpe("base")
        assert c < b, f"Conservative QPE {c:.2f} must be < base QPE {b:.2f}"

    def test_base_qpe_less_than_optimistic(self):
        b = computed_qpe("base")
        o = computed_qpe("optimistic")
        assert b < o, f"Base QPE {b:.2f} must be < optimistic QPE {o:.2f}"

    def test_optimistic_qpe_less_than_gross(self):
        o = computed_qpe("optimistic")
        assert o < GROSS_BUDGET_USD


# ---------------------------------------------------------------------------
# QPE Calculator — unit tests with minimal accounts
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_accounts():
    return [
        QPEAccount(
            amount_usd=1_000.0,
            conservative_qualifies=True,
            base_qualifies=True,
            optimistic_qualifies=True,
            description="Always qualifying",
            department="Production",
        ),
        QPEAccount(
            amount_usd=500.0,
            conservative_qualifies=False,
            base_qualifies=True,
            optimistic_qualifies=True,
            description="Base and optimistic only",
            department="Production",
        ),
        QPEAccount(
            amount_usd=250.0,
            conservative_qualifies=False,
            base_qualifies=False,
            optimistic_qualifies=True,
            description="Optimistic only",
            department="Production",
        ),
        QPEAccount(
            amount_usd=100.0,
            conservative_qualifies=False,
            base_qualifies=False,
            optimistic_qualifies=False,
            description="Never qualifies",
            department="Other",
        ),
        QPEAccount(
            amount_usd=999.0,
            conservative_qualifies=False,
            base_qualifies=False,
            optimistic_qualifies=False,
            is_memo_line=True,
            description="Memo — rebate line",
            department="Other",
        ),
    ]


class TestCalculateQPE:
    def test_version_set(self):
        assert CALCULATOR_VERSION == "0.1.0"

    def test_conservative_qpe(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        s = get_scenario(result, "conservative")
        assert s.qpe_usd == 1_000.0

    def test_base_qpe(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        s = get_scenario(result, "base")
        assert s.qpe_usd == 1_500.0

    def test_optimistic_qpe(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        s = get_scenario(result, "optimistic")
        assert s.qpe_usd == 1_750.0

    def test_memo_excluded_from_gross(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        # gross = 1000 + 500 + 250 + 100 = 1850 (memo 999 excluded)
        assert result.gross_budget_usd == 1_850.0
        assert result.excluded_memo_usd == 999.0

    def test_rebate_at_35pct(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        s = get_scenario(result, "base")
        assert abs(s.rebate_amounts[0.35] - 525.0) < 0.01  # 1500 * 0.35

    def test_multiple_rates(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.30, 0.35], "MU")
        s = get_scenario(result, "conservative")
        assert 0.30 in s.rebate_amounts
        assert 0.35 in s.rebate_amounts
        assert abs(s.rebate_amounts[0.30] - 300.0) < 0.01
        assert abs(s.rebate_amounts[0.35] - 350.0) < 0.01

    def test_finance_cost_calculated(self, simple_accounts):
        result = calculate_qpe(
            simple_accounts, [0.35], "MU",
            finance_cost_delay_weeks=52,
            finance_cost_annual_rate=0.08,
        )
        # 1 year at 8% on $350 rebate (conservative at 35%) = $28.00
        fc = result.finance_cost_estimates[0]
        assert abs(fc.finance_cost_usd - 28.0) < 0.01

    def test_no_warnings_valid_data(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        assert result.warnings == []

    def test_flag_ordering_violation_corrected(self):
        bad = [QPEAccount(
            amount_usd=100.0,
            conservative_qualifies=True,
            base_qualifies=False,  # violation
            optimistic_qualifies=True,
            description="Bad ordering",
            department="Production",
        )]
        result = calculate_qpe(bad, [0.35], "MU")
        assert len(result.warnings) > 0
        # After correction, base must be True
        s = get_scenario(result, "base")
        assert s.qpe_usd == 100.0

    def test_three_scenarios_present(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MU")
        assert {s.scenario for s in result.scenarios} == {"conservative", "base", "optimistic"}

    def test_jurisdiction_code_in_result(self, simple_accounts):
        result = calculate_qpe(simple_accounts, [0.35], "MT")
        assert result.jurisdiction_code == "MT"

    def test_marine_cluster_calculated(self):
        accounts = [
            QPEAccount(
                amount_usd=10_000.0,
                conservative_qualifies=True,
                base_qualifies=True,
                optimistic_qualifies=True,
                is_marine=True,
                description="Vessel charter",
                department="Production",
            ),
            QPEAccount(
                amount_usd=5_000.0,
                conservative_qualifies=True,
                base_qualifies=True,
                optimistic_qualifies=True,
                is_marine=False,
                description="Catering",
                department="Production",
            ),
        ]
        result = calculate_qpe(accounts, [0.35], "MU")
        assert result.marine_cluster_usd == 10_000.0


# ---------------------------------------------------------------------------
# Full fixture through QPE calculator
# ---------------------------------------------------------------------------

class TestFixtureThroughCalculator:
    @pytest.fixture(autouse=True)
    def result(self):
        self._result = calculate_qpe(ACCOUNTS, [0.30, 0.35], "MU")

    def test_gross_budget(self):
        # Calculator reports non-memo total (memo lines are excluded from calculation)
        assert abs(self._result.gross_budget_usd - computed_non_memo_budget()) < 1.0

    def test_marine_cluster(self):
        assert abs(self._result.marine_cluster_usd - MARINE_CLUSTER_USD) < 1.0

    def test_conservative_qpe_range(self):
        s = get_scenario(self._result, "conservative")
        assert s.qpe_usd > 0
        assert s.qpe_usd < GROSS_BUDGET_USD

    def test_base_qpe_greater_than_conservative(self):
        c = get_scenario(self._result, "conservative").qpe_usd
        b = get_scenario(self._result, "base").qpe_usd
        assert b > c

    def test_optimistic_qpe_greater_than_base(self):
        b = get_scenario(self._result, "base").qpe_usd
        o = get_scenario(self._result, "optimistic").qpe_usd
        assert o > b

    def test_rebate_35_calculated_for_all_scenarios(self):
        for scenario in ["conservative", "base", "optimistic"]:
            s = get_scenario(self._result, scenario)
            assert 0.35 in s.rebate_amounts
            assert s.rebate_amounts[0.35] == pytest.approx(s.qpe_usd * 0.35, abs=1.0)

    def test_no_warnings(self):
        assert self._result.warnings == []

    def test_atl_total_set(self):
        assert abs(self._result.atl_total_usd - ATL_TOTAL_USD) < 1.0

    def test_vat_memo_excluded(self):
        assert self._result.excluded_memo_usd == pytest.approx(92_439.0, abs=1.0)


# ---------------------------------------------------------------------------
# Budget parser rebate exclusion
# ---------------------------------------------------------------------------

class TestBudgetParserRebateExclusion:
    """Verify that rebate/credit/net-total lines are excluded from parsed spend."""

    def test_rebate_line_not_captured_as_account(self):
        from app.ingestion.budget_parser import _REBATE_EXCLUSION_RE

        rebate_lines = [
            "EDB Rebate at 35%",
            "EDB Rebate at 35%: $(1,275,411)",
            "Tax Credit at 30%",
            "Net Total",
            "Incentive Rebate",
            "Film Rebate at 40%",
        ]
        for line in rebate_lines:
            assert _REBATE_EXCLUSION_RE.search(line), (
                f"Rebate exclusion regex should match: {line!r}"
            )

    def test_normal_lines_not_excluded(self):
        from app.ingestion.budget_parser import _REBATE_EXCLUSION_RE

        safe_lines = [
            "20-00 Production Staff",
            "Vessel Charter — Marine Unit",
            "Catering & Craft Services",
            "Grand Total",
            "Account Total for 20-00",
            "Director Fee",
        ]
        for line in safe_lines:
            assert not _REBATE_EXCLUSION_RE.search(line), (
                f"Rebate exclusion regex should NOT match: {line!r}"
            )

    def test_film_budget_excludes_rebate_from_total(self):
        from app.ingestion.budget_parser import parse_budget_from_text

        # Synthetic film budget text with a rebate line injected
        budget_text = (
            "Acct# Category Description Page Total\n"
            "20-00 Production Staff 2 50000\n"
            "21-00 Camera Department 3 30000\n"
            "EDB Rebate at 35%  (28000)\n"
            "Net Total  52000\n"
            "Grand Total\n"
            "80000\n"
        )
        result = parse_budget_from_text(budget_text)
        # The rebate and net-total lines must not appear as line items
        descriptions = [item.description.lower() for item in result.line_items]
        assert not any("rebate" in d for d in descriptions)
        assert not any("net total" in d for d in descriptions)


# ---------------------------------------------------------------------------
# Canonical Mauritius calculation regression — The Little Utopia
#
# Locks in the corrected end-to-end calculation so it cannot silently drift
# back to the stale $2.5M/35% plug-figure model. See structuring_advisor.py
# LittleUtopiaParams and inkind_contribution.py compare_mu_vs_malta_post for
# the consumers of these canonical figures.
# ---------------------------------------------------------------------------

class TestCanonicalMauritiusCalculation:
    MU_RATE = 0.40  # EDB official programme page: "up to 40%" — canonical for this project
    INKIND_FMV = 625_000.0  # off-budget, zero cash paid — additive only, never subtracted

    @pytest.fixture(autouse=True)
    def result(self):
        import copy
        self._result = calculate_qpe(copy.deepcopy(ACCOUNTS), [self.MU_RATE], "MU")

    def test_gross_cash_budget_is_4_364_393(self):
        """Gross cash budget must reconcile to the fixture total regardless of
        rate or in-kind treatment."""
        assert self._result.gross_budget_usd + self._result.excluded_memo_usd == pytest.approx(4_364_393.0, abs=1.0)

    def test_mauritius_rate_is_40_percent_not_35(self):
        """Canonical MU rate for this project is 40%, not the stale
        budget-evidenced 35% line ('EDB Rebate at 35%')."""
        base = get_scenario(self._result, "base")
        assert self.MU_RATE == 0.40
        assert base.rebate_amounts[0.40] == pytest.approx(base.qpe_usd * 0.40, abs=0.01)

    def test_base_qpe_account_reconciles_with_no_plug(self):
        """QPE + all excluded non-memo accounts + memo lines must equal gross
        budget exactly — no residual/'Other Non-Qualifying' balancing figure."""
        base = get_scenario(self._result, "base")
        non_memo = get_non_memo_accounts()
        excluded_total = sum(a.amount_usd for a in non_memo if not a.base_qualifies)
        assert base.qpe_usd + excluded_total == pytest.approx(self._result.gross_budget_usd, abs=1.0)
        assert base.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)

    def test_accommodation_and_perdiem_not_excluded_without_rule_source(self):
        """No EDB rule source proves 37-00/38-00 (accommodation & per diems, sum
        $273,913) must be excluded — they must remain included in base QPE."""
        accom_perdiem = [a for a in ACCOUNTS if a.account_code in ("37-00", "38-00")]
        assert sum(a.amount_usd for a in accom_perdiem) == pytest.approx(273_913.0, abs=1.0)
        assert all(a.base_qualifies for a in accom_perdiem)

    def test_incentive_equals_qpe_times_40_percent(self):
        base = get_scenario(self._result, "base")
        assert base.rebate_amounts[0.40] == pytest.approx(791_965.20, abs=1.0)

    def test_inkind_fmv_is_additive_not_subtracted_from_gross(self):
        """The $625,000 in-kind FMV is off-budget (zero cash paid) and must
        never reduce gross_budget_usd or QPE — only add to QPE conditionally."""
        base = get_scenario(self._result, "base")
        qpe_with_inkind = base.qpe_usd + self.INKIND_FMV
        rebate_with_inkind = qpe_with_inkind * self.MU_RATE
        assert rebate_with_inkind > base.rebate_amounts[0.40]
        assert rebate_with_inkind - base.rebate_amounts[0.40] == pytest.approx(250_000.0, abs=1.0)
        # Gross budget must be untouched by the in-kind assumption
        assert self._result.gross_budget_usd + self._result.excluded_memo_usd == pytest.approx(4_364_393.0, abs=1.0)

    def test_net_benefit_after_finance_cost(self):
        """Net benefit after the modeled 8%/39-week bridge finance cost."""
        base = get_scenario(self._result, "base")
        rebate = base.rebate_amounts[0.40]
        fc = [f for f in self._result.finance_cost_estimates if abs(f.rebate_usd - rebate) < 1][0]
        assert fc.net_after_finance_cost_usd == pytest.approx(744_447.29, abs=1.0)
