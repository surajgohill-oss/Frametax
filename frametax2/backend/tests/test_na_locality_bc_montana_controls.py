"""NA-RECONCILIATION-23: BC 'eligible production' 75% requirements, Montana category rates with person-cap ranges, and the canonical locality resolver.

Isolated synthetic fixtures only (rolled back; no real production is read or evaluated). Every expectation is hand-derived from the text cited beside it:
- Income Tax Act (BC) s.79(1) 'eligible production': at least 75% of the cost payable to BC-based individuals or corporations for BC goods and services; at least 75% of postproduction work cost carried out in
  BC; principal photography in BC on at least 75% of the days; six Canadian-content points; a written broadcaster / distributor agreement.
- MCA 15-31-1007(3)(b): resident crew 25% (credit not above USD 150,000 per person); non-resident crew 15% (USD 150,000 per person); actors, directors, producers, writers 20% of the first USD 7,500,000
  per person; students 30% (USD 50,000 each); resident veterans / tribal members 30% (USD 150,000 each). Compensation is not a 'production expenditure' (15-31-1003(13)(b)(i)).
- RSMo 135.750 subsection 3: +5 points at least 50% filmed in Missouri; +5 points at least 15% of the Missouri filming in a rural or blighted area; +2 points for a second-, third- or fourth-class county."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators import locality as loc
from app.calculators.allocation_pricing import price_segment
from app.calculators.scenario_facts import SCHEDULE_TOTAL_DAYS_FACT, refuted, scenario_derived_facts
from tests.isolated_records import create_synthetic_project, isolated_session
from tests.test_na_stack_and_gate_repairs_controls import _alloc

MT = "us_mt_media_act_tax_credit"
MO = "us_mo_motion_media_production_tax_credit"
BCD = "ca_bc_film_tv_tax_credit"
BCP = "ca_bc_pstc"
NS, NB, SK = "ca_ns_production_incentive_fund", "ca_nb_film_tax_credit", "ca_sk_creative_saskatchewan_grant"
BC_REQ = {"cost": "ca_bc_film_tv_bc_cost_75pct_confirmed", "post": "ca_bc_film_tv_post_75pct_in_bc_confirmed", "days": "ca_bc_film_tv_photography_days_75pct_in_bc_confirmed",
          "cc": "ca_bc_film_tv_canadian_content_6_points_confirmed", "agreement": "ca_bc_film_tv_distribution_agreement_confirmed"}


# ── Montana: the KNOWN category rate; only the per-person cap is a range ─────────────────────────────────────────────────────────────────────────

def _mt(compensation_usd, amounts, facts=()):
    """All of `compensation_usd` is qualifying personnel spend in Montana; additions stated 0 and the screen credit refuted so the total IS the compensation credit (the 20% base leaves the compensation)."""
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P
    zero = {"us_mt_media_expenditure_year": 2031.0, "us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 0.0,
            "us_mt_underserved_area_expenditure_usd": 0.0}
    seg = price_segment(jurisdiction_code="US-MT", program_slug=MT, allocations=[_alloc("3100", compensation_usd, "production", "US-MT", "S0", "btl_crew_labor")],
                        spend_category_by_code={"3100": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=2 * compensation_usd,
                        confirmed_ceiling_programs=frozenset({MT}), evidenced_requirement_facts=frozenset(facts) | {refuted("us_mt_screen_credit_furnished_confirmed")} | P,
                        amount_facts={**zero, **amounts})
    return seg.incentive_floor_usd, seg.incentive_ceiling_usd


def _resident(c):  # derived from the normalized budget: btl_resident_labor
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P
    zero = {"us_mt_media_expenditure_year": 2031.0, "us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 0.0,
            "us_mt_underserved_area_expenditure_usd": 0.0}
    seg = price_segment(jurisdiction_code="US-MT", program_slug=MT, allocations=[_alloc("3100", c, "production", "US-MT", "S0", "btl_resident_labor")],
                        spend_category_by_code={"3100": "btl_resident_labor"}, offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=2 * c,
                        confirmed_ceiling_programs=frozenset({MT}), evidenced_requirement_facts=frozenset({refuted("us_mt_screen_credit_furnished_confirmed")}) | P, amount_facts=zero)
    return seg.incentive_floor_usd, seg.incentive_ceiling_usd


def test_normalized_resident_crew_compensation_is_25_percent_with_only_the_person_cap_as_a_range():
    floor, ceiling = _resident(1_000_000.0)
    assert (floor, ceiling) == pytest.approx((150_000.0, 250_000.0)), "one-person lower bound min(25% x 1,000,000, 150,000); potential 25% x 1,000,000 - never the 300,000 of the 30% maximum"
    assert ceiling < 300_000.0


@pytest.mark.parametrize("category,rate,persons,expected", [
    # (comp 1,000,000) resident crew 25%, USD 150,000 per person: cap binds below 2 persons (2 x 150,000 = 300,000 >= 250,000)
    ("resident_crew", 0.25, 1, 150_000.0), ("resident_crew", 0.25, 2, 250_000.0), ("resident_crew", 0.25, 10, 250_000.0),
    # non-resident crew 15%: 150,000 = the cap exactly, so one person is already uncapped
    ("nonresident_crew", 0.15, 1, 150_000.0), ("nonresident_crew", 0.15, 10, 150_000.0),
    # students 30%, USD 50,000 each: 5 persons = 250,000 < 300,000 (binds); 6 = 300,000 (exactly the credit); 7 = 350,000 (not binding)
    ("student", 0.30, 5, 250_000.0), ("student", 0.30, 6, 300_000.0), ("student", 0.30, 7, 300_000.0), ("student", 0.30, 1, 50_000.0),
    # veterans / tribal 30%, USD 150,000 each: 1 person binds at 150,000; 2 persons = 300,000 exactly the credit
    ("veteran_tribal", 0.30, 1, 150_000.0), ("veteran_tribal", 0.30, 2, 300_000.0), ("veteran_tribal", 0.30, 3, 300_000.0),
])
def test_every_category_is_priced_at_its_own_rate_with_identified_persons_exact(category, rate, persons, expected):
    key = f"us_mt_{category}_compensation_usd"
    floor, ceiling = _mt(1_000_000.0, {key: 1_000_000.0, f"us_mt_{category}_persons": float(persons)})
    assert floor == pytest.approx(expected) and ceiling == pytest.approx(expected), f"{category}: {rate:.0%} x 1,000,000 with {persons} identified person(s)"


@pytest.mark.parametrize("category,rate,low,high", [
    ("resident_crew", 0.25, 150_000.0, 250_000.0),       # one person: min(250,000, 150,000); many: 25% x 1,000,000
    ("nonresident_crew", 0.15, 150_000.0, 150_000.0),    # 15% x 1,000,000 = 150,000 equals the per-person cap: no range
    ("student", 0.30, 50_000.0, 300_000.0),              # one student's cap USD 50,000; many: 30% x 1,000,000
    ("veteran_tribal", 0.30, 150_000.0, 300_000.0),
    ("talent", 0.20, 200_000.0, 200_000.0),              # 20% x the first 7,500,000 per person: 1,000,000 is under it for one person already
])
def test_an_unknown_person_count_is_a_range_at_the_known_category_rate_never_the_highest_rate(category, rate, low, high):
    floor, ceiling = _mt(1_000_000.0, {f"us_mt_{category}_compensation_usd": 1_000_000.0})
    assert (floor, ceiling) == pytest.approx((low, high))
    assert ceiling <= rate * 1_000_000.0 + 0.01, f"{category}: the potential can never exceed the known category rate on all of the compensation"


@pytest.mark.parametrize("compensation,persons,expected", [
    (7_500_000.0, 1, 1_500_000.0),        # exactly the first 7,500,000: 20% x 7,500,000
    (7_500_001.0, 1, 1_500_000.0),        # one person: only the first 7,500,000 earns the credit
    (7_500_001.0, 2, 1_500_000.2),        # two persons: both under 7,500,000 each, so 20% x 7,500,001
    (8_000_000.0, 1, 1_500_000.0), (8_000_000.0, 2, 1_600_000.0),
])
def test_talent_credit_is_20_percent_of_the_first_7_5_million_per_person(compensation, persons, expected):
    floor, ceiling = _mt(compensation, {"us_mt_talent_compensation_usd": compensation, "us_mt_talent_persons": float(persons)})
    assert (floor, ceiling) == pytest.approx((expected, expected))


def test_talent_with_unknown_persons_ranges_from_one_person_to_all_of_the_compensation():
    floor, ceiling = _mt(8_000_000.0, {"us_mt_talent_compensation_usd": 8_000_000.0})
    assert (floor, ceiling) == pytest.approx((1_500_000.0, 1_600_000.0))


def test_compensation_of_unknown_category_keeps_the_highest_rate_bound_and_only_that_part():
    # 1,000,000 of personnel: 400,000 known resident crew (persons unknown), 600,000 of unknown category
    floor, ceiling = _mt(1_000_000.0, {"us_mt_resident_crew_compensation_usd": 400_000.0})
    assert (floor, ceiling) == pytest.approx((min(0.25 * 400_000.0, 150_000.0), 0.25 * 400_000.0 + 0.30 * 600_000.0)), "known part at 25%, unknown part bounded at the 30% maximum"


# ── BC: the five 'eligible production' requirements are separate resolved requirements ──────────────────────────────────────────────────────────

def _rows(bc, other, comp="principal_photography"):
    return [("CA-BC", float(bc), comp, "x"), ("CA-MB", float(other), comp, "y")]


@pytest.mark.parametrize("bc,other,state", [(749_999.99, 250_000.01, False), (750_000.0, 250_000.0, True), (750_000.01, 249_999.99, True)])
def test_bc_cost_requirement_at_the_75_percent_boundary(bc, other, state):
    rows = [("CA-BC", bc, "btl_crew_labor", "x"), ("CA-MB", other, "btl_crew_labor", "y")]
    sf = scenario_derived_facts(BCD, "CA-BC", rows, "CA-BC")
    key = BC_REQ["cost"]
    assert (key in sf.true_facts) is state and (key in sf.refuted_facts) is (not state)


@pytest.mark.parametrize("bc,other,state", [(74.0, 26.0, False), (75.0, 25.0, True), (76.0, 24.0, True)])
def test_bc_postproduction_requirement_counts_only_postproduction_allocations(bc, other, state):
    rows = [("CA-BC", 5_000_000.0, "btl_crew_labor", "x"), ("CA-BC", bc, "post", "x"), ("CA-MB", other, "post", "y")]
    sf = scenario_derived_facts(BCD, "CA-BC", rows, "CA-BC")
    key = BC_REQ["post"]
    assert (key in sf.true_facts) is state and (key in sf.refuted_facts) is (not state)


def test_bc_postproduction_requirement_is_not_derived_without_postproduction_allocations():
    sf = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 1_000_000.0, "btl_crew_labor", "x")], "CA-BC")
    assert BC_REQ["post"] not in sf.true_facts | sf.refuted_facts, "no postproduction cost: nothing to establish; the exact requirement stays"


def test_bc_75_percent_days_for_full_none_and_split_relocations():
    full = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 1.0, "principal_photography", "x")], "CA-BC")
    none = scenario_derived_facts(BCD, "CA-BC", [("CA-MB", 1.0, "principal_photography", "x")], "CA-MB")
    split = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 900.0, "principal_photography", "x"), ("CA-MB", 100.0, "principal_photography", "y")], "CA-BC")
    nothing = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 1.0, "btl_crew_labor", "x")], None)
    assert BC_REQ["days"] in full.true_facts and BC_REQ["days"] in none.refuted_facts
    assert BC_REQ["days"] not in split.true_facts | split.refuted_facts, "90% of the DOLLARS is not 90% of the days"
    assert BC_REQ["days"] not in nothing.true_facts | nothing.refuted_facts, "no principal photography modeled: Unknown"


@pytest.mark.parametrize("bc_days,state", [(29, False), (30, True), (31, True)])
def test_bc_75_percent_days_from_exact_schedule_locations_at_the_boundary(bc_days, state):
    stated = {SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts([
        loc.LocationEntry("a", "BC", "CA-BC", days=bc_days), loc.LocationEntry("b", "Elsewhere", "CA-MB", days=40 - bc_days)])}
    sf = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 500.0, "principal_photography", "x"), ("CA-MB", 500.0, "principal_photography", "y")], "CA-BC", amount_facts=stated)
    key = BC_REQ["days"]
    assert (key in sf.true_facts) is state and (key in sf.refuted_facts) is (not state), "30 of 40 days is exactly 75%"


def test_canadian_content_points_and_the_distribution_agreement_are_never_assumed():
    sf = scenario_derived_facts(BCD, "CA-BC", [("CA-BC", 1.0, "principal_photography", "x")], "CA-BC", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 30.0})
    assert not ({BC_REQ["cc"], BC_REQ["agreement"]} & (sf.true_facts | sf.refuted_facts))


def test_a_failed_bc_requirement_removes_the_credit_and_an_unstated_one_leaves_the_conditional_figure():
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P

    def price(extra):
        return price_segment(jurisdiction_code="CA-BC", program_slug=BCD, allocations=[_alloc("3100", 1_000_000.0, "production", "CA-BC", "S0", "btl_crew_labor")],
                             spend_category_by_code={"3100": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=2_000_000.0,
                             evidenced_requirement_facts=frozenset({"ca_bc_film_tv_tax_credit__cultural_test_confirmed", "ca_bc_film_tv_tax_credit__local_entity_or_partner_confirmed",
                                                                    "ca_bc_film_tv_photography_after_2024_confirmed"} | set(extra)) | P, amount_facts={})
    unstated, stated = price([]), price(BC_REQ.values())
    assert unstated.executable and unstated.incentive_floor_usd == pytest.approx(400_000.0) and unstated.ceiling_requires_confirmation is True
    assert stated.executable and stated.incentive_floor_usd == pytest.approx(400_000.0)
    for k in BC_REQ.values():
        failed = price([refuted(k)])
        assert not failed.executable and failed.incentive_floor_usd == 0.0, f"{k}: a requirement that is NOT met removes the credit for that scenario"


# ── locality resolver ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_missouri_county_dataset_is_transcribed_with_its_one_known_gap_and_never_guessed():
    counts = {k: len(v) for k, v in loc._MO_CLASSES.items()}
    stated = loc.MO_COUNTY_DATASET["stated_totals"]
    assert counts == {"charter": 5, "1": 12, "2": 3, "3": 89, "4": 4}
    assert {k: stated[k] - counts[k] for k in stated} == {"charter": 0, "1": 1, "2": 0, "3": 0, "4": 0}, "the published class-1 row shows 12 of 13: one county is not in the dataset"
    assert sum(counts.values()) == 113 and len(loc._MO_INDEX) == 113, "no county is listed in two classes"


@pytest.mark.parametrize("county,cls,qualifies", [("Johnson County", "4", True), ("johnson", "4", True), ("Callaway", "2", True), ("Adair", "3", True), ("Saint Clair", "3", True),
                                                  ("Ste. Genevieve", "3", True), ("Boone", "1", False), ("St. Louis", "charter", False), ("Jackson County", "charter", False)])
def test_missouri_county_class_and_the_second_third_fourth_class_uplift(county, cls, qualifies):
    r = loc.resolve(loc.LocationEntry("a", "x", "US-MO", county=county))
    assert r.resolution["county_class"]["value"] == cls and r.states["mo_county_qualifying"] is qualifies
    assert r.resolution["county_class"]["method"] == "DATASET_LOOKUP" and r.resolution["county_class"]["version"] == "2025-05"


@pytest.mark.parametrize("county", [None, "", "Atlantis", "Newton", "Franklin"])   # Cole left this list in NA-RECONCILIATION-24: the Official Manual resolves it
def test_an_unknown_or_unlisted_county_stays_unknown_and_names_what_is_missing(county):
    r = loc.resolve(loc.LocationEntry("a", "x", "US-MO", county=county))
    assert r.states["mo_county_qualifying"] is None and "county_class" in r.unresolved
    assert "rural_or_blighted" in r.unresolved and "Department of Economic Development" in r.unresolved["rural_or_blighted"]


def _mo_facts(entries, total=30.0, rows=None, evidenced=()):
    stated = {SCHEDULE_TOTAL_DAYS_FACT: total, **loc.locality_amount_facts(entries)}
    rows = rows or [("US-MO", 1.0, "principal_photography", "x")]
    return scenario_derived_facts(MO, "US-MO", rows, "US-MO", evidenced, stated)


def _rural(value, source="MO DED determination"):
    return {"attributes": {"rural_or_blighted": value}, "evidence": {"rural_or_blighted": {"source": source, "method": "AUTHORITY_DETERMINATION", "confidence": "AUTHORITATIVE"}}}


def test_a_full_missouri_shoot_in_a_qualifying_county_earns_filming_county_and_rural_when_the_location_is_rural():
    entry = loc.validate_entry({"id": "a", "label": "Johnson County set", "jurisdiction_code": "US-MO", "county": "Johnson County", **_rural(True)})
    sf = _mo_facts([entry])
    assert {"mo_filmed_50pct_in_missouri_confirmed", "mo_second_third_fourth_class_county_confirmed", "mo_rural_or_blighted_15pct_confirmed"} <= sf.true_facts


def test_missouri_rural_share_boundary_is_15_percent_of_the_missouri_filming_days():
    def run(rural_days, other_days, unknown_days=0):
        entries = [loc.validate_entry({"id": "r", "label": "r", "jurisdiction_code": "US-MO", "county": "Boone", "days": rural_days, **_rural(True)}),
                   loc.validate_entry({"id": "n", "label": "n", "jurisdiction_code": "US-MO", "county": "Boone", "days": other_days, **_rural(False)})]
        if unknown_days:
            entries.append(loc.LocationEntry("u", "u", "US-MO", county="Boone", days=unknown_days))
        return _mo_facts(entries, total=float(rural_days + other_days + unknown_days))
    key = "mo_rural_or_blighted_15pct_confirmed"
    assert key in run(3, 17).true_facts, "3 of 20 days is exactly 15%"
    assert key in run(2, 18).refuted_facts, "2 of 20 days is 10% and every location is classified"
    below = run(2, 10, 8)
    assert key not in below.true_facts | below.refuted_facts, "2 of 20 known rural, 8 days unclassified: 10% to 50%, Unknown"
    assert key in run(3, 9, 8).true_facts, "3 of 20 rural is already 15% whatever the unclassified days are"


def test_unknown_locality_preserves_the_conditional_upside_and_names_the_exact_requirement():
    sf = _mo_facts([])
    assert sf.true_facts == frozenset({"mo_filmed_50pct_in_missouri_confirmed"}), "the scenario alone establishes only the filming test"
    from app.services.resolved_facts import locality_requirement
    assert "county" in locality_requirement("mo_second_third_fourth_class_county_confirmed")
    rural = locality_requirement("mo_rural_or_blighted_15pct_confirmed")
    assert "Source still required" in rural and "Department of Economic Development" in rural


def test_missouri_filming_from_exact_split_schedule_days():
    def run(mo_days):
        entries = [loc.LocationEntry("a", "a", "US-MO", days=mo_days), loc.LocationEntry("b", "b", "CA-MB", days=40 - mo_days)]
        return scenario_derived_facts(MO, "US-MO", [("US-MO", 1.0, "principal_photography", "x"), ("CA-MB", 1.0, "principal_photography", "y")], "US-MO",
                                      amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts(entries)})
    key = "mo_filmed_50pct_in_missouri_confirmed"
    assert key in run(20).true_facts and key in run(21).true_facts and key in run(19).refuted_facts


@pytest.mark.parametrize("distance,a,b", [(100.0, False, False), (100.01, True, False), (150.0, True, False), (150.01, False, True)])
def test_nova_scotia_distance_bands_follow_more_than_100_and_more_than_150_km(distance, a, b):
    r = loc.resolve(loc.validate_entry({"id": "a", "label": "a", "jurisdiction_code": "CA-NS", "attributes": {"ns_distance_km": distance},
                                        "evidence": {"ns_distance_km": {"source": "producer measurement", "method": "PRODUCER_MEASURED", "confidence": "MEASURED"}}}))
    assert (r.states["ns_zone_a"], r.states["ns_zone_b"]) == (a, b)


@pytest.mark.parametrize("distance,rural,remote", [(29.99, False, False), (30.0, True, False), (150.0, True, False), (150.5, None, None), (151.0, False, True)])
def test_new_brunswick_bands_are_30_to_150_and_151_plus_with_the_fraction_between_undefined(distance, rural, remote):
    r = loc.resolve(loc.validate_entry({"id": "a", "label": "a", "jurisdiction_code": "CA-NB", "attributes": {"nb_distance_km": distance},
                                        "evidence": {"nb_distance_km": {"source": "producer measurement", "method": "PRODUCER_MEASURED", "confidence": "MEASURED"}}}))
    assert (r.states["nb_rural"], r.states["nb_remote"]) == (rural, remote)


@pytest.mark.parametrize("distance,state", [(49.99, False), (50.0, True)])
def test_saskatchewan_rural_is_at_least_50_km(distance, state):
    r = loc.resolve(loc.validate_entry({"id": "a", "label": "a", "jurisdiction_code": "CA-SK", "attributes": {"sk_distance_km": distance},
                                        "evidence": {"sk_distance_km": {"source": "producer measurement", "method": "PRODUCER_MEASURED", "confidence": "MEASURED"}}}))
    assert r.states["sk_rural50"] is state


def _zone(eid, zone, days):
    return loc.validate_entry({"id": eid, "label": eid, "jurisdiction_code": "CA-BC", "days": days, "attributes": {"bc_zone": zone},
                               "evidence": {"bc_zone": {"source": "Creative BC regional map", "method": "PRODUCER_ASSERTED", "confidence": "STATED"}}})


def test_bc_regional_and_distant_days_are_exact_schedule_days_at_resolved_locations_never_dollars():
    entries = [_zone("v", "vancouver", 10), _zone("r", "regional", 20), _zone("d", "distant", 10)]
    stated = {SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts(entries)}
    sf = scenario_derived_facts(BCP, "CA-BC", [("CA-BC", 1_000_000.0, "principal_photography", "x")], "CA-BC", amount_facts=stated)
    assert sf.amounts["ca_bc_principal_photography_days_in_bc"] == 40.0
    assert sf.amounts["ca_bc_principal_photography_days_outside_vancouver"] == 30.0 and sf.amounts["ca_bc_principal_photography_days_distant_location"] == 10.0
    partial = [_zone("v", "vancouver", 10), loc.LocationEntry("u", "u", "CA-BC", days=30)]
    sf2 = scenario_derived_facts(BCP, "CA-BC", [("CA-BC", 1_000_000.0, "principal_photography", "x")], "CA-BC",
                                 amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts(partial)})
    assert "ca_bc_principal_photography_days_outside_vancouver" not in sf2.amounts, "30 days at an unclassified location: the regional days stay Unknown"
    dollars_only = scenario_derived_facts(BCP, "CA-BC", [("CA-BC", 9_000_000.0, "principal_photography", "x")], "CA-BC", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0})
    assert "ca_bc_principal_photography_days_outside_vancouver" not in dollars_only.amounts


def test_a_stated_locality_day_count_is_never_overwritten():
    entries = [_zone("r", "regional", 40)]
    sf = scenario_derived_facts(BCP, "CA-BC", [("CA-BC", 1.0, "principal_photography", "x")], "CA-BC",
                                amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0, "ca_bc_principal_photography_days_outside_vancouver": 12.0, **loc.locality_amount_facts(entries)})
    assert "ca_bc_principal_photography_days_outside_vancouver" not in sf.amounts


@pytest.mark.parametrize("raw,match", [
    ({"id": "a", "jurisdiction_code": "Missouri"}, "jurisdiction_code"),
    ({"id": "a", "jurisdiction_code": "US-MO", "days": 1.5}, "days"),
    ({"id": "a", "jurisdiction_code": "US-MO", "attributes": {"rural_or_blighted": True}}, "source"),
    ({"id": "a", "jurisdiction_code": "US-MO", "attributes": {"rural_or_blighted": "yes"}, "evidence": {"rural_or_blighted": {"source": "s", "method": "PRODUCER_ASSERTED", "confidence": "STATED"}}}, "true or false"),
    ({"id": "a", "jurisdiction_code": "CA-BC", "attributes": {"bc_zone": "downtown"}, "evidence": {"bc_zone": {"source": "s", "method": "PRODUCER_ASSERTED", "confidence": "STATED"}}}, "bc_zone"),
    ({"id": "a", "jurisdiction_code": "CA-NS", "attributes": {"ns_distance_km": -1}, "evidence": {"ns_distance_km": {"source": "s", "method": "PRODUCER_MEASURED", "confidence": "MEASURED"}}}, "kilometres"),
    ({"id": "a", "jurisdiction_code": "US-MO", "attributes": {"vibe": 1}}, "locality attribute"),
])
def test_invalid_locations_are_refused_and_nothing_is_defaulted(raw, match):
    with pytest.raises(ValueError, match=match):
        loc.validate_entry(raw)


@pytest.mark.asyncio
async def test_locations_persist_change_the_fingerprint_once_restore_on_cold_reload_and_unchanged_saves_do_nothing():
    from sqlalchemy import func

    from app.models.production import EvaluationGenerationSummary
    from app.models.project_fact import ProjectFact
    from app.services import canonical_evaluation as ce
    from app.services.canonical_evaluation import current_generation_fingerprint
    from app.services.canonical_production_view import build_production_and_structures
    from app.services.shoot_locations import entries_from_rows, write_shoot_locations
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))

        async def generations():
            return (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary).where(EvaluationGenerationSummary.project_id == project_id))).scalar_one()

        base_fp = await current_generation_fingerprint(db, project_id)
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 1
        boone = {"id": "a", "label": "Set A", "jurisdiction_code": "US-MO", "city": "Columbia", "county": "Boone County", "days": 12}
        await write_shoot_locations(db, project_id, [boone])
        class1_fp = await current_generation_fingerprint(db, project_id)
        assert class1_fp != base_fp, "an explicit location is a changed economic input"
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 2
        await write_shoot_locations(db, project_id, [boone])                                           # the same save again
        assert await current_generation_fingerprint(db, project_id) == class1_fp
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_REUSED" and await generations() == 2
        await write_shoot_locations(db, project_id, [{**boone, "county": "Johnson County"}])           # class 1 -> class 4 changes the facts
        assert await current_generation_fingerprint(db, project_id) != class1_fp
        db.expunge_all()
        view = (await build_production_and_structures(db, project_id))["production"]["shoot_locations"]
        got = view["locations"][0]
        assert got["classifications"]["county_class"]["value"] == "4" and got["classifications"]["county_class"]["method"] == "DATASET_LOOKUP" and got["states"]["mo_county_qualifying"] is True
        assert "rural_or_blighted" in got["unresolved"], "the rural / blighted classification stays OPEN and names its source"
        rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == project_id))).scalars().all()
        assert [e.county for e in entries_from_rows(rows)] == ["Johnson County"]
        await write_shoot_locations(db, project_id, [])
        assert await current_generation_fingerprint(db, project_id) == base_fp, "clearing the locations restores Unknown and the original fingerprint"
        with pytest.raises(ValueError):
            await write_shoot_locations(db, project_id, [boone, boone])


@pytest.mark.asyncio
async def test_the_served_view_scopes_every_fact_to_its_programs_and_sorts_it_into_one_of_five_categories():
    from app.services import ny_producer_facts as npf
    from app.services.producer_fact_catalog import program_facts_view
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))

        def facts(view):
            return {f["key"]: f for g in view["groups"] for f in g["facts"]}

        fresh = facts(await program_facts_view(db, project_id))
        assert all(f["programs"] and f["category"] in {"SATISFIED", "FAILED", "EXTERNAL_APPROVAL", "CONDITIONAL_UPSIDE", "PRODUCER_INPUT"} for f in fresh.values())
        assert MO in fresh["mo_filmed_50pct_in_missouri_confirmed"]["programs"] and BCD in fresh[BC_REQ["days"]]["programs"] and MO not in fresh[BC_REQ["days"]]["programs"]
        assert fresh["mo_filmed_50pct_in_missouri_confirmed"]["category"] == "CONDITIONAL_UPSIDE" and fresh["mo_filmed_50pct_in_missouri_confirmed"]["effect_points"] == 0.05
        assert fresh[BC_REQ["cc"]]["category"] == "PRODUCER_INPUT" and fresh["us_or_opif_award_confirmed"]["category"] == "EXTERNAL_APPROVAL"
        assert "Source still required" in fresh["mo_rural_or_blighted_15pct_confirmed"]["requirement"] and "county" in fresh["mo_second_third_fourth_class_county_confirmed"]["requirement"]
        await npf.write_ny_program_facts(db, project_id, evidenced={"mo_filmed_50pct_in_missouri_confirmed": False, BC_REQ["cc"]: True, "mo_script_markets_missouri_confirmed": None})
        after = facts(await program_facts_view(db, project_id))
        assert after["mo_filmed_50pct_in_missouri_confirmed"]["category"] == "FAILED" and "+5 points are not earned" in after["mo_filmed_50pct_in_missouri_confirmed"]["failure_effect"]
        assert after[BC_REQ["cc"]]["category"] == "SATISFIED" and after[BC_REQ["cc"]]["state"] == "TRUE"
        assert after[BC_REQ["days"]]["failure_effect"] == "the credit is not available", "a failed rate requirement removes the credit"
