"""HEAVY synthetic check (explicit path; deliberately outside the default suite and NOT a skipped test): the UNBOUNDED hybrid production whose real search enumerates
hundreds of thousands of candidates (minutes). It enumerates ONCE and feeds the same candidate stream to the bounded writer and an independent legacy full-enumeration writer
(tests/retention_shared_stream.py), measuring the legacy rows itself, so it carries no pinned counts that could go stale. It runs inside the scope-limited alias / pair-rule / allocation
memos (`alias_memo_scope`, results identical, active only inside the scope) with the raised young-generation GC threshold, exactly as services/bounded_regeneration.py does for the real
exhaustive hybrid search; both settings are restored afterwards. Phase timings, a 60 s heartbeat and a stack-sampling profile (inclusive and self counts per function, every 120 s) are printed (run with -s).

    DATABASE_URL unset  perl -e 'alarm shift; exec @ARGV' 720 python -u -m pytest tests/heavy_synthetic/check_hybrid_bounded_retention_full.py -q -s"""
from __future__ import annotations

import gc
import json
import sys
import threading
import time
from collections import Counter

import pytest

from app.services.canonical_program_identity import alias_memo_scope
from tests.retention_shared_stream import assert_hybrid_bounded_retention_shared_stream
from tests.test_served_contract_bounded import db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


def _start_sampler(target_ident: int, every: float = 0.2, report_every: float = 120.0):
    """Daemon thread sampling the evaluation thread's Python stack: counts, per function, the samples where it is the innermost frame (self) and where it is anywhere on the stack
    (inclusive), restricted to application code (app/ and tests/). The report survives a run killed by an alarm."""
    stop = threading.Event()
    self_c, incl_c = Counter(), Counter()
    samples = [0]

    def key(code):
        return f"{code.co_filename.split('/backend/')[-1]}:{code.co_name}"

    def report(tag):
        n = max(samples[0], 1)
        fmt = lambda c: [f"{k} {100 * v / n:.1f}%" for k, v in c.most_common(12)]
        print(f"PROFILE {tag} samples={samples[0]} SELF {json.dumps(fmt(self_c))} INCLUSIVE {json.dumps(fmt(incl_c))}", flush=True)

    def run():
        last = time.perf_counter()
        while not stop.wait(every):
            frame = sys._current_frames().get(target_ident)
            if frame is None:
                continue
            samples[0] += 1
            seen, innermost_done = set(), False
            while frame is not None:
                k = key(frame.f_code)
                if ("/app/" in frame.f_code.co_filename or "/tests/" in frame.f_code.co_filename):
                    if not innermost_done:
                        self_c[k] += 1
                        innermost_done = True
                    if k not in seen:
                        seen.add(k)
                        incl_c[k] += 1
                frame = frame.f_back
            if time.perf_counter() - last >= report_every:
                last = time.perf_counter()
                report(f"t={last:.0f}")
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return stop, report


async def test_unbounded_hybrid_production_bounded_retention_matches_its_own_legacy_enumeration(db, isolated_hybrid_project, monkeypatch):
    timings: dict = {}
    old_thresholds = gc.get_threshold()
    stop, report = _start_sampler(threading.get_ident())
    gc.set_threshold(200_000, 20, 50)
    t0 = time.perf_counter()
    try:
        with alias_memo_scope():
            await assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, restrict=False, timings=timings, heartbeat_seconds=60)
    finally:
        gc.set_threshold(*old_thresholds)
        stop.set()
        timings["total_seconds"] = round(time.perf_counter() - t0, 2)
        print("PHASE_TIMINGS " + json.dumps(timings, sort_keys=True), flush=True)
        report("final")
