#!/usr/bin/env python3
"""Profile evaluate_project() for FVD with a hard time budget, printing
cumulative-time stats gathered so far when the budget expires (rather than
waiting for the full run to finish, which can take many minutes)."""
import asyncio
import cProfile
import os
import pstats
import signal
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
TIME_BUDGET_SECONDS = int(os.environ.get("PROFILE_BUDGET", "60"))


class TimeBudgetExceeded(Exception):
    pass


def _alarm_handler(signum, frame):
    raise TimeBudgetExceeded()


async def run():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB:
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not {APPROVED_DB!r}.")
        sys.exit(1)

    from app.services.canonical_evaluation import evaluate_project

    async with AsyncSession(engine, expire_on_commit=False) as db:
        result = await evaluate_project(db, FVD_PROJECT_ID)
    print("COMPLETED:", {k: result.get(k) for k in ("status", "engine_version", "priced_count", "unpriceable_count")})


def main():
    profiler = cProfile.Profile()
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(TIME_BUDGET_SECONDS)
    profiler.enable()
    try:
        asyncio.run(run())
    except TimeBudgetExceeded:
        print(f"\n=== TIME BUDGET ({TIME_BUDGET_SECONDS}s) EXCEEDED — dumping partial profile ===\n")
    finally:
        signal.alarm(0)
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        stats.print_stats(40)
        stats.sort_stats("tottime")
        print("\n=== BY SELF (tottime) TIME ===\n")
        stats.print_stats(25)


if __name__ == "__main__":
    main()
