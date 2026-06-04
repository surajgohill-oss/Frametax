from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from app.database import get_db
from app.models import Listing, Marketplace

router = APIRouter(prefix="/listings", tags=["listings"])

# Phase 1E-F: LIMIT 500 removed. Cursor-paginated endpoint, max 2000 per page.
LISTING_DEFAULT_PAGE_SIZE = 500
LISTING_MAX_PAGE_SIZE = 2000


@router.get("/events/{event_id}")
async def get_listings(
    event_id: int,
    marketplace: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    after_id: Optional[int] = Query(None),
    limit: int = Query(LISTING_DEFAULT_PAGE_SIZE, ge=1, le=LISTING_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
):
    filters = [Listing.event_id == event_id]
    if active_only:
        filters.append(Listing.is_active == True)
    if section_id:
        filters.append(Listing.section_id == section_id)
    if marketplace:
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == marketplace))
        mp = mp_result.scalar_one_or_none()
        if mp:
            filters.append(Listing.marketplace_id == mp.id)
    if after_id is not None:
        filters.append(Listing.id > after_id)

    stmt = (
        select(Listing, Marketplace)
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(and_(*filters))
        .order_by(Listing.price, Listing.id)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id":                   l.id,
            "external_listing_id":  l.external_listing_id,
            "section":              l.section,
            "section_name":         l.section or "—",
            "section_id":           l.section_id,
            "row":                  l.row,
            "quantity":             l.quantity,
            "price":                float(l.price),
            "price_each":           float(l.all_in_price) if l.all_in_price else float(l.price),
            "fees":                 float(l.fees) if l.fees else None,
            "all_in_price":         float(l.all_in_price) if l.all_in_price else None,
            "listing_url":          l.listing_url,
            "marketplace_slug":     mp.slug,
            "market_segment":       l.market_segment,
            "is_active":            l.is_active,
            "first_seen_at":        l.first_seen_at.isoformat() if l.first_seen_at else None,
            "last_seen_at":         l.last_seen_at.isoformat() if l.last_seen_at else None,
            "mirror_group_id":      l.mirror_group_id if hasattr(l, "mirror_group_id") else None,
            "mirror_confidence":    l.mirror_confidence if hasattr(l, "mirror_confidence") else None,
        }
        for l, mp in rows
    ]
