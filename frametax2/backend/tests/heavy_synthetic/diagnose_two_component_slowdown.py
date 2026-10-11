"""DIAGNOSTIC (not a pass/fail check): bounded cardinality and query-plan evidence for the evaluation slowdown on a budget with TWO movable
components (post-production + VFX), which exceeded a 240 s evaluation bound on a Canada-Ontario home while the same budget without the post line
took about 34 s.

Set DIAG_ALIAS_MEMO=1 to run the evaluation inside canonical_program_identity.alias_memo_scope(), as the bounded regeneration wrapper does.
Run (foreground, one process, hard alarm):
    DATABASE_URL unset  perl -e 'alarm shift; exec @ARGV' 300 python -u -m pytest tests/heavy_synthetic/diagnose_two_component_slowdown.py -q -s

Everything is synthetic and rolled back on the isolated test database. The evaluation is ABORTED by this script, deliberately, when it exceeds
BUDGET_SECONDS of CPU time or MAX_STATEMENTS database statements (whichever first); the output is the evidence, not a verdict. It records:
  * a cProfile of the evaluation up to the abort (call counts are the cardinality of the search);
  * every distinct normalized SQL statement: execution count, total and max time (a repeated statement is an N+1 pattern);
  * periodic Python stack samples (faulthandler) showing whether the process is computing or waiting on the database;
  * EXPLAIN (ANALYZE, BUFFERS) of the statement with the largest total time, when it is a SELECT."""
from __future__ import annotations

import asyncio
import contextlib
import cProfile
import faulthandler
import os
import io
import pstats
import re
import signal
import sys
import time

from sqlalchemy import event, text

from app.db.session import engine
from app.services import canonical_evaluation as ce
from tests.isolated_records import create_synthetic_project, isolated_session

BUDGET_SECONDS = 35   # CPU seconds of the profiled evaluation (cProfile roughly doubles run time); enforced by SIGVTALRM, NOT SIGALRM, so the outer perl alarm watchdog is never replaced
MAX_STATEMENTS = 400_000
LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
         ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("5000", "POST PRODUCTION", "post_production", "post", 300_000.0),
         ("6100", "VFX", "vfx", "post", 300_000.0))


class _Abort(BaseException):
    """BaseException on purpose: the evaluator has broad `except Exception` handlers that would swallow a plain Exception and keep computing."""


def _normalize(sql: str) -> str:
    sql = re.sub(r"'[^']*'", "?", sql)
    sql = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "?", sql)
    sql = re.sub(r"\b\d+(\.\d+)?\b", "?", sql)
    sql = re.sub(r"\s+", " ", sql)
    sql = re.sub(r"\(\s*\?(\s*,\s*\?)+\s*\)", "(?...)", sql)
    return sql.strip()[:600]


async def test_two_component_budget_cardinality_and_plan_evidence():
    stats: dict[str, list] = {}
    sample_params: dict[str, tuple] = {}
    state = {"n": 0, "t0": time.monotonic(), "start": {}}

    def before(conn, cursor, statement, parameters, context, executemany):   # noqa: ARG001
        state["n"] += 1
        state["start"][id(cursor)] = time.monotonic()
        if state["n"] > MAX_STATEMENTS or time.monotonic() - state["t0"] > BUDGET_SECONDS:
            raise _Abort(f"bound reached after {state['n']} statements / {time.monotonic() - state['t0']:.0f}s")

    def after(conn, cursor, statement, parameters, context, executemany):   # noqa: ARG001
        dt = time.monotonic() - state["start"].pop(id(cursor), time.monotonic())
        key = _normalize(statement)
        row = stats.setdefault(key, [0, 0.0, 0.0])
        row[0] += 1
        row[1] += dt
        row[2] = max(row[2], dt)
        sample_params.setdefault(key, (statement, parameters))

    sync = engine.sync_engine
    event.listen(sync, "before_cursor_execute", before)
    event.listen(sync, "after_cursor_execute", after)
    faulthandler.dump_traceback_later(25, repeat=True, file=sys.stderr)
    aborted = None
    plan = None
    try:
        async with isolated_session() as db:
            pid = await create_synthetic_project(db, lines=LINES, home_code="CA-ON")
            state["t0"], state["n"] = time.monotonic(), 0
            def _on_cpu_budget(signum, frame):   # noqa: ARG001
                raise _Abort(f"CPU budget of {BUDGET_SECONDS}s reached")
            signal.signal(signal.SIGVTALRM, _on_cpu_budget)
            signal.setitimer(signal.ITIMER_VIRTUAL, BUDGET_SECONDS)
            prof = cProfile.Profile()
            prof.enable()
            from app.services.canonical_program_identity import alias_memo_scope
            scope = alias_memo_scope() if os.environ.get("DIAG_ALIAS_MEMO") == "1" else contextlib.nullcontext()
            try:
                with scope:
                    await ce.evaluate_project(db, pid)
            except _Abort as exc:
                aborted = str(exc)
            except Exception as exc:                                    # an abort surfaces wrapped by the evaluator's own error handling
                aborted = f"{type(exc).__name__}: {exc}"[:300]
            signal.setitimer(signal.ITIMER_VIRTUAL, 0)
            prof.disable()
            event.remove(sync, "before_cursor_execute", before)
            heaviest = max(stats.items(), key=lambda kv: kv[1][1], default=None)
            if heaviest and heaviest[0].upper().startswith("SELECT"):
                statement, parameters = sample_params[heaviest[0]]
                try:
                    async with engine.connect() as c2:
                        rows = (await c2.exec_driver_sql("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF) " + statement, parameters)).fetchall()
                        plan = "\n".join(r[0] for r in rows)[:3500]
                except Exception as exc:
                    plan = f"EXPLAIN not run: {type(exc).__name__}: {exc}"[:300]
    finally:
        faulthandler.cancel_dump_traceback_later()
        event.remove(sync, "after_cursor_execute", after)
    total_n = sum(v[0] for v in stats.values())
    total_t = sum(v[1] for v in stats.values())
    print(f"\nDIAG aborted={aborted!r} statements={total_n} db_seconds={total_t:.1f} wall_seconds={time.monotonic() - state['t0']:.1f}")
    for key, (n, t, mx) in sorted(stats.items(), key=lambda kv: -kv[1][1])[:8]:
        print(f"DIAG count={n} total={t:.2f}s max={mx * 1000:.1f}ms :: {key}")
    print("DIAG most-repeated:", [(v[0], k[:90]) for k, v in sorted(stats.items(), key=lambda kv: -kv[1][0])[:4]])
    print("DIAG PLAN of the heaviest SELECT:\n" + (plan or "none"))
    out = io.StringIO()
    st = pstats.Stats(prof, stream=out)
    st.sort_stats("tottime").print_stats(14)
    print("DIAG CPROFILE by own time (ncalls = cardinality):\n" + "\n".join(l[:200] for l in out.getvalue().splitlines() if l.strip())[:5200])
