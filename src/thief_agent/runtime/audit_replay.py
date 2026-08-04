"""Reconstruct objective state only after both peers disclose sealed actions."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord, verify_audit
from thief_agent.domain.board import apply_move, place_barrier
from thief_agent.domain.outcome import (
    Outcome,
    TerminalReason,
    evaluate_outcome,
    score_outcome,
)
from thief_agent.domain.scent import ScentMap, decay_scent, deposit_scent
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Role
from thief_agent.protocol.actions import ActionKind
from thief_agent.protocol.scent import encode_scent


@dataclass(frozen=True, slots=True)
class AuditedSubgame:
    """Return the canonical state and outcome recovered after final disclosure."""

    state: BoardState
    outcome: Outcome


def reconstruct_audited_subgame(
    config: SharedConfig,
    records: tuple[AuditRecord, ...],
) -> AuditedSubgame:
    """Verify hidden actions, scent histories, public events, and terminal state."""
    audit = verify_audit(records)
    if audit.status != "Verified OK":
        raise ValueError(f"cannot replay tampered disclosures: {audit.errors}")
    board = BoardState(
        config.board.width,
        config.board.height,
        Coord(config.board.thief_start.row, config.board.thief_start.col),
        Coord(config.board.police_start.row, config.board.police_start.col),
    )
    scents: dict[Role, ScentMap] = {Role.THIEF: {}, Role.POLICE: {}}
    expected_role, expected_step = Role.THIEF, 1
    terminal: Outcome | None = None
    for index, record in enumerate(records):
        disclosure = record.disclosure
        if (disclosure.role, disclosure.step) != (expected_role, expected_step):
            raise ValueError(
                f"turn {index + 1} must be {expected_role.value} step {expected_step}",
            )
        recipient = Role.POLICE if disclosure.role is Role.THIEF else Role.THIEF
        if disclosure.turn_token is not recipient:
            raise ValueError(f"step {expected_step} transfers the token incorrectly")
        role = disclosure.role
        public_scent = decay_scent(scents[role], config.scent.decay)
        if disclosure.scent_heatmap != encode_scent(public_scent):
            raise ValueError(
                f"step {expected_step} {role.value} scent is not one turn delayed",
            )
        board = apply_action(board, record, config.barriers.police_capacity)
        scents[role] = deposit_scent(
            public_scent,
            board.position(role),
            board.width,
            board.height,
        )
        if role is Role.THIEF:
            board = board.after_full_turn()
            outcome = (
                score_outcome(TerminalReason.SURVIVAL, config)
                if board.step >= config.turns.survival_threshold
                else None
            )
            expected_role = Role.POLICE
        else:
            outcome = evaluate_outcome(board, config)
            expected_role, expected_step = Role.THIEF, expected_step + 1
        validate_claims((record,), board, outcome, disclosure.step)
        if outcome is not None and terminal is None:
            terminal = outcome
        if (
            outcome is not None
            and outcome.reason is TerminalReason.SURVIVAL
            and index != len(records) - 1
        ):
            raise ValueError(
                f"audited actions continue after terminal step {disclosure.step}",
            )
    if terminal is not None:
        return AuditedSubgame(board, terminal)
    raise ValueError("audited subgame has no terminal outcome")


def apply_action(board: BoardState, record: AuditRecord, capacity: int) -> BoardState:
    """Apply one action that remained secret during live play."""
    disclosure = record.disclosure
    action = disclosure.action
    if action.kind is ActionKind.MOVE:
        if action.move is None:
            raise ValueError("movement disclosure lacks move")
        return apply_move(board, disclosure.role, action.move)
    if disclosure.role is not Role.POLICE or action.barrier is None:
        raise ValueError("only Police may disclose a barrier action")
    target = Coord(action.barrier.row, action.barrier.col)
    return place_barrier(board, target, capacity)


def validate_claims(
    records: tuple[AuditRecord | None, ...],
    board: BoardState,
    outcome: Outcome | None,
    step: int,
) -> None:
    """Reject live terminal claims that the final hidden actions do not prove."""
    claims = tuple(
        record.reveal.capture_claim for record in records if record and record.reveal.capture_claim
    )
    if not claims:
        return
    if outcome is None:
        raise ValueError(f"step {step} contains a false capture claim")
    valid: set[str]
    if outcome.reason is TerminalReason.IMPRISONMENT:
        valid = {"imprisonment"}
    elif outcome.reason is TerminalReason.CAPTURE:
        valid = set()
        if board.thief == board.police:
            valid.add("overlap")
        if board.thief in board.barriers:
            valid.add("barrier")
    else:
        valid = set()
    if any(claim not in valid for claim in claims):
        raise ValueError(f"step {step} terminal claim does not match audited state")
