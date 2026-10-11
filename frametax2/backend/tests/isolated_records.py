"""Isolated synthetic project records for DB-backed tests.

Every test using this module runs inside a transaction that is ROLLED BACK, on SYNTHETIC records it creates itself, and a write guard
refuses any INSERT / UPDATE / DELETE that names a project which existed before the test began (every real project, including the
four anchors). Nothing here reads or evaluates a real production, and nothing from a test survives it.

    async def test_x(isolated_project):          # fixture from this module's conftest-style re-export
        session, project_id = isolated_project

Run these tests on the isolated ``frametax2_pytest`` database (leave DATABASE_URL unset); they never need real project data."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile

#: The four anchor productions are always protected, even in a database that does not contain them.
REAL_ANCHOR_PROJECT_IDS = frozenset({
    "fa5cade5-0669-4816-bfe6-72146f8d3bae",   # The Little Utopia
    "ab10b319-978e-44d3-9331-af2a5f2cccc2",   # Lips Like Sugar
    "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",   # F#K Valentine's Day
    "4355ae88-a636-4c18-af60-ad73b2646124",   # Bad Hombres
})
SYNTHETIC_TITLE_PREFIX = "SYNTHETIC test project"
ISOLATED_TEST_DB_NAME = "frametax2_pytest"

#: (account code, description, spend category, atl/btl, amount) -- invented, MU-eligible mix with a contingency reserve.
DEFAULT_LINES = (
    ("1000", "ABOVE THE LINE CAST", "atl_cast", "atl", 500_000.0),
    ("3100", "CAMERA AND ELECTRIC", "btl_crew_labor", "btl", 800_000.0),
    ("5000", "POST SOUND", "sound", "post", 200_000.0),
    ("8300", "CONTINGENCY", "contingency", "other", 100_000.0),
)


_DEPARTMENT_BY_ATL_BTL = {"atl": "Above the Line", "btl": "Production", "post": "Post Production", "other": "Other"}


class RealProjectWriteRefused(AssertionError):
    """A test statement tried to write to a project that is not one of this test's own synthetic records."""


def assert_synthetic_project_id(project_id, created_ids) -> None:
    pid = str(project_id)
    if pid in REAL_ANCHOR_PROJECT_IDS or pid not in created_ids:
        raise RealProjectWriteRefused(f"{pid} is not a synthetic project created by this test")


def _install_write_guard(sync_conn, protected_ids: frozenset[str]) -> None:
    def refuse_real_project_writes(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        head = statement.lstrip()[:7].upper()
        if not head.startswith(("INSERT", "UPDATE", "DELETE")):
            return
        blob = f"{statement} {parameters}".lower()
        for pid in protected_ids:
            if pid.lower() in blob:
                raise RealProjectWriteRefused(f"refused a write naming existing project {pid}: {statement[:120]}")

    event.listen(sync_conn, "before_cursor_execute", refuse_real_project_writes)


@asynccontextmanager
async def isolated_session():
    """(session, created_project_ids): a savepoint-joined session inside an outer transaction that is always rolled back."""
    async with engine.connect() as conn:
        outer = await conn.begin()
        db_name = (await conn.execute(text("select current_database()"))).scalar()
        if db_name != ISOLATED_TEST_DB_NAME:
            await outer.rollback()
            raise RealProjectWriteRefused(
                f"synthetic records run only on the isolated {ISOLATED_TEST_DB_NAME!r} database, not {db_name!r}; leave DATABASE_URL unset")
        existing = {str(i) for i in (await conn.execute(text("select id from projects"))).scalars().all()}
        _install_write_guard(conn.sync_connection, frozenset(existing | set(REAL_ANCHOR_PROJECT_IDS)))
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        session.info["synthetic_project_ids"] = set()
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()


async def create_synthetic_project(session: AsyncSession, *, lines=DEFAULT_LINES, home_code: str = "MU", title_suffix: str = "") -> str:
    """A synthetic project with a budget document and line items, home jurisdiction resolved from the existing jurisdiction table."""
    org_id = (await session.execute(select(Organization.id).limit(1))).scalar_one()
    jurisdiction = (await session.execute(select(Jurisdiction).where(Jurisdiction.code == home_code))).scalars().first()
    assert jurisdiction is not None, f"jurisdiction {home_code} is not seeded in the test database"
    total = round(sum(l[4] for l in lines), 2)
    project = Project(
        id=uuid.uuid4(), title=f"{SYNTHETIC_TITLE_PREFIX} {uuid.uuid4().hex[:8]}{title_suffix}", organization_id=org_id,
        format="feature", total_budget_usd=total, home_jurisdiction_id=jurisdiction.id,
    )
    session.add(project)
    await session.flush()
    session.info["synthetic_project_ids"].add(str(project.id))
    document = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="synthetic budget.pdf", file_type="pdf", currency_code="USD",
        total_budget_raw=total, extraction_status="complete", parser_version="synthetic",
    )
    session.add(document)
    await session.flush()
    for code, desc, category, atl_btl, amount in lines:
        session.add(BudgetLineItem(
            id=uuid.uuid4(), budget_document_id=document.id, description=f"{code} {desc}", atl_btl=atl_btl,
            department=_DEPARTMENT_BY_ATL_BTL.get(atl_btl, "Other"),
            spend_category=category, amount_raw=amount, amount_normalized=amount, amount_usd=amount, cash_amount_usd=amount,
            accounting_amount_usd=amount, currency_code="USD",
        ))
    await session.flush()
    assert_synthetic_project_id(project.id, session.info["synthetic_project_ids"])
    return str(project.id)


