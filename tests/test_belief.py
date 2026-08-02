import pytest

from thief_agent.belief.model import BeliefMap, parse_direction, uniform_belief, update_belief
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


def test_ambiguous_hint_is_ignored() -> None:
    prior = uniform_belief(3, 3)
    assert parse_direction("north then south") is None
    assert update_belief(prior, {}, frozenset(), "no clue").probabilities == prior.probabilities


def test_invalid_beliefs_and_truth_probability_fail() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        BeliefMap(2, 2, {Coord(0, 0): 0.5})
    with pytest.raises(ValueError, match="truth probability"):
        update_belief(uniform_belief(2, 2), {}, frozenset(), truth_probability=2)
    with pytest.raises(ValueError, match="feasible"):
        uniform_belief(1, 1, frozenset({Coord(0, 0)}))

