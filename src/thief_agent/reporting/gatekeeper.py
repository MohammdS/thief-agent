"""Compose quota, token bucket, circuit, deadline, backoff, and retries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.reliability.rate_limit import CircuitBreaker, DailyQuota, TokenBucket

ResultT = TypeVar("ResultT")


@dataclass(slots=True)
class ReportingGatekeeper:
    """Protect Gmail from quota abuse, floods, hangs, and retry loops."""

    external: ExternalGatekeeper
    bucket: TokenBucket
    quota: DailyQuota
    circuit: CircuitBreaker

    async def call(self, operation: Callable[[], Awaitable[ResultT]]) -> ResultT:
        """Admit one logical delivery and update DOS circuit state."""
        self.circuit.before_call()
        self.bucket.consume()
        self.quota.consume()
        try:
            result = await self.external.call(operation)
        except Exception:
            self.circuit.failure()
            raise
        self.circuit.success()
        return result


def default_reporting_gatekeeper(state_dir: Path) -> ReportingGatekeeper:
    """Build the conservative Gmail gate used by the public CLI."""
    return ReportingGatekeeper(
        external=ExternalGatekeeper(
            timeout_seconds=30,
            retry_delay_seconds=5,
            max_retries=3,
            concurrency=1,
            queue_depth=10,
        ),
        bucket=TokenBucket(capacity=2, refill_per_second=1 / 60),
        quota=DailyQuota(state_dir / "gmail-quota.json", limit=20),
        circuit=CircuitBreaker(failure_threshold=3),
    )
