"""Pydantic request and response models exposed as FastMCP tools."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from thief_agent.config.models import StrictModel
from thief_agent.protocol.actions import TurnAction
from thief_agent.protocol.envelope import HASH_PATTERN, WireEnvelope


class HealthRequest(StrictModel):
    """Request peer liveness and contract identity."""

    envelope: WireEnvelope


class HealthResponse(StrictModel):
    """Return safe peer liveness metadata."""

    status: Literal["ok"] = "ok"
    role: Literal["thief"] = "thief"
    protocol_version: Literal["1.0"] = "1.0"
    config_sha256: str = Field(pattern=HASH_PATTERN)


class NegotiationRequest(StrictModel):
    """Propose the locked contract and series parameters."""

    envelope: WireEnvelope
    contract_version: Literal["1.0"]
    counted: bool
    subgames: int = Field(ge=1)


class Ack(StrictModel):
    """Acknowledge a request deterministically."""

    message_id: UUID
    accepted: bool
    detail: str = Field(min_length=1)


class CommitTurnRequest(StrictModel):
    """Publish only a turn commitment hash."""

    envelope: WireEnvelope
    commitment: str = Field(pattern=HASH_PATTERN)


class RevealTurnRequest(StrictModel):
    """Reveal action and hint while withholding nonce and intent."""

    envelope: WireEnvelope
    action: TurnAction
    hint: str = Field(max_length=500)


class CaptureClaimRequest(StrictModel):
    """Claim one objectively auditable terminal capture condition."""

    envelope: WireEnvelope
    reason: Literal["overlap", "barrier", "imprisonment"]
    evidence_sha256: str = Field(pattern=HASH_PATTERN)


class ResultProposalRequest(StrictModel):
    """Propose an independently calculated final result hash."""

    envelope: WireEnvelope
    result_sha256: str = Field(pattern=HASH_PATTERN)
    police_score: int = Field(ge=0)
    thief_score: int = Field(ge=0)

