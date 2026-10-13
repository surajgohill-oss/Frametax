"""Focused control for what the shared-stream retention body does not cover by construction: that one enumeration fed to two writers is the enumeration an independent legacy run would
produce. On the bounded partner universe (seconds): an independent legacy full-enumeration run (its own search) and the shared-stream body (one search, two writers) must measure the same
candidate statuses, and the shared-stream body must pass every bounded-generation assertion (coverage, accounting, ranking against the legacy rows, proofs and retained incumbents, reuse)."""
from __future__ import annotations

from collections import Counter

import pytest
from sqlalchemy import text

from app.services import canonical_evaluation as ce
from app.services import canonical_production_view as cpv
from tests.retention_shared_stream import assert_hybrid_bounded_retention_shared_stream
from tests.test_served_contract_bounded import _restrict_partners, db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


async def test_the_shared_stream_legacy_rows_equal_an_independent_enumeration(db, isolated_hybrid_project, monkeypatch):
    pid = isolated_hybrid_project.id
    _restrict_partners(monkeypatch)
    Real = ce._BulkEvaluationWriter

    class _LegacyWriter(Real):
        def __init__(self, session, *a, **k):
            super().__init__(session, *a, bounded_retention=False, **k)

    independent_engine = "canonical-test-legacy-independent"
    with monkeypatch.context() as m:
        m.setattr(ce, "_BulkEvaluationWriter", _LegacyWriter)
        m.setattr(ce, "ENGINE_VERSION", independent_engine)
        m.setattr(cpv, "ENGINE_VERSION", independent_engine)
        assert (await ce.evaluate_project(db, pid))["status"] == "EVALUATION_COMPLETE"
    independent = Counter(r.st for r in (await db.execute(text(
        "select scr.calculation_trace_json->>'candidate_status' st from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev"), {"p": pid, "ev": independent_engine})).all())
    timings: dict = {}
    shared = await assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, restrict=False, timings=timings, legacy="both")
    assert shared == independent, "one enumeration fed to the legacy writer must equal an independent legacy enumeration"
    assert timings["stream_objects"] == 2 * sum(shared.values()), "every candidate reached the legacy writer as a structure and a result"
    assert timings["oracle_candidates"] == sum(shared.values()), "the oracle observed every candidate (and, in this control, equals the real persisted legacy rows cell by cell)"


async def test_the_oracle_alone_passes_the_same_bounded_generation_assertions(db, isolated_hybrid_project, monkeypatch):
    """The heavy check's mode (no legacy rows persisted) on the bounded universe: the same assertions, with the legacy reference supplied by the oracle."""
    timings: dict = {}
    measured = await assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, restrict=True, timings=timings, legacy="oracle")
    assert "legacy_rows_written" not in timings and timings["oracle_candidates"] == sum(measured.values())
