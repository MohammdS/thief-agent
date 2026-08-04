from pathlib import Path

import pytest

from thief_agent.domain.scent import advance_scent
from thief_agent.domain.types import Coord
from thief_agent.language.candidates import build_hint_request
from thief_agent.language.policy import HintPolicy
from thief_agent.language.providers import TemplateHintProvider
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.protocol.actions import HintIntent
from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reliability.watchdog import Watchdog
from thief_agent.strategy.evasion import EvasionStrategy, legal_local_moves
from thief_agent.strategy.observation import ThiefObservation


@pytest.mark.asyncio
async def test_orchestrator_seals_and_checkpoints_one_turn(tmp_path: Path) -> None:
    policy = HintPolicy(TemplateHintProvider())
    store = CheckpointStore(tmp_path / "turn.json")
    orchestrator = ThiefOrchestrator(EvasionStrategy(), policy, store, Watchdog())
    observation = ThiefObservation(
        7, 7, Coord(3, 3), frozenset(), {}, {Coord(0, 0): 1.0}, 1,
    )
    decision = await orchestrator.decide_turn(
        observation, "orchestrator-test", 1, "a" * 64, HintIntent.BLUFF,
    )
    assert decision.move in legal_local_moves(observation)
    assert decision.sealed.disclosure.hint == decision.hint
    assert decision.sealed.disclosure.scent_heatmap == ()
    assert store.load()["commitment"] == decision.sealed.commitment  # type: ignore[index]
    assert len(decision.hint.split()) <= build_hint_request(
        decision.move, HintIntent.BLUFF,
    ).max_words

    private_trail = advance_scent({}, observation.thief, 7, 7)
    next_decision = await orchestrator.decide_turn(
        observation, "orchestrator-test", 1, "b" * 64, HintIntent.BLUFF,
        own_scent=private_trail,
    )
    assert max(cell.intensity for cell in next_decision.scent_heatmap) == pytest.approx(0.81)
