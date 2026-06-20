from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GlobalProgramEntry:
    jurisdiction_code: str
    jurisdiction_name: str
    program_name: str
    program_type: str
    base_rate: float | None
    max_rate: float | None
    is_refundable: bool | None
    is_transferable: bool | None
    min_spend_usd: float | None
    annual_cap_usd: float | None
    requires_cultural_test: bool
    requires_local_entity: bool
    confidence_tier: str
    source_title: str
    source_url: str | None
    effective_from: str | None
    notes: str
    unknown_fields: list[str] = field(default_factory=list)


@dataclass
class CostBenchmarkEntry:
    jurisdiction_code: str
    crew_rate_multiplier: float | None
    equipment_rental_multiplier: float | None
    stage_facility_multiplier: float | None
    location_fees_multiplier: float | None
    post_production_multiplier: float | None
    vfx_multiplier: float | None
    catering_multiplier: float | None
    key_crew_daily_travel_usd: float | None
    marine_vessel_multiplier: float | None
    lodging_daily_usd: float | None
    per_diem_daily_usd: float | None
    confidence_tier: str
    data_source: str
    as_of_date: str
    notes: str


ALL_PROGRAMS: list[GlobalProgramEntry] = [
    GlobalProgramEntry(
        jurisdiction_code="US",
        jurisdiction_name="United States",
        program_name="State Film Tax Credits (Multi-State)",
        program_type="tax_credit",
        base_rate=None,
        max_rate=0.40,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="PARSED",
        source_title="Various state film office program summaries",
        source_url=None,
        effective_from=None,
        notes=(
            "No federal film incentive exists. State programmes vary from 15% (refundable) "
            "to 40% (Georgia, transferable). This entry represents the multi-state tier; "
            "individual state programs are modeled separately."
        ),
        unknown_fields=[
            "federal_program",
            "state_aggregate_cap",
            "residency_thresholds_by_state",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="Canada Production Tax Credit (CPTC) + Provincial Credits",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.65,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="CRA T4283; CAVCO Programme Guidelines",
        source_url="https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits.html",
        effective_from="2023-01-01",
        notes=(
            "Federal CPTC + provincial stacking. Ontario: OPSTC 21.5% on qualifying Ontario labour. "
            "BC: PSTC 28% on qualifying BC labour. Quebec: QPRDP 20% on qualifying Quebec labour."
        ),
        unknown_fields=[
            "provincial_cap_details",
            "cad_usd_rate_for_cap_calculation",
            "cavco_60pct_labour_cap_interaction",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="UK Audio Visual Expenditure Credit (AVEC)",
        program_type="tax_credit",
        base_rate=0.34,
        max_rate=0.39,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_600_000.0,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="HMRC Creative Industries Tax Relief — AVEC guidance",
        source_url="https://www.gov.uk/guidance/corporation-tax-creative-industry-tax-reliefs",
        effective_from="2024-01-01",
        notes=(
            "Replaced HETV/Film Tax Relief from Jan 2024. Gross credit 34% (film/HETV), "
            "39% (children's/animation). After 25% CT: net 25.5% / 29.25%. "
            "UK qualifying spend (UKQS) only."
        ),
        unknown_fields=[
            "atl_qualifying_cap_details",
            "animation_definition_threshold",
            "treaty_co_production_interaction",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="IE",
        jurisdiction_name="Ireland",
        program_name="Section 481 Film Tax Credit",
        program_type="tax_credit",
        base_rate=0.32,
        max_rate=0.32,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=250_000.0,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="Revenue Commissioners — Film Relief: Section 481 TCA 1997",
        source_url="https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx",
        effective_from="2015-01-01",
        notes=(
            "32% credit on eligible Irish expenditure. Max credit per film €70M. "
            "Payable over multiple years — not instant cash."
        ),
        unknown_fields=[
            "annual_programme_allocation_cap",
            "total_budget_ceiling_for_uplift",
            "foreign_crew_qualifying_threshold",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="MT",
        jurisdiction_name="Malta",
        program_name="Malta Film Commission Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=55_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="PARSED",
        source_title="Malta Film Commission Rebate Programme Guidelines",
        source_url="https://maltafilmcommission.com/rebate",
        effective_from="2022-01-01",
        notes=(
            "Base 25%, uplifted to 40% on Maltese content/digital platforms uplift. "
            "All ATL and BTL qualifying. Vessel/marine qualifying. No cultural test. "
            "MFS water tank available."
        ),
        unknown_fields=[
            "exact_uplift_thresholds",
            "annual_programme_allocation_cap",
            "rebate_assignability_to_gap_lender",
            "confirmed_processing_timeline",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="GR",
        jurisdiction_name="Greece",
        program_name="Greece Cash Rebate for International Productions",
        program_type="cash_rebate",
        base_rate=0.40,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=110_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="PARSED",
        source_title="Enterprise Greece — Film Investment Office",
        source_url="https://enterprisegreece.gov.gr",
        effective_from="2020-01-01",
        notes=(
            "40% on qualifying Greek expenditure. ATL and BTL including marine qualifying. "
            "Processing 9-12 months per market reports."
        ),
        unknown_fields=[
            "annual_allocation_cap_amount",
            "wht_on_international_cast_reduction",
            "rebate_assignability_to_financier",
            "confirmed_processing_timeline",
            "foreign_crew_local_entity_requirements",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="CY",
        jurisdiction_name="Cyprus",
        program_name="Cyprus Film Production Rebate",
        program_type="cash_rebate",
        base_rate=0.35,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=None,
        min_spend_usd=110_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=None,
        confidence_tier="DISCOVERY",
        source_title="CIPA / Deputy Ministry of Tourism — Film Production Rebate [NOT YET ACQUIRED]",
        source_url="https://cipa.org.cy",
        effective_from=None,
        notes=(
            "35% rate assumed from DISCOVERY sources. Programme run jointly by CIPA and "
            "Deputy Ministry of Tourism. Cyprus 12.5% corporate tax useful for "
            "co-production entity domicile."
        ),
        unknown_fields=[
            "confirmed_rate",
            "atl_qualifying_scope",
            "foreign_crew_qualifying_treatment",
            "accommodation_per_diem_qualifying",
            "minimum_spend_threshold",
            "annual_cap",
            "rebate_assignability",
            "processing_timeline",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="MU",
        jurisdiction_name="Mauritius",
        program_name="Mauritius EDB Film Production Incentive",
        program_type="cash_rebate",
        base_rate=0.35,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=None,
        requires_local_entity=None,
        confidence_tier="PARSED",
        source_title="EDB Mauritius — Production Budget Evidence (The Little Utopia, June 2025)",
        source_url=None,
        effective_from=None,
        notes=(
            "35% rate evidenced from production budget; not yet verified against EDB primary "
            "source document. All BTL qualifying assumed. ATL qualifying unknown. "
            "Marine/vessel qualifying via MFDC."
        ),
        unknown_fields=[
            "atl_qualifying_scope",
            "foreign_crew_treatment",
            "accommodation_per_diem_qualifying",
            "minimum_spend_threshold",
            "annual_cap",
            "rebate_assignability",
            "payment_timeline",
            "spv_requirements",
            "cultural_test_requirement",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="Tax Rebate for International Productions (TRIP)",
        program_type="tax_credit",
        base_rate=0.30,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=275_000.0,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="CNC — Tax Rebate for International Productions (TRIP)",
        source_url="https://www.cnc.fr",
        effective_from="2009-01-01",
        notes=(
            "30% base on French qualifying spend; 40% on VFX spend. Capped at €30M per film. "
            "Must use French service company. Cultural committee pre-approval required."
        ),
        unknown_fields=[
            "cultural_committee_criteria",
            "vfx_uplift_exact_threshold",
            "foreign_atl_qualifying_scope",
            "accommodation_per_diem_qualifying",
            "confirmed_cap_per_film",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="ES",
        jurisdiction_name="Spain",
        program_name="Tax Credit for Foreign Productions (Canary Islands & Mainland)",
        program_type="tax_credit",
        base_rate=0.30,
        max_rate=0.50,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_100_000.0,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="ICAA / APA — Spain Film Tax Incentive Programme [NOT YET ACQUIRED]",
        source_url="https://www.culturaydeporte.gob.es",
        effective_from=None,
        notes=(
            "Canary Islands: 50% on first €1M qualifying spend, 45% on remainder; max €18M. "
            "Mainland: 30% on qualified spend; max €10M. "
            "Separate programmes — cannot stack."
        ),
        unknown_fields=[
            "canary_islands_separate_cap_details",
            "mainland_qualifying_spend_definition",
            "atl_qualifying_scope",
            "cultural_test_criteria",
            "minimum_spend_per_island_vs_total",
            "foreign_crew_routing_requirements",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="IT",
        jurisdiction_name="Italy",
        program_name="Italian Tax Credit for Foreign Productions",
        program_type="tax_credit",
        base_rate=0.40,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_100_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="DGCinema — Tax Credit per le Produzioni Straniere [NOT YET ACQUIRED]",
        source_url="https://www.dgcinema.beniculturali.it",
        effective_from=None,
        notes=(
            "40% on qualifying Italian expenditure; capped at €20M per film. "
            "Administered by MiC (Ministry of Culture). Annual programme fund exists."
        ),
        unknown_fields=[
            "annual_fund_size",
            "atl_qualifying_scope",
            "foreign_crew_minimum_local_spend_threshold",
            "accommodation_qualifying_treatment",
            "processing_timeline",
            "rebate_assignability",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="HR",
        jurisdiction_name="Croatia",
        program_name="Croatia Film Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=220_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="HAVC — Croatian Audiovisual Centre Cash Rebate [NOT YET ACQUIRED]",
        source_url="https://www.havc.hr",
        effective_from=None,
        notes=(
            "25% if ≥20% of qualifying spend involves Croatian creative elements; 20% otherwise. "
            "No cultural test for foreign productions."
        ),
        unknown_fields=[
            "local_content_uplift_exact_criteria",
            "annual_fund_cap",
            "atl_qualifying_scope",
            "processing_timeline",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="HU",
        jurisdiction_name="Hungary",
        program_name="Hungary Film Tax Rebate (HIPA)",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="HIPA — Hungarian Investment Promotion Agency Film Incentive [NOT YET ACQUIRED]",
        source_url="https://hipa.hu",
        effective_from=None,
        notes=(
            "30% rebate on qualifying Hungarian expenditure. Administered by HIPA. "
            "Hungarian service production company required. "
            "Large studio infrastructure available (Origo, Korda)."
        ),
        unknown_fields=[
            "confirmed_rate_vs_local_and_foreign_components",
            "annual_programme_cap",
            "atl_qualifying_scope",
            "foreign_crew_routing",
            "processing_timeline",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="BE",
        jurisdiction_name="Belgium",
        program_name="Belgian Tax Shelter for Audiovisual Productions",
        program_type="tax_shelter",
        base_rate=0.42,
        max_rate=0.42,
        is_refundable=True,
        is_transferable=True,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Belgian Tax Administration — Tax Shelter for Audiovisual Works [NOT YET ACQUIRED]",
        source_url="https://finances.belgium.be",
        effective_from=None,
        notes=(
            "Pass-through tax shelter: investors get 421% tax reduction (up to 50% of taxable income). "
            "Effectively ~42% of eligible production spend. "
            "Belgian qualifying spend minimum 150% of shelter investment."
        ),
        unknown_fields=[
            "exact_investor_tax_reduction_rate",
            "qualifying_spend_definition",
            "european_work_test_criteria",
            "shelter_certificate_market_pricing",
            "processing_timeline",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="DE",
        jurisdiction_name="Germany",
        program_name="German Federal Film Fund (DFFF / GFFF)",
        program_type="grant",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=2_200_000.0,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="BKM/FFA — DFFF Programme Guidelines [NOT YET ACQUIRED]",
        source_url="https://www.bkm.de",
        effective_from=None,
        notes=(
            "DFFF (Deutscher Filmförderfonds): 25% on qualifying German spend; min €2M German spend. "
            "GFFF (Game Film): separate. Annual fund capped. "
            "Competitive application — not guaranteed."
        ),
        unknown_fields=[
            "annual_fund_cap_amount",
            "exact_cultural_points_test",
            "competition_oversubscription_risk",
            "atl_qualifying_scope",
            "processing_timeline",
            "accommodation_qualifying_treatment",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Location Offset / Post, Digital and Visual Effects (PDV) Offset",
        program_type="tax_credit",
        base_rate=0.165,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=15_000_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Screen Australia — Location Offset and PDV Offset Guidelines [NOT YET ACQUIRED]",
        source_url="https://www.screenaustralia.gov.au",
        effective_from="2021-01-01",
        notes=(
            "Location Offset: 16.5% on QAPE (min A$20M QAPE). "
            "PDV Offset: 30% on qualifying post/VFX spend (min A$500K). "
            "State rebates can top-up: NSW (+10%), VIC (+13.5%). "
            "High minimum spend limits applicability for sub-$20M budgets."
        ),
        unknown_fields=[
            "state_top_up_stacking_rules",
            "qape_definition_atl_inclusion",
            "wht_on_cast_payments",
            "aud_usd_fluctuation_risk",
            "processing_timeline",
            "confirmed_pdv_offset_qualifying_categories",
        ],
    ),
    GlobalProgramEntry(
        jurisdiction_code="NZ",
        jurisdiction_name="New Zealand",
        program_name="New Zealand Screen Production Rebate (NZSPG / International)",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=10_000_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="New Zealand Film Commission / Inland Revenue — NZSPG Guidelines [NOT YET ACQUIRED]",
        source_url="https://www.nzfilm.co.nz/resources/nz-screen-production-grant",
        effective_from="2018-01-01",
        notes=(
            "International: 20% on qualifying NZ expenditure (min NZ$16M QNZPE). "
            "Uplift: additional 5% for significant economic benefit. "
            "NZ has hosted major productions (LOTR, Avatar)."
        ),
        unknown_fields=[
            "uplift_significant_economic_benefit_criteria",
            "qnzpe_definition_atl_inclusion",
            "nzd_usd_cap_equivalents",
            "wht_on_cast_payments",
            "processing_timeline",
            "annual_programme_cap",
        ],
    ),
]

_BENCHMARK_DATA_SOURCE = (
    "Production market knowledge — not verified from primary labour cost surveys "
    "(AICP, BECTU, regional film office surveys)"
)
_BENCHMARK_CONFIDENCE = "DISCOVERY"
_BENCHMARK_DATE = "2025-06"

ALL_BENCHMARKS: list[CostBenchmarkEntry] = [
    CostBenchmarkEntry(
        jurisdiction_code="US",
        crew_rate_multiplier=1.00,
        equipment_rental_multiplier=1.00,
        stage_facility_multiplier=1.00,
        location_fees_multiplier=1.00,
        post_production_multiplier=1.00,
        vfx_multiplier=1.00,
        catering_multiplier=1.00,
        key_crew_daily_travel_usd=350.0,
        marine_vessel_multiplier=1.00,
        lodging_daily_usd=250.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="LA baseline (all multipliers = 1.0).",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CA",
        crew_rate_multiplier=0.78,
        equipment_rental_multiplier=0.75,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.65,
        post_production_multiplier=0.75,
        vfx_multiplier=0.72,
        catering_multiplier=0.70,
        key_crew_daily_travel_usd=280.0,
        marine_vessel_multiplier=0.75,
        lodging_daily_usd=190.0,
        per_diem_daily_usd=85.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Canada (primarily Vancouver/Toronto). CAD/USD exchange applies to actuals.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="GB",
        crew_rate_multiplier=0.90,
        equipment_rental_multiplier=0.85,
        stage_facility_multiplier=0.88,
        location_fees_multiplier=0.95,
        post_production_multiplier=0.90,
        vfx_multiplier=0.85,
        catering_multiplier=0.80,
        key_crew_daily_travel_usd=380.0,
        marine_vessel_multiplier=0.85,
        lodging_daily_usd=280.0,
        per_diem_daily_usd=110.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="UK (primarily London/Pinewood). GBP/USD exchange applies to actuals.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="IE",
        crew_rate_multiplier=0.80,
        equipment_rental_multiplier=0.78,
        stage_facility_multiplier=0.75,
        location_fees_multiplier=0.70,
        post_production_multiplier=0.78,
        vfx_multiplier=0.75,
        catering_multiplier=0.72,
        key_crew_daily_travel_usd=350.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=220.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Ireland (Dublin / Ardmore Studios). EUR/USD exchange applies to actuals.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="MT",
        crew_rate_multiplier=0.55,
        equipment_rental_multiplier=0.60,
        stage_facility_multiplier=0.65,
        location_fees_multiplier=0.45,
        post_production_multiplier=0.65,
        vfx_multiplier=0.65,
        catering_multiplier=0.50,
        key_crew_daily_travel_usd=280.0,
        marine_vessel_multiplier=0.60,
        lodging_daily_usd=140.0,
        per_diem_daily_usd=70.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Malta. Mediterranean marine infrastructure (MFS water tank). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="GR",
        crew_rate_multiplier=0.50,
        equipment_rental_multiplier=0.55,
        stage_facility_multiplier=0.55,
        location_fees_multiplier=0.40,
        post_production_multiplier=0.60,
        vfx_multiplier=0.60,
        catering_multiplier=0.45,
        key_crew_daily_travel_usd=270.0,
        marine_vessel_multiplier=0.55,
        lodging_daily_usd=130.0,
        per_diem_daily_usd=65.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Greece (Athens / Thessaloniki / islands). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CY",
        crew_rate_multiplier=0.45,
        equipment_rental_multiplier=0.50,
        stage_facility_multiplier=0.50,
        location_fees_multiplier=0.38,
        post_production_multiplier=0.55,
        vfx_multiplier=0.55,
        catering_multiplier=0.42,
        key_crew_daily_travel_usd=260.0,
        marine_vessel_multiplier=0.50,
        lodging_daily_usd=120.0,
        per_diem_daily_usd=60.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Cyprus. EUR/USD applies. Limited local crew pool; fly-in costs typically significant.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="MU",
        crew_rate_multiplier=0.35,
        equipment_rental_multiplier=0.55,
        stage_facility_multiplier=None,
        location_fees_multiplier=0.30,
        post_production_multiplier=0.60,
        vfx_multiplier=0.65,
        catering_multiplier=0.38,
        key_crew_daily_travel_usd=380.0,
        marine_vessel_multiplier=0.50,
        lodging_daily_usd=110.0,
        per_diem_daily_usd=55.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes=(
            "Mauritius. stage_facility_multiplier=None: no dedicated studio infrastructure "
            "at benchmarkable scale as of 2025. Equipment largely imported; higher logistics cost."
        ),
    ),
    CostBenchmarkEntry(
        jurisdiction_code="FR",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.85,
        location_fees_multiplier=0.90,
        post_production_multiplier=0.85,
        vfx_multiplier=0.82,
        catering_multiplier=0.80,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.82,
        lodging_daily_usd=240.0,
        per_diem_daily_usd=105.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="France (Paris / Ile-de-France / Provence). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="ES",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.68,
        stage_facility_multiplier=0.65,
        location_fees_multiplier=0.60,
        post_production_multiplier=0.70,
        vfx_multiplier=0.70,
        catering_multiplier=0.62,
        key_crew_daily_travel_usd=300.0,
        marine_vessel_multiplier=0.65,
        lodging_daily_usd=170.0,
        per_diem_daily_usd=80.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Spain (Madrid / Canary Islands / Andalusia). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="IT",
        crew_rate_multiplier=0.70,
        equipment_rental_multiplier=0.72,
        stage_facility_multiplier=0.70,
        location_fees_multiplier=0.68,
        post_production_multiplier=0.72,
        vfx_multiplier=0.72,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=320.0,
        marine_vessel_multiplier=0.70,
        lodging_daily_usd=185.0,
        per_diem_daily_usd=85.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Italy (Rome / Cinecittà / Naples / Sicily). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="HR",
        crew_rate_multiplier=0.45,
        equipment_rental_multiplier=0.50,
        stage_facility_multiplier=0.45,
        location_fees_multiplier=0.35,
        post_production_multiplier=0.55,
        vfx_multiplier=0.55,
        catering_multiplier=0.42,
        key_crew_daily_travel_usd=260.0,
        marine_vessel_multiplier=0.48,
        lodging_daily_usd=120.0,
        per_diem_daily_usd=60.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Croatia (Dubrovnik / Split / Zagreb). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="HU",
        crew_rate_multiplier=0.45,
        equipment_rental_multiplier=0.50,
        stage_facility_multiplier=0.55,
        location_fees_multiplier=0.38,
        post_production_multiplier=0.55,
        vfx_multiplier=0.55,
        catering_multiplier=0.42,
        key_crew_daily_travel_usd=260.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=120.0,
        per_diem_daily_usd=60.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes=(
            "Hungary (Budapest / Origo Studios / Korda Studios). HUF/USD applies. "
            "marine_vessel_multiplier=None: minimal marine production history."
        ),
    ),
    CostBenchmarkEntry(
        jurisdiction_code="BE",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.80,
        location_fees_multiplier=0.80,
        post_production_multiplier=0.82,
        vfx_multiplier=0.80,
        catering_multiplier=0.78,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=230.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Belgium (Brussels / Ghent). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="DE",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.85,
        location_fees_multiplier=0.80,
        post_production_multiplier=0.85,
        vfx_multiplier=0.82,
        catering_multiplier=0.78,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=225.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes="Germany (Berlin / Bavaria / Hamburg). EUR/USD applies.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AU",
        crew_rate_multiplier=0.75,
        equipment_rental_multiplier=0.72,
        stage_facility_multiplier=0.70,
        location_fees_multiplier=0.65,
        post_production_multiplier=0.72,
        vfx_multiplier=0.70,
        catering_multiplier=0.68,
        key_crew_daily_travel_usd=480.0,
        marine_vessel_multiplier=0.72,
        lodging_daily_usd=200.0,
        per_diem_daily_usd=90.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes=(
            "Australia (Sydney / Melbourne / Gold Coast). AUD/USD applies. "
            "High travel cost reflects long-haul flights from US/EU."
        ),
    ),
    CostBenchmarkEntry(
        jurisdiction_code="NZ",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.65,
        stage_facility_multiplier=0.60,
        location_fees_multiplier=0.55,
        post_production_multiplier=0.65,
        vfx_multiplier=0.65,
        catering_multiplier=0.60,
        key_crew_daily_travel_usd=500.0,
        marine_vessel_multiplier=0.65,
        lodging_daily_usd=170.0,
        per_diem_daily_usd=75.0,
        confidence_tier=_BENCHMARK_CONFIDENCE,
        data_source=_BENCHMARK_DATA_SOURCE,
        as_of_date=_BENCHMARK_DATE,
        notes=(
            "New Zealand (Wellington / Auckland / Queenstown). NZD/USD applies. "
            "Highest travel cost reflects extreme long-haul from US/EU. "
            "Weta VFX hub in Wellington."
        ),
    ),
]
