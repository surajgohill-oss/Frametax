#!/usr/bin/env python3
"""Reproduce the exact GET /state route steps for FVD, timing each stage,
then profile the slowest stage in isolation."""
import asyncio
import json
import os
import sys
import time

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

    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import (
        build_generic_pkg_and_economics,
        build_production_and_structures,
    )
    from app.services.fx_refresh import ensure_fx_freshness

    async with AsyncSession(engine, expire_on_commit=False) as db:
        t0 = time.monotonic()
        await ensure_fx_freshness(db)
        t1 = time.monotonic()
        print(f"ensure_fx_freshness: {t1 - t0:.2f}s")

        await evaluate_project(db, FVD_PROJECT_ID)
        t2 = time.monotonic()
        print(f"evaluate_project: {t2 - t1:.2f}s")

        view = await build_production_and_structures(db, FVD_PROJECT_ID)
        t3 = time.monotonic()
        print(f"build_production_and_structures: {t3 - t2:.2f}s")

        sections = await build_generic_pkg_and_economics(db, FVD_PROJECT_ID)
        t4 = time.monotonic()
        print(f"build_generic_pkg_and_economics: {t4 - t3:.2f}s")

        result = {
            "production": view["production"], "pkg": sections.get("pkg"),
            "structures": view["structures"], "economics": sections.get("economics"),
            "people": sections.get("people"), "facts": sections.get("facts"),
        }
        t5 = time.monotonic()
        encoded = json.dumps(result, default=str)
        t6 = time.monotonic()
        print(f"assemble dict: {t5 - t4:.2f}s")
        print(f"json.dumps: {t6 - t5:.2f}s, size={len(encoded):,} bytes")
        print(f"TOTAL: {t6 - t0:.2f}s")


if __name__ == "__main__":
    asyncio.run(run())
