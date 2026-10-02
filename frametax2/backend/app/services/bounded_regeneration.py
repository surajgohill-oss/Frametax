"""BOUNDED PROJECT REGENERATION (2026-10-02) -- the ONE entry every explicit project regeneration must use.

A cold evaluation of a real production is a long-running, CPU-bound process (Lips Like Sugar needed 2,951 s after the
2026-10-02 pricing reconciliation, 4x the project's 720 s ceiling, and nothing stopped it). This wrapper makes the
ceiling REAL:

  * a hard wall-clock limit (default 720 s) enforced twice: a SIGALRM that raises `RegenerationTimeout` inside the running
    evaluation (so the open transaction is rolled back and no partial generation is committed), and
    `faulthandler.dump_traceback_later(..., exit=True)` as a backstop that terminates the process even when stuck in C
    code (PostgreSQL then rolls the connection's transaction back);
  * the alias-lookup memo scope (`canonical_program_identity.alias_memo_scope`) for the hot hybrid search;
  * the acceptance-database assertion every long-running command must make before it starts;
  * a progress ticker (phase + elapsed) for the operator;
  * `measure_only=True`: runs the SAME evaluation under a throw-away engine stamp with commits turned into flushes and a
    final rollback, so a performance measurement can never touch (or delete) the real current generation.

Not a fingerprint-hashed module: using it changes no generation identity.
"""
from __future__ import annotations

import asyncio
import faulthandler
import gc
import os
import signal
import sys
import time
import uuid

HARD_TIMEOUT_SECONDS = 720
ACCEPTANCE_DB = "frametax2_claude_optimizer_acceptance_20260919"


class RegenerationTimeout(RuntimeError):
    """The hard wall-clock ceiling was reached; nothing was committed."""


def assert_acceptance_database(url: str | None = None) -> str:
    url = url or os.environ.get("DATABASE_URL", "")
    if not url.endswith(ACCEPTANCE_DB):
        raise RuntimeError(f"refusing to regenerate outside the acceptance database ({ACCEPTANCE_DB}); DATABASE_URL={url!r}")
    return url


async def run_bounded(coro_factory, *, timeout_s: float = HARD_TIMEOUT_SECONDS, label: str = "regeneration"):
    """Runs `coro_factory()` under the hard ceiling. Raises RegenerationTimeout on expiry (after unwinding, so the caller's
    session rolls back). `faulthandler` terminates the whole process 10 s later if the unwind itself is stuck."""
    start = time.monotonic()

    def _on_alarm(signum, frame):  # noqa: ARG001
        raise RegenerationTimeout(f"{label}: exceeded the hard {timeout_s:.0f}s ceiling after {time.monotonic() - start:.0f}s")

    previous = signal.signal(signal.SIGALRM, _on_alarm)
    faulthandler.dump_traceback_later(timeout_s + 10, exit=True, file=sys.stderr)
    signal.setitimer(signal.ITIMER_REAL, timeout_s)
    try:
        return await coro_factory()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        faulthandler.cancel_dump_traceback_later()
        signal.signal(signal.SIGALRM, previous)


async def regenerate_project(project_id, *, timeout_s: float = HARD_TIMEOUT_SECONDS, measure_only: bool = False,
                             session_factory=None, progress_every_s: float = 60.0) -> dict:
    """Evaluate one project once, bounded. Returns the evaluator's summary plus `elapsed_s` / `measure_only` / `phase_log`."""
    assert_acceptance_database()
    from app.services import _lls_profile_sink as sink
    from app.services import canonical_evaluation as ce
    from app.services.canonical_program_identity import alias_memo_scope

    if session_factory is None:
        from app.db.session import AsyncSessionLocal as session_factory  # noqa: N813
    project_id = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
    log: list[tuple[float, str]] = []
    stop = asyncio.Event()

    async def _ticker(t0: float):
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=progress_every_s)
            except asyncio.TimeoutError:
                entry = (round(time.monotonic() - t0, 1), str(sink.PHASE))
                log.append(entry)
                print(f"[regen {entry[0]:>7.1f}s] {entry[1]}", flush=True)

    real_engine_version = ce.ENGINE_VERSION
    t0 = time.monotonic()
    sink.ENABLED = True
    sink.reset()
    ticker = asyncio.ensure_future(_ticker(t0))
    try:
        async with session_factory() as session:
            if measure_only:
                ce.ENGINE_VERSION = real_engine_version + "-measure"
                session.commit = session.flush  # type: ignore[method-assign]  # never persist a measurement run

            async def _go():
                # The evaluation allocates millions of short-lived ORM / dataclass objects; with the default thresholds the
                # cyclic collector re-walks an ever-growing heap (RSS reached 1 GB+). Raise the young-generation threshold
                # for the run only (no collection is disabled, so cyclic garbage is still reclaimed).
                old_thresholds = gc.get_threshold()
                gc.set_threshold(200_000, 20, 50)
                try:
                    with alias_memo_scope():
                        return await ce.evaluate_project(session, project_id)
                finally:
                    gc.set_threshold(*old_thresholds)

            try:
                result = await run_bounded(_go, timeout_s=timeout_s, label=f"project {project_id}")
                if measure_only:
                    await session.rollback()
                else:
                    await session.commit()
            except BaseException:
                await session.rollback()
                raise
    finally:
        ce.ENGINE_VERSION = real_engine_version
        stop.set()
        await ticker
        sink.ENABLED = False
    out = dict(result) if isinstance(result, dict) else {"result": result}
    out.update(elapsed_s=round(time.monotonic() - t0, 1), measure_only=measure_only, phase_log=log,
               counters=dict(sink.COUNTERS))
    return out
