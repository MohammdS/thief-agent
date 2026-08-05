import pytest

from thief_agent.language.profile import TruthProfile
from thief_agent.protocol.actions import HintIntent


def test_truth_profile_starts_uncertain_and_learns_after_audit() -> None:
    profile = TruthProfile()
    assert profile.probability == 0.5
    profile.record(True)
    assert profile.probability > 0.5
    profile.record(False)
    assert profile.probability == 0.5


def test_truth_profile_accepts_audited_intents() -> None:
    profile = TruthProfile()
    profile.record_intent(HintIntent.TRUTH)
    profile.record_intent(HintIntent.BLUFF)
    assert profile.probability == 0.5


def test_truth_profile_rejects_empty_or_negative_counts() -> None:
    with pytest.raises(ValueError):
        TruthProfile(0, 0)
    with pytest.raises(ValueError):
        TruthProfile(-1, 2)
