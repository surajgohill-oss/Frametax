"""NA-RECONCILIATION-10 (2026-10-13): the BH CPTC delta of USD 20,380.35 reconciled from the retained raw lines, and the producer's contingency election reaching the CPTC cost cap.

Primary authority: CRA RC4164 (Form T1131 guide) Part 5 line 421 'the total amount of expenditures that is included in the qualified corporation's cost of production ... using generally accepted
accounting principles' (a deferred amount that is a contingent liability is excluded until it becomes an enforceable liability), line 423 assistance, amount A = 421 - 423, amount B = 60% x A, and
Part 6 amount F = the lesser of line 430 and the labour line 618; credit = F x 25%. An unspent contingency reserve is not an expenditure, so it is not in line 421.

Retained raw lines: docs/validation/CODEX_FINAL_AG_ADJUDICATION_LINES.csv (project 'Bad Hombres', 34 lines, amount_usd verified from the original budget PDF): gross 2,482,023.00 including the CONTINGENCY
line 94,382.00 and the 1600 SAG DEPOSIT / RESIDUAL RESERVE line 60,000.00. Codex's replay of the engine (CODEX_NA_PACKAGE_ADJUDICATION_20261011.md, item 3): credit 369,526.50, i.e. a labour basis of 1,478,106.00
(accounts 1100, 1200, 1300, 1400 and 3000), cap 60% x 2,482,023 = 1,489,213.80 not binding."""
from __future__ import annotations

import csv
import uuid
from pathlib import Path

import pytest

from app.calculators.canonical_stack_bridge import cptc_net_cost_adjusted
from app.models.enums import ProjectFactSourceType
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from tests.isolated_records import add_synthetic_people, create_synthetic_project, isolated_session, served_structures

_LINES = Path(__file__).resolve().parents[2] / "docs" / "validation" / "CODEX_FINAL_AG_ADJUDICATION_LINES.csv"


def _bh():
    return [r for r in csv.DictReader(open(_LINES, encoding="utf-8")) if r["project"] == "Bad Hombres"]


def test_the_retained_bh_lines_carry_the_two_items_in_dispute():
    rows = _bh()
    amounts = {r["account"]: float(r["amount_usd"]) for r in rows}
    assert round(sum(amounts.values()), 2) == 2_482_023.00
    assert amounts["CONTINGENCY"] == 94_382.00 and amounts["1600"] == 60_000.00
    labour = sum(amounts[a] for a in ("1100", "1200", "1300", "1400", "3000"))
    assert labour == 1_478_106.00, "the labour basis that reproduces the engine's USD 369,526.50 CPTC"


@pytest.mark.parametrize("excluded,expected_credit,expected_delta", [
    (0.0, 369_526.50, 0.0),                       # contingency and reserve presumed spent: cap 60% x 2,482,023 = 1,489,213.80 exceeds the labour 1,478,106
    (94_382.0, 358_146.15, 11_380.35),            # contingency unspent: cost 2,387,641, cap 1,432,584.60, credit 25% x 1,432,584.60
    (154_382.0, 349_146.15, 20_380.35),           # contingency unspent and the 60,000 reserve not a cost: cost 2,327,641, cap 1,396,584.60
])
def test_the_ag_delta_is_exactly_the_effect_of_taking_both_items_out_of_line_421(excluded, expected_credit, expected_delta):
    credit, cap, qualified = cptc_net_cost_adjusted(369_526.50, 0.25, 1_478_106.0, 2_482_023.0 - excluded, 0.0, 0.0)
    assert credit == pytest.approx(expected_credit, abs=0.005)
    assert 369_526.50 - credit == pytest.approx(expected_delta, abs=0.005)
    assert qualified == pytest.approx(min(1_478_106.0, 0.60 * (2_482_023.0 - excluded)), abs=0.005)


def test_adjudication_of_each_item_against_the_primary_text():
    """Contingency (94,382): SUPPORTED when the producer states it will not be spent - RC4164 line 421 is the GAAP cost of production, an unspent reserve is not an expenditure; wired below.
    SAG deposit / residual reserve (60,000): NOT ESTABLISHED - the guide names neither residuals nor union deposits; a residual obligation payable only on future distribution revenue is a contingent
    liability (excluded), a deposit actually paid is an expenditure. Which one this account is cannot be told from the topsheet, so the delta of 20,380.35 is the UPPER bound and 11,380.35 the
    part the primary text supports once the producer states the contingency election."""
    supported = 369_526.50 - cptc_net_cost_adjusted(369_526.50, 0.25, 1_478_106.0, 2_482_023.0 - 94_382.0, 0.0, 0.0)[0]
    upper = 369_526.50 - cptc_net_cost_adjusted(369_526.50, 0.25, 1_478_106.0, 2_482_023.0 - 154_382.0, 0.0, 0.0)[0]
    assert round(supported, 2) == 11_380.35 and round(upper, 2) == 20_380.35
    assert round(upper - supported, 2) == round(0.25 * 0.60 * 60_000.0, 2) == 9_000.00


