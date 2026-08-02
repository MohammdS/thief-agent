"""Local-truth-only input accepted by Thief movement policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.domain.types import Coord


@dataclass(frozen=True, slots=True)
class ThiefObservation:
    """Expose local position, public barriers, scent, and Police belief only."""

    width: int
    height: int
    thief: Coord
    known_barriers: frozenset[Coord]
    police_scent: Mapping[Coord, float]
    police_belief: Mapping[Coord, float]
    step: int
    recent_positions: tuple[Coord, ...] = ()

    def __post_init__(self) -> None:
        """Reject impossible local observations."""
        if not (0 <= self.thief.row < self.height and 0 <= self.thief.col < self.width):
            raise ValueError("Thief position must be inside the board")
        if self.thief in self.known_barriers:
            raise ValueError("Thief cannot occupy a known barrier")

