# Technical Plan

The CLI and GUI call only `ThiefSdk`. The SDK delegates to an orchestrator, which
is the sole gateway to domain, strategy, language, protocol, reliability, persistence,
replay, and reporting subsystems. No subsystem may bypass the orchestrator to mutate match
state.

The peer is simultaneously a FastMCP HTTP server and bounded FastMCP client. All payloads
use strict versioned schemas. A protocol state machine and cryptographic turn state machine
reject illegal ordering. The strategy receives local truth, opponent scent, public barrier
declarations, and processed verbal evidence. Protocol `1.3` gives Thief the initial token,
requires Commit then Acknowledge then Reveal on every token-gated turn, and reveals the
previous private scent trail after 0.1 decay. The current move and its emission stay hidden
until final audit and the role's next scent disclosure, respectively.

See the root [PLAN.md](../PLAN.md) for milestone gates.
