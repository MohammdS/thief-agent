import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.artifact_helpers import unconfirmed_result
from thief_agent.artifacts.agreed_config import build_agreed_config
from thief_agent.artifacts.common import MutualAgreement, artifact_links
from thief_agent.artifacts.declaration import (
    DeclarationArtifact,
    GroupDeclaration,
    HardwareSpec,
    McpServers,
    RepositoryLinks,
)
from thief_agent.artifacts.match_log import LogAudit, LogRecord, LogSummary, MatchLogArtifact
from thief_agent.artifacts.result import confirm_result, result_sha256
from thief_agent.artifacts.store import ArtifactStore
from thief_agent.config import load_shared_config


def test_store_writes_all_exact_artifact_names(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    config = load_shared_config(Path("config/game.json"))
    agreed = build_agreed_config(config, "uid", 1, ("police-team", "thief-team"))
    declaration = sample_declaration()
    log = sample_log()
    result = unconfirmed_result()
    paths = (
        store.write("declaration", "report-test", declaration),
        store.write("config", config.game_id, agreed, 1),
        store.write("log", "report-test", log, 1),
        store.write("result", "report-test", result),
    )
    assert [path.name for path in paths] == [
        "declaration_report-test.json",
        "config_UNCOUNTED-DEVELOPMENT_g01.json",
        "log_report-test_g01.json",
        "result_report-test.json",
    ]
    assert json.loads(paths[0].read_text(encoding="utf-8"))["_schema"]


def test_store_rejects_unsafe_ids_and_missing_subgame(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    with pytest.raises(ValueError, match="unsafe"):
        store.path_for("result", "../escape")
    with pytest.raises(ValueError, match="subgame"):
        store.path_for("log", "safe")


def test_result_agreement_requires_identical_hash() -> None:
    result = unconfirmed_result()
    digest = result_sha256(result)
    assert confirm_result(result, digest).mutual_agreement.confirmed
    with pytest.raises(ValueError, match="does not match"):
        confirm_result(result, "f" * 64)


def sample_declaration() -> DeclarationArtifact:
    now = datetime(2026, 8, 2, tzinfo=UTC)
    group = GroupDeclaration(
        group_id="thief-team",
        group_name="Thief Team",
        members=("student-id",),
        repos=RepositoryLinks(cop="https://example.test/cop", thief="https://example.test/thief"),
        mcp_servers=McpServers(cop="https://cop.test/mcp", thief="https://thief.test/mcp"),
        llm_model="template",
        hardware_spec=HardwareSpec(
            cpu_type="test", cpu_freq_mhz=1, cpu_cores=1, ram_gb=1,
            gpu_model="none", vram_gb=0,
        ),
        signature="signature",
    )
    return DeclarationArtifact(
        schema_description="Static declaration for the whole game.",
        game_id="report-test",
        game_uid="uid",
        links=artifact_links("report-test"),
        timezone="Asia/Jerusalem",
        game_started_at=now,
        num_sub_games=1,
        max_tokens_per_game=200000,
        groups={"group_1": group, "group_2": group},
    )


def sample_log() -> MatchLogArtifact:
    start = datetime(2026, 8, 2, tzinfo=UTC)
    summary = LogSummary(
        sub_game_number=1, group_id="thief-team", opponent_group_id="police-team",
        result="survival", winner_role="thief", steps=35, timezone="Asia/Jerusalem",
        started_at=start, ended_at=start + timedelta(seconds=30), duration_seconds=30,
        tokens_total=0, audit=LogAudit(passed=True, verified_steps=1),
    )
    record = LogRecord(payload={"step": 0}, nonce="0" * 32, commit="a" * 64)
    return MatchLogArtifact(
        schema_description="Per-subgame cryptographic match log.",
        game_id="report-test", game_uid="uid", links=artifact_links("report-test"),
        summary=summary, records=(record,),
        mutual_agreement=MutualAgreement(sha256="b" * 64, confirmed=True),
    )

