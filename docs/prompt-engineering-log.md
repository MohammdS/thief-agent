# Prompt Engineering Log

## Baseline policy

Physical actions are never delegated to a language model. Template hints are the default.
The optional Ollama provider receives only prevalidated truth/bluff candidates and must
return bounded structured output. Prompts, model name, outcome, fallback reason, and token
usage will be recorded here during strategy qualification.

