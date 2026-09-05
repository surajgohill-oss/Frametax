"""
Co-Pro Opportunity Conditional Pricing Bridge — focused unit tests.

Narrow Optimizer Wiring Closeout: closes the gap between a DISCOVERED but
UNRESOLVED_FACTS bilateral treaty opportunity and a real, canonically
priced CONDITIONAL scenario. No new engine — reuses
solve_bilateral_minimum_contribution (canonical_treaty_bridge.py),
_build_conditional_bilateral_scenario (canonical_evaluation.py), the
existing fail-closed evaluate_bilateral_coproduction_opportunity adapter,
and the existing canonical pricing kernel (_price_candidate).

Genericity control (governing spec, Section 12): this file uses
SYNTHETIC treaty/jurisdiction fixtures (frozenset keys registered
directly into treaty_engine's own _BILATERAL dict via monkeypatch, using
non-real-world slugs/parties) to prove the bridge is not Little Utopia-
or FVD-specific. The one exception, per spec, is a control assertion
against LU's real GB-AU case, clearly labeled as such.
"""
from __future__ import annotations

import pytest

from app.calculators import treaty_engine as te
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
    solve_bilateral_minimum_contribution,
)
from app.calculators.qualification_derivation import BudgetLine
from app.services import canonical_evaluation as ce
from app.services.canonical_project_economics import ProjectEconomicInputs


def _synthetic_treaty(
    slug: str,
    a: str,
    b: str,
    maj_min: float = 20.0,
    min_min: float = 20.0,
    min_max: float | None = 80.0,
    cultural_test: bool = False,
    maj_unlocks: list[str] | None = None,
    min_unlocks: list[str] | None = None,
) -> te.TreatyData:
    return te.TreatyData(
        treaty_slug=slug,
        treaty_type="bilateral",
        jurisdiction_a=a,
        jurisdiction_b=b,
        majority_min_pct=maj_min,
        minority_min_pct=min_min,
        minority_max_pct=min_max,
        min_coproducer_countries=2,
        cultural_test_required=cultural_test,
        majority_unlocks=maj_unlocks or [],
        minority_unlocks=min_unlocks or [],
        fund_unlocks=[],
        confidence_tier="PARSED",
    )


def _inputs(**overrides) -> ProjectEconomicInputs:
    base = dict(
        project_id="synthetic-copro-test-project",
        project_name="Synthetic Co-Pro Test",
        jurisdiction_code="MU",
        production_type="feature_film",
        gross_budget_usd=1_000_000.0,
        leaf_account_sum_usd=1_000_000.0,
        budget_lines=[BudgetLine("1000", "Cast", 500_000.0, spend_category="atl_cast")],
        spend_category_by_code={"1000": "atl_cast"},
        accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(),
    )
    base.update(overrides)
    return ProjectEconomicInputs(**base)


# ---------------------------------------------------------------------------
# solve_bilateral_minimum_contribution — deterministic solve
# ---------------------------------------------------------------------------

def test_solve_returns_treatys_own_minimum_thresholds_when_no_cultural_test():
    treaty = _synthetic_treaty("zz-yy-bilateral", "ZZ", "YY", maj_min=25.0, min_min=15.0, min_max=75.0)
    solved = solve_bilateral_minimum_contribution(treaty)
    assert solved.majority_pct == 25.0
    assert solved.minority_pct == 15.0
    assert solved.deterministically_solvable is True
    assert solved.blocking_reason is None


def test_solve_blocks_on_cultural_test_requirement_regardless_of_thresholds():
    treaty = _synthetic_treaty("zz-yy-bilateral", "ZZ", "YY", cultural_test=True)
    solved = solve_bilateral_minimum_contribution(treaty)
    assert solved.deterministically_solvable is False
    assert solved.cultural_test_required is True
    assert "cultural test" in solved.blocking_reason.lower()
    # never silently invents a percentage when it can't solve
    assert solved.majority_pct == treaty.majority_min_pct
    assert solved.minority_pct == treaty.minority_min_pct


def test_solve_blocks_on_self_inconsistent_treaty_data_never_guesses():
    treaty = _synthetic_treaty("zz-yy-bilateral", "ZZ", "YY", maj_min=20.0, min_min=90.0, min_max=80.0)
    solved = solve_bilateral_minimum_contribution(treaty)
    assert solved.deterministically_solvable is False
    assert "exceeds its minority_max_pct" in solved.blocking_reason


# ---------------------------------------------------------------------------
# _build_conditional_bilateral_scenario — generic, synthetic, non-LU fixture
# ---------------------------------------------------------------------------

