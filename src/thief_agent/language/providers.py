"""Language provider protocol and deterministic template implementation."""

from __future__ import annotations

from typing import Protocol

from thief_agent.language.models import HintRequest, HintResult
from thief_agent.protocol.actions import HintIntent


class HintProvider(Protocol):
    """Generate bounded language without controlling movement."""

    async def generate(self, request: HintRequest) -> HintResult:
        """Return one validated hint result."""
        ...


class TemplateHintProvider:
    """Return deterministic pre-approved language without external calls."""

    async def generate(self, request: HintRequest) -> HintResult:
        """Select the preferred intent and enforce the word limit."""
        candidate = request.truth if request.preferred_intent is HintIntent.TRUTH else request.bluff
        words = candidate.text.split()[: request.max_words]
        return HintResult(
            hint=" ".join(words),
            intent=candidate.intent,
            provider="template",
            prompt_tokens=0,
            completion_tokens=0,
        )

