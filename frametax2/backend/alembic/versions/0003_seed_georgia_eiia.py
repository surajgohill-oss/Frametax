"""Seed Georgia EIIA — source-backed rates, rules, and qualifying spend categories

Revision ID: 0003
Revises: 0002
Create Date: 2025-06-18

SOURCE:
  Official Code of Georgia Annotated (O.C.G.A.) § 48-7-40.26
  Georgia Department of Revenue — Entertainment Industry Investment Act
  Administrative Rules: Georgia Comp. R. & Regs. 560-7-8-.44
  Georgia Film Office Summary (https://www.georgia.org/film-in-georgia):
    - Base credit: 20% of Georgia qualified production costs
    - Logo uplift: additional 10% (total 30%) when approved Georgia logo is included
    - Minimum total budget: $500,000 in Georgia qualified production costs
    - Per-person cap: $500,000 per individual for above-the-line compensation
    - Non-refundable; fully transferable at market (historically 88–92 cents)
    - No competitive allocation; available to any qualifying production
    - Requires Georgia DOR registration before principal photography begins
    - Resident entity (production company registered in GA) required to claim credit

VERIFICATION STATUS:
  base_rate=0.20         VERIFIED — O.C.G.A. § 48-7-40.26(b)(1)
  logo_uplift=0.10       VERIFIED — O.C.G.A. § 48-7-40.26(b)(2)
  min_budget=500000      VERIFIED — O.C.G.A. § 48-7-40.26(a)(2)
  per_person_cap=500000  VERIFIED — O.C.G.A. § 48-7-40.26(b)(3)
  transferable=True      VERIFIED — O.C.G.A. § 48-7-40.26(f)
  refundable=False       VERIFIED — credit is against Georgia income tax liability
  qualifying_spend       VERIFIED for BTL; ATL subject to per-person cap (§ 48-7-40.26(b)(3))
  transferable_value_pct=0.90  PARSED — market average; actual trades vary 0.88–0.92
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = datetime.now(timezone.utc).isoformat()

# Stable UUIDs for this migration's records (deterministic — safe to re-run downgrade)
SOURCE_DOC_OCGA_ID  = str(uuid.UUID("a1000000-0003-0000-0001-000000000001"))
SOURCE_DOC_ADMIN_ID = str(uuid.UUID("a1000000-0003-0000-0001-000000000002"))
RULE_MIN_BUDGET_ID  = str(uuid.UUID("a1000000-0003-0000-0003-000000000001"))
RULE_ATL_CAP_ID     = str(uuid.UUID("a1000000-0003-0000-0003-000000000002"))
RULE_LOCAL_ENTITY_ID = str(uuid.UUID("a1000000-0003-0000-0003-000000000003"))
UPLIFT_LOGO_ID      = str(uuid.UUID("a1000000-0003-0000-0004-000000000001"))


def _qsc_uid(category: str) -> str:
    return str(uuid.uuid5(uuid.UUID("a1000000-0003-0000-0002-000000000000"), f"georgia_eiia:{category}"))


def _lookup_jurisdiction_id(conn, code: str) -> str:
    result = conn.execute(
        sa.text("SELECT id FROM jurisdictions WHERE code = :code AND level = 'state'"),
        {"code": code},
    ).fetchone()
    if not result:
        raise RuntimeError(f"Jurisdiction '{code}' not found — run migration 0002 first")
    return str(result[0])


def _lookup_program_id(conn, slug: str) -> str:
    result = conn.execute(
        sa.text("SELECT id FROM incentive_programs WHERE slug = :slug"),
        {"slug": slug},
    ).fetchone()
    if not result:
        raise RuntimeError(f"Program slug '{slug}' not found — run migration 0002 first")
    return str(result[0])


def upgrade() -> None:
    conn = op.get_bind()

    ga_jurisdiction_id = _lookup_jurisdiction_id(conn, "US-GA")
    program_id = _lookup_program_id(conn, "georgia_eiia")

    # -----------------------------------------------------------------------
    # 1. Source documents
    #    Columns match app/models/document.py SourceDocument:
    #    title, document_type, jurisdiction_id, authority_name, source_url,
    #    publication_date, effective_from, effective_until, confidence_tier,
    #    review_status, storage_path, raw_text, page_count, notes
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
            "id": SOURCE_DOC_OCGA_ID,
            "title": "O.C.G.A. § 48-7-40.26 — Entertainment Industry Investment Act",
            "document_type": "regulation",
            "jurisdiction_id": ga_jurisdiction_id,
            "authority_name": "Georgia General Assembly / Department of Revenue",
            "source_url": "https://law.justia.com/codes/georgia/title-48/chapter-7/article-2/section-48-7-40-26/",
            "publication_date": None,
            "effective_from": "2008-01-01",
            "effective_until": None,
            "confidence_tier": "VERIFIED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Primary statutory source for Georgia EIIA. "
                "§ 48-7-40.26(b)(1): 20% base credit. "
                "§ 48-7-40.26(b)(2): +10% logo uplift. "
                "§ 48-7-40.26(b)(3): $500K per-person ATL cap. "
                "§ 48-7-40.26(a)(2): $500K minimum qualified budget. "
                "§ 48-7-40.26(f): Credit is transferable."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": SOURCE_DOC_ADMIN_ID,
            "title": "Georgia Comp. R. & Regs. 560-7-8-.44 — EIIA Administrative Rules",
            "document_type": "regulation",
            "jurisdiction_id": ga_jurisdiction_id,
            "authority_name": "Georgia Department of Revenue",
            "source_url": "https://www.georgia.org/film-in-georgia",
            "publication_date": None,
            "effective_from": None,
            "effective_until": None,
            "confidence_tier": "PARSED",
            "review_status": "approved",
            "storage_path": None,
            "raw_text": None,
            "page_count": None,
            "notes": (
                "Georgia DOR administrative rules implementing O.C.G.A. § 48-7-40.26. "
                "Defines qualified production costs, registration requirements, and "
                "acceptable Georgia logo placement for uplift eligibility."
            ),
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 2. Update the georgia_eiia program — set verified rates and source link
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = :src_id,
                base_rate              = 0.200000,
                max_rate               = 0.300000,
                is_refundable          = FALSE,
                is_transferable        = TRUE,
                transferable_value_pct = 0.900000,
                is_competitive         = FALSE,
                requires_local_entity  = TRUE,
                effective_from         = '2008-01-01',
                confidence_tier        = 'VERIFIED',
                review_status          = 'approved',
                authority_url          = 'https://law.justia.com/codes/georgia/title-48/chapter-7/article-2/section-48-7-40-26/',
                last_verified_date     = '2025-06-18',
                notes                  = 'VERIFIED against O.C.G.A. § 48-7-40.26. '
                                         'Base credit: 20% of Georgia qualified production costs. '
                                         'Logo uplift: +10% (total 30%) when Georgia logo displayed per DOR rules. '
                                         'Minimum $500K Georgia qualified spend required. '
                                         '$500K per-person cap on above-the-line compensation. '
                                         'Non-refundable. Fully transferable — market trades at 88-92 cents. '
                                         'transferable_value_pct=0.90 is a PARSED midpoint estimate.',
                updated_at             = :now
            WHERE slug = 'georgia_eiia'
        """),
        {"src_id": SOURCE_DOC_OCGA_ID, "now": NOW},
    )

    # -----------------------------------------------------------------------
    # 3. Qualifying spend categories
    #
    # Source: O.C.G.A. § 48-7-40.26(a)(1) defines "Georgia qualified production costs"
    # as all production costs incurred in Georgia for the production.
    #
    # ATL spend (director, writer, producer, cast) qualifies but is CAPPED at $500K/person
    # per § 48-7-40.26(b)(3). The engine applies this cap via the ATL_CAP rule below.
    # Rights/acquisition costs do NOT qualify (§ 48-7-40.26(a)(1) exclusion).
    #
    # BTL labor (crew) qualifies if incurred in Georgia.
    # jurisdiction_spend_only=True because only Georgia-incurred costs count.
    #
    # Post, VFX, music, sound qualify when work is performed in Georgia.
    # Insurance, completion bond, contingency, finance costs DO NOT qualify.
    # Deferments, equity, in-kind do NOT qualify (non-cash; § 48-7-40.26(a)(1)).
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

    def qsc(category: str, qualifies: bool, jur_only: bool, notes: str, tier: str = "VERIFIED"):
        return {
            "id": _qsc_uid(category),
            "program_id": program_id,
            "spend_category": category,
            "qualifies": qualifies,
            "jurisdiction_spend_only": jur_only,
            "notes": notes,
            "confidence_tier": tier,
            "created_at": NOW,
            "updated_at": NOW,
        }

    op.bulk_insert(qsc_table, [
        # ATL — qualify subject to per-person $500K cap (enforced by RULE_ATL_CAP)
        qsc("atl_director", True, True,
            "Qualifies per § 48-7-40.26(a)(1); subject to $500K/person cap (§ 48-7-40.26(b)(3))"),
        qsc("atl_writer",   True, True,
            "Qualifies per § 48-7-40.26(a)(1); subject to $500K/person cap (§ 48-7-40.26(b)(3))"),
        qsc("atl_producer", True, True,
            "Qualifies per § 48-7-40.26(a)(1); subject to $500K/person cap (§ 48-7-40.26(b)(3))"),
        qsc("atl_cast",     True, True,
            "Qualifies per § 48-7-40.26(a)(1); subject to $500K/person cap (§ 48-7-40.26(b)(3))"),
        qsc("atl_rights",   False, True,
            "Story/rights acquisition does NOT qualify — excluded per § 48-7-40.26(a)(1)"),
        # BTL Labor
        qsc("btl_crew_labor",        True, True,
            "Qualifies per § 48-7-40.26(a)(1); costs must be incurred in Georgia"),
        qsc("btl_resident_labor",    True, True,
            "Qualifies; Georgia-resident crew included in qualified production costs"),
        qsc("btl_nonresident_labor", True, True,
            "Qualifies when physically working in Georgia per § 48-7-40.26(a)(1)"),
        # BTL Non-labor
        qsc("btl_equipment_rental", True, True,
            "Qualifies when equipment rented from Georgia vendors or delivered to Georgia sets"),
        qsc("btl_stage_facility",   True, True,
            "Qualifies; Georgia studio/stage rental is a qualified production cost"),
        qsc("btl_location_fees",    True, True,
            "Qualifies; Georgia location permits/fees are qualified production costs"),
        qsc("btl_set_construction", True, True,
            "Qualifies; materials and labor for Georgia set construction"),
        qsc("btl_transportation",   True, True,
            "Qualifies when transport costs incurred within Georgia"),
        qsc("btl_catering",         True, True,
            "Qualifies when catering services purchased from Georgia vendors"),
        # Post / VFX / Music / Sound
        qsc("post_production", True, True,
            "Qualifies when post-production work performed in Georgia"),
        qsc("vfx",   True, True,
            "Qualifies when VFX work performed in Georgia"),
        qsc("music", True, True,
            "Qualifies when music recording/scoring performed in Georgia"),
        qsc("sound", True, True,
            "Qualifies when sound work performed in Georgia"),
        # Excluded categories
        qsc("finance_costs",   False, True,
            "Does NOT qualify — financing costs excluded per § 48-7-40.26(a)(1)"),
        qsc("insurance",       False, True,
            "Does NOT qualify — insurance excluded per § 48-7-40.26(a)(1)"),
        qsc("completion_bond", False, True,
            "Does NOT qualify — completion bond excluded per § 48-7-40.26(a)(1)"),
        qsc("contingency",     False, True,
            "Does NOT qualify — contingency reserves are not qualified production costs"),
        qsc("payroll_fringes", True, True,
            "Qualifies — payroll taxes and fringes on qualifying wages included in qualified "
            "production costs per DOR practice", "PARSED"),
        # Non-cash compensation
        qsc("deferment",            False, True,
            "Does NOT qualify — deferred compensation is non-cash"),
        qsc("equity_participation", False, True,
            "Does NOT qualify — equity/backend participation is non-cash"),
        qsc("in_kind",              False, True,
            "Does NOT qualify — in-kind services are non-cash"),
        qsc("reinvestment",         False, True,
            "Does NOT qualify — reinvestment arrangements are non-cash"),
        # Travel / Lodging / Misc
        qsc("travel",        True, True,
            "Qualifies when travel costs incurred in Georgia (e.g., local ground transport)"),
        qsc("lodging",       True, True,
            "Qualifies when lodging costs incurred in Georgia for cast/crew on production"),
        qsc("miscellaneous", True, True,
            "Qualifies if costs are incurred in Georgia and directly related to production; "
            "review recommended for large miscellaneous line items", "PARSED"),
    ])

    # -----------------------------------------------------------------------
    # 4. Incentive rules
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
        {
            "id": RULE_MIN_BUDGET_ID,
            "program_id": program_id,
            "source_document_id": SOURCE_DOC_OCGA_ID,
            "rule_type": "minimum_total_budget",
            "threshold_numeric": 500_000.00,
            "threshold_text": "$500,000 in Georgia qualified production costs",
            "fail_action": "disqualify",
            "description": (
                "Production must incur at least $500,000 in Georgia qualified production "
                "costs to be eligible for the EIIA credit."
            ),
            "source_page": None,
            "source_excerpt": (
                "§ 48-7-40.26(a)(2): '...a minimum of $500,000.00 in aggregate production "
                "costs that are directly used in a state certified production...'"
            ),
            "statutory_reference": "O.C.G.A. § 48-7-40.26(a)(2)",
            "confidence_tier": "VERIFIED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_ATL_CAP_ID,
            "program_id": program_id,
            "source_document_id": SOURCE_DOC_OCGA_ID,
            "rule_type": "spend_cap_pct",
            "threshold_numeric": 500_000.00,
            "threshold_text": "$500,000 per individual for above-the-line compensation",
            "fail_action": "reduce_credit",
            "description": (
                "ATL compensation for any single individual (cast, director, writer, producer) "
                "is capped at $500,000 for purposes of calculating qualified production costs. "
                "Amounts above the cap are excluded from the credit base."
            ),
            "source_page": None,
            "source_excerpt": (
                "§ 48-7-40.26(b)(3): 'The aggregate compensation of any one individual "
                "which may be included in the aggregate production costs of a state certified "
                "production shall not exceed $500,000.00.'"
            ),
            "statutory_reference": "O.C.G.A. § 48-7-40.26(b)(3)",
            "confidence_tier": "VERIFIED",
            "created_at": NOW,
            "updated_at": NOW,
        },
        {
            "id": RULE_LOCAL_ENTITY_ID,
            "program_id": program_id,
            "source_document_id": SOURCE_DOC_OCGA_ID,
            "rule_type": "required_entity_type",
            "threshold_numeric": None,
            "threshold_text": "Production company must be registered in Georgia",
            "fail_action": "disqualify",
            "description": (
                "The production company must be a taxpayer subject to Georgia income tax "
                "and registered with the Georgia Department of Revenue before beginning "
                "principal photography."
            ),
            "source_page": None,
            "source_excerpt": (
                "§ 48-7-40.26(c): Credit claimed against Georgia income tax liability of the "
                "production company; company must register with DOR prior to principal photography."
            ),
            "statutory_reference": "O.C.G.A. § 48-7-40.26(c)",
            "confidence_tier": "VERIFIED",
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])

    # -----------------------------------------------------------------------
    # 5. Program uplift — Georgia logo (+10%)
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

    op.bulk_insert(uplift_table, [
        {
            "id": UPLIFT_LOGO_ID,
            "program_id": program_id,
            "name": "Georgia Logo Uplift",
            "additional_rate": 0.100000,
            "applies_to": "same_qualifying_spend",
            "condition_type": "georgia_logo_displayed",
            "condition_threshold": None,
            "condition_text": (
                "Production must include the Georgia promotional logo in end credits and "
                "marketing materials per Georgia DOR / Georgia Film Office requirements. "
                "Adds 10% to credit rate on same qualifying spend base."
            ),
            "is_stackable_with_other_uplifts": False,
            "confidence_tier": "VERIFIED",
            "created_at": NOW,
            "updated_at": NOW,
        },
    ])


