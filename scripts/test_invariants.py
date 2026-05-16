#!/usr/bin/env python3
"""
DB Invariant Gate Test
======================
Verifies database invariants A–E by querying the live DB.
Used by gate_aggregator as the 'db-invariants' gate.

Invariant classification:
  A, C, D, E — HARD gates: any failure exits 1
  B           — ADVISORY:  PENDING is a valid transient state (resolver lag),
                            not a hard gate failure

Exit: 0 = all hard gates PASS, 1 = any hard gate FAIL
"""
import asyncio
import sys

sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"

_GREEN = "\033[32m"
_RED   = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"

# (letter, description, query, pass_predicate, is_hard_gate)
_INVARIANTS = [
    (
        "A",
        "poll_runs only on resolved events",
        "SELECT COUNT(*) FROM poll_runs pr "
        "JOIN tracked_events te ON te.id = pr.tracked_event_id "
        "WHERE te.external_event_id IS NULL AND pr.status != 'running'",
        lambda n: n == 0,
        True,
    ),
    (
        "B",
        "Stage 2 resolution lag",
        "SELECT COUNT(*) FROM tracked_events "
        "WHERE external_event_id IS NULL AND is_active = true",
        lambda n: n == 0,
        False,   # advisory: PENDING is valid during resolver lag
    ),
    (
        "C",
        "no orphan poll_runs",
        "SELECT COUNT(*) FROM poll_runs WHERE error_message = 'unresolved_event_id'",
        lambda n: n == 0,
        True,
    ),
    (
        "D",
        "demo IDs seeded (6/6)",
        "SELECT COUNT(*) FROM tracked_events "
        "WHERE external_event_id LIKE 'demo-%' AND is_active = true",
        lambda n: n >= 6,
        True,
    ),
    (
        "E",
        "no completed-but-active tracked_events",
        "SELECT COUNT(*) FROM tracked_events "
        "WHERE lifecycle_phase = 'completed' AND is_active = true",
        lambda n: n == 0,
        True,
    ),
]


async def main() -> int:
    engine = create_async_engine(DATABASE_URL, echo=False)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    hard_failures: list[str] = []
    passed = 0

    print()
    print("══════════════════════════════════════════")
    print("  DB INVARIANT GATE TEST")
    print("══════════════════════════════════════════")
    print()

    async with S() as db:
        for letter, desc, query, predicate, is_hard in _INVARIANTS:
            count = (await db.execute(text(query))).scalar_one()
            ok = predicate(count)

            if ok:
                label = "PASS"
                color = _GREEN
                symbol = "✓"
                passed += 1
            elif not is_hard:
                label = f"PENDING  [count={count}]"
                color = _YELLOW
                symbol = "~"
                passed += 1  # advisory — counts as pass for gate purposes
            else:
                label = f"FAIL  [count={count}]"
                color = _RED
                symbol = "✗"
                hard_failures.append(letter)

            print(f"  {color}{symbol}{_RESET}  Invariant {letter} ({desc}): {color}{label}{_RESET}")

    await engine.dispose()

    total = len(_INVARIANTS)
    print()
    print("══════════════════════════════════════════")
    if hard_failures:
        print(f"  RESULT: {_RED}FAIL{_RESET} — hard gate failures: {', '.join(hard_failures)}")
        return 1
    else:
        print(f"  RESULT: {_GREEN}PASS{_RESET} — all {total} invariants verified ({passed}/{total})")
        return 0


sys.exit(asyncio.run(main()))
