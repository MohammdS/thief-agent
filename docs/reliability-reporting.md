# Reliability, Artifacts, and Reporting

## Bounded runtime

Every external operation passes through `ExternalGatekeeper`. Production defaults are a
30-second response deadline, five-second retry delay, three retries, two concurrent calls,
and queue depth 100. Exhaustion raises a controlled technical loss. A 60-second watchdog
detects stalled orchestration, and each sealed turn is checkpointed using fsync plus atomic
replacement before network publication.

## Required JSON artifacts

`ArtifactStore` validates Pydantic models and writes only traversal-safe exact names:

- `declaration_<game_id>.json`
- `config_<game_id>_g<NN>.json`
- `log_<game_id>_g<NN>.json`
- `result_<game_id>.json`

The committed schemas are under `contracts/artifacts/`. The result is hashed without its
self-referential agreement block. Reporting is refused until the Police hash equals the
local canonical hash and `mutual_agreement.confirmed` is true.

## Gmail safety

Gmail uses only `https://www.googleapis.com/auth/gmail.send` and the fixed course recipient
`rmisegal+uoh26finalgame@gmail.com`. Default mode is dry-run and never loads OAuth. Live
mode requires git-ignored `credentials.json` and `token.json`.

The reporting gatekeeper combines a persistent daily quota, token bucket, bounded external
gatekeeper, duplicate attachment suppression, and a failure circuit breaker. OAuth token
refresh happens only in live mode. Repeated failures, malformed API responses, timeouts,
queue overflow, invalid agreement, or duplicate delivery fail closed.

