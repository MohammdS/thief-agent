from datetime import UTC, datetime, timedelta

from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.result import ResultArtifact, SeriesTotals, SubGameResult


def unconfirmed_result() -> ResultArtifact:
    started = datetime(2026, 8, 2, tzinfo=UTC)
    ended = started + timedelta(seconds=30)
    teams = ("police-team", "thief-team")
    subgame = SubGameResult(
        sub_game_number=1,
        roles={"police-team": "police", "thief-team": "thief"},
        started_at=started,
        ended_at=ended,
        result="survival",
        winner_group="thief-team",
        tie=False,
        github_commit={"police-team": "a" * 40, "thief-team": "b" * 40},
        tokens={"police-team": 0, "thief-team": 18},
        score={"police-team": 5, "thief-team": 10},
        log_files={
            "police-team": "log-report-test_g01.json",
            "thief-team": "log-report-test_g01.json",
        },
        audit={"log_verified": True, "tampered": False},
    )
    totals = SeriesTotals(
        total_score={"police-team": 5, "thief-team": 10},
        sub_games_won={"police-team": 0, "thief-team": 1},
        ties=0,
        winner_group="thief-team",
        series_tie=False,
        tokens_total_series={"police-team": 0, "thief-team": 18},
    )
    return ResultArtifact(
        schema_description="Final result for the whole game series.",
        game_id="report-test",
        game_uid="00000000-0000-4000-8000-000000000001",
        links=artifact_links("report-test"),
        timezone="Asia/Jerusalem",
        groups=teams,
        num_sub_games=1,
        sub_games=(subgame,),
        final_result=totals,
        mutual_agreement=MutualAgreement(sha256="0" * 64, confirmed=False),
    )

