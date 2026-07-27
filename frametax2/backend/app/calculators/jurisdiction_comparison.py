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
    program_name="Mauritius EDB Film Rebate Scheme (30% / up to 40%)",
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.40,
    is_refundable=None,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
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
        "VERIFIED tier (rates): 30% general rebate / up to 40% for feature films "
        "with minimum QPE of USD 1,000,000, per EDB 'Film Rebate Scheme — "
        "Submission Procedures' (31 Jan 2020), citing the EDB (Film Rebate "
        "Scheme) Regulation 2018; corroborated by MCCI. 'Up to 40%' is a band "
        "ceiling — the awarded rate is subject to Film Rebate Committee "
        "assessment and CEO approval (see app.data.program_rate_rules). "
        "RATE CONFLICT (permanent Rules 1/2/5): the production budget's own "
        "'EDB Rebate at 35%' line is budget-evidenced, not authority — it is "
        "recorded in program_rate_rules.MU_BUDGET_EVIDENCED_RATES and IGNORED "
        "for all calculations. "
        "QPE categories per the same primary source's closed 33-item list: "
        "cast/crew remuneration (incl. ATL, no carve-out), equipment/location/"
        "studio hire, accommodation, catering, travel to Mauritius, marine/"
        "vessel services, insurance and accounting ('professional services'), "
        "post-production and VFX services (territorial: must be incurred "
        "locally). VAT: Mauritius 15% VAT non-recoverable for foreign "
        "productions ($92,439 confirmed embedded in gross budget; memo line, "
        "not QPE). Finance cost on rebate receivable: $0 in budget; engine "
        "models it at 8%/39 weeks — engineering assumption, no EDB SLA. "
        "Indian Ocean warm water, clear visibility — excellent for yacht and "
        "diving sequences. Limited local film crew base: effectively a full "
        "import production. Locally incorporated/registered production company "
        "required (100% foreign ownership permitted) — setup and compliance "
        "cost unquantified."
    ),
    data_gaps=[
        "Awarded rate within the 'up to 40%' band requires EDB approval — not pre-determinable",
        "Secondary-source claim of a 90%-of-filming-in-Mauritius condition for the 40% tier: "
        "not found in any government text reviewed; needs EDB written confirmation",
        "Producer 5-year track record and MU incorporation of the production entity: "
        "production facts not yet evidenced",
        "WHT on international cast/crew payments unverified",
        "Annual program budget/cap unknown",
        "Cashflow timing unknown — no confirmed processing SLA from EDB",
        "Rebate assignability to gap lender not confirmed",
        "Finance cost constants (8% bridge, 39 weeks) are engineering assumptions",
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
        "MATERIAL DISCREPANCY (flagged, not resolved, 2026-07-26): this record's 25%-base/40%-"
        "ceiling-via-three-stacked-uplifts structure (min spend EUR 50,000, no cultural test) "
        "traces to an undated internal citation. Five independently-converging 2024-era sources "
        "(Zerafa Advocates, Saturation.io, PCP Malta, Atlas Film Fixers, Ecovis Malta) instead "
        "describe a 35%-base/40%-for-micro-budget-QME-under-EUR-150k structure, min spend EUR "
        "100,000 (budget over EUR 200,000), WITH a cultural test — apparently reflecting a "
        "'revamped' 2024 scheme (per a Cineuropa headline: 'Malta launches revamped, bolder and "
        "better cash rebate') and a June-2024-dated official Guidelines PDF, neither of which "
        "could be directly fetched (403/unparseable) to confirm with certainty. base_rate/"
        "max_rate/min_spend_local/requires_cultural_test are NOT altered here pending a clean "
        "primary-source read of the 2024 guidelines — see app.data.program_requirements "
        "mt_mfc_rebate for the full reconciliation writeup.",
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
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.35,
    max_rate=0.45,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=650_000.0,
    min_spend_local=200_000.0,
    requires_cultural_test=True,
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
        "CORRECTED (worldwide population phase): confirmed directly from the "
        "official Cyprus Film Commission page (film.investcyprus.org.cy) — 'up "
        "to 45%,' not the flat 35% previously modeled. Real structure: 35% base, "
        "+10% cultural-test uplift to 45% (exact scoring thresholds unconfirmed, "
        "modeled as a ceiling — see program_rate_rules_worldwide.py CY_DOCTRINE). "
        "Minimum spend EUR 200,000 (feature film; also capped at 50% of total "
        "budget, not modeled). Cap EUR 650,000 max aid per production. Cultural "
        "test IS required (previous DISCOVERY entry incorrectly had this False). "
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
        "Cultural test exact scoring thresholds for the +10% uplift not "
        "confirmed from any source reviewed — the base/ceiling split (35%/45%) "
        "is confirmed, the pass criteria are not",
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
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=30_000_000.0,
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
        "TRIP, confirmed directly from cnc.fr (CNC's own TRIP page): 30% base "
        "rebate on qualifying French expenditure, rising to 40% when French "
        "VFX expenditure exceeds EUR 2,000,000 (a real statutory threshold, "
        "not a discretionary band — see program_rate_rules.py FR_RATE_RULES "
        "for why it's still modeled as a ceiling: this engine has no VFX-"
        "specific spend fact). Minimum spend EUR 250,000 or 50% of world "
        "budget (the 50%-of-budget alternative is not modeled). Cap EUR "
        "30,000,000 per project. Live action also requires >=5 shooting days "
        "in France (not modeled). Cultural test required (French/European "
        "culture, heritage, territory elements) — the prior '2 of 6 "
        "elements' points claim was NOT found in the cnc.fr text fetched "
        "and has been dropped, not carried forward unverified. Refundable: "
        "confirmed from source (State pays the difference if the rebate "
        "exceeds corporate income tax due). "
        "One of Europe's deepest crew bases. Very high employer payroll "
        "burden (~45%) substantially erodes net rate on local labor. High "
        "WHT on foreign artists (33%) requires careful talent deal "
        "structuring. Mediterranean coast (Nice, Marseille) and Atlantic "
        "provide open water; no dedicated marine film infrastructure."
    ),
    data_gaps=[
        "ATL qualifying treatment for non-French directors/cast not confirmed",
        "Cultural test exact points-based criteria not confirmed — cnc.fr "
        "references separate live-action/animation cultural test documents "
        "not fetched; requires_cultural_test=True is confirmed, the pass "
        "threshold is not",
        "50%-of-world-budget alternative minimum-spend path not modeled "
        "(only the flat EUR 250,000 threshold is)",
        "5-shooting-days requirement (live action) not modeled — no "
        "shooting-days fact exists in this engine",
        "Cashflow timing (26 weeks) is an estimate",
        "WHT rates vary by treaty and payment type; 33% is standard non-treaty",
    ],
)

_ITALY = JurisdictionIncentiveProfile(
    jurisdiction_code="IT",
    jurisdiction_name="Italy",
    program_slug="it_tax_credit_foreign",
    program_name="Italian Tax Credit for Foreign Productions",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.40,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=True,
    annual_cap_local=20_000_000.0,
    min_spend_local=None,
    requires_cultural_test=True,
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
        "CORRECTED (worldwide population phase): confirmed directly from "
        "mestierecinema.it (Italian production consultancy). 40% rate and EUR "
        "20M cap held up under verification, but 'No cultural test for foreign' "
        "(prior DISCOVERY claim) was WRONG — a real 50/100-point cultural test "
        "exists (35-point floor in Block A). This is the FOURTH jurisdiction in "
        "this batch (after Cyprus, Croatia, Hungary) where a pre-existing "
        "'no cultural test' claim was found false on direct verification — see "
        "the cultural-test pattern note in CAPABILITY_LEDGER.md. Cap is EUR 20M "
        "per company PER YEAR (not strictly per-project — treated as the "
        "effective ceiling for a single production). Transferable: CONFIRMED "
        "('can be handed over ... to banks,' offsets VAT/IRES/IRAP/social "
        "contributions/IRPEF) — previously unknown. Minimum spend (prior EUR 1M "
        "figure) not found in either source checked and dropped, not carried "
        "forward unverified. An earlier secondary source's claim of a reduced "
        "30% rate for above-the-line costs outside the EEA was checked directly "
        "against mestierecinema.it and NOT corroborated — not modeled. "
        "Extensive coastline (Amalfi, Sicily, Sardinia) + Adriatic; strong "
        "marine backdrop. Deep crew base in Rome (Cinecittà) and Milan. High "
        "employer payroll burden (~32%) and WHT (~26%) require cost modeling."
    ),
    data_gaps=[
        "Minimum spend threshold not found in either source checked",
        "Per-company-per-year cap vs. a stricter per-project figure not fully "
        "reconciled — modeled as the effective per-production ceiling",
        "WHT rates on international cast not verified from bilateral treaty schedule",
        "Cashflow timing (26 weeks) is an estimate",
    ],
)

_SPAIN = JurisdictionIncentiveProfile(
    jurisdiction_code="ES",
    jurisdiction_name="Spain",
    program_slug="es_tax_credit_foreign",
    program_name="Spanish Tax Credit for Foreign Productions",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.25,
    max_rate=0.25,
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
        "Ley 27/2014 (Impuesto sobre Sociedades) Art. 36.2, confirmed verbatim: "
        "30% on the first EUR 1,000,000 of qualifying Spanish expenditure, 25% on "
        "the excess — a real, statute-confirmed graduated bracket. "
        "program_rate_rules.py ES_RATE_RULES now computes a genuine BLENDED "
        "effective rate from this bracket via RateRule.graduated_brackets (added "
        "worldwide-population phase to fix an earlier under-representation that "
        "modeled a flat conservative 25%) — e.g. ~26.3% for Little Utopia's ~$4.36M "
        "QPE, correctly between the flat 25%/30% figures, not equal to either. "
        "base_rate=0.25 / max_rate=0.30 here represent the asymptotic floor (very "
        "large QPE) and the best case (QPE at or below the EUR 1M bracket, where "
        "blended rate approaches 30%) — the actual served figure is QPE-dependent, "
        "not a fixed pick between the two. Min spend EUR 1,000,000 (EUR 200,000 "
        "for animation). Cap EUR 20,000,000 per production (EUR 10,000,000 per "
        "episode for series). No cultural test for foreign productions. Requires "
        "ICAA registration (Registro Administrativo de Empresas Cinematográficas y "
        "Audiovisuales). "
        "Canary Islands enhanced rate (widely reported ~50%/45%) is NOT in Article "
        "36 — checked all subsections directly, not present. Almost certainly a "
        "separate Canary Islands special economic/fiscal regime (REF) provision, "
        "unverified and NOT modeled here (see program_rate_rules.py "
        "ES_UNVERIFIED_CLAIMS) — do not treat as confirmed for marine/Canaries "
        "comparisons until that regime's primary text is read."
    ),
    data_gaps=[
        "Canary Islands enhanced rate: reported by secondary sources but absent "
        "from Article 36 itself; likely lives in the separate Canarias REF regime, "
        "not yet located or read — treat as unconfirmed, not as a known 50%/45%",
        "Spend-category/QPE doctrine unclassified: Art. 36.2 names only two "
        "categories (EEA-resident creative-personnel costs; technical-industry/ "
        "supplier costs) and defers detail to an unretrieved Orden Ministerial — "
        "not enough basis to classify OPEN_DEFAULT_INCLUDE vs CLOSED_POSITIVE_LIST",
        "Cashflow timing (18 weeks) is an estimate",
        "WHT on international cast: 19% standard; bilateral treaty reduction not verified",
        "is_transferable: not confirmed from Art. 36 text (deduction structure "
        "suggests it offsets the producer's own tax liability, not a market-"
        "tradable credit like Georgia's, but this has not been verified)",
    ],
)

_CROATIA = JurisdictionIncentiveProfile(
    jurisdiction_code="HR",
    jurisdiction_name="Croatia",
    program_slug="hr_cash_rebate",
    program_name="Croatia Cash Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=263_000.0,
    requires_cultural_test=True,
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
        "CORRECTED (worldwide population phase): confirmed directly from Invest "
        "Croatia (investcroatia.gov.hr, official government investment-promotion "
        "agency). Base 25% + up to 5% regional-development uplift (30% ceiling, "
        "not modeled as guaranteed — this engine has no fact identifying which "
        "region a shoot occurs in). Minimum spend EUR 263,000 for feature films "
        "(the prior EUR 200,000 figure was an unsourced round-number guess). A "
        "REAL, points-based cultural test exists (12/34 minimum, >=4 points per "
        "category across European-content/personnel/facilities-use) — the prior "
        "DISCOVERY entry incorrectly claimed 'No cultural test.' No maximum cap "
        "specified in the source. "
        "Dalmatian coastline (Adriatic): exceptional location variety; "
        "transparent blue water, historic walled cities, islands. "
        "Historical productions: Game of Thrones (Dubrovnik), Star Wars: Rogue One. "
        "Moderate crew depth; Dubrovnik and Zagreb crews experienced in "
        "international work. Open Adriatic waters — good for boat-heavy sequences."
    ),
    data_gaps=[
        "Regional-uplift-eligible areas not enumerated — cannot pre-determine "
        "which shoot locations qualify for the +5%",
        "Maximum cap per project not found in the source fetched (earlier "
        "secondary sources gave conflicting EUR 2.65M-3M figures, not used)",
        "VFX and music qualifying treatment unconfirmed",
        "Cashflow timing (18 weeks) is an estimate",
    ],
)

