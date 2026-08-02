"""Final nonce disclosure and complete commitment audit."""

from __future__ import annotations

from pydantic import Field

from thief_agent.config.models import StrictModel
from thief_agent.crypto.commit_reveal import TurnDisclosure, verify_commitment
from thief_agent.protocol.actions import TurnAction
from thief_agent.protocol.envelope import HASH_PATTERN, WireEnvelope


class RevealedTurn(StrictModel):
    """Store immediate public reveal data without nonce or intent."""

    commitment: str = Field(pattern=HASH_PATTERN)
    action: TurnAction
    hint: str = Field(max_length=500)


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
        if record.reveal.action != record.disclosure.action:
            errors.append(f"record {index}: action mismatch")
        if record.reveal.hint != record.disclosure.hint:
            errors.append(f"record {index}: hint mismatch")
    status = "TAMPERED" if errors else "Verified OK"
    return AuditResult(status=status, errors=tuple(errors))

