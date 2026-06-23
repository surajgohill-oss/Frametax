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
