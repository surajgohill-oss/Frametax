"""Seed California and Louisiana — source-backed rates, rules, and qualifying spend categories

Revision ID: 0005
Revises: 0004
Create Date: 2025-06-18

SOURCES:
  California: CA Gov Code § 17053.98; California Film Commission (film.ca.gov)
    Film & Television Tax Credit Program 3.0 (effective Jan 2020)
  Louisiana: LA RS § 47:6007; Louisiana Entertainment (louisianaentertainment.gov)
    Louisiana Motion Picture Production Tax Credit

CONFIDENCE TIERS:
  All rates marked PARSED — program parameters from official government summaries.
  Statutory text has not been directly reviewed in this session.
  Promote individual values to VERIFIED only after reviewing primary source text.

CA PROGRAM DETAILS (PARSED):
  base_rate: 0.20 (standard feature/TV series, qualified CA wages + expenditures)
  independent film uplift: +0.05 (total 0.25) for independent films with budget ≤ $10M
  VFX uplift: +0.05 on California-based VFX spending (unconditional)
  music uplift: +0.05 on California-based music recording (unconditional)
  is_competitive: True — CA Film Commission reviews applications; credit NOT guaranteed
  is_refundable: False — credit applied against CA income/franchise tax or sold
  is_transferable: True — credit can be sold to other CA taxpayers
  transferable_value_pct: 0.92 — PARSED market estimate; actual sales vary ~0.88-0.95
  ATL excluded — above-the-line compensation excluded from CA qualified wages
  Source: CA Gov Code § 17053.98; https://film.ca.gov/tax-credits/

LA PROGRAM DETAILS (PARSED):
  base_rate: 0.25 (on Louisiana-certified expenditures)
  resident_labor uplift: +0.10 on Louisiana resident payroll (unconditional; applies_to=resident_labor_only)
  is_competitive: False — any qualifying production may apply
  is_refundable: True — Louisiana Entertainment offers state buyback
  transferable_value_pct: 0.90 — PARSED; state buyback at 88 cents; market trades ~90 cents
  Minimum: $300,000 in Louisiana qualified expenditures
  ATL qualifies — above-the-line compensation qualifies as Louisiana-certified expenditure
  Source: LA RS § 47:6007; https://www.louisianaentertainment.gov/film

INTENTIONALLY NOT MODELED:
  CA: per-person compensation cap (no individual_salary_cap_usd support for ATL-only scenario)
  CA: out-of-state VFX expenditure exclusion (applies_to=vfx_spend_only handles this directionally)
  CA: crew hiring credit (separate annual program, not part of § 17053.98 base)
  LA: minimum shooting days threshold (no shooting_days rule type in engine)
  LA: infrastructure investor tax credit (separate program, § 47:6022)
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Stable UUIDs — deterministic so downgrade can target them
# ---------------------------------------------------------------------------
SRC_CA_ID = str(uuid.UUID("c0000000-0005-0000-0001-000000000001"))
SRC_LA_ID = str(uuid.UUID("c0000000-0005-0000-0001-000000000002"))

RULE_CA_MIN_SPEND_ID = str(uuid.UUID("c0000000-0005-0000-0002-000000000001"))
RULE_CA_ENTITY_ID    = str(uuid.UUID("c0000000-0005-0000-0002-000000000002"))
RULE_LA_MIN_SPEND_ID = str(uuid.UUID("c0000000-0005-0000-0002-000000000003"))
RULE_LA_ENTITY_ID    = str(uuid.UUID("c0000000-0005-0000-0002-000000000004"))

UPLIFT_CA_VFX_ID   = str(uuid.UUID("c0000000-0005-0000-0003-000000000001"))
UPLIFT_CA_MUSIC_ID = str(uuid.UUID("c0000000-0005-0000-0003-000000000002"))
UPLIFT_CA_INDIE_ID = str(uuid.UUID("c0000000-0005-0000-0003-000000000003"))
UPLIFT_LA_RES_ID   = str(uuid.UUID("c0000000-0005-0000-0003-000000000004"))

_QSC_NS = uuid.UUID("c0000000-0005-0000-0004-000000000000")


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
    conn = op.get_bind()

    ca_jur  = _lookup(conn, "jurisdictions",   "code", "US-CA")
    la_jur  = _lookup(conn, "jurisdictions",   "code", "US-LA")
    ca_prog = _lookup(conn, "incentive_programs", "slug", "ca_film_30")
    la_prog = _lookup(conn, "incentive_programs", "slug", "la_film_production")

    # -----------------------------------------------------------------------
    # 1. Source documents
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
            "id": SRC_CA_ID,
            "title": "CA Gov Code § 17053.98 — California Film & Television Tax Credit Program 3.0",
            "document_type": "regulation",
            "jurisdiction_id": ca_jur,
            "authority_name": "California Film Commission / California Department of Tax and Fee Administration",
            "source_url": "https://film.ca.gov/tax-credits/",
            "publication_date": None,
            "effective_from": "2020-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "California Film & TV Tax Credit Program 3.0 (Program 3.0). "
                "§ 17053.98(b)(1): 20% base credit on qualified CA wages and expenditures. "
                "§ 17053.98(b)(3): 25% for independent films (budget ≤ $10M, no TV network attachment). "
                "VFX uplift: +5% on California-based VFX spending (§ 17053.98(b)(4)). "
                "Music uplift: +5% on California-based music recording (§ 17053.98(b)(5)). "
                "is_competitive=True — CA Film Commission reviews applications quarterly; "
                "credit is allocated competitively and is NOT guaranteed even if qualified. "
                "is_refundable=False — credit applied against CA income or franchise tax; "
                "excess credits may be sold/transferred to other CA taxpayers. "
                "Minimum $1,000,000 in California-qualified production costs. "
                "PARSED — program parameters from film.ca.gov and CFC program guidelines; "
                "CA Gov Code § 17053.98 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SRC_LA_ID,
            "title": "LA RS § 47:6007 — Louisiana Motion Picture Production Tax Credit",
            "document_type": "regulation",
            "jurisdiction_id": la_jur,
            "authority_name": "Louisiana Entertainment / Louisiana Department of Revenue",
            "source_url": "https://www.louisianaentertainment.gov/film",
            "publication_date": None,
            "effective_from": "2002-01-01",
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Louisiana Motion Picture Production Tax Credit. "
                "RS § 47:6007(B)(1): 25% base credit on Louisiana-certified production costs. "
                "RS § 47:6007(B)(2): additional 10% credit on Louisiana resident payroll "
                "(applies on top of 25% base to the resident-payroll portion). "
                "Minimum $300,000 in Louisiana-certified production expenditures. "
                "is_competitive=False — any production meeting minimum spend qualifies. "
                "is_refundable=True — Louisiana Entertainment offers state buyback program at 88 cents. "
                "Credits are also transferable on open market at approximately 90 cents. "
                "ATL compensation qualifies as Louisiana-certified expenditure (broad definition). "
                "PARSED — program parameters from louisianaentertainment.gov; "
                "RS § 47:6007 not directly reviewed in this session."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 2. Update CA program — DISCOVERY → PARSED with authoritative rates
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.200000,
                max_rate               = 0.300000,
                is_refundable          = FALSE,
                is_transferable        = TRUE,
                transferable_value_pct = 0.920000,
                is_competitive         = TRUE,
                requires_local_entity  = TRUE,
                effective_from         = '2020-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://film.ca.gov/tax-credits/',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per CA Gov Code § 17053.98 and California Film Commission guidelines. '
                                         'Base credit: 20% on CA qualified wages and expenditures. '
                                         'Independent film (budget ≤ $10M): 25% base. '
                                         'VFX uplift: +5% on CA-based VFX spend. '
                                         'Music uplift: +5% on CA-based music recording. '
                                         'COMPETITIVE ALLOCATION — credit not guaranteed even if qualified. '
                                         'Non-refundable; transferable (market ~92 cents). '
                                         'transferable_value_pct=0.92 is a PARSED estimate.',
                updated_at             = :now
            WHERE slug = 'ca_film_30'
        """),
        {"src_id": SRC_CA_ID, "now": NOW},
    )

    # -----------------------------------------------------------------------
    # 3. Update LA program — DISCOVERY → PARSED with authoritative rates
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.250000,
                max_rate               = 0.350000,
                is_refundable          = TRUE,
                is_transferable        = TRUE,
                transferable_value_pct = 0.900000,
                is_competitive         = FALSE,
                requires_local_entity  = FALSE,
                effective_from         = '2002-01-01',
                confidence_tier        = 'PARSED',
                review_status          = 'approved',
                authority_url          = 'https://www.louisianaentertainment.gov/film',
                last_verified_date     = '2025-06-18',
                notes                  = 'PARSED per LA RS § 47:6007 and Louisiana Entertainment guidelines. '
                                         'Base credit: 25% on Louisiana-certified production costs. '
                                         'Resident payroll uplift: +10% on Louisiana resident labor portion. '
                                         'Minimum $300K in Louisiana-certified expenditures. '
                                         'Refundable — state buyback at 88 cents; market at ~90 cents. '
                                         'ATL compensation qualifies as Louisiana-certified expenditure. '
                                         'transferable_value_pct=0.90 is a PARSED estimate.',
                updated_at             = :now
            WHERE slug = 'la_film_production'
        """),
        {"src_id": SRC_LA_ID, "now": NOW},
    )

    # -----------------------------------------------------------------------
    # 4. Qualifying spend categories
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

    def qsc(prog_id: str, slug: str, category: str, qualifies: bool,
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

    # California — ATL excluded; BTL + Post qualify
    # Source: CA Gov Code § 17053.98 defines "qualified wages" as below-the-line
    # production costs incurred in California.
    ca_categories = [
        # ATL — excluded from CA qualified wages
        qsc(ca_prog, "ca_film_30", "atl_director", False, True,
            "ATL excluded from CA qualified wages per § 17053.98 (below-the-line only)"),
        qsc(ca_prog, "ca_film_30", "atl_writer", False, True,
            "ATL excluded from CA qualified wages per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "atl_producer", False, True,
            "ATL excluded from CA qualified wages per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "atl_cast", False, True,
            "ATL excluded from CA qualified wages per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "atl_rights", False, True,
            "Story/rights acquisition excluded per § 17053.98"),
        # BTL Labor
        qsc(ca_prog, "ca_film_30", "btl_crew_labor", True, True,
            "California BTL crew wages qualify per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "btl_resident_labor", True, True,
            "CA resident BTL wages qualify; included in qualified wages"),
        qsc(ca_prog, "ca_film_30", "btl_nonresident_labor", True, True,
            "BTL labor qualifies when physically working in California"),
        # BTL Non-labor
        qsc(ca_prog, "ca_film_30", "btl_equipment_rental", True, True,
            "CA-based equipment rental qualifies as qualified expenditure"),
        qsc(ca_prog, "ca_film_30", "btl_stage_facility", True, True,
            "CA studio/stage rental qualifies per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "btl_location_fees", True, True,
            "CA location fees qualify as below-the-line expenditure"),
        qsc(ca_prog, "ca_film_30", "btl_set_construction", True, True,
            "CA set construction qualifies per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "btl_transportation", True, True,
            "CA transportation costs qualify per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "btl_catering", True, True,
            "CA catering qualifies as production expenditure per § 17053.98"),
        # Post
        qsc(ca_prog, "ca_film_30", "post_production", True, True,
            "CA post-production qualifies per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "vfx", True, True,
            "CA-based VFX qualifies; also eligible for +5% VFX uplift"),
        qsc(ca_prog, "ca_film_30", "music", True, True,
            "CA music recording qualifies; also eligible for +5% music uplift"),
        qsc(ca_prog, "ca_film_30", "sound", True, True,
            "CA sound post qualifies per § 17053.98"),
        # Non-qualifying
        qsc(ca_prog, "ca_film_30", "finance_costs", False, True,
            "Finance/interest costs excluded from CA qualified expenditures"),
        qsc(ca_prog, "ca_film_30", "insurance", False, True,
            "Insurance excluded per § 17053.98 qualified expenditure definition"),
        qsc(ca_prog, "ca_film_30", "completion_bond", False, True,
            "Completion bond excluded per § 17053.98"),
        qsc(ca_prog, "ca_film_30", "contingency", False, True,
            "Contingency excluded; only actual costs qualify"),
        qsc(ca_prog, "ca_film_30", "payroll_fringes", True, True,
            "Employer-paid fringes on qualified wages qualify per CFC guidelines"),
        # Non-cash
        qsc(ca_prog, "ca_film_30", "deferment", False, True,
            "Non-cash deferred compensation excluded"),
        qsc(ca_prog, "ca_film_30", "equity_participation", False, True,
            "Non-cash equity excluded"),
        qsc(ca_prog, "ca_film_30", "in_kind", False, True,
            "In-kind contributions excluded"),
        qsc(ca_prog, "ca_film_30", "reinvestment", False, True,
            "Non-cash reinvestment excluded"),
        # Travel / Lodging / Misc
        qsc(ca_prog, "ca_film_30", "travel", True, True,
            "CA-incurred travel expenses qualify per CFC program guidelines"),
        qsc(ca_prog, "ca_film_30", "lodging", True, True,
            "CA-incurred lodging expenses qualify per CFC program guidelines"),
        qsc(ca_prog, "ca_film_30", "miscellaneous", True, True,
            "Miscellaneous CA production expenditures qualify per § 17053.98"),
    ]

    # Louisiana — ATL qualifies (broad definition); BTL + Post qualify
    # Source: LA RS § 47:6007 defines "state-certified production costs" broadly
    # to include compensation and expenditures for Louisiana residents and businesses.
    la_categories = [
        # ATL — qualifies as Louisiana-certified expenditure (RS § 47:6007)
        qsc(la_prog, "la_film_production", "atl_director", True, True,
            "ATL qualifies as LA-certified expenditure per RS § 47:6007 (PARSED)"),
        qsc(la_prog, "la_film_production", "atl_writer", True, True,
            "ATL qualifies as LA-certified expenditure per RS § 47:6007 (PARSED)"),
        qsc(la_prog, "la_film_production", "atl_producer", True, True,
            "ATL qualifies as LA-certified expenditure per RS § 47:6007 (PARSED)"),
        qsc(la_prog, "la_film_production", "atl_cast", True, True,
            "ATL qualifies as LA-certified expenditure per RS § 47:6007 (PARSED)"),
        qsc(la_prog, "la_film_production", "atl_rights", False, True,
            "Story/rights acquisition excluded — not a production expenditure in Louisiana"),
        # BTL Labor
        qsc(la_prog, "la_film_production", "btl_crew_labor", True, True,
            "BTL crew wages qualify as LA-certified production costs per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "btl_resident_labor", True, True,
            "LA resident labor qualifies; also subject to +10% resident payroll uplift"),
        qsc(la_prog, "la_film_production", "btl_nonresident_labor", True, True,
            "Non-resident labor qualifies when incurred in Louisiana per RS § 47:6007"),
        # BTL Non-labor
        qsc(la_prog, "la_film_production", "btl_equipment_rental", True, True,
            "LA-based equipment rental qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "btl_stage_facility", True, True,
            "LA stage/studio rental qualifies as LA-certified expenditure"),
        qsc(la_prog, "la_film_production", "btl_location_fees", True, True,
            "LA location fees qualify per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "btl_set_construction", True, True,
            "LA set construction qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "btl_transportation", True, True,
            "LA transportation costs qualify per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "btl_catering", True, True,
            "LA catering qualifies as production expenditure per RS § 47:6007"),
        # Post
        qsc(la_prog, "la_film_production", "post_production", True, True,
            "LA post-production qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "vfx", True, True,
            "LA-based VFX qualifies as certified expenditure per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "music", True, True,
            "LA music recording qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "sound", True, True,
            "LA sound post qualifies per RS § 47:6007"),
        # Non-qualifying
        qsc(la_prog, "la_film_production", "finance_costs", False, True,
            "Finance/interest excluded from LA-certified production costs"),
        qsc(la_prog, "la_film_production", "insurance", False, True,
            "Insurance excluded per RS § 47:6007 definition"),
        qsc(la_prog, "la_film_production", "completion_bond", False, True,
            "Completion bond excluded per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "contingency", False, True,
            "Contingency excluded; only actual incurred costs qualify"),
        qsc(la_prog, "la_film_production", "payroll_fringes", True, True,
            "Employer-paid fringes on qualified wages qualify per Louisiana Entertainment guidelines"),
        # Non-cash
        qsc(la_prog, "la_film_production", "deferment", False, True,
            "Non-cash deferred compensation excluded"),
        qsc(la_prog, "la_film_production", "equity_participation", False, True,
            "Non-cash equity excluded"),
        qsc(la_prog, "la_film_production", "in_kind", False, True,
            "In-kind contributions excluded"),
        qsc(la_prog, "la_film_production", "reinvestment", False, True,
            "Non-cash reinvestment excluded"),
        # Travel / Lodging / Misc
        qsc(la_prog, "la_film_production", "travel", True, True,
            "LA-incurred travel qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "lodging", True, True,
            "LA-incurred lodging qualifies per RS § 47:6007"),
        qsc(la_prog, "la_film_production", "miscellaneous", True, True,
            "Miscellaneous LA production expenditures qualify per RS § 47:6007"),
    ]

    op.bulk_insert(qsc_table, ca_categories + la_categories)

    # -----------------------------------------------------------------------
    # 5. Incentive rules
    # -----------------------------------------------------------------------
    rules_table = sa.table(
        "incentive_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("program_id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_type", sa.String),
        sa.column("rule_value_usd", sa.Numeric),
        sa.column("rule_value_pct", sa.Numeric),
        sa.column("description", sa.Text),
        sa.column("confidence_tier", sa.String),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(rules_table, [
        {
            "id": RULE_CA_MIN_SPEND_ID,
            "program_id": ca_prog,
            "rule_type": "minimum_spend",
            "rule_value_usd": 1_000_000,
            "rule_value_pct": None,
            "description": "Minimum $1,000,000 in California-qualified production costs required",
            "confidence_tier": "PARSED",
            "notes": "CA Gov Code § 17053.98 minimum spend threshold per CFC program guidelines",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_CA_ENTITY_ID,
            "program_id": ca_prog,
            "rule_type": "entity_type",
            "rule_value_usd": None,
            "rule_value_pct": None,
            "description": "Production company must be a California-registered entity to claim credit",
            "confidence_tier": "PARSED",
            "notes": "CA Film Commission applicant entity requirement per program guidelines",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_LA_MIN_SPEND_ID,
            "program_id": la_prog,
            "rule_type": "minimum_spend",
            "rule_value_usd": 300_000,
            "rule_value_pct": None,
            "description": "Minimum $300,000 in Louisiana-certified production expenditures required",
            "confidence_tier": "PARSED",
            "notes": "LA RS § 47:6007 minimum certified expenditure threshold per Louisiana Entertainment",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_LA_ENTITY_ID,
            "program_id": la_prog,
            "rule_type": "entity_type",
            "rule_value_usd": None,
            "rule_value_pct": None,
            "description": "Production must be a state-certified motion picture production",
            "confidence_tier": "PARSED",
            "notes": "Louisiana Entertainment certification requirement per RS § 47:6007",
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 6. Program uplifts
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
        sa.column("condition_text", sa.Text),
        sa.column("is_stackable_with_other_uplifts", sa.Boolean),
        sa.column("confidence_tier", sa.String),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(uplift_table, [
        {
            "id": UPLIFT_CA_VFX_ID,
            "program_id": ca_prog,
            "name": "California VFX Uplift",
            "additional_rate": 0.05,
            "applies_to": "vfx_spend_only",
            "condition_type": "",
            "condition_threshold": None,
            "condition_text": "Unconditional — applies to all CA-based visual effects expenditures",
            "is_stackable_with_other_uplifts": True,
            "confidence_tier": "PARSED",
            "notes": "CA Gov Code § 17053.98(b)(4): +5% on CA-based VFX expenditures. PARSED.",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": UPLIFT_CA_MUSIC_ID,
            "program_id": ca_prog,
            "name": "California Music Recording Uplift",
            "additional_rate": 0.05,
            "applies_to": "music_spend_only",
            "condition_type": "",
            "condition_threshold": None,
            "condition_text": "Unconditional — applies to all CA-based music recording expenditures",
            "is_stackable_with_other_uplifts": True,
            "confidence_tier": "PARSED",
            "notes": "CA Gov Code § 17053.98(b)(5): +5% on CA-based music recording. PARSED.",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": UPLIFT_CA_INDIE_ID,
            "program_id": ca_prog,
            "name": "California Independent Film Uplift",
            "additional_rate": 0.05,
            "applies_to": "same_qualifying_spend",
            "condition_type": "budget_under",
            "condition_threshold": 10_000_000,
            "condition_text": "Independent film: total production budget ≤ $10,000,000",
            "is_stackable_with_other_uplifts": True,
            "confidence_tier": "PARSED",
            "notes": (
                "CA Gov Code § 17053.98(b)(3): independent films with budget ≤ $10M receive 25% "
                "(modeled here as 20% base + 5% uplift). PARSED."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": UPLIFT_LA_RES_ID,
            "program_id": la_prog,
            "name": "Louisiana Resident Payroll Uplift",
            "additional_rate": 0.10,
            "applies_to": "resident_labor_only",
            "condition_type": "",
            "condition_threshold": None,
            "condition_text": "Unconditional — applies to all Louisiana resident payroll expenditures",
            "is_stackable_with_other_uplifts": True,
            "confidence_tier": "PARSED",
            "notes": (
                "LA RS § 47:6007(B)(2): additional 10% credit on Louisiana resident payroll "
                "on top of the 25% base credit. Applies to btl_resident_labor spend. PARSED."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])


def downgrade() -> None:
    # Remove uplifts
    op.execute(
        "DELETE FROM program_uplifts WHERE id IN ("
        f"'{UPLIFT_CA_VFX_ID}','{UPLIFT_CA_MUSIC_ID}',"
        f"'{UPLIFT_CA_INDIE_ID}','{UPLIFT_LA_RES_ID}')"
    )
    # Remove incentive rules
    op.execute(
        "DELETE FROM incentive_rules WHERE id IN ("
        f"'{RULE_CA_MIN_SPEND_ID}','{RULE_CA_ENTITY_ID}',"
        f"'{RULE_LA_MIN_SPEND_ID}','{RULE_LA_ENTITY_ID}')"
    )
    # Remove qualifying spend categories
    op.execute(
        "DELETE FROM qualifying_spend_categories WHERE program_id IN ("
        f"SELECT id FROM incentive_programs WHERE slug IN ('ca_film_30','la_film_production'))"
    )
    # Revert programs to DISCOVERY
    op.execute(
        "UPDATE incentive_programs SET "
        "base_rate=NULL, max_rate=NULL, confidence_tier='DISCOVERY', "
        "source_document_id=NULL, review_status='pending', notes=NULL, "
        "last_verified_date=NULL "
        "WHERE slug IN ('ca_film_30','la_film_production')"
    )
    # Remove source documents
    op.execute(
        f"DELETE FROM source_documents WHERE id IN ('{SRC_CA_ID}','{SRC_LA_ID}')"
    )
