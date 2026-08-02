"""Persistent FastMCP client for the test-only Police stub process."""

from __future__ import annotations

from fastmcp import Client
from pydantic import BaseModel

from thief_agent.qualification.models import StubTurnRequest, StubTurnResponse


class StubClient:
    """Call the separate qualification stub without importing Police runtime code."""

    def __init__(self, url: str) -> None:
        """Configure one persistent FastMCP connection."""
        self._client = Client(url)

    async def __aenter__(self) -> StubClient:
        """Open the persistent MCP session."""
        await self._client.__aenter__()  # type: ignore[no-untyped-call]
        return self

    async def __aexit__(self, *args: object) -> None:
        """Close the MCP session."""
        await self._client.__aexit__(*args)  # type: ignore[no-untyped-call]

    async def health(self) -> bool:
        """Return whether the stub process is ready."""
        result = await self._client.call_tool("stub_health", timeout=2)
        data = result.structured_content or result.data
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        return bool(data["ready"])

    async def turn(self, request: StubTurnRequest) -> StubTurnResponse:
        """Request and strictly validate one stub-originated turn."""
        result = await self._client.call_tool(
            "scripted_police_turn",
            {"request": request.model_dump(mode="json")},
            timeout=5,
        )
        data = result.structured_content or result.data
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        return StubTurnResponse.model_validate(data)
