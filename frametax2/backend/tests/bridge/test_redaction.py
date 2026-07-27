from __future__ import annotations

import pytest

from app.bridge.redaction import OutboundTransmissionBlocked, assert_safe_to_send, preview_outbound_package
from app.bridge.schema import AuditPackage, ConfidentialityClassification, OperationType


def _minimal_package(**overrides) -> AuditPackage:
    kwargs = dict(
        package_id="pkg_test", production_or_scenario_id="test-prod",
        operation=OperationType.QUALIFICATION_AUDIT,
        confidentiality=ConfidentialityClassification.INTERNAL,
    )
    kwargs.update(overrides)
    return AuditPackage(**kwargs)


class TestSecretDetection:
    def test_clean_package_has_no_findings(self):
        pkg = _minimal_package()
        preview = preview_outbound_package(pkg)
        assert preview.secret_findings == ()
        assert preview.safe_to_send is True

    def test_openai_style_key_in_free_text_is_caught(self):
        pkg = _minimal_package()
        pkg.inputs.known_constraints = ["accidental leak: sk-abcdefghijklmnopqrstuvwxyz123456"]
        preview = preview_outbound_package(pkg)
        assert len(preview.secret_findings) == 1

    def test_anthropic_style_key_is_caught(self):
        pkg = _minimal_package()
        # Real Anthropic keys are "sk-ant-apiNN-<long-hyphenated-random>".
        pkg.inputs.assumptions = ["sk-ant-api03-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRST"]
        preview = preview_outbound_package(pkg)
        assert len(preview.secret_findings) == 1

    def test_secret_named_field_is_caught_regardless_of_value(self):
        pkg = _minimal_package()
        pkg.inputs.user_preferences = {"api_key": "anything-at-all"}
        preview = preview_outbound_package(pkg)
        assert len(preview.secret_findings) >= 1

    def test_finding_sample_is_redacted_not_the_raw_value(self):
        pkg = _minimal_package()
        pkg.inputs.assumptions = ["sk-abcdefghijklmnopqrstuvwxyz123456"]
        preview = preview_outbound_package(pkg)
        assert "abcdefghijklmnopqrstuvwxyz" not in preview.secret_findings[0].sample

    def test_hyphenated_slug_containing_sk_substring_is_not_a_false_positive(self):
        """Regression: conditional_program_ids like
        'COND-CH-media-desk-switzerland-succ-s-cin-ma-automatic-support'
        were previously flagged because the old regex allowed hyphens in
        the matched suffix — found against REAL served data this session."""
        pkg = _minimal_package()
        pkg.structures_considered = []
        pkg.inputs.known_constraints = [
            "COND-CH-media-desk-switzerland-succ-s-cin-ma-automatic-support",
            "some-risk-assessment-slug-with-many-hyphens-in-it",
        ]
        preview = preview_outbound_package(pkg)
        assert preview.secret_findings == ()

    def test_google_key_style_is_caught(self):
        pkg = _minimal_package()
        pkg.inputs.assumptions = ["AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"]
        preview = preview_outbound_package(pkg)
        assert len(preview.secret_findings) == 1


class TestSizeLimit:
    def test_within_limit_by_default(self):
        pkg = _minimal_package()
        preview = preview_outbound_package(pkg)
        assert preview.within_size_limit is True

    def test_over_limit_is_flagged(self, monkeypatch):
        from app.bridge.config import get_bridge_settings
        settings = get_bridge_settings()
        pkg = _minimal_package()
        object.__setattr__(settings, "BRIDGE_MAX_PACKAGE_BYTES", 10)  # absurdly small
        preview = preview_outbound_package(pkg, settings=settings)
        assert preview.within_size_limit is False
        assert preview.safe_to_send is False


class TestConfidentialityGating:
    def test_internal_package_needs_no_authorization(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.INTERNAL)
        preview = preview_outbound_package(pkg)
        assert preview.requires_authorization is False
        assert preview.safe_to_send is True

    def test_confidential_package_blocked_without_authorization(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.CONFIDENTIAL)
        preview = preview_outbound_package(pkg, authorized=False)
        assert preview.requires_authorization is True
        assert preview.safe_to_send is False

    def test_confidential_package_allowed_with_explicit_authorization(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.CONFIDENTIAL)
        preview = preview_outbound_package(pkg, authorized=True)
        assert preview.safe_to_send is True

    def test_safe_classification_never_requires_authorization(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.SAFE)
        preview = preview_outbound_package(pkg, authorized=False)
        assert preview.requires_authorization is False


class TestAssertSafeToSend:
    def test_raises_on_secret_finding(self):
        pkg = _minimal_package()
        pkg.inputs.assumptions = ["sk-abcdefghijklmnopqrstuvwxyz123456"]
        preview = preview_outbound_package(pkg)
        with pytest.raises(OutboundTransmissionBlocked, match="potential secret"):
            assert_safe_to_send(preview)

    def test_raises_on_missing_authorization(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.CONFIDENTIAL)
        preview = preview_outbound_package(pkg, authorized=False)
        with pytest.raises(OutboundTransmissionBlocked, match="requires explicit user authorization"):
            assert_safe_to_send(preview)

    def test_passes_for_clean_authorized_package(self):
        pkg = _minimal_package(confidentiality=ConfidentialityClassification.CONFIDENTIAL)
        preview = preview_outbound_package(pkg, authorized=True)
        assert_safe_to_send(preview)  # should not raise
