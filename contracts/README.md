# Shared Police/Thief Contract

This directory is the implementation-neutral compatibility surface for the separately
implemented Police peer.

- `schemas/` contains strict JSON Schemas for all seven FastMCP tools.
- `artifacts/` contains strict schemas for declaration, config, log, and result files.
- `vectors/commitment.json` fixes canonical serialization and SHA-256 behavior.
- `vectors/scent-lock.json` locks the scent equation, exact 5x5 kernel, and example.

Protocol `1.3` reveals `turn_token`, the pre-action delayed `scent_heatmap`, `hint`, and an
optional public `barrier`; `action` and `move` are forbidden until `final_audit`. The first
heatmap from each role is empty. A Thief that is hit or imprisoned by a public barrier uses
`capture_claim` with the Police commitment as opaque evidence, then final audit proves the
claim. Unknown payload fields are rejected. Both peers must run these vectors before a
warm-up series and compare the shared configuration hash before step zero.
