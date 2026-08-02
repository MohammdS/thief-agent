"""Single public business entry point for Thief clients."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from thief_agent import __version__
from thief_agent.config import config_sha256, load_shared_config


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
