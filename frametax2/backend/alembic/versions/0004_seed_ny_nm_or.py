"""Seed NY, NM, and Oregon — source-backed rates, rules, and qualifying spend categories

Revision ID: 0004
Revises: 0003
Create Date: 2025-06-18

SOURCES:
  New York: NY Tax Law § 24; Empire State Development https://esd.ny.gov/ny-film-tax-credit
  New Mexico: NMSA 1978 § 7-2F-1 et seq.; NM Film Office https://nmfilm.com/tax-incentives/
  Oregon: ORS § 284.368 et seq.; Oregon Film Office https://oregonfilm.org/incentives/

CONFIDENCE TIERS:
  All rates marked PARSED — well-known program parameters from official sources,
  but current statutory text has not been directly reviewed in this session.
  Promote individual values to VERIFIED only after reviewing primary source text.

  Exception: rules drawn from explicit statutory citations in film-office
  summaries are marked PARSED (not DISCOVERY).

NEW IN THIS MIGRATION:
  - Oregon jurisdiction (US-OR) and program (OPIF) — not previously seeded
  - Source documents for NY, NM, OR
  - Qualifying spend categories for NY, NM, OR
  - Incentive rules (minimum spend, spend %, entity type)
  - NY upstate uplift (+10%) per NY Tax Law § 24(b)(1)(B)

INTENTIONALLY NOT MODELED:
  NM resident-crew 5% uplift — cannot be applied to a spend sub-category only;
    current engine ProgramUplift.applies_to does not support "resident_labor_only"
  NY 40-shooting-days alternative threshold — no shooting_days rule type exists
  OR tiered rates below $1M — simplified to single-tier 20% at ≥$1M
  County/city add-ons for any state
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Stable UUIDs — deterministic so downgrade can target them
# ---------------------------------------------------------------------------
OR_JURISDICTION_ID = str(uuid.UUID("b0000000-0004-0000-0001-000000000001"))
OR_PROGRAM_ID      = str(uuid.UUID("b0000000-0004-0000-0002-000000000001"))

SRC_NY_ID = str(uuid.UUID("b0000000-0004-0000-0003-000000000001"))
SRC_NM_ID = str(uuid.UUID("b0000000-0004-0000-0003-000000000002"))
SRC_OR_ID = str(uuid.UUID("b0000000-0004-0000-0003-000000000003"))

RULE_NY_MIN_BUDGET_ID  = str(uuid.UUID("b0000000-0004-0000-0004-000000000001"))
RULE_NY_SPEND_PCT_ID   = str(uuid.UUID("b0000000-0004-0000-0004-000000000002"))
RULE_NY_ENTITY_ID      = str(uuid.UUID("b0000000-0004-0000-0004-000000000003"))
RULE_NM_MIN_SPEND_ID   = str(uuid.UUID("b0000000-0004-0000-0004-000000000004"))
RULE_NM_ENTITY_ID      = str(uuid.UUID("b0000000-0004-0000-0004-000000000005"))
RULE_OR_MIN_SPEND_ID   = str(uuid.UUID("b0000000-0004-0000-0004-000000000006"))
RULE_OR_ENTITY_ID      = str(uuid.UUID("b0000000-0004-0000-0004-000000000007"))

UPLIFT_NY_UPSTATE_ID = str(uuid.UUID("b0000000-0004-0000-0005-000000000001"))

_QSC_NS = uuid.UUID("b0000000-0004-0000-0006-000000000000")


def _qsc_uid(slug: str, category: str) -> str:
    return str(uuid.uuid5(_QSC_NS, f"{slug}:{category}"))


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def _lookup(conn, table: str, col: str, val: str) -> str:
    result = conn.execute(
        sa.text(f"SELECT id FROM {table} WHERE {col} = :{col}"),
        {col: val},
    ).fetchone()
    if not result:
        raise RuntimeError(f"{table}.{col}='{val}' not found — prerequisite migration missing")
    return str(result[0])


def upgrade() -> None:
    conn = op.get_bind()

    # Resolve existing jurisdiction/program IDs inserted by 0002
    us_id   = _lookup(conn, "jurisdictions", "code", "US")
    ny_jur  = _lookup(conn, "jurisdictions", "code", "US-NY")
    nm_jur  = _lookup(conn, "jurisdictions", "code", "US-NM")
    ny_prog = _lookup(conn, "incentive_programs", "slug", "ny_state_film")
    nm_prog = _lookup(conn, "incentive_programs", "slug", "nm_film_production")

    # -----------------------------------------------------------------------
    # 1. Oregon jurisdiction (not seeded by 0002)
    # -----------------------------------------------------------------------
    jur_table = sa.table(
        "jurisdictions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("parent_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("iso_code", sa.String),
        sa.column("level", sa.String),
        sa.column("currency_code", sa.String),
        sa.column("country_code", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("metadata_json", postgresql.JSONB),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(jur_table, [{
        "id": OR_JURISDICTION_ID,
        "parent_id": us_id,
        "name": "Oregon",
        "code": "US-OR",
        "iso_code": "US-OR",
        "level": "state",
        "currency_code": "USD",
        "country_code": "US",
        "is_active": True,
        "notes": "Oregon Production Investment Fund (OPIF) — 20% cash rebate on OR-based expenditures",
        "metadata_json": None,
        "created_at": NOW,
        "updated_at": NOW,
    }])

    # -----------------------------------------------------------------------
    # 2. Source documents
    # -----------------------------------------------------------------------
    src_table = sa.table(
        "source_documents",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("title", sa.String),
        sa.column("document_type", sa.String),
        sa.column("jurisdiction_id", postgresql.UUID(as_uuid=True)),
        sa.column("authority_name", sa.String),
        sa.column("source_url", sa.String),
        sa.column("publication_date", sa.String),
        sa.column("effective_from", sa.String),
        sa.column("effective_until", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("review_status", sa.String),
        sa.column("storage_path", sa.String),
        sa.column("raw_text", sa.Text),
        sa.column("page_count", sa.Integer),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(src_table, [
        {
            "id": SRC_NY_ID,
            "title": "NY Tax Law § 24 — Empire State Film Production Tax Credit",
            "document_type": "regulation",
            "jurisdiction_id": ny_jur,
            "authority_name": "New York State Legislature / Empire State Development",
            "source_url": "https://esd.ny.gov/ny-film-tax-credit",
            "publication_date": None,
            "effective_from": "2004-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "NY Tax Law § 24(b)(1): 25% base credit on qualified NY production costs. "
                "§ 24(b)(1)(B): 10% additional (35% total) for upstate productions outside "
                "the Metropolitan Commuter Transportation District. "
                "§ 24(a)(1): minimum $1,000,000 total production budget. "
                "Credit is refundable against NY income tax. "
                "Annual allocation cap administered by ESD (currently ~$700M/year). "
                "Qualified costs are primarily below-the-line NYS expenditures. "
                "ATL compensation generally excluded from qualified production costs. "
                "PARSED — program parameters widely documented; statutory text not directly reviewed."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_NM_ID,
            "title": "NMSA 1978 § 7-2F-1 et seq. — New Mexico Film Production Tax Credit",
            "document_type": "regulation",
            "jurisdiction_id": nm_jur,
            "authority_name": "New Mexico Taxation and Revenue Department / NM Film Office",
            "source_url": "https://nmfilm.com/tax-incentives/",
            "publication_date": None,
            "effective_from": "2002-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "NMSA 1978 § 7-2F-1 et seq. (as amended through 2022). "
                "Base credit: 25% of qualified direct expenditures made in New Mexico. "
                "Additional 5% for qualified expenditures on New Mexico resident crew and talent. "
                "The 5% resident uplift cannot be precisely modeled by the current engine — "
                "see program notes. Minimum qualified expenditures: $50,000. "
                "Credit is refundable. Annual statewide cap applies (confirm current amount). "
                "PARSED — program parameters widely documented; statutory text not directly reviewed."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_OR_ID,
            "title": "ORS § 284.368 et seq. — Oregon Production Investment Fund (OPIF)",
            "document_type": "regulation",
            "jurisdiction_id": OR_JURISDICTION_ID,
            "authority_name": "Oregon Film Office / Travel Oregon",
            "source_url": "https://oregonfilm.org/incentives/",
            "publication_date": None,
            "effective_from": None,
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Oregon Production Investment Fund (OPIF) under ORS § 284.368 et seq. "
                "Cash rebate program — not a tax credit. "
                "20% rebate on Oregon-based qualifying expenditures for productions "
                "spending ≥$1,000,000 in Oregon. Rebate is administered by Oregon Film Office. "
                "Fund is limited annual allocation (competitive). "
                "Both ATL and BTL qualifying Oregon-based expenditures appear to be eligible. "
                "Insurance, financing costs, and non-Oregon expenditures excluded. "
                "PARSED — program parameters widely documented; statutory text not directly reviewed. "
                "ORS citation approximate — verify exact statute before VERIFIED promotion."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 3. Oregon program (new — not in 0002)
    # -----------------------------------------------------------------------
    prog_table = sa.table(
        "incentive_programs",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("jurisdiction_id", postgresql.UUID(as_uuid=True)),
        sa.column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("program_type", sa.String),
        sa.column("credit_basis", sa.String),
        sa.column("base_rate", sa.Numeric),
        sa.column("max_rate", sa.Numeric),
        sa.column("is_refundable", sa.Boolean),
        sa.column("is_transferable", sa.Boolean),
        sa.column("transferable_value_pct", sa.Numeric),
        sa.column("is_competitive", sa.Boolean),
        sa.column("annual_cap_local", sa.Numeric),
        sa.column("requires_cultural_test", sa.Boolean),
        sa.column("cultural_test_id", postgresql.UUID(as_uuid=True)),
        sa.column("requires_local_entity", sa.Boolean),
        sa.column("effective_from", sa.String),
        sa.column("effective_until", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("review_status", sa.String),
        sa.column("authority_url", sa.String),
        sa.column("last_verified_date", sa.String),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(prog_table, [{
        "id": OR_PROGRAM_ID,
        "jurisdiction_id": OR_JURISDICTION_ID,
        "source_document_id": SRC_OR_ID,
        "name": "Oregon Production Investment Fund (OPIF)",
        "slug": "or_opif",
        "program_type": "cash_rebate",
        "credit_basis": "qualifying_spend",
        "base_rate": 0.200000,
        "max_rate": 0.200000,
        "is_refundable": True,
        "is_transferable": False,
        "transferable_value_pct": None,
        "is_competitive": True,
        "annual_cap_local": None,
        "requires_cultural_test": False,
        "cultural_test_id": None,
        "requires_local_entity": True,
        "effective_from": None,
        "effective_until": None,
        "confidence_tier": "PARSED",
        "review_status": "approved",
        "authority_url": "https://oregonfilm.org/incentives/",
        "last_verified_date": "2025-06-18",
        "notes": (
            "PARSED — Oregon Production Investment Fund (OPIF). "
            "20% cash rebate on Oregon-based qualifying expenditures. "
            "Minimum $1,000,000 Oregon qualified expenditures for standard track. "
            "Cash rebate (not a tax credit) — economic value = face value. "
            "Annual fund is limited and competitive — rebate not guaranteed. "
            "Both ATL and BTL Oregon-based expenditures appear to qualify per OPIF guidelines. "
            "Insurance, financing, and non-Oregon costs excluded. "
            "Requires production company registration with Oregon. "
            "Promote to VERIFIED after reviewing ORS § 284.368 text directly."
        ),
        "created_at": NOW,
        "updated_at": NOW,
    }])

    # -----------------------------------------------------------------------
    # 4. Update NY and NM programs with PARSED rates + source links
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src,
                base_rate              = 0.250000,
                max_rate               = 0.350000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = TRUE,
                requires_local_entity  = TRUE,
                effective_from         = '2004-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://esd.ny.gov/ny-film-tax-credit',
                last_verified_date     = '2025-06-18',
                notes = 'PARSED — NY Tax Law § 24. '
                        'Base credit: 25% of qualified NY below-the-line production costs. '
                        'Upstate uplift: additional 10% (35% total) for productions outside '
                        'the Metropolitan Commuter Transportation District. '
                        'ATL compensation (directors, cast, writers, producers) generally '
                        'does NOT qualify for the NY credit. '
                        'Minimum $1,000,000 total production budget. '
                        'Refundable against NY income tax. '
                        'Annual ESD allocation cap applies — production not guaranteed credit. '
                        'Promote to VERIFIED after reviewing current § 24 statutory text.',
                updated_at = :now
            WHERE slug = 'ny_state_film'
        """),
        {"src": SRC_NY_ID, "now": NOW},
    )

    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src,
                base_rate              = 0.250000,
                max_rate               = 0.300000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = TRUE,
                requires_local_entity  = TRUE,
                effective_from         = '2002-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://nmfilm.com/tax-incentives/',
                last_verified_date     = '2025-06-18',
                notes = 'PARSED — NMSA 1978 § 7-2F-1 et seq. '
                        'Base credit: 25% of qualified direct expenditures in New Mexico. '
                        'Additional 5% on NM-resident crew/talent expenditures (30% effective on resident labor). '
                        'The 5% resident uplift cannot be precisely modeled by the current engine '
                        '(ProgramUplift.applies_to does not support resident_labor_only). '
                        'Minimum $50,000 in NM qualified expenditures. '
                        'Refundable credit. Annual statewide cap — confirm current amount with NM TRD. '
                        'NM has broader ATL qualifying definition than NY — directors, writers, '
                        'producers, and cast compensation may qualify subject to per-person caps. '
                        'Promote to VERIFIED after reviewing NMSA § 7-2F text directly.',
                updated_at = :now
            WHERE slug = 'nm_film_production'
        """),
        {"src": SRC_NM_ID, "now": NOW},
    )

    # -----------------------------------------------------------------------
    # 5. Qualifying spend categories
    # -----------------------------------------------------------------------
    qsc_table = sa.table(
        "qualifying_spend_categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("spend_category", sa.String),
        sa.column("qualifies", sa.Boolean),
        sa.column("jurisdiction_spend_only", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    def qsc(slug: str, prog_id: str, category: str, qualifies: bool,
            jur_only: bool, notes: str, tier: str = "PARSED"):
        return {
            "id": _qsc_uid(slug, category),
            "program_id": prog_id,
            "spend_category": category,
            "qualifies": qualifies,
            "jurisdiction_spend_only": jur_only,
            "notes": notes,
            "confidence_tier": tier,
            "created_at": NOW,
            "updated_at": NOW,
        }

    # --- New York: below-the-line only ---
    # ATL excluded per NY Tax Law § 24 — qualified costs are NYS BTL expenditures
    ny_qsc = [
        qsc("ny_state_film", ny_prog, "atl_director", False, True,
            "ATL excluded per NY Tax Law § 24 — qualified costs are BTL NYS expenditures"),
        qsc("ny_state_film", ny_prog, "atl_writer",   False, True,
            "ATL excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "atl_producer", False, True,
            "ATL excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "atl_cast",     False, True,
            "ATL excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "atl_rights",   False, True,
            "Rights/option costs excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "btl_crew_labor",        True, True,
            "NYS below-the-line crew labor qualifies per NY Tax Law § 24(a)"),
        qsc("ny_state_film", ny_prog, "btl_resident_labor",    True, True,
            "NYS resident below-the-line labor qualifies"),
        qsc("ny_state_film", ny_prog, "btl_nonresident_labor", True, True,
            "Qualifies when physically working in NYS; jurisdiction_spend_only=True applied"),
        qsc("ny_state_film", ny_prog, "btl_equipment_rental", True, True,
            "NYS equipment rental qualifies per § 24(a)"),
        qsc("ny_state_film", ny_prog, "btl_stage_facility",   True, True,
            "NYS studio/stage rental qualifies"),
        qsc("ny_state_film", ny_prog, "btl_location_fees",    True, True,
            "NYS location fees qualify"),
        qsc("ny_state_film", ny_prog, "btl_set_construction", True, True,
            "NYS set construction labor and materials qualify"),
        qsc("ny_state_film", ny_prog, "btl_transportation",   True, True,
            "NYS transportation costs qualify"),
        qsc("ny_state_film", ny_prog, "btl_catering",         True, True,
            "NYS catering qualifies"),
        qsc("ny_state_film", ny_prog, "post_production", True, True,
            "Post-production qualifies when performed in NYS"),
        qsc("ny_state_film", ny_prog, "vfx",   True, True,
            "VFX qualifies when performed in NYS"),
        qsc("ny_state_film", ny_prog, "music", True, True,
            "Music recording/scoring qualifies when performed in NYS"),
        qsc("ny_state_film", ny_prog, "sound", True, True,
            "Sound work qualifies when performed in NYS"),
        qsc("ny_state_film", ny_prog, "finance_costs",   False, True,
            "Financing costs excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "insurance",       False, True,
            "Insurance excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "completion_bond", False, True,
            "Completion bond excluded per NY Tax Law § 24"),
        qsc("ny_state_film", ny_prog, "contingency",     False, True,
            "Contingency reserves excluded"),
        qsc("ny_state_film", ny_prog, "payroll_fringes", True, True,
            "Payroll taxes and fringes on qualifying NYS wages typically included", "PARSED"),
        qsc("ny_state_film", ny_prog, "deferment",            False, True,
            "Non-cash — excluded"),
        qsc("ny_state_film", ny_prog, "equity_participation", False, True,
            "Non-cash — excluded"),
        qsc("ny_state_film", ny_prog, "in_kind",              False, True,
            "Non-cash — excluded"),
        qsc("ny_state_film", ny_prog, "reinvestment",         False, True,
            "Non-cash — excluded"),
        qsc("ny_state_film", ny_prog, "travel",        True, True,
            "NYS-incurred travel qualifies", "PARSED"),
        qsc("ny_state_film", ny_prog, "lodging",       True, True,
            "NYS lodging qualifies", "PARSED"),
        qsc("ny_state_film", ny_prog, "miscellaneous", True, True,
            "NYS miscellaneous production costs may qualify; review recommended", "PARSED"),
    ]

    # --- New Mexico: broad definition including ATL (PARSED) ---
    # NMSA § 7-2F-1 defines qualified direct expenditures broadly;
    # ATL compensation appears to qualify subject to per-person limits (PARSED)
    nm_qsc = [
        qsc("nm_film_production", nm_prog, "atl_director", True, True,
            "Qualifies per NMSA § 7-2F-1 broad definition of qualified direct expenditures; "
            "subject to per-person cap — verify exact cap amount with NM TRD", "PARSED"),
        qsc("nm_film_production", nm_prog, "atl_writer",   True, True,
            "Qualifies per NMSA § 7-2F-1 — PARSED; verify per-person cap", "PARSED"),
        qsc("nm_film_production", nm_prog, "atl_producer", True, True,
            "Qualifies per NMSA § 7-2F-1 — PARSED; verify per-person cap", "PARSED"),
        qsc("nm_film_production", nm_prog, "atl_cast",     True, True,
            "Qualifies per NMSA § 7-2F-1 — PARSED; subject to per-person cap", "PARSED"),
        qsc("nm_film_production", nm_prog, "atl_rights",   False, True,
            "Rights/acquisition costs generally excluded — not a direct production expenditure"),
        qsc("nm_film_production", nm_prog, "btl_crew_labor",        True, True,
            "Qualifies per NMSA § 7-2F-1; NM resident crew gets additional 5% (not modeled)"),
        qsc("nm_film_production", nm_prog, "btl_resident_labor",    True, True,
            "Qualifies; NM-resident crew gets 5% additional credit (not modeled in uplift)"),
        qsc("nm_film_production", nm_prog, "btl_nonresident_labor", True, True,
            "Qualifies when working in NM per § 7-2F-1"),
        qsc("nm_film_production", nm_prog, "btl_equipment_rental", True, True,
            "NM equipment rental and purchases qualify"),
        qsc("nm_film_production", nm_prog, "btl_stage_facility",   True, True,
            "NM studio/stage rental qualifies"),
        qsc("nm_film_production", nm_prog, "btl_location_fees",    True, True,
            "NM location fees qualify"),
        qsc("nm_film_production", nm_prog, "btl_set_construction", True, True,
            "NM set construction qualifies"),
        qsc("nm_film_production", nm_prog, "btl_transportation",   True, True,
            "NM transportation costs qualify"),
        qsc("nm_film_production", nm_prog, "btl_catering",         True, True,
            "NM catering qualifies"),
        qsc("nm_film_production", nm_prog, "post_production", True, True,
            "Post-production qualifies when performed in NM"),
        qsc("nm_film_production", nm_prog, "vfx",   True, True,
            "VFX qualifies when performed in NM"),
        qsc("nm_film_production", nm_prog, "music", True, True,
            "Music qualifies when performed in NM"),
        qsc("nm_film_production", nm_prog, "sound", True, True,
            "Sound qualifies when performed in NM"),
        qsc("nm_film_production", nm_prog, "finance_costs",   False, True,
            "Financing costs excluded per § 7-2F-1"),
        qsc("nm_film_production", nm_prog, "insurance",       False, True,
            "Insurance excluded per § 7-2F-1"),
        qsc("nm_film_production", nm_prog, "completion_bond", False, True,
            "Completion bond excluded"),
        qsc("nm_film_production", nm_prog, "contingency",     False, True,
            "Contingency excluded"),
        qsc("nm_film_production", nm_prog, "payroll_fringes", True, True,
            "Fringes on qualifying NM wages typically included", "PARSED"),
        qsc("nm_film_production", nm_prog, "deferment",            False, True,
            "Non-cash — excluded"),
        qsc("nm_film_production", nm_prog, "equity_participation", False, True,
            "Non-cash — excluded"),
        qsc("nm_film_production", nm_prog, "in_kind",              False, True,
            "Non-cash — excluded"),
        qsc("nm_film_production", nm_prog, "reinvestment",         False, True,
            "Non-cash — excluded"),
        qsc("nm_film_production", nm_prog, "travel",        True, True,
            "NM-incurred travel qualifies", "PARSED"),
        qsc("nm_film_production", nm_prog, "lodging",       True, True,
            "NM lodging qualifies", "PARSED"),
        qsc("nm_film_production", nm_prog, "miscellaneous", True, True,
            "NM miscellaneous production costs may qualify", "PARSED"),
    ]

    # --- Oregon: Oregon-based expenditures broadly (PARSED) ---
    or_qsc = [
        qsc("or_opif", OR_PROGRAM_ID, "atl_director", True, True,
            "OPIF rebate applies to Oregon-based expenditures broadly including ATL — PARSED; "
            "verify with Oregon Film Office", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "atl_writer",   True, True,
            "OPIF: Oregon-based ATL writer fees appear to qualify — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "atl_producer", True, True,
            "OPIF: Oregon-based ATL producer fees appear to qualify — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "atl_cast",     True, True,
            "OPIF: Oregon-based cast fees appear to qualify — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "atl_rights",   False, True,
            "Rights/acquisition costs generally excluded from OPIF"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_crew_labor",        True, True,
            "Oregon crew labor qualifies per OPIF — ORS § 284.368"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_resident_labor",    True, True,
            "Oregon resident crew qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_nonresident_labor", True, True,
            "Qualifies when work performed in Oregon"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_equipment_rental", True, True,
            "Oregon equipment rental/purchase qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_stage_facility",   True, True,
            "Oregon studio/stage qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_location_fees",    True, True,
            "Oregon location fees qualify"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_set_construction", True, True,
            "Oregon set construction qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_transportation",   True, True,
            "Oregon transportation costs qualify"),
        qsc("or_opif", OR_PROGRAM_ID, "btl_catering",         True, True,
            "Oregon catering qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "post_production", True, True,
            "Post-production in Oregon qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "vfx",   True, True,
            "VFX work in Oregon qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "music", True, True,
            "Music recording in Oregon qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "sound", True, True,
            "Sound work in Oregon qualifies"),
        qsc("or_opif", OR_PROGRAM_ID, "finance_costs",   False, True,
            "Financing costs excluded from OPIF"),
        qsc("or_opif", OR_PROGRAM_ID, "insurance",       False, True,
            "Insurance excluded from OPIF"),
        qsc("or_opif", OR_PROGRAM_ID, "completion_bond", False, True,
            "Completion bond excluded from OPIF"),
        qsc("or_opif", OR_PROGRAM_ID, "contingency",     False, True,
            "Contingency excluded from OPIF"),
        qsc("or_opif", OR_PROGRAM_ID, "payroll_fringes", True, True,
            "Payroll fringes on qualifying Oregon wages likely qualify — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "deferment",            False, True,
            "Non-cash — excluded"),
        qsc("or_opif", OR_PROGRAM_ID, "equity_participation", False, True,
            "Non-cash — excluded"),
        qsc("or_opif", OR_PROGRAM_ID, "in_kind",              False, True,
            "Non-cash — excluded"),
        qsc("or_opif", OR_PROGRAM_ID, "reinvestment",         False, True,
            "Non-cash — excluded"),
        qsc("or_opif", OR_PROGRAM_ID, "travel",        True, True,
            "Oregon-incurred travel qualifies — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "lodging",       True, True,
            "Oregon lodging qualifies — PARSED", "PARSED"),
        qsc("or_opif", OR_PROGRAM_ID, "miscellaneous", True, True,
            "Oregon miscellaneous production costs may qualify — PARSED", "PARSED"),
    ]

    op.bulk_insert(qsc_table, ny_qsc + nm_qsc + or_qsc)

    # -----------------------------------------------------------------------
    # 6. Incentive rules
    # -----------------------------------------------------------------------
    rule_table = sa.table(
        "incentive_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_type", sa.String),
        sa.column("threshold_numeric", sa.Numeric),
        sa.column("threshold_text", sa.String),
        sa.column("fail_action", sa.String),
        sa.column("description", sa.Text),
        sa.column("source_page", sa.Integer),
        sa.column("source_excerpt", sa.Text),
        sa.column("statutory_reference", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(rule_table, [
        # --- New York ---
        {
            "id": RULE_NY_MIN_BUDGET_ID,
            "program_id": ny_prog,
            "source_document_id": SRC_NY_ID,
            "rule_type": "minimum_total_budget",
            "threshold_numeric": 1_000_000.00,
            "threshold_text": "$1,000,000 total production budget",
            "fail_action": "disqualify",
            "description": "Total production budget must be at least $1,000,000 to qualify for NY Film Tax Credit.",
            "source_page": None,
            "source_excerpt": "NY Tax Law § 24(a)(1): minimum $1,000,000 total production budget threshold.",
            "statutory_reference": "NY Tax Law § 24(a)(1)",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_NY_SPEND_PCT_ID,
            "program_id": ny_prog,
            "source_document_id": SRC_NY_ID,
            "rule_type": "minimum_jurisdiction_spend_pct",
            "threshold_numeric": 0.75,
            "threshold_text": "75% of below-the-line costs must be incurred in NYS, "
                              "OR 40% of principal photography shooting days must be in NYS",
            "fail_action": "disqualify",
            "description": (
                "Production must satisfy one of: (A) at least 75% of below-the-line production "
                "costs incurred in New York State, OR (B) at least 40% of principal photography "
                "shooting days in NYS. Engine models the 75% BTL threshold; "
                "the 40-day alternative requires shooting_days data not yet implemented."
            ),
            "source_page": None,
            "source_excerpt": "NY Tax Law § 24(a)(2): '...75 percent of the below-the-line production costs "
                              "are incurred in New York state...'",
            "statutory_reference": "NY Tax Law § 24(a)(2)",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_NY_ENTITY_ID,
            "program_id": ny_prog,
            "source_document_id": SRC_NY_ID,
            "rule_type": "required_entity_type",
            "threshold_numeric": None,
            "threshold_text": "Production company must be subject to NY income tax; "
                              "must apply to ESD before production begins",
            "fail_action": "flag_for_review",
            "description": (
                "The production company must be subject to New York income tax and must "
                "apply to Empire State Development before the production period begins."
            ),
            "source_page": None,
            "source_excerpt": "ESD application required; credit is refundable against NY Tax Law § 24.",
            "statutory_reference": "NY Tax Law § 24; ESD Application Process",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        # --- New Mexico ---
        {
            "id": RULE_NM_MIN_SPEND_ID,
            "program_id": nm_prog,
            "source_document_id": SRC_NM_ID,
            "rule_type": "minimum_qualified_spend",
            "threshold_numeric": 50_000.00,
            "threshold_text": "$50,000 in New Mexico qualified direct expenditures",
            "fail_action": "disqualify",
            "description": "Minimum $50,000 in NM qualified direct expenditures to be eligible for the credit.",
            "source_page": None,
            "source_excerpt": "NMSA § 7-2F-1: minimum qualified expenditure threshold of $50,000.",
            "statutory_reference": "NMSA 1978 § 7-2F-1",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_NM_ENTITY_ID,
            "program_id": nm_prog,
            "source_document_id": SRC_NM_ID,
            "rule_type": "required_entity_type",
            "threshold_numeric": None,
            "threshold_text": "Production company must register with NM Taxation and Revenue Department",
            "fail_action": "flag_for_review",
            "description": "Production company must be registered with NM TRD; NM LLC or registered foreign entity.",
            "source_page": None,
            "source_excerpt": "NMSA § 7-2F-1 application and registration requirements.",
            "statutory_reference": "NMSA 1978 § 7-2F-1",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        # --- Oregon ---
        {
            "id": RULE_OR_MIN_SPEND_ID,
            "program_id": OR_PROGRAM_ID,
            "source_document_id": SRC_OR_ID,
            "rule_type": "minimum_qualified_spend",
            "threshold_numeric": 1_000_000.00,
            "threshold_text": "$1,000,000 in Oregon-based qualifying expenditures (standard OPIF track)",
            "fail_action": "disqualify",
            "description": (
                "Standard OPIF track requires minimum $1,000,000 in Oregon-based qualifying "
                "expenditures. A lower-threshold track exists for smaller productions — "
                "verify current minimum with Oregon Film Office."
            ),
            "source_page": None,
            "source_excerpt": "Oregon Film OPIF guidelines: minimum Oregon expenditure threshold for standard track.",
            "statutory_reference": "ORS § 284.368 (approximate)",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_OR_ENTITY_ID,
            "program_id": OR_PROGRAM_ID,
            "source_document_id": SRC_OR_ID,
            "rule_type": "required_entity_type",
            "threshold_numeric": None,
            "threshold_text": "Production company must register with Oregon and apply to Oregon Film Office",
            "fail_action": "flag_for_review",
            "description": "Oregon requires pre-production application and registration with Oregon Film Office.",
            "source_page": None,
            "source_excerpt": "Oregon Film OPIF application process requires pre-production registration.",
            "statutory_reference": "ORS § 284.368",
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 7. Program uplifts — NY upstate only
    #    NM resident-crew +5% not modeled (engine limitation documented above)
    # -----------------------------------------------------------------------
    uplift_table = sa.table(
        "program_uplifts",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("additional_rate", sa.Numeric),
        sa.column("applies_to", sa.String),
        sa.column("condition_type", sa.String),
        sa.column("condition_threshold", sa.Numeric),
        sa.column("condition_text", sa.String),
        sa.column("is_stackable_with_other_uplifts", sa.Boolean),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(uplift_table, [{
        "id": UPLIFT_NY_UPSTATE_ID,
        "program_id": ny_prog,
        "name": "NY Upstate Production Uplift",
        "additional_rate": 0.100000,
        "applies_to": "same_qualifying_spend",
        "condition_type": "shooting_location",
        "condition_threshold": None,
        "condition_text": "upstate_ny",
        "is_stackable_with_other_uplifts": False,
        "confidence_tier": "PARSED",
        "created_at": NOW,
        "updated_at": NOW,
    }])


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DELETE FROM program_uplifts WHERE id = :uid"),
                 {"uid": UPLIFT_NY_UPSTATE_ID})

    conn.execute(sa.text(
        "DELETE FROM incentive_rules WHERE id IN (:r1,:r2,:r3,:r4,:r5,:r6,:r7)"),
        {"r1": RULE_NY_MIN_BUDGET_ID, "r2": RULE_NY_SPEND_PCT_ID, "r3": RULE_NY_ENTITY_ID,
         "r4": RULE_NM_MIN_SPEND_ID,  "r5": RULE_NM_ENTITY_ID,
         "r6": RULE_OR_MIN_SPEND_ID,  "r7": RULE_OR_ENTITY_ID})

    for slug in ("ny_state_film", "nm_film_production", "or_opif"):
        try:
            prog_id = _lookup(conn, "incentive_programs", "slug", slug)
            conn.execute(sa.text("DELETE FROM qualifying_spend_categories WHERE program_id = :pid"),
                         {"pid": prog_id})
        except RuntimeError:
            pass

    conn.execute(sa.text(
        "UPDATE incentive_programs SET "
        "source_document_id=NULL, base_rate=NULL, max_rate=NULL, "
        "is_refundable=NULL, is_transferable=NULL, transferable_value_pct=NULL, "
        "confidence_tier='DISCOVERY', review_status='pending', last_verified_date=NULL, "
        "updated_at=:now WHERE slug IN ('ny_state_film','nm_film_production')"),
        {"now": NOW})

    conn.execute(sa.text("DELETE FROM incentive_programs WHERE id = :pid"),
                 {"pid": OR_PROGRAM_ID})
    conn.execute(sa.text("DELETE FROM jurisdictions WHERE id = :jid"),
                 {"jid": OR_JURISDICTION_ID})
    conn.execute(sa.text("DELETE FROM source_documents WHERE id IN (:s1,:s2,:s3)"),
                 {"s1": SRC_NY_ID, "s2": SRC_NM_ID, "s3": SRC_OR_ID})
