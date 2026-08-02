"""Token bucket, persistent daily quota, and DOS circuit breaker."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from thief_agent.reliability.checkpoint import CheckpointStore


class RateLimitError(RuntimeError):
    """Report a local quota or token-bucket rejection."""


class CircuitOpenError(RuntimeError):
    """Report that repeated failures opened the DOS circuit."""


@dataclass(slots=True)
class TokenBucket:
    """Refill request tokens continuously up to a fixed capacity."""

    capacity: float
    refill_per_second: float
    clock: Callable[[], float] = time.monotonic
    _tokens: float = field(init=False)
    _updated: float = field(init=False)

    def __post_init__(self) -> None:
        """Initialize a full positive-capacity bucket."""
        if self.capacity <= 0 or self.refill_per_second <= 0:
            raise ValueError("token bucket values must be positive")
        self._tokens = self.capacity
        self._updated = self.clock()

    def consume(self, amount: float = 1) -> None:
        """Consume available tokens or reject without sleeping."""
        now = self.clock()
        self._tokens = min(
            self.capacity,
            self._tokens + (now - self._updated) * self.refill_per_second,
        )
        self._updated = now
        if amount <= 0 or self._tokens < amount:
            raise RateLimitError("token bucket exhausted")
        self._tokens -= amount


class DailyQuota:
    """Persist per-UTC-day external request consumption."""

    def __init__(self, path: Path, limit: int, now: Callable[[], datetime] | None = None) -> None:
        """Configure a positive quota and injectable UTC clock."""
        if limit < 1:
            raise ValueError("daily quota must be positive")
        self._store, self._limit = CheckpointStore(path), limit
        self._now = now or (lambda: datetime.now(UTC))

    def consume(self) -> None:
        """Atomically advance today's count or reject at the quota."""
        today = self._now().date().isoformat()
        data = self._store.load() or {"date": today, "count": 0}
        if data.get("date") != today:
            data = {"date": today, "count": 0}
        count = int(data["count"])
        if count >= self._limit:
            raise RateLimitError("daily quota exhausted")
        self._store.save({"date": today, "count": count + 1})


@dataclass(slots=True)
class CircuitBreaker:
    """Open after repeated external failures until explicitly reset by success."""

    failure_threshold: int = 3
    failures: int = 0
    is_open: bool = False

    def before_call(self) -> None:
        """Reject calls while the circuit is open."""
        if self.is_open:
            raise CircuitOpenError("external API circuit is open")

    def success(self) -> None:
        """Reset failure state after a successful request."""
        self.failures, self.is_open = 0, False

    def failure(self) -> None:
        """Count a failure and open at the configured threshold."""
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.is_open = True

