import json
from pathlib import Path

from scripts.export_artifact_schemas import MODELS


def test_exported_artifact_schemas_match_models() -> None:
    for name, model in MODELS.items():
        path = Path("contracts/artifacts") / f"{name}.schema.json"
        assert json.loads(path.read_text(encoding="utf-8")) == model.model_json_schema()

