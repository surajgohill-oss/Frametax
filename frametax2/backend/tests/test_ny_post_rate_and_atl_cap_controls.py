"""Focused controls for NY post-credit location rates, the unpriced post upstate uplift and the dated $500,000 ATL cap."""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.data.program_rate_rules import resolve_program_rate
from app.data.program_requirements import get_program_requirements

POST = "us_ny_post_production_credit"
FACT = frozenset({"ny_post_facility_outside_mctd"})
INSIDE = frozenset({"ny_post_facility_inside_mctd"})
NY_FILM = "ny_state_film"


def _rate(facts=None, qpe=1_200_000.0):
    return resolve_program_rate(POST, production_type="feature_film", qpe_usd=qpe, evidenced_facts=facts)


def test_post_credit_location_states_unknown_inside_outside():
    unknown, inside, outside = _rate(), _rate(INSIDE), _rate(FACT)
    # Unknown: 30% guaranteed, 35% carried as a conditional planning scenario (a ceiling needing the location fact).
    assert unknown.floor_rate == pytest.approx(0.30) and unknown.has_guaranteed_floor and unknown.modeled_rate == pytest.approx(0.35)
    assert unknown.is_band_ceiling and any(c.satisfied is None and c.condition_id == "us-ny-post-facility-outside-mctd" for c in unknown.conditions_evaluated)
    assert "NO guaranteed" not in unknown.basis and "conditional planning scenario" in unknown.basis
    # Stated inside the district: the scenario disappears.
    assert inside.modeled_rate == pytest.approx(0.30) and not inside.is_band_ceiling and inside.tier_id == "us-ny-post-base-30-mctd"
    # Stated outside: 35% is the guaranteed rate.
    assert outside.modeled_rate == pytest.approx(0.35) and outside.floor_rate == pytest.approx(0.35) and not outside.is_band_ceiling


def test_post_minimum_spend_still_gates_every_rate():
    assert _rate(qpe=900_000.0) is None and _rate(FACT, qpe=900_000.0) is None and _rate(INSIDE, qpe=900_000.0) is None


def test_post_upstate_uplift_is_a_priced_subset_rule_on_wages_not_a_rate():
    from app.data.program_rate_rules import get_subset_uplift_rules
    (rule,) = get_subset_uplift_rules(POST)
    assert rule.uplift_id == "upstate_post_wages" and rule.rate == 0.10 and rule.min_gross_budget_usd == 500_000.0
    assert rule.eligible_categories == frozenset({"post_production", "sound", "vfx"}) and "music" not in rule.eligible_categories
    assert rule.whole_base_fact is None, "wages need a per-line evidenced portion; facility fees are not wages"
    for facts in (None, FACT, INSIDE):
        assert _rate(facts).modeled_rate in (0.30, 0.35), "no +10% was added to a rate"
    assert "Tax Law 31(a)(6)" in get_program_requirements(POST).additional_facts["upstate_uplift"]


def test_production_uplifts_are_rules_on_their_own_bases_and_the_whole_base_ceilings_are_gone():
    from app.data.program_rate_rules import get_subset_uplift_rules
    rules = {r.uplift_id: r for r in get_subset_uplift_rules("ny_state_film")}
    assert set(rules) == {"upstate_labor", "upstate_other_costs", "scoring", "production_plus_10", "production_plus_5"}
    assert rules["upstate_labor"].eligible_categories >= {"atl_director", "atl_cast", "btl_crew_labor"} and rules["upstate_labor"].min_gross_budget_usd == 500_000.0
    assert rules["upstate_other_costs"].prerequisite_fact == "ny_majority_principal_photography_days_in_listed_counties"
    assert rules["upstate_other_costs"].excluded_categories >= rules["upstate_labor"].eligible_categories
    assert rules["scoring"].eligible_categories == frozenset({"music"}) and rules["scoring"].prerequisite_fact == "ny_scoring_five_musicians_in_state"
    assert rules["production_plus_10"].exclusive_group == rules["production_plus_5"].exclusive_group == "production_plus"
    assert rules["production_plus_10"].potential_requires_prerequisite and rules["production_plus_5"].potential_requires_prerequisite
    r = resolve_program_rate("ny_state_film", production_type="feature_film", qpe_usd=2_000_000.0)
    assert r.modeled_rate == pytest.approx(0.30) and not r.is_band_ceiling, "no stacked whole-base 50%/60% ceiling remains"


def test_atl_limit_period_is_established_only_for_post_effective_costs():
    from app.calculators.ny_atl_individual_cap import period_applies
    assert period_applies(target_shoot_year=2026, lifecycle="PRODUCTION") is True
    assert period_applies(target_shoot_year=2023, lifecycle="EVALUATION") is None      # straddles April 1, 2023
    assert period_applies(target_shoot_year=2022, lifecycle="EVALUATION") is False
    assert period_applies(target_shoot_year=None, lifecycle="EVALUATION") is True      # prospective plan
    assert period_applies(target_shoot_year=None, lifecycle="COMPLETED") is None       # already incurred, date unknown


