"""Run one uncounted subgame using the real Thief decision pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.belief.model import BeliefMap, uniform_belief, update_belief
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.commit_reveal import SealedTurn
from thief_agent.domain.board import apply_move, place_barrier
from thief_agent.domain.outcome import Outcome, TerminalReason, evaluate_outcome, score_outcome
from thief_agent.domain.scent import ScentMap, advance_scent
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.protocol.actions import ActionKind, HintIntent
from thief_agent.qualification.client import StubClient
from thief_agent.qualification.models import StubTurnRequest
from thief_agent.qualification.state import board_sha256, sealed_record
from thief_agent.strategy.observation import ThiefObservation


@dataclass(frozen=True, slots=True)
class GameRun:
    """Return terminal state, outcome, and final-disclosure records."""

    state: BoardState
    outcome: Outcome
    records: tuple[LogRecord, ...]
    tokens: int


async def run_game(
    config: SharedConfig,
    subgame: int,
    client: StubClient,
    orchestrator: ThiefOrchestrator,
) -> GameRun:
    """Run until capture, imprisonment, or survival without deadlock."""
    state = initial_state(config)
    belief = uniform_belief(state.width, state.height)
    scent: ScentMap = {}
    own_scent: ScentMap = {}
    records: list[LogRecord] = []
    tokens = 0
    for step in range(1, config.turns.max_steps + 1):
        observation = local_observation(state, belief, scent, step)
        decision = await orchestrator.decide_turn(
            observation, config.game_id, subgame, board_sha256(state),
            HintIntent.BLUFF if step % 2 else HintIntent.TRUTH,
            own_scent=own_scent,
            scent_decay=config.scent.decay,
        )
        own_scent = {
            Coord(cell.row, cell.col): cell.intensity for cell in decision.scent_heatmap
        }
        records.append(sealed_record(decision.sealed))
        tokens += decision.prompt_tokens + decision.completion_tokens
        state = apply_move(state, decision.sealed.disclosure.role, decision.move)
        outcome = evaluate_outcome(state, config)
        if outcome:
            return GameRun(state, outcome, tuple(records), tokens)
        police = await client.turn(StubTurnRequest(
            game_id=config.game_id, subgame=subgame, step=step,
            prior_state_sha256=board_sha256(state),
        ))
        sealed = SealedTurn(police.commitment, police.disclosure)
        records.append(sealed_record(sealed))
        state = apply_police(state, sealed, config.barriers.police_capacity)
        state = state.after_full_turn()
        scent = advance_scent(scent, state.police, state.width, state.height, config.scent.decay)
        belief = update_belief(belief, scent, state.barriers, sealed.disclosure.hint, 0.5)
        outcome = evaluate_outcome(state, config)
        if outcome:
            return GameRun(state, outcome, tuple(records), tokens)
    return GameRun(
        state, score_outcome(TerminalReason.SURVIVAL, config), tuple(records), tokens,
    )


def initial_state(config: SharedConfig) -> BoardState:
    """Create objective state inside the isolated qualification harness."""
    return BoardState(
        config.board.width,
        config.board.height,
        Coord(config.board.thief_start.row, config.board.thief_start.col),
        Coord(config.board.police_start.row, config.board.police_start.col),
    )


def local_observation(
    state: BoardState, belief: BeliefMap, scent: ScentMap, step: int,
) -> ThiefObservation:
    """Strip objective Police position before strategy invocation."""
    return ThiefObservation(
        state.width, state.height, state.thief, state.barriers,
        scent, belief.probabilities, step,
    )


def apply_police(state: BoardState, sealed: SealedTurn, capacity: int) -> BoardState:
    """Apply one test-only stub action through real physical validators."""
    action = sealed.disclosure.action
    if action.kind is ActionKind.MOVE and action.move is not None:
        return apply_move(state, sealed.disclosure.role, action.move)
    if action.kind is ActionKind.BARRIER and action.barrier is not None:
        return place_barrier(state, Coord(action.barrier.row, action.barrier.col), capacity)
    raise ValueError("stub returned malformed Police action")
