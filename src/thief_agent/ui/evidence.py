"""Headless PNG evidence rendering from the same safe presentation models."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from thief_agent.domain.types import Coord
from thief_agent.replay.models import ReplayResult
from thief_agent.ui.model import LiveSnapshot, heat_color

CELL, MARGIN, SIDE = 62, 36, 360


def render_live_png(snapshot: LiveSnapshot, path: Path) -> None:
    """Render a polished local-truth screenshot without a display server."""
    image, draw = base_image(snapshot.width, snapshot.height, "THIEF PEER - LOCAL TRUTH")
    for row in range(snapshot.height):
        for col in range(snapshot.width):
            cell = Coord(row, col)
            fill = heat_color(
                snapshot.police_belief.get(cell, 0), snapshot.police_scent.get(cell, 0),
            )
            draw_cell(draw, cell, fill)
            if cell in snapshot.known_barriers:
                draw_marker(draw, cell, "#111827", "B")
    draw_marker(draw, snapshot.thief, "#16a34a", "T")
    x = MARGIN + snapshot.width * CELL + 28
    lines = [
        f"Step {snapshot.step}",
        "THIEF TURN" if snapshot.local_turn else "WAITING FOR POLICE",
        f"Network: {snapshot.network_state}",
        f"Audit: {snapshot.audit_state}",
        f"Tokens: {snapshot.tokens_used}",
        "", "Latest Police hint:", snapshot.latest_hint or "(silence)",
        "", "Red: Police belief", "Blue: Police scent", "Black: known barrier",
    ]
    draw.multiline_text((x, 88), "\n".join(lines), fill="#e2e8f0", spacing=10)
    save(image, path)


def render_replay_png(result: ReplayResult, path: Path) -> None:
    """Render a post-match objective frame with exact audit status."""
    state = result.frames[-1].state if result.frames else None
    width, height = (state.width, state.height) if state else (7, 7)
    image, draw = base_image(width, height, "POST-MATCH AUDIT REPLAY")
    if state:
        for row in range(height):
            for col in range(width):
                draw_cell(draw, Coord(row, col), "#e2e8f0")
        for barrier in state.barriers:
            draw_marker(draw, barrier, "#111827", "B")
        draw_marker(draw, state.thief, "#16a34a", "T")
        draw_marker(draw, state.police, "#dc2626", "P")
    x = MARGIN + width * CELL + 28
    color = "#22c55e" if result.status == "Verified OK" else "#ef4444"
    draw.text((x, 92), result.status, fill=color, font=ImageFont.load_default(size=22))
    draw.multiline_text(
        (x, 140),
        f"Verified frames: {len(result.frames)}\nFailures: {len(result.failures)}\n\n"
        + "\n".join(result.failures[:5]),
        fill="#e2e8f0", spacing=8,
    )
    save(image, path)


def base_image(width: int, height: int, title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create a shared dark evidence canvas."""
    size = (MARGIN * 2 + width * CELL + SIDE, MARGIN * 2 + height * CELL + 55)
    image = Image.new("RGB", size, "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.text((MARGIN, 18), title, fill="#f8fafc", font=ImageFont.load_default(size=18))
    return image, draw


def draw_cell(draw: ImageDraw.ImageDraw, cell: Coord, fill: str) -> None:
    """Draw one grid cell."""
    x0, y0 = MARGIN + cell.col * CELL, MARGIN + 42 + cell.row * CELL
    draw.rectangle((x0, y0, x0 + CELL, y0 + CELL), fill=fill, outline="#334155")


def draw_marker(draw: ImageDraw.ImageDraw, cell: Coord, color: str, label: str) -> None:
    """Draw one circular labeled marker."""
    x0, y0 = MARGIN + cell.col * CELL + 12, MARGIN + 54 + cell.row * CELL
    draw.ellipse((x0, y0, x0 + CELL - 24, y0 + CELL - 24), fill=color, outline="white")
    draw.text((x0 + 14, y0 + 11), label, fill="white")


def save(image: Image.Image, path: Path) -> None:
    """Create the output directory and save an optimized PNG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
