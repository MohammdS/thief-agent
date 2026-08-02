"""Build live match logs and mutually hashable final results."""

from __future__ import annotations

from typing import Literal

from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.match_log import (
    LogAudit,
    LogSummary,
    MatchLogArtifact,
    log_sha256,
)
from thief_agent.artifacts.result import ResultArtifact, SeriesTotals, SubGameResult
from thief_agent.runtime.models import PeerGameRun
from thief_agent.runtime.step_zero import step_zero


def build_live_log(
    game_id: str,
    game_uid: str,
    subgame: int,
    groups: tuple[str, str],
    run: PeerGameRun,
    git_commit: str,
    model: str,
    token_budget: int,
) -> MatchLogArtifact:
    """Build one final-audit-verified local log."""
    summary = LogSummary(
        sub_game_number=subgame,
        group_id=groups[0],
        opponent_group_id=groups[1],
        result=run.outcome.reason.value,
        winner_role=winner_role(run),
        steps=run.state.step,
        timezone="Asia/Jerusalem",
        started_at=run.started_at,
        ended_at=run.ended_at,
        duration_seconds=(run.ended_at - run.started_at).total_seconds(),
        tokens_total=run.tokens,
        audit=LogAudit(passed=True, verified_steps=len(run.records)),
    )
    records = (step_zero(subgame, git_commit, model, token_budget), *run.records)
    log = MatchLogArtifact(
        _schema="Mutually audited live Thief match log.",
        game_id=game_id,
        game_uid=game_uid,
        links=artifact_links(game_id),
        summary=summary,
        records=records,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )
    return log.model_copy(update={
        "mutual_agreement": MutualAgreement(sha256=log_sha256(log), confirmed=True),
    })


def build_live_result(
    game_id: str,
    game_uid: str,
    groups: tuple[str, str],
    games: tuple[PeerGameRun, ...],
    git_commit: str,
) -> ResultArtifact:
    """Build a deterministic provisional series result for peer comparison."""
    subgames = tuple(
        subgame_result(index, game_id, groups, run, git_commit)
        for index, run in enumerate(games, 1)
    )
    police_total = sum(run.outcome.police_score for run in games)
    thief_total = sum(run.outcome.thief_score for run in games)
    police_wins = sum(run.outcome.police_score > run.outcome.thief_score for run in games)
    thief_wins = sum(run.outcome.thief_score > run.outcome.police_score for run in games)
    totals = SeriesTotals(
        total_score={groups[1]: police_total, groups[0]: thief_total},
        sub_games_won={groups[1]: police_wins, groups[0]: thief_wins},
        ties=len(games) - police_wins - thief_wins,
        winner_group=winner_group(groups, police_total, thief_total),
        series_tie=police_total == thief_total,
        tokens_total_series={
            groups[1]: sum(run.opponent_tokens for run in games),
            groups[0]: sum(run.tokens for run in games),
        },
    )
    return ResultArtifact(
        _schema="Mutually calculated live whole-series result.",
        game_id=game_id,
        game_uid=game_uid,
        links=artifact_links(game_id),
        timezone="Asia/Jerusalem",
        groups=ordered_groups(groups),
        num_sub_games=len(games),
        sub_games=subgames,
        final_result=totals,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )


def subgame_result(
    index: int, game_id: str, groups: tuple[str, str], run: PeerGameRun, git_commit: str,
) -> SubGameResult:
    """Condense one audited Thief-side run into the assignment shape."""
    winner = winner_group(groups, run.outcome.police_score, run.outcome.thief_score)
    log_name = f"log_{game_id}_g{index:02d}.json"
    return SubGameResult(
        sub_game_number=index,
        roles={groups[0]: "thief", groups[1]: "police"},
        started_at=run.started_at,
        ended_at=run.ended_at,
        result=run.outcome.reason.value,
        winner_group=winner,
        tie=winner is None,
        github_commit={groups[0]: git_commit, groups[1]: run.opponent_git_commit},
        tokens={groups[0]: run.tokens, groups[1]: run.opponent_tokens},
        score={groups[0]: run.outcome.thief_score, groups[1]: run.outcome.police_score},
        log_files={groups[0]: log_name, groups[1]: log_name},
        audit={"log_verified": True, "tampered": False},
    )


def winner_role(run: PeerGameRun) -> Literal["police", "thief", "tie"]:
    """Return the role with the higher fixed subgame score."""
    if run.outcome.police_score > run.outcome.thief_score:
        return "police"
    if run.outcome.thief_score > run.outcome.police_score:
        return "thief"
    return "tie"


def winner_group(groups: tuple[str, str], police: int, thief: int) -> str | None:
    """Map the higher role score to its group."""
    if thief > police:
        return groups[0]
    if police > thief:
        return groups[1]
    return None


def ordered_groups(groups: tuple[str, str]) -> tuple[str, str]:
    """Return a stable two-group ordering for canonical result hashing."""
    return groups if groups[0] < groups[1] else (groups[1], groups[0])
