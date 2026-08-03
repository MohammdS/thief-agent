from datetime import UTC, datetime

import pytest

from tests.protocol_helpers import (
    CONFIG_HASH,
    GAME_ID,
    commit_request,
    envelope,
    material,
    reveal_request,
)
from thief_agent.crypto.audit import AuditRecord, FinalAuditRequest, RevealedTurn
from thief_agent.crypto.commit_reveal import seal_turn
from thief_agent.protocol.firewall import ObservationEvidence
from thief_agent.protocol.messages import (
    HealthRequest,
    NegotiationRequest,
    RevealTurnRequest,
)
from thief_agent.protocol.service import ProtocolService


def service() -> ProtocolService:
    return ProtocolService(GAME_ID, CONFIG_HASH)


def test_health_and_negotiation_validate_identity_and_counted_rule() -> None:
    peer = service()
    assert peer.health(HealthRequest(envelope=envelope())).role == "thief"
    rejected = peer.negotiate(
        NegotiationRequest(
            envelope=envelope(), contract_version="1.1", counted=True, subgames=1,
            sender_group_id="other-group", game_uid="game-uid",
            series_started_at=datetime.now(UTC),
        )
    )
    assert not rejected.accepted
    wrong = envelope().model_copy(update={"config_sha256": "c" * 64})
    with pytest.raises(ValueError, match="configuration hash"):
        peer.health(HealthRequest(envelope=wrong))


def test_commit_and_reveal_are_idempotent_but_conflicts_fail() -> None:
    peer = service()
    sealed = seal_turn(material(), "01" * 32)
    request = commit_request(sealed.commitment)
    assert peer.commit_turn(request).detail == "committed"
    assert peer.commit_turn(request).detail == "duplicate commitment"
    with pytest.raises(ValueError, match="conflicting commitment"):
        peer.commit_turn(commit_request("c" * 64))
    reveal = RevealTurnRequest(
        envelope=envelope(),
        scent_heatmap=sealed.disclosure.scent_heatmap,
        hint=sealed.disclosure.hint,
    )
    assert peer.reveal_turn(reveal).detail == "revealed"
    assert peer.reveal_turn(reveal).detail == "duplicate reveal"
    assert "action" not in reveal.model_dump()


def test_reveal_before_commit_fails_and_firewall_returns_hint_only() -> None:
    peer = service()
    reveal = reveal_request(hint="words only")
    with pytest.raises(ValueError, match="before commitment"):
        peer.reveal_turn(reveal)
    evidence = peer.firewall.accept_police_reveal(reveal)
    assert evidence == ObservationEvidence(
        "words only", reveal.scent_heatmap, None, None,
    )
    assert "action" not in ObservationEvidence.__dataclass_fields__


def test_service_final_audit_verifies_complete_record() -> None:
    peer = service()
    sealed = seal_turn(material(), "01" * 32)
    peer.commit_turn(commit_request(sealed.commitment))
    reveal_request = RevealTurnRequest(
        envelope=envelope(),
        scent_heatmap=sealed.disclosure.scent_heatmap,
        hint=sealed.disclosure.hint,
    )
    peer.reveal_turn(reveal_request)
    record = AuditRecord(
        reveal=RevealedTurn(
            commitment=sealed.commitment,
            scent_heatmap=sealed.disclosure.scent_heatmap,
            hint=sealed.disclosure.hint,
        ),
        disclosure=sealed.disclosure,
    )
    request = FinalAuditRequest(envelope=envelope(step=2), records=(record,))
    assert peer.final_audit(request).status == "Verified OK"
    assert peer.final_audit(request.model_copy(update={"records": ()})).status == "TAMPERED"


def test_conflicting_reveal_fails() -> None:
    peer = service()
    sealed = seal_turn(material(), "01" * 32)
    peer.commit_turn(commit_request(sealed.commitment))
    first = reveal_request(hint="first")
    peer.reveal_turn(first)
    changed = reveal_request(intensity=0.8, hint="first")
    with pytest.raises(ValueError, match="conflicting reveal"):
        peer.reveal_turn(changed)
