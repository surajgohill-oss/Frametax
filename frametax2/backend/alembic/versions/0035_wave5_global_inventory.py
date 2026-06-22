"""0035 — Wave-5 global inventory: 13 programs (final global discovery pass).

Covers Switzerland (CH), Slovenia (SI), Ukraine (UA), Russia (RU), Belarus (BY),
Moldova (MD), Cuba (CU), Iran (IR), Algeria (DZ), Gabon (GA), Seychelles (SC),
Maldives (MV), and Bhutan (BT).

All programs are DISCOVERY tier. No benchmarks created.

Revision ID: 0035
Revises: 0034
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0035"
down_revision: Union[str, None] = "0034"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0035-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# (code, name, level, currency, country_code, parent_code)
_COUNTRIES: list[tuple] = [
    ("CH",  "Switzerland",  "country", "CHF",  "CH",  None),
    ("SI",  "Slovenia",     "country", "EUR",  "SI",  None),
    ("UA",  "Ukraine",      "country", "UAH",  "UA",  None),
    ("RU",  "Russia",       "country", "RUB",  "RU",  None),
    ("BY",  "Belarus",      "country", "BYN",  "BY",  None),
    ("MD",  "Moldova",      "country", "MDL",  "MD",  None),
    ("CU",  "Cuba",         "country", "CUP",  "CU",  None),
    ("IR",  "Iran",         "country", "IRR",  "IR",  None),
    ("DZ",  "Algeria",      "country", "DZD",  "DZ",  None),
    ("GA",  "Gabon",        "country", "XAF",  "GA",  None),
    ("SC",  "Seychelles",   "country", "SCR",  "SC",  None),
    ("MV",  "Maldives",     "country", "MVR",  "MV",  None),
    ("BT",  "Bhutan",       "country", "BTN",  "BT",  None),
]

# (jur_code, slug, name, prog_type, base_rate, max_rate, is_refundable,
#  is_transferable, annual_cap_local, req_cultural, req_local, authority_url, notes)
_PROGRAMS: list[tuple] = [
    ("CH", "ch_film_support",
     "Swiss Federal Office of Culture (FOC) Film Support",
     "direct_grant", None, None, False, False, None, True, True,
     "https://www.bak.admin.ch/bak/en/home/film/films-in-switzerland.html",
     "Federal + cantonal grants; Eurimages + MEDIA participation. DISCOVERY tier."),

    ("SI", "si_film_incentive",
     "Slovenian Film Centre (SFC) Cash Rebate and Production Support",
     "cash_rebate", None, None, True, False, None, False, False,
     "https://www.film-center.si",
     "SFC administers cash rebate for qualifying Slovenian spend. DISCOVERY tier."),

    ("UA", "ua_film_incentive",
     "Ukrainian State Film Agency Production Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.dergkino.gov.ua",
     "State film agency; note: operations constrained by ongoing conflict. DISCOVERY tier."),

    ("RU", "ru_film_incentive",
     "Russian Cinema Fund (Fond Kino) Production Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.fond-kino.ru",
     "Fond Kino state support; note: Western co-operations suspended due to sanctions. DISCOVERY tier."),

    ("BY", "by_film_incentive",
     "Belarusfilm National Film Studio Production Support",
     "production_support", None, None, False, False, None, False, True,
     "https://www.belarusfilm.by",
     "Belarusfilm studio infrastructure; note: international co-operations constrained by sanctions. DISCOVERY tier."),

    ("MD", "md_film_incentive",
     "National Centre for Cinematography Moldova (NCFM)",
     "direct_grant", None, None, False, False, None, False, True,
     "https://cnf.md",
     "NCFM administers domestic and co-production support. DISCOVERY tier."),

    ("CU", "cu_film_incentive",
     "ICAIC Cuba Film Production Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.icaic.cu",
     "ICAIC national film institute; US trade restrictions apply. DISCOVERY tier."),

    ("IR", "ir_film_incentive",
     "Farabi Cinema Foundation Film Production Support",
     "direct_grant", None, None, False, False, None, True, True,
     "https://www.farabicinema.com",
     "Farabi Cinema Foundation; international sanctions and content review apply. DISCOVERY tier."),

    ("DZ", "dz_film_incentive",
     "Centre Algérien pour le Développement du Cinéma (CADC) Film Support",
     "direct_grant", None, None, False, False, None, False, True,
     "https://www.cadc.dz",
     "CADC/FDATIC state film support. DISCOVERY tier."),

    ("GA", "ga_film_incentive",
     "Gabon Ministry of Culture Film Commission Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.agence-gabonaise-tourisme.com",
     "Ministry of Culture film commission facilitation. DISCOVERY tier."),

    ("SC", "sc_film_incentive",
     "Seychelles Tourism Board Film Production Support",
     "production_support", None, None, False, False, None, False, False,
     "https://www.seychelles.travel",
     "Tourism Board location facilitation for international productions. DISCOVERY tier."),

    ("MV", "mv_film_incentive",
     "Maldives Marketing and PR Corporation (MMPRC) Film Facilitation",
     "production_support", None, None, False, False, None, False, False,
     "https://www.visitmaldives.com",
     "MMPRC facilitates film and commercial productions. DISCOVERY tier."),

    ("BT", "bt_film_incentive",
     "Bhutan Film Commission / Tourism Council Production Facilitation",
     "production_support", None, None, False, False, None, False, False,
     "https://www.tourism.gov.bt",
     "Tourism Council permits; daily tariff applies. DISCOVERY tier."),
]


def upgrade() -> None:
    conn = op.get_bind()

    for code, name, level, currency, country_code, parent_code in _COUNTRIES:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (
                    id, code, name, level, currency_code,
                    country_code, parent_code, created_at, updated_at
                )
                SELECT
                    :id, :code, :name, :level, :currency,
                    :country_code, :parent_code, :now, :now
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code
                )
            """),
            {
                "id": _uid(f"jur:{code}"),
                "code": code, "name": name, "level": level,
                "currency": currency, "country_code": country_code,
                "parent_code": parent_code, "now": NOW,
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
                      SELECT 1 FROM incentive_programs p WHERE p.slug = :slug
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"prog:{slug}"),
                "jur_code": jur_code, "slug": slug, "name": name,
                "prog_type": prog_type, "base_rate": base_rate,
                "max_rate": max_rate, "is_refundable": is_refundable,
                "is_transferable": is_transferable,
                "annual_cap_local": annual_cap_local,
                "req_cultural": req_cultural, "req_local": req_local,
                "authority_url": authority_url, "notes": notes, "now": NOW,
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
