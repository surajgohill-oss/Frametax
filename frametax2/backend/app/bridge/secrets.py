"""
Provider status resolution and key-redaction helpers.

The one rule this whole module exists to enforce: a provider API key is
readable exactly once, at the point an SDK client is constructed, and
never again — never logged, never returned by an API response, never
included in a persisted record, never included in an audit package.
"""
from __future__ import annotations

from app.bridge.config import BridgeSettings, ProviderID, ProviderStatus, get_bridge_settings

_KEY_FIELD = {
    ProviderID.ANTHROPIC: "ANTHROPIC_API_KEY",
    ProviderID.OPENAI: "OPENAI_API_KEY",
    ProviderID.GEMINI: "GEMINI_API_KEY",
}

_ENABLED_FIELD = {
    ProviderID.ANTHROPIC: "BRIDGE_ANTHROPIC_ENABLED",
    ProviderID.OPENAI: "BRIDGE_OPENAI_ENABLED",
    ProviderID.GEMINI: "BRIDGE_GEMINI_ENABLED",
}


def provider_status(provider: ProviderID, settings: BridgeSettings | None = None) -> ProviderStatus:
    """CONFIGURED / NOT_CONFIGURED / DISABLED — never UNAVAILABLE here
    (that status is set by an adapter after a real construction/probe
    failure, e.g. an SDK import error or a failed model-list call)."""
    settings = settings or get_bridge_settings()
    if not getattr(settings, _ENABLED_FIELD[provider]):
        return ProviderStatus.DISABLED
    key = getattr(settings, _KEY_FIELD[provider])
    if not key or not key.strip():
        return ProviderStatus.NOT_CONFIGURED
    return ProviderStatus.CONFIGURED


def all_provider_statuses(settings: BridgeSettings | None = None) -> dict[str, str]:
    settings = settings or get_bridge_settings()
    return {p.value: provider_status(p, settings).value for p in ProviderID}


def has_key(provider: ProviderID, settings: BridgeSettings | None = None) -> bool:
    """True/False only — never returns or exposes the key value itself."""
    settings = settings or get_bridge_settings()
    key = getattr(settings, _KEY_FIELD[provider])
    return bool(key and key.strip())


def redact(text: str | None) -> str | None:
    """Best-effort redaction for anything that might reach a log line —
    never a substitute for simply not logging the key in the first
    place (which is the actual rule everywhere else in this module)."""
    if not text:
        return text
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}...{text[-2:]}"
