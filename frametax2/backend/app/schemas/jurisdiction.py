import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.base import TimestampedSchema
from app.models.enums import JurisdictionLevel


class JurisdictionRead(TimestampedSchema):
    parent_id: uuid.UUID | None
    name: str
    code: str
    iso_code: str | None
    level: JurisdictionLevel
    currency_code: str
    country_code: str
    is_active: bool


class JurisdictionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[JurisdictionRead]
    total: int
