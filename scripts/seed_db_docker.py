#!/usr/bin/env python3
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
    await db.commit()
    print("Seed complete.")


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with S() as db:
        await seed(db)
    await engine.dispose()


asyncio.run(main())
