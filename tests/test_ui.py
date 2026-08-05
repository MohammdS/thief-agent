from pathlib import Path

import pytest
from PIL import Image

from thief_agent.domain.outcome import Outcome, TerminalReason
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord
from thief_agent.replay.models import ReplayFrame, ReplayResult
from thief_agent.runtime.presentation import verified_event
from thief_agent.ui.evidence import render_live_png, render_replay_png
from thief_agent.ui.live import controls_enabled, phase_banner, status_text
from thief_agent.ui.model import LiveSnapshot, heat_color, heat_scale
from thief_agent.ui.store import LiveSnapshotStore


def snapshot() -> LiveSnapshot:
    return LiveSnapshot(
        7,
        7,
        Coord(3, 3),
        frozenset({Coord(1, 1)}),
        {Coord(2, 2): 0.9},
        {Coord(4, 4): 0.8},
        5,
        "I moved north",
        518,
        "connected",
        "pending",
        True,
        2,
        6,
        "Thief turn ready",
        "Police reveal verified; turn token received",
    )


def test_live_snapshot_has_no_objective_police_truth() -> None:
    fields = set(LiveSnapshot.__dataclass_fields__)
    assert "police" not in fields
    assert "police_position" not in fields
    assert "police_action" not in fields
    assert "Turn token: LOCAL (Thief)" in status_text(snapshot())
    assert "Subgame: 2/6" in status_text(snapshot())
    assert "BELIEF MAP" in status_text(snapshot())
    assert "Raw scent = hidden" in status_text(snapshot())
    assert "BELIEF MAP + SCENT OVERLAY" in status_text(snapshot(), show_scent=True)
    assert "Blue = raw Police scent" in status_text(snapshot(), show_scent=True)
    assert controls_enabled(snapshot())
    terminal = snapshot().__class__(
        7,
        7,
        Coord(3, 3),
        frozenset(),
        {},
        {},
        5,
        "",
        0,
        "ok",
        "Verified OK",
        True,
    )
    assert not controls_enabled(terminal)
    assert phase_banner(terminal) == "FINISHED - FINAL AUDIT VERIFIED"


def test_heat_color_clamps_extreme_inputs() -> None:
    assert heat_color(0, 0) == "#f8fafc"
    assert heat_color(5, -2) == heat_color(1, 0)
    belief, scent, overlap = heat_color(1, 0), heat_color(0, 1), heat_color(1, 1)
    assert belief == "#ef4444"
    assert scent == "#2563eb"
    assert overlap not in {belief, scent}
    assert heat_scale({Coord(0, 0): 0.1, Coord(0, 1): 4.2}) == 4.2


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


def test_live_snapshot_allows_verified_barrier_capture() -> None:
    captured = LiveSnapshot(
        7,
        7,
        Coord(3, 3),
        frozenset({Coord(3, 3)}),
        {},
        {},
        8,
        "",
        0,
        "connected",
        "in progress",
        False,
        1,
        6,
        "Final audit",
        "Public barrier capture claimed; exchanging secrets",
        "capture",
    )
    assert captured.terminal_reason == "capture"
    assert "Outcome reason: capture" in status_text(captured)


def test_live_snapshot_store_round_trips_without_objective_police(
    tmp_path: Path,
) -> None:
    path = tmp_path / "live.json"
    store = LiveSnapshotStore(path)
    store.write(snapshot())
    assert store.read() == snapshot()
    assert '"police"' not in path.read_text(encoding="utf-8")
    assert '"protocol_state": "Thief turn ready"' in path.read_text(encoding="utf-8")


def test_verified_event_preserves_public_capture_mechanism() -> None:
    state = BoardState(
        7, 7, Coord(1, 1), Coord(2, 1), frozenset({Coord(1, 1)}), 1, 32,
    )
    outcome = Outcome(TerminalReason.CAPTURE, 20, 5)
    assert verified_event(state, outcome) == (
        "Verified barrier capture claim: Police 20, Thief 5"
    )
