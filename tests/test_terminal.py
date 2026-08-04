from pathlib import Path

import pytest

from thief_agent.config import load_shared_config
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord
from thief_agent.protocol.messages import Ack, CaptureClaimRequest
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.terminal import claim_public_capture


class CaptureTransport:
    def __init__(self) -> None:
        self.request: CaptureClaimRequest | None = None

    async def capture_claim(self, request: CaptureClaimRequest) -> Ack:
        self.request = request
        return Ack(message_id=request.envelope.message_id, accepted=True, detail="logged")


@pytest.mark.asyncio
async def test_public_barrier_capture_claim_hides_coordinate_and_binds_commit() -> None:
    config = load_shared_config(Path("config/game.json"))
    state = BoardState(
        7,
        7,
        Coord(3, 3),
        Coord(0, 0),
        frozenset({Coord(3, 3)}),
        1,
    )
    client = CaptureTransport()
    gate = ExternalGatekeeper(1, 0, 0, 1, 1)
    commitment = "d" * 64
    claimed = await claim_public_capture(
        config,
        1,
        4,
        state,
        commitment,
        client,
        gate,  # type: ignore[arg-type]
    )
    assert claimed == "barrier"
    assert client.request is not None
    assert client.request.reason == "barrier"
    assert client.request.evidence_sha256 == commitment
    assert "row" not in client.request.model_dump(mode="json")
