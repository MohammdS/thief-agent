"""Publish information-safe Thief state for the optional live GUI."""

from __future__ import annotations

from dataclasses import dataclass

from thief_agent.belief.model import BeliefMap
from thief_agent.domain.outcome import Outcome
from thief_agent.domain.scent import ScentMap
from thief_agent.domain.state import BoardState
from thief_agent.ui.model import LiveSnapshot
from thief_agent.ui.store import LiveSnapshotStore


@dataclass(frozen=True, slots=True)
class LivePresenter:
    """Publish concise Thief-side protocol milestones to the monitor."""

    store: LiveSnapshotStore | None
    subgame: int
    series_size: int

    def turn_ready(
        self, state: BoardState, scent: ScentMap, belief: BeliefMap,
        hint: str, tokens: int,
    ) -> None:
        """Show that the verified Police reveal handed the token to Thief."""
        publish_live(
            self.store, state, scent, belief, hint, tokens,
            subgame=self.subgame,
            series_size=self.series_size,
            local_turn=True,
            protocol_state="Thief turn ready",
            event="Police reveal verified; turn token received",
        )

    def audit_claim(
        self, state: BoardState, scent: ScentMap, belief: BeliefMap,
        hint: str, tokens: int, reason: str,
    ) -> None:
        """Show the public claim after sending it and before final audit."""
        terminal = "capture" if reason == "barrier" else reason
        publish_live(
            self.store, state, scent, belief, hint, tokens,
            subgame=self.subgame,
            series_size=self.series_size,
            audit="in progress",
            protocol_state="Final audit",
            event=f"Public {reason} capture claimed; exchanging secrets",
            terminal_reason=terminal,
        )

    def audit_horizon(
        self, state: BoardState, scent: ScentMap, belief: BeliefMap,
        hint: str, tokens: int,
    ) -> None:
        """Show the transition from the turn limit into final audit."""
        publish_live(
            self.store, state, scent, belief, hint, tokens,
            subgame=self.subgame,
            series_size=self.series_size,
            audit="in progress",
            protocol_state="Final audit",
            event="Turn limit reached; exchanging audit secrets",
        )

    def finished(
        self, state: BoardState, scent: ScentMap, belief: BeliefMap,
        tokens: int, outcome: Outcome,
    ) -> None:
        """Show the verified objective result and score."""
        publish_live(
            self.store, state, scent, belief, "", tokens,
            subgame=self.subgame,
            series_size=self.series_size,
            audit="Verified OK",
            protocol_state="Finished",
            event=verified_event(state, outcome),
            terminal_reason=outcome.reason.value,
        )


def verified_event(state: BoardState, outcome: Outcome) -> str:
    """Describe whether audit verified a public claim or hidden capture."""
    if outcome.reason.value == "capture" and state.thief in state.barriers:
        label = "Verified barrier capture claim"
    elif outcome.reason.value == "capture":
        label = "Verified movement capture reconstructed by audit"
    elif outcome.reason.value == "imprisonment":
        label = "Verified imprisonment capture claim"
    else:
        label = f"Verified {outcome.reason.value}"
    return f"{label}: Police {outcome.police_score}, Thief {outcome.thief_score}"


def publish_live(
    store: LiveSnapshotStore | None, state: BoardState, scent: ScentMap,
    belief: BeliefMap, hint: str, tokens: int,
    *,
    subgame: int,
    series_size: int,
    audit: str = "pending",
    local_turn: bool = False,
    protocol_state: str = "Waiting for Police",
    event: str = "Reveal sent",
    terminal_reason: str | None = None,
) -> None:
    """Write one local-truth-only Thief snapshot when UI output is enabled."""
    if store is None:
        return
    store.write(
        LiveSnapshot(
            state.width, state.height, state.thief, state.barriers, scent,
            belief.probabilities, state.step, hint, tokens, "FastMCP connected",
            audit, local_turn, subgame, series_size, protocol_state, event,
            terminal_reason,
        )
    )
