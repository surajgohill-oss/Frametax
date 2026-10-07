"""Final pre-Codex closeout (2026-10-07): real integration proofs on the ISOLATED pytest database with disposable projects.

Gate 1 -- project-scoped location toggle: frontend-equivalent request -> POST /api/v1/cineglobe/projects/{id}/locations ->
persisted ProjectLocationRequirement -> effective physical-requirement fingerprint change -> exactly one real evaluate_project
-> served production fit/status/reason changes; identical save -> zero evaluations; another project untouched; economics
(QPE, incentive, NPC, economic identity) never change from a location requirement alone.

Gate 2 -- parsed-budget persistence: a parsed BudgetDocument / BudgetLineItem set is reused by state reads and evaluations
(no parser call), even after parser-version drift; the one documented exception (committed-material routing refreshes a
stale parse in place) is pinned as current behaviour, not endorsed.

Never touches the four real productions: refuses to run against the acceptance database.
"""
from __future__ import annotations

import hashlib
import uuid

import httpx
import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.jurisdiction_location_capability import CELLS, NOT_SUPPORTED, SUPPORTED, UNRESOLVED_NEUTRAL
from app.db.session import engine
from app.main import app
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import SpendCategory
from app.models.jurisdiction import Jurisdiction
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_location_requirement import ProjectLocationRequirement
from app.services import canonical_evaluation as ce
from app.services import material_routing as mr
from app.services.canonical_production_view import build_production_and_structures

ISOLATED_DB = "frametax2_pytest"


@pytest.fixture(autouse=True)
def _isolated_database_only():
    assert engine.url.database == ISOLATED_DB, f"refusing to run against {engine.url.database!r} (real productions)"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def eval_calls(monkeypatch):
    """Counts REAL evaluate_project invocations made by the endpoint (the endpoint imports it from the module at call time)."""
    calls = []
    real = ce.evaluate_project

    async def counting(session, project_id):
        calls.append(str(project_id))
        return await real(session, project_id)

    monkeypatch.setattr(ce, "evaluate_project", counting)
    return calls


async def _project(db, label, lines, home="US-NM"):
    jur = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == home))).scalars().first()
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"{label} Org {suffix}", slug=f"pre-codex-{suffix}")
    db.add(org)
    await db.flush()
    total = sum(a for _, a, _ in lines)
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"{label} {suffix}",
                home_jurisdiction_id=jur.id if jur else None, total_budget_usd=total)
    db.add(p)
    await db.flush()
    doc = BudgetDocument(id=uuid.uuid4(), project_id=p.id, filename="b.pdf", file_type="pdf", is_active=True,
                         extraction_status="completed", total_budget_raw=total)
    db.add(doc)
    await db.flush()
    for desc, amt, cat in lines:
        db.add(BudgetLineItem(id=uuid.uuid4(), budget_document_id=doc.id, description=desc, amount_raw=amt, amount_usd=amt,
                              spend_category=cat))
    await db.commit()
    return p.id


async def _drop(db, *project_ids):
    for pid in project_ids:
        await db.execute(sa_delete(Project).where(Project.id == pid))
    await db.commit()


LINES = [
    ("2000 ATL WRITER FEE", 1_000_000.0, SpendCategory.ATL_WRITER.value),
    ("2001 BTL CREW LABOR", 3_000_000.0, SpendCategory.BTL_CREW_LABOR.value),
    ("3000 GENERAL ADMINISTRATION", 1_000_000.0, SpendCategory.GENERAL_ADMINISTRATION.value),
]


async def _post(pid, overrides):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/api/v1/cineglobe/projects/{pid}/locations", json={"overrides": overrides})


async def _current_fp(db, pid):
    return await ce.current_generation_fingerprint(db, pid)


async def _economics(db, pid):
    """economic_identity -> (QPE, incentive, NPC) over the current generation's retained PRICED rows."""
    fp = await _current_fp(db, pid)
    rows = (await db.execute(text(
        "SELECT r.economic_identity, r.total_qualifying_spend_usd, r.total_incentive_value_usd, r.true_net_cost_usd "
        "FROM structure_calculation_results r JOIN production_structures ps ON ps.id = r.structure_id "
        "WHERE ps.project_id = :pid AND r.engine_version = :ev AND r.input_fingerprint = :fp AND r.true_net_cost_usd IS NOT NULL"
    ), {"pid": pid, "ev": ce.ENGINE_VERSION, "fp": fp})).all()
    return {r[0]: (float(r[1] or 0), float(r[2] or 0), float(r[3])) for r in rows}


async def _fits(db, pid):
    view = await build_production_and_structures(db, str(pid))
    bpj = view["structures"]["allocated_structures"]["best_per_jurisdiction"]
    return {c: (e.get("production_fit_status"), tuple(e.get("production_fit_reasons") or ())) for c, e in bpj.items() if e}


