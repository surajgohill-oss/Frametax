from __future__ import annotations

import pytest

from app.bridge.adapters.base import ModelAdapter, get_adapter
from app.bridge.config import BridgeSettings
from app.bridge.schema import ErrorCategory, ModelRequest, ModelResponse, ProviderID


def _request(provider: ProviderID) -> ModelRequest:
    return ModelRequest(
        provider=provider, model_id="test-model", operation="qualification_audit",
        system_instruction="test", structured_input={"x": 1},
        required_response_schema={"type": "object"},
    )


class _FakeAdapter(ModelAdapter):
    """A minimal concrete adapter for exercising the base class's
    send()/error-classification logic without any real SDK or network
    call — this is the 'mocked transport' the test suite uses."""
    provider = ProviderID.ANTHROPIC

    def __init__(self, settings=None, *, key="fake-key", raises: Exception | None = None,
                 response: ModelResponse | None = None):
        super().__init__(settings)
        self._key = key
        self._raises = raises
        self._response = response

    def _api_key(self) -> str:
        return self._key

    async def _send(self, request: ModelRequest, api_key: str) -> ModelResponse:
        if self._raises:
            raise self._raises
        return self._response


class TestAdapterContract:
    @pytest.mark.asyncio
    async def test_missing_key_returns_auth_error_never_raises(self):
        adapter = _FakeAdapter(key="")
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.AUTH
        assert response.parsed_response is None

    @pytest.mark.asyncio
    async def test_successful_response_passes_through(self):
        fake_response = ModelResponse(
            provider=ProviderID.ANTHROPIC, model_id="test-model", operation="qualification_audit",
            parsed_response={"ok": True}, response_text='{"ok": true}',
        )
        adapter = _FakeAdapter(response=fake_response)
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.ok is True
        assert response.latency_ms is not None  # send() always fills this in

    @pytest.mark.asyncio
    async def test_timeout_exception_classified_as_timeout(self):
        adapter = _FakeAdapter(raises=TimeoutError("request timed out"))
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.TIMEOUT

    @pytest.mark.asyncio
    async def test_rate_limit_exception_classified(self):
        adapter = _FakeAdapter(raises=RuntimeError("429 rate limit exceeded"))
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_auth_exception_classified(self):
        adapter = _FakeAdapter(raises=RuntimeError("401 Unauthorized: invalid api key"))
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.AUTH

    @pytest.mark.asyncio
    async def test_unknown_exception_classified_as_provider_error_never_crashes_caller(self):
        adapter = _FakeAdapter(raises=ValueError("some unexpected provider-side thing"))
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.PROVIDER_ERROR
        assert "unexpected provider-side thing" in response.error_message

    @pytest.mark.asyncio
    async def test_network_exception_classified(self):
        class ConnectionFailure(Exception):
            pass
        adapter = _FakeAdapter(raises=ConnectionFailure("connection refused"))
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.NETWORK

    def test_no_silent_fallback_field_defaults_false(self):
        fake_response = ModelResponse(
            provider=ProviderID.ANTHROPIC, model_id="test-model", operation="qualification_audit",
        )
        assert fake_response.fallback_used is False


class TestRealAdaptersRegisterAndReportUnconfigured:
    """Not a live network test — verifies the three REAL adapter classes
    (not the fake one above) construct cleanly and correctly report
    their configured key state, using settings with no keys set."""

    def test_all_three_providers_resolve_to_distinct_adapter_classes(self):
        settings = BridgeSettings(_env_file=None)
        classes = {get_adapter(p, settings).__class__.__name__ for p in ProviderID}
        assert len(classes) == 3

    def test_all_three_report_no_key_when_none_configured(self):
        settings = BridgeSettings(_env_file=None)
        for p in ProviderID:
            adapter = get_adapter(p, settings)
            assert adapter._api_key() == ""

    @pytest.mark.asyncio
    async def test_real_anthropic_adapter_returns_auth_error_with_no_key(self):
        settings = BridgeSettings(_env_file=None)
        adapter = get_adapter(ProviderID.ANTHROPIC, settings)
        response = await adapter.send(_request(ProviderID.ANTHROPIC))
        assert response.error_category == ErrorCategory.AUTH

    @pytest.mark.asyncio
    async def test_real_openai_adapter_returns_auth_error_with_no_key(self):
        settings = BridgeSettings(_env_file=None)
        adapter = get_adapter(ProviderID.OPENAI, settings)
        response = await adapter.send(_request(ProviderID.OPENAI))
        assert response.error_category == ErrorCategory.AUTH

    @pytest.mark.asyncio
    async def test_real_gemini_adapter_returns_auth_error_with_no_key(self):
        settings = BridgeSettings(_env_file=None)
        adapter = get_adapter(ProviderID.GEMINI, settings)
        response = await adapter.send(_request(ProviderID.GEMINI))
        assert response.error_category == ErrorCategory.AUTH
