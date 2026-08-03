# Police Peer Compatibility Contract

The current breaking wire-contract version is `1.1`.

This repository publishes strict JSON Schemas and fixed canonical/hash vectors under
[`contracts/`](../contracts/). The wire tools are `health`, `negotiate`, `commit_turn`,
`reveal_turn`, `capture_claim`, `final_audit`, and `propose_result` over FastMCP
Streamable HTTP at the negotiated `/mcp` URL.

Every message carries schema version, game/subgame/step identity, sender role, UUID,
timestamps, expiry, configuration hash, and prior-state hash. Unknown fields are rejected.

Negotiation also locks the sender group, game UID, series UTC anchor, counted flag, and
subgame count. The lower group ID coordinates the anchor to avoid dual-initiation races.
Subgame result proposals exchange terminal-state digests, fixed scores, token use, and exact
Git commits. A final series proposal confirms the canonical result artifact hash.

## Turn ordering

1. Each peer creates a fresh 256-bit nonce and hashes canonical JSON binding the game,
   subgame, step, role, previous state, hidden action, scent heatmap, hint, truth/bluff
   intent, and nonce.
2. `commit_turn` publishes only the SHA-256 hash and receives an acknowledgment.
3. `reveal_turn` publishes the row-major scent heatmap and hint. It may also publish a
   Police barrier or terminal claim, but it has no action or movement field.
4. Duplicate identical messages are idempotent; conflicting duplicates fail visibly.
5. `final_audit` discloses the complete action, heatmap, hint, intent, and nonce after play.
   Constant-time commitment comparison, immediate/final reveal matching, objective replay,
   and action-derived scent verification produce `Verified OK` or `TAMPERED`.

The live Thief process advances only its own known position. It updates Police belief from
the received heatmap and hint, and applies only public Police barriers. Exact Police actions
are reconstructed after final audit. A terminal claim stops live play and is accepted only
if the final hidden actions prove the claimed overlap, barrier capture, or imprisonment.

This contract deliberately resolves the assignment's `incoming hint + scent` strategy
boundary in favor of location privacy. Contract `1.0`, which put `action` in
`reveal_turn`, is incompatible and must not be used by the companion Police peer.

## Step zero

`StepZeroDeclaration` locks team, role, subgame, OS, CPU, RAM, GPU, language model, exact
40-character Git commit, token budget, and tokens consumed. The orchestrator signs its
canonical bytes with HMAC-SHA256 before entering the running-subgame state.

## Compatibility procedure

The Police implementation should independently generate the schemas, reproduce both
contract vectors, compare the shared configuration SHA-256, and run an uncounted localhost
warm-up. Neither repository imports runtime code from the other.
