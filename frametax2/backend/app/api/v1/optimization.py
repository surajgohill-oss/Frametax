"""
optimization.py — Phase F7: Optimization API endpoints.

Provides REST endpoints for gap analysis, recommendations, structure generation,
maximization, and travel cost estimation.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.optimization.qualification_gap_engine import analyse_gaps
from app.optimization.recommendation_engine import generate_recommendations
from app.optimization.structure_generator import generate_structures
from app.optimization.maximization_engine import maximize_structure
from app.calculators.travel_model import estimate_travel_cost


router = APIRouter(prefix="/optimization", tags=["optimization"])


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------

class GapAnalysisRequest(BaseModel):
    structure_slugs: list[str]
    project_profile: dict = Field(default_factory=dict)
    total_budget_usd: float = 5_000_000


class GapAnalysisResponse(BaseModel):
    structure_slugs: list[str]
    total_gaps: int
    blocking_count: int
    addressable_count: int
    total_value_at_risk_usd: float
    total_value_unlockable_usd: float
    gap_summary: str
    gaps: list[dict]


class RecommendationRequest(BaseModel):
    structure_slugs: list[str]
    project_profile: dict = Field(default_factory=dict)
    total_budget_usd: float = 5_000_000


class RecommendationResponse(BaseModel):
    count: int
    recommendations: list[dict]


class GenerateStructuresRequest(BaseModel):
    primary_jurisdiction: str
    secondary_jurisdictions: list[str] = Field(default_factory=list)
    total_budget_usd: float = 5_000_000
    production_type: str = "feature"
    include_treaty: bool = True
    include_regional: bool = True
    include_broadcaster: bool = True


class GenerateStructuresResponse(BaseModel):
    count: int
    structures: list[dict]


class MaximizeRequest(BaseModel):
    primary_jurisdiction: str
    secondary_jurisdictions: list[str] = Field(default_factory=list)
    project_profile: dict = Field(default_factory=dict)
    total_budget_usd: float = 5_000_000
    production_type: str = "feature"


class MaximizeResponse(BaseModel):
    current_soft_money_usd: float
    potential_soft_money_usd: float
    best_soft_money_usd: float
    incremental_gain_usd: float
    actions_required: list[str]
    qualification_risks: list[str]
    confidence: str
    current_structure: dict
    improved_structure: dict
    best_structure: dict


class TravelCostRequest(BaseModel):
    home_base: str = "LA"
    destination_jurisdiction: str
    business_class_seats: int = 1
    premium_economy_seats: int = 0
    economy_seats: int = 0
    travel_frequency_per_year: int = 4
    hotel_nights: int = 14
    per_diem_days: int = 14
    incentive_value_usd: float = 0


class TravelCostResponse(BaseModel):
    home_base: str
    destination_jurisdiction: str
    total_airfare_usd: float
    total_hotel_usd: float
    total_per_diem_usd: float
    total_travel_cost_usd: float
    incentive_value_usd: float
    net_incentive_after_travel_usd: float
    travel_cost_as_pct_of_incentive: float
    recommendation: str


# ---------------------------------------------------------------------------
# Helper to convert dataclass to dict
# ---------------------------------------------------------------------------

def _structure_to_dict(s) -> dict:
    return {
        "structure_id": s.structure_id,
        "structure_type": s.structure_type,
        "primary_jurisdiction": s.primary_jurisdiction,
        "secondary_jurisdictions": s.secondary_jurisdictions,
        "program_slugs": s.program_slugs,
        "programs_unlocked": s.programs_unlocked,
        "grants_unlocked": s.grants_unlocked,
        "funds_unlocked": s.funds_unlocked,
        "broadcasters_unlocked": s.broadcasters_unlocked,
        "estimated_soft_money_usd": s.estimated_soft_money_usd,
        "estimated_total_incentive_usd": s.estimated_total_incentive_usd,
        "qualification_risk": s.qualification_risk,
        "confidence": s.confidence,
        "required_conditions": s.required_conditions,
        "notes": s.notes,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(body: GapAnalysisRequest) -> GapAnalysisResponse:
    """Analyse qualification gaps for the given structure slugs and project profile."""
    result = analyse_gaps(
        structure_slugs=body.structure_slugs,
        project_profile=body.project_profile,
        total_budget_usd=body.total_budget_usd,
    )
    gaps_list = [
        {
            "program_slug": g.program_slug,
            "program_name": g.program_name,
            "gap_type": g.gap_type,
            "description": g.description,
            "current_value": g.current_value,
            "required_value": g.required_value,
            "gap_magnitude": g.gap_magnitude,
            "estimated_value_unlocked_usd": g.estimated_value_unlocked_usd,
            "recommendation": g.recommendation,
            "friction_score": g.friction_score,
            "is_blocker": g.is_blocker,
        }
        for g in result.all_gaps
    ]
    return GapAnalysisResponse(
        structure_slugs=result.structure_slugs,
        total_gaps=result.total_gaps,
        blocking_count=len(result.blocking_gaps),
        addressable_count=len(result.addressable_gaps),
        total_value_at_risk_usd=result.total_value_at_risk_usd,
        total_value_unlockable_usd=result.total_value_unlockable_usd,
        gap_summary=result.gap_summary,
        gaps=gaps_list,
    )


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(body: RecommendationRequest) -> RecommendationResponse:
    """Generate actionable recommendations based on gap analysis."""
    gap_result = analyse_gaps(
        structure_slugs=body.structure_slugs,
        project_profile=body.project_profile,
        total_budget_usd=body.total_budget_usd,
    )
    recs = generate_recommendations(
        gap_result=gap_result,
        structure_slugs=body.structure_slugs,
        project_profile=body.project_profile,
        total_budget_usd=body.total_budget_usd,
    )
    recs_list = [
        {
            "recommendation_id": r.recommendation_id,
            "recommendation_type": r.recommendation_type,
            "title": r.title,
            "description": r.description,
            "specific_actions": r.specific_actions,
            "estimated_value_unlocked_usd": r.estimated_value_unlocked_usd,
            "affected_programs": r.affected_programs,
            "qualification_impact": r.qualification_impact,
            "confidence": r.confidence,
            "implementation_friction": r.implementation_friction,
            "implementation_steps": r.implementation_steps,
            "timeline_weeks": r.timeline_weeks,
            "cost_estimate_usd": r.cost_estimate_usd,
            "net_value_usd": r.net_value_usd,
        }
        for r in recs
    ]
    return RecommendationResponse(count=len(recs_list), recommendations=recs_list)


@router.post("/generate-structures", response_model=GenerateStructuresResponse)
async def generate_structures_endpoint(body: GenerateStructuresRequest) -> GenerateStructuresResponse:
    """Generate candidate production structures for the given jurisdictions."""
    structures = generate_structures(
        primary_jurisdiction=body.primary_jurisdiction,
        secondary_jurisdictions=body.secondary_jurisdictions,
        total_budget_usd=body.total_budget_usd,
        production_type=body.production_type,
        include_treaty=body.include_treaty,
        include_regional=body.include_regional,
        include_broadcaster=body.include_broadcaster,
    )
    return GenerateStructuresResponse(
        count=len(structures),
        structures=[_structure_to_dict(s) for s in structures],
    )


@router.post("/maximize", response_model=MaximizeResponse)
async def maximize(body: MaximizeRequest) -> MaximizeResponse:
    """Maximize production structure incentives for the given jurisdictions."""
    comparison = maximize_structure(
        primary_jurisdiction=body.primary_jurisdiction,
        secondary_jurisdictions=body.secondary_jurisdictions,
        project_profile=body.project_profile,
        total_budget_usd=body.total_budget_usd,
        production_type=body.production_type,
    )
    return MaximizeResponse(
        current_soft_money_usd=comparison.current_soft_money_usd,
        potential_soft_money_usd=comparison.potential_soft_money_usd,
        best_soft_money_usd=comparison.best_soft_money_usd,
        incremental_gain_usd=comparison.incremental_gain_usd,
        actions_required=comparison.actions_required,
        qualification_risks=comparison.qualification_risks,
        confidence=comparison.confidence,
        current_structure=_structure_to_dict(comparison.current_structure),
        improved_structure=_structure_to_dict(comparison.improved_structure),
        best_structure=_structure_to_dict(comparison.best_structure),
    )


@router.post("/travel-cost", response_model=TravelCostResponse)
async def travel_cost(body: TravelCostRequest) -> TravelCostResponse:
    """Estimate travel costs for international production trips."""
    estimate = estimate_travel_cost(
        home_base=body.home_base,
        destination_jurisdiction=body.destination_jurisdiction,
        business_class_seats=body.business_class_seats,
        premium_economy_seats=body.premium_economy_seats,
        economy_seats=body.economy_seats,
        travel_frequency_per_year=body.travel_frequency_per_year,
        hotel_nights=body.hotel_nights,
        per_diem_days=body.per_diem_days,
        incentive_value_usd=body.incentive_value_usd,
    )
    return TravelCostResponse(
        home_base=estimate.home_base,
        destination_jurisdiction=estimate.destination_jurisdiction,
        total_airfare_usd=estimate.total_airfare_usd,
        total_hotel_usd=estimate.total_hotel_usd,
        total_per_diem_usd=estimate.total_per_diem_usd,
        total_travel_cost_usd=estimate.total_travel_cost_usd,
        incentive_value_usd=estimate.incentive_value_usd,
        net_incentive_after_travel_usd=estimate.net_incentive_after_travel_usd,
        travel_cost_as_pct_of_incentive=estimate.travel_cost_as_pct_of_incentive,
        recommendation=estimate.recommendation,
    )
