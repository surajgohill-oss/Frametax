from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.bridge.schema import (
    CANDIDATE_REQUIREMENTS_JSON_SCHEMA,
    REVIEW_RESPONSE_JSON_SCHEMA,
    CandidateRequirementsResponse,
    Finding,
    FindingClassification,
    ModelRequest,
    OperationType,
    OverallDisposition,
    ProviderID,
    ReviewResponse,
    Severity,
)


class TestReviewResponseValidation:
    def test_valid_minimal_response(self):
        r = ReviewResponse(
            review_id="r1", package_id="p1", provider=ProviderID.ANTHROPIC, model="claude",
            operation=OperationType.QUALIFICATION_AUDIT, overall_disposition=OverallDisposition.NO_ISSUES_FOUND,
            executive_summary="clean",
        )
        assert r.findings == []

    def test_duplicate_finding_ids_rejected(self):
        f = dict(classification=FindingClassification.CONFIRMED, severity=Severity.LOW, rationale="x")
        with pytest.raises(ValidationError, match="Duplicate finding_id"):
            ReviewResponse(
                review_id="r1", package_id="p1", provider=ProviderID.ANTHROPIC, model="claude",
                operation=OperationType.QUALIFICATION_AUDIT, overall_disposition=OverallDisposition.ISSUES_FOUND,
                executive_summary="x",
                findings=[Finding(finding_id="dup", **f), Finding(finding_id="dup", **f)],
            )

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Finding(finding_id="f1", classification=FindingClassification.CONFIRMED,
                    severity=Severity.LOW, rationale="x", confidence=1.5)

    def test_invalid_json_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            ReviewResponse.model_validate({"review_id": "r1"})  # missing everything else


class TestCandidateRequirementsValidation:
    def test_negative_source_index_rejected(self):
        with pytest.raises(ValidationError, match="source_index must be >= 0"):
            CandidateRequirementsResponse(
                research_id="r1", package_id="p1", provider=ProviderID.OPENAI, model="gpt",
                program_slug="x", jurisdiction_code="XX",
                candidate_facts=[{"field_name": "refundable", "proposed_value": True,
                                  "source_index": -1, "confidence": 0.5}],
            )


class TestJSONSchemaGeneration:
    def test_review_response_schema_is_generated_from_the_model(self):
        assert REVIEW_RESPONSE_JSON_SCHEMA["title"] == "ReviewResponse"
        assert "properties" in REVIEW_RESPONSE_JSON_SCHEMA

    def test_candidate_requirements_schema_is_generated_from_the_model(self):
        assert CANDIDATE_REQUIREMENTS_JSON_SCHEMA["title"] == "CandidateRequirementsResponse"

    def test_schemas_are_distinct(self):
        assert REVIEW_RESPONSE_JSON_SCHEMA != CANDIDATE_REQUIREMENTS_JSON_SCHEMA


class TestModelRequestContentHash:
    def test_same_content_same_hash(self):
        kwargs = dict(
            provider=ProviderID.ANTHROPIC, model_id="claude", operation=OperationType.QUALIFICATION_AUDIT,
            system_instruction="audit this", structured_input={"a": 1},
            required_response_schema={"type": "object"},
        )
        r1 = ModelRequest(**kwargs)
        r2 = ModelRequest(**kwargs)
        assert r1.content_hash() == r2.content_hash()

    def test_different_content_different_hash(self):
        r1 = ModelRequest(
            provider=ProviderID.ANTHROPIC, model_id="claude", operation=OperationType.QUALIFICATION_AUDIT,
            system_instruction="audit this", structured_input={"a": 1},
            required_response_schema={"type": "object"},
        )
        r2 = ModelRequest(
            provider=ProviderID.ANTHROPIC, model_id="claude", operation=OperationType.QUALIFICATION_AUDIT,
            system_instruction="audit this", structured_input={"a": 2},  # different
            required_response_schema={"type": "object"},
        )
        assert r1.content_hash() != r2.content_hash()

    def test_metadata_does_not_affect_hash(self):
        """request_metadata is bookkeeping (e.g. a timestamp/session id),
        not part of what determines the answer — must not break
        duplicate-request detection."""
        r1 = ModelRequest(
            provider=ProviderID.ANTHROPIC, model_id="claude", operation=OperationType.QUALIFICATION_AUDIT,
            system_instruction="x", structured_input={"a": 1}, required_response_schema={},
            request_metadata={"run_id": "abc"},
        )
        r2 = ModelRequest(
            provider=ProviderID.ANTHROPIC, model_id="claude", operation=OperationType.QUALIFICATION_AUDIT,
            system_instruction="x", structured_input={"a": 1}, required_response_schema={},
            request_metadata={"run_id": "xyz"},
        )
        assert r1.content_hash() == r2.content_hash()


class TestReservedFutureOperations:
    def test_reserved_operations_are_schema_compatible_but_marked(self):
        from app.bridge.schema import RESERVED_FUTURE_OPERATIONS
        assert OperationType.SCRIPT_PRODUCTION_ANALYSIS in RESERVED_FUTURE_OPERATIONS
        assert OperationType.QUALIFICATION_AUDIT not in RESERVED_FUTURE_OPERATIONS
