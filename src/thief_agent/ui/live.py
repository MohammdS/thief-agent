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
        self._snapshot = snapshot
        self._show_scent = tk.BooleanVar(value=False)
        width = snapshot.width * CELL_SIZE + 2 * GRID_MARGIN
        height = snapshot.height * CELL_SIZE + 2 * GRID_MARGIN
        self._canvas = tk.Canvas(
            self._root,
            width=width,
            height=height,
            bg="#f8fafc",
            highlightthickness=0,
        )
        self._canvas.grid(row=0, column=0, padx=18, pady=18)
        self._status = tk.Label(
            self._root,
            width=45,
            wraplength=370,
            justify="left",
            anchor="nw",
            bg="#111827",
            fg="#e2e8f0",
            font=("Segoe UI", 11),
        )
        self._status.grid(row=0, column=1, sticky="nsew", padx=(0, 18), pady=18)
        self._scent_toggle = tk.Checkbutton(
            self._root,
            text="Show scent overlay",
            variable=self._show_scent,
            command=self._toggle_scent,
            bg="#0f172a",
            fg="#e2e8f0",
            activebackground="#0f172a",
            activeforeground="#ffffff",
            selectcolor="#334155",
            anchor="w",
        )
        self._scent_toggle.grid(row=1, column=1, sticky="w", padx=(0, 18), pady=(0, 8))
        self._phase = tk.Label(
            self._root,
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
            bg="#1e293b",
            fg="#f8fafc",
        )
        self._phase.grid(row=2, column=0, columnspan=2, pady=(0, 18))
        self.update(snapshot)

    def update(self, snapshot: LiveSnapshot) -> None:
        """Refresh local board and lock controls outside the local turn."""
        self._snapshot = snapshot
        show_scent = bool(self._show_scent.get())
        draw_live_board(self._canvas, snapshot, show_scent=show_scent)
        self._status.configure(text=status_text(snapshot, show_scent=show_scent))
        self._phase.configure(
            text=phase_banner(snapshot),
            fg=phase_color(snapshot),
        )

    def _toggle_scent(self) -> None:
        """Redraw the current posterior with or without raw scent."""
        self.update(self._snapshot)

    def run(self) -> None:
        """Enter the Tk event loop."""
        self._root.mainloop()

    def monitor(
        self,
        loader: Callable[[], LiveSnapshot | None],
        interval_ms: int = 250,
    ) -> None:
        """Poll an atomic snapshot source without blocking Tk events."""

        def refresh() -> None:
            snapshot = loader()
            if snapshot is not None:
                self.update(snapshot)
            self._root.after(interval_ms, refresh)

        refresh()


def status_text(snapshot: LiveSnapshot, show_scent: bool = False) -> str:
    """Build the live status panel from information-safe fields."""
    token = "LOCAL (Thief)" if snapshot.local_turn else "OPPONENT / LOCKED"
    series = f"{snapshot.subgame}/{snapshot.series_size}" if snapshot.subgame else "not started"
    lines = [
        "LOCAL THIEF VIEW",
        "",
        f"Subgame: {series}",
        f"Step: {snapshot.step}",
        f"Protocol: {snapshot.protocol_state}",
        f"Turn token: {token}",
        f"Network: {snapshot.network_state}",
        f"Audit: {snapshot.audit_state}",
        f"Tokens: {snapshot.tokens_used}",
        "",
        "Last protocol event:",
        snapshot.last_event,
    ]
    if snapshot.terminal_reason:
        lines.extend(("", f"Outcome reason: {snapshot.terminal_reason.replace('_', ' ')}"))
    lines.extend(
        (
            "",
            "Latest Police hint:",
            snapshot.latest_hint or "(silence)",
            "",
            "BELIEF MAP" if not show_scent else "BELIEF MAP + SCENT OVERLAY",
            "Red = final Police belief (scent + hint integrated)",
            "Raw scent = hidden; use the toggle to show it" if not show_scent
            else "Blue = raw Police scent; purple = overlap",
            "Green T = local Thief position",
            "Black = known barrier",
        )
    )
    return "\n".join(lines)


def controls_enabled(snapshot: LiveSnapshot) -> bool:
    """Enable controls only during a non-terminal local turn."""
    return snapshot.local_turn and snapshot.audit_state not in {"Verified OK", "TAMPERED"}


def phase_banner(snapshot: LiveSnapshot) -> str:
    """Summarize the current autonomous phase below the board."""
    if snapshot.audit_state == "Verified OK":
        return "FINISHED - FINAL AUDIT VERIFIED"
    if snapshot.audit_state == "TAMPERED":
        return "STOPPED - AUDIT TAMPER DETECTED"
    if snapshot.audit_state == "in progress":
        return "PLAY STOPPED - FINAL AUDIT IN PROGRESS"
    return "AUTONOMOUS THIEF TURN" if snapshot.local_turn else "WAITING FOR POLICE TOKEN"


def phase_color(snapshot: LiveSnapshot) -> str:
    """Color the phase banner without reusing heatmap colors."""
    if snapshot.audit_state == "Verified OK":
        return "#22c55e"
    if snapshot.audit_state == "TAMPERED":
        return "#f87171"
    if snapshot.audit_state == "in progress":
        return "#fbbf24"
    return "#f8fafc"
