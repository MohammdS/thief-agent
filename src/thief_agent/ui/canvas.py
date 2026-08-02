"""Tkinter canvas rendering for local truth and belief."""

from __future__ import annotations

import tkinter as tk

from thief_agent.domain.types import Coord
from thief_agent.ui.model import LiveSnapshot, heat_color

CELL_SIZE = 62
GRID_MARGIN = 28


def draw_live_board(canvas: tk.Canvas, snapshot: LiveSnapshot) -> None:
    """Draw local Thief truth without any objective Police marker."""
    canvas.delete("all")
    for row in range(snapshot.height):
        for col in range(snapshot.width):
            cell = Coord(row, col)
            x0, y0 = GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN + row * CELL_SIZE
            fill = heat_color(
                snapshot.police_belief.get(cell, 0.0),
                snapshot.police_scent.get(cell, 0.0),
            )
            canvas.create_rectangle(
                x0, y0, x0 + CELL_SIZE, y0 + CELL_SIZE,
                fill=fill, outline="#334155", width=1,
            )
            if cell in snapshot.known_barriers:
                canvas.create_rectangle(
                    x0 + 12, y0 + 12, x0 + CELL_SIZE - 12, y0 + CELL_SIZE - 12,
                    fill="#172033", outline="#020617",
                )
    draw_agent(canvas, snapshot.thief, "#16a34a", "T")


def draw_agent(canvas: tk.Canvas, cell: Coord, color: str, label: str) -> None:
    """Draw one labeled circular agent marker."""
    x0 = GRID_MARGIN + cell.col * CELL_SIZE + 10
    y0 = GRID_MARGIN + cell.row * CELL_SIZE + 10
    canvas.create_oval(
        x0, y0, x0 + CELL_SIZE - 20, y0 + CELL_SIZE - 20,
        fill=color, outline="#ffffff", width=2,
    )
    canvas.create_text(
        x0 + (CELL_SIZE - 20) / 2,
        y0 + (CELL_SIZE - 20) / 2,
        text=label,
        fill="white",
        font=("Segoe UI", 13, "bold"),
    )

