"""
financing_interaction_model.py — Phase D5: Financing interaction layer.

Encodes government assistance interactions, spend reduction rules,
stacking ceilings, cap interactions, and recoupment interactions.

No DB access. Pure Python. Complements stacking_rules.py and fund_economics_model.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FinancingInteraction:
    slug_a: str          # source program slug (the one that "causes" the interaction)
    slug_b: str          # target program slug (the one "affected")
    interaction_type: str  # govt_assistance | spend_reduction | cap_interaction | recoupment | stacking_ceiling
    reduction_pct: float | None   # fraction by which slug_b's qualifying basis is reduced
    ceiling_pct: float | None     # maximum combined % of budget that A+B can cover
    condition: str                # when this interaction applies
    jurisdiction: str | None      # jurisdiction where this applies (None = universal)
    is_confirmed: bool            # True = legally confirmed, False = DISCOVERY
    notes: str


# ---------------------------------------------------------------------------
# Government Assistance interactions
# (Source grant is govt assistance → reduces tax credit qualifying basis in same jurisdiction)
# ---------------------------------------------------------------------------

_GOV_ASSIST_INTERACTIONS: list[FinancingInteraction] = [
    # UK
    FinancingInteraction(
        "gb_lon_film_london", "uk_avec",
        "govt_assistance", 1.0, None,
        "Film London grant is government assistance — reduces qualifying UK expenditure basis for AVEC "
        "by the full grant amount received.",
        "GB", True,
        "Under UK film tax law, government assistance reduces QUKE basis £ for £.",
    ),
    FinancingInteraction(
        "gb_sct_screen_production", "uk_avec",
        "govt_assistance", 1.0, None,
        "Screen Scotland Production Growth Fund grant is government assistance — reduces AVEC basis.",
        "GB", True,
        "Screen Scotland is Scottish Government funding; treated as govt assistance for AVEC purposes.",
    ),
    FinancingInteraction(
        "gb_wls_film_fund", "uk_avec",
        "govt_assistance", 1.0, None,
        "Creative Wales / Wales Film Fund grant is government assistance — reduces AVEC basis.",
        "GB", True,
        "Welsh Government funding treated as govt assistance for AVEC purposes.",
    ),
    FinancingInteraction(
        "gb_film_hub_midlands", "uk_avec",
        "govt_assistance", 1.0, None,
        "Film Hub Midlands BFI Network grant is government assistance — reduces AVEC basis.",
        "GB", False,
        "BFI Network grants are public funds; likely government assistance for AVEC.",
    ),
    FinancingInteraction(
        "gb_creative_england", "uk_avec",
        "govt_assistance", 1.0, None,
        "Creative England development/production grant is government assistance — reduces AVEC basis.",
        "GB", True,
        "Creative England receives public funding; grants are government assistance.",
    ),
    # Ireland
    FinancingInteraction(
        "ie_screen_ireland_dev", "ie_section_481",
        "govt_assistance", 1.0, None,
        "Screen Ireland development and talent grants are government assistance — reduce "
        "Section 481 qualifying Irish expenditure basis.",
        "IE", True,
        "Section 481 legislation: government assistance from State bodies reduces qualifying basis.",
    ),
    FinancingInteraction(
        "ie_tourism_film", "ie_section_481",
        "govt_assistance", 0.5, None,
        "Tourism Ireland / Fáilte Ireland film support MAY constitute government assistance — "
        "could reduce Section 481 qualifying Irish expenditure basis.",
        "IE", False,
        "Tourism Ireland funding source is semi-state; legal opinion recommended.",
    ),
    FinancingInteraction(
        "ie_rte", "ie_section_481",
        "spend_reduction", 0.0, None,
        "RTÉ broadcaster investment is NOT government assistance for Section 481 purposes — "
        "treated as commercial co-investment, does not reduce qualifying basis.",
        "IE", True,
        "RTÉ commercial co-investment excluded from govt assistance treatment by Revenue guidance.",
    ),
    # France
    FinancingInteraction(
        "fr_cnc_production", "fr_trip",
        "govt_assistance", 1.0, None,
        "CNC selective advance is government assistance — reduces TRIP qualifying French expenditure "
        "basis by the advance amount.",
        "FR", True,
        "CNC is public body; its advances are government assistance reducing TRIP basis.",
    ),
    FinancingInteraction(
        "fr_cnc_animation", "fr_trip",
        "govt_assistance", 1.0, None,
        "CNC animation fund advance is government assistance — reduces TRIP qualifying basis.",
        "FR", True,
        "CNC animation COSIP/SESAM is public funding; reduces TRIP qualifying French spend.",
    ),
    FinancingInteraction(
        "fr_ara_regional", "fr_trip",
        "govt_assistance", 1.0, None,
        "Auvergne-Rhône-Alpes regional fund grant is government assistance — reduces TRIP basis.",
        "FR", True,
        "French regional funds (collectivités) are government assistance for TRIP purposes.",
    ),
    FinancingInteraction(
        "fr_idf_regional", "fr_trip",
        "govt_assistance", 1.0, None,
        "Île-de-France regional fund grant is government assistance — reduces TRIP basis.",
        "FR", True,
        "Île-de-France (CNC/région) is government assistance for TRIP purposes.",
    ),
    FinancingInteraction(
        "fr_naq_regional", "fr_trip",
        "govt_assistance", 1.0, None,
        "Nouvelle-Aquitaine regional fund is government assistance — reduces TRIP basis.",
        "FR", True,
        "French regional funds are government assistance for TRIP.",
    ),
    FinancingInteraction(
        "fr_occ_regional", "fr_trip",
        "govt_assistance", 1.0, None,
        "Occitanie regional fund is government assistance — reduces TRIP basis.",
        "FR", True,
        "French regional funds are government assistance for TRIP.",
    ),
    # Canada
    FinancingInteraction(
        "ca_cmf", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Canada Media Fund grants are government assistance — reduce CPTC qualifying labour "
        "expenditure basis dollar-for-dollar.",
        "CA", True,
        "Income Tax Act s. 125.4: government assistance reduces qualifying labour cost.",
    ),
    FinancingInteraction(
        "ca_bell_fund", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Bell Media Fund grants are government assistance — reduce CPTC qualifying labour basis.",
        "CA", True,
        "Bell Fund is a certified independent production fund (CIPF) — government assistance.",
    ),
    FinancingInteraction(
        "ca_nsi_fund", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "National Screen Institute grants are government assistance — reduce CPTC qualifying labour.",
        "CA", True,
        "NSI receives public funding; grants are government assistance.",
    ),
    FinancingInteraction(
        "ca_telefilm_dev", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Telefilm Canada development funding is government assistance — reduces CPTC basis.",
        "CA", True,
        "Telefilm is Crown corporation; development advances are government assistance.",
    ),
    FinancingInteraction(
        "ca_telefilm_export", "ca_federal_cptc",
        "govt_assistance", 0.5, None,
        "Telefilm Canada export grants MAY constitute government assistance — could reduce CPTC basis.",
        "CA", False,
        "Export grants are at arm's length; CRA treatment uncertain. Confirm with tax counsel.",
    ),
    FinancingInteraction(
        "ca_ns_film_incentive", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Nova Scotia production incentive is government assistance — reduces CPTC qualifying labour basis.",
        "CA-NS", True,
        "Provincial incentive is government assistance for federal CPTC purposes.",
    ),
    FinancingInteraction(
        "ca_mb_film_mb", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Manitoba Film & Music grants are government assistance — reduce CPTC qualifying basis.",
        "CA-MB", True,
        "Manitoba provincial grant is government assistance.",
    ),
    FinancingInteraction(
        "ca_nb_film_nb", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "New Brunswick Film grants are government assistance — reduce CPTC qualifying basis.",
        "CA-NB", True,
        "NB provincial grant is government assistance.",
    ),
    FinancingInteraction(
        "ca_nl_film_nl", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "NL Film Development Corp grants are government assistance — reduce CPTC qualifying basis.",
        "CA-NL", True,
        "Newfoundland provincial grant is government assistance.",
    ),
    FinancingInteraction(
        "ca_pe_film_pei", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Film PEI grants are government assistance — reduce CPTC qualifying basis.",
        "CA-PE", True,
        "PEI provincial grant is government assistance.",
    ),
    FinancingInteraction(
        "nohfc_production_fund", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Northern Ontario Heritage Fund is government assistance — reduces CPTC qualifying basis.",
        "CA-ON", True,
        "Northern Ontario Heritage Fund Corp is Crown agency; grants are government assistance.",
    ),
    # Ontario
    FinancingInteraction(
        "ca_on_ocase", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "Ontario OCASE is government assistance — reduces CPTC qualifying labour basis.",
        "CA-ON", True,
        "OCASE is provincial tax credit; treated as government assistance for federal CPTC.",
    ),
    FinancingInteraction(
        "ca_on_ocase", "on_ofttc",
        "govt_assistance", 1.0, None,
        "Ontario OCASE reduces OFTTC qualifying labour basis.",
        "CA-ON", True,
        "Ontario OCASE is govt assistance for OFTTC as well.",
    ),
    FinancingInteraction(
        "ca_bc_idmtc", "ca_federal_cptc",
        "govt_assistance", 1.0, None,
        "BC IDMTC is government assistance — reduces CPTC qualifying labour basis.",
        "CA-BC", True,
        "BC IDMTC is provincial tax credit; treated as government assistance for federal CPTC.",
    ),
    # Australia
    FinancingInteraction(
        "au_pdv_offset", "au_location_offset",
        "govt_assistance", 1.0, None,
        "AU PDV Offset is government financial assistance — reduces QAPE for Location Offset "
        "by the full PDV rebate amount where PDV expenditure overlaps.",
        "AU", True,
        "Screen Australia guidelines: PDV Offset is govt financial assistance reducing Location Offset QAPE.",
    ),
    FinancingInteraction(
        "au_pdv_offset", "au_producer_offset",
        "govt_assistance", 1.0, None,
        "AU PDV Offset is government financial assistance — reduces QAPE for Producer Offset.",
        "AU", True,
        "Screen Australia guidelines: PDV Offset is govt financial assistance.",
    ),
    FinancingInteraction(
        "au_screen_production", "au_producer_offset",
        "govt_assistance", 1.0, None,
        "Screen Australia production investment is government assistance — reduces Producer Offset QAPE.",
        "AU", True,
        "Screen Australia is government agency; investment is government assistance.",
    ),
    FinancingInteraction(
        "au_vic_film_victoria", "au_producer_offset",
        "govt_assistance", 1.0, None,
        "VicScreen / Film Victoria grants are government assistance — reduce Producer Offset QAPE.",
        "AU-VIC", True,
        "Victorian Government agency funding is government assistance.",
    ),
    FinancingInteraction(
        "au_qld_screen", "au_location_offset",
        "govt_assistance", 1.0, None,
        "Screen Queensland attraction incentive is government assistance — reduces Location Offset QAPE.",
        "AU-QLD", True,
        "Queensland Government funding is government assistance.",
    ),
    FinancingInteraction(
        "au_nsw_screen", "au_location_offset",
        "govt_assistance", 1.0, None,
        "Screen NSW fund is government assistance — reduces Location Offset QAPE.",
        "AU-NSW", True,
        "NSW Government agency funding is government assistance.",
    ),
    FinancingInteraction(
        "au_tas_screen", "au_producer_offset",
        "govt_assistance", 1.0, None,
        "Screen Tasmania grants are government assistance — reduce Producer Offset QAPE.",
        "AU-TAS", True,
        "Tasmanian Government funding is government assistance.",
    ),
    FinancingInteraction(
        "au_tourism_film", "au_producer_offset",
        "govt_assistance", 0.5, None,
        "Tourism Australia production support MAY be government assistance — "
        "could reduce Producer Offset QAPE.",
        "AU", False,
        "Tourism Australia is government agency; production support likely government assistance.",
    ),
]


# ---------------------------------------------------------------------------
# Spend reduction interactions
# (source program's minimum spend requirement interacts with target program's qualifying basis)
# ---------------------------------------------------------------------------

_SPEND_REDUCTION_INTERACTIONS: list[FinancingInteraction] = [
    FinancingInteraction(
        "eu_eurimages", "at_ofi_grants",
        "spend_reduction", 0.0, None,
        "Eurimages grant does NOT reduce Austrian ÖFI qualifying basis — different funding sources.",
        "AT", True,
        "Eurimages is Council of Europe; ÖFI is Austrian national. No double-count issue.",
    ),
    FinancingInteraction(
        "eu_eurimages", "fr_trip",
        "spend_reduction", 0.0, None,
        "Eurimages grant does NOT reduce French TRIP qualifying basis — Eurimages is CoE, not French govt.",
        "FR", True,
        "Eurimages is Council of Europe institution, not French government. No TRIP basis impact.",
    ),
    FinancingInteraction(
        "ibermedia_programme", "es_cat_icec",
        "spend_reduction", 0.0, None,
        "Ibermedia grant does NOT reduce Catalan ICEC qualifying basis.",
        "ES-CAT", True,
        "Ibermedia is international fund; ICEC is regional Spanish. No overlap.",
    ),
]


# ---------------------------------------------------------------------------
# Stacking ceiling interactions
# (maximum combined value as % of production budget)
# ---------------------------------------------------------------------------

_STACKING_CEILING_INTERACTIONS: list[FinancingInteraction] = [
    FinancingInteraction(
        "eu_eurimages", "eu_media_fund",
        "stacking_ceiling", None, 0.50,
        "Eurimages + EU MEDIA combined ceiling: typically max 50% of production budget from EU/CoE funds.",
        "EU", False,
        "UNKNOWN confirmed ceiling — Eurimages and MEDIA have individual caps; combined soft ceiling ~50%.",
    ),
    FinancingInteraction(
        "fr_cnc_production", "fr_trip",
        "stacking_ceiling", None, 0.80,
        "CNC selective advance + TRIP combined: practical ceiling ~80% of qualifying French budget.",
        "FR", False,
        "No regulatory ceiling specified; practical ceiling based on qualifying expenditure structure.",
    ),
    FinancingInteraction(
        "ca_cmf", "ca_federal_cptc",
        "stacking_ceiling", None, 0.70,
        "CMF + CPTC combined: effective ceiling ~70% of qualifying production costs in practice.",
        "CA", False,
        "No regulatory ceiling; practical ceiling reflects CMF cap + CPTC 25% of labour after deductions.",
    ),
    FinancingInteraction(
        "uk_avec", "gb_bfi_production",
        "stacking_ceiling", None, 0.60,
        "AVEC + BFI Production Fund combined: max 60% of total budget (BFI internal policy).",
        "GB", True,
        "BFI Production Fund policy limits total public funding to 60% of budget.",
    ),
    FinancingInteraction(
        "eu_eurimages", "at_ofi_grants",
        "stacking_ceiling", None, 0.80,
        "Eurimages + ÖFI combined ceiling: Austrian co-productions max ~80% from public funds.",
        "AT", False,
        "ÖFI policy: total public funding typically capped at 80% of budget.",
    ),
]


# ---------------------------------------------------------------------------
# Recoupment interactions
# (how recoupable advances interact with equity and other recoupable positions)
# ---------------------------------------------------------------------------

_RECOUPMENT_INTERACTIONS: list[FinancingInteraction] = [
    FinancingInteraction(
        "gb_bfi_production", "gb_bbc_films",
        "recoupment", None, None,
        "BFI Production Fund and BBC Films both recoup from gross receipts. "
        "BFI typically in first position; BBC Films subordinated.",
        "GB", True,
        "Standard UK co-production waterfall: BFI first recoupment, broadcaster subordinated.",
    ),
    FinancingInteraction(
        "gb_bfi_production", "gb_film4",
        "recoupment", None, None,
        "BFI Production Fund and Film4 both recoup. BFI first position; Film4 pari passu with other equity.",
        "GB", True,
        "Standard UK co-production waterfall.",
    ),
    FinancingInteraction(
        "fr_cnc_production", "fr_canal_plus",
        "recoupment", None, None,
        "CNC advance and CANAL+ co-investment: CNC recoupment from gross receipts; "
        "CANAL+ recoups via minimum guarantee against theatrical receipts.",
        "FR", True,
        "French co-production standard waterfall: CNC advance subordinated to MG.",
    ),
    FinancingInteraction(
        "eu_eurimages", "eu_media_fund",
        "recoupment", None, None,
        "Eurimages loan/advance and MEDIA grant are both recoupable. "
        "Eurimages typically pari passu with national fund; MEDIA grant at back end.",
        "EU", True,
        "Council of Europe standard recoupment: Eurimages pari passu, MEDIA subordinated.",
    ),
    FinancingInteraction(
        "ca_cmf", "ca_telefilm_dev",
        "recoupment", None, None,
        "CMF advance and Telefilm development advance both recoup. "
        "Telefilm senior to CMF in development recoupment; both subordinated to production financing.",
        "CA", True,
        "Standard Canadian production waterfall: Telefilm dev advance senior at dev stage.",
    ),
    FinancingInteraction(
        "nl_hbf", "eu_eurimages",
        "recoupment", None, None,
        "Netherlands Film Fund and Eurimages both recoup at pari passu. "
        "Combined recoupment structure must be agreed in co-production contracts.",
        "NL", True,
        "NFF and Eurimages standard: pari passu recoupment in Netherlands co-productions.",
    ),
    FinancingInteraction(
        "de_dfff", "de_ffa",
        "recoupment", None, None,
        "DFFF rebate and FFA reference funding both reduce German production cost basis. "
        "FFA is repayable loan; DFFF is rebate. FFA recoupment from distribution receipts.",
        "DE", True,
        "German co-production waterfall: DFFF rebate non-recoupable; FFA loan recoupable.",
    ),
]


# ---------------------------------------------------------------------------
# Full registry
# ---------------------------------------------------------------------------

ALL_FINANCING_INTERACTIONS: list[FinancingInteraction] = (
    _GOV_ASSIST_INTERACTIONS
    + _SPEND_REDUCTION_INTERACTIONS
    + _STACKING_CEILING_INTERACTIONS
    + _RECOUPMENT_INTERACTIONS
)


# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------

def get_govt_assistance_impact(
    slug_a: str,
    slug_b: str,
) -> FinancingInteraction | None:
    """
    Return the government assistance interaction where slug_a reduces slug_b's basis.
    Returns None if no such interaction is registered.
    """
    for ia in _GOV_ASSIST_INTERACTIONS:
        if ia.slug_a == slug_a and ia.slug_b == slug_b:
            return ia
    return None


def get_stacking_ceiling(slug_a: str, slug_b: str) -> float | None:
    """
    Return the stacking ceiling (as fraction 0-1) for the combination of slug_a and slug_b.
    Returns None if no ceiling is defined.
    """
    pair = frozenset({slug_a, slug_b})
    for ia in _STACKING_CEILING_INTERACTIONS:
        if frozenset({ia.slug_a, ia.slug_b}) == pair:
            return ia.ceiling_pct
    return None


def get_all_govt_assistance_for_slug(slug_b: str) -> list[FinancingInteraction]:
    """Return all govt assistance interactions that reduce slug_b's qualifying basis."""
    return [ia for ia in _GOV_ASSIST_INTERACTIONS if ia.slug_b == slug_b]


def get_recoupment_interactions(slug: str) -> list[FinancingInteraction]:
    """Return all recoupment interactions involving a given slug."""
    return [ia for ia in _RECOUPMENT_INTERACTIONS
            if ia.slug_a == slug or ia.slug_b == slug]


def compute_effective_qualifying_basis(
    slug_b: str,
    total_qualifying_spend: float,
    grants_received: dict[str, float],
) -> float:
    """
    Compute the effective qualifying basis for slug_b after deducting government assistance.

    grants_received: {slug_a: amount_usd} — amounts received from each slug_a.
    Returns effective qualifying spend (cannot go below 0).
    """
    basis = total_qualifying_spend
    for ia in _GOV_ASSIST_INTERACTIONS:
        if ia.slug_b == slug_b and ia.reduction_pct and ia.reduction_pct > 0:
            grant_amount = grants_received.get(ia.slug_a, 0.0)
            basis -= grant_amount * ia.reduction_pct
    return max(basis, 0.0)


def list_all_govt_assistance_slugs() -> list[str]:
    """Return slugs of all programs known to be government assistance."""
    return list({ia.slug_a for ia in _GOV_ASSIST_INTERACTIONS})
