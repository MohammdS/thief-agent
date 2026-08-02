"""Compose quota, token bucket, circuit, deadline, backoff, and retries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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

