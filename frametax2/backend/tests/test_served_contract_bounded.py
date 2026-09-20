"""
Served-contract closeout: no served surface may load or embed the rejection universe or the whole
candidate set, and a fresh and a reused evaluation must present one shape.

  * GET /projects/{id}/structures/results    -- current-generation filtered, keyset-paginated;
                                                no unbounded compatibility path.
  * canonical_production_view                 -- generation summary + bounded non-rejected rows,
                                                returning ONE deterministic page (max 100) of the
                                                detailed candidates, exact counts, has_more/cursor.
  * GET /projects/{id}/evaluation/candidates  -- the remainder of those candidates, keyset-paged.
  * POST /evaluation/begin                    -- fresh vs EVALUATION_REUSED differ only in status.

ISOLATION: every test builds its own brand-new throw-away production (organization -> project ->
budget PDF on disk -> ordinary evaluation) and tears it down. No test evaluates -- or needs a
generation of -- Little Utopia, F#K Valentine's Day, Lips Like Sugar or Bad Hombres.
"""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import fitz
import pytest
from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.evaluation import begin_project_evaluation, list_served_candidates, list_unpriceable_candidates
from app.api.v1.structures import RESULTS_PAGE_DEFAULT_LIMIT, RESULTS_PAGE_MAX_LIMIT, list_structure_results
from app.core.config import get_settings
from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.schemas.production import StructureResultsPage
from app.services import canonical_evaluation as ce
from app.services.canonical_production_view import (
    CANDIDATE_PAGE_MAX_LIMIT,
    build_production_and_structures,
    encode_candidate_cursor,
)
from app.services.evaluation_contract import DISCOVERY_KEYS, apply_evaluation_contract, discovery_metadata
from app.services.material_routing import ensure_current_budget_routed

_ACCOUNT_LINES = [
    ("1100", "STORY / RIGHTS", 250_000), ("1200", "PRODUCER", 400_000), ("1300", "DIRECTOR", 350_000),
    ("1400", "CAST", 900_000), ("2000", "PRODUCTION", 1_800_000), ("2400", "CAMERA", 300_000),
    ("3000", "ART DEPARTMENT", 450_000), ("5000", "POST PRODUCTION", 500_000),
    ("6700", "INSURANCE", 150_000), ("7100", "CONTINGENCY", 300_000),
]


def _write_budget_pdf(path: Path) -> None:
    lines = ["SERVED CONTRACT ISOLATED PRODUCTION", "Account", "Description", "Total"]
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
async def isolated_project(db: AsyncSession):
    """A brand-new production created through the ordinary generic path (budget routed, NOT yet
    evaluated) and deleted afterwards."""
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"Served Contract Org {suffix}", slug=f"served-contract-{suffix}")
    db.add(org)
    await db.flush()
    org_id = org.id
    project = Project(id=uuid.uuid4(), organization_id=org_id, title=f"Served Contract Production {suffix}")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id
    storage_dir = Path(get_settings().LOCAL_STORAGE_PATH) / f"served-contract-{project_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = "Served Contract Budget.pdf"
    _write_budget_pdf(storage_dir / filename)
    document = Document(id=uuid.uuid4(), project_id=project_id, category="budget", title=f"{project.title} — Budget")
    db.add(document)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=document.id, original_filename=filename,
        storage_path=f"served-contract-{project_id}/{filename}", is_current=True,
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


async def _evaluate(db, project):
    econ = await ce.evaluate_project(db, project.id)
    assert econ["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED"), econ["status"]
    summary = await ce.load_generation_summary(db, project.id, econ["state_fingerprint"])
    return econ, summary


