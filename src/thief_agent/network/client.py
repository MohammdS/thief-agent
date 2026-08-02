"""FastMCP client with one bounded typed call surface."""

from __future__ import annotations

from fastmcp import Client
from pydantic import BaseModel

from thief_agent.protocol.messages import HealthRequest, HealthResponse


class PeerClient:
    """Call a remote Police peer with explicit per-request deadlines."""

    def __init__(self, url: str, timeout_seconds: float = 30) -> None:
        """Store peer URL and positive response timeout."""
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        self._client = Client(url)
        self._timeout = timeout_seconds

    async def health(self, request: HealthRequest) -> HealthResponse:
        """Connect, call the health tool, and validate its typed result."""
        async with self._client:
            result = await self._client.call_tool(
                "health",
                {"request": request.model_dump(mode="json")},
                timeout=self._timeout,
            )
        data = result.structured_content or result.data
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        return HealthResponse.model_validate(data)
