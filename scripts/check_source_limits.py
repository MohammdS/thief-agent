"""Fail when a production Python file exceeds the coursework line limit."""

from __future__ import annotations

from pathlib import Path

LIMIT = 150


def oversized_files(root: Path) -> list[tuple[Path, int]]:
    """Return source files whose physical line count exceeds the limit."""
    files = sorted((root / "src").rglob("*.py"))
    return [(path, len(path.read_text(encoding="utf-8").splitlines())) for path in files
            if len(path.read_text(encoding="utf-8").splitlines()) > LIMIT]


def main() -> int:
    """Print violations and return a shell-friendly status."""
    failures = oversized_files(Path.cwd())
    for path, count in failures:
        print(f"{path}: {count} lines (limit {LIMIT})")
    if failures:
        return 1
    print(f"All production Python files are <= {LIMIT} lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

