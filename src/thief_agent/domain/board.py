"""Legal movement, barrier, capture, and imprisonment rules."""

from __future__ import annotations

from dataclasses import replace

from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Move, Role

DELTAS = {
    Move.NORTH: (-1, 0),
    Move.SOUTH: (1, 0),
    Move.EAST: (0, 1),
    Move.WEST: (0, -1),
    Move.STAY: (0, 0),
}


def destination(origin: Coord, move: Move) -> Coord:
    """Apply one fixed orthogonal move to a coordinate."""
    row_delta, col_delta = DELTAS[move]
    return Coord(origin.row + row_delta, origin.col + col_delta)


def legal_moves(state: BoardState, role: Role) -> tuple[Move, ...]:
    """Return in-bounds moves that do not enter a permanent barrier."""
    origin = state.position(role)
    return tuple(
        move for move in Move
        if state.contains(destination(origin, move))
        and destination(origin, move) not in state.barriers
    )


def apply_move(state: BoardState, role: Role, move: Move) -> BoardState:
    """Return a new state after a validated movement action."""
    if move not in legal_moves(state, role):
        raise ValueError(f"illegal {role.value} move: {move.value}")
    return state.with_position(role, destination(state.position(role), move))


def place_barrier(state: BoardState, target: Coord, capacity: int) -> BoardState:
    """Place one permanent Police barrier on its cell or an adjacent cell."""
    if state.barriers_used >= capacity:
        raise ValueError("Police barrier capacity exhausted")
    if not state.contains(target) or state.police.manhattan(target) > 1:
        raise ValueError("barrier must be on or orthogonally adjacent to Police")
    if target in state.barriers:
        raise ValueError("barrier is already present")
    return replace(
        state,
        barriers=state.barriers | {target},
        barriers_used=state.barriers_used + 1,
    )


def is_captured(state: BoardState) -> bool:
    """Return whether agents overlap or a barrier was placed on the Thief."""
    return state.thief == state.police or state.thief in state.barriers


def is_imprisoned(state: BoardState) -> bool:
    """Return whether the Thief has no traversable adjacent orthogonal cell."""
    adjacent = (Move.NORTH, Move.SOUTH, Move.EAST, Move.WEST)
    candidates = (destination(state.thief, move) for move in adjacent)
    return not any(
        state.contains(cell) and cell not in state.barriers and cell != state.police
        for cell in candidates
    )


def reachable_area(state: BoardState, start: Coord) -> int:
    """Count barrier-free cells reachable orthogonally from a start."""
    if not state.contains(start) or start in state.barriers:
        return 0
    seen, pending = {start}, [start]
    while pending:
        current = pending.pop()
        for move in (Move.NORTH, Move.SOUTH, Move.EAST, Move.WEST):
            neighbor = destination(current, move)
            if state.contains(neighbor) and neighbor not in state.barriers and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return len(seen)
