"""
Budget import and line-item endpoints under /projects/{project_id}/budgets.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.project import Project
from app.schemas.budget import BudgetDocumentRead, BudgetLineItemRead

router = APIRouter(prefix="/projects/{project_id}/budgets", tags=["budgets"])


@router.post("/import", response_model=BudgetDocumentRead, status_code=201)
async def import_budget(
    project_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> BudgetDocument:
    """
    Trigger CSV/XLSX budget parsing for a previously uploaded document.
    Parses line items and runs deterministic classification.
    """
    from pathlib import Path
    from app.core.config import get_settings
    from app.ingestion.budget_parser import classify_parsed_items, parse_budget_csv
    from app.models.enums import ATLBTLCategory, CompensationType, SpendCategory

    # Verify project exists
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch budget document
    doc_result = await db.execute(
        select(BudgetDocument).where(
            BudgetDocument.id == document_id,
            BudgetDocument.project_id == project_id,
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Budget document not found for this project")

    settings = get_settings()
    local_path = Path(settings.LOCAL_STORAGE_PATH) / (doc.storage_path or "")

    if not local_path.exists():
        raise HTTPException(status_code=422, detail="Stored file not found on disk")

    suffix = local_path.suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=422,
            detail="Only CSV and XLSX files can be imported as structured budgets",
        )

    # Parse and classify
    raw_content = local_path.read_bytes()
    parse_result = parse_budget_csv(raw_content, filename=doc.filename, currency_code=doc.currency_code)
    classified = classify_parsed_items(parse_result)

    doc.total_budget_raw = classified.total_budget_raw
    doc.extraction_status = "imported"

    # Persist line items
    for item in classified.line_items:
        li = BudgetLineItem(
            id=uuid.uuid4(),
            budget_document_id=doc.id,
            description=item.description,
            department=item.department,
            amount_raw=item.amount_usd,
            amount_normalized=item.amount_usd,
            currency_code=item.currency_code,
            amount_usd=item.amount_usd,
            cash_amount_usd=item.amount_usd,
            source_row=item.source_row,
            atl_btl=getattr(item, "atl_btl", ATLBTLCategory.BTL.value),
            spend_category=getattr(item, "spend_category", None),
            is_labor=getattr(item, "is_labor", False),
            is_fixed=getattr(item, "is_fixed", False),
            compensation_type=getattr(item, "compensation_type", CompensationType.CASH.value),
            extraction_confidence=item.extraction_confidence,
        )
        db.add(li)

    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{document_id}/line-items", response_model=list[BudgetLineItemRead])
async def list_line_items(
    project_id: str,
    document_id: str,
    atl_btl: str | None = Query(None, description="ATL | BTL | POST | OTHER"),
    db: AsyncSession = Depends(get_db),
) -> list[BudgetLineItem]:
    stmt = select(BudgetLineItem).where(BudgetLineItem.budget_document_id == document_id)
    if atl_btl:
        stmt = stmt.where(BudgetLineItem.atl_btl == atl_btl.upper())
    result = await db.execute(stmt)
    return list(result.scalars().all())
