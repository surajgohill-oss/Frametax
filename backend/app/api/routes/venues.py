from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Venue

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("/")
async def list_venues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).order_by(Venue.name))
    return [_serialize(v) for v in result.scalars().all()]


@router.get("/{slug}/sections")
async def get_venue_sections(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).where(Venue.slug == slug))
    v = result.scalar_one_or_none()
    if not v: raise HTTPException(404, "Venue not found")
    return _serialize(v)["sections"]


@router.get("/{slug}")
async def get_venue(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).where(Venue.slug == slug))
    v = result.scalar_one_or_none()
    if not v: raise HTTPException(404, "Venue not found")
    return _serialize(v)


def _serialize(v: Venue) -> dict:
    return {
        "id": v.id, "slug": v.slug, "name": v.name, "city": v.city, "state": v.state,
        "capacity": v.capacity, "map_width": v.map_width, "map_height": v.map_height,
        "sections": [
            {
                "id": s.id, "venue_id": s.venue_id, "section_id": s.section_id,
                "display_name": s.display_name, "tier": s.tier, "quality_score": s.quality_score,
                "x": s.x, "y": s.y, "width": s.width, "height": s.height, "shape": s.shape,
                "stubhub_aliases": s.stubhub_aliases, "seatgeek_aliases": s.seatgeek_aliases,
            } for s in v.sections
        ],
    }
