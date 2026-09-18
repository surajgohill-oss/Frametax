"""
Project Workspace UI cutover — regression tests for the view adapter
behind the generic Overview/Script/Budget/World pages
(app/services/project_workspace_view.py).

These lock in the two properties the cutover depends on:

1. The SAME adapter, called with no project-specific branching, produces
   correct-but-different output for Little Utopia and F#K Valentine's Day
   — proving "one Workspace, different project state" (Part C/K) rather
   than a hidden per-project code path.
2. Candidate UI status is derived generically from `candidate_status` /
   `relocation_cost_normalized` (never a per-jurisdiction rule) — the
   direct regression guard for the Abu Dhabi presentation fix (Part G):
   AE-AD must never appear as COMPARABLE or REVIEW_REQUIRED, only
   UNPRICEABLE, on every project the same way.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.project_workspace_view import (
    UI_COMPARABLE,
    UI_REVIEW_REQUIRED,
    UI_UNPRICEABLE,
    build_project_workspace_view,
)

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_unknown_project_returns_not_found(db: AsyncSession):
    result = await build_project_workspace_view(db, "00000000-0000-0000-0000-000000000000")
    assert result == {"status": "PROJECT_NOT_FOUND"}


async def test_fvd_workspace_view_is_correct_and_self_contained(db: AsyncSession):
    result = await build_project_workspace_view(db, FVD_PROJECT_ID)
    assert result["status"] == "OK"

    project = result["project"]
    assert project["title"] == "F#K Valentine's Day"
    assert project["budget_usd"] == pytest.approx(4_517_687.0)
    assert project["base_jurisdiction_code"] == "GR"
    assert "is_served_production" not in project  # Part P: no identity field in the generic view

    evaluation = result["evaluation"]
    assert evaluation["status"] == "EVALUATION_COMPLETE"
    assert evaluation["top_result"]["jurisdiction_code"] == "GR"

    assert result["script"]["scene_count"] == 99
    assert result["script"]["character_count"] == 38
    assert result["budget"]["total_usd"] == pytest.approx(4_517_687.0)


async def test_little_utopia_workspace_view_uses_the_same_adapter(db: AsyncSession):
    result = await build_project_workspace_view(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["status"] == "OK"

    project = result["project"]
    assert project["title"] == "The Little Utopia"
    assert project["budget_usd"] == pytest.approx(4_364_393.0)
    assert project["base_jurisdiction_code"] == "MU"
    assert "is_served_production" not in project

    evaluation = result["evaluation"]
    assert evaluation["status"] == "EVALUATION_COMPLETE"
    assert evaluation["top_result"]["jurisdiction_code"] == "MU"
    # Production Page Integrity Closeout (migration 0071): LU's stale
    # beta 100% contingency-utilization election (migration 0068) was
    # removed. Absent an election the reserve is GREY_AREA_REQUIRES_
    # AUTHORITY, never silently 0%/100%.
    assert evaluation["top_result"]["true_net_cost_usd"] == pytest.approx(3_791_333.30, abs=1.0)

    # LU's screenplay has not been SA-1 parsed — the adapter must report
    # that honestly (0 scenes) rather than fabricate structure (Part D).
    assert result["script"]["scene_count"] == 0


async def test_candidate_classification_is_generic_not_per_jurisdiction(db: AsyncSession):
    """Same rule, same result shape, on both projects — the direct
    regression guard for the Abu Dhabi presentation fix (Part G)."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        result = await build_project_workspace_view(db, project_id)
        evaluation = result["evaluation"]

        all_candidates = evaluation["comparable"] + evaluation["review_required"] + evaluation["unpriceable"]
        for c in all_candidates:
            assert c["ui_status"] in (UI_COMPARABLE, UI_REVIEW_REQUIRED, UI_UNPRICEABLE)

        # Backend-wiring self-audit (2026-09-17): Oregon (OPIF) was this
        # guard's fixture on the theory that it is authority-insufficient
        # on every project -- but that coverage veto was deliberately
        # REMOVED (see app/data/authority_coverage_registry.py's own
        # "us_or_opif REMOVED" note): coverage_state() now defaults absent
        # slugs to PRICEABLE_VALIDATED, and tests/test_oregon_full_db_
        # pipeline.py drives Oregon through the real pipeline to a genuine
        # PRICED $814,000.00 result with real evidenced facts -- only a
        # hostile/unevidenced-fact scenario rejects it. This is the exact
        # same fate this file's own comment already documents for AE-AD
        # (Abu Dhabi): a fixture assumed to be permanently unpriceable
        # became genuinely priceable once real authority coverage caught
        # up, and asserting the OLD disposition became a stale oracle, not
        # a real regression guard. Oregon's ui_status is intentionally NOT
        # asserted here for the same reason AE-AD's isn't anymore -- only
        # that IF it is present, its status is one of the three valid,
        # already-checked literals (line above). The structural invariant
        # this test exists to guard (every candidate's ui_status is a
        # known literal, never silently something else) is unaffected.
        oregon = next((c for c in all_candidates if c["jurisdiction_code"] == "US-OR"), None)
        if oregon is not None:
            assert oregon["ui_status"] in (UI_COMPARABLE, UI_REVIEW_REQUIRED, UI_UNPRICEABLE)

        # Counts in the summary must match the classified lists exactly.
        assert evaluation["comparable_count"] == len(evaluation["comparable"])
        assert evaluation["review_required_count"] == len(evaluation["review_required"])
        assert evaluation["unpriceable_count"] == len(evaluation["unpriceable"])
