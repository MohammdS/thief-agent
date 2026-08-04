"""Expose only assignment-authorized live evidence to strategy and GUI."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.config.models import PointConfig
from thief_agent.domain.types import Role
from thief_agent.protocol.messages import RevealTurnRequest
from thief_agent.protocol.scent import ScentCell


@dataclass(frozen=True, slots=True)
class ObservationEvidence:
    """Expose scent, language, and public events without objective movement."""

    hint: str
    turn_token: Role
    scent_heatmap: tuple[ScentCell, ...]
    barrier: PointConfig | None
    capture_claim: str | None


@dataclass(slots=True)
class AuditFirewall:
    """Accept only a reveal schema that contains no opponent action field."""

    def accept_police_reveal(self, request: RevealTurnRequest) -> ObservationEvidence:
        """Return the complete safe live observation and no physical movement."""
        return ObservationEvidence(
            request.hint,
            request.turn_token,
            request.scent_heatmap,
            request.barrier,
            request.capture_claim,
        )