pytestmark_async = pytest.mark.asyncio

_LINES_PROJECT = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
                  ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("9000", "CONTINGENCY", "contingency", "other", 500_000.0))


async def _cptc_in_ofttc_stack(utilization_pct):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=_LINES_PROJECT, home_code="CA-ON")
        await add_synthetic_people(db, pid, [("director", "Dir One", "CA", True), ("writer", "Wri One", "CA", True)])
        db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="amount_fact:ca_federal_cptc_qualified_labour_usd", value="1500000",
                           source_type=ProjectFactSourceType.USER_OVERRIDE))
        if utilization_pct is not None:
            db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="contingency_expected_utilization_pct", value=str(utilization_pct),
                               source_type=ProjectFactSourceType.USER_OVERRIDE))
        await db.commit()
        await evaluate_project(db, pid)
        entries = await served_structures(db, pid)
        stack = next(e for e in entries if e["structure_type"] == "multi_program" and sorted(e["program_slugs"]) == ["ca_federal_cptc", "on_ofttc"])
        return stack["per_program_adjusted_usd"]["ca_federal_cptc"]


@pytest.mark.asyncio
async def test_a_stated_zero_contingency_utilization_lowers_the_cptc_cost_cap_and_unstated_does_not():
    # gross 3,000,000; OFTTC 35% x 1,900,000 = 665,000. Unstated: the reserve stays in the cost, cap 60% x (3,000,000 - 665,000) = 1,401,000 < 1,500,000 labour -> CPTC 350,250.
    # Stated 0% used: the 500,000 reserve is not spent, cost 2,500,000, cap 60% x (2,500,000 - 665,000) = 1,101,000 -> CPTC 275,250. Difference 25% x 60% x 500,000 = 75,000.
    unstated = await _cptc_in_ofttc_stack(None)
    zero = await _cptc_in_ofttc_stack(0)
    assert unstated == pytest.approx(0.25 * 0.60 * (3_000_000 - 665_000))
    assert zero == pytest.approx(0.25 * 0.60 * (2_500_000 - 665_000))
    assert round(unstated - zero, 2) == 75_000.00


_STACK_LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
                ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("4000", "VFX", "vfx", "post", 300_000.0))
_CPTC_FACTS = ("ca_cptc_cavco_certified", "ca_cptc_canadian_controlled_applicant")


async def _cptc_entries(facts):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=_STACK_LINES, home_code="CA-ON")
        await add_synthetic_people(db, pid, [("director", "Dir One", "CA", True), ("writer", "Wri One", "CA", True)])
        db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="amount_fact:ca_federal_cptc_qualified_labour_usd", value="1500000",
                           source_type=ProjectFactSourceType.USER_OVERRIDE))
        for f in facts:
            db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="evidenced_program_fact:" + f, value="true", source_type=ProjectFactSourceType.USER_OVERRIDE))
        await db.commit()
        await evaluate_project(db, pid)
        entries = await served_structures(db, pid)
        alone = next(e for e in entries if e["program_slugs"] == ["ca_federal_cptc"] and e["candidate_status"] == "PRICED")
        stack = next(e for e in entries if e["structure_type"] == "multi_program" and sorted(e["program_slugs"]) == ["ca_federal_cptc", "ca_mb_film_video_credit"]
                     and e["candidate_status"] == "PRICED")
        return alone, stack


@pytest.mark.asyncio
async def test_missing_cptc_producer_facts_reach_economics_certainty_and_qualification_in_the_single_program_and_the_stack():
    alone, stack = await _cptc_entries(())
    for entry in (alone, stack):
        assert entry["economics_certainty"] == "CONDITIONAL"
        assert entry["role_qualification"]["state"] == "USER_FACT_REQUIRED"
    assert {"ca-cptc-content-certification-required", "ca-cptc-canadian-controlled-corporation"} <= {m["fact_id"] for m in alone["claim_base_missing_facts"]}
    assert "ca-cptc-content-certification-required" in {m["fact_id"] for m in stack["claim_base_missing_facts"]}
    a2, s2 = await _cptc_entries(_CPTC_FACTS)
    for entry in (a2, s2):
        assert entry["economics_certainty"] == "CONFIRMED" and not entry["claim_base_missing_facts"]
    # The CPTC stays at USER_FACT_REQUIRED after the two applicant facts for a different, genuine reason: the CAVCO points test still lacks the Canadian producer and lead cast
    # on file. The cleared conditions are no longer among what it is waiting for.
    waiting = " ".join(a2["role_qualification"].get("missing_facts") or [])
    assert "Canadian producer" in waiting and "lead_cast" in waiting
    assert a2["confirmed_incentive_floor_usd"] == alone["confirmed_incentive_floor_usd"], "stating the facts changes the certainty, never the planning dollars"
