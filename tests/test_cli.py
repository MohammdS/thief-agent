import json

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

