import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.schemas.base import TimestampedSchema
from app.models.enums import StructureStatus


class ProductionStructureCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    description: str | None = None
    jurisdiction_allocations: list[dict] | None = None
    claimed_program_ids: list[uuid.UUID] | None = None
    talent_arrangements: list[dict] | None = None
    assumed_jurisdiction_spend_pcts: dict[str, float] | None = None
    uses_georgia_logo: bool | None = None
    is_official_coproduction: bool | None = None
    coproduction_treaty: str | None = None
    notes: str | None = None


class ProductionStructureRead(TimestampedSchema):
    project_id: uuid.UUID
    name: str
    description: str | None
    status: StructureStatus
    jurisdiction_allocations: list[dict] | None
    claimed_program_ids: list[Any] | None
    uses_georgia_logo: bool | None
    is_official_coproduction: bool | None
    notes: str | None


class StructureCalculationResultRead(TimestampedSchema):
    structure_id: uuid.UUID
    engine_version: str
    total_budget_usd: float | None
    rebase_btl_usd: float | None
    fixed_atl_usd: float | None
    total_qualifying_spend_usd: float | None
    total_incentive_value_usd: float | None
    total_travel_cost_usd: float | None
    true_net_cost_usd: float | None
    risk_adjusted_net_cost_usd: float | None
    effective_incentive_rate: float | None
    rank_by_net_cost: int | None
    rank_by_incentive_value: int | None
    has_unverified_inputs: bool
    legal_review_required: bool
    qualification_gaps: list[Any] | None
    stacking_violations: list[Any] | None
    warnings: list[Any] | None
    optimization_opportunities: list[Any] | None
    program_results: list[Any] | None
    calculation_trace_json: dict | None
