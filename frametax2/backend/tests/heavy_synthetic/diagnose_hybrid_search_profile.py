"""DIAGNOSTIC (not a pass/fail check): where the unbounded hybrid search spends its time, with library frames included. Runs the same evaluation as check_hybrid_bounded_retention_full.py
(same fixture, memo scope, GC threshold, bounded writer plus stream oracle) but is stopped after DIAG_SECONDS (default 110) and prints the evidence; the open transaction is rolled back by the database.

    DATABASE_URL unset  perl -e 'alarm shift; exec @ARGV' 150 python -u -m pytest tests/heavy_synthetic/diagnose_hybrid_search_profile.py -q -s

Measurement: cProfile (deterministic; per-function time INCLUDING builtins and library functions, with call counts), stopped by a one-shot CPU-time signal after DIAG_SECONDS. Sampling profilers were
tried first and rejected as unreliable here: a sampling thread only runs where the evaluation releases the GIL (it reported uuid4 at 89%), and a SIGPROF handler only runs at interpreter check
points (uuid4 at 71%), while uuid4 measures 1.6 microseconds per call in this interpreter, with the app imported, the raised GC threshold and 3 million live objects."""
from __future__ import annotations

import gc
import json
import os
import signal
import time

import cProfile
import io
import pstats

import pytest

from app.services import canonical_evaluation as ce
from app.services.canonical_program_identity import alias_memo_scope
from tests.retention_shared_stream import _make_fanout
from tests.test_served_contract_bounded import db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


async def test_profile_the_hybrid_search(db, isolated_hybrid_project, monkeypatch):
    seconds = float(os.environ.get("DIAG_SECONDS", "100"))
    stats: dict = {}
    profiler = cProfile.Profile()
    t0 = time.perf_counter()

    def report(*_):
        signal.setitimer(signal.ITIMER_PROF, 0)
        profiler.disable()
        st = pstats.Stats(profiler)
        rows = []
        for (filename, line, name), (cc, nc, tt, ct, _callers) in st.stats.items():
            rows.append((tt, ct, nc, f"{filename.split('/backend/')[-1].split('/site-packages/')[-1].split('lib/python3.12/')[-1]}:{line}:{name}"))
        total = sum(r[0] for r in rows) or 1.0
        o = stats.get("oracle")
        print("DIAG " + json.dumps({
            "elapsed_s": round(time.perf_counter() - t0, 1), "profiled_cpu_s": round(total, 1), "candidates": getattr(o, "total", 0),
            "by_own_time": [f"{r[3]} own={r[0]:.1f}s ({100 * r[0] / total:.1f}%) cum={r[1]:.1f}s calls={r[2]}" for r in sorted(rows, reverse=True)[:30]],
            "by_cumulative_time_app_only": [f"{r[3]} cum={r[1]:.1f}s calls={r[2]}" for r in sorted(rows, key=lambda r: -r[1]) if "app/" in r[3]][:12]}, indent=1), flush=True)
        os._exit(0)

    signal.signal(signal.SIGPROF, report)       # one-shot CPU-time deadline (the search never yields to the event loop)
    old = gc.get_threshold()
    gc.set_threshold(200_000, 20, 50)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    profiler.enable()
    with alias_memo_scope(), monkeypatch.context() as m:
        m.setattr(ce, "_BulkEvaluationWriter", _make_fanout("canonical-test-diag", stats, "oracle"))
        await ce.evaluate_project(db, isolated_hybrid_project.id)
    profiler.disable()
    gc.set_threshold(*old)
    signal.setitimer(signal.ITIMER_PROF, 0)
