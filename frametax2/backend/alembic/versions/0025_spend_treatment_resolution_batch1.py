"""0025 — SpendTreatment resolution batch 1: source-backed UNKNOWN resolution.

Resolves high-value UNKNOWN spend treatment fields confirmed from official
primary sources. Only fields with direct source evidence are updated.

Programs updated:
  ny_state_film   — ATL writer/director/producer/cast: QUALIFIES
                    Source: ESD NY Film Tax Credit Guidelines (ATL explicitly
                    included; director, writers, actors, composers, 2 producers
                    eligible; $500K/individual cap; ATL ≤ 40% of other QC)

  mu_edb_incentive — ATL (all 5), BTL crew (all 3), travel, accommodation,
                    per_diem, marine_vessel: QUALIFIES
                    Source: EDB Mauritius Film Rebate Scheme; MCCI documentation
                    (QPE = "transport, accommodation, manpower, catering and
                    the hiring of equipment and premises in Mauritius")

  on_opstc        — ATL writer/director/producer: QUALIFIES
                    Source: Ontario Creates OPSTC guidelines (eligible
                    expenditures paid to Ontario-based companies/individuals;
                    no ATL carve-out; consistent with atl_cast QUALIFIES)

  on_ofttc        — btl_crew_non_resident, btl_crew_foreign: DOES NOT QUALIFY
                    Source: Ontario Creates OFTTC guidelines; Ontario Tax Act
                    ("eligible Ontario labour expenditures... paid for the
                    services of individuals who were resident in Ontario")

  qc_film_production — ATL writer/director/producer: QUALIFIES
                    Source: SODEC Refundable Tax Credit for Film Production
                    Services (Sept 2025) — producer, author, scriptwriter,
                    director explicitly listed as qualified positions when
                    Quebec-resident

  bc_pstc         — ATL writer: QUALIFIES
                    Source: BC Budget 2024 announcement (news.gov.bc.ca 2024FIN0049)
                    — "PSTC supports productions to hire B.C.-based scriptwriters"

Fields NOT updated (still UNKNOWN):
  - ny_state_film: customs_imports (not confirmed)
  - mu_edb_incentive: vfx, post_production, animation, music, insurance,
    completion_bond, legal_accounting, customs_imports (not in QPE definition)
  - on_opstc: customs_imports
  - on_ofttc: customs_imports
  - qc_film_production: customs_imports
  - bc_pstc: atl_director, atl_producer (not confirmed)
  - bc_pstc: customs_imports

Revision ID: 0025
Revises: 0024
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Update data: (slug, labor_type, qualifies, treatment_notes, confidence_tier)
# qualifies: True=QUALIFIES, False=DOES_NOT_QUALIFY
# ---------------------------------------------------------------------------

_NY_ATL_NOTE = (
    "ATL {pos} fees qualify under NY State Film Tax Credit (production). "
    "Director, writers, actors, composers and 2 producers (exec + line) "
    "are explicitly listed as qualified ATL personnel. "
    "Capped at USD $500,000 per individual; total ATL salaries cannot "
    "exceed 40% of all other qualified costs. "
    "Source: Empire State Development Film Tax Credit Guidelines."
)

_MU_MANPOWER_NOTE = (
    "Manpower costs incurred in Mauritius are explicitly listed as "
    "Qualifying Production Expenditure (QPE) under the Mauritius EDB Film "
    "Rebate Scheme. ATL manpower qualifies; note that when ATL costs exceed "
    "BTL costs, a 40% cap applies to the ATL expenditure portion. "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)

_MU_TRANSPORT_NOTE = (
    "Transport expenditure (including marine/vessel) incurred in Mauritius is "
    "explicitly listed as Qualifying Production Expenditure (QPE) under the "
    "Mauritius EDB Film Rebate Scheme. "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)

_MU_ACCOMMODATION_NOTE = (
    "Accommodation incurred in Mauritius is explicitly listed as Qualifying "
    "Production Expenditure (QPE) under the Mauritius EDB Film Rebate Scheme. "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)

_MU_CATERING_NOTE = (
    "Catering/per diem incurred in Mauritius is explicitly listed as "
    "Qualifying Production Expenditure (QPE) under the Mauritius EDB Film "
    "Rebate Scheme. Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)

_OPSTC_ATL_NOTE = (
    "ATL {pos} fees qualify under Ontario OPSTC when incurred with Ontario-based "
    "companies or Ontario-resident individuals. OPSTC eligible expenditures "
    "are 'paid to companies and partnerships which have a permanent establishment "
    "in Ontario and to Ontario-based individuals' — no ATL carve-out exists; "
    "consistent with existing atl_cast QUALIFIES treatment. "
    "Source: Ontario Creates OPSTC guidelines."
)

_OFTTC_NON_RESIDENT_NOTE = (
    "Non-Ontario-resident BTL crew do not qualify under OFTTC. The OFTTC is "
    "based on 'eligible Ontario labour expenditures' = salaries paid to "
    "individuals who were resident in Ontario at the end of the calendar year "
    "prior to the commencement of principal photography. "
    "Source: Ontario Creates OFTTC guidelines; Ontario Tax Act."
)

_QC_ATL_NOTE = (
    "ATL {pos} fees qualify under the Quebec SODEC Refundable Tax Credit for "
    "Film Production Services when the individual is a Quebec resident. "
    "SODEC explicitly lists 'producer, author, scriptwriter, director' as "
    "qualified positions when the individual qualifies as a Quebec resident "
    "under the Quebec Taxation Act. "
    "Source: SODEC Refundable Tax Credit for Film Production Services (Sept 2025)."
)

_BC_WRITER_NOTE = (
    "B.C.-based scriptwriters are explicitly supported under BC PSTC per "
    "BC Budget 2024 announcement. PSTC covers accredited B.C. labour "
    "expenditures; scriptwriter/writer fees from B.C.-based individuals "
    "qualify. "
    "Source: BC Government Budget 2024 announcement (news.gov.bc.ca 2024FIN0049)."
)


_UPDATES: list[tuple[str, str, bool, str, str]] = [
    # -----------------------------------------------------------------------
    # NY State Film Tax Credit — ATL all 5 categories
    # -----------------------------------------------------------------------
    ("ny_state_film", "atl_writer",          True, _NY_ATL_NOTE.format(pos="writer"),           "PARSED"),
    ("ny_state_film", "atl_director",        True, _NY_ATL_NOTE.format(pos="director"),         "PARSED"),
    ("ny_state_film", "atl_producer",        True, _NY_ATL_NOTE.format(pos="producer (exec + line producer)"), "PARSED"),
    ("ny_state_film", "atl_cast_principal",  True, _NY_ATL_NOTE.format(pos="principal cast (actors)"), "PARSED"),
    ("ny_state_film", "atl_cast_supporting", True, _NY_ATL_NOTE.format(pos="supporting cast (actors)"), "PARSED"),

    # -----------------------------------------------------------------------
    # Mauritius EDB Film Rebate Scheme — QPE: manpower, transport, accommodation, catering
    # -----------------------------------------------------------------------
    ("mu_edb_incentive", "atl_writer",          True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "atl_director",        True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "atl_producer",        True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "atl_cast_principal",  True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "atl_cast_supporting", True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "btl_crew_resident",   True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "btl_crew_non_resident", True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "btl_crew_foreign",    True, _MU_MANPOWER_NOTE, "PARSED"),
    ("mu_edb_incentive", "travel",              True, _MU_TRANSPORT_NOTE, "PARSED"),
    ("mu_edb_incentive", "accommodation_lodging", True, _MU_ACCOMMODATION_NOTE, "PARSED"),
    ("mu_edb_incentive", "per_diem",            True, _MU_CATERING_NOTE,  "PARSED"),
    ("mu_edb_incentive", "marine_vessel",       True, _MU_TRANSPORT_NOTE, "PARSED"),

    # -----------------------------------------------------------------------
    # Ontario OPSTC — ATL writer/director/producer: QUALIFIES
    # (consistent with existing atl_cast QUALIFIES; no ATL carve-out in statute)
    # -----------------------------------------------------------------------
    ("on_opstc", "atl_writer",   True, _OPSTC_ATL_NOTE.format(pos="writer"),   "PARSED"),
    ("on_opstc", "atl_director", True, _OPSTC_ATL_NOTE.format(pos="director"), "PARSED"),
    ("on_opstc", "atl_producer", True, _OPSTC_ATL_NOTE.format(pos="producer"), "PARSED"),

    # -----------------------------------------------------------------------
    # Ontario OFTTC — non-resident and foreign BTL crew: DOES NOT QUALIFY
    # -----------------------------------------------------------------------
    ("on_ofttc", "btl_crew_non_resident", False, _OFTTC_NON_RESIDENT_NOTE, "PARSED"),
    ("on_ofttc", "btl_crew_foreign",      False, _OFTTC_NON_RESIDENT_NOTE, "PARSED"),

    # -----------------------------------------------------------------------
    # Quebec SODEC PSTC — ATL writer/director/producer: QUALIFIES (QC resident)
    # -----------------------------------------------------------------------
    ("qc_film_production", "atl_writer",   True, _QC_ATL_NOTE.format(pos="writer/scriptwriter/author"), "PARSED"),
    ("qc_film_production", "atl_director", True, _QC_ATL_NOTE.format(pos="director"),                    "PARSED"),
    ("qc_film_production", "atl_producer", True, _QC_ATL_NOTE.format(pos="producer"),                    "PARSED"),

    # -----------------------------------------------------------------------
    # BC PSTC — ATL writer: QUALIFIES (B.C.-based scriptwriters explicitly)
    # -----------------------------------------------------------------------
    ("bc_pstc", "atl_writer", True, _BC_WRITER_NOTE, "PARSED"),
]


def upgrade() -> None:
    conn = op.get_bind()

    for slug, labor_type, qualifies, notes, tier in _UPDATES:
        conn.execute(
            sa.text("""
                UPDATE program_spend_treatments
                SET qualifies = :qualifies,
                    treatment_notes = :notes,
                    confidence_tier = :tier,
                    updated_at = :now
                WHERE program_id = (
                    SELECT id FROM incentive_programs WHERE slug = :slug LIMIT 1
                )
                  AND labor_type = :labor_type
            """),
            {
                "slug": slug,
                "labor_type": labor_type,
                "qualifies": qualifies,
                "notes": notes,
                "tier": tier,
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Revert ATL and non-resident/foreign changes to UNKNOWN (None)
    _REVERT: list[tuple[str, str]] = [
        ("ny_state_film", "atl_writer"), ("ny_state_film", "atl_director"),
        ("ny_state_film", "atl_producer"), ("ny_state_film", "atl_cast_principal"),
        ("ny_state_film", "atl_cast_supporting"),
        ("mu_edb_incentive", "atl_writer"), ("mu_edb_incentive", "atl_director"),
        ("mu_edb_incentive", "atl_producer"), ("mu_edb_incentive", "atl_cast_principal"),
        ("mu_edb_incentive", "atl_cast_supporting"), ("mu_edb_incentive", "btl_crew_resident"),
        ("mu_edb_incentive", "btl_crew_non_resident"), ("mu_edb_incentive", "btl_crew_foreign"),
        ("mu_edb_incentive", "travel"), ("mu_edb_incentive", "accommodation_lodging"),
        ("mu_edb_incentive", "per_diem"), ("mu_edb_incentive", "marine_vessel"),
        ("on_opstc", "atl_writer"), ("on_opstc", "atl_director"), ("on_opstc", "atl_producer"),
        ("on_ofttc", "btl_crew_non_resident"), ("on_ofttc", "btl_crew_foreign"),
        ("qc_film_production", "atl_writer"), ("qc_film_production", "atl_director"),
        ("qc_film_production", "atl_producer"),
        ("bc_pstc", "atl_writer"),
    ]
    for slug, labor_type in _REVERT:
        conn.execute(
            sa.text("""
                UPDATE program_spend_treatments
                SET qualifies = NULL, confidence_tier = 'DISCOVERY', updated_at = :now
                WHERE program_id = (
                    SELECT id FROM incentive_programs WHERE slug = :slug LIMIT 1
                )
                  AND labor_type = :labor_type
            """),
            {"slug": slug, "labor_type": labor_type, "now": NOW},
        )
