"""NY production/post pairing under Tax Law 31(a)(1), and production vs post upstate ATL bases.

Sources (fetched 2026-10-11): Tax Law 31 (nysenate.gov, revision displayed 2025-07-11): 31(a)(1) allows the post credit to a qualified film
production company 'unless eligible for the credit under section twenty-four'; 31(a)(4) is the separate same-cost bar; 31(a)(6) upstate +10% on
post wages EXCLUDES writers, directors, composers, producers and performers. Tax Law 24 (same revision): 40% ATL group limit, at most two
producers, upstate +10% on wages in listed counties (budget over $500,000), no per-person dollar cap in the displayed text. ESD Program Guidelines
(May 2023) p.2: ATL salaries 'subject to a $500,000 cap per individual and limited to 40% of all other qualified production costs'; p.3: the post
credit is available if the project was filmed predominantly outside NY or was ineligible for the production credit.

SYNTHETIC ONLY: generator controls are DB-free; the evaluation control runs on a rolled-back synthetic NY project on the isolated test database."""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.calculators.structural_archetype_generator import generate_structural_candidate
from app.data.program_requirements import get_program_requirements
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.optimization import stacking_rules
from app.services import canonical_evaluation as ce
from tests.isolated_records import create_synthetic_project, isolated_session
from tests.test_structural_archetype_generator import _comp

NY_FILM, NY_POST = "ny_state_film", "us_ny_post_production_credit"


def test_the_pair_is_mutually_exclusive_on_the_film_level_condition_not_on_cost_pools():
    rule = stacking_rules._SLUG_PAIR_RULES[frozenset({NY_FILM, NY_POST})]
    assert rule["rule_type"] == "mutually_exclusive"
    text = rule["condition_text"]
    assert "31(a)(1)" in text and "unless eligible for the credit under section twenty-four" in text
    assert "31(a)(4)" in text and "disjoint" in text
    assert tuple(int(n) for n in stacking_rules.STACKING_RULES_VERSION.split(".")) >= (1, 5, 0)


def test_disjoint_cost_pools_do_not_make_the_production_and_post_credits_composable():
    principal = _comp(NY_FILM, "US-NY", 3_000_000.0, line_id="NY-PRINCIPAL", component_type="principal_production")
    post = _comp(NY_POST, "US-NY", 1_500_000.0, line_id="NY-POST", component_type="post")
    assert not (principal.line_ids & post.line_ids)                       # genuinely distinct pools
    res = generate_structural_candidate([principal, post], gross_budget_usd=4_500_000.0)
    assert res.executable is False
    assert res.blocking_pairs and res.blocking_pairs[0].disposition == "mutually_exclusive"


def test_the_post_credit_still_prices_for_a_post_only_film_and_the_production_credit_still_prices_alone():
    post_only = generate_structural_candidate(
        [_comp(NY_POST, "US-NY", 1_500_000.0, line_id="NY-POST-ONLY", component_type="principal_production", spend_category="post_production")],
        gross_budget_usd=1_500_000.0)
    assert post_only.executable is True, post_only.rejection_reason
    production_only = generate_structural_candidate(
        [_comp(NY_FILM, "US-NY", 3_000_000.0, line_id="NY-PROD-ONLY", component_type="principal_production")], gross_budget_usd=3_000_000.0)
    assert production_only.executable is True, production_only.rejection_reason


def test_a_post_only_routing_to_ny_remains_composable_with_a_production_credit_elsewhere():
    principal = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="GA-PRINCIPAL", component_type="principal_production")
    post = _comp(NY_POST, "US-NY", 1_500_000.0, line_id="NY-POST-ELSEWHERE", component_type="post")
    res = generate_structural_candidate([principal, post], gross_budget_usd=4_500_000.0)
    assert res.executable is True, res.rejection_reason


