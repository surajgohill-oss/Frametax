"""Independent DB-backed audit of the active AG-only/Codex-only delta.

The five cases are derived from the final canonical manifest after excluding
the frozen MATERIAL_CONFLICT cohort.  This file changes no runtime behavior.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import SpendCategory
from app.models.jurisdiction import Jurisdiction
from app.models.organization import Organization
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _project(db: AsyncSession, code: str, label: str) -> Project:
    jurisdiction = (await db.execute(
        select(Jurisdiction).where(Jurisdiction.code == code)
    )).scalars().first()
    assert jurisdiction is not None, f"canonical jurisdiction seed missing: {code}"
    suffix = uuid.uuid4().hex[:10]
    org = Organization(name=f"Codex delta {label} {suffix}", slug=f"codex-delta-{suffix}")
    db.add(org)
    await db.flush()
    project = Project(
        id=uuid.uuid4(), organization_id=org.id, title=f"Codex delta {label} {suffix}",
        home_jurisdiction_id=jurisdiction.id, total_budget_usd=2_000_000.0,
    )
    db.add(project)
    await db.flush()
    document = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="delta.csv", file_type="csv",
        is_active=True, extraction_status="completed", total_budget_raw=2_000_000.0,
    )
    db.add(document)
    db.add(BudgetLineItem(
        id=uuid.uuid4(), budget_document_id=document.id,
        description="QUALIFYING PRODUCTION LABOUR", amount_raw=2_000_000.0,
        amount_usd=2_000_000.0, spend_category=SpendCategory.BTL_CREW_LABOR.value,
    ))
    await db.commit()
    await db.refresh(project)
    return project


async def _teardown(db: AsyncSession, project_id) -> None:
    if (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none():
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.commit()


def _entries(view: dict, slug: str) -> list[dict]:
    return [
        row for row in view["structures"]["allocated_structures"]["structures"]
        if row.get("program_slug") == slug
    ]


async def _persisted(db: AsyncSession, project_id, slug: str) -> list[StructureCalculationResult]:
    rows = (await db.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == project_id)
    )).scalars().all()
    return [r for r in rows if (r.calculation_trace_json or {}).get("program_slug") == slug]


# Independent literals, intentionally not imported from production rate data.
PRICEABLE_CASES = (
    ("BG", "bg_film_encouragement_act_rebate", 500_000.0, 1_500_000.0),
    ("MY", "my_finas_rebate", 600_000.0, 1_400_000.0),
    ("US-NV", "us_nv_film_credit", 300_000.0, 1_700_000.0),
)


@pytest.mark.parametrize("code,slug,expected_incentive,expected_npc", PRICEABLE_CASES)
async def test_active_delta_real_pipeline(
    db: AsyncSession, code: str, slug: str, expected_incentive: float, expected_npc: float,
):
    project = await _project(db, code, slug)
    try:
        first = await evaluate_project(db, project.id)
        view1 = await build_production_and_structures(db, project.id)
        entries1 = _entries(view1, slug)
        assert entries1, f"{slug} is intended active but creates no canonical candidate"
        priced = [e for e in entries1 if e.get("is_fully_priced")]
        assert priced, f"{slug} creates no fully priced candidate: {entries1}"
        exact = [
            e for e in priced
            if e.get("selected_incentive_usd") == pytest.approx(expected_incentive, abs=0.01)
            and e.get("npc_with_adjustments_usd") == pytest.approx(expected_npc, abs=0.01)
        ]
        assert exact, f"{slug} did not reproduce independent economics: {priced}"
        assert first["status"] == "EVALUATION_COMPLETE"
        rows1 = await _persisted(db, project.id, slug)
        assert rows1, f"{slug} did not persist a calculation result"

        second = await evaluate_project(db, project.id)
        view2 = await build_production_and_structures(db, project.id)
        assert second["status"] == "EVALUATION_REUSED"
        assert _entries(view2, slug) == entries1
        assert len(await _persisted(db, project.id, slug)) == len(rows1)
    finally:
        await _teardown(db, project.id)


async def test_bc_dave_is_reachable_but_fail_closed_without_narrow_labour_base(
    db: AsyncSession,
):
    slug = "ca_bc_dave"
    project = await _project(db, "CA-BC", slug)
    try:
        first = await evaluate_project(db, project.id)
        view1 = await build_production_and_structures(db, project.id)
        entries1 = _entries(view1, slug)
        assert entries1, "DAVE must remain discoverable as a conditional component program"
        assert all(not entry.get("is_fully_priced") for entry in entries1)
        assert all(entry.get("selected_incentive_usd") is None for entry in entries1)
        blockers = " ".join(
            blocker
            for entry in entries1
            for blocker in entry.get("blockers", [])
        )
        assert "NARROWER base" in blockers
        assert "no labour schedule or residency split" in blockers
        assert first["status"] == "EVALUATION_COMPLETE"
        rows1 = await _persisted(db, project.id, slug)
        assert len(rows1) == 1
        assert rows1[0].total_incentive_value_usd is None
        assert (rows1[0].calculation_trace_json or {}).get("candidate_status") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"

        second = await evaluate_project(db, project.id)
        view2 = await build_production_and_structures(db, project.id)
        assert second["status"] == "EVALUATION_REUSED"
        assert _entries(view2, slug) == entries1
        assert len(await _persisted(db, project.id, slug)) == len(rows1)
    finally:
        await _teardown(db, project.id)


async def test_ohio_manifest_active_but_no_candidate_is_reachable(db: AsyncSession):
    from app.data.program_rate_rules import get_rate_rules
    from app.services.canonical_program_identity import resolve_identity

    slug = "proposed_united_states_ohio_ohio_motion_picture_tax_credit"
    jurisdiction = (await db.execute(
        select(Jurisdiction).where(Jurisdiction.code == "US-OH")
    )).scalars().first()
    assert jurisdiction is None
    assert resolve_identity(slug) is not None
    assert get_rate_rules(slug) == ()
