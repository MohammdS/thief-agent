"""Idempotent per-turn commitment and reveal ledger."""

from __future__ import annotations

from dataclasses import dataclass, field

from thief_agent.crypto.audit import RevealedTurn
from thief_agent.protocol.messages import CommitTurnRequest, RevealTurnRequest

TurnKey = tuple[int, int, str]


def turn_key(request: CommitTurnRequest | RevealTurnRequest) -> TurnKey:
    """Return the unique sender turn identity."""
    envelope = request.envelope
    return envelope.subgame, envelope.step, envelope.sender.value


@dataclass(slots=True)
class TurnLedger:
    """Reject conflicting duplicate commitments or reveals."""

    commitments: dict[TurnKey, str] = field(default_factory=dict)
    reveals: dict[TurnKey, RevealedTurn] = field(default_factory=dict)

    def record_commit(self, request: CommitTurnRequest) -> bool:
        """Store a commitment and return False for an identical duplicate."""
        key = turn_key(request)
        existing = self.commitments.get(key)
        if existing is not None and existing != request.commitment:
            raise ValueError("conflicting commitment for existing turn")
        self.commitments[key] = request.commitment
        return existing is None

    def record_reveal(self, request: RevealTurnRequest) -> bool:
        """Store an immediate reveal only after its commitment exists."""
        key = turn_key(request)
        commitment = self.commitments.get(key)
        if commitment is None:
            raise ValueError("reveal received before commitment")
        reveal = RevealedTurn(commitment=commitment, action=request.action, hint=request.hint)
        existing = self.reveals.get(key)
        if existing is not None and existing != reveal:
            raise ValueError("conflicting reveal for existing turn")
        self.reveals[key] = reveal
        return existing is None

