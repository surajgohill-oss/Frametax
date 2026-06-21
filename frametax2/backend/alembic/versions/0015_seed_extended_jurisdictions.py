"""0015 — Seed extended global jurisdiction inventory (~43 entries).

Adds jurisdictions, incentive programs, and local_cost_benchmarks for
all jurisdictions added in global_inventory_extended.py:

  US States (16): OR*, WA, IL, NC, SC, MA, TX, CT, PA, MD, VA, CO, TN, OK, AL, KY
  CA Provinces (4): AB, MB, NS, NB
  Europe (9): NL, AT, CZ, RO, PT, RS, IS, GB-SCT, GB-WLS
  Asia-Pacific (4): SG, AU-NSW, AU-VIC, AU-QLD
  Latin America (5): CO, DO, UY, AR, BR
  Middle East (3): AE, SA, JO
  Africa (2): MA, ZA

  * US-OR already seeded in 0004; all inserts use WHERE NOT EXISTS guards.

All entries are DISCOVERY tier.

Revision ID: 0015
Revises: 0014
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

_NS = uuid.UUID("a1000000-0015-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_DISC = "DISCOVERY"
_BM_SOURCE = (
    "Production market knowledge — not verified from primary labour cost surveys. "
    "Confidence tier: DISCOVERY."
)
_BM_DATE = "2025-06"

# ---------------------------------------------------------------------------
# Jurisdiction data
# (code, name, level, currency_code, country_code, parent_code or None)
# ---------------------------------------------------------------------------
_COUNTRIES = [
    ("NL", "Netherlands",        "country", "EUR", "NL", None),
    ("AT", "Austria",            "country", "EUR", "AT", None),
    ("CZ", "Czech Republic",     "country", "CZK", "CZ", None),
    ("RO", "Romania",            "country", "RON", "RO", None),
    ("PT", "Portugal",           "country", "EUR", "PT", None),
    ("RS", "Serbia",             "country", "RSD", "RS", None),
    ("IS", "Iceland",            "country", "ISK", "IS", None),
    ("SG", "Singapore",          "country", "SGD", "SG", None),
    ("CO", "Colombia",           "country", "COP", "CO", None),
    ("DO", "Dominican Republic", "country", "DOP", "DO", None),
    ("UY", "Uruguay",            "country", "UYU", "UY", None),
    ("AR", "Argentina",          "country", "ARS", "AR", None),
    ("BR", "Brazil",             "country", "BRL", "BR", None),
    ("AE", "United Arab Emirates", "country", "AED", "AE", None),
    ("SA", "Saudi Arabia",       "country", "SAR", "SA", None),
    ("JO", "Jordan",             "country", "JOD", "JO", None),
    ("MA", "Morocco",            "country", "MAD", "MA", None),
    ("ZA", "South Africa",       "country", "ZAR", "ZA", None),
]

_SUB_NATIONALS = [
    # (code, name, level, currency_code, country_code, parent_code)
    ("US-OR",  "United States — Oregon",          "state",    "USD", "US", "US"),
    ("US-WA",  "United States — Washington",      "state",    "USD", "US", "US"),
    ("US-IL",  "United States — Illinois",        "state",    "USD", "US", "US"),
    ("US-NC",  "United States — North Carolina",  "state",    "USD", "US", "US"),
    ("US-SC",  "United States — South Carolina",  "state",    "USD", "US", "US"),
    ("US-MA",  "United States — Massachusetts",   "state",    "USD", "US", "US"),
    ("US-TX",  "United States — Texas",           "state",    "USD", "US", "US"),
    ("US-CT",  "United States — Connecticut",     "state",    "USD", "US", "US"),
    ("US-PA",  "United States — Pennsylvania",    "state",    "USD", "US", "US"),
    ("US-MD",  "United States — Maryland",        "state",    "USD", "US", "US"),
    ("US-VA",  "United States — Virginia",        "state",    "USD", "US", "US"),
    ("US-CO",  "United States — Colorado",        "state",    "USD", "US", "US"),
    ("US-TN",  "United States — Tennessee",       "state",    "USD", "US", "US"),
    ("US-OK",  "United States — Oklahoma",        "state",    "USD", "US", "US"),
    ("US-AL",  "United States — Alabama",         "state",    "USD", "US", "US"),
    ("US-KY",  "United States — Kentucky",        "state",    "USD", "US", "US"),
    ("CA-AB",  "Canada — Alberta",                "province", "CAD", "CA", "CA"),
    ("CA-MB",  "Canada — Manitoba",               "province", "CAD", "CA", "CA"),
    ("CA-NS",  "Canada — Nova Scotia",            "province", "CAD", "CA", "CA"),
    ("CA-NB",  "Canada — New Brunswick",          "province", "CAD", "CA", "CA"),
    ("AU-NSW", "Australia — New South Wales",     "state",    "AUD", "AU", "AU"),
    ("AU-VIC", "Australia — Victoria",            "state",    "AUD", "AU", "AU"),
    ("AU-QLD", "Australia — Queensland",          "state",    "AUD", "AU", "AU"),
    ("GB-SCT", "United Kingdom — Scotland",       "nation",   "GBP", "GB", "GB"),
    ("GB-WLS", "United Kingdom — Wales",          "nation",   "GBP", "GB", "GB"),
]

# ---------------------------------------------------------------------------
# Program data
# (jurisdiction_code, slug, name, program_type, base_rate, max_rate,
#  is_refundable, is_transferable, annual_cap_local, requires_cultural_test,
#  requires_local_entity, authority_url, notes)
# ---------------------------------------------------------------------------
_PROGRAMS = [
    ("US-OR",  "us_or_opif",         "Oregon Production Investment Fund (OPIF)",
     "cash_rebate",  0.20, 0.20, True,  False, None,        False, False,
     "https://oregonfilm.org/incentives/",
     "20% rebate on OR-sourced goods/services; 10% on OR resident wages. Min $750K OR spend."),
    ("US-WA",  "us_wa_mpcp",         "Washington State Motion Picture Competitiveness Program",
     "cash_rebate",  0.15, 0.35, True,  False, 3_500_000,   False, False,
     "https://washingtonfilmworks.com/funding/motion-picture-competitiveness-program/",
     "Competitive rebate. Annual fund ~$3.5M. DISCOVERY — rate/cap unconfirmed."),
    ("US-IL",  "us_il_film_credit",  "Illinois Film Tax Credit",
     "tax_credit",   0.30, 0.30, True,  True,  None,        False, False,
     "https://www.illinois.gov/business/film-production",
     "30% on Illinois production spend + resident wages. No annual cap."),
    ("US-NC",  "us_nc_film_grant",   "North Carolina Film & Entertainment Grant",
     "cash_rebate",  0.25, 0.25, True,  False, 31_000_000,  False, False,
     "https://www.filmnc.com/incentives",
     "25% cash grant on NC qualifying expenditures. Annual cap ~$31M."),
    ("US-SC",  "us_sc_film_credit",  "South Carolina Film Production Credit",
     "tax_credit",   0.20, 0.30, False, True,  None,        False, False,
     "https://sc.gov/government/agencies/film-commission",
     "Up to 30% on SC qualifying expenditures. Transferable credit."),
    ("US-MA",  "us_ma_film_credit",  "Massachusetts Film Tax Credit",
     "tax_credit",   0.25, 0.25, True,  True,  None,        False, False,
     "https://www.mafilm.org/tax-incentives/",
     "25% on MA payroll + 25% on production costs. No annual cap."),
    ("US-TX",  "us_tx_miip",         "Texas Moving Image Industry Incentive Program (MIIP)",
     "cash_rebate",  0.05, 0.225, True, False, 95_000_000,  False, False,
     "https://gov.texas.gov/film/page/incentives",
     "Base 5%; up to 22.5% with TX cast/crew uplift. Annual cap ~$95M."),
    ("US-CT",  "us_ct_film_credit",  "Connecticut Film Tax Credit",
     "tax_credit",   0.10, 0.30, True,  True,  None,        False, False,
     "https://portal.ct.gov/DECD/Content/Film-television-Creative-Services",
     "Tiered: 10% (<$1M CT spend) to 30% (>$500M CT spend). No annual cap."),
    ("US-PA",  "us_pa_film_credit",  "Pennsylvania Film Production Tax Credit",
     "tax_credit",   0.25, 0.25, False, True,  100_000_000, False, False,
     "https://dced.pa.gov/programs/pa-film-office/",
     "25% on PA qualifying spend. Transferable. Annual cap ~$100M."),
    ("US-MD",  "us_md_film_credit",  "Maryland Film Production Activity Tax Credit",
     "tax_credit",   0.25, 0.27, True,  False, 25_000_000,  False, False,
     "https://www.marylandfilm.org/resources/tax-incentives",
     "Up to 27% on Maryland qualifying expenditures. Annual cap ~$25M."),
    ("US-VA",  "us_va_film_credit",  "Virginia Motion Picture Production Tax Credit",
     "tax_credit",   0.15, 0.20, False, True,  6_500_000,   False, False,
     "https://www.film.virginia.org/production/incentives",
     "15% base; +5% for VA resident crew. Annual cap ~$6.5M."),
    ("US-CO",  "us_co_film_incentive","Colorado Film Incentive",
     "cash_rebate",  0.20, 0.20, True,  False, 750_000,     False, False,
     "https://oedit.colorado.gov/colorado-office-of-film-tv-and-media",
     "20% on Colorado qualifying spend. Annual cap ~$750K — very limited."),
    ("US-TN",  "us_tn_film_incentive","Tennessee Film Entertainment Incentives",
     "cash_rebate",  None, 0.25, None,  None,  None,        False, False,
     "https://www.tnfilm.com/incentives",
     "Programme structure evolving. Rate unconfirmed. DISCOVERY only."),
    ("US-OK",  "us_ok_ofer",         "Oklahoma Film Enhancement Rebate",
     "cash_rebate",  0.35, 0.37, True,  False, 5_000_000,   False, False,
     "https://www.oklahomafilm.org/incentives",
     "35% on OK wages/goods; +2% for OK-related scripts. Annual cap ~$5M."),
    ("US-AL",  "us_al_film_incentive","Alabama Film Incentive",
     "tax_credit",   0.25, 0.35, True,  False, 20_000_000,  False, False,
     "https://www.alabamafilm.org/incentives",
     "25% base; up to 35% with AL resident payroll. Annual cap ~$20M."),
    ("US-KY",  "us_ky_keiia",        "Kentucky Entertainment Industry Incentive Act (KEIIA)",
     "tax_credit",   0.30, 0.35, True,  False, None,        False, False,
     "https://kyfilmoffice.com/production-incentives/",
     "30% refundable on KY qualifying spend; +5% for KY local companies."),
    ("CA-AB",  "ca_ab_fttc",         "Alberta Film and Television Tax Credit (FTTC)",
     "tax_credit",   0.22, 0.22, True,  False, None,        True,  False,
     "https://www.ampia.org/alberta-film-tv-tax-credit/",
     "22% on eligible Alberta labour costs. Cultural test applies."),
    ("CA-MB",  "ca_mb_fvptc",        "Manitoba Film & Video Production Tax Credit",
     "tax_credit",   0.45, 0.65, True,  False, None,        True,  False,
     "https://www.mbfilmmusic.ca/en/production-tax-credits",
     "45% base on MB labour; bonuses can reach 65%. Labour-basis only."),
    ("CA-NS",  "ca_ns_pif",          "Nova Scotia Film & Television Production Incentive Fund",
     "cash_rebate",  0.25, 0.50, True,  False, None,        True,  False,
     "https://www.novascotiabusiness.com/export/film",
     "25% base; up to 50% with NS resident crew + bonuses."),
    ("CA-NB",  "ca_nb_film_credit",  "New Brunswick Film Tax Credit",
     "tax_credit",   0.25, 0.30, True,  False, None,        True,  False,
     "https://opportunitiesnb.com",
     "~25-30% on NB labour costs. Combines with federal CPTC."),
    ("NL",     "nl_nfpi",            "Netherlands Film Production Incentive (NFPI)",
     "cash_rebate",  0.30, 0.30, True,  False, None,        True,  True,
     "https://www.filmfund.nl/en/subsidies/netherlands-film-production-incentive",
     "30% cash rebate on qualifying Dutch expenditures. Cultural test + Dutch entity required."),
    ("AT",     "at_fisa_plus",       "FISA+ Film Production Support Austria",
     "cash_rebate",  0.25, 0.25, True,  False, None,        True,  False,
     "https://www.fisa-plus.at/en/",
     "25% on Austrian qualifying spend. Min EUR 600K. Cultural points test."),
    ("CZ",     "cz_film_incentive",  "Czech Film Incentive",
     "cash_rebate",  0.20, 0.20, True,  False, None,        False, False,
     "https://www.filmcommission.cz/incentives/",
     "20% cash rebate on Czech qualifying spend. No cultural test for foreign co-productions."),
    ("RO",     "ro_cnc_rebate",      "Romanian Film Office Cash Rebate",
     "cash_rebate",  0.35, 0.45, True,  False, None,        False, False,
     "https://www.cnc.ro/en",
     "35% base; up to 45% with Romanian crew bonus. Low cost base."),
    ("PT",     "pt_film_incentive",  "Portugal Film Commission Incentive / IAPMEI",
     "cash_rebate",  0.25, 0.30, True,  False, None,        True,  False,
     "https://www.filmportugal.com/incentives",
     "~25-30% on Portuguese qualifying spend. Cultural points test required."),
    ("RS",     "rs_film_rebate",     "Serbia Film Commission Cash Rebate",
     "cash_rebate",  0.25, 0.30, True,  False, None,        False, False,
     "https://www.filmcentar.rs",
     "Up to 30% on qualifying Serbian expenditures. Growing hub."),
    ("IS",     "is_film_reimbursement","Icelandic Film Reimbursement Scheme",
     "cash_rebate",  0.25, 0.25, True,  False, None,        False, False,
     "https://www.invest.is/doing-business/incentives/film-incentive/",
     "25% reimbursement on Icelandic qualifying spend. Unique landscape."),
    ("GB-SCT", "gb_sct_screen_fund", "Screen Scotland Production Growth Fund",
     "cash_rebate",  0.20, 0.30, True,  False, None,        True,  False,
     "https://www.screen.scot/funding-and-support/screen-scotland-funding/",
     "Tops up UK HMRC relief with Scotland-specific uplift. DISCOVERY."),
    ("GB-WLS", "gb_wls_screen_fund", "Wales Screen Production Fund (Ffilm Cymru Wales)",
     "cash_rebate",  0.20, 0.30, True,  False, None,        True,  False,
     "https://www.creativewales.wales/en/screen/",
     "Tops up UK HMRC relief with Wales-specific uplift. DISCOVERY."),
    ("SG",     "sg_sfc_production",  "Singapore Film Commission (SFC) — Production Assistance",
     "cash_rebate",  None, 0.30, None,  False, None,        False, False,
     "https://www.imda.gov.sg/regulations-and-licensing-listing/fia",
     "Discretionary grants/rebates via IMDA. Up to 30% reported. Project-by-project."),
    ("AU-NSW", "au_nsw_screen",      "NSW Government Screen Incentive (Create NSW)",
     "cash_rebate",  0.20, 0.35, True,  False, None,        False, False,
     "https://www.create.nsw.gov.au/funding-and-support/screen/",
     "~10% NSW uplift on top of federal Location Offset. Combined can reach 35%+."),
    ("AU-VIC", "au_vic_vicscreen",   "VicScreen Production Investment",
     "cash_rebate",  0.20, 0.335, True, False, None,        False, False,
     "https://vicscreen.vic.gov.au/funding/production-investment",
     "13.5% VIC state uplift + 20% federal = ~33.5% combined."),
    ("AU-QLD", "au_qld_screen_qld",  "Screen Queensland Production Attraction Strategy",
     "cash_rebate",  0.15, 0.30, True,  False, None,        False, False,
     "https://screenqueensland.com.au/get-funding/production-attraction/",
     "QLD cash incentive tops up federal Location Offset. DISCOVERY."),
    ("CO",     "co_film_colombia",   "Colombia Film Commission — Film In Colombia",
     "cash_rebate",  0.40, 0.40, True,  False, None,        False, False,
     "https://procolombia.co/en/opportunities-industries/film-sector",
     "40% VAT/services tax refund on Colombian qualifying spend. Mechanism unconfirmed."),
    ("DO",     "do_film_incentive",  "Dominican Republic Film Commission Incentive",
     "cash_rebate",  0.25, 0.25, True,  False, None,        False, False,
     "https://www.drfilmcommission.com",
     "25% rebate on qualifying Dominican expenditures. Pinewood DR nearby."),
    ("UY",     "uy_xxi_incentive",   "Uruguay XXI Film Incentive",
     "cash_rebate",  None, 0.20, None,  False, None,        False, False,
     "https://www.uruguayxxi.gub.uy",
     "Tax-based rebates/exemptions for international productions. Programme evolving."),
    ("AR",     "ar_incaa_incentive", "INCAA — Argentine Film Institute Incentives",
     "cash_rebate",  None, 0.25, None,  False, None,        True,  True,
     "https://www.incaa.gov.ar",
     "VAT exemptions + rebate for qualifying international co-productions. FX risk."),
    ("BR",     "br_ancine_incentive","ANCINE — Brazilian Film Commission Tax Incentives",
     "tax_credit",   None, 0.40, None,  False, None,        True,  True,
     "https://www.ancine.gov.br",
     "Rouanet Law + ANCINE incentives up to ~40% for co-productions. Complex."),
    ("AE",     "ae_dpip",            "Dubai Film Commission — Dubai Production Incentive (DPIP)",
     "cash_rebate",  0.30, 0.30, True,  False, None,        False, False,
     "https://www.dubaifilmcommission.com/incentives",
     "30% cashback on Dubai qualifying spend. No UAE corporate/income tax."),
    ("SA",     "sa_sfc_rebate",      "Saudi Film Commission (SFC) — Production Rebate",
     "cash_rebate",  None, 0.40, None,  False, None,        False, False,
     "https://saudifi.com",
     "Emerging market under Vision 2030. Up to 40% reported. Content restrictions apply."),
    ("JO",     "jo_rfc_rebate",      "Royal Film Commission Jordan — Production Rebate",
     "cash_rebate",  0.10, 0.25, True,  False, None,        False, False,
     "https://www.rfc.jo/en/incentives",
     "~10-25% rebate on Jordanian qualifying spend. Wadi Rum, Petra locations."),
    ("MA",     "ma_ccm_rebate",      "CCM Morocco — Production Rebate",
     "cash_rebate",  0.20, 0.30, True,  False, None,        False, True,
     "https://www.ccm.ma",
     "~20-30% on Moroccan qualifying spend. Ouarzazate/Atlas Studios. Local company required."),
    ("ZA",     "za_nfvf_rebate",     "NFVF / DTI — South Africa Foreign Film & TV Production Rebate",
     "cash_rebate",  0.20, 0.25, True,  False, None,        False, False,
     "https://www.nfvf.co.za",
     "~20-25% on SA qualifying spend. Cape Town primary hub. Favourable FX."),
]

# Benchmark data: (code, crew, equip, stage, loc, post, vfx, catering, travel, overrides)
_BENCHMARKS = [
    ("US-OR",  0.78, 0.75, 0.72, 0.68, 0.78, 0.80, 0.75, 340.0,
     {"marine_vessel_multiplier": 0.70, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 90.0}),
    ("US-WA",  0.82, 0.78, 0.75, 0.72, 0.82, 0.85, 0.78, 350.0,
     {"marine_vessel_multiplier": 0.75, "lodging_daily_usd": 210.0, "per_diem_daily_usd": 95.0}),
    ("US-IL",  0.88, 0.82, 0.80, 0.85, 0.85, 0.88, 0.82, 360.0,
     {"marine_vessel_multiplier": 0.75, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 100.0}),
    ("US-NC",  0.72, 0.68, 0.65, 0.60, 0.72, 0.75, 0.68, 300.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 175.0, "per_diem_daily_usd": 80.0}),
    ("US-SC",  0.70, 0.65, 0.62, 0.55, 0.70, 0.72, 0.65, 290.0,
     {"marine_vessel_multiplier": 0.62, "lodging_daily_usd": 165.0, "per_diem_daily_usd": 78.0}),
    ("US-MA",  0.90, 0.85, 0.82, 0.90, 0.88, 0.90, 0.85, 370.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 250.0, "per_diem_daily_usd": 105.0}),
    ("US-TX",  0.78, 0.75, 0.72, 0.70, 0.78, 0.80, 0.75, 320.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 190.0, "per_diem_daily_usd": 88.0}),
    ("US-CT",  0.88, 0.82, 0.80, 0.85, 0.85, 0.88, 0.82, 360.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 100.0}),
    ("US-PA",  0.82, 0.78, 0.75, 0.80, 0.80, 0.82, 0.78, 340.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 205.0, "per_diem_daily_usd": 92.0}),
    ("US-MD",  0.85, 0.80, 0.78, 0.82, 0.82, 0.85, 0.80, 350.0,
     {"marine_vessel_multiplier": 0.78, "lodging_daily_usd": 220.0, "per_diem_daily_usd": 95.0}),
    ("US-VA",  0.80, 0.76, 0.72, 0.75, 0.78, 0.80, 0.76, 330.0,
     {"marine_vessel_multiplier": 0.72, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 88.0}),
    ("US-CO",  0.78, 0.75, 0.70, 0.68, 0.78, 0.80, 0.75, 320.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 195.0, "per_diem_daily_usd": 88.0}),
    ("US-TN",  0.70, 0.68, 0.65, 0.60, 0.70, 0.72, 0.68, 290.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 78.0}),
    ("US-OK",  0.65, 0.62, 0.60, 0.50, 0.65, 0.68, 0.62, 275.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 150.0, "per_diem_daily_usd": 70.0}),
    ("US-AL",  0.65, 0.62, 0.58, 0.50, 0.65, 0.68, 0.60, 275.0,
     {"marine_vessel_multiplier": 0.60, "lodging_daily_usd": 150.0, "per_diem_daily_usd": 70.0}),
    ("US-KY",  0.68, 0.65, 0.62, 0.55, 0.68, 0.70, 0.65, 280.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 155.0, "per_diem_daily_usd": 72.0}),
    ("CA-AB",  0.72, 0.70, 0.68, 0.60, 0.72, 0.72, 0.68, 300.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 185.0, "per_diem_daily_usd": 85.0}),
    ("CA-MB",  0.65, 0.62, 0.60, 0.52, 0.65, 0.65, 0.60, 270.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 155.0, "per_diem_daily_usd": 72.0}),
    ("CA-NS",  0.65, 0.62, 0.60, 0.55, 0.65, 0.65, 0.62, 280.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 160.0, "per_diem_daily_usd": 75.0}),
    ("CA-NB",  0.62, 0.60, 0.58, 0.50, 0.62, 0.62, 0.58, 265.0,
     {"marine_vessel_multiplier": 0.60, "lodging_daily_usd": 150.0, "per_diem_daily_usd": 70.0}),
    ("NL",     0.88, 0.85, 0.82, 0.90, 0.88, 0.85, 0.82, 370.0,
     {"marine_vessel_multiplier": 0.82, "lodging_daily_usd": 240.0, "per_diem_daily_usd": 100.0}),
    ("AT",     0.85, 0.82, 0.80, 0.88, 0.85, 0.82, 0.80, 360.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 225.0, "per_diem_daily_usd": 98.0}),
    ("CZ",     0.45, 0.50, 0.55, 0.40, 0.55, 0.55, 0.45, 260.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 130.0, "per_diem_daily_usd": 65.0}),
    ("RO",     0.38, 0.42, 0.45, 0.32, 0.48, 0.50, 0.38, 240.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 58.0}),
    ("PT",     0.60, 0.62, 0.60, 0.58, 0.65, 0.65, 0.58, 290.0,
     {"marine_vessel_multiplier": 0.60, "lodging_daily_usd": 165.0, "per_diem_daily_usd": 78.0}),
    ("RS",     0.35, 0.40, 0.42, 0.30, 0.45, 0.48, 0.35, 235.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 55.0}),
    ("IS",     0.95, 0.90, 0.85, 0.70, 0.90, 0.88, 0.88, 450.0,
     {"marine_vessel_multiplier": 0.85, "lodging_daily_usd": 280.0, "per_diem_daily_usd": 115.0}),
    ("GB-SCT", 0.85, 0.82, 0.80, 0.85, 0.85, 0.82, 0.78, 370.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 100.0}),
    ("GB-WLS", 0.82, 0.80, 0.78, 0.78, 0.82, 0.80, 0.75, 360.0,
     {"marine_vessel_multiplier": 0.78, "lodging_daily_usd": 215.0, "per_diem_daily_usd": 95.0}),
    ("SG",     0.72, 0.70, 0.68, 0.80, 0.72, 0.70, 0.65, 380.0,
     {"marine_vessel_multiplier": 0.68, "lodging_daily_usd": 220.0, "per_diem_daily_usd": 90.0}),
    ("AU-NSW", 0.80, 0.75, 0.72, 0.70, 0.75, 0.72, 0.70, 490.0,
     {"marine_vessel_multiplier": 0.75, "lodging_daily_usd": 215.0, "per_diem_daily_usd": 95.0}),
    ("AU-VIC", 0.78, 0.74, 0.70, 0.68, 0.74, 0.70, 0.68, 480.0,
     {"marine_vessel_multiplier": 0.72, "lodging_daily_usd": 205.0, "per_diem_daily_usd": 92.0}),
    ("AU-QLD", 0.74, 0.70, 0.68, 0.65, 0.70, 0.68, 0.65, 475.0,
     {"marine_vessel_multiplier": 0.70, "lodging_daily_usd": 195.0, "per_diem_daily_usd": 88.0}),
    ("CO",     0.38, 0.42, 0.40, 0.30, 0.45, 0.48, 0.35, 250.0,
     {"marine_vessel_multiplier": 0.38, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 55.0}),
    ("DO",     0.35, 0.40, 0.45, 0.28, 0.42, 0.45, 0.32, 260.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 105.0, "per_diem_daily_usd": 52.0}),
    ("UY",     0.42, 0.45, 0.42, 0.35, 0.48, 0.50, 0.40, 255.0,
     {"marine_vessel_multiplier": 0.42, "lodging_daily_usd": 115.0, "per_diem_daily_usd": 58.0}),
    ("AR",     0.28, 0.35, 0.38, 0.25, 0.38, 0.40, 0.28, 240.0,
     {"marine_vessel_multiplier": 0.32, "lodging_daily_usd": 90.0, "per_diem_daily_usd": 45.0}),
    ("BR",     0.40, 0.45, 0.45, 0.35, 0.48, 0.50, 0.38, 265.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 60.0}),
    ("AE",     0.72, 0.70, 0.72, 0.75, 0.68, 0.65, 0.65, 420.0,
     {"marine_vessel_multiplier": 0.68, "lodging_daily_usd": 260.0, "per_diem_daily_usd": 105.0}),
    ("SA",     0.68, 0.65, 0.65, 0.55, 0.62, 0.60, 0.58, 400.0,
     {"marine_vessel_multiplier": 0.60, "lodging_daily_usd": 240.0, "per_diem_daily_usd": 95.0}),
    ("JO",     0.40, 0.45, 0.42, 0.35, 0.48, 0.50, 0.38, 280.0,
     {"marine_vessel_multiplier": 0.40, "lodging_daily_usd": 130.0, "per_diem_daily_usd": 62.0}),
    ("MA",     0.32, 0.38, 0.42, 0.28, 0.42, 0.45, 0.30, 240.0,
     {"marine_vessel_multiplier": 0.35, "lodging_daily_usd": 100.0, "per_diem_daily_usd": 52.0}),
    ("ZA",     0.35, 0.40, 0.42, 0.30, 0.45, 0.48, 0.32, 255.0,
     {"marine_vessel_multiplier": 0.38, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 55.0}),
]


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Insert country-level jurisdictions (18 new countries)
    # ------------------------------------------------------------------
    for code, name, level, currency, country_code, _ in _COUNTRIES:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (id, parent_id, name, code, iso_code, level,
                    currency_code, country_code, is_active, created_at, updated_at)
                SELECT :id, NULL, :name, :code, :iso_code, :level,
                    :currency, :country_code, true, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code
                )
            """),
            {
                "id": _uid(f"jur:{code}"), "name": name, "code": code, "iso_code": code,
                "level": level, "currency": currency, "country_code": country_code, "now": NOW,
            },
        )

    # ------------------------------------------------------------------
    # 2. Insert sub-national jurisdictions (25 entries)
    # ------------------------------------------------------------------
    for code, name, level, currency, country_code, parent_code in _SUB_NATIONALS:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (id, parent_id, name, code, iso_code, level,
                    currency_code, country_code, is_active, created_at, updated_at)
                SELECT :id,
                    (SELECT id FROM jurisdictions WHERE code = :parent_code LIMIT 1),
                    :name, :code, :iso_code, :level, :currency, :country_code, true, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code
                )
            """),
            {
                "id": _uid(f"jur:{code}"), "name": name, "code": code, "iso_code": code,
                "level": level, "currency": currency, "country_code": country_code,
                "parent_code": parent_code, "now": NOW,
            },
        )

    # ------------------------------------------------------------------
    # 3. Insert incentive programs (43 entries)
    # ------------------------------------------------------------------
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
                    SELECT 1 FROM incentive_programs WHERE slug = :slug
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

    # ------------------------------------------------------------------
    # 4. Insert local_cost_benchmarks (43 entries)
    # ------------------------------------------------------------------
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

    # Remove benchmarks for extended jurisdictions
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

    # Remove programs seeded in this migration
    for _, slug, *_ in _PROGRAMS:
        conn.execute(
            sa.text("DELETE FROM incentive_programs WHERE slug = :slug AND id = :id"),
            {"slug": slug, "id": _uid(f"prog:{slug}")},
        )

    # Remove sub-national jurisdictions seeded in this migration
    for code, *_ in _SUB_NATIONALS:
        conn.execute(
            sa.text("DELETE FROM jurisdictions WHERE code = :code AND id = :id"),
            {"code": code, "id": _uid(f"jur:{code}")},
        )

    # Remove country-level jurisdictions seeded in this migration
    for code, *_ in _COUNTRIES:
        conn.execute(
            sa.text("DELETE FROM jurisdictions WHERE code = :code AND id = :id"),
            {"code": code, "id": _uid(f"jur:{code}")},
        )
