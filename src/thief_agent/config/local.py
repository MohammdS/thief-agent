"""Load strict peer-local TOML without placing secrets in shared JSON."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import Field

from thief_agent.config.models import StrictModel


class IdentitySettings(StrictModel):
    """Identify the local Thief team."""

    team_name: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    role: Literal["thief"]


class PeerSettings(StrictModel):
    """Configure local serving and the remote Police endpoint."""

    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    opponent_mcp_url: str = Field(min_length=1)
    opponent_group_id: str = Field(min_length=1)


class StrategySettings(StrictModel):
    """Configure deterministic strategy and bounded language generation."""

    seed: int
    language_provider: Literal["template", "ollama"]
    ollama_model: str = Field(min_length=1)
    hint_every_n_steps: int = Field(ge=1)
    hint_word_limit: int = Field(ge=1)


class UiSettings(StrictModel):
    """Configure optional live visualization."""

    enabled: bool
    headless: bool


class ReportingSettings(StrictModel):
    """Configure safe report delivery mode and fixed course recipient."""

    mode: Literal["dry-run", "live"]
    recipient: Literal["rmisegal+uoh26finalgame@gmail.com"]


class LocalConfig(StrictModel):
    """Represent all peer-local, non-shared settings."""

    identity: IdentitySettings
    peer: PeerSettings
    strategy: StrategySettings
    ui: UiSettings
    reporting: ReportingSettings


def load_local_config(path: Path) -> LocalConfig:
    """Parse a private TOML file using strict local models."""
    with path.open("rb") as stream:
        return LocalConfig.model_validate(tomllib.load(stream))
