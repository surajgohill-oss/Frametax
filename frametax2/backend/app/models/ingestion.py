import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.enums import IngestionStatus


class IngestionJob(Base):
    """
    Tracks async ingestion tasks (PDF extraction, LLM extraction, Drive import).
    Workers update this record during processing.
    """
    __tablename__ = "ingestion_jobs"

    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "pdf_extract", "budget_parse", "screenplay_parse",
    # "llm_extract", "drive_import", "fx_refresh"
    status: Mapped[IngestionStatus] = mapped_column(
        String(20), nullable=False, default=IngestionStatus.PENDING, index=True
    )
    document_type: Mapped[str | None] = mapped_column(String(50))
    source_path: Mapped[str | None] = mapped_column(String(1024))
    target_table: Mapped[str | None] = mapped_column(String(100))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    worker_id: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[str | None] = mapped_column(String(30))
    completed_at: Mapped[str | None] = mapped_column(String(30))
    items_processed: Mapped[int | None] = mapped_column(Integer)
    items_failed: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[dict | None] = mapped_column(JSONB)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
