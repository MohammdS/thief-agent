"""Build declaration, config, and final result around qualification logs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.declaration import (
    DeclarationArtifact,
    GroupDeclaration,
    HardwareSpec,
    McpServers,
    RepositoryLinks,
)
from thief_agent.artifacts.result import (
    ResultArtifact,
    SeriesTotals,
    SubGameResult,
    confirm_result,
    result_sha256,
)
from thief_agent.config.models import SharedConfig
from thief_agent.qualification.game import GameRun

THIEF_TEAM = "GROUP_ID"
STUB_TEAM = "qualification-police-stub"


def declaration(config: SharedConfig, stub_url: str) -> DeclarationArtifact:
    """Create an explicitly uncounted two-peer qualification declaration."""
    start = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    thief = group_declaration(
        THIEF_TEAM,
        "https://github.com/MohammdS/thief-agent",
        "https://REPLACE_WITH_COMPANION_POLICE_REPOSITORY",
        "http://127.0.0.1:8002/mcp",
        "template",
    )
    stub = group_declaration(
        STUB_TEAM, "test-only", "test-only", stub_url, "deterministic-script",
    )
    return DeclarationArtifact(
        _schema="Uncounted qualification declaration using a test-only stub.",
        game_id=config.game_id,
        game_uid="qualification-series",
        links=artifact_links(config.game_id),
        timezone="Asia/Jerusalem",
        game_started_at=start,
        game_ended_at=start + timedelta(minutes=6),
        num_sub_games=6,
        max_tokens_per_game=config.series.token_budget,
        groups={"group_1": thief, "group_2": stub},
    )


def result(config: SharedConfig, runs: tuple[GameRun, ...], git_commit: str) -> ResultArtifact:
    """Create and self-confirm the deterministic qualification result artifact."""
    subgames = tuple(subgame_result(index, run, git_commit) for index, run in enumerate(runs, 1))
    police_total = sum(run.outcome.police_score for run in runs)
    thief_total = sum(run.outcome.thief_score for run in runs)
    police_wins = sum(run.outcome.police_score > run.outcome.thief_score for run in runs)
    thief_wins = sum(run.outcome.thief_score > run.outcome.police_score for run in runs)
    totals = SeriesTotals(
        total_score={STUB_TEAM: police_total, THIEF_TEAM: thief_total},
        sub_games_won={STUB_TEAM: police_wins, THIEF_TEAM: thief_wins},
        ties=6 - police_wins - thief_wins,
        winner_group=winner(police_total, thief_total),
        series_tie=police_total == thief_total,
        tokens_total_series={STUB_TEAM: 0, THIEF_TEAM: sum(run.tokens for run in runs)},
    )
    artifact = ResultArtifact(
        _schema="Uncounted six-subgame qualification result.",
        game_id=config.game_id,
        game_uid="qualification-series",
        links=artifact_links(config.game_id),
        timezone="Asia/Jerusalem",
        groups=(STUB_TEAM, THIEF_TEAM),
        num_sub_games=6,
        sub_games=subgames,
        final_result=totals,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )
    return confirm_result(artifact, result_sha256(artifact))


def group_declaration(
    group_id: str, thief_repo: str, police_repo: str, mcp_url: str, model: str,
) -> GroupDeclaration:
    """Build one safe qualification group declaration."""
    return GroupDeclaration(
        group_id=group_id,
        group_name=group_id,
        members=("REPLACE_STUDENT_ID",),
        repos=RepositoryLinks(cop=police_repo, thief=thief_repo),
        mcp_servers=McpServers(cop=mcp_url, thief=mcp_url),
        llm_model=model,
        hardware_spec=HardwareSpec(
            cpu_type="qualification-host", cpu_freq_mhz=0, cpu_cores=1,
            ram_gb=1, gpu_model="not-declared-in-uncounted-test", vram_gb=0,
        ),
        signature="uncounted-qualification",
    )


def subgame_result(index: int, run: GameRun, git_commit: str) -> SubGameResult:
    """Condense one run into the supplied result shape."""
    start = datetime(2026, 8, 2, 12, index, tzinfo=UTC)
    return SubGameResult(
        sub_game_number=index,
        roles={STUB_TEAM: "police", THIEF_TEAM: "thief"},
        started_at=start,
        ended_at=start + timedelta(seconds=max(1, run.state.step)),
        result=run.outcome.reason.value,
        winner_group=winner(run.outcome.police_score, run.outcome.thief_score),
        tie=run.outcome.police_score == run.outcome.thief_score,
        github_commit={STUB_TEAM: "test-only", THIEF_TEAM: git_commit},
        tokens={STUB_TEAM: 0, THIEF_TEAM: run.tokens},
        score={STUB_TEAM: run.outcome.police_score, THIEF_TEAM: run.outcome.thief_score},
        log_files={
            STUB_TEAM: f"log_{config_name()}_g{index:02d}.json",
            THIEF_TEAM: f"log_{config_name()}_g{index:02d}.json",
        },
        audit={"log_verified": True, "tampered": False},
    )


def winner(police_score: int, thief_score: int) -> str | None:
    """Return the higher-scoring qualification group or None for a tie."""
    if police_score > thief_score:
        return STUB_TEAM
    if thief_score > police_score:
        return THIEF_TEAM
    return None


def config_name() -> str:
    """Return the fixed uncounted qualification game ID."""
    return "UNCOUNTED-DEVELOPMENT"
