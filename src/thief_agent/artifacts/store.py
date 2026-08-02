"""Safe names and atomic writes for mandatory JSON artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from thief_agent.reliability.checkpoint import CheckpointStore

ArtifactKind = Literal["declaration", "config", "log", "result"]
SAFE_GAME_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactStore:
    """Write validated models under exact assignment filenames."""

    def __init__(self, root: Path) -> None:
        """Store an explicit artifact root."""
        self.root = root

    def path_for(self, kind: ArtifactKind, game_id: str, subgame: int | None = None) -> Path:
        """Return a traversal-safe exact artifact path."""
        if not SAFE_GAME_ID.fullmatch(game_id):
            raise ValueError("game_id is unsafe for artifact filenames")
        if kind in {"config", "log"}:
            if subgame is None or subgame < 1:
                raise ValueError("per-subgame artifact requires a positive subgame")
            filename = f"{kind}_{game_id}_g{subgame:02d}.json"
        else:
            filename = f"{kind}_{game_id}.json"
        return self.root / filename

    def write(
        self,
        kind: ArtifactKind,
        game_id: str,
        document: BaseModel,
        subgame: int | None = None,
    ) -> Path:
        """Validate JSON serialization and atomically write one document."""
        payload = document.model_dump(mode="json", by_alias=True)
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
        path = self.path_for(kind, game_id, subgame)
        CheckpointStore(path).save(payload)
        return path

