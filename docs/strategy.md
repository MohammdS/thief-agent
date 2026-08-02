# Thief Strategy

## Belief update

The Thief starts from a uniform Police-location prior over non-barrier cells. Each full
turn applies a Bayesian likelihood from the observed Police scent map. Explicit cardinal
language can reweight board halves using a smoothed truth probability learned only from
already audited hints. Blocked cells always receive zero mass and every posterior is
normalized.

## Algorithmic movement

The LLM never selects a physical action. `EvasionStrategy` scores every locally legal
N/S/E/W/STAY candidate using:

- probability that Police can reach the target next;
- expected Manhattan distance from Police belief;
- barrier-free reachable area and immediate mobility;
- best second-ply escape safety;
- enclosure and recent-position penalties;
- stable deterministic tie-breaking.

This keeps all movement reproducible and legality-testable. The benchmark artifact under
`artifacts/analysis/strategy-benchmark.json` records representative open, corner, wall,
and revisit scenarios.

## Language provider

Template language is the committed default. Opt-in Ollama `qwen3:8b` receives only one
truth candidate, one bluff candidate, preferred intent, word limit, and a non-geometric
tactical objective. The system prompt asks it to maximize escape odds within the rules but
explicitly forbids movement selection.

Ollama must return strict JSON. The grounder requires the selected direction cue, rejects
conflicting cues and coordinates, enforces the negotiated word limit, and counts prompt
and completion tokens. Timeout, HTTP error, malformed JSON, unknown fields, hallucinated
direction, or coordinate leakage causes a deterministic template fallback.

