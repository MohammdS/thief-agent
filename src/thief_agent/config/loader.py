"""Load and hash strict shared JSON configuration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from thief_agent.config.models import SharedConfig


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible data as sorted compact UTF-8 bytes."""
    if isinstance(value, BaseException):
        raise TypeError("exceptions are not JSON values")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_shared_config(path: Path) -> SharedConfig:
    """Read a UTF-8 JSON file and reject invalid or unknown fields."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SharedConfig.model_validate(raw)


def config_sha256(config: SharedConfig) -> str:
    """Return the canonical SHA-256 identity of a validated config."""
    payload = config.model_dump(mode="json")
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

