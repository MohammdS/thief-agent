# Local-Truth GUI and Verified Replay

Run `thief-agent gui --config config/game.json --state
artifacts/matches/runtime/live.json` in a second process while the peer is active. The peer
atomically publishes safe snapshots after reveals.

The Tkinter live window consumes only `LiveSnapshot`. Its type contains local Thief
position, known barriers, observed Police scent, Police belief, hints, tokens, network
state, and audit state. It has no field for objective Police position or movement. Controls
are enabled only during a non-terminal local turn.

![Thief local-truth GUI](screenshots/thief-live-local-truth.png)

After final nonce disclosure, `ReplayVerifier` checks the whole-log mutual hash, every turn
commitment, and every physical transition before reconstructing objective state. Altered,
deleted, reordered, or illegal records produce exact `TAMPERED` status. Valid logs produce
exact `Verified OK`.

![Verified replay](screenshots/thief-replay-verified.png)

![Tamper evidence](screenshots/thief-replay-tampered.png)

The PNG evidence renderer uses the same information-safe presentation model and supports
headless CI. The interactive replay window exposes full Police and Thief positions only
post-match.
