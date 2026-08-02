"""Persistent duplicate-report suppression by attachment hash."""

from __future__ import annotations

from pathlib import Path

from thief_agent.reliability.checkpoint import CheckpointStore


class DuplicateReportError(RuntimeError):
    """Report that the same final artifact was already delivered."""


class DuplicateRegistry:
    """Persist hashes only after successful dry-run or live delivery."""

    def __init__(self, path: Path) -> None:
        """Store the registry path."""
        self._store = CheckpointStore(path)

    def ensure_new(self, digest: str) -> None:
        """Reject a digest already recorded as delivered."""
        if digest in self._hashes():
            raise DuplicateReportError("result attachment was already delivered")

    def record(self, digest: str) -> None:
        """Atomically add a successfully delivered digest."""
        hashes = self._hashes()
        hashes.add(digest)
        self._store.save({"sha256": sorted(hashes)})

    def _hashes(self) -> set[str]:
        """Load the current digest set."""
        payload = self._store.load() or {"sha256": []}
        values = payload.get("sha256", [])
        if not isinstance(values, list):
            raise ValueError("duplicate registry is malformed")
        return {str(value) for value in values}

