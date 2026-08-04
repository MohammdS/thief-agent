"""Typed outbound transport boundary used by the autonomous runtime."""

from __future__ import annotations

from typing import Protocol

from thief_agent.crypto.audit import AuditResult, FinalAuditRequest
from thief_agent.protocol.messages import (
    Ack,
    CaptureClaimRequest,
    CommitTurnRequest,
    HealthRequest,
    HealthResponse,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)


class PeerTransport(Protocol):
    """Describe every outbound peer operation used during a series."""

    async def health(self, request: HealthRequest) -> HealthResponse:
        """Return remote health and identity."""
        ...

    async def negotiate(self, request: NegotiationRequest) -> Ack:
        """Submit the shared series anchor."""
        ...

    async def commit_turn(self, request: CommitTurnRequest) -> Ack:
        """Submit one turn commitment."""
        ...

    async def reveal_turn(self, request: RevealTurnRequest) -> Ack:
        """Submit one immediate reveal."""
        ...

    async def capture_claim(self, request: CaptureClaimRequest) -> Ack:
        """Submit one provisional public capture claim."""
        ...

    async def final_audit(self, request: FinalAuditRequest) -> AuditResult:
        """Submit final secret disclosures."""
        ...

    async def propose_result(self, request: ResultProposalRequest) -> Ack:
        """Submit one result digest."""
        ...
