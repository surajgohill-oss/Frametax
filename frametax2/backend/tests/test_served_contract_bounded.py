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
#: Extra movable-component lines that make the generic discovery run its ordinary-component-hybrid and
#: multi-component best-first searches (hundreds of thousands of candidates, hundreds of dominance proofs).
_HYBRID_EXTRA_LINES = [("5400", "VISUAL EFFECTS VFX", 350_000), ("5900", "MUSIC SCORE COMPOSER", 200_000)]


def _write_budget_pdf(path: Path, extra_lines=()) -> None:
    lines = ["SERVED CONTRACT ISOLATED PRODUCTION", "Account", "Description", "Total"]
    for code, description, amount in [*_ACCOUNT_LINES, *extra_lines]:
        lines += [code, description, f"${amount:,}"]
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "\n".join(lines), fontsize=10)
    doc.save(str(path))
    doc.close()


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _isolated_project_factory(db: AsyncSession, extra_lines=()):
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
    _write_budget_pdf(storage_dir / filename, extra_lines)
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




@pytest.fixture
async def isolated_project(db: AsyncSession):
    async for project in _isolated_project_factory(db):
        yield project


@pytest.fixture
async def isolated_hybrid_project(db: AsyncSession):
    async for project in _isolated_project_factory(db, _HYBRID_EXTRA_LINES):
        yield project



def _first_diff(a, b, path=""):
    """The first differing path between two JSON-like values (bounded, cheap). Replaces a raw string comparison of two multi-MB documents: on a mismatch pytest
    spent minutes computing a character diff, which looked like a hang."""
    if type(a) is not type(b):
        return path, str(a)[:120], str(b)[:120]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                return f"{path}/{k}", "missing" if k not in a else "present", "missing" if k not in b else "present"
            d = _first_diff(a[k], b[k], f"{path}/{k}")
            if d:
                return d
    elif isinstance(a, list):
        if len(a) != len(b):
            return path, f"len {len(a)}", f"len {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = _first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
    elif a != b:
        return path, str(a)[:120], str(b)[:120]
    return None


def _assert_same_view(a, b):
    import hashlib
    da, db_ = (hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest() for v in (a, b))
    assert da == db_, f"served view is not deterministic; first difference: {_first_diff(a, b)}"


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
    assert first["total_count"] == summary.persisted_rows  # exact, from the evaluation's own summary row (rows only; rejections are counted)
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
    assert [r.generation_ordinal for r in got] == list(range(1, summary.persisted_rows + 1))  # every row, once, in order
    assert all(r.engine_version == ce.ENGINE_VERSION for r in got)
    # stale fingerprint + old engine rows exist in the table but are never served
    assert not ({r.id for r in got} & set(stale_ids))
    all_rows = (await db.execute(
        select(func.count()).select_from(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == pid)
    )).scalar()
    assert all_rows == summary.persisted_rows + 2 > len(got)


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
    assert summary.persisted_rows > 0


# ── canonical_production_view + /evaluation/candidates ────────────────────────────────────

async def test_production_view_returns_one_bounded_deterministic_page_with_exact_counts(
    db: AsyncSession, isolated_project: Project,
):
    pid = isolated_project.id
    econ, summary = await _evaluate(db, isolated_project)
    stale_sid, _ = await _add_stale_rows(db, pid, econ["state_fingerprint"])

    view = await build_production_and_structures(db, pid)
    view2 = await build_production_and_structures(db, pid)
    _assert_same_view(view, view2)  # deterministic
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
    # the persisted-row page is bounded by the default limit; the jurisdiction-accounting rows are appended beside it and counted separately
    # (accounting_rows), bounded by the number of jurisdictions examined, never by the rejection universe
    assert universe["first_page"]["returned"] - universe["first_page"].get("accounting_rows", 0) <= ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert universe["first_page"].get("accounting_rows", 0) <= 400
    assert len(a["unlockable_alternatives"]) <= CANDIDATE_PAGE_MAX_LIMIT
    assert a["unlockable_alternatives_has_more"] is (a["unlockable_alternatives_total"] > len(a["unlockable_alternatives"]))
    assert len(json.dumps(a["coverage"]["executable_jurisdictions"])) < 20_000  # distinct jurisdictions only
    # the payload-size contract is its own test (below) so a size regression cannot hide the pagination assertions that follow

    # a small page limit forces real pagination through the same builder
    small = await build_production_and_structures(db, pid, candidate_limit=7)
    sa = small["structures"]["allocated_structures"]
    assert len(sa["structures"]) == min(7, served_total) and sa["candidates_page"]["limit"] == 7
    assert sa["candidate_accounting"] == acc  # counts do not depend on the page


