"""
Bridge provider configuration. Extends app.core.config's Settings via
composition (a second BaseSettings, same env-file convention), rather
than editing the existing Settings class — the existing ANTHROPIC_API_KEY
field there is an inert placeholder from a dormant, unrelated DB-backed
path (see that field's own comment: "LLM-assisted extraction only — not
for final math") and is left untouched. This module is the ONE place
bridge provider config is read.
"""
from __future__ import annotations

import enum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderID(str, enum.Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class ProviderStatus(str, enum.Enum):
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"  # key present but SDK/import/network proved it unusable


class BridgeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Provider keys — read once, never logged, never returned by any
    # API route, never included in any audit package or persisted record.
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""  # Gemini-compatible alias, per spec section 2

    # ── Per-provider enable/disable, independent of whether a key exists —
    # lets an operator disable a configured provider without removing its key.
    BRIDGE_ANTHROPIC_ENABLED: bool = True
    BRIDGE_OPENAI_ENABLED: bool = True
    BRIDGE_GEMINI_ENABLED: bool = True

    # ── Model aliases — never hardcode a model name at a call site; every
    # call site resolves one of these. Changing a model is a one-line edit
    # here, not a grep-and-replace across the codebase.
    BRIDGE_MODEL_CLAUDE_PRIMARY_REVIEW: str = "claude-opus-4-1"
    BRIDGE_MODEL_CLAUDE_FAST_RESEARCH: str = "claude-sonnet-4-5"
    BRIDGE_MODEL_OPENAI_PRIMARY_REVIEW: str = "gpt-5.1"
    BRIDGE_MODEL_OPENAI_FAST_RESEARCH: str = "gpt-5.1-mini"
    BRIDGE_MODEL_GEMINI_PRIMARY_REVIEW: str = "gemini-3-pro"
    BRIDGE_MODEL_GEMINI_FAST_RESEARCH: str = "gemini-2.5-flash"

    # ── Cost / rate controls (section 13) ──
    BRIDGE_REQUEST_TIMEOUT_SECONDS: float = 90.0
    BRIDGE_MAX_RETRIES: int = 3
    BRIDGE_RETRY_BACKOFF_SECONDS: float = 2.0
    BRIDGE_MAX_CONCURRENCY: int = 3
    BRIDGE_MAX_OUTPUT_TOKENS: int = 8192

    # ── Persistence (own dedicated SQLite file — see persistence.py's
    # module docstring for why this is separate from the app's dormant
    # Postgres schema) ──
    BRIDGE_DB_PATH: str = "./.bridge_data/bridge.db"

    # ── Outbound-data policy ──
    BRIDGE_MAX_PACKAGE_BYTES: int = 2_000_000  # 2 MB — a budget/qualification package, not a repo dump
    BRIDGE_REQUIRE_CONFIDENTIAL_AUTHORIZATION: bool = True

    @model_validator(mode="after")
    def _apply_google_alias(self) -> "BridgeSettings":
        # GOOGLE_API_KEY is accepted as a Gemini-compatible alias (section 2)
        # — only fills in if GEMINI_API_KEY itself was not set.
        if not self.GEMINI_API_KEY and self.GOOGLE_API_KEY:
            object.__setattr__(self, "GEMINI_API_KEY", self.GOOGLE_API_KEY)
        return self

    # Provider enum value -> the prefix used in BRIDGE_MODEL_* field names.
    # Anthropic's fields are named CLAUDE_*, not ANTHROPIC_*, for readability
    # (BRIDGE_MODEL_CLAUDE_PRIMARY_REVIEW) — this map is the one place that
    # naming choice is bridged back to the ProviderID enum.
    _ALIAS_PREFIX = {"anthropic": "claude", "openai": "openai", "gemini": "gemini"}

    def resolve_provider_alias(self, provider_value: str, alias_suffix: str) -> str:
        """provider_value: 'anthropic'|'openai'|'gemini'. alias_suffix:
        'primary_review'|'fast_research'. Returns the resolved model ID."""
        prefix = self._ALIAS_PREFIX[provider_value]
        return self.model_alias(f"{prefix}_{alias_suffix}")

    def model_alias(self, alias: str) -> str:
        """Resolve a model alias string (e.g. 'claude_primary_review') to
        its configured model ID. Raises if the alias is unknown — never
        silently falls back to a different model."""
        field_name = f"BRIDGE_MODEL_{alias.upper()}"
        if not hasattr(self, field_name):
            known = sorted(
                f.removeprefix("BRIDGE_MODEL_").lower()
                for f in type(self).model_fields
                if f.startswith("BRIDGE_MODEL_")
            )
            raise ValueError(f"Unknown model alias '{alias}'. Known aliases: {known}")
        return getattr(self, field_name)


_settings: BridgeSettings | None = None


def get_bridge_settings() -> BridgeSettings:
    global _settings
    if _settings is None:
        _settings = BridgeSettings()
    return _settings


def reset_bridge_settings_cache() -> None:
    """Test-only: force re-read of environment on next get_bridge_settings()."""
    global _settings
    _settings = None
