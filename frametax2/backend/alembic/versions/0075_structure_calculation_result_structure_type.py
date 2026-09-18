"""Ingestion acceptance closeout: persist authoritative structure_type

Adds structure_calculation_results.structure_type, a real, persisted
column carrying the same value evaluate_project() already writes into
each row's own calculation_trace_json["structure_type"] (or, for the two
candidate families whose trace never carried that literal key,
calculation_trace_json["structural_family"] instead -- confirmed by
direct read of every one of the 35 real construction sites in
canonical_evaluation.py, none skipped). Removes the need for every reader
(project_workspace_view.py, canonical_production_view.py) to re-derive
this at serve time -- previously done either by reading back out of the
JSON trace, or, for an UNPRICEABLE candidate with no jurisdiction_
allocations row to resolve a code from, by parsing it out of the
structure's own display name string ("Full relocation to X").

Backfills every EXISTING row from its own already-persisted trace JSON
(never a guessed default) so a row written before this migration is
never left with a NULL a fresh row from the same code path would not
have. A row whose trace carries neither key (should not exist post the
canonical_evaluation.py fix, but the backfill is defensive) stays NULL --
an honest unknown, never fabricated.

Revision ID: 0075
Revises: 0074
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0075"
down_revision: Union[str, None] = "0074"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "structure_calculation_results",
        sa.Column("structure_type", sa.String(length=60), nullable=True),
    )
    op.create_index(
        "ix_structure_calculation_results_structure_type",
        "structure_calculation_results", ["structure_type"],
    )
    op.execute(
        """
        UPDATE structure_calculation_results
        SET structure_type = COALESCE(
            calculation_trace_json ->> 'structure_type',
            calculation_trace_json ->> 'structural_family'
        )
        WHERE structure_type IS NULL
          AND calculation_trace_json IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_structure_calculation_results_structure_type",
        table_name="structure_calculation_results",
    )
    op.drop_column("structure_calculation_results", "structure_type")
