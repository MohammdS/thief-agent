"""Optional grounded Ollama provider with deterministic safe fallback."""

from __future__ import annotations

import json

import httpx

from thief_agent.language.models import HintRequest, HintResult, OllamaOutput, OllamaResponse
from thief_agent.language.providers import TemplateHintProvider
from thief_agent.language.validation import validate_output
from thief_agent.protocol.actions import HintIntent

SYSTEM_PROMPT = (
    "You are the Thief's deception specialist in a competitive game. Maximize escape odds "
    "within all rules. You never choose movement. Return strict JSON only. Select truth or "
    "bluff, then write a natural-language hint grounded in that candidate. Preserve its exact "
    "direction cue, add no other direction, never emit coordinates, and obey the word limit."
)


class OllamaHintProvider:
    """Call Ollama for language only and fall back on every invalid outcome."""

    def __init__(
        self,
        model: str = "qwen3:8b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 10,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure local Ollama access without an API secret."""
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport
        self._fallback = TemplateHintProvider()

    async def generate(self, request: HintRequest) -> HintResult:
        """Return a validated Ollama hint or an explicit template fallback."""
        try:
            payload = await self._call(request)
            output = OllamaOutput.model_validate_json(payload.message.content)
            validate_output(output, request)
            intent = HintIntent(output.choice)
            return HintResult(
                hint=output.hint,
                intent=intent,
                provider="ollama",
                prompt_tokens=payload.prompt_eval_count,
                completion_tokens=payload.eval_count,
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            fallback = await self._fallback.generate(request)
            return fallback.model_copy(update={"fallback_reason": type(error).__name__})

    async def _call(self, request: HintRequest) -> OllamaResponse:
        """Call Ollama's chat endpoint with a strict JSON response schema."""
        user_prompt = json.dumps(request.model_dump(mode="json"), sort_keys=True)
        body = {
            "model": self._model,
            "stream": False,
            "format": OllamaOutput.model_json_schema(),
            "options": {"temperature": 0, "seed": 42},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await client.post("/api/chat", json=body)
            response.raise_for_status()
            return OllamaResponse.model_validate(response.json())
