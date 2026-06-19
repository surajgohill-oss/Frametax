"""0007 — Add fixed_grant_amount_usd column; seed NOHFC program and stacking rules.

Northern Ontario Heritage Fund Corporation (NOHFC) production fund as proof-of-concept
for the grant/discretionary_fund stacking architecture.

Source: nohfc.ca — program guidelines (PARSED tier; not independently verified against
regulation text).

Stacking rules seeded:
  NOHFC + OFTTC  → spend_reduction
  NOHFC + CPTC   → spend_reduction

Revision ID: 0007
Revises: 0006
"""
from __future__ import annotations

import uuid
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Stable UUIDs (deterministic for repeatable migrations)
# ---------------------------------------------------------------------------
NOHFC_PROGRAM_ID   = uuid.UUID("b7e00001-0001-0001-0001-000000000007")
NOHFC_SOURCE_DOC_ID = uuid.UUID("b7e00002-0001-0001-0001-000000000007")
STACKING_RULE_NOHFC_OFTTC_ID = uuid.UUID("b7e00003-0001-0001-0001-000000000007")
STACKING_RULE_NOHFC_CPTC_ID  = uuid.UUID("b7e00004-0001-0001-0001-000000000007")


def _lookup(conn, table: str, col: str, val: str):
    row = conn.execute(
        sa.text(f"SELECT id FROM {table} WHERE {col} = :v"),
        {"v": val},
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Migration 0007: {table}.{col}={val!r} not found — run 0006 first")
    return row[0]


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # DDL: add fixed_grant_amount_usd to incentive_programs
    # -----------------------------------------------------------------------
    op.add_column(
        "incentive_programs",
        sa.Column("fixed_grant_amount_usd", sa.Numeric(18, 2), nullable=True),
    )

    conn = op.get_bind()

    # -----------------------------------------------------------------------
    # Look up prerequisite IDs
    # -----------------------------------------------------------------------
    on_jur_id  = _lookup(conn, "jurisdictions", "code", "CA-ON")
    ofttc_id   = _lookup(conn, "incentive_programs", "slug", "on_ofttc")
    cptc_id    = _lookup(conn, "incentive_programs", "slug", "ca_federal_cptc")

    # -----------------------------------------------------------------------
    # Source document — NOHFC program guide
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            INSERT INTO source_documents
                (id, title, authority_name, source_url, document_type,
                 confidence_tier, notes)
            VALUES
                (:id, :title, :auth, :url, :dtype, :tier, :notes)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id":    NOHFC_SOURCE_DOC_ID,
            "title": "NOHFC Production Fund Program Guidelines",
            "auth":  "Northern Ontario Heritage Fund Corporation",
            "url":   "https://www.nohfc.ca",
            "dtype": "incentive_guide",
            "tier":  "PARSED",
            "notes": "PARSED — sourced from public program summary pages; "
                     "not independently verified against enabling legislation",
        },
    )

    # -----------------------------------------------------------------------
    # NOHFC program
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            INSERT INTO incentive_programs
                (id, jurisdiction_id, source_document_id, name, slug,
                 program_type, credit_basis, base_rate, max_rate,
                 is_refundable, is_transferable, is_competitive,
                 fixed_grant_amount_usd, requires_local_entity,
                 confidence_tier, review_status, authority_url, notes)
            VALUES
                (:id, :jur, :src, :name, :slug,
                 :ptype, :cbasis, :brate, :mrate,
                 :refund, :transfer, :competitive,
                 :grant_amt, :local_entity,
                 :tier, :rstatus, :url, :notes)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id":          NOHFC_PROGRAM_ID,
            "jur":         on_jur_id,
            "src":         NOHFC_SOURCE_DOC_ID,
            "name":        "Northern Ontario Heritage Fund — Production Fund",
            "slug":        "nohfc_production_fund",
            "ptype":       "discretionary_fund",
            "cbasis":      "total_budget",
            "brate":       None,   # Fixed amount, not rate-based
            "mrate":       None,
            "refund":      True,   # Grant is paid as cash
            "transfer":    False,
            "competitive": True,   # Discretionary allocation
            "grant_amt":   500_000.00,
            "local_entity": True,
            "tier":        "PARSED",
            "rstatus":     "pending",
            "url":         "https://www.nohfc.ca",
            "notes":       (
                "Discretionary production fund for projects shooting in Northern Ontario. "
                "Grant amount of $500,000 CAD is an illustrative example — actual amounts "
                "vary by project. Grant must be deducted from qualifying expenditure base "
                "for CPTC and OFTTC per CRA T4283 and OMDC guidelines."
            ),
        },
    )

    # -----------------------------------------------------------------------
    # Stacking rules
    # -----------------------------------------------------------------------
    conn.execute(
        sa.text("""
            INSERT INTO legal_stacking_rules
                (id, program_a_id, program_b_id, rule_type, condition_text,
                 statutory_reference, confidence_tier, notes)
            VALUES
                (:id, :a, :b, :rtype, :cond, :stat, :tier, :notes)
            ON CONFLICT (id) DO NOTHING
        """),
        [
            {
                "id":    STACKING_RULE_NOHFC_OFTTC_ID,
                "a":     NOHFC_PROGRAM_ID,
                "b":     ofttc_id,
                "rtype": "spend_reduction",
                "cond":  (
                    "NOHFC grant amount must be deducted from Ontario eligible labour "
                    "expenditure base before computing OFTTC credit (OMDC guidelines)"
                ),
                "stat":  "Ontario Reg 37/09 under Corporations Tax Act; OMDC OFTTC guidelines",
                "tier":  "PARSED",
                "notes": "spend_reduction: NOHFC grant reduces OFTTC qualifying spend basis",
            },
            {
                "id":    STACKING_RULE_NOHFC_CPTC_ID,
                "a":     NOHFC_PROGRAM_ID,
                "b":     cptc_id,
                "rtype": "spend_reduction",
                "cond":  (
                    "Government assistance (including NOHFC grants) must be deducted from "
                    "QCLE before computing CPTC (ITA § 125.4; CRA T4283)"
                ),
                "stat":  "Income Tax Act § 125.4(1) 'assistance'; CRA T4283 Guide",
                "tier":  "PARSED",
                "notes": "spend_reduction: NOHFC grant reduces CPTC qualifying labour basis",
            },
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("DELETE FROM legal_stacking_rules WHERE id IN (:a, :b)"),
        {"a": STACKING_RULE_NOHFC_OFTTC_ID, "b": STACKING_RULE_NOHFC_CPTC_ID},
    )
    conn.execute(
        sa.text("DELETE FROM incentive_programs WHERE id = :id"),
        {"id": NOHFC_PROGRAM_ID},
    )
    conn.execute(
        sa.text("DELETE FROM source_documents WHERE id = :id"),
        {"id": NOHFC_SOURCE_DOC_ID},
    )

    op.drop_column("incentive_programs", "fixed_grant_amount_usd")