async def test_evaluating_a_synthetic_ny_film_no_longer_prices_the_production_plus_post_stack():
    from sqlalchemy import select

    from app.models.production import ProductionStructure, StructureCalculationResult as R

    lines = (("2000", "ATL DIRECTOR FEE (NY principal)", "atl_director", "atl", 3_000_000.0),
             ("8000", "POST PRODUCTION (NY post)", "post_production", "post", 1_500_000.0))
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=lines, home_code="US-NY")
        await ce.evaluate_project(db, pid)
        traces = (await db.execute(
            select(R.calculation_trace_json).join(ProductionStructure, ProductionStructure.id == R.structure_id)
            .where(ProductionStructure.project_id == pid))).scalars().all()
    both = [t for t in traces if {NY_FILM, NY_POST} <= set(t.get("program_slugs") or [])]
    assert both, "the combination must still be enumerated (and rejected), never silently dropped"
    assert all(t.get("candidate_status") != "PRICED" for t in both)
    assert not any(t.get("structural_family") == "same_jurisdiction_distinct_cost_pool_stack" and t.get("candidate_status") == "PRICED" for t in traces)
    assert any(t.get("candidate_status") == "PRICED" and NY_FILM in (t.get("program_slugs") or []) for t in traces), "the production credit still prices alone"


# ── production vs post upstate / ATL eligibility ───────────────────────────────────────────────────────────────────────────

ATL_ROLES = ("atl_writer", "atl_director", "atl_producer", "atl_cast")


def _register(program, jurisdiction="US-NY"):
    lines = [BudgetLine(account_code=str(1000 + i), description=cat.upper(), amount_usd=100_000.0, spend_category=cat, is_memo=False, line_id=f"L{i}")
             for i, cat in enumerate(ATL_ROLES + ("post_production",))]
    return {a.line_id: a for a in derive_qualification_register(
        lines, program_slug=program, facts=ProductionFacts(jurisdiction_code=jurisdiction), rate=0.3,
        rules=get_program_rules(program), doctrine=resolve_program_doctrine(program).doctrine)}


def test_production_qualifies_above_the_line_labor_while_the_post_credit_excludes_it():
    production, post = _register(NY_FILM), _register(NY_POST)
    for i, _role in enumerate(ATL_ROLES):
        assert production[f"L{i}"].state == QualificationState.QUALIFIES, "production-credit labor base includes qualifying ATL (Tax Law 24)"
        assert post[f"L{i}"].state == QualificationState.EXCLUDED, "the post credit's closed base excludes ATL roles (Tax Law 31(a)(6))"
    assert post["L4"].state == QualificationState.QUALIFIES


def test_the_two_upstate_bases_are_recorded_separately_and_the_500k_guidance_is_dated_and_applies_to_identified_payees_only():
    film = get_program_requirements(NY_FILM).additional_facts
    post = get_program_requirements(NY_POST).additional_facts
    assert "INCLUDES qualifying above-the-line salaries" in film["upstate_uplift"] and "24(a)(5)" in film["upstate_uplift"]
    assert "more than 50%" in film["upstate_uplift"]                                    # shooting-day prerequisite preserved
    assert "EXCLUDES writers, directors, composers, producers and performers" in post["upstate_uplift"] and "31(a)(6)" in post["upstate_uplift"]
    cap = film["atl_per_individual_cap_guidance"]
    assert cap.startswith("DATED AGENCY RULE") and "$500,000 cap per individual" in cap and "2025-07-11" in cap and "UNRESOLVED" in cap
    assert get_program_requirements(NY_FILM).atl_cap_pct_of_other_costs == 0.40


def test_no_per_person_cap_is_applied_to_an_aggregate_atl_account_without_a_payee_split():
    big = [BudgetLine(account_code="1100", description="DIRECTOR", amount_usd=750_000.0, spend_category="atl_director", is_memo=False, line_id="D")]
    register = derive_qualification_register(
        big, program_slug=NY_FILM, facts=ProductionFacts(jurisdiction_code="US-NY"), rate=0.3,
        rules=get_program_rules(NY_FILM), doctrine=resolve_program_doctrine(NY_FILM).doctrine)
    assert [(a.state, a.amount_usd) for a in register] == [(QualificationState.QUALIFIES, 750_000.0)]   # the full account, no $500,000 trim
