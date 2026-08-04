"""Shared post-play audit, replay, and subgame agreement."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord
from thief_agent.domain.outcome import Outcome
from thief_agent.domain.state import BoardState
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.audit_replay import reconstruct_audited_subgame
from thief_agent.runtime.exchange import exchange_audit, exchange_subgame_result
from thief_agent.runtime.state import log_record, ordered_audits
from thief_agent.runtime.transport import PeerTransport


@dataclass(frozen=True, slots=True)
class FinalizedGame:
    """Return mutually audited terminal data needed by the series runner."""

    state: BoardState
    outcome: Outcome
    records: tuple[LogRecord, ...]
    opponent_tokens: int
    opponent_commit: str


async def finalize_game(
    config: SharedConfig, subgame: int, state: BoardState,
    own_audits: tuple[AuditRecord, ...], tokens: int, service: ProtocolService,
    client: PeerTransport, gate: ExternalGatekeeper, groups: tuple[str, str],
    git_commit: str,
) -> FinalizedGame:
    """Exchange secrets, reconstruct the token sequence, and agree the result."""
    opponent_records = await exchange_audit(
        config, subgame, state, own_audits, service, client, gate,
    )
    audits = ordered_audits((*own_audits, *opponent_records))
    audited = reconstruct_audited_subgame(config, audits)
    opponent = await exchange_subgame_result(
        config, subgame, audited.state, audited.outcome, tokens, service, client,
        gate, groups, git_commit,
    )
    return FinalizedGame(
        audited.state, audited.outcome, tuple(log_record(record) for record in audits),
        opponent.tokens_total, opponent.git_commit,
    )
