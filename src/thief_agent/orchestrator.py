"""Sole gateway coordinating strategy, language, crypto, and persistence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from thief_agent.crypto.commit_reveal import SealedTurn, TurnMaterial, seal_turn
from thief_agent.domain.board import destination
from thief_agent.domain.scent import advance_scent
from thief_agent.domain.types import Coord, Move, Role
from thief_agent.language.candidates import build_hint_request
from thief_agent.language.policy import HintPolicy
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction
from thief_agent.protocol.scent import ScentCell, encode_scent
from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reliability.watchdog import Watchdog
from thief_agent.strategy.evasion import EvasionStrategy
from thief_agent.strategy.observation import ThiefObservation


@dataclass(frozen=True, slots=True)
class TurnDecision:
    """Return the algorithmic move, grounded language, and sealed audit material."""

    move: Move
    hint: str
    intent: HintIntent
    prompt_tokens: int
    completion_tokens: int
    scent_heatmap: tuple[ScentCell, ...]
    sealed: SealedTurn


class ThiefOrchestrator:
    """Own subsystem sequencing so peripheral modules never call each other directly."""

    def __init__(
        self,
        strategy: EvasionStrategy,
        hint_policy: HintPolicy,
        checkpoint: CheckpointStore,
        watchdog: Watchdog,
    ) -> None:
        """Inject every subsystem through the sole gateway."""
        self._strategy = strategy
        self._hints = hint_policy
        self._checkpoint = checkpoint
        self._watchdog = watchdog

    async def decide_turn(
        self,
        observation: ThiefObservation,
        game_id: str,
        subgame: int,
        prior_state_sha256: str,
        preferred_intent: HintIntent,
        max_words: int = 15,
        own_scent: Mapping[Coord, float] | None = None,
        scent_decay: float = 0.10,
    ) -> TurnDecision:
        """Choose, ground, seal, checkpoint, and heartbeat one Thief turn."""
        self._watchdog.assert_alive()
        move = self._strategy.choose_move(observation)
        next_scent = advance_scent(
            own_scent or {},
            destination(observation.thief, move),
            observation.width,
            observation.height,
            scent_decay,
        )
        scent_heatmap = encode_scent(next_scent)
        hint_request = build_hint_request(move, preferred_intent, max_words)
        hint = await self._hints.generate(observation.step, hint_request)
        material = TurnMaterial(
            game_id=game_id,
            subgame=subgame,
            step=observation.step,
            role=Role.THIEF,
            prior_state_sha256=prior_state_sha256,
            action=TurnAction(kind=ActionKind.MOVE, move=move),
            scent_heatmap=scent_heatmap,
            hint=hint.hint,
            intent=hint.intent,
        )
        sealed = seal_turn(material)
        self._checkpoint.save({
            "game_id": game_id,
            "subgame": subgame,
            "step": observation.step,
            "commitment": sealed.commitment,
            "disclosure": sealed.disclosure.model_dump(mode="json"),
        })
        self._watchdog.heartbeat()
        return TurnDecision(
            move,
            hint.hint,
            hint.intent,
            hint.prompt_tokens,
            hint.completion_tokens,
            scent_heatmap,
            sealed,
        )
