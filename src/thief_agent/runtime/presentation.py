"""Publish information-safe Thief state for the optional live GUI."""

from __future__ import annotations

from thief_agent.belief.model import BeliefMap
from thief_agent.domain.scent import ScentMap
from thief_agent.domain.state import BoardState
from thief_agent.ui.model import LiveSnapshot
from thief_agent.ui.store import LiveSnapshotStore


def publish_live(
    store: LiveSnapshotStore | None, state: BoardState, scent: ScentMap,
    belief: BeliefMap, hint: str, tokens: int, audit: str = "pending",
) -> None:
    """Write one local-truth-only Thief snapshot when UI output is enabled."""
    if store is None:
        return
    store.write(LiveSnapshot(
        state.width, state.height, state.thief, state.barriers, scent,
        belief.probabilities, state.step, hint, tokens, "FastMCP connected",
        audit, audit == "pending",
    ))
