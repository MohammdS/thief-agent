"""Deterministic pre-game health and series-anchor negotiation."""

from __future__ import annotations

from datetime import UTC, datetime

from thief_agent.config import config_sha256
from thief_agent.config.local import LocalConfig
from thief_agent.config.models import SharedConfig
from thief_agent.domain.types import Role
from thief_agent.protocol.envelope import make_envelope
from thief_agent.protocol.messages import HealthRequest, NegotiationRequest
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.live_state import initial_state
from thief_agent.runtime.state import request_lifetime, state_sha256
from thief_agent.runtime.transport import PeerTransport
from thief_agent.runtime.wait import wait_for_value


async def negotiate_series(
    config: SharedConfig,
    local: LocalConfig,
    service: ProtocolService,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> NegotiationRequest:
    """Verify Police identity and agree on one coordinator-owned anchor."""
    state_hash = state_sha256(initial_state(config))
    health = HealthRequest(
        envelope=make_envelope(
            config.game_id,
            config_sha256(config),
            state_hash,
            sender=Role.THIEF,
            lifetime_seconds=request_lifetime(config),
        )
    )
    response = await gate.call(lambda: client.health(health))
    if response.role is not Role.POLICE or response.config_sha256 != config_sha256(config):
        raise ValueError("remote endpoint is not the agreed Police peer")
    own = local.identity.group_id
    opponent = local.peer.opponent_group_id
    if own < opponent:
        anchor = datetime.now(UTC).replace(microsecond=0)
        proposal = request(config, own, state_hash, anchor)
        await send(proposal, client, gate)
        incoming = await wait_for_value(
            lambda: service.negotiation,
            config.network.response_timeout_seconds,
            "opponent negotiation",
        )
    else:
        incoming = await wait_for_value(
            lambda: service.negotiation,
            config.network.response_timeout_seconds,
            "coordinator negotiation",
        )
        proposal = request(
            config,
            own,
            state_hash,
            incoming.series_started_at,
            incoming.game_uid,
        )
        await send(proposal, client, gate)
    validate_pair(config, incoming, proposal, opponent)
    return proposal


def request(
    config: SharedConfig,
    group_id: str,
    state_hash: str,
    started_at: datetime,
    game_uid: str | None = None,
) -> NegotiationRequest:
    """Build one strict negotiation request."""
    uid = game_uid or f"{config.game_id}-{int(started_at.timestamp())}"
    return NegotiationRequest(
        envelope=make_envelope(
            config.game_id,
            config_sha256(config),
            state_hash,
            sender=Role.THIEF,
            lifetime_seconds=request_lifetime(config),
        ),
        contract_version="1.3",
        counted=config.counted,
        subgames=config.series.subgames,
        sender_group_id=group_id,
        game_uid=uid,
        series_started_at=started_at,
    )


async def send(
    proposal: NegotiationRequest,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> None:
    """Publish one negotiation request and require acceptance."""
    ack = await gate.call(lambda: client.negotiate(proposal))
    if not ack.accepted:
        raise ValueError(ack.detail)


def validate_pair(
    config: SharedConfig,
    incoming: NegotiationRequest,
    outgoing: NegotiationRequest,
    opponent_group: str,
) -> None:
    """Require both independently stored negotiation views to match."""
    if incoming.sender_group_id != opponent_group:
        raise ValueError("negotiation group identity mismatch")
    actual = (
        incoming.game_uid,
        incoming.series_started_at,
        incoming.counted,
        incoming.subgames,
    )
    expected = (
        outgoing.game_uid,
        outgoing.series_started_at,
        config.counted,
        config.series.subgames,
    )
    if actual != expected:
        raise ValueError("peer negotiation does not match local series")
