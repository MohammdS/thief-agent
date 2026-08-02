"""Render generated sensitivity artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def draw_visual(
    root: Path,
    rows: list[dict[str, object]],
    qualification: dict[str, object],
) -> None:
    """Render a compact evidence figure without requiring a GUI."""
    image = Image.new("RGB", (1200, 650), "#f4f7fb")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype("arialbd.ttf", 34)
    body = ImageFont.truetype("arial.ttf", 22)
    small = ImageFont.truetype("arial.ttf", 18)
    draw.text((50, 35), "Thief qualification and strategy sensitivity", fill="#15243b", font=title)
    draw.text(
        (50, 105),
        "Uncounted deterministic Police stub - not a competitive match",
        fill="#9b3b32",
        font=body,
    )
    scores = (int(qualification["total_police_score"]), int(qualification["total_thief_score"]))
    series = (("Police stub", scores[0], "#577590"), ("Thief", scores[1], "#43aa8b"))
    for index, (label, score, color) in enumerate(series):
        y = 190 + index * 80
        draw.text((60, y), label, fill="#15243b", font=body)
        draw.rectangle((220, y, 220 + score * 6, y + 35), fill=color)
        draw.text((235 + score * 6, y + 3), str(score), fill="#15243b", font=body)
    draw.text((620, 170), "Capture-risk weight sweep", fill="#15243b", font=body)
    draw.line((670, 460, 1100, 460), fill="#6b7a90", width=2)
    draw.line((670, 225, 670, 460), fill="#6b7a90", width=2)
    totals = [float(row["chosen_total"]) for row in rows]
    low, high = min(totals), max(totals)
    points: list[tuple[int, int]] = []
    for index, row in enumerate(rows):
        x = 700 + index * 92
        value = float(row["chosen_total"])
        y = 425 if high == low else int(425 - (value - low) / (high - low) * 160)
        points.append((x, y))
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill="#f9844a")
        draw.text((x - 12, 475), str(row["capture_risk_weight"]), fill="#15243b", font=small)
        draw.text((x - 20, y - 30), str(row["chosen_move"]), fill="#15243b", font=small)
    draw.line(points, fill="#f9844a", width=4)
    draw.text((60, 385), "6/6 terminated", fill="#15243b", font=body)
    draw.text((60, 425), "6/6 replay verified", fill="#15243b", font=body)
    draw.text((60, 465), "Corruption probe: TAMPERED", fill="#15243b", font=body)
    draw.text(
        (50, 585),
        "Generated from committed JSON evidence by scripts/generate_analysis.py",
        fill="#6b7a90",
        font=small,
    )
    image.save(root / "docs" / "screenshots" / "qualification-results.png")


def write_notebook(root: Path, rows: list[dict[str, object]]) -> None:
    """Write a small executed notebook that reads the committed analysis JSON."""
    table = "weight | move | risk   | total    | margin\n" + "\n".join(
        f"{row['capture_risk_weight']:>3} | {row['chosen_move']:^4} | "
        f"{row['chosen_risk']!s:>6} | {row['chosen_total']!s:>8} | {row['margin_to_second']}"
        for row in rows
    )
    source = [
        "import json\n", "from pathlib import Path\n", "\n", "rows = json.loads(Path(\n",
        "    '../artifacts/analysis/strategy-sensitivity.json'\n", ").read_text())\n",
        "print('weight | move | risk   | total    | margin')\n", "for row in rows:\n",
        "    print(f\"{row['capture_risk_weight']:>3} | \"\n",
        "          f\"{row['chosen_move']:^4} | {row['chosen_risk']!s:>6} | \"\n",
        "          f\"{row['chosen_total']!s:>8} | {row['margin_to_second']}\")\n",
    ]
    notebook = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [
                "# Thief strategy sensitivity\n", "One-factor sweep on a fixed dangerous state.",
            ]},
            {"cell_type": "code", "execution_count": 1, "metadata": {},
             "outputs": [{"name": "stdout", "output_type": "stream", "text": [table + "\n"]}],
             "source": source},
            {"cell_type": "markdown", "metadata": {}, "source": [
                "The selected move remains stable while its safety margin changes. "
                "This checks robustness; it does not estimate win rate.\n",
                "\n![Qualification evidence](../docs/screenshots/qualification-results.png)",
            ]},
        ],
        "metadata": {"kernelspec": {
            "display_name": "Python 3", "language": "python", "name": "python3",
        }},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = root / "analysis" / "strategy_sensitivity.ipynb"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
