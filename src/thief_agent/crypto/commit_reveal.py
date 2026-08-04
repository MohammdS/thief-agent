"""Fresh-nonce SHA-256 commitment creation and verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from pydantic import Field, field_validator, model_validator

from thief_agent.config.loader import canonical_json_bytes
from thief_agent.config.models import StrictModel
from thief_agent.domain.types import Role
from thief_agent.protocol.actions import HintIntent, TurnAction
from thief_agent.protocol.envelope import HASH_PATTERN
from thief_agent.protocol.scent import ScentHeatmap, validate_heatmap


class TurnMaterial(StrictModel):
    """Bind state, physical action, language, and hidden intent."""

    game_id: str = Field(min_length=1)
    subgame: int = Field(ge=1)
    step: int = Field(ge=0)
    role: Role
    turn_token: Role
    prior_state_sha256: str = Field(pattern=HASH_PATTERN)
    action: TurnAction
    scent_heatmap: ScentHeatmap
    hint: str = Field(max_length=500)
    intent: HintIntent

    _canonical_heatmap = field_validator("scent_heatmap")(validate_heatmap)

    @model_validator(mode="after")
    def require_opponent_token(self) -> TurnMaterial:
        """Require every sealed turn to hand play to the other role."""
        if self.turn_token is self.role:
            raise ValueError("turn token must be granted to the opponent")
        return self


class TurnDisclosure(TurnMaterial):
    """Add the secret nonce disclosed only during final audit."""

    nonce: str = Field(pattern=r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SealedTurn:
    """Keep a disclosure secret beside its public commitment hash."""

    commitment: str
    disclosure: TurnDisclosure


def commitment_for(disclosure: TurnDisclosure) -> str:
    """Hash one canonical complete turn disclosure."""
    payload = disclosure.model_dump(mode="json")
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def seal_turn(material: TurnMaterial, nonce: str | None = None) -> SealedTurn:
    """Create a commitment with a fresh 256-bit nonce by default."""
    disclosure = TurnDisclosure(
        **material.model_dump(mode="python"),
        nonce=nonce or secrets.token_hex(32),
    )
    return SealedTurn(commitment_for(disclosure), disclosure)


def verify_commitment(commitment: str, disclosure: TurnDisclosure) -> bool:
    """Compare a recomputed commitment in constant time."""
    return hmac.compare_digest(commitment, commitment_for(disclosure))
