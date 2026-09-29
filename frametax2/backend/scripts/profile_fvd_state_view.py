#!/usr/bin/env python3
"""Profile the canonical_production_view.py serving layer for FVD directly
(evaluate_project() already confirmed fast/reused) to find the state
endpoint's actual bottleneck."""
import asyncio
import cProfile
import os
import pstats
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"


async def run():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB:
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not {APPROVED_DB!r}.")
        sys.exit(1)

    from app.services.canonical_production_view import build_production_and_structures

    async with AsyncSession(engine, expire_on_commit=False) as db:
        import time
        t0 = time.monotonic()
        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        t1 = time.monotonic()
    print(f"build_production_and_structures took {t1 - t0:.2f}s")
    structures = view.get("structures", {}).get("allocated_structures", {})
    for key in ("optimizer_scenarios", "optimizer_candidates"):
        v = structures.get(key)
        if isinstance(v, list):
            print(f"{key}: {len(v)} entries")


def main():
    profiler = cProfile.Profile()
    profiler.enable()
    asyncio.run(run())
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(40)
    stats.sort_stats("tottime")
    print("\n=== BY SELF (tottime) TIME ===\n")
    stats.print_stats(30)


if __name__ == "__main__":
    main()