async def test_production_view_payload_stays_under_the_bounded_size_contract(db: AsyncSession, isolated_project: Project):
    await _evaluate(db, isolated_project)
    view = await build_production_and_structures(db, isolated_project.id)
    a = view["structures"]["allocated_structures"]
    sizes = sorted(((len(json.dumps(v)), k) for k, v in a.items()), reverse=True)[:6]
    total = len(json.dumps(view))
    assert total < 8_000_000, f"100 detailed candidates (<= ~50 KB each) + counts, never the universe; got {total} bytes, largest sections {sizes}"


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
    assert rows == (await ce.load_generation_summary(db, pid, fresh["state_fingerprint"])).persisted_rows
    # the rejection universe is reachable from the same generation, page by page
    page = await list_unpriceable_candidates(pid, limit=40, cursor=None, db=db)
    assert page["total_unpriceable_count"] == fresh["unpriceable_count"]


# ── bounded candidate retention: legacy full enumeration vs bounded retention, end to end ────

async def test_isolated_production_legacy_full_enumeration_equals_bounded_retention(
    db: AsyncSession, isolated_project: Project, monkeypatch,
):
    """The REAL evaluate_project() on a throw-away production, run twice on identical inputs: once as the
    LEGACY full enumeration (every candidate a physical row, exactly what canonical-1.88.0 wrote) and once
    with bounded candidate retention using a SMALL policy (top-3 global / per type) so eviction really
    happens. Same winner, ranking, best-per-jurisdiction, top-per-family, economics and accounting."""
    import re
    from collections import Counter
    from sqlalchemy import text
    from app.services import candidate_aggregation as cagg, candidate_retention as cret
    from app.services import canonical_production_view as cpv
    from app.services.economic_identity import canonical_economic_identity

    pid = isolated_project.id
    Real = ce._BulkEvaluationWriter

    class _LegacyWriter(Real):
        def __init__(self, session, *a, **k):
            super().__init__(session, *a, bounded_retention=False, **k)

    legacy_engine = "canonical-test-legacy-enumeration"
    with monkeypatch.context() as m:
        m.setattr(ce, "_BulkEvaluationWriter", _LegacyWriter)
        m.setattr(ce, "ENGINE_VERSION", legacy_engine)
        m.setattr(cpv, "ENGINE_VERSION", legacy_engine)
        m.setattr(cpv, "TYPE_TOP", 3)
        legacy_econ = await ce.evaluate_project(db, pid)
        assert legacy_econ["status"] == "EVALUATION_COMPLETE"
        legacy_view = (await build_production_and_structures(db, pid))["structures"]["allocated_structures"]
    monkeypatch.setattr(cret, "GLOBAL_TOP", 3)
    monkeypatch.setattr(cret, "TYPE_TOP", 3)
    monkeypatch.setattr(cpv, "TYPE_TOP", 3)
    new_econ = await ce.evaluate_project(db, pid)
    assert new_econ["status"] == "EVALUATION_COMPLETE" and new_econ["engine_version"] == ce.ENGINE_VERSION
    new_view = (await build_production_and_structures(db, pid))["structures"]["allocated_structures"]
    fp = new_econ["state_fingerprint"]
    assert legacy_econ["state_fingerprint"] == fp

    async def rows(engine_version):
        return (await db.execute(text(
            "SELECT ps.id AS sid, ps.name, ps.description, ps.claimed_program_ids, ps.jurisdiction_allocations, scr.structure_type, "
            "       scr.total_budget_usd, scr.total_incentive_value_usd, scr.true_net_cost_usd, scr.risk_adjusted_net_cost_usd, "
            "       scr.has_unverified_inputs, scr.warnings, scr.economic_identity, scr.calculation_trace_json AS trace "
            "FROM structure_calculation_results scr JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :p AND scr.input_fingerprint = :fp AND scr.engine_version = :ev "
            "ORDER BY ps.name, scr.calculation_trace_json::text"), {"p": pid, "fp": fp, "ev": engine_version})).all()

    legacy_rows, new_rows = await rows(legacy_engine), await rows(ce.ENGINE_VERSION)
    summary = await ce.load_generation_summary(db, pid, fp)

    # ---- exact accounting: every candidate the legacy run persisted is a retained row or counted
    assert summary.total_rows == len(legacy_rows) == len(new_rows) + summary.aggregated_candidates
    assert summary.persisted_rows == len(new_rows)
    assert summary.aggregated_candidates > 0, "the small policy must actually aggregate"
    agg_sum = (await db.execute(text(
        "SELECT coalesce(sum(candidate_count), 0), count(*) FROM evaluation_candidate_aggregates "
        "WHERE project_id = :p AND input_fingerprint = :fp AND engine_version = :ev"),
        {"p": pid, "fp": fp, "ev": ce.ENGINE_VERSION})).one()
    assert agg_sum[0] == summary.aggregated_candidates and agg_sum[1] == summary.aggregate_groups

    # ---- the retained set is EXACTLY the policy applied to the full legacy enumeration (independent sort)
    def status(r):
        return (r.trace or {}).get("candidate_status")

    def is_priced(r):
        return status(r) == "PRICED" and r.true_net_cost_usd is not None

    def ident(r):
        return r.economic_identity or canonical_economic_identity(r.structure_type, r.trace)

    priced = [r for r in legacy_rows if is_priced(r)]
    INF = float("inf")
    vkey = lambda r: (float(r.true_net_cost_usd), ident(r))
    akey = lambda r: (float(r.risk_adjusted_net_cost_usd) if r.risk_adjusted_net_cost_usd is not None else INF, ident(r))
    keep = set()
    for key in (vkey, akey):
        keep |= {r.name for r in sorted(priced, key=key)[:3]}
        for t in {r.structure_type for r in priced}:
            keep |= {r.name for r in sorted((r for r in priced if r.structure_type == t), key=key)[:3]}
        for j in {(r.trace or {}).get("primary_jurisdiction") for r in priced if r.structure_type in cret.LOCAL_STACK_TYPES}:
            pool = [r for r in priced if r.structure_type in cret.LOCAL_STACK_TYPES and (r.trace or {}).get("primary_jurisdiction") == j]
            keep |= {sorted(pool, key=key)[0].name}
    by_uuid = {str(r.sid): r for r in legacy_rows}
    by_gen = {(r.trace or {}).get("structural_generator_structure_id"): r for r in legacy_rows if (r.trace or {}).get("structural_generator_structure_id")}
    for r in legacy_rows:
        t = r.trace or {}
        if t.get("is_baseline") or (not is_priced(r) and not (status(r) == "RULE_REJECTED" and r.true_net_cost_usd is None)):
            keep.add(r.name)
            ref = t.get("incumbent_structure_id") if status(r) == "DOMINATED_WITH_PROOF" else None
            if ref:
                keep.add((by_uuid.get(str(ref)) or by_gen[ref]).name)
    assert {r.name for r in new_rows} == keep
    assert len(new_rows) < len(legacy_rows)

    # ---- retained rows: byte-identical economics (ids embedded in traces are per-generation)
    _uuid = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    # The bounded writer STAMPS two persisted-contract fields the legacy (canonical-1.88.0) enumeration never wrote: the GD-2 structural classification and
    # the lazily enriched marginal-jurisdiction benefits (1.97.0). They are additions, not economics: the byte-identical comparison excludes exactly these
    # two keys, and the retained rows are separately required to CARRY them (below), so the coverage is kept rather than dropped.
    _STAMPED = ("structural_classification", "marginal_jurisdiction_benefits_usd")

    def no_ids(v, top=True):
        if isinstance(v, dict):
            return {k: no_ids(x, False) for k, x in v.items() if k not in ("engine_version", "input_fingerprint") and not (top and k in _STAMPED)}
        if isinstance(v, list):
            return [no_ids(x, False) for x in v]
        return "<id>" if isinstance(v, str) and _uuid.match(v) else v

    def mask(r):
        return (r.name, r.description, r.claimed_program_ids, r.jurisdiction_allocations, r.structure_type, r.total_budget_usd,
                r.total_incentive_value_usd, r.true_net_cost_usd, r.risk_adjusted_net_cost_usd, r.has_unverified_inputs,
                r.warnings, r.economic_identity, repr(sorted(no_ids(r.trace or {}).items())))
    legacy_masked = {r.name: mask(r) for r in legacy_rows}
    assert all(mask(r) == legacy_masked[r.name] for r in new_rows)
    assert all((r.trace or {}).get("structural_classification") for r in new_rows), "every retained row carries the stamped classification"
    assert all("structural_classification" not in (r.trace or {}) for r in legacy_rows), "the legacy enumeration is the pre-GD-2 contract"
    assert all("marginal_jurisdiction_benefits_usd" in (r.trace or {}) for r in new_rows if r.structure_type == "hybrid" and is_priced(r))

    # ---- aggregated remainder == regrouping of the legacy rows that were not retained
    from app.services.structural_classification import classify_structure

    def stamped(r):      # the legacy rows pre-date the GD-2 stamp the bounded writer applies at the single call site, so apply the same pure classification
        t = dict(r.trace or {})
        t["structural_classification"] = classify_structure(t, r.structure_type, status(r) == "PRICED")
        return t
    regroup = Counter(
        cagg.candidate_group_key(cagg.candidate_group_identity(status(r) or "", r.structure_type, stamped(r), r.claimed_program_ids))
        for r in legacy_rows if r.name not in keep)
    got = {k: c for k, c in (await db.execute(text(
        "SELECT group_key, candidate_count FROM evaluation_candidate_aggregates "
        "WHERE project_id = :p AND input_fingerprint = :fp AND engine_version = :ev"),
        {"p": pid, "fp": fp, "ev": ce.ENGINE_VERSION})).all()}
    assert got == dict(regroup)

    # ---- served: same exact totals, dispositions, baseline, winner, ranking head, best-per-jurisdiction, top-per-family
    for key in ("priced_count", "unpriceable_count", "baseline", "unpriceable_by_disposition", "unpriceable_by_reason"):
        assert new_econ[key] == legacy_econ[key], key

    def econ_of(e):
        return None if e is None else {k: v for k, v in e.items() if k != "structure_id"}
    assert econ_of(new_econ["top_result"]) == econ_of(legacy_econ["top_result"])
    assert new_econ["retained_priced_count"] == len([r for r in new_rows if is_priced(r)]) < new_econ["priced_count"]
    legacy_ranked = [econ_of(e) for e in legacy_econ["ranked"]]
    assert [econ_of(e) for e in new_econ["ranked"]][:3] == legacy_ranked[:3]              # ranking head identical
    assert new_econ["candidate_aggregates"]["accounting_holds"] and legacy_econ["candidate_aggregates"]["group_count"] == 0

    def compact(entries):
        return [(e["economic_identity"], e["npc_verified_usd"], e["npc_with_adjustments_usd"], e["primary_jurisdiction"], e["structure_type"])
                for e in entries]
    assert new_view["best_per_jurisdiction"].keys() == legacy_view["best_per_jurisdiction"].keys()
    for j, e in legacy_view["best_per_jurisdiction"].items():
        assert compact([new_view["best_per_jurisdiction"][j]]) == compact([e])
    assert new_view["top_by_structure_type"].keys() == legacy_view["top_by_structure_type"].keys()
    for t, entries in legacy_view["top_by_structure_type"].items():
        assert compact(new_view["top_by_structure_type"][t]) == compact(entries) and len(entries) <= 3
    for key in ("comparable_count", "review_required_count", "unpriceable_count"):
        assert new_view["candidate_accounting"][key] == legacy_view["candidate_accounting"][key], key
    assert new_view["canonical_selected_structure_id"] is None or (
        [e["economic_identity"] for e in new_view["structures"] if e["structure_id"] == new_view["canonical_selected_structure_id"]]
        == [e["economic_identity"] for e in legacy_view["structures"] if e["structure_id"] == legacy_view["canonical_selected_structure_id"]])
    assert new_view["retention"]["generated_candidates"] == len(legacy_rows) == summary.total_rows
    assert new_view["retention"]["retained_rows"] == len(new_rows)


