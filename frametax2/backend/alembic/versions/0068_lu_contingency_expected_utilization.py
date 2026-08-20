"""0068 — Little Utopia's contingency expected-utilization project election.

Consolidated Backend Correction, Part 19-21 (CBA-009). Persists Little
Utopia's ESTABLISHED PROJECT ELECTION — the production expects to deploy
its full $301,131.00 contingency reserve (account 8300) into real
production expenditures — as a genuine ProjectFact row, using the same
"recovered_demo_state" provenance convention 0063 established for every
other Little Utopia fact recovered from its own real source material
rather than an automated extraction pipeline.

This is NOT a Mauritius statutory rule and NOT a hard-coded assumption in
the qualification/pricing engines (app/calculators/qualification_
derivation.py, app/services/canonical_evaluation.py, app/calculators/
allocation_pricing.py remain fully generic — none reference this project
or Mauritius for this fact). It is project data, read generically by the
same seam every other production-fact ProjectFact row already uses
(app.services.canonical_project_economics.build_project_economic_inputs).

Idempotent: does nothing if the fact already exists (covers a re-run or a
project whose contingency_expected_utilization_pct was already answered
some other way) or if the Little Utopia project row is not present in
this database (matches 0063's own defensive pattern).

Revision ID: 0068
Revises: 0067
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0068"
down_revision: Union[str, None] = "0067"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FACT_KEY = "contingency_expected_utilization_pct"


def upgrade() -> None:
    conn = op.get_bind()

    project_row = conn.execute(
        sa.text("SELECT id FROM projects WHERE id = :pid"),
        {"pid": LITTLE_UTOPIA_PROJECT_ID},
    ).fetchone()
    if project_row is None:
        return

    existing = conn.execute(
        sa.text("SELECT 1 FROM project_facts WHERE project_id = :pid AND fact_key = :key"),
        {"pid": LITTLE_UTOPIA_PROJECT_ID, "key": FACT_KEY},
    ).fetchone()
    if existing is not None:
        return

    budget_version_id = conn.execute(
        sa.text("""
            SELECT d.current_version_id FROM documents d
            WHERE d.project_id = :pid AND d.category = 'budget'
            LIMIT 1
        """),
        {"pid": LITTLE_UTOPIA_PROJECT_ID},
    ).scalar()

    conn.execute(
        sa.text("""
            INSERT INTO project_facts (
                id, project_id, fact_key, value, value_type, source_type,
                source_document_version_id, source_location, extraction_confidence,
                review_status, created_at, updated_at
            ) VALUES (
                :id, :pid, :key, :val, :vt, :st, :svid, :sloc, :conf, :rs, :now, :now
            )
        """),
        {
            "id": str(uuid.uuid4()), "pid": LITTLE_UTOPIA_PROJECT_ID, "key": FACT_KEY,
            "val": "100", "vt": "number", "st": "recovered_demo_state",
            "svid": budget_version_id,
            "sloc": (
                "Established project election, previously embedded directly in "
                "app/demo/little_utopia_state.py behavior rather than persisted "
                "as project data — the production expects to deploy its full "
                "contingency reserve into real production expenditures."
            ),
            "conf": 1.0, "rs": "approved", "now": NOW,
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM project_facts WHERE project_id = :pid AND fact_key = :key"),
        {"pid": LITTLE_UTOPIA_PROJECT_ID, "key": FACT_KEY},
    )
