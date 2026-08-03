"""In-memory symmetric Police transport for autonomous runtime tests."""

from __future__ import annotations

from datetime import UTC, datetime

from thief_agent.config import config_sha256
from thief_agent.config.models import SharedConfig
from thief_agent.crypto.audit import AuditResult, FinalAuditRequest, verify_audit
from thief_agent.crypto.commit_reveal import SealedTurn, TurnMaterial, seal_turn
from thief_agent.domain.scent import ScentMap, advance_scent
from thief_agent.domain.types import Coord, Move, Role
from thief_agent.protocol.actions import ActionKind, HintIntent, TurnAction
from thief_agent.protocol.envelope import WireEnvelope, make_envelope
from thief_agent.protocol.messages import (
    Ack,
    CommitTurnRequest,
    HealthRequest,
    HealthResponse,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)
from thief_agent.protocol.scent import encode_scent
from thief_agent.protocol.service import ProtocolService
from thief_agent.runtime.state import audit_record

AckRequest = NegotiationRequest | CommitTurnRequest | RevealTurnRequest | ResultProposalRequest


class FakePoliceTransport:
    def __init__(self, config: SharedConfig, service: ProtocolService, opponent_group: str) -> None:
        """Keep strict shared identity and per-turn Police disclosures."""
        self.config, self.service = config, service
        self.opponent_group = opponent_group
        self.sealed: dict[tuple[int, int], SealedTurn] = {}
        self.scents: dict[int, ScentMap] = {}
        self.thief_reveals: list[RevealTurnRequest] = []

    async def health(self, request: HealthRequest) -> HealthResponse:
        """Return an independently typed Police identity."""
        thief_group = next(
            group for group in self.config.agreed_between if group != self.opponent_group
        )
        if self.opponent_group < thief_group:
            started_at = datetime.now(UTC).replace(microsecond=0)
            self.service.negotiate(NegotiationRequest(
                envelope=self._envelope(request.envelope.prior_state_sha256, 0, 0),
                contract_version="1.1",
                counted=self.config.counted,
                subgames=self.config.series.subgames,
                sender_group_id=self.opponent_group,
                game_uid=f"{self.config.game_id}-{int(started_at.timestamp())}",
                series_started_at=started_at,
            ))
        return HealthResponse(role=Role.POLICE, config_sha256=config_sha256(self.config))

    async def negotiate(self, request: NegotiationRequest) -> Ack:
        """Accept the coordinator anchor and send the matching callback."""
        mirrored = request.model_copy(update={
            "envelope": self._envelope(request.envelope.prior_state_sha256, 0, 0),
            "sender_group_id": self.opponent_group,
        })
        self.service.negotiate(mirrored)
        return self._ack(request, "accepted")

    async def commit_turn(self, request: CommitTurnRequest) -> Ack:
        """Create and callback one independently sealed Police commitment."""
        envelope = request.envelope
        previous = self.scents.get(envelope.subgame, {})
        next_scent = advance_scent(
            previous,
            Coord(self.config.board.police_start.row, self.config.board.police_start.col),
            self.config.board.width,
            self.config.board.height,
            self.config.scent.decay,
        )
        self.scents[envelope.subgame] = next_scent
        material = TurnMaterial(
            game_id=envelope.game_id,
            subgame=envelope.subgame,
            step=envelope.step,
            role=Role.POLICE,
            prior_state_sha256=envelope.prior_state_sha256,
            action=TurnAction(kind=ActionKind.MOVE, move=Move.STAY),
            scent_heatmap=encode_scent(next_scent),
            hint="I stayed still and watched",
            intent=HintIntent.TRUTH,
        )
        sealed = seal_turn(material)
        self.sealed[(envelope.subgame, envelope.step)] = sealed
        incoming = CommitTurnRequest(
            envelope=self._envelope(
                envelope.prior_state_sha256, envelope.subgame, envelope.step,
            ),
            commitment=sealed.commitment,
        )
        self.service.commit_turn(incoming)
        return self._ack(request, "committed")

    async def reveal_turn(self, request: RevealTurnRequest) -> Ack:
        """Callback the matching Police immediate reveal."""
        self.thief_reveals.append(request)
        envelope = request.envelope
        sealed = self.sealed[(envelope.subgame, envelope.step)]
        disclosure = sealed.disclosure
        incoming = RevealTurnRequest(
            envelope=self._envelope(
                envelope.prior_state_sha256, envelope.subgame, envelope.step,
            ),
            scent_heatmap=disclosure.scent_heatmap,
            hint=disclosure.hint,
        )
        self.service.reveal_turn(incoming)
        return self._ack(request, "revealed")

    async def final_audit(self, request: FinalAuditRequest) -> AuditResult:
        """Verify Thief disclosures and callback all Police disclosures."""
        subgame = request.envelope.subgame
        records = tuple(
            audit_record(sealed)
            for (game, _), sealed in sorted(self.sealed.items())
            if game == subgame
        )
        incoming = FinalAuditRequest(
            envelope=self._envelope(
                request.envelope.prior_state_sha256,
                subgame,
                request.envelope.step,
            ),
            records=records,
        )
        self.service.final_audit(incoming)
        return verify_audit(request.records)

    async def propose_result(self, request: ResultProposalRequest) -> Ack:
        """Callback the same independently expected digest and scores."""
        mirrored = request.model_copy(update={
            "envelope": self._envelope(
                request.envelope.prior_state_sha256,
                request.envelope.subgame,
                request.envelope.step,
            ),
            "sender_group_id": self.opponent_group,
            "tokens_total": 0,
            "git_commit": "0" * 40,
        })
        self.service.propose_result(mirrored)
        return self._ack(request, "result logged")

    def _envelope(self, state_hash: str, subgame: int, step: int) -> WireEnvelope:
        """Build fresh Police-originated metadata."""
        return make_envelope(
            self.config.game_id,
            config_sha256(self.config),
            state_hash,
            sender=Role.POLICE,
            subgame=subgame,
            step=step,
        )

    @staticmethod
    def _ack(request: AckRequest, detail: str) -> Ack:
        """Return an accepted acknowledgment for the caller's message ID."""
        return Ack(message_id=request.envelope.message_id, accepted=True, detail=detail)
