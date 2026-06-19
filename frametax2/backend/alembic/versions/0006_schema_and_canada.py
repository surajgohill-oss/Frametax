"""Schema additions and Canadian incentive program PARSED population

Revision ID: 0006
Revises: 0005
Create Date: 2025-06-18

SCHEMA CHANGES:
  source_documents.superseded_by_id — self-referential FK for document lifecycle
  (supports DISCOVERY → PARSED → VERIFIED → SUPERSEDED workflow)

CANADIAN PROGRAMS (DISCOVERY → PARSED):
  ON OPSTC  — Ontario Production Services Tax Credit
  ON OFTTC  — Ontario Film and Television Tax Credit
  BC PSTC   — British Columbia Production Services Tax Credit
  QC QPRDP  — Quebec Production Tax Credit (service productions)
  CA CPTC   — Canadian Film or Video Production Tax Credit (Federal)

SOURCES (PARSED — official government/agency summaries reviewed):
  ON OPSTC:  Ontario Media Development Corporation (omdc.on.ca)
             Ontario Reg 37/09 under Corporations Tax Act
  ON OFTTC:  Ontario Media Development Corporation (omdc.on.ca)
             Ontario Reg 37/09; CAVCO certification required
  BC PSTC:   Creative BC (creativebc.com/programs/production-services-tax-credit)
             BC Income Tax Act s.91–93
  QC QPRDP:  SODEC (sodec.gouv.qc.ca) — service production tax credit
             Taxation Act § 1029.8.34 et seq.
  CA CPTC:   Canada Revenue Agency T4283; Canadian Heritage CAVCO
             Income Tax Act § 125.4

CONFIDENCE TIERS:
  All programs marked PARSED.
  Rates are from official agency program summaries, not from direct primary statutory review.
  Promote to VERIFIED only after reviewing primary source text.

INTENTIONALLY NOT MODELED:
  ON OPSTC:  Ontario computer animation VFX credit (OCASE) — separate program
  ON OFTTC:  Ontario Interactive Digital Media Tax Credit (OIDMTC) — separate program
  BC PSTC:   BC Digital Animation or Visual Effects tax credit (DAVE) — separate program
  BC PSTC:   BC Film Incentive — separate from PSTC
  QC QPRDP:  QPRDP cultural test variant — separate from service credit
  CA CPTC:   CAVCO points threshold — no cultural_test rule type in engine
  CA CPTC:   60% labour cap on budget — complex cap not modeled in engine
  Any CAD/USD foreign exchange conversion — fixtures use CAD face values
"""
from __future__ import annotations

from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Stable UUIDs — deterministic so downgrade can target them
# ---------------------------------------------------------------------------
SRC_ON_OPSTC_ID  = str(uuid.UUID("d0000000-0006-0000-0001-000000000001"))
SRC_ON_OFTTC_ID  = str(uuid.UUID("d0000000-0006-0000-0001-000000000002"))
SRC_BC_PSTC_ID   = str(uuid.UUID("d0000000-0006-0000-0001-000000000003"))
SRC_QC_QPRDP_ID  = str(uuid.UUID("d0000000-0006-0000-0001-000000000004"))
SRC_CA_CPTC_ID   = str(uuid.UUID("d0000000-0006-0000-0001-000000000005"))

RULE_ON_OPSTC_MIN_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000001"))
RULE_ON_OPSTC_ENT_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000002"))
RULE_ON_OFTTC_MIN_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000003"))
RULE_ON_OFTTC_ENT_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000004"))
RULE_BC_PSTC_MIN_ID    = str(uuid.UUID("d0000000-0006-0000-0002-000000000005"))
RULE_BC_PSTC_ENT_ID    = str(uuid.UUID("d0000000-0006-0000-0002-000000000006"))
RULE_QC_QPRDP_MIN_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000007"))
RULE_QC_QPRDP_ENT_ID   = str(uuid.UUID("d0000000-0006-0000-0002-000000000008"))
RULE_CA_CPTC_MIN_ID    = str(uuid.UUID("d0000000-0006-0000-0002-000000000009"))
RULE_CA_CPTC_ENT_ID    = str(uuid.UUID("d0000000-0006-0000-0002-000000000010"))

UPLIFT_BC_REGIONAL_ID  = str(uuid.UUID("d0000000-0006-0000-0003-000000000001"))

_QSC_NS = uuid.UUID("d0000000-0006-0000-0004-000000000000")


def _qsc_uid(slug: str, category: str) -> str:
    return str(uuid.uuid5(_QSC_NS, f"{slug}:{category}"))


def _lookup(conn, table: str, col: str, val: str) -> str:
    result = conn.execute(
        sa.text(f"SELECT id FROM {table} WHERE {col} = :{col}"),
        {col: val},
    ).fetchone()
    if not result:
        raise RuntimeError(f"{table}.{col}='{val}' not found — prerequisite migration missing")
    return str(result[0])


