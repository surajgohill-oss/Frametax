"""LLS-CA-01: California Program 4.0 project eligibility -- at least 75% of the production budget spent in California OR at least 75% of
principal-photography days wholly in California (CFC Program Guidelines, January 1, 2026, section II.A.1; allocation letters on or after July
1, 2025). California-only VFX must not independently qualify a Manitoba-shot production.

DB-free and synthetic: components are built from explicit allocations. The Lips Like Sugar reconstruction at the bottom uses ONLY inputs retained
from a read-only extraction of the saved record (category totals of the 46 active budget lines and the figures of the stale saved row
51680824-eb85-4920-b124-04d0b6fce131, canonical-1.110.0); no real production is evaluated and nothing is written."""
from __future__ import annotations

import pytest

from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.calculators.project_eligibility_gates import GATE_FAILED_PREFIX, evaluate_project_gate
from app.calculators.structural_archetype_generator import StructuralComponent, generate_structural_candidate

MB, CA_PROGRAM = "ca_mb_film_video_credit", "ca_film_30"


def _alloc(code, amount, component, jur, line, category):
    return AccountAllocation(account_code=code, description=f"{category} {code}", amount_usd=amount, component=component, jurisdiction_code=jur,
                             assignment_kind=AssignmentKind.FIXED, rationale="control", governing_decision="control", line_id=line, spend_category=category)


def _comp(kind, jur, slug, allocs, facts=None):
    return StructuralComponent(component_type=kind, jurisdiction_code=jur, program_slug=slug, allocations=tuple(allocs),
                               spend_category_by_code={a.account_code: a.spend_category for a in allocs}, amount_facts=dict(facts or {}))


def _pp(jur, amount, line):         # a location-bound principal-photography account
    return _alloc(line, amount, "principal_photography", jur, line, "btl_crew_labor")


def _vfx(jur, amount, line="V"):
    return _alloc(line, amount, "vfx", jur, line, "vfx")


def _run(components, gross):
    return generate_structural_candidate(components, gross_budget_usd=gross)


def test_manitoba_principal_with_only_california_vfx_cannot_qualify_for_california():
    res = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 9_960_000.0, "P")]), _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", 40_000.0)])], 10_000_000.0)
    assert res.executable is False and res.rejection_reason.startswith(GATE_FAILED_PREFIX)
    assert "0.4% of the production budget" in res.rejection_reason and "0.0% of principal photography" in res.rejection_reason
    assert res.total_guaranteed_incentive_usd == 0.0 and res.blocking_pairs == ()


def test_spend_branch_passes_at_exactly_75_percent_and_fails_just_below():
    # California principal photography is in Manitoba, so only the spend branch can pass: 7.5m of 10m = 75.0%
    at = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 2_500_000.0, "P")]),
               _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", 7_500_000.0)])], 10_000_000.0)
    assert at.executable is True, at.rejection_reason
    below = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 2_501_000.0, "P")]),
                  _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", 7_499_000.0)])], 10_000_000.0)
    assert below.executable is False and below.rejection_reason.startswith(GATE_FAILED_PREFIX) and "75.0%" not in below.rejection_reason.split("spent there")[0][-8:]


def test_principal_photography_branch_passes_when_the_shoot_is_in_california_even_with_under_75_percent_of_spend():
    # 6m (60%) of spend is in California and ALL location-bound photography accounts are in California; 4m of post is routed to Newfoundland
    ok = _run([_comp("principal_production", "US-CA", CA_PROGRAM, [_pp("US-CA", 6_000_000.0, "P")]),
               _comp("post", "CA-NL", "ca_nl_all_spend_credit", [_alloc("S", 4_000_000.0, "post", "CA-NL", "S", "post_production")])], 10_000_000.0)
    assert ok.executable is True, ok.rejection_reason


def test_a_producer_stated_share_of_california_shooting_days_replaces_the_dollar_proxy():
    comps = lambda pct: [_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 9_000_000.0, "P")]),
                         _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", 1_000_000.0)], {"ca_principal_photography_days_in_california_pct": pct})]
    assert _run(comps(80.0), 10_000_000.0).executable is True            # 80% of days wholly in California satisfies the second branch
    failing = _run(comps(74.0), 10_000_000.0)
    assert failing.executable is False and "producer-stated 74.0%" in failing.rejection_reason


