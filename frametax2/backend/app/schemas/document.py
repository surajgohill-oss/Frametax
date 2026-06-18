import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.base import TimestampedSchema
from app.models.enums import DocumentType, ConfidenceTier, ReviewStatus


class SourceDocumentRead(TimestampedSchema):
    title: str
    document_type: DocumentType
    jurisdiction_id: uuid.UUID | None
    authority_name: str | None
    source_url: str | None
    publication_date: str | None
    effective_from: str | None
    effective_until: str | None
    confidence_tier: ConfidenceTier
    review_status: ReviewStatus
    storage_path: str | None
    page_count: int | None
    notes: str | None


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    storage_path: str | None
    extraction_status: str
    message: str
