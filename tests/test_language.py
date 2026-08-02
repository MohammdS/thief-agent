import json

import httpx
import pytest

from thief_agent.domain.types import Move
from thief_agent.language.candidates import build_hint_request
from thief_agent.language.models import OllamaOutput
from thief_agent.language.ollama import OllamaHintProvider
from thief_agent.language.policy import HintPolicy
from thief_agent.language.providers import TemplateHintProvider
from thief_agent.language.validation import validate_output
from thief_agent.protocol.actions import HintIntent


@pytest.mark.asyncio
async def test_template_provider_obeys_intent_and_word_limit() -> None:
    request = build_hint_request(Move.NORTH, HintIntent.BLUFF, max_words=4)
    result = await TemplateHintProvider().generate(request)
    assert result.intent is HintIntent.BLUFF
    assert len(result.hint.split()) <= 4
    assert result.provider == "template"


@pytest.mark.parametrize(
    ("hint", "error"),
    [
        ("I moved north toward 2,3", "numeric coordinate"),
        ("I moved north then south", "conflicting"),
        ("I wandered quietly", "not grounded"),
        ("north one two three four five six seven eight", "word limit"),
    ],
)
def test_grounding_validator_rejects_hallucinated_hints(hint: str, error: str) -> None:
    request = build_hint_request(Move.NORTH, HintIntent.TRUTH, max_words=5)
    with pytest.raises(ValueError, match=error):
        validate_output(OllamaOutput(choice="truth", hint=hint), request)


@pytest.mark.asyncio
async def test_ollama_provider_accepts_grounded_strict_json_and_counts_tokens() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["options"]["temperature"] == 0
        content = json.dumps({"choice": "truth", "hint": "I moved north through open ground"})
        return httpx.Response(200, json={
            "model": "qwen3:8b",
            "message": {"role": "assistant", "content": content},
            "prompt_eval_count": 42,
            "eval_count": 9,
        })

    provider = OllamaHintProvider(transport=httpx.MockTransport(handler))
    result = await provider.generate(build_hint_request(Move.NORTH, HintIntent.TRUTH))
    assert result.provider == "ollama"
    assert (result.prompt_tokens, result.completion_tokens) == (42, 9)


@pytest.mark.asyncio
async def test_invalid_ollama_response_falls_back_deterministically() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        content = json.dumps({"choice": "truth", "hint": "I am at 2,3 north"})
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": content},
        })

    provider = OllamaHintProvider(transport=httpx.MockTransport(handler))
    result = await provider.generate(build_hint_request(Move.NORTH, HintIntent.TRUTH))
    assert result.provider == "template"
    assert result.fallback_reason == "ValueError"


@pytest.mark.asyncio
async def test_hint_policy_uses_template_between_provider_steps() -> None:
    provider = OllamaHintProvider(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    policy = HintPolicy(provider, every_n_steps=2)
    result = await policy.generate(1, build_hint_request(Move.EAST, HintIntent.TRUTH))
    assert result.provider == "template"
    with pytest.raises(ValueError, match="cadence"):
        HintPolicy(provider, every_n_steps=0)

