"""
travel_model.py — Phase F6: LA Travel cost model for production incentive decisions.

Deterministic static fare tables. No live scraping, no API calls.
Pure Python, no DB access.
"""
from __future__ import annotations

from dataclasses import dataclass

MODEL_VERSION = "F6.1.0"


@dataclass
class TravelCostEstimate:
    home_base: str
    destination_jurisdiction: str
    business_class_seats: int
    premium_economy_seats: int
    economy_seats: int
    travel_frequency_per_year: int
    hotel_nights: int
    per_diem_days: int
    total_airfare_usd: float
    total_hotel_usd: float
    total_per_diem_usd: float
    total_travel_cost_usd: float
    incentive_value_usd: float
    net_incentive_after_travel_usd: float
    travel_cost_as_pct_of_incentive: float
    recommendation: str


# ---------------------------------------------------------------------------
# Fare tables
# ---------------------------------------------------------------------------

_BASE_FARES_USD: dict[tuple[str, str], float] = {
    ("LA", "GB"): 4500,
    ("LA", "IE"): 4800,
    ("LA", "FR"): 4200,
    ("LA", "DE"): 4300,
    ("LA", "AU"): 6500,
    ("LA", "CA"): 800,
    ("LA", "NZ"): 7200,
    ("LA", "JP"): 4800,
    ("LA", "KR"): 4600,
    ("NYC", "GB"): 3800,
    ("NYC", "IE"): 4000,
    ("NYC", "FR"): 3600,
    ("NYC", "CA"): 600,
    ("London", "FR"): 600,
    ("London", "DE"): 700,
    ("London", "AU"): 5500,
    ("Toronto", "GB"): 3200,
    ("Toronto", "FR"): 3400,
    ("Toronto", "IE"): 3500,
    ("LA", "HU"): 4100,
    ("LA", "CZ"): 4200,
    ("LA", "MT"): 4600,
    ("LA", "GR"): 4400,
    ("LA", "IT"): 4300,
    ("LA", "ES"): 4000,
    ("LA", "BE"): 4100,
    ("LA", "NL"): 4000,
    ("LA", "SE"): 4200,
    ("LA", "NO"): 4300,
    ("LA", "PL"): 4200,
    ("LA", "RS"): 4500,
    ("LA", "ZA"): 6000,
    ("LA", "AE"): 5200,
    ("LA", "IL"): 5000,
    ("LA", "MA"): 4800,
    ("LA", "MX"): 800,
    ("LA", "BR"): 3200,
    ("NYC", "AU"): 7500,
    ("NYC", "DE"): 3800,
    ("NYC", "IT"): 3500,
    ("NYC", "HU"): 3800,
    ("NYC", "MT"): 4200,
    ("NYC", "GR"): 4000,
}

_HOTEL_RATES_USD: dict[str, float] = {
    "GB": 350, "IE": 280, "FR": 320, "DE": 260, "AU": 300,
    "CA": 220, "NZ": 240, "JP": 280, "KR": 240, "US": 250,
    "MT": 180, "HU": 160, "CZ": 150, "PL": 140, "RS": 130,
    "IT": 250, "ES": 200, "GR": 200, "BE": 240, "NL": 270,
    "AT": 220, "SE": 280, "NO": 350, "FI": 270, "DK": 300,
    "PT": 180, "RO": 120, "BG": 100, "HR": 150,
    "ZA": 150, "MA": 140, "AE": 320, "IL": 250,
    "TH": 150, "SG": 350,
    "MX": 150, "BR": 180, "AR": 120, "CL": 150,
}

_PER_DIEM_USD: dict[str, float] = {
    "GB": 120, "IE": 110, "FR": 115, "DE": 105, "AU": 100,
    "CA": 90, "NZ": 95, "JP": 120, "KR": 100, "US": 95,
    "MT": 80, "HU": 70, "CZ": 65, "PL": 60, "RS": 55,
    "IT": 105, "ES": 95, "GR": 90, "BE": 100, "NL": 105,
    "AT": 100, "SE": 110, "NO": 130, "FI": 100, "DK": 120,
    "PT": 80, "RO": 55, "BG": 50, "HR": 65,
    "ZA": 65, "MA": 60, "AE": 120, "IL": 110,
    "TH": 65, "SG": 110,
    "MX": 65, "BR": 75, "AR": 50, "CL": 70,
}

_CABIN_MULTIPLIERS: dict[str, float] = {
    "business": 1.0,
    "premium_economy": 0.45,
    "economy": 0.25,
}


