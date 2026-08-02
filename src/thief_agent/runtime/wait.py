"""Bounded polling for state delivered asynchronously by the peer server."""

from __future__ import annotations

import asyncio
from collections.abc import Callable


async def wait_for_value[ValueT](
    lookup: Callable[[], ValueT | None],
    timeout_seconds: float,
    label: str,
) -> ValueT:
    """Return an asynchronously delivered value or fail at the deadline."""
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        value = lookup()
        if value is not None:
            return value
        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError(f"timed out waiting for {label}")
        await asyncio.sleep(0.02)
