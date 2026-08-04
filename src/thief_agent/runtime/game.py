"""Token-gated commit-reveal loop for one autonomous Thief subgame."""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import partial

from thief_agent.belief.model import advance_delayed_belief, point_belief
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord
from thief_agent.domain.scent import ScentMap, advance_scent
from thief_agent.domain.types import Coord, Role
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.protocol.actions import HintIntent
from thief_agent.protocol.machine import TurnState, turn_machine
from thief_agent.protocol.scent import decode_scent
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime import live_state
from thief_agent.runtime.exchange import send_commit, send_reveal
from thief_agent.runtime.finalize import finalize_game
from thief_agent.runtime.local_action import apply_thief_action
from thief_agent.runtime.models import PeerGameRun
from thief_agent.runtime.presentation import LivePresenter
from thief_agent.runtime.state import audit_record, state_sha256
from thief_agent.runtime.terminal import claim_public_capture
from thief_agent.runtime.transport import PeerTransport
from thief_agent.runtime.wait import wait_for_value
from thief_agent.strategy.observation import ThiefObservation
from thief_agent.ui.store import LiveSnapshotStore


async def run_peer_game(
    config: SharedConfig, subgame: int, service: ProtocolService,
    client: PeerTransport, orchestrator: ThiefOrchestrator,
    gate: ExternalGatekeeper, groups: tuple[str, str], git_commit: str,
    started_at: datetime, max_words: int,
    publisher: LiveSnapshotStore | None = None,
) -> PeerGameRun:
    """Use the initial token, then wait for each Police handoff before acting."""
    state = live_state.initial_state(config)
    belief = point_belief(state.width, state.height, state.police)
    own_scent: ScentMap = {}
    police_scent: ScentMap = {}
    own_audits: list[AuditRecord] = []
    recent: list[Coord] = []
    tokens = 0
    presenter = LivePresenter(publisher, subgame, config.series.subgames)
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
        state = apply_thief_action(state, decision.move, None, config).after_full_turn()
        own_scent = advance_scent(
            own_scent, state.thief, state.width, state.height, config.scent.decay,
        )
        own_audits.append(audit_record(decision.sealed))
        tokens += decision.prompt_tokens + decision.completion_tokens
        turn.transition(TurnState.COMMITTING)
        await send_commit(
            config, subgame, step, prior_hash, decision.sealed.commitment, client, gate,
        )
        service.ledger.complete_local_turn(subgame, step, Role.THIEF, Role.POLICE)
        await send_reveal(config, subgame, step, prior_hash, decision, client, gate)
        if state.step >= config.turns.survival_threshold:
            presenter.audit_horizon(state, police_scent, belief, decision.hint, tokens)
            turn.transition(TurnState.COMPLETE)
            break
        key = (subgame, step, Role.POLICE.value)
        await wait_for_value(
            partial(service.ledger.commitments.get, key),
            config.network.response_timeout_seconds, "commit",
        )
        turn.transition(TurnState.AWAITING_REVEAL)
        police = await wait_for_value(
            partial(service.ledger.reveals.get, key),
            config.network.response_timeout_seconds, "reveal",
        )
        turn.transition(TurnState.VERIFYING)
        if police.turn_token is not Role.THIEF:
            raise ValueError("Police reveal did not grant the turn token to Thief")
        if police.barrier is not None:
            state = live_state.apply_public_barrier(
                state, Coord(police.barrier.row, police.barrier.col), config,
            )
        recent.append(state.thief)
        observed_scent = decode_scent(police.scent_heatmap)
        live_state.require_in_bounds_heatmap(observed_scent, state)
        police_scent = observed_scent
        belief = advance_delayed_belief(
            belief, observed_scent, state.barriers, police.hint,
        )
        capture_reason = await claim_public_capture(
            config, subgame, step, state, police.commitment, client, gate,
        )
        if capture_reason:
            presenter.audit_claim(
                state, police_scent, belief, police.hint, tokens, capture_reason,
            )
            turn.transition(TurnState.COMPLETE)
            break
        presenter.turn_ready(state, police_scent, belief, police.hint, tokens)
        turn.transition(TurnState.COMPLETE)
    final = await finalize_game(
        config, subgame, state, tuple(own_audits), tokens, service, client, gate,
        groups, git_commit,
    )
    presenter.finished(final.state, police_scent, belief, tokens, final.outcome)
    return PeerGameRun(
        final.state, final.outcome, final.records, tokens, final.opponent_tokens,
        final.opponent_commit, started_at,
        started_at + timedelta(seconds=max(1, final.state.step)),
    )
