from thief_agent.crypto.commit_reveal import TurnMaterial
from thief_agent.domain.types import Move, Role
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction
from thief_agent.protocol.envelope import make_envelope
from thief_agent.protocol.messages import CommitTurnRequest, RevealTurnRequest

CONFIG_HASH = "a" * 64
STATE_HASH = "b" * 64
GAME_ID = "game-contract-test"


def envelope(*, step: int = 1, subgame: int = 1, lifetime: float = 30):
    return make_envelope(
        GAME_ID,
        CONFIG_HASH,
        STATE_HASH,
        sender=Role.POLICE,
        subgame=subgame,
        step=step,
        lifetime_seconds=lifetime,
    )


def action(move: Move = Move.SOUTH) -> TurnAction:
    return TurnAction(kind=ActionKind.MOVE, move=move)


def material(**updates: object) -> TurnMaterial:
    values = {
        "game_id": GAME_ID,
        "subgame": 1,
        "step": 1,
        "role": Role.POLICE,
        "prior_state_sha256": STATE_HASH,
        "action": action(),
        "hint": "I moved toward open ground",
        "intent": HintIntent.TRUTH,
    }
    values.update(updates)
    return TurnMaterial.model_validate(values)


def commit_request(commitment: str, *, step: int = 1) -> CommitTurnRequest:
    return CommitTurnRequest(envelope=envelope(step=step), commitment=commitment)


def reveal_request(*, move: Move = Move.SOUTH, hint: str = "safe hint") -> RevealTurnRequest:
    return RevealTurnRequest(envelope=envelope(), action=action(move), hint=hint)

