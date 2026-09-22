"""
PROJECT_LIBRARY_FIXTURE_EXCLUSION (2026-09-22) — regression protection for
the producer-visibility predicate at the GET /projects boundary.

Root cause: Project.organization_id scoping (PROJECT_UI_DATA_INTEGRITY,
2026-09-21) is necessary but not sufficient — confirmed live, this
deployment's ~49 audit/test/synthetic seed projects share the SAME real
organization as its 4 real productions, so organization scope alone never
separates them. See app/api/v1/projects.py's `_is_producer_visible` for the
full root-cause narrative and why a name-based predicate (not a new DB
column/migration — an explicit operator directive for this pass) is the
correct mechanism here.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.api.v1.projects import _is_producer_visible, list_projects
from app.core.config import settings

REAL_PRODUCTION_TITLES = {"The Little Utopia", "Bad Hombres", "F#K Valentine's Day", "Lips Like Sugar"}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── Pure predicate — no DB needed ────────────────────────────────────────

def test_is_producer_visible_excludes_the_explicit_audit_control_naming_convention():
    assert _is_producer_visible("AUDIT_CONTROL_NEW_PROJECT_aa848555") is False
    assert _is_producer_visible("AUDIT_CONTROL_NEW_PROJECT_1797ef0f") is False


def test_is_producer_visible_excludes_every_enumerated_legacy_fixture_title():
    for title in (
        "10 Double Zero", "5 LBS OF PRESSURE", "Baron Samedi", "Twilight of the Dead",
        "White Line Highway", "The Dale",
    ):
        assert _is_producer_visible(title) is False, f"{title!r} must be excluded"


def test_is_producer_visible_includes_the_four_real_productions():
    for title in REAL_PRODUCTION_TITLES:
        assert _is_producer_visible(title) is True, f"{title!r} must remain producer-visible"


def test_is_producer_visible_requires_no_allowlist_a_genuine_new_title_passes_through():
    """A project title never seen before (a genuine future ingestion) must
    be visible by default — never require an allowlist update. This is the
    literal 'genuine future ingested projects appear automatically'
    requirement: the predicate is a denylist of KNOWN fixtures, not an
    allowlist of known-real titles."""
    for title in ("A Brand New Feature Nobody Has Seen Yet", "Untitled Thriller Project 2027"):
        assert _is_producer_visible(title) is True


def test_is_producer_visible_never_excludes_a_null_or_empty_title():
    assert _is_producer_visible(None) is True
    assert _is_producer_visible("") is True


# ── Integration — the real DB, the real endpoint function ───────────────

async def test_list_projects_default_excludes_every_known_fixture(db: AsyncSession):
    org_id = settings.CURRENT_ORGANIZATION_ID
    if not org_id:
        pytest.skip("settings.CURRENT_ORGANIZATION_ID not configured in this environment")
    cards = await list_projects(organization_id=org_id, include_fixtures=False, db=db)
    titles = {c.title for c in cards}
    assert titles, "expected at least the 4 real productions"
    assert titles == REAL_PRODUCTION_TITLES, (
        f"default producer-facing listing must be EXACTLY the 4 real productions, got: {sorted(titles)}"
    )
    for c in cards:
        assert not c.title.startswith("AUDIT_CONTROL_")


async def test_list_projects_include_fixtures_reaches_the_full_set(db: AsyncSession):
    """The explicit escape hatch for audit tooling — nothing is deleted,
    everything remains reachable on request."""
    org_id = settings.CURRENT_ORGANIZATION_ID
    if not org_id:
        pytest.skip("settings.CURRENT_ORGANIZATION_ID not configured in this environment")
    default_cards = await list_projects(organization_id=org_id, include_fixtures=False, db=db)
    all_cards = await list_projects(organization_id=org_id, include_fixtures=True, db=db)
    assert len(all_cards) > len(default_cards), (
        "include_fixtures=True must reach strictly more rows than the default producer-facing listing"
    )
    all_titles = {c.title for c in all_cards}
    assert REAL_PRODUCTION_TITLES <= all_titles, "the 4 real productions must still be present when fixtures are included"
