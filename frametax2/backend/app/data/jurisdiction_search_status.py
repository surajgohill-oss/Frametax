"""
jurisdiction_search_status.py

Search coverage status records for jurisdictions that have been actively
searched for film/TV production incentives but have no known program.

Status values:
  PROGRAM_FOUND          — program exists; see GlobalProgramEntry records
  NO_KNOWN_PROGRAM_FOUND — searched; no meaningful incentive/grant found
  NOT_YET_SEARCHED       — not yet researched (inferred from absence)

Note: PROGRAM_FOUND records are derived from ALL_PROGRAMS at runtime.
Only NO_KNOWN_PROGRAM_FOUND records need explicit entries here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JurisdictionSearchStatus:
    jurisdiction_code: str
    country_name: str
    search_status: str   # PROGRAM_FOUND | NO_KNOWN_PROGRAM_FOUND | NOT_YET_SEARCHED
    source_url: str      # official agency or commission URL where search was conducted
    search_notes: str
    searched_at: str     # ISO date YYYY-MM-DD


# ---------------------------------------------------------------------------
# Jurisdictions searched with NO meaningful film/TV production incentive found
# ---------------------------------------------------------------------------

NO_PROGRAM_RECORDS: list[JurisdictionSearchStatus] = [

    # -----------------------------------------------------------------------
    # Caribbean — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="AG",
        country_name="Antigua and Barbuda",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitantiguabarbuda.com",
        search_notes="No dedicated film incentive or rebate program identified. Tourism authority handles location queries on ad-hoc basis only. No formal financial incentive confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="AI",
        country_name="Anguilla",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.anguilla-vacation.com",
        search_notes="British Overseas Territory. No film incentive or rebate program identified. Location facilitation only through Tourism Department.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="AW",
        country_name="Aruba",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.aruba.com/us/filming-in-aruba",
        search_notes="Tourism authority provides location facilitation. No formal financial incentive, rebate, or production grant program identified for foreign productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="BM",
        country_name="Bermuda",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.bermudatourism.com",
        search_notes="No film incentive program identified. Bermuda Tourism Authority handles production enquiries on a case-by-case basis only. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="BZ",
        country_name="Belize",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.belizetourism.org",
        search_notes="Belize Tourism Board handles production facilitation. No formal financial incentive or rebate program identified for foreign film/TV productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="KY",
        country_name="Cayman Islands",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitcaymanislands.com",
        search_notes="No film incentive or rebate program identified. Department of Tourism handles location requests on case-by-case basis. No formal program confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="DM",
        country_name="Dominica",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.discoverdominica.com",
        search_notes="Discover Dominica Authority handles filming enquiries. No formal incentive, rebate, or grant program for foreign film productions identified.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="GD",
        country_name="Grenada",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.puregrenada.com",
        search_notes="No dedicated film incentive program identified. Grenada Tourism Authority handles production enquiries informally.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="KN",
        country_name="Saint Kitts and Nevis",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.stkittstourism.kn",
        search_notes="No formal film incentive program identified. St. Kitts Tourism Authority handles location enquiries only. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="LC",
        country_name="Saint Lucia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.stlucia.org",
        search_notes="Saint Lucia Tourism Authority handles filming requests. No formal financial incentive program identified for foreign productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="VC",
        country_name="Saint Vincent and the Grenadines",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.discoversvg.com",
        search_notes="No film incentive identified. Tourism SVG handles ad-hoc location facilitation. No formal financial program confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SR",
        country_name="Suriname",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.surinametourism.sr",
        search_notes="No dedicated film/TV production incentive program identified for Suriname. Tourism Foundation Suriname handles enquiries informally.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TC",
        country_name="Turks and Caicos Islands",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.turksandcaicostourism.com",
        search_notes="British Overseas Territory. No formal film incentive program identified. Tourism Board handles productions on an ad-hoc basis.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # Central America — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="HN",
        country_name="Honduras",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.hondurastips.hn",
        search_notes="No formal film production incentive identified for Honduras. Limited film commission infrastructure. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SV",
        country_name="El Salvador",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.elsalvador.travel",
        search_notes="No formal film incentive program identified. CORSATUR handles tourism and location enquiries. No production rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="NI",
        country_name="Nicaragua",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.intur.gob.ni",
        search_notes="No dedicated film production incentive identified. INTUR handles tourism. INCINE (Instituto Nicaragüense de Cine) exists as regulatory/archival body only.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # South America — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="BO",
        country_name="Bolivia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.cinematecanacional.gob.bo",
        search_notes="Cinemateca Boliviana exists as an archival institution. No foreign production incentive, rebate, or grant program identified.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="PY",
        country_name="Paraguay",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.secp.gov.py",
        search_notes="Secretaría Nacional de Cultura handles cultural matters. No formal film production incentive or rebate identified for Paraguay.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # Africa — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="CD",
        country_name="Democratic Republic of the Congo",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.artsculturecd.gouv.cd",
        search_notes="Ministry of Arts, Culture and Heritage exists. No formal foreign production incentive program identified. Political instability and infrastructure constraints limit program development.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="GM",
        country_name="Gambia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitthegambia.gm",
        search_notes="No dedicated film incentive program identified for Gambia. National Centre for Arts and Culture handles cultural matters. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="ML",
        country_name="Mali",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.gouv.ml",
        search_notes="No formal foreign production incentive identified. Political instability since 2012/2021 limits program development. Ministry of Culture exists but no incentive confirmed.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # MENA — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="YE",
        country_name="Yemen",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.yemenembassy.org",
        search_notes="No film incentive program. Ongoing armed conflict since 2014 prevents meaningful international production activity or incentive program development.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="IQ",
        country_name="Iraq",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.moc.gov.iq",
        search_notes="Iraqi Ministry of Culture exists. No formal foreign production incentive identified. Security constraints and regulatory complexity limit international productions.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # Central Asia — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="KG",
        country_name="Kyrgyzstan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.minculture.gov.kg",
        search_notes="Ministry of Culture of the Kyrgyz Republic handles film regulatory matters. No formal production incentive or rebate program identified.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TJ",
        country_name="Tajikistan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.mcst.tj",
        search_notes="Ministry of Culture handles film matters. No formal foreign production incentive identified. Infrastructure constraints limit international productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TM",
        country_name="Turkmenistan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.turkmenistan.gov.tm",
        search_notes="Highly restricted access for foreign productions. No formal film incentive program identified. Government controls all media production.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # Asia — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="PK",
        country_name="Pakistan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.nfdc.gov.pk",
        search_notes="National Film Development Corporation Pakistan handles domestic production. No formal foreign production incentive or cash rebate identified for international productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="NP",
        country_name="Nepal",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.ntb.gov.np",
        search_notes="Nepal Tourism Board handles filming enquiries. No formal financial incentive program for foreign productions identified. Permit facilitation only.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MM",
        country_name="Myanmar",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.mip.gov.mm",
        search_notes="Ministry of Information handles film matters. No formal production incentive identified. Political situation since 2021 limits foreign production activity.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="LA",
        country_name="Laos",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourismlaos.org",
        search_notes="Lao National Tourism Administration handles filming. No formal financial incentive or rebate program identified for foreign productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="BN",
        country_name="Brunei Darussalam",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.bruneitourism.com",
        search_notes="Brunei Tourism Board handles filming enquiries. No formal production incentive, rebate, or grant program identified.",
        searched_at="2026-06-22",
    ),

    # -----------------------------------------------------------------------
    # Oceania / Pacific — searched, no known incentive program
    # -----------------------------------------------------------------------

    JurisdictionSearchStatus(
        jurisdiction_code="PG",
        country_name="Papua New Guinea",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.papuanewguinea.travel",
        search_notes="No formal film production incentive identified. Papua New Guinea Tourism Authority handles location enquiries only. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="WS",
        country_name="Samoa",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.samoa.travel",
        search_notes="No film incentive program identified for Samoa. Samoa Tourism Authority handles filming enquiries on an informal basis.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="VU",
        country_name="Vanuatu",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.vanuatutourism.com",
        search_notes="No dedicated film incentive program identified. Vanuatu Tourism Office handles filming enquiries. No financial program confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TO",
        country_name="Tonga",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.thekingdomoftonga.com",
        search_notes="No formal film production incentive identified for Tonga. Tourism Tonga handles production enquiries. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SB",
        country_name="Solomon Islands",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitsolomons.com.sb",
        search_notes="No film incentive program identified. Solomon Islands Visitors Bureau handles location enquiries only. No financial incentive confirmed.",
        searched_at="2026-06-22",
    ),
]

# Convenience sets for report building
NO_PROGRAM_CODES: frozenset[str] = frozenset(
    r.jurisdiction_code for r in NO_PROGRAM_RECORDS
    if r.search_status == "NO_KNOWN_PROGRAM_FOUND"
)
