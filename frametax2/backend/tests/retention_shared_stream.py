"""Bounded-retention equivalence on ONE enumeration: the hybrid search runs once, and every candidate it generates is fed, as the same stream, to two independent writers: the production
bounded-retention writer (the real evaluate_project path, so its read-back, accounting and zero-row reuse are the real ones) and a legacy full-enumeration writer (every candidate a
physical row, persisted under a separate engine label). The legacy rows are the measured ground truth the bounded generation is asserted against (assert_bounded_generation); neither writer
is ever compared with itself.

Independence of the stream: each candidate's structure and result are cloned BEFORE the bounded writer sees them (the bounded writer stamps classification and economic identity onto the
trace and may enrich retained rows; the legacy clone never sees those writes). The search never reads writer state (nothing in evaluate_project reads a writer attribute other than the two
enricher registrations), so one enumeration is the enumeration each writer would have received.

What sharing the enumeration does NOT cover is that two independent searches over the same inputs generate the same candidates (determinism of the search itself). That is covered by the
independent-enumeration body (assert_hybrid_bounded_retention) in the default suite, and test_the_shared_stream_legacy_rows_equal_an_independent_enumeration below checks the two against each
other on the bounded universe."""
from __future__ import annotations

import copy
import time
import uuid
from collections import Counter

from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect

from app.models.production import ProductionStructure, StructureCalculationResult
from app.services import candidate_retention as cret
from app.services import canonical_evaluation as ce
from app.services import canonical_production_view as cpv
from tests.test_served_contract_bounded import assert_bounded_generation

_STRUCT_KEYS = [a.key for a in sa_inspect(ProductionStructure).column_attrs]
_RESULT_KEYS = [a.key for a in sa_inspect(StructureCalculationResult).column_attrs]


def _make_fanout(legacy_engine: str, stats: dict):
    Real = ce._BulkEvaluationWriter

    class _Fanout(Real):
        def __init__(self, session, *a, **k):
            super().__init__(session, *a, **k)
            self._legacy = Real(session, bounded_retention=False)
            self._id_map: dict = {}
            stats["fanouts"] = stats.get("fanouts", 0) + 1
            stats["legacy_writer"] = self._legacy

        def _clone(self, obj):
            if isinstance(obj, ProductionStructure):
                values = {k: copy.copy(obj.__dict__[k]) for k in _STRUCT_KEYS if k in obj.__dict__ and k != "id"}
                new_id = uuid.uuid4()
                self._id_map[obj.id] = new_id
                return ProductionStructure(id=new_id, **values)
            values = {k: obj.__dict__[k] for k in _RESULT_KEYS if k in obj.__dict__ and k not in ("id", "structure_id", "calculation_trace_json", "engine_version")}
            trace = obj.calculation_trace_json
            # the bounded writer assigns top-level trace keys (classification, enrichers); a top-level copy is what keeps the legacy clone independent of them
            clone = StructureCalculationResult(
                structure_id=self._id_map[obj.structure_id], engine_version=legacy_engine,
                calculation_trace_json=dict(trace) if isinstance(trace, dict) else trace, **values)
            return clone

        def add(self, obj):
            if isinstance(obj, (ProductionStructure, StructureCalculationResult)):
                t0 = time.perf_counter()
                clone = self._clone(obj)
                stats["clone_seconds"] = stats.get("clone_seconds", 0.0) + time.perf_counter() - t0
                self._legacy.add(clone)
                stats["stream_objects"] = stats.get("stream_objects", 0) + 1
            super().add(obj)

        async def flush(self):
            await self._legacy.flush()
            await super().flush()

        async def commit(self):
            await self._legacy.commit()
            await super().commit()

        async def rollback(self):
            await self._legacy.rollback()
            await super().rollback()

    return _Fanout


def _heartbeat(stats: dict, started: float, every: float):
    """Daemon thread printing the stream's progress, so a run killed by an alarm still leaves throughput evidence."""
    import threading

    stop = threading.Event()

    def beat():
        while not stop.wait(every):
            w = stats.get("legacy_writer")
            print(f"HEARTBEAT t={time.perf_counter() - started:.0f}s stream_objects={stats.get('stream_objects', 0)} clone_s={stats.get('clone_seconds', 0.0):.1f} "
                  f"legacy_generated={getattr(w, 'generated_results', 0)} legacy_written={getattr(w, 'results_written', 0)}", flush=True)

    threading.Thread(target=beat, daemon=True).start()
    return stop


async def assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, *, restrict: bool, timings: dict | None = None, heartbeat_seconds: float = 0):
    """One enumeration, two independent writers (see the module docstring). ``timings`` receives per-phase seconds."""
    pid = isolated_hybrid_project.id
    timings = timings if timings is not None else {}
    if restrict:
        from tests.test_served_contract_bounded import _restrict_partners
        _restrict_partners(monkeypatch)
    legacy_engine = "canonical-test-legacy-shared-stream"
    stats: dict = {}
    monkeypatch.setattr(cret, "GLOBAL_TOP", 3)
    monkeypatch.setattr(cret, "TYPE_TOP", 3)
    monkeypatch.setattr(cpv, "TYPE_TOP", 3)
    t0 = time.perf_counter()
    stop = _heartbeat(stats, t0, heartbeat_seconds) if heartbeat_seconds else None
    try:
        with monkeypatch.context() as m:
            m.setattr(ce, "_BulkEvaluationWriter", _make_fanout(legacy_engine, stats))
            econ = await ce.evaluate_project(db, pid)          # the single enumeration; both writers persist from it
    finally:
        if stop:
            stop.set()
    timings["enumeration_and_both_writers_seconds"] = round(time.perf_counter() - t0, 2)
    assert econ["status"] == "EVALUATION_COMPLETE"
    legacy = stats["legacy_writer"]
    timings.update(stream_objects=stats["stream_objects"], clone_seconds=round(stats["clone_seconds"], 2), legacy_writer_drain_seconds=round(legacy.drain_seconds, 2),
                   legacy_rows_written=legacy.results_written, legacy_generated=legacy.generated_results)
    t1 = time.perf_counter()
    rows = (await db.execute(text(
        "select scr.calculation_trace_json->>'candidate_status' st from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev"), {"p": pid, "ev": legacy_engine})).all()
    measured = Counter(r.st for r in rows)
    legacy_total = sum(measured.values())
    timings["legacy_measure_seconds"] = round(time.perf_counter() - t1, 2)
    assert legacy_total == legacy.generated_results == legacy.results_written, "the legacy writer persisted every candidate of the stream"
    assert measured["PRICED"] > 0 and measured["DOMINATED_WITH_PROOF"] > 0, "the universe must still exercise hybrid pricing and dominance proofs"
    t2 = time.perf_counter()
    await assert_bounded_generation(db, pid, econ, measured, legacy_total, legacy_engine, timings)
    timings["assertions_and_reuse_seconds"] = round(time.perf_counter() - t2, 2)
    return measured
