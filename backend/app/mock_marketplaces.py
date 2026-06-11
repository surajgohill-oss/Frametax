"""
Mock marketplace data generator.
Active when Settings.env_mode != "prod".
Deterministic per event_id — stable across restarts.
Production collection path is never touched.
"""
import random
from decimal import Decimal
from datetime import datetime

_MARKETPLACES = ["seatgeek", "stubhub", "tickpick", "gametime", "vividseats", "ticketmaster"]

_SECTIONS = [
    "Floor", "Section 101", "Section 102", "Section 103",
    "Lower Box", "Club Level", "GA Pit", "Orchestra", "Mezzanine",
]
_ROWS = ["A", "B", "C", "D", "E", "F", "G", None]
_QTYS = [1, 2, 2, 4, 4, 6]


def generate_mock_listings(event_id: int) -> dict:
    """Return per-marketplace summary (counts + min prices). No DB touch."""
    rng = random.Random(event_id * 99991)
    result = {}
    for marketplace in _MARKETPLACES:
        count = rng.randint(5, 120)
        base_price = rng.randint(60, 250)
        min_price = max(20, base_price - rng.randint(5, 40))
        if marketplace in ("gametime", "vividseats", "ticketmaster") and event_id % 2 == 0:
            count = rng.randint(0, 10)
        result[marketplace] = {
            "total": count,
            "real": count,
            "demo": 0,
            "min_price": float(min_price) if count > 0 else None,
        }
    return result


async def write_mock_listings(event_id: int, session_factory) -> None:
    """
    Write deterministic mock Listing rows to DB. Idempotent.
    Also ensures a TrackedEvent exists per marketplace so _enrich_event
    can join through tracked_events and surface all marketplace prices.
    """
    from sqlalchemy import select, delete
    from app.models import Listing, Marketplace, TrackedEvent

    meta = generate_mock_listings(event_id)
    now = datetime.utcnow()

    async with session_factory() as db:
        mp_rows = (await db.execute(select(Marketplace))).scalars().all()
        mp_by_slug = {mp.slug: mp for mp in mp_rows}

        for slug, data in meta.items():
            mp = mp_by_slug.get(slug)
            if not mp:
                continue

            # Ensure TrackedEvent exists so _enrich_event can join to it
            te = (await db.execute(
                select(TrackedEvent).where(
                    TrackedEvent.event_id == event_id,
                    TrackedEvent.marketplace_id == mp.id,
                )
            )).scalar_one_or_none()
            if not te:
                db.add(TrackedEvent(
                    event_id=event_id,
                    marketplace_id=mp.id,
                    external_event_id=f"mock-{slug[:2]}-{event_id}",
                    is_active=True,
                    poll_interval_minutes=60,
                ))
            elif te.external_event_id is None or str(te.external_event_id).startswith("demo-"):
                te.external_event_id = f"mock-{slug[:2]}-{event_id}"

            count = data["total"]
            if count == 0:
                continue

            # Idempotent: remove stale mock listings before re-writing
            await db.execute(
                delete(Listing).where(
                    Listing.event_id == event_id,
                    Listing.marketplace_id == mp.id,
                    Listing.external_listing_id.like("mock-%"),
                )
            )

            # Deterministic listings — stable seed per (event_id, slug)
            rng = random.Random(event_id * 99991 + sum(ord(c) for c in slug))
            min_price = data["min_price"] or 50

            for i in range(count):
                price = min_price + rng.randint(0, max(1, int(min_price)))
                section = rng.choice(_SECTIONS)
                db.add(Listing(
                    event_id=event_id,
                    marketplace_id=mp.id,
                    external_listing_id=f"mock-{slug[:2]}-{event_id}-{i:04d}",
                    section=section,
                    section_id=section,
                    row=rng.choice(_ROWS),
                    quantity=rng.choice(_QTYS),
                    price=Decimal(str(int(price))),
                    is_active=True,
                    first_seen_at=now,
                    last_seen_at=now,
                    extra={},
                ))

        await db.commit()
