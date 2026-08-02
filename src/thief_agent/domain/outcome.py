"""Terminal detection and fixed score calculation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from thief_agent.config.models import SharedConfig
from thief_agent.domain.board import is_captured, is_imprisoned
from thief_agent.domain.state import BoardState


class TerminalReason(StrEnum):
    """Enumerate every scored terminal category."""

    CAPTURE = "capture"
    IMPRISONMENT = "imprisonment"
    SURVIVAL = "survival"
    TIE = "tie"
    TECHNICAL_LOSS = "technical_loss"


@dataclass(frozen=True, slots=True)
class Outcome:
    """Store a terminal reason and both fixed scores."""

    reason: TerminalReason
    police_score: int
    thief_score: int


def score_outcome(reason: TerminalReason, config: SharedConfig) -> Outcome:
    """Map a terminal reason to its Appendix F score pair."""
    if reason in {TerminalReason.CAPTURE, TerminalReason.IMPRISONMENT}:
        pair = config.scoring.capture
    elif reason is TerminalReason.SURVIVAL:
        pair = config.scoring.survival
    elif reason is TerminalReason.TIE:
        pair = config.scoring.tie
    else:
        pair = config.scoring.technical_loss
    return Outcome(reason, pair.police, pair.thief)


def evaluate_outcome(state: BoardState, config: SharedConfig) -> Outcome | None:
    """Return the current physical outcome or None while play continues."""
    if is_captured(state):
        return score_outcome(TerminalReason.CAPTURE, config)
    if is_imprisoned(state):
        return score_outcome(TerminalReason.IMPRISONMENT, config)
    if state.step >= config.turns.survival_threshold:
        return score_outcome(TerminalReason.SURVIVAL, config)
    return None

