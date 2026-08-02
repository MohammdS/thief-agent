import asyncio
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from thief_agent.qualification.client import StubClient
from thief_agent.qualification.series import run_qualification


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


async def wait_ready(url: str) -> None:
    for _ in range(40):
        try:
            async with StubClient(url) as client:
                if await client.health():
                    return
        except Exception:
            await asyncio.sleep(0.1)
    raise AssertionError("qualification stub did not start")


@pytest.mark.asyncio
async def test_six_game_separate_process_qualification(tmp_path: Path) -> None:
    port = free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    process = subprocess.Popen(
        [sys.executable, "-m", "tests.support.police_stub", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        await wait_ready(url)
        summary = await run_qualification(url, tmp_path, "a" * 40)
        assert len(summary.games) == 6
        assert summary.all_terminated and summary.all_verified
        assert summary.corrupted_replay_status == "TAMPERED"
        assert len(list(tmp_path.glob("log_*_g*.json"))) == 6
        assert (tmp_path / "result_UNCOUNTED-DEVELOPMENT.json").is_file()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

