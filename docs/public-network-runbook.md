# Public Network Runbook

## Prepare local configuration

Copy `config/game.toml.example` to the ignored `config/game.secret.toml`. Replace team and
group identity, set `peer.opponent_group_id`, then set `peer.opponent_mcp_url` to the
companion Police `/mcp` endpoint.
Do not place access tokens or OAuth credentials in either configuration file.

Start the Thief endpoint:

```powershell
uv run thief-agent validate config/game.json
uv run thief-agent peer --config config/game.secret.toml --game-config config/game.json
```

The default local address is `http://127.0.0.1:8002/mcp`. This one command serves inbound
tools and drives outbound health, negotiation, commitment, reveal, audit, and result calls.
For a counted series, append `--declaration config/declaration.secret.json`; counted startup
fails closed if that agreed file is absent.

## Optional ngrok exposure

In a second terminal, after authenticating your own ngrok installation:

```powershell
ngrok http 8002
```

Share only the generated HTTPS URL ending in `/mcp`. Put the Police URL only in the
git-ignored local TOML. Tunnel URLs are temporary unless your ngrok account reserves one;
re-run health and negotiation whenever either URL changes.

## Pre-match checklist

1. Both repositories are public, independent, and pinned to exact 40-character commits.
2. Both peers report the same protocol version and shared configuration SHA-256.
3. JSON schemas and canonical/hash vectors match byte-for-byte.
4. Group IDs, roles, timezone, start time, six subgames, and token budget are agreed.
5. Each side can call the other's `health` endpoint under the 30-second deadline.
6. Run one uncounted warm-up through commit, reveal, final audit, result proposal, replay,
   and dry-run report.
7. Save declaration/config/log/result artifacts independently and compare result hashes.

Start both peer commands. The lower group ID automatically proposes the shared UTC series
anchor; the other mirrors it. Neither side reveals until both commitments are present.

## Failure handling

Do not silently widen deadlines, retries, or queues during a counted game. An expired
message, conflicting duplicate, config mismatch, invalid commitment, malformed LLM output,
or watchdog expiry must fail visibly. Preserve checkpoints and logs for audit. Never reveal
nonce or truth/bluff intent before final audit, and never expose objective Police movement
to the live Thief strategy or GUI.
