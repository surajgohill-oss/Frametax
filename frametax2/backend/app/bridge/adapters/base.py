"""
ModelAdapter — the one interface every provider client implements.
Nothing outside adapters/ ever imports a provider SDK directly.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.bridge.config import BridgeSettings, get_bridge_settings
from app.bridge.schema import ErrorCategory, ModelRequest, ModelResponse, ProviderID


class ModelAdapter(ABC):
    provider: ProviderID

    def __init__(self, settings: BridgeSettings | None = None):
        self.settings = settings or get_bridge_settings()

    @abstractmethod
    def _api_key(self) -> str: ...

    @abstractmethod
    async def _send(self, request: ModelRequest, api_key: str) -> ModelResponse:
        """Provider-specific call. Must NOT catch/swallow exceptions for
        conditions this class's send() already classifies (timeout,
        auth, rate limit) — raise them so send() can categorize
        consistently across all three adapters."""
        ...

    async def list_models(self) -> list[str] | None:
        """Optional: providers that support model listing should override
        this for the startup/admin availability check (section 3). None
        means "this provider/SDK doesn't support listing" — not an error."""
        return None

    async def send(self, request: ModelRequest) -> ModelResponse:
        api_key = self._api_key()
        if not api_key:
            return ModelResponse(
                provider=self.provider, model_id=request.model_id, operation=request.operation,
                error_category=ErrorCategory.AUTH,
                error_message=f"{self.provider.value} API key is not configured.",
            )
        start = time.monotonic()
        try:
            response = await self._send(request, api_key)
        except TimeoutError as exc:
            return self._error_response(request, ErrorCategory.TIMEOUT, str(exc), start)
        except Exception as exc:  # noqa: BLE001 — deliberately broad: this is the
            # single classification point for every provider's own exception
            # hierarchy, never re-raised past here.
            category = self._classify_exception(exc)
            return self._error_response(request, category, str(exc), start)
        response.latency_ms = (time.monotonic() - start) * 1000
        return response

    def _error_response(
        self, request: ModelRequest, category: ErrorCategory, message: str, start: float,
    ) -> ModelResponse:
        return ModelResponse(
            provider=self.provider, model_id=request.model_id, operation=request.operation,
            error_category=category, error_message=message,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    @staticmethod
    def _classify_exception(exc: Exception) -> ErrorCategory:
        name = type(exc).__name__.lower()
        text = str(exc).lower()
        if "timeout" in name or "timeout" in text:
            return ErrorCategory.TIMEOUT
        if "rate" in text and "limit" in text:
            return ErrorCategory.RATE_LIMIT
        if "auth" in name or "unauthorized" in text or "api key" in text or "401" in text:
            return ErrorCategory.AUTH
        if "invalid" in text or "400" in text:
            return ErrorCategory.INVALID_REQUEST
        if "connection" in name or "network" in text:
            return ErrorCategory.NETWORK
        return ErrorCategory.PROVIDER_ERROR


_ADAPTER_CLASSES: dict[ProviderID, type[ModelAdapter]] = {}


def register_adapter(provider: ProviderID):
    def _wrap(cls: type[ModelAdapter]) -> type[ModelAdapter]:
        _ADAPTER_CLASSES[provider] = cls
        return cls
    return _wrap


def get_adapter(provider: ProviderID, settings: BridgeSettings | None = None) -> ModelAdapter:
    if provider not in _ADAPTER_CLASSES:
        # Import lazily so a missing optional SDK for one provider never
        # breaks importing the bridge package as a whole.
        if provider == ProviderID.ANTHROPIC:
            import app.bridge.adapters.anthropic_adapter  # noqa: F401
        elif provider == ProviderID.OPENAI:
            import app.bridge.adapters.openai_adapter  # noqa: F401
        elif provider == ProviderID.GEMINI:
            import app.bridge.adapters.gemini_adapter  # noqa: F401
    return _ADAPTER_CLASSES[provider](settings)
