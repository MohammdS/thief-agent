"""Atomic JSON checkpoints for crash-safe runtime recovery."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class CheckpointStore:
    """Persist checkpoints using fsync and atomic replacement."""

    def __init__(self, path: Path) -> None:
        """Store the explicit checkpoint path."""
        self.path = path

    def save(self, payload: dict[str, Any]) -> None:
        """Atomically replace the checkpoint with sorted UTF-8 JSON."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(
                    payload,
                    stream,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def load(self) -> dict[str, Any] | None:
        """Return a valid object checkpoint or None when absent."""
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("checkpoint root must be an object")
        return payload
