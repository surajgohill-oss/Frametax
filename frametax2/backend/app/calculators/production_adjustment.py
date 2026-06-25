"""
production_adjustment.py

Production Adjustment Layer — deterministic cost normalization for jurisdiction comparison.

Two modes:
  GREENFIELD       — all location-dependent costs calculated from scratch.
  EXISTING_BUDGET  — only the DELTA vs. the jurisdiction embedded in the uploaded budget.
                     Never double-counts costs already baked into the existing budget.

Every adjustment category is individually toggleable via AdjustmentToggles.
When excluded:
  - original calculated value is preserved in AdjustmentLineItem.calculated_amount_usd
  - active amount_usd is set to 0.0
  - user_excluded=True is set on the line item
  - an exclusion note is appended to the result

No live API calls. No DB access. Pure calculation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.data.location_cost_benchmarks import (
    JurisdictionCostProfile,
    get_profile_or_fallback,
)

CALCULATOR_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Enums and configuration dataclasses
# ---------------------------------------------------------------------------

class AdjustmentMode(str, Enum):
    GREENFIELD = "GREENFIELD"
    EXISTING_BUDGET = "EXISTING_BUDGET"


class AdjustmentCategory(str, Enum):
    AIRFARE = "airfare"
    HOTEL = "hotel"
    PER_DIEM = "per_diem"
    FREIGHT_CARNET = "freight_carnet"
    VISA_WORK_PERMIT = "visa_work_permit"
    PAYROLL_FRINGE = "payroll_fringe"
    LOCAL_TRANSPORT = "local_transport"
    LEGAL_ACCOUNTING = "legal_accounting"
    LOCAL_HIRE_PREMIUM = "local_hire_premium"
    EQUIPMENT = "equipment"
    STAGE_FACILITY = "stage_facility"
    CONTINGENCY = "contingency"
    FX = "fx"


@dataclass
class AdjustmentToggles:
    """
    Per-category enable/disable flags.

    When a category is False (excluded):
      - calculated_amount_usd is still populated
      - amount_usd is zeroed
      - user_excluded=True is set on the line item
    """
    airfare: bool = True
    hotel: bool = True
    per_diem: bool = True
    freight_carnet: bool = True
    visa_work_permit: bool = True
    payroll_fringe: bool = True
    local_transport: bool = True
    legal_accounting: bool = True
    local_hire_premium: bool = True
    equipment: bool = True
    stage_facility: bool = True
    contingency: bool = True
    fx: bool = True

    def is_enabled(self, category: AdjustmentCategory) -> bool:
        return getattr(self, category.value)


@dataclass
class CrewManifest:
    """
    Crew traveling from the home base to the destination jurisdiction.

    Local crew hired at destination is captured by local_btl_count.
    Business-class eligibility is role-based:
      - ATL (director, leads, exec producers) → business_class by default
      - Dept heads → business/premium-economy configurable
      - Remaining BTL crew → economy
    """
    # ATL (above-the-line) from home base — always traveling
    atl_count: int = 4
    atl_business_class: bool = True

    # BTL department heads traveling from home base
    dept_head_count: int = 8
    dept_head_business_class: bool = False   # default: economy

    # Remaining BTL crew traveling from home base
    btl_traveling_count: int = 20

    # Local crew hired at destination (NOT traveling)
    local_btl_count: int = 60

    # Producer oversight trips (separate from main company move)
    producer_oversight_trips: int = 3
    producer_oversight_business: bool = True

    # Production calendar
    shoot_days: int = 30
    hotel_nights_traveling_crew: int = 35   # includes prep/wrap overlap
    per_diem_days_traveling: int = 35

    def total_traveling(self) -> int:
        return self.atl_count + self.dept_head_count + self.btl_traveling_count

    def total_crew(self) -> int:
        return self.total_traveling() + self.local_btl_count


@dataclass
class ProductionBudgetParams:
    """
    Budget parameters used for percentage-based adjustments.
    All values in USD.
    """
    total_budget_usd: float = 5_000_000.0
    btl_budget_usd: float = 3_000_000.0
    equipment_value_usd: float = 500_000.0    # for freight/carnet
    gross_payroll_usd: float = 2_000_000.0
    la_legal_accounting_usd: float = 150_000.0  # baseline for index comparison
    la_equipment_rental_usd: float = 400_000.0  # baseline for index comparison
    la_stage_facility_usd: float = 300_000.0    # baseline for index comparison


@dataclass
class ProductionAdjustmentInput:
    home_base_iso2: str = "US"           # ISO2 of home base (US = LA)
    home_base_iata: str = "LAX"          # IATA code for airfare routing
    destination_iso2: str = "GB"
    mode: AdjustmentMode = AdjustmentMode.GREENFIELD
    existing_budget_iso2: Optional[str] = None   # required for EXISTING_BUDGET mode

    crew: CrewManifest = field(default_factory=CrewManifest)
    budget: ProductionBudgetParams = field(default_factory=ProductionBudgetParams)
    toggles: AdjustmentToggles = field(default_factory=AdjustmentToggles)

    # JFK alternative home base adds a delta from the fare tables
    use_jfk_as_secondary: bool = False


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AdjustmentLineItem:
    category: AdjustmentCategory
    subcategory: str
    calculated_amount_usd: float    # always populated, even when excluded
    amount_usd: float               # 0.0 if user_excluded
    quantity: float
    unit_cost_usd: float
    unit: str
    notes: str
    confidence: str                 # HIGH / MEDIUM / LOW
    user_excluded: bool = False

    def exclusion_note(self) -> str:
        if self.user_excluded:
            return (
                f"[USER EXCLUDED] {self.category.value}: "
                f"calculated value ${self.calculated_amount_usd:,.0f} preserved but not counted. "
                f"Recalculate net producer benefit to include."
            )
        return ""


@dataclass
class ProductionAdjustmentResult:
    calculator_version: str
    mode: AdjustmentMode
    destination_iso2: str
    existing_budget_iso2: Optional[str]
    home_base_iso2: str

    # Totals
    total_adjustment_usd: float         # sum of all active (non-excluded) adjustments
    total_calculated_usd: float         # sum of all adjustments regardless of exclusion
    total_excluded_usd: float           # sum of excluded adjustment values

    # By category totals (active only)
    airfare_usd: float
    hotel_usd: float
    per_diem_usd: float
    freight_carnet_usd: float
    visa_work_permit_usd: float
    payroll_fringe_usd: float
    local_transport_usd: float
    legal_accounting_usd: float
    local_hire_premium_usd: float
    equipment_usd: float
    stage_facility_usd: float
    contingency_usd: float
    fx_usd: float

    # Detailed line items
    line_items: list[AdjustmentLineItem] = field(default_factory=list)

    # Narrative
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    exclusion_notes: list[str] = field(default_factory=list)
    confidence: str = "MEDIUM"

    # Destination profile metadata
    destination_profile_confidence: str = "UNKNOWN"


# ---------------------------------------------------------------------------
# Internal calculation helpers
# ---------------------------------------------------------------------------

def _airfare_one_way_business(
    profile: JurisdictionCostProfile,
    home_base_iso2: str,
    use_jfk: bool,
) -> float:
    base = profile.airfare_lax_business_usd
    if use_jfk:
        base += profile.airfare_jfk_delta_usd
    # Same jurisdiction: no airfare
    if home_base_iso2.upper() == profile.iso2:
        return 0.0
    return max(0.0, base)


def _airfare_one_way_economy(
    profile: JurisdictionCostProfile,
    home_base_iso2: str,
    use_jfk: bool,
) -> float:
    return _airfare_one_way_business(profile, home_base_iso2, use_jfk) * 0.25


def _compute_airfare(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    home_base_iso2: str,
    use_jfk: bool,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2:
        return 0.0, []

    biz_ow = _airfare_one_way_business(profile, home_base_iso2, use_jfk)
    eco_ow = _airfare_one_way_economy(profile, home_base_iso2, use_jfk)
    rt_biz = biz_ow * 2
    rt_eco = eco_ow * 2

    items: list[AdjustmentLineItem] = []

    # ATL: business or economy depending on manifest flag
    atl_rate = rt_biz if crew.atl_business_class else rt_eco
    atl_cabin = "business" if crew.atl_business_class else "economy"
    atl_total = crew.atl_count * atl_rate
    items.append(AdjustmentLineItem(
        category=AdjustmentCategory.AIRFARE,
        subcategory="atl_business_class",
        calculated_amount_usd=atl_total,
        amount_usd=atl_total,
        quantity=float(crew.atl_count),
        unit_cost_usd=atl_rate,
        unit="person round-trip",
        notes=f"ATL crew ({crew.atl_count} pax), {atl_cabin}",
        confidence="HIGH",
    ))

    # Dept heads: economy or business
    dh_rate = rt_biz if crew.dept_head_business_class else rt_eco
    dh_total = crew.dept_head_count * dh_rate
    cabin = "business" if crew.dept_head_business_class else "economy"
    items.append(AdjustmentLineItem(
        category=AdjustmentCategory.AIRFARE,
        subcategory="dept_head_airfare",
        calculated_amount_usd=dh_total,
        amount_usd=dh_total,
        quantity=float(crew.dept_head_count),
        unit_cost_usd=dh_rate,
        unit="person round-trip",
        notes=f"Dept heads ({crew.dept_head_count} pax), {cabin}",
        confidence="HIGH",
    ))

    # BTL traveling crew: economy
    btl_total = crew.btl_traveling_count * rt_eco
    items.append(AdjustmentLineItem(
        category=AdjustmentCategory.AIRFARE,
        subcategory="btl_traveling_economy",
        calculated_amount_usd=btl_total,
        amount_usd=btl_total,
        quantity=float(crew.btl_traveling_count),
        unit_cost_usd=rt_eco,
        unit="person round-trip",
        notes=f"BTL traveling crew ({crew.btl_traveling_count} pax), economy",
        confidence="HIGH",
    ))

    # Producer oversight trips
    po_rate = rt_biz if crew.producer_oversight_business else rt_eco
    po_total = crew.producer_oversight_trips * po_rate
    cabin_po = "business" if crew.producer_oversight_business else "economy"
    items.append(AdjustmentLineItem(
        category=AdjustmentCategory.AIRFARE,
        subcategory="producer_oversight",
        calculated_amount_usd=po_total,
        amount_usd=po_total,
        quantity=float(crew.producer_oversight_trips),
        unit_cost_usd=po_rate,
        unit="trip round-trip",
        notes=f"Producer oversight trips ({crew.producer_oversight_trips}), {cabin_po}",
        confidence="MEDIUM",
    ))

    total = atl_total + dh_total + btl_total + po_total
    return total, items


def _compute_hotel(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2:
        return 0.0, []

    total_pax = crew.atl_count + crew.dept_head_count + crew.btl_traveling_count
    total = total_pax * crew.hotel_nights_traveling_crew * profile.hotel_rate_usd
    item = AdjustmentLineItem(
        category=AdjustmentCategory.HOTEL,
        subcategory="hotel_accommodation",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=float(total_pax * crew.hotel_nights_traveling_crew),
        unit_cost_usd=profile.hotel_rate_usd,
        unit="room-night",
        notes=(
            f"{total_pax} pax × {crew.hotel_nights_traveling_crew} nights "
            f"@ ${profile.hotel_rate_usd}/night"
        ),
        confidence="HIGH",
    )
    return total, [item]


def _compute_per_diem(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2:
        return 0.0, []

    atl_pd = crew.atl_count * crew.per_diem_days_traveling * profile.per_diem_atl_usd
    btl_pd = (crew.dept_head_count + crew.btl_traveling_count) * crew.per_diem_days_traveling * profile.per_diem_btl_usd

    items = [
        AdjustmentLineItem(
            category=AdjustmentCategory.PER_DIEM,
            subcategory="atl_per_diem",
            calculated_amount_usd=atl_pd,
            amount_usd=atl_pd,
            quantity=float(crew.atl_count * crew.per_diem_days_traveling),
            unit_cost_usd=profile.per_diem_atl_usd,
            unit="person-day",
            notes=f"ATL per diem: {crew.atl_count} pax × {crew.per_diem_days_traveling} days",
            confidence="HIGH",
        ),
        AdjustmentLineItem(
            category=AdjustmentCategory.PER_DIEM,
            subcategory="btl_per_diem",
            calculated_amount_usd=btl_pd,
            amount_usd=btl_pd,
            quantity=float((crew.dept_head_count + crew.btl_traveling_count) * crew.per_diem_days_traveling),
            unit_cost_usd=profile.per_diem_btl_usd,
            unit="person-day",
            notes=f"BTL per diem: {crew.dept_head_count + crew.btl_traveling_count} pax × {crew.per_diem_days_traveling} days",
            confidence="HIGH",
        ),
    ]
    return atl_pd + btl_pd, items


def _compute_freight_carnet(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2:
        return 0.0, []
    total = budget.equipment_value_usd * (profile.freight_carnet_pct / 100.0)
    item = AdjustmentLineItem(
        category=AdjustmentCategory.FREIGHT_CARNET,
        subcategory="freight_and_carnet",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.equipment_value_usd,
        unit_cost_usd=profile.freight_carnet_pct / 100.0,
        unit="% of equipment value",
        notes=(
            f"Freight + carnet: {profile.freight_carnet_pct}% of "
            f"${budget.equipment_value_usd:,.0f} equipment value"
        ),
        confidence="MEDIUM",
    )
    return total, [item]


def _compute_visa_work_permit(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2:
        return 0.0, []

    traveling_count = crew.total_traveling()
    wp_total = traveling_count * profile.work_permit_cost_usd
    visa_total = traveling_count * profile.visa_cost_usd

    items: list[AdjustmentLineItem] = []
    if profile.work_permit_cost_usd > 0:
        items.append(AdjustmentLineItem(
            category=AdjustmentCategory.VISA_WORK_PERMIT,
            subcategory="work_permits",
            calculated_amount_usd=wp_total,
            amount_usd=wp_total,
            quantity=float(traveling_count),
            unit_cost_usd=profile.work_permit_cost_usd,
            unit="person",
            notes=f"Work permits: {traveling_count} imported crew",
            confidence="HIGH",
        ))
    if profile.visa_cost_usd > 0:
        items.append(AdjustmentLineItem(
            category=AdjustmentCategory.VISA_WORK_PERMIT,
            subcategory="visas",
            calculated_amount_usd=visa_total,
            amount_usd=visa_total,
            quantity=float(traveling_count),
            unit_cost_usd=profile.visa_cost_usd,
            unit="person",
            notes=f"Visas: {traveling_count} crew",
            confidence="HIGH",
        ))
    return wp_total + visa_total, items


def _compute_payroll_fringe(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_us: JurisdictionCostProfile,
) -> tuple[float, list[AdjustmentLineItem]]:
    dest_fringe = budget.gross_payroll_usd * (profile.payroll_fringe_pct / 100.0)
    base_fringe = budget.gross_payroll_usd * (home_us_fringe := home_base_us.payroll_fringe_pct / 100.0)
    # We report the destination fringe + overhead; caller decides whether to delta
    total_fringe = dest_fringe
    overhead = budget.gross_payroll_usd * (profile.payroll_overhead_pct / 100.0)
    total = total_fringe + overhead
    items = [
        AdjustmentLineItem(
            category=AdjustmentCategory.PAYROLL_FRINGE,
            subcategory="employer_fringe",
            calculated_amount_usd=total_fringe,
            amount_usd=total_fringe,
            quantity=budget.gross_payroll_usd,
            unit_cost_usd=profile.payroll_fringe_pct / 100.0,
            unit="% of gross payroll",
            notes=f"Employer social charges: {profile.payroll_fringe_pct}%",
            confidence="HIGH",
        ),
        AdjustmentLineItem(
            category=AdjustmentCategory.PAYROLL_FRINGE,
            subcategory="payroll_admin_overhead",
            calculated_amount_usd=overhead,
            amount_usd=overhead,
            quantity=budget.gross_payroll_usd,
            unit_cost_usd=profile.payroll_overhead_pct / 100.0,
            unit="% of gross payroll",
            notes=f"Payroll admin/compliance overhead: {profile.payroll_overhead_pct}%",
            confidence="MEDIUM",
        ),
    ]
    return total, items


def _compute_local_transport(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    total = profile.local_transport_daily_usd * crew.shoot_days
    item = AdjustmentLineItem(
        category=AdjustmentCategory.LOCAL_TRANSPORT,
        subcategory="local_transport",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=float(crew.shoot_days),
        unit_cost_usd=profile.local_transport_daily_usd,
        unit="shoot day",
        notes=f"Local transport: ${profile.local_transport_daily_usd}/day × {crew.shoot_days} days",
        confidence="MEDIUM",
    )
    return total, [item]


def _compute_legal_accounting(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_us: JurisdictionCostProfile,
) -> tuple[float, list[AdjustmentLineItem]]:
    dest_cost = budget.la_legal_accounting_usd * profile.legal_accounting_index
    total = dest_cost
    item = AdjustmentLineItem(
        category=AdjustmentCategory.LEGAL_ACCOUNTING,
        subcategory="legal_accounting_overhead",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.la_legal_accounting_usd,
        unit_cost_usd=profile.legal_accounting_index,
        unit="index vs LA",
        notes=(
            f"Legal/accounting index {profile.legal_accounting_index:.2f} × "
            f"${budget.la_legal_accounting_usd:,.0f} LA baseline"
        ),
        confidence="MEDIUM",
    )
    return total, [item]


def _compute_local_hire_premium(
    profile: JurisdictionCostProfile,
    crew: CrewManifest,
    budget: ProductionBudgetParams,
) -> tuple[float, list[AdjustmentLineItem]]:
    if profile.local_hire_min_pct <= 0:
        return 0.0, []
    # Cost: local hires cost (crew_rate_index × btl_budget) for the required % of headcount
    # Premium is the difference vs. traveling own crew at home rates
    local_hire_fraction = profile.local_hire_min_pct / 100.0
    local_hire_budget = budget.btl_budget_usd * local_hire_fraction * profile.crew_rate_index
    # Their cost at LA rates for the same headcount (counterfactual)
    la_equivalent = budget.btl_budget_usd * local_hire_fraction
    # Premium = local cost − LA cost (could be negative = savings)
    premium = local_hire_budget - la_equivalent
    total = max(0.0, premium)  # only report if more expensive than LA crew
    confidence = "MEDIUM"
    if abs(premium) < 1:
        return 0.0, []
    item = AdjustmentLineItem(
        category=AdjustmentCategory.LOCAL_HIRE_PREMIUM,
        subcategory="local_hire_minimum",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=local_hire_fraction,
        unit_cost_usd=budget.btl_budget_usd,
        unit="% of BTL budget",
        notes=(
            f"Local hire min {profile.local_hire_min_pct}%: "
            f"destination crew rate index {profile.crew_rate_index:.2f} vs 1.0 LA. "
            f"{'Premium' if premium >= 0 else 'Saving'}: ${abs(premium):,.0f}"
        ),
        confidence=confidence,
    )
    return total, [item]


def _compute_equipment(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_us: JurisdictionCostProfile,
) -> tuple[float, list[AdjustmentLineItem]]:
    dest_cost = budget.la_equipment_rental_usd * profile.equipment_rental_index
    total = dest_cost
    item = AdjustmentLineItem(
        category=AdjustmentCategory.EQUIPMENT,
        subcategory="equipment_rental",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.la_equipment_rental_usd,
        unit_cost_usd=profile.equipment_rental_index,
        unit="index vs LA",
        notes=(
            f"Equipment rental index {profile.equipment_rental_index:.2f} × "
            f"${budget.la_equipment_rental_usd:,.0f} LA baseline"
        ),
        confidence="MEDIUM",
    )
    return total, [item]


def _compute_stage_facility(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_us: JurisdictionCostProfile,
) -> tuple[float, list[AdjustmentLineItem]]:
    dest_cost = budget.la_stage_facility_usd * profile.stage_facility_index
    total = dest_cost
    item = AdjustmentLineItem(
        category=AdjustmentCategory.STAGE_FACILITY,
        subcategory="stage_facility",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.la_stage_facility_usd,
        unit_cost_usd=profile.stage_facility_index,
        unit="index vs LA",
        notes=(
            f"Stage/facility index {profile.stage_facility_index:.2f} × "
            f"${budget.la_stage_facility_usd:,.0f} LA baseline"
        ),
        confidence="MEDIUM",
    )
    return total, [item]


def _compute_contingency(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
) -> tuple[float, list[AdjustmentLineItem]]:
    if profile.contingency_adj_pct <= 0:
        return 0.0, []
    total = budget.total_budget_usd * (profile.contingency_adj_pct / 100.0)
    item = AdjustmentLineItem(
        category=AdjustmentCategory.CONTINGENCY,
        subcategory="contingency_adjustment",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.total_budget_usd,
        unit_cost_usd=profile.contingency_adj_pct / 100.0,
        unit="% of total budget",
        notes=(
            f"Additional contingency for {profile.name}: "
            f"+{profile.contingency_adj_pct}% "
            f"(schedule risk {profile.schedule_risk_multiplier:.2f}x)"
        ),
        confidence="LOW",
    )
    return total, [item]


def _compute_fx(
    profile: JurisdictionCostProfile,
    budget: ProductionBudgetParams,
    home_base_iso2: str,
) -> tuple[float, list[AdjustmentLineItem]]:
    if home_base_iso2.upper() == profile.iso2 or profile.fx_risk_pct <= 0:
        return 0.0, []
    total = budget.total_budget_usd * (profile.fx_risk_pct / 100.0)
    item = AdjustmentLineItem(
        category=AdjustmentCategory.FX,
        subcategory="fx_normalization",
        calculated_amount_usd=total,
        amount_usd=total,
        quantity=budget.total_budget_usd,
        unit_cost_usd=profile.fx_risk_pct / 100.0,
        unit="% of total budget",
        notes=f"FX risk/hedging add-on: {profile.fx_risk_pct}% for {profile.name}",
        confidence="LOW",
    )
    return total, [item]


def _apply_toggle(
    item: AdjustmentLineItem,
    enabled: bool,
) -> AdjustmentLineItem:
    if not enabled:
        return AdjustmentLineItem(
            category=item.category,
            subcategory=item.subcategory,
            calculated_amount_usd=item.calculated_amount_usd,
            amount_usd=0.0,
            quantity=item.quantity,
            unit_cost_usd=item.unit_cost_usd,
            unit=item.unit,
            notes=item.notes,
            confidence=item.confidence,
            user_excluded=True,
        )
    return item


# ---------------------------------------------------------------------------
# Main calculation functions
# ---------------------------------------------------------------------------

def _build_result_from_items(
    items: list[AdjustmentLineItem],
    input_: ProductionAdjustmentInput,
    profile: JurisdictionCostProfile,
    existing_profile: Optional[JurisdictionCostProfile],
    assumptions: list[str],
    unknowns: list[str],
) -> ProductionAdjustmentResult:
    totals: dict[AdjustmentCategory, float] = {c: 0.0 for c in AdjustmentCategory}
    total_active = 0.0
    total_calculated = 0.0
    total_excluded = 0.0
    exclusion_notes: list[str] = []

    for item in items:
        total_calculated += item.calculated_amount_usd
        if item.user_excluded:
            total_excluded += item.calculated_amount_usd
            exclusion_notes.append(item.exclusion_note())
        else:
            totals[item.category] += item.amount_usd
            total_active += item.amount_usd

    # Overall confidence
    confidences = {i.confidence for i in items}
    if "LOW" in confidences:
        overall_conf = "LOW"
    elif "MEDIUM" in confidences:
        overall_conf = "MEDIUM"
    else:
        overall_conf = "HIGH"

    return ProductionAdjustmentResult(
        calculator_version=CALCULATOR_VERSION,
        mode=input_.mode,
        destination_iso2=input_.destination_iso2.upper(),
        existing_budget_iso2=input_.existing_budget_iso2,
        home_base_iso2=input_.home_base_iso2.upper(),
        total_adjustment_usd=round(total_active, 2),
        total_calculated_usd=round(total_calculated, 2),
        total_excluded_usd=round(total_excluded, 2),
        airfare_usd=round(totals[AdjustmentCategory.AIRFARE], 2),
        hotel_usd=round(totals[AdjustmentCategory.HOTEL], 2),
        per_diem_usd=round(totals[AdjustmentCategory.PER_DIEM], 2),
        freight_carnet_usd=round(totals[AdjustmentCategory.FREIGHT_CARNET], 2),
        visa_work_permit_usd=round(totals[AdjustmentCategory.VISA_WORK_PERMIT], 2),
        payroll_fringe_usd=round(totals[AdjustmentCategory.PAYROLL_FRINGE], 2),
        local_transport_usd=round(totals[AdjustmentCategory.LOCAL_TRANSPORT], 2),
        legal_accounting_usd=round(totals[AdjustmentCategory.LEGAL_ACCOUNTING], 2),
        local_hire_premium_usd=round(totals[AdjustmentCategory.LOCAL_HIRE_PREMIUM], 2),
        equipment_usd=round(totals[AdjustmentCategory.EQUIPMENT], 2),
        stage_facility_usd=round(totals[AdjustmentCategory.STAGE_FACILITY], 2),
        contingency_usd=round(totals[AdjustmentCategory.CONTINGENCY], 2),
        fx_usd=round(totals[AdjustmentCategory.FX], 2),
        line_items=items,
        assumptions=assumptions,
        unknowns=unknowns,
        exclusion_notes=exclusion_notes,
        confidence=overall_conf,
        destination_profile_confidence=profile.confidence,
    )


def _compute_all_items_for_profile(
    profile: JurisdictionCostProfile,
    home_base_us: JurisdictionCostProfile,
    input_: ProductionAdjustmentInput,
    toggles: AdjustmentToggles,
) -> list[AdjustmentLineItem]:
    """Compute all line items for a single jurisdiction profile."""
    all_items: list[AdjustmentLineItem] = []

    def add(
        cat: AdjustmentCategory,
        total: float,
        sub_items: list[AdjustmentLineItem],
    ) -> None:
        enabled = toggles.is_enabled(cat)
        for it in sub_items:
            all_items.append(_apply_toggle(it, enabled))
        if not sub_items and total > 0:
            # single-item categories sometimes return empty list when total=0
            pass

    _, items = _compute_airfare(profile, input_.crew, input_.home_base_iso2, input_.use_jfk_as_secondary)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.airfare))

    _, items = _compute_hotel(profile, input_.crew, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.hotel))

    _, items = _compute_per_diem(profile, input_.crew, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.per_diem))

    _, items = _compute_freight_carnet(profile, input_.budget, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.freight_carnet))

    _, items = _compute_visa_work_permit(profile, input_.crew, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.visa_work_permit))

    _, items = _compute_payroll_fringe(profile, input_.budget, home_base_us)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.payroll_fringe))

    _, items = _compute_local_transport(profile, input_.crew, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.local_transport))

    _, items = _compute_legal_accounting(profile, input_.budget, home_base_us)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.legal_accounting))

    _, items = _compute_local_hire_premium(profile, input_.crew, input_.budget)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.local_hire_premium))

    _, items = _compute_equipment(profile, input_.budget, home_base_us)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.equipment))

    _, items = _compute_stage_facility(profile, input_.budget, home_base_us)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.stage_facility))

    _, items = _compute_contingency(profile, input_.budget)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.contingency))

    _, items = _compute_fx(profile, input_.budget, input_.home_base_iso2)
    for it in items:
        all_items.append(_apply_toggle(it, toggles.fx))

    return all_items


def _delta_items(
    dest_items: list[AdjustmentLineItem],
    base_items: list[AdjustmentLineItem],
) -> list[AdjustmentLineItem]:
    """
    Produce delta line items: destination cost minus baseline cost per sub-category.

    This is the anti-double-count mechanism: when the budget is already built
    for the baseline jurisdiction, only the incremental cost difference matters.
    """
    base_by_sub: dict[str, float] = {}
    for it in base_items:
        key = f"{it.category.value}::{it.subcategory}"
        base_by_sub[key] = base_by_sub.get(key, 0.0) + it.calculated_amount_usd

    delta_items: list[AdjustmentLineItem] = []
    for it in dest_items:
        key = f"{it.category.value}::{it.subcategory}"
        base_val = base_by_sub.get(key, 0.0)
        delta_calc = it.calculated_amount_usd - base_val
        delta_active = it.amount_usd - (base_val if not it.user_excluded else 0.0)

        delta_items.append(AdjustmentLineItem(
            category=it.category,
            subcategory=it.subcategory,
            calculated_amount_usd=delta_calc,
            amount_usd=max(0.0, delta_active) if not it.user_excluded else 0.0,
            quantity=it.quantity,
            unit_cost_usd=it.unit_cost_usd,
            unit=it.unit,
            notes=(
                f"DELTA vs existing budget: {it.notes} "
                f"[base=${base_val:,.0f}, dest=${it.calculated_amount_usd:,.0f}, "
                f"delta=${delta_calc:+,.0f}]"
            ),
            confidence=it.confidence,
            user_excluded=it.user_excluded,
        ))
    return delta_items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_production_adjustment(
    input_: ProductionAdjustmentInput,
) -> ProductionAdjustmentResult:
    """
    Calculate production adjustment costs for a destination jurisdiction.

    GREENFIELD:      Full cost of all location-dependent items.
    EXISTING_BUDGET: Only the incremental delta vs. the existing budget's jurisdiction.
                     Prevents double-counting travel/accommodation embedded in the budget.

    Regression constraint:
      When mode=EXISTING_BUDGET and destination == existing_budget_iso2,
      all deltas are 0.0 (cost-neutral — already in the budget).
    """
    dest_profile = get_profile_or_fallback(input_.destination_iso2)
    home_profile = get_profile_or_fallback(input_.home_base_iso2)

    assumptions: list[str] = [
        f"Home base: {input_.home_base_iso2.upper()} ({home_profile.name})",
        f"Destination: {input_.destination_iso2.upper()} ({dest_profile.name})",
        f"Mode: {input_.mode.value}",
        f"Crew: {input_.crew.total_traveling()} traveling, {input_.crew.local_btl_count} local hires",
        f"Shoot days: {input_.crew.shoot_days}",
        f"Total budget: ${input_.budget.total_budget_usd:,.0f}",
        f"Business class fares: ATL={'yes' if input_.crew.atl_business_class else 'no'}, "
        f"Dept heads={'yes' if input_.crew.dept_head_business_class else 'no'}",
        "Airfare: deterministic static fare tables (no live API)",
        "All USD values at 2024-2025 reference rates",
    ]
    unknowns: list[str] = []

    if dest_profile.confidence == "LOW":
        unknowns.append(
            f"No verified benchmark data for {input_.destination_iso2}; "
            f"estimates derived from regional proxy. Manual verification recommended."
        )
    if dest_profile.notes:
        assumptions.append(f"Profile notes: {dest_profile.notes}")

    if input_.mode == AdjustmentMode.GREENFIELD:
        items = _compute_all_items_for_profile(dest_profile, home_profile, input_, input_.toggles)
        return _build_result_from_items(items, input_, dest_profile, None, assumptions, unknowns)

    # EXISTING_BUDGET mode
    if not input_.existing_budget_iso2:
        raise ValueError("existing_budget_iso2 is required for EXISTING_BUDGET mode")

    existing_profile = get_profile_or_fallback(input_.existing_budget_iso2)
    assumptions.append(
        f"Existing budget jurisdiction: {input_.existing_budget_iso2.upper()} ({existing_profile.name})"
    )

    # Regression constraint: same jurisdiction → all deltas = 0
    if input_.destination_iso2.upper() == input_.existing_budget_iso2.upper():
        assumptions.append(
            "Destination == existing budget jurisdiction: all cost deltas are zero (no double-counting)."
        )
        return ProductionAdjustmentResult(
            calculator_version=CALCULATOR_VERSION,
            mode=input_.mode,
            destination_iso2=input_.destination_iso2.upper(),
            existing_budget_iso2=input_.existing_budget_iso2.upper(),
            home_base_iso2=input_.home_base_iso2.upper(),
            total_adjustment_usd=0.0,
            total_calculated_usd=0.0,
            total_excluded_usd=0.0,
            airfare_usd=0.0, hotel_usd=0.0, per_diem_usd=0.0,
            freight_carnet_usd=0.0, visa_work_permit_usd=0.0, payroll_fringe_usd=0.0,
            local_transport_usd=0.0, legal_accounting_usd=0.0, local_hire_premium_usd=0.0,
            equipment_usd=0.0, stage_facility_usd=0.0, contingency_usd=0.0, fx_usd=0.0,
            line_items=[],
            assumptions=assumptions,
            unknowns=unknowns,
            exclusion_notes=[],
            confidence="HIGH",
            destination_profile_confidence=dest_profile.confidence,
        )

    dest_items = _compute_all_items_for_profile(dest_profile, home_profile, input_, input_.toggles)
    # Compute base items WITHOUT toggle filtering (we need raw values for delta)
    base_toggles = AdjustmentToggles()  # all enabled for baseline
    base_items = _compute_all_items_for_profile(existing_profile, home_profile, input_, base_toggles)

    delta = _delta_items(dest_items, base_items)
    return _build_result_from_items(delta, input_, dest_profile, existing_profile, assumptions, unknowns)
