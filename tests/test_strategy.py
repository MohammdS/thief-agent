from hypothesis import given
from hypothesis import strategies as st

from thief_agent.domain.board import destination
from thief_agent.domain.types import Coord, Move
from thief_agent.strategy.evasion import EvasionStrategy, is_open, legal_local_moves
from thief_agent.strategy.observation import ThiefObservation


def observation(
    thief: Coord | None = None,
    belief: dict[Coord, float] | None = None,
    barriers: frozenset[Coord] = frozenset(),
    recent: tuple[Coord, ...] = (),
) -> ThiefObservation:
    police_belief = belief or {Coord(0, 0): 1.0}
    return ThiefObservation(7, 7, thief or Coord(3, 3), barriers, {}, police_belief, 1, recent)


def test_strategy_moves_away_from_concentrated_police_belief() -> None:
    current = observation(belief={Coord(2, 3): 1.0})
    move = EvasionStrategy().choose_move(current)
    assert destination(current.thief, move).manhattan(Coord(2, 3)) == 2


def test_strategy_avoids_barrier_and_revisit_when_safe_alternative_exists() -> None:
    barriers = frozenset({Coord(3, 2), Coord(2, 3)})
    current = observation(barriers=barriers, recent=(Coord(3, 4),))
    move = EvasionStrategy().choose_move(current)
    assert move in {Move.SOUTH, Move.STAY}
    assert move is not Move.EAST


def test_imprisoned_strategy_returns_stay_without_illegal_escape() -> None:
    barriers = frozenset({Coord(2, 3), Coord(4, 3), Coord(3, 2), Coord(3, 4)})
    current = observation(barriers=barriers)
    assert legal_local_moves(current) == (Move.STAY,)
    assert EvasionStrategy().choose_move(current) is Move.STAY


def test_observation_schema_has_no_objective_police_position_or_action() -> None:
    fields = set(ThiefObservation.__dataclass_fields__)
    assert "police" not in fields
    assert "police_position" not in fields
    assert "police_action" not in fields


@given(row=st.integers(0, 6), col=st.integers(0, 6))
def test_strategy_always_returns_a_locally_legal_move(row: int, col: int) -> None:
    current = observation(thief=Coord(row, col))
    move = EvasionStrategy().choose_move(current)
    assert move in legal_local_moves(current)
    assert is_open(current, destination(current.thief, move))


def test_evaluations_are_deterministic_and_interpretable() -> None:
    strategy = EvasionStrategy()
    current = observation()
    assert strategy.evaluate_moves(current) == strategy.evaluate_moves(current)
    assert all(item.reachable_area > 0 for item in strategy.evaluate_moves(current))