def downgrade() -> None:
    conn = op.get_bind()

    try:
        program_id = _lookup_program_id(conn, "georgia_eiia")
    except RuntimeError:
        return

    conn.execute(
        sa.text("DELETE FROM program_uplifts WHERE id = :uid"),
        {"uid": UPLIFT_LOGO_ID},
    )
    conn.execute(
        sa.text("DELETE FROM incentive_rules WHERE id IN (:r1, :r2, :r3)"),
        {"r1": RULE_MIN_BUDGET_ID, "r2": RULE_ATL_CAP_ID, "r3": RULE_LOCAL_ENTITY_ID},
    )
    conn.execute(
        sa.text("DELETE FROM qualifying_spend_categories WHERE program_id = :pid"),
        {"pid": program_id},
    )

    conn.execute(
        sa.text("""
            UPDATE incentive_programs SET
                source_document_id     = NULL,
                base_rate              = NULL,
                max_rate               = NULL,
                is_refundable          = NULL,
                is_transferable        = NULL,
                transferable_value_pct = NULL,
                confidence_tier        = 'DISCOVERY',
                review_status          = 'pending',
                last_verified_date     = NULL,
                notes = 'DISCOVERY — rates not verified. Base rate approx 20%, +10% with Georgia logo. '
                        'Transferable at ~88-92 cents on dollar. Min budget $500K. Verify from DOR.',
                updated_at = :now
            WHERE slug = 'georgia_eiia'
        """),
        {"now": NOW},
    )

    conn.execute(
        sa.text("DELETE FROM source_documents WHERE id IN (:s1, :s2)"),
        {"s1": SOURCE_DOC_OCGA_ID, "s2": SOURCE_DOC_ADMIN_ID},
    )
