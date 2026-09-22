"""
PROJECT_LIBRARY_FIXTURE_EXCLUSION (2026-09-22, corrected same day) —
regression protection for the producer-visibility predicate at the
GET /projects boundary.

Root cause: Project.organization_id scoping (PROJECT_UI_DATA_INTEGRITY,
2026-09-21) is necessary but not sufficient — confirmed live, this
deployment's audit/test/synthetic seed projects share the SAME real
organization as its 4 real productions, so organization scope alone never
separates them.

CORRECTION (same day): the first version of `_is_producer_visible`
additionally enumerated 46 legacy titles ("Underwater", "Rust", "Safehaven",
...) as fixtures. That was wrong — those are plausible real company project
titles with no evidenced audit/test/synthetic signal — and has been
reverted. The ONLY evidenced exclusion signal, per explicit operator
direction, is the `AUDIT_CONTROL_` naming convention. See
app/api/v1/projects.py's `_is_producer_visible` for the full narrative.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.api.v1.projects import _is_producer_visible, list_projects
from app.core.config import settings

REAL_PRODUCTION_TITLES = {"The Little Utopia", "Bad Hombres", "F#K Valentine's Day", "Lips Like Sugar"}

# Representative historical company titles that the prior (incorrect) pass
# wrongly hid — none of these carry any evidenced audit/test/synthetic
# signal, so all must be producer-visible.
REPRESENTATIVE_HISTORICAL_TITLES = ("Underwater", "Rust", "Safehaven", "The Cure", "White Feather")


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── Pure predicate — no DB needed ────────────────────────────────────────

def test_is_producer_visible_excludes_only_the_explicit_audit_control_naming_convention():
    assert _is_producer_visible("AUDIT_CONTROL_NEW_PROJECT_aa848555") is False
    assert _is_producer_visible("AUDIT_CONTROL_NEW_PROJECT_1797ef0f") is False
    assert _is_producer_visible("AUDIT_CONTROL_NEW_PROJECT_f6714a35") is False


def test_is_producer_visible_no_longer_hides_plausible_historical_company_titles():
    """The corrected predicate must NOT hide titles with no evidenced
    audit/test/synthetic signal — this is the literal regression this pass
    fixes."""
    for title in REPRESENTATIVE_HISTORICAL_TITLES:
        assert _is_producer_visible(title) is True, f"{title!r} must be producer-visible — it is not an AUDIT_CONTROL_* fixture"


def test_is_producer_visible_includes_the_four_real_productions():
    for title in REAL_PRODUCTION_TITLES:
        assert _is_producer_visible(title) is True, f"{title!r} must remain producer-visible"


def test_is_producer_visible_requires_no_allowlist_a_genuine_new_title_passes_through():
    """A project title never seen before (a genuine future ingestion, or a
    historically-persisted title regardless of evaluation state) must be
    visible by default — never require an allowlist update."""
    for title in ("A Brand New Feature Nobody Has Seen Yet", "Untitled Thriller Project 2027"):
        assert _is_producer_visible(title) is True


def test_is_producer_visible_never_excludes_a_null_or_empty_title():
    assert _is_producer_visible(None) is True
    assert _is_producer_visible("") is True


# ── Integration — the real DB, the real endpoint function ───────────────

async def test_list_projects_default_excludes_only_audit_control_and_keeps_historical_titles(db: AsyncSession):
    org_id = settings.CURRENT_ORGANIZATION_ID
    if not org_id:
        pytest.skip("settings.CURRENT_ORGANIZATION_ID not configured in this environment")
    cards = await list_projects(organization_id=org_id, include_fixtures=False, db=db)
    titles = {c.title for c in cards}
    assert REAL_PRODUCTION_TITLES <= titles, "the 4 real productions must be visible"
    for title in REPRESENTATIVE_HISTORICAL_TITLES:
        assert title in titles, f"{title!r} must be visible by default — it is not an AUDIT_CONTROL_* fixture"
    for c in cards:
        assert not c.title.startswith("AUDIT_CONTROL_")


async def test_list_projects_include_fixtures_reaches_the_full_org_scoped_set(db: AsyncSession):
    """The explicit escape hatch for audit tooling — nothing is deleted,
    everything remains reachable on request. Since only AUDIT_CONTROL_*
    titles are ever excluded now, include_fixtures should add back exactly
    those rows (never more)."""
    org_id = settings.CURRENT_ORGANIZATION_ID
    if not org_id:
        pytest.skip("settings.CURRENT_ORGANIZATION_ID not configured in this environment")
    default_cards = await list_projects(organization_id=org_id, include_fixtures=False, db=db)
    all_cards = await list_projects(organization_id=org_id, include_fixtures=True, db=db)
    assert len(all_cards) >= len(default_cards)
    added_titles = {c.title for c in all_cards} - {c.title for c in default_cards}
    assert all(t.startswith("AUDIT_CONTROL_") for t in added_titles), (
        f"every row only reachable via include_fixtures=True must be an AUDIT_CONTROL_* fixture, got: {added_titles}"
    )
