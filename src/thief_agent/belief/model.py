"""Normalized Police-location belief using scent and verbal evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import pow

from thief_agent.domain.types import Coord

MIN_HINT_STRENGTH = 0.25
MAX_HINT_STRENGTH = 1.5
SCENT_HINT_CONFIDENCE = 0.4


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
    truth_probability: float = 0.5,
) -> BeliefMap:
    """Apply delayed scent, predict movement, and compare the incoming hint."""
    direction = parse_direction(hint)
    scent_alignment = hint_scent_alignment(
        scent, prior.width, prior.height, direction,
    )
    historical = update_belief(prior, scent, blocked)
    current = predict_belief(historical, blocked)
    return update_belief(
        current, {}, blocked, hint, truth_probability=truth_probability,
        scent_alignment=scent_alignment,
    )


def update_belief(
    prior: BeliefMap,
    scent: Mapping[Coord, float],
    blocked: frozenset[Coord],
    hint: str = "",
    truth_probability: float = 0.5,
    scent_alignment: float | None = None,
) -> BeliefMap:
    """Apply scent evidence and adapt hint strength to scent consistency."""
    if not 0 <= truth_probability <= 1:
        raise ValueError("truth probability must lie in [0, 1]")
    direction = parse_direction(hint)
    alignment = (
        hint_scent_alignment(scent, prior.width, prior.height, direction)
        if scent_alignment is None else scent_alignment
    )
    hint_strength = hint_integration_strength(alignment)
    effective_truth_probability = adjusted_truth_probability(
        truth_probability, alignment,
    )
    weights: dict[Coord, float] = {}
    max_scent = max(scent.values(), default=0.0)
    for cell, probability in prior.probabilities.items():
        if cell in blocked:
            continue
        scent_likelihood = 1.0 if max_scent == 0 else 0.05 + scent.get(cell, 0.0) / max_scent
        hint_likelihood = direction_likelihood(
            cell, prior, direction, effective_truth_probability, hint_strength,
        )
        weights[cell] = probability * scent_likelihood * hint_likelihood
    return normalize(prior.width, prior.height, weights, blocked)


def _directions_in_hint(hint: str) -> tuple[str, ...]:
    """Return distinct cardinal cues found in a natural-language hint."""
    lowered = hint.casefold()
    aliases = {
        "north": ("north", "northern", "upward"),
        "south": ("south", "southern", "downward"),
        "east": ("east", "eastern", "rightward"),
        "west": ("west", "western", "leftward"),
    }
    return tuple(
        name for name, words in aliases.items()
        if any(word in lowered for word in words)
    )


def is_contradictory_hint(hint: str) -> bool:
    """Return whether a hint contains opposite cardinal directions."""
    directions = set(_directions_in_hint(hint))
    return {"north", "south"} <= directions or {"east", "west"} <= directions


def parse_direction(hint: str) -> str | None:
    """Extract one unambiguous cardinal cue from natural language."""
    matches = _directions_in_hint(hint)
    return matches[0] if len(matches) == 1 else None


def hint_scent_alignment(
    scent: Mapping[Coord, float], width: int, height: int, direction: str | None,
) -> float:
    """Return directional scent support in [-1, 1] for the parsed hint."""
    if direction is None:
        return 0.0
    center_row, center_col = (height - 1) / 2, (width - 1) / 2
    supporting = 0.0
    opposing = 0.0
    for cell, value in scent.items():
        if value <= 0 or not (0 <= cell.row < height and 0 <= cell.col < width):
            continue
        offset = {
            "north": center_row - cell.row,
            "south": cell.row - center_row,
            "east": cell.col - center_col,
            "west": center_col - cell.col,
        }[direction]
        if offset > 0:
            supporting += value * offset
        elif offset < 0:
            opposing += value * -offset
    total = supporting + opposing
    return 0.0 if total == 0 else (supporting - opposing) / total


def hint_integration_strength(scent_alignment: float) -> float:
    """Scale hint evidence down on conflict and up on scent agreement."""
    if not -1 <= scent_alignment <= 1:
        raise ValueError("scent alignment must lie in [-1, 1]")
    return min(MAX_HINT_STRENGTH, max(MIN_HINT_STRENGTH, 1.0 + scent_alignment))


def adjusted_truth_probability(truth_probability: float, scent_alignment: float) -> float:
    """Temporarily update hint truth odds using current scent agreement."""
    if not 0 <= truth_probability <= 1:
        raise ValueError("truth probability must lie in [0, 1]")
    if not -1 <= scent_alignment <= 1:
        raise ValueError("scent alignment must lie in [-1, 1]")
    truth_likelihood = 0.5 + SCENT_HINT_CONFIDENCE * scent_alignment
    bluff_likelihood = 0.5 - SCENT_HINT_CONFIDENCE * scent_alignment
    denominator = (
        truth_probability * truth_likelihood
        + (1.0 - truth_probability) * bluff_likelihood
    )
    if denominator == 0:
        return truth_probability
    return truth_probability * truth_likelihood / denominator


def direction_likelihood(
    cell: Coord, belief: BeliefMap, direction: str | None, truth_probability: float,
    hint_strength: float = 1.0,
) -> float:
    """Weight a board half by truth profile and scent-consistency strength."""
    if direction is None or truth_probability == 0.5:
        return 1.0
    if hint_strength <= 0:
        raise ValueError("hint strength must be positive")
    center_row, center_col = (belief.height - 1) / 2, (belief.width - 1) / 2
    matches = {
        "north": cell.row <= center_row,
        "south": cell.row >= center_row,
        "east": cell.col >= center_col,
        "west": cell.col <= center_col,
    }[direction]
    support = truth_probability if matches else 1.0 - truth_probability
    base_likelihood = float(max(0.05, 2.0 * support))
    return pow(base_likelihood, hint_strength)


def normalize(
    width: int, height: int, weights: Mapping[Coord, float], blocked: frozenset[Coord],
) -> BeliefMap:
    """Normalize positive weights or recover to a uniform feasible prior."""
    total = sum(weights.values())
    if total <= 0:
        return uniform_belief(width, height, blocked)
    return BeliefMap(width, height, {cell: value / total for cell, value in weights.items()})
