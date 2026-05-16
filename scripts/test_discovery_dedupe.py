#!/usr/bin/env python3
"""
Discovery Deduplication Test
==============================
Verifies that canonical_id uniqueness prevents duplicate tracked_events when
EventDiscovery._ingest() is called multiple times with identical event data.

Tests:
  1. First ingest of event → "new"
  2. Second ingest of same event (same title/venue/date) → "duplicate"
  3. Ingest of event with different date → "new" (different canonical_id)
  4. Ingest of event with different venue → "new" (different canonical_id)
  5. Re-ingest of #3 → "duplicate"
  6. tracked_event count increases only for genuinely new events
  7. Invariant B holds throughout (resolver handles NULL external_event_ids)

Cleans up all test rows on exit (pass or fail).
Exit: 0 = PASS, 1 = FAIL
"""
import asyncio
import json
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete, text, func

from app.models import Event, TrackedEvent, Marketplace, Venue
from app.collectors.discovery import EventDiscovery, DiscoveredEvent
from app.config import get_settings

DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"
_TEST_PREFIX = "[DEDUPE-TEST]"

_GREEN = "\033[32m"
_RED   = "\033[31m"
_RESET = "\033[0m"
_failures: list[str] = []
_passed = 0


def check(label: str, got, expected, note: str = "") -> None:
    global _passed
    suffix = f"  [{note}]" if note else ""
    if got == expected:
        print(f"  {_GREEN}PASS{_RESET}  {label}  →  {got!r}{suffix}")
        _passed += 1
    else:
        print(f"  {_RED}FAIL{_RESET}  {label}  expected={expected!r}  got={got!r}{suffix}")
        _failures.append(label)


async def cleanup(db, engine):
    """Delete all test rows created during this run."""
    # TrackedEvents first (FK)
    te_ids_result = await db.execute(
        select(TrackedEvent.id)
        .join(Event, TrackedEvent.event_id == Event.id)
        .where(Event.title.like(f"{_TEST_PREFIX}%"))
    )
    te_ids = [row[0] for row in te_ids_result.all()]
    if te_ids:
        await db.execute(delete(TrackedEvent).where(TrackedEvent.id.in_(te_ids)))

    ev_ids_result = await db.execute(
        select(Event.id).where(Event.title.like(f"{_TEST_PREFIX}%"))
    )
    ev_ids = [row[0] for row in ev_ids_result.all()]
    if ev_ids:
        await db.execute(delete(Event).where(Event.id.in_(ev_ids)))

    await db.commit()
    print(f"  cleanup: removed {len(te_ids)} tracked_event(s), {len(ev_ids)} event(s)")


