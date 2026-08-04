# Police Peer Compatibility Contract

The current breaking wire-contract version is `1.3`.

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

1. Thief owns the initial turn token. The service rejects a new commitment from any
   non-owner or for any skipped step.
2. Before choosing the current action, the owner decays its private accumulated trail by
   `0.1`. That decayed pre-action trail is the public heatmap for this turn. It is empty on
   the role's first turn because that role has no earlier emission.
3. The owner creates a fresh 256-bit nonce and hashes canonical JSON binding the game,
   subgame, step, role, next token owner, previous state, hidden current action, delayed
   heatmap, hint, truth/bluff intent, and nonce.
4. `commit_turn` publishes only the SHA-256 hash. The opponent must acknowledge that hash
   before any reveal is sent. Only then does `reveal_turn` publish the delayed row-major
   heatmap, hint, token handoff, and any public Police barrier. It never publishes an action
   or movement field.
5. After applying the current hidden action locally, the owner deposits the current 5x5
   emission into its private trail. That emission is withheld now; it can first affect the
   role's next reveal, after another `0.1` decay.
6. Receiving `turn_token: police` permits Police step 1; Police returns
   `turn_token: thief`, permitting Thief step 2. The sequence is
   `T1 -> P1 -> T2 -> P2`, never simultaneous.
7. At the survival threshold the final Thief turn is terminal, so it has no Police reply.
   Duplicate identical messages remain idempotent; conflicting or out-of-turn messages
   fail visibly.
8. `final_audit` discloses the complete action, heatmap, hint, intent, token, and nonce.
   Constant-time commitment comparison, immediate/final reveal matching, objective replay,
   and action-derived scent verification produce `Verified OK` or `TAMPERED`.

The live Thief process advances only its own known position and applies public Police
barriers. A received heatmap describes Police's accumulated trail through its previous
action, not the position reached by its just-committed action. Thief filters the historical
belief with that trail and predicts one legal hidden Police move. Exact actions and the
earliest overlap, barrier capture, or imprisonment are reconstructed only after final
audit. Because neither peer can prove current overlap from delayed evidence, live play does
not stop on an unverified overlap claim. A revealed Police barrier is different: the Thief
can compare that public cell with its own private cell or mobility. For barrier capture or
imprisonment it sends `capture_claim` referencing the triggering Police commitment, both
peers enter final audit, and the claim is accepted only if objective replay proves it.

This contract deliberately resolves the assignment's `incoming hint + scent` strategy
boundary in favor of location privacy. Contract `1.0`, which put `action` in
`reveal_turn`, is incompatible and must not be used by the companion Police peer. Contract
`1.1`, which committed both roles before ordered reveal, and `1.2`, which exposed the
current action's emission in the same turn, are also incompatible.

## Step zero

`StepZeroDeclaration` locks team, role, subgame, OS, CPU, RAM, GPU, language model, exact
40-character Git commit, token budget, and tokens consumed. The orchestrator signs its
canonical bytes with HMAC-SHA256 before entering the running-subgame state.

## Compatibility procedure

The Police implementation should independently generate the schemas, reproduce both
contract vectors, compare the shared configuration SHA-256, and run an uncounted localhost
warm-up. Neither repository imports runtime code from the other.
