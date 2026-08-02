"""Immutable objective state used only by validation and post-match replay."""

from __future__ import annotations

from dataclasses import dataclass, replace

from thief_agent.domain.types import Coord, Role


@dataclass(frozen=True, slots=True)
class BoardState:
    """Store physical state without exposing it directly to live strategy or UI."""

    width: int
    height: int
    thief: Coord
    police: Coord
    barriers: frozenset[Coord] = frozenset()
    barriers_used: int = 0
    step: int = 0

    def __post_init__(self) -> None:
        """Reject internally inconsistent physical state."""
        if self.width < 1 or self.height < 1 or self.step < 0:
            raise ValueError("board dimensions and step must be non-negative")
        if not self.contains(self.thief) or not self.contains(self.police):
            raise ValueError("agent coordinates must be inside the board")
        if any(not self.contains(cell) for cell in self.barriers):
            raise ValueError("barriers must be inside the board")
        if self.barriers_used < len(self.barriers):
            raise ValueError("barrier usage cannot be smaller than placed barriers")

    def contains(self, coord: Coord) -> bool:
        """Return whether a coordinate is inside the board."""
        return 0 <= coord.row < self.height and 0 <= coord.col < self.width

    def position(self, role: Role) -> Coord:
        """Return one role's objective position for validators and replay."""
        return self.thief if role is Role.THIEF else self.police

    def with_position(self, role: Role, coord: Coord) -> BoardState:
        """Return a new state with one role moved."""
        if role is Role.THIEF:
            return replace(self, thief=coord)
        return replace(self, police=coord)

    def after_full_turn(self) -> BoardState:
        """Increment the full-turn counter after both roles have acted."""
        return replace(self, step=self.step + 1)
