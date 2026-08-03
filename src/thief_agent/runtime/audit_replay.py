"""Reconstruct objective state only after both peers disclose sealed actions."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditRecord, verify_audit
from thief_agent.domain.board import apply_move, place_barrier
from thief_agent.domain.outcome import Outcome, TerminalReason, evaluate_outcome
from thief_agent.domain.scent import ScentMap, advance_scent
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
    by_turn = {(record.disclosure.step, record.disclosure.role): record for record in records}
    if len(by_turn) != len(records):
        raise ValueError("duplicate role disclosure in audited subgame")
    board = BoardState(
        config.board.width,
        config.board.height,
        Coord(config.board.thief_start.row, config.board.thief_start.col),
        Coord(config.board.police_start.row, config.board.police_start.col),
    )
    scents: dict[Role, ScentMap] = {Role.THIEF: {}, Role.POLICE: {}}
    final_step = max((step for step, _ in by_turn), default=0)
    for step in range(1, final_step + 1):
        pair = tuple(by_turn.get((step, role)) for role in (Role.THIEF, Role.POLICE))
        if any(record is None for record in pair):
            raise ValueError(f"step {step} does not contain both role disclosures")
        thief_record, police_record = pair
        assert thief_record is not None and police_record is not None
        board = apply_action(board, thief_record, config.barriers.police_capacity)
        board = apply_action(board, police_record, config.barriers.police_capacity)
        board = board.after_full_turn()
        for role, record in ((Role.THIEF, thief_record), (Role.POLICE, police_record)):
            scents[role] = advance_scent(
                scents[role],
                board.position(role),
                board.width,
                board.height,
                config.scent.decay,
            )
            if record.disclosure.scent_heatmap != encode_scent(scents[role]):
                raise ValueError(f"step {step} {role.value} scent heatmap is not action-derived")
        outcome = evaluate_outcome(board, config)
        validate_claims(pair, board, outcome, step)
        if outcome is not None:
            if step != final_step:
                raise ValueError(f"audited actions continue after terminal step {step}")
            return AuditedSubgame(board, outcome)
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
        record.reveal.capture_claim
        for record in records
        if record and record.reveal.capture_claim
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
