"""
Project CRUD endpoints, plus the Project Library / Project Record read
surface (Phase D): a Library grid card needs artwork + material
completeness beyond plain ProjectRead; a Record needs a combined view
across documents, people, facts, locations, structures and activity that
no single existing table read provides.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.models.project import Project
from app.models.organization import Organization
from app.models.library_document import Document, DocumentVersion
from app.models.project_asset import ProjectAsset
from app.models.project_alias import ProjectAlias
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.models.project_fact import ProjectFact
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.project_activity import ProjectActivity
from app.models.production import ProductionStructure
from app.demo.little_utopia_state import PRODUCTION_NAME
from app.schemas.project import MaterialsCompleteness, ProjectCard, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

# The four CORE categories a Library card / Record "at a glance" answer
# is scoped to — deliberately not the full DocumentCategory taxonomy.
_CORE_CATEGORIES = {"screenplay": "script", "budget": "budget", "deck": "deck", "schedule": "schedule"}


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = Project(
        id=uuid.uuid4(),
        **body.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectCard])
async def list_projects(
    organization_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectCard]:
    """Project Library grid — every real persisted Project, each carrying
    just what a card needs: artwork, and completeness across the four
    CORE material categories. No NPC, no scenario economics — those are
    optimizer output and don't belong in a durable-corpus summary."""
    stmt = select(Project)
    if organization_id:
        stmt = stmt.where(Project.organization_id == organization_id)
    stmt = stmt.order_by(Project.updated_at.desc())
    projects = list((await db.execute(stmt)).scalars().all())
    if not projects:
        return []

    project_ids = [p.id for p in projects]
    org_rows = (await db.execute(
        select(Organization.id, Organization.name).where(
            Organization.id.in_({p.organization_id for p in projects})
        )
    )).all()
    org_names = {oid: name for oid, name in org_rows}

    doc_rows = (await db.execute(
        select(Document.project_id, Document.category).where(
            Document.project_id.in_(project_ids), Document.category.in_(_CORE_CATEGORIES)
        )
    )).all()
    categories_by_project: dict[uuid.UUID, set[str]] = {}
    for pid, category in doc_rows:
        categories_by_project.setdefault(pid, set()).add(category)

    artwork_rows = (await db.execute(
        select(ProjectAsset.project_id).where(
            ProjectAsset.project_id.in_(project_ids), ProjectAsset.is_master.is_(True)
        )
    )).all()
    has_artwork = {pid for (pid,) in artwork_rows}

    cards: list[ProjectCard] = []
    for p in projects:
        cats = categories_by_project.get(p.id, set())
        cards.append(ProjectCard(
            **ProjectRead.model_validate(p).model_dump(),
            organization_name=org_names.get(p.organization_id),
            artwork_url=f"/api/v1/projects/{p.id}/artwork" if p.id in has_artwork else None,
            materials=MaterialsCompleteness(
                script="screenplay" in cats, budget="budget" in cats,
                deck="deck" in cats, schedule="schedule" in cats,
            ),
        ))
    return cards


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


@router.get("/{project_id}/artwork")
async def get_project_artwork(project_id: str, db: AsyncSession = Depends(get_db)) -> FileResponse:
    """Serves the master ProjectAsset's cached bytes. Deliberately scoped
    to files this project's own master-artwork row points at — never a
    general file server over LOCAL_STORAGE_PATH."""
    asset = (await db.execute(
        select(ProjectAsset).where(
            ProjectAsset.project_id == project_id, ProjectAsset.is_master.is_(True),
        )
    )).scalars().first()
    if asset is None or not asset.storage_path:
        raise HTTPException(status_code=404, detail="No master artwork for this project")
    full_path = Path(settings.LOCAL_STORAGE_PATH) / asset.storage_path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="Artwork file missing from storage")
    return FileResponse(full_path)


