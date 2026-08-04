"""Normalized Police-location belief using scent and verbal evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.domain.types import Coord


@dataclass(frozen=True, slots=True)
class BeliefMap:
    """Store a normalized probability for every feasible Police cell."""

    width: int
    height: int
    probabilities: Mapping[Coord, float]

    def __post_init__(self) -> None:
        """Require finite, normalized, in-bounds probabilities."""
        if any(not 0 <= value <= 1 for value in self.probabilities.values()):
            raise ValueError("belief probabilities must lie in [0, 1]")
        if any(not (0 <= cell.row < self.height and 0 <= cell.col < self.width)
               for cell in self.probabilities):
            raise ValueError("belief cells must lie inside the board")
        if abs(sum(self.probabilities.values()) - 1.0) > 1e-9:
            raise ValueError("belief probabilities must sum to one")

    def probability(self, cell: Coord) -> float:
        """Return a cell probability, treating excluded cells as zero."""
        return self.probabilities.get(cell, 0.0)

    def most_likely(self) -> Coord:
        """Return the highest-probability cell with stable coordinate ties."""
        return min(self.probabilities, key=lambda cell: (-self.probability(cell), cell))


def uniform_belief(width: int, height: int, blocked: frozenset[Coord] = frozenset()) -> BeliefMap:
    """Create a uniform prior over all non-blocked cells."""
    cells = [Coord(row, col) for row in range(height) for col in range(width)
             if Coord(row, col) not in blocked]
    if not cells:
        raise ValueError("belief requires at least one feasible cell")
    probability = 1.0 / len(cells)
    return BeliefMap(width, height, {cell: probability for cell in cells})


def point_belief(width: int, height: int, cell: Coord) -> BeliefMap:
    """Create the public pre-game certainty at an agreed start cell."""
    if not (0 <= cell.row < height and 0 <= cell.col < width):
        raise ValueError("belief point must lie inside the board")
    return BeliefMap(width, height, {cell: 1.0})


def predict_belief(prior: BeliefMap, blocked: frozenset[Coord]) -> BeliefMap:
    """Propagate probability through one unknown legal N/S/E/W/STAY action."""
    predicted: dict[Coord, float] = {}
    for cell, probability in prior.probabilities.items():
        candidates = tuple(
            target for row_delta, col_delta in ((-1, 0), (0, 1), (1, 0), (0, -1), (0, 0))
            if 0 <= (target := Coord(cell.row + row_delta, cell.col + col_delta)).row < prior.height
            and 0 <= target.col < prior.width
            and target not in blocked
        )
        share = probability / len(candidates)
        for target in candidates:
            predicted[target] = predicted.get(target, 0.0) + share
    return normalize(prior.width, prior.height, predicted, blocked)


def advance_delayed_belief(
    prior: BeliefMap,
    scent: Mapping[Coord, float],
    blocked: frozenset[Coord],
    hint: str = "",
) -> BeliefMap:
    """Apply the historical scent, then predict the opponent's hidden current move."""
    historical = update_belief(prior, scent, blocked)
    current = predict_belief(historical, blocked)
    return update_belief(current, {}, blocked, hint)


def update_belief(
    prior: BeliefMap,
    scent: Mapping[Coord, float],
    blocked: frozenset[Coord],
    hint: str = "",
    truth_probability: float = 0.5,
) -> BeliefMap:
    """Apply scent likelihood and optional directional hint evidence."""
    if not 0 <= truth_probability <= 1:
        raise ValueError("truth probability must lie in [0, 1]")
    direction = parse_direction(hint)
    weights: dict[Coord, float] = {}
    max_scent = max(scent.values(), default=0.0)
    for cell, probability in prior.probabilities.items():
        if cell in blocked:
            continue
        scent_likelihood = 1.0 if max_scent == 0 else 0.05 + scent.get(cell, 0.0) / max_scent
        hint_likelihood = direction_likelihood(cell, prior, direction, truth_probability)
        weights[cell] = probability * scent_likelihood * hint_likelihood
    return normalize(prior.width, prior.height, weights, blocked)


def parse_direction(hint: str) -> str | None:
    """Extract one explicit cardinal cue from natural language."""
    lowered = hint.casefold()
    aliases = {
        "north": ("north", "northern", "upward"),
        "south": ("south", "southern", "downward"),
        "east": ("east", "eastern", "rightward"),
        "west": ("west", "western", "leftward"),
    }
    matches = [name for name, words in aliases.items() if any(word in lowered for word in words)]
    return matches[0] if len(matches) == 1 else None


def direction_likelihood(
    cell: Coord, belief: BeliefMap, direction: str | None, truth_probability: float,
) -> float:
    """Weight a board half by the learned probability that hints are truthful."""
    if direction is None or truth_probability == 0.5:
        return 1.0
    center_row, center_col = (belief.height - 1) / 2, (belief.width - 1) / 2
    matches = {
        "north": cell.row <= center_row,
        "south": cell.row >= center_row,
        "east": cell.col >= center_col,
        "west": cell.col <= center_col,
    }[direction]
    support = truth_probability if matches else 1.0 - truth_probability
    return max(0.05, 2.0 * support)


def normalize(
    width: int, height: int, weights: Mapping[Coord, float], blocked: frozenset[Coord],
) -> BeliefMap:
    """Normalize positive weights or recover to a uniform feasible prior."""
    total = sum(weights.values())
    if total <= 0:
        return uniform_belief(width, height, blocked)
    return BeliefMap(width, height, {cell: value / total for cell, value in weights.items()})
