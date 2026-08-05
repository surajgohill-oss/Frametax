"""0017 — ProgramSpendTreatment population for 8 Tier-1 programs.

Captures per-category spend treatment (QUALIFIES / DOES_NOT_QUALIFY / UNKNOWN)
for: UK AVEC, IE S481, GA EIIA, CA Film 3.0, MT MFC, GR EKOME,
     ON OPSTC, NY State Film.

qualifies: True=QUALIFIES, False=DOES_NOT_QUALIFY, None=UNKNOWN

Revision ID: 0017
Revises: 0016
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0017-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# Treatment data: (slug, labor_type, qualifies, treatment_notes, confidence_tier)
# qualifies: True=QUALIFIES, False=DOES_NOT_QUALIFY, None=UNKNOWN
# ---------------------------------------------------------------------------

# Shared notes
_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_CUSTOMS_UNKNOWN = (
    "Customs/import duties treatment unconfirmed from primary source."
)

_TREATMENTS: list[tuple[str, str, bool | None, str, str]] = [

    # -----------------------------------------------------------------------
    # UK AVEC — geography-based; all UK-incurred spend qualifies regardless
    # of nationality. Nationality of crew/cast is irrelevant.
    # -----------------------------------------------------------------------
    ("uk_avec", "atl_writer",          True,  "ATL writer fees for UK-incurred work qualify under AVEC (geography-based test).", "PARSED"),
    ("uk_avec", "atl_director",        True,  "ATL director fees for UK-incurred work qualify under AVEC.", "PARSED"),
    ("uk_avec", "atl_producer",        True,  "ATL producer fees for UK-incurred work qualify under AVEC.", "PARSED"),
    ("uk_avec", "atl_cast_principal",  True,  "Principal cast fees for UK-incurred work qualify under AVEC.", "PARSED"),
    ("uk_avec", "atl_cast_supporting", True,  "Supporting cast fees for UK-incurred work qualify under AVEC.", "PARSED"),
    ("uk_avec", "btl_crew_resident",   True,  "UK resident BTL crew qualify under AVEC.", "PARSED"),
    ("uk_avec", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in UK qualify; nationality irrelevant under AVEC.", "PARSED"),
    ("uk_avec", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in UK qualify; geography-based test.", "PARSED"),
    ("uk_avec", "travel",              True,  "UK travel expenditure qualifies under AVEC.", "PARSED"),
    ("uk_avec", "accommodation_lodging", True, "UK accommodation and lodging qualifies under AVEC.", "PARSED"),
    ("uk_avec", "per_diem",            True,  "Per diem costs incurred in UK qualify under AVEC.", "PARSED"),
    ("uk_avec", "insurance",           True,  "UK-sourced production insurance qualifies under AVEC.", "PARSED"),
    ("uk_avec", "completion_bond",     True,  "Completion bond costs qualify under AVEC.", "PARSED"),
    ("uk_avec", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("uk_avec", "marine_vessel",       True,  "Marine vessel hire in UK qualifies under AVEC.", "PARSED"),
    ("uk_avec", "vfx",                 True,  "UK VFX expenditure qualifies under AVEC.", "PARSED"),
    ("uk_avec", "post_production",     True,  "UK post-production expenditure qualifies under AVEC.", "PARSED"),
    ("uk_avec", "animation",           True,  "UK animation expenditure qualifies under AVEC.", "PARSED"),
    ("uk_avec", "music",               True,  "UK music expenditure qualifies under AVEC.", "PARSED"),
    ("uk_avec", "legal_accounting",    True,  "UK legal and accounting costs qualify under AVEC.", "PARSED"),
    ("uk_avec", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # IE Section 481 — geography-based; all qualifying Irish spend qualifies
    # -----------------------------------------------------------------------
    ("ie_section_481", "atl_writer",          True,  "ATL writer fees for Irish-incurred work qualify under S481.", "PARSED"),
    ("ie_section_481", "atl_director",        True,  "ATL director fees for Irish-incurred work qualify under S481.", "PARSED"),
    ("ie_section_481", "atl_producer",        True,  "ATL producer fees for Irish-incurred work qualify under S481.", "PARSED"),
    ("ie_section_481", "atl_cast_principal",  True,  "Principal cast fees for Irish-incurred work qualify under S481.", "PARSED"),
    ("ie_section_481", "atl_cast_supporting", True,  "Supporting cast fees for Irish-incurred work qualify under S481.", "PARSED"),
    ("ie_section_481", "btl_crew_resident",   True,  "Irish resident BTL crew qualify under S481.", "PARSED"),
    ("ie_section_481", "btl_crew_non_resident", True, "Non-resident BTL crew working in Ireland qualify; geography-based.", "PARSED"),
    ("ie_section_481", "btl_crew_foreign",    True,  "Foreign BTL crew working in Ireland qualify under S481.", "PARSED"),
    ("ie_section_481", "travel",              True,  "Irish travel expenditure qualifies under S481.", "PARSED"),
    ("ie_section_481", "accommodation_lodging", True, "Irish accommodation qualifies under S481.", "PARSED"),
    ("ie_section_481", "per_diem",            True,  "Irish per diem costs qualify under S481.", "PARSED"),
    ("ie_section_481", "insurance",           True,  "Irish-sourced production insurance qualifies under S481.", "PARSED"),
    ("ie_section_481", "completion_bond",     True,  "Completion bond costs qualify under S481.", "PARSED"),
    ("ie_section_481", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("ie_section_481", "marine_vessel",       True,  "Marine vessel hire in Ireland qualifies under S481.", "PARSED"),
    ("ie_section_481", "vfx",                 True,  "Irish VFX expenditure qualifies under S481.", "PARSED"),
    ("ie_section_481", "post_production",     True,  "Irish post-production qualifies under S481.", "PARSED"),
    ("ie_section_481", "animation",           True,  "Irish animation qualifies under S481.", "PARSED"),
    ("ie_section_481", "music",               True,  "Irish music expenditure qualifies under S481.", "PARSED"),
    ("ie_section_481", "legal_accounting",    True,  "Irish legal and accounting costs qualify under S481.", "PARSED"),
    ("ie_section_481", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # GA EIIA — ATL explicitly eligible; unique among US state credits.
    # All Georgia qualifying expenditures qualify regardless of labor category.
    # -----------------------------------------------------------------------
    ("georgia_eiia", "atl_writer",          True,  "GA EIIA explicitly qualifies ATL writer fees incurred in Georgia. Unique among US state credits.", "PARSED"),
    ("georgia_eiia", "atl_director",        True,  "GA EIIA explicitly qualifies ATL director fees incurred in Georgia.", "PARSED"),
    ("georgia_eiia", "atl_producer",        True,  "GA EIIA explicitly qualifies ATL producer fees incurred in Georgia.", "PARSED"),
    ("georgia_eiia", "atl_cast_principal",  True,  "GA EIIA explicitly qualifies principal cast fees incurred in Georgia.", "PARSED"),
    ("georgia_eiia", "atl_cast_supporting", True,  "GA EIIA explicitly qualifies supporting cast fees incurred in Georgia.", "PARSED"),
    ("georgia_eiia", "btl_crew_resident",   True,  "Georgia resident BTL crew qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "btl_crew_non_resident", True, "Non-resident BTL crew working in Georgia qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "btl_crew_foreign",    True,  "Foreign BTL crew working in Georgia qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "travel",              True,  "Georgia travel expenditure qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "accommodation_lodging", True, "Georgia accommodation qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "per_diem",            True,  "Per diem costs incurred in Georgia qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "insurance",           True,  "Production insurance sourced in Georgia qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "completion_bond",     True,  "Completion bond costs qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("georgia_eiia", "marine_vessel",       True,  "Marine vessel hire in Georgia qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "vfx",                 True,  "Georgia VFX expenditure qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "post_production",     True,  "Georgia post-production qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "animation",           True,  "Georgia animation qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "music",               True,  "Georgia music expenditure qualifies under GA EIIA.", "PARSED"),
    ("georgia_eiia", "legal_accounting",    True,  "Georgia legal and accounting costs qualify under GA EIIA.", "PARSED"),
    ("georgia_eiia", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # CA Film 3.0 (non-indie standard track) — ATL does NOT qualify.
    # BTL and production expenditures incurred in California qualify.
    # The CA Film Commission credit excludes above-the-line costs for
    # non-independent productions on the standard 20–25% base credit.
    # -----------------------------------------------------------------------
    ("ca_film_30", "atl_writer",          False, "CA Film 3.0 (standard track) excludes ATL writer fees. ATL does not qualify for non-independent productions.", "PARSED"),
    ("ca_film_30", "atl_director",        False, "CA Film 3.0 (standard track) excludes ATL director fees.", "PARSED"),
    ("ca_film_30", "atl_producer",        False, "CA Film 3.0 (standard track) excludes ATL producer fees.", "PARSED"),
    ("ca_film_30", "atl_cast_principal",  False, "CA Film 3.0 (standard track) excludes principal cast fees. Cast salaries are ATL and not qualifying spend.", "PARSED"),
    ("ca_film_30", "atl_cast_supporting", False, "CA Film 3.0 (standard track) excludes supporting cast fees.", "PARSED"),
    ("ca_film_30", "btl_crew_resident",   True,  "CA resident BTL crew are the primary qualifying category under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in California qualify under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in California qualify under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "travel",              True,  "California travel expenditure qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "accommodation_lodging", True, "California accommodation qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "per_diem",            True,  "Per diem costs incurred in California qualify under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "insurance",           True,  "California-sourced production insurance qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "completion_bond",     True,  "Completion bond costs qualify under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("ca_film_30", "marine_vessel",       True,  "Marine vessel hire in California qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "vfx",                 True,  "California VFX expenditure qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "post_production",     True,  "California post-production qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "animation",           True,  "California animation qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "music",               True,  "California music expenditure qualifies under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "legal_accounting",    True,  "California legal and accounting costs qualify under CA Film 3.0.", "PARSED"),
    ("ca_film_30", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # MT MFC Cash Rebate — ATL explicitly qualifies per MFC programme rules.
    # Marine vessel explicitly qualifies per MFC documentation.
    # -----------------------------------------------------------------------
    ("mt_mfc_rebate", "atl_writer",          True,  "ATL writer fees for Malta-incurred work explicitly qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "atl_director",        True,  "ATL director fees for Malta-incurred work explicitly qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "atl_producer",        True,  "ATL producer fees for Malta-incurred work explicitly qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "atl_cast_principal",  True,  "Principal cast fees for Malta-incurred work qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "atl_cast_supporting", True,  "Supporting cast fees for Malta-incurred work qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "btl_crew_resident",   True,  "Maltese resident BTL crew qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "btl_crew_non_resident", True, "Non-resident BTL crew working in Malta qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "btl_crew_foreign",    True,  "Foreign BTL crew working in Malta qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "travel",              True,  "Malta travel expenditure qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "accommodation_lodging", True, "Malta accommodation qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "per_diem",            True,  "Per diem costs incurred in Malta qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "insurance",           True,  "Malta-sourced production insurance qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "completion_bond",     True,  "Completion bond costs qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("mt_mfc_rebate", "marine_vessel",       True,  "Marine vessel hire explicitly qualifies under MFC rebate. Malta is a primary marine production location.", "PARSED"),
    ("mt_mfc_rebate", "vfx",                 True,  "Malta VFX expenditure qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "post_production",     True,  "Malta post-production qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "animation",           True,  "Malta animation qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "music",               True,  "Malta music expenditure qualifies under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "legal_accounting",    True,  "Malta legal and accounting costs qualify under MFC rebate.", "PARSED"),
    ("mt_mfc_rebate", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # GR EKOME Cash Rebate — ATL qualifies; marine explicitly qualifies.
    # Greece is a major marine location — vessel treatment explicitly confirmed.
    # -----------------------------------------------------------------------
    ("gr_cash_rebate", "atl_writer",          True,  "ATL writer fees for Greek-incurred work qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "atl_director",        True,  "ATL director fees for Greek-incurred work qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "atl_producer",        True,  "ATL producer fees for Greek-incurred work qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "atl_cast_principal",  True,  "Principal cast fees for Greek-incurred work qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "atl_cast_supporting", True,  "Supporting cast fees for Greek-incurred work qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "btl_crew_resident",   True,  "Greek resident BTL crew qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "btl_crew_non_resident", True, "Non-resident BTL crew working in Greece qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "btl_crew_foreign",    True,  "Foreign BTL crew working in Greece qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "travel",              True,  "Greek travel expenditure qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "accommodation_lodging", True, "Greek accommodation qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "per_diem",            True,  "Per diem costs incurred in Greece qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "insurance",           True,  "Greek-sourced production insurance qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "completion_bond",     True,  "Completion bond costs qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("gr_cash_rebate", "marine_vessel",       True,  "Marine vessel hire explicitly qualifies under EKOME rebate. Greece (Aegean/Ionian waters) is a primary marine production location.", "PARSED"),
    ("gr_cash_rebate", "vfx",                 True,  "Greek VFX expenditure qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "post_production",     True,  "Greek post-production qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "animation",           True,  "Greek animation qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "music",               True,  "Greek music expenditure qualifies under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "legal_accounting",    True,  "Greek legal and accounting costs qualify under EKOME rebate.", "PARSED"),
    ("gr_cash_rebate", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # ON OPSTC — Ontario Production Services Tax Credit for foreign productions.
    # Service credit — BTL/production categories qualify. ATL treatment unknown
    # (OPSTC rules primarily target BTL service spend in Ontario).
    # -----------------------------------------------------------------------
    ("on_opstc", "atl_writer",          None,  "ATL writer treatment under OPSTC unconfirmed. OPSTC primarily targets BTL service spend; ATL treatment requires confirmation from Ontario Creates.", "DISCOVERY"),
    ("on_opstc", "atl_director",        None,  "ATL director treatment under OPSTC unconfirmed from primary source.", "DISCOVERY"),
    ("on_opstc", "atl_producer",        None,  "ATL producer treatment under OPSTC unconfirmed from primary source.", "DISCOVERY"),
    ("on_opstc", "atl_cast_principal",  True,  "Principal cast fees incurred in Ontario qualify as production expenditure under OPSTC for foreign productions.", "PARSED"),
    ("on_opstc", "atl_cast_supporting", True,  "Supporting cast fees incurred in Ontario qualify as production expenditure under OPSTC.", "PARSED"),
    ("on_opstc", "btl_crew_resident",   True,  "Ontario resident BTL crew are the primary qualifying category under OPSTC.", "PARSED"),
    ("on_opstc", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Ontario qualify under OPSTC (service credit).", "PARSED"),
    ("on_opstc", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Ontario qualify under OPSTC.", "PARSED"),
    ("on_opstc", "travel",              True,  "Ontario travel expenditure qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "accommodation_lodging", True, "Ontario accommodation qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "per_diem",            True,  "Per diem costs incurred in Ontario qualify under OPSTC.", "PARSED"),
    ("on_opstc", "insurance",           True,  "Ontario-sourced production insurance qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "completion_bond",     True,  "Completion bond costs qualify under OPSTC.", "PARSED"),
    ("on_opstc", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("on_opstc", "marine_vessel",       True,  "Marine vessel hire in Ontario qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "vfx",                 True,  "Ontario VFX expenditure qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "post_production",     True,  "Ontario post-production qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "animation",           True,  "Ontario animation qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "music",               True,  "Ontario music expenditure qualifies under OPSTC.", "PARSED"),
    ("on_opstc", "legal_accounting",    True,  "Ontario legal and accounting costs qualify under OPSTC.", "PARSED"),
    ("on_opstc", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # NY State Film Tax Credit — BTL strongly supported; ATL treatment UNKNOWN.
    # Program focuses on NY production expenditure but ATL eligibility
    # not confirmed from primary ESD source documentation.
    # -----------------------------------------------------------------------
    ("ny_state_film", "atl_writer",          None,  "ATL writer treatment under NY State Film Tax Credit not confirmed from ESD primary source. Likely excluded but requires verification.", "DISCOVERY"),
    ("ny_state_film", "atl_director",        None,  "ATL director treatment under NY State Film Tax Credit not confirmed from primary source.", "DISCOVERY"),
    ("ny_state_film", "atl_producer",        None,  "ATL producer treatment under NY State Film Tax Credit not confirmed from primary source.", "DISCOVERY"),
    ("ny_state_film", "atl_cast_principal",  None,  "Principal cast treatment under NY State Film Tax Credit not confirmed. May be excluded as ATL; requires ESD verification.", "DISCOVERY"),
    ("ny_state_film", "atl_cast_supporting", None,  "Supporting cast treatment under NY State Film Tax Credit not confirmed from primary source.", "DISCOVERY"),
    ("ny_state_film", "btl_crew_resident",   True,  "NY resident BTL crew are the primary qualifying category under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in New York qualify under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in New York qualify under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "travel",              True,  "New York travel expenditure qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "accommodation_lodging", True, "New York accommodation qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "per_diem",            True,  "Per diem costs incurred in New York qualify under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "insurance",           True,  "New York production insurance qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "completion_bond",     True,  "Completion bond costs qualify under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("ny_state_film", "marine_vessel",       True,  "Marine vessel hire in New York qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "vfx",                 True,  "New York VFX expenditure qualifies under NY State Film Tax Credit. NY VFX credit is separate programme with additional 5% uplift.", "PARSED"),
    ("ny_state_film", "post_production",     True,  "New York post-production qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "animation",           True,  "New York animation qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "music",               True,  "New York music expenditure qualifies under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "legal_accounting",    True,  "New York legal and accounting costs qualify under NY State Film Tax Credit.", "PARSED"),
    ("ny_state_film", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),
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
            sa.text("""
                DELETE FROM program_spend_treatments
                WHERE id = :id
            """),
            {"id": _uid(f"treatment:{slug}:{labor_type}")},
        )