def test_gate_arithmetic_and_basis_are_reported():
    rows = [("CA-MB", 9_960_000.0, "principal_photography", "principal_production"), ("US-CA", 40_000.0, "vfx", "vfx")]
    out = evaluate_project_gate(CA_PROGRAM, "US-CA", rows, "CA-MB")
    assert out.passed is False and out.spend_share == pytest.approx(0.004) and out.photography_share == 0.0
    assert evaluate_project_gate(MB, "CA-MB", rows, "CA-MB") is None, "a program without a project-level gate is never gated"
    none_modeled = evaluate_project_gate(CA_PROGRAM, "US-CA", [("US-CA", 10.0, "vfx", "vfx")], None)
    assert none_modeled.passed is True and none_modeled.spend_share == 1.0


def test_programs_without_the_gate_and_all_california_structures_are_untouched():
    assert _run([_comp("principal_production", "US-CA", CA_PROGRAM, [_pp("US-CA", 5_000_000.0, "P")])], 5_000_000.0).executable is True
    mb_vfx = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 9_960_000.0, "P")]),
                   _comp("vfx", "CA-ON", "ontario_computer_animation_and_special_effects_tax_credit_ocase", [_vfx("CA-ON", 40_000.0)])], 10_000_000.0)
    assert not (mb_vfx.rejection_reason or "").startswith(GATE_FAILED_PREFIX)


# ── Lips Like Sugar: independent reconstruction from retained inputs (assumptions disclosed) ──────────────────────────────

#: Read-only extraction of the 46 active budget lines, 2026-10-11 (category -> USD). Sum = 11,983,654.00 = the saved gross.
LLS = {
    "miscellaneous": 2_385_314.0, "finance_costs": 1_700_000.0, "atl_producer": 1_414_198.0, "payroll_fringes": 1_091_423.0 + 255_291.0,
    "atl_cast": 863_388.0, "btl_set_construction": 808_296.0, "post_production": 571_710.0, "btl_transportation": 547_205.0, "contingency": 400_000.0,
    "residuals_reserve": 400_000.0, "atl_writer": 314_153.0, "atl_director": 267_384.0, "music": 206_774.0, "legal_accounting": 150_000.0,
    "completion_bond": 115_000.0, "insurance": 106_000.0, "production_sound": 87_067.0, "general_administration": 84_195.0, "btl_crew_labor": 76_175.0,
    "travel": 60_561.0, "vfx": 40_000.0, "sound": 39_520.0,
}
SAVED = {"gross": 11_983_654.0, "total_incentive": 4_263_644.30, "npc": 7_720_009.70, "mb_allocated": 11_943_654.0, "mb_floor": 4_249_644.30, "ca_allocated": 40_000.0, "ca_floor": 14_000.0}


def test_lls_retained_inputs_conserve_and_the_saved_row_is_arithmetically_consistent_only():
    assert round(sum(LLS.values()), 2) == SAVED["gross"]
    assert SAVED["mb_allocated"] + SAVED["ca_allocated"] == SAVED["gross"]
    assert round(SAVED["gross"] - SAVED["total_incentive"], 2) == SAVED["npc"] and SAVED["mb_floor"] + SAVED["ca_floor"] == pytest.approx(SAVED["total_incentive"])
    # the stale Manitoba floor is exactly 45% of a 9,443,654 base -- an all-spend base, not Manitoba LABOUR (canonical-1.110.0, before the 1.115 repair)
    assert SAVED["mb_floor"] == pytest.approx(0.45 * 9_443_654.0)


