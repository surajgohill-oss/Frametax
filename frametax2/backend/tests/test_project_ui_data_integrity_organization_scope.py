"""
PROJECT_UI_DATA_INTEGRITY, Phase 3 whitelist item 2 -- organization scope.

Confirmed defect: GET /api/v1/projects with no organization context
returned every project across every organization (245 of 329 real rows
were one-off AUDIT_CONTROL_* fixture organizations, alongside the real
production company's own 4 real productions). list_projects() must now
fail closed when no organization context resolves, and must scope
strictly to the active organization when one does.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.projects import list_projects
from app.core.config import settings
from app.db.session import engine

_MIND_THE_STORY_MEDIA_ORG_ID = "11381771-5b1c-4980-9117-e3e47a4cb354"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_missing_organization_context_fails_closed_never_returns_every_organization(db, monkeypatch):
    monkeypatch.setattr(settings, "CURRENT_ORGANIZATION_ID", "")
    result = await list_projects(organization_id=None, db=db)
    assert result == [], "no organization context must fail closed to an empty list, never every organization's projects"


async def test_active_organization_returns_only_its_own_projects(db, monkeypatch):
    monkeypatch.setattr(settings, "CURRENT_ORGANIZATION_ID", _MIND_THE_STORY_MEDIA_ORG_ID)
    result = await list_projects(organization_id=None, db=db)
    assert result, "the real organization must return its own real projects"
    titles = {p.title for p in result}
    assert {"The Little Utopia", "Bad Hombres", "F#K Valentine's Day", "Lips Like Sugar"}.issubset(titles)
    assert all(p.organization_name == "Mind The Story Media" for p in result), (
        "every returned project must belong to the active organization -- never a project from an "
        "AUDIT_CONTROL fixture organization leaking through"
    )
