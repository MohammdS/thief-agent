# Police Peer Compatibility Contract

This repository will publish strict JSON Schemas and fixed canonical/hash vectors. The
wire tools are `health`, `negotiate`, `commit_turn`, `reveal_turn`, `capture_claim`,
`final_audit`, and `propose_result` over FastMCP Streamable HTTP.

Every message carries schema version, game/subgame/step identity, sender role, UUID,
timestamps, expiry, configuration hash, and prior-state hash. Unknown fields are rejected.
The detailed schema and test vectors arrive with protocol milestone 3.

