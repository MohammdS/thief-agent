"""Schedule optional LLM hints while preserving deterministic fallback."""

from __future__ import annotations

from thief_agent.language.models import HintRequest, HintResult
from thief_agent.language.providers import HintProvider, TemplateHintProvider


class HintPolicy:
    """Use the configured provider only on explicitly scheduled steps."""

    def __init__(self, provider: HintProvider, every_n_steps: int = 1) -> None:
        """Configure a positive LLM cadence and template fallback steps."""
        if every_n_steps < 1:
            raise ValueError("hint cadence must be positive")
        self._provider = provider
        self._every_n_steps = every_n_steps
        self._template = TemplateHintProvider()

    async def generate(self, step: int, request: HintRequest) -> HintResult:
        """Generate externally only at the configured cadence."""
        if step % self._every_n_steps:
            return await self._template.generate(request)
        return await self._provider.generate(request)

