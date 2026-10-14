"""NA-RECONCILIATION-13: BC DAVE's host-credit dependency through the real evaluation pipeline (rolled-back synthetic records on the isolated pytest database; no real production is read or written).

Income Tax Act (BC) s.81.2(1)(a): DAVE is claimable only with the s.80 credit (s.82.3(1)(a): the s.82.1 credit). The host fact is derived from the structure the program is priced in; it is never a producer fact."""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.services import canonical_evaluation as ce


@pytest.fixture
async def db():
    from tests.isolated_records import isolated_session
    async with isolated_session() as session:
        yield session


LINES = (
    ("2000", "DIRECTOR FEE", "atl_director", "atl", 300_000.0),
    ("3000", "CREW", "btl_crew_labor", "btl", 1_200_000.0),
    ("3200", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 500_000.0),
    ("4200", "VISUAL EFFECTS", "vfx", "post", 600_000.0),
)


@pytest.mark.asyncio
async def test_dave_is_priced_with_its_host_in_a_british_columbia_production_and_never_asks_the_producer_for_the_host(db):
    from tests.isolated_records import create_synthetic_project
    pid = await create_synthetic_project(db, lines=LINES, home_code="CA-BC")
    result = await ce.evaluate_project(db, pid)
    fp = result["state_fingerprint"]
    rows = (await db.execute(text("""
        SELECT scr.calculation_trace_json AS trace
        FROM production_structures ps JOIN structure_calculation_results scr ON scr.structure_id = ps.id
        WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
          AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
    """), {"pid": str(pid), "ev": ce.ENGINE_VERSION, "fp": fp})).all()
    traces = [r[0] for r in rows]
    dave_rows = [t for t in traces if t.get("program_slug") == "ca_bc_dave" or "ca_bc_dave" in (t.get("program_slugs") or [])]
    assert dave_rows, "DAVE is priced for a British Columbia production with 600,000 of VFX labour"
    for t in dave_rows:
        text_blob = repr(t)
        assert "ca-bc-dave-host-credit-in-structure" not in text_blob, "the host fact is derived from the structure, so it is never left unresolved when the host is a candidate"
        assert "ca_bc_dave__structure_host_credit_present" not in repr(t.get("missing_facts") or [])
