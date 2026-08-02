"""Strict movement, barrier, and hidden intent payloads."""

from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from thief_agent.config.models import PointConfig, StrictModel
from thief_agent.domain.types import Move


class ActionKind(StrEnum):
    """Distinguish a movement turn from Police barrier placement."""

    MOVE = "move"
    BARRIER = "barrier"


class HintIntent(StrEnum):
    """Record truth or bluff intent for final audit only."""

    TRUTH = "truth"
    BLUFF = "bluff"


class TurnAction(StrictModel):
    """Represent exactly one physical turn action."""

    kind: ActionKind
    move: Move | None = None
    barrier: PointConfig | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> TurnAction:
        """Require the field matching the selected action kind."""
        if self.kind is ActionKind.MOVE and (self.move is None or self.barrier is not None):
            raise ValueError("move action requires only move")
        if self.kind is ActionKind.BARRIER and (self.barrier is None or self.move is not None):
            raise ValueError("barrier action requires only barrier")
        return self

