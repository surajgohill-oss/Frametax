"""
Chunked bulk persistence + projected read-back for evaluate_project().

evaluate_project() used to persist each candidate with ``session.add`` plus a
per-structure ``session.flush`` and read the whole generation back as ORM
objects (an FVD-scale evaluation is >500K rows). These tests pin that the
replacement (``_BulkEvaluationWriter`` + the projected ``_summarize_evaluation``
read) writes and serves exactly what the row-at-a-time path did.

The writer tests run inside one transaction that is always rolled back, against
a synthetic engine_version/fingerprint, so they leave nothing behind. The two
DB-backed evaluation tests are read-only/idempotent against the real Bad
Hombres project row, same convention as the other canonical_evaluation tests.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services import canonical_evaluation as ce
from app.services.economic_identity import canonical_economic_identity

BAD_HOMBRES_PROJECT_ID = uuid.UUID("4355ae88-a636-4c18-af60-ad73b2646124")
TEST_ENGINE = "test-bulk-writer"
TEST_FP = "b" * 64
# Written only by the bulk writer (the legacy ORM path leaves them NULL); everything ELSE
# must be identical. generation_ordinal: 1..N in add order; economic_identity: PRICED rows only.
_DERIVED_COLUMNS = ("generation_ordinal", "economic_identity")


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.rollback()


def _pair(tag: str, i: int):
    """One structure + its result, built the way evaluate_project() builds them:
    client-side ids, constructor sets only what it needs (defaults do the rest)."""
    sid = uuid.uuid4()
    structure = ProductionStructure(
        id=sid, project_id=BAD_HOMBRES_PROJECT_ID, name=f"{tag} {i}",
        description=f"synthetic {i}", jurisdiction_allocations=[],
        claimed_program_ids=["a", f"p{i}"],
    )
    result = StructureCalculationResult(
        id=uuid.uuid4(), structure_id=sid, engine_version=TEST_ENGINE,
        total_budget_usd=1_000_000, total_incentive_value_usd=None if i % 2 else 12345.67,
        true_net_cost_usd=None if i % 2 else 987654.32, risk_adjusted_net_cost_usd=None,
        has_unverified_inputs=bool(i % 3), warnings=["w", i],
        structure_type="component_relocation",
        calculation_trace_json={"candidate_status": "PRICED" if not i % 2 else "RULE_REJECTED",
                                "is_baseline": False, "reason": f"r{i}", "nested": {"k": [1, 2, {"z": i}]}},
        input_fingerprint=TEST_FP,
    )
    return structure, result


async def _masked_rows(session: AsyncSession, tag: str):
    rows = (await session.execute(text(
        "SELECT to_jsonb(ps) - 'id' - 'created_at' - 'updated_at' AS ps, "
        "       to_jsonb(scr) - 'id' - 'structure_id' - 'created_at' - 'updated_at' AS scr, "
        "       ps.created_at IS NOT NULL AS ps_ts, scr.created_at IS NOT NULL AS scr_ts, "
        "       scr.updated_at IS NOT NULL AS scr_uts "
        "FROM production_structures ps JOIN structure_calculation_results scr ON scr.structure_id = ps.id "
        "WHERE ps.name LIKE :tag AND scr.engine_version = :ev ORDER BY ps.name"
    ), {"tag": f"{tag} %", "ev": TEST_ENGINE})).all()
    out = []
    for r in rows:
        ps = dict(r.ps)
        ps["name"] = ps["name"].split(" ", 1)[1]  # drop the per-group tag
        scr = dict(r.scr)
        derived = {k: scr.pop(k) for k in _DERIVED_COLUMNS}  # compared separately below
        out.append((ps, scr, r.ps_ts, r.scr_ts, r.scr_uts, derived))
    return out


async def test_bulk_writer_writes_exactly_what_orm_add_flush_wrote(db: AsyncSession):
    n = 23
    # legacy path: real session.add + per-structure flush
    for i in range(n):
        s, r = _pair("LEGACYGRP", i)
        db.add(s)
        await db.flush()
        db.add(r)
    await db.flush()
    # new path: bulk writer, tiny chunks so several chunk boundaries are crossed
    writer = ce._BulkEvaluationWriter(db, chunk_rows=4)
    for i in range(n):
        s, r = _pair("BULKGRP", i)
        writer.add(s)
        await writer.flush()
        writer.add(r)
    await writer._drain()

    legacy = await _masked_rows(db, "LEGACYGRP")
    bulk = await _masked_rows(db, "BULKGRP")
    assert len(legacy) == len(bulk) == n
    assert writer.structures_written == writer.results_written == n
    assert writer.chunks > 1
    # every column, JSON payload and Python-side default identical
    assert [row[:5] for row in legacy] == [row[:5] for row in bulk]
    # defaults really applied (not NULL) on the bulk path
    assert all(ps_ts and scr_ts and scr_uts for _, _, ps_ts, scr_ts, scr_uts, _ in bulk)
    # ordinals are 1..N in add order across chunk boundaries (chunk_rows=4); identity only for PRICED rows
    by_name = sorted(bulk, key=lambda row: int(row[0]["name"]))
    assert [row[5]["generation_ordinal"] for row in by_name] == list(range(1, n + 1))
    for ps, scr, _, _, _, derived in bulk:
        trace = scr["calculation_trace_json"]
        if scr["true_net_cost_usd"] is not None:
            assert derived["economic_identity"] == canonical_economic_identity(scr["structure_type"], trace)
            assert len(derived["economic_identity"]) == 64
        else:
            assert derived["economic_identity"] is None
    assert all(row[5]["generation_ordinal"] is None and row[5]["economic_identity"] is None for row in legacy)


async def test_bulk_writer_fk_order_holds_at_every_chunk_boundary(db: AsyncSession):
    """chunk_rows=1 drains after every flush(): each result's structure is already
    in an earlier chunk; chunk_rows=1000 keeps structure and result in the same
    chunk. Either way structures are inserted before results (FKs are enforced)."""
    for chunk_rows in (1, 2, 1000):
        writer = ce._BulkEvaluationWriter(db, chunk_rows=chunk_rows)
        for i in range(7):
            s, r = _pair(f"FK{chunk_rows}", i)
            writer.add(s)
            await writer.flush()
            writer.add(r)
        await writer._drain()
        assert writer.structures_written == writer.results_written == 7
    count = (await db.execute(text(
        "SELECT count(*) FROM structure_calculation_results WHERE engine_version = :ev"), {"ev": TEST_ENGINE})).scalar()
    assert count == 21


async def test_bulk_writer_reads_see_buffered_rows_and_rollback_discards_everything(db: AsyncSession):
    before = (await db.execute(text(
        "SELECT count(*) FROM production_structures WHERE name LIKE 'RYW %'"))).scalar()
    writer = ce._BulkEvaluationWriter(db, chunk_rows=10_000)  # nothing hits the threshold
    for i in range(5):
        s, r = _pair("RYW", i)
        writer.add(s)
        await writer.flush()
        writer.add(r)
    assert writer.structures_written == 0  # still buffered
    seen = (await writer.execute(text("SELECT count(*) FROM production_structures WHERE name LIKE 'RYW %'"))).scalar()
    assert seen == before + 5  # a read drains first: read-your-writes, as per-row flush gave
    s, r = _pair("RYW", 99)
    writer.add(s)
    writer.add(r)  # left in the buffer
    await writer.rollback()
    after = (await db.execute(text("SELECT count(*) FROM production_structures WHERE name LIKE 'RYW %'"))).scalar()
    assert after == before  # both the drained chunk and the still-buffered pair are gone


async def test_bounded_readback_accounts_for_every_row_of_the_orm_readback(db: AsyncSession):
    """The payload no longer embeds every unpriced row -- but every one must still be
    ACCOUNTED for: exact totals, grouped counts, and a page walk that returns each row
    exactly once and equals an independent ORM read of the same generation."""
    econ = await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    project = await db.get(Project, BAD_HOMBRES_PROJECT_ID)
    rows = (await db.execute(
        select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == econ["state_fingerprint"],
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
        )
    )).all()
    priced = [(s, r) for s, r in rows if r.true_net_cost_usd is not None]
    unpriced = [(s, r) for s, r in rows if r.true_net_cost_usd is None]

    assert econ["priced_count"] == len(priced)
    assert econ["unpriceable_count"] == len(unpriced) == econ["unpriceable_page"]["total"]
    assert sum(econ["unpriceable_by_disposition"].values()) == len(unpriced)
    assert sum(g["count"] for g in econ["unpriceable_by_reason"]) == len(unpriced)
    orm_by_status: dict = {}
    for _, r in unpriced:
        status = (r.calculation_trace_json or {}).get("candidate_status") or "UNSPECIFIED"
        orm_by_status[status] = orm_by_status.get(status, 0) + 1
    assert econ["unpriceable_by_disposition"] == orm_by_status  # the accumulated summary == a fresh ORM count

    # the summary's total row count and ordinals cover the whole generation, 1..N
    summary = await ce.load_generation_summary(db, project.id, econ["state_fingerprint"])
    assert summary.total_rows == len(rows) == len(priced) + len(unpriced)
    assert sorted(r.generation_ordinal for _, r in rows) == list(range(1, len(rows) + 1))

    # bounded first page with explicit continuation metadata
    page = econ["unpriceable_page"]
    assert page["limit"] == ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert page["returned"] == len(econ["unpriceable"]) == min(len(unpriced), page["limit"])
    assert page["has_more"] is (len(unpriced) > page["limit"])
    assert (page["next_cursor"] is not None) is page["has_more"]

    # walking the cursor returns EVERY unpriced row exactly once, in generation order
    walked, cursor = list(econ["unpriceable"]), page["next_cursor"]
    while cursor:
        nxt = await ce.unpriceable_page(db, project.id, econ["state_fingerprint"], limit=97, cursor=cursor)
        walked.extend(nxt["results"])
        cursor = nxt["next_cursor"]
        assert nxt["has_more"] is (cursor is not None)
    assert sorted(e["structure_id"] for e in walked) == sorted(str(s.id) for s, _ in unpriced)
    assert len({e["structure_id"] for e in walked}) == len(walked)
    ords = [e["generation_ordinal"] for e in walked]
    assert ords == sorted(ords) and len(set(ords)) == len(ords)

    # priced ranking: non-decreasing NPC; equal-NPC ties ordered by canonical identity, not uuid
    ranked = econ["ranked"]
    assert len(ranked) == len(priced)
    seq = [(e["true_net_cost_usd"], e["economic_identity"]) for e in ranked]
    assert seq == sorted(seq)
    base = next(e for e in ranked if e["is_baseline"])
    assert econ["baseline"] == base


async def test_identical_input_rerun_creates_zero_rows(db: AsyncSession):
    first = await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    count_sql = text(
        "SELECT (SELECT count(*) FROM production_structures WHERE project_id = :p), "
        "       (SELECT count(*) FROM structure_calculation_results scr "
        "          JOIN production_structures ps ON ps.id = scr.structure_id WHERE ps.project_id = :p)")
    before = tuple((await db.execute(count_sql, {"p": BAD_HOMBRES_PROJECT_ID})).one())
    second = await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    after = tuple((await db.execute(count_sql, {"p": BAD_HOMBRES_PROJECT_ID})).one())
    assert second["status"] == "EVALUATION_REUSED"
    assert after == before
    assert second["baseline"] == first["baseline"]
    assert (second["priced_count"], second["unpriceable_count"]) == (first["priced_count"], first["unpriceable_count"])


class _RecordingSession:
    """Stub AsyncSession: records what the writer executes/commits, touches no database."""

    def __init__(self):
        self.executed: list[str] = []
        self.commits = 0

    async def flush(self):
        pass

    async def execute(self, stmt, *args, **kwargs):
        self.executed.append(str(stmt)[:60])

    async def commit(self):
        self.commits += 1


async def test_writer_commit_is_idempotent_summary_row_and_analyze_run_exactly_once(monkeypatch):
    """evaluate_project()'s read-back may commit AGAIN (leading-structure repoint): the
    summary insert and the post-write ANALYZE must not repeat -- the second summary insert
    violated the (project, fingerprint, engine) unique constraint and each ANALYZE costs ~30 s
    at FVD scale."""
    monkeypatch.setattr(ce, "_ANALYZE_AFTER_ROWS", 1)
    session = _RecordingSession()
    writer = ce._BulkEvaluationWriter(session)
    writer._summary.observe(1, status="PRICED", reason="", priced=True, is_baseline=True)
    writer._summary.observe(2, status="RULE_REJECTED", reason="THRESHOLD_NOT_MET", priced=False, is_baseline=False)
    writer._generation = {"project_id": uuid.uuid4(), "input_fingerprint": "e" * 64, "engine_version": "x"}
    writer.structures_written = writer.results_written = 2  # as if drained

    await writer.commit()
    after_first = list(session.executed)
    await writer.commit()  # the repoint commit
    await writer.commit()

    assert sum("evaluation_generation_summaries" in e for e in session.executed) == 1
    assert sum(e.startswith("ANALYZE production_structures") for e in session.executed) == 1
    assert sum(e.startswith("ANALYZE structure_calculation_results") for e in session.executed) == 1
    assert session.executed == after_first  # nothing more executed by the 2nd/3rd commit
    assert session.commits == 2 + 2  # first: commit + post-ANALYZE commit; then one plain commit each