def _get_fare(home_base: str, destination: str) -> float:
    fare = _BASE_FARES_USD.get((home_base, destination))
    if fare:
        return fare
    fare = _BASE_FARES_USD.get((destination, home_base))
    if fare:
        return fare
    intercontinental_defaults = {
        "AU": 6500, "NZ": 7200, "JP": 4800, "KR": 4600,
        "ZA": 6000, "AE": 5200, "IL": 5000,
    }
    if destination in intercontinental_defaults:
        return intercontinental_defaults[destination]
    return 4200.0


def estimate_travel_cost(
    home_base: str = "LA",
    destination_jurisdiction: str = "GB",
    business_class_seats: int = 1,
    premium_economy_seats: int = 0,
    economy_seats: int = 0,
    travel_frequency_per_year: int = 4,
    hotel_nights: int = 14,
    per_diem_days: int = 14,
    incentive_value_usd: float = 0.0,
) -> TravelCostEstimate:
    """
    Estimate travel costs for international production trips.

    Args:
        home_base: Origin city code ("LA", "NYC", "London", "Toronto")
        destination_jurisdiction: Country code ("GB", "IE", "FR", etc.)
        business_class_seats: Number of business class seats per trip
        premium_economy_seats: Number of premium economy seats per trip
        economy_seats: Number of economy seats per trip
        travel_frequency_per_year: Number of trips per year
        hotel_nights: Total hotel nights across all trips combined
        per_diem_days: Total per diem days across all trips combined
        incentive_value_usd: Expected incentive value to compare against

    Returns:
        TravelCostEstimate with full cost breakdown and net incentive
    """
    base_fare = _get_fare(home_base, destination_jurisdiction)
    hotel_rate = _HOTEL_RATES_USD.get(destination_jurisdiction, 200.0)
    per_diem_rate = _PER_DIEM_USD.get(destination_jurisdiction, 80.0)

    # Round trip = base_fare * 2
    rt_business = base_fare * 2 * _CABIN_MULTIPLIERS["business"]
    rt_premium = base_fare * 2 * _CABIN_MULTIPLIERS["premium_economy"]
    rt_economy = base_fare * 2 * _CABIN_MULTIPLIERS["economy"]

    total_airfare = (
        business_class_seats * rt_business
        + premium_economy_seats * rt_premium
        + economy_seats * rt_economy
    ) * travel_frequency_per_year

    total_hotel = hotel_nights * hotel_rate
    total_per_diem = per_diem_days * per_diem_rate
    total_travel = total_airfare + total_hotel + total_per_diem

    net_incentive = incentive_value_usd - total_travel
    travel_pct = (total_travel / incentive_value_usd) if incentive_value_usd > 0 else 0.0

    if incentive_value_usd == 0:
        recommendation = "Enter expected incentive value to see net return."
    elif travel_pct < 0.05:
        recommendation = "Excellent ROI: travel costs are less than 5% of incentive value."
    elif travel_pct < 0.15:
        recommendation = "Good ROI: travel costs are under 15% of incentive value."
    elif travel_pct < 0.30:
        recommendation = "Acceptable ROI: consider reducing trip frequency or combining trips."
    elif travel_pct < 0.50:
        recommendation = "Marginal ROI: optimize crew size and trip duration."
    else:
        recommendation = "Poor ROI: travel costs exceed 50% of incentive. Review necessity."

    return TravelCostEstimate(
        home_base=home_base,
        destination_jurisdiction=destination_jurisdiction,
        business_class_seats=business_class_seats,
        premium_economy_seats=premium_economy_seats,
        economy_seats=economy_seats,
        travel_frequency_per_year=travel_frequency_per_year,
        hotel_nights=hotel_nights,
        per_diem_days=per_diem_days,
        total_airfare_usd=total_airfare,
        total_hotel_usd=total_hotel,
        total_per_diem_usd=total_per_diem,
        total_travel_cost_usd=total_travel,
        incentive_value_usd=incentive_value_usd,
        net_incentive_after_travel_usd=net_incentive,
        travel_cost_as_pct_of_incentive=travel_pct,
        recommendation=recommendation,
    )


def estimate_net_incentive_after_travel(
    incentive_value_usd: float,
    home_base: str = "LA",
    destination_jurisdiction: str = "GB",
    business_class_seats: int = 2,
    travel_frequency_per_year: int = 4,
    hotel_nights: int = 14,
    per_diem_days: int = 14,
) -> float:
    """Returns net incentive after subtracting estimated travel costs."""
    est = estimate_travel_cost(
        home_base=home_base,
        destination_jurisdiction=destination_jurisdiction,
        business_class_seats=business_class_seats,
        travel_frequency_per_year=travel_frequency_per_year,
        hotel_nights=hotel_nights,
        per_diem_days=per_diem_days,
        incentive_value_usd=incentive_value_usd,
    )
    return est.net_incentive_after_travel_usd