async def _add_stale_rows(db, project_id, current_fp):
    """One structure carrying a stale-fingerprint result and an old-engine result."""
    sid = uuid.uuid4()
    db.add(ProductionStructure(id=sid, project_id=project_id, name="STALE", jurisdiction_allocations=[], claimed_program_ids=[]))
    await db.flush()
    stale = []
    for engine_version, fp in ((ce.ENGINE_VERSION, "9" * 64), ("canonical-0.0.1", current_fp)):
        rid = uuid.uuid4()
        stale.append(rid)
        db.add(StructureCalculationResult(
            id=rid, structure_id=sid, engine_version=engine_version, input_fingerprint=fp, generation_ordinal=1,
            true_net_cost_usd=1, calculation_trace_json={"candidate_status": "PRICED", "is_baseline": True}))
    await db.flush()
    return sid, stale


# ── GET /structures/results ────────────────────────────────────────────────────────────────

async def test_results_route_pages_only_the_current_generation_exactly_once_in_generation_order(
    db: AsyncSession, isolated_project: Project,
):
    pid = isolated_project.id
    econ, summary = await _evaluate(db, isolated_project)
    _, stale_ids = await _add_stale_rows(db, pid, econ["state_fingerprint"])

    first = await list_structure_results(pid, historical=False, limit=200, cursor=None, db=db)
    assert first["status"] == "OK" and first["scope"] == "current_generation"
    assert first["engine_version"] == ce.ENGINE_VERSION and first["input_fingerprint"] == econ["state_fingerprint"]
    assert first["total_count"] == summary.total_rows  # exact, from the evaluation's own summary row
    assert first["limit"] == 200 and first["returned"] == len(first["results"]) <= 200
    assert first["order"] == "generation_ordinal"

    got, page, pages = list(first["results"]), first, 1
    while page["has_more"]:
        assert page["next_cursor"]
        page = await list_structure_results(pid, historical=False, limit=200, cursor=page["next_cursor"], db=db)
        assert page["total_count"] is None  # the total rides the first page only
        assert page["returned"] <= 200
        got += page["results"]
        pages += 1
    assert pages > 1, "the isolated generation must span several pages for this test to mean anything"
    assert page["next_cursor"] is None
    assert [r.generation_ordinal for r in got] == list(range(1, summary.total_rows + 1))  # every row, once, in order
    assert all(r.engine_version == ce.ENGINE_VERSION for r in got)
    # stale fingerprint + old engine rows exist in the table but are never served
    assert not ({r.id for r in got} & set(stale_ids))
    all_rows = (await db.execute(
        select(func.count()).select_from(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == pid)
    )).scalar()
    assert all_rows == summary.total_rows + 2 > len(got)


async def test_results_route_has_no_unbounded_path_and_validates_its_arguments(
    db: AsyncSession, isolated_project: Project,
):
    pid = isolated_project.id
    econ, summary = await _evaluate(db, isolated_project)
    await _add_stale_rows(db, pid, econ["state_fingerprint"])
    assert RESULTS_PAGE_DEFAULT_LIMIT == 50 and RESULTS_PAGE_MAX_LIMIT == 200
    page = await list_structure_results(pid, historical=False, limit=RESULTS_PAGE_DEFAULT_LIMIT, cursor=None, db=db)
    assert page["returned"] <= RESULTS_PAGE_DEFAULT_LIMIT
    served = StructureResultsPage.model_validate(page)  # the real response schema accepts the page
    assert served.results[0].generation_ordinal == 1 and served.results[0].id
    assert len(served.model_dump_json()) < 2_000_000  # a full default page, traces included, stays bounded
    # audit mode: bounded, keyset-paged by row id, spans every generation
    h1 = await list_structure_results(pid, historical=True, limit=25, cursor=None, db=db)
    assert h1["scope"] == "historical" and h1["returned"] == 25 and h1["has_more"] and h1["next_cursor"]
    h2 = await list_structure_results(pid, historical=True, limit=25, cursor=h1["next_cursor"], db=db)
    ids = [r.id for r in h1["results"]] + [r.id for r in h2["results"]]
    assert ids == sorted(ids) and len(set(ids)) == 50
    for kwargs in (dict(historical=False), dict(historical=True)):
        with pytest.raises(HTTPException) as bad:
            await list_structure_results(pid, limit=10, cursor="nope", db=db, **kwargs)
        assert bad.value.status_code == 422
    with pytest.raises(HTTPException) as missing:
        await list_structure_results(uuid.uuid4(), historical=False, limit=10, cursor=None, db=db)
    assert missing.value.status_code == 404
    assert summary.total_rows > 0


