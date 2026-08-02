import hashlib
import json
from pathlib import Path

from scripts.export_contracts import MODELS
from thief_agent.config.loader import canonical_json_bytes
from thief_agent.crypto.commit_reveal import TurnDisclosure, commitment_for


def test_exported_wire_schemas_match_authoritative_models() -> None:
    for name, model in MODELS.items():
        path = Path("contracts/schemas") / f"{name}.schema.json"
        assert json.loads(path.read_text(encoding="utf-8")) == model.model_json_schema()


def test_commitment_vector_locks_canonical_bytes_and_hash() -> None:
    vector = json.loads(Path("contracts/vectors/commitment.json").read_text(encoding="utf-8"))
    disclosure = TurnDisclosure.model_validate(vector["disclosure"])
    assert canonical_json_bytes(vector["disclosure"]).decode() == vector["canonical_json"]
    assert commitment_for(disclosure) == vector["commitment_sha256"]


def test_scent_model_lock_hash_is_reproducible() -> None:
    vector = json.loads(Path("contracts/vectors/scent-lock.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(canonical_json_bytes(vector["model"])).hexdigest()
    assert digest == vector["lock_sha256"]

