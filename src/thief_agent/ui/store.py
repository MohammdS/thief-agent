"""Atomic file boundary between the Thief runtime and optional live GUI."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from thief_agent.domain.types import Coord
from thief_agent.ui.model import LiveSnapshot


class LiveSnapshotStore:
    """Persist only information-safe live presentation fields."""

    def __init__(self, path: Path) -> None:
        """Store the monitored JSON path."""
        self.path = path

    def write(self, snapshot: LiveSnapshot) -> None:
        """Atomically replace the latest live snapshot."""
        payload = {
            "width": snapshot.width,
            "height": snapshot.height,
            "thief": coord(snapshot.thief),
            "known_barriers": [coord(cell) for cell in sorted(snapshot.known_barriers)],
            "police_scent": heatmap(snapshot.police_scent),
            "police_belief": heatmap(snapshot.police_belief),
            "step": snapshot.step,
            "latest_hint": snapshot.latest_hint,
            "tokens_used": snapshot.tokens_used,
            "network_state": snapshot.network_state,
            "audit_state": snapshot.audit_state,
            "local_turn": snapshot.local_turn,
            "subgame": snapshot.subgame,
            "series_size": snapshot.series_size,
            "protocol_state": snapshot.protocol_state,
            "last_event": snapshot.last_event,
            "terminal_reason": snapshot.terminal_reason,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)

    def read(self) -> LiveSnapshot | None:
        """Load the latest complete snapshot when it exists."""
        if not self.path.is_file():
            return None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return LiveSnapshot(
            raw["width"],
            raw["height"],
            parse_coord(raw["thief"]),
            frozenset(parse_coord(cell) for cell in raw["known_barriers"]),
            parse_heatmap(raw["police_scent"]),
            parse_heatmap(raw["police_belief"]),
            raw["step"],
            raw["latest_hint"],
            raw["tokens_used"],
            raw["network_state"],
            raw["audit_state"],
            raw["local_turn"],
            raw.get("subgame", 0),
            raw.get("series_size", 1),
            raw.get("protocol_state", "Waiting for peer"),
            raw.get("last_event", "No protocol event yet"),
            raw.get("terminal_reason"),
        )


def coord(cell: Coord) -> list[int]:
    """Encode one coordinate."""
    return [cell.row, cell.col]


def parse_coord(value: list[int]) -> Coord:
    """Decode one coordinate."""
    return Coord(value[0], value[1])


def heatmap(values: Mapping[Coord, float]) -> list[list[float | int]]:
    """Encode a coordinate mapping in stable row-major order."""
    return [[cell.row, cell.col, value] for cell, value in sorted(values.items())]


def parse_heatmap(values: list[list[float]]) -> dict[Coord, float]:
    """Decode one wire heatmap."""
    return {Coord(int(row), int(col)): value for row, col, value in values}
