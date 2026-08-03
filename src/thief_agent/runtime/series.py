"""Autonomous six-subgame Thief series over symmetric P2P tools."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from thief_agent.artifacts.agreed_config import build_agreed_config
from thief_agent.artifacts.declaration import DeclarationArtifact
from thief_agent.artifacts.store import ArtifactStore
from thief_agent.config import LocalConfig, SharedConfig
from thief_agent.protocol.machine import MatchState, match_machine
from thief_agent.protocol.service import ProtocolService
from thief_agent.reliability.gatekeeper import ExternalGatekeeper
from thief_agent.runtime.factory import build_orchestrator
from thief_agent.runtime.game import run_peer_game
from thief_agent.runtime.models import PeerSeriesRun
from thief_agent.runtime.negotiation import negotiate_series
from thief_agent.runtime.package import build_live_log, build_live_result, ordered_groups
from thief_agent.runtime.result_exchange import agree_series_result
from thief_agent.runtime.transport import PeerTransport
from thief_agent.ui.store import LiveSnapshotStore


class PeerSeriesRunner:
    """Coordinate live Thief decisions, peer exchange, and artifacts."""

    def __init__(
        self,
        config: SharedConfig,
        local: LocalConfig,
        service: ProtocolService,
        client: PeerTransport,
        output: Path,
        git_commit: str,
        declaration_path: Path | None = None,
    ) -> None:
        """Inject all boundaries needed for one independently managed series."""
        self.config, self.local = config, local
        self.service, self.client = service, client
        self.output, self.git_commit = output, git_commit
        self.declaration_path = declaration_path
        self.gate = ExternalGatekeeper(
            config.network.response_timeout_seconds,
            config.network.retry_delay_seconds,
            config.network.retries,
            config.network.concurrency,
            config.network.queue_depth,
        )

    async def run(self) -> PeerSeriesRun:
        """Run negotiation, all subgames, mutual result agreement, and persistence."""
        configured_groups = {
            self.local.identity.group_id,
            self.local.peer.opponent_group_id,
        }
        if configured_groups != set(self.config.agreed_between):
            raise ValueError("local peer identities do not match agreed_between")
        if self.config.counted and self.declaration_path is None:
            raise ValueError("counted series requires an agreed declaration")
        machine = match_machine()
        machine.transition(MatchState.NEGOTIATING)
        negotiated = await negotiate_series(
            self.config, self.local, self.service, self.client, self.gate,
        )
        machine.transition(MatchState.STEP_ZERO)
        store = ArtifactStore(self.output)
        if self.declaration_path:
            declaration = DeclarationArtifact.model_validate_json(
                self.declaration_path.read_bytes(),
            )
            expected = (
                self.config.game_id, negotiated.game_uid,
                self.config.series.subgames, self.config.series.token_budget,
            )
            actual = (
                declaration.game_id, declaration.game_uid,
                declaration.num_sub_games, declaration.max_tokens_per_game,
            )
            if actual != expected:
                raise ValueError("declaration does not match negotiated series")
            store.write("declaration", self.config.game_id, declaration)
        machine.transition(MatchState.RUNNING_SUBGAME)
        groups = (self.local.identity.group_id, self.local.peer.opponent_group_id)
        publisher = (
            LiveSnapshotStore(self.output / "runtime" / "live.json")
            if self.local.ui.enabled else None
        )
        games = []
        for subgame in range(1, self.config.series.subgames + 1):
            orchestrator = build_orchestrator(self.config, self.local, self.output, subgame)
            offset = timedelta(
                seconds=(subgame - 1) * (self.config.turns.max_steps + 1),
            )
            start = negotiated.series_started_at + offset
            game = await run_peer_game(
                self.config, subgame, self.service, self.client, orchestrator,
                self.gate, groups, self.git_commit, start,
                self.local.strategy.hint_word_limit,
                publisher,
            )
            games.append(game)
            agreed = build_agreed_config(
                self.config, negotiated.game_uid, subgame, ordered_groups(groups),
            )
            store.write("config", self.config.game_id, agreed, subgame)
            log = build_live_log(
                self.config.game_id, negotiated.game_uid, subgame, groups, game,
                self.git_commit, self.local.strategy.language_provider,
                self.config.series.token_budget,
            )
            store.write("log", self.config.game_id, log, subgame)
        machine.transition(MatchState.FINAL_AUDIT)
        machine.transition(MatchState.AGREEING_RESULT)
        provisional = build_live_result(
            self.config.game_id, negotiated.game_uid, groups, tuple(games), self.git_commit,
        )
        result = await agree_series_result(
            self.config, provisional, games[-1].state, groups, self.git_commit,
            self.service, self.client, self.gate,
        )
        path = store.write("result", self.config.game_id, result)
        machine.transition(MatchState.REPORTING)
        machine.transition(MatchState.FINISHED)
        return PeerSeriesRun(result, path, tuple(games))
