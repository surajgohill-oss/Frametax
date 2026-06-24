"""Phase D1/D2/D4: Cultural qualification rules and structure graph schema.

Revision ID: 0058
Revises: 0057
Create Date: 2026-06-23

Creates:
- cultural_qualification_rules table (D1/D2)
- structure_graph_edges table (D4)
- financing_interactions table (D5)
"""
from alembic import op
import sqlalchemy as sa

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # D1/D2: Cultural qualification rules
    # ------------------------------------------------------------------
    op.create_table(
        "cultural_qualification_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("program_slug", sa.String(128), nullable=False, index=True),
        sa.Column("test_slug", sa.String(128), nullable=True),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("jurisdiction_code", sa.String(16), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),  # required|optional|weighted|unknown
        sa.Column("weight", sa.Numeric(5, 3), nullable=True),
        sa.Column("min_pct", sa.Numeric(5, 3), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("confidence_tier", sa.String(16), nullable=False, server_default="DISCOVERY"),
    )
    op.create_index(
        "ix_cqr_program_slug", "cultural_qualification_rules", ["program_slug"]
    )

    # ------------------------------------------------------------------
    # D2: Cultural test definitions
    # ------------------------------------------------------------------
    op.create_table(
        "cultural_test_definitions",
        sa.Column("test_slug", sa.String(128), primary_key=True),
        sa.Column("test_name", sa.String(256), nullable=False),
        sa.Column("program_slug", sa.String(128), nullable=True),
        sa.Column("test_type", sa.String(32), nullable=False),  # points|checklist|threshold
        sa.Column("total_available_points", sa.Integer, nullable=True),
        sa.Column("minimum_pass_points", sa.Integer, nullable=True),
        sa.Column("section_minimums", sa.JSON, nullable=True),  # {section: min_pts}
        sa.Column("disqualifying_rules", sa.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("confidence_tier", sa.String(16), nullable=False, server_default="PARSED"),
    )

    # ------------------------------------------------------------------
    # D2: Cultural test criteria (individual point criteria per test)
    # ------------------------------------------------------------------
    op.create_table(
        "cultural_test_criteria",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("test_slug", sa.String(128), sa.ForeignKey("cultural_test_definitions.test_slug"),
                  nullable=False, index=True),
        sa.Column("criterion_code", sa.String(16), nullable=False),
        sa.Column("section", sa.String(8), nullable=True),
        sa.Column("section_name", sa.String(128), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("max_points", sa.Integer, nullable=False, server_default="1"),
        sa.Column("input_type", sa.String(16), nullable=False, server_default="boolean"),
        sa.Column("input_key", sa.String(64), nullable=False),
        sa.Column("threshold_value", sa.Numeric(8, 4), nullable=True),
        sa.Column("scoring_logic", sa.Text, nullable=True),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="false"),
    )

    # ------------------------------------------------------------------
    # D4: Structure graph edges
    # ------------------------------------------------------------------
    op.create_table(
        "structure_graph_edges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_type", sa.String(32), nullable=False),  # program|treaty|fund|region
        sa.Column("source_slug", sa.String(128), nullable=False, index=True),
        sa.Column("edge_type", sa.String(32), nullable=False),    # unlocks|requires|improves|reduces|incompatible_with
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_slug", sa.String(128), nullable=False, index=True),
        sa.Column("condition", sa.Text, nullable=True),
        sa.Column("magnitude", sa.Numeric(5, 3), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("confidence_tier", sa.String(16), nullable=False, server_default="DISCOVERY"),
    )
    op.create_index(
        "ix_sge_source_slug", "structure_graph_edges", ["source_slug"]
    )
    op.create_index(
        "ix_sge_target_slug", "structure_graph_edges", ["target_slug"]
    )
    op.create_index(
        "ix_sge_edge_type", "structure_graph_edges", ["edge_type"]
    )

    # ------------------------------------------------------------------
    # D5: Financing interactions
    # ------------------------------------------------------------------
    op.create_table(
        "financing_interactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug_a", sa.String(128), nullable=False, index=True),
        sa.Column("slug_b", sa.String(128), nullable=False, index=True),
        sa.Column("interaction_type", sa.String(32), nullable=False),
        sa.Column("reduction_pct", sa.Numeric(6, 4), nullable=True),
        sa.Column("ceiling_pct", sa.Numeric(6, 4), nullable=True),
        sa.Column("condition", sa.Text, nullable=True),
        sa.Column("jurisdiction", sa.String(16), nullable=True),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_fi_slug_pair", "financing_interactions", ["slug_a", "slug_b"]
    )


def downgrade() -> None:
    op.drop_table("financing_interactions")
    op.drop_table("structure_graph_edges")
    op.drop_table("cultural_test_criteria")
    op.drop_table("cultural_test_definitions")
    op.drop_table("cultural_qualification_rules")
