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
    assert "0.4% of the production budget" in res.rejection_reason and "ALL of its principal photography outside US-CA (explicit modeled scenario" in res.rejection_reason
    assert "not met in this modeled scenario" in res.rejection_reason, "a failure of the MODELED scenario, not a finding about an actual shoot"
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
    assert out.failed and out.spend_share == pytest.approx(0.004) and out.photography_share == 0.0
    assert evaluate_project_gate(MB, "CA-MB", rows, "CA-MB") is None, "a program without a project-level gate is never gated"
    none_modeled = evaluate_project_gate(CA_PROGRAM, "US-CA", [("US-CA", 10.0, "vfx", "vfx")], None)
    assert none_modeled.passed is True and none_modeled.spend_share == 1.0


# ── Codex finding 1: dollars do not establish shooting days (unknown / mixed / explicit entirely-outside / explicit entirely-inside) ──────────

def _outcome(pp_rows, spend_ca=10_000.0, other=990_000.0, primary="CA-MB", facts=None):
    rows = [("US-CA", spend_ca, "vfx", "vfx"), ("CA-MB", other, "above_the_line", "principal_production")] + pp_rows
    return evaluate_project_gate(CA_PROGRAM, "US-CA", rows, primary, facts)


def test_mixed_principal_photography_is_conditional_not_a_proven_pass_or_failure():
    # 40% of the location-bound accounts' dollars are in California: dollars do not establish that 75% of the DAYS are
    mixed = _outcome([("US-CA", 400_000.0, "principal_photography", "x"), ("CA-MB", 600_000.0, "principal_photography", "x")])
    assert mixed.conditional and not mixed.passed and not mixed.failed and mixed.photography_share is None
    assert mixed.reason.startswith("PROJECT_ELIGIBILITY_GATE_CONDITIONAL:") and "dollar shares do not establish shooting days" in mixed.reason
    # even 90% of the dollars in California cannot PROVE 75% of the days
    assert _outcome([("US-CA", 900_000.0, "principal_photography", "x"), ("CA-MB", 100_000.0, "principal_photography", "x")]).conditional


def test_unknown_principal_photography_is_conditional():
    assert _outcome([], primary=None).conditional


def test_explicitly_modeled_shoot_entirely_outside_fails_only_that_modeled_scenario_and_entirely_inside_passes():
    outside = _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")])
    assert outside.failed and "ALL of its principal photography outside US-CA (explicit modeled scenario; not an inferred dollar ratio)" in outside.reason
    inside = _outcome([("US-CA", 1_000_000.0, "principal_photography", "x")])
    assert inside.passed and inside.photography_share == 1.0 and "ALL of its principal photography in US-CA (explicit modeled scenario)" in inside.photography_basis
    # no photography accounts modeled: the modeled principal-production jurisdiction stands for the shoot
    assert _outcome([], primary="CA-MB").failed and _outcome([], primary="US-CA").passed


def test_a_known_passing_spend_branch_is_sufficient_whatever_the_photography_is():
    # California 7.5m of a 10m total (the 1m of photography is part of the remaining 2.5m): exactly 75.0%
    assert _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")], spend_ca=7_500_000.0, other=1_500_000.0).passed
    assert _outcome([("US-CA", 400_000.0, "principal_photography", "x"), ("CA-MB", 600_000.0, "principal_photography", "x")], spend_ca=7_100_000.0, other=1_900_000.0).passed


def test_a_stated_share_of_days_overrides_the_modeled_placement_in_both_directions():
    facts = lambda pct: {"ca_principal_photography_days_in_california_pct": pct}
    assert _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")], facts=facts(80.0)).passed
    assert _outcome([("US-CA", 1_000_000.0, "principal_photography", "x")], facts=facts(74.0)).failed


def test_a_conditional_gate_keeps_the_hybrid_visible_with_no_guaranteed_california_value():
    mixed = [_pp("CA-MB", 5_000_000.0, "P1"), _pp("US-CA", 3_000_000.0, "P2")]
    res = _run([_comp("principal_production", "CA-MB", MB, [mixed[0]]), _comp("vfx", "US-CA", CA_PROGRAM, [mixed[1], _vfx("US-CA", 40_000.0)])], 8_040_000.0)
    assert res.executable is True, res.rejection_reason
    ca = next(e for e in res.component_economics if e.component.jurisdiction_code == "US-CA")
    assert ca.is_guaranteed is False and ca.guaranteed_incentive_usd == 0.0 and ca.conditional_incentive_usd > 0.0
    assert ca.segment.ceiling_requires_confirmation and any(c["condition_id"] == "project-eligibility-days-undetermined" for c in ca.segment.ceiling_conditions)


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
    assert "0.3% of the production budget" in res.rejection_reason and "ALL of its principal photography outside US-CA (explicit modeled scenario" in res.rejection_reason


