"""Construct fresh per-subgame runtime dependencies."""

from __future__ import annotations

from pathlib import Path

from thief_agent.config import LocalConfig, SharedConfig
from thief_agent.language.ollama import OllamaHintProvider
from thief_agent.language.policy import HintPolicy
from thief_agent.language.providers import TemplateHintProvider
from thief_agent.orchestrator import ThiefOrchestrator
from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reliability.watchdog import Watchdog
from thief_agent.strategy.evasion import EvasionStrategy


def build_orchestrator(
    config: SharedConfig,
    local: LocalConfig,
    output: Path,
    subgame: int,
) -> ThiefOrchestrator:
    """Build a fresh strategy, language policy, checkpoint, and watchdog."""
    provider = (
        OllamaHintProvider(model=local.strategy.ollama_model)
        if local.strategy.language_provider == "ollama"
        else TemplateHintProvider()
    )
    return ThiefOrchestrator(
        EvasionStrategy(),
        HintPolicy(provider, local.strategy.hint_every_n_steps),
        CheckpointStore(output / "runtime" / f"checkpoint-g{subgame:02d}.json"),
        Watchdog(config.network.watchdog_seconds),
    )
