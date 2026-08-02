"""Strict models shared by language providers and validators."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from thief_agent.config.models import StrictModel
from thief_agent.protocol.actions import HintIntent


class HintCandidate(StrictModel):
    """Describe one pre-approved semantic hint candidate."""

    intent: HintIntent
    text: str = Field(min_length=1)
    required_cue: str = Field(min_length=1)


class HintRequest(StrictModel):
    """Provide only grounded candidates and non-geometric tactical context."""

    truth: HintCandidate
    bluff: HintCandidate
    preferred_intent: HintIntent
    max_words: int = Field(ge=1)
    tactic: str = Field(min_length=1, max_length=200)


class HintResult(StrictModel):
    """Return validated natural language and transparent token accounting."""

    hint: str
    intent: HintIntent
    provider: Literal["template", "ollama"]
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    fallback_reason: str | None = None


class OllamaOutput(StrictModel):
    """Constrain the language model to one grounded candidate family."""

    choice: Literal["truth", "bluff"]
    hint: str = Field(min_length=1)


class OllamaMessage(StrictModel):
    """Extract only the assistant content from an Ollama response."""

    model_config = ConfigDict(extra="ignore", frozen=True)
    role: str
    content: str


class OllamaResponse(StrictModel):
    """Validate Ollama content and token usage fields."""

    model_config = ConfigDict(extra="ignore", frozen=True)
    message: OllamaMessage
    prompt_eval_count: int = Field(default=0, ge=0)
    eval_count: int = Field(default=0, ge=0)
