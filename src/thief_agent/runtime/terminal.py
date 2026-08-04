"""Publish captures the Thief can prove from its own cell and public barriers."""

from typing import Literal

from thief_agent.config.models import SharedConfig
from thief_agent.domain.board import is_imprisoned
from thief_agent.domain.state import BoardState
from thief_agent.protocol.messages import CaptureClaimRequest
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.exchange import envelope
from thief_agent.runtime.transport import PeerTransport


async def claim_public_capture(
    config: SharedConfig,
    subgame: int,
    step: int,
    state: BoardState,
    evidence_sha256: str,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> Literal["barrier", "imprisonment"] | None:
    """Claim a public capture and return its coordinate-free reason."""
    reason: Literal["barrier", "imprisonment"] | None = (
        "barrier"
        if state.thief in state.barriers
        else "imprisonment"
        if is_imprisoned(state)
        else None
    )
    if reason is None:
        return None
    request = CaptureClaimRequest(
        envelope=envelope(config, evidence_sha256, subgame, step),
        reason=reason,
        evidence_sha256=evidence_sha256,
    )
    ack = await gate.call(lambda: client.capture_claim(request))
    if not ack.accepted:
        raise RuntimeError(ack.detail)
    return reason
