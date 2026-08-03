"""Build deterministic coordinator callbacks for in-memory peer tests."""

from __future__ import annotations

from datetime import UTC, datetime

from thief_agent.config.models import SharedConfig
from thief_agent.protocol.envelope import WireEnvelope
from thief_agent.protocol.messages import NegotiationRequest


def police_proposal(
    config: SharedConfig, police_group: str, thief_group: str, envelope: WireEnvelope,
) -> NegotiationRequest | None:
    """Return a Police-owned anchor only when its ID is coordinator-first."""
    if police_group >= thief_group:
        return None
    started_at = datetime.now(UTC).replace(microsecond=0)
    return NegotiationRequest(
        envelope=envelope,
        contract_version="1.1",
        counted=config.counted,
        subgames=config.series.subgames,
        sender_group_id=police_group,
        game_uid=f"{config.game_id}-{int(started_at.timestamp())}",
        series_started_at=started_at,
    )
