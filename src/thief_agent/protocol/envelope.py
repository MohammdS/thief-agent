"""Strict identity and freshness metadata carried by every wire request."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from thief_agent.config.models import StrictModel
from thief_agent.domain.types import Role

HASH_PATTERN = r"^[0-9a-f]{64}$"


class WireEnvelope(StrictModel):
    """Bind a request to one peer, configuration, state, and deadline."""

    schema_version: Literal["1.0"] = "1.0"
    game_id: str = Field(min_length=1)
    subgame: int = Field(ge=0)
    step: int = Field(ge=0)
    sender: Role
    message_id: UUID
    timestamp: datetime
    expires_at: datetime
    config_sha256: str = Field(pattern=HASH_PATTERN)
    prior_state_sha256: str = Field(pattern=HASH_PATTERN)

    @field_validator("timestamp", "expires_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject ambiguous naive timestamps."""
        if value.tzinfo is None:
            raise ValueError("wire timestamps must include a timezone")
        return value

    def assert_fresh(self, now: datetime | None = None) -> None:
        """Raise when a message has expired or predates its own timestamp."""
        current = now or datetime.now(UTC)
        if self.expires_at <= self.timestamp or current > self.expires_at:
            raise ValueError("wire message expired")


def make_envelope(
    game_id: str,
    config_hash: str,
    state_hash: str,
    *,
    sender: Role = Role.POLICE,
    subgame: int = 0,
    step: int = 0,
    lifetime_seconds: float = 30,
) -> WireEnvelope:
    """Create a fresh request envelope for a client call."""
    timestamp = datetime.now(UTC)
    return WireEnvelope(
        game_id=game_id,
        subgame=subgame,
        step=step,
        sender=sender,
        message_id=uuid4(),
        timestamp=timestamp,
        expires_at=timestamp + timedelta(seconds=lifetime_seconds),
        config_sha256=config_hash,
        prior_state_sha256=state_hash,
    )

