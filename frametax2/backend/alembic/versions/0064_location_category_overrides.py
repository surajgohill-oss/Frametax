"""0064 — Project Library Phase C closeout: location-category override columns.

Small additive migration. The frontend's "Major Location Requirements"
chip UI (13 canonical categories, click-to-toggle override over a
script-derived seed — see app/demo/little_utopia_state.py's
LOCATION_TAXONOMY / apply_location_overrides) currently persists its
override state in a process-local module dict (`_location_overrides`),
lost on every backend restart. This migration gives that override state a
durable home on the EXISTING `project_location_requirements` table (per
Phase B's own docstring: "the persistent home for what the existing
frontend Location Requirements chips already represent") rather than a
second/new table.

Two nullable columns, additive only, no existing column touched:
  - category_key: which of the 13 canonical LOCATION_TAXONOMY slugs this
    row represents (NULL for the 4 free-text script-requirement rows the
    0063 migration already wrote — those are a different, narrower concept
    and are left exactly as they are).
  - override: the producer's true/false override value for that category
    (NULL = no override recorded / cleared, matching the demo module's
    existing None-clears-the-override semantics).

A partial unique index prevents two override rows for the same
(project_id, category_key) pair; rows with category_key IS NULL (the
existing script-requirement rows) are unaffected by it.

Revision ID: 0064
Revises: 0063
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0064"
down_revision: Union[str, None] = "0063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project_location_requirements",
        sa.Column("category_key", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "project_location_requirements",
        sa.Column("override", sa.Boolean(), nullable=True),
    )
    op.create_index(
        "uq_project_location_requirements_category",
        "project_location_requirements",
        ["project_id", "category_key"],
        unique=True,
        postgresql_where=sa.text("category_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_project_location_requirements_category",
        table_name="project_location_requirements",
    )
    op.drop_column("project_location_requirements", "override")
    op.drop_column("project_location_requirements", "category_key")
