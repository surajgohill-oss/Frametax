"""Focused controls for NY post-credit location rates, the unpriced post upstate uplift and the dated $500,000 ATL cap."""
from __future__ import annotations

from datetime import date

import pytest

from app.calculators.ny_atl_individual_cap import AtlPayeeLine, apply_ny_atl_individual_cap
from app.data.program_rate_rules import resolve_program_rate
from app.data.program_requirements import get_program_requirements

POST = "us_ny_post_production_credit"
FACT = frozenset({"ny_post_facility_outside_mctd"})


def _rate(facts=None, qpe=1_200_000.0):
    return resolve_program_rate(POST, production_type="feature_film", qpe_usd=qpe, evidenced_facts=facts)


def test_post_credit_is_30_percent_in_the_commuter_district_by_default_and_35_only_with_the_evidenced_fact():
    base, outside = _rate(), _rate(FACT)
    assert base.modeled_rate == pytest.approx(0.30) and base.has_guaranteed_floor and base.tier_id == "us-ny-post-base-30-mctd"
    assert outside.modeled_rate == pytest.approx(0.35) and outside.has_guaranteed_floor and outside.tier_id == "us-ny-post-outside-mctd-35"


def test_post_minimum_spend_still_gates_both_rates():
    assert _rate(qpe=900_000.0) is None and _rate(FACT, qpe=900_000.0) is None


def test_post_upstate_uplift_is_disclosed_on_its_own_base_and_never_priced_as_a_rate():
    for facts in (None, FACT):
        r = _rate(facts)
        cond = next(c for c in r.conditions_evaluated if c.condition_id == "us-ny-post-upstate-wage-uplift-not-modeled")
        assert cond.satisfied is None and "EXCLUDES writers, directors, composers, producers and performers" in cond.description
        assert r.modeled_rate in (0.30, 0.35), "no +10% was added to the whole base"
    assert "Tax Law 31(a)(6)" in get_program_requirements(POST).additional_facts["upstate_uplift"]


def test_cap_applies_only_to_an_identified_payee_with_complete_compensation():
    lines = [AtlPayeeLine("a", 400_000.0, "p1", True), AtlPayeeLine("b", 300_000.0, "p1", True),
             AtlPayeeLine("c", 450_000.0, "p2", True)]
    res = apply_ny_atl_individual_cap(lines, costs_incurred_on_or_after=date(2024, 1, 1))
    assert res.applied and res.capped_payees == {"p1": 700_000.0, "p2": 450_000.0}
    assert sum(res.excess_usd_by_line.values()) == 200_000.0 and set(res.excess_usd_by_line) <= {"a", "b"}   # p1 only; p2 is under the cap
    assert not res.unresolved_line_ids


def test_cap_is_never_applied_to_an_aggregate_account_or_incomplete_compensation():
    lines = [AtlPayeeLine("agg", 750_000.0), AtlPayeeLine("x", 700_000.0, "p1", False), AtlPayeeLine("y", 600_000.0, None, True)]
    res = apply_ny_atl_individual_cap(lines, costs_incurred_on_or_after=date(2024, 1, 1))
    assert res.excess_usd_by_line == {} and set(res.unresolved_line_ids) == {"agg", "x", "y"} and res.unresolved_usd == 2_050_000.0


def test_cap_is_not_applied_without_an_established_incurred_date_or_before_the_effective_date():
    line = [AtlPayeeLine("a", 900_000.0, "p1", True)]
    for when in (None, date(2023, 3, 31)):
        res = apply_ny_atl_individual_cap(line, costs_incurred_on_or_after=when)
        assert res.applied is False and res.excess_usd_by_line == {} and res.unresolved_line_ids == ("a",)
    assert apply_ny_atl_individual_cap(line, costs_incurred_on_or_after=date(2023, 4, 1)).excess_usd_by_line == {"a": 400_000.0}


def test_program_record_dates_the_cap_and_names_what_stays_unresolved():
    cap = get_program_requirements("ny_state_film").additional_facts["atl_per_individual_cap_guidance"]
    assert cap.startswith("DATED AGENCY RULE") and "20250418" in cap and "April 1, 2023" in cap and "2025-07-11" in cap
    assert "UNRESOLVED" in cap and "never capped or assumed" in cap
    assert "ny_post_facility_outside_mctd" in get_program_requirements(POST).additional_facts["rate_by_facility_location"]
