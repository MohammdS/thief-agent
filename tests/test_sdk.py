from pathlib import Path

from thief_agent.sdk import ThiefSdk


def test_doctor_reports_missing_config_without_failure(tmp_path: Path) -> None:
    report = ThiefSdk().doctor(tmp_path / "missing.json")
    assert report.version == "0.1.0"
    assert report.config_exists is False


def test_foundation_status_is_honest() -> None:
    assert "not implemented" in ThiefSdk().foundation_status()

