#!/usr/bin/env python3
"""Docker-internal version of seed_db.py."""
import asyncio, json, sys
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models import Venue, VenueSection, Marketplace
from app.database import Base

VENUE_MAP_DIR = Path("/shared/venue_maps")
DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"


async def seed(db):
    for mp in [
        {"slug": "stubhub", "name": "StubHub", "base_url": "https://www.stubhub.com", "is_active": True},
        {"slug": "seatgeek", "name": "SeatGeek", "base_url": "https://seatgeek.com", "is_active": True},
        {"slug": "tickpick", "name": "TickPick", "base_url": "https://www.tickpick.com", "is_active": False},
        {"slug": "gametime", "name": "Gametime", "base_url": "https://gametime.co", "is_active": False},
    ]:
        ex = await db.execute(select(Marketplace).where(Marketplace.slug == mp["slug"]))
        if not ex.scalar_one_or_none():
            db.add(Marketplace(**mp))
    await db.flush()
    for map_file in sorted(VENUE_MAP_DIR.glob("*.json")):
        data = json.loads(map_file.read_text())
        ex = await db.execute(select(Venue).where(Venue.slug == data["slug"]))
        venue = ex.scalar_one_or_none()
        if not venue:
            venue = Venue(slug=data["slug"], name=data["name"], map_width=data["map_width"], map_height=data["map_height"])
            db.add(venue)
            await db.flush()
        for sec in data["sections"]:
            ex2 = await db.execute(select(VenueSection).where(VenueSection.venue_id == venue.id, VenueSection.section_id == sec["section_id"]))
            if not ex2.scalar_one_or_none():
                db.add(VenueSection(venue_id=venue.id, section_id=sec["section_id"], display_name=sec["display_name"], tier=sec["tier"], quality_score=sec["quality_score"], x=sec["x"], y=sec["y"], width=sec.get("width", 40), height=sec.get("height", 30), shape=sec.get("shape", "rect"), shape_data=sec.get("shape_data"), stubhub_aliases=sec.get("stubhub_aliases"), seatgeek_aliases=sec.get("seatgeek_aliases")))
    await db.commit()


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with S() as db:
        await seed(db)
    await engine.dispose()


asyncio.run(main())
