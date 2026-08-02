"""Immutable values returned by autonomous subgame and series execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from thief_agent.artifacts.match_log import LogRecord
from thief_agent.artifacts.result import ResultArtifact
from thief_agent.domain.outcome import Outcome
from thief_agent.domain.state import BoardState


@dataclass(frozen=True, slots=True)
class PeerGameRun:
    """Capture one fully audited symmetric subgame."""

    state: BoardState
    outcome: Outcome
    records: tuple[LogRecord, ...]
    tokens: int
    opponent_tokens: int
    opponent_git_commit: str
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True, slots=True)
class PeerSeriesRun:
    """Return final local artifacts from one mutually agreed series."""

    result: ResultArtifact
    result_path: Path
    games: tuple[PeerGameRun, ...]
