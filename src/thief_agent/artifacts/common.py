"""Shared strict models for assignment-compatible JSON artifacts."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from thief_agent.config.models import StrictModel
from thief_agent.protocol.envelope import HASH_PATTERN


class ArtifactModel(StrictModel):
    """Serialize aliases such as the supplied `_schema` field."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ArtifactLinks(ArtifactModel):
    """Link the four mandatory files by stable game-derived names."""

    remark: str = Field(alias="_remark")
    declaration: str
    config: str
    log: str
    result: str


class MutualAgreement(ArtifactModel):
    """Record the peer-calculated canonical artifact hash agreement."""

    sha256: str = Field(pattern=HASH_PATTERN)
    confirmed: bool


def artifact_links(game_id: str) -> ArtifactLinks:
    """Return assignment filenames without mixing games."""
    return ArtifactLinks(
        _remark="Match files derive only from game_id; NN is the two-digit subgame.",
        declaration=f"declaration_{game_id}.json",
        config=f"config_{game_id}_g<NN>.json",
        log=f"log_{game_id}_g<NN>.json",
        result=f"result_{game_id}.json",
    )
