"""Auditable beta profile for estimating opponent hint honesty."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TruthProfile:
    """Learn a smoothed truth probability from verified prior hints."""

    truthful: int = 1
    deceptive: int = 1

    def __post_init__(self) -> None:
        """Reject negative or empty beta counts."""
        if self.truthful < 0 or self.deceptive < 0 or self.truthful + self.deceptive == 0:
            raise ValueError("truth profile counts must be non-negative and non-empty")

    @property
    def probability(self) -> float:
        """Return the posterior mean probability of a truthful hint."""
        return self.truthful / (self.truthful + self.deceptive)

    def record(self, was_truthful: bool) -> None:
        """Update the profile only after objective final audit."""
        if was_truthful:
            self.truthful += 1
        else:
            self.deceptive += 1

