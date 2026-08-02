from pathlib import Path
from unittest.mock import patch

from thief_agent.sdk import ThiefSdk


def test_doctor_reports_missing_config_without_failure(tmp_path: Path) -> None:
    report = ThiefSdk().doctor(tmp_path / "missing.json")
    assert report.version == "0.1.0"
    assert report.config_exists is False


def test_sdk_validates_default_shared_configuration() -> None:
    report = ThiefSdk().validate_config(Path("config/game.json"))
    assert report.subgames == 6
    assert len(report.sha256) == 64


def test_sdk_runs_peer_with_local_network_settings() -> None:
    with patch("thief_agent.sdk.build_server") as build_server:
        ThiefSdk().run_peer(
            Path("config/game.toml.example"),
            Path("config/game.json"),
        )
    build_server.return_value.run.assert_called_once_with(
        transport="http",
        host="127.0.0.1",
        port=8002,
        path="/mcp",
        show_banner=True,
    )
