import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.base import TimestampedSchema
from app.models.enums import ProgramType, CreditBasis, ConfidenceTier, ReviewStatus


class IncentiveProgramRead(TimestampedSchema):
    jurisdiction_id: uuid.UUID
    name: str
    slug: str
    program_type: ProgramType
    credit_basis: CreditBasis
    base_rate: float | None
    max_rate: float | None
    is_refundable: bool | None
    is_transferable: bool | None
    transferable_value_pct: float | None
    is_competitive: bool
    annual_cap_local: float | None
    requires_cultural_test: bool
    requires_local_entity: bool
    effective_from: str | None
    effective_until: str | None
    confidence_tier: ConfidenceTier
    review_status: ReviewStatus
    authority_url: str | None
    last_verified_date: str | None
    notes: str | None


class IncentiveProgramList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[IncentiveProgramRead]
    total: int
