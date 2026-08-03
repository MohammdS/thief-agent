from pathlib import Path

from tests.replay_helpers import record, replay_log
from thief_agent.artifacts.common import MutualAgreement
from thief_agent.artifacts.match_log import LogRecord, MatchLogArtifact, log_sha256
from thief_agent.config import load_shared_config
from thief_agent.crypto.commit_reveal import TurnMaterial, seal_turn
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


def test_hash_valid_but_action_inconsistent_scent_is_tampered() -> None:
    log = replay_log()
    source = log.records[0]
    values = source.payload | {
        "scent_heatmap": [{"row": 0, "col": 0, "intensity": 0.9}],
    }
    material = TurnMaterial.model_validate(values)
    sealed = seal_turn(material, source.nonce)
    changed = LogRecord(
        payload=sealed.disclosure.model_dump(mode="json", exclude={"nonce"}),
        nonce=sealed.disclosure.nonce,
        commit=sealed.commitment,
    )
    tampered = log.model_copy(update={"records": (changed, *log.records[1:])})
    tampered = tampered.model_copy(update={
        "mutual_agreement": MutualAgreement(sha256=log_sha256(tampered), confirmed=True),
    })
    result = verifier().verify(tampered)
    assert result.status == "TAMPERED"
    assert any("scent heatmap" in failure for failure in result.failures)
