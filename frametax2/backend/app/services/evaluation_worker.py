"""One evaluation of one project in its OWN process, under the existing bounded workflow (services/bounded_regeneration.py).

Run by ``evaluation_jobs.EvaluationJobs`` for the producer-input Save (POST /projects/{id}/evaluation/begin). It is the same
``evaluate_project`` behind the same hard 720 s ceiling (SIGALRM unwinds the open transaction; faulthandler is the backstop); a separate
process only keeps the API's event loop responsive while the CPU-bound search runs, and lets the parent kill it at the deadline -- PostgreSQL
then rolls the transaction back, so no partial generation is ever committed and the saved inputs and prior generations are untouched.

A session-level PostgreSQL advisory lock keyed on the project makes a second evaluation of the same project (another API worker, another
tab, a retry that raced the first) refuse immediately instead of duplicating work; the lock dies with the connection, so a killed worker never leaves it held.

Final stdout line is one JSON object: ``{"outcome": "COMPLETED"|"TIMED_OUT"|"ALREADY_RUNNING"|"FAILED", ...}``. Not a fingerprint-hashed module."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid

from sqlalchemy import text

from app.services.bounded_regeneration import HARD_TIMEOUT_SECONDS, RegenerationTimeout, regenerate_project


def advisory_key(project_id: uuid.UUID) -> int:
    """Stable signed 64-bit key for pg_try_advisory_lock."""
    return int.from_bytes(hashlib.sha256(f"evaluate:{project_id}".encode()).digest()[:8], "big", signed=True)


async def _evaluate(project_id: uuid.UUID, timeout_s: float) -> dict:
    from app.db.session import engine

    async with engine.connect() as lock_conn:
        got = (await lock_conn.execute(text("select pg_try_advisory_lock(:k)"), {"k": advisory_key(project_id)})).scalar()
        if not got:
            return {"outcome": "ALREADY_RUNNING"}
        try:
            out = await regenerate_project(project_id, timeout_s=timeout_s, require_isolated_database=False, progress_every_s=3600.0)
        finally:
            await lock_conn.execute(text("select pg_advisory_unlock(:k)"), {"k": advisory_key(project_id)})
    keep = {k: v for k, v in out.items() if k in ("status", "blockers", "elapsed_s", "engine_version", "input_fingerprint")}
    return {"outcome": "COMPLETED", **keep}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_id")
    ap.add_argument("--timeout", type=float, default=HARD_TIMEOUT_SECONDS)
    a = ap.parse_args(argv)
    timeout_s = min(a.timeout, HARD_TIMEOUT_SECONDS)  # the ceiling can be lowered, never raised
    try:
        result = asyncio.run(_evaluate(uuid.UUID(a.project_id), timeout_s))
        code = 3 if result["outcome"] == "ALREADY_RUNNING" else 0
    except RegenerationTimeout as exc:
        result, code = {"outcome": "TIMED_OUT", "detail": str(exc)}, 2
    except Exception as exc:  # noqa: BLE001 -- reported to the parent as a failure; the transaction was rolled back by regenerate_project
        result, code = {"outcome": "FAILED", "detail": f"{type(exc).__name__}: {exc}"[:500]}, 1
    print(json.dumps(result, default=str), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
