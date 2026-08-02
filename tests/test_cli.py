import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.artifact_helpers import unconfirmed_result
from tests.replay_helpers import replay_log
from thief_agent.artifacts.result import confirm_result, result_sha256
from thief_agent.cli import main


def test_doctor_command_emits_json(capsys: object) -> None:
    assert main(["doctor"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["version"] == "0.1.0"


def test_peer_command_starts_configured_server() -> None:
    with patch("thief_agent.cli.ThiefSdk.run_peer") as run_peer:
        run_peer.return_value = SimpleNamespace(result_path=Path("result.json"), games=())
        assert main(["peer", "--config", "local.toml", "--game-config", "game.json"]) == 0
    run_peer.assert_called_once_with(
        Path("local.toml"), Path("game.json"), Path("artifacts/matches"), None,
    )


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


def test_report_command_can_write_protected_dry_run(tmp_path: Path, capsys: object) -> None:
    result = unconfirmed_result()
    result = confirm_result(result, result_sha256(result))
    path = tmp_path / "result.json"
    path.write_text(result.model_dump_json(by_alias=True), encoding="utf-8")
    state = tmp_path / "reporting"
    assert main(["report", str(path), "--mode", "dry-run", "--state-dir", str(state)]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["mode"] == "dry-run"
    assert Path(output["dry_run_path"]).is_file()
