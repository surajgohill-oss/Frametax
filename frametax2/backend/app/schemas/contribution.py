import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ContributionType, ConfidenceTier
from app.schemas.base import TimestampedSchema


class ContributionCreate(BaseModel):
    project_id: uuid.UUID
    contribution_type: ContributionType
    provider: str
    amount: float = Field(ge=0)
    fair_market_value: Optional[float] = Field(default=None, ge=0)
    replacement_cost: Optional[float] = Field(default=None, ge=0)
    jurisdiction_id: Optional[uuid.UUID] = None
    jurisdiction_specific: bool = False
    qualifies_for_incentive: Optional[bool] = None
    is_conditional: bool = False
    condition_notes: Optional[str] = None
    confidence_tier: ConfidenceTier = ConfidenceTier.DISCOVERY
    source_document_id: Optional[uuid.UUID] = None
    effective_date: Optional[str] = None
    notes: Optional[str] = None


class ContributionRead(TimestampedSchema):
    project_id: uuid.UUID
    contribution_type: ContributionType
    provider: str
    amount: float
    fair_market_value: Optional[float]
    replacement_cost: Optional[float]
    jurisdiction_id: Optional[uuid.UUID]
    jurisdiction_specific: bool
    qualifies_for_incentive: Optional[bool]
    is_conditional: bool
    condition_notes: Optional[str]
    confidence_tier: ConfidenceTier
    source_document_id: Optional[uuid.UUID]
    effective_date: Optional[str]
    notes: Optional[str]


class ContributionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: Optional[float] = Field(default=None, ge=0)
    fair_market_value: Optional[float] = Field(default=None, ge=0)
    replacement_cost: Optional[float] = Field(default=None, ge=0)
    qualifies_for_incentive: Optional[bool] = None
    is_conditional: Optional[bool] = None
    condition_notes: Optional[str] = None
    confidence_tier: Optional[ConfidenceTier] = None
    notes: Optional[str] = None
