"""
Canonical served evaluation runtime — Phase 2 cutover regression tests.

`app/api/v1/evaluation.py` (the route behind "Begin Evaluation") now calls
`canonical_evaluation.evaluate_project` — the validated qualification/
allocation/pricing stack — instead of `project_evaluation.begin_evaluation`,
which called `run_full_analysis` (ENGINE_VERSION 0.1.0, proven in bca893a to
reference none of the canonical layers and to be $1.12M off Little Utopia's
accepted NPC). These tests lock in the cutover against the two real,
already-persisted projects it must serve correctly: Little Utopia (the
regression oracle) and F#K Valentine's Day.

Read/idempotent against real project rows — same precedent as
test_canonical_project_economics.py's Little Utopia tests. No disposable
project needed: `evaluate_project` is safe to call repeatedly (idempotent
per input fingerprint) and never mutates validated economics.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"

#: Consolidated Backend Correction, Part 19-21 (CBA-009) — see the
#: matching, more fully documented constant in
#: test_canonical_project_economics.py. Little Utopia's own real,
#: persisted 100% contingency-expected-utilization project election
#: (alembic migration 0068) reproduces the historical accepted figure
#: through the fully generic pipeline.
ACCEPTED_LU_NPC_USD = 3_057_794.90
FVD_GROSS_BUDGET_USD = 4_517_687.00


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_little_utopia_canonical_service_reproduces_exact_npc_and_winner(db: AsyncSession):
    """THE acceptance test for the served cutover: run through the actual
    served entry point (not the lower-level calculators directly, which
    test_canonical_project_economics.py already covers), the economics
    must still be Mauritius at exactly the accepted NPC — disclosed on
    `baseline`, even though `top_result` is correctly None.

    Final Consolidated Backend Correction + Global Structuring
    Intelligence Acceptance, Part 4/CBA-001: Mauritius's own cultural-
    test-applicability research remains genuinely AUTHORITY_UNRESOLVED
    (a real, prior-session finding — whether the program even has a
    cultural test at all is unconfirmed by primary authority). Per this
    task's own explicit instruction ("DO NOT weaken qualification gates
    merely because LU ... would otherwise have no Recommended scenario.
    Truthful unresolved status is preferable to false recommendation"),
    `top_result` is honestly None rather than presenting an unresolved
    baseline as a recommended winner. The real, priced economics remain
    fully disclosed on `baseline` and in `ranked`."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")
    assert result["engine_version"] == ENGINE_VERSION
    assert result["base_jurisdiction_code"] == "MU"
    assert result["baseline"]["true_net_cost_usd"] == ACCEPTED_LU_NPC_USD
    assert result["baseline"]["is_baseline"] is True
    assert result["baseline"]["candidate_status"] == "PRICED"
    assert result["top_result"] is None


async def test_fvd_canonical_service_uses_real_budget_and_greece_baseline(db: AsyncSession):
    """FVD must go through the SAME service, with its own real evidence —
    never the old run_full_analysis figure ($3,627,135.60, commit 87440df)
    presented as current.

    Greece's own cultural-test point table currently resolves
    USER_FACT_REQUIRED for this project (0 of 20 points confirmed; a real
    production-plan fact is genuinely missing) — so, per the same Part
    4/CBA-001 reasoning as Little Utopia above, `top_result` is honestly
    None rather than presenting an unresolved baseline as recommended.
    The real, priced economics remain disclosed on `baseline`."""
    result = await evaluate_project(db, FVD_PROJECT_ID)
    assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")
    assert result["engine_version"] == ENGINE_VERSION
    assert result["gross_budget_usd"] == FVD_GROSS_BUDGET_USD
    assert result["base_jurisdiction_code"] == "GR"
    assert result["baseline"]["is_baseline"] is True
    assert result["baseline"]["candidate_status"] == "PRICED"
    # Not the stale legacy figure, and not fabricated — whatever the
    # canonical engine honestly produces for Greece's real program.
    assert result["baseline"]["true_net_cost_usd"] != 3_627_135.60
    assert result["baseline"]["true_net_cost_usd"] is not None
    assert result["top_result"] is None


async def test_project_leading_structure_is_cleared_pending_qualification_resolution(db: AsyncSession):
    """The stale legacy-engine result (run_full_analysis, commit 87440df)
    must never be what the project's leading structure resolves to.

    Neither Little Utopia's nor FVD's own baseline currently admits
    Recommended (see the two tests above) — so `leading_structure_id` is
    correctly cleared to None (Part 4/CBA-001: a stale prior leading
    structure must never keep rendering as though still current and
    recommended) rather than left pointing at a superseded result."""
    for project_id in (LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID):
        await evaluate_project(db, project_id)
        project = await db.get(Project, project_id)
        assert project.leading_structure_id is None


