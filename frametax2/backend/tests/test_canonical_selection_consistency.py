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
from app.models.project import Project
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"

# Optimizer FINAL P0 remediation (P0-SEL-001) — the nine broader-corpus
# projects Codex found with NO current baseline row at all, where
# _summarize_evaluation's no-baseline-row branch was persisting the
# cheapest non-comparable priced relocation into Project.leading_structure_id
# while the served view correctly showed null.
BROADER_CORPUS_NO_BASELINE_PROJECT_IDS = {
    "10 Double Zero": "3519feda-d280-435f-badc-1e4c788a2cb3",
    "Baron Samedi": "fcbb9190-5b9c-4af8-96fa-359fce1cf79a",
    "Going Places": "dee8feca-7b94-4330-ac19-79969e8facb8",
    "Interference": "565744c5-86fd-4c1d-bdb5-fdd4b910d0b0",
    "Rocky Mountain": "191f1422-79a1-4a6c-a3fb-cafa0c2c2343",
    "The Cure": "f3c1a6f1-a357-407f-8072-7dfbba87ceae",
    "The System": "e1f2444d-4eac-410e-9c92-45637b8f2ae0",
    "Twilight of the Dead": "92167170-9e42-4bbb-9754-877ce1692b8a",
    "Underwater": "f1292c56-0288-4575-91ec-1f00081f07a0",
}


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


async def test_no_baseline_projects_persist_null_leading_structure_id(db: AsyncSession):
    """Optimizer FINAL P0 remediation, P0-SEL-001 — the exact named
    real-project regression. Each of these nine projects currently has NO
    baseline row at all (not even a blocked one). Before this fix,
    _summarize_evaluation's final else-branch (`top_pair = priced[0] if
    priced else None`) persisted the cheapest non-comparable priced
    relocation into Project.leading_structure_id, while the served view
    correctly showed canonical_selected_structure_id=None — the exact
    evaluator/served divergence Codex's broader-corpus audit found.
    Required invariant: with no baseline row, EVERY SOURCE must agree
    there is no winner — evaluator top_result, persisted
    Project.leading_structure_id, and served canonical_selected_structure_id
    all None."""
    for label, project_id in BROADER_CORPUS_NO_BASELINE_PROJECT_IDS.items():
        econ_status = await evaluate_project(db, project_id)
        assert econ_status.get("top_result") is None, (
            f"{label}: evaluator top_result must be None with no baseline row, "
            f"got {econ_status.get('top_result')!r}"
        )
        project = await db.get(Project, project_id)
        assert project is not None, f"{label}: project not found by id {project_id}"
        assert project.leading_structure_id is None, (
            f"{label}: Project.leading_structure_id must be None with no baseline row — "
            f"got {project.leading_structure_id!r} (the exact P0-SEL-001 defect: a "
            "non-comparable relocation invented as a persisted winner)"
        )
        view = await build_production_and_structures(db, project_id)
        allocated = view["structures"]["allocated_structures"]
        assert allocated["canonical_selected_structure_id"] is None, (
            f"{label}: served canonical_selected_structure_id must be None"
        )


async def test_evaluator_persisted_and_served_selection_agree_across_full_corpus(db: AsyncSession):
    """Optimizer FINAL P0 remediation, P0-SEL-001 — the general contract,
    proven across every currently optimizer-ready project this test file
    already has real IDs for: evaluator top_result, persisted
    Project.leading_structure_id, and served
    canonical_selected_structure_id must always be identical (all three
    equal, or all three None). This is the single-semantic-source
    contract Codex found broken corpus-wide; the four locked-corpus IDs
    plus the nine broader-corpus no-baseline IDs together cover both a
    real comparable winner and a real no-winner state."""
    all_ids = {
        "Little Utopia": LITTLE_UTOPIA_PROJECT_ID,
        "F#K Valentine's Day": FVD_PROJECT_ID,
        "Bad Hombres": BAD_HOMBRES_PROJECT_ID,
        "Lips Like Sugar": LIPS_LIKE_SUGAR_PROJECT_ID,
        **BROADER_CORPUS_NO_BASELINE_PROJECT_IDS,
    }
    for label, project_id in all_ids.items():
        econ_status = await evaluate_project(db, project_id)
        top_result = econ_status.get("top_result")
        evaluator_top_id = top_result["structure_id"] if top_result else None
        project = await db.get(Project, project_id)
        persisted_id = str(project.leading_structure_id) if project.leading_structure_id else None
        view = await build_production_and_structures(db, project_id)
        served_id = view["structures"]["allocated_structures"]["canonical_selected_structure_id"]
        assert evaluator_top_id == persisted_id == served_id, (
            f"{label}: selection divergence — evaluator={evaluator_top_id}, "
            f"persisted={persisted_id}, served={served_id}"
        )
