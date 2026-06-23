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
