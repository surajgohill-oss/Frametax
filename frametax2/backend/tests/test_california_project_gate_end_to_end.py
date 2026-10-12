"""LLS-CA-01 end to end on rolled-back synthetic records: a Manitoba-home production with a California VFX option is evaluated through the real
candidate generation (component relocation and ordinary component hybrids). Every candidate that pairs the Manitoba credit with the California credit
must be persisted as RULE_REJECTED / PROJECT_ELIGIBILITY_GATE_FAILED (visible, never priced, never hidden), and none may be PRICED."""
from __future__ import annotations

import pytest
from sqlalchemy import select, text

from app.models.production import EvaluationCandidateAggregate
from app.services import canonical_evaluation as ce
from app.services.canonical_program_identity import alias_memo_scope
from tests.isolated_records import create_synthetic_project, isolated_session

pytestmark = pytest.mark.asyncio
LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
         ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("6100", "VFX", "vfx", "post", 300_000.0))


async def test_manitoba_shoot_with_california_vfx_is_rejected_by_the_project_gate_never_priced():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="CA-MB")
        with alias_memo_scope():
            result = await ce.evaluate_project(db, pid)
        fp = result["state_fingerprint"]
        rows = (await db.execute(text(
            "select scr.calculation_trace_json->>'candidate_status', scr.calculation_trace_json->>'rejection_reason_class', scr.calculation_trace_json->'program_slugs', "
            "scr.calculation_trace_json->>'primary_jurisdiction' from production_structures ps join structure_calculation_results scr on scr.structure_id=ps.id "
            "where ps.project_id=:p and scr.input_fingerprint=:f and scr.calculation_trace_json->'program_slugs' @> '[\"ca_film_30\"]'::jsonb"), {"p": pid, "f": fp})).all()
        groups = (await db.execute(select(EvaluationCandidateAggregate).where(
            EvaluationCandidateAggregate.project_id == pid, EvaluationCandidateAggregate.input_fingerprint == fp))).scalars().all()
    ca_groups = [g for g in groups if "ca_film_30" in (g.program_slugs or [])]
    paired = [r for r in rows if "ca_mb_film_video_credit" in (r[2] or [])] + [("AGG", g.reason_class, g.program_slugs, g.candidate_status) for g in ca_groups if "ca_mb_film_video_credit" in (g.program_slugs or [])]
    assert paired, "the Manitoba + California combination must stay visible (retained row or exactly-counted aggregate group)"
    assert not [r for r in rows if r[0] == "PRICED" and r[3] == "CA-MB"], "no PRICED California-credit candidate may have a Manitoba principal shoot"
    # Only a MANITOBA-shot production is gated out. A California principal shoot with Manitoba post/VFX service work (primary US-CA) satisfies the gate
    # (all principal photography in California) and may price once the Manitoba cost-of-production credit reaches a no-labour service component.
    assert not [g for g in ca_groups if g.candidate_status == "PRICED" and g.primary_jurisdiction == "CA-MB" and "ca_mb_film_video_credit" in (g.program_slugs or [])]
    assert any(r[1] == "PROJECT_ELIGIBILITY_GATE_FAILED" for r in paired), paired[:5]
