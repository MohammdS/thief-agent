# Prompt Engineering Log

## Baseline policy

Physical actions are never delegated to a language model. Template hints are the default.
The optional Ollama provider receives only prevalidated truth/bluff candidates and must
return bounded structured output. Prompts, model name, outcome, fallback reason, and token
usage will be recorded here during strategy qualification.

## 2026-08-02 - Grounded competitive Ollama prompt

- Goal: let the LLM choose and phrase deception while preventing spatial hallucination.
- Model: local `qwen3:8b`, temperature 0, seed 42, strict JSON schema.
- Input: approved truth/bluff candidates, required cues, preferred intent, word limit, and
  the instruction to maximize escape odds within all game rules.
- Guardrails: no board coordinates or objective Police position are provided; movement is
  selected in Python; output must preserve exactly one approved direction cue.
- First result: safe template fallback because Qwen returned provider `thinking` metadata.
- Adjustment: ignore provider response metadata while continuing to reject unknown fields
  in the actual `choice`/`hint` object.
- Verified result: Ollama produced the grounded bluff `I headed east toward the open edge`
  for a westward move, with 498 prompt and 20 completion tokens in the observed smoke run.

