"""Fixed 5x5 radial scent emission and full-turn decay."""

from __future__ import annotations

from collections.abc import Mapping
from math import isclose

from thief_agent.domain.types import Coord

SCENT_KERNEL = (
    (0.04, 0.14, 0.20, 0.14, 0.04),
    (0.14, 0.42, 0.62, 0.42, 0.14),
    (0.20, 0.62, 0.90, 0.62, 0.20),
    (0.14, 0.42, 0.62, 0.42, 0.14),
    (0.04, 0.14, 0.20, 0.14, 0.04),
)
ScentMap = dict[Coord, float]


def emission(center: Coord, width: int, height: int) -> ScentMap:
    """Return the clipped fixed radial emission around one agent."""
    result: ScentMap = {}
    for kernel_row, values in enumerate(SCENT_KERNEL):
        for kernel_col, intensity in enumerate(values):
            cell = Coord(center.row + kernel_row - 2, center.col + kernel_col - 2)
            if 0 <= cell.row < height and 0 <= cell.col < width:
                result[cell] = intensity
    return result


def advance_scent(
    previous: Mapping[Coord, float],
    center: Coord,
    width: int,
    height: int,
    decay: float = 0.10,
) -> ScentMap:
    """Apply tau(t+1)=max(0,(1-rho)*tau(t)+delta) after a full turn."""
    if not 0 <= decay <= 1:
        raise ValueError("decay must be between zero and one")
    deposited = emission(center, width, height)
    cells = set(previous) | set(deposited)
    return {
        cell: max(0.0, (1.0 - decay) * previous.get(cell, 0.0) + deposited.get(cell, 0.0))
        for cell in cells
        if 0 <= cell.row < height and 0 <= cell.col < width
    }


def infer_emitter(
    previous: Mapping[Coord, float], observed: Mapping[Coord, float],
    width: int, height: int, decay: float = 0.10,
    blocked: frozenset[Coord] = frozenset(),
) -> Coord:
    """Invert the public deterministic scent transition to one unique cell."""
    candidates = (
        Coord(row, col) for row in range(height) for col in range(width)
        if Coord(row, col) not in blocked
    )
    matches = tuple(
        cell for cell in candidates
        if same_scent(advance_scent(previous, cell, width, height, decay), observed)
    )
    if len(matches) != 1:
        raise ValueError(f"scent transition has {len(matches)} feasible emitters")
    return matches[0]


def same_scent(left: Mapping[Coord, float], right: Mapping[Coord, float]) -> bool:
    """Compare canonical heatmaps with a tight wire-roundtrip tolerance."""
    return left.keys() == right.keys() and all(
        isclose(value, right[cell], rel_tol=0.0, abs_tol=1e-9)
        for cell, value in left.items()
    )
