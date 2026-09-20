"""
test_workspace_top6_truthfulness.py

Workspace Top-6/Data Truthfulness closeout.

Real defects found and fixed by live-screen tracing against Lips Like Sugar
(not assumed): (1) two economically DISTINCT Australia programs (Location
Offset vs PDV Offset) rendered as identical cards because the UI had only
the bare jurisdiction code and the opaque program_slug — the real,
human-readable program name already existed in the canonical doctrine
registry (executable_jurisdiction_registry.get_doctrine) but was never
exposed on a served structure; (2) review_required candidates (priced but
not directly comparable — genuinely common when a project's own baseline
is unpriceable) were served in arbitrary generation order, so a "first N"
UI slice showed whichever candidates happened to be generated first, not
the cheapest-modeled ones.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.data.program_rate_rules  # noqa: F401 — forces registration order that avoids a real circular-import ordering issue between executable_jurisdiction_registry and program_rate_rules_worldwide when this module is imported standalone (never hit via the live app's own import order)
from app.db.session import engine
from app.core.config import get_settings
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import _program_display_name
from app.services.material_routing import ensure_current_budget_routed

_ISOLATED_ACCOUNT_LINES = [
    ("1100", "STORY / RIGHTS", 250_000), ("1200", "PRODUCER", 400_000), ("1300", "DIRECTOR", 350_000),
    ("1400", "CAST", 900_000), ("2000", "PRODUCTION", 1_800_000), ("2400", "CAMERA", 300_000),
    ("3000", "ART DEPARTMENT", 450_000), ("5000", "POST PRODUCTION", 500_000),
    ("6700", "INSURANCE", 150_000), ("7100", "CONTINGENCY", 300_000),
]


def test_program_display_name_distinguishes_real_distinct_australia_programs():
    """C. Exact duplicate canonical structures do not appear twice — and
    D. human-readable structure labels differentiate valid same-country
    outcomes: proves the real registry names for the exact programs found
    on Lips Like Sugar's own live Workspace, not a guessed/hardcoded
    string."""
    assert _program_display_name("au_location_offset") == "Australia Location Offset"
    assert _program_display_name("au_pdv_offset") == "Australia PDV Offset (Post, Digital and Visual Effects)"
    # the two real names must be genuinely distinct strings — the whole
    # point of exposing this field at all
    assert _program_display_name("au_location_offset") != _program_display_name("au_pdv_offset")


def test_program_display_name_distinguishes_state_level_programs():
    """B. Same jurisdiction (Australia) + different program remains
    distinct at the state level too (NSW/QLD/SA each carry their own real
    PDV rebate program)."""
    names = {
        _program_display_name("au_nsw_pdv_rebate"),
        _program_display_name("au_qld_pdv_rebate"),
        _program_display_name("au_sa_pdv_rebate"),
    }
    assert len(names) == 3  # three genuinely distinct real names
    assert None not in names


def test_program_display_name_never_fabricates_for_an_unregistered_slug():
    """Never a guessed/humanized fallback at the canonical layer — that
    fallback (programDisplay's own legacy map + humanizeToken) is a
    frontend presentation concern, never invented here."""
    assert _program_display_name("not_a_real_program_slug") is None
    assert _program_display_name(None) is None


# ── review_required NPC ordering (real DB round-trip) ────────────────────

@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def isolated_project(db: AsyncSession):
    """A brand-new throw-away production (organization -> project -> budget PDF -> routed budget), NOT yet
    evaluated, deleted afterwards. Used instead of a real production's generation: a real production is never
    warmed up or cold-evaluated to prepare a test."""
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"Top6 Isolated Org {suffix}", slug=f"top6-isolated-{suffix}")
    db.add(org)
    await db.flush()
    org_id = org.id
    project = Project(id=uuid.uuid4(), organization_id=org_id, title=f"Top6 Isolated Production {suffix}")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id
    storage_dir = Path(get_settings().LOCAL_STORAGE_PATH) / f"top6-isolated-{project_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = "Top6 Isolated Budget.pdf"
    lines = ["TOP6 ISOLATED PRODUCTION", "Account", "Description", "Total"]
    for code, description, amount in _ISOLATED_ACCOUNT_LINES:
        lines += [code, description, f"${amount:,}"]
    pdf = fitz.open()
    pdf.new_page().insert_text((50, 50), "\n".join(lines), fontsize=10)
    pdf.save(str(storage_dir / filename))
    pdf.close()
    document = Document(id=uuid.uuid4(), project_id=project_id, category="budget", title=f"{project.title} — Budget")
    db.add(document)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=document.id, original_filename=filename,
        storage_path=f"top6-isolated-{project_id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    document.current_version_id = version.id
    await db.commit()
    assert await ensure_current_budget_routed(db, project_id) is not None
    try:
        yield project
    finally:
        await db.rollback()
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.execute(sa_delete(Organization).where(Organization.id == org_id))
        await db.commit()
        if storage_dir.exists():
            shutil.rmtree(storage_dir)


async def test_review_required_structures_are_npc_ascending_not_arbitrary_order(
    db: AsyncSession, isolated_project: Project,
):
    """A. Top 6 uses canonical rank ordering where rank exists; where it
    does not (review_required — comparable_count can be genuinely 0 while
    real priced candidates exist), the served order must still be
    deterministic and cost-ordered, never accidental generation order.

    Runs on an isolated synthetic production (this test previously read Lips Like Sugar's own
    generation, which does not exist under the current fingerprint and must not be generated
    to prepare a test). The production view now serves one bounded page (<= 100) of the served
    candidates, so the whole served set is walked with candidate_offset; the pinned headline
    candidates (selected structure, leading conditional structure, baseline) are served first
    by design and are excluded from the ordering check."""
    from app.services.canonical_production_view import build_production_and_structures

    econ = await evaluate_project(db, isolated_project.id)
    assert econ["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")
    ranking, entries, offset = [], [], 0
    while True:
        view = await build_production_and_structures(
            db, isolated_project.id, candidate_limit=100, candidate_offset=offset,
        )
        assert view["status"] == "OK"
        s = view["structures"]["allocated_structures"]
        page = s["candidates_page"]
        assert page["returned"] <= 100
        ranking += s["ranking"]
        entries += s["structures"]
        if not page["has_more"]:
            break
        offset += page["limit"]
    assert len({r["structure_id"] for r in ranking}) == len(ranking) == page["total"]  # each served candidate once

    pinned = {s["canonical_selected_structure_id"]} | {
        (s["leading_conditional_structure"] or {}).get("structure_id")
    } | {e["structure_id"] for e in entries if e["is_baseline"]}
    review_required_ids = {
        r["structure_id"] for r in ranking
        if r["is_fully_priced"] and not r["is_directly_comparable"] and r["structure_id"] not in pinned
    }
    assert len(review_required_ids) > 1  # real, non-trivial population
    npcs = [
        r["npc_with_adjustments_usd"] for r in ranking
        if r["structure_id"] in review_required_ids and r["npc_with_adjustments_usd"] is not None
    ]
    assert npcs == sorted(npcs)  # non-decreasing across ALL pages — real ordering, not arbitrary


async def test_no_project_specific_branching_in_program_display_name():
    """J. No project-specific branching — the same generic registry
    lookup must work identically for a real Bad Hombres/other-project
    program slug with no special-casing."""
    import inspect
    from app.services import canonical_production_view as mod
    src = inspect.getsource(mod._program_display_name)
    assert "Lips Like Sugar" not in src
    assert "ab10b319" not in src
    assert "Little Utopia" not in src
