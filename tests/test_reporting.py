from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.artifact_helpers import unconfirmed_result
from thief_agent.artifacts.result import confirm_result, result_sha256
from thief_agent.reliability.gatekeeper import ExternalGatekeeper, TechnicalLoss
from thief_agent.reliability.rate_limit import CircuitBreaker, DailyQuota, TokenBucket
from thief_agent.reporting.duplicates import DuplicateReportError
from thief_agent.reporting.gatekeeper import ReportingGatekeeper
from thief_agent.reporting.gmail import GmailReporter


class MockExecute:
    def __init__(self, response: object) -> None:
        self.response = response

    def execute(self) -> object:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class MockService:
    def __init__(self, response: object) -> None:
        self.response = response
        self.body: dict[str, str] | None = None

    def users(self) -> MockService:
        return self

    def messages(self) -> MockService:
        return self

    def send(self, *, userId: str, body: dict[str, str]) -> MockExecute:
        assert userId == "me"
        self.body = body
        return MockExecute(self.response)


def guard(tmp_path: Path, failures: int = 3) -> ReportingGatekeeper:
    return ReportingGatekeeper(
        ExternalGatekeeper(0.5, 0, 0, 2, 100),
        TokenBucket(2, 1),
        DailyQuota(tmp_path / "quota.json", 20),
        CircuitBreaker(failures),
    )


def write_result(path: Path, confirmed: bool = True) -> Path:
    result = unconfirmed_result()
    if confirmed:
        result = confirm_result(result, result_sha256(result))
    path.write_text(result.model_dump_json(by_alias=True), encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_dry_run_writes_mime_and_suppresses_duplicate(tmp_path: Path) -> None:
    result_path = write_result(tmp_path / "result.json")
    reporter = GmailReporter("dry-run", tmp_path / "state", guard(tmp_path))
    receipt = await reporter.send(result_path)
    assert receipt.mode == "dry-run"
    payload = json.loads(receipt.dry_run_path.read_text())  # type: ignore[union-attr]
    assert payload["raw"]
    with pytest.raises(DuplicateReportError):
        await reporter.send(result_path)


@pytest.mark.asyncio
async def test_unconfirmed_result_is_never_reported(tmp_path: Path) -> None:
    path = write_result(tmp_path / "result.json", confirmed=False)
    with pytest.raises(ValueError, match="mutual agreement"):
        await GmailReporter("dry-run", tmp_path / "state", guard(tmp_path)).send(path)


@pytest.mark.asyncio
async def test_live_delivery_uses_mocked_gmail_and_records_id(tmp_path: Path) -> None:
    service = MockService({"id": "gmail-message-id"})
    reporter = GmailReporter("live", tmp_path / "state", guard(tmp_path), service=service)
    receipt = await reporter.send(write_result(tmp_path / "result.json"))
    assert receipt.message_id == "gmail-message-id"
    assert service.body and service.body["raw"]


@pytest.mark.asyncio
async def test_repeated_gmail_failures_open_circuit(tmp_path: Path) -> None:
    reporter = GmailReporter(
        "live", tmp_path / "state", guard(tmp_path, failures=1),
        service=MockService(RuntimeError("429")),
    )
    path = write_result(tmp_path / "result.json")
    with pytest.raises(TechnicalLoss):
        await reporter.send(path)
    assert reporter._gatekeeper.circuit.is_open  # type: ignore[attr-defined]
