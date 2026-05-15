#!/usr/bin/env python3
"""Idempotent seed — runs on every backend startup. Safe to re-run."""
import asyncio, hashlib, json, sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models import Venue, VenueSection, Marketplace, Event, TrackedEvent, Listing

VENUE_MAP_DIR = Path("/shared/venue_maps")
DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"


def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def seed_marketplaces(db):
    for mp in [
        {"slug": "stubhub",  "name": "StubHub",  "base_url": "https://www.stubhub.com",  "is_active": True},
        {"slug": "seatgeek", "name": "SeatGeek", "base_url": "https://seatgeek.com",      "is_active": True},
        {"slug": "tickpick", "name": "TickPick", "base_url": "https://www.tickpick.com",  "is_active": False},
        {"slug": "gametime", "name": "Gametime", "base_url": "https://gametime.co",       "is_active": False},
    ]:
        ex = await db.execute(select(Marketplace).where(Marketplace.slug == mp["slug"]))
        if not ex.scalar_one_or_none():
            db.add(Marketplace(**mp))
    await db.flush()


async def seed_venues(db):
    for i, map_file in enumerate(sorted(VENUE_MAP_DIR.glob("*.json"))):
        data = json.loads(map_file.read_text())
        ex = await db.execute(select(Venue).where(Venue.slug == data["slug"]))
        venue = ex.scalar_one_or_none()
        if not venue:
            venue = Venue(
                slug=data["slug"],
                name=data["name"],
                map_width=data.get("map_width", 700),
                map_height=data.get("map_height", 500),
            )
            db.add(venue)
            await db.flush()
        for j, sec in enumerate(data.get("sections", [])):
            sid = sec.get("section_id") or sec.get("slug") or f"sec-{i}-{j}"
            ex2 = await db.execute(
                select(VenueSection).where(
                    VenueSection.venue_id == venue.id,
                    VenueSection.section_id == sid,
                )
            )
            if not ex2.scalar_one_or_none():
                db.add(VenueSection(
                    venue_id=venue.id,
                    section_id=sid,
                    display_name=sec.get("display_name") or sec.get("name") or sid,
                    tier=sec.get("tier") or sec.get("section_type") or "general",
                    quality_score=sec.get("quality_score", 50),
                    x=float(sec.get("x", 0)),
                    y=float(sec.get("y", 0)),
                    width=float(sec.get("width", 40)),
                    height=float(sec.get("height", 30)),
                    shape=sec.get("shape", "rect"),
                    shape_data=sec.get("shape_data"),
                    stubhub_aliases=sec.get("stubhub_aliases"),
                    seatgeek_aliases=sec.get("seatgeek_aliases"),
                ))
    await db.flush()


