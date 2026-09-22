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
from sqlalchemy import delete, func, select
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
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.budget import BudgetDocument
from app.demo.little_utopia_state import PRODUCTION_NAME
from app.schemas.project import MaterialsCompleteness, ProjectCard, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

# The four CORE categories a Library card / Record "at a glance" answer
# is scoped to — deliberately not the full DocumentCategory taxonomy.
_CORE_CATEGORIES = {"screenplay": "script", "budget": "budget", "deck": "deck", "schedule": "schedule"}

# PROJECT_LIBRARY_FIXTURE_EXCLUSION (2026-09-22) — ROOT CAUSE: the
# `Project.organization_id` scoping above (PROJECT_UI_DATA_INTEGRITY) is
# necessary but, confirmed live against this database, not sufficient. The
# ~49 audit/test/synthetic projects seeded alongside the 4 real productions
# (Little Utopia, Bad Hombres, F#K Valentine's Day, Lips Like Sugar) were
# NOT each minted under their own one-off organization the way
# scripts/build_audit_control_fixtures.py does for its own later batches —
# they were bulk-created under the SAME real organization ("Mind The Story
# Media") in the same seeding pass, so organization scope alone cannot
# separate them.
#
# There is no explicit audit/test/synthetic metadata field, no provenance/
# source-type column, and no reliable per-row signal on `Project` today
# (confirmed by inspecting the model: no is_test/is_fixture/source column
# exists) — a real DB column + migration + backfill was considered and
# explicitly deferred (operator directive: name-based filtering only for
# this pass, no schema change against the shared acceptance database).
# Falling back to naming convention (per this task's own explicit priority
# order, item 4) is therefore the correct, evidenced mechanism here: 3 of
# the 49 fixtures already follow the `AUDIT_CONTROL_*` convention
# (scripts/build_audit_control_fixtures.py's own naming); the other 46 were
# confirmed, by direct operator review of the live title list, to be
# synthetic seed data with no shared substring — enumerated explicitly
# below rather than guessed at with a fragile regex. A GENUINE new project
# (real future ingestion) is never affected: it is never named
# `AUDIT_CONTROL_*` and is never one of these 46 exact legacy titles, so it
# appears automatically with no allowlist update required. Nothing here
# deletes or modifies a fixture row — see `include_fixtures` below for how
# audit tooling reaches them deliberately.
_AUDIT_CONTROL_TITLE_PREFIX = "AUDIT_CONTROL_"
_KNOWN_LEGACY_FIXTURE_TITLES: frozenset[str] = frozenset({
    "10 Double Zero", "5 LBS OF PRESSURE", "97 Minutes", "Adam & Eve",
    "All My Friends Are Dead", "Almost Perfect", "Artists of Cinema",
    "Baron Samedi", "Being Britney", "Braking Point", "David",
    "Dead After Dark", "Drug Honey", "Flash Before the Bang", "Gifted",
    "Give or Take", "Going Places", "Hightower", "Interference",
    "Jane Millen", "Maggie Moves On", "Model Wars", "One Night Stand",
    "Otherwise Engaged", "Replacements", "Rocky Mountain", "Rust",
    "Safehaven", "Serpent Girl", "Sierra Madre", "Sky Unconditional",
    "Spice Route", "Terezin", "The Arrangement", "The Cure", "The Dale",
    "The Men We Leave Behind", "The Room Below", "The System",
    "Trail Mates", "Twilight of the Dead", "Unconditional Love",
    "Underwater", "Werewolf", "White Feather", "White Line Highway",
})