async def test_project_scoped_location_toggle_real_integration(db: AsyncSession, eval_calls):
    pid = await _project(db, "Location Toggle", LINES)
    other = await _project(db, "Untouched Other", LINES)
    try:
        assert (await ce.evaluate_project(db, pid))["status"] == "EVALUATION_COMPLETE"
        assert (await ce.evaluate_project(db, other))["status"] == "EVALUATION_COMPLETE"
        eval_calls.clear()
        other_fp = await _current_fp(db, other)
        other_gens = (await db.execute(text("SELECT count(*) FROM evaluation_generation_summaries WHERE project_id = :p"), {"p": other})).scalar_one()
        base_econ = await _economics(db, pid)
        base_fits = await _fits(db, pid)
        assert base_econ and all(status == "UNKNOWN" for status, _ in base_fits.values())   # no requirement on file yet

        # unknown category is rejected, persists nothing, evaluates nothing
        r = await _post(pid, {"not_a_category": True})
        assert r.status_code == 422 and eval_calls == []

        # HARD requirement ON: one evaluation; supported / not supported / unresolved each served correctly
        r = await _post(pid, {"desert_arid": True})
        assert r.status_code == 200 and r.json()["changed"] and r.json()["evaluation_triggered"] and len(eval_calls) == 1
        row = (await db.execute(select(ProjectLocationRequirement).where(
            ProjectLocationRequirement.project_id == pid, ProjectLocationRequirement.category_key == "desert_arid"))).scalar_one()
        assert row.override is True
        fits = await _fits(db, pid)
        by_status = {s: [c for c in fits if CELLS.get((c, "desert_arid"), (None,))[0] == s]
                     for s in (SUPPORTED, NOT_SUPPORTED, UNRESOLVED_NEUTRAL)}
        assert all(by_status.values()), {k: len(v) for k, v in by_status.items()}
        for c in by_status[SUPPORTED]:
            assert fits[c][0] in ("STRONG", "WORKABLE") and not any("DESERT" in x for x in fits[c][1]), (c, fits[c])
        for c in by_status[NOT_SUPPORTED]:
            assert fits[c][0] == "WEAK" and any("DESERT_ENVIRONMENTS_NOT_SUPPORTED" in x for x in fits[c][1]), (c, fits[c])
        for c in by_status[UNRESOLVED_NEUTRAL]:
            assert fits[c][0] == "UNKNOWN" and any("DESERT_ENVIRONMENTS_NOT_ASSESSABLE" in x for x in fits[c][1]), (c, fits[c])
        assert await _economics(db, pid) == base_econ                               # QPE / incentive / NPC / identity unchanged

        # identical save: nothing changes, zero evaluations
        r = await _post(pid, {"desert_arid": True})
        assert r.status_code == 200 and not r.json()["changed"] and not r.json()["evaluation_triggered"] and len(eval_calls) == 1

        # restart / session reload preserves the saved state
        async with AsyncSession(engine, expire_on_commit=False) as fresh:
            from app.services.canonical_project_economics import build_ui_location_categories
            cats = await build_ui_location_categories(fresh, pid)
            assert cats["desert_arid"]["effective"] is True

        # hard requirement OFF: one evaluation; the hard reasons disappear
        r = await _post(pid, {"desert_arid": False})
        assert r.status_code == 200 and r.json()["evaluation_triggered"] and len(eval_calls) == 2
        fits_off = await _fits(db, pid)
        assert not any("DESERT" in x for _, reasons in fits_off.values() for x in reasons)
        assert await _economics(db, pid) == base_econ

        # SOFT requirement ON / OFF: evaluated once each, never blocking (no WEAK from a soft capability)
        r = await _post(pid, {"desert_arid": None, "urban_major_city": True})
        assert r.status_code == 200 and r.json()["evaluation_triggered"] and len(eval_calls) == 3
        soft = await _fits(db, pid)
        assert not any(status == "WEAK" for status, _ in soft.values())
        assert not any("URBAN" in x for _, reasons in soft.values() for x in reasons)
        assert await _economics(db, pid) == base_econ
        r = await _post(pid, {"urban_major_city": False})
        assert r.status_code == 200 and r.json()["evaluation_triggered"] and len(eval_calls) == 4
        assert await _economics(db, pid) == base_econ

        # the other project is untouched by every toggle above
        assert set(eval_calls) == {str(pid)}
        assert (await db.execute(select(func.count()).select_from(ProjectLocationRequirement).where(
            ProjectLocationRequirement.project_id == other))).scalar_one() == 0
        assert await _current_fp(db, other) == other_fp
        assert (await db.execute(text("SELECT count(*) FROM evaluation_generation_summaries WHERE project_id = :p"), {"p": other})).scalar_one() == other_gens
    finally:
        await _drop(db, pid, other)