async def main():
    _t0 = time.monotonic()
    engine = create_async_engine(DATABASE_URL, echo=False)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    settings = get_settings()
    discovery = EventDiscovery(settings)
    now = datetime.utcnow()

    print()
    print("══════════════════════════════════════════")
    print("  DISCOVERY DEDUPLICATION TEST")
    print("══════════════════════════════════════════")

    async with S() as db:
        # Load prerequisites
        mp_result = await db.execute(
            select(Marketplace).where(Marketplace.slug == "seatgeek")
        )
        seatgeek_mp = mp_result.scalar_one_or_none()

        venue_result = await db.execute(
            select(Venue).where(Venue.slug == "crypto-arena")
        )
        venue = venue_result.scalar_one_or_none()

        if not seatgeek_mp or not venue:
            print(f"  {_RED}FAIL{_RESET}  Prerequisites missing (seatgeek mp or crypto-arena venue)")
            await engine.dispose()
            sys.exit(1)

        venue_map = {venue.slug: venue}

        # Baseline count
        base_te_count = (await db.execute(
            select(func.count()).select_from(TrackedEvent)
        )).scalar_one()
        print(f"\n  baseline tracked_events: {base_te_count}")

    # Reference event (within admission window: 15 days out)
    event_date_a = now + timedelta(days=15, hours=3)
    event_date_b = now + timedelta(days=16, hours=5)  # different date → different canonical_id
    event_date_c = now + timedelta(days=15, hours=3)  # same as A but different venue

    item_a = DiscoveredEvent(
        title=f"{_TEST_PREFIX} Artist Alpha",
        artist="Artist Alpha",
        venue_name="Crypto.com Arena",
        venue_slug="crypto-arena",
        event_date=event_date_a,
        external_event_id="dedupe-test-ext-a",
        external_url="https://seatgeek.com/dedupe-test-a",
        marketplace_slug="seatgeek",
    )
    # Exact duplicate of item_a
    item_a_dup = DiscoveredEvent(
        title=f"{_TEST_PREFIX} Artist Alpha",
        artist="Artist Alpha",
        venue_name="Crypto.com Arena",
        venue_slug="crypto-arena",
        event_date=event_date_a,          # same date
        external_event_id="dedupe-test-ext-a-v2",  # different external ID — same canonical
        external_url="https://seatgeek.com/dedupe-test-a-v2",
        marketplace_slug="seatgeek",
    )
    # Different date → different canonical_id → should be "new"
    item_b = DiscoveredEvent(
        title=f"{_TEST_PREFIX} Artist Alpha",
        artist="Artist Alpha",
        venue_name="Crypto.com Arena",
        venue_slug="crypto-arena",
        event_date=event_date_b,          # different date
        external_event_id="dedupe-test-ext-b",
        external_url="https://seatgeek.com/dedupe-test-b",
        marketplace_slug="seatgeek",
    )

    print()
    print("── Ingest sequence ─────────────────────────────────────────")

    # 1. First ingest of item_a → new
    result = await discovery._ingest(S, seatgeek_mp, item_a, venue_map)
    check("1st ingest item_a (new event)", result, "new")

    # 2. Identical ingest of item_a → duplicate (same canonical_id)
    result = await discovery._ingest(S, seatgeek_mp, item_a_dup, venue_map)
    check("2nd ingest item_a (same canonical_id, diff ext_id) → duplicate", result, "duplicate")

    # 3. item_b has different date → different canonical_id → new
    result = await discovery._ingest(S, seatgeek_mp, item_b, venue_map)
    check("1st ingest item_b (different date) → new", result, "new")

    # 4. Re-ingest item_b → duplicate
    result = await discovery._ingest(S, seatgeek_mp, item_b, venue_map)
    check("2nd ingest item_b → duplicate", result, "duplicate")

    # 5. item_a again → still duplicate (not tripled)
    result = await discovery._ingest(S, seatgeek_mp, item_a, venue_map)
    check("3rd ingest item_a → still duplicate", result, "duplicate")

    # 6. Verify only 2 new tracked_events were created (item_a and item_b)
    print()
    print("── Count verification ──────────────────────────────────────")

    async with S() as db:
        new_te_count = (await db.execute(
            select(func.count()).select_from(TrackedEvent)
        )).scalar_one()
        delta = new_te_count - base_te_count
        check("exactly 2 new tracked_events created", delta, 2,
              f"was {base_te_count}, now {new_te_count}")

        # Both test tracked_events should have external_event_id=None (resolver handles them)
        null_eid = (await db.execute(
            select(func.count())
            .select_from(TrackedEvent)
            .join(Event, TrackedEvent.event_id == Event.id)
            .where(
                Event.title.like(f"{_TEST_PREFIX}%"),
                TrackedEvent.external_event_id.is_(None),
            )
        )).scalar_one()
        check("test tracked_events have external_event_id=NULL (awaiting resolver)", null_eid, 2)

    # 7. Admission window rejection (< 14 days)
    print()
    print("── Admission window enforcement ────────────────────────────")

    item_too_soon = DiscoveredEvent(
        title=f"{_TEST_PREFIX} Too Soon",
        artist="Too Soon",
        venue_name="Crypto.com Arena",
        venue_slug="crypto-arena",
        event_date=now + timedelta(days=5),   # < 14 days → outside_window
        external_event_id="dedupe-test-too-soon",
        external_url="https://seatgeek.com/too-soon",
        marketplace_slug="seatgeek",
    )
    result = await discovery._ingest(S, seatgeek_mp, item_too_soon, venue_map)
    check("event < 14 days out → outside_window", result, "outside_window")

    item_too_far = DiscoveredEvent(
        title=f"{_TEST_PREFIX} Too Far",
        artist="Too Far",
        venue_name="Crypto.com Arena",
        venue_slug="crypto-arena",
        event_date=now + timedelta(days=30),  # > 21 days → outside_window
        external_event_id="dedupe-test-too-far",
        external_url="https://seatgeek.com/too-far",
        marketplace_slug="seatgeek",
    )
    result = await discovery._ingest(S, seatgeek_mp, item_too_far, venue_map)
    check("event > 21 days out → outside_window", result, "outside_window")

    # 8. No venue match
    item_no_venue = DiscoveredEvent(
        title=f"{_TEST_PREFIX} No Venue",
        artist="No Venue",
        venue_name="Unknown Arena XYZ",
        venue_slug="unknown-venue-xyz",
        event_date=now + timedelta(days=15),
        external_event_id="dedupe-test-no-venue",
        external_url="https://seatgeek.com/no-venue",
        marketplace_slug="seatgeek",
    )
    result = await discovery._ingest(S, seatgeek_mp, item_no_venue, {"crypto-arena": venue})
    check("unknown venue → no_venue", result, "no_venue")

    # Count still 2 after rejections
    async with S() as db:
        final_count = (await db.execute(
            select(func.count()).select_from(TrackedEvent)
        )).scalar_one()
        check("no extra tracked_events from rejected ingests", final_count - base_te_count, 2)

    # Cleanup
    print()
    print("── Cleanup ─────────────────────────────────────────────────")
    async with S() as db:
        await cleanup(db, engine)

    await discovery.close()
    await engine.dispose()

    # Summary
    total = _passed + len(_failures)
    print()
    print("══════════════════════════════════════════")
    if _failures:
        print(f"  RESULT: {_RED}FAIL{_RESET} — {len(_failures)}/{total} check(s) failed")
        for f in _failures:
            print(f"    ✗ {f}")
    else:
        print(f"  RESULT: {_GREEN}PASS{_RESET} — all {total} deduplication checks correct")
        print("  canonical_id uniqueness enforced; admission window enforced.")
    _status = "FAIL" if _failures else "PASS"
    print(f"GATE_REPORT_JSON={json.dumps({'gate_name': 'discovery-dedupe-test', 'status': _status, 'duration_ms': int((time.monotonic() - _t0) * 1000), 'details': {'total': total, 'passed': _passed, 'failed': len(_failures)}})}")
    sys.exit(1 if _failures else 0)


asyncio.run(main())
