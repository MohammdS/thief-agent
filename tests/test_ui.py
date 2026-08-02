from pathlib import Path

import pytest
from PIL import Image

from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord
from thief_agent.replay.models import ReplayFrame, ReplayResult
from thief_agent.ui.evidence import render_live_png, render_replay_png
from thief_agent.ui.live import controls_enabled, status_text
from thief_agent.ui.model import LiveSnapshot, heat_color


def snapshot() -> LiveSnapshot:
    return LiveSnapshot(
        7, 7, Coord(3, 3), frozenset({Coord(1, 1)}),
        {Coord(2, 2): 0.9}, {Coord(4, 4): 0.8}, 5,
        "I moved north", 518, "connected", "pending", True,
    )


def test_live_snapshot_has_no_objective_police_truth() -> None:
    fields = set(LiveSnapshot.__dataclass_fields__)
    assert "police" not in fields
    assert "police_position" not in fields
    assert "police_action" not in fields
    assert "THIEF TURN" in status_text(snapshot())
    assert controls_enabled(snapshot())
    terminal = snapshot().__class__(
        7, 7, Coord(3, 3), frozenset(), {}, {}, 5, "", 0, "ok", "Verified OK", True,
    )
    assert not controls_enabled(terminal)


def test_heat_color_clamps_extreme_inputs() -> None:
    assert heat_color(0, 0).startswith("#")
    assert heat_color(5, -2) == heat_color(1, 0)


def test_headless_live_and_replay_evidence_are_valid_pngs(tmp_path: Path) -> None:
    live_path, replay_path = tmp_path / "live.png", tmp_path / "replay.png"
    render_live_png(snapshot(), live_path)
    state = BoardState(7, 7, Coord(4, 3), Coord(1, 0))
    result = ReplayResult("Verified OK", (), (ReplayFrame(1, state, "hint", "a" * 64),))
    render_replay_png(result, replay_path)
    for path in (live_path, replay_path):
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.width > 700


def test_live_snapshot_rejects_impossible_local_truth() -> None:
    with pytest.raises(ValueError):
        LiveSnapshot(7, 7, Coord(3, 3), frozenset({Coord(3, 3)}), {}, {}, 0, "", 0, "", "", False)