# ── real hybrid + multi-component search: bounded retention, proofs, incumbents, reuse ──────

_BOUNDED_PARTNERS = ("GB", "IE", "MT", "FR", "CA-ON", "US-GA")


def _restrict_partners(monkeypatch):
    """Bound the hybrid search universe to a handful of partners (home + _BOUNDED_PARTNERS) so a full hybrid enumeration finishes in seconds while keeping
    the hybrid / multi-component incumbent sites and dominance proofs this test exists to cover. The unbounded 250k-candidate production is the heavy
    check in tests/heavy_synthetic/check_hybrid_bounded_retention_full.py (explicit path)."""
    import dataclasses
    real = ce.discover_executable_jurisdictions

    def bounded(*a, **k):
        d = real(*a, **k)
        keep = set(_BOUNDED_PARTNERS) | {k.get("home_code")}
        return dataclasses.replace(
            d, accepted=tuple((c, sl) for c, sl in d.accepted if c in keep),
            examinations=tuple(e for e in d.examinations if e.jurisdiction_code in keep))
    monkeypatch.setattr(ce, "discover_executable_jurisdictions", bounded)


async def test_hybrid_production_bounded_retention_keeps_every_proof_and_incumbent_and_reuses_for_free(
    db: AsyncSession, isolated_hybrid_project: Project, monkeypatch,
):
    """The hybrid and multi-component incumbent-tracking sites and the dominance proofs, on a bounded partner universe: bounded retention keeps the accounting
    exact against a LEGACY full enumeration of the SAME universe (measured in this test, not pinned), keeps every proof's referenced incumbent, stays bounded,
    and an identical-input rerun is a zero-row reuse."""
    await assert_hybrid_bounded_retention(db, isolated_hybrid_project, monkeypatch, restrict=True)


