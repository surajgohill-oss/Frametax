"""
Marketplace freshness monitoring.

Freshness is computed per tracked_event and represents how current the
collection data is for that (marketplace, event) pair.

Status levels
─────────────
  fresh  — data collected within the expected cadence window
  late   — data within 2× the expected window (one missed cycle)
  stale  — data older than 2× the expected window, OR the event is fewer
            than 14 days away and the data is older than 24 h
  dead   — data older than 7 days, OR ≥ 10 consecutive failures, OR never
            collected at all

Stale reasons
─────────────
  never_collected       — no successful poll run has ever completed
  collector_dead        — ≥ 10 consecutive failures OR > 7 d without success
  near_event_24h_rule   — event < 14 days away and data > 24 h old
  missed_cadence_window — data older than 2× the expected polling interval

Usage
─────
  from app.utils.freshness import compute_freshness, is_current

  result = compute_freshness(
      marketplace_slug="stubhub",
      event_date=event.event_date,
      poll_interval_minutes=te.poll_interval_minutes,
      last_success_at=last_success_dt,   # or None
      consecutive_failures=4,
  )

  if not is_current(result):
      # exclude this marketplace from current-price summaries
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


# ── Status constants ──────────────────────────────────────────────────────────

FRESH = "fresh"
LATE  = "late"
STALE = "stale"
DEAD  = "dead"


# ── Thresholds ────────────────────────────────────────────────────────────────

_DEAD_AGE_MINUTES    = 7 * 24 * 60   # 7 days without a successful collection → DEAD
_DEAD_FAILURE_COUNT  = 10            # ≥ 10 consecutive errors → DEAD
_NEAR_EVENT_DAYS     = 14            # within 14 days of the event…
_NEAR_EVENT_MAX_AGE  = 24 * 60       # …data must be < 24 h old or it's STALE


# ── Expected interval computation ────────────────────────────────────────────

def _expected_interval_minutes(
    event_date: datetime,
    stored_poll_interval_minutes: int,
) -> int:
    """
    Return the expected polling interval in minutes for this tracked event.

    We prefer the stored `poll_interval_minutes` from the TrackedEvent row
    (the scheduler's last computed value) because it already accounts for how
    far the event is in the future.  If that value is missing or implausible
    we fall back to the scheduler's own 5-tier formula.
    """
    if stored_poll_interval_minutes and 1 <= stored_poll_interval_minutes <= 1440:
        return stored_poll_interval_minutes

    # Scheduler's 5-tier formula (mirrors scheduler.compute_poll_interval_minutes)
    now = _utcnow_naive()
    seconds = (_to_naive(event_date) - now).total_seconds()

    if seconds < -5 * 60:   return 5     # just-completed
    if seconds < 8 * 3600:  return 15    # < 8 h
    if seconds < 2 * 86400: return 60    # < 2 days
    if seconds < 10 * 86400:return 240   # < 10 days
    return 1440                          # >= 10 days


# ── Core calculation ──────────────────────────────────────────────────────────

def compute_freshness(
    *,
    marketplace_slug: str,
    event_date: datetime,
    poll_interval_minutes: int,
    last_success_at: Optional[datetime],
    consecutive_failures: int,
    now: Optional[datetime] = None,
) -> dict:
    """
    Compute freshness for a single (marketplace, event) pair.

    Returns a dict:
      freshness_status           "fresh" | "late" | "stale" | "dead"
      last_success_at            ISO-8601 string | None
      age_minutes                int | None   (None when never collected)
      consecutive_failures       int
      stale_reason               str | None
      expected_interval_minutes  int
    """
    now_naive = _to_naive(now) if now is not None else _utcnow_naive()
    expected  = _expected_interval_minutes(event_date, poll_interval_minutes)

    # ── Never collected ───────────────────────────────────────────────────────
    if last_success_at is None:
        return _make(
            status=DEAD,
            last_success_at=None,
            age_minutes=None,
            consecutive_failures=consecutive_failures,
            stale_reason="never_collected",
            expected=expected,
        )

    # ── Age ───────────────────────────────────────────────────────────────────
    age_minutes = max(0, int((_to_naive(now_naive) - _to_naive(last_success_at)).total_seconds() / 60))

    # ── DEAD: very old or too many consecutive failures ───────────────────────
    if age_minutes >= _DEAD_AGE_MINUTES or consecutive_failures >= _DEAD_FAILURE_COUNT:
        return _make(
            status=DEAD,
            last_success_at=last_success_at,
            age_minutes=age_minutes,
            consecutive_failures=consecutive_failures,
            stale_reason="collector_dead",
            expected=expected,
        )

    # ── Near-event rule ───────────────────────────────────────────────────────
    seconds_to_event = (_to_naive(event_date) - now_naive).total_seconds()
    if 0 < seconds_to_event < _NEAR_EVENT_DAYS * 86400:
        if age_minutes > _NEAR_EVENT_MAX_AGE:
            return _make(
                status=STALE,
                last_success_at=last_success_at,
                age_minutes=age_minutes,
                consecutive_failures=consecutive_failures,
                stale_reason="near_event_24h_rule",
                expected=expected,
            )

    # ── Normal cadence ────────────────────────────────────────────────────────
    if age_minutes <= expected:
        status, reason = FRESH, None
    elif age_minutes <= 2 * expected:
        status, reason = LATE, None
    else:
        status, reason = STALE, "missed_cadence_window"

    return _make(
        status=status,
        last_success_at=last_success_at,
        age_minutes=age_minutes,
        consecutive_failures=consecutive_failures,
        stale_reason=reason,
        expected=expected,
    )


def is_current(freshness: dict) -> bool:
    """Return True if the status is fresh or late (safe to use as current market data)."""
    return freshness.get("freshness_status") in (FRESH, LATE)


# ── Private helpers ───────────────────────────────────────────────────────────

def _utcnow_naive() -> datetime:
    return datetime.utcnow()


def _to_naive(dt: datetime) -> datetime:
    """Strip timezone info for consistent arithmetic."""
    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _make(
    *,
    status: str,
    last_success_at: Optional[datetime],
    age_minutes: Optional[int],
    consecutive_failures: int,
    stale_reason: Optional[str],
    expected: int,
) -> dict:
    return {
        "freshness_status":          status,
        "last_success_at":           last_success_at.isoformat() if last_success_at else None,
        "age_minutes":               age_minutes,
        "consecutive_failures":      consecutive_failures,
        "stale_reason":              stale_reason,
        "expected_interval_minutes": expected,
    }