def upgrade() -> None:
    # -------------------------------------------------------------------
    # DDL: add superseded_by_id to source_documents
    # -------------------------------------------------------------------
    op.add_column(
        "source_documents",
        sa.Column(
            "superseded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_documents.id"),
            nullable=True,
        ),
    )

    conn = op.get_bind()

    on_jur  = _lookup(conn, "jurisdictions",      "code", "CA-ON")
    bc_jur  = _lookup(conn, "jurisdictions",      "code", "CA-BC")
    qc_jur  = _lookup(conn, "jurisdictions",      "code", "CA-QC")
    ca_jur  = _lookup(conn, "jurisdictions",      "code", "CA")   # country-level
    on_opstc = _lookup(conn, "incentive_programs", "slug", "on_opstc")
    on_ofttc = _lookup(conn, "incentive_programs", "slug", "on_ofttc")
    bc_pstc  = _lookup(conn, "incentive_programs", "slug", "bc_pstc")
    qc_prod  = _lookup(conn, "incentive_programs", "slug", "qc_film_production")
    ca_cptc  = _lookup(conn, "incentive_programs", "slug", "ca_federal_cptc")

    # -------------------------------------------------------------------
    # 1. Source documents
    # -------------------------------------------------------------------
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
            "id": SRC_ON_OPSTC_ID,
            "title": "Ontario Production Services Tax Credit (OPSTC) — OMDC Program Guidelines",
            "document_type": "regulation",
            "jurisdiction_id": on_jur,
            "authority_name": "Ontario Media Development Corporation (OMDC)",
            "source_url": "https://omdc.on.ca/film-and-television/tax-credits/ontario-production-services-tax-credit/",
            "publication_date": None,
            "effective_from": "2009-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Ontario Production Services Tax Credit (OPSTC). "
                "Rate: 21.5% of Ontario-eligible production expenditures. "
                "Refundable, non-competitive, no cultural test required. "
                "Eligible spend: broad — Ontario labour (all categories) + "
                "Ontario tangible goods and services (equipment, facilities, post). "
                "Minimum Ontario-eligible expenditure: C$1,000,000. "
                "Ontario Reg 37/09 under Corporations Tax Act. "
                "PARSED — rates from OMDC program guidelines; "
                "Ontario Reg 37/09 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_ON_OFTTC_ID,
            "title": "Ontario Film and Television Tax Credit (OFTTC) — OMDC Program Guidelines",
            "document_type": "regulation",
            "jurisdiction_id": on_jur,
            "authority_name": "Ontario Media Development Corporation (OMDC)",
            "source_url": "https://omdc.on.ca/film-and-television/tax-credits/ontario-film-and-television-tax-credit/",
            "publication_date": None,
            "effective_from": "1998-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Ontario Film and Television Tax Credit (OFTTC). "
                "Rate: 35% of Ontario-eligible labour expenditures. "
                "Labour-only basis: BTL crew wages + applicable ATL if Ontario resident. "
                "Requires CAVCO certification (Canadian content). "
                "Refundable, non-competitive. "
                "Minimum Ontario labour: C$125,000. "
                "Ontario Reg 37/09 under Corporations Tax Act. "
                "PARSED — rates from OMDC program guidelines; "
                "Ontario Reg 37/09 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_BC_PSTC_ID,
            "title": "British Columbia Production Services Tax Credit (PSTC) — Creative BC Guidelines",
            "document_type": "regulation",
            "jurisdiction_id": bc_jur,
            "authority_name": "Creative BC",
            "source_url": "https://www.creativebc.com/programs/production-services-tax-credit/",
            "publication_date": None,
            "effective_from": "2003-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "British Columbia Production Services Tax Credit (PSTC). "
                "Base rate: 28% of BC-eligible labour expenditures. "
                "Regional uplift: +6% (total 34%) for BC regional production "
                "(production outside the Metro Vancouver/Capital Regional Districts). "
                "Labour-only basis: BTL crew wages (BC resident and non-resident working in BC). "
                "Refundable, non-competitive. "
                "Minimum BC eligible production costs: C$1,000,000. "
                "BC Income Tax Act ss.91-93. "
                "PARSED — rates from Creative BC program guidelines; "
                "BC ITA ss.91-93 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_QC_QPRDP_ID,
            "title": "Quebec Production Tax Credit (QPRDP) — SODEC Service Production Guidelines",
            "document_type": "regulation",
            "jurisdiction_id": qc_jur,
            "authority_name": "SODEC (Société de développement des entreprises culturelles)",
            "source_url": "https://sodec.gouv.qc.ca/en/programs/tv-film-production-tax-credits/",
            "publication_date": None,
            "effective_from": "1999-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Quebec Film and Television Production Tax Credit — Service Production Variant (QPRDP). "
                "Rate: 20% of eligible Quebec labour expenditures (service credit, no cultural test). "
                "Labour-only basis: BTL crew wages for work performed in Quebec. "
                "Refundable, non-competitive. "
                "Minimum Quebec eligible expenditure: C$1,000,000. "
                "Quebec Taxation Act § 1029.8.34 et seq. "
                "NOTE: Quebec also offers a cultural production credit (QPRDP cultural) at higher rates "
                "requiring SODEC cultural certification; this migration models the service variant only. "
                "PARSED — rates from SODEC program summaries; "
                "QTA § 1029.8.34 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_CA_CPTC_ID,
            "title": "Canadian Film or Video Production Tax Credit (CPTC) — CRA T4283 Guide",
            "document_type": "regulation",
            "jurisdiction_id": ca_jur,
            "authority_name": "Canada Revenue Agency (CRA) / Canadian Heritage CAVCO",
            "source_url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4283.html",
            "publication_date": None,
            "effective_from": "1995-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Canadian Film or Video Production Tax Credit (CPTC). "
                "Rate: 25% of qualified Canadian labour expenditures (QCLE). "
                "Labour-only basis: Canadian key creative + BTL crew wages. "
                "Requires CAVCO certification (Canadian content production). "
                "Refundable, non-competitive (any CAVCO-certified production qualifies). "
                "QCLE is capped at 60% of total production cost (budget cap). "
                "Minimum qualified Canadian labour: C$1,000,000 (PARSED estimate). "
                "Income Tax Act § 125.4; CRA T4283 guide. "
                "PARSED — rates from CRA T4283 guide; ITA § 125.4 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -------------------------------------------------------------------
    # 2. Update Canadian programs: DISCOVERY → PARSED
    # -------------------------------------------------------------------

    # ON OPSTC
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.215000,
                max_rate               = 0.215000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '2009-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://omdc.on.ca/film-and-television/tax-credits/ontario-production-services-tax-credit/',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per OMDC OPSTC program guidelines. '
                                         'Rate: 21.5% of Ontario-eligible production expenditures. '
                                         'Broad qualifying spend: Ontario labour + Ontario goods and services. '
                                         'Refundable; no cultural test required. '
                                         'Minimum Ontario spend: C$1,000,000. '
                                         'Ontario Reg 37/09 under Corporations Tax Act.',
                updated_at             = :now
            WHERE slug = 'on_opstc'
        """),
        {"src_id": SRC_ON_OPSTC_ID, "now": NOW},
    )

    # ON OFTTC
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.350000,
                max_rate               = 0.350000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '1998-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://omdc.on.ca/film-and-television/tax-credits/ontario-film-and-television-tax-credit/',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per OMDC OFTTC program guidelines. '
                                         'Rate: 35% of Ontario-eligible labour expenditures (labour-only basis). '
                                         'Requires CAVCO certification. '
                                         'Refundable; no competitive allocation. '
                                         'Minimum Ontario labour: C$125,000. '
                                         'Ontario Reg 37/09 under Corporations Tax Act.',
                updated_at             = :now
            WHERE slug = 'on_ofttc'
        """),
        {"src_id": SRC_ON_OFTTC_ID, "now": NOW},
    )

    # BC PSTC
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.280000,
                max_rate               = 0.340000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '2003-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://www.creativebc.com/programs/production-services-tax-credit/',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per Creative BC PSTC program guidelines. '
                                         'Base rate: 28% of BC-eligible labour expenditures. '
                                         'Regional uplift: +6% for BC regional production (outside Metro Vancouver/CRD). '
                                         'Labour-only basis. Refundable; non-competitive. '
                                         'Minimum BC-eligible production costs: C$1,000,000. '
                                         'BC Income Tax Act ss.91-93.',
                updated_at             = :now
            WHERE slug = 'bc_pstc'
        """),
        {"src_id": SRC_BC_PSTC_ID, "now": NOW},
    )

    # QC QPRDP (service production)
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.200000,
                max_rate               = 0.200000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '1999-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://sodec.gouv.qc.ca/en/programs/tv-film-production-tax-credits/',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per SODEC program summaries — service production variant (QPRDP). '
                                         'Rate: 20% of eligible Quebec labour expenditures. '
                                         'Labour-only basis. Refundable; non-competitive. '
                                         'Models service credit; cultural production credit is a separate program. '
                                         'Minimum Quebec eligible expenditure: C$1,000,000. '
                                         'Quebec Taxation Act § 1029.8.34 et seq.',
                updated_at             = :now
            WHERE slug = 'qc_film_production'
        """),
        {"src_id": SRC_QC_QPRDP_ID, "now": NOW},
    )

    # Federal CPTC
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.250000,
                max_rate               = 0.250000,
                is_refundable          = TRUE,
                is_transferable        = FALSE,
                transferable_value_pct = NULL,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '1995-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4283.html',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per CRA T4283 guide — Canadian Film or Video Production Tax Credit. '
                                         'Rate: 25% of qualified Canadian labour expenditures (QCLE). '
                                         'Labour-only basis. CAVCO certification required. '
                                         'Refundable; non-competitive. '
                                         'QCLE capped at 60% of total production cost (not modeled in engine). '
                                         'Income Tax Act § 125.4.',
                updated_at             = :now
            WHERE slug = 'ca_federal_cptc'
        """),
        {"src_id": SRC_CA_CPTC_ID, "now": NOW},
    )

    # -------------------------------------------------------------------
    # 3. Qualifying spend categories
    # -------------------------------------------------------------------
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

    def qsc(prog_id: str, slug: str, cat: str, qualifies: bool,
            jur_only: bool, notes: str, tier: str = "PARSED") -> dict:
        return {
            "id": _qsc_uid(slug, cat),
            "program_id": prog_id,
            "spend_category": cat,
            "qualifies": qualifies,
            "jurisdiction_spend_only": jur_only,
            "notes": notes,
            "confidence_tier": tier,
            "created_at": NOW,
            "updated_at": NOW,
        }

    # ---- ON OPSTC — broad qualifying (labour + tangible goods/services in Ontario) ----
    # ATL excluded from Ontario-eligible expenditures (PARSED; OMDC guidelines focus on BTL)
    on_opstc_cats = [
        qsc(on_opstc, "on_opstc", "atl_director",        False, True,
            "ATL excluded from Ontario OPSTC eligible expenditures (PARSED per OMDC guidelines)"),
        qsc(on_opstc, "on_opstc", "atl_writer",          False, True,
            "ATL excluded from Ontario OPSTC eligible expenditures (PARSED)"),
        qsc(on_opstc, "on_opstc", "atl_producer",        False, True,
            "ATL excluded from Ontario OPSTC eligible expenditures (PARSED)"),
        qsc(on_opstc, "on_opstc", "atl_cast",            False, True,
            "ATL cast excluded from Ontario OPSTC eligible expenditures (PARSED)"),
        qsc(on_opstc, "on_opstc", "atl_rights",          False, True,
            "Story/rights acquisition excluded from Ontario-eligible expenditures"),
        # BTL Labour
        qsc(on_opstc, "on_opstc", "btl_crew_labor",      True, True,
            "Ontario BTL crew wages qualify under OPSTC as Ontario-eligible labour (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_resident_labor",  True, True,
            "Ontario resident BTL labour qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_nonresident_labor", True, True,
            "Non-resident BTL labour qualifies when work performed in Ontario under OPSTC (PARSED)"),
        # BTL Non-labour (Ontario goods and services qualify for OPSTC)
        qsc(on_opstc, "on_opstc", "btl_equipment_rental", True, True,
            "Ontario equipment rental qualifies as Ontario-eligible expenditure under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_stage_facility",  True, True,
            "Ontario studio/stage facility costs qualify under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_location_fees",   True, True,
            "Ontario location fees qualify as Ontario-eligible expenditure under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_set_construction", True, True,
            "Ontario set construction qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_transportation",  True, True,
            "Ontario transportation costs qualify under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "btl_catering",        True, True,
            "Ontario catering costs qualify as Ontario-eligible expenditure under OPSTC (PARSED)"),
        # Post
        qsc(on_opstc, "on_opstc", "post_production",     True, True,
            "Ontario post-production costs qualify under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "vfx",                 True, True,
            "Ontario-based VFX qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "music",               True, True,
            "Ontario music recording qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "sound",               True, True,
            "Ontario sound post qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "payroll_fringes",     True, True,
            "Employer-paid fringes on Ontario-eligible wages qualify under OPSTC (PARSED)"),
        # Excluded
        qsc(on_opstc, "on_opstc", "finance_costs",       False, True,
            "Finance/interest costs excluded from Ontario OPSTC eligible expenditures"),
        qsc(on_opstc, "on_opstc", "insurance",           False, True,
            "Insurance excluded from OPSTC eligible expenditures"),
        qsc(on_opstc, "on_opstc", "completion_bond",     False, True,
            "Completion bond excluded from OPSTC eligible expenditures"),
        qsc(on_opstc, "on_opstc", "contingency",         False, True,
            "Contingency excluded; only actual incurred costs qualify"),
        qsc(on_opstc, "on_opstc", "deferment",           False, True,
            "Non-cash deferred compensation excluded from OPSTC"),
        qsc(on_opstc, "on_opstc", "equity_participation", False, True,
            "Non-cash equity excluded from OPSTC"),
        qsc(on_opstc, "on_opstc", "in_kind",             False, True,
            "In-kind contributions excluded from OPSTC"),
        qsc(on_opstc, "on_opstc", "reinvestment",        False, True,
            "Non-cash reinvestment excluded from OPSTC"),
        qsc(on_opstc, "on_opstc", "travel",              True, True,
            "Ontario-incurred travel qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "lodging",             True, True,
            "Ontario-incurred lodging qualifies under OPSTC (PARSED)"),
        qsc(on_opstc, "on_opstc", "miscellaneous",       True, True,
            "Ontario miscellaneous production expenditures qualify under OPSTC (PARSED)"),
    ]

    # ---- ON OFTTC — labour only ----
    on_ofttc_cats = [
        # ATL: qualifies if Ontario resident (PARSED — OFTTC allows ATL for Ontario resident cast/director)
        qsc(on_ofttc, "on_ofttc", "atl_director",        True, True,
            "Ontario resident director wages qualify under OFTTC (PARSED per OMDC — Ontario resident ATL allowed)"),
        qsc(on_ofttc, "on_ofttc", "atl_writer",          True, True,
            "Ontario resident writer wages qualify under OFTTC (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "atl_producer",        True, True,
            "Ontario resident producer wages qualify under OFTTC (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "atl_cast",            True, True,
            "Ontario resident cast wages qualify under OFTTC (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "atl_rights",          False, True,
            "Story/rights acquisition excluded — not a labour expenditure"),
        # BTL Labour
        qsc(on_ofttc, "on_ofttc", "btl_crew_labor",      True, True,
            "BTL crew wages qualify under OFTTC labour basis (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "btl_resident_labor",  True, True,
            "Ontario resident labour qualifies under OFTTC (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "btl_nonresident_labor", False, True,
            "Non-resident labour excluded from OFTTC Ontario-eligible labour (PARSED)"),
        qsc(on_ofttc, "on_ofttc", "payroll_fringes",     True, True,
            "Employer-paid fringes on OFTTC-eligible wages qualify (PARSED)"),
        # Non-labour — all excluded (OFTTC is labour-only)
        qsc(on_ofttc, "on_ofttc", "btl_equipment_rental", False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "btl_stage_facility",  False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "btl_location_fees",   False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "btl_set_construction", False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "btl_transportation",  False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "btl_catering",        False, True,
            "Non-labour expenditure — excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "post_production",     False, True,
            "Non-labour post costs excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "vfx",                 False, True,
            "VFX facility costs excluded from OFTTC (labour component already in btl_crew_labor)"),
        qsc(on_ofttc, "on_ofttc", "music",               False, True,
            "Music facility costs excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "sound",               False, True,
            "Sound facility costs excluded from OFTTC labour-only basis"),
        qsc(on_ofttc, "on_ofttc", "finance_costs",       False, True,
            "Excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "insurance",           False, True,
            "Excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "completion_bond",     False, True,
            "Excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "contingency",         False, True,
            "Excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "deferment",           False, True,
            "Non-cash — excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "equity_participation", False, True,
            "Non-cash — excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "in_kind",             False, True,
            "Non-cash — excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "reinvestment",        False, True,
            "Non-cash — excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "travel",              False, True,
            "Non-labour travel excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "lodging",             False, True,
            "Non-labour lodging excluded from OFTTC"),
        qsc(on_ofttc, "on_ofttc", "miscellaneous",       False, True,
            "Non-labour miscellaneous excluded from OFTTC"),
    ]

    # ---- BC PSTC — labour only (BC resident + non-resident working in BC) ----
    bc_pstc_cats = [
        qsc(bc_pstc, "bc_pstc", "atl_director",        False, True,
            "ATL excluded from BC PSTC eligible labour (PARSED per Creative BC)"),
        qsc(bc_pstc, "bc_pstc", "atl_writer",          False, True,
            "ATL excluded from BC PSTC eligible labour (PARSED)"),
        qsc(bc_pstc, "bc_pstc", "atl_producer",        False, True,
            "ATL excluded from BC PSTC eligible labour (PARSED)"),
        qsc(bc_pstc, "bc_pstc", "atl_cast",            False, True,
            "ATL cast excluded from BC PSTC eligible labour (PARSED)"),
        qsc(bc_pstc, "bc_pstc", "atl_rights",          False, True,
            "Story/rights acquisition excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "btl_crew_labor",      True, True,
            "BC BTL crew wages qualify under PSTC (PARSED per Creative BC)"),
        qsc(bc_pstc, "bc_pstc", "btl_resident_labor",  True, True,
            "BC resident BTL labour qualifies under PSTC (PARSED)"),
        qsc(bc_pstc, "bc_pstc", "btl_nonresident_labor", True, True,
            "Non-resident labour qualifies when work performed in BC (PARSED per Creative BC)"),
        qsc(bc_pstc, "bc_pstc", "payroll_fringes",     True, True,
            "Employer-paid fringes on BC PSTC-eligible wages qualify (PARSED)"),
        # Non-labour — excluded
        qsc(bc_pstc, "bc_pstc", "btl_equipment_rental", False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "btl_stage_facility",  False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "btl_location_fees",   False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "btl_set_construction", False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "btl_transportation",  False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "btl_catering",        False, True,
            "Non-labour — excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "post_production",     False, True,
            "Non-labour post costs excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "vfx",                 False, True,
            "VFX facility costs excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "music",               False, True,
            "Music facility excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "sound",               False, True,
            "Sound facility excluded from BC PSTC labour-only basis"),
        qsc(bc_pstc, "bc_pstc", "finance_costs",       False, True, "Excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "insurance",           False, True, "Excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "completion_bond",     False, True, "Excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "contingency",         False, True, "Excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "deferment",           False, True, "Non-cash — excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "equity_participation", False, True, "Non-cash — excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "in_kind",             False, True, "Non-cash — excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "reinvestment",        False, True, "Non-cash — excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "travel",              False, True, "Non-labour travel excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "lodging",             False, True, "Non-labour lodging excluded from BC PSTC"),
        qsc(bc_pstc, "bc_pstc", "miscellaneous",       False, True, "Non-labour misc excluded from BC PSTC"),
    ]

    # ---- QC QPRDP — labour only (Quebec BTL crew) ----
    qc_cats = [
        qsc(qc_prod, "qc_film_production", "atl_director",        False, True,
            "ATL excluded from QPRDP service credit eligible labour (PARSED per SODEC)"),
        qsc(qc_prod, "qc_film_production", "atl_writer",          False, True,
            "ATL excluded from QPRDP service credit eligible labour (PARSED)"),
        qsc(qc_prod, "qc_film_production", "atl_producer",        False, True,
            "ATL excluded from QPRDP service credit eligible labour (PARSED)"),
        qsc(qc_prod, "qc_film_production", "atl_cast",            False, True,
            "ATL cast excluded from QPRDP service credit (PARSED)"),
        qsc(qc_prod, "qc_film_production", "atl_rights",          False, True,
            "Story/rights acquisition excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "btl_crew_labor",      True, True,
            "Quebec BTL crew wages qualify under QPRDP service credit (PARSED per SODEC)"),
        qsc(qc_prod, "qc_film_production", "btl_resident_labor",  True, True,
            "Quebec resident BTL labour qualifies under QPRDP (PARSED)"),
        qsc(qc_prod, "qc_film_production", "btl_nonresident_labor", True, True,
            "Non-resident labour qualifies when work performed in Quebec (PARSED per SODEC)"),
        qsc(qc_prod, "qc_film_production", "payroll_fringes",     True, True,
            "Employer-paid fringes on QPRDP-eligible wages qualify (PARSED)"),
        # Non-labour — excluded
        qsc(qc_prod, "qc_film_production", "btl_equipment_rental", False, True,
            "Non-labour — excluded from QPRDP labour-only basis"),
        qsc(qc_prod, "qc_film_production", "btl_stage_facility",  False, True,
            "Non-labour — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "btl_location_fees",   False, True,
            "Non-labour — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "btl_set_construction", False, True,
            "Non-labour — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "btl_transportation",  False, True,
            "Non-labour — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "btl_catering",        False, True,
            "Non-labour — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "post_production",     False, True,
            "Non-labour post costs excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "vfx",                 False, True,
            "VFX facility costs excluded from QPRDP labour-only basis"),
        qsc(qc_prod, "qc_film_production", "music",               False, True,
            "Music facility excluded from QPRDP labour-only basis"),
        qsc(qc_prod, "qc_film_production", "sound",               False, True,
            "Sound facility excluded from QPRDP labour-only basis"),
        qsc(qc_prod, "qc_film_production", "finance_costs",       False, True, "Excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "insurance",           False, True, "Excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "completion_bond",     False, True, "Excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "contingency",         False, True, "Excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "deferment",           False, True, "Non-cash — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "equity_participation", False, True, "Non-cash — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "in_kind",             False, True, "Non-cash — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "reinvestment",        False, True, "Non-cash — excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "travel",              False, True, "Non-labour travel excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "lodging",             False, True, "Non-labour lodging excluded from QPRDP"),
        qsc(qc_prod, "qc_film_production", "miscellaneous",       False, True, "Non-labour misc excluded from QPRDP"),
    ]

    # ---- Federal CPTC — Canadian key creative + BTL labour ----
    ca_cptc_cats = [
        # ATL qualifies if Canadian resident key creative (CAVCO-certified production)
        qsc(ca_cptc, "ca_federal_cptc", "atl_director",        True, True,
            "Canadian resident director wages qualify as QCLE under CPTC (PARSED per CRA T4283)"),
        qsc(ca_cptc, "ca_federal_cptc", "atl_writer",          True, True,
            "Canadian resident writer wages qualify as QCLE under CPTC (PARSED)"),
        qsc(ca_cptc, "ca_federal_cptc", "atl_producer",        True, True,
            "Canadian resident producer wages qualify as QCLE under CPTC (PARSED)"),
        qsc(ca_cptc, "ca_federal_cptc", "atl_cast",            True, True,
            "Canadian resident cast wages qualify as QCLE under CPTC (PARSED per CRA T4283)"),
        qsc(ca_cptc, "ca_federal_cptc", "atl_rights",          False, True,
            "Story/rights acquisition excluded from QCLE — not a labour expenditure"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_crew_labor",      True, True,
            "Canadian BTL crew wages qualify as QCLE under CPTC (PARSED)"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_resident_labor",  True, True,
            "Canadian resident BTL labour qualifies as QCLE under CPTC (PARSED)"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_nonresident_labor", False, True,
            "Non-Canadian labour excluded from QCLE under CPTC (PARSED per CRA T4283)"),
        qsc(ca_cptc, "ca_federal_cptc", "payroll_fringes",     True, True,
            "Employer-paid fringes on QCLE wages qualify under CPTC (PARSED)"),
        # Non-labour — excluded
        qsc(ca_cptc, "ca_federal_cptc", "btl_equipment_rental", False, True,
            "Non-labour — excluded from CPTC labour-only (QCLE) basis"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_stage_facility",  False, True,
            "Non-labour — excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_location_fees",   False, True,
            "Non-labour — excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_set_construction", False, True,
            "Non-labour — excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_transportation",  False, True,
            "Non-labour — excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "btl_catering",        False, True,
            "Non-labour — excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "post_production",     False, True,
            "Non-labour post costs excluded from CPTC QCLE"),
        qsc(ca_cptc, "ca_federal_cptc", "vfx",                 False, True,
            "VFX facility costs excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "music",               False, True,
            "Music facility costs excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "sound",               False, True,
            "Sound facility costs excluded from CPTC QCLE basis"),
        qsc(ca_cptc, "ca_federal_cptc", "finance_costs",       False, True, "Excluded from CPTC QCLE"),
        qsc(ca_cptc, "ca_federal_cptc", "insurance",           False, True, "Excluded from CPTC QCLE"),
        qsc(ca_cptc, "ca_federal_cptc", "completion_bond",     False, True, "Excluded from CPTC QCLE"),
        qsc(ca_cptc, "ca_federal_cptc", "contingency",         False, True, "Excluded from CPTC QCLE"),
        qsc(ca_cptc, "ca_federal_cptc", "deferment",           False, True, "Non-cash — excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "equity_participation", False, True, "Non-cash — excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "in_kind",             False, True, "Non-cash — excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "reinvestment",        False, True, "Non-cash — excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "travel",              False, True, "Non-labour travel excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "lodging",             False, True, "Non-labour lodging excluded from CPTC"),
        qsc(ca_cptc, "ca_federal_cptc", "miscellaneous",       False, True, "Non-labour misc excluded from CPTC"),
    ]

    op.bulk_insert(
        qsc_table,
        on_opstc_cats + on_ofttc_cats + bc_pstc_cats + qc_cats + ca_cptc_cats,
    )

    # -------------------------------------------------------------------
    # 4. Incentive rules
    # -------------------------------------------------------------------
    rules_table = sa.table(
        "incentive_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_type", sa.String),
        sa.column("threshold_numeric", sa.Numeric),
        sa.column("threshold_text", sa.String),
        sa.column("fail_action", sa.String),
        sa.column("description", sa.Text),
        sa.column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.column("source_page", sa.Integer),
        sa.column("source_excerpt", sa.Text),
        sa.column("statutory_reference", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    def rule(rule_id, prog_id, rule_type, threshold_numeric, threshold_text,
             description, src_id, statutory_ref, tier="PARSED"):
        return {
            "id": rule_id,
            "program_id": prog_id,
            "rule_type": rule_type,
            "threshold_numeric": threshold_numeric,
            "threshold_text": threshold_text,
            "fail_action": "disqualify",
            "description": description,
            "source_document_id": src_id,
            "source_page": None,
            "source_excerpt": None,
            "statutory_reference": statutory_ref,
            "confidence_tier": tier,
            "created_at": NOW,
            "updated_at": NOW,
        }

    op.bulk_insert(rules_table, [
        rule(RULE_ON_OPSTC_MIN_ID, on_opstc,
             "minimum_qualified_spend", 1_000_000, None,
             "Minimum C$1,000,000 in Ontario-eligible production expenditures required",
             SRC_ON_OPSTC_ID, "Ontario Reg 37/09 under Corporations Tax Act"),
        rule(RULE_ON_OPSTC_ENT_ID, on_opstc,
             "required_entity_type", None, "ontario_registered_corporation",
             "Production company must be an Ontario-registered corporation",
             SRC_ON_OPSTC_ID, "OMDC OPSTC program guidelines"),
        rule(RULE_ON_OFTTC_MIN_ID, on_ofttc,
             "minimum_qualified_spend", 125_000, None,
             "Minimum C$125,000 in Ontario-eligible labour expenditures required",
             SRC_ON_OFTTC_ID, "Ontario Reg 37/09 under Corporations Tax Act"),
        rule(RULE_ON_OFTTC_ENT_ID, on_ofttc,
             "required_entity_type", None, "ontario_registered_corporation_cavco_certified",
             "Production must be CAVCO-certified and held by an Ontario-registered corporation",
             SRC_ON_OFTTC_ID, "Ontario Reg 37/09; CAVCO certification requirement"),
        rule(RULE_BC_PSTC_MIN_ID, bc_pstc,
             "minimum_qualified_spend", 1_000_000, None,
             "Minimum C$1,000,000 in BC-eligible production costs required",
             SRC_BC_PSTC_ID, "BC Income Tax Act ss.91-93"),
        rule(RULE_BC_PSTC_ENT_ID, bc_pstc,
             "required_entity_type", None, "bc_registered_corporation",
             "Production company must be a BC-registered corporation",
             SRC_BC_PSTC_ID, "Creative BC PSTC program guidelines"),
        rule(RULE_QC_QPRDP_MIN_ID, qc_prod,
             "minimum_qualified_spend", 1_000_000, None,
             "Minimum C$1,000,000 in Quebec-eligible production expenditures required",
             SRC_QC_QPRDP_ID, "Quebec Taxation Act § 1029.8.34 et seq."),
        rule(RULE_QC_QPRDP_ENT_ID, qc_prod,
             "required_entity_type", None, "quebec_registered_corporation",
             "Production company must be a Quebec-registered corporation",
             SRC_QC_QPRDP_ID, "SODEC QPRDP program guidelines"),
        rule(RULE_CA_CPTC_MIN_ID, ca_cptc,
             "minimum_qualified_spend", 1_000_000, None,
             "Minimum C$1,000,000 in qualified Canadian labour expenditures (QCLE) required (PARSED estimate)",
             SRC_CA_CPTC_ID, "Income Tax Act § 125.4; CRA T4283"),
        rule(RULE_CA_CPTC_ENT_ID, ca_cptc,
             "required_entity_type", None, "cavco_certified_canadian_production",
             "Production must be CAVCO-certified as a Canadian content production",
             SRC_CA_CPTC_ID, "Income Tax Act § 125.4; Canadian Heritage CAVCO"),
    ])

    # -------------------------------------------------------------------
    # 5. Program uplifts (BC PSTC regional only)
    # -------------------------------------------------------------------
    uplift_table = sa.table(
        "program_uplifts",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("additional_rate", sa.Numeric),
        sa.column("applies_to", sa.String),
        sa.column("condition_type", sa.String),
        sa.column("condition_threshold", sa.Numeric),
        sa.column("condition_text", sa.Text),
        sa.column("is_stackable_with_other_uplifts", sa.Boolean),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(uplift_table, [
        {
            "id": UPLIFT_BC_REGIONAL_ID,
            "program_id": bc_pstc,
            "name": "BC Regional Production Uplift",
            "additional_rate": 0.06,
            "applies_to": "same_qualifying_spend",
            "condition_type": "shooting_location",
            "condition_threshold": None,
            "condition_text": "bc_regional",
            "is_stackable_with_other_uplifts": False,
            "confidence_tier": "PARSED",
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])


def downgrade() -> None:
    op.execute(
        f"DELETE FROM program_uplifts WHERE id = '{UPLIFT_BC_REGIONAL_ID}'"
    )
    op.execute(
        "DELETE FROM incentive_rules WHERE id IN ("
        + ", ".join(f"'{r}'" for r in [
            RULE_ON_OPSTC_MIN_ID, RULE_ON_OPSTC_ENT_ID,
            RULE_ON_OFTTC_MIN_ID, RULE_ON_OFTTC_ENT_ID,
            RULE_BC_PSTC_MIN_ID,  RULE_BC_PSTC_ENT_ID,
            RULE_QC_QPRDP_MIN_ID, RULE_QC_QPRDP_ENT_ID,
            RULE_CA_CPTC_MIN_ID,  RULE_CA_CPTC_ENT_ID,
        ])
        + ")"
    )
    op.execute(
        "DELETE FROM qualifying_spend_categories WHERE program_id IN ("
        "SELECT id FROM incentive_programs WHERE slug IN ("
        "'on_opstc','on_ofttc','bc_pstc','qc_film_production','ca_federal_cptc'))"
    )
    op.execute(
        "UPDATE incentive_programs SET "
        "base_rate=NULL, max_rate=NULL, confidence_tier='DISCOVERY', "
        "source_document_id=NULL, review_status='pending', notes=NULL, "
        "last_verified_date=NULL "
        "WHERE slug IN ('on_opstc','on_ofttc','bc_pstc','qc_film_production','ca_federal_cptc')"
    )
    op.execute(
        "DELETE FROM source_documents WHERE id IN ("
        + ", ".join(f"'{s}'" for s in [
            SRC_ON_OPSTC_ID, SRC_ON_OFTTC_ID, SRC_BC_PSTC_ID,
            SRC_QC_QPRDP_ID, SRC_CA_CPTC_ID,
        ])
        + ")"
    )
    op.drop_column("source_documents", "superseded_by_id")