async def assert_hybrid_bounded_retention(db, isolated_hybrid_project, monkeypatch, *, restrict: bool):
    """The shared body: restrict=True bounds the partner universe (default suite); restrict=False runs the unbounded production (tests/heavy_synthetic), measuring its own legacy
    enumeration instead of pinning counts."""
    from collections import Counter
    from sqlalchemy import text
    from app.services import candidate_retention as cret, canonical_production_view as cpv
    pid = isolated_hybrid_project.id
    if restrict:
        _restrict_partners(monkeypatch)
    Real = ce._BulkEvaluationWriter

    class _LegacyWriter(Real):
        def __init__(self, session, *a, **k):
            super().__init__(session, *a, bounded_retention=False, **k)

    legacy_engine = "canonical-test-legacy-enumeration"
    with monkeypatch.context() as m:
        m.setattr(ce, "_BulkEvaluationWriter", _LegacyWriter)
        m.setattr(ce, "ENGINE_VERSION", legacy_engine)
        m.setattr(cpv, "ENGINE_VERSION", legacy_engine)
        legacy = await ce.evaluate_project(db, pid)
        assert legacy["status"] == "EVALUATION_COMPLETE"
    legacy_rows = (await db.execute(text(
        "select scr.calculation_trace_json->>'candidate_status' st from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev"), {"p": pid, "ev": legacy_engine})).all()
    measured = Counter(r.st for r in legacy_rows)
    legacy_total = sum(measured.values())
    assert measured["PRICED"] > 0 and measured["DOMINATED_WITH_PROOF"] > 0, "the bounded universe must still exercise hybrid pricing and dominance proofs"

    monkeypatch.setattr(cret, "GLOBAL_TOP", 3)
    monkeypatch.setattr(cret, "TYPE_TOP", 3)
    monkeypatch.setattr(cpv, "TYPE_TOP", 3)
    econ = await ce.evaluate_project(db, pid)          # commit() enforces generated == persisted + aggregated
    await assert_bounded_generation(db, pid, econ, measured, legacy_total, legacy_engine)


