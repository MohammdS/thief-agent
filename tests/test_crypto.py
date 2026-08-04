import pytest

from tests.protocol_helpers import action, material
from thief_agent.crypto.audit import AuditRecord, RevealedTurn, verify_audit
from thief_agent.crypto.commit_reveal import TurnDisclosure, seal_turn, verify_commitment
from thief_agent.crypto.step_zero import StepZeroDeclaration, sign_step_zero, verify_step_zero
from thief_agent.domain.types import Move, Role
from thief_agent.protocol.scent import ScentCell

FIXED_NONCE = "01" * 32


def test_commitment_is_stable_for_fixed_nonce_and_fresh_by_default() -> None:
    first = seal_turn(material(), FIXED_NONCE)
    second = seal_turn(material(), FIXED_NONCE)
    assert first.commitment == second.commitment
    assert seal_turn(material()).commitment != seal_turn(material()).commitment


@pytest.mark.parametrize(
    "field",
    [
        "action",
        "turn_token",
        "scent_heatmap",
        "hint",
        "intent",
        "prior_state_sha256",
        "nonce",
    ],
)
def test_every_bound_field_detects_tampering(field: str) -> None:
    sealed = seal_turn(material(), FIXED_NONCE)
    values = sealed.disclosure.model_dump(mode="python")
    replacements = {
        "action": action(Move.NORTH),
        "turn_token": Role.POLICE,
        "scent_heatmap": (ScentCell(row=0, col=0, intensity=0.8),),
        "hint": "altered hint",
        "intent": "bluff",
        "prior_state_sha256": "c" * 64,
        "nonce": "02" * 32,
    }
    values[field] = replacements[field]
    altered = (
        sealed.disclosure.model_copy(update={"turn_token": Role.POLICE})
        if field == "turn_token"
        else TurnDisclosure.model_validate(values)
    )
    assert not verify_commitment(sealed.commitment, altered)


def test_final_audit_checks_hash_action_and_hint() -> None:
    sealed = seal_turn(material(), FIXED_NONCE)
    reveal = RevealedTurn(
        commitment=sealed.commitment,
        turn_token=sealed.disclosure.turn_token,
        scent_heatmap=sealed.disclosure.scent_heatmap,
        hint=sealed.disclosure.hint,
    )
    record = AuditRecord(reveal=reveal, disclosure=sealed.disclosure)
    assert verify_audit((record,)).status == "Verified OK"
    bad_reveal = reveal.model_copy(update={"hint": "changed"})
    result = verify_audit((AuditRecord(reveal=bad_reveal, disclosure=sealed.disclosure),))
    assert result.status == "TAMPERED"
    assert "hint mismatch" in result.errors[0]


def test_step_zero_signature_is_strict_and_constant_time_verified() -> None:
    declaration = StepZeroDeclaration(
        team="team-eight",
        role=Role.THIEF,
        subgame=1,
        os="Windows 11",
        cpu="test cpu",
        ram_bytes=16_000_000_000,
        gpu="none",
        model="template",
        git_commit="a" * 40,
        token_budget=200_000,
        tokens_used=0,
    )
    key = b"shared-test-key-material"
    signature = sign_step_zero(declaration, key)
    assert verify_step_zero(declaration, key, signature)
    changed = declaration.model_copy(update={"tokens_used": 1})
    assert not verify_step_zero(changed, key, signature)
    with pytest.raises(ValueError, match="at least 16"):
        sign_step_zero(declaration, b"short")