def _mb_component(include_vfx_line):
    from app.calculators.production_allocation import COMPONENT_BY_SPEND_CATEGORY
    return _comp("principal_production", "CA-MB", MB, [
        _alloc(str(i), amount, COMPONENT_BY_SPEND_CATEGORY.get(cat, "principal_photography"), "CA-MB", str(i), cat)
        for i, (cat, amount) in enumerate(c for c in LLS.items() if include_vfx_line or c[0] != "vfx")])


RESERVE = LLS["contingency"]          # the contingency-category line (the residuals reserve is a separate obligation, not the planning reserve)
ELIGIBLE_ALL_MB = SAVED["gross"] - LLS["finance_costs"] - LLS["contingency"] - LLS["residuals_reserve"]      # 9,483,654 (travel assumed eligible)
ELIGIBLE_SAME_ALLOCATION = ELIGIBLE_ALL_MB - LLS["vfx"]                                                      # 9,443,654 (the 40,000 VFX stays in California)


def test_lls_three_distinct_artifacts_rejected_hybrid_same_allocation_sensitivity_and_all_manitoba_alternative():
    """Codex finding 2. Three DIFFERENT things that must never be mixed:
    (1) the retained hybrid (Manitoba principal 11,943,654 + California VFX 40,000): in the modeled scenario the shoot is entirely in Manitoba, so the
        California gate FAILS and the hybrid is a rejected candidate, not a priced one (no NPC is claimed for it);
    (2) the SAME-ALLOCATION SENSITIVITY: the Manitoba leg alone on its own 11,943,654 allocation with the California VFX earning nothing. 30% x 9,443,654
        = 2,833,096.20; NPC arithmetic = gross 11,983,654 - 2,833,096.20 = 9,150,557.80. Arithmetic on the allocation, not a candidate and not certified QPE;
    (3) the RELOCATED ALL-MANITOBA ALTERNATIVE: the 40,000 VFX moved into Manitoba (a different structure with its own relocation cost, not computed here):
        30% x 9,483,654 = 2,845,096.20; NPC 9,138,557.80. The two Manitoba figures differ by exactly 30% x 40,000 = 12,000."""
    hybrid = _run([_mb_component(False), _comp("vfx", "US-CA", CA_PROGRAM, [_vfx("US-CA", LLS["vfx"])])], SAVED["gross"])
    assert hybrid.executable is False and hybrid.rejection_reason.startswith(GATE_FAILED_PREFIX) and hybrid.npc_usd is None, "(1) rejected, no NPC claimed"
    same = _run([_mb_component(False)], SAVED["gross"])
    assert round(0.30 * ELIGIBLE_SAME_ALLOCATION, 2) == 2_833_096.20 == pytest.approx(same.total_guaranteed_incentive_usd)
    assert same.npc_usd == pytest.approx(9_150_557.80) == pytest.approx(SAVED["gross"] - 2_833_096.20), "(2) same-allocation sensitivity"
    alt = _run([_mb_component(True)], SAVED["gross"])
    assert round(0.30 * ELIGIBLE_ALL_MB, 2) == 2_845_096.20 == pytest.approx(alt.total_guaranteed_incentive_usd)
    assert alt.npc_usd == pytest.approx(9_138_557.80), "(3) relocated all-Manitoba alternative"
    assert round(alt.total_guaranteed_incentive_usd - same.total_guaranteed_incentive_usd, 2) == 12_000.00 == round(0.30 * LLS["vfx"], 2)
    # hand cross-check of the labour credit, which never exceeds the cost-of-production alternative here
    labour = sum(LLS[c] for c in ("atl_producer", "atl_cast", "atl_writer", "atl_director", "btl_crew_labor"))
    assert labour == 2_935_298.0 and round(0.45 * labour, 2) == 1_320_884.10 < 2_833_096.20
    # versus the stale row: the stale Manitoba floor was 45% of a 9,443,654 ALL-SPEND base (the same-allocation eligible amount), not a labour base
    assert SAVED["mb_floor"] == pytest.approx(0.45 * ELIGIBLE_SAME_ALLOCATION) and round(SAVED["total_incentive"] - 2_833_096.20, 2) == 1_430_548.10


