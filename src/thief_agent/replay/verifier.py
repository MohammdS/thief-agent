"""Verify commitments and reconstruct legal objective post-match state."""

from __future__ import annotations

import hmac

from thief_agent.artifacts.match_log import MatchLogArtifact, log_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.commit_reveal import TurnDisclosure, verify_commitment
from thief_agent.domain.board import apply_move, place_barrier
from thief_agent.domain.scent import ScentMap, decay_scent, deposit_scent
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Role
from thief_agent.protocol.actions import ActionKind
from thief_agent.protocol.scent import encode_scent
from thief_agent.replay.models import ReplayFrame, ReplayResult


class ReplayVerifier:
    """Reconstruct full state only from final disclosed audit material."""

    def __init__(self, config: SharedConfig) -> None:
        """Lock replay to the same validated game rules."""
        self._config = config

    def verify(self, log: MatchLogArtifact) -> ReplayResult:
        """Verify every turn hash and physical transition."""
        board = BoardState(
            self._config.board.width,
            self._config.board.height,
            Coord(self._config.board.thief_start.row, self._config.board.thief_start.col),
            Coord(self._config.board.police_start.row, self._config.board.police_start.col),
        )
        failures: list[str] = []
        frames: list[ReplayFrame] = []
        scents: dict[Role, ScentMap] = {Role.THIEF: {}, Role.POLICE: {}}
        if not log.mutual_agreement.confirmed:
            failures.append("log mutual agreement is not confirmed")
        elif not hmac.compare_digest(log.mutual_agreement.sha256, log_sha256(log)):
            failures.append("log agreement hash mismatch")
        expected_role, expected_step = Role.THIEF, 1
        terminal = False
        action_records = tuple(
            (index, record)
            for index, record in enumerate(log.records)
            if "action" in record.payload
        )
        for index, record in action_records:
            try:
                if terminal:
                    raise ValueError("audited actions continue after terminal turn")
                values = record.payload | {"nonce": record.nonce}
                disclosure = TurnDisclosure.model_validate(values)
                if not verify_commitment(record.commit, disclosure):
                    raise ValueError("commitment mismatch")
                if (disclosure.role, disclosure.step) != (expected_role, expected_step):
                    raise ValueError(
                        f"expected {expected_role.value} step {expected_step}",
                    )
                recipient = Role.POLICE if disclosure.role is Role.THIEF else Role.THIEF
                if disclosure.turn_token is not recipient:
                    raise ValueError("turn token was not transferred to the opponent")
                role = disclosure.role
                public_scent = decay_scent(scents[role], self._config.scent.decay)
                if disclosure.scent_heatmap != encode_scent(public_scent):
                    raise ValueError("scent heatmap is not one turn delayed")
                board = apply_disclosure(board, disclosure, self._config.barriers.police_capacity)
                scents[role] = deposit_scent(
                    public_scent,
                    board.position(role),
                    board.width,
                    board.height,
                )
                if role is Role.THIEF:
                    board = board.after_full_turn()
                    expected_role = Role.POLICE
                    terminal = board.step >= self._config.turns.survival_threshold
                else:
                    expected_role, expected_step = Role.THIEF, expected_step + 1
                frames.append(
                    ReplayFrame(
                        disclosure.step,
                        board,
                        disclosure.hint,
                        record.commit,
                    )
                )
            except (ValueError, TypeError) as error:
                failures.append(f"record {index}: {error}")
        status = "TAMPERED" if failures else "Verified OK"
        return ReplayResult(status, tuple(failures), tuple(frames))


def apply_disclosure(
    board: BoardState,
    disclosure: TurnDisclosure,
    barrier_capacity: int,
) -> BoardState:
    """Apply one already hash-verified physical action."""
    action = disclosure.action
    if action.kind is ActionKind.MOVE:
        if action.move is None:
            raise ValueError("movement disclosure lacks move")
        return apply_move(board, disclosure.role, action.move)
    if action.barrier is None:
        raise ValueError("barrier disclosure lacks target")
    target = Coord(action.barrier.row, action.barrier.col)
    return place_barrier(board, target, barrier_capacity)
