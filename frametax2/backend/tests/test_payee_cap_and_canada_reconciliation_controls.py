"""F-10 (Georgia and Illinois per-individual limits, applied to identified payees only) and the Canadian authority reconciliation
(Alberta native minimum and 30% criteria, Manitoba deeming base, bonuses and the cost-of-production bonus). Register / rule cases are
DB-free and hand-computed; the Manitoba election case runs on rolled-back synthetic records."""
from __future__ import annotations

import pytest

from app.calculators.mb_nonresident_limit import apply_mb_nonresident_limit
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_rate_rules import get_subset_uplift_rules, resolve_program_rate
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.calculators.canonical_requirements_gate_bridge import evaluate_requirements_gate

Q, X = QualificationState.QUALIFIES, QualificationState.EXCLUDED
GA, IL = "us_ga_film_credit", "us_il_film_production_services_credit"
TYPE = {"employee": 1, "individual_contractor": 2, "loan_out_corp": 3}


def _reg(slug, rows, payees=None, types=None):
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="US", ny_atl_payee_by_line=tuple((payees or {}).items()), payee_type_by_line=tuple((types or {}).items()))
    return derive_qualification_register(lines, program_slug=slug, facts=pf, rate=0.2, rules=get_program_rules(slug), doctrine=resolve_program_doctrine(slug).doctrine)


def _sum(reg, state, needle="", line=None):
    return round(sum(a.amount_usd for a in reg if a.state == state and needle in a.reason and (line is None or a.line_id == line)), 2)


ROWS = (("atl_director", 700_000.0), ("btl_crew_labor", 3_000_000.0))


def test_georgia_cap_applies_to_an_identified_w2_payee_only():
    w2 = _reg(GA, ROWS, payees={"L0": 1}, types={"L0": TYPE["employee"]})
    assert _sum(w2, X, "per person, per production", line="L0") == 200_000.0 and _sum(w2, Q, line="L0") == 500_000.0
    loan_out = _reg(GA, ROWS, payees={"L0": 1}, types={"L0": TYPE["loan_out_corp"]})
    assert _sum(loan_out, X) == 0.0 and _sum(loan_out, Q, line="L0") == 700_000.0, "no salary cap for 1099, personal services contract or loan-out"
    assert "UNRESOLVED" not in " ".join(a.reason for a in loan_out if a.line_id == "L0"), "a stated uncapped type settles the question"


def test_georgia_unstated_type_or_unidentified_payee_is_never_capped_and_says_so():
    for payees, types in (({"L0": 1}, {}), ({}, {})):
        reg = _reg(GA, ROWS, payees=payees, types=types)
        assert _sum(reg, X) == 0.0 and _sum(reg, Q, "UNRESOLVED", line="L0") == 700_000.0
    small = _reg(GA, (("atl_director", 700_000.0), ("btl_crew_labor", 400_000.0)))
    assert _sum(small, Q, "UNRESOLVED", line="L1") == 0.0, "an account under the cap carries no note"


def test_one_individual_across_accounts_is_capped_once_in_georgia():
    reg = _reg(GA, (("atl_director", 400_000.0), ("atl_writer", 300_000.0), ("btl_crew_labor", 3_000_000.0)),
               payees={"L0": 1, "L1": 1}, types={"L0": TYPE["employee"], "L1": TYPE["employee"]})
    assert _sum(reg, X, "per person") == 200_000.0


def test_illinois_cap_applies_to_every_identified_worker_and_unidentified_stays_visible():
    reg = _reg(IL, ROWS, payees={"L0": 1})
    assert _sum(reg, X, "per worker", line="L0") == 200_000.0 and _sum(reg, Q, line="L0") == 500_000.0
    bare = _reg(IL, ROWS)
    assert _sum(bare, X) == 0.0 and _sum(bare, Q, "UNRESOLVED", line="L0") == 700_000.0


def test_other_programs_are_untouched_by_the_payee_caps():
    assert _sum(_reg("us_nm_film_credit", ROWS, payees={"L0": 1}), X, "per ") == 0.0


