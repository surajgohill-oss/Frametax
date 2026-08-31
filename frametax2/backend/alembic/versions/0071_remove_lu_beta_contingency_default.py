"""Production Page Integrity: remove Little Utopia's stale beta 100%
contingency-expected-utilization election.

Migration 0068 persisted a 100% expected-utilization election for Little
Utopia specifically, sourced from a beta/testing-era assumption embedded
directly in app/demo/little_utopia_state.py's own prior behavior. That
assumption is no longer canonical: the product now exposes a real,
generic producer-facing control (POST /projects/{id}/assumptions) for
this same fact, and no project — Little Utopia included — is meant to
carry a silent default. With no fact row present,
qualification_derivation.derive_qualification_register's own existing,
already-correct behavior applies: the contingency reserve genuinely
requires producer/authority resolution (GREY_AREA_REQUIRES_AUTHORITY),
never silently assumed at either 0% or 100%.

This is a one-time DATA correction for the one project the original
beta migration touched — it does not add or change any runtime
behavior, and no calculator/service file references this project by id
or title. Idempotent: a no-op if the fact is already absent (e.g. a
producer has since set an explicit value through the new real control,
in which case this migration correctly leaves that explicit choice
untouched — it only ever removes the row this exact migration inserted,
identified by its own "recovered_demo_state" provenance + "100" value,
never a differently-sourced or differently-valued row).

Revision ID: 0071
Revises: 0070
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0071"
down_revision: Union[str, None] = "0070"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FACT_KEY = "contingency_expected_utilization_pct"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            DELETE FROM project_facts
            WHERE project_id = :pid AND fact_key = :key
              AND value = '100' AND source_type = 'recovered_demo_state'
        """),
        {"pid": LITTLE_UTOPIA_PROJECT_ID, "key": FACT_KEY},
    )


def downgrade() -> None:
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
    import uuid
    from datetime import datetime, timezone
    conn.execute(
        sa.text("""
            INSERT INTO project_facts (
                id, project_id, fact_key, value, value_type, source_type,
                review_status, created_at, updated_at
            ) VALUES (:id, :pid, :key, '100', 'number', 'recovered_demo_state', 'approved', :now, :now)
        """),
        {"id": str(uuid.uuid4()), "pid": LITTLE_UTOPIA_PROJECT_ID, "key": FACT_KEY, "now": datetime.now(timezone.utc).isoformat()},
    )
