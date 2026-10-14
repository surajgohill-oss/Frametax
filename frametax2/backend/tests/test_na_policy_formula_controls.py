"""NA-RECONCILIATION-19: Montana compensation credits and first credit year, New Brunswick deemed spend and Micro stream, Nova Scotia supplier residency and per-individual cap, Saskatchewan potential.

Synthetic and DB-free; hand arithmetic from the cited text.
- MCA 15-31-1007(3) / 15-31-1003(13): compensation is NOT a production expenditure; it earns 25% (resident crew, USD 150,000 credit per person), 15% (non-resident with Montana tax withheld, USD 150,000 per
  person), 20% of the first USD 7.5 million (actors / directors / producers / writers), 30% (students, USD 50,000 each), 30% (resident veterans / tribal members, USD 150,000 each); +10% college payments,
  +10% studio rental of 20 days or more, +5% underserved area, +5% of base investment with a Montana screen credit; everything limited to 35% of base investment. Department of Revenue: first credit year 2031.
- LIFT 2026/2027: Total NB Spend may include up to 15% eligible deemed spend; Micro Production = up to 30% to a maximum of CAD 100,000 for total budgets under CAD 400,000; Major needs NB spend of at least 20%.
- NSFPIF s.3.2(d), s.3.2(b), s.4: no individual may receive more than CAD 150,000 of incentive; ineligible supplier spend and Equity Tax Credit Act financing leave the base.
- Creative Saskatchewan FFTV 2026-27: 51% activity test gates the bonuses; Saskatchewan Stream +5, Rural +5 (more than half of days 50 km+ outside Regina/Saskatoon), Post +5, Volume +10; totals 40% / 35%."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import _price_statutory_formula, price_segment
from app.data.program_rate_rules import get_subset_uplift_rules
from tests.test_na_stack_and_gate_repairs_controls import _alloc

MT, NB, NS, SK = "us_mt_media_act_tax_credit", "ca_nb_film_tax_credit", "ca_ns_production_incentive_fund", "ca_sk_creative_saskatchewan_grant"


def _price(slug, jur, rows, *, amounts=None, facts=frozenset(), gross=None):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    allocs = [_alloc(str(3100 + i), amt, "production", jur, f"S{i}", cat) for i, (cat, amt) in enumerate(rows)]
    return price_segment(jurisdiction_code=jur, program_slug=slug, allocations=allocs, spend_category_by_code={a.account_code: a.spend_category for a in allocs}, offshore_payroll_accounts=frozenset(),
                         production_type="feature_film", gross_budget_usd=gross if gross is not None else sum(a for _c, a in rows) * 2.0,
                         evidenced_requirement_facts=frozenset(facts) | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS, amount_facts=dict(amounts or {}))


def _cad_per_usd() -> float:
    from app.calculators import apply_fx_rates
    from app.calculators.production_normalization import build_fx_context
    return float(apply_fx_rates.resolve_fx_rate(build_fx_context(), "CAD").rate)


# ── Montana ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ROWS_MT = [("btl_crew_labor", 1_000_000.0), ("btl_set_construction", 1_000_000.0)]          # 1,000,000 compensation + 1,000,000 production expenditure; base investment 2,000,000
YEAR = "us_mt_media_expenditure_year"


def test_montana_unknown_inputs_are_bounded_at_the_thirty_five_percent_aggregate():
    r = _price(MT, "US-MT", ROWS_MT)
    assert r.executable and r.incentive_floor_usd == 0.0
    assert r.incentive_ceiling_usd == pytest.approx(0.35 * 2_000_000.0)                    # 700,000; the additions' bounds exceed the aggregate limit


def test_montana_compensation_credits_use_category_rates_and_per_person_caps():
    amounts = {"us_mt_resident_crew_compensation_usd": 600_000.0, "us_mt_resident_crew_persons": 6,          # 25% x 600,000 = 150,000 (<= 6 x 150,000)
               "us_mt_nonresident_crew_compensation_usd": 100_000.0, "us_mt_nonresident_crew_persons": 2,    # 15% x 100,000 = 15,000
               "us_mt_talent_compensation_usd": 200_000.0, "us_mt_talent_persons": 1,                        # 20% x min(200,000, 7.5M) = 40,000
               "us_mt_student_compensation_usd": 50_000.0, "us_mt_student_persons": 1,                       # 30% x 50,000 = 15,000 (<= 50,000)
               "us_mt_veteran_tribal_compensation_usd": 50_000.0, "us_mt_veteran_tribal_persons": 1,         # 30% x 50,000 = 15,000
               "us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 10, "us_mt_underserved_area_expenditure_usd": 0.0}
    r = _price(MT, "US-MT", ROWS_MT, amounts=amounts)
    # 20% x 1,000,000 production expenditure + (150,000 + 15,000 + 40,000 + 15,000 + 15,000) compensation credits + 5% x 2,000,000 screen-credit bound (a boolean never stored false) = 535,000
    assert r.incentive_ceiling_usd == pytest.approx(200_000.0 + 235_000.0 + 100_000.0)
    with_screen = _price(MT, "US-MT", ROWS_MT, amounts=amounts, facts={"us_mt_screen_credit_furnished_confirmed"})
    assert with_screen.incentive_ceiling_usd == pytest.approx(535_000.0), "the screen credit is +5% of base investment either way: stated or bounded"


@pytest.mark.parametrize("comp,persons,expected_credit", [
    (1_000_000.0, 1, 150_000.0),      # 25% x 1,000,000 = 250,000 > the USD 150,000 per-person credit cap
    (1_000_000.0, 10, 250_000.0),     # ten persons: 10 x 150,000 = 1,500,000 not binding
    (1_000_000.0, 0, 0.0),            # zero persons stated: nothing can qualify
])
def test_montana_resident_crew_per_person_credit_cap(comp, persons, expected_credit):
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(MT)}
    amounts = {"us_mt_resident_crew_compensation_usd": comp, "us_mt_resident_crew_persons": persons}
    fl, pot, _note = _price_statutory_formula(MT, rules["compensation_credits"], rules, 1_000_000.0, amounts, frozenset(), "feature_film", qualified_by_category={"btl_crew_labor": 1_000_000.0})
    assert pot == pytest.approx(-0.20 * 1_000_000.0 + expected_credit + 0.30 * 0.0)             # the whole compensation is stated, so no bound remains


def test_montana_talent_credit_is_twenty_percent_of_the_first_7_5_million_per_person_and_students_stop_at_50000():
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(MT)}
    big = {"btl_crew_labor": 20_000_000.0}
    _fl, pot, _ = _price_statutory_formula(MT, rules["compensation_credits"], rules, 20_000_000.0, {"us_mt_talent_compensation_usd": 20_000_000.0, "us_mt_talent_persons": 2}, frozenset(), "feature_film", qualified_by_category=big)
    assert pot == pytest.approx(-0.20 * 20_000_000.0 + 0.20 * 15_000_000.0)                     # two persons x 7.5 million = 15 million at 20%
    _fl, pot, _ = _price_statutory_formula(MT, rules["compensation_credits"], rules, 400_000.0, {"us_mt_student_compensation_usd": 400_000.0, "us_mt_student_persons": 2}, frozenset(), "feature_film", qualified_by_category={"btl_crew_labor": 400_000.0})
    assert pot == pytest.approx(-0.20 * 400_000.0 + 100_000.0)                                  # 30% x 400,000 = 120,000 > 2 x 50,000
    with pytest.raises(ValueError):
        _price_statutory_formula(MT, rules["compensation_credits"], rules, 400_000.0, {"us_mt_resident_crew_compensation_usd": 500_000.0}, frozenset(), "feature_film", qualified_by_category={"btl_crew_labor": 400_000.0})


def test_montana_studio_rental_needs_twenty_days_and_story_rights_are_not_production_expenditure():
    base = _price(MT, "US-MT", ROWS_MT)
    rights = _price(MT, "US-MT", ROWS_MT + [("atl_rights", 500_000.0)])
    assert rights.qpe_usd == pytest.approx(base.qpe_usd), "MCA 15-31-1003(13)(b)(iv): story rights are not a production expenditure"
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(MT)}
    rental = rules["studio_rental"]
    for days, credit in ((19, 0.0), (20, 20_000.0), (45, 20_000.0)):
        _fl, pot, _ = _price_statutory_formula(MT, rental, rules, 2_000_000.0, {"us_mt_studio_rental_expenditure_usd": 200_000.0, "us_mt_studio_rental_days": days}, frozenset(), "feature_film")
        assert pot == pytest.approx(credit), days


@pytest.mark.parametrize("year,potential", [(2030, 0.0), (2031, 0.35 * 2_000_000.0), (2040, 0.35 * 2_000_000.0)])
def test_montana_credit_exists_only_for_expenditures_from_2031_and_the_pause_is_not_the_credit_year(year, potential):
    r = _price(MT, "US-MT", ROWS_MT, amounts={YEAR: year})
    assert r.executable and r.incentive_floor_usd == 0.0 and r.incentive_ceiling_usd == pytest.approx(potential)
    unstated = _price(MT, "US-MT", ROWS_MT)
    assert any(c["condition_id"].endswith(":timing") for c in unstated.ceiling_conditions), "an unstated year is a disclosed timing condition, never silently assumed"


# ── New Brunswick ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_new_brunswick_deemed_spend_scales_the_base_up_to_fifteen_percent():
    rows = [("btl_crew_labor", 1_000_000.0)]
    unknown = _price(NB, "CA-NB", rows)
    assert unknown.incentive_ceiling_usd == pytest.approx(0.35 * 1_000_000.0 * 1.15)                         # the combined 35% on a base that may include 15% deemed spend
    stated = _price(NB, "CA-NB", rows, amounts={"ca_nb_eligible_deemed_spend_usd": 100_000.0})
    assert stated.incentive_ceiling_usd == pytest.approx(0.35 * 1_000_000.0 * 1.10) or stated.incentive_ceiling_usd == pytest.approx(0.35 * 1_100_000.0)
    over = _price(NB, "CA-NB", rows, amounts={"ca_nb_eligible_deemed_spend_usd": 400_000.0})
    assert over.incentive_ceiling_usd == pytest.approx(0.35 * 1_150_000.0), "deemed spend above 15% of eligible in-province spend is not counted"


def test_new_brunswick_micro_stream_for_budgets_under_cad_400000_is_thirty_percent_capped_at_cad_100000():
    rate = _cad_per_usd()
    gross = 399_000.0 / rate                                                                                  # a total budget of CAD 399,000
    qle = 0.5 * gross                                                                                         # NB spend 50% of the budget (>= 25%)
    micro = _price(NB, "CA-NB", [("btl_crew_labor", qle)], gross=gross)
    assert micro.incentive_floor_usd == 0.0
    assert micro.incentive_ceiling_usd == pytest.approx(min(0.30 * qle, 100_000.0 / rate), rel=1e-4)
    major = _price(NB, "CA-NB", [("btl_crew_labor", 0.5 * (401_000.0 / rate))], gross=401_000.0 / rate)       # CAD 401,000: Major Production
    assert major.incentive_ceiling_usd == pytest.approx(0.35 * 1.15 * 0.5 * (401_000.0 / rate), rel=1e-4)
    thin = _price(NB, "CA-NB", [("btl_crew_labor", 0.10 * gross)], gross=gross)                               # NB spend 10% < 25% of the budget
    assert thin.incentive_ceiling_usd == 0.0


def test_new_brunswick_major_stream_needs_nb_spend_of_twenty_percent_of_the_budget():
    big = 3_000_000.0
    ok = _price(NB, "CA-NB", [("btl_crew_labor", 0.20 * big)], gross=big)
    assert ok.incentive_ceiling_usd > 0.0
    short = _price(NB, "CA-NB", [("btl_crew_labor", 0.1999 * big)], gross=big)
    assert short.incentive_ceiling_usd == 0.0


# ── Nova Scotia ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_nova_scotia_ineligible_supplier_spend_and_equity_financing_leave_the_base():
    rows = [("btl_crew_labor", 1_000_000.0)]
    base = _price(NS, "CA-NS", rows)
    assert base.incentive_floor_usd == pytest.approx(250_000.0)
    cut = _price(NS, "CA-NS", rows, amounts={"ca_ns_ineligible_supplier_spend_usd": 250_000.0})
    assert cut.incentive_floor_usd == pytest.approx(0.25 * 750_000.0)
    both = _price(NS, "CA-NS", rows, amounts={"ca_ns_ineligible_supplier_spend_usd": 250_000.0, "ca_ns_equity_tax_credit_financing_usd": 250_000.0})
    assert both.incentive_floor_usd == pytest.approx(0.25 * 500_000.0), "each stated deduction shrinks the base once"
    refused = _price(NS, "CA-NS", rows, amounts={"ca_ns_ineligible_supplier_spend_usd": 1_500_000.0})
    assert not refused.executable and refused.blockers
    assert any(c["condition_id"].endswith("ca_ns_ineligible_supplier_spend_usd") for c in base.ceiling_conditions), "unstated: presumed absent and disclosed"


def test_nova_scotia_individual_incentive_cap_removes_the_incentive_above_cad_150000_per_identified_person():
    rate = _cad_per_usd()
    cap_usd = 150_000.0 / rate
    rows = [("btl_crew_labor", 1_000_000.0)]
    one_person = _price(NS, "CA-NS", rows, amounts={"ny_atl_payee:S0": 1.0})
    # 25% x 1,000,000 = 250,000 of incentive for one person; the cap leaves cap_usd of it
    assert one_person.incentive_floor_usd == pytest.approx(cap_usd, rel=1e-4) if 250_000.0 > cap_usd else True
    small = _price(NS, "CA-NS", [("btl_crew_labor", 0.5 * cap_usd / 0.25)], amounts={"ny_atl_payee:S0": 1.0})
    assert small.incentive_floor_usd == pytest.approx(0.25 * 0.5 * cap_usd / 0.25), "below the cap nothing is removed"
    # two lines of the SAME person are aggregated; an unidentified line is never capped
    two_lines = _price(NS, "CA-NS", [("btl_crew_labor", 500_000.0), ("atl_cast", 500_000.0)], amounts={"ny_atl_payee:S0": 1.0, "ny_atl_payee:S1": 1.0})
    assert two_lines.incentive_floor_usd == pytest.approx(cap_usd, rel=1e-4)
    different = _price(NS, "CA-NS", [("btl_crew_labor", 300_000.0), ("atl_cast", 300_000.0)], amounts={"ny_atl_payee:S0": 1.0, "ny_atl_payee:S1": 2.0})
    assert different.incentive_floor_usd == pytest.approx(0.25 * 600_000.0), "two persons at 75,000 of incentive each stay under the cap"
    over = _price(NS, "CA-NS", [("btl_crew_labor", 500_000.0), ("atl_cast", 500_000.0)], amounts={"ny_atl_payee:S0": 1.0, "ny_atl_payee:S1": 2.0})
    assert over.incentive_floor_usd == pytest.approx(2 * cap_usd, rel=1e-4), "two persons at 125,000 of incentive each are each cut to the cap"
    unidentified = _price(NS, "CA-NS", rows)
    assert unidentified.incentive_floor_usd == pytest.approx(250_000.0)


# ── Saskatchewan ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ROWS_SK = [("btl_crew_labor", 1_000_000.0)]
TOT, INSK, RURAL = "ca_sk_principal_photography_days_total", "ca_sk_principal_photography_days_in_sk", "ca_sk_days_50km_outside_regina_saskatoon"
SKS, SVC = "ca_sk_saskatchewan_stream_confirmed", "ca_sk_service_production_stream_confirmed"
POST, VOL = "ca_sk_majority_post_spend_in_sk_confirmed", "ca_sk_volume_threshold_confirmed"


def test_saskatchewan_is_visible_zero_guaranteed_potential_capped_by_stream():
    from app.data import authority_coverage_registry as acr
    assert "ca_sk_production_grant" not in acr._B1_DISCRETIONARY_RULING and acr.economic_block_for_program(SK) is None
    none = _price(SK, "CA-SK", ROWS_SK)
    assert none.executable and none.incentive_floor_usd == 0.0 and none.ceiling_requires_confirmation
    assert none.incentive_ceiling_usd == pytest.approx(0.40 * 1_000_000.0), "25 base + 5 + 5 + 5 + 10 bounds clipped at the Saskatchewan Stream total"
    service = _price(SK, "CA-SK", ROWS_SK, facts={SVC})
    assert service.incentive_ceiling_usd == pytest.approx(0.35 * 1_000_000.0), "Service Production Stream stated: total capped at 35%"
    assert service.incentive_floor_usd == 0.0


@pytest.mark.parametrize("in_sk,rural,met", [(50, 60, False), (51, 60, True), (100, 100, True), (0, 0, False)])
def test_saskatchewan_bonuses_need_the_51_percent_activity_test_and_a_rural_majority(in_sk, rural, met):
    total = 100
    r = _price(SK, "CA-SK", ROWS_SK, amounts={TOT: total, INSK: in_sk, RURAL: min(rural, total)}, facts={SVC, POST, VOL})
    base_points = 25.0
    if met:
        points = base_points + (5 if min(rural, total) > 50 else 0) + 5 + 10               # rural (more than half of days), post, volume
    else:
        points = base_points + 0                                                           # the activity test fails: no bonus applies (stated post/volume are gated too)
    assert r.incentive_ceiling_usd == pytest.approx(min(points, 35.0) / 100.0 * 1_000_000.0)


def test_saskatchewan_rural_majority_is_more_than_half_of_the_days():
    ok = _price(SK, "CA-SK", ROWS_SK, amounts={TOT: 100, INSK: 100, RURAL: 51}, facts={SVC})
    edge = _price(SK, "CA-SK", ROWS_SK, amounts={TOT: 100, INSK: 100, RURAL: 50}, facts={SVC})
    assert ok.incentive_ceiling_usd - edge.incentive_ceiling_usd == pytest.approx(0.05 * 1_000_000.0) or ok.incentive_ceiling_usd == pytest.approx(0.35 * 1_000_000.0)
    # with the post and volume bounds present the 35% cap hides the rural point; isolate it by comparing unclipped scenarios
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(SK)}
    fifty = _price_statutory_formula(SK, rules["rural_bonus"], rules, 1_000_000.0, {TOT: 100, RURAL: 50}, frozenset(), "feature_film")
    fifty_one = _price_statutory_formula(SK, rules["rural_bonus"], rules, 1_000_000.0, {TOT: 100, RURAL: 51}, frozenset(), "feature_film")
    assert fifty[:2] == (0.0, 0.0) and fifty_one[:2] == (50_000.0, 50_000.0)


def test_every_new_input_has_a_producer_writer():
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS, PROGRAM_AMOUNT_FACTS
    for program in (MT, NS, SK):
        for rule in get_subset_uplift_rules(program):
            booleans = [rule.prerequisite_fact, rule.excluded_fact, rule.whole_base_fact, *rule.criteria_facts, *[c[5] for c in rule.compensation_credits if len(c) > 5]]
            amounts = [rule.day_numerator_fact, rule.day_denominator_fact, rule.amount_fact, *rule.assistance_facts, *[f for c in rule.compensation_credits for f in c[:2]], rule.post_wage_fact]
            for key in filter(None, booleans):
                assert key in NY_EVIDENCED_FACTS, f"{program}/{rule.uplift_id}: {key}"
            for key in filter(None, amounts):
                assert key in PROGRAM_AMOUNT_FACTS, f"{program}/{rule.uplift_id}: {key}"
    from app.data.program_rate_rules import SUBSET_BASE_DEDUCTIONS, SUBSET_DEEMED_SPEND
    for _slug, items in SUBSET_BASE_DEDUCTIONS.items():
        for key, _src in items:
            assert key in PROGRAM_AMOUNT_FACTS
    assert all(v[0] in PROGRAM_AMOUNT_FACTS for v in SUBSET_DEEMED_SPEND.values())
    assert NY_EVIDENCED_FACTS[SKS] == SVC and NY_EVIDENCED_FACTS[SVC] == SKS


# ── Current versus historical BC regimes ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_bc_domestic_record_states_its_current_scope_and_refuses_to_model_older_regimes():
    from app.data.program_rate_rules_worldwide import CA_BC_FILM_TV_DOCTRINE as d
    note = d.provenance.interpretation_note
    assert "CURRENT regime" in note and "after December 31, 2024" in note and "2016-10-01" in note and "NOT modelled" in note and "never mixed" in note


# ── NA-RECONCILIATION-20 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_montana_postproduction_wages_are_compensation_priced_at_25_percent_only_for_an_approved_postproduction_company():
    rows = [("btl_crew_labor", 1_000_000.0), ("btl_set_construction", 500_000.0), ("post_production", 500_000.0)]        # base investment 2,000,000
    zero_extras = {"us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 0, "us_mt_underserved_area_expenditure_usd": 0.0}
    amounts = {**zero_extras, "us_mt_postproduction_wages_usd": 300_000.0}
    approved = _price(MT, "US-MT", rows, amounts=amounts, facts={"us_mt_postproduction_company_approved_confirmed"})
    # 20% x 2,000,000 = 400,000; the 1,300,000 of compensation (1,000,000 crew + 300,000 post wages) leaves the base: -260,000; post wages 25% x 300,000 = +75,000 (15-31-1009(2));
    # the 1,000,000 of crew compensation has no stated category: bounded at 30% = +300,000; screen-credit bound 5% x 2,000,000 = +100,000  -> 615,000 (< the 700,000 aggregate)
    assert approved.incentive_ceiling_usd == pytest.approx(400_000.0 - 260_000.0 + 75_000.0 + 300_000.0 + 100_000.0)
    unapproved = _price(MT, "US-MT", rows, amounts=amounts)
    # without the approved-company statement the wages are compensation of unstated category: bounded at 30% (390,000) -> 400,000 - 260,000 + 390,000 + 100,000 = 630,000
    assert unapproved.incentive_ceiling_usd == pytest.approx(630_000.0)
    with pytest.raises(ValueError):
        rules = {r.uplift_id: r for r in get_subset_uplift_rules(MT)}
        _price_statutory_formula(MT, rules["compensation_credits"], rules, 2_000_000.0, {"us_mt_postproduction_wages_usd": 600_000.0}, frozenset(), "feature_film",
                                 qualified_by_category={"btl_crew_labor": 1_000_000.0, "post_production": 500_000.0})
    refused = _price(MT, "US-MT", rows, amounts={"us_mt_postproduction_wages_usd": 600_000.0})
    assert not refused.executable and refused.blockers, "stated postproduction wages cannot exceed the post-production spend in the budget"


def test_montana_record_resolves_the_expenditure_exclusion_conflict_without_hiding_it():
    from app.data.program_rate_rules_worldwide import US_MT_DOCTRINE as d
    note = d.provenance.interpretation_note
    assert "(13)(a)(ix)" in note and "(13)(b)(vi)" in note and "never defines" in note and "OPEN interpretation" in note and "15-31-1009" in note


def test_nova_scotia_producer_second_positions_are_removed_from_the_floor_until_approved_and_limited_to_20_percent_of_the_budget():
    rows = [("btl_crew_labor", 1_000_000.0)]                                                                              # gross budget 2,000,000 in the helper
    base = _price(NS, "CA-NS", rows)
    unapproved = _price(NS, "CA-NS", rows, amounts={"ca_ns_producer_extra_position_fees_usd": 100_000.0})
    assert unapproved.incentive_floor_usd == pytest.approx(0.25 * 900_000.0), "second and further positions are not eligible without the Administrator's advance approval"
    assert unapproved.incentive_ceiling_usd == pytest.approx(base.incentive_ceiling_usd), "the potential assumes the approval and the total is within 20% of the budget"
    approved = _price(NS, "CA-NS", rows, amounts={"ca_ns_producer_extra_position_fees_usd": 100_000.0}, facts={"ca_ns_producer_extra_positions_approved_confirmed"})
    assert approved.incentive_floor_usd == pytest.approx(0.25 * 1_000_000.0)
    # total fees to such producers 500,000 against 20% x 2,000,000 = 400,000: 100,000 over is removed from the base (floor once approved, potential always)
    over = _price(NS, "CA-NS", rows, amounts={"ca_ns_producer_extra_position_fees_usd": 100_000.0, "ca_ns_producer_hod_performer_fees_total_usd": 500_000.0},
                  facts={"ca_ns_producer_extra_positions_approved_confirmed"})
    assert over.incentive_floor_usd == pytest.approx(0.25 * 900_000.0)
    assert over.incentive_ceiling_usd == pytest.approx(base.incentive_ceiling_usd * 0.9)
    exact = _price(NS, "CA-NS", rows, amounts={"ca_ns_producer_extra_position_fees_usd": 100_000.0, "ca_ns_producer_hod_performer_fees_total_usd": 400_000.0},
                   facts={"ca_ns_producer_extra_positions_approved_confirmed"})
    assert exact.incentive_floor_usd == pytest.approx(0.25 * 1_000_000.0), "exactly 20% of the budget is allowed"


def test_saskatchewan_apprenticeship_earns_the_main_grants_percentage_on_matched_mentor_salaries():
    rows = ROWS_SK
    none = _price(SK, "CA-SK", rows)
    assert none.incentive_ceiling_usd == pytest.approx(400_000.0) and any(c["condition_id"].endswith("ca_sk_apprenticeship_mentor_salaries_usd") for c in none.ceiling_conditions)
    stated = _price(SK, "CA-SK", rows, amounts={"ca_sk_apprenticeship_mentor_salaries_usd": 100_000.0})
    assert stated.incentive_ceiling_usd == pytest.approx(400_000.0 + 0.40 * 100_000.0), "40% total x 100,000 of eligible non-resident salaries"
    service = _price(SK, "CA-SK", rows, amounts={"ca_sk_apprenticeship_mentor_salaries_usd": 100_000.0}, facts={SVC})
    assert service.incentive_ceiling_usd == pytest.approx(350_000.0 + 0.35 * 100_000.0)
    assert stated.incentive_floor_usd == 0.0
    from app.data.program_rate_rules import get_incentive_value_cap
    cap = get_incentive_value_cap(SK)
    assert cap.cap_currency == "CAD" and cap.cap_native_amount == 5_000_000.0 and "Apprenticeship" in cap.description
    huge = _price(SK, "CA-SK", [("btl_crew_labor", 20_000_000.0)])
    rate = _cad_per_usd()
    assert huge.incentive_ceiling_usd == pytest.approx(5_000_000.0 / rate, rel=1e-4), "the CAD 5 million per-project maximum clips the ceiling"


def test_new_brunswick_deemed_spend_worksheet_is_not_public_so_the_amount_is_a_stated_input_not_a_formula():
    from app.data.program_rate_rules import SUBSET_DEEMED_SPEND
    key, share, source = SUBSET_DEEMED_SPEND[NB]
    assert key == "ca_nb_eligible_deemed_spend_usd" and share == 0.15 and "Deemed Spend Worksheet" in source
