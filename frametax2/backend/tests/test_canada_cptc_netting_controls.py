"""F-14, re-derived from primary authority (CRA RC4164, Form T1131 guide, lines 421-430, 423, 618): assistance, including ANY provincial tax
credit, reduces the PRODUCTION COST, and CPTC qualified labour = min(labour expenditure, 60% x (production cost - assistance)). Labour itself is not
reduced, the whole provincial credit counts, and it matters only when the 60% cap falls below the labour. Rolled-back synthetic records; the CPTC
labour basis is a STATED planning fact, not payroll evidence. Hand computation, budget 2,500,000 (labour 1,500,000 CPTC / 1,900,000 Ontario):
  OFTTC 35% x 1,900,000 = 665,000 ; cap = 60% x (2,500,000 - 665,000) = 1,101,000 < 1,500,000 -> CPTC = 25% x 1,101,000 = 275,250 (unlimited: 375,000)
  stack 940,250 ; reduction 99,750.   Quebec 25% x 2,500,000 = 625,000 ; cap 1,125,000 -> CPTC 281,250 ; stack 906,250.
  Large non-labour budget (gross 7,900,000): cap = 60% x (7,900,000 - 665,000) = 4,341,000 > 1,500,000 -> CPTC stays 375,000 despite the OFTTC."""
from __future__ import annotations

import uuid

import pytest

from app.models.enums import ProjectFactSourceType
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from tests.isolated_records import add_synthetic_people, create_synthetic_project, isolated_session, served_structures

pytestmark = pytest.mark.asyncio

LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
         ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0))


async def _stack(db_lines):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=db_lines, home_code="CA-ON")
        await add_synthetic_people(db, pid, [("director", "Dir One", "CA", True), ("writer", "Wri One", "CA", True)])
        db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="amount_fact:ca_federal_cptc_qualified_labour_usd", value="1500000",
                           source_type=ProjectFactSourceType.USER_OVERRIDE))
        await db.commit()
        await evaluate_project(db, pid)
        entries = await served_structures(db, pid)
        return {tuple(sorted(e["program_slugs"])): e for e in entries if e["structure_type"] == "multi_program"}, \
            next(e for e in entries if e["program_slugs"] == ["ca_federal_cptc"] and e["candidate_status"] == "PRICED")


async def test_cptc_cap_is_measured_on_production_cost_net_of_assistance_not_on_labour():
    by, alone = await _stack(LINES)
    assert alone["confirmed_incentive_floor_usd"] == pytest.approx(0.25 * 1_500_000)
    ofttc = by[("ca_federal_cptc", "on_ofttc")]
    assert ofttc["candidate_status"] == "PRICED" and ofttc["stacking_rule_type"] == "spend_reduction"
    assert ofttc["per_program_adjusted_usd"]["on_ofttc"] == pytest.approx(665_000.0)
    assert ofttc["per_program_adjusted_usd"]["ca_federal_cptc"] == pytest.approx(0.25 * 0.60 * (2_500_000 - 665_000))
    assert ofttc["confirmed_incentive_floor_usd"] == pytest.approx(940_250.0) and ofttc["stacking_reduction_usd"] == pytest.approx(99_750.0)
    quebec = by[("ca_federal_cptc", "ca_qc_pstc")]
    assert quebec["per_program_adjusted_usd"]["ca_federal_cptc"] == pytest.approx(0.25 * 0.60 * (2_500_000 - 625_000))
    assert quebec["confirmed_incentive_floor_usd"] == pytest.approx(906_250.0)
    # NA-CODEX-08: Ontario Creates OPSTC Guidelines s.1.01 permit the OPSTC alongside the CPTC; it is assistance that lowers the cost behind the cap.
    # OPSTC 21.5% x 2,500,000 = 537,500; cap 60% x (2,500,000 - 537,500) = 1,177,500 < 1,500,000 -> CPTC 25% x 1,177,500 = 294,375; stack 831,875.
    opstc = by[("ca_federal_cptc", "on_opstc")]
    assert opstc["candidate_status"] == "PRICED" and opstc["stacking_rule_type"] == "spend_reduction"
    assert opstc["per_program_adjusted_usd"]["on_opstc"] == pytest.approx(537_500.0)
    assert opstc["per_program_adjusted_usd"]["ca_federal_cptc"] == pytest.approx(0.25 * 0.60 * (2_500_000 - 537_500))
    assert opstc["confirmed_incentive_floor_usd"] == pytest.approx(831_875.0) and opstc["stacking_reduction_usd"] == pytest.approx(80_625.0)
    # the domestic OFTTC and the service OPSTC stay mutually exclusive, so the triple is still rejected
    assert by[("ca_federal_cptc", "on_ofttc", "on_opstc")]["candidate_status"] == "RULE_REJECTED"


async def test_a_provincial_credit_does_not_reduce_cptc_when_the_cost_cap_is_not_binding():
    big = LINES[:2] + (("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 6_000_000.0),)
    by, _ = await _stack(big)
    ofttc = by[("ca_federal_cptc", "on_ofttc")]
    assert ofttc["per_program_adjusted_usd"]["ca_federal_cptc"] == pytest.approx(375_000.0), "60% x (7.9M - 665k) = 4.34M exceeds the 1.5M labour"
    assert ofttc["stacking_reduction_usd"] == pytest.approx(0.0)
