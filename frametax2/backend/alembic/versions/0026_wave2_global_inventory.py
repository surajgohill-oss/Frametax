"""0026 — Wave-2 global inventory: 47 new programs across 37 jurisdictions.

Seeds jurisdictions, incentive programs, and cost benchmarks for:

  US states/territories (6): HI, UT, MN, MS, AZ, PR
  CA provinces (2):          SK, NL
  Europe (12):               SE, NO, FI, DK, PL, BG, EE, LT, LV, SK(Slovakia), LU, TR
  Asia-Pacific (6):          TH, MY, PH, KR, IN, LK
  Latin America/Caribbean(4):MX, CL, JM, TT
  Middle East/Africa (5):    IL, QA, TN(Tunisia), KE, NG
  Special (2):               EU, NORDIC

  + 12 grant/fund programs for existing jurisdictions:
    CA (CMF, Telefilm), GB (BFI), FR (CNC), AU (Screen Australia),
    NL (Hubert Bals Fund), QA (DFI), US (Sundance), ZA (DAC/NFVF),
    EU (Eurimages, MEDIA), NORDIC (Nordisk Film & TV Fond)

All entries are DISCOVERY tier.

Revision ID: 0026
Revises: 0025
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: Union[str, None] = "0025"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0026-0000-0001-000000000000")
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
    # Europe
    ("SE",     "Sweden",              "country", "SEK", "SE", None),
    ("NO",     "Norway",              "country", "NOK", "NO", None),
    ("FI",     "Finland",             "country", "EUR", "FI", None),
    ("DK",     "Denmark",             "country", "DKK", "DK", None),
    ("PL",     "Poland",              "country", "PLN", "PL", None),
    ("BG",     "Bulgaria",            "country", "BGN", "BG", None),
    ("EE",     "Estonia",             "country", "EUR", "EE", None),
    ("LT",     "Lithuania",           "country", "EUR", "LT", None),
    ("LV",     "Latvia",              "country", "EUR", "LV", None),
    ("SK",     "Slovakia",            "country", "EUR", "SK", None),
    ("LU",     "Luxembourg",          "country", "EUR", "LU", None),
    ("TR",     "Turkey",              "country", "TRY", "TR", None),
    # Asia-Pacific
    ("TH",     "Thailand",            "country", "THB", "TH", None),
    ("MY",     "Malaysia",            "country", "MYR", "MY", None),
    ("PH",     "Philippines",         "country", "PHP", "PH", None),
    ("KR",     "South Korea",         "country", "KRW", "KR", None),
    ("IN",     "India",               "country", "INR", "IN", None),
    ("LK",     "Sri Lanka",           "country", "LKR", "LK", None),
    # Latin America & Caribbean
    ("MX",     "Mexico",              "country", "MXN", "MX", None),
    ("CL",     "Chile",               "country", "CLP", "CL", None),
    ("JM",     "Jamaica",             "country", "JMD", "JM", None),
    ("TT",     "Trinidad & Tobago",   "country", "TTD", "TT", None),
    # Middle East & Africa
    ("IL",     "Israel",              "country", "ILS", "IL", None),
    ("QA",     "Qatar",               "country", "QAR", "QA", None),
    ("TN",     "Tunisia",             "country", "TND", "TN", None),
    ("KE",     "Kenya",               "country", "KES", "KE", None),
    ("NG",     "Nigeria",             "country", "NGN", "NG", None),
    # Special / multi-national
    ("EU",     "European Union",      "supranational", "EUR", "EU", None),
    ("NORDIC", "Nordic Region",       "supranational", "EUR", "NORDIC", None),
]

_SUB_NATIONALS: list[tuple] = [
    # US states / territories
    ("US-HI", "United States — Hawaii",           "state",     "USD", "US", "US"),
    ("US-UT", "United States — Utah",             "state",     "USD", "US", "US"),
    ("US-MN", "United States — Minnesota",        "state",     "USD", "US", "US"),
    ("US-MS", "United States — Mississippi",      "state",     "USD", "US", "US"),
    ("US-AZ", "United States — Arizona",          "state",     "USD", "US", "US"),
    ("US-PR", "United States — Puerto Rico",      "territory", "USD", "US", "US"),
    # Canadian provinces
    ("CA-SK", "Canada — Saskatchewan",            "province",  "CAD", "CA", "CA"),
    ("CA-NL", "Canada — Newfoundland & Labrador", "province",  "CAD", "CA", "CA"),
]

# ---------------------------------------------------------------------------
# Program data
# (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
#  is_transferable, annual_cap_local, req_cultural, req_local, authority_url, notes)
# ---------------------------------------------------------------------------
_PROGRAMS: list[tuple] = [
    # --- US states/territories ---
    ("US-HI", "us_hi_film_tax_credit", "Hawaii Film and Digital Media Income Tax Credit",
     "tax_credit", 0.20, 0.20, True, False, None, False, False,
     "https://filmoffice.hawaii.gov/incentives-tax-credits/",
     "20% refundable credit on Hawaii qualifying production costs."),
    ("US-UT", "us_ut_film_incentive", "Utah Motion Picture Incentive Program",
     "cash_rebate", 0.20, 0.25, True, False, 8_100_000, False, False,
     "https://film.utah.gov/",
     "20% base cash rebate; 25% with UT cast/crew bonus. Annual fund ~$8.1M."),
    ("US-MN", "us_mn_film_credit", "Minnesota Film Production Tax Credit",
     "tax_credit", 0.25, 0.25, True, False, 25_000_000, False, False,
     "https://www.revenue.state.mn.us/film-production-credit",
     "25% refundable credit on Minnesota qualifying expenditures. Cap ~$25M."),
    ("US-MS", "us_ms_film_credit", "Mississippi Advantage Film Program",
     "tax_credit", 0.25, 0.35, True, False, None, False, False,
     "https://filmmississippi.org/incentive/",
     "25% base; up to 35% with MS resident crew bonus. No annual cap."),
    ("US-AZ", "us_az_film_credit", "Arizona Motion Picture Production Program",
     "cash_rebate", 0.15, 0.20, True, False, 75_000_000, False, False,
     "https://www.azcommerce.com/film-media/incentive/",
     "15-20% cash rebate on AZ qualifying spend. Annual cap ~$75M."),
    ("US-PR", "us_pr_film_incentive", "Puerto Rico Film Industry Economic Incentives Act",
     "tax_credit", 0.40, 0.40, True, True, None, False, False,
     "https://puertoricofilm.ddec.pr.gov/",
     "40% refundable/transferable credit under Act 421-2012 / Act 60."),
    # --- Canadian provinces ---
    ("CA-SK", "ca_sk_production_grant", "Creative Saskatchewan Film and TV Production Grant",
     "direct_grant", None, 0.40, None, False, None, True, False,
     "https://www.creativesask.ca/funding/",
     "Discretionary production grants; SFETC repealed 2012. Up to ~40% on SK spend. DISCOVERY."),
    ("CA-NL", "ca_nl_production_fund", "Newfoundland & Labrador Film Development Corp Production Incentive",
     "tax_credit", 0.40, 0.45, True, False, None, True, False,
     "https://picturenl.ca/",
     "40-45% on eligible NL labour. Combines with federal CPTC."),
    # --- Europe ---
    ("SE", "se_film_incentive", "Sweden Film Commission Production Rebate",
     "cash_rebate", 0.25, 0.25, True, False, None, True, False,
     "https://www.filminstitutet.se/en/",
     "25% cash rebate on qualifying Swedish expenditures. Cultural test."),
    ("NO", "no_film_incentive", "Norwegian Film Commission Production Incentive",
     "cash_rebate", 0.25, 0.25, True, False, None, True, False,
     "https://www.norwegianfilm.com/25-incentive",
     "25% cash rebate on Norwegian qualifying expenditures."),
    ("FI", "fi_film_incentive", "Business Finland Film Incentive",
     "cash_rebate", 0.25, 0.25, True, False, None, True, False,
     "https://www.businessfinland.fi/en/for-finnish-customers/services/funding/cash-rebate",
     "25% cash rebate on Finnish qualifying expenditures."),
    ("DK", "dk_film_incentive", "Danish Film Institute Production Support",
     "direct_grant", None, 0.25, None, False, None, True, False,
     "https://www.dfi.dk/en/english/funding",
     "Danish Film Institute grants and market scheme. Cultural test required."),
    ("PL", "pl_film_incentive", "Polish Film Institute (PISF) Cash Rebate",
     "cash_rebate", 0.30, 0.30, True, False, None, True, False,
     "https://polishfilmcommission.pl/incentives/30-cash-rebate-basics/",
     "30% cash rebate on qualifying Polish expenditures for foreign co-productions."),
    ("BG", "bg_film_incentive", "Bulgarian Film Commission Cash Rebate",
     "cash_rebate", 0.25, 0.25, True, False, None, False, False,
     "https://www.nfc.gov.bg",
     "25% cash rebate on Bulgarian qualifying spend. Low cost EU base."),
    ("EE", "ee_film_incentive", "Film Estonia Cash Rebate",
     "cash_rebate", 0.30, 0.30, True, False, None, False, False,
     "https://filmestonia.eu/",
     "30% cash rebate on qualifying Estonian expenditures."),
    ("LT", "lt_film_incentive", "Lithuanian Film Centre Production Cash Rebate",
     "cash_rebate", 0.30, 0.30, True, False, None, False, False,
     "https://www.lkc.lt/en/tax-incentives",
     "30% cash rebate on qualifying Lithuanian expenditures."),
    ("LV", "lv_film_incentive", "National Film Centre of Latvia Production Incentive",
     "cash_rebate", 0.20, 0.25, True, False, None, False, False,
     "https://www.nkc.gov.lv/en",
     "20-25% cash rebate on qualifying Latvian expenditures."),
    ("SK", "sk_film_incentive", "Slovak Audiovisual Fund (AVF) Production Incentive",
     "cash_rebate", 0.33, 0.33, True, False, None, False, False,
     "https://www.avf.sk/english.aspx",
     "33% cash rebate on qualifying Slovak expenditures."),
    ("LU", "lu_film_incentive", "Film Fund Luxembourg — Tax Shelter & Production Rebate",
     "tax_credit", 0.30, 0.40, True, False, None, True, True,
     "https://filmfund.lu/en/",
     "Up to 40% on Luxembourg qualifying spend. Tax shelter + rebate framework."),
    ("TR", "tr_film_incentive", "Turkey Cinema General Directorate Production Support",
     "cash_rebate", None, 0.25, None, False, None, True, False,
     "https://www.sinema.gov.tr/en",
     "Turkish Cinema General Directorate co-production and production support. DISCOVERY."),
    # --- Asia-Pacific ---
    ("TH", "th_film_incentive", "Thailand BOI Film Production Incentive",
     "cash_rebate", 0.15, 0.20, True, False, None, False, False,
     "https://tfo.dot.go.th/incentive-measures/",
     "15-20% cash rebate on Thai qualifying expenditures via BOI."),
    ("MY", "my_film_incentive", "FINAS Malaysia Film Rebate",
     "cash_rebate", 0.30, 0.30, True, False, None, False, False,
     "https://filminmalaysia.com/",
     "30% cash rebate on qualifying Malaysian spend administered by FINAS."),
    ("PH", "ph_film_incentive", "Film Development Council of the Philippines (FDCP) Incentive",
     "cash_rebate", 0.20, 0.20, True, False, None, False, False,
     "https://fdcp.ph/",
     "Up to 20% cash rebate on qualifying Philippine expenditures."),
    ("KR", "kr_film_incentive", "Korea Film Council (KOFIC) Location Incentive",
     "cash_rebate", None, 0.25, None, False, None, False, False,
     "https://www.koreanfilm.or.kr/eng/",
     "KOFIC location incentive for foreign productions. Rate unconfirmed. DISCOVERY."),
    ("IN", "in_national_film", "India NFDC and State Incentives",
     "direct_grant", None, 0.30, None, False, None, True, False,
     "https://www.nfdcindia.com/",
     "Multiple state film incentives (MP 25%, RJ 20%, UP 25%). NFDC facilitates co-productions."),
    ("LK", "lk_film_incentive", "Sri Lanka Film Commission Production Incentive",
     "cash_rebate", None, 0.25, None, False, None, False, False,
     "https://srilankafilmcommission.lk/incentives/",
     "Sri Lanka production incentives; confirmed rate unverified. DISCOVERY."),
    # --- Latin America & Caribbean ---
    ("MX", "mx_eficine_incentive", "Mexico EFICINE (Article 226) and PROCINE Fund",
     "tax_credit", 0.10, 0.175, False, False, None, True, True,
     "https://www.imcine.gob.mx/",
     "EFICINE Art. 226: 10% tax credit for investors. PROCINE adds up to 17.5%."),
    ("CL", "cl_corfo_incentive", "Chile Corfo Film Incentive",
     "cash_rebate", 0.20, 0.30, True, False, None, False, False,
     "https://www.corfo.cl/",
     "20-30% cash rebate on qualifying Chilean expenditures via Corfo."),
    ("JM", "jm_film_incentive", "Jamaica Entertainment Industry Incentive Programme",
     "tax_credit", 0.40, 0.50, True, False, None, False, False,
     "https://www.filmjamaica.com/",
     "Up to 50% combined tax incentives on qualifying Jamaica expenditures."),
    ("TT", "tt_film_incentive", "Trinidad & Tobago Creative Industries Production Incentive",
     "tax_credit", 0.35, 0.35, None, False, None, False, False,
     "https://filmtt.co.tt/",
     "~35% allowance on qualifying T&T expenditures under Creative Industries legislation."),
    # --- Middle East & Africa ---
    ("IL", "il_film_incentive", "Israel Film Fund / Maslool Incentive",
     "cash_rebate", None, 0.30, None, False, None, False, False,
     "https://israel-trade.net/filmisrael/",
     "Israel Film Fund co-production and production support up to ~30%. DISCOVERY."),
    ("QA", "qa_film_incentive", "Qatar Film Commission Production Incentive",
     "cash_rebate", 0.25, 0.35, True, False, None, False, False,
     "https://www.dohafilm.com/",
     "20-35% in production incentives on Qatar qualifying spend."),
    ("TN", "tn_film_incentive", "Tunisia CNCI Cash Rebate",
     "cash_rebate", 0.25, 0.30, True, False, None, False, False,
     "https://cnci.tn/",
     "25-30% cash rebate on qualifying Tunisian expenditures. Sahara/Medina locations."),
    ("KE", "ke_film_incentive", "Kenya Film Commission (KFC) Production Incentive",
     "cash_rebate", None, 0.20, None, False, None, False, False,
     "https://kenyafilmcommission.go.ke/",
     "Kenya Film Commission rebates and support for qualifying productions. DISCOVERY."),
    ("NG", "ng_film_incentive", "Nigeria NFC / Creative Economy Incentive",
     "direct_grant", None, None, None, False, None, False, False,
     "https://www.nfvcb.gov.ng/",
     "Nigeria formal international rebate unconfirmed. Policy framework exists. DISCOVERY."),
    # --- Grants / Funds (existing jurisdictions) ---
    ("EU",     "eu_eurimages", "Eurimages — Council of Europe Co-production Fund",
     "co_production_fund", None, None, False, False, 1_500_000, True, True,
     "https://www.coe.int/en/web/eurimages",
     "Council of Europe co-production fund. Up to EUR 1.5M. 44 member states. Repayable."),
    ("EU",     "eu_media_fund", "Creative Europe MEDIA Programme",
     "co_production_fund", None, None, False, False, 2_500_000, True, True,
     "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/crea",
     "EU MEDIA programme for European audiovisual. Up to EUR 2.5M. Budget 2021-27: EUR 1.07B."),
    ("NORDIC", "nordic_ftvf", "Nordisk Film & TV Fond",
     "co_production_fund", None, None, False, False, 1_400_000, True, True,
     "https://nordiskfilmogtvfond.com/",
     "Nordic co-production fund for DK/FI/IS/NO/SE. Up to SEK 8-15M per project."),
    ("CA",     "ca_cmf", "Canada Media Fund (CMF) — Convergent Stream",
     "direct_grant", None, None, False, False, 10_000_000, True, True,
     "https://cmf-fmc.ca/",
     "CAD$400M+ annually. Per-project up to CAD$10M for major drama. Performance-based."),
    ("CA",     "ca_telefilm_dev", "Telefilm Canada — Canada Feature Film Fund (CFFF)",
     "direct_grant", None, None, False, False, 5_000_000, True, True,
     "https://telefilm.ca/",
     "Equity investment/advances for Canadian feature films. Up to CAD$5M. Repayable."),
    ("GB",     "gb_bfi_production", "BFI Film Fund — Production Funding",
     "direct_grant", None, None, False, False, 2_000_000, True, True,
     "https://www.bfi.org.uk/get-funding-support",
     "Up to GBP 1.5M per project. Lottery-funded. British cultural content required."),
    ("FR",     "fr_cnc_production", "CNC France — Avances sur Recettes (Cinema Production Aid)",
     "direct_grant", None, None, False, False, 1_500_000, True, True,
     "https://www.cnc.fr/web/en",
     "CNC production grants up to ~EUR 1.2M. Repayable advance. French content required."),
    ("AU",     "au_screen_production", "Screen Australia — Production Funding",
     "direct_grant", None, None, False, False, 3_000_000, True, True,
     "https://www.screenaustralia.gov.au/funding-and-support",
     "Equity investment in Australian film. Up to AUD $3M+. Australian content required."),
    ("NL",     "nl_hbf", "Hubert Bals Fund (IFFR) — Development and Production Fund",
     "development_fund", None, None, False, False, 150_000, True, False,
     "https://iffr.com/en/hubert-bals-fund",
     "Up to EUR 50-100K for Global South filmmakers. Based at IFFR Rotterdam."),
    ("QA",     "qa_dfi_fund", "Doha Film Institute — Grants for Filmmakers",
     "development_fund", None, None, False, False, 300_000, True, False,
     "https://www.dohafilm.com/",
     "Up to QAR 1.5M (~USD $400K) per project. Two annual cycles. Arab/international focus."),
    ("US",     "us_sundance_doc", "Sundance Institute — Documentary Fund",
     "development_fund", None, None, False, False, 300_000, False, False,
     "https://www.sundance.org/documentary-fund/",
     "Grants up to USD $250-300K for feature documentaries. Development and production."),
    ("ZA",     "za_dac_fund", "NFVF South Africa — Development and Production Fund",
     "development_fund", None, None, False, False, 250_000, True, True,
     "https://www.nfvf.co.za/funding/",
     "NFVF grants up to ZAR 3-4M (~USD $200-250K). Stacks with NFVF Foreign Film rebate."),
]

# ---------------------------------------------------------------------------
# Cost benchmarks — new country-level jurisdictions only
# (code, crew, equip, stage, loc, post, vfx, catering, travel_usd, overrides)
# LA = 1.0 baseline. Values are LA-relative multipliers.
# ---------------------------------------------------------------------------
_BENCHMARKS: list[tuple] = [
    # Europe — high-cost
    ("SE",  0.90, 0.85, 0.82, 0.85, 0.88, 0.85, 0.80, 420.0,
     {"marine_vessel_multiplier": 0.82, "lodging_daily_usd": 250.0, "per_diem_daily_usd": 105.0}),
    ("NO",  0.95, 0.90, 0.88, 0.88, 0.90, 0.88, 0.82, 440.0,
     {"marine_vessel_multiplier": 0.88, "lodging_daily_usd": 270.0, "per_diem_daily_usd": 115.0}),
    ("FI",  0.85, 0.82, 0.80, 0.80, 0.85, 0.82, 0.78, 400.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 235.0, "per_diem_daily_usd": 100.0}),
    ("DK",  0.92, 0.88, 0.85, 0.85, 0.88, 0.85, 0.80, 425.0,
     {"marine_vessel_multiplier": 0.85, "lodging_daily_usd": 260.0, "per_diem_daily_usd": 108.0}),
    ("PL",  0.45, 0.48, 0.45, 0.40, 0.52, 0.55, 0.42, 290.0,
     {"marine_vessel_multiplier": 0.42, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 58.0}),
    ("BG",  0.28, 0.32, 0.30, 0.25, 0.38, 0.42, 0.28, 270.0,
     {"marine_vessel_multiplier": 0.30, "lodging_daily_usd": 80.0, "per_diem_daily_usd": 40.0}),
    ("EE",  0.38, 0.42, 0.40, 0.35, 0.45, 0.48, 0.38, 280.0,
     {"marine_vessel_multiplier": 0.38, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 52.0}),
    ("LT",  0.35, 0.40, 0.38, 0.32, 0.42, 0.45, 0.35, 275.0,
     {"marine_vessel_multiplier": 0.36, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 50.0}),
    ("LV",  0.35, 0.40, 0.38, 0.32, 0.42, 0.45, 0.35, 272.0,
     {"marine_vessel_multiplier": 0.36, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 50.0}),
    ("SK",  0.32, 0.36, 0.34, 0.30, 0.40, 0.44, 0.32, 270.0,
     {"marine_vessel_multiplier": 0.32, "lodging_daily_usd": 95.0, "per_diem_daily_usd": 48.0}),
    ("LU",  0.88, 0.85, 0.82, 0.80, 0.85, 0.82, 0.78, 400.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 250.0, "per_diem_daily_usd": 100.0}),
    ("TR",  0.35, 0.40, 0.38, 0.35, 0.42, 0.45, 0.35, 270.0,
     {"marine_vessel_multiplier": 0.36, "lodging_daily_usd": 100.0, "per_diem_daily_usd": 48.0}),
    # Asia-Pacific — low-cost
    ("TH",  0.25, 0.30, 0.28, 0.25, 0.35, 0.38, 0.28, 300.0,
     {"marine_vessel_multiplier": 0.28, "lodging_daily_usd": 80.0, "per_diem_daily_usd": 38.0}),
    ("MY",  0.28, 0.32, 0.30, 0.28, 0.38, 0.40, 0.30, 310.0,
     {"marine_vessel_multiplier": 0.30, "lodging_daily_usd": 90.0, "per_diem_daily_usd": 42.0}),
    ("PH",  0.22, 0.28, 0.25, 0.22, 0.32, 0.35, 0.25, 290.0,
     {"marine_vessel_multiplier": 0.28, "lodging_daily_usd": 70.0, "per_diem_daily_usd": 35.0}),
    ("KR",  0.60, 0.58, 0.55, 0.58, 0.60, 0.58, 0.55, 370.0,
     {"marine_vessel_multiplier": 0.55, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 75.0}),
    ("IN",  0.20, 0.25, 0.22, 0.18, 0.28, 0.32, 0.20, 280.0,
     {"marine_vessel_multiplier": 0.22, "lodging_daily_usd": 60.0, "per_diem_daily_usd": 30.0}),
    ("LK",  0.18, 0.22, 0.20, 0.18, 0.25, 0.28, 0.20, 285.0,
     {"marine_vessel_multiplier": 0.22, "lodging_daily_usd": 55.0, "per_diem_daily_usd": 28.0}),
    # Latin America & Caribbean
    ("MX",  0.38, 0.42, 0.40, 0.35, 0.45, 0.48, 0.35, 265.0,
     {"marine_vessel_multiplier": 0.38, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 52.0}),
    ("CL",  0.42, 0.45, 0.42, 0.38, 0.48, 0.50, 0.40, 270.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 56.0}),
    ("JM",  0.35, 0.40, 0.42, 0.32, 0.40, 0.42, 0.35, 260.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 50.0}),
    ("TT",  0.38, 0.42, 0.42, 0.35, 0.42, 0.44, 0.36, 260.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 108.0, "per_diem_daily_usd": 52.0}),
    # Middle East & Africa
    ("IL",  0.72, 0.70, 0.68, 0.70, 0.70, 0.68, 0.65, 380.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 85.0}),
    ("QA",  0.75, 0.72, 0.70, 0.72, 0.68, 0.65, 0.65, 400.0,
     {"marine_vessel_multiplier": 0.68, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 95.0}),
    ("TN",  0.22, 0.28, 0.30, 0.20, 0.32, 0.35, 0.22, 240.0,
     {"marine_vessel_multiplier": 0.28, "lodging_daily_usd": 65.0, "per_diem_daily_usd": 32.0}),
    ("KE",  0.20, 0.25, 0.28, 0.22, 0.30, 0.32, 0.22, 255.0,
     {"marine_vessel_multiplier": 0.25, "lodging_daily_usd": 70.0, "per_diem_daily_usd": 34.0}),
    ("NG",  0.22, 0.28, 0.28, 0.20, 0.30, 0.32, 0.22, 250.0,
     {"marine_vessel_multiplier": 0.24, "lodging_daily_usd": 70.0, "per_diem_daily_usd": 35.0}),
    # US sub-nationals (USD, similar to US base)
    ("US-HI", 1.10, 1.05, 1.00, 1.10, 1.00, 0.95, 1.00, 540.0,
     {"marine_vessel_multiplier": 1.05, "lodging_daily_usd": 320.0, "per_diem_daily_usd": 120.0}),
    ("US-UT", 0.80, 0.78, 0.75, 0.78, 0.80, 0.78, 0.75, 390.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 175.0, "per_diem_daily_usd": 80.0}),
    ("US-MN", 0.82, 0.80, 0.78, 0.80, 0.82, 0.80, 0.78, 380.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 180.0, "per_diem_daily_usd": 82.0}),
    ("US-MS", 0.65, 0.65, 0.62, 0.62, 0.70, 0.70, 0.65, 350.0,
     {"marine_vessel_multiplier": 0.62, "lodging_daily_usd": 130.0, "per_diem_daily_usd": 62.0}),
    ("US-AZ", 0.80, 0.78, 0.75, 0.80, 0.80, 0.78, 0.75, 380.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 175.0, "per_diem_daily_usd": 80.0}),
    ("US-PR", 0.70, 0.68, 0.65, 0.70, 0.72, 0.68, 0.65, 360.0,
     {"marine_vessel_multiplier": 0.68, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 75.0}),
    # Canadian provinces (CAD-based)
    ("CA-SK", 0.52, 0.55, 0.50, 0.48, 0.55, 0.55, 0.50, 340.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 140.0, "per_diem_daily_usd": 68.0}),
    ("CA-NL", 0.55, 0.55, 0.50, 0.48, 0.55, 0.55, 0.50, 355.0,
     {"marine_vessel_multiplier": 0.52, "lodging_daily_usd": 148.0, "per_diem_daily_usd": 70.0}),
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

    # Remove programs
    for (_, slug, *_rest) in _PROGRAMS:
        conn.execute(
            sa.text("DELETE FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug},
        )

    # Remove benchmarks for new jurisdictions
    for code, *_ in _BENCHMARKS:
        conn.execute(
            sa.text("""
                DELETE FROM local_cost_benchmarks
                WHERE jurisdiction_id = (
                    SELECT id FROM jurisdictions WHERE code = :code LIMIT 1
                )
                AND created_at >= :since
            """),
            {"code": code, "since": NOW},
        )