async def seed_demo_events(db):
    """3 realistic demo events so the dashboard is populated on first boot."""
    now = datetime.utcnow()

    DEMO_EVENTS = [
        {
            "title": "Kendrick Lamar",
            "artist": "Kendrick Lamar",
            "venue_slug": "crypto-arena",
            "event_date": now + timedelta(days=45),
            "stubhub_url": "https://www.stubhub.com/kendrick-lamar-los-angeles-tickets",
            "seatgeek_url": "https://seatgeek.com/kendrick-lamar-tickets",
            "stubhub_event_id": "demo-sh-kendrick",
            "seatgeek_event_id": "demo-sg-kendrick",
            "listings": [
                {"section": "Floor GA",    "row": "GA", "qty": 2, "price": 285.00},
                {"section": "Floor GA",    "row": "GA", "qty": 4, "price": 310.00},
                {"section": "Section 101", "row": "A",  "qty": 2, "price": 195.00},
                {"section": "Section 101", "row": "C",  "qty": 2, "price": 175.00},
                {"section": "Section 102", "row": "B",  "qty": 4, "price": 165.00},
                {"section": "Section 215", "row": "D",  "qty": 2, "price": 95.00},
                {"section": "Section 215", "row": "F",  "qty": 6, "price": 88.00},
                {"section": "Section 320", "row": "G",  "qty": 4, "price": 55.00},
            ],
        },
        {
            "title": "Taylor Swift | The Eras Tour",
            "artist": "Taylor Swift",
            "venue_slug": "sofi-stadium",
            "event_date": now + timedelta(days=72),
            "stubhub_url": "https://www.stubhub.com/taylor-swift-inglewood-tickets",
            "seatgeek_url": "https://seatgeek.com/taylor-swift-tickets",
            "stubhub_event_id": "demo-sh-taylorswift",
            "seatgeek_event_id": "demo-sg-taylorswift",
            "listings": [
                {"section": "Field A",     "row": "1",  "qty": 2, "price": 750.00},
                {"section": "Field B",     "row": "3",  "qty": 2, "price": 620.00},
                {"section": "Section 121", "row": "A",  "qty": 2, "price": 420.00},
                {"section": "Section 121", "row": "E",  "qty": 4, "price": 380.00},
                {"section": "Section 235", "row": "C",  "qty": 2, "price": 210.00},
                {"section": "Section 235", "row": "J",  "qty": 6, "price": 185.00},
                {"section": "Section 510", "row": "M",  "qty": 4, "price": 115.00},
                {"section": "Section 510", "row": "P",  "qty": 4, "price": 98.00},
                {"section": "Section 510", "row": "S",  "qty": 2, "price": 89.00},
            ],
        },
        {
            "title": "Dave Matthews Band",
            "artist": "Dave Matthews Band",
            "venue_slug": "hollywood-bowl",
            "event_date": now + timedelta(days=28),
            "stubhub_url": "https://www.stubhub.com/dave-matthews-band-hollywood-tickets",
            "seatgeek_url": "https://seatgeek.com/dave-matthews-band-tickets",
            "stubhub_event_id": "demo-sh-davematthews",
            "seatgeek_event_id": "demo-sg-davematthews",
            "listings": [
                {"section": "Box 1",       "row": "1",  "qty": 2, "price": 320.00},
                {"section": "Box 5",       "row": "2",  "qty": 2, "price": 295.00},
                {"section": "Section D1",  "row": "A",  "qty": 4, "price": 145.00},
                {"section": "Section D2",  "row": "C",  "qty": 2, "price": 130.00},
                {"section": "Section J1",  "row": "G",  "qty": 4, "price": 75.00},
                {"section": "Section J2",  "row": "H",  "qty": 6, "price": 68.00},
            ],
        },
    ]

    stub_r = await db.execute(select(Marketplace).where(Marketplace.slug == "stubhub"))
    stub_mp = stub_r.scalar_one_or_none()
    sg_r = await db.execute(select(Marketplace).where(Marketplace.slug == "seatgeek"))
    sg_mp = sg_r.scalar_one_or_none()

    created_count = 0
    skipped_venues = []
    for demo in DEMO_EVENTS:
        venue_r = await db.execute(select(Venue).where(Venue.slug == demo["venue_slug"]))
        venue = venue_r.scalar_one_or_none()
        if not venue:
            print(f"  skip event (venue missing): {demo['venue_slug']}")
            skipped_venues.append(demo["venue_slug"])
            continue

        canonical = _canonical_id(demo["title"], demo["venue_slug"], demo["event_date"])
        ev_r = await db.execute(select(Event).where(Event.canonical_id == canonical))
        event = ev_r.scalar_one_or_none()
        if not event:
            event = Event(
                canonical_id=canonical,
                title=demo["title"],
                artist=demo["artist"],
                venue_id=venue.id,
                event_date=demo["event_date"],
            )
            db.add(event)
            await db.flush()
            created_count += 1
            print(f"  created: {demo['title']}")
        else:
            created_count += 1
            print(f"  exists:  {demo['title']}")

        # TrackedEvents for both marketplaces
        mp_pairs = [
            (stub_mp, "stubhub_url", "stubhub_event_id"),
            (sg_mp,   "seatgeek_url", "seatgeek_event_id"),
        ]
        for mp, url_key, eid_key in mp_pairs:
            if not mp:
                continue
            demo_eid = demo.get(eid_key)
            te_r = await db.execute(
                select(TrackedEvent).where(
                    TrackedEvent.event_id == event.id,
                    TrackedEvent.marketplace_id == mp.id,
                )
            )
            te = te_r.scalar_one_or_none()
            if not te:
                db.add(TrackedEvent(
                    event_id=event.id,
                    marketplace_id=mp.id,
                    external_url=demo[url_key],
                    external_event_id=demo_eid,
                    is_active=True,
                    poll_interval_minutes=60,
                    next_poll_at=datetime.utcnow() + timedelta(hours=1),
                ))
            elif te.external_event_id is None and demo_eid:
                # Backfill missing IDs on existing rows (e.g. after a reset-less redeploy)
                te.external_event_id = demo_eid

        # Demo listings (stubhub) so dashboard stat cards show real numbers
        if stub_mp:
            existing_r = await db.execute(
                select(Listing).where(
                    Listing.event_id == event.id,
                    Listing.marketplace_id == stub_mp.id,
                )
            )
            if not existing_r.scalars().first():
                for idx, l in enumerate(demo["listings"]):
                    price = Decimal(str(l["price"]))
                    db.add(Listing(
                        event_id=event.id,
                        marketplace_id=stub_mp.id,
                        external_listing_id=f"demo-{canonical}-{idx}",
                        section=l["section"],
                        section_id=None,
                        row=l["row"],
                        quantity=l["qty"],
                        price=price,
                        fees=round(price * Decimal("0.27"), 2),
                        all_in_price=round(price * Decimal("1.27"), 2),
                        is_active=True,
                    ))

    await db.flush()
    if created_count == 0:
        raise RuntimeError(
            f"SEED FAILURE: All {len(DEMO_EVENTS)} demo events were skipped — "
            f"venues not found: {skipped_venues}. "
            "Check that venue JSON files exist in /shared/venue_maps and slugs match."
        )
    print(f"  seed_demo_events: {created_count}/{len(DEMO_EVENTS)} events processed")
    return created_count


async def main():
    # Alembic owns schema — do NOT call create_all here.
    # create_all would duplicate indexes: ORM-named on top of migration-named.
    engine = create_async_engine(DATABASE_URL, echo=False)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with S() as db:
        await seed_marketplaces(db)
        await seed_venues(db)
        await seed_demo_events(db)
        await db.commit()
    await engine.dispose()
    print("Seed complete.")


asyncio.run(main())
