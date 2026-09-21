"""
document_person_ingestion.py

PROJECT_UI_DATA_INTEGRITY (2026-09-21) — wires document_person_extractor's
generic credit extraction into real, persisted ProjectPerson/TalentProfile
rows, through the existing ingestion architecture (app/ingestion/*,
consumed by app/api/v1/documents.py's project-document read paths).

Never infers nationality/residency: a newly-created TalentProfile always
carries nationality_resolution_status="not_attempted" and
primary_nationality=None -- canonical_production_view.py's existing
missing_inputs disclosure already asks the resulting "what is {name}'s
({role}) nationality?" question the moment a real name with no
nationality exists (no new disclosure mechanism needed here).

Idempotent: re-running against documents already ingested never creates
a duplicate ProjectPerson row for the same (project, talent, role) --
safe to call again after new documents are added.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.ingestion.document_person_extractor import ExtractedPersonCredit, extract_credits_from_pages
from app.ingestion.pdf_extractor import extract_text_from_pdf
from app.models.library_document import Document, DocumentVersion
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile

#: Document categories a credited name/role is realistically sourced
#: from -- never every category (e.g. "artwork"/"budget" have no prose
#: credit lines to extract from; scanning them would only cost time).
_CREDIT_BEARING_CATEGORIES = ("screenplay", "deck")


async def _current_pdf_documents(session: AsyncSession, project_id) -> list[tuple[Document, DocumentVersion]]:
    rows = (await session.execute(
        select(Document, DocumentVersion)
        .join(DocumentVersion, DocumentVersion.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            Document.category.in_(_CREDIT_BEARING_CATEGORIES),
            DocumentVersion.is_current.is_(True),
        )
    )).all()
    return [(d, v) for d, v in rows if v.storage_path and v.storage_path.lower().endswith(".pdf")]


def _extract_from_document(version: DocumentVersion) -> list[ExtractedPersonCredit]:
    path = Path(settings.LOCAL_STORAGE_PATH) / version.storage_path
    if not path.is_file():
        return []
    result = extract_text_from_pdf(str(path))
    return extract_credits_from_pages(result.pages)


async def extract_and_persist_project_people(session: AsyncSession, project_id) -> list[ProjectPerson]:
    """Scans this project's own current screenplay/deck documents on
    disk, extracts real credited names/roles (document_person_extractor's
    generic patterns -- never a hardcoded name), and creates any
    ProjectPerson/TalentProfile rows that don't already exist. Returns
    every ProjectPerson row this call created (empty list when nothing
    new was found or the project has no readable credit-bearing
    document)."""
    documents = await _current_pdf_documents(session, project_id)
    existing_talent_by_name = {
        t.name: t for t in (await session.execute(select(TalentProfile))).scalars().all()
    }
    existing_links = {
        (pp.project_id, pp.talent_id, pp.role)
        for pp in (await session.execute(
            select(ProjectPerson).where(ProjectPerson.project_id == project_id)
        )).scalars().all()
    }

    created: list[ProjectPerson] = []
    for document, version in documents:
        for credit in _extract_from_document(version):
            talent = existing_talent_by_name.get(credit.name)
            if talent is None:
                talent = TalentProfile(
                    id=uuid.uuid4(), name=credit.name, role=credit.role,
                    # Never inferred -- a real, disclosed gap the existing
                    # missing_inputs question surfaces to the producer.
                    primary_nationality=None, nationality_resolution_status="not_attempted",
                )
                session.add(talent)
                existing_talent_by_name[credit.name] = talent

            key = (project_id, talent.id, credit.role)
            if key in existing_links:
                continue
            existing_links.add(key)
            project_person = ProjectPerson(
                id=uuid.uuid4(), project_id=project_id, talent_id=talent.id, role=credit.role,
                is_confirmed=False,
                notes=(
                    f"Extracted from {document.title}, page {credit.page_number}: "
                    f"\"{credit.evidence_text}\""
                ),
            )
            session.add(project_person)
            created.append(project_person)
    return created
