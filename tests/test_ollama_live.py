import os

import pytest

from thief_agent.domain.types import Move
from thief_agent.language.candidates import build_hint_request
from thief_agent.language.ollama import OllamaHintProvider
from thief_agent.protocol.actions import HintIntent


@pytest.mark.ollama
@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv("RUN_OLLAMA_TESTS") != "1", reason="live Ollama test is opt-in")
async def test_live_qwen_hint_is_grounded_and_token_counted() -> None:
    provider = OllamaHintProvider(model=os.getenv("OLLAMA_MODEL", "qwen3:8b"), timeout_seconds=60)
    request = build_hint_request(Move.WEST, HintIntent.BLUFF)
    result = await provider.generate(request)
    assert result.provider == "ollama"
    assert len(result.hint.split()) <= request.max_words
    assert result.prompt_tokens + result.completion_tokens > 0