async def add_synthetic_people(session: AsyncSession, project_id: str, people) -> None:
    """people: (role, name, primary_nationality, confirmed[, known_residencies]) -- synthetic talent attached to a synthetic project."""
    assert_synthetic_project_id(project_id, session.info["synthetic_project_ids"])
    for entry in people:
        role, name, nationality, confirmed, *rest = entry
        talent = TalentProfile(id=uuid.uuid4(), name=name, role=role, primary_nationality=nationality,
                               known_residencies=rest[0] if rest else None)
        session.add(talent)
        await session.flush()
        session.add(ProjectPerson(id=uuid.uuid4(), project_id=uuid.UUID(str(project_id)), talent_id=talent.id, role=role, is_confirmed=confirmed))
    await session.flush()


@pytest.fixture
async def isolated_project():
    """(session, synthetic_project_id) with the default budget; everything rolls back."""
    async with isolated_session() as session:
        yield session, await create_synthetic_project(session)


#: A synthetic budget WITH a vfx line makes the evaluator enumerate ~170k hybrid candidates (about four minutes, measured). Those tests
#: stay on synthetic, rolled-back records but are opt-in: set CINEGLOBE_RUN_HEAVY_SYNTHETIC=1 to run them.
HEAVY_SYNTHETIC_ENV = "CINEGLOBE_RUN_HEAVY_SYNTHETIC"
HEAVY_LINES = DEFAULT_LINES + (("6100", "VFX", "vfx", "post", 300_000.0), ("6000", "MUSIC", "music", "post", 120_000.0))


def heavy_synthetic_enabled() -> bool:
    import os
    return os.environ.get(HEAVY_SYNTHETIC_ENV) == "1"


requires_heavy_synthetic = pytest.mark.skipif(
    not heavy_synthetic_enabled(), reason=f"~4 minute synthetic evaluation (vfx-driven hybrid search); set {HEAVY_SYNTHETIC_ENV}=1 to run")


#: Tests that assert FROZEN BASELINES of the four real productions cannot be synthetic. They run only when explicitly authorised, only
#: against a database that contains those productions (set DATABASE_URL to it), and inside a READ ONLY transaction: any write fails.
REAL_READS_ENV = "CINEGLOBE_ALLOW_REAL_PRODUCTION_READS"
requires_real_production_reads = pytest.mark.skipif(
    __import__("os").environ.get(REAL_READS_ENV) != "1",
    reason=f"asserts frozen real-production baselines; set {REAL_READS_ENV}=1 with DATABASE_URL on a database that holds them (read-only)")


@asynccontextmanager
async def real_readonly_session():
    async with engine.connect() as conn:
        outer = await conn.begin()
        await conn.execute(text("SET TRANSACTION READ ONLY"))
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()


@pytest.fixture
async def real_readonly_db():
    async with real_readonly_session() as session:
        yield session
