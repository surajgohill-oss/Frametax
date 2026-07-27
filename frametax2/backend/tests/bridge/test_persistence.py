from __future__ import annotations

from app.bridge.persistence import (
    PackageRecord,
    ProviderResponseRecord,
    get_session,
)


class TestPackagePersistence:
    def test_insert_and_read_back(self):
        session = get_session()
        try:
            session.add(PackageRecord(
                package_id="pkg_1", package_schema_version="1.0.0",
                production_or_scenario_id="little-utopia", operation="qualification_audit",
                confidentiality="internal", generated_at="2026-01-01T00:00:00Z",
                package_json='{"package_id": "pkg_1"}',
            ))
            session.commit()
            row = session.get(PackageRecord, "pkg_1")
            assert row is not None
            assert row.production_or_scenario_id == "little-utopia"
        finally:
            session.close()


class TestProviderResponsePersistence:
    def test_insert_response_and_query_by_package(self):
        session = get_session()
        try:
            session.add(ProviderResponseRecord(
                response_id="resp_1", package_id="pkg_1", provider="anthropic",
                model_id="claude-test", operation="qualification_audit",
                request_json="{}", response_text="hello", usage_json="{}",
                error_category="none", request_content_hash="abc123",
            ))
            session.commit()
            rows = session.query(ProviderResponseRecord).filter(
                ProviderResponseRecord.package_id == "pkg_1"
            ).all()
            assert len(rows) == 1
            assert rows[0].provider == "anthropic"
        finally:
            session.close()

    def test_duplicate_request_hash_detectable(self):
        """The table itself doesn't enforce uniqueness on
        request_content_hash (a re-run is legitimate — see spec's
        'cache/reuse for identical research requests') — but the hash
        must be queryable so a caller CAN detect and skip a duplicate."""
        session = get_session()
        try:
            for i in range(2):
                session.add(ProviderResponseRecord(
                    response_id=f"resp_dup_{i}", package_id="pkg_1", provider="openai",
                    model_id="gpt-test", operation="qualification_audit",
                    request_json="{}", response_text="x", usage_json="{}",
                    error_category="none", request_content_hash="same-hash-both-times",
                ))
            session.commit()
            existing = session.query(ProviderResponseRecord).filter(
                ProviderResponseRecord.request_content_hash == "same-hash-both-times"
            ).all()
            assert len(existing) == 2  # both persisted (append-only) — caller decides whether to reuse
        finally:
            session.close()


class TestTablesAreIsolatedPerTest:
    def test_fresh_db_has_no_leftover_rows_from_other_tests(self):
        session = get_session()
        try:
            assert session.query(PackageRecord).count() == 0
        finally:
            session.close()
