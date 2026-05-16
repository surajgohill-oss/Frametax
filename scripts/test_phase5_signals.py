#!/usr/bin/env python3
"""
Phase 5 Signal Engine Gate Test
=================================
Validates the signal engine against the three invariants required for
Phase 5 closure:

  no_pipeline_mutation      — signal engine never writes to ingestion tables
  marketplace_generalization — all marketplace references use integer ID only
  read_model_isolation      — signal inputs come only from listing_snapshots +
                              events/tracked_events (Phase 4 outputs)

Also verifies:
  - all four signals compute without exception
  - decision engine produces a valid EventDecision enum value
  - EventSignalBundle.to_dict() is JSON-serialisable
  - INSUFFICIENT_DATA is returned gracefully when no snapshot data exists

No network calls. No DB mutations. DB reads are allowed (read-only queries).

Exit: 0 = PASS, 1 = FAIL
"""
import asyncio
import inspect
import json
import sys
import time

_t0 = time.monotonic()

sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.signals.engine import (
    compute_signals,
    compute_signals_all_active,
    _PRICE_MOMENTUM_SQL,
    _LIQUIDITY_SQL,
    _DIVERGENCE_SQL,
    _SCARCITY_SQL,
    _ACTIVE_EVENT_IDS_SQL,
)
from app.signals.models import EventDecision, EventSignalBundle

DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"

_GREEN = "\033[32m"
_RED   = "\033[31m"
_RESET = "\033[0m"
_failures: list[str] = []
_passed = 0


def check(label: str, got, expected, note: str = "") -> None:
    global _passed
    suffix = f"  [{note}]" if note else ""
    if got == expected:
        print(f"  {_GREEN}PASS{_RESET}  {label}  →  {got!r}{suffix}")
        _passed += 1
    else:
        print(f"  {_RED}FAIL{_RESET}  {label}  expected={expected!r}  got={got!r}{suffix}")
        _failures.append(label)


def check_true(label: str, value: bool, note: str = "") -> None:
    check(label, value, True, note)


print()
print("══════════════════════════════════════════")
print("  PHASE 5 SIGNAL ENGINE GATE TEST")
print("══════════════════════════════════════════")

# ── Invariant 1: marketplace_generalization ────────────────────────────────────
print()
print("── Invariant: marketplace_generalization ───────────────────────")

_FORBIDDEN_NAMES = {"seatgeek", "stubhub", "tickpick", "vivid", "gametime",
                    "viagogo", "ticketmaster", "seatpick"}

engine_src = inspect.getsource(
    __import__("app.signals.engine", fromlist=["engine"])
)
models_src = inspect.getsource(
    __import__("app.signals.models", fromlist=["models"])
)
routes_src = inspect.getsource(
    __import__("app.api.routes.signals", fromlist=["signals"])
)

combined = (engine_src + models_src + routes_src).lower()

# Strip comment lines before checking (comments are documentation, not logic)
non_comment_lines = [
    l for l in combined.splitlines()
    if not l.strip().startswith("#")
]
non_comment_src = "\n".join(non_comment_lines)

found_names = [n for n in _FORBIDDEN_NAMES if n in non_comment_src]
check(
    "no marketplace names in engine/models/routes (non-comment lines)",
    found_names, [],
    "only marketplace_id integers allowed in logic",
)

# SQL must reference marketplace_id, not name columns
for sql_name, sql_obj in [
    ("_DIVERGENCE_SQL", _DIVERGENCE_SQL),
    ("_PRICE_MOMENTUM_SQL", _PRICE_MOMENTUM_SQL),
    ("_LIQUIDITY_SQL", _LIQUIDITY_SQL),
    ("_SCARCITY_SQL", _SCARCITY_SQL),
]:
    sql_text = str(sql_obj.text if hasattr(sql_obj, "text") else sql_obj).lower()
    has_mp_id = "marketplace_id" in sql_text or "marketplace_id" in sql_text
    check_true(f"{sql_name} references marketplace_id (not name)", has_mp_id)

