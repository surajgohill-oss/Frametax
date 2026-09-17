#!/usr/bin/env python3
"""Fresh four-production acceptance batch under canonical-1.73.0.
Runs against the isolated audit database only."""
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"
PROJECTS = {
    "The Little Utopia": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "F#K Valentine's Day": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "Bad Hombres": "4355ae88-a636-4c18-af60-ad73b2646124",
    "Lips Like Sugar": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
}
EXCLUDED_TITLES = {"V-BRAT", "Underwater"}


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved audit database.")
        sys.exit(1)

    from app.services import canonical_evaluation as ce

    async with AsyncSession(engine, expire_on_commit=False) as db:
        for title, pid in PROJECTS.items():
            result = await ce.evaluate_project(db, pid)
            fp = result.get("state_fingerprint")
            counts = (await db.execute(text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status', count(*)
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
                GROUP BY 1 ORDER BY 2 DESC
                """
            ), {"pid": pid, "ev": ce.ENGINE_VERSION, "fp": fp})).fetchall()
            anchor = (await db.execute(text(
                """
                SELECT scr.total_incentive_value_usd, scr.true_net_cost_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'is_baseline' = 'true'
                LIMIT 1
                """
            ), {"pid": pid, "ev": ce.ENGINE_VERSION, "fp": fp})).fetchone()
            ho_check = (await db.execute(text(
                """
                SELECT scr.calculation_trace_json->'program_slugs', scr.calculation_trace_json->>'candidate_status'
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->'program_slugs' @> '"us_ga_film_credit"'::jsonb
                LIMIT 3
                """
            ), {"pid": pid, "ev": ce.ENGINE_VERSION, "fp": fp})).fetchall()
            print(f"=== {title} ===")
            print(f"  status={result.get('status')} fingerprint={fp}")
            print(f"  anchor_incentive={anchor[0] if anchor else None} anchor_npc={anchor[1] if anchor else None}")
            print(f"  disposition counts: {dict(counts)}")
            print(f"  HO-001-related rows sample: {ho_check[:3]}")
            print()

        excluded = (await db.execute(text(
            "SELECT title FROM projects WHERE title = ANY(:titles)"
        ), {"titles": list(EXCLUDED_TITLES)})).fetchall()
        print(f"V-BRAT/Underwater present in DB (should be for informational check only, "
              f"NOT evaluated by this script): {[r[0] for r in excluded]}")


if __name__ == "__main__":
    asyncio.run(main())
