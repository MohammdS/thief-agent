"""Canonical state, audit, and result conversions for live peer play."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Literal

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.config.loader import canonical_json_bytes
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord, RevealedTurn
from thief_agent.crypto.commit_reveal import SealedTurn
from thief_agent.domain.outcome import Outcome
from thief_agent.domain.state import BoardState


def state_sha256(state: BoardState) -> str:
    """Hash objective validator state without exposing it to strategy."""
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


def audit_record(
    sealed: SealedTurn,
    capture_claim: Literal["overlap", "barrier", "imprisonment"] | None = None,
) -> AuditRecord:
    """Pair an immediate public reveal with its final disclosure."""
    action = sealed.disclosure.action
    return AuditRecord(
        reveal=RevealedTurn(
            commitment=sealed.commitment,
            turn_token=sealed.disclosure.turn_token,
            scent_heatmap=sealed.disclosure.scent_heatmap,
            hint=sealed.disclosure.hint,
            barrier=action.barrier if action.kind.value == "barrier" else None,
            capture_claim=capture_claim,
        ),
        disclosure=sealed.disclosure,
    )


def log_record(record: AuditRecord) -> LogRecord:
    """Convert a verified final disclosure to one replay record."""
    return LogRecord(
        payload=record.disclosure.model_dump(mode="json", exclude={"nonce"}),
        nonce=record.disclosure.nonce,
        commit=record.reveal.commitment,
    )


def ordered_audits(records: Iterable[AuditRecord]) -> tuple[AuditRecord, ...]:
    """Order the token sequence as Thief then Police for every numbered step."""
    return tuple(
        sorted(
            records,
            key=lambda item: (
                item.disclosure.step,
                0 if item.disclosure.role.value == "thief" else 1,
            ),
        )
    )


def subgame_digest(state: BoardState, outcome: Outcome, subgame: int) -> str:
    """Hash deterministic terminal facts for independent peer comparison."""
    payload = {
        "subgame": subgame,
        "state_sha256": state_sha256(state),
        "reason": outcome.reason.value,
        "police_score": outcome.police_score,
        "thief_score": outcome.thief_score,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def request_lifetime(config: SharedConfig) -> float:
    """Cover every bounded retry while each attempt retains an expiry."""
    network = config.network
    return (
        network.response_timeout_seconds * (network.retries + 1)
        + network.retry_delay_seconds * network.retries
    )
