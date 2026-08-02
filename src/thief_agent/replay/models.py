"""Immutable frames and result status for post-match replay."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.domain.state import BoardState


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    """Store full objective state only for verified post-match playback."""

    step: int
    state: BoardState
    hint: str
    commitment: str


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Return exact audit status, failures, and reconstructable frames."""

    status: str
    failures: tuple[str, ...]
    frames: tuple[ReplayFrame, ...]

