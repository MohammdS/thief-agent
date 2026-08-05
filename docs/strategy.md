# Thief Strategy

## Belief update

The shared Police start supplies the first point belief. A received heatmap contains the
decayed trail through Police's previous action; it deliberately excludes the current
action's new emission. The Thief applies that historical evidence to its prior belief,
then `predict_belief` spreads probability over one legal hidden N/S/E/W/STAY action and
removes public barriers. It never converts the delayed trail into exact current Police
state.

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

The receiver keeps a smoothed `TruthProfile`, initialized at 0.5. Its current probability
is passed into the hint likelihood during each live belief update, so a hint can help or
mislead without ever selecting a physical action. Opposite directional words make a hint
ambiguous and remove its evidence. For an unambiguous hint, the belief engine compares its
direction with the signed directional balance of the received scent map: conflict lowers
the hint exponent toward neutrality and temporarily lowers the current hint-truth odds so
scent dominates, while agreement raises both so the two evidence sources reinforce one
another. The persistent profile is updated only from the opponent's verified final-audit
disclosures and is retained across subgames.

## Language provider

Template language is the committed default. Opt-in Ollama `qwen3:8b` receives only one
truth candidate, one bluff candidate, preferred intent, word limit, and a non-geometric
tactical objective. The system prompt asks it to maximize escape odds within the rules but
explicitly forbids movement selection.

Ollama must return strict JSON. The grounder requires the selected direction cue, rejects
conflicting cues and coordinates, enforces the negotiated word limit, and counts prompt
and completion tokens. Timeout, HTTP error, malformed JSON, unknown fields, hallucinated
direction, or coordinate leakage causes a deterministic template fallback.
