"""
fund_economics_model.py — Phase E4: Pure-Python fund economics intelligence.

Provides structured economics data for grant/fund programs in ALL_PROGRAMS.
Covers recoupment structures, equity participation, repayment mechanics,
soft-money classification, and value adjustment factors.

No DB access. Mirrors and extends fund_economics DB table (migrations 0046, 0051).
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FundEconomicsEntry:
    program_slug: str

    # Core economic type
    # grant | loan | equity | advance | tax_credit | rebate | tax_shelter
    classification: str

    # Repayment mechanics
    is_repayable: bool
    is_recoupable: bool

    # Equity / profit participation
    has_equity_participation: bool
    equity_pct: float | None = None             # if has_equity_participation

    # Recoupment position (when is_recoupable=True)
    recoupment_position: str | None = None      # first | pari_passu | corridor | subordinated
    recoupment_trigger: str | None = None       # gross_receipts | net_profit | first_dollar | corridor_start
    recoupment_multiple: float | None = None    # e.g., 1.0 = 100%, 1.2 = 120% of advance

    # Revenue / profit participation beyond recoupment
    revenue_participation_pct: float | None = None
    profit_participation_pct: float | None = None

    # Soft money classification
    is_soft_money: bool = True   # True = non-repayable or deeply subordinated

    # Matching / spending requirements
    has_matching_requirement: bool = False
    matching_ratio: str | None = None    # e.g., "1:1", "2:1 from private"
    has_territorial_spend_requirement: bool = False
    min_territorial_spend_pct: float | None = None

    # Scale
    typical_max_award_usd: int | None = None
    is_competitive: bool = True

    # Stacking behaviour
    stackable_with_incentives: bool = True
    is_government_assistance: bool = False  # triggers qualifying spend reduction

    # Programme administration
    is_assignable: bool = False
    notes: str | None = None


# ---------------------------------------------------------------------------
# Fund registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, FundEconomicsEntry] = {}

def _r(e: FundEconomicsEntry) -> None:
    _REGISTRY[e.program_slug] = e


# ---------------------------------------------------------------------------
# Pan-European funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="eu_eurimages",
    classification="grant",
    is_repayable=False,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="net_profit",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    matching_ratio="Majority private financing required",
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_650_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    is_assignable=False,
    notes=(
        "Eurimages grants are non-repayable up to the point of recoupment; "
        "Eurimages participates in net profits after recoupment at a corridor rate. "
        "Does not reduce national incentive qualifying spend. Max ~€1.5M for features."
    ),
))

_r(FundEconomicsEntry(
    program_slug="eu_media_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="net_profit",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Creative Europe MEDIA development/co-production grants; primarily for development.",
))

# ---------------------------------------------------------------------------
# Ibermedia
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ibermedia_programme",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=330_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Ibermedia co-production grants €60k–€300k. Non-repayable. Soft money.",
))

# ---------------------------------------------------------------------------
# Canada federal funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ca_cmf",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    equity_pct=None,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    revenue_participation_pct=None,
    is_soft_money=False,
    has_matching_requirement=True,
    matching_ratio="Private broadcaster licence required",
    has_territorial_spend_requirement=False,
    typical_max_award_usd=2_750_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    is_assignable=False,
    notes=(
        "CMF equity investment recouped pari-passu with other investors from gross receipts. "
        "Government assistance: reduces CPTC/OFTTC qualifying labour expenditure."
    ),
))

_r(FundEconomicsEntry(
    program_slug="ca_telefilm_dev",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "Telefilm Canada development and production equity; repayable from first gross receipts. "
        "Government assistance under ITA §125.4; reduces CPTC qualifying labour."
    ),
))

_r(FundEconomicsEntry(
    program_slug="nohfc_production_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "NOHFC discretionary grant for Northern Ontario productions. "
        "Government assistance: reduces CPTC and OFTTC qualifying labour expenditure."
    ),
))

# ---------------------------------------------------------------------------
# UK funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_bfi_production",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    equity_pct=None,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    profit_participation_pct=None,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "BFI Film Fund equity investment; not government assistance for AVEC purposes "
        "(co-financing arrangement). Recouped pari-passu from gross receipts."
    ),
))

_r(FundEconomicsEntry(
    program_slug="gb_scot_creative_scotland",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Creative Scotland: co-financing equity, not government assistance for AVEC.",
))

_r(FundEconomicsEntry(
    program_slug="gb_wls_creative_wales",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Creative Wales: co-financing equity, not government assistance for AVEC.",
))

_r(FundEconomicsEntry(
    program_slug="gb_nir_northern_ireland",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Northern Ireland Screen: co-financing equity, not government assistance for AVEC.",
))

_r(FundEconomicsEntry(
    program_slug="gb_yrk_screen_yorkshire",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Screen Yorkshire: recoupable equity, not government assistance for AVEC.",
))

# ---------------------------------------------------------------------------
# Australia funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_screen_production",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    equity_pct=None,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=2_750_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "Screen Australia equity investment: government financial assistance under ITAA97 §376-170, "
        "reduces qualifying Australian production expenditure (QAPE) for Location Offset and Producer Offset."
    ),
))

_r(FundEconomicsEntry(
    program_slug="au_screenwest",
    classification="grant",
    is_repayable=False,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="net_profit",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "Screenwest WA: government financial assistance reducing QAPE for Location Offset and Producer Offset."
    ),
))

# ---------------------------------------------------------------------------
# Nordic / Scandinavian funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="nordic_ftvf",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=275_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Nordic Film and TV Fund: non-repayable grants for Nordic co-productions.",
))

_r(FundEconomicsEntry(
    program_slug="nl_hbf",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=275_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Hubert Bals Fund (IFFR): development/production grants for films from developing countries.",
))

_r(FundEconomicsEntry(
    program_slug="se_goteborg_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=110_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Göteborg Film Festival: development grants, primarily Nordic focus.",
))

# ---------------------------------------------------------------------------
# Belgian funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="be_wal_wallimage",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Wallimage provides repayable advances (subordinated to investors). "
        "Not government assistance for Belgian tax shelter purposes. "
        "Stackable with Belgian tax shelter."
    ),
))

_r(FundEconomicsEntry(
    program_slug="be_vlg_vaf",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "VAF Flanders: repayable advance, subordinated recoupment. "
        "Stackable with Belgian tax shelter."
    ),
))

_r(FundEconomicsEntry(
    program_slug="be_bru_screen",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Screen.Brussels: non-repayable grants. Stackable with tax shelter.",
))

# ---------------------------------------------------------------------------
# French funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="fr_cnc_production",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "CNC Avances sur Recettes: repayable advances from first gross receipts. "
        "Government support — interactions with tax crédit may apply."
    ),
))

_r(FundEconomicsEntry(
    program_slug="fr_idf_regional",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=330_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Île-de-France regional grant. Non-repayable. Stackable with CNC national aids.",
))

_r(FundEconomicsEntry(
    program_slug="fr_naq_regional",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Nouvelle-Aquitaine regional grant. Non-repayable.",
))

_r(FundEconomicsEntry(
    program_slug="fr_ara_regional",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Auvergne-Rhône-Alpes regional grant. Non-repayable.",
))

_r(FundEconomicsEntry(
    program_slug="fr_occ_regional",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Occitanie regional grant. Non-repayable.",
))

# ---------------------------------------------------------------------------
# German funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="de_fff_bayern",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_650_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="FFF Bayern: repayable loans subordinated to other investors. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_nrw_filmstiftung",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=2_200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Filmstiftung NRW: repayable loans. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_ni_nordmedia",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="nordmedia (Lower Saxony/Bremen): repayable loans. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_bb_medienboard",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Medienboard Berlin-Brandenburg: repayable loans up to €1M. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_bw_mfg",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="MFG Baden-Württemberg: repayable loans. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_hh_film_hamburg",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film Hamburg: repayable loans up to €500k. Stackable with DFFF.",
))

_r(FundEconomicsEntry(
    program_slug="de_mdm_mitteldeutsche",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="MDM Mitteldeutsche Medienförderung: repayable loans. Stackable with DFFF.",
))

# ---------------------------------------------------------------------------
# Danish Film Institute
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="dk_dfi_support",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    equity_pct=None,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_650_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="DFI: equity investment recouped pari-passu; government assistance in Denmark.",
))

# ---------------------------------------------------------------------------
# South Africa
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="za_idc_film",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="IDC South Africa: commercial loan with equity participation.",
))

# ---------------------------------------------------------------------------
# Tax credits — UK
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="uk_avec",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=10.0,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "AVEC (Audio Visual Expenditure Credit): 34% for film, 39% for high-end TV. "
        "Reduces qualifying UK expenditure by government assistance received. "
        "Minimum 10% UK qualifying expenditure. Claimed by UK-qualifying production company."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — Ireland
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ie_section_481",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=7_000_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Section 481 Film Tax Credit: 32% of qualifying Irish expenditure. "
        "Maximum €70M expenditure (€22.4M credit). "
        "Eligible spend includes BTL and limited ATL costs incurred in Ireland. "
        "Minimum 10% total budget spent in Ireland."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — Canada (federal)
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ca_federal_cptc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "CPTC (Canadian Production Tax Credit): 25% of qualified labour expenditure (QCLE), "
        "capped at 60% of production cost net of government assistance. "
        "Government assistance received (CMF, Telefilm, NOHFC, etc.) reduces QCLE. "
        "Must be Canadian content (CAVCO points system). Not government assistance for other credits."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — Canada (provincial)
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ca_bc_pstc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "BC PSTC (BC Production Services Tax Credit): 28% of qualifying BC labour. "
        "Cannot be combined with CPTC on same production (foreign vs. Canadian content split). "
        "Government assistance does not reduce PSTC basis. BTL focus."
    ),
))

_r(FundEconomicsEntry(
    program_slug="on_ofttc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "OFTTC (Ontario Film and Television Tax Credit): 35% of qualifying Ontario labour "
        "for Canadian content productions. Government assistance (CMF, Telefilm, NOHFC) reduces "
        "qualifying labour expenditure. Must be Ontario-certified Canadian content."
    ),
))

_r(FundEconomicsEntry(
    program_slug="on_opstc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "OPSTC (Ontario Production Services Tax Credit): 21.5% of qualifying Ontario production "
        "expenditure for non-Canadian content (foreign/treaty). Mutually exclusive with OFTTC. "
        "No government assistance reduction applied."
    ),
))

_r(FundEconomicsEntry(
    program_slug="qc_film_production",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Quebec QPRDP (Quebec Film and Television Production Tax Credit): "
        "28%-36% of qualifying Quebec labour for Canadian content. "
        "Government assistance (CMF, Telefilm, SODEC) reduces qualifying labour. "
        "Regional bonuses apply outside Montreal."
    ),
))

_r(FundEconomicsEntry(
    program_slug="ca_qc_qprdp",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Quebec QPRDP — Foreign Productions tax credit: 20%-28% of qualifying Quebec "
        "labour for foreign/treaty co-productions. Conditional on qualifying with CPTC or treaty. "
        "No government assistance reduction for foreign track."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — France
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="fr_trip",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=3_000_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "TRIP (Tax Rebate for International Productions): 30% of qualifying French spend "
        "for foreign productions, capped at €30M (i.e., max spend €100M). "
        "Minimum €1M French spend required. Stackable with regional funds and Eurimages. "
        "Separate from CNC domestic tax crédit cinéma (used by French productions)."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — Italy
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="it_tax_credit_foreign",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=6_000_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Italian Tax Credit for Foreign Productions: 40% of qualifying Italian spend. "
        "Maximum credit €20M per project (spend cap €50M). "
        "Minimum Italian spend €1M. Administered by MiC. "
        "Stackable with Italian regional film commission grants."
    ),
))

# ---------------------------------------------------------------------------
# Tax credits — Australia
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_location_offset",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Location Offset: 16.5% of Qualifying Australian Production Expenditure (QAPE). "
        "Minimum A$15M QAPE for film. Government financial assistance (Screen Australia, Screenwest) "
        "reduces QAPE. Cannot be combined with Producer Offset on same film. "
        "Post/Digital/VFX Offset: 30% of qualifying post-production spend (A$500k min)."
    ),
))

# ---------------------------------------------------------------------------
# Cash rebates
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_sa_safc",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "SAFC (South Australian Film Corporation): government financial assistance "
        "reducing QAPE for Location and Producer Offsets. Non-repayable rebate/grant. "
        "Minimum South Australian spend required. Competitive allocation."
    ),
))

_r(FundEconomicsEntry(
    program_slug="gr_cash_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Greece Cash Rebate: 40% of qualifying Greek spend for international productions. "
        "Administered by the Greek Film Centre and National Film Centre. "
        "Does not reduce Eurimages qualifying spend. Minimum spend threshold required. "
        "UNKNOWN: current annual cap, minimum spend in USD."
    ),
))

_r(FundEconomicsEntry(
    program_slug="hr_cash_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Croatia Cash Rebate: up to 25% of qualifying Croatian spend for international productions. "
        "Administered by the Croatian Audiovisual Centre (HAVC). "
        "Does not reduce Eurimages qualifying spend. Minimum spend threshold required. "
        "UNKNOWN: current annual cap, minimum spend in USD."
    ),
))

_r(FundEconomicsEntry(
    program_slug="bg_cash_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Bulgaria Cash Rebate: 25% of qualifying Bulgarian spend. "
        "Administered by the National Film Centre Bulgaria. "
        "Does not reduce Eurimages qualifying spend. "
        "UNKNOWN: current annual cap, minimum spend in USD."
    ),
))

_r(FundEconomicsEntry(
    program_slug="mt_mfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Malta Film Commission Cash Rebate: 40% on qualifying Maltese expenditure. "
        "Up to 5% additional digital media bonus. "
        "Does not reduce Eurimages qualifying spend. "
        "UNKNOWN: current annual cap, minimum spend in USD."
    ),
))

_r(FundEconomicsEntry(
    program_slug="mu_edb_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Mauritius EDB Film Rebate Scheme: up to 40% of qualifying Mauritius spend. "
        "Administered by the Economic Development Board (EDB). "
        "UNKNOWN: current annual cap, minimum spend in USD."
    ),
))

# ---------------------------------------------------------------------------
# Development / selective support funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ca_bell_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "Bell Fund: government assistance under ITA §125.4. "
        "Reduces CPTC and OFTTC qualifying labour expenditure. "
        "Requires broadcaster licence. Focus on digital content."
    ),
))

_r(FundEconomicsEntry(
    program_slug="ca_nsi_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=75_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes=(
        "NSI (National Screen Institute) grants: government assistance. "
        "Reduces CPTC qualifying labour. Drama Prize and development programs up to C$75k."
    ),
))

_r(FundEconomicsEntry(
    program_slug="de_berlinale_wcf",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Berlinale World Cinema Fund: development/production grants €10k–€200k. "
        "For co-productions from underrepresented territories with German partner. "
        "Not government assistance for German incentives. Non-repayable."
    ),
))

_r(FundEconomicsEntry(
    program_slug="fi_ses_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Finnish Film Foundation (SES): selective production support up to €750k. "
        "Non-repayable grants. Not government assistance for Eurimages. "
        "Combines with Eurimages, YLE, and Nordic Film & TV Fond."
    ),
))

_r(FundEconomicsEntry(
    program_slug="no_nfi_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "NFI (Norwegian Film Institute) selective production grants up to NOK 8M (~€750k). "
        "Also administers Norwegian Incentive Scheme (25% cash rebate for foreign productions). "
        "Selective grants not government assistance for Eurimages. "
        "Combines with NRK, Eurimages, Nordic Fund."
    ),
))

# ---------------------------------------------------------------------------
# Direct grants — German federal
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="de_dfff",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=6_500_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "DFFF/GFFF (German Federal Film Fund): automatic 25% of qualifying German spend. "
        "Maximum €25M per project for feature films (DFFF I: up to €25M; DFFF II: international productions). "
        "Minimum 25% German spend. Not government assistance for regional fund calculations. "
        "Stackable with all German regional funds."
    ),
))

# ---------------------------------------------------------------------------
# Direct grants — UK regional
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_creative_england",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Creative England (now integrated with BFI): recoupable equity for English regional productions. "
        "Not government assistance for AVEC. Pari-passu recoupment."
    ),
))

# ---------------------------------------------------------------------------
# Co-production funds — regional Sweden
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="film_i_vast",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes=(
        "Film i Väst (Trollhättan region, Sweden): repayable advances/co-production contributions. "
        "One of Europe's most prolific co-production hubs. "
        "Combines with SFI, Eurimages, Arte, ZDF, and international partners. "
        "Minimum Västra Götaland regional spend required."
    ),
))

# ---------------------------------------------------------------------------
# Spanish regional direct grants
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="es_cat_icec",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=275_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ICEC (Catalan cultural institute): grants for Catalan productions. Stackable with ICAA national deduction.",
))

_r(FundEconomicsEntry(
    program_slug="es_and_andalusia",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Andalusia Film Commission: grants for Andalusian productions. Stackable with ICAA national deduction.",
))

_r(FundEconomicsEntry(
    program_slug="es_gal_agadic",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="AGADIC (Galicia): grants for Galician productions. Stackable with ICAA national deduction.",
))

_r(FundEconomicsEntry(
    program_slug="es_val_ivc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="IVC (Institut Valencià de Cultura): grants for Valencian productions. Stackable with ICAA national deduction.",
))

_r(FundEconomicsEntry(
    program_slug="es_eus_basque",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=275_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Basque Audiovisual (Eusko Jaurlaritza): grants for Basque productions. Stackable with ICAA national deduction.",
))

# ---------------------------------------------------------------------------
# Italian regional direct grants
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="it_laz_lazio_fc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=220_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Lazio Cinema International: regional grants. Stackable with MiC national tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="it_sic_sicilia_fc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Sicilia Film Commission: regional grants. Stackable with MiC national tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="it_cam_campania_fc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film Commission Campania: regional grants. Stackable with MiC national tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="it_tos_tuscany_fc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film Commission Toscana: regional grants. Stackable with MiC national tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="it_pie_piemonte_fc",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film Commission Torino Piemonte: regional grants. Stackable with MiC national tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="it_apu_apulia_ff",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=165_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Apulia Film Commission Film Fund: regional grants. Stackable with MiC national tax credit.",
))

# ---------------------------------------------------------------------------
# Transferable tax credit — US California
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="us_ca_ftc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    min_territorial_spend_pct=None,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    is_assignable=True,
    notes=(
        "California Film & Television Tax Credit Program 3.0: 20%-25% of qualifying California "
        "production expenditure. Transferable (assignable to California taxpayers). "
        "Competitive allocation — annual lottery/application process. "
        "ATL exclusions apply. Non-resident ATL costs generally excluded."
    ),
))

# ---------------------------------------------------------------------------
# Broadcaster funds economics
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_bbc_films",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=3_850_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="BBC Films: co-financing equity, not government assistance for AVEC. Pari-passu recoupment.",
))

_r(FundEconomicsEntry(
    program_slug="gb_film4",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=2_750_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film4/Channel 4: co-financing equity, not government assistance for AVEC. Pari-passu recoupment.",
))

_r(FundEconomicsEntry(
    program_slug="de_zdf",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ZDF co-production: pre-sale/commission model; does not reduce DFFF qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="de_arte",
    classification="equity",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Arte: Franco-German broadcaster co-production; does not reduce DFFF or CNC qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="fr_canal_plus",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="CANAL+ pre-purchase: minimum guarantee / advance against TV rights. Does not reduce CNC tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="ie_rte",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="RTÉ co-production: pre-purchase/commission; does not reduce Section 481 qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="it_rai_cinema",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=2_200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="RAI Cinema: broadcaster pre-purchase with territorial spend obligation. Does not reduce MiC tax credit.",
))

_r(FundEconomicsEntry(
    program_slug="es_rtve",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="first",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_650_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="RTVE: broadcaster investment obligated by Spanish law. Does not reduce ICAA deduction.",
))

_r(FundEconomicsEntry(
    program_slug="se_svt",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_650_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="SVT: broadcaster pre-purchase/commission; does not reduce Swedish Film Institute qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="no_nrk",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="NRK: broadcaster commission/co-production; does not reduce NFI qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="dk_dr",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="DR: broadcaster commission/co-production; does not reduce DFI qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="fi_yle",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="YLE: broadcaster commission/co-production; does not reduce SES qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="at_orf",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=825_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ORF Film/Fernseh-Abkommen: broadcaster co-investment; does not reduce ÖFI qualifying spend.",
))

_r(FundEconomicsEntry(
    program_slug="nl_npo",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    has_equity_participation=False,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    is_soft_money=False,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=660_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="NPO/VPRO: broadcaster co-production; does not reduce Netherlands Film Fund qualifying spend.",
))

# ---------------------------------------------------------------------------
# Additional national fund economics
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="at_ofi_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ÖFI (Austrian Film Institute): selective grants. Not government assistance for other European funds.",
))

_r(FundEconomicsEntry(
    program_slug="pl_pisf_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="PISF (Polish Film Institute): selective grants. Eurimages member. Not govt assistance for EU funds.",
))

_r(FundEconomicsEntry(
    program_slug="cz_czech_film_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Czech Film Fund: selective grants. Eurimages member. Not govt assistance for Eurimages.",
))

_r(FundEconomicsEntry(
    program_slug="hu_nfi_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="NFI Hungary: selective grants. Eurimages member. Hungary also has 30% cash rebate for foreign productions.",
))

_r(FundEconomicsEntry(
    program_slug="pt_ica_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ICA Portugal: selective and automatic grants. Eurimages member. Ibermedia member (Lusophone track).",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Cash Rebates (financial programs)
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="cy_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=3_500_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Cyprus cash rebate: 35% on qualifying Cyprus expenditure. Government assistance — reduces basis for co-financing. UNKNOWN: confirmed annual cap.",
))

_r(FundEconomicsEntry(
    program_slug="hu_hipa_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Hungary HIPA (30% cash rebate on qualifying HU spend for foreign productions). Separate from NFI grant program. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="nz_nzspg",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="NZ Screen Production Grant — International (20% base + 5% uplift). Government financial assistance. UNKNOWN: annual global cap.",
))

_r(FundEconomicsEntry(
    program_slug="nz_pdv_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="NZ PDV/post rebate: 20% base + up to 5% uplift on NZ post/VFX expenditure. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="au_nsw_screen",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=4_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen NSW production attraction fund: location grant/rebate for NSW productions. Government assistance stacks with federal offsets. UNKNOWN: exact rate structure.",
))

_r(FundEconomicsEntry(
    program_slug="au_nsw_screen_fund",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=4_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen NSW production support fund — production attraction incentive. Government assistance. UNKNOWN: current program year rate.",
))

_r(FundEconomicsEntry(
    program_slug="au_vic_vicscreen",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=3_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="VicScreen Production Investment — state rebate/grant for Victoria filming. Government assistance stacks with AU Producer Offset. UNKNOWN: rate structure.",
))

_r(FundEconomicsEntry(
    program_slug="au_qld_screen",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=2_500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Queensland Production Attraction Strategy: location offset incentive for QLD. Government assistance. UNKNOWN: rate.",
))

_r(FundEconomicsEntry(
    program_slug="nl_nfpi",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Netherlands Film Production Incentive: 30% cash rebate on qualifying NL production expenditure. Government assistance. Competitive allocation.",
))

_r(FundEconomicsEntry(
    program_slug="at_fisa_plus",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=4_000_000,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Austria FISA+: 25-35% cash rebate on qualifying Austrian expenditure (film, series, documentary). Government assistance. Reduces co-financing basis.",
))

_r(FundEconomicsEntry(
    program_slug="cz_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Czech Film Incentive (CzechInvest): 20% rebate on qualifying Czech expenditure. Government assistance. Separate from Czech Film Fund selective grants.",
))

_r(FundEconomicsEntry(
    program_slug="ro_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Romania film rebate: 35% on qualifying Romanian expenditure (min RON equivalent ~$250k). Government assistance. UNKNOWN: annual cap.",
))

_r(FundEconomicsEntry(
    program_slug="pt_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Portugal film & TV incentive (IAPMEI/ICA): up to 25% rebate on qualifying PT expenditure. Government assistance. Separate from ICA selective grants.",
))

_r(FundEconomicsEntry(
    program_slug="rs_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Serbia film incentive: 25% rebate on qualifying Serbian expenditure. Government assistance. UNKNOWN: annual cap, min spend.",
))

_r(FundEconomicsEntry(
    program_slug="is_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Iceland film rebate: 25% on qualifying Icelandic expenditure (Icelandic Film Centre). Government assistance. Separate from post rebate.",
))

_r(FundEconomicsEntry(
    program_slug="is_post_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Iceland post-production/VFX/animation rebate: 25% on qualifying IS post expenditure. Can be claimed separately from location rebate. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="gb_sct_screen_production",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=2_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Scotland Production Growth Fund: location grant for Scottish-based filming. Stackable with UK Film Tax Relief. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="gb_wls_film_fund",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Wales Film Fund / Creative Wales production attraction: location grant for Wales filming. Stacks with UK AVEC. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="se_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Sweden film incentive (Swedish Film Institute): 25% location rebate on qualifying Swedish expenditure. Government assistance. UNKNOWN: annual cap.",
))

_r(FundEconomicsEntry(
    program_slug="no_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Norway film incentive (NFI): 25% rebate on qualifying Norwegian expenditure for international productions. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="ee_film_estonia",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Estonia film incentive: 30% rebate on qualifying Estonian expenditure (Enterprise Estonia). Government assistance. Minimum ~EUR 100k spend.",
))

_r(FundEconomicsEntry(
    program_slug="lt_lcc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Lithuania film incentive (Lithuanian Film Centre): 30% rebate on qualifying Lithuanian expenditure. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="lv_nkmp_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Latvia film incentive (NKMP / National Film Centre Latvia): 30% rebate on qualifying Latvian expenditure. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="sk_avf_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Slovakia Audiovisual Fund (AVF): 33% rebate on qualifying Slovak expenditure. Government assistance. UNKNOWN: annual cap, min spend.",
))

_r(FundEconomicsEntry(
    program_slug="si_sfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Slovenia Film Centre incentive: 25% rebate on qualifying Slovenian expenditure. Government assistance. UNKNOWN: annual cap.",
))

_r(FundEconomicsEntry(
    program_slug="al_anca_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Albania National Cinema Centre (ANCA): cash rebate for international productions filming in Albania. Rate and cap UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="me_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Montenegro film incentive: up to 25% rebate on qualifying MNE expenditure. Government assistance. Rate and cap UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="mk_mfa_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="North Macedonia MFA film incentive: cash rebate for foreign productions. Rate and cap UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="ge_gnfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Georgia National Film Centre: cash rebate for international productions. Rate and cap UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="tr_cinema_support",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Turkey Ministry of Culture Cinema Support Fund: selective grants and production support for international co-productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="ae_dxb_dpi",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Dubai Department of Production and Industries (DPI): 30% cash rebate on qualifying Dubai expenditure. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="ae_adfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Abu Dhabi Film Commission (ADFC): 30% rebate on qualifying Abu Dhabi expenditure. Government assistance. Separate from Dubai DPI rebate.",
))

_r(FundEconomicsEntry(
    program_slug="sa_sfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Saudi Film Commission: cash rebate for international productions. Rate UNKNOWN — program developing; likely 40% target per Vision 2030.",
))

_r(FundEconomicsEntry(
    program_slug="jo_rfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Jordan Royal Film Commission (RFC): up to 15% rebate on qualifying Jordanian expenditure. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="qa_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Qatar Film Commission: cash rebate / production support for international productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="il_maslool_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Israel Maslool (Track) incentive: 30% rebate on qualifying Israeli expenditure for foreign productions. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="ma_ccm_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Morocco CCM (Centre Cinématographique Marocain): cash rebate for international productions. Rate and cap UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="tn_cnci_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Tunisia CNCI film incentive: production support/rebate for international filming in Tunisia. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="ke_kfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Kenya Film Commission: cash rebate / filming incentive. Rate UNKNOWN. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="za_dti_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="South Africa DTI foreign film and TV production incentive: 20-25% rebate on qualifying SA expenditure. Government assistance. Separate from IDC equity.",
))

_r(FundEconomicsEntry(
    program_slug="na_nfc_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Namibia Film Commission (NFC): filming incentive for international productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="sg_sfc_production",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Singapore Film Commission (SFC): production rebate / incentive for international productions filming in Singapore. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="my_finas_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Malaysia FINAS film incentive: cash rebate for international productions filming in Malaysia. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="ph_fdcp_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Philippines FDCP incentive: filming incentive for international productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="kr_kofic_location",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Korea KOFIC location incentive: production support for international productions filming in Korea. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="tw_tfai_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Taiwan TFAI (Taiwan Film and Audiovisual Institute): cash rebate for international productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="lk_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Sri Lanka film incentive: cash rebate / filming incentive for international productions. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="th_boi_film",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Thailand BOI film incentive: 20% cash rebate on qualifying Thai expenditure. Government assistance under BOI promotional framework.",
))

_r(FundEconomicsEntry(
    program_slug="jp_jloc_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Japan JLOC (Japan Location Organizing Committee): cash back incentive for international productions filming in Japan. Up to 25% on qualifying spend. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="ar_incaa_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Argentina INCAA cash rebate for international productions. Rate and cap UNKNOWN. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="cl_corfo_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Chile CORFO Audiovisual Incentive: up to 30% rebate on qualifying Chilean expenditure. Government assistance. Competitive.",
))

_r(FundEconomicsEntry(
    program_slug="co_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Colombia film rebate (FDC / ProColombia): tax reimbursement incentive for international productions. ~20% rebate on qualifying Colombian spend. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="do_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Dominican Republic film rebate: 25% tax credit/rebate on qualifying DR expenditure. Government assistance. UNKNOWN: annual cap.",
))

_r(FundEconomicsEntry(
    program_slug="uy_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Uruguay film incentive (ICAU): cash rebate for international productions filming in Uruguay. Rate UNKNOWN.",
))

_r(FundEconomicsEntry(
    program_slug="ca_ns_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Nova Scotia Film and Television Production Incentive: up to 25% rebate on qualifying NS expenditure. Government assistance stacks with CPTC.",
))

# US state incentives

_r(FundEconomicsEntry(
    program_slug="us_or_opif",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=14_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Oregon Production Investment Fund (OPIF): 20% rebate on qualifying Oregon expenditure. Government assistance. US state — no federal stacking.",
))

_r(FundEconomicsEntry(
    program_slug="us_wa_mpcp",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=3_500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Washington Motion Picture Competitiveness Program: 15-30% rebate on qualifying WA expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_nc_film_grant",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=31_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="North Carolina Film and Entertainment Grant: up to 25% grant on qualifying NC expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_tx_miip",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=22_500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Texas Moving Image Industry Incentive Program (MIIP): 5-22.5% rebate on qualifying TX expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_co_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=5_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Colorado Film Incentive: up to 20% rebate on qualifying CO expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_tn_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Tennessee Film & Entertainment Incentive: up to 25% rebate on qualifying TN expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_ok_film_rebate",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=8_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Oklahoma Film Enhancement Rebate: 35-37% rebate on qualifying OK expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_ut_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Utah Motion Picture Incentive Program: 20-25% rebate on qualifying UT expenditure. Government assistance. US state.",
))

_r(FundEconomicsEntry(
    program_slug="us_az_film_incentive",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Arizona Refundable Film Tax Credit: 15-20% rebate on qualifying AZ expenditure. Government assistance. US state.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — VFX / Animation / Post-Production Incentives
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_pdv_offset",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Australia PDV (Post, Digital & Visual Effects) Offset: 30% rebate on qualifying AU PDV expenditure. Government assistance — reduces QAPE for Location and Producer Offsets if combined.",
))

_r(FundEconomicsEntry(
    program_slug="ca_on_ocase",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Ontario OCASE: 18% refundable tax credit on qualifying Ontario animation/VFX labour. Government assistance — reduces qualifying labour for CPTC.",
))

_r(FundEconomicsEntry(
    program_slug="ca_bc_idmtc",
    classification="tax_credit",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="BC Interactive Digital Media Tax Credit (IDMTC): 17.5% refundable tax credit on qualifying BC digital media/VFX labour. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="sg_imda_digital",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Singapore IMDA (Infocomm Media Development Authority) digital media development fund: grants for animation, VFX, and digital content production in Singapore. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="kr_kocca_animation",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Korea KOCCA animation and content fund: grants for animation production with Korean participation. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="fr_cnc_animation",
    classification="grant",
    is_repayable=True,
    is_recoupable=True,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="French CNC animation fund (COSIP/SESAM): selective advance on receipts for animation production. Recoupable from receipts. Government assistance — reduces TRIP basis.",
))

_r(FundEconomicsEntry(
    program_slug="jp_vipo_animation",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Japan VIPO (Visual Industry Promotion Organization): animation and content development support for international co-productions. Government assistance.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Export Promotion Funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_bfi_international",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="BFI International (export/market support): grants for UK productions at international festivals and markets. Not government assistance for film tax relief purposes.",
))

_r(FundEconomicsEntry(
    program_slug="fr_unifrance",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=150_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="UniFrance export support: grants/subsidies for distribution, promotion and international sales of French films. Not government assistance for TRIP purposes.",
))

_r(FundEconomicsEntry(
    program_slug="de_german_films",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="German Films (FFA): export support and international market promotion for German productions. Not government assistance for DFFF purposes.",
))

_r(FundEconomicsEntry(
    program_slug="it_anica_export",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ANICA/MiC Italy export promotion: support for Italian films at international festivals and markets. Not government assistance for Italian tax credit purposes.",
))

_r(FundEconomicsEntry(
    program_slug="ca_telefilm_export",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Telefilm Canada Export and Market Development: grants for Canadian productions at international festivals and markets. Government assistance — may reduce CPTC basis.",
))

_r(FundEconomicsEntry(
    program_slug="au_screen_international",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=150_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Australia International (export development): grants for Australian productions at international festivals and markets. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="es_icaa_export",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Spain ICAA export promotion: support for Spanish films at international festivals and markets.",
))

_r(FundEconomicsEntry(
    program_slug="kr_kofic_export",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=150_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="KOFIC international/export support: grants for Korean productions at international festivals and markets. Government assistance.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Workforce / Training Subsidies
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_screenskills",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=50_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="ScreenSkills UK: workforce training grants for UK screen industry productions. Industry-funded (not govt). Not government assistance for AVEC purposes.",
))

_r(FundEconomicsEntry(
    program_slug="au_screen_talent",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Australia Talent Fund: workforce development grants. Government assistance for Australian productions.",
))

_r(FundEconomicsEntry(
    program_slug="ie_screen_ireland_dev",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Ireland development and talent fund: grants for Irish-qualifying development and talent. Government assistance — reduces Section 481 qualifying basis.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Tourism Board / Destination Marketing Support
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Tourism Australia film support: destination marketing support for productions filming in Australia. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="nz_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Tourism New Zealand film support: destination marketing support for productions filming in NZ. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="ie_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Tourism Ireland / Fáilte Ireland film support: destination marketing support for productions filming in Ireland. Government assistance — may reduce Section 481 basis.",
))

_r(FundEconomicsEntry(
    program_slug="jo_rfc_tourism",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=200_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Jordan Royal Film Commission tourism facilitation: production support/logistics for filming in Jordan. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="mv_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Maldives tourism film support: production support and location facilitation for productions filming in the Maldives. UNKNOWN: program details.",
))

_r(FundEconomicsEntry(
    program_slug="sc_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Seychelles tourism film support: destination marketing support for productions filming in Seychelles. UNKNOWN: program details.",
))

_r(FundEconomicsEntry(
    program_slug="fj_tourism_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Fiji Tourism film support: destination marketing support for productions filming in Fiji. UNKNOWN: program details.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Airline / Transport Production Support
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ae_emirates_support",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Emirates Airline film partnership: in-kind and logistical support (flights, cargo, etc.) for major productions. Not financial — facilitation only. Not government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="nz_air_production",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Air New Zealand film support: in-kind logistical support for productions filming in NZ. Not financial — facilitation only. Not government assistance.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — National / Cultural Ministry Grants (remaining)
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gr_gnf_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Greek Film Centre (GFC): selective production grants. Eurimages member. Not govt assistance for EU fund purposes.",
))

_r(FundEconomicsEntry(
    program_slug="sa_sfc_grants",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Saudi Film Commission development/production grants: selective grants as part of Vision 2030 film sector development. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="it_mic_national",
    classification="grant",
    is_repayable=True,
    is_recoupable=True,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=2_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Italian Ministry of Culture (MiC) national film fund: selective advances on receipts for Italian co-productions. Recoupable. Government assistance — reduces Italian tax credit basis.",
))

_r(FundEconomicsEntry(
    program_slug="de_ffa",
    classification="loan",
    is_repayable=True,
    is_recoupable=True,
    recoupment_position="pari_passu",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    has_equity_participation=False,
    is_soft_money=False,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="German FFA (Filmförderungsanstalt): reference and project film funding — repayable advance. Pari passu with other German funders. Government assistance — reduces DFFF basis.",
))

_r(FundEconomicsEntry(
    program_slug="de_wdr_ard",
    classification="advance",
    is_repayable=True,
    is_recoupable=True,
    recoupment_position="subordinated",
    recoupment_trigger="gross_receipts",
    recoupment_multiple=1.0,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=False,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=1_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="WDR/ARD German broadcaster co-production advance: recoupable advance against broadcast rights. Soft money — subordinated recoupment. Not government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="fi_business_finland",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Business Finland audiovisual grant: innovation and international development support for Finnish productions. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="hk_createhk",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=500_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Hong Kong CreateHK (Create Smart Initiative): production and development grants for Hong Kong film and creative content. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="cn_film_coproduction",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="China official co-production fund/support via NRTA (National Radio and Television Administration). Government assistance. Treaty co-productions only. UNKNOWN: financial details.",
))

_r(FundEconomicsEntry(
    program_slug="streamer_uk_local",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="UK streamer local content obligation (AVMSD/Ofcom): production spend obligations from platforms operating in UK. Not a grant program — a regulatory spend requirement. UNKNOWN: financial value per production.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Norwegian Regional Funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="no_vgn_viken",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Viken Film (regional Norwegian fund): selective grants for productions in Viken region. Not government assistance for national incentive purposes.",
))

_r(FundEconomicsEntry(
    program_slug="no_inl_midtnorsk",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=400_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Midtnorsk Filmsenter: regional grants for productions in central Norway. Stacks with national NFI grants.",
))

_r(FundEconomicsEntry(
    program_slug="no_rog_vestnorsk",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=400_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Vestnorsk Filmsenter: regional grants for productions in western Norway. Stacks with national NFI grants.",
))

_r(FundEconomicsEntry(
    program_slug="no_tro_nordnorsk",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=400_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Nord Norsk Filmsenter: regional grants for productions in northern Norway. Stacks with national NFI grants.",
))

_r(FundEconomicsEntry(
    program_slug="no_mro_film3",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=350_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film3 (Møre og Romsdal / Midt-Norge): regional grants for productions in mid-western Norway. Stacks with national NFI grants.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Swedish / Danish Regional Funds
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="se_sk_film_skane",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film i Skåne: regional fund for productions in Skåne (southern Sweden). Stacks with SFI national grants.",
))

_r(FundEconomicsEntry(
    program_slug="se_ab_filmstockholm",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Filmregion Stockholm-Mälardalen: regional fund for productions in Stockholm region. Stacks with SFI national grants.",
))

_r(FundEconomicsEntry(
    program_slug="dk_cph_film_fund",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Copenhagen Film Fund: regional fund for productions in Copenhagen/Zealand region. Stacks with DFI national grants.",
))

_r(FundEconomicsEntry(
    program_slug="dk_fyn_film",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=350_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Film Fyn: regional fund for productions in Funen region, Denmark. Stacks with DFI national grants.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Australian State Additional
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="au_vic_film_victoria",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=1_000_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Film Victoria (now VicScreen) production development grants: selective grants for Victorian productions. Government assistance stacks with AU Producer Offset.",
))

_r(FundEconomicsEntry(
    program_slug="au_tas_screen",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Screen Tasmania: production grants for productions filming in Tasmania. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="au_nt_territory",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Territory Screen Office (NT): production grants for productions filming in Northern Territory. Government assistance.",
))

_r(FundEconomicsEntry(
    program_slug="au_miff_premiere",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=False,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="MIFF Premiere Fund: selective development/production grants for Australian features premiering at Melbourne International Film Festival. Not government assistance.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — UK Regional Additional
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="gb_lon_film_london",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_matching_requirement=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Film London production fund: grants for productions with significant London filming. Government assistance — reduces AVEC basis.",
))

_r(FundEconomicsEntry(
    program_slug="gb_film_hub_midlands",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=100_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Film Hub Midlands (BFI Network): development and production micro-grants for Midlands-based productions. Government assistance.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Canadian Provincial Additional
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="ca_pe_film_pei",
    classification="rebate",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Film PEI (Prince Edward Island): production rebate/grant for productions filming in PEI. Government assistance stacks with CPTC.",
))

_r(FundEconomicsEntry(
    program_slug="ca_mb_film_mb",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=550_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Manitoba Film & Music production support: grants for Manitoba productions. Government assistance stacks with CPTC and Manitoba Film & Video Production Tax Credit (MFVPTC).",
))

_r(FundEconomicsEntry(
    program_slug="ca_nb_film_nb",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="New Brunswick Film: production grants for NB-based productions. Government assistance stacks with CPTC.",
))

_r(FundEconomicsEntry(
    program_slug="ca_nl_film_nl",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=True,
    notes="Newfoundland & Labrador Film Development Corporation: production grants for NL-based productions. Government assistance stacks with CPTC.",
))

# ---------------------------------------------------------------------------
# Phase A-D Final Sweep — Production Support / Facilitation Services
# (Non-financial film commissions — classification=grant, no financial value)
# ---------------------------------------------------------------------------

_r(FundEconomicsEntry(
    program_slug="bs_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Bahamas Film Commission: location facilitation, permits, location scout support. Non-financial services only.",
))

_r(FundEconomicsEntry(
    program_slug="bb_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Barbados Film Commission: location facilitation, permits, location scout support. Non-financial services only.",
))

_r(FundEconomicsEntry(
    program_slug="pa_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Panama Film Commission: location facilitation and production support services. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="cr_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Costa Rica Film Commission: location facilitation and production support services. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="ec_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Ecuador Film Commission: location facilitation and production support services. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="eg_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Egypt Film Commission: location facilitation, permits, and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="gh_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Ghana Film Authority: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="rw_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Rwanda Film Commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="tz_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Tanzania Film Board: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="sn_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Senegal film commission/bureau: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="kw_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Kuwait film bureau: location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="bh_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Bahrain Authority for Culture (film support): location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="kz_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Kazakhstan film commission / Kazakhfilm: location facilitation and production support. UNKNOWN: financial incentive status.",
))

_r(FundEconomicsEntry(
    program_slug="vn_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Vietnam Film Development Department: location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="id_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Indonesian film commission (BPIFB): location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="kh_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Cambodia Department of Cinema: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="fj_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Fiji Audio Visual Commission: location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="uz_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Uzbekistan film commission / Uzbekkino: location facilitation and production support. UNKNOWN: financial incentive status.",
))

_r(FundEconomicsEntry(
    program_slug="om_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Oman Film Centre: location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="gy_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Guyana film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="gt_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Guatemala film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="bw_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Botswana film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="et_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Ethiopia film commission / Ethiopian Film Commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="ug_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Uganda Film Commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="mz_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Mozambique film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="zm_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Zambia National Arts Council (film): location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="zw_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Zimbabwe Film and Television Authority: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="ga_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Gabon film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="sc_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Seychelles film commission: location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="mn_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Mongolia film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="bd_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Bangladesh film commission (FDC/BFDC): location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="by_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Belarus film support (Belarusfilm): location facilitation and production support. Non-financial primarily.",
))

_r(FundEconomicsEntry(
    program_slug="bt_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Bhutan film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="mv_film_commission",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    typical_max_award_usd=None,
    is_competitive=False,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Maldives film commission: location facilitation and production support. Non-financial.",
))

_r(FundEconomicsEntry(
    program_slug="ba_film_centre",
    classification="grant",
    is_repayable=False,
    is_recoupable=False,
    has_equity_participation=False,
    is_soft_money=True,
    has_territorial_spend_requirement=True,
    typical_max_award_usd=300_000,
    is_competitive=True,
    stackable_with_incentives=True,
    is_government_assistance=False,
    notes="Bosnia and Herzegovina Film Fund (BHFF): selective production grants. Eurimages member. Not government assistance for EU fund purposes.",
))

# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------

def get_fund_economics(program_slug: str) -> FundEconomicsEntry | None:
    """Return FundEconomicsEntry for a given program slug, or None if not registered."""
    return _REGISTRY.get(program_slug)


def is_soft_money(program_slug: str) -> bool:
    """True if the fund is classified as soft money (non-repayable or deeply subordinated)."""
    entry = _REGISTRY.get(program_slug)
    return entry.is_soft_money if entry else False


def is_government_assistance(program_slug: str) -> bool:
    """True if the fund's proceeds constitute government assistance (reduces tax credit basis)."""
    entry = _REGISTRY.get(program_slug)
    return entry.is_government_assistance if entry else False


def get_typical_max_usd(program_slug: str) -> int | None:
    """Return typical maximum award in USD, or None if unknown."""
    entry = _REGISTRY.get(program_slug)
    return entry.typical_max_award_usd if entry else None


def list_all_slugs() -> list[str]:
    """Return all registered fund slugs."""
    return list(_REGISTRY.keys())
