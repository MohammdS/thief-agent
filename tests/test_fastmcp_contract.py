import asyncio
import socket
import subprocess
import sys

import pytest

from tests.protocol_helpers import CONFIG_HASH, GAME_ID, envelope
from thief_agent.network.client import PeerClient
from thief_agent.protocol.messages import HealthRequest


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@pytest.mark.asyncio
async def test_separate_process_streamable_http_contract() -> None:
    port = free_port()
    command = [
        sys.executable,
        "-m",
        "thief_agent.network.server",
        "--port",
        str(port),
        "--game-id",
        GAME_ID,
        "--config-hash",
        CONFIG_HASH,
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        response = await wait_for_health(port)
        assert response.status == "ok"
        assert response.config_sha256 == CONFIG_HASH
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


async def wait_for_health(port: int):
    last_error: Exception | None = None
    for _ in range(40):
        try:
            client = PeerClient(f"http://127.0.0.1:{port}/mcp", timeout_seconds=2)
            return await client.health(HealthRequest(envelope=envelope()))
        except Exception as error:
            last_error = error
            await asyncio.sleep(0.1)
    raise AssertionError(f"FastMCP peer failed to start: {last_error}")

