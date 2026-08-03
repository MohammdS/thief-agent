# Shared Police/Thief Contract

This directory is the implementation-neutral compatibility surface for the separately
implemented Police peer.

- `schemas/` contains strict JSON Schemas for all seven FastMCP tools.
- `artifacts/` contains strict schemas for declaration, config, log, and result files.
- `vectors/commitment.json` fixes canonical serialization and SHA-256 behavior.
- `vectors/scent-lock.json` locks the scent equation, exact 5x5 kernel, and example.

Protocol `1.1` reveals `scent_heatmap`, `hint`, optional public `barrier`, and optional
`capture_claim`; `action` and `move` are forbidden until `final_audit`. Unknown payload
fields are rejected. Both peers must run these vectors before a warm-up series and compare
the shared configuration hash before step zero.
