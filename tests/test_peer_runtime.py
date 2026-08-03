from __future__ import annotations

from pathlib import Path

import pytest

from tests.runtime_fake import FakePoliceTransport
from thief_agent.artifacts.match_log import MatchLogArtifact
from thief_agent.config import config_sha256, load_local_config, load_shared_config
from thief_agent.protocol.service import ProtocolService
from thief_agent.replay.verifier import ReplayVerifier
from thief_agent.runtime.series import PeerSeriesRunner


@pytest.mark.asyncio
async def test_autonomous_peer_runs_mutual_commit_reveal_series(tmp_path: Path) -> None:
    config = load_shared_config(Path("config/game.json"))
    config = config.model_copy(update={
        "series": config.series.model_copy(update={"subgames": 1}),
    })
    local = load_local_config(Path("config/game.toml.example"))
    local = local.model_copy(update={
        "identity": local.identity.model_copy(update={"group_id": config.group_id}),
        "peer": local.peer.model_copy(update={"opponent_group_id": "ZZZZZZZZ"}),
    })
    service = ProtocolService(config.game_id, config_sha256(config))
    police = FakePoliceTransport(config, service, "ZZZZZZZZ")
    run = await PeerSeriesRunner(
        config, local, service, police, tmp_path, "a" * 40,
    ).run()
    assert len(run.games) == 1
    assert run.games[0].state.step == 35
    assert len(police.thief_reveals) == 35
    assert all("action" not in reveal.model_dump() for reveal in police.thief_reveals)
    assert all(reveal.scent_heatmap for reveal in police.thief_reveals)
    assert run.result.mutual_agreement.confirmed
    assert run.result_path.is_file()
    log_path = tmp_path / f"log_{config.game_id}_g01.json"
    log = MatchLogArtifact.model_validate_json(log_path.read_bytes())
    turn_records = tuple(record for record in log.records if "hint" in record.payload)
    assert len(turn_records) == 70
    assert all("action" in record.payload for record in turn_records)
    assert ReplayVerifier(config).verify(log).status == "Verified OK"
