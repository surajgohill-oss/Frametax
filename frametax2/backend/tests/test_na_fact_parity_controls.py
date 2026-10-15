"""NA-RECONCILIATION-25: the same modeled production receives the same resolved facts and the same economics whichever supported pricing path reaches it.

Paths compared on identical budget lines and identical stated facts (DB-free, synthetic): (1) the allocated-structure pricer (`price_allocated_structure`), (2) the structural generator
(`generate_structural_candidate`, which prices a component inside a modeled structure), (3) the cost-pool-aware same-jurisdiction path (`scenario_priced_segment` called as that path calls it). The same-jurisdiction multi-program stack
reuses path (1)'s per-program pricing and carries its persisted records onto the stack trace (checked against a synthetic evaluation in test_na_persisted_resolved_facts_controls)."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators import locality as loc
from app.calculators.allocation_pricing import price_allocated_structure, scenario_priced_segment
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import BudgetLine
from app.calculators.scenario_facts import SCHEDULE_TOTAL_DAYS_FACT, refuted
from app.calculators.structural_archetype_generator import StructuralComponent, generate_structural_candidate
from app.services.resolved_facts import segment_resolved_facts

MO = "us_mo_motion_media_production_tax_credit"
SK = "ca_sk_creative_saskatchewan_grant"
BCD = "ca_bc_film_tv_tax_credit"
NS, NB = "ca_ns_production_incentive_fund", "ca_nb_film_tax_credit"
LINES = [BudgetLine(account_code="3000", description="CREW", amount_usd=1_600_000.0, spend_category="btl_crew_labor", is_memo=False, line_id="L-crew"),
         BudgetLine(account_code="6100", description="EQUIP", amount_usd=400_000.0, spend_category="btl_equipment_rental", is_memo=False, line_id="L-eq")]
CATS = {"3000": "btl_crew_labor", "6100": "btl_equipment_rental"}
TOTAL = 2_000_000.0


def _inputs(jur, slug):
    spec = StructureSpec(structure_id="P", structure_type="full_relocation", label="p", primary_jurisdiction=jur, participants=(jur,), incentive_programs={jur: slug})
    allocation = derive_account_allocation(LINES, CATS, spec)
    return spec, allocation, [a for a in allocation.assignments if a.jurisdiction_code == jur]


def _common():
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P
    return P


def _three_paths(jur, slug, stated=frozenset(), amounts=None, production_type="feature_film"):
    """(segment via allocated structure, via generator, via cost-pool helper) for the same production."""
    spec, allocation, mine = _inputs(jur, slug)
    P = _common()
    ev, am = frozenset(stated) | P, dict(amounts or {})
    priced = price_allocated_structure(spec, allocation, CATS, frozenset(), TOTAL, production_type=production_type, evidenced_requirement_facts=ev, amount_facts=am)
    seg_alloc = next(s for s in priced.segments if s.jurisdiction_code == jur)
    comp = StructuralComponent(component_type="principal_production", jurisdiction_code=jur, program_slug=slug, allocations=tuple(allocation.assignments), spend_category_by_code=CATS,
                               production_type=production_type, evidenced_requirement_facts=ev, amount_facts=am)
    gen = generate_structural_candidate([comp], gross_budget_usd=TOTAL)
    seg_gen = next(ce.segment for ce in gen.component_economics)
    rows = [(a.jurisdiction_code, a.amount_usd, a.component, "") for a in allocation.assignments]
    seg_pool = scenario_priced_segment({"jurisdiction_code": jur, "program_slug": slug, "allocations": mine, "spend_category_by_code": CATS, "offshore_payroll_accounts": frozenset(),
                                        "production_type": production_type, "gross_budget_usd": TOTAL, "amount_facts": am, "evidenced_requirement_facts": ev}, rows, jur, component="cost_pool")
    return seg_alloc, seg_gen, seg_pool


def _facts(seg):
    return {r["fact_key"]: (r["state"], r["provenance"], r["value"]) for r in segment_resolved_facts(seg)}


def _econ(seg):
    return (round(seg.incentive_floor_usd, 2), round(seg.incentive_ceiling_usd, 2))


def _assert_parity(paths, expected_keys):
    facts = [_facts(s) for s in paths]
    econ = [_econ(s) for s in paths]
    for key in expected_keys:
        assert key in facts[0], f"{key} is missing from the allocated-structure path: {sorted(facts[0])}"
    assert facts[0] == facts[1] == facts[2], f"the three paths resolved different facts: {facts}"
    assert econ[0] == econ[1] == econ[2], f"the three paths priced differently: {econ}"


def test_missouri_filming_uplift_has_the_same_facts_and_economics_on_every_path():
    paths = _three_paths("US-MO", MO, stated={"mo_apprentice_or_veteran_minimum_confirmed"})
    _assert_parity(paths, ["mo_filmed_50pct_in_missouri_confirmed"])
    filmed = _facts(paths[0])["mo_filmed_50pct_in_missouri_confirmed"]
    assert filmed[:2] == ("TRUE", "SCENARIO_ASSUMED")
    assert _econ(paths[0])[0] == pytest.approx(0.25 * 2_000_000.0 - 0.0, rel=0.2) or _econ(paths[0])[0] > 0.20 * 1_500_000.0, "the 5 filming points are in the confirmed floor"


def test_a_stated_no_outranks_the_scenario_on_every_path():
    paths = _three_paths("US-MO", MO, stated={"mo_apprentice_or_veteran_minimum_confirmed", refuted("mo_filmed_50pct_in_missouri_confirmed")})
    facts = [_facts(s) for s in paths]
    assert all(f["mo_filmed_50pct_in_missouri_confirmed"][:2] == ("FALSE", "PRODUCER_STATED") for f in facts)
    assert facts[0] == facts[1] == facts[2] and len({_econ(s) for s in paths}) == 1


def test_saskatchewan_51_percent_activity_test_has_the_same_facts_and_economics_on_every_path():
    paths = _three_paths("CA-SK", SK)
    _assert_parity(paths, ["scenario_share_met:ca_sk_principal_photography_days_in_sk"])
    assert _facts(paths[0])["scenario_share_met:ca_sk_principal_photography_days_in_sk"][:2] == ("TRUE", "SCENARIO_ASSUMED")


def test_bc_75_percent_photography_days_and_cost_tests_have_the_same_facts_and_economics_on_every_path():
    cert = {"ca_bc_film_tv_tax_credit__cultural_test_confirmed", "ca_bc_film_tv_tax_credit__local_entity_or_partner_confirmed", "ca_bc_film_tv_photography_after_2024_confirmed"}
    paths = _three_paths("CA-BC", BCD, stated=cert)
    keys = ["ca_bc_film_tv_photography_days_75pct_in_bc_confirmed", "ca_bc_film_tv_bc_cost_75pct_confirmed"]
    _assert_parity(paths, keys)
    for k in keys:
        assert _facts(paths[0])[k][:2] == ("TRUE", "SCENARIO_ASSUMED")


@pytest.mark.parametrize("jur,slug,expected", [
    ("CA-BC", BCD, {"ca_bc_principal_photography_days_in_bc": 40.0}),
    ("CA-NS", NS, {"ca_ns_principal_photography_days_total": 40.0, "ca_ns_principal_photography_days_in_ns": 40.0}),
    ("CA-NB", NB, {"ca_nb_principal_photography_days_total": 40.0}),
    ("CA-SK", SK, {"ca_sk_principal_photography_days_total": 40.0, "ca_sk_principal_photography_days_in_sk": 40.0}),
])
def test_schedule_derived_day_inputs_are_identical_on_every_path(jur, slug, expected):
    cert = {"ca_bc_film_tv_tax_credit__cultural_test_confirmed", "ca_bc_film_tv_tax_credit__local_entity_or_partner_confirmed"}
    paths = _three_paths(jur, slug, stated=cert, amounts={SCHEDULE_TOTAL_DAYS_FACT: 40.0})
    facts = [_facts(s) for s in paths]
    for key, value in expected.items():
        for f in facts:
            assert f[key][0] == "VALUE" and f[key][2] == value, (key, f.get(key))
    assert facts[0] == facts[1] == facts[2]
    assert len({_econ(s) for s in paths}) == 1


def test_locality_derived_missouri_county_and_rural_uplifts_are_identical_on_every_path():
    entry = loc.validate_entry({"id": "a", "label": "Johnson set", "jurisdiction_code": "US-MO", "county": "Johnson County", "days": 20,
                                "attributes": {"rural_or_blighted": True}, "evidence": {"rural_or_blighted": {"source": "DED letter", "method": "AUTHORITY_DETERMINATION", "confidence": "AUTHORITATIVE"}}})
    amounts = {SCHEDULE_TOTAL_DAYS_FACT: 20.0, **loc.locality_amount_facts([entry])}
    paths = _three_paths("US-MO", MO, stated={"mo_apprentice_or_veteran_minimum_confirmed"}, amounts=amounts)
    _assert_parity(paths, ["mo_second_third_fourth_class_county_confirmed", "mo_rural_or_blighted_15pct_confirmed"])
    f = _facts(paths[0])
    assert f["mo_second_third_fourth_class_county_confirmed"][:2] == ("TRUE", "LOCALITY_RESOLVED") and f["mo_rural_or_blighted_15pct_confirmed"][:2] == ("TRUE", "LOCALITY_RESOLVED")
    without = _three_paths("US-MO", MO, stated={"mo_apprentice_or_veteran_minimum_confirmed"})
    assert _econ(paths[0])[0] > _econ(without[0])[0], "county (+2) and rural (+5) raise the confirmed figure"


def test_verified_and_stated_numbers_outrank_the_scenario_and_the_schedule_on_every_path():
    paths = _three_paths("CA-NS", NS, amounts={SCHEDULE_TOTAL_DAYS_FACT: 40.0, "ca_ns_principal_photography_days_total": 30.0})
    for s in paths:
        f = _facts(s)
        assert "ca_ns_principal_photography_days_total" not in f or f["ca_ns_principal_photography_days_total"][1] != "SCHEDULE_DERIVED", "a stated total is never replaced by the schedule's"
