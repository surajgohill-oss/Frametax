import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.base import TimestampedSchema


class ProjectCreate(BaseModel):
    organization_id: uuid.UUID
    title: str
    logline: str | None = None
    genre: str | None = None
    format: str | None = None
    total_budget_usd: float | None = None
    home_jurisdiction_id: uuid.UUID | None = None
    target_shoot_year: int | None = None
    notes: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project title cannot be blank")
        return v.strip()


class ProjectRead(TimestampedSchema):
    organization_id: uuid.UUID
    owner_id: uuid.UUID | None
    title: str
    logline: str | None
    genre: str | None
    format: str | None
    total_budget_usd: float | None
    home_jurisdiction_id: uuid.UUID | None
    target_shoot_year: int | None
    notes: str | None
    lifecycle: str | None = None
    leading_structure_id: uuid.UUID | None = None


class ProjectUpdate(BaseModel):
    """
    Partial update — Phase C wiring for the two fields whose source of
    truth is moving from frontend-only state to the real Project row:
    lifecycle (user-controlled only — never set by this API on the
    engine's behalf) and leading_structure_id (the producer's "Set as
    Leading" selection). Both optional; only supplied fields are changed.
    """
    lifecycle: str | None = None
    leading_structure_id: uuid.UUID | None = None


class ProjectList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[ProjectRead]
    total: int


class MaterialsCompleteness(BaseModel):
    """The four CORE categories the Project Library card and Project
    Record both key off — never the full document taxonomy (that lives
    on the Record's Materials panel). Fixed set, not a variable list, so
    a card stays scannable at a glance."""
    script: bool
    budget: bool
    deck: bool
    schedule: bool


class ProjectCard(ProjectRead):
    """Project Library grid card — ProjectRead plus the fields the grid
    needs that a plain Project row doesn't carry: artwork, at-a-glance
    material completeness, and served-production state. Never used by
    create/get/update, which don't need the extra queries this costs.

    is_served_production is the SAME canonical served-state signal
    projects.py::get_project_record already computes (structure_count >
    0) — not leading_structure_id, which is narrower (only set once a
    structure is repointed as "leading" and can legitimately stay null
    for a fully-served, mature production). Inspector/Sidebar Closeout
    Phase 1: the Library grid previously had no served-state signal of
    its own and fell back to leading_structure_id for its card-click
    routing, which silently gated already-served productions (e.g. a
    mature production whose baseline was never repointed) behind the
    Project Record's legacy workspace-entry CTA."""
    organization_name: str | None = None
    artwork_url: str | None = None
    materials: MaterialsCompleteness
    is_served_production: bool = False
