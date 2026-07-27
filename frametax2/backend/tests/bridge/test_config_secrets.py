from __future__ import annotations

import pytest

from app.bridge.config import BridgeSettings, ProviderID, ProviderStatus
from app.bridge.secrets import all_provider_statuses, has_key, provider_status, redact


class TestModelAliasResolution:
    def test_known_alias_resolves(self):
        settings = BridgeSettings()
        assert settings.model_alias("claude_primary_review") == settings.BRIDGE_MODEL_CLAUDE_PRIMARY_REVIEW

    def test_unknown_alias_raises_never_falls_back(self):
        settings = BridgeSettings()
        with pytest.raises(ValueError, match="Unknown model alias"):
            settings.model_alias("not_a_real_alias")

    def test_resolve_provider_alias_for_all_three_providers(self):
        settings = BridgeSettings()
        assert settings.resolve_provider_alias("anthropic", "fast_research") == settings.BRIDGE_MODEL_CLAUDE_FAST_RESEARCH
        assert settings.resolve_provider_alias("openai", "fast_research") == settings.BRIDGE_MODEL_OPENAI_FAST_RESEARCH
        assert settings.resolve_provider_alias("gemini", "fast_research") == settings.BRIDGE_MODEL_GEMINI_FAST_RESEARCH


class TestMissingKeyBehavior:
    def test_no_env_vars_set_reports_not_configured(self, monkeypatch):
        for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        settings = BridgeSettings(_env_file=None)
        assert provider_status(ProviderID.ANTHROPIC, settings) == ProviderStatus.NOT_CONFIGURED
        assert provider_status(ProviderID.OPENAI, settings) == ProviderStatus.NOT_CONFIGURED
        assert provider_status(ProviderID.GEMINI, settings) == ProviderStatus.NOT_CONFIGURED
        assert has_key(ProviderID.ANTHROPIC, settings) is False

    def test_configured_when_key_present(self):
        settings = BridgeSettings(_env_file=None, ANTHROPIC_API_KEY="sk-ant-fake-for-test-only")
        assert provider_status(ProviderID.ANTHROPIC, settings) == ProviderStatus.CONFIGURED
        assert has_key(ProviderID.ANTHROPIC, settings) is True

    def test_disabled_wins_over_configured(self):
        settings = BridgeSettings(
            _env_file=None, ANTHROPIC_API_KEY="sk-ant-fake", BRIDGE_ANTHROPIC_ENABLED=False,
        )
        assert provider_status(ProviderID.ANTHROPIC, settings) == ProviderStatus.DISABLED

    def test_google_api_key_is_gemini_alias_only_when_gemini_key_empty(self):
        settings = BridgeSettings(_env_file=None, GOOGLE_API_KEY="fake-google-key")
        assert settings.GEMINI_API_KEY == "fake-google-key"

        settings2 = BridgeSettings(_env_file=None, GEMINI_API_KEY="real-gemini-key", GOOGLE_API_KEY="fake-google-key")
        assert settings2.GEMINI_API_KEY == "real-gemini-key"  # explicit GEMINI_API_KEY wins

    def test_all_provider_statuses_never_includes_key_values(self):
        settings = BridgeSettings(_env_file=None, ANTHROPIC_API_KEY="sk-ant-super-secret-value")
        statuses = all_provider_statuses(settings)
        assert "sk-ant-super-secret-value" not in str(statuses)
        assert statuses["anthropic"] == "configured"


class TestKeyRedaction:
    def test_redact_short_string(self):
        assert redact("abc") == "***"

    def test_redact_long_string_shows_partial(self):
        result = redact("sk-ant-abcdefghijklmnopqrstuvwxyz")
        assert result.startswith("sk-a")
        assert "abcdefghijklmnopqrstuvwxyz" not in result

    def test_redact_none(self):
        assert redact(None) is None
        assert redact("") == ""