# ── Alberta ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_alberta_minimum_total_production_cost_is_a_native_cad_gate():
    below = evaluate_requirements_gate("ca_ab_fttc", segment_allocated_usd=300_000.0, gross_budget_usd=300_000.0)
    assert below.blocks_deterministic_pricing and any(e.requirement == "min_total_budget_native" and e.state == "FAILED" for e in below.evaluations)
    ok = evaluate_requirements_gate("ca_ab_fttc", segment_allocated_usd=900_000.0, gross_budget_usd=900_000.0)
    assert not ok.blocks_deterministic_pricing and any(e.requirement == "min_total_budget_native" and e.state == "SATISFIED" for e in ok.evaluations)
    unknown = evaluate_requirements_gate("ca_ab_fttc", segment_allocated_usd=None, gross_budget_usd=None)
    assert any(e.requirement == "min_total_budget_native" and e.state == "UNKNOWN" for e in unknown.evaluations)


def test_alberta_30_percent_is_a_stated_criteria_tier_over_a_guaranteed_22():
    unknown = resolve_program_rate("ca_ab_fttc", production_type="feature_film", qpe_usd=2_000_000.0)
    assert unknown.floor_rate == pytest.approx(0.22) and unknown.modeled_rate == pytest.approx(0.30) and unknown.is_band_ceiling
    stated = resolve_program_rate("ca_ab_fttc", production_type="feature_film", qpe_usd=2_000_000.0, evidenced_facts=frozenset({"ab_fttc_30pct_criteria_met"}))
    assert stated.floor_rate == pytest.approx(0.30) and not stated.is_band_ceiling and stated.has_guaranteed_floor


# ── Manitoba ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _mb(rows, evidenced=frozenset()):
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="CA-MB", evidenced_facts=frozenset(evidenced))
    return derive_qualification_register(lines, program_slug="ca_mb_film_video_credit", facts=pf, rate=0.45, rules=get_program_rules("ca_mb_film_video_credit"),
                                         doctrine=resolve_program_doctrine("ca_mb_film_video_credit").doctrine)


def test_manitoba_deeming_cap_is_measured_against_all_eligible_manitoba_salaries_including_above_the_line():
    # eligible Manitoba salaries: cast 700,000 + crew 300,000 = 1,000,000 ; non-resident technical 400,000 ; limits 100,000 (10%) / 300,000 (30%)
    reg = _mb((("atl_cast", 700_000.0), ("btl_crew_labor", 300_000.0), ("btl_nonresident_labor", 400_000.0)))
    assert _sum(reg, Q, line="L2") == 100_000.0 and _sum(reg, X, line="L2") == 100_000.0
    assert _sum(reg, QualificationState.GREY_AREA_REQUIRES_AUTHORITY, line="L2") == 200_000.0


def test_manitoba_bonus_rules_carry_the_primary_conditions():
    rules = {r.uplift_id: r for r in get_subset_uplift_rules("ca_mb_film_video_credit")}
    assert rules["rural_northern"].prerequisite_fact == "mb_rural_permanent_establishment_35km" and rules["rural_northern"].whole_base_fact == "mb_rural_majority_days_35km"
    assert rules["frequent_filming"].prerequisite_fact == "mb_frequent_filming_principal_owner_declared" and rules["frequent_filming"].whole_base_fact == "mb_frequent_filming_third_film_in_two_years"
    assert rules["manitoba_producer"].whole_base_fact == "mb_resident_producer_screen_credit" and rules["manitoba_producer"].prerequisite_fact is None


@pytest.mark.asyncio
async def test_manitoba_cost_of_production_bonus_is_a_bound_until_the_co_production_is_stated():
    from app.services.canonical_evaluation import evaluate_project
    from app.services.ny_producer_facts import write_ny_program_facts
    from tests.isolated_records import create_synthetic_project, isolated_session, served_structures
    lines = (("3000", "CREW", "btl_crew_labor", "btl", 400_000.0), ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 1_600_000.0))
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=lines, home_code="CA-MB")
        await evaluate_project(db, pid)
        e = next(x for x in await served_structures(db, pid) if x["program_slugs"] == ["ca_mb_film_video_credit"] and x["structure_type"] == "single_country" and x["candidate_status"] == "PRICED")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(0.30 * 2_000_000) and e["maximum_supported_incentive_usd"] == pytest.approx(0.38 * 2_000_000)
        assert e["ceiling_requires_confirmation"] is True
        await write_ny_program_facts(db, pid, evidenced={"mb_production_company_bonus_eligible": True})
        await evaluate_project(db, pid)
        e = next(x for x in await served_structures(db, pid) if x["program_slugs"] == ["ca_mb_film_video_credit"] and x["structure_type"] == "single_country" and x["candidate_status"] == "PRICED")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(0.38 * 2_000_000)
