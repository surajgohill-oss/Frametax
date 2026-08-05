"""0010 — Seed placeholder SourceDocument records for Tier 1 Mediterranean incentive guides.

No PDF files exist in the repository yet.  These rows are DISCOVERY-tier
placeholders that:
  - Record the known authority name and public URL hint for each program
  - Provide a source_document_id that program rows can reference once the
    actual PDF is ingested via the /documents/upload API endpoint
  - Track the data-acquisition status (pending review)

Once an authoritative PDF or web page is reviewed and parsed, update the row:
  - confidence_tier: DISCOVERY → PARSED
  - raw_text: paste extracted text
  - storage_path: local path or S3 key
  - review_status: pending → in_review → approved
  - last_verified_date: ISO date of review

Revision ID: 0010
Revises: 0009
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# Re-derive jurisdiction IDs from 0008
_JUR_NS = uuid.UUID("a1000000-0008-0000-0001-000000000000")

def _jid(seed: str) -> str:
    return str(uuid.uuid5(_JUR_NS, seed))

MU_ID = _jid("jur:MU")
MT_ID = _jid("jur:MT")
GR_ID = _jid("jur:GR")
CY_ID = _jid("jur:CY")

# Source document IDs — new namespace for 0010
_DOC_NS = uuid.UUID("a1000000-0010-0000-0001-000000000000")

def _did(seed: str) -> str:
    return str(uuid.uuid5(_DOC_NS, seed))

DOC_MU_ID = _did("doc:mu_edb_production_incentive_guide")
DOC_MT_ID = _did("doc:mt_mfc_rebate_guidelines_2024")
DOC_GR_ID = _did("doc:gr_enterprise_greece_cash_rebate_guide")
DOC_CY_ID = _did("doc:cy_cipa_film_production_rebate")


SOURCE_DOCS = [
    {
        "id": DOC_MU_ID,
        "title": "Mauritius EDB Film Production Incentive — Programme Guidelines [NOT YET ACQUIRED]",
        "document_type": "incentive_guide",
        "jurisdiction_id": MU_ID,
        "authority_name": "Economic Development Board Mauritius (EDB)",
        "source_url": None,    # URL not confirmed; check edbmauritius.org
        "publication_date": None,
        "effective_from": None,
        "effective_until": None,
        "confidence_tier": "DISCOVERY",
        "review_status": "pending",
        "storage_path": None,
        "raw_text": None,
        "page_count": None,
        "notes": (
            "Primary source for the Mauritius EDB production incentive not yet obtained. "
            "Rate of 35% inferred from production budget evidence (The Little Utopia, June 2025). "
            "Data gaps: ATL scope, foreign crew treatment, accommodation/per-diem qualifying, "
            "minimum spend, annual cap, rebate assignability, payment timeline, SPV requirements. "
            "Acquisition priority: HIGH — rate not verified from any authoritative source. "
            "Contact: Economic Development Board Mauritius, edbmauritius.org. "
            "Also check: Mauritius Film Development Corporation (MFDC), mfdc.mu."
        ),
        "superseded_by_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": DOC_MT_ID,
        "title": "Malta Film Commission Cash Rebate Programme Guidelines (2024/2025)",
        "document_type": "incentive_guide",
        "jurisdiction_id": MT_ID,
        "authority_name": "Malta Film Commission (MFC)",
        "source_url": "https://maltafilmcommission.com/rebate",
        "publication_date": "2024-01-01",
        "effective_from": "2024-01-01",
        "effective_until": None,
        "confidence_tier": "DISCOVERY",
        "review_status": "pending",
        "storage_path": None,
        "raw_text": None,
        "page_count": None,
        "notes": (
            "Malta Film Commission administers the cash rebate. "
            "URL hint: maltafilmcommission.com/rebate. "
            "Known data from public MFC summary: 25% base; uplifts to 40%; "
            "all ATL and BTL qualifying; no cultural test for foreign productions; "
            "min EUR 50,000 spend; vessel/marine explicitly qualifying; "
            "Mediterranean Film Studios water tank (750,000-gal outdoor). "
            "Data gaps to verify from primary source text: "
            "exact uplift thresholds and stacking rules; "
            "rebate assignability to gap lender; "
            "annual programme allocation limit; "
            "confirmed cashflow processing timeline; "
            "WHT on international cast under applicable treaty. "
            "Acquisition priority: HIGH — programme is key comparator for marine productions."
        ),
        "superseded_by_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": DOC_GR_ID,
        "title": "Greece Cash Rebate for International Productions — Enterprise Greece Guide",
        "document_type": "incentive_guide",
        "jurisdiction_id": GR_ID,
        "authority_name": "Enterprise Greece / Greek Film Centre (GFC)",
        "source_url": "https://enterprisegreece.gov.gr",
        "publication_date": None,
        "effective_from": None,
        "effective_until": None,
        "confidence_tier": "DISCOVERY",
        "review_status": "pending",
        "storage_path": None,
        "raw_text": None,
        "page_count": None,
        "notes": (
            "Enterprise Greece administers the 40% cash rebate. "
            "URL hint: enterprisegreece.gov.gr (Film Investment section). "
            "Known from public overview: 40% on all qualifying Greek expenditure; "
            "ATL and BTL including marine stated as qualifying; "
            "min EUR 100,000 spend; no cultural test for foreign productions; "
            "annual allocation exists (oversubscription risk). "
            "Data gaps to verify from primary source text: "
            "annual programme allocation cap; "
            "WHT on international cast (standard 20%; treaty reduction requires verification); "
            "rebate assignability to financier; "
            "exact accommodation and per-diem qualifying scope; "
            "foreign crew routing requirements through Greek entity; "
            "confirmed processing timeline (market reports: 9-12 months). "
            "Acquisition priority: HIGH — 40% rate is highest among Tier 1 comparators."
        ),
        "superseded_by_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": DOC_CY_ID,
        "title": "Cyprus Film Production Rebate — CIPA / Deputy Ministry of Tourism Guidelines",
        "document_type": "incentive_guide",
        "jurisdiction_id": CY_ID,
        "authority_name": "Cyprus Investment Promotion Agency (CIPA) / Deputy Ministry of Tourism",
        "source_url": "https://cipa.org.cy",
        "publication_date": None,
        "effective_from": None,
        "effective_until": None,
        "confidence_tier": "DISCOVERY",
        "review_status": "pending",
        "storage_path": None,
        "raw_text": None,
        "page_count": None,
        "notes": (
            "CIPA and the Deputy Ministry of Tourism jointly administer the Cyprus rebate. "
            "URL hint: cipa.org.cy. "
            "Rate of 35% from DISCOVERY sources — not verified from programme statute. "
            "Data gaps to verify from primary source text: "
            "programme rate (35% assumed); "
            "ATL qualifying scope; "
            "foreign crew qualifying treatment; "
            "accommodation and per-diem qualifying treatment; "
            "minimum spend threshold (EUR 100,000 assumed); "
            "annual cap; "
            "rebate assignability; "
            "processing timeline (26 weeks estimated). "
            "Additional note: Cyprus 12.5% corporate tax rate makes it useful as "
            "co-production entity domicile independent of production incentive. "
            "Acquisition priority: MEDIUM — DISCOVERY tier; lower confidence than MT/GR."
        ),
        "superseded_by_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    },
]


def upgrade() -> None:
    op.bulk_insert(
        sa.table(
            "source_documents",
            sa.column("id"),
            sa.column("title"),
            sa.column("document_type"),
            sa.column("jurisdiction_id"),
            sa.column("authority_name"),
            sa.column("source_url"),
            sa.column("publication_date"),
            sa.column("effective_from"),
            sa.column("effective_until"),
            sa.column("confidence_tier"),
            sa.column("review_status"),
            sa.column("storage_path"),
            sa.column("raw_text"),
            sa.column("page_count"),
            sa.column("notes"),
            sa.column("superseded_by_id"),
            sa.column("created_at"),
            sa.column("updated_at"),
        ),
        SOURCE_DOCS,
    )


def downgrade() -> None:
    ids = [d["id"] for d in SOURCE_DOCS]
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM source_documents WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True)
        ),
        {"ids": ids},
    )
