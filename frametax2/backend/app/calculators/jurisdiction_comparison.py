"""
jurisdiction_comparison.py

Jurisdiction Comparison Engine — Phase 1.
Comparison profiles and scoring framework for marine/water-heavy production structuring.

Scope:
  Tier 1:  Mauritius, Malta, Greece, Cyprus
  Secondary Reference: UK (existing), Ireland, France, Italy, Spain, Croatia,
                       Hungary, Belgium, Germany

CONFIDENCE NOTES:
  All profiles are DISCOVERY or PARSED tier.
  No rates in this module should feed deterministic incentive calculations until
  promoted to VERIFIED via primary source review.
  Data gaps per jurisdiction are listed in each profile's .data_gaps field.

FRAMEWORK_VERSION tracks the scoring dimension schema, not the data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


FRAMEWORK_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Tier / Rating Constants  (not enums — extensible without migration)
# ---------------------------------------------------------------------------

class MarineSuitability:
    EXCELLENT = "excellent"  # Purpose-built water tanks + open water + established precedent
    STRONG    = "strong"     # Excellent open water + supporting marine infrastructure
    MODERATE  = "moderate"   # Open water available; limited film-specific marine infrastructure
    LIMITED   = "limited"    # Some access; no meaningful marine production history
    NONE      = "none"       # Landlocked or no usable marine access

VALID_MARINE_SUITABILITY = {
    MarineSuitability.EXCELLENT,
    MarineSuitability.STRONG,
    MarineSuitability.MODERATE,
    MarineSuitability.LIMITED,
    MarineSuitability.NONE,
}


class CrewDepth:
    DEEP    = "deep"    # 200+ shoot-day productions without heavy import required
    MEDIUM  = "medium"  # Mid-size productions workable; import needed at scale
    SHALLOW = "shallow" # Substantial BTL import required even for small productions

VALID_CREW_DEPTH = {CrewDepth.DEEP, CrewDepth.MEDIUM, CrewDepth.SHALLOW}


class FinancingFriction:
    LOW    = "low"    # Rebate assignable to gap lender; fast payment; mature film finance market
    MEDIUM = "medium" # Rebate exists; moderate bureaucratic delay; some financing options
    HIGH   = "high"   # Complex or slow program; limited financing ecosystem; structural uncertainty

VALID_FINANCING_FRICTION = {
    FinancingFriction.LOW,
    FinancingFriction.MEDIUM,
    FinancingFriction.HIGH,
}


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ComparisonDimension:
    key: str
    label: str
    description: str
    weight_default: float  # Must sum to 1.0 across all dimensions


@dataclass
class JurisdictionIncentiveProfile:
    """
    Raw comparison data for one jurisdiction's primary film incentive.

    No scores are computed here — this object is the input to the scoring engine
    (not yet built). All numeric rates are expressed as decimals (0.30 = 30%).

    Fields marked Optional[...] are genuinely unknown or unverified —
    do not substitute zero for None; they represent data gaps.
    """
    jurisdiction_code: str         # ISO 3166-1 alpha-2
    jurisdiction_name: str
    program_slug: str
    program_name: str
    confidence_tier: str           # ConfidenceTier string

    # --- Incentive Program ---
    incentive_type: str            # ProgramType string
    base_rate: Optional[float]     # None = unverified
    max_rate: Optional[float]      # With all uplifts
    is_refundable: Optional[bool]
    is_transferable: Optional[bool]  # Assignable to gap lender?
    annual_cap_local: Optional[float]  # Jurisdiction currency; None = uncapped or unknown
    min_spend_local: Optional[float]   # In jurisdiction currency; None = unknown
    requires_cultural_test: bool
    atl_qualifies: Optional[bool]
    btl_qualifies: Optional[bool]
    vfx_qualifies: Optional[bool]
    music_qualifies: Optional[bool]
    vessel_marine_qualifies: Optional[bool]  # Vessel charter / marine support costs
    resident_labor_uplift_available: bool
    cashflow_timing_weeks: Optional[int]  # Approx weeks from production end to receipt

    # --- Marine & Production Suitability ---
    marine_suitability: str     # MarineSuitability constant
    has_water_tanks: bool       # Purpose-built film water tanks
    has_open_water_filming: bool
    crew_depth_rating: str      # CrewDepth constant
    studio_available: bool
    post_production_available: bool

    # --- Financial / Structural ---
    vat_recoverable: Optional[bool]
    vat_rate_pct: Optional[float]
    withholding_tax_pct: Optional[float]   # WHT on cast/crew payments (typical; treaty may reduce)
    payroll_burden_pct: Optional[float]    # Employer social contributions approx
    financing_friction: str                # FinancingFriction constant

    # --- Authority & Metadata ---
    authority_name: str
    authority_url_hint: str  # May not be current; verify before use
    notes: str
    data_gaps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scoring Framework (dimensions only — no calculation)
# ---------------------------------------------------------------------------

SCORING_DIMENSIONS: list[ComparisonDimension] = [
    ComparisonDimension(
        key="net_producer_benefit",
        label="Net Producer Benefit",
        description=(
            "Effective cash return as a percentage of total spend after all caps, "
            "offsets, minimum spend hurdles, and transaction costs. "
            "Headline rate minus real-world friction. "
            "Key inputs: base_rate, max_rate, annual_cap_local, financing_friction."
        ),
        weight_default=0.30,
    ),
    ComparisonDimension(
        key="ease_of_qualification",
        label="Ease of Qualification",
        description=(
            "How straightforward the application process, cultural test (if any), "
            "minimum spend threshold, and entity structure requirements are "
            "relative to this production profile. "
            "Key inputs: requires_cultural_test, min_spend_local, is_competitive."
        ),
        weight_default=0.20,
    ),
    ComparisonDimension(
        key="marine_suitability",
        label="Marine & Water Suitability",
        description=(
            "Dedicated water tanks, open water access, marine logistics infrastructure, "
            "dive support, vessel charter market depth, and historical precedent for "
            "boat-heavy productions. "
            "Key inputs: marine_suitability, has_water_tanks, has_open_water_filming, "
            "vessel_marine_qualifies."
        ),
        weight_default=0.20,
    ),
    ComparisonDimension(
        key="crew_depth",
        label="Crew Depth",
        description=(
            "Availability of qualified BTL crew (camera, grip, electric, art, marine specialist) "
            "without large-scale import, reducing payroll friction and travel overhead. "
            "Key inputs: crew_depth_rating, studio_available."
        ),
        weight_default=0.15,
    ),
    ComparisonDimension(
        key="financing_efficiency",
        label="Financing Efficiency",
        description=(
            "Speed of rebate/credit receipt, assignability of incentive receivable to a gap lender, "
            "gap financing market availability, and overall cashflow predictability. "
            "Key inputs: cashflow_timing_weeks, is_transferable, financing_friction."
        ),
        weight_default=0.10,
    ),
    ComparisonDimension(
        key="operational_complexity",
        label="Operational Complexity",
        description=(
            "Regulatory burden, visa and work permit requirements, labor law compliance, "
            "language friction, and entity setup cost. "
            "Lower complexity produces a higher score. "
            "Key inputs: requires_cultural_test, payroll_burden_pct, withholding_tax_pct."
        ),
        weight_default=0.05,
    ),
]

assert abs(sum(d.weight_default for d in SCORING_DIMENSIONS) - 1.0) < 1e-9, (
    "Scoring dimension weights must sum to 1.0"
)


# ---------------------------------------------------------------------------
# Tier 1 Profiles
# ---------------------------------------------------------------------------

_MAURITIUS = JurisdictionIncentiveProfile(
    jurisdiction_code="MU",
    jurisdiction_name="Mauritius",
    program_slug="mu_edb_incentive",
    program_name="Mauritius EDB Production Incentive (Budget-Evidenced 35%)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.35,
    max_rate=0.35,
    is_refundable=None,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False,
    post_production_available=False,
    vat_recoverable=False,
    vat_rate_pct=0.15,
    withholding_tax_pct=None,
    payroll_burden_pct=0.09,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Economic Development Board Mauritius (EDB) / Mauritius Film Development Corp.",
    authority_url_hint="edbmauritius.org",
    notes=(
        "PARSED tier: base rate of 35% inferred from production budget evidence "
        "(budget line 'EDB Rebate at 35%: $(1,275,411)' applied to ~$3.64M QPE). "
        "This rate has NOT been verified against EDB statute text or primary source documentation. "
        "Promote to VERIFIED only after reviewing current EDB Film Production Incentive guidelines. "
        "Vessel and marine costs (charter, safety boats, underwater equipment) included in "
        "budget QPE per production team's Groups report — treated as qualifying BTL spend. "
        "VAT: Mauritius 15% VAT is non-recoverable for foreign film productions "
        "($92,439 confirmed embedded in gross budget; excluded from QPE). "
        "ATL qualifying scope unknown — director/producer/cast fee treatment not confirmed. "
        "Frogsquad (SA-based marine team): largest single QPE uncertainty; "
        "routing through Mauritius SPV vs. offshore SA entity swings qualifying spend by ~$72K-$100K. "
        "Finance cost on rebate receivable: $0 in budget but estimated $70K-$77K at 8%/9-month delay. "
        "Indian Ocean warm water, clear visibility — excellent for yacht and diving sequences. "
        "Limited local film crew base: effectively a full import production. "
        "SPV required to claim rebate — setup and compliance cost unquantified."
    ),
    data_gaps=[
        "Base rate of 35% not verified from EDB statute text — inferred from budget only",
        "ATL qualifying scope (director, producer, cast fees) unknown",
        "Frogsquad routing: SA offshore vs. Mauritius SPV — swings QPE by ~$72K-$100K",
        "Accommodation and per diem qualifying treatment not confirmed",
        "WHT on international cast/crew payments unverified",
        "Minimum spend threshold unknown",
        "Annual program budget/cap unknown",
        "Cashflow timing unknown — no confirmed processing SLA from EDB",
        "Rebate assignability to gap lender not confirmed",
        "Finance cost on rebate receivable not modeled in production budget",
        "SPV setup and compliance cost not estimated",
    ],
)

_MALTA = JurisdictionIncentiveProfile(
    jurisdiction_code="MT",
    jurisdiction_name="Malta",
    program_slug="mt_mfc_rebate",
    program_name="Malta Film Commission Cash Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=50_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=True,
    cashflow_timing_weeks=20,
    marine_suitability=MarineSuitability.EXCELLENT,
    has_water_tanks=True,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.18,
    withholding_tax_pct=0.0,
    payroll_burden_pct=0.10,
    financing_friction=FinancingFriction.LOW,
    authority_name="Malta Film Commission (MFC)",
    authority_url_hint="maltafilmcommission.com",
    notes=(
        "Strongest marine/water infrastructure in the Mediterranean. "
        "Mediterranean Film Studios (MFS): 750,000-gallon outdoor water tank + indoor tanks. "
        "Historical marine productions: Titanic (1943), Gladiator, Troy, Count of Monte Cristo. "
        "Base 25% on all qualifying Malta expenditure for non-Maltese productions; "
        "additional 2% for Maltese-element productions. "
        "Uplifts: +3% MFC cultural contribution, +3% VFX/post in Malta, "
        "+7% small-budget (<EUR 3M). Maximum with all uplifts: ~40%. "
        "No cultural test required for foreign productions. "
        "ATL costs (director, cast, writer fees) explicitly eligible. "
        "Vessel charter, underwater equipment, and marine logistics all qualify as BTL spend. "
        "Cashflow: MFC typically processes within 60 working days of audit submission. "
        "Low employer WHT burden; EU VAT recoverable via registration."
    ),
    data_gaps=[
        "Exact uplift thresholds and stacking rules not verified from MFC statute text",
        "Assignability of rebate receivable to gap lender not confirmed from primary source",
        "Annual program allocation limit not publicly stated — confirm before committing spend",
        "Cashflow timing (20 weeks) is an estimate; verify against current MFC processing terms",
        "WHT on international cast: confirm under applicable tax treaty",
        "Maltese element definition (for +2% uplift) not verified from current guidelines",
    ],
)

_GREECE = JurisdictionIncentiveProfile(
    jurisdiction_code="GR",
    jurisdiction_name="Greece",
    program_slug="gr_cash_rebate",
    program_name="Greece Cash Rebate for International Productions",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.40,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=100_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=39,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.24,
    withholding_tax_pct=0.20,
    payroll_burden_pct=0.22,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Enterprise Greece / Greek Film Centre (GFC)",
    authority_url_hint="enterprisegreece.gov.gr",
    notes=(
        "Highest headline rate (40%) among Tier 1 comparators. "
        "16,000+ km coastline; Aegean and Ionian access offer exceptional open-water variety. "
        "Greek shipping industry (Piraeus) provides commercial vessel operators with maritime "
        "logistics experience — directly transferable to boat-heavy film operations. "
        "No dedicated film water tank equivalent to Malta MFS. "
        "ATL and BTL costs qualify as eligible Greek expenditure. "
        "Vessel charter and marine support qualify as production expenditure. "
        "High employer social contributions (~22-24%) increase local crew cost. "
        "Cashflow risk: Greek administrative processes routinely extend to 9-12+ months. "
        "Annual program allocation exists but specific cap not publicly confirmed — "
        "budget oversubscription is a real risk for scheduling."
    ),
    data_gaps=[
        "Annual program allocation/cap: exact budget not publicly confirmed",
        "WHT on international cast: standard 20% rate; treaty reduction requires bilateral verification",
        "Cashflow timing (39 weeks): based on market reports, not official program SLA",
        "Vessel/marine explicit qualifying spend confirmation not verified from program text",
        "Post-production facilities in Greece: limited compared to major markets",
    ],
)

_CYPRUS = JurisdictionIncentiveProfile(
    jurisdiction_code="CY",
    jurisdiction_name="Cyprus",
    program_slug="cy_film_rebate",
    program_name="Cyprus Film Production Rebate",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    base_rate=0.35,
    max_rate=0.35,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=100_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=26,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False,
    post_production_available=False,
    vat_recoverable=True,
    vat_rate_pct=0.19,
    withholding_tax_pct=0.0,
    payroll_burden_pct=0.08,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Cyprus Investment Promotion Agency (CIPA) / Deputy Ministry of Tourism",
    authority_url_hint="cipa.org.cy",
    notes=(
        "35% cash rebate — DISCOVERY tier: rate unverified from statute text. "
        "Mediterranean coastline (648 km); warm water similar to Greece. "
        "No film-specific marine infrastructure; crew base very shallow. "
        "Substantially all BTL crew must be imported, reducing net producer benefit. "
        "Low employer tax burden (~8%) partially offsets import cost premium. "
        "Cyprus 12.5% corporate tax rate makes it a useful co-production entity domicile "
        "independent of where spend is incurred — this structural use case should be evaluated "
        "separately from the production incentive itself. "
        "Vessel and marine costs expected to qualify but not confirmed from program text."
    ),
    data_gaps=[
        "Program rate of 35% not verified from statute text (DISCOVERY)",
        "Minimum spend of EUR 100,000 not confirmed from primary source",
        "Annual program budget cap unknown",
        "VFX and music qualifying treatment not confirmed",
        "Vessel/marine explicit qualification not confirmed",
        "Cashflow timing (26 weeks) is an estimate",
        "ATL qualifying scope not confirmed from current program guidelines",
        "Track record: program is relatively new; limited completed-claim history",
    ],
)

TIER1_PROFILES: dict[str, JurisdictionIncentiveProfile] = {
    "MU": _MAURITIUS,
    "MT": _MALTA,
    "GR": _GREECE,
    "CY": _CYPRUS,
}


# ---------------------------------------------------------------------------
# Secondary Reference Group Profiles
# ---------------------------------------------------------------------------

_IRELAND = JurisdictionIncentiveProfile(
    jurisdiction_code="IE",
    jurisdiction_name="Ireland",
    program_slug="ie_section_481",
    program_name="Section 481 Film Tax Credit",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.32,
    max_rate=0.32,
    is_refundable=True,
    is_transferable=True,
    annual_cap_local=None,
    min_spend_local=125_000.0,
    requires_cultural_test=True,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=12,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.23,
    withholding_tax_pct=0.20,
    payroll_burden_pct=0.11,
    financing_friction=FinancingFriction.LOW,
    authority_name="Revenue Commissioners Ireland",
    authority_url_hint="revenue.ie",
    notes=(
        "Section 481: 32% refundable tax credit. Assignable to gap lender — strong financing. "
        "Cultural test required (Irish Qualifying Test). "
        "80% budget cap or EUR 70M qualifying spend, whichever lower. "
        "Atlantic coastline; limited dedicated marine infrastructure. "
        "Ardmore Studios (Wicklow) + Screen Ireland ecosystem. Strong crew base for land productions. "
        "PARSED tier: rates and cap confirmed from Finance Act; cultural test points system unverified."
    ),
    data_gaps=[
        "Cultural test passing threshold and points system not verified from primary source",
        "WHT on international cast: 20% standard; treaty rate reduction requires verification",
        "Cashflow timing (12 weeks) is an estimate based on Revenue processing norms",
    ],
)

_FRANCE = JurisdictionIncentiveProfile(
    jurisdiction_code="FR",
    jurisdiction_name="France",
    program_slug="fr_trip",
    program_name="Tax Rebate for International Productions (TRIP)",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=250_000.0,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=26,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.20,
    withholding_tax_pct=0.33,
    payroll_burden_pct=0.45,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Centre National du Cinéma (CNC)",
    authority_url_hint="cnc.fr",
    notes=(
        "TRIP: 30% rebate on qualifying French expenditure. Cultural test (2 of 6 French elements). "
        "Minimum EUR 250,000. One of Europe's deepest crew bases. "
        "Very high employer payroll burden (~45%) substantially erodes net rate on local labor. "
        "High WHT on foreign artists (33%) requires careful talent deal structuring. "
        "Mediterranean coast (Nice, Marseille) and Atlantic provide open water; "
        "no dedicated marine film infrastructure. "
        "ATL qualifying treatment unclear: French artists favored but foreign ATL may qualify partially."
    ),
    data_gaps=[
        "ATL qualifying treatment for non-French directors/cast not confirmed",
        "Cultural test exact requirements unverified from CNC source",
        "Cashflow timing (26 weeks) is an estimate",
        "WHT rates vary by treaty and payment type; 33% is standard non-treaty",
    ],
)

_ITALY = JurisdictionIncentiveProfile(
    jurisdiction_code="IT",
    jurisdiction_name="Italy",
    program_slug="it_tax_credit_foreign",
    program_name="Italian Tax Credit for Foreign Productions",
    confidence_tier="DISCOVERY",
    incentive_type="tax_credit",
    base_rate=0.40,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=20_000_000.0,
    min_spend_local=1_000_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=26,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.22,
    withholding_tax_pct=0.26,
    payroll_burden_pct=0.32,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Ministero della Cultura (MiC)",
    authority_url_hint="cultura.gov.it",
    notes=(
        "40% tax credit on qualifying Italian spend — equal to Greece's headline rate. "
        "No cultural test for foreign productions. Min EUR 1M; cap EUR 20M per film. "
        "Extensive coastline (Amalfi, Sicily, Sardinia) + Adriatic; strong marine backdrop. "
        "Deep crew base in Rome (Cinecittà) and Milan. "
        "High employer payroll burden (~32%) and WHT (~26%) require cost modeling. "
        "EUR 20M per-project cap is the binding constraint for large productions."
    ),
    data_gaps=[
        "EUR 20M cap and current implementing decrees not verified from primary source",
        "WHT rates on international cast not verified from bilateral treaty schedule",
        "Tax credit assignability to financier not confirmed",
        "Cashflow timing (26 weeks) is an estimate",
    ],
)

_SPAIN = JurisdictionIncentiveProfile(
    jurisdiction_code="ES",
    jurisdiction_name="Spain",
    program_slug="es_tax_credit_foreign",
    program_name="Spanish Tax Credit for Foreign Productions",
    confidence_tier="DISCOVERY",
    incentive_type="tax_credit",
    base_rate=0.30,
    max_rate=0.50,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=1_000_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=18,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.21,
    withholding_tax_pct=0.19,
    payroll_burden_pct=0.30,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Instituto de la Cinematografía y de las Artes Audiovisuales (ICAA)",
    authority_url_hint="cultura.gob.es",
    notes=(
        "Mainland Spain: 30% on qualifying spend. "
        "Canary Islands: 50% — most competitive warm-water marine rate in Europe. "
        "No cultural test for foreign productions. Min EUR 1M. "
        "Canary Islands (Tenerife, Gran Canaria) provide warm water, diverse coastline, "
        "and established marine tourism infrastructure reusable for film. "
        "Deep Spanish crew base (Madrid, Barcelona, Canaries). "
        "Marine productions considering warm water should evaluate Canary Islands 50% vs "
        "Malta 40% max — Canaries may be superior if spend concentration achievable."
    ),
    data_gaps=[
        "Canary Islands 50% rate and exact threshold not verified from primary source",
        "Minimum spend threshold (EUR 1M) and 50% of budget rule not verified from statute",
        "Cashflow timing (18 weeks) is an estimate",
        "WHT on international cast: 19% standard; bilateral treaty reduction not verified",
    ],
)

_CROATIA = JurisdictionIncentiveProfile(
    jurisdiction_code="HR",
    jurisdiction_name="Croatia",
    program_slug="hr_cash_rebate",
    program_name="Croatia Cash Rebate",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=200_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=18,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False,
    post_production_available=False,
    vat_recoverable=True,
    vat_rate_pct=0.25,
    withholding_tax_pct=0.15,
    payroll_burden_pct=0.17,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Croatian Audiovisual Centre (HAVC)",
    authority_url_hint="havc.hr",
    notes=(
        "25% cash rebate on qualifying Croatian spend. No cultural test. "
        "Dalmatian coastline (Adriatic): exceptional location variety; "
        "transparent blue water, historic walled cities, islands. "
        "Historical productions: Game of Thrones (Dubrovnik), Star Wars: Rogue One. "
        "Croatia joined Eurozone Jan 2023 — EUR spend now native. "
        "Moderate crew depth; Dubrovnik and Zagreb crews experienced in international work. "
        "Lower headline rate (25%) but lower costs than Malta or Greece. "
        "Open Adriatic waters — good for boat-heavy sequences."
    ),
    data_gaps=[
        "Rate of 25% and current HAVC guidelines not verified from primary source",
        "Minimum spend EUR 200,000 not confirmed post-Eurozone transition",
        "VFX and music qualifying treatment unconfirmed",
        "Cashflow timing (18 weeks) is an estimate",
    ],
)

_HUNGARY = JurisdictionIncentiveProfile(
    jurisdiction_code="HU",
    jurisdiction_name="Hungary",
    program_slug="hu_hipa_rebate",
    program_name="Hungarian Tax Rebate (HIPA)",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=20_000_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=False,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=24,
    marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False,
    has_open_water_filming=False,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.27,
    withholding_tax_pct=0.0,
    payroll_burden_pct=0.13,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Hungarian Investment Promotion Agency (HIPA) / National Film Institute",
    authority_url_hint="hipa.hu",
    notes=(
        "30% tax rebate on qualifying Hungarian spend. Very low minimum spend (HUF 20M ~EUR 55K). "
        "Landlocked: no marine access. vessel_marine_qualifies=False — costs would not be incurred. "
        "Strongest studio infrastructure in Eastern Europe: Origo Studios (Budapest). "
        "Deep, cost-effective crew base. Useful for land/studio components of a split shoot. "
        "For marine-heavy productions: Hungary is relevant only as a VFX/post complement "
        "or for interior studio work, not as primary shooting jurisdiction."
    ),
    data_gaps=[
        "Rate of 30% and current HIPA guidelines not verified from primary source",
        "Minimum spend (HUF 20M) not confirmed from current program rules",
        "Tax rebate structure (vs. cash rebate) requires verification",
    ],
)

_BELGIUM = JurisdictionIncentiveProfile(
    jurisdiction_code="BE",
    jurisdiction_name="Belgium",
    program_slug="be_tax_shelter",
    program_name="Belgian Tax Shelter (+ Regional Cash Rebates)",
    confidence_tier="DISCOVERY",
    incentive_type="regional_fund",
    base_rate=0.17,
    max_rate=0.40,
    is_refundable=None,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=True,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.21,
    withholding_tax_pct=0.30,
    payroll_burden_pct=0.35,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Tax Shelter.be / Regional film agencies (Screen Flanders, Wallimage, Inver)",
    authority_url_hint="taxshelter.be",
    notes=(
        "Two distinct mechanisms: Tax Shelter (federal) and regional cash rebates. "
        "Tax Shelter is not a direct rebate — it is a fundraising mechanism generating "
        "~16-17% effective benefit via Belgian investor tax advantage. "
        "Regional programs (Flanders: Screen Flanders; Wallonia: Wallimage) provide "
        "direct cash support up to ~40% on regional qualifying spend. "
        "Mechanisms can stack but are structurally complex. "
        "North Sea coastal access (Oostende) — limited for warm-water marine productions. "
        "High payroll burden and WHT make Belgium expensive for imported crew. "
        "For a water-based marine production, Belgium is a reference point only — "
        "not a primary candidate."
    ),
    data_gaps=[
        "Regional rebate rates (up to 40%) not verified from Flanders/Wallonia source documents",
        "Tax Shelter effective rate (17%) is a market estimate; deal-specific",
        "Cultural test requirements per region not verified",
        "Cashflow timing: highly variable due to deal structure complexity",
        "Stacking rules between Tax Shelter and regional programs not verified",
    ],
)

_GERMANY = JurisdictionIncentiveProfile(
    jurisdiction_code="DE",
    jurisdiction_name="Germany",
    program_slug="de_dfff",
    program_name="German Federal Film Fund (DFFF/GFFF)",
    confidence_tier="DISCOVERY",
    incentive_type="grant",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=25_000_000.0,
    min_spend_local=1_000_000.0,
    requires_cultural_test=True,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=26,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.19,
    withholding_tax_pct=0.15,
    payroll_burden_pct=0.20,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Filmförderungsanstalt (FFA) / Beauftragter für Kultur und Medien (BKM)",
    authority_url_hint="ffa.de",
    notes=(
        "DFFF: 25% grant on qualifying German spend. Cultural/economic test required. "
        "Minimum 30% of total budget must be qualifying German spend — structural gate. "
        "Cap EUR 25M per production (DFFF); GFFF available for larger productions. "
        "Very deep crew base: Bavaria Studios (Munich), Babelsberg (Potsdam/Berlin). "
        "North Sea and Baltic coastal access but unsuitable for warm-water marine work. "
        "30% German spend requirement makes Germany a poor fit unless substantial "
        "interior or studio work can be structurally placed there. "
        "For marine-heavy productions: Germany is a reference point only."
    ),
    data_gaps=[
        "DFFF rate of 25% and current guidelines not verified from BKM primary source",
        "30% German spend threshold not confirmed from current BKM rules",
        "GFFF allocation and eligibility not verified",
        "Cultural/economic test scoring not verified",
        "Cashflow timing (26 weeks) is an estimate",
    ],
)

SECONDARY_PROFILES: dict[str, JurisdictionIncentiveProfile] = {
    "IE": _IRELAND,
    "FR": _FRANCE,
    "IT": _ITALY,
    "ES": _SPAIN,
    "HR": _CROATIA,
    "HU": _HUNGARY,
    "BE": _BELGIUM,
    "DE": _GERMANY,
}

ALL_PROFILES: dict[str, JurisdictionIncentiveProfile] = {
    **TIER1_PROFILES,
    **SECONDARY_PROFILES,
}


# ---------------------------------------------------------------------------
# Tier 1 Gap Matrix (Mauritius vs Malta / Greece / Cyprus)
#
# Values: True = confirmed, False = confirmed-no, None = unknown/unverified,
#         str = descriptive status note where boolean is insufficient.
# Source tier: same as profile.confidence_tier.
# Do not promote any cell to True without a primary-source citation.
# ---------------------------------------------------------------------------

GAP_MATRIX: dict[str, dict[str, object]] = {
    "MU": {
        "rate_verified": False,          # 35% from budget evidence only, not EDB statute
        "atl_treatment": None,           # Director/producer/cast qualifying scope unknown
        "foreign_labor": None,           # International crew routing rules unconfirmed
        "vessel_marine": True,           # Confirmed in production budget QPE (Groups report)
        "accommodation_per_diem": None,  # Mauritius per-diem qualifying treatment unconfirmed
        "vat_customs": "15pct_non_recoverable",  # Confirmed: $92,439 embedded in gross budget
        "finance_timing": None,          # No confirmed EDB processing SLA
        "grants_support": None,          # Location/permit facilitation via MFDC; no confirmed grant
    },
    "MT": {
        "rate_verified": False,          # 25%-40% from public MFC summary; statute text unverified
        "atl_treatment": True,           # ATL explicitly eligible per MFC published guidelines
        "foreign_labor": True,           # No restriction on imported crew BTL costs
        "vessel_marine": True,           # Vessel charter and marine logistics explicitly qualify
        "accommodation_per_diem": True,  # Qualifying Malta expenditure includes accommodation
        "vat_customs": "recoverable_eu", # EU VAT registration available; recoverable
        "finance_timing": "20_weeks_estimated",  # ~60 working days per MFC — not SLA-confirmed
        "grants_support": None,          # No confirmed direct production grant separate from rebate
    },
    "GR": {
        "rate_verified": False,          # 40% from Enterprise Greece summary; statute text unverified
        "atl_treatment": True,           # ATL costs stated as qualifying in program overview
        "foreign_labor": None,           # Qualifying scope for non-Greek crew costs unverified
        "vessel_marine": True,           # Vessel and marine support stated as qualifying
        "accommodation_per_diem": None,  # Accommodation qualifying scope not confirmed
        "vat_customs": "recoverable_eu", # EU VAT registration available; recoverable
        "finance_timing": "39_weeks_estimated",  # 9-12 month market reports; no official SLA
        "grants_support": None,          # Annual allocation cap exists; competitive risk unquantified
    },
    "CY": {
        "rate_verified": False,          # 35% from DISCOVERY sources; not verified from statute
        "atl_treatment": None,           # ATL scope confirmed as eligible in profile but not from statute
        "foreign_labor": None,           # Rules on international crew costs unconfirmed
        "vessel_marine": True,           # Expected to qualify; not confirmed from program text
        "accommodation_per_diem": None,  # Qualifying treatment unconfirmed
        "vat_customs": "recoverable_eu", # EU VAT registration available; recoverable
        "finance_timing": "26_weeks_estimated",  # Estimated only
        "grants_support": None,          # No confirmed supplementary grant program identified
    },
}
