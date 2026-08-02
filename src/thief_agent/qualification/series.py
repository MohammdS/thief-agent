"""Coordinate six qualification games and prove replay tamper detection."""

from __future__ import annotations

import json
from pathlib import Path

from thief_agent.artifacts.agreed_config import build_agreed_config
from thief_agent.artifacts.match_log import MatchLogArtifact
from thief_agent.artifacts.store import ArtifactStore
from thief_agent.config import load_shared_config
from thief_agent.config.models import SharedConfig
from thief_agent.language.policy import HintPolicy
from thief_agent.language.providers import TemplateHintProvider
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.qualification.client import StubClient
from thief_agent.qualification.game import GameRun, run_game
from thief_agent.qualification.logging import build_log
from thief_agent.qualification.models import QualificationSummary, QualifiedGame
from thief_agent.qualification.package import declaration, result
from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reliability.watchdog import Watchdog
from thief_agent.replay.verifier import ReplayVerifier
from thief_agent.strategy.evasion import EvasionStrategy


async def run_qualification(
    stub_url: str,
    output: Path,
    git_commit: str,
    config_path: Path = Path("config/game.json"),
) -> QualificationSummary:
    """Run six games, write four artifact families, and corrupt one replay."""
    config = load_shared_config(config_path)
    store = ArtifactStore(output)
    runs: list[GameRun] = []
    qualified: list[QualifiedGame] = []
    logs = []
    async with StubClient(stub_url) as client:
        if not await client.health():
            raise RuntimeError("qualification Police stub is not ready")
        for subgame in range(1, 7):
            orchestrator = build_orchestrator(output, subgame)
            run = await run_game(config, subgame, client, orchestrator)
            log = build_log(config.game_id, subgame, run, git_commit)
            replay = ReplayVerifier(config).verify(log)
            store.write("config", config.game_id, build_agreed_config(
                config, f"qualification-{subgame:02d}", subgame,
                ("qualification-police-stub", "GROUP_ID"),
            ), subgame)
            store.write("log", config.game_id, log, subgame)
            runs.append(run)
            logs.append(log)
            qualified.append(QualifiedGame(
                subgame=subgame,
                outcome=run.outcome.reason.value,
                steps=run.state.step,
                police_score=run.outcome.police_score,
                thief_score=run.outcome.thief_score,
                replay_status=replay.status,
                barriers_placed=run.state.barriers_used,
            ))
    store.write("declaration", config.game_id, declaration(config, stub_url))
    store.write("result", config.game_id, result(config, tuple(runs), git_commit))
    corrupted = corrupt_status(config, logs[0])
    summary = QualificationSummary(
        game_id=config.game_id,
        games=tuple(qualified),
        all_terminated=all(game.steps <= config.turns.max_steps for game in qualified),
        all_verified=all(game.replay_status == "Verified OK" for game in qualified),
        corrupted_replay_status=corrupted,
        total_police_score=sum(game.police_score for game in qualified),
        total_thief_score=sum(game.thief_score for game in qualified),
    )
    (output / "qualification-summary.json").write_text(
        json.dumps(summary.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8",
    )
    return summary


def build_orchestrator(output: Path, subgame: int) -> ThiefOrchestrator:
    """Build a fresh deterministic Thief gateway for one subgame."""
    return ThiefOrchestrator(
        EvasionStrategy(),
        HintPolicy(TemplateHintProvider()),
        CheckpointStore(output / "runtime" / f"checkpoint-g{subgame:02d}.json"),
        Watchdog(60),
    )


def corrupt_status(config: SharedConfig, log: MatchLogArtifact) -> str:
    """Alter one committed hint and return the replay verifier status."""
    first = log.records[0]
    changed = first.model_copy(update={"payload": first.payload | {"hint": "corrupted"}})
    corrupted = log.model_copy(update={"records": (changed, *log.records[1:])})
    return ReplayVerifier(config).verify(corrupted).status
