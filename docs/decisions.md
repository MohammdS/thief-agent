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
Protocol `1.1` removes actions from the live wire schema: peers exchange only scent,
language, public barriers, and terminal claims. Hidden actions are disclosed after the
subgame, when objective replay verifies action legality, scent history, claims, and scores.