def test_lls_manitoba_california_hybrid_fails_the_california_gate_so_the_stale_row_cannot_stand():
    ca_spend_share = SAVED["ca_allocated"] / SAVED["gross"]
    assert ca_spend_share == pytest.approx(0.0033378, abs=1e-6) and ca_spend_share < 0.75
    # every non-VFX account is allocated to Manitoba under its real component label (location-bound accounts default to principal_photography)
    from app.calculators.production_allocation import COMPONENT_BY_SPEND_CATEGORY
    mb = _comp("principal_production", "CA-MB", MB, [
        _alloc(str(i), amount, COMPONENT_BY_SPEND_CATEGORY.get(cat, "principal_photography"), "CA-MB", str(i), cat)
        for i, (cat, amount) in enumerate(c for c in LLS.items() if c[0] != "vfx")])
    assert round(mb.allocated_usd, 2) == SAVED["mb_allocated"]
    ca = _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", LLS["vfx"])])
    res = _run([mb, ca], SAVED["gross"])
    assert res.executable is False and res.rejection_reason.startswith(GATE_FAILED_PREFIX), "the saved 4,263,644.30 row would now be RULE_REJECTED"
    assert "0.3% of the production budget" in res.rejection_reason and "0.0% of principal photography" in res.rejection_reason


def test_lls_independent_manitoba_reconstruction_against_the_stale_row_and_the_current_engine():
    """Hand reconstruction from the raw category totals; the assumptions are this test's contract, not engine output.
    A1 cost-of-salaries credit: 45% of labour = atl_producer + atl_cast + atl_writer + atl_director + btl_crew_labor (payroll fringes excluded as employer
       payroll deductions; 'miscellaneous' is unclassified and not assumed to be labour) = 2,935,298 -> 1,320,884.10
    A2 cost-of-production alternative: 30% of all eligible Manitoba expenditures. Assumed ineligible: finance costs 1,700,000, the unspent contingency
       400,000 and the residuals reserve 400,000 (obligations, not incurred spend). In-Manitoba travel 60,561 is assumed ELIGIBLE: the budget does not
       separate per diems / living expenses (ineligible) from other travel, so excluding it is a sensitivity (-18,168.30), not an assumption.
       Eligible (all production in Manitoba) = 11,983,654 - 2,500,000 = 9,483,654 -> 2,845,096.20
    The corporation claims one credit, so the planning figure is the larger (A2). California adds nothing (gate fails). The stale row's Manitoba floor
    (4,249,644.30) was 45% of a 9,443,654 ALL-SPEND base, which is not the cost-of-salaries base."""
    labour = sum(LLS[c] for c in ("atl_producer", "atl_cast", "atl_writer", "atl_director", "btl_crew_labor"))
    assert labour == 2_935_298.0 and round(0.45 * labour, 2) == 1_320_884.10
    eligible = SAVED["gross"] - LLS["finance_costs"] - LLS["contingency"] - LLS["residuals_reserve"]
    assert eligible == 9_483_654.0 and round(0.30 * eligible, 2) == 2_845_096.20
    sensitivity_no_travel = round(0.30 * (eligible - LLS["travel"]), 2)
    assert sensitivity_no_travel == 2_826_927.90 and round(2_845_096.20 - sensitivity_no_travel, 2) == 18_168.30
    planning = max(round(0.45 * labour, 2), round(0.30 * eligible, 2))
    new_npc = round(SAVED["gross"] - planning, 2)
    assert planning == 2_845_096.20 and new_npc == 9_138_557.80
    # the current engine, run on the same inputs as one all-Manitoba candidate (DB-free, no real project), reproduces the hand figure to the cent
    from app.calculators.production_allocation import COMPONENT_BY_SPEND_CATEGORY
    everything = _comp("principal_production", "CA-MB", MB, [
        _alloc(str(i), amount, COMPONENT_BY_SPEND_CATEGORY.get(cat, "principal_photography"), "CA-MB", str(i), cat) for i, (cat, amount) in enumerate(LLS.items())])
    res = _run([everything], SAVED["gross"])
    assert res.executable is True and res.total_guaranteed_incentive_usd == pytest.approx(planning) and res.npc_usd == pytest.approx(new_npc)
    # versus the stale row (canonical-1.110.0): overstated incentive and understated NPC by the same amount
    assert round(SAVED["total_incentive"] - planning, 2) == 1_418_548.10 and round(new_npc - SAVED["npc"], 2) == 1_418_548.10
