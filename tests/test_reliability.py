import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reliability.gatekeeper import (
    ExternalGatekeeper,
    QueueFullError,
    TechnicalLoss,
)
from thief_agent.reliability.rate_limit import (
    CircuitBreaker,
    CircuitOpenError,
    DailyQuota,
    RateLimitError,
    TokenBucket,
)
from thief_agent.reliability.watchdog import Watchdog


def test_checkpoint_round_trip_and_replacement(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "state" / "checkpoint.json")
    assert store.load() is None
    store.save({"step": 1})
    store.save({"step": 2})
    assert store.load() == {"step": 2}
    assert list((tmp_path / "state").iterdir()) == [store.path]


@pytest.mark.asyncio
async def test_gatekeeper_retries_then_returns_and_times_out() -> None:
    attempts = 0
    gate = ExternalGatekeeper(0.05, 0, 2, 2, 100)

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise OSError("temporary")
        return "ok"

    assert await gate.call(flaky) == "ok"
    assert attempts == 3

    async def slow() -> None:
        await asyncio.sleep(1)

    with pytest.raises(TechnicalLoss):
        await ExternalGatekeeper(0.01, 0, 0, 1, 1).call(slow)


@pytest.mark.asyncio
async def test_gatekeeper_enforces_concurrency_and_queue_depth() -> None:
    gate = ExternalGatekeeper(1, 0, 0, 1, 1)
    release = asyncio.Event()

    async def blocked() -> str:
        await release.wait()
        return "done"

    first = asyncio.create_task(gate.call(blocked))
    await asyncio.sleep(0)
    second = asyncio.create_task(gate.call(blocked))
    await asyncio.sleep(0)
    with pytest.raises(QueueFullError):
        await gate.call(blocked)
    release.set()
    assert await asyncio.gather(first, second) == ["done", "done"]


def test_token_bucket_refills_and_quota_persists(tmp_path: Path) -> None:
    clock = [0.0]
    bucket = TokenBucket(1, 1, lambda: clock[0])
    bucket.consume()
    with pytest.raises(RateLimitError):
        bucket.consume()
    clock[0] = 1
    bucket.consume()

    today = datetime(2026, 8, 2, tzinfo=UTC)
    quota = DailyQuota(tmp_path / "quota.json", 1, lambda: today)
    quota.consume()
    with pytest.raises(RateLimitError):
        quota.consume()
    tomorrow = today + timedelta(days=1)
    DailyQuota(tmp_path / "quota.json", 1, lambda: tomorrow).consume()


def test_circuit_and_watchdog_fail_closed() -> None:
    circuit = CircuitBreaker(2)
    circuit.failure()
    circuit.failure()
    with pytest.raises(CircuitOpenError):
        circuit.before_call()
    circuit.success()
    circuit.before_call()

    clock = [0.0]
    watchdog = Watchdog(60, lambda: clock[0])
    clock[0] = 61
    with pytest.raises(TechnicalLoss, match="watchdog"):
        watchdog.assert_alive()
    watchdog.heartbeat()
    watchdog.assert_alive()

