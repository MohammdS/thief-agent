from pathlib import Path

import pytest

from thief_agent.config import load_shared_config
from thief_agent.domain.outcome import TerminalReason, evaluate_outcome, score_outcome
from thief_agent.domain.scent import advance_scent, emission
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord


def game_config():
    return load_shared_config(Path("config/game.json"))


def test_fixed_kernel_and_board_clipping() -> None:
    centered = emission(Coord(3, 3), 7, 7)
    assert centered[Coord(3, 3)] == 0.90
    assert centered[Coord(1, 1)] == 0.04
    assert len(centered) == 25
    assert len(emission(Coord(0, 0), 7, 7)) == 9


def test_decay_and_reemission_follow_locked_formula() -> None:
    center = Coord(3, 3)
    first = advance_scent({}, center, 7, 7)
    second = advance_scent(first, center, 7, 7)
    assert first[center] == 0.9
    assert second[center] == pytest.approx(1.71)
    moved = advance_scent(first, Coord(6, 6), 7, 7)
    assert moved[center] == pytest.approx(0.81)


def test_invalid_decay_is_rejected() -> None:
    with pytest.raises(ValueError):
        advance_scent({}, Coord(0, 0), 7, 7, decay=1.1)


def test_capture_imprisonment_and_survival_scores() -> None:
    config = game_config()
    captured = BoardState(7, 7, Coord(2, 2), Coord(2, 2))
    assert evaluate_outcome(captured, config) == score_outcome(TerminalReason.CAPTURE, config)
    blocked = frozenset({Coord(2, 3), Coord(4, 3), Coord(3, 2), Coord(3, 4)})
    prison = BoardState(7, 7, Coord(3, 3), Coord(0, 0), blocked, 4)
    assert evaluate_outcome(prison, config).reason is TerminalReason.IMPRISONMENT  # type: ignore[union-attr]
    survived = BoardState(7, 7, Coord(3, 3), Coord(0, 0), step=35)
    outcome = evaluate_outcome(survived, config)
    assert (outcome.police_score, outcome.thief_score) == (5, 10)  # type: ignore[union-attr]


def test_nonterminal_and_all_fixed_score_pairs() -> None:
    config = game_config()
    state = BoardState(7, 7, Coord(3, 3), Coord(0, 0))
    assert evaluate_outcome(state, config) is None
    assert score_outcome(TerminalReason.TIE, config).thief_score == 2
    assert score_outcome(TerminalReason.TECHNICAL_LOSS, config).police_score == 0

