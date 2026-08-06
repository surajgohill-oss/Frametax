"""
Organization read endpoints. List-only — organization creation/management
has no product surface yet; this exists so the Project Library's "New
Project" flow can attach a project to the (currently single) real
organization instead of the frontend guessing or hardcoding an id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationRead

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(db: AsyncSession = Depends(get_db)) -> list[Organization]:
    result = await db.execute(select(Organization).order_by(Organization.name))
    return list(result.scalars().all())
