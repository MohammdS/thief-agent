"""Per-subgame byte-identical agreed configuration artifact."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from thief_agent.artifacts.common import ArtifactLinks, ArtifactModel, artifact_links
from thief_agent.config.loader import config_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.protocol.envelope import HASH_PATTERN


class AgreedConfigArtifact(ArtifactModel):
    """Preserve assignment metadata around the validated shared rules."""

    schema_description: str = Field(alias="_schema")
    schema_version: Literal["1.1"] = "1.1"
    note: str = Field(alias="_note")
    agreed_between: tuple[str, str]
    board_and_agents: dict[str, object]
    movement_and_barriers: dict[str, object]
    scoring: dict[str, int]
    pheromones: dict[str, float | int]
    network_and_league: dict[str, int]
    rate_limiter_gatekeeper: dict[str, float | int]
    game_id: str
    game_uid: str
    sub_game_number: int = Field(ge=1)
    links: ArtifactLinks
    config_name: str
    config_sha256: str = Field(pattern=HASH_PATTERN)


def build_agreed_config(
    config: SharedConfig,
    game_uid: str,
    subgame: int,
    teams: tuple[str, str],
) -> AgreedConfigArtifact:
    """Wrap validated rules in a uniquely named per-subgame artifact."""
    name = f"config_{config.game_id}_g{subgame:02d}.json"
    return AgreedConfigArtifact(
        _schema="Agreed byte-identical game configuration for one subgame.",
        _note="Shared agreed terms overlay the private peer TOML.",
        agreed_between=teams,
        board_and_agents={
            "grid_size": config.board.width,
            "thief_start": [config.board.thief_start.row, config.board.thief_start.col],
            "cop_start": [config.board.police_start.row, config.board.police_start.col],
        },
        movement_and_barriers={
            "move_set": list(config.board.legal_moves),
            "max_barriers": config.barriers.police_capacity,
            "max_moves": config.turns.max_steps,
            "survival_threshold": config.turns.survival_threshold,
        },
        scoring={
            "capture_cop": config.scoring.capture.police,
            "capture_thief": config.scoring.capture.thief,
            "survival_cop": config.scoring.survival.police,
            "survival_thief": config.scoring.survival.thief,
            "tie_score": config.scoring.tie.police,
        },
        pheromones={
            "pheromone_center_intensity": config.scent.center,
            "pheromone_decay": config.scent.decay,
            "pheromone_grid_size": config.scent.field_size,
        },
        network_and_league={
            "num_games": config.series.subgames,
            "token_budget_per_series": config.series.token_budget,
        },
        rate_limiter_gatekeeper={
            "requests_per_minute": config.network.requests_per_minute,
            "concurrent_requests": config.network.concurrency,
            "retry_backoff_sec": config.network.retry_delay_seconds,
            "max_retries": config.network.retries,
            "queue_depth": config.network.queue_depth,
        },
        game_id=config.game_id,
        game_uid=game_uid,
        sub_game_number=subgame,
        links=artifact_links(config.game_id),
        config_name=name,
        config_sha256=config_sha256(config),
    )
