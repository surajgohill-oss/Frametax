"""0009 — Update Mauritius EDB program: DISCOVERY → PARSED, set base_rate=0.35.

Source of change: production budget evidence (The Little Utopia, June 2025)
contains 'EDB Rebate at 35%: $(1,275,411)' applied to ~$3.64M QPE.

This rate is budget-evidenced (PARSED), NOT verified from EDB statute text.
Promote to VERIFIED only after reviewing current EDB Film Production Incentive
guidelines directly from edbmauritius.org or equivalent primary source.

Also sets vessel_marine_qualifies context note in program metadata.

Revision ID: 0009
Revises: 0008
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# Re-derive the same UUID5 as 0008 to target the correct row
_NS = uuid.UUID("a1000000-0008-0000-0001-000000000000")
PROG_MU_ID = str(uuid.uuid5(_NS, "prog:mu_edb_incentive"))


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE incentive_programs
            SET
                confidence_tier    = 'PARSED',
                base_rate          = 0.35,
                max_rate           = 0.35,
                name               = 'Mauritius EDB Production Incentive (Budget-Evidenced 35%)',
                notes              = 'PARSED tier: base rate of 35% inferred from production budget '
                                     'evidence. Not verified from EDB statute text. '
                                     'Vessel/marine costs confirmed qualifying per budget QPE. '
                                     'ATL scope unknown. Cashflow timing unknown. '
                                     'Finance cost on rebate receivable not modeled.',
                updated_at         = :now
            WHERE id = :prog_id
            """
        ).bindparams(prog_id=PROG_MU_ID, now=NOW)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE incentive_programs
            SET
                confidence_tier = 'DISCOVERY',
                base_rate       = NULL,
                max_rate        = NULL,
                name            = 'Mauritius EDB Production Incentive (Unverified)',
                notes           = 'No verified structured film production incentive confirmed.',
                updated_at      = :now
            WHERE id = :prog_id
            """
        ).bindparams(prog_id=PROG_MU_ID, now=NOW)
    )