# ── canonical_production_view + /evaluation/candidates ────────────────────────────────────

async def test_production_view_returns_one_bounded_deterministic_page_with_exact_counts(
    db: AsyncSession, isolated_project: Project,
):
    pid = isolated_project.id
    econ, summary = await _evaluate(db, isolated_project)
    stale_sid, _ = await _add_stale_rows(db, pid, econ["state_fingerprint"])

    view = await build_production_and_structures(db, pid)
    view2 = await build_production_and_structures(db, pid)
    assert json.dumps(view, sort_keys=True) == json.dumps(view2, sort_keys=True)  # deterministic
    a = view["structures"]["allocated_structures"]
    page = a["candidates_page"]

    # never more than one bounded page of detailed candidates; never the rejected mass
    assert len(a["structures"]) == len(a["ranking"]) == page["returned"] <= CANDIDATE_PAGE_MAX_LIMIT
    assert all(e["candidate_status"] != "RULE_REJECTED" for e in a["structures"])
    served_total = len(summary.non_rejected_ordinals)
    assert page["total"] == served_total  # every served (non-rejected) candidate is reachable through the pages
    assert page["has_more"] is (served_total > page["returned"]) and (page["next_cursor"] is not None) is page["has_more"]
    assert [e["structure_id"] for e in a["structures"]] == [r["structure_id"] for r in a["ranking"]]
    assert str(stale_sid) not in {e["structure_id"] for e in a["structures"]}  # stale generations excluded
    # headline candidates come first (baseline is served on page 1)
    if econ["baseline"] is not None:  # a baseline (when the production has one) is always served on page 1
        baseline = next(e for e in a["structures"] if e["is_baseline"])
        assert baseline["npc_verified_usd"] == econ["baseline"]["true_net_cost_usd"]
    else:
        assert not any(e["is_baseline"] for e in a["structures"])
    if a["canonical_selected_structure_id"]:
        assert a["structures"][0]["structure_id"] == a["canonical_selected_structure_id"]

    # exact counts computed over ALL served candidates, not just the page
    acc = a["candidate_accounting"]
    assert acc["unpriceable_count"] == summary.unpriced_count == econ["unpriceable_count"]
    assert acc["comparable_count"] + acc["review_required_count"] == summary.priced_count
    assert a["discovery"]["generated_structures"] == summary.total_rows
    universe = a["rejection_universe"]
    assert universe["total_count"] == summary.unpriced_count and universe["by_disposition"] == econ["unpriceable_by_disposition"]
    assert universe["first_page"]["returned"] <= ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert len(a["unlockable_alternatives"]) <= CANDIDATE_PAGE_MAX_LIMIT
    assert a["unlockable_alternatives_has_more"] is (a["unlockable_alternatives_total"] > len(a["unlockable_alternatives"]))
    assert len(json.dumps(a["coverage"]["executable_jurisdictions"])) < 20_000  # distinct jurisdictions only
    assert len(json.dumps(view)) < 8_000_000  # 100 detailed candidates (<= ~50 KB each) + counts, never the universe

    # a small page limit forces real pagination through the same builder
    small = await build_production_and_structures(db, pid, candidate_limit=7)
    sa = small["structures"]["allocated_structures"]
    assert len(sa["structures"]) == min(7, served_total) and sa["candidates_page"]["limit"] == 7
    assert sa["candidate_accounting"] == acc  # counts do not depend on the page


