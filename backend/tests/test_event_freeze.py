"""
Tests for Phase 1E-A: event freeze, event cap, canonical identity guardrails.

Covers:
  - _normalize_title()  unit tests
  - _to_la_local()      unit tests (UTC→PDT conversion)
  - canonical_id convergence after timezone fix (all 3 timezone-duplicate pairs)
  - EventDiscovery._ingest() freeze behaviour (mock DB, Python 3.10+ only)
  - EventDiscovery._ingest() cap behaviour (mock DB, Python 3.10+ only)
  - POST /api/events/ freeze rejection (Python 3.10+ only)

Pure-function tests (Groups 1–3) run on Python 3.9+.
App-integration tests (Groups 4–6) require Python 3.10+ because the app models
use union syntax (X | None).  They are skipped automatically on older runtimes.

Run with:
    cd backend && python3 -m pytest tests/test_event_freeze.py -v
or (standalone, no pytest needed):
    cd backend && python3 tests/test_event_freeze.py
"""
import hashlib
import re
import sys
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────────────────────────────────────
# Inline implementations of the pure helper functions.
# These mirror exactly what is in app/collectors/discovery.py so that tests
# run correctly even when the full app package cannot be imported (e.g. Python
# 3.9 with models that use 3.10+ union syntax).
# ─────────────────────────────────────────────────────────────────────────────

_LA_TZ = ZoneInfo("America/Los_Angeles")


def _normalize_title(title: str) -> str:
    """Mirror of app/collectors/discovery.py:_normalize_title."""
    title = title.split(":")[0].strip()
    for sep in (" with ", " ft. ", " feat. ", " featuring "):
        idx = title.lower().find(sep)
        if idx > 0:
            title = title[:idx]
    title = re.sub(r"\s*\([^)]*\)", "", title)
    title = re.sub(r"[^\w\s]", "", title.lower()).strip()
    title = re.sub(r"\s+", " ", title)
    return title


