"""
Fresh Project Ingestion Acceptance, Phase 1 — is_served_production identity fix.

GET /projects/{id}/record's "is_served_production" field (consumed by
ProjectRecord.jsx to decide between a clean "Enter Workspace" state and a
lesser "Re-run Evaluation" + secondary-button state) was hardcoded to
`project.title == PRODUCTION_NAME` (Little Utopia only) -- confirmed via
runtime trace against a real second project (F#K Valentine's Day, which
evaluates successfully with 135 priced candidates but was permanently
denied the same "served" UI state LU gets). Fixed to the same generic
`structure_count > 0` condition evaluation_begun already uses -- no
project-specific branch.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.api.v1.projects import get_project_record


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Served-Identity Test Org", slug=f"served-identity-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(
        id=uuid.uuid4(), organization_id=org.id,
        title=f"Served Identity Test Project {uuid.uuid4().hex[:8]}",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.commit()


async def test_never_evaluated_project_is_not_served(db: AsyncSession, project: Project):
    record = await get_project_record(str(project.id), db=db)
    assert record["project"]["is_served_production"] is False
    assert record["analysis"]["evaluation_begun"] is False


async def test_evaluated_non_lu_project_becomes_served_generically(db: AsyncSession, project: Project):
    """The exact defect: a real, non-Little-Utopia project that HAS
    produced real ProductionStructure/StructureCalculationResult rows
    must be reported as served -- never gated on the project's title."""
    structure = ProductionStructure(id=uuid.uuid4(), project_id=project.id, name="Test structure")
    db.add(structure)
    await db.flush()
    result = StructureCalculationResult(
        id=uuid.uuid4(), structure_id=structure.id, engine_version="test-engine-1.0.0",
    )
    db.add(result)
    await db.commit()

    record = await get_project_record(str(project.id), db=db)
    assert record["project"]["title"] != "The Little Utopia"
    assert record["analysis"]["evaluation_begun"] is True
    assert record["project"]["is_served_production"] is True, (
        "is_served_production must follow real evaluation state (structure_count > 0), "
        "never a hardcoded title match against a single named production"
    )
