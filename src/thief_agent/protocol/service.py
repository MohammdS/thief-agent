"""Pure service backing all FastMCP protocol tools."""

from __future__ import annotations

from dataclasses import dataclass, field

from thief_agent.crypto.audit import AuditResult, FinalAuditRequest, verify_audit
from thief_agent.protocol.firewall import AuditFirewall
from thief_agent.protocol.ledger import TurnLedger
from thief_agent.protocol.messages import (
    Ack,
    CaptureClaimRequest,
    CommitTurnRequest,
    HealthRequest,
    HealthResponse,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)


@dataclass(slots=True)
class ProtocolService:
    """Validate identity, freshness, idempotency, and audit routing."""

    game_id: str
    config_hash: str
    ledger: TurnLedger = field(default_factory=TurnLedger)
    firewall: AuditFirewall = field(default_factory=AuditFirewall)

    def _validate(self, request: object) -> None:
        """Validate the shared request envelope against local identity."""
        envelope = request.envelope  # type: ignore[attr-defined]
        envelope.assert_fresh()
        if envelope.game_id != self.game_id:
            raise ValueError("game_id mismatch")
        if envelope.config_sha256 != self.config_hash:
            raise ValueError("configuration hash mismatch")

    def health(self, request: HealthRequest) -> HealthResponse:
        """Respond only after envelope validation."""
        self._validate(request)
        return HealthResponse(config_sha256=self.config_hash)

    def negotiate(self, request: NegotiationRequest) -> Ack:
        """Accept only the fixed contract and counted six-game rule."""
        self._validate(request)
        accepted = not request.counted or request.subgames == 6
        detail = "accepted" if accepted else "counted series requires six subgames"
        return Ack(message_id=request.envelope.message_id, accepted=accepted, detail=detail)

    def commit_turn(self, request: CommitTurnRequest) -> Ack:
        """Record a new or identical duplicate turn commitment."""
        self._validate(request)
        created = self.ledger.record_commit(request)
        detail = "committed" if created else "duplicate commitment"
        return Ack(message_id=request.envelope.message_id, accepted=True, detail=detail)

    def reveal_turn(self, request: RevealTurnRequest) -> Ack:
        """Record a reveal while firewalling movement from strategy."""
        self._validate(request)
        created = self.ledger.record_reveal(request)
        if created:
            self.firewall.accept_police_reveal(request)
        detail = "revealed" if created else "duplicate reveal"
        return Ack(message_id=request.envelope.message_id, accepted=True, detail=detail)

    def capture_claim(self, request: CaptureClaimRequest) -> Ack:
        """Acknowledge a claim for later objective audit."""
        self._validate(request)
        return Ack(message_id=request.envelope.message_id, accepted=True, detail="claim logged")

    def final_audit(self, request: FinalAuditRequest) -> AuditResult:
        """Verify all final nonce disclosures and reveal consistency."""
        self._validate(request)
        result = verify_audit(request.records)
        errors = list(result.errors)
        if len(request.records) != len(self.ledger.reveals):
            errors.append("final disclosure count does not match reveal ledger")
        for index, record in enumerate(request.records):
            disclosure = record.disclosure
            key = (disclosure.subgame, disclosure.step, disclosure.role.value)
            if self.ledger.reveals.get(key) != record.reveal:
                errors.append(f"record {index}: reveal absent from local ledger")
        return AuditResult(status="TAMPERED" if errors else "Verified OK", errors=tuple(errors))

    def propose_result(self, request: ResultProposalRequest) -> Ack:
        """Acknowledge an independently hashed result proposal."""
        self._validate(request)
        return Ack(message_id=request.envelope.message_id, accepted=True, detail="result logged")
