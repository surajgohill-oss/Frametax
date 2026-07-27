"""
Gemini native adapter — google-genai>=2.14.0's models.generate_content,
the current officially recommended endpoint for this SDK generation (no
separately-named "Interactions API" exists in the installed official SDK
as of this SDK version; per spec section 3C's own fallback clause, this
is the correct choice rather than guessing at an unshipped endpoint
name). Uses native response_json_schema + response_mime_type=
"application/json" (Gemini's SDK supports this directly, unlike the
prompt-only enforcement the Anthropic/OpenAI adapters use) — still
parsed and validated the same way as the other two, never trusted blind.
"""
from __future__ import annotations

import json

from app.bridge.adapters.base import ModelAdapter, register_adapter
from app.bridge.schema import ErrorCategory, ModelRequest, ModelResponse, ProviderID


@register_adapter(ProviderID.GEMINI)
class GeminiAdapter(ModelAdapter):
    provider = ProviderID.GEMINI

    def _api_key(self) -> str:
        return self.settings.GEMINI_API_KEY

    async def list_models(self) -> list[str] | None:
        from google import genai

        client = genai.Client(api_key=self._api_key())
        models = []
        async for m in await client.aio.models.list():
            models.append(m.name)
        return models

    async def _send(self, request: ModelRequest, api_key: str) -> ModelResponse:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=request.system_instruction,
            max_output_tokens=min(request.max_output_tokens, self.settings.BRIDGE_MAX_OUTPUT_TOKENS),
            response_mime_type="application/json",
            response_json_schema=request.required_response_schema,
        )
        response = await client.aio.models.generate_content(
            model=request.model_id,
            contents=json.dumps(request.structured_input, default=str),
            config=config,
        )

        text = response.text or ""
        parsed, parse_error = _try_parse_json(text)
        usage = {}
        if response.usage_metadata is not None:
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }
        return ModelResponse(
            provider=self.provider, model_id=request.model_id, operation=request.operation,
            request_metadata=request.request_metadata,
            response_text=text,
            parsed_response=parsed,
            usage=usage,
            provider_request_id=getattr(response, "response_id", None),
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