def _is_producer_visible(title: str | None) -> bool:
    """The ONE canonical producer-visibility predicate — every project-
    listing surface must call this, never re-derive its own fixture check.
    A project is a fixture when its title carries the evidenced
    AUDIT_CONTROL_ naming convention OR is one of the enumerated legacy
    seed titles above; everything else (including every title never seen
    before) is producer-visible by default."""
    if not title:
        return True
    if title.startswith(_AUDIT_CONTROL_TITLE_PREFIX):
        return False
    return title not in _KNOWN_LEGACY_FIXTURE_TITLES


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
    include_fixtures: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectCard]:
    """Project Library grid — every real persisted Project belonging to
    ONE organization, each carrying just what a card needs: artwork, and
    completeness across the four CORE material categories. No NPC, no
    scenario economics — those are optimizer output and don't belong in
    a durable-corpus summary.

    PROJECT_UI_DATA_INTEGRITY (2026-09-21): PREVIOUSLY, an absent
    `organization_id` returned every project across every organization —
    confirmed live to include 245 of 329 total projects belonging to 256
    separate one-off `AUDIT_CONTROL_*` fixture organizations, alongside
    the real production company's own 4 real productions. Organization
    scope is never optional now: an explicit `organization_id` is used
    when the caller supplies one, otherwise the deployment's own
    settings.CURRENT_ORGANIZATION_ID (see app/api/v1/organizations.py's
    `/organizations/current`) — and if NEITHER resolves to a real
    organization, this fails closed (returns an empty list) rather than
    ever falling back to "every organization".

    PROJECT_LIBRARY_FIXTURE_EXCLUSION (2026-09-22): organization scope
    alone is NOT sufficient — confirmed live, this deployment's own
    audit/test/synthetic seed projects share the SAME real organization as
    its 4 real productions (see `_is_producer_visible`'s own header
    comment for the full root-cause). The default producer-facing response
    additionally excludes every fixture by the one canonical
    `_is_producer_visible` predicate. `include_fixtures=true` is the
    explicit, deliberate escape hatch for audit tooling that genuinely
    needs to see fixtures (e.g. a future `build_audit_control_fixtures.py`
    verification pass) — nothing is ever deleted or hidden from the
    database itself, only from this default producer-facing listing.
    """
    organization_id = organization_id or settings.CURRENT_ORGANIZATION_ID or None
    if not organization_id:
        return []
    stmt = select(Project).where(Project.organization_id == organization_id)
    stmt = stmt.order_by(Project.updated_at.desc())
    projects = list((await db.execute(stmt)).scalars().all())
    if not include_fixtures:
        projects = [p for p in projects if _is_producer_visible(p.title)]
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

    # Backend-wiring self-audit (2026-09-17): this previously flagged a
    # project "served" the moment ANY ProductionStructure row existed for
    # it, with no engine_version/input_fingerprint check at all —
    # ProductionStructure doesn't even carry engine_version, so a project
    # whose only rows are a retired engine's or a superseded fingerprint's
    # still rendered is_served_production=True on the Library grid.
    # Confirmed live against the shared DB: 4 real named productions sit
    # on canonical-1.72.0 (9 minor versions behind current), and would
    # have shown as "served" despite no row at the current engine/
    # fingerprint existing. Scoped to CURRENT engine_version AND each
    # project's own freshly-recomputed input_fingerprint — the same
    # canonical_evaluation.current_generation_fingerprint() every other
    # current-evaluation reader (build_project_workspace_view,
    # canonical_production_view) already keys off, so "served" here means
    # exactly what it means everywhere else in this codebase.
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint

    current_engine_rows = (await db.execute(
        select(ProductionStructure.project_id, StructureCalculationResult.input_fingerprint)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id.in_(project_ids),
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).all()
    current_engine_fingerprints_by_project: dict[uuid.UUID, set[str]] = {}
    for pid, fp in current_engine_rows:
        current_engine_fingerprints_by_project.setdefault(pid, set()).add(fp)

    served_project_ids: set[uuid.UUID] = set()
    for pid, persisted_fingerprints in current_engine_fingerprints_by_project.items():
        fingerprint = await current_generation_fingerprint(db, pid)
        if fingerprint is not None and fingerprint in persisted_fingerprints:
            served_project_ids.add(pid)

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
            is_served_production=p.id in served_project_ids,
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


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Permanently removes a CineGlobe Project and every record it owns —
    documents/versions/sources, artwork, facts, people-links, location
    requirements, structures/calculation results, aliases, activity — via
    the ON DELETE CASCADE already declared on every FK back to
    projects.id (verified directly against the model source before this
    endpoint was written, not assumed). Shared entities a project merely
    REFERENCES (TalentProfile, Organization) are never touched: only
    ProjectPerson — the join row — cascades.

    Never deletes original source files (Drive/local) — this table only
    ever held a cached copy path + provenance pointer, never the source
    itself. Deletion is Archive's opposite: Archive keeps the project and
    everything about it; this removes the CineGlobe record entirely, for
    the accidental/test/duplicate/mistaken-import case only.

    Refuses to delete the project the demo engine (Overview/Workspace/
    Scenarios) currently serves — a cheap, deliberate safety net, not a
    general restriction: nothing else about this endpoint is special-
    cased to Little Utopia.
    """
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.title == PRODUCTION_NAME:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the project currently served by the production engine.",
        )
    # A Core DELETE, not db.delete(project): the ORM relationship() calls
    # on Document/BudgetDocument/etc. carry no cascade= argument (this
    # codebase relies on the DB's own ON DELETE CASCADE), so the ORM's
    # default ("save-update, merge" only) tries to NULL the child's FK
    # instead of deleting it first — and since documents.project_id is
    # nullable (a Document may instead be organization-owned), that NULL
    # trips the ck_documents_exactly_one_owner CHECK constraint. A plain
    # DELETE statement never loads or touches child rows at all; the
    # already-verified DB-level CASCADE does the real work.
    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()


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


@router.get("/{project_id}/artwork/{asset_id}")
async def get_project_artwork_candidate(project_id: str, asset_id: str, db: AsyncSession = Depends(get_db)) -> FileResponse:
    """Serves ONE specific ProjectAsset's bytes (master or candidate) —
    the picker needs to preview every candidate, not only the current
    master. Scoped to this project's own assets, same as the master route."""
    asset = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.id == asset_id, ProjectAsset.project_id == project_id)
    )).scalar_one_or_none()
    if asset is None or not asset.storage_path:
        raise HTTPException(status_code=404, detail="Asset not found for this project")
    full_path = Path(settings.LOCAL_STORAGE_PATH) / asset.storage_path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="Asset file missing from storage")
    return FileResponse(full_path)