def test_payee_facts_map_only_identified_payees_with_complete_compensation():
    from types import SimpleNamespace as R
    from app.calculators.ny_atl_individual_cap import FACT_PAYEE_PREFIX, payee_amount_facts
    rows = [R(fact_key="line_fact:a:payee_id", value="P1"), R(fact_key="line_fact:a:payee_compensation_complete", value="true"),
            R(fact_key="line_fact:b:payee_id", value="P1"), R(fact_key="line_fact:b:payee_compensation_complete", value="true"),
            R(fact_key="line_fact:c:payee_id", value="P2"),                                              # complete not stated: Unknown
            R(fact_key="line_fact:d:payee_id", value="P3"), R(fact_key="line_fact:d:payee_compensation_complete", value="false"),
            R(fact_key="line_fact:zz:payee_id", value="P9"), R(fact_key="line_fact:zz:payee_compensation_complete", value="true")]  # not a budget line
    got = payee_amount_facts(rows, {"a", "b", "c", "d"})
    assert got == {FACT_PAYEE_PREFIX + "a": 1.0, FACT_PAYEE_PREFIX + "b": 1.0}


def _reg(amounts, payees=None):
    """Qualification register of NY ATL/other accounts run through the real derivation with the limits switched on."""
    lines = [BudgetLine(account_code=str(1000 + i), description=cat.upper(), amount_usd=amt, spend_category=cat, is_memo=False, line_id=f"L{i}")
             for i, (cat, amt) in enumerate(amounts)]
    facts = ProductionFacts(jurisdiction_code="US-NY", ny_atl_limits_apply=True, ny_atl_payee_by_line=tuple((payees or {}).items()))
    return derive_qualification_register(lines, program_slug=NY_FILM, facts=facts, rate=0.3,
                                         rules=get_program_rules(NY_FILM), doctrine=resolve_program_doctrine(NY_FILM).doctrine)


def _sum(reg, state, needle=""):
    return round(sum(a.amount_usd for a in reg if a.state == state and needle in a.reason), 2)


def test_group_limit_is_exactly_forty_percent_of_other_qualified_costs():
    reg = _reg([("atl_director", 600_000.0), ("atl_cast", 400_000.0), ("btl_crew_labor", 1_000_000.0)])
    assert _sum(reg, QualificationState.EXCLUDED, "forty percent") == 600_000.0          # ATL 1.0M vs limit 0.4 x 1.0M = 0.4M
    assert _sum(reg, QualificationState.QUALIFIES) == 1_400_000.0
    within = _reg([("atl_director", 400_000.0), ("btl_crew_labor", 1_000_000.0)])
    assert _sum(within, QualificationState.EXCLUDED, "forty percent") == 0.0              # exactly at the limit: untouched


def test_individual_cap_is_definitive_for_an_identified_payee_and_unresolved_otherwise():
    amounts = [("atl_director", 700_000.0), ("atl_cast", 900_000.0), ("btl_crew_labor", 9_000_000.0)]
    identified = _reg(amounts, payees={"L0": 1})
    assert _sum(identified, QualificationState.EXCLUDED, "per-individual cap") == 200_000.0
    unidentified = _reg(amounts)
    assert _sum(unidentified, QualificationState.EXCLUDED, "per-individual cap") == 0.0
    assert _sum(unidentified, QualificationState.QUALIFIES, "UNRESOLVED: the $500,000 per-individual cap") == 1_600_000.0
    # one individual across two accounts: the cap is on the person, so their accounts are summed
    shared = _reg([("atl_director", 400_000.0), ("atl_writer", 300_000.0), ("btl_crew_labor", 9_000_000.0)], payees={"L0": 1, "L1": 1})
    assert _sum(shared, QualificationState.EXCLUDED, "per-individual cap") == 200_000.0
    distinct = _reg([("atl_director", 400_000.0), ("atl_writer", 300_000.0), ("btl_crew_labor", 9_000_000.0)], payees={"L0": 1, "L1": 2})
    assert _sum(distinct, QualificationState.EXCLUDED, "per-individual cap") == 0.0


def test_limits_are_inert_unless_the_period_is_established_and_for_every_other_program():
    lines = [BudgetLine(account_code="1000", description="DIRECTOR", amount_usd=3_000_000.0, spend_category="atl_director", is_memo=False, line_id="L0"),
             BudgetLine(account_code="1001", description="CREW", amount_usd=1_000_000.0, spend_category="btl_crew_labor", is_memo=False, line_id="L1")]
    off = derive_qualification_register(lines, program_slug=NY_FILM, facts=ProductionFacts(jurisdiction_code="US-NY"), rate=0.3,
                                        rules=get_program_rules(NY_FILM), doctrine=resolve_program_doctrine(NY_FILM).doctrine)
    assert _sum(off, QualificationState.EXCLUDED) == 0.0
    ga = derive_qualification_register(lines, program_slug="us_ga_film_credit", facts=ProductionFacts(jurisdiction_code="US-GA", ny_atl_limits_apply=True), rate=0.3,
                                       rules=get_program_rules("us_ga_film_credit"), doctrine=resolve_program_doctrine("us_ga_film_credit").doctrine)
    assert not any("forty percent" in a.reason for a in ga)


def test_program_record_dates_the_cap_and_names_what_stays_unresolved():
    cap = get_program_requirements("ny_state_film").additional_facts["atl_per_individual_cap_guidance"]
    assert cap.startswith("DATED AGENCY RULE") and "20250418" in cap and "April 1, 2023" in cap and "2025-07-11" in cap
    assert "UNRESOLVED" in cap and "never capped or assumed" in cap
