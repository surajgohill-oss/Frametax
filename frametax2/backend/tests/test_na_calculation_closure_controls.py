"""NA-RECONCILIATION-13: the statute-read rate, base, cap, timing and dependency controls. Synthetic and DB-free; every expectation is hand arithmetic from the primary text cited beside it
(RSMo 135.750; W. Va. Code 11-13X; N.J.S.A. 54:10A-5.39b; Ark. Code 15-4-2005 as amended by Act 517 of 2023; MCA 15-31-1005/1007/1010; ORC 122.85; Income Tax Act (BC) s.81.2 and B.C. Reg. 4/99;
O. Reg. 37/09; LISR art. 189; Telefilm Canada Production Program Guidelines applicable October 31, 2025)."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from tests.test_na_stack_and_gate_repairs_controls import _alloc

Q, X = QualificationState.QUALIFIES, QualificationState.EXCLUDED
NJ, AR, MO, MT, WV, OH = ("us_nj_garden_state_film_credit", "us_ar_digital_motion_picture_incentive", "us_mo_motion_media_production_tax_credit", "us_mt_media_act_tax_credit",
                          "us_wv_film_production_tax_credit", "us_oh_motion_picture_tax_credit")
TYPE = {"employee": 1, "individual_contractor": 2, "loan_out_corp": 3}


def _reg(slug, rows, payees=None, types=None):
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="US", ny_atl_payee_by_line=tuple((payees or {}).items()), payee_type_by_line=tuple((types or {}).items()))
    return derive_qualification_register(lines, program_slug=slug, facts=pf, rate=0.2, rules=get_program_rules(slug), doctrine=resolve_program_doctrine(slug).doctrine)


def _sum(reg, state, needle="", line=None):
    return round(sum(a.amount_usd for a in reg if a.state == state and needle in a.reason and (line is None or a.line_id == line)), 2)


def _segment(jur, slug, rows, facts=frozenset(), gross_factor=1.4):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS      # the producer-controlled administrative assumptions every real pricing path unions in
    facts = frozenset(facts) | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    allocs = [_alloc(str(3100 + i), amt, "production", jur, f"S{i}", cat) for i, (cat, amt) in enumerate(rows)]
    total = sum(a for _c, a in rows)
    return price_segment(jurisdiction_code=jur, program_slug=slug, allocations=allocs, spend_category_by_code={a.account_code: a.spend_category for a in allocs},
                         offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=total * gross_factor, evidenced_requirement_facts=frozenset(facts))


# ── New Jersey: USD 750,000 per highly compensated individual (writers, directors, producers, performers); crew are not in the group ───────────────────────────────────────────────
def test_new_jersey_excludes_pay_above_750000_for_an_identified_director_but_never_for_crew():
    rows = (("atl_director", 1_000_000.0), ("btl_crew_labor", 1_200_000.0))
    reg = _reg(NJ, rows, payees={"L0": 1, "L1": 2}, types={"L0": TYPE["employee"], "L1": TYPE["employee"]})
    assert _sum(reg, X, "750,000", line="L0") == 250_000.0 and _sum(reg, Q, line="L0") == 750_000.0       # 1,000,000 - 750,000
    assert _sum(reg, X, line="L1") == 0.0 and _sum(reg, Q, line="L1") == 1_200_000.0                      # crew above 750,000 are not capped (not writers, directors, producers or performers)


def test_new_jersey_unidentified_payee_stays_qualified_with_an_unresolved_note():
    reg = _reg(NJ, (("atl_cast", 900_000.0), ("btl_crew_labor", 1_000_000.0)))
    assert _sum(reg, X) == 0.0 and _sum(reg, Q, "UNRESOLVED", line="L0") == 900_000.0


# ── Arkansas: wages limited to the first USD 500,000 per employee (W-2 payees) ──────────────────────────────────────────────────────────────────────────────────────────────────────
def test_arkansas_caps_an_identified_employee_but_not_a_loan_out():
    rows = (("atl_director", 700_000.0), ("btl_crew_labor", 3_000_000.0))
    emp = _reg(AR, rows, payees={"L0": 1}, types={"L0": TYPE["employee"]})
    assert _sum(emp, X, "500,000", line="L0") == 200_000.0 and _sum(emp, Q, line="L0") == 500_000.0
    loan = _reg(AR, rows, payees={"L0": 1}, types={"L0": TYPE["loan_out_corp"]})
    assert _sum(loan, X) == 0.0 and _sum(loan, Q, line="L0") == 700_000.0


# ── Missouri: above-the-line compensation counts only up to 25% of overall qualifying expenses ─────────────────────────────────────────────────────────────────────────────────────
def test_missouri_limits_above_the_line_compensation_to_a_quarter_of_the_qualifying_total():
    # Missouri crew 600,000 + director 400,000: the 25% limit is on the total INCLUDING the capped group, so T = 600,000 + 0.25 T -> T = 800,000, director counted 200,000.
    seg = _segment("US-MO", MO, (("btl_crew_labor", 600_000.0), ("atl_director", 400_000.0)))
    assert seg.executable
    assert seg.qpe_usd == pytest.approx(800_000.0)
    assert seg.incentive_floor_usd == pytest.approx(160_000.0)                                           # 20% x 800,000
    below = _segment("US-MO", MO, (("btl_crew_labor", 900_000.0), ("atl_director", 100_000.0)))
    assert below.qpe_usd == pytest.approx(1_000_000.0) and below.incentive_floor_usd == pytest.approx(200_000.0)   # 10% above the line: no limit binds


def test_missouri_is_not_refundable_sunsets_in_2029_and_shows_the_statutory_42_percent_ceiling():
    from app.data.program_requirements import get_program_requirements
    from app.data.program_rate_rules_worldwide import US_MO_DOCTRINE as d
    prof = get_program_requirements(MO)
    assert d.is_refundable is False and d.is_transferable is True and prof.refundable is False and prof.sunset_date == "2029-12-31"
    assert {t.rate for t in d.tiers} == {0.20, 0.42}
    ceiling = next(t for t in d.tiers if t.is_band_ceiling)
    assert {c.required_boolean_fact_key for c in ceiling.conditions} == {
        "mo_filmed_50pct_in_missouri_confirmed", "mo_rural_or_blighted_15pct_confirmed", "mo_three_departments_missouri_hires_confirmed",
        "mo_script_markets_missouri_confirmed", "mo_second_third_fourth_class_county_confirmed"}                # 22% (20 + 10% of 20) + 4 x 5% = 42%
    base = next(t for t in d.tiers if not t.is_band_ceiling)
    assert {c.required_boolean_fact_key for c in base.conditions if c.required_boolean_fact_key} == {"mo_apprentice_or_veteran_minimum_confirmed"}


# ── West Virginia: nonrefundable, transferable, sunset for expenditures after December 31, 2027 ───────────────────────────────────────────────────────────────────────────────
def test_west_virginia_is_nonrefundable_transferable_and_ends_with_2027():
    from app.data.program_requirements import get_program_requirements
    from app.data.program_rate_rules_worldwide import US_WV_DOCTRINE as d
    prof = get_program_requirements(WV)
    assert d.is_refundable is False and d.is_transferable is True and prof.refundable is False and prof.sunset_date == "2027-12-31" and prof.min_local_spend_usd == 50_000.0
    assert {t.rate for t in d.tiers} == {0.27, 0.31}


# ── New Jersey record: 2049 sunset, USD 100 million a fiscal year, first-come order, no refund ────────────────────────────────────────────────────────────────────────────────────
def test_new_jersey_record_carries_the_statute_not_the_older_page():
    from app.data.program_requirements import AllocationType, get_program_requirements
    from app.data.program_rate_rules_worldwide import US_NJ_DOCTRINE as d
    prof = get_program_requirements(NJ)
    assert prof.sunset_date == "2049-07-01" and prof.annual_program_cap_usd == 100_000_000.0 and prof.allocation_type == AllocationType.FIRST_COME_FIRST_SERVED
    assert d.is_refundable is False and d.is_transferable is True and prof.per_person_cap_usd == 750_000.0
    assert _segment("US-NJ", NJ, (("btl_crew_labor", 2_000_000.0),)).incentive_floor_usd == pytest.approx(600_000.0)     # 30% radius rate guaranteed on 2,000,000


# ── Arkansas: the add-on arithmetic is resolved by the statute, selection stays discretionary ──────────────────────────────────────────────────────────────────────────────────
def test_arkansas_add_ons_are_capped_at_thirty_percent_by_the_statute_and_remain_a_ceiling():
    from app.data.program_rate_rules_worldwide import US_AR_DOCTRINE as d
    assert "(f) 'The maximum total tax incentives" in d.citation and "thirty percent (30%)" in d.citation and "multi-project" in d.citation and "RESOLVED" in d.provenance.interpretation_note
    seg = _segment("US-AR", AR, (("btl_crew_labor", 1_000_000.0),))
    assert seg.incentive_floor_usd == 0.0 and seg.ceiling_requires_confirmation and seg.incentive_ceiling_usd == pytest.approx(300_000.0)


# ── Montana: statute caps, threshold and sunset ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_montana_record_carries_the_statute_cap_threshold_and_sunset():
    from app.data.program_requirements import get_program_requirements
    from app.data.program_rate_rules_worldwide import US_MT_DOCTRINE as d
    prof = get_program_requirements(MT)
    assert d.annual_cap_usd == 12_000_000.0 and prof.annual_program_cap_usd == 12_000_000.0 and prof.min_local_spend_usd == 350_000.0
    assert prof.sunset_date == "2045-12-31" and prof.refundable is False and prof.transferable is True
    seg = _segment("US-MT", MT, (("btl_crew_labor", 1_000_000.0),))
    # Restated in NA-RECONCILIATION-19. 1,000,000 of crew labour is COMPENSATION, which is not a 'production expenditure' (MCA 15-31-1003(13)(b)(i)); it earns the category credits (up to 30% each) plus the
    # additions, every credit limited to 35% of base investment (15-31-1007(3)(a)): unknown inputs bound the potential at 35% x 1,000,000 = 350,000. Still no guaranteed credit while certification is paused.
    assert seg.incentive_floor_usd == 0.0 and seg.incentive_ceiling_usd == pytest.approx(350_000.0)


# ── Ohio: authoritative silence on transfer and sunset ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_ohio_is_refundable_and_not_transferable_with_no_sunset():
    from app.data.program_requirements import get_program_requirements
    prof = get_program_requirements(OH)
    assert prof.refundable is True and prof.transferable is False and prof.sunset_date is None


# ── BC DAVE: the host credit is derived from the structure, never stated ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_dave_is_a_presumption_alone_and_clean_when_the_structure_holds_its_host():
    from app.optimization.structural_prerequisites import host_present, structure_derived_facts
    rows = (("vfx", 600_000.0),)
    alone = _segment("CA-BC", "ca_bc_dave", rows)
    assert alone.incentive_floor_usd == pytest.approx(96_000.0)                                              # 16% x 600,000 VFX labour (11% + 5% prescribed, B.C. Reg. 4/99 s.13)
    assert "ca-bc-dave-host-credit-in-structure" in {p["condition_id"] for p in alone.presumed_facts}
    assert structure_derived_facts("ca_bc_dave", ["ca_bc_dave"]) == frozenset()
    facts = structure_derived_facts("ca_bc_dave", ["ca_bc_dave", "ca_bc_film_tv_tax_credit"])
    assert facts == frozenset({"ca_bc_dave__structure_host_credit_present"})
    assert structure_derived_facts("ca_bc_dave", ["ca_bc_dave", "ca_bc_pstc"]) == facts
    assert host_present("ca_bc_dave", ["ca_bc_film_tv_tax_credit"]) and not host_present("ca_bc_dave", ["ca_federal_cptc"])
    hosted = _segment("CA-BC", "ca_bc_dave", rows, facts=facts)
    assert hosted.incentive_floor_usd == pytest.approx(96_000.0)
    assert "ca-bc-dave-host-credit-in-structure" not in {p["condition_id"] for p in hosted.presumed_facts}


def test_dave_rate_record_states_the_statute_and_regulation():
    from app.data.program_rate_rules_worldwide import CA_BC_DAVE_DOCTRINE as d
    assert d.confidence_tier == "VERIFIED" and d.tiers[0].rate == 0.16
    for needle in ("s.81.2(8)", "11%", "13(1)-(2)", "October 1, 2016", "s.83.1", "10.1", "s.85(4)"):
        assert needle in d.citation, needle


# ── Federal PSTC allocation: a statutory reasonableness test, no formula ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_all_spend_allocation_residual_names_the_statutory_test_and_the_needed_authority():
    from app.services.na_canonical_reconciliation import RESIDUALS
    r = next(x for x in RESIDUALS if x["id"] == "ALLOCATION-QC-MB-NL")
    assert "can reasonably be considered to be in respect of" in r["what"] and "s.90(4)" in r["what"] and "CRA written position" in r["need"]
    assert "ASSUMED ALLOCATION" in r["treatment"] and "VERIFIED NETTING" in r["treatment"]


# ── Selective funds: reclassified on primary text, never priced ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("slug", ["ca_cmf", "nohfc_production_fund", "us_sundance_doc", "us_itvs_fund", "mx_eficine_incentive", "ca_telefilm_dev", "ca_bell_fund"])
def test_selective_funds_carry_the_selective_state_and_block_economic_candidacy(slug):
    from app.data import authority_coverage_registry as acr
    assert acr.coverage_state(slug) == "NON_GUARANTEED_SELECTIVE" and acr.blocks_economic_candidacy(slug)


def test_the_cmpa_foreign_spelling_is_retired_to_the_federal_pstc():
    from app.data.program_slug_aliases import canonical_slug
    from app.calculators.canonical_stack_bridge import load_named_pair_rule
    assert canonical_slug("ca_cmpa_foreign") == "ca_federal_pstc"
    rule = load_named_pair_rule("ca_cmpa_foreign", "on_ofttc")
    assert rule is not None and rule["rule_type"] == "spend_reduction"
