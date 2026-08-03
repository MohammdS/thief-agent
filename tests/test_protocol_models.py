from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from tests.protocol_helpers import (
    CONFIG_HASH,
    GAME_ID,
    STATE_HASH,
    action,
    envelope,
    reveal_request,
)
from thief_agent.config.models import PointConfig
from thief_agent.domain.types import Move, Role
from thief_agent.protocol.actions import ActionKind, TurnAction
from thief_agent.protocol.envelope import WireEnvelope
from thief_agent.protocol.machine import (
    MatchState,
    TurnState,
    match_machine,
    turn_machine,
)
from thief_agent.protocol.messages import RevealTurnRequest
from thief_agent.protocol.scent import ScentCell


def test_envelope_rejects_expiry_and_unknown_fields() -> None:
    expired = envelope(lifetime=-1)
    with pytest.raises(ValueError, match="expired"):
        expired.assert_fresh()
    data = envelope().model_dump(mode="python") | {"objective_position": [1, 2]}
    with pytest.raises(ValidationError):
        WireEnvelope.model_validate(data)


def test_envelope_rejects_naive_time() -> None:
    now = datetime.now(UTC)
    values = envelope().model_dump(mode="python")
    values["timestamp"] = now.replace(tzinfo=None)
    values["expires_at"] = now + timedelta(seconds=1)
    with pytest.raises(ValidationError, match="timezone"):
        WireEnvelope.model_validate(values)


def test_action_requires_exactly_one_matching_payload() -> None:
    with pytest.raises(ValidationError, match="requires only"):
        TurnAction(kind=ActionKind.MOVE)
    barrier = TurnAction(kind=ActionKind.BARRIER, barrier=PointConfig(row=0, col=1))
    assert barrier.move is None
    with pytest.raises(ValidationError):
        TurnAction(kind=ActionKind.BARRIER, move=Move.NORTH)


def test_match_machine_accepts_only_explicit_sequence() -> None:
    machine = match_machine()
    for state in (
        MatchState.NEGOTIATING,
        MatchState.STEP_ZERO,
        MatchState.RUNNING_SUBGAME,
        MatchState.FINAL_AUDIT,
        MatchState.AGREEING_RESULT,
        MatchState.REPORTING,
        MatchState.FINISHED,
    ):
        machine.transition(state)
    with pytest.raises(ValueError, match="illegal transition"):
        machine.transition(MatchState.ABORTED)


def test_turn_machine_has_controlled_loss_path() -> None:
    machine = turn_machine()
    machine.transition(TurnState.COMPUTING_MOVE)
    machine.transition(TurnState.TECHNICAL_LOSS)
    assert machine.state is TurnState.TECHNICAL_LOSS


def test_envelope_identity_values() -> None:
    request = envelope()
    assert (request.game_id, request.sender) == (GAME_ID, Role.POLICE)
    assert (request.config_sha256, request.prior_state_sha256) == (CONFIG_HASH, STATE_HASH)


def test_live_reveal_contains_heatmap_but_rejects_physical_action() -> None:
    request = reveal_request()
    payload = request.model_dump(mode="json")
    assert "scent_heatmap" in payload
    assert "action" not in payload
    assert "move" not in payload
    with pytest.raises(ValidationError, match="Extra inputs"):
        RevealTurnRequest.model_validate(payload | {"action": action().model_dump(mode="json")})


def test_scent_heatmap_requires_unique_row_major_cells() -> None:
    reversed_cells = (
        ScentCell(row=1, col=0, intensity=0.4),
        ScentCell(row=0, col=0, intensity=0.9),
    )
    with pytest.raises(ValidationError, match="row-major"):
        RevealTurnRequest(
            envelope=envelope(),
            scent_heatmap=reversed_cells,
            hint="scent only",
        )
    duplicate_cells = (
        ScentCell(row=0, col=0, intensity=0.9),
        ScentCell(row=0, col=0, intensity=0.8),
    )
    with pytest.raises(ValidationError, match="unique"):
        RevealTurnRequest(
            envelope=envelope(),
            scent_heatmap=duplicate_cells,
            hint="scent only",
        )
