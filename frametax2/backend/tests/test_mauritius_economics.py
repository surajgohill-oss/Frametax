"""
test_mauritius_economics.py

Targeted regression tests for the Mauritius Qualification Closeout +
Production-Economics Controls phase. One test per validation point.
"""
from __future__ import annotations

import pytest

from app.calculators.mauritius_economics import (
    FinancingMethod,
    FinancingModel,
    FinancingSource,
    InKindAcceptance,
    InKindPostModel,
    PostLocation,
    compute_mauritius_economics,
)
from app.calculators.qualification_model import QualificationState

GROSS = 4_364_393.0
QPE = 4_355_327.0
FLOOR = 0.30
CEILING = 0.40


def _econ(financing=None, inkind=None, awarded=None):
    return compute_mauritius_economics(
        GROSS, QPE, FLOOR, CEILING,
        financing or FinancingModel(),
        inkind or InKindPostModel(),
        awarded_rate=awarded,
    )


# ── (1) Local-SPV default does not exclude foreign people/vendors ────────────

class TestSPVDefaultForeignInclusive:
    def test_state_exposes_foreign_inclusive_spv_default(self):
        from app.demo.little_utopia_state import SPV_PRODUCTION_STRUCTURE_DEFAULT as d
        assert d["assumption"] == "optimized_legal_local_structure"
        assert any("foreign" in a.lower() and "not" in a.lower() for a in d["assumptions"])
        # Exclusion is gated to the three legitimate reasons only.
        assert len(d["exclusion_gates"]) == 3

    def test_foreign_labour_account_qualifies(self):
        # 1400 CAST (foreign cast) must qualify — never excluded for being foreign.
        from app.calculators.qualification_model import build_little_utopia_real_register
        reg = build_little_utopia_real_register()
        cast = next(a for a in reg if a.account_code == "1400")
        assert cast.state == QualificationState.QUALIFIES


# ── (2) Financing defaults to zero ───────────────────────────────────────────

class TestFinancingDefaultsZero:
    def test_default_financing_is_zero(self):
        f = _econ()["verified_floor_case"]
        assert f.financing_cost_usd == 0.0
        assert f.financing_source == FinancingSource.DEFAULT_ZERO.value

    def test_no_silent_8pct_39wk(self):
        f = _econ()["verified_floor_case"]
        # NPC with zero financing = gross - incentive (no financing subtracted twice).
        assert f.net_production_cost_usd == pytest.approx(GROSS - QPE * FLOOR, abs=0.01)


# ── (3) Rate-and-time financing ──────────────────────────────────────────────

class TestRateTimeFinancing:
    def test_rate_time_cost_and_formula(self):
        fin = FinancingModel(
            source=FinancingSource.USER_INPUT, method=FinancingMethod.RATE_TIME,
            annual_rate=0.08, weeks=39, financed_amount_pct=1.0,
        )
        f = _econ(financing=fin)["verified_floor_case"]
        expected = round(QPE * FLOOR * 0.08 * (39 / 52), 2)
        assert f.financing_cost_usd == pytest.approx(expected, abs=0.01)
        assert f.financing_source == FinancingSource.USER_INPUT.value
        assert "39/52" in f.financing_formula

    def test_partial_financed_amount_scales(self):
        fin = FinancingModel(
            source=FinancingSource.USER_INPUT, method=FinancingMethod.RATE_TIME,
            annual_rate=0.08, weeks=39, financed_amount_pct=0.5,
        )
        f = _econ(financing=fin)["verified_floor_case"]
        expected = round(QPE * FLOOR * 0.5 * 0.08 * (39 / 52), 2)
        assert f.financing_cost_usd == pytest.approx(expected, abs=0.01)


# ── (4) Hard-cost financing ──────────────────────────────────────────────────

class TestHardCostFinancing:
    def test_hard_cost_used_verbatim(self):
        fin = FinancingModel(
            source=FinancingSource.USER_INPUT, method=FinancingMethod.HARD_COST,
            hard_cost_usd=50_000.0,
        )
        f = _econ(financing=fin)["verified_floor_case"]
        assert f.financing_cost_usd == 50_000.0
        assert f.net_production_cost_usd == pytest.approx(GROSS - (QPE * FLOOR - 50_000.0), abs=0.01)


# ── (5) In-kind accepted / rejected / lost = three different outcomes ────────

class TestInKindThreeOutcomes:
    def test_three_distinct_economic_outcomes(self):
        opts = _econ()["inkind_post_options"]
        accepted = opts["accepted_as_qpe"]
        rejected = opts["not_accepted_as_qpe"]
        lost = opts["lost_or_moved_outside_mu"]
        # Distinct economic production values.
        vals = {accepted.economic_production_value_usd,
                rejected.economic_production_value_usd,
                lost.economic_production_value_usd}
        assert len(vals) == 3

    def test_accepted_earns_incremental_incentive_off_budget(self):
        acc = _econ()["inkind_post_options"]["accepted_as_qpe"]
        # incentive = cash QPE*rate + FMV*rate ; FMV never added to cash budget.
        assert acc.incentive_usd == pytest.approx(QPE * FLOOR + 625_000 * FLOOR, abs=0.01)
        assert acc.gross_cash_budget_usd == GROSS  # unchanged
        assert acc.off_budget_inkind_usd == 625_000.0

    def test_rejected_no_incentive_but_preserves_noncash_benefit(self):
        rej = _econ()["inkind_post_options"]["not_accepted_as_qpe"]
        assert rej.incentive_usd == pytest.approx(QPE * FLOOR, abs=0.01)  # no in-kind incentive
        # Economic value credits the non-cash $625k benefit.
        assert rej.economic_production_value_usd == pytest.approx(rej.net_production_cost_usd - 625_000, abs=0.01)


