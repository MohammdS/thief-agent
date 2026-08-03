"""FastMCP Streamable HTTP server exposing the versioned peer tools."""

from __future__ import annotations

import argparse

from fastmcp import FastMCP

from thief_agent.crypto.audit import AuditResult, FinalAuditRequest
from thief_agent.protocol.messages import (
    Ack,
    CaptureClaimRequest,
    CommitTurnRequest,
    HealthRequest,
    HealthResponse,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)
from thief_agent.protocol.service import ProtocolService


def build_server(service: ProtocolService) -> FastMCP:
    """Create a FastMCP server whose tools delegate only to the protocol service."""
    server = FastMCP("thief-peer")

    @server.tool
    def health(request: HealthRequest) -> HealthResponse:
        """Return liveness and contract identity."""
        return service.health(request)

    @server.tool
    def negotiate(request: NegotiationRequest) -> Ack:
        """Negotiate configuration and counted-series rules."""
        return service.negotiate(request)

    @server.tool
    def commit_turn(request: CommitTurnRequest) -> Ack:
        """Accept one public commitment hash."""
        return service.commit_turn(request)

    @server.tool
    def reveal_turn(request: RevealTurnRequest) -> Ack:
        """Accept scent and hint without action, nonce, or intent."""
        return service.reveal_turn(request)

    @server.tool
    def capture_claim(request: CaptureClaimRequest) -> Ack:
        """Record a capture claim for later audit."""
        return service.capture_claim(request)

    @server.tool
    def final_audit(request: FinalAuditRequest) -> AuditResult:
        """Verify final nonce disclosures."""
        return service.final_audit(request)

    @server.tool
    def propose_result(request: ResultProposalRequest) -> Ack:
        """Record the Police peer's independently hashed result."""
        return service.propose_result(request)

    return server


def main() -> int:
    """Run a standalone testable Streamable HTTP peer process."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--game-id", default="UNCOUNTED-DEVELOPMENT")
    parser.add_argument("--config-hash", required=True)
    args = parser.parse_args()
    server = build_server(ProtocolService(args.game_id, args.config_hash))
    server.run(transport="http", host=args.host, port=args.port, path="/mcp", show_banner=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
