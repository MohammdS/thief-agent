# Thief Agent

`thief-agent` is a from-scratch, standalone Thief peer for the Distributed
Police-and-Thief over P2P coursework project. It is intentionally independent of the
Police implementation: the peers share only versioned JSON contracts and communicate
through FastMCP.

## Current status

The repository is under milestone-driven construction. The checked-in code must pass its
quality gates at every milestone; unfinished capabilities are listed in [TODO.md](TODO.md)
instead of being presented as complete.

## Design commitments

- The Thief runs as its own process and repository, with no shared live state.
- Python chooses and validates physical actions; an LLM may only produce or interpret
  bounded natural-language hints.
- Commit-reveal binds every move and hint to a fresh nonce for post-match audit.
- The live GUI exposes local truth and belief only. Full state is available only in the
  verified post-match replay.
- External requests pass through bounded gatekeepers with deadlines and retry limits.
- Secrets, OAuth credentials, and tokens are never committed.

## Install

Requirements: Python 3.12 and [`uv`](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/MohammdS/thief-agent.git
cd thief-agent
uv sync --frozen
uv run thief-agent doctor
```

## Command surface

```text
thief-agent doctor                 environment and configuration diagnostics
thief-agent validate [FILE]        validate the shared game configuration
thief-agent peer [--config FILE]   start the Thief FastMCP peer
thief-agent replay LOG             verify and view a completed log
thief-agent report RESULT          dry-run or send an agreed result
```

Commands are introduced behind a single `ThiefSdk` business entry point. See
[docs/PLAN.md](docs/PLAN.md) for the architecture and [docs/protocol.md](docs/protocol.md)
for the compatibility contract being implemented for the companion Police peer.

## Development

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/check_source_limits.py
uv run python scripts/submission_check.py --allow-placeholders
```

Production Python source files are limited to 150 lines and all public modules, classes,
and functions are documented. The final gate requires branch-aware coverage of at least
85 percent.

## Configuration and secrets

The shared, hash-locked rules live in `config/game.json`. Copy
`config/game.toml.example` to a git-ignored `config/game.secret.toml` for peer-local
values. Copy `.env-example` to `.env` only if an integration needs environment secrets.

The eight-character group ID, student identifiers, and companion Police URL are explicit
placeholders. `scripts/submission_check.py` will reject a release until they are replaced.

## Companion repository

Police repository: `REPLACE_WITH_COMPANION_POLICE_REPOSITORY`

## Coursework documentation

- [Product requirements](docs/PRD.md)
- [Architecture and implementation plan](docs/PLAN.md)
- [Documented architecture decisions](docs/decisions.md)
- [Bayesian evasion and grounded language strategy](docs/strategy.md)
- [Reliability, artifacts, and Gmail reporting](docs/reliability-reporting.md)
- [Tracked work](docs/TODO.md)
- [Mechanism PRDs](prd/)
- [Prompt engineering log](docs/prompt-engineering-log.md)

## License

MIT. Coursework submission rules and academic attribution requirements still apply.