async def test_relocation_candidates_never_become_top_result(db: AsyncSession):
    """Little Utopia has real, honestly-priced relocation candidates with a
    LOWER npc_verified than the baseline (no travel/in-kind cost is modeled
    generically) — they must never be selected as top_result. This is the
    exact "invented savings" trap the RELOCATION_COMPARABILITY_NOTE guards
    against; this test locks in that the guard actually holds even when
    the baseline itself is qualification-unresolved and top_result is
    therefore None (Part 4/CBA-001) rather than a relocation candidate
    silently stepping in to fill the gap."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    cheaper_alternatives = [
        r for r in result["ranked"]
        if not r["is_baseline"] and r["true_net_cost_usd"] < result["baseline"]["true_net_cost_usd"]
    ]
    assert len(cheaper_alternatives) > 0, "test is meaningless without a real cheaper alternative to guard against"
    assert result["top_result"] is None
    assert all(not r["is_baseline"] for r in cheaper_alternatives)


#: Canonical served wiring repair (Codex Defect 4) — the real terminal
#: causes an unpriceable candidate can reach, never flattened to one
#: generic value. AU Location Offset (real statutory rules that don't
#: resolve for this production/QPE) is RULE_REJECTED; a program the
#: completed authority-coverage audit adjudicated selective/superseded is
#: FEASIBILITY_REVIEW_REQUIRED; everything else with no classified
#: doctrine/rate data at all is UNPRICEABLE_AUTHORITY_INSUFFICIENT.
#:
#: Consolidated Backend Correction, CBA-001 (Part 2) — QUALIFICATION_
#: HARD_FAIL is a genuine terminal cause too: a candidate whose role_
#: qualification bridge resolved a real HARD_FAIL (never CURABLE_GAP/
#: USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED/
#: RULE_DATA_INCOMPLETE — those are priced and disclosed, not blocked;
#: see _QUALIFICATION_ADMITS_PRICING) never enters pricing at all.
#: QUALIFICATION_UNRESOLVED is listed for completeness (currently
#: unreachable given the admitted set above, but a real, defined terminal
#: status the same code path can still emit).
UNPRICEABLE_STATUSES = {
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "RULE_REJECTED", "FEASIBILITY_REVIEW_REQUIRED",
    "QUALIFICATION_HARD_FAIL", "QUALIFICATION_UNRESOLVED",
}


async def test_unpriceable_candidates_are_accounted_for_not_dropped(db: AsyncSession):
    """Every candidate that reaches structure generation (Part N) ends in a
    terminal state — none are silently dropped. Capability-only
    jurisdictions (the Abu Dhabi case's own classification) are recorded
    with their real discovery reason, not ranked as executable."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["unpriceable_count"] > 0
    for entry in result["unpriceable"]:
        assert entry["candidate_status"] in UNPRICEABLE_STATUSES
        assert entry["true_net_cost_usd"] is None
        assert entry["reason"]  # never an unexplained drop
    for entry in result["ranked"]:
        assert entry["candidate_status"] == "PRICED"


async def test_mfni_limitation_present_on_every_result(db: AsyncSession):
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert "mfni_limitation" in result and result["mfni_limitation"]
    assert "not yet applied" in result["mfni_limitation"]

    rows = (await db.execute(
        select(StructureCalculationResult).where(
            StructureCalculationResult.input_fingerprint == result["state_fingerprint"]
        )
    )).scalars().all()
    assert rows
    for row in rows:
        assert row.warnings, f"{row.structure_id} carries no MFNI disclosure"


async def test_evaluation_route_no_longer_reaches_run_full_analysis():
    """Part S — regression protection. The served route must import the
    canonical service only; run_full_analysis must not be reachable from it."""
    import ast
    import inspect

    from app.api.v1 import evaluation as route_mod

    tree = ast.parse(inspect.getsource(route_mod))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert "app.services.canonical_evaluation" in imported_modules
    assert "app.services.project_evaluation" not in imported_modules
    assert not any("run_full_analysis" in m for m in imported_modules)


async def test_canonical_evaluation_module_reads_no_project_specific_data():
    """Same convention as canonical_project_economics.py's own guard: the
    served engine must import no per-project data module."""
    import ast
    import inspect

    from app.services import canonical_evaluation as mod

    tree = ast.parse(inspect.getsource(mod))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "little_utopia" not in node.module, (
                f"canonical_evaluation.py must stay project-agnostic; imports {node.module!r}"
            )
            assert "run_full_analysis" not in node.module, (
                f"canonical_evaluation.py must not depend on the legacy engine; imports {node.module!r}"
            )
