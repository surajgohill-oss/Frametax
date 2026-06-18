"""initial schema — all 23 tables

Revision ID: 0001
Revises:
Create Date: 2025-06-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.String(512)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # 3. jurisdictions (before projects — projects FK to jurisdictions)
    op.create_table(
        "jurisdictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("iso_code", sa.String(20), unique=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("currency_code", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("country_code", sa.String(5), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_jurisdictions_code", "jurisdictions", ["code"])
    op.create_index("ix_jurisdictions_level", "jurisdictions", ["level"])
    op.create_index("ix_jurisdictions_country_code", "jurisdictions", ["country_code"])

    # 4. projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("logline", sa.Text),
        sa.Column("genre", sa.String(100)),
        sa.Column("format", sa.String(100)),
        sa.Column("total_budget_usd", sa.Numeric(18, 2)),
        sa.Column("home_jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("target_shoot_year", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    # 5. source_documents
    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("authority_name", sa.String(255)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("publication_date", sa.String(20)),
        sa.Column("effective_from", sa.String(20)),
        sa.Column("effective_until", sa.String(20)),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("raw_text", sa.Text),
        sa.Column("page_count", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_documents_document_type", "source_documents", ["document_type"])

    # 6. qualification_tests (before incentive_programs — programs FK to tests)
    op.create_table(
        "qualification_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("total_available_points", sa.Integer),
        sa.Column("minimum_pass_points", sa.Integer),
        sa.Column("has_section_minimums", sa.Boolean, server_default="false"),
        sa.Column("section_minimums_json", postgresql.JSONB),
        sa.Column("authority_url", sa.String(2048)),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_qualification_tests_slug", "qualification_tests", ["slug"])

    # 7. qualification_test_rules
    op.create_table(
        "qualification_test_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("qualification_tests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_code", sa.String(20), nullable=False),
        sa.Column("section", sa.String(10)),
        sa.Column("section_name", sa.String(100)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("max_points", sa.Integer, nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False),
        sa.Column("input_key", sa.String(100), nullable=False),
        sa.Column("threshold_value", sa.Numeric(10, 6)),
        sa.Column("scoring_logic", sa.Text, nullable=False),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_qualification_test_rules_test_id", "qualification_test_rules", ["test_id"])

    # 8. incentive_programs
    op.create_table(
        "incentive_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("program_type", sa.String(30), nullable=False),
        sa.Column("credit_basis", sa.String(30), nullable=False),
        sa.Column("base_rate", sa.Numeric(7, 6)),
        sa.Column("max_rate", sa.Numeric(7, 6)),
        sa.Column("is_refundable", sa.Boolean),
        sa.Column("is_transferable", sa.Boolean),
        sa.Column("transferable_value_pct", sa.Numeric(7, 6)),
        sa.Column("is_competitive", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("annual_cap_local", sa.Numeric(18, 2)),
        sa.Column("requires_cultural_test", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("cultural_test_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("qualification_tests.id"), nullable=True),
        sa.Column("requires_local_entity", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("effective_from", sa.String(20)),
        sa.Column("effective_until", sa.String(20)),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("authority_url", sa.String(2048)),
        sa.Column("last_verified_date", sa.String(20)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incentive_programs_jurisdiction_id", "incentive_programs", ["jurisdiction_id"])
    op.create_index("ix_incentive_programs_slug", "incentive_programs", ["slug"])
    op.create_index("ix_incentive_programs_program_type", "incentive_programs", ["program_type"])

    # 9. incentive_rules
    op.create_table(
        "incentive_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("threshold_numeric", sa.Numeric(20, 8)),
        sa.Column("threshold_text", sa.String(512)),
        sa.Column("fail_action", sa.String(30), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("source_page", sa.Integer),
        sa.Column("source_excerpt", sa.Text),
        sa.Column("statutory_reference", sa.String(255)),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incentive_rules_program_id", "incentive_rules", ["program_id"])
    op.create_index("ix_incentive_rules_rule_type", "incentive_rules", ["rule_type"])

    # 10. qualifying_spend_categories
    op.create_table(
        "qualifying_spend_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spend_category", sa.String(50), nullable=False),
        sa.Column("qualifies", sa.Boolean, nullable=False),
        sa.Column("jurisdiction_spend_only", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_qualifying_spend_categories_program_id", "qualifying_spend_categories", ["program_id"])

    # 11. program_uplifts
    op.create_table(
        "program_uplifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("additional_rate", sa.Numeric(7, 6), nullable=False),
        sa.Column("applies_to", sa.String(50), nullable=False),
        sa.Column("condition_type", sa.String(50), nullable=False),
        sa.Column("condition_threshold", sa.Numeric(10, 6)),
        sa.Column("condition_text", sa.String(512)),
        sa.Column("is_stackable_with_other_uplifts", sa.Boolean, server_default="true"),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 12. legal_stacking_rules
    op.create_table(
        "legal_stacking_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("program_a_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id"), nullable=False),
        sa.Column("program_b_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id"), nullable=False),
        sa.Column("rule_type", sa.String(20), nullable=False),
        sa.Column("condition_text", sa.Text),
        sa.Column("statutory_reference", sa.String(255)),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_legal_stacking_rules_program_a_id", "legal_stacking_rules", ["program_a_id"])
    op.create_index("ix_legal_stacking_rules_program_b_id", "legal_stacking_rules", ["program_b_id"])

    # 13. local_cost_benchmarks
    op.create_table(
        "local_cost_benchmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baseline_jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("crew_rate_multiplier", sa.Numeric(8, 6)),
        sa.Column("equipment_rental_multiplier", sa.Numeric(8, 6)),
        sa.Column("stage_facility_multiplier", sa.Numeric(8, 6)),
        sa.Column("location_fees_multiplier", sa.Numeric(8, 6)),
        sa.Column("post_production_multiplier", sa.Numeric(8, 6)),
        sa.Column("vfx_multiplier", sa.Numeric(8, 6)),
        sa.Column("catering_multiplier", sa.Numeric(8, 6)),
        sa.Column("key_crew_daily_travel_usd", sa.Numeric(10, 2)),
        sa.Column("category_overrides_json", postgresql.JSONB),
        sa.Column("data_source", sa.String(512)),
        sa.Column("as_of_date", sa.String(20)),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_local_cost_benchmarks_jurisdiction_id", "local_cost_benchmarks", ["jurisdiction_id"])

    # 14. union_fringe_rules
    op.create_table(
        "union_fringe_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("union_name", sa.String(255), nullable=False),
        sa.Column("fringe_rate", sa.Numeric(7, 6), nullable=False),
        sa.Column("applies_to_categories", postgresql.JSONB),
        sa.Column("cap_per_employee_usd", sa.Numeric(12, 2)),
        sa.Column("effective_from", sa.String(20)),
        sa.Column("effective_until", sa.String(20)),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 15. talent_profiles
    op.create_table(
        "talent_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("imdb_id", sa.String(50), unique=True),
        sa.Column("primary_nationality", sa.String(100)),
        sa.Column("known_residencies", postgresql.JSONB),
        sa.Column("guild_memberships", postgresql.JSONB),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_talent_profiles_name", "talent_profiles", ["name"])
    op.create_index("ix_talent_profiles_role", "talent_profiles", ["role"])

    # 16. talent_qualification_attributes
    op.create_table(
        "talent_qualification_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("talent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("attribute_key", sa.String(100), nullable=False),
        sa.Column("attribute_value", sa.Boolean),
        sa.Column("attribute_text", sa.String(255)),
        sa.Column("confirmed", sa.Boolean, server_default="false"),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 17. budget_documents
    op.create_table(
        "budget_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("raw_text", sa.Text),
        sa.Column("page_count", sa.Integer),
        sa.Column("currency_code", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("total_budget_raw", sa.Numeric(18, 2)),
        sa.Column("origin_city", sa.String(255)),
        sa.Column("rate_base", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("extraction_status", sa.String(20), server_default="pending"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_budget_documents_project_id", "budget_documents", ["project_id"])

    # 18. budget_line_items
    op.create_table(
        "budget_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("budget_document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("budget_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(255)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("atl_btl", sa.String(10), nullable=False, server_default="btl"),
        sa.Column("spend_category", sa.String(50)),
        sa.Column("is_labor", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_resident_labor", sa.Boolean),
        sa.Column("is_fixed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("amount_raw", sa.Numeric(18, 2)),
        sa.Column("amount_normalized", sa.Numeric(18, 2)),
        sa.Column("currency_code", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("amount_usd", sa.Numeric(18, 2)),
        sa.Column("cash_amount_usd", sa.Numeric(18, 2)),
        sa.Column("accounting_amount_usd", sa.Numeric(18, 2)),
        sa.Column("compensation_type", sa.String(20), nullable=False, server_default="cash"),
        sa.Column("deferred_amount_usd", sa.Numeric(18, 2)),
        sa.Column("equity_amount_usd", sa.Numeric(18, 2)),
        sa.Column("in_kind_amount_usd", sa.Numeric(18, 2)),
        sa.Column("is_qualifying_spend_candidate", sa.Boolean, server_default="true"),
        sa.Column("qualifying_amount_usd", sa.Numeric(18, 2)),
        sa.Column("source_row", sa.Integer),
        sa.Column("source_page", sa.Integer),
        sa.Column("extraction_confidence", sa.Numeric(5, 4)),
        sa.Column("review_status", sa.String(20), server_default="pending"),
        sa.Column("llm_extracted_raw", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_budget_line_items_budget_document_id", "budget_line_items", ["budget_document_id"])
    op.create_index("ix_budget_line_items_spend_category", "budget_line_items", ["spend_category"])

    # 19. screenplay_documents
    op.create_table(
        "screenplay_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("raw_text", sa.Text),
        sa.Column("page_count", sa.Integer),
        sa.Column("word_count", sa.Integer),
        sa.Column("extraction_status", sa.String(20), server_default="pending"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_screenplay_documents_project_id", "screenplay_documents", ["project_id"])

    # 20. screenplay_chunks
    op.create_table(
        "screenplay_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("screenplay_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("screenplay_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("start_page", sa.Integer),
        sa.Column("end_page", sa.Integer),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_screenplay_chunks_screenplay_id", "screenplay_chunks", ["screenplay_id"])

    # 21. extracted_script_elements
    op.create_table(
        "extracted_script_elements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("screenplay_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("screenplay_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("element_type", sa.String(100), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("context_excerpt", sa.Text),
        sa.Column("page_reference", sa.Integer),
        sa.Column("extraction_confidence", sa.Numeric(5, 4)),
        sa.Column("is_confirmed", sa.String(1)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_extracted_script_elements_screenplay_id", "extracted_script_elements", ["screenplay_id"])
    op.create_index("ix_extracted_script_elements_element_type", "extracted_script_elements", ["element_type"])

    # 22. production_structures
    op.create_table(
        "production_structures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("jurisdiction_allocations", postgresql.JSONB),
        sa.Column("claimed_program_ids", postgresql.JSONB),
        sa.Column("talent_arrangements", postgresql.JSONB),
        sa.Column("assumed_jurisdiction_spend_pcts", postgresql.JSONB),
        sa.Column("uses_georgia_logo", sa.Boolean),
        sa.Column("is_official_coproduction", sa.Boolean),
        sa.Column("coproduction_treaty", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_production_structures_project_id", "production_structures", ["project_id"])

    # 23. structure_calculation_results
    op.create_table(
        "structure_calculation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("structure_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production_structures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engine_version", sa.String(50), nullable=False),
        sa.Column("total_budget_usd", sa.Numeric(18, 2)),
        sa.Column("rebase_btl_usd", sa.Numeric(18, 2)),
        sa.Column("fixed_atl_usd", sa.Numeric(18, 2)),
        sa.Column("total_qualifying_spend_usd", sa.Numeric(18, 2)),
        sa.Column("total_incentive_value_usd", sa.Numeric(18, 2)),
        sa.Column("total_travel_cost_usd", sa.Numeric(18, 2)),
        sa.Column("true_net_cost_usd", sa.Numeric(18, 2)),
        sa.Column("risk_adjusted_net_cost_usd", sa.Numeric(18, 2)),
        sa.Column("effective_incentive_rate", sa.Numeric(8, 6)),
        sa.Column("rank_by_net_cost", sa.Integer),
        sa.Column("rank_by_incentive_value", sa.Integer),
        sa.Column("rank_by_optimization_opportunity", sa.Integer),
        sa.Column("program_results", postgresql.JSONB),
        sa.Column("qualification_test_scores", postgresql.JSONB),
        sa.Column("calculation_trace_json", postgresql.JSONB),
        sa.Column("has_unverified_inputs", sa.Boolean, server_default="false"),
        sa.Column("legal_review_required", sa.Boolean, server_default="false"),
        sa.Column("qualification_gaps", postgresql.JSONB),
        sa.Column("stacking_violations", postgresql.JSONB),
        sa.Column("warnings", postgresql.JSONB),
        sa.Column("optimization_opportunities", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_structure_calculation_results_structure_id",
                    "structure_calculation_results", ["structure_id"])

    # 24. fx_rates
    op.create_table(
        "fx_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("base_currency", sa.String(10), nullable=False),
        sa.Column("quote_currency", sa.String(10), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("effective_date", sa.String(20), nullable=False),
        sa.Column("source", sa.String(255), server_default="open.er-api.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fx_rates_base_currency", "fx_rates", ["base_currency"])
    op.create_index("ix_fx_rates_effective_date", "fx_rates", ["effective_date"])
    op.create_unique_constraint("uq_fx_rate_pair_date", "fx_rates",
                                ["base_currency", "quote_currency", "effective_date"])

    # 25. ingestion_jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("document_type", sa.String(50)),
        sa.Column("source_path", sa.String(1024)),
        sa.Column("target_table", sa.String(100)),
        sa.Column("target_id", postgresql.UUID(as_uuid=True)),
        sa.Column("worker_id", sa.String(255)),
        sa.Column("started_at", sa.String(30)),
        sa.Column("completed_at", sa.String(30)),
        sa.Column("items_processed", sa.Integer),
        sa.Column("items_failed", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("result_summary", postgresql.JSONB),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ingestion_jobs_job_type", "ingestion_jobs", ["job_type"])
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("ingestion_jobs")
    op.drop_table("fx_rates")
    op.drop_table("structure_calculation_results")
    op.drop_table("production_structures")
    op.drop_table("extracted_script_elements")
    op.drop_table("screenplay_chunks")
    op.drop_table("screenplay_documents")
    op.drop_table("budget_line_items")
    op.drop_table("budget_documents")
    op.drop_table("talent_qualification_attributes")
    op.drop_table("talent_profiles")
    op.drop_table("union_fringe_rules")
    op.drop_table("local_cost_benchmarks")
    op.drop_table("legal_stacking_rules")
    op.drop_table("program_uplifts")
    op.drop_table("qualifying_spend_categories")
    op.drop_table("incentive_rules")
    op.drop_table("incentive_programs")
    op.drop_table("qualification_test_rules")
    op.drop_table("qualification_tests")
    op.drop_table("source_documents")
    op.drop_table("projects")
    op.drop_table("jurisdictions")
    op.drop_table("users")
    op.drop_table("organizations")
