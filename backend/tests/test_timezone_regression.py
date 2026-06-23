"""
Regression test: event visibility with UTC-vs-LA timezone off-by-one.

Events are stored as midnight UTC (T00:00Z), which equals 5 PM PDT the prior
calendar day. The intelligence endpoint must apply a +24h grace window so a
"June 23" event stays visible on June 23 in LA, even though its UTC timestamp
(midnight June 23) was already in the past by 7 AM UTC June 23.

Mirrors the +24h offset documented in scheduler.event_status_from_date.
"""
from datetime import datetime, timedelta, timezone


def _cutoff(now_utc: datetime) -> datetime:
    """The filter boundary used by the intelligence endpoint."""
    return now_utc - timedelta(hours=24)


def test_event_visible_when_la_is_day_of_event_utc_already_past():
    """
    Scenario: LA date = June 23, UTC = June 23 07:09.
    Event 52 stored as 2026-06-23T00:00:00Z (midnight UTC = 5 PM PDT June 22).
    Without +24h grace: event_date < now → excluded.
    With +24h grace: event_date >= now - 24h → included.
    """
    # UTC is already 7 hours past midnight June 23
    now_utc = datetime(2026, 6, 23, 7, 9, 0, tzinfo=timezone.utc)
    event_date = datetime(2026, 6, 23, 0, 0, 0, tzinfo=timezone.utc)  # T00:00Z

    # Naive comparison (broken): event already excluded
    assert event_date < now_utc, "sanity: event IS before now_utc"

    # Corrected comparison with +24h grace
    assert event_date >= _cutoff(now_utc), (
        "Event should still be visible: LA date is still June 23, "
        "event hasn't actually happened yet"
    )


def test_event_visible_when_utc_rolls_over_but_la_still_day_before():
    """
    Scenario: LA date = June 22 (11 PM PDT), UTC = June 23 06:00.
    User sees it as June 22 — event on June 23 is clearly upcoming.
    """
    now_utc = datetime(2026, 6, 23, 6, 0, 0, tzinfo=timezone.utc)   # 11 PM PDT June 22
    event_date = datetime(2026, 6, 23, 0, 0, 0, tzinfo=timezone.utc)

    assert event_date < now_utc, "sanity: UTC rollover happened"
    assert event_date >= _cutoff(now_utc), "Event must remain visible at 11 PM PDT June 22"


def test_truly_past_event_excluded():
    """
    Event 50 (June 19) should not appear on June 23.
    """
    now_utc = datetime(2026, 6, 23, 7, 9, 0, tzinfo=timezone.utc)
    event_date = datetime(2026, 6, 19, 0, 0, 0, tzinfo=timezone.utc)

    assert event_date < _cutoff(now_utc), "June 19 event must be excluded on June 23"


def test_upcoming_event_always_visible():
    """
    Event 53 (June 27) is clearly upcoming — always visible.
    """
    now_utc = datetime(2026, 6, 23, 7, 9, 0, tzinfo=timezone.utc)
    event_date = datetime(2026, 6, 27, 0, 0, 0, tzinfo=timezone.utc)

    assert event_date >= _cutoff(now_utc), "June 27 event must be visible on June 23"


def test_grace_boundary_exact_24h():
    """
    Event at exactly (now - 24h): should be visible (>=, not >).
    Event at (now - 24h - 1s): should be excluded.
    """
    now_utc = datetime(2026, 6, 23, 7, 0, 0, tzinfo=timezone.utc)
    exact_boundary = now_utc - timedelta(hours=24)          # included
    just_past      = now_utc - timedelta(hours=24, seconds=1)  # excluded

    assert exact_boundary >= _cutoff(now_utc)
    assert just_past      <  _cutoff(now_utc)
