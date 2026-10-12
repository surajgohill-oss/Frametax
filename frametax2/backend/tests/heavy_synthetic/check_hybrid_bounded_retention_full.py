"""HEAVY synthetic check (explicit path; deliberately outside the default suite and NOT a skipped test): the UNBOUNDED hybrid production whose real search enumerates
hundreds of thousands of candidates (minutes; it exceeded 640 s here). It enumerates ONCE and feeds the same candidate stream to the bounded writer and an independent legacy full-enumeration writer
(tests/retention_shared_stream.py), measuring the legacy rows itself, so it carries no pinned counts that could go stale; phase timings are printed (run with -s).

    DATABASE_URL unset  perl -e 'alarm shift; exec @ARGV' 720 python -m pytest tests/heavy_synthetic/check_hybrid_bounded_retention_full.py -q -s"""
from __future__ import annotations

import json
import time

import pytest

from tests.retention_shared_stream import assert_hybrid_bounded_retention_shared_stream
from tests.test_served_contract_bounded import db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


async def test_unbounded_hybrid_production_bounded_retention_matches_its_own_legacy_enumeration(db, isolated_hybrid_project, monkeypatch):
    timings: dict = {}
    t0 = time.perf_counter()
    try:
        await assert_hybrid_bounded_retention_shared_stream(db, isolated_hybrid_project, monkeypatch, restrict=False, timings=timings, heartbeat_seconds=60)
    finally:
        timings["total_seconds"] = round(time.perf_counter() - t0, 2)
        print("PHASE_TIMINGS " + json.dumps(timings, sort_keys=True), flush=True)