@router.post("/{project_id}/artwork/{asset_id}/set-master")
async def set_master_artwork(project_id: str, asset_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Explicit user selection of master artwork. Never deletes the
    previous master row — only flips is_master, so prior candidates/
    history remain fully retained and selectable again later."""
    target = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.id == asset_id, ProjectAsset.project_id == project_id)
    )).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="Asset not found for this project")

    all_assets = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project_id))).scalars().all()
    for a in all_assets:
        a.is_master = (a.id == target.id)
    await db.commit()
    return {"project_id": project_id, "master_asset_id": str(target.id)}


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

    # Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 5:
    # document-version permission reduction. CineGlobe should act like a
    # competent production analyst -- auto-resolve routine version state,
    # ask only when a producer decision is genuinely material (see the
    # task's four control classes: AUTOMATIC / AUTOMATIC+SURFACE /
    # DECISION REQUIRED / AUTHORITY LOCKED).
    #
    # ROOT CAUSE (confirmed, not guessed): current_unresolved fired
    # whenever a Document had >1 version and NO supersedes_version_id
    # link existed between ANY of them -- regardless of category, and
    # regardless of whether the system already had a confident current
    # pick. But DocumentVersion.is_current is a REAL, reliably-maintained
    # field (see its own model docstring: "a replaced 'current' version
    # is marked is_current=False, not removed") -- the exact same field
    # `current` above already trusts. Flagging a document "unresolved"
    # merely because OTHER historical versions exist, while the system
    # itself already has a confident is_current pick, is asking the
    # producer to re-confirm something CineGlobe already knows -- pure
    # friction, not a real decision.
    #
    # Fixed generically (no per-document/per-project branch):
    #   1. AUTOMATIC — any version genuinely marked is_current=True means
    #      the system has a confident pick; never unresolved, regardless
    #      of category or how many other versions exist.
    #   2. Only when NO version carries is_current=True (a genuine,
    #      system-acknowledged authority gap) does version count matter
    #      at all -- and even then, restricted to the categories where a
    #      wrong pick can materially change downstream analysis (budget,
    #      schedule — the task's own stricter categories). Artwork/deck/
    #      screenplay auto-resolve (fall through to the doc_versions[0]
    #      fallback already used for `current` above) rather than
    #      blocking on a producer decision that rarely matters for them.
    _MATERIAL_VERSION_CATEGORIES = {"budget", "schedule"}

    def _document_payload(doc: Document) -> dict[str, Any]:
        doc_versions = versions_by_doc.get(doc.id, [])
        has_confident_current = any(v.is_current for v in doc_versions)
        current = next((v for v in doc_versions if v.is_current), None) or (
            doc_versions[0] if doc_versions else None
        )
        current_unresolved = (
            not has_confident_current
            and doc.category in _MATERIAL_VERSION_CATEGORIES
            and len(doc_versions) > 1
            and not any(v.supersedes_version_id is not None for v in doc_versions)
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
            "current_unresolved": current_unresolved,
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

    # Backend-wiring self-audit (2026-09-17): previously, `leading_result`
    # was simply "the newest StructureCalculationResult row for whatever
    # structure leading_structure_id currently names" — no engine_version/
    # input_fingerprint check against the CURRENT generation. If a
    # project's facts changed since its last evaluation (no re-run
    # triggered yet), this would keep silently serving the PRIOR
    # generation's NPC/warnings/limitation_note as if current, while
    # build_project_workspace_view (which does key off
    # current_generation_fingerprint) would correctly show no current
    # candidates for the same project. Fixed to use the SAME single
    # canonical generation identity every other current-evaluation reader
    # already uses, so "leading" here never means "stale."
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint

    current_fingerprint = await current_generation_fingerprint(db, project.id)

    leading_structure = None
    leading_result = None
    if project.leading_structure_id and current_fingerprint is not None:
        candidate_result = (await db.execute(
            select(StructureCalculationResult)
            .where(
                StructureCalculationResult.structure_id == project.leading_structure_id,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == current_fingerprint,
            )
            .order_by(StructureCalculationResult.created_at.desc())
        )).scalars().first()
        if candidate_result is not None:
            leading_result = candidate_result
            leading_structure = (await db.execute(
                select(ProductionStructure).where(ProductionStructure.id == project.leading_structure_id)
            )).scalar_one_or_none()

    # Structures sharing the CURRENT evaluation's own input_fingerprint —
    # never a raw count of every ProductionStructure row ever created for
    # the project. A superseded run (a stale legacy-engine result, or an
    # earlier budget version) leaves its rows in place for provenance but
    # must not inflate what the UI reports as "generated" for the
    # currently-displayed evaluation. Always scoped this way now — never
    # falls back to an unscoped raw count, which was the same staleness
    # gap as leading_result above whenever leading_structure_id was unset.
    if current_fingerprint is not None:
        structure_count = (await db.execute(
            select(func.count()).select_from(StructureCalculationResult)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(
                ProductionStructure.project_id == project.id,
                StructureCalculationResult.input_fingerprint == current_fingerprint,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
            )
        )).scalar_one()
    else:
        structure_count = 0

    activity = (await db.execute(
        select(ProjectActivity).where(ProjectActivity.project_id == project.id)
        .order_by(ProjectActivity.created_at.desc()).limit(20)
    )).scalars().all()

    # Read-time fallback, not a mutation: a BudgetDocument can exist for a
    # project whose Project.total_budget_usd was never set — either it
    # predates the commit-time routing in material_routing.py, or it was
    # imported via the standalone /budgets/import endpoint, which has never
    # written Project.total_budget_usd. Rather than requiring a backfill or
    # re-import, fall back to the most recently ingested budget document's
    # own declared total. Computed on read only; the column itself is left
    # untouched here.
    effective_total_budget_usd = project.total_budget_usd
    if effective_total_budget_usd is None:
        fallback_budget_doc = (await db.execute(
            select(BudgetDocument)
            .where(BudgetDocument.project_id == project.id, BudgetDocument.total_budget_raw.is_not(None))
            .order_by(BudgetDocument.created_at.desc())
        )).scalars().first()
        if fallback_budget_doc is not None:
            effective_total_budget_usd = fallback_budget_doc.total_budget_raw

    return {
        "project": {
            "id": str(project.id), "title": project.title, "logline": project.logline,
            "genre": project.genre, "format": project.format, "lifecycle": project.lifecycle,
            "total_budget_usd": effective_total_budget_usd, "target_shoot_year": project.target_shoot_year,
            "notes": project.notes,
            # Fresh Project Ingestion Acceptance, Phase 1: whether this
            # project has a real, priced canonical evaluation to enter —
            # i.e. whether /projects/{id}/overview (Overview.jsx's
            # useCineGlobe(projectId) -> GET /cineglobe/projects/{id}/state,
            # already generic and project-scoped) has something to show.
            # PREVIOUSLY hardcoded to `project.title == PRODUCTION_NAME`
            # (Little Utopia only) — a real identity defect: any other
            # project that successfully evaluated (confirmed via runtime
            # trace against F#K Valentine's Day, 135 priced/34 unpriceable
            # candidates) was permanently denied the same clean "Enter
            # Workspace" state LU gets, stuck showing a redundant "Re-run
            # Evaluation" + secondary "Enter Workspace" pair instead. Uses
            # the SAME generic structure_count condition `evaluation_begun`
            # already computes below — never a title/production match.
            "is_served_production": structure_count > 0,
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
                {"id": str(a.id), "url": f"/api/v1/projects/{project.id}/artwork/{a.id}", "is_master": a.is_master,
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
            "leading_true_net_cost_usd": (
                float(leading_result.true_net_cost_usd)
                if leading_result is not None and leading_result.true_net_cost_usd is not None else None
            ),
            "has_unverified_inputs": leading_result.has_unverified_inputs if leading_result is not None else None,
            "limitation_note": (leading_result.warnings or [None])[0] if leading_result is not None else None,
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


@router.post("/{project_id}/people/extract")
async def extract_project_people(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """PROJECT_UI_DATA_INTEGRITY (2026-09-21): scans this project's own
    current screenplay/deck documents on disk for real credited names/
    roles (app/ingestion/document_person_extractor.py's generic patterns
    -- never a hardcoded name) and creates any missing ProjectPerson/
    TalentProfile rows. Idempotent -- safe to call again after new
    documents are added; never duplicates an already-extracted (project,
    person, role). Never infers nationality/residency -- a new record's
    nationality_resolution_status is always "not_attempted", which the
    existing missing_inputs disclosure (canonical_production_view.py)
    already surfaces to the producer as a real question."""
    from app.ingestion.document_person_ingestion import extract_and_persist_project_people

    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    created = await extract_and_persist_project_people(db, project_id)
    await db.commit()
    return {
        "created_count": len(created),
        "created": [
            {"project_person_id": str(pp.id), "talent_id": str(pp.talent_id), "role": pp.role}
            for pp in created
        ],
    }
