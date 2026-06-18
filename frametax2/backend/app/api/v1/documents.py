"""
Budget document upload and extraction endpoints.
POST /documents/upload  — upload a budget CSV/XLSX/PDF
GET  /documents/{id}    — get document metadata
POST /documents/{id}/extract-text — run text extraction sync (MVP)
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.budget import BudgetDocument
from app.schemas.document import DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_SUFFIXES = {".pdf", ".csv", ".xlsx", ".txt", ".fdx"}
_MAX_FILE_SIZE_MB = 50


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    currency_code: str = Form("USD"),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not allowed. Supported: {_ALLOWED_SUFFIXES}",
        )

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {_MAX_FILE_SIZE_MB}MB limit")

    doc_id = uuid.uuid4()
    storage_path = f"budget_documents/{doc_id}{suffix}"

    if settings.STORAGE_BACKEND == "local":
        local_path = Path(settings.LOCAL_STORAGE_PATH) / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)

    doc = BudgetDocument(
        id=doc_id,
        project_id=project_id,
        filename=file.filename or f"upload{suffix}",
        file_type=suffix.lstrip("."),
        storage_path=storage_path,
        currency_code=currency_code,
        extraction_status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return DocumentUploadResponse(
        id=doc_id,
        filename=doc.filename,
        storage_path=doc.storage_path,
        extraction_status=doc.extraction_status,
        message="File uploaded. Call /extract-text to run extraction.",
    )


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    result = await db.execute(
        select(BudgetDocument).where(BudgetDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        storage_path=doc.storage_path,
        extraction_status=doc.extraction_status,
        message="",
    )


@router.post("/{document_id}/extract-text", response_model=DocumentUploadResponse)
async def extract_text(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Run text extraction on the stored file (synchronous for MVP)."""
    result = await db.execute(
        select(BudgetDocument).where(BudgetDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    settings = get_settings()
    local_path = Path(settings.LOCAL_STORAGE_PATH) / (doc.storage_path or "")

    if not local_path.exists():
        raise HTTPException(status_code=422, detail="Stored file not found on disk")

    try:
        suffix = local_path.suffix.lower()
        if suffix == ".pdf":
            from app.ingestion.pdf_extractor import extract_text_from_pdf
            extracted = extract_text_from_pdf(local_path)
            doc.raw_text = extracted.raw_text
            doc.page_count = extracted.page_count
        elif suffix == ".csv":
            doc.raw_text = local_path.read_text(errors="replace")
        else:
            doc.raw_text = local_path.read_text(errors="replace")
        doc.extraction_status = "extracted"
    except Exception as exc:
        doc.extraction_status = "failed"
        doc.notes = f"Extraction error: {exc}"

    await db.commit()
    await db.refresh(doc)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        storage_path=doc.storage_path,
        extraction_status=doc.extraction_status,
        message="Extraction complete" if doc.extraction_status == "extracted" else "Extraction failed",
    )