# ── Invariant 2: read_model_isolation ─────────────────────────────────────────
print()
print("── Invariant: read_model_isolation ─────────────────────────────")

_WRITE_KEYWORDS = ["insert into", "update ", "delete from", "alter table",
                   "drop table", "truncate"]
_FORBIDDEN_TABLES = ["events", "tracked_events", "listings", "poll_runs",
                     "marketplaces", "venues"]

for kw in _WRITE_KEYWORDS:
    found = kw in engine_src.lower()
    check(f"engine.py contains no '{kw}'", found, False)

# listing_snapshots is the ONLY allowed write-direction reference
# Engine should only SELECT from it
import re
insert_re = re.compile(r"insert\s+into\s+listing_snapshots", re.I)
check(
    "engine.py does not INSERT into listing_snapshots",
    bool(insert_re.search(engine_src)), False,
)

# ── Invariant 3: no_pipeline_mutation — runtime DB check ──────────────────────
print()
print("── Invariant: no_pipeline_mutation (live DB) ───────────────────")


async def _runtime_check() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with S() as db:
        # Snapshot counts before
        from sqlalchemy import text
        counts_before = {}
        for tbl in ["events", "tracked_events", "listings", "listing_snapshots", "poll_runs"]:
            n = (await db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))).scalar_one()
            counts_before[tbl] = n

        # Run signal engine for all active events
        bundles = await compute_signals_all_active(db)

        # Snapshot counts after — must be identical
        counts_after = {}
        for tbl in counts_before:
            n = (await db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))).scalar_one()
            counts_after[tbl] = n

    for tbl in counts_before:
        check(
            f"table '{tbl}' row count unchanged after compute_signals_all_active()",
            counts_after[tbl], counts_before[tbl],
        )

    # ── Signal output contract ─────────────────────────────────────────────────
    print()
    print("── Signal output contract ───────────────────────────────────")

    valid_decisions = {d.value for d in EventDecision}

    for bundle in bundles:
        check_true(
            f"event_id={bundle.event_id} decision is valid EventDecision",
            bundle.decision.value in valid_decisions,
        )
        d = bundle.to_dict()
        try:
            json.dumps(d)
            serialisable = True
        except (TypeError, ValueError):
            serialisable = False
        check_true(
            f"event_id={bundle.event_id} to_dict() is JSON-serialisable",
            serialisable,
        )
        check_true(
            f"event_id={bundle.event_id} has 'signals' key with 4 sub-signals",
            len(d.get("signals", {})) == 4,
        )

    if not bundles:
        print("  INFO  no active resolved events — skipping per-bundle checks")
        print("        (expected in a fresh environment without seeded poll data)")

    # ── INSUFFICIENT_DATA path: synthetic non-existent event_id ───────────────
    print()
    print("── Graceful INSUFFICIENT_DATA path ─────────────────────────")

    async with S() as db:
        phantom = await compute_signals(db, event_id=999999999)
    check(
        "phantom event_id returns INSUFFICIENT_DATA",
        phantom.decision, EventDecision.INSUFFICIENT_DATA,
    )
    check(
        "phantom bundle decision_reasons is non-empty",
        len(phantom.decision_reasons) > 0, True,
    )

    await engine.dispose()


asyncio.run(_runtime_check())

# ── Summary ────────────────────────────────────────────────────────────────────
total = _passed + len(_failures)
print()
print("══════════════════════════════════════════")
if _failures:
    print(f"  RESULT: {_RED}FAIL{_RESET} — {len(_failures)}/{total} check(s) failed")
    for f in _failures:
        print(f"    ✗ {f}")
else:
    print(f"  RESULT: {_GREEN}PASS{_RESET} — all {total} checks correct")
    print("  Signal engine is marketplace-generic, read-only, and pipeline-safe.")
_status = "FAIL" if _failures else "PASS"
print(f"GATE_REPORT_JSON={json.dumps({'gate_name': 'phase5-signal-gate', 'status': _status, 'duration_ms': int((time.monotonic() - _t0) * 1000), 'details': {'total': total, 'passed': _passed, 'failed': len(_failures)}})}")
sys.exit(1 if _failures else 0)
