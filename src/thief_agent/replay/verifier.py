"""Verify commitments and reconstruct legal objective post-match state."""

from __future__ import annotations

import hmac
from dataclasses import replace

from thief_agent.artifacts.match_log import MatchLogArtifact, log_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.commit_reveal import TurnDisclosure, verify_commitment
from thief_agent.domain.board import apply_move, place_barrier
from thief_agent.domain.scent import ScentMap, advance_scent
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
        for index, record in enumerate(log.records):
            if "action" not in record.payload:
                continue
            try:
                values = record.payload | {"nonce": record.nonce}
                disclosure = TurnDisclosure.model_validate(values)
                if not verify_commitment(record.commit, disclosure):
                    raise ValueError("commitment mismatch")
                board = apply_disclosure(board, disclosure, self._config.barriers.police_capacity)
                role = disclosure.role
                scents[role] = advance_scent(
                    scents[role],
                    board.position(role),
                    board.width,
                    board.height,
                    self._config.scent.decay,
                )
                if disclosure.scent_heatmap != encode_scent(scents[role]):
                    raise ValueError("scent heatmap does not match hidden action history")
                board = replace(board, step=max(board.step, disclosure.step))
                frames.append(ReplayFrame(
                    disclosure.step, board, disclosure.hint, record.commit,
                ))
            except (ValueError, TypeError) as error:
                failures.append(f"record {index}: {error}")
        status = "TAMPERED" if failures else "Verified OK"
        return ReplayResult(status, tuple(failures), tuple(frames))


def apply_disclosure(
    board: BoardState, disclosure: TurnDisclosure, barrier_capacity: int,
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
