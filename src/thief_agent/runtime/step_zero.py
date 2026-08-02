"""Step-zero declaration record for live match logs."""

from __future__ import annotations

import hashlib
import secrets

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.config.loader import canonical_json_bytes


def step_zero(subgame: int, commit: str, model: str, budget: int) -> LogRecord:
    """Record exact code and model identity before the first move."""
    payload = {
        "step": 0,
        "type": "system_spec",
        "role": "thief",
        "sub_game_number": subgame,
        "git_commit": commit,
        "model": model,
        "token_budget": budget,
    }
    nonce = secrets.token_hex(16)
    digest = hashlib.sha256(canonical_json_bytes(payload | {"nonce": nonce})).hexdigest()
    return LogRecord(payload=payload, nonce=nonce, commit=digest)
