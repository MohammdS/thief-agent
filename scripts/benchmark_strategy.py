"""Run deterministic evasion scenarios and save transparent score evidence."""

from __future__ import annotations

import json
from pathlib import Path

from thief_agent.belief.model import uniform_belief
from thief_agent.domain.types import Coord
from thief_agent.strategy.evasion import EvasionStrategy
from thief_agent.strategy.observation import ThiefObservation


def scenarios() -> list[ThiefObservation]:
    """Return representative open, corner, wall, and revisit scenarios."""
    belief = uniform_belief(7, 7).probabilities
    return [
        ThiefObservation(7, 7, Coord(3, 3), frozenset(), {}, belief, 1),
        ThiefObservation(7, 7, Coord(0, 0), frozenset(), {}, belief, 2),
        ThiefObservation(7, 7, Coord(3, 3), frozenset({Coord(3, 2)}), {}, belief, 3),
        ThiefObservation(7, 7, Coord(6, 6), frozenset(), {}, belief, 4, (Coord(6, 5),)),
    ]


def main() -> int:
    """Evaluate scenarios and write a reproducible JSON artifact."""
    strategy = EvasionStrategy()
    rows = []
    for index, observation in enumerate(scenarios(), start=1):
        evaluations = strategy.evaluate_moves(observation)
        rows.append({
            "scenario": index,
            "chosen_move": strategy.choose_move(observation).value,
            "legal_moves": [item.move.value for item in evaluations],
            "best_score": max(item.total for item in evaluations),
        })
    output = Path("artifacts/analysis/strategy-benchmark.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} deterministic benchmark scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

