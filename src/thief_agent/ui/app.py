"""SDK-facing launcher for the live Thief local-truth monitor."""

from __future__ import annotations

from pathlib import Path

from thief_agent.config import load_shared_config
from thief_agent.domain.types import Coord
from thief_agent.ui.live import LiveGui
from thief_agent.ui.model import LiveSnapshot
from thief_agent.ui.store import LiveSnapshotStore


def run_live_gui(config_path: Path, state_path: Path) -> None:
    """Open a monitor that updates whenever the peer publishes safe state."""
    config = load_shared_config(config_path)
    start = config.board.thief_start
    initial = LiveSnapshot(
        config.board.width,
        config.board.height,
        Coord(start.row, start.col),
        frozenset(),
        {},
        {},
        0,
        "",
        0,
        "waiting for peer",
        "pending",
        False,
        0,
        config.series.subgames,
        "Waiting for peer",
        "No protocol event yet",
    )
    gui, store = LiveGui(initial), LiveSnapshotStore(state_path)
    gui.monitor(store.read)
    gui.run()
