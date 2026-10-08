"""Projects: derived Company Globe snapshot (compact leading-structure topology per served generation)

Company Globe previously fetched every active project's full served state (~34 MB each). The aggregate portfolio
read keeps a compact snapshot keyed by engine version + input fingerprint instead; see
app/services/portfolio_globe_view.py. Derived cache only.

Revision ID: 0080
Revises: 0079
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0080"
down_revision: Union[str, None] = "0079"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("portfolio_globe_snapshot", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "portfolio_globe_snapshot")
