"""
Anthropic native adapter (Messages API — anthropic>=0.120.0).

JSON-schema compliance is prompt-enforced (the schema is embedded in the
system instruction and the model is told to return ONLY that JSON) rather
than relying on a provider-specific structured-output feature — this
keeps the three adapters' contract identical and is why schema.py's
review_response parsing + one-shot repair path (see reconciliation
call sites) exists at all.
"""
from __future__ import annotations

import json

from app.bridge.adapters.base import ModelAdapter, register_adapter
from app.bridge.schema import ErrorCategory, ModelRequest, ModelResponse, ProviderID


def _build_system(request: ModelRequest) -> str:
    schema_json = json.dumps(request.required_response_schema, indent=2)
    return (
        f"{request.system_instruction}\n\n"
        "Respond with ONLY a single JSON object matching this JSON Schema "
        "exactly — no prose before or after, no markdown code fence:\n"
        f"{schema_json}"
    )


@register_adapter(ProviderID.ANTHROPIC)
class AnthropicAdapter(ModelAdapter):
    provider = ProviderID.ANTHROPIC

    def _api_key(self) -> str:
        return self.settings.ANTHROPIC_API_KEY

    async def list_models(self) -> list[str] | None:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._api_key())
        try:
            page = await client.models.list(limit=50)
            return [m.id for m in page.data]
        finally:
            await client.close()

    async def _send(self, request: ModelRequest, api_key: str) -> ModelResponse:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key, timeout=request.timeout_seconds,
                                 max_retries=request.max_retries)
        try:
            message = await client.messages.create(
                model=request.model_id,
                max_tokens=min(request.max_output_tokens, self.settings.BRIDGE_MAX_OUTPUT_TOKENS),
                system=_build_system(request),
                messages=[{
                    "role": "user",
                    "content": json.dumps(request.structured_input, default=str),
                }],
            )
        finally:
            await client.close()

        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        parsed, parse_error = _try_parse_json(text)
        usage = {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        }
        return ModelResponse(
            provider=self.provider, model_id=request.model_id, operation=request.operation,
            request_metadata=request.request_metadata,
            response_text=text,
            parsed_response=parsed,
            usage=usage,
            provider_request_id=getattr(message, "id", None),
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
