import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Numeric, Boolean, UniqueConstraint
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

    # Additive Phase B link into the universal Document/DocumentVersion
    # layer — same pattern as BudgetDocument.document_version_id.
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Script Analyzer SA-1 (canonical: ScriptDocument, EXTEND) ───────────
    # DocumentVersion — not filename — is the source authority. A parse is
    # scoped to exactly one DocumentVersion; a revised screenplay is a new
    # version and therefore a new parse lineage that never overwrites the
    # prior one.
    parser_version: Mapped[str | None] = mapped_column(String(64))
    # Which deterministic parser produced the current structure.
    input_fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)
    # sha256 of the exact parsed text. Together with parser_version this
    # makes reprocessing an unchanged version idempotent.
    parse_status: Mapped[str | None] = mapped_column(String(40), index=True)
    # See app/services/script_parse_status.py for the canonical enum.
    parse_error: Mapped[str | None] = mapped_column(Text)
    page_basis: Mapped[str | None] = mapped_column(String(40))
    # LAYOUT_FORM_FEED | LAYOUT_PAGE_MARKER | APPROXIMATE_NO_LAYOUT — never
    # let an approximate page count be mistaken for a real one.
    total_eighths: Mapped[int | None] = mapped_column(Integer)
    parsed_at: Mapped[str | None] = mapped_column(String(40))
    parse_warnings: Mapped[list | None] = mapped_column(JSONB)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="screenplay_documents")
    chunks: Mapped[list["ScreenplayChunk"]] = relationship(back_populates="screenplay")
    extracted_elements: Mapped[list["ExtractedScriptElement"]] = relationship(
        back_populates="screenplay"
    )
    document_version: Mapped["DocumentVersion | None"] = relationship()
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="screenplay", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="screenplay", cascade="all, delete-orphan"
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


class Scene(Base):
    """
    Script Analyzer SA-1 (canonical: Scene, BUILD_NEW).

    A version-scoped deterministic screenplay scene. Identity is stable
    WITHIN a DocumentVersion: (screenplay_id, sequence) is unique, and
    scene_hash fingerprints sequence + normalized heading + source offset so
    a re-parse of identical bytes reproduces identical rows.

    Cross-draft lineage is deliberately NOT inferred here. When a revised
    screenplay arrives it becomes a new ScreenplayDocument for the new
    DocumentVersion with its own scenes; linking scene N of draft 2 to scene
    N of draft 1 is a separate, explicit operation and is left null rather
    than guessed.
    """
    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("screenplay_id", "sequence", name="uq_scenes_screenplay_sequence"),
    )

    screenplay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1-based order of appearance — always present, unlike source_scene_number.
    source_scene_number: Mapped[str | None] = mapped_column(String(20))
    # The number printed in the script ("14A"), when the script numbers scenes.

    raw_heading: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_heading: Mapped[str] = mapped_column(Text, nullable=False)
    int_ext: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # INT | EXT | INT_EXT | UNKNOWN — ambiguity stays UNKNOWN, never guessed.
    time_of_day: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    # DAY | NIGHT | DAWN | DUSK | CONTINUOUS | LATER | UNKNOWN
    scripted_location: Mapped[str | None] = mapped_column(Text)
    # The location AS WRITTEN. The real production location is a producer
    # decision and is never stored here.
    location_key: Mapped[str | None] = mapped_column(String(255), index=True)
    # Canonicalized form used for recurrence counting.

    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    eighths: Mapped[int | None] = mapped_column(Integer)

    scene_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    screenplay: Mapped["ScreenplayDocument"] = relationship(back_populates="scenes")
    elements: Mapped[list["ExtractedScriptElement"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class Character(Base):
    """
    Script Analyzer SA-1 (canonical: Character, BUILD_NEW).

    A FICTIONAL character within one screenplay version. Deliberately NOT
    ProjectPerson: ProjectPerson represents a real attached human (a cast
    or crew member). Conflating the two would let a casting decision
    silently become a script fact, or vice versa. A confirmed casting link
    is a later, explicit connection — not this table's job.
    """
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("screenplay_id", "canonical_name", name="uq_characters_screenplay_name"),
    )

    screenplay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    aliases: Mapped[list | None] = mapped_column(JSONB)
    # Only deterministically-resolvable variants (e.g. a "(CONT'D)" cue).

    scene_sequences: Mapped[list | None] = mapped_column(JSONB)
    scene_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dialogue_block_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dialogue_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_speaking_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # DERIVED_DETERMINISTIC: has at least one linked dialogue block.
    eighths_burden: Mapped[int | None] = mapped_column(Integer)
    # Sum of the eighths of scenes this character speaks in. A workload
    # signal only — never a fee, tier or compensation assumption.

    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    screenplay: Mapped["ScreenplayDocument"] = relationship(back_populates="characters")


class ExtractedScriptElement(Base):
    """
    Structured elements extracted from a screenplay that affect jurisdiction decisions.
    e.g. locations, environments, character nationalities, cultural references.

    Script Analyzer SA-1 extends this into the canonical SceneElement: an
    evidence-backed observation scoped to a Scene, carrying its taxonomy key,
    normalized value, source span and evidence state. Pre-SA-1 rows keep
    scene_id NULL and are untouched.
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

    # ── Script Analyzer SA-1 (canonical: SceneElement, EXTEND) ─────────────
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    taxonomy_key: Mapped[str | None] = mapped_column(String(48), index=True)
    # SA-1 objective subset only — see screenplay_structural_parser.SA1_TAXONOMY.
    normalized_value: Mapped[str | None] = mapped_column(String(512))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4))
    quantity_max: Mapped[float | None] = mapped_column(Numeric(18, 4))
    unit: Mapped[str | None] = mapped_column(String(32))
    # SA-1 leaves quantity/unit NULL: presence is evidence, scale is not.
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    extraction_method: Mapped[str | None] = mapped_column(String(40), index=True)
    # DETERMINISTIC_PARSE (SA-1). AI methods arrive in later phases and are
    # always distinguishable from this value.
    evidence_state: Mapped[str | None] = mapped_column(String(40), index=True)
    # OBJECTIVE_SCRIPT_FACT | DERIVED_DETERMINISTIC
    is_interpretation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Always False in SA-1 — nothing here is interpreted.
    review_state: Mapped[str | None] = mapped_column(String(24))
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_script_elements.id", ondelete="SET NULL"),
        nullable=True,
    )
    parser_version: Mapped[str | None] = mapped_column(String(64))

    # Relationships
    screenplay: Mapped["ScreenplayDocument"] = relationship(back_populates="extracted_elements")
    scene: Mapped["Scene | None"] = relationship(back_populates="elements")