def test_lls_contingency_election_is_a_planning_cost_mechanism_separate_from_manitoba_qpe():
    """Codex finding 3. The Manitoba program has no contingency rule, so the 400,000 contingency line is excluded from QPE under EVERY election (verified
    below); the election changes only the PLANNING cost basis: planned cost = original gross - reserve x (1 - utilization), applied once to NPC. A reconciliation
    that treated the whole reserve as 'unspent' substituted an incurred-cost case for the planning case. No LLS contingency election is stored in the
    acceptance or shared database as of this read (state NOT_STATED, planned cost = gross), so the table below is the mechanism, not a saved value."""
    from app.calculators.allocation_pricing import price_segment
    from app.services.canonical_project_economics import contingency_planning_view
    cats = {str(i): c for i, (c, _) in enumerate(LLS.items())}
    allocs = list(_mb_component(True).allocations)
    floors = set()
    for pct in (None, 0.0, 50.0, 100.0):
        seg = price_segment("CA-MB", MB, allocs, cats, frozenset(), production_type="feature_film", gross_budget_usd=SAVED["gross"], contingency_expected_utilization_pct=pct)
        floors.add(seg.incentive_floor_usd)
        assert seg.excluded_usd == RESERVE, f"contingency excluded from Manitoba QPE under election {pct}"
    assert floors == {2_845_096.20}, "the Manitoba credit does not depend on the election"
    view = contingency_planning_view(SAVED["gross"], RESERVE, None)
    assert view["state"] == "NOT_STATED" and view["planned_cost_usd"] == SAVED["gross"] and view["undeployed_reserve_usd"] is None
    expected = {0.0: 8_750_557.80, 50.0: 8_950_557.80, 100.0: 9_150_557.80}              # same-allocation sensitivity NPC by election
    expected_alt = {0.0: 8_738_557.80, 50.0: 8_938_557.80, 100.0: 9_138_557.80}          # all-Manitoba alternative NPC by election
    for pct, npc in expected.items():
        view = contingency_planning_view(SAVED["gross"], RESERVE, pct)
        reduction = view["undeployed_reserve_usd"]
        assert view["planned_cost_usd"] == pytest.approx(SAVED["gross"] - RESERVE * (1 - pct / 100.0)) and view["original_gross_usd"] == SAVED["gross"]
        same = generate_structural_candidate([_mb_component(False)], gross_budget_usd=SAVED["gross"], planned_cost_reduction_usd=reduction)
        alt = generate_structural_candidate([_mb_component(True)], gross_budget_usd=SAVED["gross"], planned_cost_reduction_usd=reduction)
        assert same.npc_usd == pytest.approx(npc) and alt.npc_usd == pytest.approx(expected_alt[pct])
        assert round(SAVED["gross"] - reduction - 2_833_096.20, 2) == npc, "independent arithmetic: gross - undeployed reserve - incentive"


# ── Codex finding 1: dollars do not establish shooting days (unknown / mixed / explicit entirely-outside / explicit entirely-inside) ──────────

def _outcome(pp_rows, spend_ca=10_000.0, other=990_000.0, primary="CA-MB", facts=None):
    rows = [("US-CA", spend_ca, "vfx", "vfx"), ("CA-MB", other, "above_the_line", "principal_production")] + pp_rows
    return evaluate_project_gate(CA_PROGRAM, "US-CA", rows, primary, facts)


def test_mixed_principal_photography_is_conditional_not_a_proven_pass_or_failure():
    # 40% of the location-bound accounts' dollars are in California: dollars do not establish that 75% of the DAYS are
    mixed = _outcome([("US-CA", 400_000.0, "principal_photography", "x"), ("CA-MB", 600_000.0, "principal_photography", "x")])
    assert mixed.conditional and not mixed.passed and not mixed.failed and mixed.photography_share is None
    assert mixed.reason.startswith("PROJECT_ELIGIBILITY_GATE_CONDITIONAL:") and "dollar shares do not establish shooting days" in mixed.reason
    # even 90% of the dollars in California cannot PROVE 75% of the days
    assert _outcome([("US-CA", 900_000.0, "principal_photography", "x"), ("CA-MB", 100_000.0, "principal_photography", "x")]).conditional


def test_unknown_principal_photography_is_conditional():
    assert _outcome([], primary=None).conditional


def test_explicitly_modeled_shoot_entirely_outside_fails_only_that_modeled_scenario_and_entirely_inside_passes():
    outside = _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")])
    assert outside.failed and "ALL of its principal photography outside US-CA (explicit modeled scenario; not an inferred dollar ratio)" in outside.reason
    inside = _outcome([("US-CA", 1_000_000.0, "principal_photography", "x")])
    assert inside.passed and inside.photography_share == 1.0 and "ALL of its principal photography in US-CA (explicit modeled scenario)" in inside.photography_basis
    # no photography accounts modeled: the modeled principal-production jurisdiction stands for the shoot
    assert _outcome([], primary="CA-MB").failed and _outcome([], primary="US-CA").passed