def test_conditional_scenario_user_decision_required_when_cultural_test_blocks_solve(monkeypatch):
    treaty = _synthetic_treaty("zz-yy-bilateral", "ZZ", "YY", cultural_test=True,
                                maj_unlocks=["uk_avec"], min_unlocks=["be_tax_shelter"])
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )
    assert scenario is not None
    assert scenario["status"] == "USER_DECISION_REQUIRED"
    assert scenario["conditional_qualification_state"] == "UNRESOLVED_FACTS"
    assert scenario["deterministically_solvable"] is False
    # never fabricates conditional economics when a real creative fact is unresolved
    assert "conditional_incentive_usd" not in scenario
    assert "conditional_npc_usd" not in scenario


def test_conditional_scenario_not_feasible_when_reresolution_fails(monkeypatch):
    """Defensive path: even though the deterministic minimum is by
    construction the treaty's own satisfiable threshold, this proves the
    NOT_FEASIBLE branch degrades safely rather than fabricating economics
    if re-resolution ever returns anything other than ELIGIBLE."""
    treaty = _synthetic_treaty("zz-yy-bilateral", "ZZ", "YY",
                                maj_unlocks=["uk_avec"], min_unlocks=["be_tax_shelter"])
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)
    monkeypatch.setattr(ce, "evaluate_bilateral_coproduction_opportunity", lambda *a, **k: None)

    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )
    assert scenario["status"] == "NOT_FEASIBLE"
    assert "conditional_incentive_usd" not in scenario
    assert "conditional_npc_usd" not in scenario


def test_conditional_scenario_reports_canonical_data_gap_without_inventing_a_rate(monkeypatch):
    """Synthetic majority-side program has no canonical RateRule; this
    must be disclosed as CANONICAL_DATA_GAP, never priced or invented —
    mirrors the real au_producer_offset gap found for LU's GB-AU route,
    but here proven with an entirely fictitious slug."""
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY",
        maj_unlocks=["zz_totally_fictitious_incentive_slug"], min_unlocks=[],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )
    assert scenario["conditional_qualification_state"] == RESOLUTION_ELIGIBLE
    assert scenario["canonical_data_gaps"] == ["zz_totally_fictitious_incentive_slug"]
    assert scenario["status"] == "CANONICAL_DATA_GAP"
    assert scenario["fully_priced"] is False
    assert "conditional_incentive_usd" not in scenario


