from pathlib import Path

from scripts.submission_check import find_issues


def test_placeholders_are_release_blockers() -> None:
    issues = find_issues(Path.cwd())
    assert any("unresolved submission metadata" in issue for issue in issues)


def test_placeholders_can_be_allowed_during_development() -> None:
    assert find_issues(Path.cwd(), allow_placeholders=True) == []

