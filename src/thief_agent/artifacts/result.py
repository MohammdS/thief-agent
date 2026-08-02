"""Whole-series final result artifact and mutual hash agreement."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import Field

from thief_agent.artifacts.common import ArtifactLinks, ArtifactModel, MutualAgreement
from thief_agent.config.loader import canonical_json_bytes


class SubGameResult(ArtifactModel):
    """Condense one audited subgame for both groups."""

    sub_game_number: int = Field(ge=1)
    roles: dict[str, Literal["police", "thief"]]
    started_at: datetime
    ended_at: datetime
    result: str
    winner_group: str | None
    tie: bool
    github_commit: dict[str, str]
    tokens: dict[str, int]
    score: dict[str, int]
    log_files: dict[str, str]
    audit: dict[str, bool]


class SeriesTotals(ArtifactModel):
    """Store aggregate scores, wins, ties, winner, and tokens."""

    total_score: dict[str, int]
    sub_games_won: dict[str, int]
    ties: int = Field(ge=0)
    winner_group: str | None
    series_tie: bool
    tokens_total_series: dict[str, int]


class ResultArtifact(ArtifactModel):
    """Represent the assignment final whole-series report shape."""

    schema_description: str = Field(alias="_schema")
    schema_version: Literal["1.1"] = "1.1"
    report_type: Literal["final_game_result"] = "final_game_result"
    game_id: str
    game_uid: str
    links: ArtifactLinks
    timezone: str
    groups: tuple[str, str]
    num_sub_games: int = Field(ge=1)
    sub_games: tuple[SubGameResult, ...]
    final_result: SeriesTotals
    mutual_agreement: MutualAgreement


def result_sha256(result: ResultArtifact) -> str:
    """Hash result content while excluding the self-referential agreement block."""
    payload = result.model_dump(mode="json", by_alias=True, exclude={"mutual_agreement"})
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def confirm_result(result: ResultArtifact, peer_hash: str) -> ResultArtifact:
    """Confirm only an identical independently calculated result hash."""
    local_hash = result_sha256(result)
    if local_hash != peer_hash:
        raise ValueError("peer result hash does not match local result")
    agreement = MutualAgreement(sha256=local_hash, confirmed=True)
    return result.model_copy(update={"mutual_agreement": agreement})

