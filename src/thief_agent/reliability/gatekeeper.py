"""Central deadline, retry, concurrency, and queue gatekeeper."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar

ResultT = TypeVar("ResultT")


class QueueFullError(RuntimeError):
    """Report deterministic rejection when the bounded queue is full."""


class TechnicalLoss(RuntimeError):
    """Report controlled external-call exhaustion without deadlock."""


@dataclass(slots=True)
class ExternalGatekeeper:
    """Run every external operation under the negotiated reliability limits."""

    timeout_seconds: float = 30
    retry_delay_seconds: float = 5
    max_retries: int = 3
    concurrency: int = 2
    queue_depth: int = 100
    _waiting: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _semaphore: asyncio.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        """Reject non-positive safety limits and create the semaphore."""
        if self.timeout_seconds <= 0 or self.retry_delay_seconds < 0:
            raise ValueError("deadline must be positive and retry delay non-negative")
        if self.max_retries < 0 or self.concurrency < 1 or self.queue_depth < 1:
            raise ValueError("retry, concurrency, and queue limits are invalid")
        self._semaphore = asyncio.Semaphore(self.concurrency)

    async def call(self, operation: Callable[[], Awaitable[ResultT]]) -> ResultT:
        """Execute with bounded admission, timeout, retry, and controlled failure."""
        await self._enter_queue()
        queued = True
        try:
            async with self._semaphore:
                await self._leave_queue()
                queued = False
                for attempt in range(self.max_retries + 1):
                    try:
                        return await asyncio.wait_for(operation(), self.timeout_seconds)
                    except (TimeoutError, OSError) as error:
                        if attempt == self.max_retries:
                            raise TechnicalLoss("external request exhausted retries") from error
                        await asyncio.sleep(self.retry_delay_seconds)
        finally:
            if queued:
                await self._leave_queue()
        raise AssertionError("unreachable gatekeeper state")

    async def _enter_queue(self) -> None:
        """Reserve one bounded waiting slot."""
        async with self._lock:
            if self._waiting >= self.queue_depth:
                raise QueueFullError("external request queue is full")
            self._waiting += 1

    async def _leave_queue(self) -> None:
        """Release one waiting slot after semaphore admission."""
        async with self._lock:
            self._waiting -= 1

