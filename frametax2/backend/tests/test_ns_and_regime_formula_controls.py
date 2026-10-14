"""NA-RECONCILIATION-17: Nova Scotia Location / Distant Location incentives (NSFPIF Guidelines, April 1, 2024, s.6.1/6.2) and the BC domestic rate regime by principal-photography date
(Income Tax Act (BC) s.80(2),(4),(6),(8)). Synthetic and DB-free; hand arithmetic from the cited text.

Nova Scotia: percentage points of additional funding on ALL Eligible Nova Scotia Costs. Location Incentive +2 points (more than 50% of principal photography rural / non-metropolitan). Distant Location:
up to 10 points, only when first eligible for the Location Incentive; 7% for locations more than 100 km, 10% for more than 150 km from Halifax City Hall, each prorated on distant days / total days."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from tests.test_na_stack_and_gate_repairs_controls import _alloc

NS, BC = "ca_ns_production_incentive_fund", "ca_bc_film_tv_tax_credit"
BASE = 1_000_000.0
RURAL = "ca_ns_rural_majority_principal_photography_confirmed"
T, A, B = "ca_ns_principal_photography_days_total", "ca_ns_principal_photography_days_100_to_150km", "ca_ns_principal_photography_days_over_150km"


def _price(slug, jur, *, amounts=None, facts=frozenset(), gross_factor=2.0, labour=BASE):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    allocs = [_alloc("3100", labour, "production", jur, "S0", "btl_crew_labor")]
    return price_segment(jurisdiction_code=jur, program_slug=slug, allocations=allocs, spend_category_by_code={"3100": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
                         production_type="feature_film", gross_budget_usd=labour * gross_factor, evidenced_requirement_facts=frozenset(facts) | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS,
                         amount_facts=dict(amounts or {}))


def _ns(**kw):
    return _price(NS, "CA-NS", **kw)


NS0 = _ns()


def test_nova_scotia_base_is_unchanged_and_the_unknown_bonuses_are_a_bounded_potential():
    assert NS0.executable and NS0.incentive_floor_usd == pytest.approx(0.25 * BASE)                                   # Stream II base, s.6.2
    # potential: +2 points Location Incentive (whole base) and the guideline's 10-point maximum for the distant incentive
    # Restated in NA-RECONCILIATION-18: the potential also carries the other stated-fact additions (Stream I +1, Shooting Length +1, performers +1.5, three-of-seven +1.5 = 5 points)
    OTHER = 0.05
    assert NS0.incentive_ceiling_usd == pytest.approx((0.25 + 0.02 + 0.10 + OTHER) * BASE)
    ids = {c["condition_id"] for c in NS0.ceiling_conditions}
    assert f"{NS}:distant_location:statutory_formula" in ids and f"{NS}:location_rural:qualified_subset" in ids


@pytest.mark.parametrize("a_days,b_days,total,points", [
    (4, 6, 20, 0.07 * 4 / 20 + 0.10 * 6 / 20),    # 1.4% + 3.0% = 4.4 points
    (0, 20, 20, 0.10),                            # every day beyond 150 km: the full 10 points
    (20, 0, 20, 0.07),                            # every day in the 100-150 km band: 7 points
    (0, 0, 20, 0.0),                              # no distant day
    (1, 0, 40, 0.07 / 40),                        # one day of forty
])
def test_distant_location_incentive_prorates_each_distance_band_on_total_days(a_days, b_days, total, points):
    amounts = {T: total, A: a_days, B: b_days}
    stated = _ns(amounts=amounts, facts={RURAL})
    assert stated.incentive_floor_usd == pytest.approx((0.25 + 0.02 + points) * BASE)
    # the distant-location bound is settled; the other (unrelated) additions still carry their 5 points of bounded potential
    assert stated.incentive_ceiling_usd == pytest.approx(stated.incentive_floor_usd + 0.05 * BASE)


def test_distant_location_needs_the_location_incentive_first():
    amounts = {T: 20, A: 4, B: 6}
    no_rural = _ns(amounts=amounts)
    assert no_rural.incentive_floor_usd == pytest.approx(0.25 * BASE), "the Location Incentive is not stated: neither bonus is confirmed"
    assert no_rural.incentive_ceiling_usd == pytest.approx((0.25 + 0.02 + 0.044 + 0.05) * BASE)
    assert f"{NS}:distant_location:statutory_formula" in {c["condition_id"] for c in no_rural.ceiling_conditions}


def test_partial_band_days_stay_bounded_at_the_guideline_maximum_and_impossible_days_are_refused():
    partial = _ns(amounts={T: 20, A: 4}, facts={RURAL})
    assert partial.incentive_floor_usd == pytest.approx((0.25 + 0.02) * BASE)
    assert partial.incentive_ceiling_usd == pytest.approx((0.25 + 0.02 + 0.10 + 0.05) * BASE)
    for bad in ({T: 20, A: 15, B: 6}, {T: 0}, {T: 20, A: -1, B: 0}, {T: 20, A: 2.5, B: 0}):
        refused = _ns(amounts=bad, facts={RURAL})
        assert not refused.executable and refused.blockers, bad


def test_nova_scotia_inputs_have_producer_writers_and_the_rules_are_exclusive_bands():
    from app.data.program_rate_rules import get_subset_uplift_rules
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS, PROGRAM_AMOUNT_FACTS
    rules = {r.uplift_id: r for r in get_subset_uplift_rules(NS)}
    # Restated in NA-RECONCILIATION-18: the exact-set pin predates the remaining Nova Scotia rules (Stream I, Shooting Length, Content, Head-of-Department), pinned in test_na_bonus_formula_controls.
    assert {"location_rural", "distant_location"} <= set(rules)
    dist = rules["distant_location"]
    assert dist.tier_rates == (0.07, 0.10) and max(dist.tier_rates) == pytest.approx(rules["distant_location"].rate), "never above the guideline's 10-point maximum"
    for key in (dist.day_denominator_fact, *dist.tier_numerator_facts):
        assert key in PROGRAM_AMOUNT_FACTS
    assert dist.prerequisite_fact in NY_EVIDENCED_FACTS and rules["location_rural"].whole_base_fact in NY_EVIDENCED_FACTS


# ── BC domestic rate by the date principal photography BEGINS: s.80(2)+(4)+(6) = 35%; s.80(8) +5% only for photography after December 31, 2024 ────────────────────────────────
AFTER, BEFORE = "ca_bc_film_tv_photography_after_2024_confirmed", "ca_bc_film_tv_photography_before_2025_confirmed"


def _bc(**kw):
    return _price(BC, "CA-BC", gross_factor=2.5, **kw)


def test_bc_domestic_rate_regimes_are_never_mixed():
    none = _bc()
    assert none.incentive_floor_usd == pytest.approx(0.35 * BASE)                                                   # guaranteed 35% in every regime
    assert none.incentive_ceiling_usd == pytest.approx((0.40 + 0.125 + 0.06) * BASE), "unstated date: 40% is a labelled planning scenario"
    after = _bc(facts={AFTER})
    assert after.incentive_floor_usd == pytest.approx(0.40 * BASE), "photography after 2024-12-31: 20+10+5+5 = 40%"
    before = _bc(facts={BEFORE})
    assert before.incentive_floor_usd == pytest.approx(0.35 * BASE), "photography on or before 2024-12-31: 20+10+5 = 35%"
    assert before.incentive_ceiling_usd == pytest.approx((0.35 + 0.125 + 0.06) * BASE), "the historical regime carries no 40% scenario, only the day-ratio bounds"
    assert before.incentive_ceiling_usd < none.incentive_ceiling_usd


def test_the_two_regime_statements_are_mutually_exclusive_writers():
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS
    assert NY_EVIDENCED_FACTS[AFTER] == BEFORE and NY_EVIDENCED_FACTS[BEFORE] == AFTER
