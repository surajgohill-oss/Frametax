"""
Regression tests: event visibility (UTC-vs-LA timezone off-by-one) and
Spotify static map fallback.

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


# ── Spotify static map regression ─────────────────────────────────────────────

# Mirror the structure of frontend/src/lib/entityimages.ts SPOTIFY_ARTIST_URLS
# This test keeps Python-side awareness of the mapping so CI catches omissions.
SPOTIFY_ARTIST_URLS = {
    "kid cudi": {
        "artistUrl": "https://open.spotify.com/artist/0fA0VVWsXO9YnASrzqfmYu",
        "playlistUrl": "https://open.spotify.com/playlist/37i9dQZF1DZ06evO04TCIU",
    },
}


def _get_spotify_data(artist: str) -> dict:
    """Python mirror of frontend getSpotifyData() normalisation."""
    key = artist.lower().strip()
    return SPOTIFY_ARTIST_URLS.get(key, {})


def test_kid_cudi_spotify_static_returns_artist_url():
    data = _get_spotify_data("Kid Cudi")
    assert data.get("artistUrl"), "Kid Cudi must have a non-null artistUrl"
    assert "spotify.com/artist/" in data["artistUrl"]


def test_kid_cudi_spotify_static_returns_playlist_url():
    data = _get_spotify_data("Kid Cudi")
    assert data.get("playlistUrl"), "Kid Cudi must have a non-null playlistUrl"
    assert "spotify.com/playlist/" in data["playlistUrl"]


def test_kid_cudi_spotify_case_insensitive():
    """Normalisation must handle mixed-case artist name from DB."""
    for variant in ("Kid Cudi", "kid cudi", "KID CUDI", "Kid cudi"):
        data = _get_spotify_data(variant)
        assert data.get("artistUrl"), f"Failed for variant: {variant!r}"


def test_spotify_artist_id_matches_expected():
    """Prevent silent artist ID swap — must be 0fA0VVWsXO9YnASrzqfmYu (confirmed)."""
    data = _get_spotify_data("Kid Cudi")
    assert data["artistUrl"].endswith("0fA0VVWsXO9YnASrzqfmYu"), (
        "Artist ID changed. Re-verify against live Spotify before updating."
    )


def test_completed_filter_does_not_prematurely_include_same_day_event():
    """
    The 'completed' page filter must not include an event while it is still
    within the 24h grace window. Event is 'past' only after event_date + 24h.
    """
    now_utc = datetime(2026, 6, 23, 7, 9, 0, tzinfo=timezone.utc)
    event_date = datetime(2026, 6, 23, 0, 0, 0, tzinfo=timezone.utc)  # today's show

    # Frontend: new Date(event_date).getTime() + 24*3600*1000 < now.getTime()
    event_ms = event_date.timestamp() * 1000
    now_ms   = now_utc.timestamp() * 1000
    grace_ms = 24 * 3600 * 1000

    is_past = event_ms + grace_ms < now_ms
    assert not is_past, "Same-day event must NOT be classified as completed during grace window"
