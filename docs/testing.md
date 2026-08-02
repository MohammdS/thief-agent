# Testing and Evidence

## Automated gates

CI performs a frozen dependency install, Ruff, strict mypy, branch-aware pytest coverage,
the 150-line project-source gate, contract regeneration/drift checking, and the
placeholder-aware submission structure check. Live Ollama is opt-in so CI remains
deterministic; its strict fallback path is covered with mocked provider failures.

`test_peer_runtime.py` drives the complete autonomous Thief loop through a reciprocal
Police transport: health, coordinator negotiation, 35 simultaneous commit/reveal steps,
final nonce audits, subgame digest agreement, final artifact hash agreement, persistence,
and verified replay. A separate-process FastMCP test exercises all six outbound client
operations against the public server tools.

## Six-game qualification

`scripts/run_qualification.py` starts `tests.support.police_stub` in a separate process on
an ephemeral loopback port. The real Thief orchestrator, strategy, commitment code,
physical validators, belief update, artifact models, and replay verifier run unchanged.

Evidence is locked to Git commit
`9b07886b126ca99aa8c0cb0d5f9eedfcb01b6426`. Across six uncounted games:

- every game terminated at the 35-step survival threshold;
- the Police stub placed five permanent barriers per game;
- every saved replay returned `Verified OK`;
- a deliberately changed committed hint returned `TAMPERED`;
- aggregate stub/Thief scores were 30/60 under the shared development config.

The deterministic stub follows a serpentine script. Therefore 6/6 Thief survival is a
pipeline result, not an estimate of strategic strength and not a valid counted result.
The committed package is under `artifacts/qualification/`.

## Reproduce

```powershell
uv sync --frozen
uv run pytest
uv run python scripts/run_qualification.py
uv run python scripts/generate_analysis.py
uv run thief-agent replay artifacts/qualification/log_UNCOUNTED-DEVELOPMENT_g01.json
```

The generated figure labels the test boundary directly. The executed notebook reads the
committed sensitivity JSON and explains that stable selection under one coefficient sweep
does not establish win rate.

## Unverified external boundaries

No counted series against the companion repository is included. Gmail live send is tested
only through a mocked API service; no course email was sent. Public tunnel instructions are
documented but a persistent tunnel URL is deliberately not committed.
