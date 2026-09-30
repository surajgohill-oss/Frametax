#!/usr/bin/env python3
"""Lips Like Sugar — canonicalize its real California allocation letter.

Confirmed defect: "3C-122 Lips Like Sugar CAL 8-053.pdf" -- a real, e-signed
California Film Commission Credit Allocation Letter (Program 3.0, dated
03/06/2023, allocation #8-053, reserving $1,470,365, jobs ratio 3.26035) --
existed only at /Users/Suraj/Downloads/lipslikesugar/ and was never ingested
into this project's canonical document store or fact layer. Confirmed by
reading both the letter itself and the project's own storage directory
(~/.cineglobe/storage/lips-like-sugar/, which held only the budget and a
screenplay cover image, no allocation letter). This is exactly the
"stranded ingestion-candidate" gap PROJECT_RULES describes.

This script does NOT invent a new project-evidence registry (PROJECT_RULES
forbids that). It uses the two existing canonical owners:
  - library_document.py's Document/DocumentVersion layer (project-scoped
    document identity + physical artifact), for the copied PDF itself;
  - project_fact.py's ProjectFact extensible key/value layer, for the
    letter's structured facts (allocation number, date, program version,
    reserved amount, jobs ratio, status).

The letter explicitly states "The allocation of tax credits indicated in
this letter are not guaranteed and are only an estimate. Final granting of
tax credits is subject to examination and verification..." -- so
ca_allocation_status is recorded as "reserved_not_final_award", never
promoted to a confirmed/final credit.

Idempotent: keyed on (project_id, checksum_sha256) for the document and
(project_id, fact_key) for facts (project_facts has a real UNIQUE
constraint on that pair) -- safe to re-run, every statement is a no-op
once applied. The original file at Downloads is only ever copied, never
moved or modified.

Run with (DATABASE_URL must resolve to the approved acceptance database):
    cd frametax2/backend && python3 scripts/canonicalize_lls_allocation_letter.py
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"
LLS_PROJECT_TITLE = "Lips Like Sugar"

SOURCE_PDF = Path("/Users/Suraj/Downloads/lipslikesugar/3C-122 Lips Like Sugar CAL 8-053.pdf")
STORAGE_ROOT = Path(os.path.expanduser("~/.cineglobe/storage"))

# fact_key -> (value, value_type). All independently verified against the
# real signed letter (page 2 form fields + Adobe Sign audit report, page 3).
FACTS: dict[str, tuple[str, str]] = {
    "ca_allocation_letter_number": ("8-053", "string"),
    "ca_allocation_letter_date": ("2023-03-06", "string"),
    "ca_allocation_program_version": (
        "California Film and Television Tax Credit Program 3.0", "string",
    ),
    "ca_allocation_reserved_usd": ("1470365", "number"),
    "ca_allocation_jobs_ratio": ("3.26035", "number"),
    # Never "confirmed"/"final" -- the letter's own text: "not guaranteed
    # and are only an estimate. Final granting ... subject to examination
    # and verification of the claimed Qualified Expenditures."
    "ca_allocation_status": ("reserved_not_final_award", "string"),
}


async def main() -> int:
    db_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2"
    )
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB:
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved database {APPROVED_DB!r}.")
        await engine.dispose()
        return 1

    if not SOURCE_PDF.exists():
        print(f"REFUSING TO RUN: source PDF not found at {SOURCE_PDF}")
        await engine.dispose()
        return 1

    from app.models.enums import DocumentCategory, ProjectFactSourceType, ReviewStatus
    from app.models.library_document import Document, DocumentVersion
    from app.models.project import Project
    from app.models.project_fact import ProjectFact

    checksum = hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()

    async with AsyncSession(engine) as session:
        project = (
            await session.execute(select(Project).where(Project.title == LLS_PROJECT_TITLE))
        ).scalars().first()
        if project is None:
            print(f"REFUSING TO RUN: no project titled {LLS_PROJECT_TITLE!r} found.")
            await engine.dispose()
            return 1

        existing_version = (
            await session.execute(
                select(DocumentVersion)
                .join(Document, Document.id == DocumentVersion.document_id)
                .where(Document.project_id == project.id, DocumentVersion.checksum_sha256 == checksum)
            )
        ).scalars().first()

        if existing_version is None:
            dest_dir = STORAGE_ROOT / "lips-like-sugar"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / SOURCE_PDF.name
            if not dest_path.exists():
                shutil.copy2(SOURCE_PDF, dest_path)  # copy only -- original untouched

            doc = Document(
                project_id=project.id,
                category=DocumentCategory.PRE_QUALIFICATION,
                title="Lips Like Sugar — CA Film Commission Credit Allocation Letter #8-053",
            )
            session.add(doc)
            await session.flush()

            version = DocumentVersion(
                document_id=doc.id,
                original_filename=SOURCE_PDF.name,
                storage_path=str(dest_path),
                checksum_sha256=checksum,
                file_size=dest_path.stat().st_size,
                detected_date="2023-03-06",
                version_label="Signed Credit Allocation Letter #8-053",
                ingested_at=datetime.now(timezone.utc).isoformat(),
                is_current=True,
                extraction_status="extracted",
                notes=(
                    "California Film Commission Program 3.0 Credit Allocation Letter, "
                    "e-signed 2023-03-02 (Adobe Sign audit trail on file), reserving "
                    "$1,470,365. Explicitly NOT a final audited credit -- the letter's "
                    "own text states the amount is an estimate subject to examination "
                    "and verification."
                ),
            )
            session.add(version)
            await session.flush()
            doc.current_version_id = version.id
            print(f"Created Document {doc.id} / DocumentVersion {version.id}")
        else:
            version = existing_version
            print(f"Already canonicalized -- reusing existing DocumentVersion {version.id}")

        for fact_key, (value, value_type) in FACTS.items():
            existing_fact = (
                await session.execute(
                    select(ProjectFact).where(
                        ProjectFact.project_id == project.id, ProjectFact.fact_key == fact_key
                    )
                )
            ).scalars().first()
            if existing_fact is None:
                session.add(ProjectFact(
                    project_id=project.id,
                    fact_key=fact_key,
                    value=value,
                    value_type=value_type,
                    source_type=ProjectFactSourceType.EXTRACTED,
                    source_document_version_id=version.id,
                    source_location="page 2 (Credit Allocation Letter form, CFC Form D3, June 25 2019)",
                    extraction_confidence=1.0,
                    review_status=ReviewStatus.PENDING,
                ))
                print(f"Inserted fact {fact_key} = {value}")
            else:
                print(f"Fact already present, left untouched: {fact_key} = {existing_fact.value}")

        await session.commit()

    await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