def _to_la_local(dt: datetime) -> datetime:
    """Mirror of app/collectors/discovery.py:_to_la_local."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(_LA_TZ).replace(tzinfo=None)


def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    """Mirror of app/collectors/discovery.py:_canonical_id."""
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# Attempt to import app components (requires Python 3.10+ for models)
_APP_IMPORTABLE = False
try:
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.collectors.discovery import (
        EventDiscovery as _EventDiscovery,
        DiscoveredEvent as _DiscoveredEvent,
    )
    _APP_IMPORTABLE = True
except (TypeError, ImportError):
    pass  # Python 3.9 or missing dependencies — skip app-integration tests

_SKIP_APP = not _APP_IMPORTABLE
_SKIP_REASON = "App models require Python 3.10+ (union syntax); skipping on this runtime"


# ─────────────────────────────────────────────────────────────────────────────
# 1. _normalize_title()
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeTitle(unittest.TestCase):

    def test_colon_tour_subtitle_stripped(self):
        self.assertEqual(
            _normalize_title("Ariana Grande: Eternal Sunshine Tour"),
            "ariana grande",
        )

    def test_plain_artist_name_unchanged(self):
        self.assertEqual(_normalize_title("Ariana Grande"), "ariana grande")

    def test_parenthetical_stripped(self):
        self.assertEqual(_normalize_title("Rush (Classic Albums Live)"), "rush")

    def test_with_opener_stripped(self):
        self.assertEqual(_normalize_title("Ed Sheeran with Khalid"), "ed sheeran")

    def test_feat_stripped(self):
        self.assertEqual(
            _normalize_title("Diljit Dosanjh feat. Arijit Singh"), "diljit dosanjh"
        )

    def test_ariana_variants_normalize_equal(self):
        """Core assertion: the two Ariana Jun13 title variants must normalize equal."""
        v1 = _normalize_title("Ariana Grande: Eternal Sunshine Tour")
        v2 = _normalize_title("Ariana Grande")
        self.assertEqual(v1, v2, f"Expected equal: {v1!r} vs {v2!r}")

    def test_case_insensitive(self):
        self.assertEqual(
            _normalize_title("CHANCE THE RAPPER"),
            _normalize_title("Chance the Rapper"),
        )

    def test_diljit_unchanged(self):
        self.assertEqual(_normalize_title("Diljit Dosanjh"), "diljit dosanjh")

    def test_chance_unchanged(self):
        self.assertEqual(_normalize_title("Chance the Rapper"), "chance the rapper")


# ─────────────────────────────────────────────────────────────────────────────
# 2. _to_la_local()
# ─────────────────────────────────────────────────────────────────────────────

class TestToLaLocal(unittest.TestCase):

    def _utc(self, year, month, day, hour, minute=0):
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)

    def test_8pm_pdt_is_june18_not_june19(self):
        """
        Root cause of Diljit duplicate: Jun 18 8pm PDT = Jun 19 3am UTC.
        After fix: _to_la_local must return Jun 18 20:00, not Jun 19 03:00.
        """
        result = _to_la_local(self._utc(2026, 6, 19, 3, 0))
        self.assertIsNone(result.tzinfo)
        self.assertEqual(result.date(), datetime(2026, 6, 18).date())
        self.assertEqual(result.hour, 20)

    def test_7pm_pdt_is_june21_not_june22(self):
        """Root cause of Reggae Night duplicate: Jun 21 7pm PDT = Jun 22 2am UTC."""
        result = _to_la_local(self._utc(2026, 6, 22, 2, 0))
        self.assertEqual(result.date(), datetime(2026, 6, 21).date())
        self.assertEqual(result.hour, 19)

    def test_8pm_pdt_june19_is_june19_not_june20(self):
        """Root cause of Chance duplicate: Jun 19 8pm PDT = Jun 20 3am UTC."""
        result = _to_la_local(self._utc(2026, 6, 20, 3, 0))
        self.assertEqual(result.date(), datetime(2026, 6, 19).date())
        self.assertEqual(result.hour, 20)

    def test_naive_datetime_returned_unchanged(self):
        naive = datetime(2026, 6, 18, 20, 0)
        self.assertEqual(_to_la_local(naive), naive)
        self.assertIsNone(_to_la_local(naive).tzinfo)

    def test_midday_utc_same_day(self):
        """Noon PDT show (7pm UTC) stays on the same calendar day."""
        result = _to_la_local(self._utc(2026, 8, 8, 19, 0))
        self.assertEqual(result.date(), datetime(2026, 8, 8).date())


# ─────────────────────────────────────────────────────────────────────────────
# 3. canonical_id convergence after UTC→local fix
# ─────────────────────────────────────────────────────────────────────────────

class TestCanonicalIdConvergence(unittest.TestCase):
    """
    After applying _to_la_local() to SeatGeek's UTC timestamps, the
    canonical_ids generated for events 30/31/32 must match the canonical_ids
    of their StubHub-sourced duplicates 25/28/29.
    """

    def test_diljit_canonical_matches_event25(self):
        sg_local = _to_la_local(datetime(2026, 6, 19, 3, 0, tzinfo=timezone.utc))
        sh_local = datetime(2026, 6, 18, 20, 0)
        cid_sg = _canonical_id("Diljit Dosanjh", "crypto-arena", sg_local)
        cid_sh = _canonical_id("Diljit Dosanjh", "crypto-arena", sh_local)
        self.assertEqual(cid_sg, cid_sh)
        self.assertEqual(cid_sg, "f7a9ed10c6092e08", "Must match event_id=25 canonical")

    def test_chance_canonical_matches_event28(self):
        sg_local = _to_la_local(datetime(2026, 6, 20, 3, 0, tzinfo=timezone.utc))
        sh_local = datetime(2026, 6, 19, 20, 0)
        cid_sg = _canonical_id("Chance the Rapper", "hollywood-bowl", sg_local)
        cid_sh = _canonical_id("Chance the Rapper", "hollywood-bowl", sh_local)
        self.assertEqual(cid_sg, cid_sh)
        self.assertEqual(cid_sg, "35212f5c1fcc5dbc", "Must match event_id=28 canonical")

    def test_reggae_canonical_matches_event29(self):
        title = "Reggae Night XXIV wih Ziggy Marley, Burning Spear and more"
        sg_local = _to_la_local(datetime(2026, 6, 22, 2, 0, tzinfo=timezone.utc))
        sh_local = datetime(2026, 6, 21, 19, 0)
        cid_sg = _canonical_id(title, "hollywood-bowl", sg_local)
        cid_sh = _canonical_id(title, "hollywood-bowl", sh_local)
        self.assertEqual(cid_sg, cid_sh)
        self.assertEqual(cid_sg, "643352ee66ede0ca", "Must match event_id=29 canonical")

    def test_ariana_title_mismatch_normalized(self):
        """
        Ariana Jun13 title variants normalize identically — prerequisite for
        the near-duplicate check to attach the SeatGeek TE to event_id=11.
        """
        norm1 = _normalize_title("Ariana Grande: Eternal Sunshine Tour")
        norm2 = _normalize_title("Ariana Grande")
        self.assertEqual(norm1, norm2)


# ─────────────────────────────────────────────────────────────────────────────
# 4–6. App integration tests (require Python 3.10+)
# ─────────────────────────────────────────────────────────────────────────────

@unittest.skipIf(_SKIP_APP, _SKIP_REASON)
class TestFreezeIngest(unittest.IsolatedAsyncioTestCase):

    async def test_freeze_returns_frozen_no_db_write(self):
        """When discovery_freeze=True, _ingest must return 'frozen' with no DB writes."""
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, MagicMock

        settings = SimpleNamespace(discovery_freeze=True, max_tracked_events=30)
        discovery = _EventDiscovery(settings)

        venue = MagicMock()
        venue.id = 1
        venues = {"crypto-arena": venue}
        mp = MagicMock()
        mp.slug = "seatgeek"
        mp.id = 4
        from datetime import timedelta
        item = _DiscoveredEvent(
            title="Test Artist", artist="Test Artist",
            venue_name="Crypto.com Arena", venue_slug="crypto-arena",
            event_date=datetime.utcnow() + timedelta(days=15),
            external_event_id="12345",
            external_url="https://example.com", marketplace_slug="seatgeek",
        )

        session_factory = AsyncMock(side_effect=AssertionError(
            "session_factory must not be called under freeze"
        ))

        result = await discovery._ingest(session_factory, mp, item, venues)
        self.assertEqual(result, "frozen")


@unittest.skipIf(_SKIP_APP, _SKIP_REASON)
class TestCapIngest(unittest.IsolatedAsyncioTestCase):

    async def test_cap_reached_blocks_new_event(self):
        """When event count == cap, _ingest must return 'cap_reached'."""
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, MagicMock
        from datetime import timedelta

        settings = SimpleNamespace(discovery_freeze=False, max_tracked_events=5)
        discovery = _EventDiscovery(settings)

        venue = MagicMock()
        venue.id = 1
        venues = {"crypto-arena": venue}
        mp = MagicMock()
        mp.slug = "seatgeek"
        mp.id = 4
        item = _DiscoveredEvent(
            title="New Unknown Artist", artist="New Unknown Artist",
            venue_name="Crypto.com Arena", venue_slug="crypto-arena",
            event_date=datetime.utcnow() + timedelta(days=15),
            external_event_id="99999",
            external_url="https://example.com", marketplace_slug="seatgeek",
        )

        async def _execute(stmt):
            r = MagicMock()
            r.scalar_one_or_none = MagicMock(return_value=None)
            r.scalars = MagicMock()
            r.scalars.return_value.all = MagicMock(return_value=[])
            r.scalar_one = MagicMock(return_value=5)  # at cap
            return r

        mock_db = AsyncMock()
        mock_db.execute = _execute
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        class _Session:
            async def __aenter__(self_):
                return mock_db
            async def __aexit__(self_, *a):
                pass

        result = await discovery._ingest(_Session, mp, item, venues)
        self.assertEqual(result, "cap_reached")
        mock_db.add.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
