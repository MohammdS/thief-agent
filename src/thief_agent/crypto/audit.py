"""Final nonce disclosure and complete commitment audit."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from thief_agent.config.models import PointConfig, StrictModel
from thief_agent.crypto.commit_reveal import TurnDisclosure, verify_commitment
from thief_agent.protocol.actions import ActionKind
from thief_agent.protocol.envelope import HASH_PATTERN, WireEnvelope
from thief_agent.protocol.scent import ScentHeatmap


class RevealedTurn(StrictModel):
    """Store immediate public reveal data without nonce or intent."""

    commitment: str = Field(pattern=HASH_PATTERN)
    scent_heatmap: ScentHeatmap
    hint: str = Field(max_length=500)
    barrier: PointConfig | None = None
    capture_claim: Literal["overlap", "barrier", "imprisonment"] | None = None


class AuditRecord(StrictModel):
    """Pair an immediate reveal with its final secret disclosure."""

    reveal: RevealedTurn
    disclosure: TurnDisclosure


class AuditResult(StrictModel):
    """Report exact verifier status and any indexed failures."""

    status: str
    errors: tuple[str, ...] = ()


class FinalAuditRequest(StrictModel):
    """Carry final records only after the subgame series ends."""

    envelope: WireEnvelope
    records: tuple[AuditRecord, ...]


def verify_audit(records: tuple[AuditRecord, ...]) -> AuditResult:
    """Verify hashes and immediate/final reveal consistency."""
    errors: list[str] = []
    for index, record in enumerate(records):
        if not verify_commitment(record.reveal.commitment, record.disclosure):
            errors.append(f"record {index}: commitment mismatch")
        if record.reveal.scent_heatmap != record.disclosure.scent_heatmap:
            errors.append(f"record {index}: scent heatmap mismatch")
        if record.reveal.hint != record.disclosure.hint:
            errors.append(f"record {index}: hint mismatch")
        action = record.disclosure.action
        expected_barrier = action.barrier if action.kind is ActionKind.BARRIER else None
        if record.reveal.barrier != expected_barrier:
            errors.append(f"record {index}: public barrier mismatch")
    status = "TAMPERED" if errors else "Verified OK"
    return AuditResult(status=status, errors=tuple(errors))
