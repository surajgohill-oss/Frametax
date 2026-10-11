"""F-14: CPTC qualified labour is reduced by provincial assistance before the credit is computed. Rolled-back synthetic records only; the
CPTC labour basis below is a STATED planning fact (amount_fact), not payroll evidence. Hand computation:
  OFTTC            = 35% x eligible Ontario labour (director 400,000 + crew 1,500,000) = 665,000
  CPTC net basis   = 1,500,000 (qualifying labour) - 665,000 = 835,000   ->  CPTC = 25% x 835,000 = 208,750 (unnetted would be 375,000)
  stack total      = 665,000 + 208,750 = 873,750 ; stacking reduction = 375,000 - 208,750 = 166,250."""
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


async def test_cptc_is_computed_on_labour_net_of_the_provincial_credit_and_never_stacks_with_opstc():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="CA-ON")
        await add_synthetic_people(db, pid, [("director", "Dir One", "CA", True), ("writer", "Wri One", "CA", True)])
        db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="amount_fact:ca_federal_cptc_qualified_labour_usd", value="1500000",
                           source_type=ProjectFactSourceType.USER_OVERRIDE))
        await db.commit()
        await evaluate_project(db, pid)
        entries = await served_structures(db, pid)
        by = {tuple(sorted(e["program_slugs"])): e for e in entries if e["structure_type"] == "multi_program"}
        alone = next(e for e in entries if e["program_slugs"] == ["ca_federal_cptc"] and e["candidate_status"] == "PRICED")
        assert alone["confirmed_incentive_floor_usd"] == pytest.approx(0.25 * 1_500_000)             # unnetted on its own
        stack = by[("ca_federal_cptc", "on_ofttc")]
        assert stack["candidate_status"] == "PRICED" and stack["stacking_rule_type"] == "spend_reduction"
        assert stack["per_program_adjusted_usd"]["on_ofttc"] == pytest.approx(0.35 * 1_900_000)
        assert stack["per_program_adjusted_usd"]["ca_federal_cptc"] == pytest.approx(0.25 * (1_500_000 - 665_000))
        assert stack["confirmed_incentive_floor_usd"] == pytest.approx(873_750.0) and stack["stacking_reduction_usd"] == pytest.approx(166_250.0)
        # CPTC (domestic content) and OPSTC (service) are mutually exclusive, alone or inside a larger group
        assert by[("ca_federal_cptc", "on_opstc")]["candidate_status"] == "RULE_REJECTED"
        assert by[("ca_federal_cptc", "on_ofttc", "on_opstc")]["candidate_status"] == "RULE_REJECTED"
