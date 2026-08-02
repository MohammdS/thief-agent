# Architecture Decisions

## ADR-001 - Scent recurrence wording contradiction

The assignment describes scent values as lying in `[0, 0.9]`, while its displayed update
equation is `tau(t+1) = max(0, (1-rho) * tau(t) + delta)` and does not include an upper
clamp. We implement the displayed equation exactly because the assignment requires both
peers to lock the formula and a numeric example before play. Re-emission can therefore
exceed `0.9`; the contract vectors make this choice visible to the Police implementer.

## ADR-002 - Information firewall

Objective positions are accepted only by physical validation, append-only logging, and
post-match replay. Strategy and the live GUI receive a separate local observation type.
This resolves the assignment conflict between reveal validation and partial observability.

