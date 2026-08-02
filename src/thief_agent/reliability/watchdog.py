"""Heartbeat watchdog for bounded runtime termination."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from thief_agent.reliability.gatekeeper import TechnicalLoss


@dataclass(slots=True)
class Watchdog:
    """Track the last orchestrator heartbeat against a fixed deadline."""

    timeout_seconds: float = 60
    clock: Callable[[], float] = time.monotonic
    _last_heartbeat: float = field(init=False)

    def __post_init__(self) -> None:
        """Initialize from a positive timeout."""
        if self.timeout_seconds <= 0:
            raise ValueError("watchdog timeout must be positive")
        self._last_heartbeat = self.clock()

    def heartbeat(self) -> None:
        """Record visible orchestrator progress."""
        self._last_heartbeat = self.clock()

    def expired(self) -> bool:
        """Return whether the orchestrator missed its deadline."""
        return self.clock() - self._last_heartbeat > self.timeout_seconds

    def assert_alive(self) -> None:
        """Raise a controlled technical loss after watchdog expiry."""
        if self.expired():
            raise TechnicalLoss("watchdog expired")

