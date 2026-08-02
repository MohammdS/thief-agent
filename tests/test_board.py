import pytest
from hypothesis import given
from hypothesis import strategies as st

from thief_agent.domain.board import (
    apply_move,
    is_captured,
    is_imprisoned,
    legal_moves,
    place_barrier,
    reachable_area,
)
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Move, Role


def basic_state(**changes: object) -> BoardState:
    values = {"width": 7, "height": 7, "thief": Coord(3, 3), "police": Coord(0, 0)}
    values.update(changes)
    return BoardState(**values)  # type: ignore[arg-type]


def test_corner_movement_and_stay() -> None:
    moves = legal_moves(basic_state(thief=Coord(0, 0), police=Coord(6, 6)), Role.THIEF)
    assert moves == (Move.SOUTH, Move.EAST, Move.STAY)


def test_illegal_move_is_rejected() -> None:
    with pytest.raises(ValueError, match="illegal"):
        apply_move(basic_state(thief=Coord(0, 0)), Role.THIEF, Move.NORTH)


def test_barrier_is_adjacent_permanent_and_consumes_quota() -> None:
    state = place_barrier(basic_state(), Coord(0, 1), capacity=14)
    assert state.barriers == {Coord(0, 1)}
    assert state.barriers_used == 1
    with pytest.raises(ValueError, match="already"):
        place_barrier(state, Coord(0, 1), capacity=14)


def test_barrier_capacity_and_range_are_enforced() -> None:
    with pytest.raises(ValueError, match="adjacent"):
        place_barrier(basic_state(), Coord(2, 2), capacity=14)
    exhausted = basic_state(barriers_used=14)
    with pytest.raises(ValueError, match="exhausted"):
        place_barrier(exhausted, Coord(0, 0), capacity=14)


def test_overlap_and_barrier_on_thief_capture() -> None:
    assert is_captured(basic_state(thief=Coord(0, 0)))
    state = basic_state(thief=Coord(0, 1))
    assert is_captured(place_barrier(state, Coord(0, 1), capacity=14))


def test_stay_does_not_avoid_imprisonment() -> None:
    barriers = frozenset({Coord(2, 3), Coord(4, 3), Coord(3, 2), Coord(3, 4)})
    assert is_imprisoned(basic_state(barriers=barriers, barriers_used=4))
    assert Move.STAY in legal_moves(basic_state(barriers=barriers, barriers_used=4), Role.THIEF)


def test_reachable_area_respects_barriers() -> None:
    wall = frozenset(Coord(row, 1) for row in range(7))
    state = basic_state(thief=Coord(3, 0), barriers=wall, barriers_used=7)
    assert reachable_area(state, state.thief) == 7


@given(row=st.integers(0, 6), col=st.integers(0, 6))
def test_every_reported_legal_move_stays_in_bounds(row: int, col: int) -> None:
    state = basic_state(thief=Coord(row, col), police=Coord(6 - row, 6 - col))
    if state.thief == state.police:
        return
    for move in legal_moves(state, Role.THIEF):
        assert state.contains(apply_move(state, Role.THIEF, move).thief)

