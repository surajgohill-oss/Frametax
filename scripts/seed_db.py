#!/usr/bin/env python3
"""Local seed script (run outside Docker). Requires DATABASE_URL in env."""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.venue import Venue, VenueSection
from app.models.event import Marketplace
from app.database import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://concert:concert@localhost:5432/concert_tracker"
)

VENUE_MAPS_DIR = Path(__file__).parent.parent / "shared" / "venue_maps"

MARKETPLACES = [
    {"name": "StubHub", "slug": "stubhub", "base_url": "https://www.stubhub.com", "logo_url": "https://www.stubhub.com/favicon.ico"},
    {"name": "SeatGeek", "slug": "seatgeek", "base_url": "https://seatgeek.com", "logo_url": "https://seatgeek.com/favicon.ico"},
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for mp_data in MARKETPLACES:
            result = await session.execute(select(Marketplace).where(Marketplace.slug == mp_data["slug"]))
            if not result.scalar_one_or_none():
                session.add(Marketplace(**mp_data))
                print(f"Created marketplace: {mp_data['name']}")

        venue_files = sorted(VENUE_MAPS_DIR.glob("*.json"))
        if not venue_files:
            print(f"No venue map JSON files found in {VENUE_MAPS_DIR}")
        for venue_file in venue_files:
            data = json.loads(venue_file.read_text())
            result = await session.execute(select(Venue).where(Venue.slug == data["slug"]))
            venue = result.scalar_one_or_none()
            if not venue:
                venue = Venue(
                    name=data["name"],
                    slug=data["slug"],
                    city="Los Angeles",
                    state="CA",
                )
                session.add(venue)
                await session.flush()
                print(f"Created venue: {data['name']}")

                for s in data.get("sections", []):
                    section = VenueSection(
                        venue_id=venue.id,
                        name=s["name"],
                        slug=s["slug"],
                        capacity=s.get("capacity"),
                        section_type=s.get("section_type"),
                        row_count=s.get("row_count"),
                        seats_per_row=s.get("seats_per_row"),
                    )
                    session.add(section)
                print(f"  Added {len(data.get('sections', []))} sections")
            else:
                print(f"Venue already exists: {data['name']}")

        await session.commit()
    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
