"""LLS-SPECIFIC PERFORMANCE REPAIR (2026-09-30) -- a tiny, opt-in diagnostic
sink for the ONE authorized instrumented Lips Like Sugar profiling run.

Disabled by default (`ENABLED = False`) -- every counter call is a single
boolean check plus (when disabled) nothing else, so normal evaluate_project
calls (every existing test, every other production) pay no real cost and are
byte-identical to before this file existed. The standalone profiling script
flips `ENABLED = True` before calling evaluate_project, and reads `COUNTERS`/
`PHASE` directly (including from a SIGALRM handler, since this is plain
synchronous module state -- no event loop or lock needed to read it).

This sink is a default-disabled diagnostic: counters, phase timers
(`timed`) and bulk-writer drain records. Disabled, every call is a single
boolean check.
"""
from __future__ import annotations

import time
from contextlib import contextmanager

ENABLED = False
COUNTERS: dict[str, int] = {}
TIMERS: dict[str, float] = {}
DRAINS: list[tuple[int, float, float, int]] = []  # (n, start_s, end_s, rows)
PHASE: str = "not started"
PHASE_HISTORY: list[tuple[float, str]] = []
_START = 0.0
_LAST_PRINT = 0.0


def reset(start_time: float | None = None) -> None:
    global PHASE, _START
    COUNTERS.clear()
    TIMERS.clear()
    DRAINS.clear()
    PHASE_HISTORY.clear()
    PHASE = "not started"
    _START = start_time if start_time is not None else time.time()


def tick(key: str, n: int = 1) -> None:
    if not ENABLED:
        return
    COUNTERS[key] = COUNTERS.get(key, 0) + n


class _NoopTimer:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


_NOOP = _NoopTimer()


class _Timer:
    __slots__ = ("key", "t0")

    def __init__(self, key: str):
        self.key = key

    def __enter__(self):
        self.t0 = time.perf_counter()

    def __exit__(self, *exc):
        TIMERS[self.key] = TIMERS.get(self.key, 0.0) + (time.perf_counter() - self.t0)
        return False


def timed(key: str):
    """Context manager accumulating wall seconds under `key` (no-op when disabled)."""
    return _Timer(key) if ENABLED else _NOOP


def record_drain(start_s: float, end_s: float, rows: int) -> None:
    if not ENABLED:
        return
    DRAINS.append((len(DRAINS) + 1, start_s, end_s, rows))
    TIMERS["db_drain"] = TIMERS.get("db_drain", 0.0) + (end_s - start_s)
    print(f"[drain #{len(DRAINS)} rows={rows} t={start_s:.1f}->{end_s:.1f}s took={end_s - start_s:.2f}s "
          f"cumulative={TIMERS['db_drain']:.2f}s]", flush=True)


def set_phase(phase: str) -> None:
    global PHASE
    if not ENABLED:
        return
    PHASE = phase
    PHASE_HISTORY.append((round(time.time() - _START, 2), phase))


def elapsed() -> float:
    return round(time.time() - _START, 2)


def _rss_mb() -> int:
    import resource
    import sys
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(r / (1024 * 1024) if sys.platform == "darwin" else r / 1024)


def maybe_print(interval_s: float = 10.0) -> None:
    """Prints a one-line progress snapshot to stdout at most once per
    `interval_s` seconds -- called from a hot loop (cheap: one time.time()
    comparison when nothing is due). This is the "periodic progress output"
    the diagnostic run needs; `dump()` above is the fuller on-demand/signal-
    handler report."""
    global _LAST_PRINT
    if not ENABLED:
        return
    now = time.time()
    if now - _LAST_PRINT < interval_s:
        return
    _LAST_PRINT = now
    print(
        f"[progress t={elapsed()}s rss={_rss_mb()}MB] phase={PHASE} | "
        + " ".join(f"{k}={v}" for k, v in sorted(COUNTERS.items()))
        + " | " + " ".join(f"T.{k}={v:.1f}s" for k, v in sorted(TIMERS.items())),
        flush=True,
    )


def dump(label: str = "PROFILE DUMP") -> str:
    lines = [f"=== {label} (elapsed={elapsed()}s) ===", f"current phase: {PHASE}"]
    for k in sorted(COUNTERS):
        lines.append(f"  {k} = {COUNTERS[k]}")
    for k in sorted(TIMERS):
        lines.append(f"  timer {k} = {TIMERS[k]:.2f}s")
    lines.append(f"  drains = {len(DRAINS)} rows={sum(d[3] for d in DRAINS)}")
    if PHASE_HISTORY:
        lines.append("phase history (last 10):")
        for t, p in PHASE_HISTORY[-10:]:
            lines.append(f"  t={t}s: {p}")
    return "\n".join(lines)