_HUNGARY = JurisdictionIncentiveProfile(
    jurisdiction_code="HU",
    jurisdiction_name="Hungary",
    program_slug="hu_hipa_rebate",
    program_name="Hungarian Film Incentive (NFI)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.375,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=True,
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
        "CORRECTED (worldwide population phase): confirmed directly, verbatim, "
        "from NFI's own official page (nfi.hu). 30% base cash rebate ('cash "
        "refund (post-financing)') on Hungarian direct production costs, real "
        "and confirmed — but 'No cultural test for foreign' (the prior DISCOVERY "
        "claim) was WRONG: a real 16-point EU-content/cultural-values test is "
        "required. A real 37.5% ceiling exists via a cross-border cost-inclusion "
        "mechanism (adding non-Hungarian costs, capped at 25% of the rebate) — "
        "not modeled as guaranteed since this engine has no Hungarian-vs-non-"
        "Hungarian QPE split fact. Total state subsidies capped at 50% of "
        "production budget (%-of-budget, not modeled as an absolute figure). The "
        "prior HUF 20,000,000 minimum-spend figure was NOT found in the primary "
        "source fetched and is not carried forward unconfirmed. "
        "Landlocked: no marine access. vessel_marine_qualifies=False — costs "
        "would not be incurred. Strongest studio infrastructure in Eastern "
        "Europe: Origo Studios (Budapest). Deep, cost-effective crew base."
    ),
    data_gaps=[
        "No explicit minimum production budget/spend threshold confirmed from "
        "the primary source fetched (prior HUF 20M figure dropped, not carried "
        "forward unverified)",
        "16-point cultural test scoring breakdown not detailed in source fetched",
        "Exact mechanics of the 25%-of-rebate cross-border cap not fully clear "
        "from the source summary — modeled as an unenforced ceiling condition",
    ],
)

_BELGIUM = JurisdictionIncentiveProfile(
    jurisdiction_code="BE",
    jurisdiction_name="Belgium",
    program_slug="be_tax_shelter",
    program_name="Belgian Tax Shelter (+ Regional Cash Rebates)",
    confidence_tier="PARSED",
    incentive_type="regional_fund",
    base_rate=0.42,
    max_rate=0.44,
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
        "CORRECTED (worldwide population phase): the prior ~16-17% figure was an "
        "unsourced DISCOVERY-tier estimate (also present, unsourced, in the Alembic "
        "migration seed — checked first, added no independent confidence). Cross-"
        "checked against two independent Belgian tax-shelter-industry sources "
        "(beci.be business federation; scopeinvest.be, a licensed tax-shelter "
        "intermediary), both agreeing: producers net 42-44% of eligible Belgian "
        "expenditure through the Tax Shelter mechanism, AFTER deduction of investor "
        "return/broker/insurance costs (i.e. this is already the producer's real net "
        "benefit, not a gross raise figure needing further discount). A third, semi-"
        "official regional source (screenflanders.be) states a lower, differently-"
        "framed 38-40% 'financeable' figure — likely gross-financeable rather than "
        "net, but not reconciled; disclosed as a genuine unresolved discrepancy, not "
        "silently dropped. No minimum expenditure threshold for the federal Tax "
        "Shelter (confirmed from source). Cap conflicting across sources (~EUR 5M "
        "per beci.be/scopeinvest.be vs ~EUR 7.25M/$8M per another source) — left "
        "UNKNOWN (not modeled) rather than picking one arbitrarily. Cultural "
        "requirement confirmed: certified as a 'European work' under the AVMS "
        "Directive, or qualifying international co-production. "
        "Regional cash rebates (Flanders: Screen Flanders; Wallonia: Wallimage) "
        "exist separately and can stack, but their own rates remain unverified — "
        "not modeled here; this program's rate reflects the federal Tax Shelter only. "
        "North Sea coastal access (Oostende) — limited for warm-water marine "
        "productions. High payroll burden and WHT make Belgium expensive for "
        "imported crew."
    ),
    data_gaps=[
        "Exact net-benefit percentage still has a real spread (38-44%) across "
        "sources; modeled at the better-corroborated 42-44% (two independent "
        "sources), not the FPS Finance ministerial brochure itself (not fetched)",
        "Project cap: EUR 5M vs EUR 7.25M/$8M conflict across sources, left UNKNOWN",
        "Regional rebate rates (Flanders/Wallonia, reportedly up to ~40%) not "
        "verified from source documents — not modeled, program covers federal "
        "Tax Shelter only",
        "Cashflow timing: highly variable due to deal structure complexity",
        "Stacking rules between Tax Shelter and regional programs not verified",
    ],
)

_GERMANY = JurisdictionIncentiveProfile(
    jurisdiction_code="DE",
    jurisdiction_name="Germany",
    program_slug="de_dfff",
    program_name="German Federal Film Fund (DFFF II — production service)",
    confidence_tier="PARSED",
    incentive_type="grant",
    base_rate=0.30,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=25_000_000.0,
    min_spend_local=None,
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
        "CORRECTED (worldwide population phase): the prior 25% figure was not "
        "merely unverified — it was STALE. Confirmed directly, verbatim, from "
        "FFA's own official page (ffa.de/dfff-en): 'The grant for both types of "
        "funding was increased in 2025 to a uniform 30 per cent.' DFFF II (the "
        "sub-program for production service providers — the relevant path for a "
        "foreign production service-shooting in Germany) cap EUR 25M, corroborated "
        "by Greenberg Traurig's reporting on the May 2026 BKM draft guidelines. "
        "Minimum German spend must be >=20% of TOTAL production budget (not an "
        "absolute EUR figure — not modeled as min_spend_local since this engine "
        "has no total-worldwide-budget-ratio fact). A further BKM restructuring "
        "(new framework replacing DFFF/GMPF) is in draft as of May 2026, intended "
        "for 2027 — today's 30%/EUR 25M figures are the CURRENT regime, subject "
        "to real, disclosed near-term change. Very deep crew base: Bavaria "
        "Studios (Munich), Babelsberg (Potsdam/Berlin). North Sea and Baltic "
        "coastal access but unsuitable for warm-water marine work."
    ),
    data_gaps=[
        "20%-of-total-budget minimum German spend not independently fetched from "
        "primary BKM guideline text (Greenberg Traurig secondary reporting only)",
        "2027 restructured framework (draft as of May 2026) will supersede "
        "today's DFFF/GMPF figures — not modeled, current regime only",
        "Cultural/economic test scoring not verified",
        "Cashflow timing (26 weeks) is an estimate",
    ],
)

_UNITED_KINGDOM = JurisdictionIncentiveProfile(
    jurisdiction_code="GB",
    jurisdiction_name="United Kingdom",
    program_slug="uk_avec",
    program_name="Audio-Visual Expenditure Credit (AVEC)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.255,
    max_rate=0.2925,
    is_refundable=None,
    is_transferable=None,
    annual_cap_local=None,   # confirmed NO cap on claimable amount — genuine
                              # confirmed-uncapped, not merely unknown
    min_spend_local=None,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=None,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=True,
    vat_rate_pct=0.20,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="HM Revenue & Customs (HMRC) / British Film Institute (BFI)",
    authority_url_hint="bfi.org.uk",
    notes=(
        "NEW jurisdiction, added Worldwide Jurisdiction Population phase — no "
        "prior entry existed despite the UK being one of the largest global "
        "production markets. Confirmed directly, verbatim, from BFI's own "
        "official page (bfi.org.uk): AVEC is 'a taxable credit at a rate of "
        "34%,' which is itself taxable at UK corporation tax (25%), netting "
        "to a real 25.5% cash benefit (34% x 0.75 = 25.5%, independently "
        "verified by arithmetic, not just quoted). A VFX Additional Credit "
        "(+3.75%, effective 1 Jan 2025, reaching 29.25% net) exists but was "
        "NOT independently confirmed from the BFI text fetched — corroborated "
        "only by a second secondary source (Entertainment Partners), modeled "
        "as a ceiling with that caveat explicit (see program_rate_rules_"
        "worldwide.py GB_DOCTRINE). QPE itself is capped at the lower of 80% "
        "of total core expenditure or actual UK spend (a QPE-eligibility cap, "
        "not modeled — this engine has no such mechanism). At least 10% of "
        "total costs must be UK QPE (ratio condition, not modeled as an "
        "absolute threshold). Confirmed NO cap on claimable amount. Cultural "
        "test or official co-production required. Deep crew base and studio "
        "infrastructure (Pinewood, Leavesden, Shepperton) — common industry "
        "knowledge, not independently sourced this phase. Coastline exists "
        "(English Channel, North Sea, Irish Sea) but cold water, similar "
        "marine tier to France/Germany rather than Mediterranean jurisdictions."
    ),
    data_gaps=[
        "Refundability/transferability not explicitly confirmed from the "
        "source fetched (payable-credit structure strongly implied, not "
        "asserted)",
        "VFX +3.75% uplift not independently confirmed from BFI's own text — "
        "only corroborated by a secondary source",
        "WHT and payroll burden percentages not verified — left UNKNOWN "
        "rather than guessed",
        "ATL/BTL/music/marine spend-category qualification not confirmed",
        "Financing friction (assignability to gap lender) not confirmed — "
        "modeled as MEDIUM, a conservative middle judgment, not LOW",
        "Cashflow timing not verified",
    ],
)

_CANADA_FEDERAL = JurisdictionIncentiveProfile(
    jurisdiction_code="CA",
    jurisdiction_name="Canada (Federal)",
    program_slug="ca_federal_pstc",
    program_name="Canada Federal Production Services Tax Credit (PSTC)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.16,
    max_rate=0.16,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="CAVCO (Canadian Audio-Visual Certification Office) / CRA",
    authority_url_hint="canada.ca",
    notes=(
        "NEW jurisdiction, Worldwide Jurisdiction Population phase. Federal "
        "PSTC (the foreign/service-production program — CAVCO's separate "
        "CPTC is for Canadian-content productions, not modeled here): 16% "
        "REFUNDABLE credit on qualified CANADIAN LABOUR expenditure "
        "specifically, not total QPE (see program_rate_rules_worldwide.py "
        "CA_DOCTRINE for how this engine handles the narrower base). "
        "canada.ca's own PSTC page returned HTTP 403 on direct fetch — "
        "corroborated from a secondary production-services consultancy "
        "instead (PARSED, not VERIFIED). No minimum spend or cap. Stacks "
        "with provincial PSTC programs (e.g. British Columbia, separately "
        "modeled as CA-BC) — a real production filming in a Canadian "
        "province claims BOTH. Deep crew base (Vancouver 'Hollywood "
        "North', Toronto); real studio infrastructure."
    ),
    data_gaps=[
        "Primary canada.ca PSTC page could not be fetched directly (HTTP "
        "403) — relying on secondary consultancy corroboration",
        "VAT/GST/HST, withholding tax, and payroll burden vary by province "
        "and were not verified — left UNKNOWN rather than guessed",
        "Refundable credit's labour-only base vs this engine's total-QPE "
        "model means the served rate understates the true benefit for "
        "productions with high non-labour Canadian spend",
        "Federal-provincial stacking mechanics (federal + BC/Ontario/Quebec) "
        "not modeled — each jurisdiction priced independently, not combined",
    ],
)

_CANADA_BC = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-BC",
    jurisdiction_name="Canada — British Columbia",
    program_slug="ca_bc_pstc",
    program_name="British Columbia Production Services Tax Credit",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.36,
    max_rate=0.48,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Creative BC",
    authority_url_hint="gov.bc.ca",
    notes=(
        "NEW jurisdiction (sub-national — 'CA-BC' extends the jurisdiction_"
        "code convention beyond ISO 3166-1 alpha-2; checked directly that no "
        "code anywhere assumes a fixed 2-character length before using this). "
        "Confirmed directly, verbatim, from gov.bc.ca: base 36% PSTC on "
        "qualified BC labour expenditure (same labour-only-base caveat as "
        "the federal program — see program_rate_rules_worldwide.py "
        "CA_BC_DOCTRINE), +6% regional / +6% distant-location uplifts (up to "
        "48% combined, not modeled — no fact identifying WHERE in BC a "
        "shoot occurs). A separate 16% DAVE (animation/VFX/post) credit "
        "exists, not modeled as part of this program. Fully refundable. "
        "STACKS with the federal 16% PSTC (see CA federal profile). "
        "Vancouver ('Hollywood North') has deep, internationally experienced "
        "crew and real studio infrastructure (Bridge Studios, Martini Film "
        "Studios). No minimum spend or cap specified."
    ),
    data_gaps=[
        "Regional/distant-location uplift-eligible areas not enumerated — "
        "cannot pre-determine which shoot locations qualify for the +6%/+6%",
        "DAVE (animation/VFX/post) 16% credit not modeled as a separate "
        "program — would need its own program_slug if pursued",
        "VAT/GST/PST, withholding tax, and payroll burden not verified",
        "Federal-provincial stacking (CA + CA-BC combined) not modeled — "
        "each priced independently",
    ],
)

_CANADA_ON = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-ON",
    jurisdiction_name="Canada — Ontario",
    program_slug="ca_on_opstc",
    program_name="Ontario Production Services Tax Credit (OPSTC)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.215,
    max_rate=0.215,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=707_463.74,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Ontario Creates",
    authority_url_hint="ontariocreates.ca",
    notes=(
        "NEW jurisdiction. Confirmed directly, verbatim, from "
        "ontariocreates.ca (official). 21.5% on TOTAL qualifying "
        "production expenditure — a clean base, unlike federal/BC's "
        "labour-only structure. Real eligibility gate: Ontario labour "
        "must be >=25% of QPE claimed (disclosed, not enforced — no fact "
        "splitting Ontario-labour vs total QPE). Min spend CAD $1,000,000 "
        "(feature). No cap. Refundable. Stacks with the federal 16% PSTC. "
        "Toronto has deep, internationally experienced crew and real "
        "studio infrastructure (Pinewood Toronto, Cinespace)."
    ),
    data_gaps=[
        "25%-Ontario-labour eligibility gate not modeled — no fact to "
        "pre-evaluate it",
        "VAT/HST, withholding tax, and payroll burden not verified",
        "Federal-provincial stacking (CA + CA-ON combined) not modeled",
    ],
)

_CANADA_QC = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-QC",
    jurisdiction_name="Canada — Quebec",
    program_slug="ca_qc_pstc",
    program_name="Quebec Tax Credit for Film Production Services",
    confidence_tier="DISCOVERY",
    incentive_type="tax_credit",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="SODEC (Société de développement des entreprises culturelles)",
    authority_url_hint="sodec.gouv.qc.ca",
    notes=(
        "NEW jurisdiction. Base rate (25% on 'all-spend' costs — labour + "
        "qualified property) corroborated by two secondary program-guide "
        "sources but the official SODEC PDF fact sheet could not be parsed "
        "on fetch (binary/encoding issue) — held at DISCOVERY tier "
        "deliberately, not promoted to PARSED. A computer-aided-effects/"
        "animation uplift was reported but its exact mechanics were "
        "inconsistent across sources and NOT modeled (never guess at a "
        "garbled figure). Montreal has deep VFX/animation crew base."
    ),
    data_gaps=[
        "Official SODEC primary source not successfully read this phase — "
        "held at DISCOVERY, needs a working primary-source fetch",
        "VFX/animation uplift band not modeled — sources were internally "
        "inconsistent",
        "Minimum spend and cap not confirmed",
        "VAT/QST, withholding tax, and payroll burden not verified",
    ],
)

