"""Single public business entry point for Thief clients."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from thief_agent import __version__
from thief_agent.artifacts.match_log import MatchLogArtifact
from thief_agent.artifacts.result import ResultArtifact, result_sha256
from thief_agent.config import config_sha256, load_shared_config
from thief_agent.replay.verifier import ReplayVerifier


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Describe the local runtime without exposing secrets."""

    version: str
    python: str
    platform: str
    config_exists: bool


@dataclass(frozen=True, slots=True)
class ConfigReport:
    """Describe a successfully validated shared configuration."""

    game_id: str
    counted: bool
    subgames: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ReplayReport:
    """Summarize deterministic post-match verification."""

    status: str
    failures: tuple[str, ...]
    frames: int


@dataclass(frozen=True, slots=True)
class ResultReport:
    """Summarize whether a final result is mutually agreed and hash-valid."""

    game_id: str
    confirmed: bool
    sha256: str


class ThiefSdk:
    """Coordinate every supported Thief business operation."""

    def doctor(self, config_path: Path = Path("config/game.json")) -> DoctorReport:
        """Return safe environment diagnostics."""
        return DoctorReport(
            version=__version__,
            python=sys.version.split()[0],
            platform=platform.platform(),
            config_exists=config_path.is_file(),
        )

    def foundation_status(self) -> str:
        """Return the honest implementation status for scaffolded commands."""
        return "foundation-ready; gameplay milestones are not implemented yet"

    def validate_config(self, path: Path) -> ConfigReport:
        """Validate and identify one shared game configuration."""
        config = load_shared_config(path)
        return ConfigReport(
            game_id=config.game_id,
            counted=config.counted,
            subgames=config.series.subgames,
            sha256=config_sha256(config),
        )

    def verify_replay(self, log_path: Path, config_path: Path) -> ReplayReport:
        """Validate a saved log and return exact replay status."""
        log = MatchLogArtifact.model_validate_json(log_path.read_bytes())
        result = ReplayVerifier(load_shared_config(config_path)).verify(log)
        return ReplayReport(result.status, result.failures, len(result.frames))

    def validate_result(self, path: Path) -> ResultReport:
        """Require confirmed agreement and a matching canonical result hash."""
        result = ResultArtifact.model_validate_json(path.read_bytes())
        digest = result_sha256(result)
        confirmed = result.mutual_agreement.confirmed and result.mutual_agreement.sha256 == digest
        return ResultReport(result.game_id, confirmed, digest)
