"""Generate deterministic local-truth and replay PNG evidence."""

from __future__ import annotations

from pathlib import Path

from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord
from thief_agent.replay.models import ReplayFrame, ReplayResult
from thief_agent.ui.evidence import render_live_png, render_replay_png
from thief_agent.ui.model import LiveSnapshot


def main() -> int:
    """Write three screenshots for README and replay evidence."""
    belief = {
        Coord(1, 1): 0.10,
        Coord(1, 2): 0.18,
        Coord(2, 1): 0.24,
        Coord(2, 2): 0.32,
        Coord(3, 2): 0.16,
    }
    scent = {Coord(1, 1): 0.9, Coord(1, 2): 0.62, Coord(2, 1): 0.62}
    live = LiveSnapshot(
        7,
        7,
        Coord(4, 4),
        frozenset({Coord(2, 4), Coord(3, 4)}),
        scent,
        belief,
        12,
        "I moved north through open ground",
        518,
        "FastMCP connected",
        "commit acknowledged",
        True,
        1,
        6,
        "Thief turn ready",
        "Police reveal verified; turn token received",
    )
    output = Path("docs/screenshots")
    render_live_png(live, output / "thief-live-local-truth.png")
    state = BoardState(
        7,
        7,
        Coord(4, 4),
        Coord(2, 2),
        frozenset({Coord(2, 4), Coord(3, 4)}),
        2,
        12,
    )
    frame = ReplayFrame(12, state, live.latest_hint, "a" * 64)
    render_replay_png(
        ReplayResult("Verified OK", (), (frame,)),
        output / "thief-replay-verified.png",
    )
    render_replay_png(
        ReplayResult("TAMPERED", ("record 11: commitment mismatch",), (frame,)),
        output / "thief-replay-tampered.png",
    )
    print("Generated local-truth, verified, and tampered GUI evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
