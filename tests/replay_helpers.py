from datetime import UTC, datetime, timedelta
from pathlib import Path

from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.match_log import (
    LogAudit,
    LogRecord,
    LogSummary,
    MatchLogArtifact,
    log_sha256,
)
from thief_agent.config import load_shared_config
from thief_agent.crypto.commit_reveal import TurnMaterial, seal_turn
from thief_agent.domain.types import Move, Role
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction


def replay_log() -> MatchLogArtifact:
    config = load_shared_config(Path("config/game.json"))
    records = (
        record(Role.THIEF, Move.SOUTH, 1, "I moved south", "01" * 32),
        record(Role.POLICE, Move.SOUTH, 1, "I moved south", "02" * 32),
    )
    start = datetime(2026, 8, 2, tzinfo=UTC)
    summary = LogSummary(
        sub_game_number=1,
        group_id="thief-team",
        opponent_group_id="police-team",
        result="running",
        winner_role="tie",
        steps=1,
        timezone="Asia/Jerusalem",
        started_at=start,
        ended_at=start + timedelta(seconds=1),
        duration_seconds=1,
        tokens_total=0,
        audit=LogAudit(passed=True, verified_steps=2),
    )
    log = MatchLogArtifact(
        schema_description="Replay test log.",
        game_id=config.game_id,
        game_uid="replay-test-uid",
        links=artifact_links(config.game_id),
        summary=summary,
        records=records,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )
    agreement = MutualAgreement(sha256=log_sha256(log), confirmed=True)
    return log.model_copy(update={"mutual_agreement": agreement})


def record(role: Role, move: Move, step: int, hint: str, nonce: str) -> LogRecord:
    material = TurnMaterial(
        game_id="UNCOUNTED-DEVELOPMENT",
        subgame=1,
        step=step,
        role=role,
        prior_state_sha256="b" * 64,
        action=TurnAction(kind=ActionKind.MOVE, move=move),
        hint=hint,
        intent=HintIntent.TRUTH,
    )
    sealed = seal_turn(material, nonce)
    payload = sealed.disclosure.model_dump(mode="json", exclude={"nonce"})
    return LogRecord(payload=payload, nonce=nonce, commit=sealed.commitment)
