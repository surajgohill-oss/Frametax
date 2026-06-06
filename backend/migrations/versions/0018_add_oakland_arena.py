"""add oakland arena venue

Revision ID: 0018_add_oakland_arena
Revises: 0017_mirror_normalization
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO venues (slug, name, city, state, capacity)
        VALUES ('oakland-arena', 'Oakland Arena', 'Oakland', 'CA', 19596)
        ON CONFLICT (slug) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM venues WHERE slug = 'oakland-arena'")
