import json
from pathlib import Path

from tests.artifact_helpers import unconfirmed_result
from tests.replay_helpers import replay_log
from thief_agent.artifacts.result import confirm_result, result_sha256
from thief_agent.cli import main


def test_doctor_command_emits_json(capsys: object) -> None:
    assert main(["doctor"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["version"] == "0.1.0"


def test_peer_command_is_available(capsys: object) -> None:
    assert main(["peer"]) == 0
    assert "foundation-ready" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_validate_command_reports_config_hash(capsys: object) -> None:
    assert main(["validate"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["subgames"] == 6
    assert len(output["sha256"]) == 64


def test_replay_command_reports_exact_verified_status(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "log.json"
    path.write_text(replay_log().model_dump_json(by_alias=True), encoding="utf-8")
    assert main(["replay", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "Verified OK"  # type: ignore[attr-defined]


def test_report_command_requires_valid_mutual_hash(tmp_path: Path, capsys: object) -> None:
    result = unconfirmed_result()
    result = confirm_result(result, result_sha256(result))
    path = tmp_path / "result.json"
    path.write_text(result.model_dump_json(by_alias=True), encoding="utf-8")
    assert main(["report", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["confirmed"] is True  # type: ignore[attr-defined]
