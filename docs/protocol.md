# Police Peer Compatibility Contract

This repository publishes strict JSON Schemas and fixed canonical/hash vectors under
[`contracts/`](../contracts/). The wire tools are `health`, `negotiate`, `commit_turn`,
`reveal_turn`, `capture_claim`, `final_audit`, and `propose_result` over FastMCP
Streamable HTTP at the negotiated `/mcp` URL.

Every message carries schema version, game/subgame/step identity, sender role, UUID,
timestamps, expiry, configuration hash, and prior-state hash. Unknown fields are rejected.
## Turn ordering

1. Each peer creates a fresh 256-bit nonce and hashes canonical JSON binding the game,
   subgame, step, role, previous state, action, hint, truth/bluff intent, and nonce.
2. `commit_turn` publishes only the SHA-256 hash and receives an acknowledgment.
3. `reveal_turn` publishes action and hint, but keeps nonce and intent secret.
4. Duplicate identical messages are idempotent; conflicting duplicates fail visibly.
5. `final_audit` discloses the complete payload after play. Constant-time comparison and
   immediate/final reveal matching produce exactly `Verified OK` or `TAMPERED`.

Revealed Police movement is accepted by the physical validator and audit ledger. The audit
firewall returns hint-only evidence to the Thief strategy and live GUI.

## Step zero

`StepZeroDeclaration` locks team, role, subgame, OS, CPU, RAM, GPU, language model, exact
40-character Git commit, token budget, and tokens consumed. The orchestrator signs its
canonical bytes with HMAC-SHA256 before entering the running-subgame state.

## Compatibility procedure

The Police implementation should independently generate the schemas, reproduce both
contract vectors, compare the shared configuration SHA-256, and run an uncounted localhost
warm-up. Neither repository imports runtime code from the other.

