"""Static whole-series pre-game declaration artifact."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from thief_agent.artifacts.common import ArtifactLinks, ArtifactModel


class RepositoryLinks(ArtifactModel):
    """Publish both role repositories for one group."""

    cop: str
    thief: str


class McpServers(ArtifactModel):
    """Publish both role endpoints for one group."""

    cop: str
    thief: str


class HardwareSpec(ArtifactModel):
    """Describe declared compute hardware without secrets."""

    cpu_type: str
    cpu_freq_mhz: float = Field(ge=0)
    cpu_cores: int = Field(ge=1)
    ram_gb: float = Field(gt=0)
    gpu_model: str
    vram_gb: float = Field(ge=0)


class GroupDeclaration(ArtifactModel):
    """Declare one team's identity, endpoints, model, and signature."""

    group_id: str
    group_name: str
    members: tuple[str, ...]
    repos: RepositoryLinks
    mcp_servers: McpServers
    llm_model: str
    hardware_spec: HardwareSpec
    signature: str


class DeclarationArtifact(ArtifactModel):
    """Represent the supplied whole-series declaration shape."""

    schema_description: str = Field(alias="_schema")
    schema_version: Literal["1.1"] = "1.1"
    declaration_type: Literal["pre_game_declaration"] = "pre_game_declaration"
    game_id: str
    game_uid: str
    links: ArtifactLinks
    timezone: str
    game_started_at: datetime
    game_ended_at: datetime | None = None
    num_sub_games: int = Field(ge=1)
    max_tokens_per_game: int = Field(gt=0)
    groups: dict[str, GroupDeclaration]

