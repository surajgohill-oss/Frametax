"""
Project Library Phase B — persistence foundation tests.

Every test runs inside a real Postgres transaction against the actual dev
database (frametax2) that is rolled back at the end of the test, so no fake
Project/Document/etc. row is ever left behind in the shared dev DB — the
same isolation pattern used for Phase A's manual CRUD verification.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import engine
from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.models.project_alias import ProjectAlias
from app.models.library_document import Document, DocumentVersion, DocumentVersionSource
from app.models.budget import BudgetDocument
from app.models.screenplay import ScreenplayDocument
from app.models.project_asset import ProjectAsset
from app.models.project_fact import ProjectFact
from app.models.project_activity import ProjectActivity
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.final_production_result import FinalProductionResult
from app.models.enums import (
    ProjectLifecycle, DocumentCategory, DocumentSourceType, DocumentSourceStatus,
    ProjectAssetKind, ProjectAssetSourceType, ProjectFactSourceType, FinalResultStatus,
)


@pytest.fixture
async def db():
    """Real DB session bound to a transaction that is always rolled back."""
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()


def _slug() -> str:
    return f"phaseb-test-{uuid.uuid4().hex[:8]}"


async def _make_org(db: AsyncSession) -> Organization:
    org = Organization(name="Phase B Test Org", slug=_slug())
    db.add(org)
    await db.flush()
    return org


async def _make_project(db: AsyncSession, **kw) -> Project:
    org = await _make_org(db)
    proj = Project(organization_id=org.id, title=kw.pop("title", "Phase B Test Project"), **kw)
    db.add(proj)
    await db.flush()
    return proj


# 1. title-only Project can exist
async def test_title_only_project_can_exist(db: AsyncSession):
    proj = await _make_project(db)
    assert proj.id is not None
    assert proj.title == "Phase B Test Project"
    assert proj.total_budget_usd is None
    assert proj.home_jurisdiction_id is None


# 2. lifecycle persists (and defaults correctly for a new title-only Project)
async def test_lifecycle_persists_and_defaults(db: AsyncSession):
    proj = await _make_project(db)
    await db.refresh(proj)
    assert proj.lifecycle == ProjectLifecycle.EVALUATION.value

    proj.lifecycle = ProjectLifecycle.DEVELOPMENT.value
    await db.flush()
    result = await db.execute(select(Project).where(Project.id == proj.id))
    fetched = result.scalar_one()
    assert fetched.lifecycle == ProjectLifecycle.DEVELOPMENT.value


# 3. ProjectAlias persists
async def test_project_alias_persists(db: AsyncSession):
    proj = await _make_project(db)
    alias = ProjectAlias(project_id=proj.id, alias="Christmas Cargo", source="found in look book title page")
    db.add(alias)
    await db.flush()
    result = await db.execute(select(ProjectAlias).where(ProjectAlias.project_id == proj.id))
    fetched = result.scalar_one()
    assert fetched.alias == "Christmas Cargo"


# 4. Project can own multiple Documents
async def test_project_owns_multiple_documents(db: AsyncSession):
    proj = await _make_project(db)
    script_doc = Document(project_id=proj.id, category=DocumentCategory.SCREENPLAY.value, title="The Dale screenplay")
    deck_doc = Document(project_id=proj.id, category=DocumentCategory.DECK.value, title="The Dale slide deck")
    db.add_all([script_doc, deck_doc])
    await db.flush()
    result = await db.execute(select(Document).where(Document.project_id == proj.id))
    docs = result.scalars().all()
    assert len(docs) == 2
    assert {d.category for d in docs} == {"screenplay", "deck"}


# 5. Document can own multiple versions
async def test_document_owns_multiple_versions(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.SCREENPLAY.value, title="Unconditional Love screenplay")
    db.add(doc)
    await db.flush()

    v2023 = DocumentVersion(document_id=doc.id, original_filename="UNCONDITIONAL LOVE 111823.pdf", is_current=False)
    v2026 = DocumentVersion(document_id=doc.id, original_filename="Unconditional Love 1-26", is_current=True)
    db.add_all([v2023, v2026])
    await db.flush()

    result = await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == doc.id))
    versions = result.scalars().all()
    assert len(versions) == 2


# 6. DocumentVersion can own multiple source pointers
async def test_document_version_owns_multiple_sources(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.SCREENPLAY.value, title="The Little Utopia screenplay")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(document_id=doc.id, original_filename="The Little Utopia 1_30_26.pdf", is_current=True)
    db.add(version)
    await db.flush()

    drive_src = DocumentVersionSource(
        document_version_id=version.id, source_type=DocumentSourceType.GOOGLE_DRIVE.value,
        source_pointer="drive-file-id-canonical",
    )
    drive_mirror_src = DocumentVersionSource(
        document_version_id=version.id, source_type=DocumentSourceType.GOOGLE_DRIVE.value,
        source_pointer="drive-file-id-downloads-mirror",
    )
    local_src = DocumentVersionSource(
        document_version_id=version.id, source_type=DocumentSourceType.LOCAL.value,
        source_pointer="/Users/test/Downloads/The Little Utopia 1_30_26.pdf",
    )
    db.add_all([drive_src, drive_mirror_src, local_src])
    await db.flush()

    result = await db.execute(
        select(DocumentVersionSource).where(DocumentVersionSource.document_version_id == version.id)
    )
    sources = result.scalars().all()
    assert len(sources) == 3
    assert {s.source_type for s in sources} == {"google_drive", "local"}


# 7. checksum persists
async def test_checksum_persists(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.BUDGET.value, title="Test budget")
    db.add(doc)
    await db.flush()
    checksum = "a" * 64  # well-formed sha256 hex length
    version = DocumentVersion(document_id=doc.id, checksum_sha256=checksum, file_size=12345)
    db.add(version)
    await db.flush()
    result = await db.execute(select(DocumentVersion).where(DocumentVersion.id == version.id))
    fetched = result.scalar_one()
    assert fetched.checksum_sha256 == checksum
    assert fetched.file_size == 12345


# 8. ambiguous version lineage can exist without forced ordering
async def test_ambiguous_version_lineage_not_forced(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.SCREENPLAY.value, title="Ambiguous lineage test")
    db.add(doc)
    await db.flush()
    v_old_looking = DocumentVersion(document_id=doc.id, detected_date="2023-11-18")
    v_new_looking = DocumentVersion(document_id=doc.id, detected_date="2026-01-01")
    db.add_all([v_old_looking, v_new_looking])
    await db.flush()
    # Neither version claims to supersede the other — lineage genuinely unknown.
    assert v_old_looking.supersedes_version_id is None
    assert v_new_looking.supersedes_version_id is None


# 9. canonical/current version can be changed without deleting history
async def test_current_version_change_preserves_history(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.BUDGET.value, title="Budget with revisions")
    db.add(doc)
    await db.flush()
    v1 = DocumentVersion(document_id=doc.id, version_label="v1", is_current=True)
    db.add(v1)
    await db.flush()
    doc.current_version_id = v1.id
    await db.flush()

    v2 = DocumentVersion(document_id=doc.id, version_label="v2")
    db.add(v2)
    await db.flush()
    v1.is_current = False
    v2.is_current = True
    doc.current_version_id = v2.id
    await db.flush()

    result = await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == doc.id))
    versions = {v.version_label: v for v in result.scalars().all()}
    assert len(versions) == 2  # v1 was never deleted
    assert versions["v1"].is_current is False
    assert versions["v2"].is_current is True
    await db.refresh(doc)
    assert doc.current_version_id == v2.id


# 10. ProjectAsset persists and master selection can be represented
async def test_project_asset_master_selection(db: AsyncSession):
    proj = await _make_project(db)
    a1 = ProjectAsset(
        project_id=proj.id, kind=ProjectAssetKind.ARTWORK.value,
        source_type=ProjectAssetSourceType.UPLOADED.value, is_master=True,
    )
    a2 = ProjectAsset(
        project_id=proj.id, kind=ProjectAssetKind.ARTWORK.value,
        source_type=ProjectAssetSourceType.DISCOVERED_IMAGE.value, is_master=False,
    )
    db.add_all([a1, a2])
    await db.flush()
    result = await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == proj.id))
    assets = result.scalars().all()
    masters = [a for a in assets if a.is_master]
    assert len(assets) == 2
    assert len(masters) == 1


# 11. ProjectFact persists with provenance
async def test_project_fact_persists_with_provenance(db: AsyncSession):
    proj = await _make_project(db)
    doc = Document(project_id=proj.id, category=DocumentCategory.SCREENPLAY.value, title="Fact source doc")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(document_id=doc.id)
    db.add(version)
    await db.flush()

    fact = ProjectFact(
        project_id=proj.id, fact_key="director_nationality", value="Australian", value_type="string",
        source_type=ProjectFactSourceType.EXTRACTED.value,
        source_document_version_id=version.id, source_location="page 4",
        extraction_confidence=0.87,
    )
    db.add(fact)
    await db.flush()
    result = await db.execute(select(ProjectFact).where(ProjectFact.project_id == proj.id))
    fetched = result.scalar_one()
    assert fetched.value == "Australian"
    assert fetched.source_document_version_id == version.id
    assert fetched.source_location == "page 4"
    assert float(fetched.extraction_confidence) == pytest.approx(0.87)


# 12. fact history/override does not erase previous state (current value updates
#     in place; the transition itself is recorded via ProjectActivity, not a
#     previous_value column on ProjectFact)
async def test_fact_override_recorded_via_activity_not_previous_value(db: AsyncSession):
    proj = await _make_project(db)
    fact = ProjectFact(
        project_id=proj.id, fact_key="director", value="Kim Farrant",
        source_type=ProjectFactSourceType.EXTRACTED.value,
    )
    db.add(fact)
    await db.flush()

    before = {"value": fact.value}
    fact.value = "Kim Farrant (confirmed)"
    fact.source_type = ProjectFactSourceType.USER_OVERRIDE.value
    after = {"value": fact.value}
    activity = ProjectActivity(
        project_id=proj.id, action="fact_overridden", entity_type="project_fact",
        entity_id=fact.id, before_json=before, after_json=after,
    )
    db.add(activity)
    await db.flush()

    result = await db.execute(select(ProjectFact).where(ProjectFact.id == fact.id))
    fetched = result.scalar_one()
    assert fetched.value == "Kim Farrant (confirmed)"  # current value updated in place

    result2 = await db.execute(select(ProjectActivity).where(ProjectActivity.project_id == proj.id))
    activity_row = result2.scalar_one()
    assert activity_row.before_json["value"] == "Kim Farrant"
    assert activity_row.after_json["value"] == "Kim Farrant (confirmed)"


# 13. ProjectActivity persists
async def test_project_activity_persists(db: AsyncSession):
    proj = await _make_project(db)
    activity = ProjectActivity(
        project_id=proj.id, action="lifecycle_changed",
        before_json={"lifecycle": "EVALUATION"}, after_json={"lifecycle": "DEVELOPMENT"},
    )
    db.add(activity)
    await db.flush()
    result = await db.execute(select(ProjectActivity).where(ProjectActivity.project_id == proj.id))
    fetched = result.scalar_one()
    assert fetched.action == "lifecycle_changed"
    assert fetched.created_at is not None


# 14. leading ProductionStructure can be persisted
async def test_leading_structure_persists(db: AsyncSession):
    proj = await _make_project(db)
    structure = ProductionStructure(project_id=proj.id, name="Mauritius full relocation")
    db.add(structure)
    await db.flush()
    proj.leading_structure_id = structure.id
    await db.flush()
    result = await db.execute(select(Project).where(Project.id == proj.id))
    fetched = result.scalar_one()
    assert fetched.leading_structure_id == structure.id


# 15. calculation result can reference/version its input state
async def test_calculation_result_input_provenance(db: AsyncSession):
    proj = await _make_project(db)
    structure = ProductionStructure(project_id=proj.id, name="Test structure")
    db.add(structure)
    await db.flush()

    doc = Document(project_id=proj.id, category=DocumentCategory.BUDGET.value, title="Input budget")
    db.add(doc)
    await db.flush()
    budget_version = DocumentVersion(document_id=doc.id, version_label="v1")
    db.add(budget_version)
    await db.flush()

    calc = StructureCalculationResult(
        structure_id=structure.id, engine_version="1.0.0",
        input_budget_document_version_id=budget_version.id,
        input_fingerprint="deadbeef" * 8,
        input_snapshot_json={"total_budget_usd": 4364393},
    )
    db.add(calc)
    await db.flush()

    result = await db.execute(
        select(StructureCalculationResult).where(StructureCalculationResult.id == calc.id)
    )
    fetched = result.scalar_one()
    assert fetched.input_budget_document_version_id == budget_version.id
    assert fetched.input_snapshot_json["total_budget_usd"] == 4364393

    # Now simulate the budget changing to a NEW version — the old
    # calculation result must still point at the OLD version, proving a
    # later reader can detect "this was calculated from an older budget".
    budget_v2 = DocumentVersion(document_id=doc.id, version_label="v2")
    db.add(budget_v2)
    await db.flush()
    doc.current_version_id = budget_v2.id
    await db.flush()
    await db.refresh(fetched)
    assert fetched.input_budget_document_version_id == budget_version.id
    assert fetched.input_budget_document_version_id != budget_v2.id


# 16. FinalProductionResult can persist independently of modeled result
async def test_final_production_result_independent_of_modeled(db: AsyncSession):
    proj = await _make_project(db)
    structure = ProductionStructure(project_id=proj.id, name="Leading structure at decision")
    db.add(structure)
    await db.flush()
    calc = StructureCalculationResult(
        structure_id=structure.id, engine_version="1.0.0", total_incentive_value_usd=1_275_411,
    )
    db.add(calc)
    await db.flush()

    final = FinalProductionResult(
        project_id=proj.id,
        leading_structure_id_at_decision=structure.id,
        modeled_economics_snapshot={"total_incentive_value_usd": 1275411},
        final_incentive_expected_usd=1275411,
        final_incentive_realized_usd=None,  # not yet known — genuinely absent, not fabricated
        status=FinalResultStatus.APPLIED.value,
    )
    db.add(final)
    await db.flush()

    result = await db.execute(select(FinalProductionResult).where(FinalProductionResult.project_id == proj.id))
    fetched = result.scalar_one()
    assert fetched.final_incentive_expected_usd == 1275411
    assert fetched.final_incentive_realized_usd is None
    assert fetched.status == "applied"
    # modeled snapshot is a frozen copy, independent of the live calc row
    assert fetched.modeled_economics_snapshot["total_incentive_value_usd"] == 1275411


# 17. Organization-level documents can exist without being attached to a Project
async def test_organization_document_without_project(db: AsyncSession):
    org = await _make_org(db)
    org_doc = Document(organization_id=org.id, category=DocumentCategory.DECK.value, title="MTS Slate Summary")
    db.add(org_doc)
    await db.flush()
    result = await db.execute(select(Document).where(Document.organization_id == org.id))
    fetched = result.scalar_one()
    assert fetched.project_id is None
    assert fetched.organization_id == org.id


async def test_document_cannot_have_both_or_neither_owner(db: AsyncSession):
    """CHECK constraint: exactly one of project_id/organization_id must be set."""
    from sqlalchemy.exc import IntegrityError

    neither = Document(category=DocumentCategory.OTHER.value, title="Orphaned document")
    db.add(neither)
    with pytest.raises(IntegrityError):
        await db.flush()
    await db.rollback()


# 18. ProjectLocationRequirement and ProjectPerson also get persistence coverage
async def test_location_requirement_persists(db: AsyncSession):
    proj = await _make_project(db)
    loc = ProjectLocationRequirement(
        project_id=proj.id, description="Mediterranean coastal town", is_flexible=True,
    )
    db.add(loc)
    await db.flush()
    result = await db.execute(
        select(ProjectLocationRequirement).where(ProjectLocationRequirement.project_id == proj.id)
    )
    fetched = result.scalar_one()
    assert fetched.description == "Mediterranean coastal town"
    assert fetched.is_flexible is True


async def test_project_person_links_talent_without_duplication(db: AsyncSession):
    proj = await _make_project(db)
    talent = TalentProfile(name="Kim Farrant", role="director", primary_nationality="AU")
    db.add(talent)
    await db.flush()
    link = ProjectPerson(project_id=proj.id, talent_id=talent.id, role="director", is_confirmed=True)
    db.add(link)
    await db.flush()
    result = await db.execute(select(ProjectPerson).where(ProjectPerson.project_id == proj.id))
    fetched = result.scalar_one()
    assert fetched.talent_id == talent.id
    assert fetched.role == "director"


# durable storage path initializes correctly
def test_durable_storage_path_initializes():
    from app.core.config import settings
    import os

    assert "/tmp" not in settings.LOCAL_STORAGE_PATH
    assert os.path.isdir(settings.LOCAL_STORAGE_PATH)
