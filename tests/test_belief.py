import pytest

from thief_agent.belief.model import (
    BeliefMap,
    adjusted_truth_probability,
    advance_delayed_belief,
    hint_integration_strength,
    hint_scent_alignment,
    is_contradictory_hint,
    parse_direction,
    uniform_belief,
    update_belief,
)
from thief_agent.domain.types import Coord


def test_uniform_belief_excludes_barriers_and_normalizes() -> None:
    blocked = frozenset({Coord(0, 0)})
    belief = uniform_belief(2, 2, blocked)
    assert belief.probability(Coord(0, 0)) == 0
    assert sum(belief.probabilities.values()) == pytest.approx(1)


def test_scent_concentrates_probability_and_blocked_cells_stay_zero() -> None:
    prior = uniform_belief(3, 3)
    hot = Coord(2, 2)
    posterior = update_belief(prior, {hot: 0.9}, frozenset({Coord(0, 0)}))
    assert posterior.most_likely() == hot
    assert posterior.probability(Coord(0, 0)) == 0
    assert sum(posterior.probabilities.values()) == pytest.approx(1)


def test_truthful_and_deceptive_profiles_invert_directional_hint() -> None:
    prior = uniform_belief(5, 5)
    truthful = update_belief(prior, {}, frozenset(), "I moved north", 0.9)
    deceptive = update_belief(prior, {}, frozenset(), "I moved north", 0.1)
    assert truthful.probability(Coord(0, 2)) > truthful.probability(Coord(4, 2))
    assert deceptive.probability(Coord(0, 2)) < deceptive.probability(Coord(4, 2))


def test_delayed_belief_uses_the_runtime_hint_reliability() -> None:
    prior = uniform_belief(5, 5)
    reliable = advance_delayed_belief(
        prior, {}, frozenset(), "I moved north", truth_probability=0.9,
    )
    deceptive = advance_delayed_belief(
        prior, {}, frozenset(), "I moved north", truth_probability=0.1,
    )
    assert reliable.probability(Coord(0, 2)) > reliable.probability(Coord(4, 2))
    assert deceptive.probability(Coord(0, 2)) < deceptive.probability(Coord(4, 2))
    assert sum(reliable.probabilities.values()) == pytest.approx(1)


def test_ambiguous_hint_is_ignored() -> None:
    prior = uniform_belief(3, 3)
    assert is_contradictory_hint("north then south")
    assert parse_direction("north then south") is None
    assert update_belief(prior, {}, frozenset(), "no clue").probabilities == prior.probabilities


def test_scent_conflict_reduces_hint_and_agreement_increases_it() -> None:
    prior = uniform_belief(5, 5)
    north = Coord(0, 2)
    south = Coord(4, 2)
    south_scent = {south: 0.9}
    north_scent = {north: 0.9}

    scent_only = update_belief(prior, south_scent, frozenset())
    hint_only = update_belief(prior, {}, frozenset(), "I moved north", 0.9)
    conflicted = update_belief(
        prior, south_scent, frozenset(), "I moved north", 0.9,
    )
    aligned = update_belief(
        prior, north_scent, frozenset(), "I moved north", 0.9,
    )
    aligned_from_neutral = update_belief(
        prior, north_scent, frozenset(), "I moved north", 0.5,
    )
    conflicted_from_neutral = update_belief(
        prior, south_scent, frozenset(), "I moved north", 0.5,
    )

    assert hint_scent_alignment(south_scent, 5, 5, "north") < 0
    assert hint_scent_alignment(north_scent, 5, 5, "north") > 0
    assert adjusted_truth_probability(0.5, 1) > 0.5
    assert adjusted_truth_probability(0.5, -1) < 0.5
    assert hint_integration_strength(-1) < hint_integration_strength(0)
    assert hint_integration_strength(0) < hint_integration_strength(1)
    assert conflicted.probability(south) > conflicted.probability(north)
    assert conflicted.probability(north) < hint_only.probability(north)
    assert conflicted.probability(south) > hint_only.probability(south)
    assert aligned.probability(north) > scent_only.probability(north)
    assert aligned_from_neutral.probability(north) > scent_only.probability(north)
    assert conflicted_from_neutral.probability(south) > conflicted_from_neutral.probability(north)


def test_invalid_beliefs_and_truth_probability_fail() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        BeliefMap(2, 2, {Coord(0, 0): 0.5})
    with pytest.raises(ValueError, match="truth probability"):
        update_belief(uniform_belief(2, 2), {}, frozenset(), truth_probability=2)
    with pytest.raises(ValueError, match="feasible"):
        uniform_belief(1, 1, frozenset({Coord(0, 0)}))
