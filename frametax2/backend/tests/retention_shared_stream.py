"""Bounded-retention equivalence on ONE enumeration: the hybrid search runs once, and every candidate it generates is fed, as the same stream, to the production bounded-retention writer (the
real evaluate_project path, so its read-back, accounting and zero-row reuse are the real ones) and to an independent legacy reference measured from the stream before the bounded writer sees it.

Two legacy references exist, selected by ``legacy``:
  * "writer": a legacy full-enumeration _BulkEvaluationWriter persisting every candidate as a database row under its own engine label (what the bounded-universe control uses);
  * "oracle": an in-memory StreamOracle tallying exactly what the assertions read (the heavy check: persisting every legacy row was ~75% of its wall time, see the ledger);
  * "both": the control that validates the oracle against the real persisted legacy rows.
Neither reference reads the bounded writer's state and the bounded writer never reads theirs; the search reads no writer state (evaluate_project touches only the two enricher registrations), so one
enumeration is the enumeration each would have received. Each candidate is observed/cloned BEFORE the bounded writer stamps classification and identity onto its trace.

What sharing the enumeration does NOT cover is that two independent searches over the same inputs generate the same candidates (determinism of the search itself): the independent-enumeration body
(assert_hybrid_bounded_retention) stays in the default suite, and tests/test_retention_shared_stream.py checks the shared stream against it."""
from __future__ import annotations

import copy
import heapq
import time
import uuid
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text

from app.models.production import ProductionStructure, StructureCalculationResult
from app.services import candidate_retention as cret
from app.services import canonical_evaluation as ce
from app.services import canonical_production_view as cpv
from app.services.economic_identity import candidate_status_of, canonical_economic_identity
from tests.test_served_contract_bounded import assert_bounded_generation

_STRUCT_KEYS = [a.key for a in sa_inspect(ProductionStructure).column_attrs]
_RESULT_KEYS = [a.key for a in sa_inspect(StructureCalculationResult).column_attrs]
_CENT = Decimal("0.01")


def cents(value) -> Decimal:
    """The database's Numeric(18,2) view of a float NPC (what both persisted row sets store)."""
    return Decimal(format(float(value), ".15g")).quantize(_CENT, rounding=ROUND_HALF_UP)


class StreamOracle:
    """In-memory legacy reference over the full candidate stream. Tallies, per (status, structure_type, structural_family, reason_class): the candidate count and the min/max NPC (cents) of
    candidates carrying an NPC; the global top ``top_n`` by (NPC cents, canonical economic identity); per structure_type the best NPC and the identities attaining it; and proof completeness."""

    def __init__(self, top_n: int = 3):
        self.top_n = top_n
        self.total = 0
        self.status_counts: Counter = Counter()
        self.cells: dict = {}
        self.top: list = []
        self.best_by_type: dict = {}
        self.proofs = 0
        self.proofs_incomplete = 0
        self.proof_refs: set = set()
        self.observe_seconds = 0.0

    def observe(self, result) -> None:
        t0 = time.perf_counter()
        trace = result.calculation_trace_json or {}
        status = candidate_status_of(trace)
        stype = result.structure_type or trace.get("structure_type") or ""
        self.total += 1
        self.status_counts[status] += 1
        key = (status, stype, str(trace.get("structural_family") or ""), str(trace.get("rejection_reason_class") or ""))
        cell = self.cells.get(key)
        if cell is None:
            cell = self.cells[key] = {"count": 0, "min": None, "max": None}
        cell["count"] += 1
        npc = result.true_net_cost_usd
        if npc is not None:
            c = cents(npc)
            cell["min"] = c if cell["min"] is None or c < cell["min"] else cell["min"]
            cell["max"] = c if cell["max"] is None or c > cell["max"] else cell["max"]
            if status == "PRICED":
                ident = canonical_economic_identity(result.structure_type, trace)
                entry = (c, ident)
                if len(self.top) < self.top_n or entry < self.top[-1]:
                    self.top.append(entry)
                    self.top.sort()
                    del self.top[self.top_n:]
                best = self.best_by_type.get(stype)
                if best is None or c < best[0]:
                    self.best_by_type[stype] = (c, {ident})
                elif c == best[0]:
                    best[1].add(ident)
        if status == "DOMINATED_WITH_PROOF":
            self.proofs += 1
            if not (isinstance(trace.get("incumbent_value_usd"), (int, float)) and trace.get("stopping_inequality_holds") is True):
                self.proofs_incomplete += 1
            if trace.get("incumbent_structure_id"):
                self.proof_refs.add(str(trace["incumbent_structure_id"]))
        self.observe_seconds += time.perf_counter() - t0


