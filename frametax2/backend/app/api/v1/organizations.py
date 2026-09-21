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
from app.core.config import settings
from app.models.organization import Organization
from app.schemas.organization import OrganizationRead

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(db: AsyncSession = Depends(get_db)) -> list[Organization]:
    result = await db.execute(select(Organization).order_by(Organization.name))
    return list(result.scalars().all())


@router.get("/current", response_model=OrganizationRead | None)
async def get_current_organization(db: AsyncSession = Depends(get_db)) -> Organization | None:
    """PROJECT_UI_DATA_INTEGRITY (2026-09-21): the one organization this
    deployment is scoped to today -- resolved from settings.
    CURRENT_ORGANIZATION_ID (an explicit configuration choice), never
    guessed as list_organizations()[0] and never inferred from a name
    pattern. Fails closed: unset/unresolvable configuration returns null,
    never an arbitrary organization. The Project Library (and any other
    organization-scoped read) must call this rather than list every
    organization and pick one client-side."""
    if not settings.CURRENT_ORGANIZATION_ID:
        return None
    result = await db.execute(select(Organization).where(Organization.id == settings.CURRENT_ORGANIZATION_ID))
    return result.scalar_one_or_none()
