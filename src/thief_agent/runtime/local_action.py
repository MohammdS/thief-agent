"""Apply Thief-local truth and public Police barrier events."""

from __future__ import annotations

from thief_agent.config.models import PointConfig, SharedConfig
from thief_agent.domain.board import apply_move
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Move, Role
from thief_agent.runtime.live_state import apply_public_barrier


def apply_thief_action(
    state: BoardState, move: Move, barrier: PointConfig | None, config: SharedConfig,
) -> BoardState:
    """Apply local movement followed by an optional public barrier event."""
    updated = apply_move(state, Role.THIEF, move)
    if barrier is None:
        return updated
    return apply_public_barrier(updated, Coord(barrier.row, barrier.col), config)