def _make_fanout(legacy_engine: str, stats: dict, legacy: str):
    Real = ce._BulkEvaluationWriter
    use_writer = legacy in ("writer", "both")
    use_oracle = legacy in ("oracle", "both")

    class _Fanout(Real):
        def __init__(self, session, *a, **k):
            super().__init__(session, *a, **k)
            self._legacy = Real(session, bounded_retention=False) if use_writer else None
            self._id_map: dict = {}
            stats["fanouts"] = stats.get("fanouts", 0) + 1
            stats["legacy_writer"] = self._legacy
            if use_oracle:
                stats["oracle"] = StreamOracle()

        def _clone(self, obj):
            if isinstance(obj, ProductionStructure):
                values = {k: copy.copy(obj.__dict__[k]) for k in _STRUCT_KEYS if k in obj.__dict__ and k != "id"}
                new_id = uuid.uuid4()
                self._id_map[obj.id] = new_id
                return ProductionStructure(id=new_id, **values)
            values = {k: obj.__dict__[k] for k in _RESULT_KEYS if k in obj.__dict__ and k not in ("id", "structure_id", "calculation_trace_json", "engine_version")}
            trace = obj.calculation_trace_json
            # the bounded writer assigns top-level trace keys (classification, enrichers); a top-level copy keeps the legacy clone independent of them
            return StructureCalculationResult(
                structure_id=self._id_map[obj.structure_id], engine_version=legacy_engine,
                calculation_trace_json=dict(trace) if isinstance(trace, dict) else trace, **values)

        def add(self, obj):
            if isinstance(obj, (ProductionStructure, StructureCalculationResult)):
                if use_oracle and isinstance(obj, StructureCalculationResult):
                    stats["oracle"].observe(obj)
                if use_writer:
                    t0 = time.perf_counter()
                    clone = self._clone(obj)
                    stats["clone_seconds"] = stats.get("clone_seconds", 0.0) + time.perf_counter() - t0
                    self._legacy.add(clone)
                stats["stream_objects"] = stats.get("stream_objects", 0) + 1
            super().add(obj)

        async def flush(self):
            if use_writer:
                await self._legacy.flush()
            await super().flush()

        async def commit(self):
            if use_writer:
                await self._legacy.commit()
            await super().commit()

        async def rollback(self):
            if use_writer:
                await self._legacy.rollback()
            await super().rollback()

    return _Fanout


def _heartbeat(stats: dict, started: float, every: float):
    """Daemon thread printing the stream's progress, so a run killed by an alarm still leaves throughput evidence."""
    import threading

    stop = threading.Event()

    def beat():
        while not stop.wait(every):
            w, o = stats.get("legacy_writer"), stats.get("oracle")
            print(f"HEARTBEAT t={time.perf_counter() - started:.0f}s stream_objects={stats.get('stream_objects', 0)} oracle_observed={getattr(o, 'total', 0)} "
                  f"oracle_s={getattr(o, 'observe_seconds', 0.0):.1f} legacy_generated={getattr(w, 'generated_results', 0)} legacy_written={getattr(w, 'results_written', 0)}", flush=True)

    threading.Thread(target=beat, daemon=True).start()
    return stop


