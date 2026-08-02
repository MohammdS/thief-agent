"""Signed step-zero hardware, model, code, and token declaration."""

from __future__ import annotations

import hashlib
import hmac

from pydantic import Field

from thief_agent.config.loader import canonical_json_bytes
from thief_agent.config.models import StrictModel
from thief_agent.domain.types import Role


class StepZeroDeclaration(StrictModel):
    """Record the exact runtime identity before a subgame starts."""

    team: str = Field(min_length=1)
    role: Role
    subgame: int = Field(ge=1)
    os: str = Field(min_length=1)
    cpu: str = Field(min_length=1)
    ram_bytes: int = Field(gt=0)
    gpu: str
    model: str = Field(min_length=1)
    git_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    token_budget: int = Field(gt=0)
    tokens_used: int = Field(ge=0)


def sign_step_zero(declaration: StepZeroDeclaration, key: bytes) -> str:
    """Return an HMAC-SHA256 signature over canonical declaration bytes."""
    if len(key) < 16:
        raise ValueError("step-zero signing key must be at least 16 bytes")
    payload = canonical_json_bytes(declaration.model_dump(mode="json"))
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify_step_zero(declaration: StepZeroDeclaration, key: bytes, signature: str) -> bool:
    """Verify a step-zero signature in constant time."""
    return hmac.compare_digest(sign_step_zero(declaration, key), signature)

