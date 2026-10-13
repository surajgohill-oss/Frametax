"""Seed the Jurisdiction rows for the US states that became rate-bearing in NA-RECONCILIATION-12.

Ohio, West Virginia, Missouri, New Jersey, Montana and Arkansas now have canonical RateRules but no ``jurisdictions`` row, so a production cannot be based there and the candidate
universe cannot discover them. Only the facts the programs' own sources establish are seeded (code, name, USD, state level, parent US); no cost benchmark or cost index is invented.
Idempotent (``WHERE NOT EXISTS``); the downgrade removes only these rows and only when nothing references them.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0088"
down_revision = "0087"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0025-0000-0001-000000000000")
_STATES = (
    ("US-OH", "United States — Ohio"), ("US-WV", "United States — West Virginia"), ("US-MO", "United States — Missouri"),
    ("US-NJ", "United States — New Jersey"), ("US-MT", "United States — Montana"), ("US-AR", "United States — Arkansas"),
)


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for code, name in _STATES:
        conn.execute(sa.text("""
            INSERT INTO jurisdictions (id, parent_id, name, code, iso_code, level, currency_code, country_code, is_active, created_at, updated_at)
            SELECT :id, (SELECT id FROM jurisdictions WHERE code = 'US' LIMIT 1), :name, :code, :code, 'state', 'USD', 'US', true, :now, :now
            WHERE NOT EXISTS (SELECT 1 FROM jurisdictions WHERE code = :code ::varchar)
        """), {"id": str(uuid.uuid5(_NS, f"jur:{code}")), "name": name, "code": code, "now": now})


def downgrade() -> None:
    conn = op.get_bind()
    for code, _ in _STATES:
        conn.execute(sa.text("""
            DELETE FROM jurisdictions WHERE code = :code AND id = :id
              AND NOT EXISTS (SELECT 1 FROM projects WHERE home_jurisdiction_id = jurisdictions.id)
        """), {"code": code, "id": str(uuid.uuid5(_NS, f"jur:{code}"))})