async def _row_tally(db, pid, engine, fingerprint=None):
    """(status, structure_type, structural_family, reason_class) -> {count, min, max NPC cents} over the persisted detailed rows of one generation."""
    fp = "and scr.input_fingerprint=:fp" if fingerprint else ""
    params = {"p": pid, "ev": engine, **({"fp": fingerprint} if fingerprint else {})}
    rows = (await db.execute(text(
        "select scr.calculation_trace_json->>'candidate_status' st, coalesce(scr.structure_type,'') ty, coalesce(scr.calculation_trace_json->>'structural_family','') fam, "
        "coalesce(scr.calculation_trace_json->>'rejection_reason_class','') rc, count(*) n, min(scr.true_net_cost_usd) mn, max(scr.true_net_cost_usd) mx "
        "from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        f"where ps.project_id=:p and scr.engine_version=:ev {fp} group by 1,2,3,4"), params)).all()
    return {(r.st, r.ty, r.fam, r.rc): {"count": r.n, "min": r.mn, "max": r.mx} for r in rows}


def _merge(into: dict, key, count, mn, mx):
    cell = into.setdefault(key, {"count": 0, "min": None, "max": None})
    cell["count"] += count
    if mn is not None:
        cell["min"] = mn if cell["min"] is None or mn < cell["min"] else cell["min"]
    if mx is not None:
        cell["max"] = mx if cell["max"] is None or mx > cell["max"] else cell["max"]


async def assert_oracle_matches_bounded(db, pid, fingerprint, oracle: StreamOracle, summary):
    """The stream oracle against the bounded generation, cell by cell: candidate counts per (status, type, family, reason class); NPC min/max per cell (retained rows plus aggregate groups);
    the best NPC and its identity per structure_type; and proof completeness (every stream proof complete, every referenced incumbent retained)."""
    bounded: dict = {}
    for key, c in (await _row_tally(db, pid, ce.ENGINE_VERSION, fingerprint)).items():
        _merge(bounded, key, c["count"], c["min"], c["max"])
    agg = (await db.execute(text(
        "select candidate_status st, structure_type ty, coalesce(structural_family,'') fam, coalesce(reason_class,'') rc, sum(candidate_count) n, min(min_npc_usd) mn, max(max_npc_usd) mx "
        "from evaluation_candidate_aggregates where project_id=:p and input_fingerprint=:fp and engine_version=:ev group by 1,2,3,4"),
        {"p": pid, "fp": fingerprint, "ev": ce.ENGINE_VERSION})).all()
    for r in agg:
        _merge(bounded, (r.st, r.ty, r.fam, r.rc), int(r.n), r.mn, r.mx)
    assert set(bounded) == set(oracle.cells), ("cells differ", sorted(set(bounded) ^ set(oracle.cells))[:5])
    for key, o in oracle.cells.items():
        b = bounded[key]
        assert b["count"] == o["count"], ("candidate count per cell", key, b["count"], o["count"])
        assert (b["min"], b["max"]) == (o["min"], o["max"]), ("NPC min/max per cell", key, (b["min"], b["max"]), (o["min"], o["max"]))
    assert sum(c["count"] for c in bounded.values()) == oracle.total == summary.total_rows

    # best NPC per structure_type and its identity: retained rows (npc, economic_identity) plus aggregate groups (min NPC, best identity)
    best: dict = {}
    for r in (await db.execute(text(
            "select coalesce(scr.structure_type,'') ty, scr.true_net_cost_usd npc, scr.economic_identity ident from structure_calculation_results scr "
            "join production_structures ps on ps.id=scr.structure_id where ps.project_id=:p and scr.engine_version=:ev and scr.input_fingerprint=:fp "
            "and scr.calculation_trace_json->>'candidate_status'='PRICED' and scr.true_net_cost_usd is not null"), {"p": pid, "ev": ce.ENGINE_VERSION, "fp": fingerprint})).all():
        best.setdefault(r.ty, []).append((r.npc, r.ident))
    for r in (await db.execute(text(
            "select structure_type ty, min_npc_usd npc, best_economic_identity ident from evaluation_candidate_aggregates where project_id=:p and input_fingerprint=:fp "
            "and engine_version=:ev and candidate_status='PRICED' and min_npc_usd is not null"), {"p": pid, "fp": fingerprint, "ev": ce.ENGINE_VERSION})).all():
        best.setdefault(r.ty, []).append((r.npc, r.ident))
    assert set(best) == set(oracle.best_by_type), ("priced structure types differ", set(best) ^ set(oracle.best_by_type))
    for ty, entries in best.items():
        low = min(n for n, _ in entries)
        assert low == oracle.best_by_type[ty][0], ("best NPC for structure type", ty, low, oracle.best_by_type[ty][0])
        assert {i for n, i in entries if n == low} & oracle.best_by_type[ty][1], ("best identity for structure type", ty)

    # proof completeness: the stream's proofs are all complete, equal the bounded generation's, and every referenced incumbent is a retained row
    assert oracle.proofs == oracle.status_counts["DOMINATED_WITH_PROOF"] > 0 and oracle.proofs_incomplete == 0, "every dominance proof in the stream is complete"
    known = {r.sid for r in (await db.execute(text(
        "select ps.id::text sid from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev and scr.input_fingerprint=:fp"), {"p": pid, "ev": ce.ENGINE_VERSION, "fp": fingerprint})).all()}
    known |= {r.gen for r in (await db.execute(text(
        "select scr.calculation_trace_json->>'structural_generator_structure_id' gen from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev and scr.input_fingerprint=:fp"), {"p": pid, "ev": ce.ENGINE_VERSION, "fp": fingerprint})).all() if r.gen}
    missing = oracle.proof_refs - known
    assert not missing, ("proof incumbents not retained", sorted(missing)[:3])


async def assert_oracle_matches_legacy_rows(db, pid, legacy_engine, oracle: StreamOracle):
    """Validation of the oracle against the real persisted legacy rows (the bounded control): same cells, same NPC min/max, same top-3 ranking."""
    rows = await _row_tally(db, pid, legacy_engine)
    assert set(rows) == set(oracle.cells)
    for key, o in oracle.cells.items():
        assert (rows[key]["count"], rows[key]["min"], rows[key]["max"]) == (o["count"], o["min"], o["max"]), ("oracle disagrees with the legacy rows", key)
    top = [tuple(r) for r in (await db.execute(text(
        "select scr.true_net_cost_usd npc, scr.economic_identity ident from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
        "where ps.project_id=:p and scr.engine_version=:ev and scr.calculation_trace_json->>'candidate_status'='PRICED' and scr.true_net_cost_usd is not null "
        "order by scr.true_net_cost_usd, scr.economic_identity limit 3"), {"p": pid, "ev": legacy_engine})).all()]
    assert top == oracle.top, ("oracle top-3 disagrees with the legacy rows", top, oracle.top)


async def assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, *, restrict: bool, timings: dict | None = None, heartbeat_seconds: float = 0,
                                                       legacy: str = "writer"):
    """One enumeration, a bounded writer and an independent legacy reference (see the module docstring). ``timings`` receives per-phase seconds; returns the measured status counts."""
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
            m.setattr(ce, "_BulkEvaluationWriter", _make_fanout(legacy_engine, stats, legacy))
            econ = await ce.evaluate_project(db, pid)          # the single enumeration; the bounded writer and the legacy reference both read it
    finally:
        if stop:
            stop.set()
    timings["enumeration_and_bounded_writer_seconds"] = round(time.perf_counter() - t0, 2)
    assert econ["status"] == "EVALUATION_COMPLETE"
    oracle, writer = stats.get("oracle"), stats.get("legacy_writer")
    timings["stream_objects"] = stats["stream_objects"]
    if writer is not None:
        timings.update(clone_seconds=round(stats["clone_seconds"], 2), legacy_writer_drain_seconds=round(writer.drain_seconds, 2),
                       legacy_rows_written=writer.results_written, legacy_generated=writer.generated_results)
    if oracle is not None:
        timings.update(oracle_observe_seconds=round(oracle.observe_seconds, 2), oracle_candidates=oracle.total)

    t1 = time.perf_counter()
    if writer is not None:
        rows = (await db.execute(text(
            "select scr.calculation_trace_json->>'candidate_status' st from structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id "
            "where ps.project_id=:p and scr.engine_version=:ev"), {"p": pid, "ev": legacy_engine})).all()
        measured = Counter(r.st for r in rows)
        legacy_total = sum(measured.values())
        assert legacy_total == writer.generated_results == writer.results_written, "the legacy writer persisted every candidate of the stream"
        if oracle is not None:
            assert measured == oracle.status_counts and legacy_total == oracle.total, "the oracle saw exactly the candidates the legacy writer persisted"
            await assert_oracle_matches_legacy_rows(db, pid, legacy_engine, oracle)
        legacy_top = None
    else:
        measured, legacy_total, legacy_top = Counter(oracle.status_counts), oracle.total, list(oracle.top)
    timings["legacy_measure_seconds"] = round(time.perf_counter() - t1, 2)
    assert measured["PRICED"] > 0 and measured["DOMINATED_WITH_PROOF"] > 0, "the universe must still exercise hybrid pricing and dominance proofs"
    t2 = time.perf_counter()
    await assert_bounded_generation(db, pid, econ, measured, legacy_total, legacy_engine, timings, legacy_top=legacy_top)
    timings["assertions_and_reuse_seconds"] = round(time.perf_counter() - t2, 2)
    if oracle is not None:
        t3 = time.perf_counter()
        summary = await ce.load_generation_summary(db, pid, econ["state_fingerprint"])
        await assert_oracle_matches_bounded(db, pid, econ["state_fingerprint"], oracle, summary)
        timings["oracle_comparison_seconds"] = round(time.perf_counter() - t3, 2)
    return measured