# ── (6) Moving post outside Mauritius adds $625,000 to cash budget ──────────

class TestInKindLostAddsCash:
    def test_lost_adds_replacement_to_cash_budget(self):
        lost = _econ()["inkind_post_options"]["lost_or_moved_outside_mu"]
        assert lost.gross_cash_budget_usd == pytest.approx(GROSS + 625_000, abs=0.01)
        assert lost.off_budget_inkind_usd == 0.0  # no longer off-budget in-kind
        assert lost.qpe_usd == QPE  # replacement post outside MU does not qualify

    def test_custom_replacement_cost_respected(self):
        inkind = InKindPostModel(replacement_post_cost_if_lost_usd=700_000.0)
        lost = _econ(inkind=inkind)["inkind_post_options"]["lost_or_moved_outside_mu"]
        assert lost.gross_cash_budget_usd == pytest.approx(GROSS + 700_000, abs=0.01)


# ── (7) Changing post location reruns qualification and structures ──────────

class TestPostLocationReruns:
    def test_post_location_flips_register_and_structures(self):
        from app.demo.little_utopia_state import (
            apply_fact_answers, get_state, reset_fact_answers,
        )
        from app.calculators.optimization_engine import RiskCase
        reset_fact_answers()
        base = get_state()
        base_qpe = sum(a.amount_usd for a in base.register if a.state == QualificationState.QUALIFIES)
        base_5000 = next(a.state for a in base.register if a.account_code == "5000")
        assert base_5000 == QualificationState.EXCLUDED  # post outside MU by default

        apply_fact_answers({"post_work_in_jurisdiction": True})
        moved = get_state()
        moved_qpe = sum(a.amount_usd for a in moved.register if a.state == QualificationState.QUALIFIES)
        moved_5000 = next(a.state for a in moved.register if a.account_code == "5000")
        moved_struct_qpe = next(
            c for c in moved.composition.candidates if c.candidate_id == "PSC-MU"
        ).cases[RiskCase.CONSERVATIVE].qpe_usd

        assert moved_5000 == QualificationState.QUALIFIES  # register reran
        assert moved_qpe > base_qpe                         # QPE reran
        assert moved_struct_qpe == pytest.approx(moved_qpe, abs=0.01)  # structures reran
        reset_fact_answers()


# ── (8) 30% and 40% outputs are clearly separated ───────────────────────────

class TestRateSeparation:
    def test_floor_and_ceiling_are_distinct_labeled_results(self):
        e = _econ()
        floor = e["verified_floor_case"]
        ceiling = e["potential_ceiling_case"]
        assert floor.incentive_rate == 0.30
        assert floor.rate_authority_status == "VERIFIED_FLOOR"
        assert ceiling.incentive_rate == 0.40
        assert ceiling.rate_authority_status == "CONDITIONAL_CEILING"
        assert ceiling.conditions  # exact unmet conditions listed
        assert floor.incentive_usd < ceiling.incentive_usd

    def test_user_elected_rate_is_labeled_election_not_award(self):
        e = _econ(awarded=0.35)
        ue = e["user_elected_case"]
        assert ue.incentive_rate == 0.35
        assert ue.rate_authority_status == "USER_ELECTED_INTERMEDIATE"


# ── (9) No budget incentive percentage affects calculations ─────────────────

class TestBudgetRateIgnored:
    def test_modeled_rate_from_statute_not_budget(self):
        from app.demo.little_utopia_state import get_state, reset_fact_answers
        reset_fact_answers()
        s = get_state()
        assert s.rate == 0.40                          # statutory ceiling
        assert s.rate_resolution.modeled_rate == 0.40
        # The budget's own 35% is recorded only as a reported conflict.
        assert any(c.claimed_rate == 0.35 and c.database_rate == 0.40
                   for c in s.rate_resolution.conflicts)


# ── (10) No MockConnector result affects canonical financial outputs ────────

class TestMockNeverResolvesGrey:
    def test_inkind_grey_stays_open_not_auto_resolved(self):
        from app.demo.little_utopia_state import get_state, reset_fact_answers
        from app.calculators.qualification_model import GreyAreaStatus
        reset_fact_answers()
        s = get_state()
        # Demo does NOT auto-commit the genuine in-kind grey via mock.
        assert s.legal_commit is None
        inkind = next(g for g in s.grey_areas_baseline if g.item_id == "GA-INKIND-FMV")
        assert inkind.status == GreyAreaStatus.OPEN
        assert inkind.resolution_paths  # concrete producer resolution paths exposed
        assert "producer_election" in inkind.grey_kinds

    def test_headline_economics_independent_of_legal_view(self):
        # The /economics headline is a pure function of register QPE + rate +
        # controls — never the legal/mock cycle.
        from app.demo.little_utopia_state import get_state, reset_fact_answers
        reset_fact_answers()
        s = get_state()
        qpe = sum(a.amount_usd for a in s.register if a.state == QualificationState.QUALIFIES)
        floor = compute_mauritius_economics(
            s.gross_budget_usd, qpe, 0.30, 0.40, FinancingModel(), InKindPostModel()
        )["verified_floor_case"]
        assert floor.qpe_usd == pytest.approx(qpe, abs=0.01)
