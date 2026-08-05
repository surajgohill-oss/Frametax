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
