"""0062 — Project Library Phase B: persistence foundation.

Adds the persistence primitives the Company Project Library needs:

  - projects.lifecycle, projects.leading_structure_id
  - project_aliases
  - documents / document_versions / document_version_sources
    (the universal Document identity/version/source layer — owned by
    exactly one of Project or Organization, enforced by a CHECK constraint,
    so company/slate documents and individual-film documents share one
    architecture instead of a duplicated implementation)
  - budget_documents.document_version_id, screenplay_documents.document_version_id
    (additive links from the existing rich typed models into the universal
    layer — those tables are otherwise untouched)
  - project_assets (artwork)
  - project_facts (structured facts with provenance)
  - project_activity (immutable provenance log)
  - project_location_requirements
  - project_people (Project <-> TalentProfile join)
  - structure_calculation_results.input_budget_document_version_id,
    .input_fingerprint, .input_snapshot_json (calculation-input provenance)
  - final_production_results (modeled vs. actual)

This is a persistence-only migration: no data is seeded, no Little Utopia
row is created, no existing table's existing columns are altered or
dropped. See CAPABILITY_LEDGER.md "Project Library Phase B" for the full
architecture writeup.

Revision ID: 0062
Revises: 0061
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0062"
down_revision: Union[str, None] = "0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. projects — lifecycle (user-controlled only) + leading structure
    # ------------------------------------------------------------------
    op.add_column(
        "projects",
        sa.Column("lifecycle", sa.String(20), nullable=False, server_default="EVALUATION"),
    )
    op.add_column(
        "projects",
        sa.Column("leading_structure_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_leading_structure_id", "projects", "production_structures",
        ["leading_structure_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_projects_leading_structure_id", "projects", ["leading_structure_id"])

    # ------------------------------------------------------------------
    # 2. project_aliases
    # ------------------------------------------------------------------
    op.create_table(
        "project_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(512), nullable=False),
        sa.Column("source", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_aliases_project_id", "project_aliases", ["project_id"])

    # ------------------------------------------------------------------
    # 3. documents (universal document identity — Project XOR Organization owner)
    #    current_version_id FK to document_versions is added AFTER that
    #    table exists (circular dependency between documents <-> document_versions).
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(project_id IS NOT NULL AND organization_id IS NULL) OR "
            "(project_id IS NULL AND organization_id IS NOT NULL)",
            name="ck_documents_exactly_one_owner",
        ),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"])
    op.create_index("ix_documents_category", "documents", ["category"])

    # ------------------------------------------------------------------
    # 4. document_versions
    # ------------------------------------------------------------------
    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(512)),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("file_size", sa.Integer),
        sa.Column("detected_date", sa.String(20)),
        sa.Column("version_label", sa.String(255)),
        sa.Column("ingested_at", sa.String(30)),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("supersedes_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("extraction_status", sa.String(20)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])
    op.create_index("ix_document_versions_checksum_sha256", "document_versions", ["checksum_sha256"])
    op.create_foreign_key(
        "fk_document_versions_supersedes", "document_versions", "document_versions",
        ["supersedes_version_id"], ["id"], ondelete="SET NULL",
    )

    # Now that document_versions exists, close the circular FK from documents.
    op.create_foreign_key(
        "fk_documents_current_version", "documents", "document_versions",
        ["current_version_id"], ["id"], ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # 5. document_version_sources
    # ------------------------------------------------------------------
    op.create_table(
        "document_version_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_pointer", sa.String(2048), nullable=False),
        sa.Column("source_path", sa.Text),
        sa.Column("source_owner", sa.String(320)),
        sa.Column("source_status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("last_verified_at", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_version_id", "source_pointer", name="uq_docversion_source_pointer"),
    )
    op.create_index(
        "ix_document_version_sources_document_version_id",
        "document_version_sources", ["document_version_id"],
    )
    op.create_index("ix_document_version_sources_source_type", "document_version_sources", ["source_type"])

    # ------------------------------------------------------------------
    # 6. Additive links from existing typed document tables into the
    #    universal layer. Both tables, all their existing columns, and all
    #    their existing data (none in this dev DB) are otherwise untouched.
    # ------------------------------------------------------------------
    op.add_column(
        "budget_documents",
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_budget_documents_document_version_id", "budget_documents", "document_versions",
        ["document_version_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index(
        "ix_budget_documents_document_version_id", "budget_documents", ["document_version_id"],
    )

    op.add_column(
        "screenplay_documents",
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_screenplay_documents_document_version_id", "screenplay_documents", "document_versions",
        ["document_version_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index(
        "ix_screenplay_documents_document_version_id", "screenplay_documents", ["document_version_id"],
    )

    # ------------------------------------------------------------------
    # 7. project_assets (artwork)
    # ------------------------------------------------------------------
    op.create_table(
        "project_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False, server_default="artwork"),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("file_size", sa.Integer),
        sa.Column("is_master", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source_document_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_assets_project_id", "project_assets", ["project_id"])
    op.create_index("ix_project_assets_checksum_sha256", "project_assets", ["checksum_sha256"])

    # ------------------------------------------------------------------
    # 8. project_facts
    # ------------------------------------------------------------------
    op.create_table(
        "project_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fact_key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("value_type", sa.String(20)),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_document_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_location", sa.String(255)),
        sa.Column("extraction_confidence", sa.Numeric(5, 4)),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "fact_key", name="uq_project_facts_project_key"),
    )
    op.create_index("ix_project_facts_project_id", "project_facts", ["project_id"])
    op.create_index("ix_project_facts_fact_key", "project_facts", ["fact_key"])

    # ------------------------------------------------------------------
    # 9. project_activity (immutable provenance log)
    # ------------------------------------------------------------------
    op.create_table(
        "project_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor", sa.String(320)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("before_json", postgresql.JSONB),
        sa.Column("after_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_activity_project_id", "project_activity", ["project_id"])
    op.create_index("ix_project_activity_action", "project_activity", ["action"])

    # ------------------------------------------------------------------
    # 10. project_location_requirements
    # ------------------------------------------------------------------
    op.create_table(
        "project_location_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("is_flexible", sa.Boolean),
        sa.Column("source_document_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_project_location_requirements_project_id", "project_location_requirements", ["project_id"],
    )

    # ------------------------------------------------------------------
    # 11. project_people (Project <-> TalentProfile)
    # ------------------------------------------------------------------
    op.create_table(
        "project_people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("talent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_people_project_id", "project_people", ["project_id"])
    op.create_index("ix_project_people_talent_id", "project_people", ["talent_id"])

    # ------------------------------------------------------------------
    # 12. structure_calculation_results — calculation-input provenance
    #     (additive only; no optimizer/calculation logic touched)
    # ------------------------------------------------------------------
    op.add_column(
        "structure_calculation_results",
        sa.Column("input_budget_document_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_scr_input_budget_document_version_id",
        "structure_calculation_results", "document_versions",
        ["input_budget_document_version_id"], ["id"], ondelete="SET NULL",
    )
    op.add_column(
        "structure_calculation_results",
        sa.Column("input_fingerprint", sa.String(64)),
    )
    op.add_column(
        "structure_calculation_results",
        sa.Column("input_snapshot_json", postgresql.JSONB),
    )

    # ------------------------------------------------------------------
    # 13. final_production_results (modeled vs. actual — 1:1 per project)
    # ------------------------------------------------------------------
    op.create_table(
        "final_production_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leading_structure_id_at_decision", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production_structures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("modeled_economics_snapshot", postgresql.JSONB),
        sa.Column("final_incentive_expected_usd", sa.Numeric(18, 2)),
        sa.Column("final_incentive_applied_for_usd", sa.Numeric(18, 2)),
        sa.Column("final_incentive_approved_usd", sa.Numeric(18, 2)),
        sa.Column("final_incentive_realized_usd", sa.Numeric(18, 2)),
        sa.Column("final_local_cost_usd", sa.Numeric(18, 2)),
        sa.Column("final_production_cost_usd", sa.Numeric(18, 2)),
        sa.Column("variance_notes", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("recorded_at", sa.String(30)),
        sa.Column("recorded_by", sa.String(320)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_final_production_results_project_id"),
    )
    op.create_index("ix_final_production_results_project_id", "final_production_results", ["project_id"])


def downgrade() -> None:
    op.drop_table("final_production_results")

    op.drop_column("structure_calculation_results", "input_snapshot_json")
    op.drop_column("structure_calculation_results", "input_fingerprint")
    op.drop_constraint(
        "fk_scr_input_budget_document_version_id", "structure_calculation_results", type_="foreignkey",
    )
    op.drop_column("structure_calculation_results", "input_budget_document_version_id")

    op.drop_table("project_people")
    op.drop_table("project_location_requirements")
    op.drop_table("project_activity")
    op.drop_table("project_facts")
    op.drop_table("project_assets")

    op.drop_constraint(
        "fk_screenplay_documents_document_version_id", "screenplay_documents", type_="foreignkey",
    )
    op.drop_column("screenplay_documents", "document_version_id")
    op.drop_constraint(
        "fk_budget_documents_document_version_id", "budget_documents", type_="foreignkey",
    )
    op.drop_column("budget_documents", "document_version_id")

    op.drop_table("document_version_sources")
    op.drop_constraint("fk_documents_current_version", "documents", type_="foreignkey")
    op.drop_table("document_versions")
    op.drop_table("documents")

    op.drop_table("project_aliases")

    op.drop_constraint("fk_projects_leading_structure_id", "projects", type_="foreignkey")
    op.drop_column("projects", "leading_structure_id")
    op.drop_column("projects", "lifecycle")
