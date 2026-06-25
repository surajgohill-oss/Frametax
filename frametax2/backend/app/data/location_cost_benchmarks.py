"""
location_cost_benchmarks.py

Static per-jurisdiction cost profiles for production adjustment calculations.

All values are in USD at 2024-2025 reference rates.
Crew rate index: 1.0 = Los Angeles baseline.
Equipment/stage index: 1.0 = Los Angeles baseline.
No live API calls. No DB access. Pure static data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

BENCHMARK_VERSION = "1.0.0"


@dataclass
class JurisdictionCostProfile:
    iso2: str
    name: str
    region: str

    # Airfare from LAX (business class, one-way USD)
    airfare_lax_business_usd: float
    airfare_lax_economy_usd: float
    # Delta vs LAX for JFK departures (negative = JFK is cheaper)
    airfare_jfk_delta_usd: float

    # Accommodation
    hotel_rate_usd: float           # per night, production-grade
    apartment_monthly_usd: float    # per unit/month for long shoots

    # Per diem (daily all-inclusive)
    per_diem_atl_usd: float         # above-the-line
    per_diem_btl_usd: float         # below-the-line

    # Cost indices (1.0 = LA baseline)
    crew_rate_index: float
    equipment_rental_index: float
    stage_facility_index: float
    post_production_index: float
    vfx_index: float

    # Per person per-production costs
    work_permit_cost_usd: float
    visa_cost_usd: float

    # Local transport (van/car per shoot day)
    local_transport_daily_usd: float

    # Freight / carnet (% of equipment value shipped)
    freight_carnet_pct: float

    # Payroll and legal (% of relevant base)
    payroll_fringe_pct: float       # employer social charges on gross wages
    payroll_overhead_pct: float     # processing, HR, compliance overhead
    legal_accounting_index: float   # multiplier vs LA baseline

    # Local hire minimum requirement (% of BTL crew headcount)
    local_hire_min_pct: float

    # Catering / craft services (per person per shoot day)
    catering_daily_usd: float

    # Risk parameters
    fx_risk_pct: float              # currency volatility add-on
    contingency_adj_pct: float      # extra contingency above standard (delta)
    schedule_risk_multiplier: float # 1.0 = no additional risk

    # Metadata
    confidence: str = "HIGH"        # HIGH / MEDIUM / LOW
    notes: str = ""
    data_sources: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Static benchmark data
# ---------------------------------------------------------------------------
# fmt: off
_RAW_PROFILES: list[dict] = [
    # ------------------------------------------------------------------ USA
    {
        "iso2": "US", "name": "United States (LA)", "region": "north_america",
        "airfare_lax_business_usd": 0, "airfare_lax_economy_usd": 0,
        "airfare_jfk_delta_usd": 0,
        "hotel_rate_usd": 250, "apartment_monthly_usd": 4500,
        "per_diem_atl_usd": 160, "per_diem_btl_usd": 95,
        "crew_rate_index": 1.00, "equipment_rental_index": 1.00,
        "stage_facility_index": 1.00, "post_production_index": 1.00, "vfx_index": 1.00,
        "work_permit_cost_usd": 0, "visa_cost_usd": 0,
        "local_transport_daily_usd": 180,
        "freight_carnet_pct": 0.00,
        "payroll_fringe_pct": 25.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 1.00,
        "local_hire_min_pct": 0.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 0.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH", "notes": "LA baseline; domestic shoots require no travel cost delta",
    },
    # ------------------------------------------------------------------ Canada
    {
        "iso2": "CA", "name": "Canada (Vancouver/Toronto)", "region": "north_america",
        "airfare_lax_business_usd": 2400, "airfare_lax_economy_usd": 600,
        "airfare_jfk_delta_usd": -200,
        "hotel_rate_usd": 220, "apartment_monthly_usd": 3200,
        "per_diem_atl_usd": 140, "per_diem_btl_usd": 90,
        "crew_rate_index": 0.85, "equipment_rental_index": 0.88,
        "stage_facility_index": 0.82, "post_production_index": 0.82, "vfx_index": 0.80,
        "work_permit_cost_usd": 800, "visa_cost_usd": 0,
        "local_transport_daily_usd": 160,
        "freight_carnet_pct": 0.5,
        "payroll_fringe_pct": 20.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 48,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Mexico
    {
        "iso2": "MX", "name": "Mexico", "region": "latin_america",
        "airfare_lax_business_usd": 1800, "airfare_lax_economy_usd": 450,
        "airfare_jfk_delta_usd": 200,
        "hotel_rate_usd": 150, "apartment_monthly_usd": 1800,
        "per_diem_atl_usd": 110, "per_diem_btl_usd": 65,
        "crew_rate_index": 0.45, "equipment_rental_index": 0.60,
        "stage_facility_index": 0.55, "post_production_index": 0.50, "vfx_index": 0.45,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 90,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 28.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.70,
        "local_hire_min_pct": 80.0,
        "catering_daily_usd": 28,
        "fx_risk_pct": 4.0, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ United Kingdom
    {
        "iso2": "GB", "name": "United Kingdom", "region": "western_europe",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 350, "apartment_monthly_usd": 5000,
        "per_diem_atl_usd": 200, "per_diem_btl_usd": 120,
        "crew_rate_index": 0.80, "equipment_rental_index": 0.82,
        "stage_facility_index": 0.78, "post_production_index": 0.80, "vfx_index": 0.78,
        "work_permit_cost_usd": 1200, "visa_cost_usd": 130,
        "local_transport_daily_usd": 200,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 18.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.95,
        "local_hire_min_pct": 100.0,
        "catering_daily_usd": 60,
        "fx_risk_pct": 2.5, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Ireland
    {
        "iso2": "IE", "name": "Ireland", "region": "western_europe",
        "airfare_lax_business_usd": 5800, "airfare_lax_economy_usd": 1300,
        "airfare_jfk_delta_usd": -800,
        "hotel_rate_usd": 280, "apartment_monthly_usd": 4200,
        "per_diem_atl_usd": 175, "per_diem_btl_usd": 110,
        "crew_rate_index": 0.75, "equipment_rental_index": 0.78,
        "stage_facility_index": 0.72, "post_production_index": 0.75, "vfx_index": 0.73,
        "work_permit_cost_usd": 700, "visa_cost_usd": 0,
        "local_transport_daily_usd": 175,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 15.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 80.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ France
    {
        "iso2": "FR", "name": "France", "region": "western_europe",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 320, "apartment_monthly_usd": 4500,
        "per_diem_atl_usd": 180, "per_diem_btl_usd": 115,
        "crew_rate_index": 0.80, "equipment_rental_index": 0.82,
        "stage_facility_index": 0.80, "post_production_index": 0.82, "vfx_index": 0.80,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 180,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 45.0, "payroll_overhead_pct": 4.5, "legal_accounting_index": 0.92,
        "local_hire_min_pct": 80.0,
        "catering_daily_usd": 65,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Germany
    {
        "iso2": "DE", "name": "Germany", "region": "western_europe",
        "airfare_lax_business_usd": 5300, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 260, "apartment_monthly_usd": 3800,
        "per_diem_atl_usd": 165, "per_diem_btl_usd": 105,
        "crew_rate_index": 0.78, "equipment_rental_index": 0.80,
        "stage_facility_index": 0.78, "post_production_index": 0.78, "vfx_index": 0.76,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 165,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 21.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Italy
    {
        "iso2": "IT", "name": "Italy", "region": "western_europe",
        "airfare_lax_business_usd": 5400, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 280, "apartment_monthly_usd": 3200,
        "per_diem_atl_usd": 165, "per_diem_btl_usd": 105,
        "crew_rate_index": 0.72, "equipment_rental_index": 0.74,
        "stage_facility_index": 0.70, "post_production_index": 0.72, "vfx_index": 0.70,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 165,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 32.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.85,
        "local_hire_min_pct": 75.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Spain
    {
        "iso2": "ES", "name": "Spain", "region": "western_europe",
        "airfare_lax_business_usd": 5000, "airfare_lax_economy_usd": 1050,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 220, "apartment_monthly_usd": 2800,
        "per_diem_atl_usd": 150, "per_diem_btl_usd": 95,
        "crew_rate_index": 0.65, "equipment_rental_index": 0.68,
        "stage_facility_index": 0.65, "post_production_index": 0.67, "vfx_index": 0.65,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 150,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 30.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.82,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 45,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Portugal
    {
        "iso2": "PT", "name": "Portugal", "region": "western_europe",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -800,
        "hotel_rate_usd": 180, "apartment_monthly_usd": 2200,
        "per_diem_atl_usd": 140, "per_diem_btl_usd": 80,
        "crew_rate_index": 0.58, "equipment_rental_index": 0.62,
        "stage_facility_index": 0.58, "post_production_index": 0.60, "vfx_index": 0.58,
        "work_permit_cost_usd": 450, "visa_cost_usd": 0,
        "local_transport_daily_usd": 130,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 23.5, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.78,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 38,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Netherlands
    {
        "iso2": "NL", "name": "Netherlands", "region": "western_europe",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 270, "apartment_monthly_usd": 4000,
        "per_diem_atl_usd": 165, "per_diem_btl_usd": 105,
        "crew_rate_index": 0.75, "equipment_rental_index": 0.78,
        "stage_facility_index": 0.75, "post_production_index": 0.78, "vfx_index": 0.76,
        "work_permit_cost_usd": 550, "visa_cost_usd": 0,
        "local_transport_daily_usd": 165,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 18.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Belgium
    {
        "iso2": "BE", "name": "Belgium", "region": "western_europe",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 240, "apartment_monthly_usd": 3500,
        "per_diem_atl_usd": 158, "per_diem_btl_usd": 100,
        "crew_rate_index": 0.73, "equipment_rental_index": 0.76,
        "stage_facility_index": 0.72, "post_production_index": 0.74, "vfx_index": 0.72,
        "work_permit_cost_usd": 550, "visa_cost_usd": 0,
        "local_transport_daily_usd": 160,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 35.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.88,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 52,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Austria
    {
        "iso2": "AT", "name": "Austria", "region": "western_europe",
        "airfare_lax_business_usd": 5300, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 220, "apartment_monthly_usd": 3200,
        "per_diem_atl_usd": 155, "per_diem_btl_usd": 100,
        "crew_rate_index": 0.78, "equipment_rental_index": 0.80,
        "stage_facility_index": 0.76, "post_production_index": 0.78, "vfx_index": 0.76,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 155,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 22.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.88,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 50,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Switzerland
    {
        "iso2": "CH", "name": "Switzerland", "region": "western_europe",
        "airfare_lax_business_usd": 5400, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 450, "apartment_monthly_usd": 6000,
        "per_diem_atl_usd": 220, "per_diem_btl_usd": 145,
        "crew_rate_index": 1.10, "equipment_rental_index": 1.05,
        "stage_facility_index": 1.05, "post_production_index": 1.05, "vfx_index": 1.02,
        "work_permit_cost_usd": 900, "visa_cost_usd": 0,
        "local_transport_daily_usd": 220,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 13.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 1.10,
        "local_hire_min_pct": 60.0,
        "catering_daily_usd": 75,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.00,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Sweden
    {
        "iso2": "SE", "name": "Sweden", "region": "northern_europe",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 280, "apartment_monthly_usd": 3800,
        "per_diem_atl_usd": 175, "per_diem_btl_usd": 110,
        "crew_rate_index": 0.78, "equipment_rental_index": 0.80,
        "stage_facility_index": 0.76, "post_production_index": 0.78, "vfx_index": 0.76,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 175,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 31.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 60,
        "fx_risk_pct": 2.5, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Norway
    {
        "iso2": "NO", "name": "Norway", "region": "northern_europe",
        "airfare_lax_business_usd": 5600, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 380, "apartment_monthly_usd": 5000,
        "per_diem_atl_usd": 210, "per_diem_btl_usd": 130,
        "crew_rate_index": 0.90, "equipment_rental_index": 0.88,
        "stage_facility_index": 0.85, "post_production_index": 0.86, "vfx_index": 0.82,
        "work_permit_cost_usd": 700, "visa_cost_usd": 0,
        "local_transport_daily_usd": 200,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 14.1, "payroll_overhead_pct": 3.5, "legal_accounting_index": 1.00,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 70,
        "fx_risk_pct": 2.5, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Denmark
    {
        "iso2": "DK", "name": "Denmark", "region": "northern_europe",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 300, "apartment_monthly_usd": 4200,
        "per_diem_atl_usd": 190, "per_diem_btl_usd": 120,
        "crew_rate_index": 0.82, "equipment_rental_index": 0.82,
        "stage_facility_index": 0.80, "post_production_index": 0.80, "vfx_index": 0.78,
        "work_permit_cost_usd": 650, "visa_cost_usd": 0,
        "local_transport_daily_usd": 185,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 4.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.92,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 62,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.0, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Finland
    {
        "iso2": "FI", "name": "Finland", "region": "northern_europe",
        "airfare_lax_business_usd": 5600, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": -700,
        "hotel_rate_usd": 270, "apartment_monthly_usd": 3500,
        "per_diem_atl_usd": 165, "per_diem_btl_usd": 100,
        "crew_rate_index": 0.76, "equipment_rental_index": 0.78,
        "stage_facility_index": 0.74, "post_production_index": 0.76, "vfx_index": 0.74,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 165,
        "freight_carnet_pct": 1.0,
        "payroll_fringe_pct": 19.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.90,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 55,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Hungary
    {
        "iso2": "HU", "name": "Hungary", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5100, "airfare_lax_economy_usd": 1050,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 160, "apartment_monthly_usd": 1800,
        "per_diem_atl_usd": 120, "per_diem_btl_usd": 70,
        "crew_rate_index": 0.42, "equipment_rental_index": 0.55,
        "stage_facility_index": 0.50, "post_production_index": 0.48, "vfx_index": 0.45,
        "work_permit_cost_usd": 300, "visa_cost_usd": 0,
        "local_transport_daily_usd": 100,
        "freight_carnet_pct": 1.2,
        "payroll_fringe_pct": 20.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.70,
        "local_hire_min_pct": 60.0,
        "catering_daily_usd": 28,
        "fx_risk_pct": 4.0, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.03,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Czech Republic
    {
        "iso2": "CZ", "name": "Czech Republic", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1050,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 150, "apartment_monthly_usd": 1700,
        "per_diem_atl_usd": 118, "per_diem_btl_usd": 65,
        "crew_rate_index": 0.45, "equipment_rental_index": 0.58,
        "stage_facility_index": 0.52, "post_production_index": 0.50, "vfx_index": 0.48,
        "work_permit_cost_usd": 250, "visa_cost_usd": 0,
        "local_transport_daily_usd": 95,
        "freight_carnet_pct": 1.2,
        "payroll_fringe_pct": 35.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.68,
        "local_hire_min_pct": 50.0,
        "catering_daily_usd": 26,
        "fx_risk_pct": 3.5, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Poland
    {
        "iso2": "PL", "name": "Poland", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5300, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 140, "apartment_monthly_usd": 1500,
        "per_diem_atl_usd": 110, "per_diem_btl_usd": 60,
        "crew_rate_index": 0.40, "equipment_rental_index": 0.52,
        "stage_facility_index": 0.48, "post_production_index": 0.45, "vfx_index": 0.43,
        "work_permit_cost_usd": 280, "visa_cost_usd": 0,
        "local_transport_daily_usd": 88,
        "freight_carnet_pct": 1.2,
        "payroll_fringe_pct": 21.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 55.0,
        "catering_daily_usd": 24,
        "fx_risk_pct": 3.5, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Romania
    {
        "iso2": "RO", "name": "Romania", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 120, "apartment_monthly_usd": 1200,
        "per_diem_atl_usd": 100, "per_diem_btl_usd": 55,
        "crew_rate_index": 0.32, "equipment_rental_index": 0.45,
        "stage_facility_index": 0.42, "post_production_index": 0.40, "vfx_index": 0.38,
        "work_permit_cost_usd": 200, "visa_cost_usd": 0,
        "local_transport_daily_usd": 75,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 22.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.60,
        "local_hire_min_pct": 50.0,
        "catering_daily_usd": 20,
        "fx_risk_pct": 4.0, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Bulgaria
    {
        "iso2": "BG", "name": "Bulgaria", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5600, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 100, "apartment_monthly_usd": 1000,
        "per_diem_atl_usd": 90, "per_diem_btl_usd": 50,
        "crew_rate_index": 0.30, "equipment_rental_index": 0.42,
        "stage_facility_index": 0.38, "post_production_index": 0.36, "vfx_index": 0.34,
        "work_permit_cost_usd": 200, "visa_cost_usd": 0,
        "local_transport_daily_usd": 70,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 19.5, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.58,
        "local_hire_min_pct": 45.0,
        "catering_daily_usd": 18,
        "fx_risk_pct": 4.0, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Serbia
    {
        "iso2": "RS", "name": "Serbia", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 130, "apartment_monthly_usd": 1200,
        "per_diem_atl_usd": 100, "per_diem_btl_usd": 55,
        "crew_rate_index": 0.35, "equipment_rental_index": 0.45,
        "stage_facility_index": 0.40, "post_production_index": 0.38, "vfx_index": 0.36,
        "work_permit_cost_usd": 250, "visa_cost_usd": 0,
        "local_transport_daily_usd": 80,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 20.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.60,
        "local_hire_min_pct": 45.0,
        "catering_daily_usd": 22,
        "fx_risk_pct": 4.5, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Croatia
    {
        "iso2": "HR", "name": "Croatia", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5400, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 150, "apartment_monthly_usd": 1600,
        "per_diem_atl_usd": 108, "per_diem_btl_usd": 65,
        "crew_rate_index": 0.38, "equipment_rental_index": 0.48,
        "stage_facility_index": 0.44, "post_production_index": 0.42, "vfx_index": 0.40,
        "work_permit_cost_usd": 280, "visa_cost_usd": 0,
        "local_transport_daily_usd": 90,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 18.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.62,
        "local_hire_min_pct": 50.0,
        "catering_daily_usd": 25,
        "fx_risk_pct": 3.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Malta
    {
        "iso2": "MT", "name": "Malta", "region": "southern_europe",
        "airfare_lax_business_usd": 5600, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 180, "apartment_monthly_usd": 2200,
        "per_diem_atl_usd": 130, "per_diem_btl_usd": 80,
        "crew_rate_index": 0.60, "equipment_rental_index": 0.65,
        "stage_facility_index": 0.62, "post_production_index": 0.60, "vfx_index": 0.58,
        "work_permit_cost_usd": 350, "visa_cost_usd": 0,
        "local_transport_daily_usd": 120,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 10.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.72,
        "local_hire_min_pct": 30.0,
        "catering_daily_usd": 30,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Greece
    {
        "iso2": "GR", "name": "Greece", "region": "southern_europe",
        "airfare_lax_business_usd": 5400, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 200, "apartment_monthly_usd": 2200,
        "per_diem_atl_usd": 135, "per_diem_btl_usd": 90,
        "crew_rate_index": 0.60, "equipment_rental_index": 0.63,
        "stage_facility_index": 0.58, "post_production_index": 0.58, "vfx_index": 0.55,
        "work_permit_cost_usd": 400, "visa_cost_usd": 0,
        "local_transport_daily_usd": 130,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 24.5, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.75,
        "local_hire_min_pct": 55.0,
        "catering_daily_usd": 32,
        "fx_risk_pct": 2.5, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Slovenia
    {
        "iso2": "SI", "name": "Slovenia", "region": "central_eastern_europe",
        "airfare_lax_business_usd": 5400, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -650,
        "hotel_rate_usd": 160, "apartment_monthly_usd": 1800,
        "per_diem_atl_usd": 118, "per_diem_btl_usd": 68,
        "crew_rate_index": 0.52, "equipment_rental_index": 0.60,
        "stage_facility_index": 0.55, "post_production_index": 0.52, "vfx_index": 0.50,
        "work_permit_cost_usd": 300, "visa_cost_usd": 0,
        "local_transport_daily_usd": 100,
        "freight_carnet_pct": 1.2,
        "payroll_fringe_pct": 22.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.70,
        "local_hire_min_pct": 50.0,
        "catering_daily_usd": 26,
        "fx_risk_pct": 2.5, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Australia
    {
        "iso2": "AU", "name": "Australia", "region": "asia_pacific",
        "airfare_lax_business_usd": 7500, "airfare_lax_economy_usd": 1600,
        "airfare_jfk_delta_usd": 400,
        "hotel_rate_usd": 300, "apartment_monthly_usd": 4000,
        "per_diem_atl_usd": 170, "per_diem_btl_usd": 100,
        "crew_rate_index": 0.82, "equipment_rental_index": 0.85,
        "stage_facility_index": 0.80, "post_production_index": 0.82, "vfx_index": 0.80,
        "work_permit_cost_usd": 900, "visa_cost_usd": 230,
        "local_transport_daily_usd": 180,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 11.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.88,
        "local_hire_min_pct": 75.0,
        "catering_daily_usd": 50,
        "fx_risk_pct": 3.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ New Zealand
    {
        "iso2": "NZ", "name": "New Zealand", "region": "asia_pacific",
        "airfare_lax_business_usd": 8500, "airfare_lax_economy_usd": 1800,
        "airfare_jfk_delta_usd": 600,
        "hotel_rate_usd": 240, "apartment_monthly_usd": 3200,
        "per_diem_atl_usd": 155, "per_diem_btl_usd": 95,
        "crew_rate_index": 0.75, "equipment_rental_index": 0.78,
        "stage_facility_index": 0.72, "post_production_index": 0.74, "vfx_index": 0.72,
        "work_permit_cost_usd": 700, "visa_cost_usd": 0,
        "local_transport_daily_usd": 155,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 10.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.85,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 45,
        "fx_risk_pct": 3.5, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Japan
    {
        "iso2": "JP", "name": "Japan", "region": "asia_pacific",
        "airfare_lax_business_usd": 5800, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": 400,
        "hotel_rate_usd": 350, "apartment_monthly_usd": 4500,
        "per_diem_atl_usd": 185, "per_diem_btl_usd": 120,
        "crew_rate_index": 0.88, "equipment_rental_index": 0.88,
        "stage_facility_index": 0.86, "post_production_index": 0.85, "vfx_index": 0.84,
        "work_permit_cost_usd": 800, "visa_cost_usd": 0,
        "local_transport_daily_usd": 180,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 15.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.92,
        "local_hire_min_pct": 80.0,
        "catering_daily_usd": 60,
        "fx_risk_pct": 3.0, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.05,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ South Korea
    {
        "iso2": "KR", "name": "South Korea", "region": "asia_pacific",
        "airfare_lax_business_usd": 5600, "airfare_lax_economy_usd": 1150,
        "airfare_jfk_delta_usd": 400,
        "hotel_rate_usd": 260, "apartment_monthly_usd": 3500,
        "per_diem_atl_usd": 165, "per_diem_btl_usd": 100,
        "crew_rate_index": 0.70, "equipment_rental_index": 0.73,
        "stage_facility_index": 0.70, "post_production_index": 0.68, "vfx_index": 0.65,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 155,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 11.0, "payroll_overhead_pct": 3.5, "legal_accounting_index": 0.82,
        "local_hire_min_pct": 75.0,
        "catering_daily_usd": 45,
        "fx_risk_pct": 3.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.02,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Singapore
    {
        "iso2": "SG", "name": "Singapore", "region": "asia_pacific",
        "airfare_lax_business_usd": 6000, "airfare_lax_economy_usd": 1250,
        "airfare_jfk_delta_usd": 400,
        "hotel_rate_usd": 380, "apartment_monthly_usd": 5500,
        "per_diem_atl_usd": 190, "per_diem_btl_usd": 110,
        "crew_rate_index": 0.80, "equipment_rental_index": 0.82,
        "stage_facility_index": 0.78, "post_production_index": 0.78, "vfx_index": 0.75,
        "work_permit_cost_usd": 700, "visa_cost_usd": 0,
        "local_transport_daily_usd": 170,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 16.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.88,
        "local_hire_min_pct": 60.0,
        "catering_daily_usd": 52,
        "fx_risk_pct": 2.0, "contingency_adj_pct": 0.5, "schedule_risk_multiplier": 1.00,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Thailand
    {
        "iso2": "TH", "name": "Thailand", "region": "asia_pacific",
        "airfare_lax_business_usd": 5200, "airfare_lax_economy_usd": 1050,
        "airfare_jfk_delta_usd": 400,
        "hotel_rate_usd": 150, "apartment_monthly_usd": 2000,
        "per_diem_atl_usd": 120, "per_diem_btl_usd": 65,
        "crew_rate_index": 0.40, "equipment_rental_index": 0.52,
        "stage_facility_index": 0.48, "post_production_index": 0.45, "vfx_index": 0.42,
        "work_permit_cost_usd": 300, "visa_cost_usd": 50,
        "local_transport_daily_usd": 90,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 5.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 80.0,
        "catering_daily_usd": 20,
        "fx_risk_pct": 4.0, "contingency_adj_pct": 1.5, "schedule_risk_multiplier": 1.05,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ India
    {
        "iso2": "IN", "name": "India", "region": "asia_pacific",
        "airfare_lax_business_usd": 5800, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": 300,
        "hotel_rate_usd": 200, "apartment_monthly_usd": 2500,
        "per_diem_atl_usd": 140, "per_diem_btl_usd": 70,
        "crew_rate_index": 0.30, "equipment_rental_index": 0.40,
        "stage_facility_index": 0.38, "post_production_index": 0.35, "vfx_index": 0.30,
        "work_permit_cost_usd": 600, "visa_cost_usd": 80,
        "local_transport_daily_usd": 80,
        "freight_carnet_pct": 2.5,
        "payroll_fringe_pct": 12.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.60,
        "local_hire_min_pct": 90.0,
        "catering_daily_usd": 15,
        "fx_risk_pct": 5.0, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.10,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ UAE
    {
        "iso2": "AE", "name": "United Arab Emirates", "region": "middle_east",
        "airfare_lax_business_usd": 5800, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": 200,
        "hotel_rate_usd": 350, "apartment_monthly_usd": 5000,
        "per_diem_atl_usd": 190, "per_diem_btl_usd": 120,
        "crew_rate_index": 0.65, "equipment_rental_index": 0.72,
        "stage_facility_index": 0.68, "post_production_index": 0.65, "vfx_index": 0.62,
        "work_permit_cost_usd": 500, "visa_cost_usd": 100,
        "local_transport_daily_usd": 160,
        "freight_carnet_pct": 1.5,
        "payroll_fringe_pct": 0.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.80,
        "local_hire_min_pct": 20.0,
        "catering_daily_usd": 50,
        "fx_risk_pct": 1.5, "contingency_adj_pct": 1.0, "schedule_risk_multiplier": 1.03,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Israel
    {
        "iso2": "IL", "name": "Israel", "region": "middle_east",
        "airfare_lax_business_usd": 5800, "airfare_lax_economy_usd": 1200,
        "airfare_jfk_delta_usd": -200,
        "hotel_rate_usd": 280, "apartment_monthly_usd": 4000,
        "per_diem_atl_usd": 170, "per_diem_btl_usd": 110,
        "crew_rate_index": 0.75, "equipment_rental_index": 0.78,
        "stage_facility_index": 0.72, "post_production_index": 0.72, "vfx_index": 0.70,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 160,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 18.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.85,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 50,
        "fx_risk_pct": 5.0, "contingency_adj_pct": 3.0, "schedule_risk_multiplier": 1.15,
        "confidence": "MEDIUM",
        "notes": "Security risk contingency elevated",
    },
    # ------------------------------------------------------------------ Morocco
    {
        "iso2": "MA", "name": "Morocco", "region": "africa",
        "airfare_lax_business_usd": 5500, "airfare_lax_economy_usd": 1100,
        "airfare_jfk_delta_usd": -500,
        "hotel_rate_usd": 140, "apartment_monthly_usd": 1500,
        "per_diem_atl_usd": 105, "per_diem_btl_usd": 60,
        "crew_rate_index": 0.32, "equipment_rental_index": 0.42,
        "stage_facility_index": 0.40, "post_production_index": 0.38, "vfx_index": 0.35,
        "work_permit_cost_usd": 400, "visa_cost_usd": 0,
        "local_transport_daily_usd": 80,
        "freight_carnet_pct": 2.5,
        "payroll_fringe_pct": 18.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 50.0,
        "catering_daily_usd": 18,
        "fx_risk_pct": 5.0, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.08,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ South Africa
    {
        "iso2": "ZA", "name": "South Africa", "region": "africa",
        "airfare_lax_business_usd": 7000, "airfare_lax_economy_usd": 1500,
        "airfare_jfk_delta_usd": 200,
        "hotel_rate_usd": 180, "apartment_monthly_usd": 2000,
        "per_diem_atl_usd": 130, "per_diem_btl_usd": 65,
        "crew_rate_index": 0.45, "equipment_rental_index": 0.58,
        "stage_facility_index": 0.52, "post_production_index": 0.48, "vfx_index": 0.45,
        "work_permit_cost_usd": 600, "visa_cost_usd": 0,
        "local_transport_daily_usd": 110,
        "freight_carnet_pct": 2.5,
        "payroll_fringe_pct": 5.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.70,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 22,
        "fx_risk_pct": 7.0, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.08,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Mauritius (regression anchor)
    {
        "iso2": "MU", "name": "Mauritius", "region": "africa",
        "airfare_lax_business_usd": 8500, "airfare_lax_economy_usd": 1800,
        "airfare_jfk_delta_usd": 300,
        "hotel_rate_usd": 200, "apartment_monthly_usd": 2500,
        "per_diem_atl_usd": 140, "per_diem_btl_usd": 80,
        "crew_rate_index": 0.50, "equipment_rental_index": 0.65,
        "stage_facility_index": 0.55, "post_production_index": 0.50, "vfx_index": 0.48,
        "work_permit_cost_usd": 400, "visa_cost_usd": 0,
        "local_transport_daily_usd": 120,
        "freight_carnet_pct": 3.0,
        "payroll_fringe_pct": 6.0, "payroll_overhead_pct": 3.0, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 40.0,
        "catering_daily_usd": 28,
        "fx_risk_pct": 4.5, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.08,
        "confidence": "MEDIUM",
        "notes": "Regression anchor: Little Utopia existing-budget scenario",
    },
    # ------------------------------------------------------------------ Brazil
    {
        "iso2": "BR", "name": "Brazil", "region": "latin_america",
        "airfare_lax_business_usd": 4500, "airfare_lax_economy_usd": 950,
        "airfare_jfk_delta_usd": -300,
        "hotel_rate_usd": 200, "apartment_monthly_usd": 2200,
        "per_diem_atl_usd": 140, "per_diem_btl_usd": 75,
        "crew_rate_index": 0.50, "equipment_rental_index": 0.60,
        "stage_facility_index": 0.55, "post_production_index": 0.50, "vfx_index": 0.48,
        "work_permit_cost_usd": 700, "visa_cost_usd": 0,
        "local_transport_daily_usd": 110,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 45.0, "payroll_overhead_pct": 5.0, "legal_accounting_index": 0.80,
        "local_hire_min_pct": 70.0,
        "catering_daily_usd": 25,
        "fx_risk_pct": 6.0, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.10,
        "confidence": "HIGH",
    },
    # ------------------------------------------------------------------ Argentina
    {
        "iso2": "AR", "name": "Argentina", "region": "latin_america",
        "airfare_lax_business_usd": 4200, "airfare_lax_economy_usd": 900,
        "airfare_jfk_delta_usd": -400,
        "hotel_rate_usd": 120, "apartment_monthly_usd": 1200,
        "per_diem_atl_usd": 105, "per_diem_btl_usd": 50,
        "crew_rate_index": 0.35, "equipment_rental_index": 0.45,
        "stage_facility_index": 0.42, "post_production_index": 0.40, "vfx_index": 0.38,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 75,
        "freight_carnet_pct": 2.5,
        "payroll_fringe_pct": 25.0, "payroll_overhead_pct": 4.5, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 60.0,
        "catering_daily_usd": 18,
        "fx_risk_pct": 12.0, "contingency_adj_pct": 5.0, "schedule_risk_multiplier": 1.15,
        "confidence": "MEDIUM",
        "notes": "High FX volatility; significant contingency required",
    },
    # ------------------------------------------------------------------ Chile
    {
        "iso2": "CL", "name": "Chile", "region": "latin_america",
        "airfare_lax_business_usd": 4500, "airfare_lax_economy_usd": 950,
        "airfare_jfk_delta_usd": -300,
        "hotel_rate_usd": 160, "apartment_monthly_usd": 1800,
        "per_diem_atl_usd": 120, "per_diem_btl_usd": 70,
        "crew_rate_index": 0.45, "equipment_rental_index": 0.55,
        "stage_facility_index": 0.50, "post_production_index": 0.48, "vfx_index": 0.45,
        "work_permit_cost_usd": 500, "visa_cost_usd": 0,
        "local_transport_daily_usd": 95,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 22.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.70,
        "local_hire_min_pct": 60.0,
        "catering_daily_usd": 22,
        "fx_risk_pct": 5.0, "contingency_adj_pct": 2.0, "schedule_risk_multiplier": 1.08,
        "confidence": "MEDIUM",
    },
    # ------------------------------------------------------------------ Colombia
    {
        "iso2": "CO", "name": "Colombia", "region": "latin_america",
        "airfare_lax_business_usd": 3500, "airfare_lax_economy_usd": 750,
        "airfare_jfk_delta_usd": -300,
        "hotel_rate_usd": 140, "apartment_monthly_usd": 1500,
        "per_diem_atl_usd": 110, "per_diem_btl_usd": 60,
        "crew_rate_index": 0.38, "equipment_rental_index": 0.48,
        "stage_facility_index": 0.45, "post_production_index": 0.42, "vfx_index": 0.40,
        "work_permit_cost_usd": 450, "visa_cost_usd": 0,
        "local_transport_daily_usd": 85,
        "freight_carnet_pct": 2.0,
        "payroll_fringe_pct": 30.0, "payroll_overhead_pct": 4.0, "legal_accounting_index": 0.65,
        "local_hire_min_pct": 65.0,
        "catering_daily_usd": 20,
        "fx_risk_pct": 6.0, "contingency_adj_pct": 2.5, "schedule_risk_multiplier": 1.10,
        "confidence": "MEDIUM",
    },
]
# fmt: on

# ---------------------------------------------------------------------------
# Build lookup dict
# ---------------------------------------------------------------------------
_PROFILES: dict[str, JurisdictionCostProfile] = {}
for _raw in _RAW_PROFILES:
    _p = JurisdictionCostProfile(**_raw)
    _PROFILES[_p.iso2] = _p

# Regional fallbacks: map region → representative profile iso2
_REGION_FALLBACK: dict[str, str] = {
    "north_america": "CA",
    "western_europe": "MT",
    "northern_europe": "SE",
    "central_eastern_europe": "HU",
    "southern_europe": "GR",
    "asia_pacific": "TH",
    "middle_east": "AE",
    "africa": "MA",
    "latin_america": "CL",
}


def get_profile(iso2: str) -> Optional[JurisdictionCostProfile]:
    return _PROFILES.get(iso2.upper())


def get_profile_or_fallback(iso2: str, region: Optional[str] = None) -> JurisdictionCostProfile:
    p = _PROFILES.get(iso2.upper())
    if p:
        return p
    if region and region in _REGION_FALLBACK:
        fallback = _PROFILES[_REGION_FALLBACK[region]]
        return JurisdictionCostProfile(
            iso2=iso2.upper(),
            name=f"{iso2.upper()} (regional estimate)",
            region=region,
            **{
                k: getattr(fallback, k)
                for k in fallback.__dataclass_fields__
                if k not in ("iso2", "name", "region", "confidence", "notes", "data_sources")
            },
            confidence="LOW",
            notes=f"No benchmark data for {iso2}; using {fallback.name} as regional proxy",
            data_sources=[],
        )
    # Last resort: US baseline with penalty markers
    us = _PROFILES["US"]
    return JurisdictionCostProfile(
        iso2=iso2.upper(),
        name=f"{iso2.upper()} (unknown)",
        region="unknown",
        **{
            k: getattr(us, k)
            for k in us.__dataclass_fields__
            if k not in ("iso2", "name", "region", "confidence", "notes", "data_sources")
        },
        confidence="LOW",
        notes=f"No benchmark data for {iso2}; US values used as placeholder",
        data_sources=[],
    )


def list_supported_jurisdictions() -> list[str]:
    return sorted(_PROFILES.keys())
