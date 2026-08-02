"""Small immutable types used throughout the physical game model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Move(StrEnum):
    """Enumerate the fixed physical action alphabet."""

    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    STAY = "STAY"


class Role(StrEnum):
    """Identify either autonomous peer role."""

    THIEF = "thief"
    POLICE = "police"


@dataclass(frozen=True, order=True, slots=True)
class Coord:
    """Represent a zero-based row and column."""

    row: int
    col: int

    def manhattan(self, other: Coord) -> int:
        """Return orthogonal grid distance to another coordinate."""
        return abs(self.row - other.row) + abs(self.col - other.col)

