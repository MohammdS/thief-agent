from pathlib import Path

from thief_agent.config import load_shared_config
from thief_agent.crypto.commit_reveal import TurnMaterial, seal_turn
from thief_agent.domain.board import apply_move
from thief_agent.domain.outcome import TerminalReason
from thief_agent.domain.scent import ScentMap, decay_scent, deposit_scent
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Move, Role
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction
from thief_agent.protocol.scent import encode_scent
from thief_agent.runtime.audit_replay import reconstruct_audited_subgame
from thief_agent.runtime.state import audit_record


def test_final_audit_keeps_earliest_hidden_capture_when_live_play_continues() -> None:
    config = load_shared_config(Path("config/game.json"))
    board = BoardState(7, 7, Coord(3, 3), Coord(0, 0))
    scents: dict[Role, ScentMap] = {Role.THIEF: {}, Role.POLICE: {}}
    records = []
    moves = (
        (Move.STAY, Move.SOUTH),
        (Move.STAY, Move.SOUTH),
        (Move.STAY, Move.SOUTH),
        (Move.STAY, Move.EAST),
        (Move.STAY, Move.EAST),
        (Move.STAY, Move.EAST),
        (Move.EAST, Move.STAY),
    )
    for step, pair in enumerate(moves, start=1):
        for role, move in zip((Role.THIEF, Role.POLICE), pair, strict=True):
            public = decay_scent(scents[role], config.scent.decay)
            sealed = seal_turn(
                TurnMaterial(
                    game_id=config.game_id,
                    subgame=1,
                    step=step,
                    role=role,
                    turn_token=Role.POLICE if role is Role.THIEF else Role.THIEF,
                    prior_state_sha256="b" * 64,
                    action=TurnAction(kind=ActionKind.MOVE, move=move),
                    scent_heatmap=encode_scent(public),
                    hint="audit",
                    intent=HintIntent.TRUTH,
                ),
                f"{len(records) + 1:064x}",
            )
            records.append(audit_record(sealed))
            board = apply_move(board, role, move)
            scents[role] = deposit_scent(public, board.position(role), 7, 7)
            if role is Role.THIEF:
                board = board.after_full_turn()

    audited = reconstruct_audited_subgame(config, tuple(records))
    assert audited.outcome.reason is TerminalReason.CAPTURE
    assert audited.state.thief == Coord(3, 4)
