"""Local-truth state helpers that do not require opponent movement."""

from __future__ import annotations

from dataclasses import replace

from thief_agent.config.models import SharedConfig
from thief_agent.domain.scent import ScentMap
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord


def initial_state(config: SharedConfig) -> BoardState:
    """Create the negotiated starts before either role moves."""
    return BoardState(
        config.board.width,
        config.board.height,
        Coord(config.board.thief_start.row, config.board.thief_start.col),
        Coord(config.board.police_start.row, config.board.police_start.col),
    )


def apply_public_barrier(state: BoardState, target: Coord, config: SharedConfig) -> BoardState:
    """Apply a public barrier notice without learning the hidden Police position."""
    if not state.contains(target):
        raise ValueError("public barrier lies outside the board")
    if target in state.barriers:
        raise ValueError("public barrier is already present")
    if state.barriers_used >= config.barriers.police_capacity:
        raise ValueError("public barrier exceeds Police capacity")
    return replace(
        state,
        barriers=state.barriers | {target},
        barriers_used=state.barriers_used + 1,
    )


def require_in_bounds_heatmap(scent: ScentMap, state: BoardState) -> None:
    """Reject remote heatmap coordinates outside the negotiated board."""
    if any(not state.contains(cell) for cell in scent):
        raise ValueError("scent heatmap contains an out-of-bounds cell")
