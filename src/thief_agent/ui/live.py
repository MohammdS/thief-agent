"""Tkinter live window rendering only the Thief's local truth."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from thief_agent.ui.canvas import CELL_SIZE, GRID_MARGIN, draw_live_board
from thief_agent.ui.model import LiveSnapshot


class LiveGui:
    """Display live belief and status without objective Police state."""

    def __init__(self, snapshot: LiveSnapshot) -> None:
        """Create the window and render an initial snapshot."""
        self._root = tk.Tk()
        self._root.title("Thief Peer - Local Truth")
        self._root.configure(bg="#0f172a")
        width = snapshot.width * CELL_SIZE + 2 * GRID_MARGIN
        height = snapshot.height * CELL_SIZE + 2 * GRID_MARGIN
        self._canvas = tk.Canvas(
            self._root, width=width, height=height,
            bg="#f8fafc", highlightthickness=0,
        )
        self._canvas.grid(row=0, column=0, padx=18, pady=18)
        self._status = tk.Label(
            self._root, width=38, justify="left", anchor="nw",
            bg="#111827", fg="#e2e8f0", font=("Segoe UI", 11),
        )
        self._status.grid(row=0, column=1, sticky="nsew", padx=(0, 18), pady=18)
        self._control = tk.Button(self._root, text="Local turn ready")
        self._control.grid(row=1, column=0, columnspan=2, pady=(0, 18))
        self.update(snapshot)

    def update(self, snapshot: LiveSnapshot) -> None:
        """Refresh local board and lock controls outside the local turn."""
        draw_live_board(self._canvas, snapshot)
        self._status.configure(text=status_text(snapshot))
        enabled = controls_enabled(snapshot)
        self._control.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def run(self) -> None:
        """Enter the Tk event loop."""
        self._root.mainloop()

    def monitor(
        self, loader: Callable[[], LiveSnapshot | None], interval_ms: int = 250,
    ) -> None:
        """Poll an atomic snapshot source without blocking Tk events."""
        def refresh() -> None:
            snapshot = loader()
            if snapshot is not None:
                self.update(snapshot)
            self._root.after(interval_ms, refresh)

        refresh()


def status_text(snapshot: LiveSnapshot) -> str:
    """Build the live status panel from information-safe fields."""
    turn = "THIEF TURN" if snapshot.local_turn else "WAITING FOR POLICE"
    return "\n".join((
        "LOCAL THIEF VIEW",
        "",
        f"Step: {snapshot.step}",
        f"Turn: {turn}",
        f"Network: {snapshot.network_state}",
        f"Audit: {snapshot.audit_state}",
        f"Tokens: {snapshot.tokens_used}",
        "",
        "Latest Police hint:",
        snapshot.latest_hint or "(silence)",
        "",
        "Red = Police belief",
        "Blue = Police scent",
        "Black = known barrier",
    ))


def controls_enabled(snapshot: LiveSnapshot) -> bool:
    """Enable controls only during a non-terminal local turn."""
    return snapshot.local_turn and snapshot.audit_state not in {"Verified OK", "TAMPERED"}
