"""Explicit match and turn transition tables."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MatchState(StrEnum):
    """Enumerate match-level lifecycle states."""

    BOOTSTRAP = "bootstrap"
    NEGOTIATING = "negotiating"
    STEP_ZERO = "step_zero"
    RUNNING_SUBGAME = "running_subgame"
    FINAL_AUDIT = "final_audit"
    AGREEING_RESULT = "agreeing_result"
    REPORTING = "reporting"
    FINISHED = "finished"
    ABORTED = "aborted"


class TurnState(StrEnum):
    """Enumerate commit-reveal turn states."""

    WAITING_FOR_OPPONENT = "waiting_for_opponent"
    COMPUTING_MOVE = "computing_move"
    COMMITTING = "committing"
    AWAITING_REVEAL = "awaiting_reveal"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    TECHNICAL_LOSS = "technical_loss"


MATCH_TRANSITIONS = {
    MatchState.BOOTSTRAP: {MatchState.NEGOTIATING, MatchState.ABORTED},
    MatchState.NEGOTIATING: {MatchState.STEP_ZERO, MatchState.ABORTED},
    MatchState.STEP_ZERO: {MatchState.RUNNING_SUBGAME, MatchState.ABORTED},
    MatchState.RUNNING_SUBGAME: {MatchState.FINAL_AUDIT, MatchState.ABORTED},
    MatchState.FINAL_AUDIT: {MatchState.AGREEING_RESULT, MatchState.ABORTED},
    MatchState.AGREEING_RESULT: {MatchState.REPORTING, MatchState.ABORTED},
    MatchState.REPORTING: {MatchState.FINISHED, MatchState.ABORTED},
}
TURN_TRANSITIONS = {
    TurnState.WAITING_FOR_OPPONENT: {TurnState.COMPUTING_MOVE, TurnState.TECHNICAL_LOSS},
    TurnState.COMPUTING_MOVE: {TurnState.COMMITTING, TurnState.TECHNICAL_LOSS},
    TurnState.COMMITTING: {TurnState.AWAITING_REVEAL, TurnState.TECHNICAL_LOSS},
    TurnState.AWAITING_REVEAL: {TurnState.VERIFYING, TurnState.TECHNICAL_LOSS},
    TurnState.VERIFYING: {TurnState.COMPLETE, TurnState.TECHNICAL_LOSS},
}
@dataclass(slots=True)
class StateMachine[StateT: (MatchState, TurnState)]:
    """Reject any transition absent from an explicit table."""

    state: StateT
    transitions: dict[StateT, set[StateT]]

    def transition(self, target: StateT) -> None:
        """Move to a legal target or raise a visible protocol error."""
        if target not in self.transitions.get(self.state, set()):
            raise ValueError(f"illegal transition: {self.state.value} -> {target.value}")
        self.state = target


def match_machine() -> StateMachine[MatchState]:
    """Create a match state machine at bootstrap."""
    return StateMachine(MatchState.BOOTSTRAP, MATCH_TRANSITIONS)


def turn_machine() -> StateMachine[TurnState]:
    """Create a turn state machine waiting for the opponent."""
    return StateMachine(TurnState.WAITING_FOR_OPPONENT, TURN_TRANSITIONS)
