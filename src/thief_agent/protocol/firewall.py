"""Prevent objective movement reveals from reaching strategy or live GUI."""

from __future__ import annotations

from dataclasses import dataclass, field

from thief_agent.protocol.actions import TurnAction
from thief_agent.protocol.messages import RevealTurnRequest


@dataclass(frozen=True, slots=True)
class HintEvidence:
    """Expose only natural-language evidence to live decision code."""

    hint: str


@dataclass(slots=True)
class AuditFirewall:
    """Route objective action data only to the private audit sink."""

    _audit_actions: list[TurnAction] = field(default_factory=list)

    def accept_police_reveal(self, request: RevealTurnRequest) -> HintEvidence:
        """Store the action for audit while returning hint-only evidence."""
        self._audit_actions.append(request.action)
        return HintEvidence(hint=request.hint)

    def actions_for_final_audit(self) -> tuple[TurnAction, ...]:
        """Return an immutable audit view unavailable to strategy interfaces."""
        return tuple(self._audit_actions)