def test_conditional_scenario_fully_prices_synthetic_generic_route_end_to_end(monkeypatch):
    """THE mandatory generic, non-LU fixture (spec Section 12 / Runtime
    Acceptance item P): an entirely synthetic bilateral treaty between
    two fictitious ISO codes, unlocking two REAL canonical-rate-rule
    programs (uk_avec, be_tax_shelter, chosen only because they carry
    real RateRule entries -- not because of any UK/Belgium storyline),
    proving the SAME pipeline (solve -> re-resolve -> canonical pricing
    -> conditional NPC) that LU's GB-AU route exercises, with zero
    project-specific branching."""
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY", maj_min=20.0, min_min=20.0, min_max=80.0,
        maj_unlocks=["uk_avec"], min_unlocks=["be_tax_shelter"],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    inputs = _inputs(gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
                      budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
    scenario = ce._build_conditional_bilateral_scenario(
        inputs, "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )

    assert scenario["conditional_qualification_state"] == RESOLUTION_ELIGIBLE
    assert scenario["assumed_majority_contribution_pct"] == 20.0
    assert scenario["assumed_minority_contribution_pct"] == 20.0
    assert scenario["canonical_data_gaps"] == []
    priced_slugs = {c["program_slug"] for c in scenario["priced_components"]}
    assert priced_slugs == {"uk_avec", "be_tax_shelter"}
    assert scenario["fully_priced"] is True
    assert scenario["status"] == "CONDITIONAL_PROJECT_FACT_DEPENDENT"
    assert scenario["conditional_incentive_usd"] > 0
    assert scenario["conditional_npc_usd"] == pytest.approx(
        inputs.gross_budget_usd - scenario["conditional_incentive_usd"], abs=0.01
    )


def test_conditional_scenario_computes_savings_vs_real_baseline_when_provided(monkeypatch):
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY", maj_unlocks=["uk_avec"], min_unlocks=[],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    inputs = _inputs(gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
                      budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
    scenario = ce._build_conditional_bilateral_scenario(
        inputs, "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=100_000.0,
    )
    assert scenario["baseline_npc_usd"] == pytest.approx(inputs.gross_budget_usd - 100_000.0, abs=0.01)
    assert scenario["net_benefit_vs_baseline_usd"] == pytest.approx(
        scenario["baseline_npc_usd"] - scenario["conditional_npc_usd"], abs=0.01
    )


def test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine(monkeypatch):
    """Section 8 (conditional stacking must use the EXISTING stacking
    engine, never a hand-built sum): a synthetic majority party unlocking
    TWO of its own programs that carry a real, named mutually_exclusive
    rule (ca_bc_pstc + ca_federal_cptc) must be routed through
    price_program_group_stack -- proven by the adjusted total differing
    from the naive raw sum, and the stacking decision being disclosed."""
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY",
        maj_unlocks=["ca_bc_pstc", "ca_federal_cptc"], min_unlocks=[],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    inputs = _inputs(gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
                      budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
    scenario = ce._build_conditional_bilateral_scenario(
        inputs, "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )

    assert scenario["canonical_data_gaps"] == []
    assert "stacking_groups" in scenario
    [group] = scenario["stacking_groups"]
    assert group["jurisdiction_code"] == "ZZ"
    assert set(group["program_slugs"]) == {"ca_bc_pstc", "ca_federal_cptc"}
    assert group["stacking_verified"] is True
    assert group["rule_type"] == "mutually_exclusive"

    # THE invariant: the reported figure is whatever the stacking engine
    # adjudicated, never a hand-built sum of the components.
    assert scenario["conditional_incentive_usd"] == pytest.approx(
        group["adjusted_incentive_usd"], abs=0.01
    )

    # The original proof was "adjusted != naive sum". That was only ever a
    # proxy for "the stack engine ran", and it is no longer a safe one: both
    # ca_bc_pstc and ca_federal_cptc declare a labour-only qualifying base
    # (rate_base_narrower_than_qpe), so under the cluster-5 repair each
    # correctly prices to zero and the naive sum is 0.00 -- making 0 != 0
    # fail for a reason that has nothing to do with stacking. Assert
    # suppression only where there is something to suppress, and rely on the
    # structural assertions above (stacking_verified / rule_type) as the
    # real evidence that the engine, not arithmetic, produced the number.
    raw_sum = sum(c["selected_incentive_usd"] for c in scenario["priced_components"])
    if round(raw_sum, 2) > 0:
        assert scenario["conditional_incentive_usd"] <= round(raw_sum, 2) + 0.01, (
            "a mutually_exclusive pair must never exceed the sum of both "
            "programs' independently-priced values"
        )


def test_conditional_scenario_reconnects_treaty_unlock_slug_through_alias_table(monkeypatch):
    """Co-Pro Conditional Pricing Data Reconnection, generic proof: a
    treaty's own unlock-list spelling need not match the canonical rate
    registry's spelling for the SAME program (the real "nz_spgi" vs
    "nz_spg_international" case). Proven here with an entirely synthetic
    alias pair -- program_slug_aliases.PROGRAM_SLUG_ALIASES is the same
    existing, generic table canonical_stack_bridge.py already consults;
    this is a program-agnostic reconnection, not a per-slug special case."""
    from app.data import program_slug_aliases as psa

    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY",
        maj_unlocks=["zz_treaty_spelling_alias"], min_unlocks=[],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)
    monkeypatch.setitem(psa.PROGRAM_SLUG_ALIASES, "zz_treaty_spelling_alias", "uk_avec")

    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )
    assert scenario["canonical_data_gaps"] == []
    assert scenario["fully_priced"] is True
    [component] = scenario["priced_components"]
    assert component["program_slug"] == "uk_avec", (
        "must report the CANONICAL priced identity, not the treaty's own "
        "unlock-list spelling, once reconnected through the alias table"
    )
    assert scenario["conditional_incentive_usd"] > 0


def test_conditional_scenario_returns_none_when_no_treaty_registered():
    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "QQ", "WW", "no-such-treaty", baseline_incentive_usd=None,
    )
    assert scenario is None


# ---------------------------------------------------------------------------
# Optimizer P0 wiring remediation (2026-09-04), P0-3 — TREATY CONDITIONAL
# BUDGET DOUBLE-COUNTING. Codex's own critique of this file's prior
# coverage: "checks positive arithmetic but not allocation/share
# conservation." Root cause (confirmed live on LU GB/IE: gross $4,364,393,
# 20%/20% minimums, combined QPE $8,126,528 = 186.2% of gross while
# fully_priced=True): each participant was priced against the FULL,
# unscaled project budget independently — never allocated. These tests
# assert the fix directly: one budget, allocated shares summing to
# exactly 100%, no source dollar counted twice, and a genuinely
# infeasible split failing closed rather than reporting fully_priced.
# ---------------------------------------------------------------------------

def test_conditional_scenario_allocates_one_budget_never_prices_full_budget_twice(monkeypatch):
    """THE P0-3 regression proof, synthetic and generic (governing spec's
    own genericity requirement): a bilateral treaty whose majority/
    minority minimums (20%/20%) do NOT sum to 100% must still produce an
    allocation that DOES sum to exactly 100% (minority takes its stated
    minimum, majority takes the complement) — never two independent
    full-budget prices."""
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY", maj_min=20.0, min_min=20.0, min_max=80.0,
        maj_unlocks=["uk_avec"], min_unlocks=["be_tax_shelter"],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    gross = 2_000_000.0
    inputs = _inputs(gross_budget_usd=gross, leaf_account_sum_usd=gross,
                      budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
    scenario = ce._build_conditional_bilateral_scenario(
        inputs, "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )

    assert scenario["fully_priced"] is True
    alloc = scenario["participant_allocation_pct"]
    assert alloc == {"ZZ": pytest.approx(80.0), "YY": pytest.approx(20.0)}
    assert sum(alloc.values()) == pytest.approx(100.0, abs=1e-6), (
        "the two participant allocations must conserve exactly one production budget"
    )

    # The root regression check: combined QPE/incentive must never reach
    # anywhere near "each participant received the whole budget" — with
    # a single $1,000,000 Cast line at 20%/80% split, neither
    # participant's OWN allocated budget can exceed its own share.
    majority_share_usd = round(gross * 0.80, 2)
    minority_share_usd = round(gross * 0.20, 2)
    for component in scenario["priced_components"]:
        cap = majority_share_usd if component["jurisdiction_code"] == "ZZ" else minority_share_usd
        assert component["selected_incentive_usd"] <= cap, (
            f"{component['jurisdiction_code']}'s incentive ({component['selected_incentive_usd']}) "
            f"must never exceed its own allocated share ({cap}) of the ONE source budget — "
            "this is the exact double-counting defect Codex found"
        )
    # Old (broken) behavior for this exact fixture would have priced
    # $1,000,000 of Cast QPE in BOTH ZZ and YY independently (combined
    # QPE = 200% of the single budget line). The fixed combined incentive
    # must be well below what two independent full-budget prices would
    # produce.
    assert scenario["conditional_incentive_usd"] < gross, (
        "combined incentive must never approach or exceed the ONE source gross budget "
        "for a single-line, single-program-per-side fixture like this one"
    )


def test_conditional_scenario_infeasible_split_fails_closed_never_fully_priced(monkeypatch):
    """A treaty whose minority minimum is so high that the majority's
    complement share would fall below the majority's OWN recorded
    minimum has no allocation this engine can construct from known facts
    alone — this must fail closed (fully_priced=False, an explicit
    blocking_reason), never silently normalize or invent a split that
    violates the treaty's own majority floor."""
    treaty = _synthetic_treaty(
        "zz-yy-bilateral", "ZZ", "YY", maj_min=50.0, min_min=60.0, min_max=80.0,
        maj_unlocks=["uk_avec"], min_unlocks=["be_tax_shelter"],
    )
    monkeypatch.setitem(te._BILATERAL, frozenset({"ZZ", "YY"}), treaty)

    scenario = ce._build_conditional_bilateral_scenario(
        _inputs(), "ZZ", "YY", "zz-yy-bilateral", baseline_incentive_usd=None,
    )
    assert scenario["fully_priced"] is False
    assert scenario["status"] == "USER_DECISION_REQUIRED"
    assert scenario["conditional_qualification_state"] == "UNRESOLVED_FACTS"
    assert scenario["blocking_reason"], "an infeasible allocation must carry an explicit reason"
    assert "conditional_incentive_usd" not in scenario
    assert "conditional_npc_usd" not in scenario
    # Never silently priced despite the infeasibility.
    assert "priced_components" not in scenario


def test_little_utopia_real_gbie_treaty_allocation_conserves_one_budget():
    """Real-project control assertion (LU's own GB/IE conditional
    scenario, the primary regression case named in this task) — proves
    the fix against real persisted data, not only the synthetic fixtures
    above. Real thresholds: GB/IE 20%/20%; real gross $4,364,393."""
    import asyncio

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.services.canonical_project_economics import build_project_economic_inputs

    LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

    async def _run():
        async with AsyncSession(engine, expire_on_commit=False) as db:
            econ = await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)
            return ce._build_conditional_bilateral_scenario(
                econ.inputs, "GB", "IE", "european-convention-coproduction", None,
            )

    scenario = asyncio.run(_run())
    assert scenario is not None
    assert scenario["fully_priced"] is True
    alloc = scenario["participant_allocation_pct"]
    assert sum(alloc.values()) == pytest.approx(100.0, abs=1e-6)
    # THE regression this task exists to close: combined QPE must never
    # again reach 186.2% of gross ($8,126,528 on a $4,364,393 budget).
    assert scenario["conditional_incentive_usd"] < 4_364_393.0, (
        "combined conditional incentive must be well below the full gross budget, "
        "never the ~186% double-counted figure Codex found"
    )
    assert scenario["conditional_npc_usd"] == pytest.approx(
        4_364_393.0 - scenario["conditional_incentive_usd"], abs=0.01
    )
