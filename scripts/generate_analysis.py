"""Generate reproducible strategy sensitivity and qualification visuals."""

from __future__ import annotations

import json
from pathlib import Path

from analysis_outputs import draw_visual, write_notebook

from thief_agent.domain.types import Coord
from thief_agent.strategy.evasion import EvasionStrategy, EvasionWeights
from thief_agent.strategy.observation import ThiefObservation

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = (20, 35, 50, 65, 80)


def sensitivity() -> list[dict[str, object]]:
    """Evaluate the capture-risk coefficient on one fixed dangerous state."""
    observation = ThiefObservation(
        width=7,
        height=7,
        thief=Coord(3, 3),
        known_barriers=frozenset({Coord(4, 3), Coord(3, 2)}),
        police_scent={},
        police_belief={Coord(2, 3): 0.7, Coord(2, 4): 0.3},
        step=8,
        recent_positions=(Coord(3, 4),),
    )
    rows: list[dict[str, object]] = []
    for weight in WEIGHTS:
        evaluations = EvasionStrategy(EvasionWeights(capture_risk=weight)).evaluate_moves(
            observation,
        )
        ordered = sorted(evaluations, key=lambda item: item.total, reverse=True)
        best = ordered[0]
        rows.append(
            {
                "capture_risk_weight": weight,
                "chosen_move": best.move.value,
                "chosen_risk": round(best.capture_risk, 4),
                "chosen_total": round(best.total, 4),
                "margin_to_second": round(best.total - ordered[1].total, 4),
            },
        )
    return rows


def main() -> int:
    """Generate all analysis artifacts from deterministic inputs."""
    rows = sensitivity()
    analysis = ROOT / "artifacts" / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / "strategy-sensitivity.json").write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )
    qualification = json.loads(
        (ROOT / "artifacts" / "qualification" / "qualification-summary.json").read_text(),
    )
    draw_visual(ROOT, rows, qualification)
    write_notebook(ROOT, rows)
    print("Generated sensitivity JSON, executed notebook, and qualification visual.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
