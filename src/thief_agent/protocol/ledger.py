"""Idempotent per-turn commitment and reveal ledger."""

from __future__ import annotations

from dataclasses import dataclass, field

from thief_agent.crypto.audit import RevealedTurn
from thief_agent.domain.types import Role
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
    token_owners: dict[int, Role] = field(default_factory=dict)
    completed_steps: dict[tuple[int, Role], int] = field(default_factory=dict)

    def _require_turn(self, subgame: int, step: int, sender: Role) -> None:
        """Reject actions by a non-owner or a skipped/repeated new step."""
        owner = self.token_owners.setdefault(subgame, Role.THIEF)
        if owner is not sender:
            raise ValueError(f"turn token belongs to {owner.value}")
        expected = self.completed_steps.get((subgame, sender), 0) + 1
        if step != expected:
            raise ValueError(f"expected {sender.value} step {expected}")

    def complete_local_turn(
        self,
        subgame: int,
        step: int,
        sender: Role,
        recipient: Role,
    ) -> None:
        """Record a locally sent reveal and transfer its token exactly once."""
        self._require_turn(subgame, step, sender)
        if recipient is sender:
            raise ValueError("turn token must be granted to the opponent")
        self.completed_steps[(subgame, sender)] = step
        self.token_owners[subgame] = recipient

    def record_commit(self, request: CommitTurnRequest) -> bool:
        """Store a commitment and return False for an identical duplicate."""
        key = turn_key(request)
        existing = self.commitments.get(key)
        if existing is not None and existing != request.commitment:
            raise ValueError("conflicting commitment for existing turn")
        if existing is None:
            self._require_turn(
                request.envelope.subgame,
                request.envelope.step,
                request.envelope.sender,
            )
        self.commitments[key] = request.commitment
        return existing is None

    def record_reveal(self, request: RevealTurnRequest) -> bool:
        """Store an immediate reveal only after its commitment exists."""
        key = turn_key(request)
        existing = self.reveals.get(key)
        if existing is not None:
            candidate = RevealedTurn(
                commitment=self.commitments[key],
                turn_token=request.turn_token,
                scent_heatmap=request.scent_heatmap,
                hint=request.hint,
                barrier=request.barrier,
                capture_claim=request.capture_claim,
            )
            if existing != candidate:
                raise ValueError("conflicting reveal for existing turn")
            return False
        commitment = self.commitments.get(key)
        if commitment is None:
            raise ValueError("reveal received before commitment")
        envelope = request.envelope
        self._require_turn(envelope.subgame, envelope.step, envelope.sender)
        reveal = RevealedTurn(
            commitment=commitment,
            turn_token=request.turn_token,
            scent_heatmap=request.scent_heatmap,
            hint=request.hint,
            barrier=request.barrier,
            capture_claim=request.capture_claim,
        )
        self.reveals[key] = reveal
        self.completed_steps[(envelope.subgame, envelope.sender)] = envelope.step
        self.token_owners[envelope.subgame] = request.turn_token
        return True
