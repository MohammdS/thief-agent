"""Run the MCP server and outbound autonomous loop in one peer process."""

from __future__ import annotations

import asyncio
import subprocess
from contextlib import suppress
from pathlib import Path

from thief_agent.config import config_sha256, load_local_config, load_shared_config
from thief_agent.network.client import PeerClient
from thief_agent.network.server import build_server
from thief_agent.protocol.service import ProtocolService
from thief_agent.runtime.models import PeerSeriesRun
from thief_agent.runtime.series import PeerSeriesRunner


async def run_peer_runtime(
    local_path: Path,
    shared_path: Path,
    output: Path,
    declaration_path: Path | None,
) -> PeerSeriesRun:
    """Serve inbound tools while driving outbound commits and reveals."""
    local = load_local_config(local_path)
    shared = load_shared_config(shared_path)
    service = ProtocolService(shared.game_id, config_sha256(shared))
    server = build_server(service)
    server_task = asyncio.create_task(server.run_async(
        transport="http",
        host=local.peer.host,
        port=local.peer.port,
        path="/mcp",
        show_banner=True,
    ))
    try:
        await asyncio.sleep(0.5)
        if server_task.done():
            await server_task
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        client = PeerClient(
            local.peer.opponent_mcp_url,
            shared.network.response_timeout_seconds,
        )
        runner = PeerSeriesRunner(
            shared, local, service, client, output, commit, declaration_path,
        )
        return await runner.run()
    finally:
        server_task.cancel()
        with suppress(asyncio.CancelledError):
            await server_task
