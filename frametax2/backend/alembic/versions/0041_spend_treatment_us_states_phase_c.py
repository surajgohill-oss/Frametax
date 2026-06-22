"""0041 — Phase C spend-treatment resolution: US state incentive programs.

Resolves qualifies / does_not_qualify for 5 programs that were seeded as UNKNOWN
in migrations 0024 (us_or_opif) and 0031 (wave-3 US states):
  us_ga_film_credit   — Georgia EIIA (transferable credit on in-state spend)
  us_la_film_incentive — Louisiana MPPTC (transferable credit on in-state spend)
  us_nm_film_credit   — New Mexico FPTC (refundable credit on in-state spend)
  us_ny_film_credit   — New York SFTC (refundable credit on in-state spend)
  us_or_opif          — Oregon OPIF (cash rebate on Oregon-sourced goods/services)

Rules applied (source: state film office programme summaries — same framework as
georgia_eiia established in migration 0017):
  QUALIFIES   — all ATL (including cast), BTL resident/non-resident/foreign,
                travel, accommodation, per diem, insurance, completion_bond,
                marine_vessel, vfx, post_production, animation, music,
                legal_accounting
  DNQ         — contingency
  UNKNOWN     — customs_imports (state-specific; not confirmed from primary source)

Revision ID: 0041
Revises: 0040
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: Union[str, None] = "0040"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

_CONTINGENCY_NOTE = (
    "Contingency is not a qualifying production expenditure under any US state incentive — "
    "it is a budget reserve, not an incurred cost."
)

_CUSTOMS_NOTE = (
    "Customs/import duties treatment under US state film incentives is programme-specific "
    "and not confirmed from primary source. UNKNOWN pending review."
)

_PROGRAMS = {
    "us_ga_film_credit": {
        "prog": "Georgia EIIA",
        "q_note": "qualifying Georgia-incurred production expenditure (GA EIIA § 48-7-40.26)",
        "d_note": "does not qualify under Georgia EIIA as a qualifying production expenditure",
    },
    "us_la_film_incentive": {
        "prog": "Louisiana MPPTC",
        "q_note": "qualifying Louisiana production expenditure (LA R.S. 47:6007)",
        "d_note": "does not qualify under Louisiana MPPTC as a base investment expenditure",
    },
    "us_nm_film_credit": {
        "prog": "New Mexico FPTC",
        "q_note": "qualifying New Mexico production cost (NM Stat. § 7-2F-1)",
        "d_note": "does not qualify under New Mexico FPTC as a qualifying production cost",
    },
    "us_ny_film_credit": {
        "prog": "New York SFTC",
        "q_note": "qualifying New York State production expenditure (NY Tax Law § 24)",
        "d_note": "does not qualify under New York SFTC as a qualified production cost",
    },
    "us_or_opif": {
        "prog": "Oregon OPIF",
        "q_note": "qualifying Oregon-sourced good/service (ORS 284.367 OPIF programme)",
        "d_note": "does not qualify under Oregon OPIF as a qualifying Oregon expenditure",
    },
}

_QUALIFIES_CATEGORIES = [
    "atl_writer",
    "atl_director",
    "atl_producer",
    "atl_exec_producer",
    "atl_line_producer",
    "atl_cast_principal",
    "atl_cast_supporting",
    "btl_crew_resident",
    "btl_crew_non_resident",
    "btl_crew_foreign",
    "travel",
    "accommodation_lodging",
    "per_diem",
    "insurance",
    "completion_bond",
    "marine_vessel",
    "vfx",
    "post_production",
    "animation",
    "music",
    "legal_accounting",
]

_UPSERT_SQL = sa.text("""
    UPDATE program_spend_treatments pst
       SET qualifies      = :qualifies,
           notes          = :note,
           updated_at     = :now
      FROM incentive_programs ip
     WHERE ip.id        = pst.program_id
       AND ip.slug      = :slug
       AND pst.labor_type = :lt
""")

_RESET_SQL = sa.text("""
    UPDATE program_spend_treatments pst
       SET qualifies      = NULL,
           notes          = NULL,
           updated_at     = :now
      FROM incentive_programs ip
     WHERE ip.id        = pst.program_id
       AND ip.slug      = :slug
""")


def upgrade() -> None:
    conn = op.get_bind()
    for slug, meta in _PROGRAMS.items():
        prog = meta["prog"]
        q_note = meta["q_note"]
        d_note = meta["d_note"]

        for lt in _QUALIFIES_CATEGORIES:
            conn.execute(_UPSERT_SQL, {
                "slug": slug,
                "lt": lt,
                "qualifies": True,
                "note": f"{prog}: {lt.replace('_', ' ')} is {q_note}.",
                "now": NOW,
            })

        conn.execute(_UPSERT_SQL, {
            "slug": slug,
            "lt": "contingency",
            "qualifies": False,
            "note": _CONTINGENCY_NOTE,
            "now": NOW,
        })

        conn.execute(_UPSERT_SQL, {
            "slug": slug,
            "lt": "customs_imports",
            "qualifies": None,
            "note": _CUSTOMS_NOTE,
            "now": NOW,
        })


def downgrade() -> None:
    conn = op.get_bind()
    for slug in _PROGRAMS:
        conn.execute(_RESET_SQL, {"slug": slug, "now": NOW})
