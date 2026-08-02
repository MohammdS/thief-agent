# Architecture

## Trust boundaries

The objective board is confined to physical validation, qualification, and post-match
replay. Live movement receives `ThiefObservation`, which has no objective Police field.
`AuditFirewall` accepts Police reveals into the ledger but exposes only hint evidence to
strategy. The UI repeats the same separation through `LiveSnapshot`.

The CLI delegates business operations to `ThiefSdk`. During play, `ThiefOrchestrator`
sequences legal movement, language generation, commitment sealing, atomic checkpointing,
and watchdog heartbeat. Network handlers delegate strict validation and idempotency to
`ProtocolService`; they do not make physical decisions.

## Turn data flow

1. Bayesian filtering combines the prior Police belief with the current scent and
   previously audited linguistic evidence.
2. `EvasionStrategy` evaluates all legal moves and selects one deterministically.
3. `HintPolicy` chooses a bounded template or requests grounded Ollama language. Provider
   failure always returns a valid template candidate.
4. `seal_turn` binds action, hint, truth/bluff intent, prior state, and a fresh 256-bit nonce
   into a SHA-256 commitment.
5. The checkpoint is atomically persisted before publication.
6. FastMCP carries commitment first, reveal second; nonce and intent remain secret until
   final audit.
7. Both peers independently validate logs, calculate results, and compare result hashes.

## State and reliability

Explicit match and turn state machines reject illegal phase transitions. Network and LLM
calls use bounded queues, concurrency, a 30-second timeout, five-second delay, and at most
three retries. A 60-second watchdog detects orchestration stalls. Exhaustion becomes a
controlled technical loss instead of an unbounded wait.

Checkpoints use temporary files, flush, `fsync`, and atomic replacement. Wire operations
are idempotent for identical duplicate message IDs and fail for conflicting duplicates.

## Deployment boundary

`thief-agent peer` launches the receiving FastMCP server and outbound autonomous client
loop in one process. The lexicographically smaller group ID anchors the series start and
game UID; the other peer mirrors that exact negotiation. On every step both peers publish
commitments, wait for the opponent commitment, reveal, validate, and continue. Every
subgame ends with mutual nonce audit and an independently calculated terminal digest; the
series ends only after the final result artifact hashes match.

The separate companion Police process must implement the reciprocal contract. The included
qualification runner remains isolated test infrastructure and calls only the deterministic
Police stub; it must not be used as competitive evidence.
