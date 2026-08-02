"""Deterministic message-only Police stub for uncounted qualification."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

from fastmcp import FastMCP

from thief_agent.config.models import PointConfig
from thief_agent.crypto.commit_reveal import TurnMaterial, seal_turn
from thief_agent.domain.board import destination
from thief_agent.domain.types import Coord, Move, Role
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction
from thief_agent.qualification.models import StubTurnRequest, StubTurnResponse


@dataclass(slots=True)
class StubState:
    position: Coord = field(default_factory=lambda: Coord(0, 0))
    barriers: set[Coord] = field(default_factory=set)


def build_stub() -> FastMCP:
    server = FastMCP("qualification-police-stub")
    states: dict[int, StubState] = {}

    @server.tool
    def stub_health() -> dict[str, bool]:
        """Report readiness without changing scripted state."""
        return {"ready": True}

    @server.tool
    def scripted_police_turn(request: StubTurnRequest) -> StubTurnResponse:
        """Return a separately generated, committed deterministic Police turn."""
        if request.step == 1:
            states[request.subgame] = StubState()
        state = states.setdefault(request.subgame, StubState())
        action = choose_action(state, request.step)
        hint = hint_for(action)
        material = TurnMaterial(
            game_id=request.game_id,
            subgame=request.subgame,
            step=request.step,
            role=Role.POLICE,
            prior_state_sha256=request.prior_state_sha256,
            action=action,
            hint=hint,
            intent=HintIntent.TRUTH if request.step % 3 else HintIntent.BLUFF,
        )
        sealed = seal_turn(material)
        return StubTurnResponse(
            commitment=sealed.commitment,
            disclosure=sealed.disclosure,
        )

    return server


def choose_action(state: StubState, step: int) -> TurnAction:
    """Walk a barrier-aware serpentine script and occasionally place a barrier."""
    if step % 7 == 0 and state.position not in state.barriers:
        state.barriers.add(state.position)
        return TurnAction(
            kind=ActionKind.BARRIER,
            barrier=PointConfig(row=state.position.row, col=state.position.col),
        )
    horizontal = Move.EAST if state.position.row % 2 == 0 else Move.WEST
    candidates = (horizontal, Move.SOUTH, Move.WEST, Move.EAST, Move.NORTH)
    for move in candidates:
        target = destination(state.position, move)
        if 0 <= target.row < 7 and 0 <= target.col < 7 and target not in state.barriers:
            state.position = target
            return TurnAction(kind=ActionKind.MOVE, move=move)
    return TurnAction(kind=ActionKind.MOVE, move=Move.STAY)


def hint_for(action: TurnAction) -> str:
    """Return public natural language or truthful barrier declaration."""
    if action.kind is ActionKind.BARRIER:
        return "I placed a barrier on my current block"
    words = {
        Move.NORTH: "north", Move.SOUTH: "south", Move.EAST: "east",
        Move.WEST: "west", Move.STAY: "still",
    }
    return f"I moved {words[action.move]} along the open street"


def main() -> int:
    """Run the stub as a separate FastMCP HTTP process."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    build_stub().run(
        transport="http", host="127.0.0.1", port=args.port,
        path="/mcp", show_banner=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