def test_a_known_passing_spend_branch_is_sufficient_whatever_the_photography_is():
    # California 7.5m of a 10m total (the 1m of photography is part of the remaining 2.5m): exactly 75.0%
    assert _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")], spend_ca=7_500_000.0, other=1_500_000.0).passed
    assert _outcome([("US-CA", 400_000.0, "principal_photography", "x"), ("CA-MB", 600_000.0, "principal_photography", "x")], spend_ca=7_100_000.0, other=1_900_000.0).passed


def test_a_stated_share_of_days_overrides_the_modeled_placement_in_both_directions():
    facts = lambda pct: {"ca_principal_photography_days_in_california_pct": pct}
    assert _outcome([("CA-MB", 1_000_000.0, "principal_photography", "x")], facts=facts(80.0)).passed
    assert _outcome([("US-CA", 1_000_000.0, "principal_photography", "x")], facts=facts(74.0)).failed


def test_a_conditional_gate_keeps_the_hybrid_visible_with_no_guaranteed_california_value():
    mixed = [_pp("CA-MB", 5_000_000.0, "P1"), _pp("US-CA", 3_000_000.0, "P2")]
    res = _run([_comp("principal_production", "CA-MB", MB, [mixed[0]]), _comp("vfx", "US-CA", CA_PROGRAM, [mixed[1], _vfx("US-CA", 40_000.0)])], 8_040_000.0)
    assert res.executable is True, res.rejection_reason
    ca = next(e for e in res.component_economics if e.component.jurisdiction_code == "US-CA")
    assert ca.is_guaranteed is False and ca.guaranteed_incentive_usd == 0.0 and ca.conditional_incentive_usd > 0.0
    assert ca.segment.ceiling_requires_confirmation and any(c["condition_id"] == "project-eligibility-days-undetermined" for c in ca.segment.ceiling_conditions)


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
    assert "0.3% of the production budget" in res.rejection_reason and "ALL of its principal photography outside US-CA (explicit modeled scenario" in res.rejection_reason


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


# ── the allocated-structure kernel (price_allocated_structure) honours the same three outcomes ─────────────────────────────

def _allocated(splits, vfx_to_ca=True):
    from app.calculators.allocation_pricing import price_allocated_structure
    from app.calculators.production_allocation import StructureSpec, derive_account_allocation
    from app.calculators.qualification_derivation import BudgetLine
    lines = [BudgetLine(account_code="3000", description="CREW", amount_usd=8_000_000.0, spend_category="btl_crew_labor", is_memo=False, line_id="L-crew"),
             BudgetLine(account_code="6100", description="VFX", amount_usd=200_000.0, spend_category="vfx", is_memo=False, line_id="L-vfx")]
    cats = {"3000": "btl_crew_labor", "6100": "vfx"}
    spec = StructureSpec(structure_id="X", structure_type="hybrid", label="x", primary_jurisdiction="CA-MB", participants=("CA-MB", "US-CA"),
                         incentive_programs={"CA-MB": MB, "US-CA": CA_PROGRAM}, component_routes={"vfx": "US-CA"} if vfx_to_ca else {},
                         account_splits=splits)
    allocation = derive_account_allocation(lines, cats, spec)
    return price_allocated_structure(spec, allocation, cats, frozenset(), 8_200_000.0)


def test_allocated_structure_fails_the_modeled_outside_shoot_and_keeps_a_mixed_split_conditional():
    outside = _allocated({})
    assert outside.is_fully_priced is False and any(b.startswith(GATE_FAILED_PREFIX) for b in outside.blockers)
    ca_seg = next(s for s in outside.segments if s.jurisdiction_code == "US-CA")
    assert ca_seg.incentive_floor_usd == 0.0 and ca_seg.incentive_ceiling_usd == 0.0
    mixed = _allocated({"3000": {"CA-MB": 0.5, "US-CA": 0.5}})        # the shoot account is split 50/50: days undetermined
    ca_mixed = next(s for s in mixed.segments if s.jurisdiction_code == "US-CA")
    assert not any(b.startswith(GATE_FAILED_PREFIX) for b in mixed.blockers), mixed.blockers
    assert ca_mixed.incentive_floor_usd == 0.0 and ca_mixed.ceiling_requires_confirmation and any(
        c["condition_id"] == "project-eligibility-days-undetermined" for c in ca_mixed.ceiling_conditions)
