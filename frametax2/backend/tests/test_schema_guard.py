"""Focused tests for the fail-closed test-database schema guard (pure; no DB access)."""
from __future__ import annotations

from tests._schema_guard import check_schema, migration_head


def test_head_is_single_and_includes_source_incentive_estimates_migration():
    head = migration_head()
    assert head >= "0078"


def test_outdated_revision_aborts_with_remediation():
    msg = check_schema("frametax2_pytest", "0074", "0078", None)
    assert msg and "0074" in msg and "0078" in msg and "alembic upgrade head" in msg
    assert "source_incentive_estimates" in msg


def test_missing_alembic_version_aborts():
    assert check_schema("x", None, "0078", None)


def test_head_revision_proceeds():
    assert check_schema("frametax2_claude_optimizer_acceptance_20260919", "0078", "0078", None) is None


def test_expected_database_name_is_enforced_before_schema():
    msg = check_schema("frametax2_pytest", "0078", "0078", "frametax2_claude_optimizer_acceptance_20260919")
    assert msg and "frametax2_pytest" in msg
    assert check_schema("frametax2_claude_optimizer_acceptance_20260919", "0078", "0078",
                        "frametax2_claude_optimizer_acceptance_20260919") is None


def test_shared_database_is_always_refused():
    msg = check_schema("frametax2", "0078", "0078", None)
    assert msg and "shared" in msg and "prepare_test_database.py" in msg


def test_default_test_database_is_the_isolated_one(monkeypatch):
    from tests._schema_guard import DEFAULT_TEST_DATABASE_URL, select_test_database

    monkeypatch.delenv("DATABASE_URL", raising=False)
    select_test_database()
    import os
    assert os.environ["DATABASE_URL"] == DEFAULT_TEST_DATABASE_URL and DEFAULT_TEST_DATABASE_URL.endswith("/frametax2_pytest")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x@h/acceptance")
    select_test_database()
    assert os.environ["DATABASE_URL"] == "postgresql+psycopg://x@h/acceptance"
