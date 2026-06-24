from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GraphEdge:
    source_type: str   # "program" | "treaty" | "fund" | "region"
    source_slug: str
    edge_type: str     # "unlocks" | "requires" | "improves" | "reduces" | "incompatible_with"
    target_type: str   # "program" | "treaty" | "fund" | "test" | "region"
    target_slug: str
    condition: str | None = None
    magnitude: float | None = None
    notes: str = ""


_EDGES: list[GraphEdge] = [

    # -------------------------------------------------------------------------
    # Treaty → Program (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "uk_avec",
              condition="Canadian majority co-production"),
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="UK majority co-production"),

    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "ie_section_481"),

    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "fr_trip"),

    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "au_producer_offset"),

    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "de_dfff"),

    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "au_producer_offset"),

    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "it_tax_credit_foreign"),
    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "fr_trip"),

    # -------------------------------------------------------------------------
    # Treaty → Fund (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "eu_eurimages", "unlocks", "fund", "eu_eurimages",
              condition="Member country eligibility for Eurimages grant"),
    GraphEdge("treaty", "ibermedia_programme", "unlocks", "fund", "ibermedia_programme",
              condition="Member country eligibility for Ibermedia fund"),
    GraphEdge("treaty", "eu_european_convention", "unlocks", "fund", "eu_european_convention",
              condition="Signatory country access to European Convention co-production framework"),

    # -------------------------------------------------------------------------
    # Program → Test (requires)
    # -------------------------------------------------------------------------
    GraphEdge("program", "uk_avec", "requires", "test", "uk_bfi_cultural_test"),
    GraphEdge("program", "ca_federal_cptc", "requires", "test", "ca_content_test"),
    GraphEdge("program", "ca_cmf", "requires", "test", "ca_content_test"),
    GraphEdge("program", "au_producer_offset", "requires", "test", "au_content_test"),
    GraphEdge("program", "eu_eurimages", "requires", "test", "eu_eurimages_test"),
    GraphEdge("program", "ibermedia_programme", "requires", "test", "ibermedia_test"),
    GraphEdge("program", "fr_cnc_production", "requires", "test", "fr_cnc_cultural_test"),
    GraphEdge("program", "eu_media_fund", "requires", "test", "eu_european_convention_test"),

    # -------------------------------------------------------------------------
    # Program → Program (improves)
    # -------------------------------------------------------------------------
    GraphEdge("program", "eu_eurimages", "improves", "program", "at_ofi_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Austrian partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "pl_pisf_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Polish partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "cz_czech_film_fund",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Czech partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "hu_nfi_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Hungarian partners"),

    GraphEdge("program", "film_i_vast", "improves", "program", "se_svt",
              magnitude=0.15,
              notes="Regional Swedish production attracts broadcaster interest"),

    GraphEdge("program", "ca_cmf", "improves", "program", "ca_federal_cptc",
              magnitude=0.1,
              notes="Certified Canadian content qualifies for both CMF and CPTC"),
    GraphEdge("program", "ca_bell_fund", "improves", "program", "ca_cmf",
              magnitude=0.1),

    # -------------------------------------------------------------------------
    # Program → Program (reduces)
    # -------------------------------------------------------------------------
    GraphEdge("program", "ie_screen_ireland_dev", "reduces", "program", "ie_section_481",
              condition="Screen Ireland development grants are govt assistance — reduces Section 481 qualifying basis",
              magnitude=0.05),
    GraphEdge("program", "gb_lon_film_london", "reduces", "program", "uk_avec",
              condition="Film London grant reduces AVEC qualifying expenditure basis",
              magnitude=0.05),
    GraphEdge("program", "au_tourism_film", "reduces", "program", "au_producer_offset",
              condition="Tourism Australia grant may constitute govt assistance reducing QAPE",
              magnitude=0.02),
    GraphEdge("program", "ca_telefilm_export", "reduces", "program", "ca_federal_cptc",
              condition="Telefilm export grant is govt assistance potentially reducing CPTC labour basis",
              magnitude=0.03),
    GraphEdge("program", "au_pdv_offset", "reduces", "program", "au_location_offset",
              condition="PDV Offset is govt assistance — reduces QAPE for Location Offset if combined",
              magnitude=0.10),
    GraphEdge("program", "au_pdv_offset", "reduces", "program", "au_producer_offset",
              condition="PDV Offset is govt assistance — reduces QAPE for Producer Offset if combined",
              magnitude=0.10),
    GraphEdge("program", "fr_cnc_animation", "reduces", "program", "fr_trip",
              condition="CNC animation fund is govt assistance reducing TRIP qualifying expenditure",
              magnitude=0.05),

    # -------------------------------------------------------------------------
    # Program → Program (incompatible_with)
    # -------------------------------------------------------------------------
    GraphEdge("program", "au_location_offset", "incompatible_with", "program", "au_producer_offset",
              notes="Same production cannot claim both — different offset tracks"),
    GraphEdge("program", "se_sk_film_skane", "incompatible_with", "program", "se_ab_filmstockholm",
              notes="Swedish regional funds mutually exclusive for same spend"),
    GraphEdge("program", "dk_cph_film_fund", "incompatible_with", "program", "dk_fyn_film",
              notes="Danish regional funds mutually exclusive for same spend"),
    GraphEdge("program", "ae_dxb_dpi", "incompatible_with", "program", "ae_adfc_rebate",
              notes="Dubai and Abu Dhabi rebates cannot both apply to the same spend"),

    # -------------------------------------------------------------------------
    # Broadcaster → Incentive (improves)
    # -------------------------------------------------------------------------
    GraphEdge("program", "gb_bbc_films", "improves", "program", "uk_avec",
              condition="BBC co-production strengthens BFI cultural test British creative element score"),
    GraphEdge("program", "gb_film4", "improves", "program", "uk_avec",
              condition="BBC co-production strengthens BFI cultural test British creative element score"),
    GraphEdge("program", "fr_canal_plus", "improves", "program", "fr_trip",
              condition="CANAL+ co-production evidence of French creative commitment"),
    GraphEdge("program", "se_svt", "improves", "program", "no_nfi_grants",
              condition="SVT/NRK broadcaster co-production demonstrates Nordic market reach; improves NFI application"),
    GraphEdge("program", "no_nrk", "improves", "program", "no_nfi_grants",
              condition="SVT/NRK broadcaster co-production demonstrates Nordic market reach; improves NFI application"),
    GraphEdge("program", "dk_dr", "improves", "program", "dk_dfi_support"),
    GraphEdge("program", "fi_yle", "improves", "program", "fi_ses_grants"),

    # -------------------------------------------------------------------------
    # Regional → National (requires / improves)
    # -------------------------------------------------------------------------
    GraphEdge("region", "no_vgn_viken", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_rog_vestnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_tro_nordnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_inl_midtnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),

    GraphEdge("region", "film_i_vast", "improves", "program", "se_svt",
              condition="Västra Götaland-based production demonstrates regional cultural value"),
    GraphEdge("region", "gb_lon_film_london", "improves", "program", "uk_avec",
              condition="Film London increases AVEC qualifying UK spend concentration in London"),
    GraphEdge("region", "gb_sct_screen_production", "improves", "program", "uk_avec"),
    GraphEdge("region", "gb_wls_film_fund", "improves", "program", "uk_avec"),

    GraphEdge("region", "au_vic_film_victoria", "improves", "program", "au_producer_offset",
              condition="VicScreen support increases Australian content credentials"),
    GraphEdge("region", "au_tas_screen", "improves", "program", "au_producer_offset"),
    GraphEdge("region", "au_nt_territory", "improves", "program", "au_producer_offset"),

    # -------------------------------------------------------------------------
    # Streamer → Incentive (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("program", "streamer_uk_local", "unlocks", "program", "uk_avec",
              condition="Content commissioned to satisfy UK streamer obligation typically qualifies for AVEC"),
    GraphEdge("program", "streamer_uk_local", "unlocks", "program", "gb_bbc_films",
              condition="Streamer-commissioned content may include BBC co-production"),
]


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

STRUCTURE_GRAPH_EDGES: list[GraphEdge] = _EDGES


# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------

def get_edges_from(source_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.source_slug == source_slug]


def get_edges_to(target_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.target_slug == target_slug]


def get_edges_by_type(edge_type: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.edge_type == edge_type]


def get_unlocked_by(source_slug: str) -> list[str]:
    return [e.target_slug for e in _EDGES
            if e.source_slug == source_slug and e.edge_type == "unlocks"]


def get_requirements(target_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES
            if e.target_slug == target_slug and e.edge_type == "requires"]


def get_incompatibilities(slug: str) -> list[str]:
    results: list[str] = []
    for e in _EDGES:
        if e.edge_type != "incompatible_with":
            continue
        if e.source_slug == slug:
            results.append(e.target_slug)
        elif e.target_slug == slug:
            results.append(e.source_slug)
    return results
