# Architecture Decisions

## ADR-001 - Scent recurrence wording contradiction

The assignment describes scent values as lying in `[0, 0.9]`, while its displayed update
equation is `tau(t+1) = max(0, (1-rho) * tau(t) + delta)` and does not include an upper
clamp. We implement the displayed equation exactly because the assignment requires both
peers to lock the formula and a numeric example before play. Re-emission can therefore
exceed `0.9`; the contract vectors make this choice visible to the Police implementer.

## ADR-002 - Information firewall

Protocol `1.0` exposed an action in every live reveal and relied on an internal firewall.
That still allowed the remote process to reconstruct exact positions from known starts.
Protocol `1.3` removes actions from the live wire schema, enforces token handoffs, and
reveals only the accumulated trail from before the current hidden action. The first reveal
from each role is empty. On later turns the private trail is decayed, committed, acknowledged,
and revealed before the current emission is added privately for the role's next turn.
Hidden actions and nonces are disclosed after the subgame, when objective replay verifies
action legality, delayed scent history, the earliest terminal outcome, and scores.
