#!/usr/bin/env python3
"""Force a reparse of every BudgetDocument whose parser_version is behind
BUDGET_PARSER_VERSION, via the SAME _route_budget() pipeline real ingestion
uses -- never a duplicated parse implementation.

Needed because bumping BUDGET_PARSER_VERSION (budget-1.4.0: capture the
producer's own stated incentive/rebate estimate line -- see budget_parser.py
and migration 0078) only causes an automatic reparse the NEXT time a
document is (re-)routed; it does not retroactively touch already-persisted
BudgetDocument rows on its own. Confirmed live: Little Utopia and F#K
Valentine's Day both still carried parser_version="budget-1.3.0+..." and
served `pkg.budget.source_incentive_estimates: []` even after the code
fix, purely because nothing had re-invoked routing for their existing
documents.

Idempotent: _route_budget() itself is idempotent on parser_version (an
already-current document is a genuine no-op, "already_current"); this
script is therefore safe to re-run at any time, including after a further
parser change.

Run with (DATABASE_URL must resolve to the approved acceptance database):
    cd frametax2/backend && python3 scripts/reparse_stale_budget_documents.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"

# Scoped to the four real productions this task's project-evidence
# reconciliation actually covers -- never a blanket reparse of every
# BudgetDocument in the database (dozens of unrelated test/demo projects
# also live here; PROJECT_RULES forbids broadening scope beyond what was
# requested).
IN_SCOPE_PROJECT_TITLES = {
    "The Little Utopia",
    "F#K Valentine's Day",
    "Lips Like Sugar",
    "Bad Hombres",
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

    from app.core.config import settings
    from app.ingestion.budget_parser import BUDGET_PARSER_VERSION
    from app.models.budget import BudgetDocument
    from app.models.library_document import DocumentVersion
    from app.models.project import Project
    from app.services.material_routing import _route_budget

    storage_root = Path(settings.LOCAL_STORAGE_PATH)

    async with AsyncSession(engine) as session:
        in_scope_project_ids = {
            p.id for p in (
                await session.execute(
                    select(Project).where(Project.title.in_(IN_SCOPE_PROJECT_TITLES))
                )
            ).scalars().all()
        }
        stale_docs = (
            await session.execute(
                select(BudgetDocument).where(
                    BudgetDocument.parser_version != BUDGET_PARSER_VERSION,
                    BudgetDocument.project_id.in_(in_scope_project_ids),
                )
            )
        ).scalars().all()

        if not stale_docs:
            print(f"Nothing stale among the {len(IN_SCOPE_PROJECT_TITLES)} in-scope productions -- already at {BUDGET_PARSER_VERSION}.")
            await engine.dispose()
            return 0

        for bd in stale_docs:
            project = await session.get(Project, bd.project_id)
            if bd.document_version_id is None:
                print(f"SKIP {project.title if project else bd.project_id}: no document_version_id linked -- cannot re-route via the real pipeline, needs manual review.")
                continue
            version = await session.get(DocumentVersion, bd.document_version_id)
            if version is None:
                print(f"SKIP {project.title}: document_version_id {bd.document_version_id} does not resolve -- orphaned link.")
                continue
            local_path = Path(bd.storage_path) if os.path.isabs(bd.storage_path or "") else storage_root / (bd.storage_path or "")
            if not local_path.exists():
                print(f"SKIP {project.title}: source file not found at {local_path}")
                continue
            status = await _route_budget(session, project=project, version=version, local_path=local_path)
            print(f"{project.title}: _route_budget -> {status}")

        await session.commit()

    await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
