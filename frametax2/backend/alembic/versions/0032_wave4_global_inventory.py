"""0032 — Wave-4 global inventory: 21 programs across 21 new jurisdictions.

Region completion pass covering Central Asia (AZ, UZ), Middle East (OM, LB),
South America (VE, GY), Central America (GT), Africa (NA, BW, ET, CI, CM, AO,
UG, MZ, ZM, ZW), East Asia (CN, MN, MO), and South Asia (BD).

All programs are DISCOVERY tier. No benchmarks created (mandate: Phase 2 only).

Revision ID: 0032
Revises: 0031
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: Union[str, None] = "0031"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0032-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# (code, name, level, currency, country_code, parent_code)
_COUNTRIES: list[tuple] = [
    # Central Asia / Caucasus
    ("AZ",  "Azerbaijan",            "country", "AZN",  "AZ",  None),
    ("UZ",  "Uzbekistan",            "country", "UZS",  "UZ",  None),
    # Middle East
    ("OM",  "Oman",                  "country", "OMR",  "OM",  None),
    ("LB",  "Lebanon",               "country", "LBP",  "LB",  None),
    # South America
    ("VE",  "Venezuela",             "country", "VES",  "VE",  None),
    ("GY",  "Guyana",                "country", "GYD",  "GY",  None),
    # Central America
    ("GT",  "Guatemala",             "country", "GTQ",  "GT",  None),
    # Africa
    ("NA",  "Namibia",               "country", "NAD",  "NA",  None),
    ("BW",  "Botswana",              "country", "BWP",  "BW",  None),
    ("ET",  "Ethiopia",              "country", "ETB",  "ET",  None),
    ("CI",  "Côte d'Ivoire",         "country", "XOF",  "CI",  None),
    ("CM",  "Cameroon",              "country", "XAF",  "CM",  None),
    ("AO",  "Angola",                "country", "AOA",  "AO",  None),
    ("UG",  "Uganda",                "country", "UGX",  "UG",  None),
    ("MZ",  "Mozambique",            "country", "MZN",  "MZ",  None),
    ("ZM",  "Zambia",                "country", "ZMW",  "ZM",  None),
    ("ZW",  "Zimbabwe",              "country", "USD",  "ZW",  None),
    # East Asia
    ("CN",  "China",                 "country", "CNY",  "CN",  None),
    ("MN",  "Mongolia",              "country", "MNT",  "MN",  None),
    ("MO",  "Macau SAR",             "country", "MOP",  "MO",  None),
    # South Asia
    ("BD",  "Bangladesh",            "country", "BDT",  "BD",  None),
]

# (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
#  is_transferable, annual_cap_local, req_cultural, req_local, authority_url, notes)
_PROGRAMS: list[tuple] = [
    ("AZ", "az_film_incentive",
     "Azerbaijan Film Fund Production Support",
     "direct_grant", None, None, False, False, None, False, False,
     "https://www.azfilm.az",
     "State support for domestic and international co-productions. DISCOVERY tier."),

    ("UZ", "uz_film_incentive",
     "Uzbekkino National Film Support Program",
     "production_support", None, None, False, False, None, False, True,
     "https://www.uzbekkino.uz",
     "Uzbekkino state agency; studio and location support. DISCOVERY tier."),

    ("OM", "om_film_commission",
     "Oman Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.omanfilmcommission.com",
     "Location permits, government liaison, in-kind support. DISCOVERY tier."),

    ("LB", "lb_film_incentive",
     "Centre du Cinéma Libanais (CCL) Production Support",
     "direct_grant", None, None, False, False, None, True, True,
     "https://www.culture.gov.lb",
     "Co-production grants via Ministry of Culture. Status affected by economic crisis. DISCOVERY tier."),

    ("VE", "ve_cnac_fund",
     "CNAC Venezuela Film Production Fund",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.cnac.gob.ve",
     "CNAC national film fund for domestic and co-productions. DISCOVERY tier."),

    ("GY", "gy_film_commission",
     "Guyana Tourism Authority Film Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.guyanatourism.com",
     "Location facilitation and permit support. DISCOVERY tier."),

    ("GT", "gt_film_commission",
     "Guatemala Film Commission (INGUAT) Production Facilitation",
     "production_support", None, None, False, False, None, False, False,
     "https://www.inguat.net",
     "Location permits and government liaison via INGUAT. DISCOVERY tier."),

    ("NA", "na_film_commission",
     "Namibia Film Commission Production Incentive",
     "cash_rebate", None, None, True, False, None, False, False,
     "https://www.namibiafilmcommission.com",
     "Cash rebate on qualifying Namibian spend; rate unconfirmed. DISCOVERY tier."),

    ("BW", "bw_film_commission",
     "Botswana Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.botswanafilm.co.bw",
     "Location permits and production facilitation. DISCOVERY tier."),

    ("ET", "et_film_commission",
     "Ethiopian Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.moct.gov.et",
     "Facilitation through Ministry of Culture and Tourism. DISCOVERY tier."),

    ("CI", "ci_film_incentive",
     "Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.culture.gouv.ci",
     "State support via CNCI for domestic and co-productions. DISCOVERY tier."),

    ("CM", "cm_film_incentive",
     "Cameroon Centre National de la Cinématographie Film Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.minac.cm",
     "Film support via MINAC directorate. DISCOVERY tier."),

    ("AO", "ao_film_incentive",
     "Angola Instituto do Cinema e Audiovisual (ICA) Production Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.mincult.gov.ao",
     "ICA state support for productions with Angolan partners. DISCOVERY tier."),

    ("UG", "ug_film_commission",
     "Uganda Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.ugandafilmcommission.org",
     "Location permits and production facilitation. DISCOVERY tier."),

    ("MZ", "mz_film_incentive",
     "Mozambique Instituto do Cinema Film Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.cultura.gov.mz",
     "Facilitation through Ministry of Culture cinema institute. DISCOVERY tier."),

    ("ZM", "zm_film_commission",
     "Zambia Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.zfc.gov.zm",
     "Location permits and production liaison. DISCOVERY tier."),

    ("ZW", "zw_film_commission",
     "Zimbabwe Film and Broadcasting Authority Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.zbfta.co.zw",
     "ZBFTA facilitates film productions. DISCOVERY tier."),

    ("CN", "cn_film_incentive",
     "China Film Administration Domestic Co-production Support",
     "production_support", None, None, False, False, None, True, True,
     "https://www.nrta.gov.cn",
     "Co-production access via China Film Administration; content review required. DISCOVERY tier."),

    ("MN", "mn_film_commission",
     "Mongolian Film Commission Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.mcta.gov.mn",
     "Permitting through Ministry of Culture. DISCOVERY tier."),

    ("MO", "mo_film_fund",
     "Macau Cultural Industries Fund Film Production Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.ic.gov.mo",
     "Instituto Cultural film grants for co-productions. DISCOVERY tier."),

    ("BD", "bd_film_incentive",
     "Bangladesh Film Development Corporation (BFDC) Production Support",
     "production_support", None, None, False, False, None, False, True,
     "https://www.bfdc.gov.bd",
     "BFDC studio and production support. DISCOVERY tier."),
]


def upgrade() -> None:
    conn = op.get_bind()

    for code, name, level, currency, country_code, parent_code in _COUNTRIES:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (
                    id, code, name, level, currency_code,
                    country_code, parent_id, created_at, updated_at
                )
                SELECT
                    :id, :code, :name, :level, :currency,
                    :country_code,
                    (SELECT id FROM jurisdictions WHERE code = :parent_code ::varchar LIMIT 1),
                    :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code ::varchar
                )
            """),
            {
                "id": _uid(f"jur:{code}"),
                "code": code,
                "name": name,
                "level": level,
                "currency": currency,
                "country_code": country_code,
                "parent_code": parent_code,
                "now": NOW,
            },
        )

    for (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
         is_transferable, annual_cap_local, req_cultural, req_local,
         authority_url, notes) in _PROGRAMS:
        conn.execute(
            sa.text("""
                INSERT INTO incentive_programs (
                    id, jurisdiction_id, name, slug, program_type,
                    credit_basis, base_rate, max_rate, is_refundable,
                    is_transferable, annual_cap_local,
                    requires_cultural_test, requires_local_entity,
                    authority_url, notes, confidence_tier,
                    is_competitive, created_at, updated_at
                )
                SELECT
                    :id, j.id, :name, :slug, :prog_type,
                    'qualifying_spend', :base_rate, :max_rate, :is_refundable,
                    :is_transferable, :annual_cap_local,
                    :req_cultural, :req_local,
                    :authority_url, :notes, 'DISCOVERY',
                    false, :now, :now
                FROM jurisdictions j
                WHERE j.code = :jur_code
                  AND NOT EXISTS (
                      SELECT 1 FROM incentive_programs p WHERE p.slug = :slug ::varchar
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"prog:{slug}"),
                "jur_code": jur_code,
                "slug": slug,
                "name": name,
                "prog_type": prog_type,
                "base_rate": base_rate,
                "max_rate": max_rate,
                "is_refundable": is_refundable,
                "is_transferable": is_transferable,
                "annual_cap_local": annual_cap_local,
                "req_cultural": req_cultural,
                "req_local": req_local,
                "authority_url": authority_url,
                "notes": notes,
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for _, slug, *_ in _PROGRAMS:
        conn.execute(
            sa.text("DELETE FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug},
        )
    for code, *_ in _COUNTRIES:
        conn.execute(
            sa.text("DELETE FROM jurisdictions WHERE code = :code"),
            {"code": code},
        )
