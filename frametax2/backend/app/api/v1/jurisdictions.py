"""
GET /jurisdictions — list and filter jurisdictions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.jurisdiction import Jurisdiction
from app.schemas.jurisdiction import JurisdictionRead

router = APIRouter(prefix="/jurisdictions", tags=["jurisdictions"])


@router.get("", response_model=list[JurisdictionRead])
async def list_jurisdictions(
    country_code: str | None = Query(None, description="Filter by ISO country code (e.g. US, CA, GB)"),
    level: str | None = Query(None, description="Filter by level: country, state, province"),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> list[Jurisdiction]:
    stmt = select(Jurisdiction).where(Jurisdiction.is_active == is_active)
    if country_code:
        stmt = stmt.where(Jurisdiction.country_code == country_code.upper())
    if level:
        stmt = stmt.where(Jurisdiction.level == level)
    stmt = stmt.order_by(Jurisdiction.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{jurisdiction_id}", response_model=JurisdictionRead)
async def get_jurisdiction(
    jurisdiction_id: str,
    db: AsyncSession = Depends(get_db),
) -> Jurisdiction:
    from fastapi import HTTPException
    result = await db.execute(
        select(Jurisdiction).where(Jurisdiction.id == jurisdiction_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return row
