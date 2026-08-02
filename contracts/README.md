# Shared Police/Thief Contract

This directory is the implementation-neutral compatibility surface for the separately
implemented Police peer.

- `schemas/` contains strict JSON Schemas for all seven FastMCP tools.
- `vectors/commitment.json` fixes canonical serialization and SHA-256 behavior.
- `vectors/scent-lock.json` locks the scent equation, exact 5x5 kernel, and example.

Unknown payload fields are rejected. Both peers must run these vectors before a warm-up
series and compare the shared configuration hash before step zero.

