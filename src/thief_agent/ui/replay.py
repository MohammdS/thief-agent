"""Tkinter post-match replay window with objective reconstruction."""

from __future__ import annotations

import tkinter as tk

from thief_agent.replay.models import ReplayResult
from thief_agent.ui.canvas import CELL_SIZE, GRID_MARGIN, draw_agent


class ReplayGui:
    """Display full objective state only after final audit."""

    def __init__(self, result: ReplayResult) -> None:
        """Create the window and initial verified/tampered banner."""
        self._result, self._index = result, 0
        self._root = tk.Tk()
        self._root.title("Thief Peer - Verified Replay")
        self._banner = tk.Label(
            self._root,
            text=result.status,
            font=("Segoe UI", 18, "bold"),
            fg="#15803d" if result.status == "Verified OK" else "#b91c1c",
        )
        self._banner.pack(pady=10)
        self._canvas = tk.Canvas(self._root, width=500, height=500, bg="#f8fafc")
        self._canvas.pack(padx=12, pady=8)
        tk.Button(self._root, text="Next", command=self.next_frame).pack(pady=8)
        self.render()

    def next_frame(self) -> None:
        """Advance by one available replay frame."""
        if self._result.frames:
            self._index = min(self._index + 1, len(self._result.frames) - 1)
            self.render()

    def render(self) -> None:
        """Draw barriers and both objective positions for the selected frame."""
        self._canvas.delete("all")
        if not self._result.frames:
            self._canvas.create_text(250, 250, text="No verified frames")
            return
        frame = self._result.frames[self._index]
        for row in range(frame.state.height):
            for col in range(frame.state.width):
                x0, y0 = GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN + row * CELL_SIZE
                self._canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + CELL_SIZE,
                    y0 + CELL_SIZE,
                    outline="#334155",
                    fill="#e2e8f0",
                )
        for barrier in frame.state.barriers:
            x0 = GRID_MARGIN + barrier.col * CELL_SIZE + 12
            y0 = GRID_MARGIN + barrier.row * CELL_SIZE + 12
            self._canvas.create_rectangle(
                x0,
                y0,
                x0 + CELL_SIZE - 24,
                y0 + CELL_SIZE - 24,
                fill="#111827",
            )
        draw_agent(self._canvas, frame.state.thief, "#16a34a", "T")
        draw_agent(self._canvas, frame.state.police, "#dc2626", "P")

    def run(self) -> None:
        """Enter the replay Tk event loop."""
        self._root.mainloop()