_AUSTRALIA = JurisdictionIncentiveProfile(
    jurisdiction_code="AU",
    jurisdiction_name="Australia",
    program_slug="au_location_offset",
    program_name="Australia Location Offset",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.30,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,   # AUD $20M real and confirmed but not converted —
                             # no sourced AUD/USD FX rate in this project
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=True,   # confirmed common knowledge: Warner Bros Gold
                             # Coast/Village Roadshow Studios has purpose-
                             # built water tanks — not independently
                             # sourced this phase, disclosed
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Department of Infrastructure, Transport, Regional "
                    "Development, Communications, Sport and the Arts",
    authority_url_hint="screenaustralia.gov.au",
    notes=(
        "NEW jurisdiction. Rate STALE, not merely unverified — the migration "
        "corpus's 16.5% figure was superseded by a real 2026 increase to "
        "30% (confirmed via multiple sources). Confirmed directly from "
        "Screen Australia's own official page: Location Offset (foreign "
        "productions, no cultural test) is 'mutually exclusive' with PDV "
        "Offset (post/VFX) and Producer Offset (Australian-content "
        "productions, requires 'significant Australian content') — an "
        "earlier secondary source's claim that Location + PDV could stack "
        "was checked against this government source and found wrong, not "
        "modeled. Min spend AUD $20,000,000 (film) — real and confirmed "
        "but NOT converted to USD: no sourced AUD/USD FX rate exists in "
        "this project. Gold Coast (Warner Bros/Village Roadshow Studios) "
        "has purpose-built water tanks — common industry knowledge, not "
        "independently sourced this phase."
    ),
    data_gaps=[
        "AUD/USD FX rate not in this project's sourced FX table — min "
        "spend cannot be pre-evaluated against a USD QPE fact",
        "PDV Offset and Producer Offset not modeled as alternative "
        "programs (mutually exclusive with Location Offset, would need "
        "their own program_slugs)",
        "VAT/GST, withholding tax, and payroll burden not verified",
        "Water tank/studio infrastructure claims are common industry "
        "knowledge, not independently sourced this phase",
    ],
)

_NEW_ZEALAND = JurisdictionIncentiveProfile(
    jurisdiction_code="NZ",
    jurisdiction_name="New Zealand",
    program_slug="nz_spg_international",
    program_name="New Zealand Screen Production Rebate (International)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.20,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=True,   # common industry knowledge (Weta Workshop /
                             # Stone Street Studios water infrastructure) —
                             # not independently sourced this phase
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="New Zealand Film Commission (NZFC)",
    authority_url_hint="mbie.govt.nz",
    notes=(
        "NEW jurisdiction. Confirmed directly from mbie.govt.nz (official "
        "government ministry): '20% for international productions (25% in "
        "certain circumstances)' — a real +5% uplift for 'significant "
        "economic benefits to New Zealand,' exact criteria unconfirmed. "
        "Program recently renamed from 'Screen Production Grant' (NZSPG) "
        "to 'Screen Production Rebate' in official government naming — "
        "internal program_slug (nz_spg_international) kept for continuity. "
        "Wellington (Weta Workshop, Stone Street Studios) has deep VFX/"
        "post crew and real water-tank infrastructure — common industry "
        "knowledge, not independently sourced this phase."
    ),
    data_gaps=[
        "Minimum spend and maximum cap not found in either source checked",
        "Exact 'significant economic benefit' uplift criteria unconfirmed",
        "VAT/GST, withholding tax, and payroll burden not verified",
    ],
)

_US_GEORGIA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-GA",
    jurisdiction_name="United States — Georgia",
    program_slug="us_ga_film_credit",
    program_name="Georgia Entertainment Industry Investment Act (EIIA)",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    base_rate=0.20,
    max_rate=0.30,
    is_refundable=False,
    is_transferable=True,
    annual_cap_local=None,
    min_spend_local=500_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=False,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Georgia Department of Economic Development (GDEcD) / Dept. of Revenue",
    authority_url_hint="georgia.org",
    notes=(
        "Reused from Alembic migration 0003 — the most rigorously statute-"
        "cited entry in the entire migration corpus (real O.C.G.A. "
        "§ 48-7-40.26 subsection citations, per-field VERIFIED status). "
        "Sanity-checked current for 2026 via a fresh search (georgia.org, "
        "dor.georgia.gov) — held up UNCHANGED, the only US state in this "
        "batch that did NOT turn out to be stale. 20% base + 10% Georgia "
        "logo uplift (or pre-approved alternative marketing) = 30% "
        "ceiling. Min spend $500,000. No annual cap. Non-refundable but "
        "fully transferable (market ~88-92 cents on the dollar). Very "
        "deep, mature crew base and studio infrastructure (Trilith "
        "Studios, Pinewood Atlanta); low financing friction (assignable "
        "credit, mature market)."
    ),
    data_gaps=[
        "Per-person ATL compensation cap ($500,000) not modeled as a "
        "distinct condition — this engine has no per-person compensation "
        "fact",
        "VAT/sales tax, withholding tax, and payroll burden not verified",
        "Transferable market value (~90 cents) is an estimate, not a fixed "
        "statutory figure",
    ],
)

_US_CALIFORNIA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-CA",
    jurisdiction_name="United States — California",
    program_slug="us_ca_film_credit",
    program_name="California Film & Television Tax Credit Program 4.0",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.35,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=True,
    annual_cap_local=120_000_000.0,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=False,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=True,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="California Film Commission",
    authority_url_hint="film.ca.gov",
    notes=(
        "CORRECTED — this is the SIXTH jurisdiction this population effort "
        "found genuinely STALE, not merely unverified. Alembic 0005's "
        "entry (20% base, up to 35% only with all three uplifts stacked, "
        "non-refundable) reflected the OLD Program 3.0. A real, major "
        "2025 legislative expansion (AB 132 + AB 1138, 'Program 4.0', "
        "effective 1 July 2025) replaced it: base 35%, +5% ceiling to 40% "
        "(outside LA County or VFX spend), program size $750M/year (was "
        "$330M), per-production cap raised to $120,000,000, and NEW "
        "electable refundability for applications on/after 1 July 2025 "
        "(previously non-refundable, sold at a market discount only). "
        "Confirmed via three independent production-industry legal/finance "
        "sources corroborating the same bill (direct fetch of film.ca.gov "
        "itself returned stale cached 2022 content, not used). Deepest "
        "studio/crew infrastructure of any US state (Hollywood); real "
        "purpose-built water tanks. Competitive/allocated program — credit "
        "not guaranteed even if criteria are met."
    ),
    data_gaps=[
        "Minimum spend threshold not confirmed for Program 4.0 "
        "specifically — the old Program 3.0 figure not carried forward",
        "Competitive/allocated selection process not modeled — this "
        "engine treats the rate as available, not probabilistic",
        "VAT/sales tax, withholding tax, and payroll burden not verified",
    ],
)

_US_NEW_YORK = JurisdictionIncentiveProfile(
    jurisdiction_code="US-NY",
    jurisdiction_name="United States — New York",
    program_slug="us_ny_film_credit",
    program_name="New York State Film Tax Credit Program (Production)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.30,
    max_rate=0.50,
    is_refundable=None,
    is_transferable=None,
    annual_cap_local=None,
    min_spend_local=250_000.0,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=True,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.DEEP,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Empire State Development (ESD)",
    authority_url_hint="esd.ny.gov",
    notes=(
        "CORRECTED — the migration's 25%/35%/BTL-only entry was stale. "
        "Confirmed directly, verbatim, from esd.ny.gov (official): base "
        "30%, ATL wages qualify subject to a 40%-of-other-costs cap (NOT "
        "excluded as previously modeled), +10% upstate uplift + +10% "
        "scoring uplift (5+ musicians) = 50% ceiling. Min spend $1,000,000 "
        "(NYC-area) or $250,000 (other NY counties) — modeled at the lower, "
        "conservative threshold. $700M/year program cap through 2036 (a "
        "program-wide cap, not a per-production figure — not modeled as "
        "annual_cap_local). 'Production Plus' offers a further +5-10% for "
        "companies with multiple NY productions, not modeled (producer-"
        "election fact this engine doesn't have). Deep NYC crew base and "
        "studio infrastructure (Silvercup, Kaufman Astoria)."
    ),
    data_gaps=[
        "Refundability/transferability not stated in the source fetched",
        "Upstate/scoring uplift eligibility not pre-evaluable — no shoot-"
        "location or scoring-vendor facts",
        "Production Plus multi-production uplift not modeled",
        "VAT/sales tax, withholding tax, and payroll burden not verified",
    ],
)

_US_NEW_MEXICO = JurisdictionIncentiveProfile(
    jurisdiction_code="US-NM",
    jurisdiction_name="United States — New Mexico",
    program_slug="us_nm_film_credit",
    program_name="New Mexico Film Production Tax Credit",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.25,
    max_rate=0.40,
    is_refundable=True,
    is_transferable=None,
    annual_cap_local=140_000_000.0,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=True,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=True,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.NONE,
    has_water_tanks=True,   # confirmed common knowledge: Albuquerque Studios
                             # has a purpose-built water tank — not
                             # independently sourced this phase
    has_open_water_filming=False,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="New Mexico Film Office / Taxation and Revenue Department",
    authority_url_hint="tax.newmexico.gov",
    notes=(
        "CORRECTED — stacking to 40% (was 30% in the migration). Cap "
        "$140,000,000 (FY2026) confirmed directly from tax.newmexico.gov "
        "(official). Rate structure (25% base, +10% rural / +5% TV pilot-"
        "series / +5% qualified facility = 40%) corroborated by 3 "
        "independent sources; the official nmfilm.com program page itself "
        "404'd on fetch. Refundable credit. Landlocked; no marine access."
    ),
    data_gaps=[
        "Minimum spend threshold not confirmed",
        "Rural/TV/facility uplift eligibility not pre-evaluable",
        "VAT/GRT, withholding tax, and payroll burden not verified",
    ],
)

_US_OREGON = JurisdictionIncentiveProfile(
    jurisdiction_code="US-OR",
    jurisdiction_name="United States — Oregon",
    program_slug="us_or_opif",
    program_name="Oregon Production Investment Fund (OPIF)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.262,
    max_rate=0.262,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=21_200_000.0,
    min_spend_local=1_000_000.0,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=0.0,   # confirmed: Oregon has no state sales tax
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Oregon Film",
    authority_url_hint="oregonfilm.org",
    notes=(
        "Mostly CONFIRMED, not stale — unlike every other US state checked "
        "this batch. 20% base + 6.2% separate labor rebate = 26.2% "
        "combined effective rate (corroborated by 3 independent sources). "
        "Min spend $1,000,000. Annual fund cap $21,200,000 — a real, "
        "small, competitive fund; no single project may receive more than "
        "50% of the annual fund in any fiscal year (not guaranteed even "
        "if criteria are met). Oregon has no state sales tax (confirmed)."
    ),
    data_gaps=[
        "ATL/VFX/music qualifying treatment not confirmed",
        "Withholding tax and payroll burden not verified",
        "Exact competitive-allocation odds not modeled — this engine "
        "treats the rate as available, not probabilistic",
    ],
)

_US_LOUISIANA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-LA",
    jurisdiction_name="United States — Louisiana",
    program_slug="us_la_film_incentive",
    program_name="Louisiana Motion Picture Production Tax Credit",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    base_rate=0.25,
    max_rate=0.40,
    is_refundable=False,
    is_transferable=True,
    annual_cap_local=150_000_000.0,
    min_spend_local=300_000.0,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=True,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Louisiana Economic Development (LED)",
    authority_url_hint="opportunitylouisiana.gov",
    notes=(
        "CORRECTED — confirmed directly from opportunitylouisiana.gov "
        "(official). Base 25%, +10% Louisiana screenplay / +5% outside "
        "New Orleans metro = 40% ceiling on total QPE. Separate 15% "
        "resident-payroll-only and 5% VFX-only credits exist but apply to "
        "narrower bases, NOT modeled here. NOT simply refundable — "
        "transferable at 88% net (90% face value minus 2% transfer fee), "
        "corrected from the migration's 'refundable via state buyback' "
        "framing. Cap $150M issued/$180M claimed per fiscal year — a "
        "secondary source's claim of a $125M cap (citing 'Act 44') "
        "conflicts with this official figure and was NOT used; disclosed "
        "as an unresolved discrepancy, not silently picked either way."
    ),
    data_gaps=[
        "The $125M-vs-$150M annual cap discrepancy between a secondary "
        "source and the official LED page is unresolved — modeled at the "
        "official $150M figure",
        "Screenplay/outside-NOLA uplift eligibility not pre-evaluable",
        "VAT/sales tax, withholding tax, and payroll burden not verified",
    ],
)

