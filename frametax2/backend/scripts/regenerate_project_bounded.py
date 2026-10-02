"""Regenerate ONE project under the hard 720 s ceiling (services/bounded_regeneration.py).

    DATABASE_URL=postgresql+psycopg://.../frametax2_claude_optimizer_acceptance_20260919 \\
        python scripts/regenerate_project_bounded.py <project_id> [--measure] [--timeout 720]

--measure runs the identical evaluation under a throw-away engine stamp and rolls back (never persists, never deletes the
real generation). Exactly one process; never loop this over projects without reading each result.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.services.bounded_regeneration import HARD_TIMEOUT_SECONDS, RegenerationTimeout, regenerate_project


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_id")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--timeout", type=float, default=HARD_TIMEOUT_SECONDS)
    a = ap.parse_args()
    try:
        out = asyncio.run(regenerate_project(a.project_id, timeout_s=min(a.timeout, HARD_TIMEOUT_SECONDS), measure_only=a.measure))
    except RegenerationTimeout as exc:
        print(json.dumps({"status": "TIMEOUT", "detail": str(exc)}))
        return 2
    keep = {k: v for k, v in out.items() if not isinstance(v, (list, dict)) or k in ("counters",)}
    print(json.dumps(keep, default=str)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
