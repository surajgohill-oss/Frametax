"""
GET /incentive-programs — list and filter incentive programs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.incentive import IncentiveProgram
from app.schemas.incentive import IncentiveProgramRead

router = APIRouter(prefix="/incentive-programs", tags=["incentive-programs"])


@router.get("", response_model=list[IncentiveProgramRead])
async def list_incentive_programs(
    jurisdiction_id: str | None = Query(None),
    confidence_tier: str | None = Query(None, description="VERIFIED | PARSED | DISCOVERY"),
    program_type: str | None = Query(None, description="tax_credit | rebate | grant | loan"),
    db: AsyncSession = Depends(get_db),
) -> list[IncentiveProgram]:
    stmt = select(IncentiveProgram)
    if jurisdiction_id:
        stmt = stmt.where(IncentiveProgram.jurisdiction_id == jurisdiction_id)
    if confidence_tier:
        stmt = stmt.where(IncentiveProgram.confidence_tier == confidence_tier.upper())
    if program_type:
        stmt = stmt.where(IncentiveProgram.program_type == program_type)
    stmt = stmt.order_by(IncentiveProgram.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{program_id}", response_model=IncentiveProgramRead)
async def get_incentive_program(
    program_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncentiveProgram:
    result = await db.execute(
        select(IncentiveProgram).where(IncentiveProgram.id == program_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Incentive program not found")
    return row
