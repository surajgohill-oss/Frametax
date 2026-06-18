import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ScreenplayDocument(Base):
    """
    An uploaded screenplay, treatment, or outline.
    """
    __tablename__ = "screenplay_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int | None] = mapped_column(Integer)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="screenplay_documents")
    chunks: Mapped[list["ScreenplayChunk"]] = relationship(back_populates="screenplay")
    extracted_elements: Mapped[list["ExtractedScriptElement"]] = relationship(
        back_populates="screenplay"
    )


class ScreenplayChunk(Base):
    """
    A segment of a screenplay used for vector search or LLM context window management.
    Stored as text chunks with page/sequence references.
    """
    __tablename__ = "screenplay_chunks"

    screenplay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_page: Mapped[int | None] = mapped_column(Integer)
    end_page: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    # embedding: Mapped[list | None] = mapped_column(Vector(1536))
    # Uncomment when pgvector is added

    # Relationships
    screenplay: Mapped["ScreenplayDocument"] = relationship(back_populates="chunks")


class ExtractedScriptElement(Base):
    """
    Structured elements extracted from a screenplay that affect jurisdiction decisions.
    e.g. locations, environments, character nationalities, cultural references.
    """
    __tablename__ = "extracted_script_elements"

    screenplay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    element_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "location", "environment", "climate", "character_nationality",
    # "language", "cultural_reference", "would_not_work_in"
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    context_excerpt: Mapped[str | None] = mapped_column(Text)
    page_reference: Mapped[int | None] = mapped_column(Integer)
    extraction_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    # LLM extraction confidence 0.0–1.0
    is_confirmed: Mapped[bool | None] = mapped_column(
        String(1), default=None
    )  # null=unreviewed

    # Relationships
    screenplay: Mapped["ScreenplayDocument"] = relationship(back_populates="extracted_elements")
