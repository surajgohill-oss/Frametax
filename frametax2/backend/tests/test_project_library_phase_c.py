"""
Project Library Phase C — Little Utopia persistence migration tests.

Unlike Phase A/B (which build/verify throwaway fixture rows inside a rolled-
back transaction), Phase C's subject IS the one real, permanent Organization/
Project migrated by alembic/versions/0063_migrate_little_utopia.py. These
tests are read-only verification against that real data — there is nothing
to roll back, and nothing here may mutate it.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_alias import ProjectAlias
from app.models.library_document import Document, DocumentVersion, DocumentVersionSource
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.screenplay import ScreenplayDocument
from app.models.project_asset import ProjectAsset
from app.models.project_fact import ProjectFact
from app.models.project_person import ProjectPerson
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.enums import ProjectLifecycle

ORG_SLUG = "mind-the-story-media"
PROJECT_TITLE = "The Little Utopia"


@pytest.fixture
async def db():
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.title == PROJECT_TITLE))
    row = result.scalar_one_or_none()
    assert row is not None, "Phase C migration (0063) has not been applied — Little Utopia project not found"
    return row


async def test_exactly_one_real_organization_and_project(db: AsyncSession, project: Project):
    org_count = (await db.execute(
        select(func.count()).select_from(Organization).where(Organization.slug == ORG_SLUG)
    )).scalar_one()
    assert org_count == 1

    project_count = (await db.execute(
        select(func.count()).select_from(Project).where(Project.title == PROJECT_TITLE)
    )).scalar_one()
    assert project_count == 1

    org = (await db.execute(select(Organization).where(Organization.id == project.organization_id))).scalar_one()
    assert org.slug == ORG_SLUG


async def test_project_core_fields(project: Project):
    assert project.lifecycle == ProjectLifecycle.EVALUATION.value
    assert float(project.total_budget_usd) == pytest.approx(4364393.00, abs=0.01)
    assert project.target_shoot_year == 2026
    assert project.leading_structure_id is not None


async def test_project_alias(db: AsyncSession, project: Project):
    alias = (await db.execute(
        select(ProjectAlias).where(ProjectAlias.project_id == project.id)
    )).scalar_one_or_none()
    assert alias is not None
    assert alias.alias == "The Boat"


async def test_documents_versions_and_sources(db: AsyncSession, project: Project):
    docs = (await db.execute(select(Document).where(Document.project_id == project.id))).scalars().all()
    assert len(docs) == 5

    doc_ids = [d.id for d in docs]
    versions = (await db.execute(
        select(DocumentVersion).where(DocumentVersion.document_id.in_(doc_ids))
    )).scalars().all()
    assert len(versions) == 6

    version_ids = [v.id for v in versions]
    sources = (await db.execute(
        select(DocumentVersionSource).where(DocumentVersionSource.document_version_id.in_(version_ids))
    )).scalars().all()
    assert len(sources) == 10

    # Screenplay checksum spot-check — confirms the migrated version row
    # points at the exact independently-verified file, not a placeholder.
    screenplay_version = next(
        (v for v in versions if v.checksum_sha256 == "c5213c9ced713e071a21647a4c08cec7914f18cf6bdd1432c33d4c00ff4038c0"),
        None,
    )
    assert screenplay_version is not None
    assert screenplay_version.file_size == 1250024


async def test_budget_document_linked_with_line_items(db: AsyncSession, project: Project):
    budget_doc = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalar_one_or_none()
    assert budget_doc is not None
    assert budget_doc.document_version_id is not None

    line_count = (await db.execute(
        select(func.count()).select_from(BudgetLineItem).where(BudgetLineItem.budget_document_id == budget_doc.id)
    )).scalar_one()
    assert line_count == 44


async def test_screenplay_document_linked(db: AsyncSession, project: Project):
    screenplay_doc = (await db.execute(
        select(ScreenplayDocument).where(ScreenplayDocument.project_id == project.id)
    )).scalar_one_or_none()
    assert screenplay_doc is not None
    assert screenplay_doc.document_version_id is not None


async def test_project_asset_artwork(db: AsyncSession, project: Project):
    asset = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id)
    )).scalar_one_or_none()
    assert asset is not None
    assert asset.is_master is True


async def test_project_facts_with_provenance(db: AsyncSession, project: Project):
    facts = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == project.id))).scalars().all()
    assert len(facts) == 11
    by_key = {f.fact_key: f for f in facts}

    assert by_key["gross_budget_usd"].value == "4364393.0" or float(by_key["gross_budget_usd"].value) == pytest.approx(4364393.0, abs=0.01)
    assert by_key["writer_name"].value == "Clara Salaman"
    assert by_key["director_name"].value == "Kim Farrant"
    # Genuinely unknown fact — never fabricated.
    assert by_key["lead_cast_nationality"].value is None
    assert by_key["lead_cast_nationality"].review_status == "pending"

    for fact in facts:
        assert fact.source_type == "recovered_demo_state"


async def test_project_people(db: AsyncSession, project: Project):
    people = (await db.execute(
        select(ProjectPerson).where(ProjectPerson.project_id == project.id)
    )).scalars().all()
    assert len(people) == 4
    roles = {p.role for p in people}
    assert "writer" in roles
    assert "director" in roles
    assert sum(1 for p in people if p.role == "producer") == 2


async def test_project_location_requirements(db: AsyncSession, project: Project):
    # Scoped to category_key IS NULL: the Phase C closeout (0064) added
    # category-override rows to this same table, so an unscoped count no
    # longer means "the migrated script requirements".
    locations = (await db.execute(
        select(ProjectLocationRequirement).where(
            ProjectLocationRequirement.project_id == project.id,
            ProjectLocationRequirement.category_key.is_(None),
        )
    )).scalars().all()
    assert len(locations) == 4
    descriptions = {loc.description for loc in locations}
    assert any("Marine" in d or "open-water" in d.lower() for d in descriptions)


async def test_production_structure_and_leading_selection(db: AsyncSession, project: Project):
    structures = (await db.execute(
        select(ProductionStructure).where(ProductionStructure.project_id == project.id)
    )).scalars().all()
    assert len(structures) == 1
    structure = structures[0]
    assert project.leading_structure_id == structure.id

    calc = (await db.execute(
        select(StructureCalculationResult).where(StructureCalculationResult.structure_id == structure.id)
    )).scalar_one_or_none()
    assert calc is not None
    assert float(calc.total_budget_usd) == pytest.approx(4364393.00, abs=0.01)
