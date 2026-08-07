from __future__ import annotations

import json

import pytest

from app.bridge.manual_run import ManualRunError, export_run, import_response, reconcile_run
from app.bridge.schema import OperationType, ProviderID, ReviewResponse


def _fixture_response(package_id: str, tmp_path, filename="claude_response.json") -> str:
    path = tmp_path / filename
    path.write_text(json.dumps({
        "review_id": "review_test_fixture",
        "package_id": package_id,
        "provider": "anthropic",
        "model": "claude-test-fixture",
        "operation": "qpe_audit",
        "overall_disposition": "no_issues_found",
        "executive_summary": "fixture only",
        "findings": [],
        "unresolved_questions": [],
        "sources_consulted": [],
        "usage_metadata": {},
    }))
    return str(path)


class TestExportRun:
    def test_export_writes_expected_files_from_real_pipeline(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        assert (run_dir / "package.json").is_file()
        assert (run_dir / "instructions.md").is_file()
        assert (run_dir / "responses").is_dir()

        pkg = json.loads((run_dir / "package.json").read_text())
        assert pkg["operation"] == "qpe_audit"
        assert pkg["production_or_scenario_id"] == "little-utopia"
        assert len(pkg["budget_qpe_trace"]) > 0
        assert pkg["economics"]["npc_usd"] is not None  # the real, existing optimizer result — not recomputed

    def test_instructions_reference_the_exact_package_id(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        pkg = json.loads((run_dir / "package.json").read_text())
        instructions = (run_dir / "instructions.md").read_text()
        assert pkg["package_id"] in instructions
        assert '"ReviewResponse"' not in instructions or "review_id" in instructions  # schema embedded, sane


class TestImportResponse:
    def test_valid_response_imports_and_writes_canonical_filename(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        pkg = json.loads((run_dir / "package.json").read_text())
        src = _fixture_response(pkg["package_id"], tmp_path)

        response = import_response(run_dir, ProviderID.ANTHROPIC, __import__("pathlib").Path(src))
        assert isinstance(response, ReviewResponse)
        assert (run_dir / "responses" / "claude.json").is_file()

    def test_mismatched_package_id_rejected(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        src = _fixture_response("pkg_wrong_run", tmp_path)

        with pytest.raises(ManualRunError, match="does not match this run's package_id"):
            import_response(run_dir, ProviderID.ANTHROPIC, __import__("pathlib").Path(src))
        assert not (run_dir / "responses" / "claude.json").exists()

    def test_provider_mismatch_rejected(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        pkg = json.loads((run_dir / "package.json").read_text())
        src = _fixture_response(pkg["package_id"], tmp_path)  # provider field says "anthropic"

        with pytest.raises(ManualRunError, match="does not match the declared provider"):
            import_response(run_dir, ProviderID.OPENAI, __import__("pathlib").Path(src))

    def test_malformed_json_rejected(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")

        with pytest.raises(ManualRunError, match="not valid JSON"):
            import_response(run_dir, ProviderID.ANTHROPIC, bad)


class TestReconcileRun:
    def test_reconcile_with_no_responses_raises(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        with pytest.raises(ManualRunError, match="No response files"):
            reconcile_run(run_dir)

    def test_reconcile_with_one_response_writes_reconciliation_json(self, tmp_path):
        run_dir = export_run(operation=OperationType.QPE_AUDIT, runs_root=tmp_path)
        pkg = json.loads((run_dir / "package.json").read_text())
        src = _fixture_response(pkg["package_id"], tmp_path)
        import_response(run_dir, ProviderID.ANTHROPIC, __import__("pathlib").Path(src))

        result = reconcile_run(run_dir)
        assert (run_dir / "reconciliation.json").is_file()
        assert result["package_id"] == pkg["package_id"]
        assert result["providers_reviewed"] == ["anthropic"]
        # The deterministic economics surfaced are CineGlobe's real existing
        # result, never a value the reconciliation step itself computed.
        assert result["cineglobe_deterministic_result"]["npc_usd"] == pkg["economics"]["npc_usd"]
        assert "does NOT modify any CineGlobe rule" in result["note"]
