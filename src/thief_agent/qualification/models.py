"""Strict test-only Police stub requests and qualification summaries."""

from __future__ import annotations

from pydantic import Field

from thief_agent.config.models import StrictModel
from thief_agent.crypto.commit_reveal import TurnDisclosure
from thief_agent.protocol.envelope import HASH_PATTERN


class StubTurnRequest(StrictModel):
    """Request one deterministic test-only Police action."""

    game_id: str
    subgame: int = Field(ge=1)
    step: int = Field(ge=1)
    prior_state_sha256: str = Field(pattern=HASH_PATTERN)


class StubTurnResponse(StrictModel):
    """Return a stub-originated commitment and final disclosure."""

    commitment: str = Field(pattern=HASH_PATTERN)
    disclosure: TurnDisclosure


class QualifiedGame(StrictModel):
    """Summarize one terminating uncounted subgame."""

    subgame: int
    outcome: str
    steps: int
    police_score: int
    thief_score: int
    replay_status: str
    barriers_placed: int


class QualificationSummary(StrictModel):
    """Summarize six games plus deliberate corruption evidence."""

    game_id: str
    games: tuple[QualifiedGame, ...]
    all_terminated: bool
    all_verified: bool
    corrupted_replay_status: str
    total_police_score: int
    total_thief_score: int

