"""Check structural release requirements and intentional metadata blockers."""

from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = (
    "README.md", "PLAN.md", "TODO.md", "pyproject.toml", "uv.lock",
    "docs/PRD.md", "docs/PLAN.md", "docs/TODO.md", "config/game.json",
)
PLACEHOLDERS = ("GROUP_ID", "REPLACE_ME", "REPLACE_WITH_COMPANION")


def find_issues(root: Path, allow_placeholders: bool = False) -> list[str]:
    """Return missing-file and unresolved-metadata issues."""
    issues = [f"missing required file: {name}" for name in REQUIRED if not (root / name).is_file()]
    if allow_placeholders:
        return issues
    for name in ("README.md", "config/game.json", "config/game.toml.example"):
        path = root / name
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        if any(marker in content for marker in PLACEHOLDERS):
            issues.append(f"unresolved submission metadata: {name}")
    return issues


def main() -> int:
    """Run the submission check from the repository root."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()
    issues = find_issues(Path.cwd(), args.allow_placeholders)
    for issue in issues:
        print(issue)
    if issues:
        return 1
    print("Submission structure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
