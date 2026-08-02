"""Qualification-only state hashing and log record conversion."""

from __future__ import annotations

import hashlib

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.config.loader import canonical_json_bytes
from thief_agent.crypto.commit_reveal import SealedTurn
from thief_agent.domain.state import BoardState


def board_sha256(state: BoardState) -> str:
    """Hash objective qualification state without exposing it to strategy."""
    payload = {
        "width": state.width,
        "height": state.height,
        "thief": [state.thief.row, state.thief.col],
        "police": [state.police.row, state.police.col],
        "barriers": [[cell.row, cell.col] for cell in sorted(state.barriers)],
        "barriers_used": state.barriers_used,
        "step": state.step,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sealed_record(sealed: SealedTurn) -> LogRecord:
    """Convert a sealed turn to the mandatory final-audit log record shape."""
    payload = sealed.disclosure.model_dump(mode="json", exclude={"nonce"})
    return LogRecord(
        payload=payload,
        nonce=sealed.disclosure.nonce,
        commit=sealed.commitment,
    )

