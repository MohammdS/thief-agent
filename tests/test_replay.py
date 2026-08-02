from pathlib import Path

from tests.replay_helpers import record, replay_log
from thief_agent.artifacts.match_log import MatchLogArtifact
from thief_agent.config import load_shared_config
from thief_agent.domain.types import Move, Role
from thief_agent.replay.verifier import ReplayVerifier


def verifier() -> ReplayVerifier:
    return ReplayVerifier(load_shared_config(Path("config/game.json")))


def test_valid_final_disclosures_reconstruct_verified_replay() -> None:
    result = verifier().verify(replay_log())
    assert result.status == "Verified OK"
    assert len(result.frames) == 2
    assert result.frames[-1].state.thief.row == 4
    assert result.frames[-1].state.police.row == 1


def test_altered_payload_is_tampered() -> None:
    log = replay_log()
    changed = log.records[0].model_copy(update={
        "payload": log.records[0].payload | {"hint": "altered"},
    })
    tampered = log.model_copy(update={"records": (changed, *log.records[1:])})
    result = verifier().verify(tampered)
    assert result.status == "TAMPERED"
    assert any("commitment mismatch" in failure for failure in result.failures)


def test_hash_valid_but_physically_illegal_move_is_tampered() -> None:
    illegal = record(Role.POLICE, Move.NORTH, 1, "north", "03" * 32)
    log: MatchLogArtifact = replay_log().model_copy(update={"records": (illegal,)})
    result = verifier().verify(log)
    assert result.status == "TAMPERED"
    assert any("illegal police move" in failure for failure in result.failures)


def test_deleted_record_breaks_whole_log_agreement() -> None:
    log = replay_log()
    deleted = log.model_copy(update={"records": log.records[1:]})
    result = verifier().verify(deleted)
    assert result.status == "TAMPERED"
    assert "log agreement hash mismatch" in result.failures[0]
