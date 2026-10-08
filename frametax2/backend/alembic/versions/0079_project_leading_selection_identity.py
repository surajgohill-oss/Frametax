"""Projects: persist the producer's own leading-structure choice by stable identity

Project.leading_structure_id is written by both the canonical evaluation (its own leader) and the producer's
"Set as Leading". Structure rows are re-created per evaluation generation, so the evaluation could not tell a
user choice from its own pick and replaced or cleared it on every regeneration. This nullable column records a
user selection by its run-independent economic identity; see app/services/leading_selection.py.

Revision ID: 0079
Revises: 0078
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0079"
down_revision: Union[str, None] = "0078"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("leading_selection_identity", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "leading_selection_identity")
