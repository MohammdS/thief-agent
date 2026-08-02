"""Reject hallucinated, ungrounded, numeric, or oversized model hints."""

from __future__ import annotations

import re

from thief_agent.language.models import HintCandidate, HintRequest, OllamaOutput

COORDINATE_PATTERN = re.compile(r"\b\d+\s*[,;:]\s*\d+\b|\(\s*\d+\s*,\s*\d+\s*\)")
ALL_CUES = {"north", "south", "east", "west", "still"}


def validate_output(output: OllamaOutput, request: HintRequest) -> None:
    """Require explicit grounding to exactly the selected candidate meaning."""
    candidate = request.truth if output.choice == "truth" else request.bluff
    other = request.bluff if output.choice == "truth" else request.truth
    words = output.hint.split()
    lowered = output.hint.casefold()
    if len(words) > request.max_words:
        raise ValueError("hint exceeds negotiated word limit")
    if COORDINATE_PATTERN.search(output.hint):
        raise ValueError("hint contains a numeric coordinate protocol")
    if not has_cue(lowered, candidate):
        raise ValueError("hint is not grounded in the selected candidate")
    if has_cue(lowered, other) or extra_direction(lowered, candidate.required_cue):
        raise ValueError("hint introduces a conflicting directional claim")


def has_cue(text: str, candidate: HintCandidate) -> bool:
    """Return whether a candidate's explicit grounding cue appears as a word."""
    return re.search(rf"\b{re.escape(candidate.required_cue)}\b", text) is not None


def extra_direction(text: str, selected: str) -> bool:
    """Return whether text adds another cardinal/still cue."""
    return any(re.search(rf"\b{cue}\b", text) for cue in ALL_CUES - {selected})

