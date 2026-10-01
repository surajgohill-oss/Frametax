"""LLS repair 3 (2026-10-01): the default-disabled drain/phase instrumentation must not change
bounded-retention accounting. Streams a deterministic candidate set (reusing the retention
tests' own fixtures) through the bulk writer with the sink ENABLED, inside the retention
fixture's rolled-back transaction, and proves the retained set, accounting invariant and
proof references are exact, and that drain records reconcile to the rows actually written."""
from __future__ import annotations

from app.db.session import engine
from app.services import _lls_profile_sink as prof
from tests.test_bounded_candidate_retention import (  # noqa: F401  (project_id is a pytest fixture)
    NEW_ENGINE, NEW_FP, _rows, candidates, expected_retained, finish, idx_of, project_id, stream,
)

ACCEPTANCE_DB = "frametax2_claude_optimizer_acceptance_20260919"


async def test_writer_accounting_and_proof_refs_exact_with_drain_instrumentation(project_id):
    assert engine.url.database == ACCEPTANCE_DB, engine.url.database
    session, pid = project_id
    cands = candidates(600)
    prof.ENABLED = True
    prof.reset()
    try:
        writer = await finish(await stream(
            session, pid, cands, engine_version=NEW_ENGINE, fingerprint=NEW_FP, bounded=True, chunk_rows=50))
        rows = await _rows(session, NEW_ENGINE)
        drains = list(prof.DRAINS)
        cumulative = prof.TIMERS.get("db_drain", 0.0)
        retention_time = prof.TIMERS.get("retention_aggregation")
    finally:
        prof.ENABLED = False
        prof.reset()

    # accounting invariant: generated == persisted details + aggregate counts (raises if violated)
    writer._assert_accounting()
    assert writer.generated_results == 600 == writer.results_written + writer._aggregator.total
    # retained set equals the independently sorted policy; every proof reference resolves
    expected = expected_retained(cands)
    assert {idx_of(r.name) for r in rows} == expected
    proofs = [c for c in cands if c.status == "DOMINATED_WITH_PROOF" and c.idx in expected]
    assert proofs and all((c.idx - 1) in expected for c in proofs)
    # drain records reconcile exactly to what the writer wrote
    assert len(drains) == writer.chunks
    assert sum(d[3] for d in drains) == writer.structures_written + writer.results_written
    assert all(d[2] >= d[1] for d in drains)
    assert abs(cumulative - sum(d[2] - d[1] for d in drains)) < 1e-6
    assert retention_time is not None and retention_time >= 0.0


def test_sink_is_inert_when_disabled():
    prof.ENABLED = False
    prof.reset()
    prof.tick("x")
    with prof.timed("y"):
        pass
    prof.record_drain(0.0, 1.0, 5)
    assert not prof.COUNTERS and not prof.TIMERS and not prof.DRAINS
