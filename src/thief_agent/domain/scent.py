"""Fixed 5x5 radial scent emission and full-turn decay."""

from __future__ import annotations

from collections.abc import Mapping

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
    return deposit_scent(
        decay_scent(previous, decay), center, width, height,
    )


def decay_scent(
    previous: Mapping[Coord, float], decay: float = 0.10,
) -> ScentMap:
    """Return the public trail after decay but before the current emission."""
    if not 0 <= decay <= 1:
        raise ValueError("decay must be between zero and one")
    return {
        cell: max(0.0, (1.0 - decay) * value)
        for cell, value in previous.items()
    }


def deposit_scent(
    previous: Mapping[Coord, float], center: Coord, width: int, height: int,
) -> ScentMap:
    """Add one private current-turn emission to an already-decayed trail."""
    deposited = emission(center, width, height)
    cells = set(previous) | set(deposited)
    return {
        cell: previous.get(cell, 0.0) + deposited.get(cell, 0.0)
        for cell in cells
        if 0 <= cell.row < height and 0 <= cell.col < width
    }
