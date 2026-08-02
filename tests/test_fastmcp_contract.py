import asyncio
import socket
import subprocess
import sys
from datetime import UTC, datetime

import pytest

from tests.protocol_helpers import CONFIG_HASH, GAME_ID, envelope, material
from thief_agent.crypto.audit import AuditRecord, FinalAuditRequest, RevealedTurn
from thief_agent.crypto.commit_reveal import seal_turn
from thief_agent.network.client import PeerClient
from thief_agent.protocol.messages import (
    CommitTurnRequest,
    HealthRequest,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)


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
        await exercise_turn_contract(port)
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


async def exercise_turn_contract(port: int) -> None:
    client = PeerClient(f"http://127.0.0.1:{port}/mcp", timeout_seconds=2)
    negotiation = NegotiationRequest(
        envelope=envelope(step=0, subgame=0),
        contract_version="1.0",
        counted=False,
        subgames=1,
        sender_group_id="police-group",
        game_uid="network-contract",
        series_started_at=datetime.now(UTC),
    )
    assert (await client.negotiate(negotiation)).accepted
    sealed = seal_turn(material())
    assert (await client.commit_turn(CommitTurnRequest(
        envelope=envelope(), commitment=sealed.commitment,
    ))).accepted
    disclosure = sealed.disclosure
    assert (await client.reveal_turn(RevealTurnRequest(
        envelope=envelope(), action=disclosure.action, hint=disclosure.hint,
    ))).accepted
    record = AuditRecord(
        reveal=RevealedTurn(
            commitment=sealed.commitment,
            action=disclosure.action,
            hint=disclosure.hint,
        ),
        disclosure=disclosure,
    )
    audit = await client.final_audit(FinalAuditRequest(
        envelope=envelope(), records=(record,),
    ))
    assert audit.status == "Verified OK"
    proposal = ResultProposalRequest(
        envelope=envelope(),
        phase="subgame",
        sender_group_id="police-group",
        result_sha256="c" * 64,
        police_score=20,
        thief_score=5,
        tokens_total=0,
        git_commit="d" * 40,
    )
    assert (await client.propose_result(proposal)).accepted
