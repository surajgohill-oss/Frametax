"""Script Analyzer SA-1: canonical script entities

Adds the deterministic, version-scoped script structure the SA-1 vertical
slice persists, plus the minimum requirement/assumption layer the generic
CanonicalProductionState needs.

New tables:
  scenes                    — version-scoped deterministic screenplay scene
  characters                — fictional character per screenplay version
                              (deliberately NOT ProjectPerson)
  production_requirements   — evidence-backed "the production needs X"
  production_assumptions    — explicit producer inputs, with authority state

Extended tables (all additive/nullable — nothing existing is rewritten):
  screenplay_documents          parse provenance + status
  extracted_script_elements     -> canonical SceneElement
  project_location_requirements -> canonical LocationRequirement

Revision ID: 0067
Revises: 0066
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0067"
down_revision: Union[str, None] = "0066"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── scenes ─────────────────────────────────────────────────────────────
    op.create_table(
        "scenes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("screenplay_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("source_scene_number", sa.String(length=20)),
        sa.Column("raw_heading", sa.Text(), nullable=False),
        sa.Column("normalized_heading", sa.Text(), nullable=False),
        sa.Column("int_ext", sa.String(length=10), nullable=False),
        sa.Column("time_of_day", sa.String(length=12), nullable=False),
        sa.Column("scripted_location", sa.Text()),
        sa.Column("location_key", sa.String(length=255)),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer()),
        sa.Column("page_end", sa.Integer()),
        sa.Column("eighths", sa.Integer()),
        sa.Column("scene_hash", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["screenplay_id"], ["screenplay_documents.id"],
                                ondelete="CASCADE"),
        sa.UniqueConstraint("screenplay_id", "sequence",
                            name="uq_scenes_screenplay_sequence"),
    )
    op.create_index("ix_scenes_screenplay_id", "scenes", ["screenplay_id"])
    op.create_index("ix_scenes_int_ext", "scenes", ["int_ext"])
    op.create_index("ix_scenes_time_of_day", "scenes", ["time_of_day"])
    op.create_index("ix_scenes_location_key", "scenes", ["location_key"])

    # ── characters ─────────────────────────────────────────────────────────
    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("screenplay_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_name", sa.String(length=120), nullable=False),
        sa.Column("aliases", postgresql.JSONB()),
        sa.Column("scene_sequences", postgresql.JSONB()),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dialogue_block_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dialogue_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_speaking_role", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("eighths_burden", sa.Integer()),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["screenplay_id"], ["screenplay_documents.id"],
                                ondelete="CASCADE"),
        sa.UniqueConstraint("screenplay_id", "canonical_name",
                            name="uq_characters_screenplay_name"),
    )
    op.create_index("ix_characters_screenplay_id", "characters", ["screenplay_id"])
    op.create_index("ix_characters_canonical_name", "characters", ["canonical_name"])

    # ── production_requirements ────────────────────────────────────────────
    op.create_table(
        "production_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_key", sa.String(length=64), nullable=False),
        sa.Column("normalized_value", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("quantity", sa.Numeric(18, 4)),
        sa.Column("quantity_max", sa.Numeric(18, 4)),
        sa.Column("unit", sa.String(length=32)),
        sa.Column("evidence_state", sa.String(length=32), nullable=False,
                  server_default="DETERMINISTIC_DERIVED"),
        sa.Column("is_interpretation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source_screenplay_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_document_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_scene_sequences", postgresql.JSONB()),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sample_evidence", sa.Text()),
        sa.Column("parser_version", sa.String(length=64)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_screenplay_id"], ["screenplay_documents.id"],
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_document_version_id"], ["document_versions.id"],
                                ondelete="SET NULL"),
    )
    op.create_index("ix_production_requirements_project_id",
                    "production_requirements", ["project_id"])
    op.create_index("ix_production_requirements_key",
                    "production_requirements", ["requirement_key"])
    op.create_index("ix_production_requirements_evidence_state",
                    "production_requirements", ["evidence_state"])
    op.create_index("ix_production_requirements_source_screenplay_id",
                    "production_requirements", ["source_screenplay_id"])

    # ── production_assumptions ─────────────────────────────────────────────
    op.create_table(
        "production_assumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assumption_key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text()),
        sa.Column("value_type", sa.String(length=20)),
        sa.Column("unit", sa.String(length=32)),
        sa.Column("evidence_state", sa.String(length=32), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("source", sa.String(length=120)),
        sa.Column("lower_bound", sa.Numeric(18, 4)),
        sa.Column("upper_bound", sa.Numeric(18, 4)),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_production_assumptions_project_id",
                    "production_assumptions", ["project_id"])
    op.create_index("ix_production_assumptions_key",
                    "production_assumptions", ["assumption_key"])
    op.create_index("ix_production_assumptions_evidence_state",
                    "production_assumptions", ["evidence_state"])

    # ── screenplay_documents: parse provenance ─────────────────────────────
    op.add_column("screenplay_documents", sa.Column("parser_version", sa.String(length=64)))
    op.add_column("screenplay_documents", sa.Column("input_fingerprint", sa.String(length=64)))
    op.add_column("screenplay_documents", sa.Column("parse_status", sa.String(length=40)))
    op.add_column("screenplay_documents", sa.Column("parse_error", sa.Text()))
    op.add_column("screenplay_documents", sa.Column("page_basis", sa.String(length=40)))
    op.add_column("screenplay_documents", sa.Column("total_eighths", sa.Integer()))
    op.add_column("screenplay_documents", sa.Column("parsed_at", sa.String(length=40)))
    op.add_column("screenplay_documents", sa.Column("parse_warnings", postgresql.JSONB()))
    op.create_index("ix_screenplay_documents_input_fingerprint",
                    "screenplay_documents", ["input_fingerprint"])
    op.create_index("ix_screenplay_documents_parse_status",
                    "screenplay_documents", ["parse_status"])

    # ── extracted_script_elements -> canonical SceneElement ────────────────
    op.add_column("extracted_script_elements",
                  sa.Column("scene_id", postgresql.UUID(as_uuid=True)))
    op.add_column("extracted_script_elements", sa.Column("taxonomy_key", sa.String(length=48)))
    op.add_column("extracted_script_elements", sa.Column("normalized_value", sa.String(length=512)))
    op.add_column("extracted_script_elements", sa.Column("quantity", sa.Numeric(18, 4)))
    op.add_column("extracted_script_elements", sa.Column("quantity_max", sa.Numeric(18, 4)))
    op.add_column("extracted_script_elements", sa.Column("unit", sa.String(length=32)))
    op.add_column("extracted_script_elements", sa.Column("char_start", sa.Integer()))
    op.add_column("extracted_script_elements", sa.Column("char_end", sa.Integer()))
    op.add_column("extracted_script_elements", sa.Column("evidence_hash", sa.String(length=64)))
    op.add_column("extracted_script_elements", sa.Column("extraction_method", sa.String(length=40)))
    op.add_column("extracted_script_elements", sa.Column("evidence_state", sa.String(length=40)))
    op.add_column("extracted_script_elements",
                  sa.Column("is_interpretation", sa.Boolean(), nullable=False,
                            server_default="false"))
    op.add_column("extracted_script_elements", sa.Column("review_state", sa.String(length=24)))
    op.add_column("extracted_script_elements",
                  sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True)))
    op.add_column("extracted_script_elements", sa.Column("parser_version", sa.String(length=64)))
    op.create_foreign_key("fk_extracted_script_elements_scene_id",
                          "extracted_script_elements", "scenes",
                          ["scene_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_extracted_script_elements_superseded_by",
                          "extracted_script_elements", "extracted_script_elements",
                          ["superseded_by_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_extracted_script_elements_scene_id",
                    "extracted_script_elements", ["scene_id"])
    op.create_index("ix_extracted_script_elements_taxonomy_key",
                    "extracted_script_elements", ["taxonomy_key"])
    op.create_index("ix_extracted_script_elements_extraction_method",
                    "extracted_script_elements", ["extraction_method"])
    op.create_index("ix_extracted_script_elements_evidence_state",
                    "extracted_script_elements", ["evidence_state"])

    # ── project_location_requirements -> canonical LocationRequirement ─────
    op.add_column("project_location_requirements", sa.Column("location_key", sa.String(length=255)))
    op.add_column("project_location_requirements",
                  sa.Column("source_screenplay_id", postgresql.UUID(as_uuid=True)))
    op.add_column("project_location_requirements", sa.Column("scene_sequences", postgresql.JSONB()))
    op.add_column("project_location_requirements", sa.Column("scene_count", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("eighths_total", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("int_count", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("ext_count", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("day_count", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("night_count", sa.Integer()))
    op.add_column("project_location_requirements", sa.Column("is_recurring", sa.Boolean()))
    op.add_column("project_location_requirements",
                  sa.Column("production_approach", sa.String(length=24)))
    op.add_column("project_location_requirements",
                  sa.Column("production_location", sa.String(length=255)))
    op.add_column("project_location_requirements", sa.Column("evidence_state", sa.String(length=32)))
    op.add_column("project_location_requirements", sa.Column("parser_version", sa.String(length=64)))
    op.create_foreign_key("fk_project_location_requirements_screenplay",
                          "project_location_requirements", "screenplay_documents",
                          ["source_screenplay_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_project_location_requirements_location_key",
                    "project_location_requirements", ["location_key"])
    op.create_index("ix_project_location_requirements_source_screenplay_id",
                    "project_location_requirements", ["source_screenplay_id"])


def downgrade() -> None:
    op.drop_index("ix_project_location_requirements_source_screenplay_id",
                  table_name="project_location_requirements")
    op.drop_index("ix_project_location_requirements_location_key",
                  table_name="project_location_requirements")
    op.drop_constraint("fk_project_location_requirements_screenplay",
                       "project_location_requirements", type_="foreignkey")
    for col in ("parser_version", "evidence_state", "production_location",
                "production_approach", "is_recurring", "night_count", "day_count",
                "ext_count", "int_count", "eighths_total", "scene_count",
                "scene_sequences", "source_screenplay_id", "location_key"):
        op.drop_column("project_location_requirements", col)

    op.drop_index("ix_extracted_script_elements_evidence_state",
                  table_name="extracted_script_elements")
    op.drop_index("ix_extracted_script_elements_extraction_method",
                  table_name="extracted_script_elements")
    op.drop_index("ix_extracted_script_elements_taxonomy_key",
                  table_name="extracted_script_elements")
    op.drop_index("ix_extracted_script_elements_scene_id",
                  table_name="extracted_script_elements")
    op.drop_constraint("fk_extracted_script_elements_superseded_by",
                       "extracted_script_elements", type_="foreignkey")
    op.drop_constraint("fk_extracted_script_elements_scene_id",
                       "extracted_script_elements", type_="foreignkey")
    for col in ("parser_version", "superseded_by_id", "review_state",
                "is_interpretation", "evidence_state", "extraction_method",
                "evidence_hash", "char_end", "char_start", "unit",
                "quantity_max", "quantity", "normalized_value", "taxonomy_key",
                "scene_id"):
        op.drop_column("extracted_script_elements", col)

    op.drop_index("ix_screenplay_documents_parse_status", table_name="screenplay_documents")
    op.drop_index("ix_screenplay_documents_input_fingerprint", table_name="screenplay_documents")
    for col in ("parse_warnings", "parsed_at", "total_eighths", "page_basis",
                "parse_error", "parse_status", "input_fingerprint", "parser_version"):
        op.drop_column("screenplay_documents", col)

    op.drop_table("production_assumptions")
    op.drop_table("production_requirements")
    op.drop_table("characters")
    op.drop_table("scenes")
