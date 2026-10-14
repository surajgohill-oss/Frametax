"""NA-RECONCILIATION-16: the British Columbia shooting-day, training and scriptwriting credits on their exact statutory bases.

Synthetic and DB-free. Every expectation is hand arithmetic from Income Tax Act (BC) Part 5 (bclaws.gov.bc.ca, read 2026-10-14):
- s.81.1(1)-(2) regional: requires s.80; principal photography outside the designated Vancouver area for at least 5 days AND during more than 50% of the BC days; 12.5% x QLE x RD/TD.
- s.81.11 distant location: requires s.80 and s.81.1; at least 1 distant-location day; 6% x QLE x DLD/TD.
- s.82.2 / s.82.21: the production-services equivalents, 6% x AQLE x RD/TD and 6% x AQLE x DLD/TD (hosts s.82.1).
- s.82 training: the lesser of 3% of QLE and 30% of (payments attributable to training - assistance); needs an approved training program.
- s.80.1(3) scriptwriting: 35% x (SE - (TA + RE)).
Days are stated producer facts; no day count is ever derived from dollars."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from app.data.program_rate_rules import SUBSET_UPLIFT_RULES, get_subset_uplift_rules
from tests.test_na_stack_and_gate_repairs_controls import _alloc

DOM, PS = "ca_bc_film_tv_tax_credit", "ca_bc_pstc"
LABOUR = 1_000_000.0
DAYS_BC, DAYS_OUT, DAYS_FAR = ("ca_bc_principal_photography_days_in_bc", "ca_bc_principal_photography_days_outside_vancouver", "ca_bc_principal_photography_days_distant_location")


def _price(slug, *, amounts=None, facts=frozenset(), production_type="feature_film", labour=LABOUR, gross_factor=2.5):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    allocs = [_alloc("3100", labour, "production", "CA-BC", "S0", "btl_crew_labor")]
    return price_segment(jurisdiction_code="CA-BC", program_slug=slug, allocations=allocs, spend_category_by_code={"3100": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
                         production_type=production_type, gross_budget_usd=labour * gross_factor, evidenced_requirement_facts=frozenset(facts) | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS,
                         amount_facts=dict(amounts or {}))


def _days(td, rd=None, dld=None):
    out = {DAYS_BC: td}
    if rd is not None:
        out[DAYS_OUT] = rd
    if dld is not None:
        out[DAYS_FAR] = dld
    return out


BASE = {DOM: _price(DOM), PS: _price(PS)}
#: The domestic host's own potential before any formula credit: 40% when photography begins after 2024-12-31 (s.80(8)) over the guaranteed 35%; kept as a conditional BASE-rate scenario.
DOM_POT = 0.40 * LABOUR


def test_the_established_bc_bases_are_unchanged_when_no_day_is_stated():
    assert BASE[DOM].executable and BASE[PS].executable
    assert BASE[PS].incentive_floor_usd == pytest.approx(0.36 * LABOUR)                                             # production services base, s.82.1(2)+(5)
    assert BASE[PS].incentive_ceiling_usd == pytest.approx(0.36 * LABOUR + 0.06 * LABOUR + 0.06 * LABOUR)           # the long-standing 48% bound (regional + distant at ratio 1)
    assert BASE[DOM].incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd) and BASE[DOM].incentive_floor_usd > 0
    # domestic: the floor is the host base alone; the potential adds regional 12.5% + distant 6% at ratio 1 (training and scriptwriting exist only by application)
    assert BASE[DOM].incentive_floor_usd == pytest.approx(0.35 * LABOUR)
    assert BASE[DOM].incentive_ceiling_usd == pytest.approx(DOM_POT + (0.125 + 0.06) * LABOUR)
    assert BASE[DOM].ceiling_requires_confirmation and BASE[PS].ceiling_requires_confirmation
    ids = {c["condition_id"] for c in BASE[DOM].ceiling_conditions}
    assert {f"{DOM}:regional:statutory_formula", f"{DOM}:distant_location:statutory_formula"} <= ids
    assert not any("film_training" in i or "scriptwriting" in i for i in ids), "an application-only credit contributes nothing, not even a bound, until its prerequisite is stated"


@pytest.mark.parametrize("rd,td,expected_ratio", [
    (4, 8, None),      # 4 days: below the statutory minimum of 5 although 50%... (4/8 is not more than 50% either)
    (4, 5, None),      # 80% outside, but only 4 days: fails "at least 5 days"
    (5, 9, 5 / 9),     # exactly 5 days and 5/9 > 50%: eligible; ratio is RD/TD
    (5, 10, None),     # exactly 5 days but exactly 50%: "more than 50%" fails
    (20, 40, None),    # exactly 50%
    (21, 40, 21 / 40), # one day more than half
    (40, 40, 1.0),     # every day outside the designated Vancouver area
])
def test_regional_credit_boundary_arithmetic_on_both_hosts(rd, td, expected_ratio):
    for slug, rate in ((DOM, 0.125), (PS, 0.06)):
        priced = _price(slug, amounts=_days(td, rd))
        added = priced.incentive_floor_usd - BASE[slug].incentive_floor_usd
        assert added == pytest.approx(0.0 if expected_ratio is None else round(rate * LABOUR * expected_ratio, 2), abs=0.01), (slug, rd, td)
        # stated days settle the credit: either confirmed or stated-ineligible; the regional condition is no longer unresolved
        assert f"{slug}:regional:statutory_formula" not in {c["condition_id"] for c in priced.ceiling_conditions}


def test_distant_location_requires_the_regional_credit_and_at_least_one_day():
    # RD=30, TD=40 (75% outside) and DLD=10: regional 12.5% x 0.75 + distant 6% x 0.25 on the domestic host
    both = _price(DOM, amounts=_days(40, 30, 10))
    assert both.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(LABOUR * (0.125 * 30 / 40 + 0.06 * 10 / 40))
    ps = _price(PS, amounts=_days(40, 30, 10))
    assert ps.incentive_floor_usd == pytest.approx(LABOUR * (0.36 + 0.06 * 30 / 40 + 0.06 * 10 / 40))                # 0.42 of labour
    assert ps.incentive_floor_usd == pytest.approx(ps.incentive_ceiling_usd) and not ps.ceiling_requires_confirmation
    # zero distant days: the distant credit needs at least one day
    zero = _price(DOM, amounts=_days(40, 30, 0))
    assert zero.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(LABOUR * 0.125 * 30 / 40)
    one = _price(DOM, amounts=_days(40, 30, 1))
    assert one.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(LABOUR * (0.125 * 30 / 40 + 0.06 * 1 / 40))
    # the regional credit fails (4 outside days): the distant credit cannot apply either (s.81.11(1)(a))
    failed = _price(DOM, amounts=_days(40, 4, 3))
    assert failed.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd) and failed.incentive_ceiling_usd == pytest.approx(DOM_POT)


def test_unknown_days_stay_a_bounded_condition_never_a_default():
    # only the total is stated: regional and distant are unknown -> floor unchanged, potential bounded at ratio 1
    only_total = _price(DOM, amounts=_days(40))
    assert only_total.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assert only_total.incentive_ceiling_usd == pytest.approx(DOM_POT + (0.125 + 0.06) * LABOUR)
    # regional settled (RD=30 of 40), distant unknown: distant bounded by the regional days, 6% x 30/40
    partial = _price(DOM, amounts=_days(40, 30))
    assert partial.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(LABOUR * 0.125 * 30 / 40)
    assert partial.incentive_ceiling_usd - partial.incentive_floor_usd == pytest.approx(DOM_POT - BASE[DOM].incentive_floor_usd + LABOUR * 0.06 * 30 / 40)
    assert partial.ceiling_requires_confirmation
    # distant days stated without the regional figures: confirmed only once the companion is stated; bounded by DLD/TD meanwhile
    lone = _price(DOM, amounts={DAYS_BC: 40, DAYS_FAR: 8})
    assert lone.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assert lone.incentive_ceiling_usd == pytest.approx(DOM_POT + LABOUR * 0.125 + LABOUR * 0.06 * 8 / 40)


@pytest.mark.parametrize("amounts", [_days(40, 41), _days(0), {DAYS_BC: 40, DAYS_OUT: 10, DAYS_FAR: 11}, _days(40, 10.5), _days(40, -1)])
def test_impossible_or_non_whole_day_statements_are_refused_not_coerced(amounts):
    refused = _price(DOM, amounts=amounts)
    assert not refused.executable and refused.blockers, amounts


def test_a_series_and_an_animation_are_priced_on_the_base_but_not_from_whole_production_days():
    # Restated in NA-RECONCILIATION-20. Income Tax Act (BC) s.79(1) 'eligible production' and 'accredited production' cover series (each episode over its threshold) and animation, and s.80(2)-(8) / s.82.1(2),(5) set
    # the same rates, so both BC hosts now price series and animation. What the budget cannot supply stays out of the confirmed figure: a series is computed on its qualifying episodes only (s.81.1(1)(c)), and an
    # animation production's regional credits require photography that began before 2024-06-01 (s.81.1(4)(b)).
    for slug in (DOM, PS):
        for kind in ("tv_series", "animation"):
            base = _price(slug, production_type=kind)
            assert base.executable and base.incentive_floor_usd == pytest.approx(BASE[slug].incentive_floor_usd), (slug, kind)
            days = _price(slug, amounts=_days(40, 30, 10), production_type=kind)
            assert days.incentive_floor_usd == pytest.approx(base.incentive_floor_usd), "no day-ratio credit is confirmed for a series or an animation"
    series = _price(DOM, amounts=_days(40, 30, 10), production_type="tv_series")
    assert series.incentive_ceiling_usd - series.incentive_floor_usd == pytest.approx(LABOUR * (0.40 - 0.35 + 0.125 + 0.06)), "a series stays bounded by the whole-production figure"
    animation = _price(DOM, amounts=_days(40, 30, 10), production_type="animation")
    assert animation.incentive_ceiling_usd - animation.incentive_floor_usd == pytest.approx(LABOUR * 0.05), "an animation has no regional or distant credit for current photography (only the 40% scenario remains)"
    # documentaries stay out of scope of this record (their own 75% tests are separate)
    assert not _price(DOM, production_type="creative_documentary").executable
    from app.calculators.allocation_pricing import _price_statutory_formula
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(DOM)}
    amounts = _days(40, 30, 10)
    confirmed, potential, note = _price_statutory_formula(DOM, rules["regional"], rules, LABOUR, amounts, frozenset(), "tv_series")
    assert (confirmed, potential) == (0.0, 125_000.0) and "qualifying episodes" in note
    confirmed, potential, note = _price_statutory_formula(DOM, rules["regional"], rules, LABOUR, amounts, frozenset(), "animation")
    assert (confirmed, potential) == (0.0, 0.0) and "animation" in note
    assert _price_statutory_formula(DOM, rules["regional"], rules, LABOUR, amounts, frozenset(), "feature_film")[:2] == (93_750.0, 93_750.0)   # 12.5% x 1,000,000 x 30/40


def test_the_labour_base_is_the_hosts_own_trimmed_qualified_labour_so_assistance_and_the_cap_flow_through():
    # gross 1.4M -> the 60% cap (s.79(1) 'qualified BC labour expenditure') trims 1,000,000 of labour to 840,000 before the regional ratio applies
    trimmed_base = _price(DOM, gross_factor=1.4)
    trimmed = _price(DOM, amounts=_days(40, 30, 10), gross_factor=1.4)
    assert trimmed.incentive_floor_usd - trimmed_base.incentive_floor_usd == pytest.approx(840_000.0 * (0.125 * 30 / 40 + 0.06 * 10 / 40))


def test_training_is_the_lesser_of_three_percent_of_qle_and_thirty_percent_of_net_training_payments():
    prereq = frozenset({"ca_bc_film_training_program_approved_confirmed"})
    pay, ass = "ca_bc_training_payments_usd", "ca_bc_training_assistance_usd"
    base = _price(DOM, facts=prereq)
    assert base.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assert base.incentive_ceiling_usd == pytest.approx(BASE[DOM].incentive_ceiling_usd + 0.03 * LABOUR)             # prerequisite stated, payments unknown: bounded at 3% of QLE
    smaller_net = _price(DOM, facts=prereq, amounts={pay: 50_000.0, ass: 10_000.0})
    assert smaller_net.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(0.30 * 40_000.0)         # 12,000 < 30,000
    capped = _price(DOM, facts=prereq, amounts={pay: 500_000.0, ass: 0.0})
    assert capped.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(0.03 * LABOUR)               # 150,000 > 30,000 -> the 3% cap
    none_left = _price(DOM, facts=prereq, amounts={pay: 20_000.0, ass: 20_000.0})
    assert none_left.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assistance_unknown = _price(DOM, facts=prereq, amounts={pay: 50_000.0})
    assert assistance_unknown.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assert assistance_unknown.incentive_ceiling_usd - BASE[DOM].incentive_ceiling_usd == pytest.approx(0.30 * 50_000.0)
    unapproved = _price(DOM, amounts={pay: 50_000.0, ass: 0.0})
    assert unapproved.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd), "no approved training program stated: the credit does not exist"


def test_scriptwriting_is_thirty_five_percent_of_expenditure_less_assistance_and_reimbursement():
    prereq = frozenset({"ca_bc_scriptwriting_application_confirmed"})
    se, ta, re_ = "ca_bc_scriptwriting_expenditure_usd", "ca_bc_scriptwriting_assistance_usd", "ca_bc_scriptwriting_parent_reimbursement_usd"
    full = _price(DOM, facts=prereq, amounts={se: 200_000.0, ta: 20_000.0, re_: 30_000.0})
    assert full.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(0.35 * 150_000.0)               # 52,500
    zero_stated = _price(DOM, facts=prereq, amounts={se: 100_000.0, ta: 0.0, re_: 0.0})
    assert zero_stated.incentive_floor_usd - BASE[DOM].incentive_floor_usd == pytest.approx(35_000.0)
    over = _price(DOM, facts=prereq, amounts={se: 10_000.0, ta: 20_000.0, re_: 0.0})
    assert over.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd), "assistance above the expenditure leaves nothing, never a negative credit"
    ta_missing = _price(DOM, facts=prereq, amounts={se: 200_000.0, re_: 30_000.0})
    assert ta_missing.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)
    assert ta_missing.incentive_ceiling_usd - BASE[DOM].incentive_ceiling_usd == pytest.approx(0.35 * 170_000.0)
    no_expenditure = _price(DOM, facts=prereq)
    assert no_expenditure.incentive_ceiling_usd == pytest.approx(BASE[DOM].incentive_ceiling_usd), "no figure is derived from the budget's writer lines"
    assert f"{DOM}:scriptwriting:statutory_formula" in {c["condition_id"] for c in no_expenditure.ceiling_conditions}
    unapplied = _price(DOM, amounts={se: 200_000.0, ta: 0.0, re_: 0.0})
    assert unapplied.incentive_floor_usd == pytest.approx(BASE[DOM].incentive_floor_usd)


def test_host_dependency_the_formula_credits_exist_only_under_their_host_programs():
    assert {r.uplift_id for r in get_subset_uplift_rules(DOM)} == {"regional", "distant_location", "film_training", "scriptwriting"}
    assert {r.uplift_id for r in get_subset_uplift_rules(PS)} == {"regional", "distant_location"}
    assert get_subset_uplift_rules("ca_bc_dave") == ()
    # training / scriptwriting are s.80 add-ons only: the production services host (s.82.1) has neither
    assert not any(r.kind in ("training", "scriptwriting") for r in SUBSET_UPLIFT_RULES[PS])
    # the formula credits are priced inside the host's segment, so a DAVE-only or CPTC-only segment carries none of them
    dave = _price("ca_bc_dave")
    assert not any("statutory_formula" in c["condition_id"] for c in dave.ceiling_conditions)


def test_every_formula_input_has_one_producer_writer():
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS, PROGRAM_AMOUNT_FACTS
    for program in (DOM, PS):
        for rule in get_subset_uplift_rules(program):
            if rule.kind == "subset":
                continue
            for key in (rule.day_numerator_fact, rule.day_denominator_fact, rule.amount_fact, *rule.assistance_facts):
                if key:
                    assert key in PROGRAM_AMOUNT_FACTS, f"{key} has no producer writer"
            if rule.prerequisite_fact:
                assert rule.prerequisite_fact in NY_EVIDENCED_FACTS, f"{rule.prerequisite_fact} has no producer writer"
    assert "bc_labour_in_regional_zone" not in NY_EVIDENCED_FACTS, "the dollar-proxy zone facts are retired"
