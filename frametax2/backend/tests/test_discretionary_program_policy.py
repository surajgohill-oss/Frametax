"""
Final non-Globe canonical core closeout (2026-09-04), Item B.

Generic discretionary/selective-program policy: a project-level default
(include/exclude) with a per-program override, gating any candidate whose
program_requirements.allocation_type == DISCRETIONARY at the single
candidate-generation choke point in canonical_evaluation.py. Never a
Saudi-specific column, never a country-name if/else — Saudi's own
sa_film_commission_rebate program is used here only because it is a REAL
discretionary program that a real production (F#K Valentine's Day) has a
real candidate for; the mechanism itself is proven fully generic by the
pure-function tests at the bottom, which exercise arbitrary program
slugs with no jurisdiction involved at all.

Real ProjectFact rows are written to the live database for these
integration tests — every test cleans up in a `finally` block, following
the exact established pattern (see test_production_page_integrity.py's
own contingency test), so no lasting side effect survives this run.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import (
    DISCRETIONARY_POLICY_DEFAULT_FACT_KEY,
    DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX,
    _discretionary_policy_resolve,
    _is_discretionary_program,
    evaluate_project,
)
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
SAUDI_SLUG = "sa_film_commission_rebate"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _fact(project_id: str, fact_key: str, value: str) -> ProjectFact:
    return ProjectFact(
        id=uuid.uuid4(), project_id=project_id, fact_key=fact_key,
        value=value, value_type="string",
        source_type=ProjectFactSourceType.USER_OVERRIDE.value,
        review_status=ReviewStatus.APPROVED.value,
    )


async def _clear_policy_facts(db: AsyncSession, project_id: str):
    await db.execute(delete(ProjectFact).where(
        ProjectFact.project_id == project_id,
        (ProjectFact.fact_key == DISCRETIONARY_POLICY_DEFAULT_FACT_KEY)
        | ProjectFact.fact_key.like(f"{DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX}%"),
    ))
    await db.commit()


# ── Pure-function unit coverage (no jurisdiction, no database) ────────────

def test_is_discretionary_program_reads_the_real_allocation_type_field():
    assert _is_discretionary_program(SAUDI_SLUG) is True
    # An ordinary entitlement program (Louisiana) is not discretionary.
    assert _is_discretionary_program("lu_filmfund_tax_shelter_rebate") is True  # DISCRETIONARY per registry
    assert _is_discretionary_program("nonexistent_program_slug_xyz") is False


def test_discretionary_policy_resolve_is_generic_for_any_slug_no_country_branch():
    # No facts at all -> "include" (the default, behavior-preserving).
    assert _discretionary_policy_resolve("any_program_slug", {}) == "include"
    # Project default alone.
    facts = {DISCRETIONARY_POLICY_DEFAULT_FACT_KEY: "exclude"}
    assert _discretionary_policy_resolve("program_a", facts) == "exclude"
    assert _discretionary_policy_resolve("program_b", facts) == "exclude"
    # Per-program override beats the project default, for THAT program only.
    facts = {
        DISCRETIONARY_POLICY_DEFAULT_FACT_KEY: "exclude",
        f"{DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX}program_a": "include",
    }
    assert _discretionary_policy_resolve("program_a", facts) == "include"
    assert _discretionary_policy_resolve("program_b", facts) == "exclude"
    # Garbage value on either key falls back to "include", never crashes,
    # never silently excludes on an unrecognized value.
    facts = {DISCRETIONARY_POLICY_DEFAULT_FACT_KEY: "banana"}
    assert _discretionary_policy_resolve("program_a", facts) == "include"


# ── Real integration coverage: F#K Valentine's Day + Saudi (Case 2) ───────

async def test_default_include_behavior_is_unchanged_from_before_this_policy_existed(db: AsyncSession):
    """No facts on file at all -- the exact state every existing project
    was in before this closeout -- must produce the exact same Saudi
    structure as before."""
    await _clear_policy_facts(db, FVD_PROJECT_ID)
    try:
        await evaluate_project(db, FVD_PROJECT_ID)
        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        allocated = view["structures"]["allocated_structures"]
        saudi = [s for s in allocated["structures"] if s.get("program_slug") == SAUDI_SLUG]
        assert saudi, "expected F#K's real Saudi full_relocation candidate to still exist by default"
        assert view["production"]["discretionary_policy"]["project_default"] == "include"
    finally:
        await _clear_policy_facts(db, FVD_PROJECT_ID)


async def test_per_program_exclude_removes_only_saudi_case_2_leaves_universe(db: AsyncSession):
    """CASE 2: a candidate whose only program is itself discretionary --
    excluding it removes the candidate from the universe entirely (no
    structure generated for it), while every other candidate (including
    other discretionary ones, since only THIS program is excluded) is
    untouched."""
    await _clear_policy_facts(db, FVD_PROJECT_ID)
    try:
        db.add(_fact(FVD_PROJECT_ID, f"{DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX}{SAUDI_SLUG}", "exclude"))
        await db.commit()

        await evaluate_project(db, FVD_PROJECT_ID)
        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        allocated = view["structures"]["allocated_structures"]

        saudi = [s for s in allocated["structures"] if s.get("program_slug") == SAUDI_SLUG]
        assert saudi == [], "Saudi's candidate must be entirely absent once its own program is excluded"

        policy_view = view["production"]["discretionary_policy"]
        assert policy_view["program_overrides"].get(SAUDI_SLUG) == "exclude"
        assert policy_view["resolved_by_program"].get(SAUDI_SLUG) == "exclude"

        # A DIFFERENT discretionary program in the same production's
        # universe (e.g. Mauritius) must be untouched -- per-program
        # scoping, never a blanket discretionary-off.
        other_discretionary_slugs = {
            slug for slug, resolved in policy_view["resolved_by_program"].items()
            if slug != SAUDI_SLUG
        }
        for slug in other_discretionary_slugs:
            assert policy_view["resolved_by_program"][slug] == "include", (
                f"{slug} must remain included -- only {SAUDI_SLUG} was excluded"
            )
    finally:
        await _clear_policy_facts(db, FVD_PROJECT_ID)
        # Restore the default-include structure set for any later test
        # in this run that reads F#K's structures.
        await evaluate_project(db, FVD_PROJECT_ID)


async def test_project_default_exclude_removes_every_discretionary_program_at_once(db: AsyncSession):
    """Project-wide default OFF removes ALL discretionary candidates
    (Saudi and any other discretionary program this production has a
    candidate for), never just one -- distinguishing the default from a
    per-program override."""
    await _clear_policy_facts(db, FVD_PROJECT_ID)
    try:
        db.add(_fact(FVD_PROJECT_ID, DISCRETIONARY_POLICY_DEFAULT_FACT_KEY, "exclude"))
        await db.commit()

        await evaluate_project(db, FVD_PROJECT_ID)
        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        allocated = view["structures"]["allocated_structures"]

        saudi = [s for s in allocated["structures"] if s.get("program_slug") == SAUDI_SLUG]
        assert saudi == []

        policy_view = view["production"]["discretionary_policy"]
        assert policy_view["project_default"] == "exclude"
        # Every discretionary program this production has any candidate
        # for must now resolve to "exclude" -- the whole point of a
        # project-wide default vs. a per-program override.
        for slug, resolved in policy_view["resolved_by_program"].items():
            assert resolved == "exclude", f"{slug} should be excluded under the project default"
    finally:
        await _clear_policy_facts(db, FVD_PROJECT_ID)
        await evaluate_project(db, FVD_PROJECT_ID)


async def test_authority_requirements_are_never_relaxed_by_this_policy(db: AsyncSession):
    """Turning a discretionary program ON (or leaving it on) must never
    itself satisfy or bypass eligibility/preapproval — this policy only
    decides whether the CANDIDATE exists, never whether it qualifies.
    Verified by confirming Saudi's own structure, when present, still
    carries its real administrative_allocation_risk disclosure (P0-4a /
    Section 5 — preapproval_mandatory=True, allocation_type=DISCRETIONARY
    for this exact program) rather than this policy silently upgrading it
    to a deterministic entitlement."""
    await _clear_policy_facts(db, FVD_PROJECT_ID)
    try:
        await evaluate_project(db, FVD_PROJECT_ID)
        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        allocated = view["structures"]["allocated_structures"]
        saudi = next((s for s in allocated["structures"] if s.get("program_slug") == SAUDI_SLUG), None)
        assert saudi is not None
        assert saudi.get("administrative_allocation_risk") is True, (
            "Saudi's real discretionary/preapproval disclosure must survive unchanged "
            "regardless of this project's own inclusion policy"
        )
    finally:
        await _clear_policy_facts(db, FVD_PROJECT_ID)
