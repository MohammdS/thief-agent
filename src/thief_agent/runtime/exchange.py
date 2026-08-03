"""Outbound commit, reveal, audit, and result exchanges."""

from __future__ import annotations

from thief_agent.config import config_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord, FinalAuditRequest
from thief_agent.domain.outcome import Outcome
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Role
from thief_agent.orchestrator import TurnDecision
from thief_agent.protocol.actions import ActionKind
from thief_agent.protocol.envelope import WireEnvelope, make_envelope
from thief_agent.protocol.messages import (
    CommitTurnRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.state import request_lifetime, state_sha256, subgame_digest
from thief_agent.runtime.transport import PeerTransport
from thief_agent.runtime.wait import wait_for_value


def envelope(
    config: SharedConfig, state_hash: str, subgame: int, step: int,
) -> WireEnvelope:
    """Create one fresh Thief envelope under negotiated limits."""
    return make_envelope(
        config.game_id,
        config_sha256(config),
        state_hash,
        sender=Role.THIEF,
        subgame=subgame,
        step=step,
        lifetime_seconds=request_lifetime(config),
    )


async def send_commit(
    config: SharedConfig,
    subgame: int,
    step: int,
    state_hash: str,
    commitment: str,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> None:
    """Publish and require acknowledgment of one opaque commitment."""
    request = CommitTurnRequest(
        envelope=envelope(config, state_hash, subgame, step),
        commitment=commitment,
    )
    ack = await gate.call(lambda: client.commit_turn(request))
    if not ack.accepted:
        raise RuntimeError(ack.detail)


async def send_reveal(
    config: SharedConfig,
    subgame: int,
    step: int,
    state_hash: str,
    decision: TurnDecision,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> None:
    """Publish scent and hint while retaining the physical movement for final audit."""
    disclosure = decision.sealed.disclosure
    request = RevealTurnRequest(
        envelope=envelope(config, state_hash, subgame, step),
        scent_heatmap=disclosure.scent_heatmap,
        hint=disclosure.hint,
        barrier=(
            disclosure.action.barrier
            if disclosure.action.kind is ActionKind.BARRIER
            else None
        ),
    )
    ack = await gate.call(lambda: client.reveal_turn(request))
    if not ack.accepted:
        raise RuntimeError(ack.detail)


async def exchange_audit(
    config: SharedConfig,
    subgame: int,
    state: BoardState,
    own_records: tuple[AuditRecord, ...],
    service: ProtocolService,
    client: PeerTransport,
    gate: ExternalGatekeeper,
) -> tuple[AuditRecord, ...]:
    """Exchange final secrets and require two successful audits."""
    request = FinalAuditRequest(
        envelope=envelope(config, state_sha256(state), subgame, state.step),
        records=own_records,
    )
    remote = await gate.call(lambda: client.final_audit(request))
    if remote.status != "Verified OK":
        raise ValueError(f"peer rejected final audit: {remote.errors}")
    local = await wait_for_value(
        lambda: service.audit_results.get(subgame),
        config.network.response_timeout_seconds,
        "opponent final audit",
    )
    if local.status != "Verified OK":
        raise ValueError(f"local final audit failed: {local.errors}")
    return service.audit_records[subgame]


async def exchange_subgame_result(
    config: SharedConfig,
    subgame: int,
    state: BoardState,
    outcome: Outcome,
    tokens: int,
    service: ProtocolService,
    client: PeerTransport,
    gate: ExternalGatekeeper,
    groups: tuple[str, str],
    git_commit: str,
) -> ResultProposalRequest:
    """Compare independently calculated terminal state and scores."""
    digest = subgame_digest(state, outcome, subgame)
    request = ResultProposalRequest(
        envelope=envelope(config, state_sha256(state), subgame, state.step),
        phase="subgame",
        sender_group_id=groups[0],
        result_sha256=digest,
        police_score=outcome.police_score,
        thief_score=outcome.thief_score,
        tokens_total=tokens,
        git_commit=git_commit,
    )
    ack = await gate.call(lambda: client.propose_result(request))
    if not ack.accepted:
        raise RuntimeError(ack.detail)
    key = ("subgame", subgame, groups[1])
    opponent = await wait_for_value(
        lambda: service.result_proposals.get(key),
        config.network.response_timeout_seconds,
        "opponent subgame result",
    )
    expected = (digest, outcome.police_score, outcome.thief_score)
    actual = (opponent.result_sha256, opponent.police_score, opponent.thief_score)
    if actual != expected:
        raise ValueError("opponent subgame result does not match local result")
    return opponent
