"""
test_generic_future_project_propagation.py

GENERIC FUTURE-PROJECT PROPAGATION PROOF.

The prior "future project PASS" claim was overstated: every runtime assertion
behind it used an EXISTING project (Little Utopia, later Lips/FVD), and Little
Utopia in particular has no external control documents at all. Passing on
already-seeded fixtures cannot prove that a NEWLY CREATED production inherits
the repaired machinery -- which is precisely how defects survived earlier
verification.

This test creates a temporary production through the ordinary generic path
(Organization -> Project -> budget Document/DocumentVersion on disk ->
material_routing) and drives the full chain end to end:

    creation -> ingestion -> normalized budget -> project facts
      -> economic inputs -> optimizer/candidates -> authority + eligibility
      -> qualifying base -> rate/caps -> pricing -> fingerprint/persistence
      -> refetch/API view

and asserts the repaired invariants hold for a project that did not exist when
any of them were written. No project-id or title-specific behavior is used
anywhere; the fixture is torn down afterwards.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.material_routing import ensure_current_budget_routed

#: A deliberately ordinary feature budget: ATL, BTL, post, and a contingency
#: reserve. Amounts are synthetic -- this proves PROPAGATION, and nothing here
#: is asserted as a jurisdiction's real economics.
_ACCOUNT_LINES = [
    ("1100", "STORY / RIGHTS", 250_000),
    ("1200", "PRODUCER", 400_000),
    ("1300", "DIRECTOR", 350_000),
    ("1400", "CAST", 900_000),
    ("2000", "PRODUCTION", 1_800_000),
    ("2400", "CAMERA", 300_000),
    ("3000", "ART DEPARTMENT", 450_000),
    ("5000", "POST PRODUCTION", 500_000),
    ("6700", "INSURANCE", 150_000),
    ("7100", "CONTINGENCY", 300_000),
]
_EXPECTED_LEAF_SUM = float(sum(amount for _, _, amount in _ACCOUNT_LINES))


def _write_budget_pdf(path: Path) -> None:
    lines = ["CLEAN SLATE PROPAGATION PRODUCTION", "Account", "Description", "Total"]
    for code, description, amount in _ACCOUNT_LINES:
        lines += [code, description, f"${amount:,}"]
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "\n".join(lines), fontsize=10)
    doc.save(str(path))
    doc.close()


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def clean_slate_project(db: AsyncSession):
    """A brand-new production created through the ordinary generic path."""
    suffix = uuid.uuid4().hex[:8]
    org = Organization(
        name=f"Clean Slate Propagation Org {suffix}",
        slug=f"clean-slate-propagation-{suffix}",
    )
    db.add(org)
    await db.flush()

    project = Project(
        id=uuid.uuid4(), organization_id=org.id,
        title=f"Clean Slate Propagation Production {suffix}",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id

    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"clean-slate-{project_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = "Clean Slate Budget.pdf"
    _write_budget_pdf(storage_dir / filename)

    document = Document(
        id=uuid.uuid4(), project_id=project_id, category="budget",
        title=f"{project.title} — Budget",
    )
    db.add(document)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=document.id, original_filename=filename,
        storage_path=f"clean-slate-{project_id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    document.current_version_id = version.id
    await db.commit()

    try:
        yield project
    finally:
        remaining = (await db.execute(
            select(Project).where(Project.id == project_id)
        )).scalar_one_or_none()
        if remaining is not None:
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()
        if storage_dir.exists():
            shutil.rmtree(storage_dir)


async def test_new_production_propagates_the_repaired_machinery_end_to_end(
    db: AsyncSession, clean_slate_project: Project,
):
    project_id = str(clean_slate_project.id)

    # ── ingestion -> normalized budget ───────────────────────────────────
    budget_document = await ensure_current_budget_routed(db, clean_slate_project.id)
    assert budget_document is not None, "generic ingestion did not route the budget"

    from app.models.budget import BudgetLineItem

    lines = (await db.execute(
        select(BudgetLineItem).where(
            BudgetLineItem.budget_document_id == budget_document.id
        )
    )).scalars().all()
    assert lines, "no normalized budget lines"
    leaf_sum = round(sum(float(line.amount_usd or 0.0) for line in lines), 2)
    assert leaf_sum == pytest.approx(_EXPECTED_LEAF_SUM, abs=0.01), (
        f"leaf-line sum {leaf_sum:,.2f} != source {_EXPECTED_LEAF_SUM:,.2f} — "
        "no dollars may appear or disappear during normalization"
    )
    # ATL/BTL identity survives normalization generically (account-code
    # convention, not a per-project rule).
    departments = {line.department for line in lines}
    assert "Above The Line" in departments, f"ATL not classified: {departments}"

    # ── economic inputs -> fingerprint ───────────────────────────────────
    econ = await build_project_economic_inputs(db, clean_slate_project.id)
    assert econ.ok, f"economic inputs blocked: {econ.blockers}"
    assert econ.inputs.gross_budget_usd == pytest.approx(_EXPECTED_LEAF_SUM, abs=0.01)

    # ── optimizer -> evaluation -> persistence ───────────────────────────
    result = await evaluate_project(db, project_id)
    assert result["engine_version"] == ENGINE_VERSION

    # ── refetch / API view ───────────────────────────────────────────────
    view = await build_production_and_structures(db, project_id)
    assert view["status"] == "OK"
    entries = view["structures"]["allocated_structures"]["structures"]
    assert entries, "a new production generated no candidates"

    priced = [e for e in entries if e["is_fully_priced"]]
    assert priced, "a new production priced nothing at all"

    # ── the repaired invariants, on a project that did not exist when they
    #    were written ──────────────────────────────────────────────────────
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    for entry in entries:
        slugs = entry.get("program_slugs") or (
            [entry["program_slug"]] if entry.get("program_slug") else []
        )

        # CLUSTER 1: an authority-unresolved program never carries economics.
        if entry["is_fully_priced"]:
            for slug in slugs:
                assert not blocks_economic_candidacy(slug), (
                    f"{slug} is authority-blocked yet priced on a new project"
                )

        # CLUSTER 16: no raw jurisdiction code reaches the producer.
        if entry.get("primary_jurisdiction"):
            assert entry.get("jurisdiction_display_name"), (
                f"{entry['primary_jurisdiction']} served without a display name"
            )
        for allocation in entry.get("component_allocations") or []:
            assert allocation.get("jurisdiction_display_name"), (
                f"{allocation.get('jurisdiction_code')} component served raw"
            )

        # CLUSTER 7: no priced segment exceeds its own declared dollar cap.
        for segment in entry.get("segments") or []:
            slug = segment.get("program_slug")
            if not slug or not segment.get("executable", True):
                continue
            cap, _kind, _basis = _resolve_incentive_dollar_cap(slug)
            if cap:
                assert (segment.get("incentive_ceiling_usd") or 0.0) <= cap + 0.01, (
                    f"{slug} exceeded its dollar cap on a new project"
                )

    # CLUSTER 11: default inclusion is never reported as explicit statute.
    for entry in priced:
        for segment in entry.get("segments") or []:
            for line in segment.get("qualification_trace") or []:
                reason = (line.get("reason") or "").lower()
                if "included by default" in reason:
                    assert line["authority_basis"] != "explicit_statute", (
                        "a default-included line claimed express statutory support"
                    )


async def test_new_production_read_path_is_pure(
    db: AsyncSession, clean_slate_project: Project,
):
    """Read purity must hold for a project created after the repair, not only
    for the seeded fixtures it was developed against."""
    from sqlalchemy import text

    await ensure_current_budget_routed(db, clean_slate_project.id)
    await evaluate_project(db, str(clean_slate_project.id))

    async def snapshot() -> dict:
        counts = {}
        for table in ("budget_documents", "production_structures", "project_facts"):
            counts[table] = (await db.execute(
                text(f"select count(*) from {table} where project_id = :p"),
                {"p": str(clean_slate_project.id)},
            )).scalar()
        counts["home"] = str((await db.execute(
            text("select home_jurisdiction_id from projects where id = :p"),
            {"p": str(clean_slate_project.id)},
        )).scalar())
        return counts

    before = await snapshot()
    await build_production_and_structures(db, str(clean_slate_project.id))
    after = await snapshot()
    assert after == before, f"a GET mutated new-project state: {before} -> {after}"
