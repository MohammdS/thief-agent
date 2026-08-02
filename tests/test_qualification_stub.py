import pytest
from fastmcp import Client

from tests.support.police_stub import build_stub
from thief_agent.qualification.models import StubTurnRequest, StubTurnResponse


@pytest.mark.asyncio
async def test_stub_originates_valid_committed_police_turn() -> None:
    request = StubTurnRequest(
        game_id="stub-test", subgame=1, step=1, prior_state_sha256="a" * 64,
    )
    async with Client(build_stub()) as client:
        result = await client.call_tool(
            "scripted_police_turn", {"request": request.model_dump(mode="json")},
        )
    response = StubTurnResponse.model_validate(result.structured_content)
    assert response.disclosure.role.value == "police"
    assert len(response.commitment) == 64

