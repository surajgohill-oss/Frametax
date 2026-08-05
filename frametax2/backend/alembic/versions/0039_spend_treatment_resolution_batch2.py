"""0039 — Phase C spend-treatment resolution batch 2.

Resolves qualifies / does_not_qualify for 5 VERIFIED programs:
  uk_avec, ie_section_481, fr_trip, it_tax_credit_foreign, gr_cash_rebate

Rules applied (source-backed):
  QUALIFIES   — ATL (writer/director/producer/exec_producer/line_producer),
                btl_crew_resident, btl_crew_non_resident, travel,
                accommodation_lodging, per_diem, insurance, marine_vessel,
                vfx, post_production, animation, music, legal_accounting
  DNQ         — contingency, customs_imports, btl_crew_foreign
  UNKNOWN     — completion_bond (all programs)
               atl_cast_principal + atl_cast_supporting (fr_trip only —
               cultural-committee test prevents deterministic confirmation)

Revision ID: 0039
Revises: 0038
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0039"
down_revision: Union[str, None] = "0038"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(slug: str, lt: str, note: str) -> dict:
    return {"slug": slug, "lt": lt, "qualifies": True, "note": note, "now": NOW}


def _d(slug: str, lt: str, note: str) -> dict:
    return {"slug": slug, "lt": lt, "qualifies": False, "note": note, "now": NOW}


def _u(slug: str, lt: str, note: str) -> dict:
    return {"slug": slug, "lt": lt, "qualifies": None, "note": note, "now": NOW}


# ---------------------------------------------------------------------------
# Update rows
# ---------------------------------------------------------------------------

_ATL_QUALIFIES = [
    "atl_writer",
    "atl_director",
    "atl_producer",
    "atl_exec_producer",
    "atl_line_producer",
]

_BTL_QUALIFIES = [
    "btl_crew_resident",
    "btl_crew_non_resident",
    "travel",
    "accommodation_lodging",
    "per_diem",
    "insurance",
    "marine_vessel",
    "vfx",
    "post_production",
    "animation",
    "music",
    "legal_accounting",
]

_DNQ = [
    "contingency",
    "customs_imports",
    "btl_crew_foreign",
]

_CAST = [
    "atl_cast_principal",
    "atl_cast_supporting",
]

_COMPLETION_BOND = "completion_bond"


def _build_updates(slug: str, cast_qualifies: bool | None, note_q: str, note_d: str, note_unk: str) -> list[dict]:
    rows: list[dict] = []
    for lt in _ATL_QUALIFIES:
        rows.append(_q(slug, lt, note_q))
    for lt in _CAST:
        if cast_qualifies is True:
            rows.append(_q(slug, lt, note_q))
        elif cast_qualifies is False:
            rows.append(_d(slug, lt, note_d))
        else:
            rows.append(_u(slug, lt, note_unk))
    for lt in _BTL_QUALIFIES:
        rows.append(_q(slug, lt, note_q))
    for lt in _DNQ:
        rows.append(_d(slug, lt, note_d))
    rows.append(_u(slug, _COMPLETION_BOND, note_unk))
    return rows


_UPDATES: list[dict] = [
    *_build_updates(
        "uk_avec",
        cast_qualifies=True,
        note_q="UK AVEC: goods/services used or consumed in the UK qualify (HMRC AVEC guidance)",
        note_d="UK AVEC: does not qualify under HMRC AVEC eligible expenditure rules",
        note_unk="UK AVEC: completion bond eligibility not confirmed in primary HMRC source",
    ),
    *_build_updates(
        "ie_section_481",
        cast_qualifies=True,
        note_q="IE S481: eligible element expenditure confirmed (Revenue Commissioners S481 guidance)",
        note_d="IE S481: does not qualify as eligible element expenditure under S481",
        note_unk="IE S481: completion bond eligibility not confirmed in primary Revenue source",
    ),
    *_build_updates(
        "fr_trip",
        cast_qualifies=None,  # cultural-committee test — UNKNOWN
        note_q="FR TRIP: qualifying French expenditure confirmed (CNC TRIP official programme page)",
        note_d="FR TRIP: does not qualify as French expenditure under TRIP rules",
        note_unk="FR TRIP: eligibility not deterministically confirmed from primary CNC source",
    ),
    *_build_updates(
        "it_tax_credit_foreign",
        cast_qualifies=True,
        note_q="IT Foreign Tax Credit: qualifying expenditure confirmed (MiC/DGCinema official page)",
        note_d="IT Foreign Tax Credit: does not qualify under MiC eligible expenditure rules",
        note_unk="IT Foreign Tax Credit: completion bond eligibility not confirmed in primary MiC source",
    ),
    *_build_updates(
        "gr_cash_rebate",
        cast_qualifies=True,
        note_q="GR Cash Rebate: qualifying Greek expenditure confirmed (Enterprise Greece/EKOME)",
        note_d="GR Cash Rebate: does not qualify under EKOME eligible expenditure rules",
        note_unk="GR Cash Rebate: completion bond eligibility not confirmed in primary EKOME source",
    ),
]

_UPSERT_SQL = sa.text("""
    UPDATE program_spend_treatments pst
       SET qualifies      = :qualifies,
           treatment_notes = :note,
           updated_at     = :now
      FROM incentive_programs ip
     WHERE ip.id        = pst.program_id
       AND ip.slug      = :slug
       AND pst.labor_type = :lt
""")

_RESET_SQL = sa.text("""
    UPDATE program_spend_treatments pst
       SET qualifies      = NULL,
           treatment_notes = NULL,
           updated_at     = :now
      FROM incentive_programs ip
     WHERE ip.id        = pst.program_id
       AND ip.slug      = :slug
""")


def upgrade() -> None:
    conn = op.get_bind()
    for row in _UPDATES:
        conn.execute(_UPSERT_SQL, row)


def downgrade() -> None:
    conn = op.get_bind()
    for slug in ("uk_avec", "ie_section_481", "fr_trip", "it_tax_credit_foreign", "gr_cash_rebate"):
        conn.execute(_RESET_SQL, {"slug": slug, "now": NOW})
