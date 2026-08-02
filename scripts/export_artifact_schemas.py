"""Export deterministic JSON Schemas for all mandatory assignment artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from thief_agent.artifacts.agreed_config import AgreedConfigArtifact
from thief_agent.artifacts.declaration import DeclarationArtifact
from thief_agent.artifacts.match_log import MatchLogArtifact
from thief_agent.artifacts.result import ResultArtifact

MODELS = {
    "declaration": DeclarationArtifact,
    "config": AgreedConfigArtifact,
    "log": MatchLogArtifact,
    "result": ResultArtifact,
}


def main() -> int:
    """Write one stable schema file per mandatory artifact."""
    output = Path("contracts/artifacts")
    output.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        (output / f"{name}.schema.json").write_text(schema, encoding="utf-8")
    print(f"Exported {len(MODELS)} artifact schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

