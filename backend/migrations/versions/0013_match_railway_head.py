"""Match Railway DB head revision

The Railway production database was migrated to revision 0013 from a prior
codebase.  This no-op migration file makes revision 0013 recognisable to
alembic so that 'alembic upgrade head' exits cleanly (already at head).

No schema changes are performed; the schema was applied by the prior
deployment that is currently running on Railway.

Revision ID: 0013
Revises: 0006
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema already present; this is a no-op alignment marker.
    pass


def downgrade() -> None:
    pass
