"""Mutually confirm the final whole-series result artifact."""

from __future__ import annotations

from thief_agent.artifacts.result import ResultArtifact, confirm_result, result_sha256
from thief_agent.config import config_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Role
from thief_agent.protocol.envelope import make_envelope
from thief_agent.protocol.messages import ResultProposalRequest
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.state import request_lifetime, state_sha256
from thief_agent.runtime.transport import PeerTransport
from thief_agent.runtime.wait import wait_for_value


async def agree_series_result(
    config: SharedConfig,
    provisional: ResultArtifact,
    last_state: BoardState,
    groups: tuple[str, str],
    git_commit: str,
    service: ProtocolService,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> ResultArtifact:
    """Exchange final hashes and confirm only an independently exact match."""
    digest = result_sha256(provisional)
    totals = provisional.final_result
    request = ResultProposalRequest(
        envelope=make_envelope(
            config.game_id,
            config_sha256(config),
            state_sha256(last_state),
            sender=Role.THIEF,
            subgame=0,
            step=len(provisional.sub_games),
            lifetime_seconds=request_lifetime(config),
        ),
        phase="series",
        sender_group_id=groups[0],
        result_sha256=digest,
        police_score=totals.total_score[groups[1]],
        thief_score=totals.total_score[groups[0]],
        tokens_total=totals.tokens_total_series[groups[0]],
        git_commit=git_commit,
    )
    ack = await gate.call(lambda: client.propose_result(request))
    if not ack.accepted:
        raise ValueError(ack.detail)
    peer = await wait_for_value(
        lambda: service.result_proposals.get(("series", 0, groups[1])),
        config.network.response_timeout_seconds,
        "opponent series result",
    )
    if peer.result_sha256 != digest:
        raise ValueError("opponent final result hash does not match")
    return confirm_result(provisional, peer.result_sha256)