_BUDGET_CSV = (
    "description,amount,department\n"
    "Director fee,50000,Above the Line\n"
    "Camera crew labor,75000,Below the Line\n"
    "Grip equipment rental,25000,Below the Line\n"
)


async def _budget_snapshot(db, pid):
    docs = (await db.execute(select(BudgetDocument).where(BudgetDocument.project_id == pid))).scalars().all()
    assert len(docs) == 1
    doc = docs[0]
    lines = (await db.execute(select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id)
                              .order_by(BudgetLineItem.id))).scalars().all()
    payload = [(str(li.id), li.description, li.spend_category, float(li.amount_usd or 0)) for li in lines]
    checksum = hashlib.sha256(repr(payload).encode()).hexdigest()
    return {"doc_id": str(doc.id), "dv": str(doc.document_version_id), "rows": len(lines), "checksum": checksum,
            "categories": sorted({p[2] or "" for p in payload}), "amounts": sorted(p[3] for p in payload)}, doc.parser_version


async def test_parsed_budget_is_persisted_and_never_reparsed_by_state_or_evaluation(db: AsyncSession, tmp_path, monkeypatch):
    from app.ingestion.budget_parser import BUDGET_PARSER_VERSION
    from app.services.canonical_production_state import CanonicalProductionStateBuilder

    path = tmp_path / "Budget.csv"
    path.write_bytes(_BUDGET_CSV.encode())
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"Budget Reuse Org {suffix}", slug=f"budget-reuse-{suffix}")
    db.add(org)
    await db.flush()
    pid = uuid.uuid4()
    nm = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == "US-NM"))).scalars().first()
    db.add(Project(id=pid, organization_id=org.id, title=f"Budget Reuse {suffix}", home_jurisdiction_id=nm.id))
    await db.flush()
    document = Document(id=uuid.uuid4(), project_id=pid, category="budget", title="Budget")
    db.add(document)
    await db.flush()
    version = DocumentVersion(id=uuid.uuid4(), document_id=document.id, original_filename="Budget.csv",
                              storage_path=str(path), is_current=True)
    db.add(version)
    await db.flush()
    document.current_version_id = version.id
    await db.commit()

    parses = []
    real_csv = mr.parse_budget_csv

    def counting_csv(*a, **k):
        parses.append("csv")
        return real_csv(*a, **k)

    monkeypatch.setattr(mr, "parse_budget_csv", counting_csv)
    try:
        # first routing parses once and persists the BudgetDocument / BudgetLineItem rows
        routed = await mr.ensure_current_budget_routed(db, pid)
        assert routed is not None and parses == ["csv"]
        snap, parser_version = await _budget_snapshot(db, pid)
        assert parser_version == BUDGET_PARSER_VERSION and snap["rows"] == 3 and snap["dv"] == str(version.id)
        parses.clear()

        # repeated state reads and evaluations reuse the persisted parse
        for _ in range(2):
            await CanonicalProductionStateBuilder(db).build(pid)
        first = await ce.evaluate_project(db, pid)
        second = await ce.evaluate_project(db, pid)
        assert first["status"] == "EVALUATION_COMPLETE", (first.get("status"), first.get("blockers"))
        assert second["status"] == "EVALUATION_REUSED", second.get("status")
        await build_production_and_structures(db, str(pid))
        assert parses == []
        assert (await _budget_snapshot(db, pid))[0] == snap
        assert (await db.execute(select(func.count()).select_from(DocumentVersion).where(
            DocumentVersion.document_id == document.id))).scalar_one() == 1

        # parser-version drift alone does not touch normal state / evaluation reads
        doc = (await db.execute(select(BudgetDocument).where(BudgetDocument.project_id == pid))).scalars().one()
        doc.parser_version = "0-stale"
        await db.commit()
        await CanonicalProductionStateBuilder(db).build(pid)
        await ce.evaluate_project(db, pid)
        await build_production_and_structures(db, str(pid))
        assert parses == []
        snap_after, pv_after = await _budget_snapshot(db, pid)
        assert snap_after == snap and pv_after == "0-stale"

        # DOCUMENTED EXCEPTION (current behaviour, an ingestion-phase product decision): committed-material routing
        # refreshes a stale parse IN PLACE on the same BudgetDocument / DocumentVersion.
        status = await mr.route_committed_material(db, project_id=pid, category="budget", document_version_id=version.id)
        assert status is not None and parses == ["csv"]
        refreshed, pv = await _budget_snapshot(db, pid)
        assert refreshed["doc_id"] == snap["doc_id"] and refreshed["dv"] == snap["dv"] and pv == BUDGET_PARSER_VERSION
        assert refreshed["categories"] == snap["categories"] and refreshed["amounts"] == snap["amounts"]
    finally:
        await _drop(db, pid)
