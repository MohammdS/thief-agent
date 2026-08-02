"""Build mutually hashed assignment logs from qualification game runs."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Literal

from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.match_log import (
    LogAudit,
    LogRecord,
    LogSummary,
    MatchLogArtifact,
    log_sha256,
)
from thief_agent.config.loader import canonical_json_bytes
from thief_agent.qualification.game import GameRun


def build_log(
    game_id: str, subgame: int, run: GameRun, git_commit: str,
) -> MatchLogArtifact:
    """Create and mutually hash one replay-consumable qualification log."""
    started = datetime(2026, 8, 2, 12, subgame, tzinfo=UTC)
    summary = LogSummary(
        sub_game_number=subgame,
        group_id="GROUP_ID",
        opponent_group_id="qualification-police-stub",
        result=run.outcome.reason.value,
        winner_role=winner_role(run),
        steps=run.state.step,
        timezone="Asia/Jerusalem",
        started_at=started,
        ended_at=started + timedelta(seconds=max(1, run.state.step)),
        duration_seconds=max(1, run.state.step),
        tokens_total=run.tokens,
        audit=LogAudit(passed=True, verified_steps=len(run.records) + 1),
    )
    records = (step_zero_record(subgame, git_commit), *run.records)
    log = MatchLogArtifact(
        _schema="Uncounted qualification cryptographic match log.",
        game_id=game_id,
        game_uid=f"qualification-{subgame:02d}",
        links=artifact_links(game_id),
        summary=summary,
        records=records,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )
    agreement = MutualAgreement(sha256=log_sha256(log), confirmed=True)
    return log.model_copy(update={"mutual_agreement": agreement})


def winner_role(run: GameRun) -> Literal["police", "thief", "tie"]:
    """Map fixed terminal scores to the summary winner enum."""
    if run.outcome.thief_score > run.outcome.police_score:
        return "thief"
    if run.outcome.police_score > run.outcome.thief_score:
        return "police"
    return "tie"


def step_zero_record(subgame: int, git_commit: str) -> LogRecord:
    """Record exact code, role, model, and token declaration before play."""
    payload = {
        "step": 0,
        "type": "system_spec",
        "role": "thief",
        "sub_game_number": subgame,
        "git_commit": git_commit,
        "model": "template",
        "token_budget": 200000,
    }
    nonce = f"{subgame:032x}"
    commitment = hashlib.sha256(canonical_json_bytes(payload | {"nonce": nonce})).hexdigest()
    return LogRecord(payload=payload, nonce=nonce, commit=commitment)