async def assert_bounded_generation(db, pid, econ, measured, legacy_total, legacy_engine, timings=None):
    """Everything asserted about a bounded generation against a measured legacy enumeration (statuses ``measured``, rows ``legacy_total``, rows persisted under
    ``legacy_engine``): coverage and accounting, bounded persistence, the retained global ranking against the legacy ranking, proof completeness and retained incumbents,
    group accounting, and the zero-row reuse. Shared by the independent-enumeration body and the shared-stream body (tests/retention_shared_stream.py)."""
    import time
    from sqlalchemy import text
    from app.services import candidate_retention as cret
    assert econ["status"] == "EVALUATION_COMPLETE"
    fp = econ["state_fingerprint"]
    summary = await ce.load_generation_summary(db, pid, fp)
    assert summary.total_rows == legacy_total == summary.persisted_rows + summary.aggregated_candidates
    assert summary.priced_count == measured["PRICED"] == econ["priced_count"]
    by = dict(summary.by_disposition)
    assert by == {k: v for k, v in measured.items() if k != "PRICED"}      # exact, incl. aggregated rejections

    G = "ps.project_id=:p and scr.engine_version=:ev and scr.input_fingerprint=:fp"
    P = {"p": pid, "ev": ce.ENGINE_VERSION, "fp": fp}
    J = "structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id"
    persisted = (await db.execute(text(f"select count(*) from {J} where {G}"), P)).scalar()
    assert persisted == summary.persisted_rows < legacy_total                              # bounded by policy, not enumeration
    assert summary.aggregated_candidates > 0, "the small policy must actually aggregate"
    types = (await db.execute(text(f"select count(distinct scr.structure_type) from {J} where {G}"), P)).scalar()
    non_priced = (await db.execute(text(f"select count(*) from {J} where {G} and scr.true_net_cost_usd is null"), P)).scalar()
    priced_rows = persisted - non_priced
    assert priced_rows <= cret.BoundedRetention().bound(structure_types=types + 2, jurisdictions=64) + 8

    # ranking: the bounded generation's retained global top equals the legacy enumeration's own top (verified NPC, ties by canonical economic identity); the legacy
    # rows are a separate writer's persistence, so this compares two independent row sets, never a writer with itself
    top = lambda fp: text(
        "select scr.true_net_cost_usd npc, scr.economic_identity ident from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        f"where ps.project_id=:p and scr.engine_version=:ev {fp} and scr.calculation_trace_json->>'candidate_status'='PRICED' and scr.true_net_cost_usd is not null "
        "order by scr.true_net_cost_usd, scr.economic_identity limit 3")
    legacy_top = [tuple(r) for r in (await db.execute(top(""), {"p": pid, "ev": legacy_engine})).all()]
    bounded_top = [tuple(r) for r in (await db.execute(top("and scr.input_fingerprint=:fp"), P)).all()]
    assert legacy_top and bounded_top == legacy_top, ("retained global ranking differs from the legacy enumeration's", bounded_top, legacy_top)

    # every persisted proof is complete AND its incumbent is a persisted row
    proofs = (await db.execute(text(f"select scr.calculation_trace_json trace from {J} where {G} and scr.calculation_trace_json->>'candidate_status'='DOMINATED_WITH_PROOF'"), P)).all()
    assert len(proofs) == measured["DOMINATED_WITH_PROOF"]
    rows = (await db.execute(text(f"select ps.id::text sid, scr.calculation_trace_json->>'structural_generator_structure_id' gen from {J} where {G}"), P)).all()
    known = {r.sid for r in rows} | {r.gen for r in rows if r.gen}
    referenced = 0
    for (t,) in proofs:
        assert isinstance(t.get("incumbent_value_usd"), (int, float)) and t.get("stopping_inequality_holds") is True
        ref = t.get("incumbent_structure_id")
        if ref:
            referenced += 1
            assert str(ref) in known, f"a retained proof references a candidate that is not retained: {ref}"
    assert referenced > 0, "the fixture must exercise proof-referenced incumbents"

    # group accounting reconciles with the summary; the priced remainder is dominated by a retained row
    agg = (await db.execute(text(
        "select coalesce(sum(candidate_count),0), count(*), coalesce(sum(candidate_count) filter (where candidate_status='PRICED'),0) "
        "from evaluation_candidate_aggregates where project_id=:p and input_fingerprint=:fp and engine_version=:ev"), P)).one()
    assert agg[0] == summary.aggregated_candidates and agg[1] == summary.aggregate_groups and agg[2] == summary.aggregated_priced
    assert summary.aggregate_groups <= 5000 + 40 * 64
    assert (await db.execute(text(
        "select count(*) from evaluation_candidate_aggregates a where a.project_id=:p and a.input_fingerprint=:fp and a.engine_version=:ev "
        "and a.candidate_status='PRICED' and a.dominating_structure_id is null"), P)).scalar() == 0

    # identical-input rerun: a zero-row reuse
    counts = lambda: text("select (select count(*) from production_structures where project_id=:p), "
                          "(select count(*) from evaluation_candidate_aggregates where project_id=:p), "
                          "(select count(*) from evaluation_generation_summaries where project_id=:p)")
    before = tuple((await db.execute(counts(), {"p": pid})).one())
    t_reuse = time.perf_counter()
    again = await ce.evaluate_project(db, pid)
    if timings is not None:
        timings["reuse_seconds"] = round(time.perf_counter() - t_reuse, 2)
    assert again["status"] == "EVALUATION_REUSED"
    assert tuple((await db.execute(counts(), {"p": pid})).one()) == before
    assert again["priced_count"] == econ["priced_count"] and again["baseline"] == econ["baseline"]
