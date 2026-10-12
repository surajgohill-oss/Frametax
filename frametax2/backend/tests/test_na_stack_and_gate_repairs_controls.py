"""NA adjudication repairs, second pass (2026-10-12): whole-structure project gates (Minnesota, Pennsylvania, Massachusetts), Alabama's payroll-only 35%/45%, the
CPTC cost cap net of assistance in both the standalone kernel and the generator, the federal PSTC netting against only the labour portion of the Ontario OPSTC,
and the contingency deployment passthrough. DB-free and synthetic; every expectation is hand-derived from the primary text cited beside it.

Primary text (read 2026-10-12): Minn. Stat. 116U.27 subd. 1(h)(2) (project: taxpayer expended at least $1,000,000 in any consecutive 12-month period);
Massachusetts DOR Film Incentive Tax Credit (production expense credit needs Massachusetts production expenses to EXCEED 75% of total OR at least 75% of filming
days; payroll credit is separate, $50,000 minimum); Pennsylvania DCED guidelines via the adjudication (at least 60% of total production expenses in Pennsylvania);
Alabama DOR (25% of certain expenditures plus 35% of payroll paid to Alabama residents; 45% of resident payroll for total expenditures of $100,000-$499,999)."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401  (registers the rate rules)
from app.calculators.allocation_pricing import price_allocated_structure, price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind, StructureSpec, derive_account_allocation
from app.calculators.project_eligibility_gates import GATE_FAILED_PREFIX, evaluate_project_gate
from app.calculators.qualification_derivation import BudgetLine
from app.calculators.structural_archetype_generator import StructuralComponent, generate_structural_candidate

MB, MA, PA, MN, AL = "ca_mb_film_video_credit", "us_ma_film_tax_credit", "us_pa_film_production_credit", "us_mn_film_production_credit", "us_al_film_incentive"


def _alloc(code, amount, component, jur, line, category):
    return AccountAllocation(account_code=code, description=f"{category} {code}", amount_usd=amount, component=component, jurisdiction_code=jur,
                             assignment_kind=AssignmentKind.FIXED, rationale="control", governing_decision="control", line_id=line, spend_category=category)


def _comp(kind, jur, slug, allocs, facts=None):
    return StructuralComponent(component_type=kind, jurisdiction_code=jur, program_slug=slug, allocations=tuple(allocs),
                               spend_category_by_code={a.account_code: a.spend_category for a in allocs}, amount_facts=dict(facts or {}))


def _pp(jur, amount, line):
    return _alloc(line, amount, "principal_photography", jur, line, "btl_crew_labor")


def _run(components, gross):
    return generate_structural_candidate(components, gross_budget_usd=gross)


def _seg(res, slug):
    return next(c.segment for c in res.component_economics if c.component.program_slug == slug)


# ── Minnesota: at least $1,000,000 of eligible Minnesota production costs ──────────────────────────────────────────────────────────────────────

def test_minnesota_needs_one_million_of_minnesota_costs():
    short = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 1_800_000.0, "P")]),
                  _comp("vfx", "US-MN", MN, [_alloc("V", 200_000.0, "vfx", "US-MN", "V", "vfx")])], 2_000_000.0)
    assert short.executable is False and "us_mn_film_production_credit" in short.rejection_reason       # was priced at 50,000
    exact = _run([_comp("principal_production", "US-MN", MN, [_pp("US-MN", 1_000_000.0, "P")])], 1_000_000.0)
    assert exact.executable is True and exact.total_guaranteed_incentive_usd == pytest.approx(250_000.0)   # 25% x 1,000,000
    just_under = _run([_comp("principal_production", "US-MN", MN, [_pp("US-MN", 999_999.0, "P")])], 999_999.0)
    assert just_under.executable is False


# ── Pennsylvania: Pennsylvania production expenses at least 60% of the total ───────────────────────────────────────────────────────────────────

def test_pennsylvania_share_gate_fails_below_60_percent_and_passes_at_60():
    ten = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 1_800_000.0, "P")]),
                _comp("vfx", "US-PA", PA, [_alloc("V", 200_000.0, "vfx", "US-PA", "V", "vfx")])], 2_000_000.0)
    assert ten.executable is False and ten.rejection_reason.startswith(GATE_FAILED_PREFIX) and "10.0%" in ten.rejection_reason
    at = _run([_comp("principal_production", "US-PA", PA, [_pp("US-PA", 1_200_000.0, "P")]),
               _comp("vfx", "CA-MB", MB, [_alloc("V", 800_000.0, "vfx", "CA-MB", "V", "vfx")])], 2_000_000.0)
    assert at.executable is True, at.rejection_reason
    assert _seg(at, PA).incentive_floor_usd == pytest.approx(300_000.0)                       # 25% x 1,200,000 (the +5% facility uplift stays a ceiling)
    below = _run([_comp("principal_production", "US-PA", PA, [_pp("US-PA", 1_198_000.0, "P")]),
                  _comp("vfx", "CA-MB", MB, [_alloc("V", 802_000.0, "vfx", "CA-MB", "V", "vfx")])], 2_000_000.0)
    assert below.executable is False and below.rejection_reason.startswith(GATE_FAILED_PREFIX)


# ── Massachusetts: the NON-PAYROLL credit needs >75% of expenses or >=75% of filming days; payroll has its own test ─────────────────────────

def _ma_structure(extra_ma_allocs, facts=None, principal=1_500_000.0):
    ma = [_alloc("W", 300_000.0, "vfx", "US-MA", "W", "btl_resident_labor"), *extra_ma_allocs]
    return _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", principal, "P")]), _comp("vfx", "US-MA", MA, ma, facts)], principal + sum(a.amount_usd for a in ma))


def test_massachusetts_non_payroll_costs_are_excluded_when_the_75_percent_test_fails_but_payroll_stays():
    res = _ma_structure([_alloc("V", 200_000.0, "vfx", "US-MA", "V", "vfx")])
    seg = _seg(res, MA)
    assert res.executable is True, res.rejection_reason
    assert seg.incentive_floor_usd == pytest.approx(75_000.0)           # 25% x payroll 300,000 only; the 200,000 VFX earns nothing (was 125,000)
    assert seg.qpe_usd == pytest.approx(300_000.0) and seg.excluded_usd == pytest.approx(200_000.0)
    assert any(n.startswith(GATE_FAILED_PREFIX) for n in seg.notes)
    only_vfx = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 1_800_000.0, "P")]),
                     _comp("vfx", "US-MA", MA, [_alloc("V", 200_000.0, "vfx", "US-MA", "V", "vfx")])], 2_000_000.0)
    assert only_vfx.executable is False                                  # nothing but non-payroll: no credit remains, the candidate stays visible and unpriced


def test_massachusetts_stated_filming_days_restore_the_non_payroll_credit_and_unknown_days_make_it_conditional():
    vfx = [_alloc("V", 200_000.0, "vfx", "US-MA", "V", "vfx")]
    stated = _ma_structure(vfx, {"ma_filming_days_in_massachusetts_pct": 80.0})
    assert _seg(stated, MA).incentive_floor_usd == pytest.approx(125_000.0)        # 25% x (300,000 + 200,000)
    short = _ma_structure(vfx, {"ma_filming_days_in_massachusetts_pct": 74.0})
    assert _seg(short, MA).incentive_floor_usd == pytest.approx(75_000.0)
    # mixed modeled photography (some in Massachusetts, most in Manitoba): days undetermined -> payroll guaranteed, non-payroll a disclosed conditional ceiling
    ma = [_pp("US-MA", 100_000.0, "PM"), _alloc("V", 200_000.0, "vfx", "US-MA", "V", "vfx")]
    cond = _run([_comp("principal_production", "CA-MB", MB, [_pp("CA-MB", 1_700_000.0, "P")]), _comp("vfx", "US-MA", MA, ma)], 2_000_000.0)
    seg = _seg(cond, MA)
    assert cond.executable is True, cond.rejection_reason
    assert seg.incentive_floor_usd == pytest.approx(25_000.0) and seg.incentive_ceiling_usd == pytest.approx(75_000.0)     # 25% x 100,000 payroll / x 300,000 all
    assert seg.ceiling_requires_confirmation and any(c["condition_id"] == "project-eligibility-days-undetermined" for c in seg.ceiling_conditions)


def test_massachusetts_spend_share_must_exceed_not_merely_equal_75_percent():
    rows = lambda ma: [("CA-MB", 1_000_000.0 - ma, "principal_photography", "principal_production"), ("US-MA", ma, "vfx", "vfx")]
    assert evaluate_project_gate(MA, "US-MA", rows(750_000.0), "CA-MB").status != "PASS"        # exactly 75.0% does not EXCEED 75%
    assert evaluate_project_gate(MA, "US-MA", rows(750_001.0), "CA-MB").passed


def test_the_allocated_structure_path_applies_the_same_gates():
    lines = [BudgetLine(account_code="3000", description="CREW", amount_usd=8_000_000.0, spend_category="btl_crew_labor", is_memo=False, line_id="L-crew"),
             BudgetLine(account_code="6100", description="VFX", amount_usd=200_000.0, spend_category="vfx", is_memo=False, line_id="L-vfx")]
    cats = {"3000": "btl_crew_labor", "6100": "vfx"}
    for slug, jur in ((PA, "US-PA"), (MA, "US-MA")):
        spec = StructureSpec(structure_id="X", structure_type="hybrid", label="x", primary_jurisdiction="CA-MB", participants=("CA-MB", jur),
                             incentive_programs={"CA-MB": MB, jur: slug}, component_routes={"vfx": jur})
        priced = price_allocated_structure(spec, derive_account_allocation(lines, cats, spec), cats, frozenset(), 8_200_000.0)
        seg = next(s for s in priced.segments if s.jurisdiction_code == jur)
        assert seg.incentive_floor_usd == 0.0 and seg.executable is False, slug
        assert any("PROJECT_ELIGIBILITY_GATE_FAILED" in b for b in seg.blockers) or any(GATE_FAILED_PREFIX in b for b in priced.blockers), slug


# ── Alabama: the 35% (45% small budget) applies to resident payroll only ───────────────────────────────────────────────────────────────────────

def _al(rows, gross, facts=frozenset()):
    a = [_alloc(str(i), m, "principal_production", "US-AL", f"L{i}", c) for i, (c, m) in enumerate(rows)]
    return price_segment("US-AL", AL, a, {x.account_code: x.spend_category for x in a}, frozenset(), gross_budget_usd=gross, evidenced_requirement_facts=facts)


def test_alabama_prices_a_non_payroll_service_at_25_percent_and_resident_payroll_only_at_35():
    assert _al([("vfx", 200_000.0)], 2_000_000.0).incentive_floor_usd == pytest.approx(50_000.0)         # 25% (was 70,000 at 35%)
    unproven = _al([("btl_resident_labor", 100_000.0), ("vfx", 200_000.0)], 2_000_000.0)
    assert unproven.incentive_floor_usd == pytest.approx(75_000.0) and unproven.incentive_ceiling_usd == pytest.approx(85_000.0)   # the +10 points is a bound
    proven = _al([("btl_resident_labor", 100_000.0), ("vfx", 200_000.0)], 2_000_000.0, frozenset({"al_all_payroll_to_alabama_residents"}))
    assert proven.incentive_floor_usd == pytest.approx(85_000.0)                                          # 25% x 300,000 + 10% x 100,000 resident payroll


def test_alabama_small_budget_bracket_is_45_percent_of_resident_payroll_between_100k_and_499999():
    fact = frozenset({"al_all_payroll_to_alabama_residents"})
    small = _al([("btl_resident_labor", 100_000.0), ("vfx", 300_000.0)], 400_000.0, fact)
    assert small.incentive_floor_usd == pytest.approx(120_000.0)                                          # 25% x 400,000 + 20% x 100,000 = 45% on payroll
    boundary = _al([("btl_resident_labor", 100_000.0), ("vfx", 399_999.0)], 499_999.0, fact)
    assert boundary.incentive_floor_usd == pytest.approx(0.25 * 499_999.0 + 0.20 * 100_000.0)
    over = _al([("btl_resident_labor", 100_000.0), ("vfx", 400_000.0)], 500_000.0, fact)
    assert over.incentive_floor_usd == pytest.approx(0.25 * 500_000.0 + 0.10 * 100_000.0)                 # above 499,999 the general 35% applies
    below = _al([("btl_resident_labor", 50_000.0), ("vfx", 40_000.0)], 90_000.0, fact)
    assert below.incentive_floor_usd == pytest.approx(0.25 * 90_000.0 + 0.10 * 50_000.0)                  # under 100,000 the small-budget bracket does not apply


# ── CPTC: the standalone cap is net of stated assistance, and agrees with the stack arithmetic ────────────────────────────────────────────────

def test_the_standalone_cptc_cap_is_net_of_stated_assistance_exactly_as_the_stack_engine_computes_it():
    from app.calculators.canonical_stack_bridge import cptc_net_cost_adjusted
    a = [_alloc("1", 1_400_000.0, "principal_production", "CA", "L0", "btl_crew_labor"), _alloc("2", 600_000.0, "principal_production", "CA", "L1", "btl_equipment_rental")]
    cats = {x.account_code: x.spend_category for x in a}
    price = lambda facts: price_segment("CA", "ca_federal_cptc", a, cats, frozenset(), gross_budget_usd=2_000_000.0, amount_facts=facts)
    assert price({}).incentive_floor_usd == pytest.approx(300_000.0)                                      # 25% x min(1,400,000; 60% x 2,000,000)
    stated = price({"ca_federal_cptc_assistance_usd": 400_000.0})
    assert stated.incentive_floor_usd == pytest.approx(240_000.0)                                         # 25% x min(1,400,000; 60% x (2,000,000 - 400,000) = 960,000)
    adjusted, cap, qualified = cptc_net_cost_adjusted(350_000.0, 0.25, 1_400_000.0, 2_000_000.0, 400_000.0, 0.0)
    assert (cap, qualified, adjusted) == (960_000.0, 960_000.0, 240_000.0)                                # the stack engine reaches the same credit


def test_a_hybrid_cptc_with_stack_assistance_matches_the_stack_formula():
    from app.calculators.canonical_stack_bridge import cptc_net_cost_adjusted
    res = _run([_comp("principal_production", "CA", "ca_federal_cptc", [_alloc("1", 1_500_000.0, "principal_production", "CA", "L0", "atl_director")]),
                _comp("principal_production", "CA-ON", "on_opstc", [_alloc("2", 1_000_000.0, "principal_production", "CA-ON", "L1", "atl_director")])], 2_500_000.0)
    assert res.executable is True, res.rejection_reason
    expected, *_ = cptc_net_cost_adjusted(375_000.0, 0.25, 1_500_000.0, 2_500_000.0, 0.0, 215_000.0)
    assert res.post_adjustment_component_incentives_usd["ca_federal_cptc"] == pytest.approx(expected) == pytest.approx(342_750.0)


# ── Federal PSTC with the Ontario OPSTC: only the OPSTC labour portion is assistance ───────────────────────────────────────────────────────────

def test_the_generator_nets_only_the_opstc_labour_portion_against_the_federal_pstc():
    res = _run([_comp("principal_production", "CA", "ca_federal_pstc", [_alloc("1", 600_000.0, "principal_production", "CA", "L0", "btl_crew_labor")]),
                _comp("principal_production", "CA-ON", "on_opstc", [_alloc("2", 1_000_000.0, "principal_production", "CA-ON", "L1", "btl_crew_labor")])], 1_600_000.0)
    assert res.executable is True, res.rejection_reason
    raw = res.raw_component_incentives_usd
    assert raw["ca_federal_pstc"] == pytest.approx(96_000.0) and raw["on_opstc"] == pytest.approx(215_000.0)      # 16% x 600,000 ; 21.5% x 1,000,000
    # labour portion of the OPSTC = 21.5% x labour 600,000 = 129,000; PSTC reduction = 129,000 x 16% = 20,640 (the whole-credit reading: 34,400)
    assert res.post_adjustment_component_incentives_usd["ca_federal_pstc"] == pytest.approx(75_360.0)
    assert res.total_guaranteed_incentive_usd == pytest.approx(290_360.0)


# ── Contingency deployment (eligible destination category) reaches component pricing on the same terms as the allocated path ─────────────────────

def test_a_deployed_contingency_reserve_is_priced_by_its_destination_category_through_the_generator_and_the_allocated_path():
    from app.calculators.contingency_treatment import ContingencyAllocation, ContingencyDeployment, add_deployment
    comp = _comp("principal_production", "US-GA", "us_ga_film_credit",
                 [_alloc("3000", 1_000_000.0, "principal_production", "US-GA", "L0", "btl_crew_labor"),
                  _alloc("7902", 250_000.0, "principal_production", "US-GA", "L1", "contingency")])
    base = generate_structural_candidate([comp], gross_budget_usd=1_250_000.0)
    assert base.executable is True, base.rejection_reason
    deployed = add_deployment(
        ContingencyAllocation(source_account_code="7902", source_description="CONTINGENCY", original_amount_usd=250_000.0),
        ContingencyDeployment(destination_account_code="3000", destination_description="crew overage", destination_spend_category="btl_crew_labor",
                              amount_usd=100_000.0, note="control", deployed_by="control", deployed_at="2026-10-12"))
    through_generator = generate_structural_candidate([comp], gross_budget_usd=1_250_000.0, contingency_allocations={"7902": deployed})
    assert _seg(through_generator, "us_ga_film_credit").qpe_usd == pytest.approx(_seg(base, "us_ga_film_credit").qpe_usd + 100_000.0)
    direct = price_segment("US-GA", "us_ga_film_credit", list(comp.allocations), comp.spend_category_by_code, frozenset(), gross_budget_usd=1_250_000.0,
                           contingency_allocations={"7902": deployed})
    assert _seg(through_generator, "us_ga_film_credit").qpe_usd == pytest.approx(direct.qpe_usd)          # identical eligible deployment in both pricing paths
    assert _seg(through_generator, "us_ga_film_credit").incentive_floor_usd == pytest.approx(direct.incentive_floor_usd)
