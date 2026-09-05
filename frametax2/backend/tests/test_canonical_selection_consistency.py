"""
Final non-Globe canonical core closeout (2026-09-04), Item A —
UPDATED by Optimizer P0 wiring remediation (2026-09-04), P0-1.

ROOT CAUSE (Codex, non-Globe closeout pass): Reports.jsx resolved its
"leading structure" using ONLY rank==1 with no fallback, while
Overview.jsx/Workspace.jsx additionally fell back to a client-side
bestPricedCandidate() re-derivation whenever rank 1 was absent. Fixed by
computing ONE canonical field server-side
(allocated_structures.canonical_selected_structure_id).

SECOND, DEEPER DEFECT FOUND BY CODEX'S OPTIMIZER WIRING AUDIT (P0-1,
2026-09-04): the "no rank 1" fallback THIS test file itself originally
encoded — "pick the lowest-NPC structure among ALL is_fully_priced
candidates" — was ITSELF wrong. It let a non-comparable, PRICED_LOW_FIT
candidate (e.g. a Saudi full-relocation review-only candidate) become
"the" canonical selection even though canonical_evaluation.py's own
_summarize_evaluation deliberately selects NONE in that exact state
(no candidate is both is_directly_comparable and admits Recommended).
Confirmed live: Little Utopia and F#K Valentine's Day both have
leading_structure_id=None and comparable_count=0, yet the OLD fallback
was silently promoting each one's own Saudi PRICED_LOW_FIT candidate as
project truth.

This file is corrected accordingly: the field must equal rank 1 when a
comparable rank-1 candidate exists, and must be None — never a
non-comparable fallback — when it does not. Bad Hombres and Lips Like
Sugar (which DO have a comparable rank-1 winner) prove the positive
path; Little Utopia and F#K Valentine's Day (which do NOT) prove the
negative path — both real, both currently exercised.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _assert_canonical_field_correct(view: dict, label: str) -> str:
    """Shared assertion, data-driven: whichever branch applies to this
    production's OWN real current state, the served
    canonical_selected_structure_id must match it exactly. Returns which
    branch was exercised, so callers can assert real coverage of both."""
    allocated = view["structures"]["allocated_structures"]
    rank1 = next((r for r in allocated["ranking"] if r.get("rank") == 1), None)
    canonical_id = allocated["canonical_selected_structure_id"]

    if rank1 is not None:
        assert canonical_id == rank1["structure_id"], (
            f"{label}: canonical field must equal rank 1 when a comparable rank-1 candidate exists"
        )
        return "rank1"

    # Optimizer P0 wiring remediation, P0-1: no comparable rank-1
    # candidate means NO canonical selection — never a fallback to the
    # lowest-NPC candidate among non-comparable/PRICED_LOW_FIT structures.
    assert canonical_id is None, (
        f"{label}: canonical_selected_structure_id must be None when no comparable rank-1 "
        f"candidate exists — got {canonical_id!r}, which would be a manufactured, "
        "non-comparable canonical selection (the exact P0-1 defect Codex found)"
    )
    return "no-comparable-winner"


async def test_canonical_field_correct_across_all_four_locked_corpus_productions(db: AsyncSession):
    """Runs all four real productions and asserts the canonical field is
    correct for each given its OWN real current state, then asserts that
    both branches (a real comparable rank-1 winner, and the real
    no-comparable-winner state) are genuinely exercised by real data —
    not merely theoretically covered."""
    branches_seen = set()
    for project_id, label in (
        (LITTLE_UTOPIA_PROJECT_ID, "Little Utopia"),
        (FVD_PROJECT_ID, "F#K Valentine's Day"),
        (BAD_HOMBRES_PROJECT_ID, "Bad Hombres"),
        (LIPS_LIKE_SUGAR_PROJECT_ID, "Lips Like Sugar"),
    ):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        branches_seen.add(await _assert_canonical_field_correct(view, label))

    assert branches_seen == {"rank1", "no-comparable-winner"}, (
        f"expected both branches genuinely exercised across the real corpus, got {branches_seen}"
    )


async def test_little_utopia_and_fvd_never_surface_a_noncomparable_candidate_as_canonical(db: AsyncSession):
    """The exact real-project regression case Codex named: Little Utopia
    and F#K Valentine's Day must never expose their own Saudi
    full-relocation PRICED_LOW_FIT candidate (or any other non-comparable
    candidate) as canonical_selected_structure_id."""
    for project_id, label in (
        (LITTLE_UTOPIA_PROJECT_ID, "Little Utopia"),
        (FVD_PROJECT_ID, "F#K Valentine's Day"),
    ):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        allocated = view["structures"]["allocated_structures"]
        canonical_id = allocated["canonical_selected_structure_id"]
        comparable_count = len([r for r in allocated["ranking"] if r.get("rank") == 1])
        assert comparable_count == 0, f"{label}: expected this real production to currently have no comparable winner"
        assert canonical_id is None, (
            f"{label}: canonical_selected_structure_id must be None (got {canonical_id!r}) — "
            "no comparable Recommended candidate exists, so there is no canonical selection"
        )


async def test_bad_hombres_and_lips_valid_canonical_selection_preserved(db: AsyncSession):
    """Regression guard: the two productions that DO have a real
    comparable rank-1 winner must keep their valid selection unaffected
    by the P0-1 fix."""
    for project_id, label in (
        (BAD_HOMBRES_PROJECT_ID, "Bad Hombres"),
        (LIPS_LIKE_SUGAR_PROJECT_ID, "Lips Like Sugar"),
    ):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        allocated = view["structures"]["allocated_structures"]
        rank1 = next((r for r in allocated["ranking"] if r.get("rank") == 1), None)
        assert rank1 is not None, f"{label}: expected this real production to currently have a comparable winner"
        assert allocated["canonical_selected_structure_id"] == rank1["structure_id"]


async def test_canonical_field_is_none_only_when_no_comparable_winner_exists(db: AsyncSession):
    """Sanity guard against ever fabricating a selection: the field may
    only be None when there is genuinely no comparable rank-1 candidate —
    never merely because a NON-comparable candidate happens to be
    cheaper."""
    for project_id in (
        LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID, BAD_HOMBRES_PROJECT_ID, LIPS_LIKE_SUGAR_PROJECT_ID,
    ):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        allocated = view["structures"]["allocated_structures"]
        canonical_id = allocated["canonical_selected_structure_id"]
        rank1 = next((r for r in allocated["ranking"] if r.get("rank") == 1), None)
        if canonical_id is None:
            assert rank1 is None, f"{project_id}: canonical field is None despite a comparable rank-1 candidate existing"
        else:
            assert rank1 is not None and canonical_id == rank1["structure_id"]
