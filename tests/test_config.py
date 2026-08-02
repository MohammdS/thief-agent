import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from thief_agent.config import (
    canonical_json_bytes,
    config_sha256,
    load_local_config,
    load_shared_config,
)


def config_data() -> dict[str, object]:
    return json.loads(Path("config/game.json").read_text(encoding="utf-8"))


def test_assignment_config_is_strict_and_hashable() -> None:
    config = load_shared_config(Path("config/game.json"))
    assert config.scent.center == 0.9
    assert config.series.subgames == 6
    assert len(config_sha256(config)) == 64


def test_canonical_json_is_order_independent() -> None:
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("board", "width"), 6),
        (("barriers", "police_capacity"), 13),
        (("scent", "center"), 0.8),
        (("scoring", "capture", "police"), 19),
        (("network", "queue_depth"), 99),
    ],
)
def test_fixed_or_minimum_rules_reject_reduction(path: tuple[str, ...], value: object) -> None:
    data = config_data()
    target = data
    for key in path[:-1]:
        target = target[key]  # type: ignore[index,assignment]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError):
        load_from_data(data)


def test_counted_series_requires_six_subgames() -> None:
    data = config_data()
    data["counted"] = True
    data["series"]["subgames"] = 1  # type: ignore[index]
    with pytest.raises(ValidationError, match="exactly six"):
        load_from_data(data)


def test_unknown_shared_field_is_rejected() -> None:
    data = config_data()
    data["secret_position"] = [1, 2]
    with pytest.raises(ValidationError):
        load_from_data(data)


def test_private_toml_loads_as_thief_only() -> None:
    config = load_local_config(Path("config/game.toml.example"))
    assert config.identity.role == "thief"
    assert config.reporting.mode == "dry-run"


def load_from_data(data: dict[str, object]) -> object:
    path = Path("config/matches/test-invalid.json")
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        return load_shared_config(path)
    finally:
        path.unlink()