_SOUTH_AFRICA = JurisdictionIncentiveProfile(
    jurisdiction_code="ZA",
    jurisdiction_name="South Africa",
    program_slug="za_dtic_foreign_film",
    program_name="South Africa DTIC Foreign Film & TV Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.30,
    is_refundable=None,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Department of Trade, Industry and Competition (DTIC)",
    authority_url_hint="thedtic.gov.za",
    notes=(
        "Checked internal catalog lead first (global_inventory_extended.py "
        "already had ~20-25%, DISCOVERY). Refined directly from "
        "thedtic.gov.za (official): 25% base + 5% black-owned-service-"
        "company uplift = 30% ceiling. Min spend R15,000,000, cap "
        "R25,000,000 — not converted to USD (no sourced ZAR/USD FX rate "
        "in this project). "
        "MATERIAL, DISCLOSED RISK: 2026 news coverage (variety.com, "
        "shockng.com) reports a serious DTIC funding freeze threatening "
        "this rebate system industry-wide ('Rescue Rebate System,' "
        "workers protesting) — the DTIC page itself shows no suspension "
        "notice, so this is a genuine, unresolved tension between the "
        "statutory framework and its real-world funding reliability, "
        "disclosed rather than silently ignored or assumed either way. "
        "Cape Town is Africa's primary international production hub; "
        "favourable USD/ZAR exchange rate historically enhances real "
        "benefit (not independently verified this phase)."
    ),
    data_gaps=[
        "ZAR/USD FX rate not in this project's sourced FX table — min "
        "spend and cap cannot be pre-evaluated against USD facts",
        "Program funding-crisis status (2026 DTIC freeze reports) not "
        "resolved — a material risk this engine has no fact to track",
        "Refundability not confirmed from the source fetched",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_UAE_ABU_DHABI = JurisdictionIncentiveProfile(
    jurisdiction_code="AE-AD",
    jurisdiction_name="United Arab Emirates — Abu Dhabi",
    program_slug="ae_ad_film_rebate",
    program_name="Abu Dhabi 35%++ Cashback Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.35,
    max_rate=0.50,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=True,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=0.05,   # UAE standard VAT — common knowledge, not
                          # independently sourced this phase
    withholding_tax_pct=0.0,   # UAE has no individual income tax — common
                                # knowledge, not independently sourced
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Abu Dhabi Film Commission (twofour54)",
    authority_url_hint="film.gov.ae",
    notes=(
        "Checked internal catalog lead first (a 30% UAE/Dubai DISCOVERY "
        "entry in global_inventory_extended.py — stale; Dubai and Abu "
        "Dhabi are separate emirate-level programs, this models Abu Dhabi "
        "specifically). Real 2025 rate increase confirmed: 30%->35% "
        "standard, up to 50% via an 85+-point Enhanced Rebate system "
        "(including a per-shoot-day tariff). Direct official fetch "
        "blocked (film.gov.ae HTTP 403; a law-firm analysis was "
        "paywalled) — modeled from search-result excerpts quoting the "
        "official page and a UAE government media office press release. "
        "PARSED, not VERIFIED. UAE has no individual income tax, no "
        "corporate tax on individuals; 5% standard VAT — common industry "
        "knowledge, not independently sourced this phase."
    ),
    data_gaps=[
        "Minimum spend and maximum cap not found in sources checked",
        "Exact points-system criteria (beyond the shoot-days tariff) "
        "unconfirmed",
        "Direct primary-source fetch was blocked (403/paywall) — this "
        "entry rests on search-result excerpts of the primary source, "
        "not a raw fetch",
    ],
)

_MOROCCO = JurisdictionIncentiveProfile(
    jurisdiction_code="MA",
    jurisdiction_name="Morocco",
    program_slug="ma_ccm_rebate",
    program_name="Morocco CCM Foreign Production Cash Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.30,
    max_rate=0.30,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=1_000_000.0,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=False,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Centre Cinématographique Marocain (CCM)",
    authority_url_hint="ccm.ma",
    notes=(
        "Checked internal catalog lead first (global_inventory_extended.py "
        "already had a real ~20-30% DISCOVERY entry). Confirmed the top of "
        "that range at a flat 30%, corroborated by 4 independent sources: "
        "'no longer capped at the project level.' Min spend ~10,000,000 "
        "MAD (~$1,000,000) + 18 shooting days (the days condition not "
        "pre-evaluable). QPE capped at 90% of total expenditure "
        "(eligibility ceiling, not modeled). Requires mandatory CCM-"
        "registered Moroccan production company partner. Ouarzazate / "
        "Atlas Studios — one of Africa's largest studio complexes; strong "
        "track record (Gladiator, Game of Thrones)."
    ),
    data_gaps=[
        "18-shooting-days condition not modeled — no shoot-days fact "
        "exists in this engine",
        "VFX/music qualifying treatment not confirmed",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_DENMARK = JurisdictionIncentiveProfile(
    jurisdiction_code="DK",
    jurisdiction_name="Denmark",
    program_slug="dk_production_rebate",
    program_name="Denmark Production Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Danish Film Institute (DFI)",
    authority_url_hint="dfi.dk",
    notes=(
        "A genuinely NEW program (launched 2026, not a stale rate on an "
        "old one) — confirmed by 3 corroborating sources including "
        "nordiskfilmogtvfond.com, a real Nordic film-fund industry body: "
        "25% cash rebate, EUR 17,000,000 (DKK 125M) annual program "
        "budget. Resolves the pre-existing catalog entry's own disclosed "
        "uncertainty ('cash rebate vs grant structure') in favor of "
        "rebate. Cultural test required. Copenhagen, Zealand locations."
    ),
    data_gaps=[
        "Minimum spend threshold not confirmed",
        "ATL/VFX/music qualifying treatment not confirmed",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_FINLAND = JurisdictionIncentiveProfile(
    jurisdiction_code="FI",
    jurisdiction_name="Finland",
    program_slug="fi_business_finland_incentive",
    program_name="Business Finland Film Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=500_000.0,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Business Finland",
    authority_url_hint="businessfinland.fi",
    notes=(
        "Confirmed unchanged from the pre-existing catalog lead: 25% cash "
        "rebate, EUR 10-12M annual program budget (two sources gave "
        "close-but-not-identical figures, both confirm a low-tens-of-"
        "millions annual program size, not a per-production cap). "
        "Helsinki, Lapland (aurora borealis) locations. Cultural test "
        "required."
    ),
    data_gaps=[
        "ATL/VFX/music qualifying treatment not confirmed",
        "Exact annual budget: EUR 10M vs EUR 12M discrepancy across "
        "sources, not resolved (not modeled as a cap either way)",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_NORWAY = JurisdictionIncentiveProfile(
    jurisdiction_code="NO",
    jurisdiction_name="Norway",
    program_slug="no_film_incentive",
    program_name="Norwegian Film Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=True,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Norwegian Film Institute (NFI)",
    authority_url_hint="nfi.no",
    notes=(
        "Confirmed via NFI's own official page (the URL itself, "
        "norwegianfilm.com/25-incentive, names the rate). COMPETITIVE, "
        "not an entitlement — a 2026 round selected only 5 productions "
        "sharing a NOK 84,700,000 total reimbursement cap; financing "
        "friction modeled HIGH to reflect this. Min spend NOK 4,000,000 "
        "(not converted — no sourced NOK/USD FX rate). Requires >=30% "
        "international financing at application time. Fjords, Arctic, "
        "Oslo locations."
    ),
    data_gaps=[
        "NOK/USD FX rate not in this project's sourced FX table",
        "Exact competitive-selection odds not modeled — this engine "
        "treats the rate as available, not probabilistic",
        "ATL/VFX/music qualifying treatment not confirmed",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_SWEDEN = JurisdictionIncentiveProfile(
    jurisdiction_code="SE",
    jurisdiction_name="Sweden",
    program_slug="se_production_rebate",
    program_name="Sweden Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.25,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=700_000.0,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True,
    post_production_available=True,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Swedish Film Institute",
    authority_url_hint="filminstitutet.se",
    notes=(
        "Confirmed via nordiskfilmogtvfond.com (real Nordic film-fund "
        "industry body). COMPETITIVE, first-come-first-served allocation "
        "(SEK 100M first round) — publicly criticised by Swedish "
        "industry bodies as a real friction point; financing friction "
        "modeled HIGH to reflect this. Stockholm, Malmo, Gotland "
        "locations."
    ),
    data_gaps=[
        "Exact first-come-first-served allocation odds not modeled",
        "ATL/VFX/music qualifying treatment not confirmed",
        "VAT, withholding tax, and payroll burden not verified",
    ],
)

_SAUDI_ARABIA = JurisdictionIncentiveProfile(
    jurisdiction_code="SA",
    jurisdiction_name="Saudi Arabia",
    program_slug="sa_film_commission_rebate",
    program_name="Saudi Film Commission Production Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    base_rate=0.60,
    max_rate=0.60,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=200_000.0,
    requires_cultural_test=False,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False,
    has_open_water_filming=True,
    crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False,
    post_production_available=False,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Saudi Film Commission",
    authority_url_hint="film.sa",
    notes=(
        "CORRECTED — dramatically stale. The pre-existing catalog lead "
        "(40%) was superseded by a real 2026 increase to 60%, confirmed "
        "by 8 independent major industry sources (Deadline, Hollywood "
        "Reporter, Variety, Screen Daily, Arab News, etc.), positioning "
        "Saudi Arabia 'at the very top of the global film incentive "
        "landscape.' Min spend SAR 750,000 (feature; SAR 187,000 "
        "documentary/animation) confirmed 2026-07-26 via direct fetch of "
        "film.sa. No distinct cultural/values TEST exists (corrects a "
        "prior True) — content vetting instead runs through two named "
        "gates, Script Content Clearance and a Filming Non-Objection "
        "Certificate, a regulatory content-clearance mechanism rather "
        "than a cultural test. Emerging market under Vision 2030 — crew "
        "depth and studio infrastructure still developing, modeled "
        "SHALLOW/False pending verification; financing friction HIGH "
        "given the market's youth and evolving disbursement process."
    ),
    data_gaps=[
        "Minimum spend threshold not found in any source checked",
        "Annual/per-production cap not confirmed",
        "Content-restriction/cultural-review criteria not detailed",
        "Crew depth and studio infrastructure not independently verified "
        "— modeled conservatively given the market's recency",
    ],
)

_JORDAN = JurisdictionIncentiveProfile(
    jurisdiction_code="JO",
    jurisdiction_name="Jordan",
    program_slug="jo_rfc_rebate",
    program_name="Jordan Royal Film Commission Production Rebate",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    base_rate=0.10,
    max_rate=0.25,
    is_refundable=True,
    is_transferable=False,
    annual_cap_local=None,
    min_spend_local=None,
    requires_cultural_test=True,
    atl_qualifies=None,
    btl_qualifies=True,
    vfx_qualifies=None,
    music_qualifies=None,
    vessel_marine_qualifies=None,
    resident_labor_uplift_available=False,
    cashflow_timing_weeks=None,
    marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False,
    has_open_water_filming=False,
    crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False,
    post_production_available=False,
    vat_recoverable=None,
    vat_rate_pct=None,
    withholding_tax_pct=None,
    payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Royal Film Commission Jordan (RFC)",
    authority_url_hint="rfc.jo",
    notes=(
        "No fresher rate found this pass — remains DISCOVERY tier, carried "
        "forward from the pre-existing catalog lead, not promoted further. "
        "Petra, Wadi Rum, Aqaba are major location assets (Lawrence of "
        "Arabia, The Martian, Dune). Content review required."
    ),
    data_gaps=[
        "Confirmed current rate (within the 10-25% range) not verified",
        "Minimum spend and annual cap unknown",
        "Crew depth and studio infrastructure not verified",
    ],
)

_THAILAND = JurisdictionIncentiveProfile(
    jurisdiction_code="TH", jurisdiction_name="Thailand",
    program_slug="th_boi_incentive", program_name="Thailand BOI Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=1_400_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Thailand Board of Investment (BOI)", authority_url_hint="thailandfilmoffice.org",
    notes=(
        "CORRECTED — stale 15-20% catalog figure superseded by a real "
        "30% rate, corroborated by 2 independent sources. Min spend "
        "$1,400,000. Bangkok, Chiang Mai, coastal/island locations."
    ),
    data_gaps=["Annual cap not confirmed", "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_MALAYSIA = JurisdictionIncentiveProfile(
    jurisdiction_code="MY", jurisdiction_name="Malaysia",
    program_slug="my_finas_rebate", program_name="Malaysia FINAS Film Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.35, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=1_000_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="FINAS Malaysia", authority_url_hint="finas.gov.my",
    notes=(
        "Refined — base 30% confirmed unchanged, but a real +5% cultural-"
        "test uplift found (35% ceiling), not previously known. Kuala "
        "Lumpur, Langkawi, rainforest/coastal locations."
    ),
    data_gaps=["Cultural test scoring criteria unconfirmed",
               "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_PHILIPPINES = JurisdictionIncentiveProfile(
    jurisdiction_code="PH", jurisdiction_name="Philippines",
    program_slug="ph_fdcp_flip",
    program_name="Philippines FDCP Film Location Incentive Program (FLIP)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=540_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Film Development Council of the Philippines (FDCP)",
    authority_url_hint="fdcp.ph",
    notes=(
        "Refined — 20-25% range confirmed, plus a real per-production cap "
        "($540,000/PHP 30M) not previously known. Manila, Palawan, "
        "Visayas island locations."
    ),
    data_gaps=["Exact criteria for 20% vs 25% not confirmed",
               "Minimum spend not found", "ATL/VFX/music treatment not confirmed"],
)

_SOUTH_KOREA = JurisdictionIncentiveProfile(
    jurisdiction_code="KR", jurisdiction_name="South Korea",
    program_slug="kr_kofic_location_incentive",
    program_name="South Korea KOFIC Location Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=176_000.0, min_spend_local=44_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Korean Film Council (KOFIC)", authority_url_hint="koreanfilm.or.kr",
    notes=(
        "Confirmed tiered structure: 20% (>3 shoot days, $44K-$700K spend), "
        "25% ceiling (>10 shoot days, >=$700K spend). Cap is real and small "
        "-- ~$176,000 per grant, a binding constraint for any production "
        "above token scale. Seoul, Busan, DMZ, diverse modern/traditional "
        "settings; deep crew base (major domestic film/TV industry)."
    ),
    data_gaps=["Not dated to a specific year in sources found",
               "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_MEXICO = JurisdictionIncentiveProfile(
    jurisdiction_code="MX", jurisdiction_name="Mexico",
    program_slug="mx_federal_film_incentive_2026",
    program_name="Mexico Federal Film & Audiovisual Production Tax Incentive",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.30, max_rate=0.30, is_refundable=False, is_transferable=True,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=True, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=True,  # Baja Studios (Fox Baja) has the world's largest
                            # purpose-built water tank complex -- common
                            # industry knowledge, not independently sourced
    has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="IMCINE / Mexican federal government",
    authority_url_hint="gob.mx",
    notes=(
        "A genuinely NEW program (federal law published in the Official "
        "Gazette, effective 30 March 2026 through 30 September 2030), NOT "
        "a correction of the pre-existing catalog entry -- that entry "
        "(EFICINE, Art. 226) is a DIFFERENT, older program for investors "
        "in Mexican-content film, left untouched, not modeled here. "
        "Confirmed directly from Baker McKenzie (major international law "
        "firm), corroborated by KPMG/FisherBroyles: 30% on qualifying "
        "Mexico-incurred costs. Individual cap MXN 40M, annual program "
        "cap MXN 400M (not converted -- no sourced MXN/USD FX rate). Min "
        "spend MXN 40M (feature). Transferable up to 70%, NOT refundable. "
        "Requires >=70% national supply + Technical Committee "
        "certification. Baja Studios (Fox Baja): world's largest "
        "purpose-built water tank complex (Titanic, many marine "
        "productions) -- common industry knowledge."
    ),
    data_gaps=[
        "MXN/USD FX rate not in this project's sourced FX table",
        "70%-national-supply requirement not modeled -- no supply-chain "
        "fact exists",
        "Interaction with the separate, older EFICINE program (Art. 226) "
        "not evaluated -- both may be real, distinct, potentially "
        "stackable programs, not reconciled this phase",
    ],
)

_CHILE = JurisdictionIncentiveProfile(
    jurisdiction_code="CL", jurisdiction_name="Chile",
    program_slug="cl_corfo_incentive", program_name="Chile CORFO Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.40, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=1_000_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="CORFO (Corporación de Fomento de la Producción)",
    authority_url_hint="corfo.cl",
    notes=(
        "CORRECTED -- stale 20-30% catalog figure superseded by a real "
        "increase to a flat 40%, confirmed via Entertainment Partners' "
        "Spring 2026 global incentive roundup. Min spend $1,000,000 "
        "confirmed directly. Patagonia, Atacama Desert, coastal locations."
    ),
    data_gaps=["Annual cap not confirmed", "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_ISRAEL = JurisdictionIncentiveProfile(
    jurisdiction_code="IL", jurisdiction_name="Israel",
    program_slug="il_foreign_production_fund",
    program_name="Israel Fund for the Promotion of Foreign Productions",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=4_800_000.0, min_spend_local=50_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=True, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Israel Ministry of Economy & Industry",
    authority_url_hint="gov.il",
    notes=(
        "Refined -- 30% base + 10% post/animation uplift (40% ceiling), "
        "corroborated by Hollywood Reporter/Times of Israel across "
        "multiple years. Cap $4,800,000. NOT confirmed specifically for "
        "2026 in any source checked -- disclosed as a real gap, not "
        "assumed unchanged. Mediterranean coastline, diverse ancient/"
        "modern settings."
    ),
    data_gaps=["Not confirmed for 2026 specifically -- program appears "
               "stable since ~2017 but this is an assumption, not a fact",
               "ATL/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_JAPAN = JurisdictionIncentiveProfile(
    jurisdiction_code="JP", jurisdiction_name="Japan",
    program_slug="jp_vipo_location_incentive",
    program_name="Japan VIPO Location Incentive Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.50, max_rate=0.50, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="VIPO (Visual Industry Promotion Organization)",
    authority_url_hint="vipo.or.jp",
    notes=(
        "NEW jurisdiction. Confirmed via multiple entertainment-industry "
        "sources (Variety, Deadline, Screen Daily) plus vipo.or.jp: up to "
        "50% cash rebate, recently expanded (Dec 2025) with multi-year "
        "subsidies for co-productions spanning up to two years. Deep "
        "crew base and studio infrastructure."
    ),
    data_gaps=["Minimum spend and cap not confirmed",
               "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_EGYPT = JurisdictionIncentiveProfile(
    jurisdiction_code="EG", jurisdiction_name="Egypt",
    program_slug="eg_empc_cashback",
    program_name="Egypt EMPC (Media Production City) Cashback",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Egyptian Media Production City (EMPC)",
    authority_url_hint="egyptfilm.gov.eg",
    notes=(
        "NEW jurisdiction. The pre-existing catalog entry explicitly said "
        "'No confirmed formal percentage rebate' (a genuine prior "
        "absence, not a stale figure) -- this is a real, NEW, facility-"
        "specific program: 30% cashback on EMPC studio spend, 20% "
        "off-site supplement (Giza/Luxor/Red Sea), but ONLY for "
        "productions with a genuine EMPC studio anchor component -- "
        "productions shooting entirely on location cannot claim this at "
        "all. Financing friction modeled HIGH to reflect the structural "
        "eligibility gate."
    ),
    data_gaps=["EMPC-anchor eligibility gate not modeled -- no fact "
               "tracks studio-anchor usage, so eligibility itself (not "
               "just rate) cannot be pre-evaluated",
               "Minimum spend and cap not specified in source",
               "VAT, withholding tax, payroll burden not verified"],
)

_PANAMA = JurisdictionIncentiveProfile(
    jurisdiction_code="PA", jurisdiction_name="Panama",
    program_slug="pa_film_rebate", program_name="Panama Film Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=500_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Panama Film Commission", authority_url_hint="panamafilmcommission.com",
    notes=("NEW -- catalog said 'no confirmed formal rebate,' a real 25% flat "
           "cash rebate found, corroborated by 2 sources. Panama City, Canal "
           "Zone, Darien jungle, archipelago islands."),
    data_gaps=["Annual cap not confirmed", "ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_COSTA_RICA = JurisdictionIncentiveProfile(
    jurisdiction_code="CR", jurisdiction_name="Costa Rica",
    program_slug="cr_tax_return_incentive",
    program_name="Costa Rica Tax Return Cash Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.117, max_rate=0.117, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Costa Rica Film Commission (CINDE/PROCOMER)",
    authority_url_hint="costaricafilm.com",
    notes=("NEW -- catalog said 'no formal rebate confirmed.' Single-source "
           "(screendaily.com, not corroborated) finding: a tax-paid refund "
           "mechanism (90% of taxes paid), netting to an average effective "
           "~11.7% of total CR expenditure. Structurally distinct from a "
           "spend-percentage rebate -- disclosed. Rainforest, volcanoes, "
           "beaches."),
    data_gaps=["Single-source figure, not independently corroborated",
               "The 11.7% is described as an average, not a guaranteed rate",
               "ATL/VFX/music treatment not confirmed"],
)

_GHANA = JurisdictionIncentiveProfile(
    jurisdiction_code="GH", jurisdiction_name="Ghana",
    program_slug="gh_film_tax_incentive", program_name="Ghana Film Tax Incentive",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.20, max_rate=0.20, is_refundable=None, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="National Film Authority (Ghana)", authority_url_hint="nfa.gov.gh",
    notes=("NEW -- catalog said 'no confirmed formal rebate.' Real program "
           "announced Feb 2024: 20% tax rebate + import duty/port tax "
           "exemptions. 2026 operational status not independently "
           "confirmed -- financing friction modeled HIGH to reflect this."),
    data_gaps=["2026 operational status not confirmed", "Minimum spend and cap unknown",
               "ATL/VFX/music treatment not confirmed"],
)

_FIJI = JurisdictionIncentiveProfile(
    jurisdiction_code="FJ", jurisdiction_name="Fiji",
    program_slug="fj_film_rebate", program_name="Fiji Film Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.20, is_refundable=True, is_transferable=False,
    annual_cap_local=1_750_000.0, min_spend_local=110_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Fiji Audio Visual Commission", authority_url_hint="unctad.org",
    notes=("Confirmed via UNCTAD: 20% rebate, min spend $110,000, cap "
           "$1,750,000, requires locally registered company. Real "
           "production history (Survivor, Blue Lagoon). Strong tropical "
           "marine access."),
    data_gaps=["ATL/VFX/music treatment not confirmed",
               "VAT, withholding tax, payroll burden not verified"],
)

_GEORGIA_COUNTRY = JurisdictionIncentiveProfile(
    jurisdiction_code="GE", jurisdiction_name="Georgia (country)",
    program_slug="ge_film_rebate", program_name="Georgia (country) Film Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Georgian National Film Center", authority_url_hint="georgia.org",
    notes=("Confirmed via georgia.org (official government portal): 20-25% "
           "rebate on qualified expenses. Caucasus mountains, Black Sea "
           "coast, Tbilisi historic architecture. Distinct from US-GA "
           "(American state), already modeled separately."),
    data_gaps=["Exact criteria for 20% vs 25% not confirmed",
               "Minimum spend and cap unknown",
               "ATL/VFX/music treatment not confirmed"],
)

_TAIWAN = JurisdictionIncentiveProfile(
    jurisdiction_code="TW", jurisdiction_name="Taiwan",
    program_slug="tw_bamid_rebate", program_name="Taiwan TFAI/BAMID Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Bureau of Audiovisual and Music Industry Development (BAMID)",
    authority_url_hint="bamid.gov.tw",
    notes=("30% base rate confirmed, but the program is real and "
           "COMPETITIVE/'highly selective' -- not an automatic "
           "entitlement, financing friction modeled HIGH to reflect "
           "this. Taipei, Taroko Gorge, Sun Moon Lake, Jiufen locations."),
    data_gaps=["Competitive-selection odds not modeled",
               "Minimum spend and cap unknown",
               "ATL/VFX/music treatment not confirmed"],
)

_KAZAKHSTAN = JurisdictionIncentiveProfile(
    jurisdiction_code="KZ", jurisdiction_name="Kazakhstan",
    program_slug="kz_investment_subsidy",
    program_name="Kazakhstan Investment Subsidy Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=850_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Kazakhstan Ministry of Culture and Information",
    authority_url_hint="mbrellafilms.com",
    notes=("Single source (mbrellafilms.com, not corroborated): 30% "
           "rebate, min spend $850,000. Steppe, mountains, Almaty. "
           "Landlocked -- no marine access."),
    data_gaps=["Single-source figure, not independently corroborated",
               "Annual cap and ATL/VFX/music treatment not confirmed"],
)

_ALBANIA = JurisdictionIncentiveProfile(
    jurisdiction_code="AL", jurisdiction_name="Albania",
    program_slug="al_cash_rebate", program_name="Albania Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.35, max_rate=0.35, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Albanian National Center for Cinematography",
    authority_url_hint="invest-in-albania.org",
    notes=("CORRECTED -- stale 20% catalog figure superseded by a real "
           "new cinema law: 35%, confirmed by 2 sources. Adriatic/Ionian "
           "coastline."),
    data_gaps=["Minimum spend, cap, ATL/VFX/music treatment not confirmed"],
)

_MONTENEGRO = JurisdictionIncentiveProfile(
    jurisdiction_code="ME", jurisdiction_name="Montenegro",
    program_slug="me_cash_rebate", program_name="Montenegro Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Montenegro Film Commission", authority_url_hint="mbrellafilms.com",
    notes=("CORRECTED -- stale 20% catalog figure superseded: 25%. "
           "Adriatic coastline, Bay of Kotor."),
    data_gaps=["Minimum spend, cap, ATL/VFX/music treatment not confirmed"],
)

_NORTH_MACEDONIA = JurisdictionIncentiveProfile(
    jurisdiction_code="MK", jurisdiction_name="North Macedonia",
    program_slug="mk_cash_rebate", program_name="North Macedonia Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.20, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="North Macedonia Film Agency",
    authority_url_hint="filmagency.mk",
    notes=("Confirmed unchanged: 20%. Landlocked -- no marine access."),
    data_gaps=["Minimum spend, cap, ATL/VFX/music treatment not confirmed"],
)

_US_NEVADA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-NV", jurisdiction_name="Nevada",
    program_slug="us_nv_film_credit", program_name="Nevada Film Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.12, max_rate=0.25, is_refundable=False, is_transferable=True,
    annual_cap_local=10_000_000.0, min_spend_local=500_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Nevada Film Office", authority_url_hint="shamelstudio.com+wrapbook.com",
    notes=("CORRECTED -- stale 15%/47% catalog figures superseded: 12% "
           "base, 25% ceiling via +5% resident-crew / +5% rural-county "
           "uplifts. Separate $6M per-project cap alongside $10M annual "
           "program cap not modeled (single-cap schema)."),
    data_gaps=["Per-project cap ($6M) not modeled", "ATL/VFX/music treatment not confirmed"],
)

_US_RHODE_ISLAND = JurisdictionIncentiveProfile(
    jurisdiction_code="US-RI", jurisdiction_name="Rhode Island",
    program_slug="us_ri_film_credit", program_name="Rhode Island Motion Picture Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.30, max_rate=0.30, is_refundable=None, is_transferable=None,
    annual_cap_local=40_000_000.0, min_spend_local=100_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Rhode Island Film & TV Office", authority_url_hint="film.ri.gov",
    notes=("Confirmed unchanged: 30% flat, official film.ri.gov source. "
           "$100K min spend / 51%-in-state waived at $10M+ QPE. $7M "
           "per-project cap (waivable) alongside $40M annual cap not "
           "modeled. Cap conflict: wrapbook.com separately cites $30M -- "
           "official $40M used, conflict flagged not dropped. Narragansett "
           "Bay coastline. Sunsets 2027-07-01."),
    data_gaps=["Refundability/transferability not stated by sources checked",
               "Per-project cap ($7M) not modeled", "ATL/VFX/music treatment not confirmed"],
)

_TRINIDAD_TOBAGO = JurisdictionIncentiveProfile(
    jurisdiction_code="TT", jurisdiction_name="Trinidad and Tobago",
    program_slug="tt_production_expenditure_rebate",
    program_name="Trinidad and Tobago Production Expenditure Rebate Programme",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.125, max_rate=0.35, is_refundable=None, is_transferable=None,
    annual_cap_local=8_000_000.0, min_spend_local=100_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="FilmTT", authority_url_hint="ttbizlink.gov.tt",
    notes=("Official govt portal confirmed: non-national tiered rebate "
           "12.5%/15%/35% by spend threshold ($100K/$500K/$1M), +20% "
           "local-labor uplift. $8M project cap. ep.com's 'Dec 31 2024 "
           "sunset' conflicts with the official page (no sunset stated) "
           "-- official source used, conflict flagged. Caribbean coastline."),
    data_gaps=["Refundability/transferability not stated by sources checked",
               "Sunset-date cross-source conflict (ep.com vs. official) unresolved"],
)

_QATAR = JurisdictionIncentiveProfile(
    jurisdiction_code="QA", jurisdiction_name="Qatar",
    program_slug="qa_screen_production_incentive",
    program_name="Qatar Screen Production Incentive (QSPI)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.40, max_rate=0.50, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Film Committee, Media City Qatar", authority_url_hint="screendaily.com",
    notes=("Single-source (screendaily.com), not further corroborated: 40% "
           "base + discretionary 10% Qatari-talent/training/culture uplift "
           "= 50% ceiling. Applications opened Q2 2026. Up to 25% of QPE "
           "may be filmed in neighboring Arab countries and still qualify. "
           "Min spend / caps not stated in the source -- left UNKNOWN."),
    data_gaps=["Min spend not stated", "Caps not stated",
               "Single-source only -- not corroborated by a second outlet"],
)

_UZBEKISTAN = JurisdictionIncentiveProfile(
    jurisdiction_code="UZ", jurisdiction_name="Uzbekistan",
    program_slug="uz_film_rebate", program_name="Uzbekistan Film Rebate Programme",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.10, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=315_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Film in Uzbekistan platform (launching by 2026-11-01)",
    authority_url_hint="tashkenttimes.uz",
    notes=("Brand-new program (Cabinet Resolution 2026-07-08): 10-25% "
           "rebate by undisclosed investment-size schedule, ~$315K "
           "(4bn soum) per-project cap. Silk Road historic sites, Central "
           "Asian steppe/mountain landscapes. Landlocked -- no marine access."),
    data_gaps=["Exact investment-size tier breakpoints not disclosed",
               "Minimum spend threshold not specified",
               "Program administratively brand-new -- application platform not yet live"],
)

_MONGOLIA = JurisdictionIncentiveProfile(
    jurisdiction_code="MN", jurisdiction_name="Mongolia",
    program_slug="mn_production_incentive", program_name="Mongolia Film & TV Production Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.45, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=500_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Mongolian National Film Council", authority_url_hint="montsame.mn",
    notes=("Parliament-approved cash rebate, not tax-linked: 30% base "
           "(min $500K spend) + 10% culture/heritage uplift + 5% "
           "foreign-crew uplift = 45% ceiling, independently stackable. "
           "Steppe, Gobi Desert, nomadic-culture locations. Landlocked."),
    data_gaps=["Annual/per-project cap not stated", "ATL/VFX/music treatment not confirmed"],
)

_SWITZERLAND = JurisdictionIncentiveProfile(
    jurisdiction_code="CH", jurisdiction_name="Switzerland",
    program_slug="ch_pics_national_rebate", program_name="Switzerland PICS National Location Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=741_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Swiss Films / PICS", authority_url_hint="filmincentive.com",
    notes=("National PICS scheme: 20-40% band, targets international "
           "co-productions, CHF 600K ($741K) per-project cap. Separate "
           "cantonal funds (Geneva/Zurich/Valais/Neuchatel) stack on top, "
           "not modeled. Alps, lakes -- limited marine (freshwater only)."),
    data_gaps=["Min spend not disclosed", "Exact 20-40% scaling criteria not disclosed",
               "Cantonal stacking funds not modeled"],
)

_SLOVENIA = JurisdictionIncentiveProfile(
    jurisdiction_code="SI", jurisdiction_name="Slovenia",
    program_slug="si_cash_rebate", program_name="Slovenia Cash Rebate Scheme",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Slovenian Film Centre", authority_url_hint="filminslovenia.si",
    notes=("Official source confirmed: 'up to 25%' ceiling on acknowledged "
           "(post)production expenses. Requires an eligible Slovenian "
           "producer/co-producer/service-provider applicant with prior "
           "screen credit. No min spend or cap disclosed."),
    data_gaps=["Min spend not disclosed", "Cap not disclosed"],
)

_UKRAINE = JurisdictionIncentiveProfile(
    jurisdiction_code="UA", jurisdiction_name="Ukraine",
    program_slug="ua_cash_rebate", program_name="Ukraine Cash Rebate for Foreign Film Producers",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.045, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Ukraine State Film Agency", authority_url_hint="usfa.gov.ua",
    notes=("Statute-confirmed, president-signed rebate: 4.5% floor, 25% "
           "with a VAT-registered Ukrainian production-agreement partner, "
           "+5% Ukrainian-literary-work uplift = 30% ceiling. MATERIAL "
           "UNMODELED RISK: active state of war -- real-world production "
           "feasibility/safety is not captured by the rate schema and "
           "must be evaluated separately before any allocation."),
    data_gaps=["Min spend not disclosed", "Cap not disclosed",
               "Active-conflict operational feasibility not modeled by this schema"],
)

_PORTUGAL = JurisdictionIncentiveProfile(
    jurisdiction_code="PT", jurisdiction_name="Portugal",
    program_slug="pt_scri_pt_cash_rebate", program_name="Portugal SCRI.PT Cash Rebate Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="ICA (Instituto do Cinema e do Audiovisual)", authority_url_hint="ica-ip.pt",
    notes=("New SCRI.PT program (Decree-Law 57/2026): 30% first EUR 2M "
           "QPE, 25% excess (real graduated bracket); flat 30% outside "
           "Lisbon/Porto. EUR 350M budget 2026-2029. A separate 'large-"
           "scale' >=EUR 2.5M track exists -- relationship to the 30/25 "
           "bracket unconfirmed. Atlantic coastline, Lisbon/Porto/Algarve."),
    data_gaps=["Min spend for the base bracket not disclosed",
               "Relationship between the 30/25 bracket and the EUR 2.5M "
               "large-scale track not confirmed"],
)

_AUSTRALIA_SA = JurisdictionIncentiveProfile(
    jurisdiction_code="AU-SA", jurisdiction_name="Australia — South Australia",
    program_slug="au_sa_pdv_rebate", program_name="South Australia PDV Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.10, max_rate=0.10, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=False, btl_qualifies=False, vfx_qualifies=True, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="South Australian Film Corporation", authority_url_hint="safilm.com.au",
    notes=("Official source confirmed: 10% state rebate on PDV spend "
           "ONLY (not general production QPE), stacks with the AUS "
           "federal 30% PDV offset for 40% combined on PDV. Separate "
           "payroll-tax exemption (up to 4.95%) not modeled -- not a QPE "
           "rate. Genuinely narrow-scope, PDV/post-only incentive."),
    data_gaps=["Does not cover general ATL/BTL production spend -- PDV-only",
               "Payroll tax exemption disclosed but not modeled"],
)

_US_WASHINGTON = JurisdictionIncentiveProfile(
    jurisdiction_code="US-WA", jurisdiction_name="Washington",
    program_slug="us_wa_motion_picture_competitiveness", program_name="Washington State Motion Picture Competitiveness Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.45, is_refundable=True, is_transferable=False,
    annual_cap_local=3_500_000.0, min_spend_local=500_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Washington Filmworks", authority_url_hint="washingtonfilmworks.com",
    notes=("CORRECTED -- stale 15% base superseded: 30-35% base, stacks "
           "to 45% via Enhanced Incentives. Competitive/oversubscribed "
           "~$3.5M annual fund. Pacific coastline, Puget Sound."),
    data_gaps=["Exact Enhanced Incentive stacking criteria not disclosed"],
)

_US_ILLINOIS = JurisdictionIncentiveProfile(
    jurisdiction_code="US-IL", jurisdiction_name="Illinois",
    program_slug="us_il_film_production_services_credit", program_name="Illinois Film Production Services Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.30, max_rate=0.35, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=None, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Illinois Film Office", authority_url_hint="greenslate.com",
    notes=("SB 1911 (signed): 30% base confirmed, 35% ceiling via "
           "in-state-labor/vendor uplifts, extended through 2038. "
           "Chicago studio infrastructure, Great Lakes (limited marine)."),
    data_gaps=["Exact resident-labor uplift criteria not disclosed"],
)

_US_NORTH_CAROLINA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-NC", jurisdiction_name="North Carolina",
    program_slug="us_nc_film_entertainment_grant", program_name="North Carolina Film & Entertainment Grant",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=None, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="NC Film Office", authority_url_hint="greenslate.com",
    notes=("25% carried forward from catalog, not re-confirmed against a "
           "dedicated primary source this pass (only the 4% loan-out "
           "withholding rate was found). Atlantic coastline, Outer Banks."),
    data_gaps=["Headline rate not independently re-confirmed this pass"],
)

_US_SOUTH_CAROLINA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-SC", jurisdiction_name="South Carolina",
    program_slug="us_sc_film_production_credit", program_name="South Carolina Film Production Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.20, max_rate=0.30, is_refundable=None, is_transferable=None,
    annual_cap_local=15_500_000.0, min_spend_local=1_000_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="SC Film Commission", authority_url_hint="shamelstudio.com",
    notes=("Official-adjacent source confirmed: 20% base, up to 30% with "
           "uplifts, $1M min spend, $15.5M annual cap. Atlantic coastline."),
    data_gaps=["Exact uplift criteria for the 30% ceiling not disclosed"],
)

_US_MASSACHUSETTS = JurisdictionIncentiveProfile(
    jurisdiction_code="US-MA", jurisdiction_name="Massachusetts",
    program_slug="us_ma_film_tax_credit", program_name="Massachusetts Film Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.25, is_refundable=False, is_transferable=True,
    annual_cap_local=None, min_spend_local=50_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Massachusetts Film Office", authority_url_hint="shamelstudio.com",
    notes=("Confirmed unchanged: 25% transferable, no annual cap, $50K "
           "min spend. Atlantic coastline, Boston studio infrastructure."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): internal rate-rule conditions carried no eligibility/operational facts (local entity, cultural test, preapproval, transferability, timing) beyond what is already recorded above; a primary-source pass is needed to populate app.data.program_requirements for this program."],
)

_US_TEXAS = JurisdictionIncentiveProfile(
    jurisdiction_code="US-TX", jurisdiction_name="Texas",
    program_slug="us_tx_miip", program_name="Texas Moving Image Industry Incentive Program (MIIP)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.05, max_rate=0.31, is_refundable=True, is_transferable=False,
    annual_cap_local=200_000_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Texas Film Commission", authority_url_hint="greenslate.com",
    notes=("5% base tier confirmed, $200M annual cap NEW. Stackable "
           "bonuses could reach 31% starting 2026-09-01 with added "
           "post-production/crew-payroll criteria. Gulf coastline."),
    data_gaps=["Exact 2026-09-01 stackable-bonus tier schedule not disclosed"],
)

_US_CONNECTICUT = JurisdictionIncentiveProfile(
    jurisdiction_code="US-CT", jurisdiction_name="Connecticut",
    program_slug="us_ct_film_tax_credit", program_name="Connecticut Film Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.10, max_rate=0.10, is_refundable=None, is_transferable=True,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="CT Office of Film, TV & Digital Media", authority_url_hint="greenslate.com",
    notes=("10% floor carried forward; 'no annual cap' newly confirmed. "
           "Real program is historically tiered up to 30% by CT spend -- "
           "exact current tier thresholds not confirmed this pass."),
    data_gaps=["Full tier schedule (commonly cited up to 30%) not confirmed this pass"],
)

_US_PENNSYLVANIA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-PA", jurisdiction_name="Pennsylvania",
    program_slug="us_pa_film_production_credit", program_name="Pennsylvania Film Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.30, is_refundable=None, is_transferable=True,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="PA Film Office", authority_url_hint="greenslate.com",
    notes=("25% base confirmed, 30% ceiling with unconfirmed criteria. "
           "Philadelphia/Pittsburgh studio infrastructure."),
    data_gaps=["Exact 30%-ceiling criteria not disclosed"],
)

_US_MARYLAND = JurisdictionIncentiveProfile(
    jurisdiction_code="US-MD", jurisdiction_name="Maryland",
    program_slug="us_md_film_production_activity_credit", program_name="Maryland Film Production Activity Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.28, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=12_000_000.0, min_spend_local=250_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Maryland Dept of Commerce", authority_url_hint="commerce.maryland.gov",
    notes=("CORRECTED -- stale 25% superseded via official "
           "commerce.maryland.gov: up to 28% standard productions (30% for "
           "television series), $12M FY2026 certification cap, USD 250,000 "
           "min spend (USD 25,000 / USD 125,000-cap for the separate "
           "'Maryland Small Film' category). Allocation is FIRST-COME-"
           "FIRST-SERVED against the certification cap, not competitive as "
           "an earlier DISCOVERY-tier note had assumed. Chesapeake Bay "
           "coastline."),
    data_gaps=["Exact ATL/VFX/music qualification scope not confirmed against the current regulation text."],
)

_US_VIRGINIA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-VA", jurisdiction_name="Virginia",
    program_slug="us_va_motion_picture_credit", program_name="Virginia Motion Picture Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.15, max_rate=0.15, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Virginia Film Office", authority_url_hint="catalog-unchallenged",
    notes=("15% carried forward from catalog, not re-confirmed this "
           "pass -- no dedicated source surfaced. Atlantic/Chesapeake coastline."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_US_COLORADO = JurisdictionIncentiveProfile(
    jurisdiction_code="US-CO", jurisdiction_name="Colorado",
    program_slug="us_co_film_incentive", program_name="Colorado Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.20, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Colorado Office of Film, TV & Media", authority_url_hint="catalog-unchallenged",
    notes=("20% carried forward from catalog, not re-confirmed this pass "
           "(only a 1099/withholding procedural change was found). "
           "Rocky Mountains, no marine access."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_US_TENNESSEE = JurisdictionIncentiveProfile(
    jurisdiction_code="US-TN", jurisdiction_name="Tennessee",
    program_slug="us_tn_performance_grant", program_name="Tennessee Film, Entertainment & Music Commission Performance Grant",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=True,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="TN Entertainment Commission", authority_url_hint="saturation.io",
    notes=("First confirmed rate for this catalog entry (was None): 25% "
           "for Nashville-metro/tier-1 areas, plus undisclosed-magnitude "
           "bonuses for tier 2-4 rural counties. Music-industry hub."),
    data_gaps=["Tier 2-4 bonus magnitude not disclosed"],
)

_US_OKLAHOMA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-OK", jurisdiction_name="Oklahoma",
    program_slug="us_ok_film_enhancement_rebate", program_name="Oklahoma Film Enhancement Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Oklahoma Film + Music Office", authority_url_hint="greenslate.com",
    notes=("CONFLICT: fresh source gives 20-30%, pre-existing catalog "
           "claimed 35% -- unresolved, fresher/dedicated source used, "
           "35% flagged not dropped."),
    data_gaps=["35% vs 20-30% conflict with prior catalog figure unresolved"],
)

_US_ALABAMA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-AL", jurisdiction_name="Alabama",
    program_slug="us_al_film_incentive", program_name="Alabama Film Incentive",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.45, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Alabama Film Office", authority_url_hint="greenslate.com",
    notes=("25% general program confirmed. NEW (HB379, eff. 2026-10-01): "
           "separate 45% rebate on AL-resident PAYROLL ONLY for small-"
           "budget productions ($100K-$499,999 total) -- narrow bracket, "
           "not the general ceiling."),
    data_gaps=["45% small-budget tier interacts with general 25% program in an unconfirmed way"],
)

_US_KENTUCKY = JurisdictionIncentiveProfile(
    jurisdiction_code="US-KY", jurisdiction_name="Kentucky",
    program_slug="us_ky_keiia", program_name="Kentucky Entertainment Industry Incentive Act (KEIIA)",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.30, max_rate=0.35, is_refundable=True, is_transferable=False,
    annual_cap_local=75_000_000.0, min_spend_local=250_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.LIMITED,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Kentucky Dept of Revenue", authority_url_hint="revenue.ky.gov",
    notes=("Confirmed exactly: 30% base, up to 35% with uplifts, $250K/"
           "$20K min spend (feature/doc), $75M annual cap."),
    data_gaps=["Exact 35%-ceiling uplift criteria not disclosed"],
)

_CA_ALBERTA = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-AB", jurisdiction_name="Canada — Alberta",
    program_slug="ca_ab_fttc", program_name="Alberta Film and Television Tax Credit (FTTC)",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.22, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Alberta Media Fund", authority_url_hint="thereactionlab.com",
    notes=("22% general tier confirmed, 30% ceiling for Alberta-owned "
           "companies (ownership-based, not spend-based). Rocky "
           "Mountains, landlocked."),
    data_gaps=["Exact Alberta-ownership threshold for the 30% tier not disclosed"],
)

_CA_MANITOBA = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-MB", jurisdiction_name="Canada — Manitoba",
    program_slug="ca_mb_film_video_credit", program_name="Manitoba Film & Video Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.45, max_rate=0.65, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Manitoba Film & Music", authority_url_hint="thereactionlab.com",
    notes=("CORRECTED -- catalog's 45% flat massively undercounted the "
           "real ceiling: 45% base + Frequent Filming 10% + Producer "
           "Bonus 5% + Rural/Northern 5% = up to 65%. One of the "
           "highest-rate jurisdictions in the registry. Landlocked."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): internal rate-rule conditions carried no eligibility/operational facts (local entity, cultural test, preapproval, transferability, timing) beyond what is already recorded above; a primary-source pass is needed to populate app.data.program_requirements for this program."],
)

_CA_NOVA_SCOTIA = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-NS", jurisdiction_name="Canada — Nova Scotia",
    program_slug="ca_ns_production_incentive_fund", program_name="Nova Scotia Film & Television Production Incentive Fund",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Screen Nova Scotia", authority_url_hint="thereactionlab.com",
    notes=("25% base on eligible NS labour confirmed, plus undisclosed-"
           "magnitude rural bonuses. Atlantic coastline, Bay of Fundy."),
    data_gaps=["Rural bonus magnitude not disclosed"],
)

_CA_NEW_BRUNSWICK = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-NB", jurisdiction_name="Canada — New Brunswick",
    program_slug="ca_nb_film_tax_credit", program_name="New Brunswick Film Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Film New Brunswick", authority_url_hint="thereactionlab.com",
    notes=("25%-30% depending on project type: features/mini-series/TV "
           "series all at 30%. Atlantic coastline."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): internal rate-rule conditions carried no eligibility/operational facts (local entity, cultural test, preapproval, transferability, timing) beyond what is already recorded above; a primary-source pass is needed to populate app.data.program_requirements for this program."],
)

_NETHERLANDS = JurisdictionIncentiveProfile(
    jurisdiction_code="NL", jurisdiction_name="Netherlands",
    program_slug="nl_film_production_incentive", program_name="Netherlands Film Production Incentive (NFPI)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Netherlands Film Fund", authority_url_hint="rodriqueslaw.com",
    notes=("30% floor confirmed, 40% ceiling newly found (single source, "
           "not further corroborated). North Sea coastline."),
    data_gaps=["Single-source only -- not corroborated by a second outlet"],
)

_AUSTRIA = JurisdictionIncentiveProfile(
    jurisdiction_code="AT", jurisdiction_name="Austria",
    program_slug="at_fisa_plus", program_name="FISA+ Film Production Support Austria",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.35, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=True,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Austria Wirtschaftsservice (aws)", authority_url_hint="filminaustria.com",
    notes=("CORRECTED -- stale 25% superseded: 30% base + 5% green-filming "
           "bonus = 35% ceiling, confirmed via multiple converging sources "
           "(needafixer.com, progressiveproductions.eu, variety.com 2023). "
           "Cultural (points-based) test IS required -- resolves this "
           "repository's own prior internal inconsistency against the "
           "DISCOVERY catalog entry, which had this correct all along. "
           "Administered by aws (Austria Wirtschaftsservice), with FILM in "
           "AUSTRIA as first point of contact; applications via the AWS "
           "Funding Manager platform (confirmed via direct official fetch). "
           "Alps, landlocked."),
    data_gaps=["Exact cultural-test points threshold and per-format min-spend/annual-cap figures not independently confirmed from an official primary source (secondary aggregators only)."],
)

_CZECH_REPUBLIC = JurisdictionIncentiveProfile(
    jurisdiction_code="CZ", jurisdiction_name="Czech Republic",
    program_slug="cz_film_incentive", program_name="Czech Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=True,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Czech Film Fund (Statni fond audiovize)", authority_url_hint="sfa.gov.cz",
    notes=("CORRECTED -- stale 20% superseded: 25% live-action feature "
           "film rate. A separate 35% animation/digital-only (no live "
           "action) program exists as its own doctrine record "
           "(cz_film_incentive_animation) -- not representable in this "
           "one-profile-per-jurisdiction schema, disclosed here only. "
           "Cultural test IS required -- corrects a prior False, "
           "confirmed via direct official fetch (sfa.gov.cz, 2026-07-26). "
           "Prague Barrandov Studios, landlocked."),
    data_gaps=["Separate 35% animation-only program not representable in this profile", "Changes effective 2026-01-01 referenced by the official page but not detailed in the content retrieved"],
)

_ROMANIA = JurisdictionIncentiveProfile(
    jurisdiction_code="RO", jurisdiction_name="Romania",
    program_slug="ro_film_office_cash_rebate", program_name="Romanian Film Office Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Romanian Film Office", authority_url_hint="aol.com",
    notes=("CONFLICT: catalog claimed 35%, fresh source confirms 30% "
           "current with a possible-but-unconfirmed-effective-date "
           "expansion to 40% in 2026. 30% used as the present-tense-"
           "confirmed figure. Black Sea coastline."),
    data_gaps=["35% vs 30%/40% conflict with prior catalog figure unresolved"],
)

_SERBIA = JurisdictionIncentiveProfile(
    jurisdiction_code="RS", jurisdiction_name="Serbia",
    program_slug="rs_film_commission_cash_rebate", program_name="Serbia Film Commission Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Film Commission Serbia", authority_url_hint="catalog-unchallenged",
    notes=("25% carried forward, not re-confirmed this pass. Landlocked, "
           "Belgrade studio infrastructure."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_ICELAND_GENERAL = JurisdictionIncentiveProfile(
    jurisdiction_code="IS", jurisdiction_name="Iceland",
    program_slug="is_film_reimbursement_scheme", program_name="Icelandic Film Reimbursement Scheme",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.35, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Icelandic Film Centre", authority_url_hint="rodriqueslaw.com",
    notes=("25% base confirmed, 35% ceiling for larger-scale productions "
           "meeting unconfirmed requirements. Dramatic volcanic/glacial "
           "coastline, strong marine access."),
    data_gaps=["Exact larger-scale-production requirements for the 35% ceiling not disclosed"],
)

_AUSTRALIA_NSW = JurisdictionIncentiveProfile(
    jurisdiction_code="AU-NSW", jurisdiction_name="Australia — New South Wales",
    program_slug="au_nsw_pdv_rebate", program_name="New South Wales PDV Rebate (Screen NSW)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.10, max_rate=0.10, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=False, btl_qualifies=False, vfx_qualifies=True, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Screen NSW", authority_url_hint="mbrellafilms.com",
    notes=("CORRECTED -- catalog's 20% conflated two distinct mechanisms: "
           "this models the 10% PDV-only rebate (stacks with AUS federal "
           "30% PDV offset). A separate 'up to 35%' regional-NSW-location "
           "incentive exists but is NOT modeled here (distinct mechanism, "
           "unclear eligibility). Sydney studio infrastructure."),
    data_gaps=["Regional-location 'up to 35%' incentive not modeled -- distinct mechanism"],
)

_AUSTRALIA_QLD = JurisdictionIncentiveProfile(
    jurisdiction_code="AU-QLD", jurisdiction_name="Australia — Queensland",
    program_slug="au_qld_pdv_rebate", program_name="Queensland PDV Rebate (Screen Queensland)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.15, max_rate=0.15, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=False, btl_qualifies=False, vfx_qualifies=True, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Screen Queensland", authority_url_hint="mbrellafilms.com",
    notes=("15% PDV-only rebate confirmed (mirrors AU-SA/AU-NSW pattern), "
           "combines with AUS federal 30% PDV offset. Additional regional "
           "incentives exist, magnitude undisclosed. Great Barrier Reef coastline."),
    data_gaps=["Regional-Queensland uplift magnitude not disclosed"],
)

_COLOMBIA = JurisdictionIncentiveProfile(
    jurisdiction_code="CO", jurisdiction_name="Colombia",
    program_slug="co_film_in_colombia", program_name="Colombia Film Commission — Film In Colombia",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.35, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=90_000_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Colombia Film Commission", authority_url_hint="vitrina.ai",
    notes=("35-40% confirmed, 2026 budget increased 49% to $90M. Both "
           "Caribbean and Pacific coastlines."),
    data_gaps=["Exact 35% vs 40% scaling criteria not disclosed"],
)

_DOMINICAN_REPUBLIC = JurisdictionIncentiveProfile(
    jurisdiction_code="DO", jurisdiction_name="Dominican Republic",
    program_slug="do_film_commission_incentive", program_name="Dominican Republic Film Commission Incentive",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.25, is_refundable=False, is_transferable=True,
    annual_cap_local=None, min_spend_local=500_000.0, requires_cultural_test=False,
    atl_qualifies=True, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="DR Film Commission (DGCINE)", authority_url_hint="vitrina.ai",
    notes=("Confirmed exactly: 25% freely-transferable tax credit on ATL "
           "and BTL, $500K min spend. Caribbean coastline."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): internal rate-rule conditions carried no eligibility/operational facts (local entity, cultural test, preapproval, transferability, timing) beyond what is already recorded above; a primary-source pass is needed to populate app.data.program_requirements for this program."],
)

_SINGAPORE = JurisdictionIncentiveProfile(
    jurisdiction_code="SG", jurisdiction_name="Singapore",
    program_slug="sg_made_with_singapore_rebate", program_name="Made-with-Singapore Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=7_400_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Singapore Film Commission / IMDA", authority_url_hint="lexology.com",
    notes=("Distinct, currently-active scheme found ('Made-with-"
           "Singapore') vs. catalog's 'SFC Production Assistance' "
           "framing. Genuine source ambiguity between 40% (local "
           "spending) and 'up to 30% for certain programs' -- both "
           "disclosed. S$10M fund cap. Small city-state, no rural/marine variety."),
    data_gaps=["30% vs 40% ambiguity in the same source not reconciled"],
)

_UAE_DUBAI = JurisdictionIncentiveProfile(
    jurisdiction_code="AE-DXB", jurisdiction_name="United Arab Emirates — Dubai",
    program_slug="ae_dxb_dpip", program_name="Dubai Production Incentive Programme (DPIP)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.40, max_rate=0.40, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=True, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Dubai Film and TV Commission", authority_url_hint="jjagency.co",
    notes=("NEW 40% rebate effective 2026-06-01, corrects stale 30% "
           "catalog figure filed under the ambiguous bare 'AE' code. "
           "Distinct emirate/commission from AE-AD (Abu Dhabi, already "
           "modeled at 35%/50%). Persian Gulf coastline, major studio infrastructure."),
    data_gaps=["Min spend and annual cap not disclosed"],
)

_BULGARIA = JurisdictionIncentiveProfile(
    jurisdiction_code="BG", jurisdiction_name="Bulgaria",
    program_slug="bg_film_encouragement_act_rebate", program_name="Bulgarian Film Industry Encouragement Act Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Bulgarian National Film Center", authority_url_hint="innovires.com",
    notes=("Confirmed exactly: 25% flat. Black Sea coastline, low cost base."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): "
               "internal rate-rule conditions carried no eligibility/operational facts "
               "(local entity, cultural test, preapproval, transferability, timing) beyond "
               "what is already recorded above; a primary-source pass is needed to populate "
               "app.data.program_requirements for this program."],
)

_ESTONIA = JurisdictionIncentiveProfile(
    jurisdiction_code="EE", jurisdiction_name="Estonia",
    program_slug="ee_film_estonia_rebate", program_name="Film Estonia Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.30, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=True,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.HIGH,
    authority_name="Film Estonia / Estonian Film Institute", authority_url_hint="innovires.com",
    notes=("'Up to 30%' discretionary ceiling requiring Estonian-based "
           "crew/actors and Estonian story/setting. New studio "
           "infrastructure investment underway. Baltic coastline."),
    data_gaps=["Discretionary criteria for reaching the full 30% not fully specified"],
)

_LATVIA = JurisdictionIncentiveProfile(
    jurisdiction_code="LV", jurisdiction_name="Latvia",
    program_slug="lv_national_film_centre_incentive", program_name="National Film Centre of Latvia Production Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="National Film Centre of Latvia", authority_url_hint="camaleonrental.com",
    notes=("Genuinely tiered 20-30% by spend, but source gives two "
           "conflicting tier-threshold schedules -- disclosed, not "
           "reconciled. Baltic coastline."),
    data_gaps=["Two conflicting spend-tier-threshold schedules in the source, not reconciled"],
)

_LITHUANIA = JurisdictionIncentiveProfile(
    jurisdiction_code="LT", jurisdiction_name="Lithuania",
    program_slug="lt_film_centre_cash_rebate", program_name="Lithuanian Film Centre Production Cash Rebate",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.20, max_rate=0.20, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=True,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Lithuanian Film Centre", authority_url_hint="camaleonrental.com",
    notes=("CONFLICT: catalog claimed 30%, fresh source confirms 20% "
           "with a cultural test and a 3-day minimum shoot requirement "
           "(waived for animation). Baltic coastline."),
    data_gaps=["30% vs 20% conflict with prior catalog figure unresolved"],
)

_POLAND = JurisdictionIncentiveProfile(
    jurisdiction_code="PL", jurisdiction_name="Poland",
    program_slug="pl_pisf_cash_rebate", program_name="Polish Film Institute (PISF) Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.25, max_rate=0.30, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.DEEP,
    studio_available=True, post_production_available=True,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Polish Film Institute (PISF)", authority_url_hint="variety.com",
    notes=("Confirmed 25-30% range, part of the Central/Eastern Europe "
           "incentives arms race (variety.com). Baltic coastline, "
           "established studio infrastructure."),
    data_gaps=["Exact 25% vs 30% scaling criteria not disclosed"],
)

_SLOVAKIA = JurisdictionIncentiveProfile(
    jurisdiction_code="SK", jurisdiction_name="Slovakia",
    program_slug="sk_avf_production_incentive", program_name="Slovak Audiovisual Fund (AVF) Production Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.33, max_rate=0.33, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=True, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Slovak Audiovisual Fund (AVF)", authority_url_hint="camaleonrental.com",
    notes=("Confirmed exactly: 33% flat, applies to both ATL and BTL "
           "talent -- unusually broad-scoped for a European rebate. Landlocked."),
    data_gaps=["No ProgramRequirementsProfile exists yet (Pass A migration, 2026-07-26): internal rate-rule conditions carried no eligibility/operational facts (local entity, cultural test, preapproval, transferability, timing) beyond what is already recorded above; a primary-source pass is needed to populate app.data.program_requirements for this program."],
)

_LUXEMBOURG = JurisdictionIncentiveProfile(
    jurisdiction_code="LU", jurisdiction_name="Luxembourg",
    program_slug="lu_filmfund_tax_shelter_rebate", program_name="Film Fund Luxembourg (Filmfund) — Tax Shelter & Rebate",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.30, max_rate=0.40, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Film Fund Luxembourg", authority_url_hint="catalog-unchallenged",
    notes=("30-40% carried forward from catalog, not re-confirmed this "
           "pass. Landlocked, small market."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_US_HAWAII = JurisdictionIncentiveProfile(
    jurisdiction_code="US-HI", jurisdiction_name="Hawaii",
    program_slug="us_hi_film_digital_media_credit", program_name="Hawaii Film and Digital Media Income Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.22, max_rate=0.27, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.EXCELLENT,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=True, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.LOW,
    authority_name="Hawaii Film Office", authority_url_hint="alohastatedaily.com",
    notes=("CORRECTED -- stale 20% flat superseded: 22% Oahu, 27% "
           "neighbor islands. Pending SB 2580 (NOT YET LAW) could add "
           "+5% more for 80%-local-hire productions -- not modeled as "
           "current. World-class Pacific island marine access."),
    data_gaps=["SB 2580 pending -- not yet enacted, not modeled"],
)

_US_UTAH = JurisdictionIncentiveProfile(
    jurisdiction_code="US-UT", jurisdiction_name="Utah",
    program_slug="us_ut_motion_picture_incentive", program_name="Utah Motion Picture Incentive Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.20, max_rate=0.25, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Utah Film Commission", authority_url_hint="catalog-unchallenged",
    notes=("20-25% carried forward, not re-confirmed this pass. Program "
           "confirmed extended through 2030. Desert/mountain landscapes, no marine access."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_US_MINNESOTA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-MN", jurisdiction_name="Minnesota",
    program_slug="us_mn_film_production_credit", program_name="Minnesota Film Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.25, is_refundable=None, is_transferable=True,
    annual_cap_local=25_000_000.0, min_spend_local=1_000_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Explore Minnesota Film", authority_url_hint="revenue.state.mn.us",
    notes=("25% confirmed, USD 1,000,000 min spend (12 consecutive months), "
           "USD 25,000,000 annual cap, first-come-first-served, TRANSFERABLE "
           "('assignable income tax credit') -- corrects a prior None/False "
           "guess -- all confirmed directly via revenue.state.mn.us "
           "(2026-07-26). Applications now run through Explore Minnesota "
           "Film (mnfilmtv.org), which has superseded the previously-cited "
           "'Minnesota Film & TV Board' as the administering body. Multiple "
           "small local/regional add-on rebates (Iron Range, Duluth, Austin "
           "MN, Maple Lake) not individually modeled. Great Lakes region."),
    data_gaps=["Local/regional add-on rebates not individually modeled", "Refundability not confirmed (revenue.state.mn.us did not state it explicitly)"],
)

_US_MISSISSIPPI = JurisdictionIncentiveProfile(
    jurisdiction_code="US-MS", jurisdiction_name="Mississippi",
    program_slug="us_ms_advantage_film_program", program_name="Mississippi Advantage Film Program",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.25, max_rate=0.35, is_refundable=None, is_transferable=None,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.MODERATE,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Mississippi Film Office", authority_url_hint="greenslate.com",
    notes=("25% base confirmed. Catalog's 35% ceiling not re-confirmed "
           "this pass. Gulf coastline."),
    data_gaps=["35% ceiling not independently re-confirmed this pass"],
)

_US_ARIZONA = JurisdictionIncentiveProfile(
    jurisdiction_code="US-AZ", jurisdiction_name="Arizona",
    program_slug="us_az_motion_picture_production", program_name="Arizona Motion Picture Production Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    base_rate=0.15, max_rate=0.20, is_refundable=True, is_transferable=False,
    annual_cap_local=None, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=None,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Arizona Commerce Authority", authority_url_hint="catalog-unchallenged",
    notes=("15-20% carried forward, not re-confirmed this pass. Desert "
           "landscapes, no marine access."),
    data_gaps=["Not independently re-confirmed this pass"],
)

_US_PUERTO_RICO = JurisdictionIncentiveProfile(
    jurisdiction_code="US-PR", jurisdiction_name="Puerto Rico",
    program_slug="us_pr_film_incentives_act", program_name="Puerto Rico Film Industry Economic Incentives Act",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.20, max_rate=0.40, is_refundable=False, is_transferable=True,
    annual_cap_local=38_000_000.0, min_spend_local=50_000.0, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.MEDIUM,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Puerto Rico Film Commission", authority_url_hint="shamelstudio.com",
    notes=("CORRECTED -- catalog's flat 40% was really a 20% base / 40% "
           "ceiling structure. $50K min spend, ~$38M annual cap, 22-26% "
           "payroll burden. Caribbean coastline."),
    data_gaps=["Exact uplift criteria for the 40% ceiling not disclosed"],
)

_CA_SASKATCHEWAN = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-SK", jurisdiction_name="Canada — Saskatchewan",
    program_slug="ca_sk_creative_saskatchewan_grant", program_name="Creative Saskatchewan Film and TV Production Grant",
    confidence_tier="PARSED", incentive_type="direct_grant",
    base_rate=0.25, max_rate=0.30, is_refundable=None, is_transferable=False,
    annual_cap_local=5_000_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=False, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.NONE,
    has_water_tanks=False, has_open_water_filming=False, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="Creative Saskatchewan", authority_url_hint="hellodarwin.com",
    notes=("First confirmed rate for this catalog entry (was None): two "
           "streams -- Service Production 25% (modeled as base) and "
           "Saskatchewan Stream 30% (modeled as ceiling, likely requires "
           "local ownership/content). Prairies, landlocked."),
    data_gaps=["Saskatchewan Stream's local-ownership/content requirement not confirmed"],
)

_CA_NEWFOUNDLAND_LABRADOR = JurisdictionIncentiveProfile(
    jurisdiction_code="CA-NL", jurisdiction_name="Canada — Newfoundland & Labrador",
    program_slug="ca_nl_all_spend_credit", program_name="Newfoundland & Labrador All-Spend Film and Video Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    base_rate=0.40, max_rate=0.45, is_refundable=True, is_transferable=False,
    annual_cap_local=7_400_000.0, min_spend_local=None, requires_cultural_test=False,
    atl_qualifies=None, btl_qualifies=True, vfx_qualifies=None, music_qualifies=None,
    vessel_marine_qualifies=True, resident_labor_uplift_available=False,
    cashflow_timing_weeks=None, marine_suitability=MarineSuitability.STRONG,
    has_water_tanks=False, has_open_water_filming=True, crew_depth_rating=CrewDepth.SHALLOW,
    studio_available=False, post_production_available=False,
    vat_recoverable=None, vat_rate_pct=None, withholding_tax_pct=None, payroll_burden_pct=None,
    financing_friction=FinancingFriction.MEDIUM,
    authority_name="NL Film Development Corporation", authority_url_hint="gov.nl.ca",
    notes=("Official (gov.nl.ca + canada.ca) confirmed 40% base exactly, "
           "CAD $10M per-production cap. Catalog's 45% ceiling not "
           "independently re-confirmed this pass. Atlantic coastline, "
           "icebergs/rugged coast."),
    data_gaps=["45% ceiling not independently re-confirmed this pass"],
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
    "GB": _UNITED_KINGDOM,
    "CA": _CANADA_FEDERAL,
    "CA-BC": _CANADA_BC,
    "CA-ON": _CANADA_ON,
    "CA-QC": _CANADA_QC,
    "AU": _AUSTRALIA,
    "NZ": _NEW_ZEALAND,
    "US-GA": _US_GEORGIA,
    "US-CA": _US_CALIFORNIA,
    "US-NY": _US_NEW_YORK,
    "US-NM": _US_NEW_MEXICO,
    "US-OR": _US_OREGON,
    "US-LA": _US_LOUISIANA,
    "ZA": _SOUTH_AFRICA,
    "AE-AD": _UAE_ABU_DHABI,
    "MA": _MOROCCO,
    "DK": _DENMARK,
    "FI": _FINLAND,
    "NO": _NORWAY,
    "SE": _SWEDEN,
    "SA": _SAUDI_ARABIA,
    "JO": _JORDAN,
    "TH": _THAILAND,
    "MY": _MALAYSIA,
    "PH": _PHILIPPINES,
    "KR": _SOUTH_KOREA,
    "MX": _MEXICO,
    "CL": _CHILE,
    "IL": _ISRAEL,
    "JP": _JAPAN,
    "EG": _EGYPT,
    "PA": _PANAMA,
    "CR": _COSTA_RICA,
    "GH": _GHANA,
    "FJ": _FIJI,
    "GE": _GEORGIA_COUNTRY,
    "TW": _TAIWAN,
    "KZ": _KAZAKHSTAN,
    "AL": _ALBANIA,
    "ME": _MONTENEGRO,
    "MK": _NORTH_MACEDONIA,
    "US-NV": _US_NEVADA,
    "US-RI": _US_RHODE_ISLAND,
    "TT": _TRINIDAD_TOBAGO,
    "QA": _QATAR,
    "UZ": _UZBEKISTAN,
    "MN": _MONGOLIA,
    "CH": _SWITZERLAND,
    "SI": _SLOVENIA,
    "UA": _UKRAINE,
    "PT": _PORTUGAL,
    "AU-SA": _AUSTRALIA_SA,
    "US-WA": _US_WASHINGTON,
    "US-IL": _US_ILLINOIS,
    "US-NC": _US_NORTH_CAROLINA,
    "US-SC": _US_SOUTH_CAROLINA,
    "US-MA": _US_MASSACHUSETTS,
    "US-TX": _US_TEXAS,
    "US-CT": _US_CONNECTICUT,
    "US-PA": _US_PENNSYLVANIA,
    "US-MD": _US_MARYLAND,
    "US-VA": _US_VIRGINIA,
    "US-CO": _US_COLORADO,
    "US-TN": _US_TENNESSEE,
    "US-OK": _US_OKLAHOMA,
    "US-AL": _US_ALABAMA,
    "US-KY": _US_KENTUCKY,
    "CA-AB": _CA_ALBERTA,
    "CA-MB": _CA_MANITOBA,
    "CA-NS": _CA_NOVA_SCOTIA,
    "CA-NB": _CA_NEW_BRUNSWICK,
    "NL": _NETHERLANDS,
    "AT": _AUSTRIA,
    "CZ": _CZECH_REPUBLIC,
    "RO": _ROMANIA,
    "RS": _SERBIA,
    "IS": _ICELAND_GENERAL,
    "AU-NSW": _AUSTRALIA_NSW,
    "AU-QLD": _AUSTRALIA_QLD,
    "CO": _COLOMBIA,
    "DO": _DOMINICAN_REPUBLIC,
    "SG": _SINGAPORE,
    "AE-DXB": _UAE_DUBAI,
    "BG": _BULGARIA,
    "EE": _ESTONIA,
    "LV": _LATVIA,
    "LT": _LITHUANIA,
    "PL": _POLAND,
    "SK": _SLOVAKIA,
    "LU": _LUXEMBOURG,
    "US-HI": _US_HAWAII,
    "US-UT": _US_UTAH,
    "US-MN": _US_MINNESOTA,
    "US-MS": _US_MISSISSIPPI,
    "US-AZ": _US_ARIZONA,
    "US-PR": _US_PUERTO_RICO,
    "CA-SK": _CA_SASKATCHEWAN,
    "CA-NL": _CA_NEWFOUNDLAND_LABRADOR,
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
