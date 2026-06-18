import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.base import TimestampedSchema
from app.models.enums import ATLBTLCategory, SpendCategory, CompensationType


class BudgetDocumentRead(TimestampedSchema):
    project_id: uuid.UUID
    filename: str
    file_type: str
    currency_code: str
    total_budget_raw: float | None
    origin_city: str | None
    rate_base: str | None
    extraction_status: str
    is_active: bool


class BudgetLineItemRead(TimestampedSchema):
    budget_document_id: uuid.UUID
    department: str | None
    description: str
    atl_btl: ATLBTLCategory
    spend_category: SpendCategory | None
    is_labor: bool
    is_resident_labor: bool | None
    is_fixed: bool
    amount_usd: float | None
    cash_amount_usd: float | None
    compensation_type: CompensationType
    is_qualifying_spend_candidate: bool
    qualifying_amount_usd: float | None
    review_status: str
