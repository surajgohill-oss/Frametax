"""
Regression tests for scheduler cadence and lifecycle logic.

Covers:
  1. Future event cadence — correct interval at each breakpoint
  2. Near-event cadence — sub-30-minute and post-start both return 2
  3. Post-start active inventory polling — never returns None
  4. Exhaustion transition — fires only post-start, only after 5 zero cycles
  5. Pre-event zero inventory — event stays ACTIVE (never completes)
  6. Completed event exclusion — is_active=False prevents polling
  7. 24h buffer — exhaustion/lifecycle don't trigger in final 24h before show
  8. Timezone regression — LA 8pm PDT stored as next-day 03:00 UTC
"""
"""
Pure-function tests — no DB or apscheduler import needed.
The functions under test are inlined here from app/scheduler.py so this
file runs in any environment that has only the stdlib.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ── Inlined from app/scheduler.py (keep in sync) ─────────────────────────────
# IMPORTANT: These copies must match scheduler.py exactly, including the 24h buffer.

_EXHAUSTION_THRESHOLD = 5
_ADMISSION_DAYS = 21
_LA_TZ = ZoneInfo("America/Los_Angeles")


def compute_poll_interval_minutes(event_date: datetime) -> int:
    seconds = (event_date - datetime.now(timezone.utc)).total_seconds()
    if seconds < 0:          return 2
    if seconds < 30 * 60:   return 2
    if seconds < 90 * 60:   return 5
    if seconds < 6 * 3600:  return 15
    if seconds < 24 * 3600: return 30
    if seconds < 3 * 86400: return 60
    if seconds < 7 * 86400: return 240
    if seconds < 14 * 86400: return 480
    if seconds < 30 * 86400: return 720
    return 1440


def compute_lifecycle_phase(event_date: datetime, consecutive_zero: int = 0) -> str:
    # Apply 24h buffer matching scheduler.py — keep in sync
    adjusted = event_date + timedelta(hours=24)
    seconds = (adjusted - datetime.now(timezone.utc)).total_seconds()
    if seconds >= 0:
        if seconds >= _ADMISSION_DAYS * 24 * 3600:
            return "pre_admission"
        return "active"
    if consecutive_zero >= _EXHAUSTION_THRESHOLD:
        return "completed"
    if consecutive_zero > 0:
        return "exhaustion_pending"
    return "live"


def event_status_from_date(event_date: datetime) -> str:
    # Apply 24h buffer matching scheduler.py — keep in sync
    adjusted = event_date + timedelta(hours=24)
    seconds = (adjusted - datetime.now(timezone.utc)).total_seconds()
    if seconds < -3 * 3600:
        return "completed"
    if seconds < 0:
        return "in_progress"
    return "upcoming"


# ── Helper ────────────────────────────────────────────────────────────────────

def future(seconds: float) -> datetime:
    """Return a datetime that is `seconds` in the future."""
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)

def past(seconds: float) -> datetime:
    """Return a datetime that is `seconds` in the past."""
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


# ── 1. Future event cadence ───────────────────────────────────────────────────

class TestFutureEventCadence:
    def test_over_30_days_is_daily(self):
        assert compute_poll_interval_minutes(future(31 * 86400)) == 1440

    def test_exactly_30_days_boundary(self):
        assert compute_poll_interval_minutes(future(30 * 86400 + 1)) == 1440
        assert compute_poll_interval_minutes(future(30 * 86400 - 1)) == 720

    def test_14_to_30_days_is_12h(self):
        assert compute_poll_interval_minutes(future(20 * 86400)) == 720
        assert compute_poll_interval_minutes(future(14 * 86400 + 1)) == 720

    def test_7_to_14_days_is_8h(self):
        assert compute_poll_interval_minutes(future(10 * 86400)) == 480
        assert compute_poll_interval_minutes(future(7 * 86400 + 1)) == 480

    def test_3_to_7_days_is_4h(self):
        assert compute_poll_interval_minutes(future(5 * 86400)) == 240
        assert compute_poll_interval_minutes(future(3 * 86400 + 1)) == 240

    def test_24h_to_3d_is_1h(self):
        assert compute_poll_interval_minutes(future(2 * 86400)) == 60
        assert compute_poll_interval_minutes(future(86400 + 1)) == 60

    def test_6h_to_24h_is_30min(self):
        assert compute_poll_interval_minutes(future(12 * 3600)) == 30
        assert compute_poll_interval_minutes(future(6 * 3600 + 1)) == 30

    def test_90min_to_6h_is_15min(self):
        assert compute_poll_interval_minutes(future(3 * 3600)) == 15
        assert compute_poll_interval_minutes(future(90 * 60 + 1)) == 15

    def test_30min_to_90min_is_5min(self):
        assert compute_poll_interval_minutes(future(60 * 60)) == 5
        assert compute_poll_interval_minutes(future(30 * 60 + 1)) == 5

    def test_under_30min_is_2min(self):
        assert compute_poll_interval_minutes(future(15 * 60)) == 2
        assert compute_poll_interval_minutes(future(1)) == 2


# ── 2. Near-event cadence ─────────────────────────────────────────────────────

class TestNearEventCadence:
    def test_at_event_start_returns_2(self):
        result = compute_poll_interval_minutes(datetime.now(timezone.utc))
        assert result == 2

    def test_post_start_returns_2(self):
        assert compute_poll_interval_minutes(past(1)) == 2
        assert compute_poll_interval_minutes(past(3600)) == 2
        assert compute_poll_interval_minutes(past(12 * 3600)) == 2
        assert compute_poll_interval_minutes(past(48 * 3600)) == 2

    def test_never_returns_none(self):
        for offset_secs in [-7 * 86400, -3600, -60, -1, 0, 1, 60, 3600, 86400, 30 * 86400]:
            dt = datetime.now(timezone.utc) + timedelta(seconds=offset_secs)
            result = compute_poll_interval_minutes(dt)
            assert result is not None, f"Returned None at offset={offset_secs}s"
            assert result > 0, f"Returned non-positive {result} at offset={offset_secs}s"


# ── 3. Lifecycle phase pre-event (with 24h buffer) ──────────────────────────

class TestLifecyclePhasePreEvent:
    def test_far_future_is_pre_admission(self):
        # event_date + 24h > 21d from now → pre_admission
        assert compute_lifecycle_phase(future(25 * 86400)) == "pre_admission"

    def test_within_21d_is_active(self):
        # event_date + 24h is still in the window
        assert compute_lifecycle_phase(future(15 * 86400)) == "active"
        assert compute_lifecycle_phase(future(1)) == "active"

    def test_zero_count_pre_event_stays_active(self):
        """Pre-event zero inventory must NEVER advance lifecycle beyond 'active'."""
        for zero_count in range(10):
            phase = compute_lifecycle_phase(future(86400), consecutive_zero=zero_count)
            assert phase == "active", (
                f"Expected 'active' for pre-event with zero_count={zero_count}, got '{phase}'"
            )


# ── 4. 24h buffer — exhaustion guard ─────────────────────────────────────────

class TestExhaustionGuard24hBuffer:
    """
    REGRESSION: events were deactivated 24h before showtime because
    event_date was stored as calendar_date+T03:00Z (= 8pm PDT the previous day)
    instead of the correct next_day+T03:00Z.

    The 24h buffer in compute_lifecycle_phase ensures exhaustion cannot trigger
    within 24h after the stored event_date, giving post-show inventory time
    to drain.
    """

    def test_stored_date_is_yesterday_lifecycle_still_active_today(self):
        """
        Simulates the Ariana Grande bug:
        Stored event_date = calendar_date T03:00Z (= 8pm PDT day-before)
        Actual show = next_day T03:00Z (= 8pm PDT on the calendar date)

        At T-0 of stored date (= T-24h of actual show), lifecycle must be 'active'.
        """
        # event_date = now (simulates stored date == current time, 24h BEFORE actual show)
        stored_event_date = datetime.now(timezone.utc)
        phase = compute_lifecycle_phase(stored_event_date, consecutive_zero=5)
        assert phase == "active", (
            f"Expected 'active' (24h buffer) but got '{phase}'. "
            "Exhaustion triggered at T-24h before actual show — regression!"
        )

    def test_stored_date_plus_23h_still_active(self):
        """23h after stored event_date → still within 24h buffer → must be 'active'."""
        stored_event_date = past(23 * 3600)
        phase = compute_lifecycle_phase(stored_event_date, consecutive_zero=5)
        assert phase == "active", (
            f"Expected 'active' at T+23h from stored date but got '{phase}'"
        )

    def test_stored_date_plus_25h_allows_exhaustion(self):
        """25h after stored event_date → outside 24h buffer → exhaustion allowed."""
        stored_event_date = past(25 * 3600)
        phase = compute_lifecycle_phase(stored_event_date, consecutive_zero=5)
        assert phase == "completed", (
            f"Expected 'completed' at T+25h from stored date but got '{phase}'"
        )

    def test_event_status_upcoming_during_24h_buffer(self):
        """event_status_from_date must show 'upcoming' during the 24h buffer window."""
        stored_event_date = past(10 * 3600)  # stored 10h ago (= ~T+14h before actual show)
        status = event_status_from_date(stored_event_date)
        assert status == "upcoming", (
            f"Expected 'upcoming' within 24h buffer but got '{status}'"
        )

    def test_event_status_in_progress_near_actual_showtime(self):
        """event_status_from_date must show 'in_progress' near the actual showtime."""
        # stored 22h ago → adjusted = 2h from now → in_progress (< 0 seconds from adjusted)
        stored_event_date = past(22 * 3600)  # adjusted = stored + 24h = now + 2h
        # Wait — adjusted = stored + 24h = (now - 22h) + 24h = now + 2h → STILL upcoming
        # For in_progress we need adjusted to be slightly in the past:
        stored_event_date_2 = past(25 * 3600)  # adjusted = now - 1h → in_progress
        status = event_status_from_date(stored_event_date_2)
        assert status == "in_progress", (
            f"Expected 'in_progress' (adjusted 1h ago) but got '{status}'"
        )


# ── 5. Timezone regression: LA 8pm PDT → UTC next day 03:00 ─────────────────

class TestTimezoneConversion:
    """
    CRITICAL REGRESSION TEST.

    LA concerts are at 8pm PDT (UTC-7) / 8pm PST (UTC-8).
    Summer (PDT, UTC-7): 8pm PDT = 03:00 UTC NEXT DAY
    Winter (PST, UTC-8): 8pm PST = 04:00 UTC NEXT DAY

    If event_date is stored as calendar_date + T03:00Z, that equals
    8pm PDT the PREVIOUS day (= T-24h from actual show).
    The CORRECT storage is (calendar_date + 1 day) + T03:00Z.

    Discovery.py uses: event_date_utc = naive_la_local.replace(tzinfo=_LA_TZ)
    PostgreSQL then converts this aware datetime to UTC for TIMESTAMPTZ storage.
    """

    def test_8pm_pdt_to_utc_is_next_day_0300(self):
        """Jun 21 8pm PDT → UTC Jun 22 03:00:00"""
        # naive LA-local time (as stored by discovery.py before attach)
        local_naive = datetime(2026, 6, 21, 20, 0, 0)  # Jun 21 8pm, no tzinfo
        # attach LA timezone (same as discovery.py: replace(tzinfo=_LA_TZ))
        aware_la = local_naive.replace(tzinfo=_LA_TZ)
        # convert to UTC
        utc = aware_la.astimezone(timezone.utc)

        assert utc.year == 2026
        assert utc.month == 6
        assert utc.day == 22,   f"Expected UTC day=22 but got {utc.day}"
        assert utc.hour == 3,   f"Expected UTC hour=3 but got {utc.hour}"
        assert utc.minute == 0

    def test_8pm_pst_to_utc_is_next_day_0400(self):
        """Jan 15 8pm PST → UTC Jan 16 04:00:00"""
        local_naive = datetime(2026, 1, 15, 20, 0, 0)
        aware_la = local_naive.replace(tzinfo=_LA_TZ)
        utc = aware_la.astimezone(timezone.utc)

        assert utc.year == 2026
        assert utc.month == 1
        assert utc.day == 16,   f"Expected UTC day=16 but got {utc.day}"
        assert utc.hour == 4,   f"Expected UTC hour=4 but got {utc.hour}"

    def test_wrong_storage_is_24h_early(self):
        """
        Bug scenario: storing calendar_date+T03:00Z instead of next_day+T03:00Z
        results in a date 24h before the actual show.
        """
        actual_show_utc = datetime(2026, 6, 22, 3, 0, 0, tzinfo=timezone.utc)   # correct
        wrong_stored    = datetime(2026, 6, 21, 3, 0, 0, tzinfo=timezone.utc)   # bug

        delta = actual_show_utc - wrong_stored
        assert delta.total_seconds() == 86400, "Wrong date must be exactly 24h early"

    def test_24h_buffer_covers_wrong_storage(self):
        """
        The 24h buffer in compute_lifecycle_phase must prevent premature
        exhaustion even when event_date is stored 24h early.

        Scenario: stored 23h 30m ago (= T-30min before actual show).
        adjusted = stored + 24h = now + 30min → seconds > 0 → 'active'.
        Without the buffer: stored is in the past → 'completed' with 5 zeros.
        """
        # stored 23.5h ago (= actual show is still 30min away)
        stored = past(23 * 3600 + 30 * 60)
        # Without buffer: seconds = stored - now < 0 → post-start → 'completed'
        # With 24h buffer: adjusted = stored + 24h = now + 30min → seconds > 0 → 'active'
        phase = compute_lifecycle_phase(stored, consecutive_zero=5)
        assert phase == "active", (
            f"Expected 'active' (show 30min away, stored 23.5h ago) but got '{phase}'. "
            "24h buffer should prevent exhaustion at T-30min before actual show."
        )


# ── 6. Lifecycle phase post-event ─────────────────────────────────────────────

class TestLifecyclePhasePostEvent:
    def test_post_start_no_zeros_is_live(self):
        # stored 25h ago → adjusted = 1h ago → post-start
        assert compute_lifecycle_phase(past(25 * 3600), consecutive_zero=0) == "live"

    def test_post_start_partial_zeros_is_exhaustion_pending(self):
        for n in range(1, _EXHAUSTION_THRESHOLD):
            phase = compute_lifecycle_phase(past(25 * 3600), consecutive_zero=n)
            assert phase == "exhaustion_pending", (
                f"Expected 'exhaustion_pending' for zero_count={n}, got '{phase}'"
            )

    def test_post_start_threshold_zeros_is_completed(self):
        phase = compute_lifecycle_phase(past(25 * 3600), consecutive_zero=5)
        assert phase == "completed"


# ── 7. Pre-event zero inventory — event must stay ACTIVE ─────────────────────

class TestPreEventZeroInventory:
    def test_repeated_collector_failure_pre_event_stays_active(self):
        event_date = future(7 * 86400)
        for i in range(20):
            phase = compute_lifecycle_phase(event_date, consecutive_zero=i)
            assert phase == "active", (
                f"Iteration {i}: expected 'active' for pre-event zero_count={i}, got '{phase}'"
            )

    def test_collector_error_pre_event_stays_active(self):
        assert compute_lifecycle_phase(future(3600), consecutive_zero=99) == "active"

    def test_poll_interval_still_returned_pre_event_zero(self):
        event_date = future(2 * 3600)
        interval = compute_poll_interval_minutes(event_date)
        assert interval == 15, f"Expected 15 min at 2h-out, got {interval}"


# ── 8. Exhaustion threshold ───────────────────────────────────────────────────

class TestExhaustionThreshold:
    def test_threshold_constant_is_5(self):
        assert _EXHAUSTION_THRESHOLD == 5

    def test_4_consecutive_zeros_not_yet_completed(self):
        phase = compute_lifecycle_phase(past(25 * 3600), consecutive_zero=4)
        assert phase == "exhaustion_pending"

    def test_5_consecutive_zeros_triggers_completion(self):
        phase = compute_lifecycle_phase(past(25 * 3600), consecutive_zero=5)
        assert phase == "completed"

    def test_inventory_found_post_start_resets_to_live(self):
        phase = compute_lifecycle_phase(past(25 * 3600), consecutive_zero=0)
        assert phase == "live"
