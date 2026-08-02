"""Information-safe presentation model for the live Thief GUI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.domain.types import Coord


@dataclass(frozen=True, slots=True)
class LiveSnapshot:
    """Contain only local truth, public facts, and hidden-Police belief."""

    width: int
    height: int
    thief: Coord
    known_barriers: frozenset[Coord]
    police_scent: Mapping[Coord, float]
    police_belief: Mapping[Coord, float]
    step: int
    latest_hint: str
    tokens_used: int
    network_state: str
    audit_state: str
    local_turn: bool

    def __post_init__(self) -> None:
        """Reject impossible or negative live presentation state."""
        if not (0 <= self.thief.row < self.height and 0 <= self.thief.col < self.width):
            raise ValueError("live Thief position must be inside the board")
        if self.thief in self.known_barriers or self.step < 0 or self.tokens_used < 0:
            raise ValueError("live snapshot contains impossible local state")


def heat_color(belief: float, scent: float) -> str:
    """Blend Police belief as red and scent as blue on a pale background."""
    belief_strength = max(0.0, min(1.0, belief))
    scent_strength = max(0.0, min(1.0, scent / 0.9))
    red = int(245 - 90 * scent_strength)
    green = int(245 - 125 * max(belief_strength, scent_strength))
    blue = int(245 - 100 * belief_strength)
    return f"#{red:02x}{green:02x}{blue:02x}"