@router.get("/{project_id}/documents/{version_id}/file")
async def get_document_version_file(
    project_id: str, version_id: str, db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Serves a DocumentVersion's cached bytes — completes the read path
    for the canonical Document/DocumentVersion architecture Phase B built
    and Phase C populated, which had no viewing capability at all before
    this. Deliberately scoped: the version must belong to a Document
    owned by THIS project, never an open-ended file server."""
    version = (await db.execute(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(DocumentVersion.id == version_id, Document.project_id == project_id)
    )).scalar_one_or_none()
    if version is None or not version.storage_path:
        raise HTTPException(status_code=404, detail="Document version not found for this project")
    full_path = Path(settings.LOCAL_STORAGE_PATH) / version.storage_path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="Document file missing from storage")
    return FileResponse(full_path, filename=version.original_filename or full_path.name)


@router.get("/{project_id}/record")
async def get_project_record(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Combined Project Record payload — identity, materials, known
    production information, analysis state, and recent activity, in one
    fetch (the same combined-fetch convention useCineGlobe.js already
    uses). Read-only; never mutates, never triggers the optimizer."""
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    organization = (await db.execute(
        select(Organization).where(Organization.id == project.organization_id)
    )).scalar_one_or_none()

    aliases = (await db.execute(
        select(ProjectAlias).where(ProjectAlias.project_id == project.id)
    )).scalars().all()

    assets = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id).order_by(ProjectAsset.created_at)
    )).scalars().all()
    master = next((a for a in assets if a.is_master), None)

    docs = (await db.execute(
        select(Document).where(Document.project_id == project.id).order_by(Document.category)
    )).scalars().all()
    doc_ids = [d.id for d in docs]
    versions = (
        (await db.execute(
            select(DocumentVersion).where(DocumentVersion.document_id.in_(doc_ids))
        )).scalars().all()
        if doc_ids else []
    )
    versions_by_doc: dict[uuid.UUID, list[DocumentVersion]] = {}
    for v in versions:
        versions_by_doc.setdefault(v.document_id, []).append(v)

    def _document_payload(doc: Document) -> dict[str, Any]:
        doc_versions = versions_by_doc.get(doc.id, [])
        current = next((v for v in doc_versions if v.is_current), None) or (
            doc_versions[0] if doc_versions else None
        )
        return {
            "category": doc.category,
            "title": doc.title,
            "current_version": (
                {
                    "id": str(current.id),
                    "filename": current.original_filename,
                    "version_label": current.version_label,
                    "file_size": current.file_size,
                    "detected_date": current.detected_date,
                    "file_url": (
                        f"/api/v1/projects/{project_id}/documents/{current.id}/file"
                        if current.storage_path else None
                    ),
                }
                if current else None
            ),
            "version_count": len(doc_versions),
            # No supersedes_version_id relationship connects the versions
            # in a genuinely ambiguous case — never guessed at, see the
            # Phase C migration notes for Little Utopia's own deck.
            "current_unresolved": len(doc_versions) > 1 and not any(
                v.supersedes_version_id is not None for v in doc_versions
            ),
        }

    categories_present = {d.category for d in docs}
    materials_core = MaterialsCompleteness(
        script="screenplay" in categories_present, budget="budget" in categories_present,
        deck="deck" in categories_present, schedule="schedule" in categories_present,
    )

    people_rows = (
        await db.execute(
            select(ProjectPerson, TalentProfile)
            .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
            .where(ProjectPerson.project_id == project.id)
        )
    ).all()

    facts = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id).order_by(ProjectFact.fact_key)
    )).scalars().all()

    locations = (await db.execute(
        select(ProjectLocationRequirement).where(
            ProjectLocationRequirement.project_id == project.id,
            ProjectLocationRequirement.category_key.is_(None),
        )
    )).scalars().all()

    structure_count = (await db.execute(
        select(func.count()).select_from(ProductionStructure).where(ProductionStructure.project_id == project.id)
    )).scalar_one()
    leading_structure = None
    if project.leading_structure_id:
        leading_structure = (await db.execute(
            select(ProductionStructure).where(ProductionStructure.id == project.leading_structure_id)
        )).scalar_one_or_none()

    activity = (await db.execute(
        select(ProjectActivity).where(ProjectActivity.project_id == project.id)
        .order_by(ProjectActivity.created_at.desc()).limit(20)
    )).scalars().all()

    return {
        "project": {
            "id": str(project.id), "title": project.title, "logline": project.logline,
            "genre": project.genre, "format": project.format, "lifecycle": project.lifecycle,
            "total_budget_usd": project.total_budget_usd, "target_shoot_year": project.target_shoot_year,
            "notes": project.notes,
            # Whether /api/v1/cineglobe/* (Overview/Workspace/Scenarios —
            # the actual evaluation engine) currently serves THIS project.
            # Only one project can be true today (the engine is still
            # single-production); told to the frontend rather than left
            # for it to guess by matching titles across two layers.
            "is_served_production": project.title == PRODUCTION_NAME,
        },
        "organization": {"id": str(organization.id), "name": organization.name} if organization else None,
        "aliases": [a.alias for a in aliases],
        "artwork": {
            "master": (
                {
                    "id": str(master.id), "url": f"/api/v1/projects/{project.id}/artwork",
                    "source_type": master.source_type,
                }
                if master else None
            ),
            # Reserved for a future candidate picker (Phase D explicitly
            # defers artwork extraction) — every persisted asset is
            # already returned so the Record has a sensible place to
            # eventually render them, without a second fetch.
            "candidates": [
                {"id": str(a.id), "url": f"/api/v1/projects/{project.id}/artwork", "is_master": a.is_master,
                 "source_type": a.source_type}
                for a in assets
            ],
        },
        "materials_core": materials_core.model_dump(),
        "documents": [_document_payload(d) for d in docs],
        "people": [
            {"role": pp.role, "name": tp.name, "nationality": tp.primary_nationality,
             "residency": (tp.known_residencies or [{}])[0].get("jurisdiction_code") if tp.known_residencies else None}
            for pp, tp in people_rows
        ],
        "facts": [
            {"fact_key": f.fact_key, "value": f.value, "source_type": f.source_type, "review_status": f.review_status}
            for f in facts
        ],
        "locations": [
            {"description": l.description, "is_flexible": l.is_flexible, "notes": l.notes}
            for l in locations
        ],
        "analysis": {
            "evaluation_begun": structure_count > 0,
            "structures_available": structure_count,
            "leading_structure_name": leading_structure.name if leading_structure else None,
        },
        "activity": [
            {"action": a.action, "entity_type": a.entity_type, "actor": a.actor, "created_at": a.created_at.isoformat()}
            for a in activity
        ],
    }


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Partial update. Phase C wiring: this is how the shared Production
    Stage control and "Set as Leading" persist lifecycle/leading_structure_id
    against the real Project row instead of frontend-only state. This
    endpoint itself never changes lifecycle on the engine's behalf — it
    only writes whatever the caller (a human action) explicitly supplies.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row
