"""Information-safe presentation model for the live Thief GUI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.domain.types import Coord

BASE_COLOR = "#f8fafc"
BELIEF_COLOR = "#ef4444"
SCENT_COLOR = "#2563eb"
THIEF_COLOR = "#16a34a"
BARRIER_COLOR = "#111827"


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
    subgame: int = 0
    series_size: int = 1
    protocol_state: str = "Waiting for peer"
    last_event: str = "No protocol event yet"
    terminal_reason: str | None = None

    def __post_init__(self) -> None:
        """Reject impossible or negative live presentation state."""
        if not (0 <= self.thief.row < self.height and 0 <= self.thief.col < self.width):
            raise ValueError("live Thief position must be inside the board")
        captured_by_barrier = (
            self.thief in self.known_barriers and self.terminal_reason == "capture"
        )
        if (
            (self.thief in self.known_barriers and not captured_by_barrier)
            or self.step < 0
            or self.tokens_used < 0
        ):
            raise ValueError("live snapshot contains impossible local state")
        if self.subgame < 0 or self.series_size < 1:
            raise ValueError("live snapshot contains invalid series progress")
        if self.subgame > self.series_size:
            raise ValueError("live snapshot subgame exceeds series size")
        valid_reasons = {None, "capture", "imprisonment", "survival", "tie", "technical_loss"}
        if self.terminal_reason not in valid_reasons:
            raise ValueError("live snapshot contains unsupported terminal reason")


def heat_scale(values: Mapping[Coord, float]) -> float:
    """Return the positive layer peak used for relative color intensity."""
    return max((value for value in values.values() if value > 0), default=1.0)


def heat_color(belief: float, scent: float) -> str:
    """Blend normalized belief as red and normalized scent as blue."""
    belief_strength = max(0.0, min(1.0, belief))
    scent_strength = max(0.0, min(1.0, scent))
    if belief_strength + scent_strength == 0:
        return BASE_COLOR
    base, red, blue = (248, 250, 252), (239, 68, 68), (37, 99, 235)
    total = belief_strength + scent_strength
    target = tuple(
        (belief_strength * red[index] + scent_strength * blue[index]) / total for index in range(3)
    )
    intensity = max(belief_strength, scent_strength)
    mixed = tuple(
        round(base[index] * (1 - intensity) + target[index] * intensity) for index in range(3)
    )
    return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"
