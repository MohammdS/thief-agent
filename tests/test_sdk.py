from pathlib import Path
from unittest.mock import AsyncMock, patch

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
    expected = object()
    with patch(
        "thief_agent.sdk.run_peer_runtime", new_callable=AsyncMock,
    ) as run_runtime:
        run_runtime.return_value = expected
        actual = ThiefSdk().run_peer(
            Path("config/game.toml.example"),
            Path("config/game.json"),
        )
    assert actual is expected
    run_runtime.assert_awaited_once_with(
        Path("config/game.toml.example"), Path("config/game.json"),
        Path("artifacts/matches"), None,
    )
