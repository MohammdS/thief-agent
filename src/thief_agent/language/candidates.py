"""Build coordinate-free truth and bluff candidates from an algorithmic move."""

from __future__ import annotations

from thief_agent.domain.types import Move
from thief_agent.language.models import HintCandidate, HintRequest
from thief_agent.protocol.actions import HintIntent

DIRECTIONS = {
    Move.NORTH: ("north", "I slipped north toward the open edge"),
    Move.SOUTH: ("south", "I drifted south toward the open edge"),
    Move.EAST: ("east", "I headed east toward the open edge"),
    Move.WEST: ("west", "I moved west toward the open edge"),
    Move.STAY: ("still", "I stayed still and watched"),
}
OPPOSITE = {
    Move.NORTH: Move.SOUTH,
    Move.SOUTH: Move.NORTH,
    Move.EAST: Move.WEST,
    Move.WEST: Move.EAST,
    Move.STAY: Move.EAST,
}


def build_hint_request(
    move: Move,
    preferred_intent: HintIntent,
    max_words: int = 15,
    tactic: str = "maximize uncertainty and improve escape odds within the rules",
) -> HintRequest:
    """Create two safe candidate meanings without coordinates or hidden state."""
    truth_cue, truth_text = DIRECTIONS[move]
    bluff_cue, bluff_text = DIRECTIONS[OPPOSITE[move]]
    return HintRequest(
        truth=HintCandidate(intent=HintIntent.TRUTH, text=truth_text, required_cue=truth_cue),
        bluff=HintCandidate(intent=HintIntent.BLUFF, text=bluff_text, required_cue=bluff_cue),
        preferred_intent=preferred_intent,
        max_words=max_words,
        tactic=tactic,
    )
