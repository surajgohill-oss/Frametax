"""0018 — ProgramSpendTreatment for Louisiana, British Columbia, Quebec.

These three programs already have ProgramAdminDetails (seeded in 0016).
This migration adds the 21-category spend treatment matrix for each.

Louisiana: ATL qualifies (unique US state alongside GA).
BC PSTC: ATL writer/director/producer UNKNOWN (service credit, primary source
  confirmation pending from Creative BC); cast QUALIFIES as labor in BC.
QC SODEC: ATL writer/director/producer UNKNOWN (SODEC CTVM documentation
  pending); cast QUALIFIES; BTL/production QUALIFIES.

Revision ID: 0018
Revises: 0017
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0018-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_CUSTOMS_UNKNOWN = (
    "Customs/import duties treatment unconfirmed from primary source."
)

# (slug, labor_type, qualifies, treatment_notes, confidence_tier)
_TREATMENTS: list[tuple[str, str, bool | None, str, str]] = [

    # -----------------------------------------------------------------------
    # Louisiana (la_film_production)
    # LA Entertainment Industry Tax Credit explicitly qualifies ATL labor.
    # This is one of only two US states (alongside GA) where ATL qualifies.
    # Source: Louisiana LED film office / lafilm.org programme documentation.
    # -----------------------------------------------------------------------
    ("la_film_production", "atl_writer",          True,  "ATL writer fees incurred in Louisiana explicitly qualify under LA Entertainment Industry Tax Credit. LA is one of only two US states (with GA) where ATL labor qualifies.", "PARSED"),
    ("la_film_production", "atl_director",        True,  "ATL director fees incurred in Louisiana explicitly qualify under LA Entertainment Industry Tax Credit.", "PARSED"),
    ("la_film_production", "atl_producer",        True,  "ATL producer fees incurred in Louisiana explicitly qualify under LA Entertainment Industry Tax Credit.", "PARSED"),
    ("la_film_production", "atl_cast_principal",  True,  "Principal cast fees incurred in Louisiana qualify under LA Entertainment Industry Tax Credit.", "PARSED"),
    ("la_film_production", "atl_cast_supporting", True,  "Supporting cast fees incurred in Louisiana qualify under LA Entertainment Industry Tax Credit.", "PARSED"),
    ("la_film_production", "btl_crew_resident",   True,  "Louisiana resident BTL crew qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "btl_crew_non_resident", True, "Non-resident BTL crew working in Louisiana qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Louisiana qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "travel",              True,  "Louisiana travel expenditure qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "accommodation_lodging", True, "Louisiana accommodation qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "per_diem",            True,  "Per diem costs incurred in Louisiana qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "insurance",           True,  "Production insurance sourced in Louisiana qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "completion_bond",     True,  "Completion bond costs qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("la_film_production", "marine_vessel",       True,  "Marine vessel hire in Louisiana qualifies under LA film tax credit. Louisiana bayou/water productions are a primary use case.", "PARSED"),
    ("la_film_production", "vfx",                 True,  "Louisiana VFX expenditure qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "post_production",     True,  "Louisiana post-production qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "animation",           True,  "Louisiana animation qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "music",               True,  "Louisiana music expenditure qualifies under LA film tax credit.", "PARSED"),
    ("la_film_production", "legal_accounting",    True,  "Louisiana legal and accounting costs qualify under LA film tax credit.", "PARSED"),
    ("la_film_production", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # British Columbia (bc_pstc)
    # BC Production Services Tax Credit — foreign production service credit.
    # ATL writer/director/producer: UNKNOWN pending Creative BC documentation
    # confirmation. Cast qualifies as labor incurred in BC. BTL/production
    # categories confirmed qualifying. BC is major VFX/animation hub.
    # -----------------------------------------------------------------------
    ("bc_pstc", "atl_writer",          None,  "ATL writer treatment under BC PSTC unconfirmed from Creative BC primary source. PSTC covers BC labor costs broadly but ATL creative fee eligibility requires confirmation.", "DISCOVERY"),
    ("bc_pstc", "atl_director",        None,  "ATL director treatment under BC PSTC unconfirmed from Creative BC primary source.", "DISCOVERY"),
    ("bc_pstc", "atl_producer",        None,  "ATL producer treatment under BC PSTC unconfirmed from Creative BC primary source.", "DISCOVERY"),
    ("bc_pstc", "atl_cast_principal",  True,  "Principal cast fees incurred in BC qualify as production labor under BC PSTC for foreign productions.", "PARSED"),
    ("bc_pstc", "atl_cast_supporting", True,  "Supporting cast fees incurred in BC qualify as production labor under BC PSTC.", "PARSED"),
    ("bc_pstc", "btl_crew_resident",   True,  "BC resident BTL crew are the primary qualifying category under BC PSTC.", "PARSED"),
    ("bc_pstc", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in BC qualify under BC PSTC (service credit for foreign productions).", "PARSED"),
    ("bc_pstc", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in BC qualify under BC PSTC.", "PARSED"),
    ("bc_pstc", "travel",              True,  "BC travel expenditure qualifies under BC PSTC.", "PARSED"),
    ("bc_pstc", "accommodation_lodging", True, "BC accommodation qualifies under BC PSTC.", "PARSED"),
    ("bc_pstc", "per_diem",            True,  "Per diem costs incurred in BC qualify under BC PSTC.", "PARSED"),
    ("bc_pstc", "insurance",           True,  "BC-sourced production insurance qualifies under BC PSTC.", "PARSED"),
    ("bc_pstc", "completion_bond",     True,  "Completion bond costs qualify under BC PSTC.", "PARSED"),
    ("bc_pstc", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("bc_pstc", "marine_vessel",       True,  "Marine vessel hire in BC qualifies under BC PSTC. BC coastal/water locations are a significant production asset.", "PARSED"),
    ("bc_pstc", "vfx",                 True,  "BC VFX expenditure qualifies under BC PSTC. BC has one of the largest VFX sectors in North America.", "PARSED"),
    ("bc_pstc", "post_production",     True,  "BC post-production qualifies under BC PSTC.", "PARSED"),
    ("bc_pstc", "animation",           True,  "BC animation qualifies under BC PSTC. BC is a major North American animation hub.", "PARSED"),
    ("bc_pstc", "music",               True,  "BC music expenditure qualifies under BC PSTC.", "PARSED"),
    ("bc_pstc", "legal_accounting",    True,  "BC legal and accounting costs qualify under BC PSTC.", "PARSED"),
    ("bc_pstc", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # Quebec (qc_film_production)
    # Quebec Production Services Tax Credit (SODEC / CTVM) — foreign
    # production credit on Quebec-incurred expenditure. ATL writer/director/
    # producer UNKNOWN pending SODEC documentation; cast qualifies as Quebec
    # labor. Strong post/animation/VFX sector in Montreal.
    # -----------------------------------------------------------------------
    ("qc_film_production", "atl_writer",          None,  "ATL writer treatment under QC SODEC production credit unconfirmed from SODEC primary source. CTVM documentation pending review.", "DISCOVERY"),
    ("qc_film_production", "atl_director",        None,  "ATL director treatment under QC SODEC production credit unconfirmed from primary source.", "DISCOVERY"),
    ("qc_film_production", "atl_producer",        None,  "ATL producer treatment under QC SODEC production credit unconfirmed from primary source.", "DISCOVERY"),
    ("qc_film_production", "atl_cast_principal",  True,  "Principal cast fees incurred in Quebec qualify as production labor under QC SODEC credit.", "PARSED"),
    ("qc_film_production", "atl_cast_supporting", True,  "Supporting cast fees incurred in Quebec qualify as production labor under QC SODEC credit.", "PARSED"),
    ("qc_film_production", "btl_crew_resident",   True,  "Quebec resident BTL crew qualify under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Quebec qualify under QC SODEC credit (foreign production service credit).", "PARSED"),
    ("qc_film_production", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Quebec qualify under QC SODEC credit.", "PARSED"),
    ("qc_film_production", "travel",              True,  "Quebec travel expenditure qualifies under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "accommodation_lodging", True, "Quebec accommodation qualifies under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "per_diem",            True,  "Per diem costs incurred in Quebec qualify under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "insurance",           True,  "Quebec-sourced production insurance qualifies under QC SODEC credit.", "PARSED"),
    ("qc_film_production", "completion_bond",     True,  "Completion bond costs qualify under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("qc_film_production", "marine_vessel",       True,  "Marine vessel hire in Quebec qualifies under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "vfx",                 True,  "Quebec VFX expenditure qualifies under QC SODEC production credit. Montreal is a major VFX hub.", "PARSED"),
    ("qc_film_production", "post_production",     True,  "Quebec post-production qualifies under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "animation",           True,  "Quebec animation qualifies under QC SODEC production credit. Montreal has a strong animation industry.", "PARSED"),
    ("qc_film_production", "music",               True,  "Quebec music expenditure qualifies under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "legal_accounting",    True,  "Quebec legal and accounting costs qualify under QC SODEC production credit.", "PARSED"),
    ("qc_film_production", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),
]


def upgrade() -> None:
    conn = op.get_bind()

    for slug, labor_type, qualifies, treatment_notes, tier in _TREATMENTS:
        conn.execute(
            sa.text("""
                INSERT INTO program_spend_treatments (
                    id, program_id, labor_type,
                    qualifies, cap_pct, cap_amount_local,
                    treatment_notes, confidence_tier,
                    created_at, updated_at
                )
                SELECT
                    :id, p.id, :labor_type,
                    :qualifies, NULL, NULL,
                    :notes, :tier,
                    :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_spend_treatments t
                      WHERE t.program_id = p.id AND t.labor_type = :labor_type ::varchar
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"treatment:{slug}:{labor_type}"),
                "slug": slug,
                "labor_type": labor_type,
                "qualifies": qualifies,
                "notes": treatment_notes,
                "tier": tier,
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    for slug, labor_type, *_ in _TREATMENTS:
        conn.execute(
            sa.text("DELETE FROM program_spend_treatments WHERE id = :id"),
            {"id": _uid(f"treatment:{slug}:{labor_type}")},
        )