async def test_candidates_route_pages_every_served_candidate_exactly_once_and_refuses_foreign_cursors(
    db: AsyncSession, isolated_project: Project,
):
    pid = isolated_project.id
    econ, summary = await _evaluate(db, isolated_project)
    expected = {
        str(s.id) for s, _ in await ce.load_retained_rows(db, pid, econ["state_fingerprint"], summary)
    }
    assert len(expected) == len(summary.non_rejected_ordinals)
    assert len(expected) > 40, "the served set must span several 20-row pages for this walk to mean anything"

    async def walk():
        seen, cursor = [], None
        while True:
            page = await list_served_candidates(pid, limit=20, cursor=cursor, db=db)
            assert page["status"] == "OK" and page["input_fingerprint"] == econ["state_fingerprint"]
            assert page["returned"] == len(page["structures"]) == len(page["ranking"]) <= 20
            assert page["total"] == len(expected)
            seen += [e["structure_id"] for e in page["structures"]]
            cursor = page["next_cursor"]
            assert page["has_more"] is (cursor is not None)
            if not page["has_more"]:
                return seen
    first, second = await walk(), await walk()
    assert len(first) == len(set(first)) == len(expected) and set(first) == expected  # once each, none dropped
    assert first == second  # deterministic order
    # page 1 of the route == the production view's own page (same sequence)
    view_page = (await build_production_and_structures(db, pid, candidate_limit=20))["structures"]["allocated_structures"]
    assert [e["structure_id"] for e in view_page["structures"]] == first[:20]

    fake = encode_candidate_cursor("f" * 16, 20)  # minted for some other generation
    with pytest.raises(HTTPException) as foreign:
        await list_served_candidates(pid, limit=20, cursor=fake, db=db)
    assert foreign.value.status_code == 409
    with pytest.raises(HTTPException) as bad:
        await list_served_candidates(pid, limit=20, cursor="nope", db=db)
    assert bad.value.status_code == 422
    with pytest.raises(HTTPException) as missing:
        await list_served_candidates(uuid.uuid4(), limit=20, cursor=None, db=db)
    assert missing.value.status_code == 404


# ── fresh vs reused ───────────────────────────────────────────────────────────────────────

async def test_fresh_and_reused_evaluation_responses_differ_only_in_status(db: AsyncSession, isolated_project: Project):
    pid = isolated_project.id
    fresh_raw = await ce.evaluate_project(db, pid)  # function-level, un-normalized, a genuinely FRESH generation
    assert fresh_raw["status"] == "EVALUATION_COMPLETE"
    # the served metadata is derived by the same discovery pass evaluate_project() runs
    meta = await discovery_metadata(db, pid)
    assert meta == {k: fresh_raw[k] for k in DISCOVERY_KEYS} and meta["discovery_examined"] > 0

    fresh = await apply_evaluation_contract(db, pid, fresh_raw)
    reused = await begin_project_evaluation(pid, db)  # the served route, on the now-existing generation
    assert reused["status"] == "EVALUATION_REUSED" and fresh["status"] == "EVALUATION_COMPLETE"
    assert set(fresh) == set(reused)
    for key in fresh:
        if key != "status":
            assert fresh[key] == reused[key], key  # engine version, fingerprint, discovery, counts, ranking, first page
    assert fresh["engine_version"] == ce.ENGINE_VERSION
    assert len(fresh["unpriceable"]) <= ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert len(json.dumps({k: reused[k] for k in ("unpriceable", "unpriceable_page", "unpriceable_by_reason")})) < 200_000
    # the reuse created no rows
    rows = (await db.execute(
        select(func.count()).select_from(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == pid)
    )).scalar()
    assert rows == (await ce.load_generation_summary(db, pid, fresh["state_fingerprint"])).total_rows
    # the rejection universe is reachable from the same generation, page by page
    page = await list_unpriceable_candidates(pid, limit=40, cursor=None, db=db)
    assert page["total_unpriceable_count"] == fresh["unpriceable_count"]
