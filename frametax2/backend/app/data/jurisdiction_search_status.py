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

    # -----------------------------------------------------------------------
    # Wave-5: Final global pass — remaining 40 UN-member countries
    # -----------------------------------------------------------------------

    # Europe (micro-states / Eastern Europe)
    JurisdictionSearchStatus(
        jurisdiction_code="AD",
        country_name="Andorra",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitandorra.com",
        search_notes="Micro-state between France and Spain. No dedicated film incentive or rebate programme identified. Tourism Ministry handles occasional film enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="LI",
        country_name="Liechtenstein",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.liechtenstein.li",
        search_notes="Micro-state between Switzerland and Austria. No dedicated film production incentive identified. Occasional productions use Liechtenstein locations via Swiss commission infrastructure.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MC",
        country_name="Monaco",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitmonaco.com",
        search_notes="City-state on French Riviera. No formal film production incentive or rebate identified. Some productions use Monaco locations; infrastructure handled by France/CNC.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SM",
        country_name="San Marino",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visitsanmarino.com",
        search_notes="Micro-state within Italy. No dedicated film incentive programme identified. Productions in San Marino typically handled through Italian film framework.",
        searched_at="2026-06-22",
    ),

    # Africa — West
    JurisdictionSearchStatus(
        jurisdiction_code="BF",
        country_name="Burkina Faso",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.culture.gov.bf",
        search_notes="Hosts FESPACO (Pan-African Film Festival) in Ouagadougou. CNC Burkina Faso exists but military rule since 2022 has suspended international cultural programmes. No formal foreign production incentive confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="BJ",
        country_name="Benin",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.benintourisme.com",
        search_notes="Ministry of Culture exists. No formal foreign film production incentive or rebate programme identified for Benin.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="CV",
        country_name="Cape Verde",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.caboverde.com",
        search_notes="Island archipelago. Tourism board handles occasional film enquiries. No formal film incentive or rebate programme identified.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="GN",
        country_name="Guinea",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.mcc.gov.gn",
        search_notes="Ministry of Culture exists. Political instability (military coup 2021) limits programme development. No formal foreign production incentive identified.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="GQ",
        country_name="Equatorial Guinea",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.ceiba-guinea-ecuatorial.org",
        search_notes="Oil-rich Central African state. No formal film production incentive or rebate programme identified for foreign productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="GW",
        country_name="Guinea-Bissau",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visaguineabissau.com",
        search_notes="One of West Africa's smallest economies. No formal film production incentive identified. Limited film commission infrastructure.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="LR",
        country_name="Liberia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.liberia.travel",
        search_notes="Post-conflict recovery. No formal film production incentive or rebate programme identified. Liberia Tourism Board handles limited enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MR",
        country_name="Mauritania",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.mauritanie-tourisme.mr",
        search_notes="Northwest African state. No formal film production incentive or rebate identified. Ministry of Culture exists but no confirmed programme.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="NE",
        country_name="Niger",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.gouv.ne",
        search_notes="Military coup 2023. No formal film production incentive identified. Tourism Ministry suspended. Security situation limits international productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SL",
        country_name="Sierra Leone",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.sierraleone.travel",
        search_notes="No formal film production incentive or rebate programme identified. Sierra Leone Tourism Board handles production enquiries informally.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TG",
        country_name="Togo",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.tg",
        search_notes="Ministry of Culture and Tourism exists. No formal foreign film production incentive identified for Togo.",
        searched_at="2026-06-22",
    ),

    # Africa — Central
    JurisdictionSearchStatus(
        jurisdiction_code="BI",
        country_name="Burundi",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.burundi.gov.bi",
        search_notes="No formal film production incentive identified. Political constraints and limited infrastructure restrict international productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="CF",
        country_name="Central African Republic",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.finance.gouv.cf",
        search_notes="Ongoing civil conflict. No formal film production incentive identified. Security situation makes international productions impractical.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="CG",
        country_name="Republic of Congo",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.gouv.cg",
        search_notes="No formal film production incentive or rebate programme identified for the Republic of Congo (Brazzaville). Some wildlife documentary productions visit.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="ST",
        country_name="São Tomé and Príncipe",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.saotomeprincipe.st",
        search_notes="Tiny island state in Gulf of Guinea. No formal film incentive identified. Tourism authority handles occasional filming enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TD",
        country_name="Chad",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.gouv.td",
        search_notes="Landlocked Central African state. No formal film production incentive identified. Security constraints limit international productions.",
        searched_at="2026-06-22",
    ),

    # Africa — East / Horn
    JurisdictionSearchStatus(
        jurisdiction_code="DJ",
        country_name="Djibouti",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.office-tourisme.dj",
        search_notes="Small Horn of Africa state. No formal film production incentive identified. Strategic military location; some documentary productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="ER",
        country_name="Eritrea",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.eritreainformation.com",
        search_notes="Highly isolated state. No formal film production incentive identified. Severe restrictions on foreign journalists and film crews.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SO",
        country_name="Somalia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.somaliancabinet.com",
        search_notes="Failed/fragile state. No film production incentive exists. Severe security risks make international productions impractical.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SS",
        country_name="South Sudan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.mct.gov.ss",
        search_notes="World's newest country (2011). Ongoing conflict. No film production incentive or programme identified. Ministry of Culture and Tourism exists but no confirmed programme.",
        searched_at="2026-06-22",
    ),

    # Africa — Southern
    JurisdictionSearchStatus(
        jurisdiction_code="LS",
        country_name="Lesotho",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.ltdc.org.ls",
        search_notes="Landlocked kingdom within South Africa. No formal film production incentive identified. Lesotho Tourism Development Corporation handles occasional productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MG",
        country_name="Madagascar",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.madagascar-tourisme.com",
        search_notes="No formal film production incentive identified for Madagascar. Office National du Tourisme de Madagascar handles filming enquiries. Popular for nature documentaries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MW",
        country_name="Malawi",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.malawitourism.com",
        search_notes="No formal film production incentive identified. Malawi Tourism Board handles filming enquiries. No rebate or grant confirmed.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SD",
        country_name="Sudan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourism.gov.sd",
        search_notes="Ongoing civil war since 2023. No film production incentive. International productions suspended due to security situation.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SZ",
        country_name="Eswatini",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.thekingdomofeswatini.com",
        search_notes="Small landlocked kingdom. No formal film production incentive identified. Eswatini Tourism Authority handles occasional productions.",
        searched_at="2026-06-22",
    ),

    # Africa — North / MENA
    JurisdictionSearchStatus(
        jurisdiction_code="LY",
        country_name="Libya",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.libyanembassy.com",
        search_notes="Ongoing conflict since 2011. No formal film production incentive. Security situation makes international productions impractical.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="SY",
        country_name="Syria",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.syria-tourism.org",
        search_notes="Ongoing civil war since 2011; transitional government as of late 2024. No film production incentive programme. Security situation severely limits international productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="AF",
        country_name="Afghanistan",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.afghanistanembassy.org",
        search_notes="Taliban government since 2021. No film production incentive. Severe restrictions on arts, media, and entertainment under Taliban rule. International productions not feasible.",
        searched_at="2026-06-22",
    ),

    # Asia — Small / island states
    JurisdictionSearchStatus(
        jurisdiction_code="KI",
        country_name="Kiribati",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.kiribatitourism.gov.ki",
        search_notes="Remote Pacific island nation. No formal film production incentive identified. Tourism board handles occasional production enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="KM",
        country_name="Comoros",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.tourisme.gouv.km",
        search_notes="Small island nation in Indian Ocean. No formal film production incentive identified. Tourism Ministry handles enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="MH",
        country_name="Marshall Islands",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.rmiembassyus.org",
        search_notes="Pacific island nation. No formal film production incentive. Nuclear test history makes some areas restricted for filming.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="FM",
        country_name="Micronesia",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.visit-micronesia.fm",
        search_notes="Federated States of Micronesia. No formal film production incentive identified. Tourism Board handles occasional filming enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="NR",
        country_name="Nauru",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.naurugov.nr",
        search_notes="World's smallest island republic. No film production incentive. Very limited tourism infrastructure.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="PW",
        country_name="Palau",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.pristineparadisepalau.com",
        search_notes="Pacific island nation. No formal film production incentive identified. Palau Tourism Authority handles filming enquiries for marine/diving productions.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="TL",
        country_name="Timor-Leste",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.timorlesteturismo.gov.tl",
        search_notes="Southeast Asia's newest nation (2002). No formal film production incentive identified. Tourism Authority handles enquiries.",
        searched_at="2026-06-22",
    ),
    JurisdictionSearchStatus(
        jurisdiction_code="HT",
        country_name="Haiti",
        search_status="NO_KNOWN_PROGRAM_FOUND",
        source_url="https://www.haititourisme.gouv.ht",
        search_notes="Ongoing humanitarian and security crisis. No formal film production incentive. International productions suspended due to gang violence and political instability.",
        searched_at="2026-06-22",
    ),
]

# Convenience sets for report building
NO_PROGRAM_CODES: frozenset[str] = frozenset(
    r.jurisdiction_code for r in NO_PROGRAM_RECORDS
    if r.search_status == "NO_KNOWN_PROGRAM_FOUND"
)
