"""Manitoba: the non-resident salary limit (register, DB-free) and the producer-elected cost-of-production alternative (rolled-back synthetic
evaluations). Hand-computed from Manitoba Film & Music / Manitoba Finance: cost-of-salaries 45% of eligible labour; non-resident salary
<= 30% (two or more residents trained per non-resident) or 10% (one) of eligible resident salaries; alternative 30% of all eligible
Manitoba production expenditures. The corporation claims one credit."""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.services.canonical_evaluation import evaluate_project
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

MB = "ca_mb_film_video_credit"
Q, X, G = QualificationState.QUALIFIES, QualificationState.EXCLUDED, QualificationState.GREY_AREA_REQUIRES_AUTHORITY


def _reg(evidenced=frozenset(), scenario_local_btl=False, rows=(("btl_resident_labor", 1_000_000.0), ("btl_nonresident_labor", 400_000.0))):
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="CA-MB", evidenced_facts=frozenset(evidenced), scenario_local_btl=scenario_local_btl)
    return derive_qualification_register(lines, program_slug=MB, facts=pf, rate=0.45, rules=get_program_rules(MB), doctrine=resolve_program_doctrine(MB).doctrine)


def _sum(reg, state, line="L1"):
    return round(sum(a.amount_usd for a in reg if a.state == state and a.line_id == line), 2)


def test_nonresident_salary_limit_by_training_ratio():
    # resident 1,000,000 -> limits 100,000 (10%) and 300,000 (30%) on 400,000 of non-resident salary
    unknown = _reg()
    assert (_sum(unknown, Q), _sum(unknown, G), _sum(unknown, X)) == (100_000.0, 200_000.0, 100_000.0)      # only 10% counted; 10-30% is a producer-fact question
    two = _reg({"mb_two_residents_trained_per_nonresident"})
    assert (_sum(two, Q), _sum(two, G), _sum(two, X)) == (300_000.0, 0.0, 100_000.0)
    one = _reg({"mb_one_resident_trained_per_nonresident"})
    assert (_sum(one, Q), _sum(one, G), _sum(one, X)) == (100_000.0, 0.0, 300_000.0)


def test_nonresident_limit_is_inert_without_nonresident_accounts_for_local_hire_scenarios_and_within_the_limit():
    assert _sum(_reg(rows=(("btl_resident_labor", 1_000_000.0), ("btl_crew_labor", 400_000.0))), X, "L1") == 0.0
    assert _sum(_reg(scenario_local_btl=True), X) == 0.0 and _sum(_reg(scenario_local_btl=True), Q) == 400_000.0   # relocated BTL is hired locally
    within = _reg(rows=(("btl_resident_labor", 1_000_000.0), ("btl_nonresident_labor", 90_000.0)))
    assert (_sum(within, Q), _sum(within, G), _sum(within, X)) == (90_000.0, 0.0, 0.0)


@pytest.mark.asyncio
async def test_the_higher_of_the_two_elective_credits_is_the_planning_figure_and_the_other_is_disclosed():
    cases = (  # (crew labour, equipment) -> labour credit 45% x labour vs alternative 30% x all spend
        (400_000.0, 1_600_000.0, 600_000.0, "cost-of-production credit"),      # 180,000 vs 600,000 -> alternative
        (1_800_000.0, 200_000.0, 810_000.0, "is the alternative elective credit"),   # 810,000 vs 600,000 -> labour credit
    )
    for crew, equipment, expected_floor, note_fragment in cases:
        async with isolated_session() as db:
            pid = await create_synthetic_project(db, lines=(("3000", "CREW", "btl_crew_labor", "btl", crew), ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", equipment)), home_code="CA-MB")
            await evaluate_project(db, pid)
            hits = [e for e in await served_structures(db, pid) if e["program_slugs"] == [MB] and e["structure_type"] == "single_country" and e["candidate_status"] == "PRICED"]
            assert hits, "Manitoba home candidate must price"
            e = hits[0]
            assert e["confirmed_incentive_floor_usd"] == pytest.approx(expected_floor)
            assert any(note_fragment in n for n in (e.get("notes") or [])) or any(note_fragment in str(x) for x in e.get("segments", [{}])[0].get("notes", [])), e.get("notes")
