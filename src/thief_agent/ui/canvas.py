"""Tkinter canvas rendering for local truth and belief."""

from __future__ import annotations

import tkinter as tk

from thief_agent.domain.types import Coord
from thief_agent.ui.model import (
    BARRIER_COLOR,
    THIEF_COLOR,
    LiveSnapshot,
    heat_color,
    heat_scale,
)

CELL_SIZE = 62
GRID_MARGIN = 28


def draw_live_board(
    canvas: tk.Canvas, snapshot: LiveSnapshot, show_scent: bool = False,
) -> None:
    """Draw the belief map, optionally with a raw scent overlay."""
    canvas.delete("all")
    belief_scale = heat_scale(snapshot.police_belief)
    scent_scale = heat_scale(snapshot.police_scent)
    draw_coordinates(canvas, snapshot.width, snapshot.height)
    for row in range(snapshot.height):
        for col in range(snapshot.width):
            cell = Coord(row, col)
            x0, y0 = GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN + row * CELL_SIZE
            fill = heat_color(
                snapshot.police_belief.get(cell, 0.0) / belief_scale,
                snapshot.police_scent.get(cell, 0.0) / scent_scale if show_scent else 0.0,
            )
            canvas.create_rectangle(
                x0,
                y0,
                x0 + CELL_SIZE,
                y0 + CELL_SIZE,
                fill=fill,
                outline="#334155",
                width=1,
            )
            if cell in snapshot.known_barriers:
                canvas.create_rectangle(
                    x0 + 12,
                    y0 + 12,
                    x0 + CELL_SIZE - 12,
                    y0 + CELL_SIZE - 12,
                    fill=BARRIER_COLOR,
                    outline="#020617",
                )
    draw_agent(canvas, snapshot.thief, THIEF_COLOR, "T")


def draw_coordinates(canvas: tk.Canvas, width: int, height: int) -> None:
    """Label zero-based columns and rows around the board."""
    for col in range(width):
        canvas.create_text(
            GRID_MARGIN + col * CELL_SIZE + CELL_SIZE / 2,
            13,
            text=str(col),
            fill="#475569",
            font=("Segoe UI", 10, "bold"),
        )
    for row in range(height):
        canvas.create_text(
            13,
            GRID_MARGIN + row * CELL_SIZE + CELL_SIZE / 2,
            text=str(row),
            fill="#475569",
            font=("Segoe UI", 10, "bold"),
        )


def draw_agent(canvas: tk.Canvas, cell: Coord, color: str, label: str) -> None:
    """Draw one labeled circular agent marker."""
    x0 = GRID_MARGIN + cell.col * CELL_SIZE + 10
    y0 = GRID_MARGIN + cell.row * CELL_SIZE + 10
    canvas.create_oval(
        x0,
        y0,
        x0 + CELL_SIZE - 20,
        y0 + CELL_SIZE - 20,
        fill=color,
        outline="#ffffff",
        width=2,
    )
    canvas.create_text(
        x0 + (CELL_SIZE - 20) / 2,
        y0 + (CELL_SIZE - 20) / 2,
        text=label,
        fill="white",
        font=("Segoe UI", 13, "bold"),
    )
