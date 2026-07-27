"""
OpenAI native adapter (Responses API — openai>=2.48.0), per spec 3B.
"""
from __future__ import annotations

import json

from app.bridge.adapters.base import ModelAdapter, register_adapter
from app.bridge.schema import ErrorCategory, ModelRequest, ModelResponse, ProviderID


def _build_instructions(request: ModelRequest) -> str:
    schema_json = json.dumps(request.required_response_schema, indent=2)
    return (
        f"{request.system_instruction}\n\n"
        "Respond with ONLY a single JSON object matching this JSON Schema "
        "exactly — no prose before or after, no markdown code fence:\n"
        f"{schema_json}"
    )


@register_adapter(ProviderID.OPENAI)
class OpenAIAdapter(ModelAdapter):
    provider = ProviderID.OPENAI

    def _api_key(self) -> str:
        return self.settings.OPENAI_API_KEY

    async def list_models(self) -> list[str] | None:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key())
        try:
            page = await client.models.list()
            return [m.id for m in page.data]
        finally:
            await client.close()

    async def _send(self, request: ModelRequest, api_key: str) -> ModelResponse:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, timeout=request.timeout_seconds,
                              max_retries=request.max_retries)
        try:
            response = await client.responses.create(
                model=request.model_id,
                instructions=_build_instructions(request),
                input=json.dumps(request.structured_input, default=str),
                max_output_tokens=min(request.max_output_tokens, self.settings.BRIDGE_MAX_OUTPUT_TOKENS),
            )
        finally:
            await client.close()

        text = response.output_text or ""
        parsed, parse_error = _try_parse_json(text)
        usage = {}
        if response.usage is not None:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        return ModelResponse(
            provider=self.provider, model_id=request.model_id, operation=request.operation,
            request_metadata=request.request_metadata,
            response_text=text,
            parsed_response=parsed,
            usage=usage,
            provider_request_id=getattr(response, "id", None),
            error_category=ErrorCategory.SCHEMA_VALIDATION_FAILED if parse_error else ErrorCategory.NONE,
            error_message=parse_error,
        )


def _try_parse_json(text: str) -> tuple[dict | None, str | None]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        return json.loads(stripped), None
    except json.JSONDecodeError as exc:
        return None, f"JSON parse failed: {exc}"
