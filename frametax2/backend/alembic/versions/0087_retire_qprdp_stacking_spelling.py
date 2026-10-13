"""Retire the unofficial QPRDP stacking spelling (NA-RECONCILIATION-12).

SODEC and Revenu Quebec name one foreign-production credit, the refundable tax credit for film or television production services (form CO-1029.8.36.SP), which is ca_qc_pstc / qc_film_production.
The code registry (app/optimization/stacking_rules.py, 1.11.0) resolves the "QPRDP" name patterns to it and drops the duplicate ca_qc_qprdp pair rules; this removes the same legacy rows
(seeded by 0045 and the wave-6 migrations as DISCOVERY-tier text) so run_full_analysis and the structures API agree. Only rows touching the ca_qc_qprdp program are deleted.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0087"
down_revision = "0086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(sa.text("""
        DELETE FROM legal_stacking_rules
        WHERE program_a_id IN (SELECT id FROM incentive_programs WHERE slug = 'ca_qc_qprdp')
           OR program_b_id IN (SELECT id FROM incentive_programs WHERE slug = 'ca_qc_qprdp')
    """))


def downgrade() -> None:
    """Not reversible: the deleted rows duplicated rules that exist under qc_film_production and rested on an unofficial credit name."""
