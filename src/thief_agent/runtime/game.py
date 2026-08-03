"""Symmetric commit-reveal loop for one autonomous Thief subgame."""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import partial

from thief_agent.belief.model import uniform_belief, update_belief
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord
from thief_agent.domain.board import apply_move
from thief_agent.domain.scent import ScentMap
from thief_agent.domain.types import Coord, Role
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.protocol.actions import HintIntent
from thief_agent.protocol.machine import TurnState, turn_machine
from thief_agent.protocol.scent import decode_scent
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.audit_replay import reconstruct_audited_subgame
from thief_agent.runtime.exchange import (
    exchange_audit,
    exchange_subgame_result,
    send_commit,
    send_reveal,
)
from thief_agent.runtime.live_state import (
    apply_public_barrier,
    initial_state,
    require_in_bounds_heatmap,
)
from thief_agent.runtime.models import PeerGameRun
from thief_agent.runtime.state import audit_record, log_record, state_sha256
from thief_agent.runtime.transport import PeerTransport
from thief_agent.runtime.wait import wait_for_value
from thief_agent.strategy.observation import ThiefObservation


async def run_peer_game(
    config: SharedConfig,
    subgame: int,
    service: ProtocolService,
    client: PeerTransport,
    orchestrator: ThiefOrchestrator,
    gate: ExternalGatekeeper,
    groups: tuple[str, str],
    git_commit: str,
    started_at: datetime,
    max_words: int,
) -> PeerGameRun:
    """Run simultaneous commitments, mutual reveals, and final audit."""
    state = initial_state(config)
    belief = uniform_belief(state.width, state.height)
    own_scent: ScentMap = {}
    police_scent: ScentMap = {}
    own_audits: list[AuditRecord] = []
    recent: list[Coord] = []
    tokens = 0
    for step in range(1, config.turns.max_steps + 1):
        turn = turn_machine()
        turn.transition(TurnState.COMPUTING_MOVE)
        prior_hash = state_sha256(state)
        observation = ThiefObservation(
            state.width, state.height, state.thief, state.barriers,
            police_scent, belief.probabilities, step, tuple(recent[-4:]),
        )
        decision = await orchestrator.decide_turn(
            observation, config.game_id, subgame, prior_hash,
            HintIntent.BLUFF if step % 2 else HintIntent.TRUTH,
            max_words=max_words,
            own_scent=own_scent,
            scent_decay=config.scent.decay,
        )
        own_scent = decode_scent(decision.scent_heatmap)
        own_audits.append(audit_record(decision.sealed))
        tokens += decision.prompt_tokens + decision.completion_tokens
        turn.transition(TurnState.COMMITTING)
        await send_commit(
            config, subgame, step, prior_hash, decision.sealed.commitment, client, gate,
        )
        key = (subgame, step, Role.POLICE.value)
        await wait_for_value(
            partial(service.ledger.commitments.get, key),
            config.network.response_timeout_seconds,
            "commit",
        )
        turn.transition(TurnState.AWAITING_REVEAL)
        await send_reveal(config, subgame, step, prior_hash, decision, client, gate)
        police = await wait_for_value(
            partial(service.ledger.reveals.get, key),
            config.network.response_timeout_seconds,
            "reveal",
        )
        turn.transition(TurnState.VERIFYING)
        state = apply_move(state, Role.THIEF, decision.move)
        if police.barrier is not None:
            target = Coord(police.barrier.row, police.barrier.col)
            state = apply_public_barrier(state, target, config)
        state = state.after_full_turn()
        recent.append(state.thief)
        police_scent = decode_scent(police.scent_heatmap)
        require_in_bounds_heatmap(police_scent, state)
        belief = update_belief(belief, police_scent, state.barriers, police.hint, 0.5)
        turn.transition(TurnState.COMPLETE)
        if police.capture_claim is not None or state.step >= config.turns.survival_threshold:
            break
    opponent_records = await exchange_audit(
        config, subgame, state, tuple(own_audits), service, client, gate,
    )
    audited = reconstruct_audited_subgame(
        config,
        tuple(
            sorted(
                (*own_audits, *opponent_records),
                key=lambda item: (
                    item.disclosure.step,
                    0 if item.disclosure.role is Role.THIEF else 1,
                ),
            )
        ),
    )
    state, outcome = audited.state, audited.outcome
    opponent = await exchange_subgame_result(
        config, subgame, state, outcome, tokens, service, client, gate, groups, git_commit,
    )
    records = tuple(
        log_record(record)
        for record in sorted(
            (*own_audits, *opponent_records),
            key=lambda item: (
                item.disclosure.step,
                0 if item.disclosure.role is Role.THIEF else 1,
            ),
        )
    )
    return PeerGameRun(
        state, outcome, records, tokens, opponent.tokens_total, opponent.git_commit,
        started_at, started_at + timedelta(seconds=max(1, state.step)),
    )
