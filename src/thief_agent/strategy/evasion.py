"""Deterministic two-ply evasion under a hidden Police belief map."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.domain.board import destination
from thief_agent.domain.types import Coord, Move
from thief_agent.strategy.observation import ThiefObservation

MOVE_ORDER = (Move.NORTH, Move.EAST, Move.SOUTH, Move.WEST, Move.STAY)


@dataclass(frozen=True, slots=True)
class MoveEvaluation:
    """Expose interpretable components used to rank one legal move."""

    move: Move
    destination: Coord
    capture_risk: float
    belief_distance: float
    reachable_area: int
    mobility: int
    next_escape: float
    revisit_penalty: int
    total: float


class EvasionStrategy:
    """Choose legal movement without delegating geometry to an LLM."""

    def choose_move(self, observation: ThiefObservation) -> Move:
        """Return the highest-scoring legal move with stable ties."""
        evaluations = self.evaluate_moves(observation)
        if not evaluations:
            return Move.STAY
        return max(evaluations, key=lambda item: (item.total, -MOVE_ORDER.index(item.move))).move

    def evaluate_moves(self, observation: ThiefObservation) -> tuple[MoveEvaluation, ...]:
        """Score each legal move using immediate and next-turn safety."""
        return tuple(self._evaluate(observation, move) for move in legal_local_moves(observation))

    def _evaluate(self, observation: ThiefObservation, move: Move) -> MoveEvaluation:
        """Calculate the transparent two-ply heuristic for one action."""
        target = destination(observation.thief, move)
        risk = capture_risk(target, observation.police_belief)
        distance = sum(
            target.manhattan(cell) * probability
            for cell, probability in observation.police_belief.items()
        )
        area = reachable_area(observation, target)
        mobility = len(neighbors(observation, target))
        next_escape = max(
            (1.0 - capture_risk(cell, observation.police_belief)
             for cell in neighbors(observation, target)),
            default=0.0,
        )
        revisit = observation.recent_positions.count(target)
        total = (
            -50.0 * risk + 2.0 * distance + 0.15 * area + 1.5 * mobility
            + 4.0 * next_escape - 3.0 * (4 - mobility) - 1.5 * revisit
        )
        return MoveEvaluation(
            move, target, risk, distance, area, mobility, next_escape, revisit, total,
        )


def legal_local_moves(observation: ThiefObservation) -> tuple[Move, ...]:
    """Return moves allowed by local geometry and public barriers."""
    return tuple(
        move for move in MOVE_ORDER
        if is_open(observation, destination(observation.thief, move))
    )


def is_open(observation: ThiefObservation, cell: Coord) -> bool:
    """Return whether a local cell is in bounds and not a known barrier."""
    return (
        0 <= cell.row < observation.height
        and 0 <= cell.col < observation.width
        and cell not in observation.known_barriers
    )


def neighbors(observation: ThiefObservation, cell: Coord) -> tuple[Coord, ...]:
    """Return open adjacent orthogonal cells, excluding STAY."""
    moves = (Move.NORTH, Move.EAST, Move.SOUTH, Move.WEST)
    return tuple(
        candidate
        for move in moves
        if is_open(observation, candidate := destination(cell, move))
    )


def capture_risk(target: Coord, belief: Mapping[Coord, float]) -> float:
    """Estimate risk that Police can reach a target in its next movement."""
    return min(
        1.0,
        sum(probability for cell, probability in belief.items() if cell.manhattan(target) <= 1),
    )


def reachable_area(observation: ThiefObservation, start: Coord) -> int:
    """Count locally reachable cells behind current permanent barriers."""
    seen, pending = {start}, [start]
    while pending:
        current = pending.pop()
        for cell in neighbors(observation, current):
            if cell not in seen:
                seen.add(cell)
                pending.append(cell)
    return len(seen)
