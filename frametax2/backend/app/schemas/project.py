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


class ProjectList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[ProjectRead]
    total: int
