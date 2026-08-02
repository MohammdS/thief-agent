"""Launch the separate Police stub and run six uncounted subgames."""

from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
from pathlib import Path

from thief_agent.qualification.client import StubClient
from thief_agent.qualification.series import run_qualification


def free_port() -> int:
    """Reserve an available loopback port for the stub process."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


async def wait_until_ready(url: str) -> None:
    """Poll bounded stub health until ready or fail visibly."""
    last_error: Exception | None = None
    for _ in range(50):
        try:
            async with StubClient(url) as client:
                if await client.health():
                    return
        except Exception as error:
            last_error = error
        await asyncio.sleep(0.1)
    raise RuntimeError(f"qualification stub failed to start: {last_error}")


async def run() -> int:
    """Run qualification and print its strict JSON summary."""
    port = free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    process = subprocess.Popen(
        [sys.executable, "-m", "tests.support.police_stub", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        await wait_until_ready(url)
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
        ).stdout.strip()
        summary = await run_qualification(
            url, Path("artifacts/qualification"), commit,
        )
        print(summary.model_dump_json(indent=2))
        return 0 if summary.all_terminated and summary.all_verified else 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> int:
    """Run the asynchronous qualification entry point."""
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())

