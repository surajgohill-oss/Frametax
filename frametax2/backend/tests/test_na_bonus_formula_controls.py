"""NA-RECONCILIATION-18: Nova Scotia (Stream I, Shooting Length, Content, Head-of-Department), New Brunswick stackable bonuses, Missouri uplifts and Arkansas add-ons on their exact text.

Synthetic and DB-free; hand arithmetic from the cited text. Basis in every case: 1,000,000 of qualifying spend, so one percentage point = 10,000.
- NSFPIF Guidelines (April 1, 2024) s.5-7: Stream I base 26% / Stream II 25%; Shooting Length +1 for MORE THAN 30 days in Nova Scotia; Content +1.5 when no less than 60% of principal performers are
  Nova Scotia residents and +1.5 when at least 3 of 7 content criteria are met; the base is reduced 0.5 point per Head of Department position below the stream minimum (Stream I: 50% of filled positions
  rounded up; Stream II: half rounded up when 8 or fewer are filled, four when 9 or more).
- LIFT 2026/2027 Stream 2: base up to 25% plus +3% (30%+ HOD / lead talent), +3% or +4% (50%+ of principal photography rural / remote), +3% (at least 2 NB-content thresholds) to a combined 35%.
- RSMo 135.750 subsection 3: 20% + 5 + 5 + 5 + 5 (+2 for a second-, third- or fourth-class county) = 42%.
- Ark. Code 15-4-2005(f): the total claimed on any expenditure is capped at 30% (so at most 5 points over the 25% base)."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from tests.test_na_stack_and_gate_repairs_controls import _alloc

BASE = 1_000_000.0
PT = BASE / 100.0      # one percentage point


def _price(slug, jur, *, amounts=None, facts=frozenset(), category="btl_crew_labor"):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    allocs = [_alloc("3100", BASE, "production", jur, "S0", category)]
    return price_segment(jurisdiction_code=jur, program_slug=slug, allocations=allocs, spend_category_by_code={"3100": category}, offshore_payroll_accounts=frozenset(), production_type="feature_film",
                         gross_budget_usd=BASE * 2.0, evidenced_requirement_facts=frozenset(facts) | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS, amount_facts=dict(amounts or {}))


NS = "ca_ns_production_incentive_fund"
NB = "ca_nb_film_tax_credit"
MO = "us_mo_motion_media_production_tax_credit"
AR = "us_ar_digital_motion_picture_incentive"


def ns(**kw):
    return _price(NS, "CA-NS", **kw)


NS0 = ns()
S1, S2 = "ca_ns_stream_i_ownership_control_confirmed", "ca_ns_stream_ii_confirmed"
DAYS_NS = "ca_ns_principal_photography_days_in_ns"
PERF_N, PERF_D = "ca_ns_principal_performers_ns_residents", "ca_ns_principal_performers_total"
HF, HR = "ca_ns_hod_positions_filled", "ca_ns_hod_positions_held_by_ns_residents"
CONTENT = ("ca_ns_content_majority_copyright_ns_ownership_confirmed", "ca_ns_content_two_new_trainees_confirmed", "ca_ns_content_post_75pct_in_ns_confirmed",
           "ca_ns_content_ns_resident_producer_confirmed", "ca_ns_content_ns_spend_75pct_confirmed", "ca_ns_content_ns_writer_confirmed", "ca_ns_content_ns_director_confirmed")


def test_nova_scotia_floor_is_the_stream_ii_base_and_every_unknown_addition_is_a_bounded_potential():
    assert NS0.incentive_floor_usd == pytest.approx(25 * PT)
    # potential: Location +2, Distant up to +10, Stream I +1, Shooting Length +1, performers +1.5, three-of-seven +1.5 (the Head-of-Department reduction is presumed met)
    assert NS0.incentive_ceiling_usd == pytest.approx((25 + 2 + 10 + 1 + 1 + 1.5 + 1.5) * PT)


def test_stream_i_adds_one_point_and_stream_ii_removes_the_bound():
    assert ns(facts={S1}).incentive_floor_usd == pytest.approx(26 * PT)
    assert ns(facts={S2}).incentive_ceiling_usd == pytest.approx(NS0.incentive_ceiling_usd - 1 * PT), "stream II stated: no Stream I point is possible"


@pytest.mark.parametrize("days,added", [(30, 0.0), (31, 1.0), (45, 1.0), (0, 0.0)])
def test_shooting_length_needs_more_than_thirty_days(days, added):
    stated = ns(amounts={DAYS_NS: days})
    assert stated.incentive_floor_usd == pytest.approx((25 + added) * PT)


@pytest.mark.parametrize("res,total,met", [(6, 10, True), (3, 5, True), (59, 100, False), (5, 9, False), (60, 100, True), (0, 4, False)])
def test_content_incentive_performers_is_sixty_percent_inclusive(res, total, met):
    stated = ns(amounts={PERF_N: res, PERF_D: total})
    assert stated.incentive_floor_usd == pytest.approx((25 + (1.5 if met else 0.0)) * PT)


def test_content_incentive_three_of_seven_counts_only_stated_true_criteria():
    two = ns(facts=set(CONTENT[:2]))
    assert two.incentive_floor_usd == pytest.approx(25 * PT), "two of seven is not enough"
    assert two.incentive_ceiling_usd == pytest.approx(NS0.incentive_ceiling_usd), "unstated criteria stay a bounded potential"
    three = ns(facts=set(CONTENT[:3]))
    assert three.incentive_floor_usd == pytest.approx(26.5 * PT)


@pytest.mark.parametrize("stream,filled,resident,short", [
    ("II", 8, 4, 0), ("II", 8, 3, 1), ("II", 7, 3, 1), ("II", 7, 4, 0),       # eight or fewer: half rounded up (7 -> 4)
    ("II", 9, 4, 0), ("II", 9, 3, 1), ("II", 16, 4, 0), ("II", 16, 2, 2),     # nine or more: a minimum of four
    ("I", 9, 5, 0), ("I", 9, 4, 1), ("I", 16, 8, 0), ("I", 16, 5, 3),         # Stream I: 50% rounded up (9 -> 5, 16 -> 8)
])
def test_head_of_department_reduction_is_half_a_point_per_missing_position(stream, filled, resident, short):
    stated = ns(amounts={HF: filled, HR: resident}, facts={S1 if stream == "I" else S2})
    base = 26 if stream == "I" else 25
    assert stated.incentive_floor_usd == pytest.approx((base - 0.5 * short) * PT)


def test_unknown_stream_takes_the_worse_reduction_for_the_floor_and_the_better_for_the_potential():
    # 16 filled, 5 resident: Stream I minimum 8 (short 3), Stream II minimum 4 (short 0)
    unknown = ns(amounts={HF: 16, HR: 5})
    assert unknown.incentive_floor_usd == pytest.approx((25 - 1.5) * PT)
    assert unknown.incentive_ceiling_usd == pytest.approx(NS0.incentive_ceiling_usd - 0.0)
    for bad in ({HF: 17, HR: 3}, {HF: 5, HR: 6}):
        refused = ns(amounts=bad)
        assert not refused.executable and refused.blockers, bad


# ── New Brunswick: potential-only grant; the bonuses refine the ceiling, never a guarantee ───────────────────────────────────────────────────────────────────────────────
TOT, RUR, REM = "ca_nb_principal_photography_days_total", "ca_nb_days_rural_30_to_150km", "ca_nb_days_remote_151km_plus"
HODB = "ca_nb_bonus_hod_lead_talent_30pct_confirmed"
MADE = ("ca_nb_made_spend_50pct_confirmed", "ca_nb_made_copyright_50pct_confirmed", "ca_nb_made_writer_nb_resident_confirmed", "ca_nb_made_director_nb_resident_confirmed",
        "ca_nb_made_post_20pct_in_nb_confirmed", "ca_nb_made_photography_days_25pct_in_nb_confirmed")


def nb(**kw):
    return _price(NB, "CA-NB", **kw)


def test_new_brunswick_is_potential_only_at_the_35_percent_combined_ceiling_until_facts_are_stated():
    base = nb()
    assert base.executable and base.incentive_floor_usd == 0.0
    assert base.incentive_ceiling_usd == pytest.approx(35 * PT)                                  # 25 + 3 + 4 + 3, within the 35% cap


@pytest.mark.parametrize("rural,remote,total,points", [
    (4, 8, 20, 3.0),      # 12 of 20 = 60% rural-or-remote, remote alone 40%: the 3% band
    (0, 10, 20, 4.0),     # remote alone is exactly 50%: the 4% band (50%+ inclusive)
    (9, 0, 20, 0.0),      # 45% rural: below 50%
    (10, 0, 20, 3.0),     # exactly 50% rural: 3%
    (3, 7, 20, 3.0),      # 10 of 20 rural-or-remote but remote only 35%: 3%
])
def test_new_brunswick_rural_remote_bonus_uses_the_highest_band_holding_half_the_days(rural, remote, total, points):
    stated = nb(amounts={TOT: total, RUR: rural, REM: remote})
    # HOD (+3) and NB Made (+3) stay unknown bounds; the rural/remote bonus is settled by the stated days
    assert stated.incentive_ceiling_usd == pytest.approx((25 + 3 + points + 3) * PT)


def test_new_brunswick_made_needs_two_stated_criteria_and_stated_facts_cannot_lower_a_bound_they_do_not_contradict():
    one = nb(facts={MADE[0]})
    assert one.incentive_ceiling_usd == pytest.approx(35 * PT)
    two = nb(facts={MADE[0], MADE[1], HODB}, amounts={TOT: 20, RUR: 0, REM: 10})
    assert two.incentive_ceiling_usd == pytest.approx(35 * PT) and two.incentive_floor_usd == 0.0


# ── Missouri: each stated fact adds its points to the 20% base ───────────────────────────────────────────────────────────────────────────────────────────────────────────
BASEF = ("mo_apprentice_or_veteran_minimum_confirmed",)
UP = {"a": "mo_filmed_50pct_in_missouri_confirmed", "b": "mo_rural_or_blighted_15pct_confirmed", "c": "mo_three_departments_missouri_hires_confirmed", "d": "mo_script_markets_missouri_confirmed",
      "county": "mo_second_third_fourth_class_county_confirmed"}


def mo(*keys):
    return _price(MO, "US-MO", facts=set(BASEF) | {UP[k] for k in keys})


@pytest.mark.parametrize("keys,points", [((), 20), (("a",), 25), (("a", "b"), 30), (("a", "b", "c", "d"), 40), (("county",), 22), (("a", "b", "c", "d", "county"), 42)])
def test_missouri_floor_follows_the_stated_uplifts(keys, points):
    r = mo(*keys)
    assert r.incentive_floor_usd == pytest.approx(points * PT)
    assert r.incentive_ceiling_usd == pytest.approx(42 * PT if len(keys) < 5 else 42 * PT), "never above the statute's 42%"


# ── Arkansas: add-ons never push the claimed total above 30% ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_arkansas_addons_are_at_most_five_points_over_the_base_and_per_line_portions_refine_the_bound():
    assert _price(AR, "US-AR").incentive_ceiling_usd == pytest.approx(30 * PT)
    key = f"uplift_basis:{AR}:addons_to_the_30pct_cap:S0"
    refined = _price(AR, "US-AR", amounts={key: 400_000.0}, facts={key})
    assert refined.incentive_ceiling_usd == pytest.approx(25 * PT + 0.05 * 400_000.0)             # 250,000 + 20,000
    assert refined.incentive_floor_usd == 0.0, "a discretionary grant keeps a zero guaranteed floor"


def test_the_combined_caps_are_the_programs_own_statements():
    from app.data.program_rate_rules import SUBSET_COMBINED_RATE_CAPS
    assert {k: v[0] for k, v in SUBSET_COMBINED_RATE_CAPS.items()} == {NB: 0.35, AR: 0.30, MO: 0.42}


def test_every_new_formula_input_has_a_producer_writer():
    from app.data.program_rate_rules import get_subset_uplift_rules
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS, PROGRAM_AMOUNT_FACTS
    for program in (NS, NB, MO, AR):
        for rule in get_subset_uplift_rules(program):
            booleans = [rule.prerequisite_fact, rule.excluded_fact, rule.whole_base_fact, rule.stream_i_fact, rule.stream_ii_fact, *rule.criteria_facts]
            amounts = [rule.day_numerator_fact, rule.day_denominator_fact, rule.hod_filled_fact, rule.hod_resident_fact, *rule.tier_numerator_facts,
                       *[f for g in rule.tier_numerator_groups for f in g]]
            for key in filter(None, booleans):
                assert key in NY_EVIDENCED_FACTS, f"{program}/{rule.uplift_id}: {key} has no boolean writer"
            for key in filter(None, amounts):
                assert key in PROGRAM_AMOUNT_FACTS, f"{program}/{rule.uplift_id}: {key} has no numeric writer"
    assert NY_EVIDENCED_FACTS[S1] == S2 and NY_EVIDENCED_FACTS[S2] == S1


# ── Federal CPTC: contingent liabilities are not production cost (RC4164 line 421) ─────────────────────────────────────────────────────────────────────────────────────────
def test_stated_contingent_liabilities_lower_the_cptc_cost_base_exactly_like_stated_assistance():
    """60% x (cost - assistance - contingent liabilities): labour 2,000,000 against cost 3,000,000 -> cap 1,800,000; a stated 60,000 reserve lowers the cap by 36,000, a stated 40,000 of assistance by 24,000
    (so both together by 60,000 x 0.6 = 60% of 100,000)."""
    from app.calculators.canonical_stack_bridge import cptc_stated_cost_deductions_usd
    assert cptc_stated_cost_deductions_usd(None) == 0.0
    assert cptc_stated_cost_deductions_usd({"ca_federal_cptc_assistance_usd": 40_000.0, "ca_federal_cptc_contingent_liabilities_usd": 60_000.0}) == 100_000.0

    def cptc(amounts):
        allocs = [_alloc("3100", 2_000_000.0, "production", "CA", "S0", "btl_crew_labor")]
        from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
        return price_segment(jurisdiction_code="CA", program_slug="ca_federal_cptc", allocations=allocs, spend_category_by_code={"3100": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(), production_type="feature_film",
                             gross_budget_usd=3_000_000.0, evidenced_requirement_facts=frozenset(_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS), amount_facts=dict(amounts))
    none = cptc({}).incentive_floor_usd
    reserve = cptc({"ca_federal_cptc_contingent_liabilities_usd": 60_000.0}).incentive_floor_usd
    assist = cptc({"ca_federal_cptc_assistance_usd": 60_000.0}).incentive_floor_usd
    assert none == pytest.approx(0.25 * 1_800_000.0)
    assert reserve == pytest.approx(0.25 * (1_800_000.0 - 36_000.0)) == pytest.approx(assist)
    from app.services.ny_producer_facts import PROGRAM_AMOUNT_FACTS
    assert "ca_federal_cptc_contingent_liabilities_usd" in PROGRAM_AMOUNT_FACTS and "ca_federal_cptc_assistance_usd" in PROGRAM_AMOUNT_FACTS
