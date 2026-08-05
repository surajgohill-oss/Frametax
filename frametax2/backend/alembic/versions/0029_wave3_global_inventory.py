"""0029 — Wave-3 global inventory: 43 new programs across 38 jurisdictions.

Seeds jurisdictions, incentive programs, and cost benchmarks for:

  US states (6):              GA, LA, NM, NY, NV, RI
  Caribbean / C.America (4):  BS (Bahamas), BB (Barbados), PA (Panama), CR (Costa Rica)
  South America (2):          PE (Peru), EC (Ecuador)
  Africa (5):                 EG, GH, RW, TZ, SN
  Gulf States (2):            KW, BH
  Central Asia / Caucasus (3): GE (Georgia), KZ, AM
  Southeast Asia (3):         VN, ID, KH
  East Asia (3):              JP, TW, HK
  Balkans / Europe (4):       AL, ME, MK, BA
  Pacific (1):                FJ
  Supranationals (2):         IBERO, ACP
  Germany regional (2):       DE-BY, DE-NW
  Sweden regional (1):        SE-VG

  + 10 grant/fund programs:
    IBERO (IBERMEDIA), DE-BY (FFF Bayern), DE-NW (NRW Filmstiftung),
    HK (Film Dev Fund), IN (NFDC Co-prod), SG (IMDA),
    TW (TAICCA), SE-VG (Film i Väst), ACP (ACP Films), US (ITVS)

All entries are DISCOVERY tier.

Revision ID: 0029
Revises: 0028
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029"
down_revision: Union[str, None] = "0028"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0029-0000-0001-000000000000")
_DISC = "DISCOVERY"
_BM_SOURCE = (
    "Production market knowledge — not verified from primary labour cost surveys. "
    "Confidence tier: DISCOVERY."
)
_BM_DATE = "2025-06"


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# Jurisdiction data
# (code, name, level, currency_code, country_code, parent_code or None)
# ---------------------------------------------------------------------------
_COUNTRIES: list[tuple] = [
    # Caribbean & Central America
    ("BS",    "Bahamas",                              "country",       "BSD",  "BS",    None),
    ("BB",    "Barbados",                             "country",       "BBD",  "BB",    None),
    ("PA",    "Panama",                               "country",       "USD",  "PA",    None),
    ("CR",    "Costa Rica",                           "country",       "CRC",  "CR",    None),
    # South America
    ("PE",    "Peru",                                 "country",       "PEN",  "PE",    None),
    ("EC",    "Ecuador",                              "country",       "USD",  "EC",    None),
    # Africa
    ("EG",    "Egypt",                                "country",       "EGP",  "EG",    None),
    ("GH",    "Ghana",                                "country",       "GHS",  "GH",    None),
    ("RW",    "Rwanda",                               "country",       "RWF",  "RW",    None),
    ("TZ",    "Tanzania",                             "country",       "TZS",  "TZ",    None),
    ("SN",    "Senegal",                              "country",       "XOF",  "SN",    None),
    # Gulf States
    ("KW",    "Kuwait",                               "country",       "KWD",  "KW",    None),
    ("BH",    "Bahrain",                              "country",       "BHD",  "BH",    None),
    # Central Asia / Caucasus
    ("GE",    "Georgia",                              "country",       "GEL",  "GE",    None),
    ("KZ",    "Kazakhstan",                           "country",       "KZT",  "KZ",    None),
    ("AM",    "Armenia",                              "country",       "AMD",  "AM",    None),
    # Southeast Asia
    ("VN",    "Vietnam",                              "country",       "VND",  "VN",    None),
    ("ID",    "Indonesia",                            "country",       "IDR",  "ID",    None),
    ("KH",    "Cambodia",                             "country",       "KHR",  "KH",    None),
    # East Asia
    ("JP",    "Japan",                                "country",       "JPY",  "JP",    None),
    ("TW",    "Taiwan",                               "country",       "TWD",  "TW",    None),
    ("HK",    "Hong Kong SAR",                        "country",       "HKD",  "HK",    None),
    # Balkans / Additional Europe
    ("AL",    "Albania",                              "country",       "ALL",  "AL",    None),
    ("ME",    "Montenegro",                           "country",       "EUR",  "ME",    None),
    ("MK",    "North Macedonia",                      "country",       "MKD",  "MK",    None),
    ("BA",    "Bosnia and Herzegovina",               "country",       "BAM",  "BA",    None),
    # Pacific
    ("FJ",    "Fiji",                                 "country",       "FJD",  "FJ",    None),
    # Supranationals
    ("IBERO", "Ibero-American Region (SEGIB)",        "supranational", "EUR",  "IBERO", None),
    ("ACP",   "African, Caribbean and Pacific Group", "supranational", "EUR",  "ACP",   None),
]

_SUB_NATIONALS: list[tuple] = [
    # US states — wave 3
    ("US-GA", "United States — Georgia",              "state",  "USD", "US", "US"),
    ("US-LA", "United States — Louisiana",            "state",  "USD", "US", "US"),
    ("US-NM", "United States — New Mexico",           "state",  "USD", "US", "US"),
    ("US-NY", "United States — New York",             "state",  "USD", "US", "US"),
    ("US-NV", "United States — Nevada",               "state",  "USD", "US", "US"),
    ("US-RI", "United States — Rhode Island",         "state",  "USD", "US", "US"),
    # Germany regional
    ("DE-BY", "Germany — Bavaria",                    "region", "EUR", "DE", "DE"),
    ("DE-NW", "Germany — North Rhine-Westphalia",     "region", "EUR", "DE", "DE"),
    # Sweden regional
    ("SE-VG", "Sweden — Västra Götaland",             "region", "SEK", "SE", "SE"),
]

# ---------------------------------------------------------------------------
# Program data
# (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
#  is_transferable, annual_cap_local, req_cultural, req_local, authority_url, notes)
# ---------------------------------------------------------------------------
_PROGRAMS: list[tuple] = [
    # --- US states wave 3 ---
    ("US-GA", "us_ga_film_credit",
     "Georgia Entertainment Industry Investment Act",
     "transferable_tax_credit", 0.20, 0.30, False, True, None, False, False,
     "https://www.georgia.org/industries/film-entertainment/georgia-film",
     "20% transferable tax credit; 30% with Georgia logo embed. No annual cap."),
    ("US-LA", "us_la_film_incentive",
     "Louisiana Motion Picture Production Program",
     "transferable_tax_credit", 0.25, 0.40, False, True, None, False, False,
     "https://www.louisianaentertainment.gov/film",
     "25% base; up to 40% on LA resident labor. Transferable tax credit."),
    ("US-NM", "us_nm_film_credit",
     "New Mexico Film Production Tax Credit",
     "tax_credit", 0.25, 0.35, True, False, None, False, False,
     "https://nmfilm.com/incentives/",
     "25-35% refundable credit. Bonuses for NM residents and rural filming."),
    ("US-NY", "us_ny_film_credit",
     "New York State Film Tax Credit Program",
     "tax_credit", 0.25, 0.35, True, False, None, False, False,
     "https://esd.ny.gov/ny-film-incentive",
     "25% state + up to 10% NYC bonus = 35% max refundable. Annual queue."),
    ("US-NV", "us_nv_film_incentive",
     "Nevada Film Incentive Program",
     "transferable_tax_credit", 0.15, 0.47, False, True, 10_000_000, False, False,
     "https://nevadafilm.com/incentive/",
     "15% base; up to 47% with NV resident and rural bonuses. Cap ~$10M."),
    ("US-RI", "us_ri_film_credit",
     "Rhode Island Motion Picture Production Tax Credit",
     "transferable_tax_credit", 0.30, 0.30, False, True, None, False, False,
     "https://commerceri.com/film-tv/ri-tax-incentive/",
     "30% transferable tax credit on qualifying Rhode Island production expenditures."),
    # --- Caribbean & Central America ---
    ("BS", "bs_film_incentive",
     "Bahamas Film Commission Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://www.bahamasfilm.com/",
     "Production facilitation, customs duty concessions. No formal rebate confirmed. DISCOVERY."),
    ("BB", "bb_film_incentive",
     "Barbados Film and Entertainment Production Incentives",
     "production_support", None, None, None, None, None, False, False,
     "https://bidc.com/incentives/",
     "BIDC production facilitation. No formal rebate confirmed. DISCOVERY."),
    ("PA", "pa_film_incentive",
     "Panama Film Commission Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://www.panamafilmcommission.com/",
     "ATP facilitation; Canal Zone, jungle, island locations. DISCOVERY."),
    ("CR", "cr_film_incentive",
     "Costa Rica Film Commission Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://costaricafilm.com/",
     "CINDE/PROCOMER facilitation; biodiversity locations. DISCOVERY."),
    # --- South America ---
    ("PE", "pe_film_incentive",
     "Peru DAFO Film Production Support",
     "direct_grant", None, None, None, None, None, True, False,
     "https://dafo.cultura.pe/",
     "DAFO ministry grants; IBERMEDIA co-production eligible. DISCOVERY."),
    ("EC", "ec_film_incentive",
     "Ecuador Film Commission Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://www.ecuador.travel/filming-in-ecuador",
     "Galápagos, Amazon, Andes. No formal rebate confirmed. DISCOVERY."),
    # --- Africa ---
    ("EG", "eg_film_incentive",
     "Egypt Film Commission Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://egyptfilm.gov.eg/",
     "Media Production City; pyramid/desert locations. DISCOVERY."),
    ("GH", "gh_film_incentive",
     "Ghana National Film Authority Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://nfa.gov.gh/",
     "NFA facilitation; growing Ghanaian film industry. DISCOVERY."),
    ("RW", "rw_film_incentive",
     "Rwanda Development Board Film Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://rdb.rw/filming/",
     "RDB facilitation; gorilla habitat, Kigali, Lake Kivu. DISCOVERY."),
    ("TZ", "tz_film_incentive",
     "Tanzania Film Board Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://www.tanzaniafilmboard.go.tz/",
     "Serengeti, Kilimanjaro, Zanzibar. DISCOVERY."),
    ("SN", "sn_film_incentive",
     "Senegal Bureau d'Accueil des Tournages Film Support",
     "production_support", None, None, None, None, None, False, False,
     "https://www.senegalfilm.sn/",
     "Dakar, Sahara, Lac Rose film heritage. DISCOVERY."),
    # --- Gulf States ---
    ("KW", "kw_film_incentive",
     "Kuwait Film Committee Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://kuwaitfilmfund.com/",
     "Film Committee facilitation. No formal rebate confirmed. DISCOVERY."),
    ("BH", "bh_film_incentive",
     "Bahrain Film Commission Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://www.bahrainfilm.com/",
     "BFC facilitation; Manama, desert, Gulf coast. DISCOVERY."),
    # --- Central Asia / Caucasus ---
    ("GE", "ge_film_incentive",
     "Georgian National Film Centre Production Incentive",
     "cash_rebate", None, 0.25, None, None, None, False, False,
     "https://gnfc.ge/",
     "GNFC up to 25% reported; formal programme unverified. DISCOVERY."),
    ("KZ", "kz_film_incentive",
     "Kazakhfilm Studios Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://kazakhfilm.kz/",
     "Kazakhfilm Studios; steppe, mountains, Silk Road cities. DISCOVERY."),
    ("AM", "am_film_incentive",
     "National Cinema Centre of Armenia Production Support",
     "direct_grant", None, None, None, None, None, True, False,
     "https://www.film.am/",
     "NCCA grants; Yerevan, Lake Sevan, monasteries. DISCOVERY."),
    # --- Southeast Asia ---
    ("VN", "vn_film_incentive",
     "Vietnam Cinema Department Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://vfc.gov.vn/",
     "Kong, Crouching Tiger filmed here; no formal rebate confirmed. DISCOVERY."),
    ("ID", "id_film_incentive",
     "Indonesian Film Commission Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://filmcommission.or.id/",
     "Bali, Komodo, Java. IFC facilitation; no formal rebate. DISCOVERY."),
    ("KH", "kh_film_incentive",
     "Cambodia Ministry of Culture Film Production Facilitation",
     "production_support", None, None, None, None, None, False, False,
     "https://www.mcc.gov.kh/",
     "Angkor Wat, Khmer temples. Ministry facilitation. DISCOVERY."),
    # --- East Asia ---
    ("JP", "jp_film_incentive",
     "Japan Film Commission Location Incentive (JLOC)",
     "cash_rebate", None, 0.20, None, None, None, False, False,
     "https://www.japanfilmcommission.or.jp/",
     "Prefecture-level incentives up to ~20% via JFC/JLOC. National programme unconfirmed. DISCOVERY."),
    ("TW", "tw_film_incentive",
     "Taiwan Film and Audiovisual Institute (TFAI) Cash Rebate",
     "cash_rebate", 0.30, 0.30, True, False, None, False, False,
     "https://bamid.gov.tw/",
     "30% cash rebate on qualifying Taiwan spend via BAMID/TFAI."),
    ("HK", "hk_film_incentive",
     "Create Hong Kong (CreateHK) Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://www.createhk.gov.hk/",
     "CreateHK and HKFDC facilitation; no formal rebate percentage. DISCOVERY."),
    # --- Balkans / Additional Europe ---
    ("AL", "al_film_incentive",
     "Albanian National Cinema Agency (ANCA) Cash Rebate",
     "cash_rebate", 0.20, 0.20, True, False, None, False, False,
     "https://www.nationalcinema.al/",
     "Up to 20% on qualifying Albanian expenditures. DISCOVERY."),
    ("ME", "me_film_incentive",
     "Film Centre of Montenegro Production Incentive",
     "cash_rebate", 0.20, 0.25, True, False, None, False, False,
     "https://www.filmcentre.me/",
     "20-25% cash rebate on qualifying Montenegro expenditures. DISCOVERY."),
    ("MK", "mk_film_incentive",
     "Macedonian Film Agency (MFA) Cash Rebate",
     "cash_rebate", 0.20, 0.20, True, False, None, False, False,
     "https://mfa.gov.mk/",
     "~20% on qualifying North Macedonia expenditures. DISCOVERY."),
    ("BA", "ba_film_incentive",
     "Film Centre Bosnia and Herzegovina Production Support",
     "production_support", None, None, None, None, None, False, False,
     "https://www.filmcenter.ba/",
     "FCBH facilitation; Sarajevo, Mostar. No formal rebate. DISCOVERY."),
    # --- Pacific ---
    ("FJ", "fj_film_incentive",
     "Fiji Audio Visual Commission Production Incentive",
     "production_support", None, 0.47, None, None, None, False, False,
     "https://www.favc.com.fj/",
     "FAVC; duty exemptions and deductions up to ~47% on local spend. DISCOVERY."),
    # --- Grants / Funds ---
    ("IBERO", "ibermedia_programme",
     "IBERMEDIA Programme for Ibero-American Co-productions",
     "co_production_fund", None, None, False, False, 150_000, True, True,
     "https://programaibermedia.com/",
     "~16-member Ibero-American co-production fund since 1997. Up to EUR 150K per project."),
    ("DE-BY", "de_fff_bayern",
     "FilmFernsehFonds Bayern (FFF Bayern)",
     "direct_grant", None, None, False, False, None, True, False,
     "https://www.fff-bayern.de/",
     "Germany's largest regional fund (~EUR 52M/year). Bavaria spending required."),
    ("DE-NW", "de_nrw_filmstiftung",
     "Film und Medienstiftung NRW",
     "direct_grant", None, None, False, False, None, True, False,
     "https://www.filmstiftung.de/",
     "Major NRW regional fund (~EUR 40M/year). NRW spending required."),
    ("HK", "hk_film_dev_fund",
     "Hong Kong Film Development Fund (FDF)",
     "direct_grant", None, None, False, False, None, True, True,
     "https://www.fdc.gov.hk/",
     "HKD 400M+ fund supporting HK films and co-productions."),
    ("IN", "in_nfdc_coproduction",
     "NFDC International Co-production Development Fund",
     "co_production_fund", None, None, False, False, None, True, True,
     "https://www.nfdcindia.com/",
     "NFDC facilitates international co-productions via bilateral treaty network."),
    ("SG", "sg_imda_film_fund",
     "IMDA Singapore — Feature Film Production Grant",
     "direct_grant", None, None, False, False, None, True, True,
     "https://www.imda.gov.sg/",
     "IMDA feature film grants for Singapore-based productions."),
    ("TW", "tw_taicca_fund",
     "Taiwan Creative Content Agency (TAICCA) International Co-production Fund",
     "co_production_fund", None, None, False, False, None, True, True,
     "https://www.taicca.tw/",
     "TAICCA co-production grants separate from TFAI cash rebate."),
    ("SE-VG", "film_i_vast",
     "Film i Väst — Regional Co-production Fund",
     "co_production_fund", None, None, False, False, None, True, False,
     "https://www.filmivast.se/",
     "Europe's most active regional co-producer. Västra Götaland spending required."),
    ("ACP", "acpfilms_fund",
     "ACP Films — EU-ACP Cultural Film Co-production Fund",
     "co_production_fund", None, None, False, False, None, True, True,
     "https://www.acpfilms.eu/",
     "EU-ACP co-production fund for African, Caribbean and Pacific films."),
    ("US", "us_itvs_fund",
     "ITVS International Documentary Fund",
     "development_fund", None, None, False, False, None, False, False,
     "https://itvs.org/funding/",
     "ITVS development grants for international documentary films for public television."),
]

# ---------------------------------------------------------------------------
# Local cost benchmarks — new jurisdictions only (excludes IBERO, ACP)
# (code, crew, equip, stage, loc, post, vfx, catering, travel_usd, overrides)
# ---------------------------------------------------------------------------
_BENCHMARKS: list[tuple] = [
    # Caribbean & Central America
    ("BS",    0.58, 0.62, 0.60, 0.55, 0.55, 0.52, 0.55, 290.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 160.0, "per_diem_daily_usd": 68.0}),
    ("BB",    0.62, 0.65, 0.62, 0.58, 0.58, 0.55, 0.58, 295.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 165.0, "per_diem_daily_usd": 70.0}),
    ("PA",    0.42, 0.45, 0.42, 0.38, 0.45, 0.45, 0.40, 260.0,
     {"marine_vessel_multiplier": 0.42, "lodging_daily_usd": 115.0, "per_diem_daily_usd": 52.0}),
    ("CR",    0.40, 0.42, 0.40, 0.35, 0.42, 0.42, 0.38, 255.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 48.0}),
    # South America
    ("PE",    0.32, 0.35, 0.33, 0.28, 0.38, 0.40, 0.30, 250.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 90.0, "per_diem_daily_usd": 42.0}),
    ("EC",    0.30, 0.33, 0.30, 0.25, 0.35, 0.38, 0.28, 248.0,
     {"marine_vessel_multiplier": 0.32, "lodging_daily_usd": 85.0, "per_diem_daily_usd": 40.0}),
    # Africa
    ("EG",    0.25, 0.30, 0.28, 0.22, 0.32, 0.35, 0.25, 245.0,
     {"marine_vessel_multiplier": 0.28, "lodging_daily_usd": 75.0, "per_diem_daily_usd": 35.0}),
    ("GH",    0.22, 0.25, 0.25, 0.20, 0.28, 0.30, 0.22, 245.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 70.0, "per_diem_daily_usd": 32.0}),
    ("RW",    0.20, 0.22, 0.22, 0.18, 0.25, 0.28, 0.20, 240.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 65.0, "per_diem_daily_usd": 30.0}),
    ("TZ",    0.20, 0.22, 0.20, 0.18, 0.25, 0.28, 0.20, 240.0,
     {"marine_vessel_multiplier": 0.25, "lodging_daily_usd": 62.0, "per_diem_daily_usd": 30.0}),
    ("SN",    0.22, 0.25, 0.24, 0.20, 0.28, 0.30, 0.22, 242.0,
     {"marine_vessel_multiplier": 0.25, "lodging_daily_usd": 65.0, "per_diem_daily_usd": 32.0}),
    # Gulf States
    ("KW",    0.78, 0.75, 0.72, 0.75, 0.70, 0.68, 0.68, 390.0,
     {"marine_vessel_multiplier": 0.68, "lodging_daily_usd": 225.0, "per_diem_daily_usd": 90.0}),
    ("BH",    0.70, 0.68, 0.65, 0.68, 0.65, 0.62, 0.62, 370.0,
     {"marine_vessel_multiplier": 0.62, "lodging_daily_usd": 195.0, "per_diem_daily_usd": 82.0}),
    # Central Asia / Caucasus
    ("GE",    0.30, 0.35, 0.32, 0.28, 0.38, 0.40, 0.30, 250.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 85.0, "per_diem_daily_usd": 40.0}),
    ("KZ",    0.32, 0.35, 0.33, 0.28, 0.38, 0.40, 0.30, 255.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 90.0, "per_diem_daily_usd": 42.0}),
    ("AM",    0.28, 0.30, 0.28, 0.25, 0.35, 0.38, 0.28, 248.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 80.0, "per_diem_daily_usd": 38.0}),
    # Southeast Asia
    ("VN",    0.20, 0.25, 0.22, 0.18, 0.28, 0.30, 0.20, 250.0,
     {"marine_vessel_multiplier": 0.22, "lodging_daily_usd": 60.0, "per_diem_daily_usd": 28.0}),
    ("ID",    0.22, 0.28, 0.25, 0.20, 0.30, 0.32, 0.22, 255.0,
     {"marine_vessel_multiplier": 0.25, "lodging_daily_usd": 65.0, "per_diem_daily_usd": 30.0}),
    ("KH",    0.18, 0.22, 0.20, 0.16, 0.25, 0.28, 0.18, 240.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 55.0, "per_diem_daily_usd": 26.0}),
    # East Asia
    ("JP",    0.95, 0.92, 0.90, 0.95, 0.90, 0.88, 0.85, 460.0,
     {"marine_vessel_multiplier": 0.88, "lodging_daily_usd": 260.0, "per_diem_daily_usd": 105.0}),
    ("TW",    0.75, 0.72, 0.70, 0.72, 0.72, 0.70, 0.68, 370.0,
     {"marine_vessel_multiplier": 0.70, "lodging_daily_usd": 175.0, "per_diem_daily_usd": 78.0}),
    ("HK",    1.00, 0.98, 0.95, 1.00, 0.92, 0.90, 0.88, 470.0,
     {"marine_vessel_multiplier": 0.92, "lodging_daily_usd": 280.0, "per_diem_daily_usd": 110.0}),
    # Balkans / Additional Europe
    ("AL",    0.28, 0.32, 0.30, 0.26, 0.35, 0.38, 0.28, 250.0,
     {"marine_vessel_multiplier": 0.30, "lodging_daily_usd": 80.0, "per_diem_daily_usd": 38.0}),
    ("ME",    0.32, 0.36, 0.34, 0.30, 0.38, 0.40, 0.32, 255.0,
     {"marine_vessel_multiplier": 0.32, "lodging_daily_usd": 90.0, "per_diem_daily_usd": 42.0}),
    ("MK",    0.28, 0.32, 0.30, 0.26, 0.35, 0.38, 0.28, 248.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 78.0, "per_diem_daily_usd": 36.0}),
    ("BA",    0.30, 0.33, 0.30, 0.28, 0.36, 0.40, 0.30, 250.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 80.0, "per_diem_daily_usd": 38.0}),
    # Pacific
    ("FJ",    0.62, 0.65, 0.62, 0.58, 0.60, 0.58, 0.58, 310.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 165.0, "per_diem_daily_usd": 70.0}),
    # US sub-nationals — wave 3
    ("US-GA", 0.90, 0.88, 0.85, 0.88, 0.88, 0.85, 0.82, 425.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 185.0, "per_diem_daily_usd": 85.0}),
    ("US-LA", 0.85, 0.83, 0.80, 0.82, 0.85, 0.82, 0.78, 400.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 78.0}),
    ("US-NM", 0.75, 0.73, 0.70, 0.72, 0.75, 0.72, 0.68, 380.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 155.0, "per_diem_daily_usd": 72.0}),
    ("US-NY", 1.05, 1.02, 1.00, 1.05, 1.00, 0.98, 0.95, 480.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 280.0, "per_diem_daily_usd": 110.0}),
    ("US-NV", 0.85, 0.83, 0.80, 0.82, 0.82, 0.80, 0.78, 400.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 175.0, "per_diem_daily_usd": 80.0}),
    ("US-RI", 0.92, 0.90, 0.88, 0.90, 0.88, 0.85, 0.82, 420.0,
     {"marine_vessel_multiplier": 0.85, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 88.0}),
    # Germany regional
    ("DE-BY", 0.88, 0.85, 0.82, 0.82, 0.85, 0.82, 0.78, 400.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 210.0, "per_diem_daily_usd": 90.0}),
    ("DE-NW", 0.85, 0.82, 0.80, 0.80, 0.82, 0.80, 0.76, 390.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 86.0}),
    # Sweden regional
    ("SE-VG", 0.90, 0.88, 0.85, 0.85, 0.88, 0.85, 0.82, 420.0,
     {"marine_vessel_multiplier": 0.85, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 96.0}),
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Insert country-level / supranational jurisdictions
    for code, name, level, currency, country_code, _ in _COUNTRIES:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (id, parent_id, name, code, iso_code, level,
                    currency_code, country_code, is_active, created_at, updated_at)
                SELECT :id, NULL, :name, :code, :iso_code, :level,
                    :currency, :country_code, true, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code ::varchar
                )
            """),
            {
                "id": _uid(f"jur:{code}"), "name": name, "code": code, "iso_code": code,
                "level": level, "currency": currency, "country_code": country_code, "now": NOW,
            },
        )

    # 2. Insert sub-national jurisdictions
    for code, name, level, currency, country_code, parent_code in _SUB_NATIONALS:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (id, parent_id, name, code, iso_code, level,
                    currency_code, country_code, is_active, created_at, updated_at)
                SELECT :id,
                    (SELECT id FROM jurisdictions WHERE code = :parent_code LIMIT 1),
                    :name, :code, :iso_code, :level, :currency, :country_code, true, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code ::varchar
                )
            """),
            {
                "id": _uid(f"jur:{code}"), "name": name, "code": code, "iso_code": code,
                "level": level, "currency": currency, "country_code": country_code,
                "parent_code": parent_code, "now": NOW,
            },
        )

    # 3. Insert incentive programs
    for (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
         is_transferable, annual_cap_local, req_cultural, req_local, authority_url, notes) in _PROGRAMS:
        conn.execute(
            sa.text("""
                INSERT INTO incentive_programs (
                    id, jurisdiction_id, source_document_id, name, slug, program_type,
                    credit_basis, base_rate, max_rate, is_refundable, is_transferable,
                    transferable_value_pct, is_competitive, annual_cap_local,
                    fixed_grant_amount_usd, requires_cultural_test, cultural_test_id,
                    requires_local_entity, confidence_tier, review_status,
                    authority_url, notes, created_at, updated_at
                )
                SELECT
                    :id,
                    (SELECT id FROM jurisdictions WHERE code = :jur_code LIMIT 1),
                    NULL, :name, :slug, :prog_type, 'qualifying_spend',
                    :base_rate, :max_rate, :is_refundable, :is_transferable,
                    NULL, false, :annual_cap_local, NULL,
                    :req_cultural, NULL, :req_local,
                    'DISCOVERY', 'pending', :authority_url, :notes, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM incentive_programs WHERE slug = :slug ::varchar
                )
            """),
            {
                "id": _uid(f"prog:{slug}"),
                "jur_code": jur_code, "name": name, "slug": slug,
                "prog_type": prog_type,
                "base_rate": base_rate, "max_rate": max_rate,
                "is_refundable": is_refundable, "is_transferable": is_transferable,
                "annual_cap_local": annual_cap_local,
                "req_cultural": req_cultural, "req_local": req_local,
                "authority_url": authority_url, "notes": notes, "now": NOW,
            },
        )

    # 4. Insert local_cost_benchmarks (new jurisdictions only)
    for (code, crew, equip, stage, loc, post, vfx, catering, travel, overrides) in _BENCHMARKS:
        conn.execute(
            sa.text("""
                INSERT INTO local_cost_benchmarks (
                    id, jurisdiction_id,
                    crew_rate_multiplier, equipment_rental_multiplier,
                    stage_facility_multiplier, location_fees_multiplier,
                    post_production_multiplier, vfx_multiplier, catering_multiplier,
                    key_crew_daily_travel_usd, category_overrides_json,
                    data_source, as_of_date, confidence_tier, notes, created_at, updated_at
                )
                SELECT
                    gen_random_uuid(),
                    j.id,
                    :crew, :equip, :stage, :loc, :post, :vfx, :catering,
                    :travel, CAST(:overrides AS jsonb),
                    :source, :as_of, 'DISCOVERY',
                    :notes, :now, :now
                FROM jurisdictions j
                WHERE j.code = :code
                  AND NOT EXISTS (
                      SELECT 1 FROM local_cost_benchmarks lcb
                      WHERE lcb.jurisdiction_id = j.id
                  )
                LIMIT 1
            """),
            {
                "code": code, "crew": crew, "equip": equip, "stage": stage,
                "loc": loc, "post": post, "vfx": vfx, "catering": catering,
                "travel": travel, "overrides": json.dumps(overrides),
                "source": _BM_SOURCE, "as_of": _BM_DATE,
                "notes": f"LA-relative cost multipliers for {code}. DISCOVERY tier.",
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for (_, slug, *_rest) in _PROGRAMS:
        conn.execute(
            sa.text("DELETE FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug},
        )
