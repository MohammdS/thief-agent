"""FastMCP client with one bounded typed call surface."""

from __future__ import annotations

from typing import TypeVar

from fastmcp import Client
from pydantic import BaseModel

from thief_agent.crypto.audit import AuditResult, FinalAuditRequest
from thief_agent.protocol.messages import (
    Ack,
    CommitTurnRequest,
    HealthRequest,
    HealthResponse,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class PeerClient:
    """Call a remote peer with explicit per-request deadlines."""

    def __init__(self, url: str, timeout_seconds: float = 30) -> None:
        """Store peer URL and positive response timeout."""
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        self._client = Client(url)
        self._timeout = timeout_seconds

    async def health(self, request: HealthRequest) -> HealthResponse:
        """Validate remote role, protocol, and configuration identity."""
        return await self._call("health", request, HealthResponse)

    async def negotiate(self, request: NegotiationRequest) -> Ack:
        """Submit the locked series anchor and rules."""
        return await self._call("negotiate", request, Ack)

    async def commit_turn(self, request: CommitTurnRequest) -> Ack:
        """Publish one opaque turn commitment."""
        return await self._call("commit_turn", request, Ack)

    async def reveal_turn(self, request: RevealTurnRequest) -> Ack:
        """Reveal action and hint after both commitments are locked."""
        return await self._call("reveal_turn", request, Ack)

    async def final_audit(self, request: FinalAuditRequest) -> AuditResult:
        """Disclose final turn secrets and parse the peer audit."""
        return await self._call("final_audit", request, AuditResult)

    async def propose_result(self, request: ResultProposalRequest) -> Ack:
        """Publish one independently calculated result digest."""
        return await self._call("propose_result", request, Ack)

    async def _call(
        self,
        tool: str,
        request: BaseModel,
        response_type: type[ResponseT],
    ) -> ResponseT:
        """Execute one MCP tool and validate its structured response."""
        async with self._client:
            result = await self._client.call_tool(
                tool,
                {"request": request.model_dump(mode="json")},
                timeout=self._timeout,
            )
        data = result.structured_content or result.data
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        return response_type.model_validate(data)
