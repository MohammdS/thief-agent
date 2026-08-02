"""Per-subgame append-only cryptographic match log artifact."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from thief_agent.artifacts.common import ArtifactLinks, ArtifactModel, MutualAgreement
from thief_agent.protocol.envelope import HASH_PATTERN


class LogAudit(ArtifactModel):
    """Summarize replay audit coverage."""

    passed: bool
    verified_steps: int = Field(ge=0)
    failed_steps: tuple[int, ...] = ()


class LogSummary(ArtifactModel):
    """Summarize one role's view of a subgame."""

    sub_game_number: int = Field(ge=1)
    group_id: str
    role: Literal["thief"] = "thief"
    opponent_group_id: str
    result: str
    winner_role: Literal["police", "thief", "tie", "technical_loss"]
    steps: int = Field(ge=0)
    timezone: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float = Field(ge=0)
    tokens_total: int = Field(ge=0)
    audit: LogAudit


class LogRecord(ArtifactModel):
    """Store one canonical payload, final nonce, and public commitment."""

    payload: dict[str, Any]
    nonce: str = Field(pattern=r"^[0-9a-f]{32,64}$")
    commit: str = Field(pattern=HASH_PATTERN)


class MatchLogArtifact(ArtifactModel):
    """Represent the supplied replay-consumable log shape."""

    schema_description: str = Field(alias="_schema")
    schema_version: Literal["1.1"] = "1.1"
    game_id: str
    game_uid: str
    links: ArtifactLinks
    summary: LogSummary
    records: tuple[LogRecord, ...]
    mutual_agreement: MutualAgreement

