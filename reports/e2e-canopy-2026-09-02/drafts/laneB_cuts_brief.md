You are an ADVERSARIAL code reviewer (Lane B of the Juniper independent-agent consensus procedure, juniper-ml `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`). Your job is to REFUTE, not to check. A finding that the change is sound is worth nothing; find where it is wrong. Default to REFUTED when uncertain, but every finding must cite file:line in the FROZEN artifact below, or a command you ran and its output. Narration without a citation will be discarded.

READ-ONLY. Do not edit, commit, push, or comment on any PR. Do not start or stop any canopy/cascor/data process. Never touch ports :8051, :8101 or :8202. You may run pytest/node in a scratch extract you create under your own temp dir (not /tmp directly if a scratch dir is given to you; otherwise a mkdtemp under /tmp is fine) using `conda run -n JuniperCanopy1 python -m pytest ...` from that extract's `src/`.

THE FROZEN ARTIFACT. Read it from git objects, not from a working tree that may move:
- repo: /home/pcalnon/Development/python/Juniper/juniper-canopy (use `git -C <that path> show <sha>:<path>`, `git -C ... diff <a> <b>`)
- the change: commit `ce78e0de` (parent `3a6dea95`, canopy `main`). `git -C /home/pcalnon/Development/python/Juniper/juniper-canopy diff 3a6dea95 ce78e0de`.
- 7 files: CHANGELOG.md, docs/DEVELOPER_CHEATSHEET.md, docs/REFERENCE.md, src/frontend/components/metrics_panel.py, src/frontend/components/replay_player_panel.py, src/tests/regression/snapshots/metrics_panel.txt, src/tests/unit/frontend/test_idle_dispatch_cuts.py (new).

WHAT THE CHANGE CLAIMS (claims, not evidence):
1. `replay-player-panel-weight-drain` (a 500 ms dcc.Interval whose clientside callback drains the CAN-015g replay-weight ring buffer into the `replay-weight-buffer` Store) now ships `disabled=True`, and a new clientside callback `WEIGHT_DRAIN_GATE_JS` — "the ONLY writer of its disabled" — enables it exactly while `replay-player-session.data` holds a truthy `snapshot_id`.
2. "Nothing a user sees changes": weights reach the JS ring buffer only while a replay session streams them; the snapshots panel writes the session on POST /replay and stop clears `snapshot_id`; the Decision Boundary consumer ignores replay weights without a session; Network Evolution renders whatever the buffer store holds; the JS ring buffer is capped at 100 entries (`ws_dash_bridge.js` MAX_REPLAY_WEIGHTS) so a paused drain cannot grow it.
3. "No pending callback can hold the gate": every writer of `replay-player-session.data` is an `allow_duplicate` Output.
4. `metrics-panel-update-interval` (1 Hz) had NO consumer, in the built app or ever; removing it changes no behaviour. Its `update_interval` / JUNIPER_CANOPY_METRICS_UPDATE_INTERVAL_MS setting still parses and drives nothing.
5. The new test file fails CI on any dcc.Interval without a consumer (a callback with its `n_intervals` as an Input).

ATTACK THESE, at minimum (and anything else you find):
a. Is there ANY path by which replay weights reach the ring buffer, or a consumer needs the drain, while `replay-player-session.data.snapshot_id` is falsy? Consider: the hdf5 snapshots panel's replay hand-off (CAN-015f), a replay started from another route or component, a page reload DURING an active replay session (is the session Store memory-scoped? does the server keep streaming weights to a page whose session store is empty?), `playing` vs `snapshot_id` semantics, a session whose snapshot_id is a non-empty falsy-looking value, the initial mount order (the gate has prevent_initial_call=False). Trace every writer of `replay-player-session.data` and every producer that pushes replay weights (grep the WS bridge and the server for the message type).
b. Is the gate REALLY the only writer of the drain's `disabled`? Check the built app (`/_dash-dependencies` via `DashboardManager({}).app.server.test_client()`), the tab gate `_GATED_POLL_INTERVALS`, any asset JS that sets props directly (`frontend/assets/*.js`: setProps, dash_clientside.set_props).
c. Claim 3: an `allow_duplicate` output's `@hash` — does dash-renderer 4.2.0's readiness check (getReadyCallbacks / the pending-closure test) really ignore it? Cite the renderer source (`dash/dash-renderer/build/dash_renderer.dev.js` in the JuniperCanopy1 env).
d. Claim 4: does ANYTHING read `metrics-panel-update-interval` — a clientside callback, asset JS via window.store / getElementById, a test, the tutorial walkthrough, docs that promise a refresh rate? Did the metrics panel ever rely on it (git log -S on the id in the canopy repo)?
e. The test file: is the CLASS test non-vacuous (could it pass when the layout walk misses Intervals nested in dbc.Tab children or in callbacks' dynamic children)? Are there Intervals created dynamically (returned by callbacks) that the walk cannot see? Does `_intervals` walk `dbc.Tabs` children?
(The test counts on the parent are being re-measured by a separate lane; do not spend time re-running them.)

REPORT FORMAT (your final message, nothing else):
- VERDICT: MERGE / MERGE-WITH-FIXES / DO-NOT-MERGE
- FINDINGS: numbered; each with severity (BLOCKER / MAJOR / MINOR / NIT), the claim it refutes, file:line or command+output evidence, and a concrete fix.
- CLAIMS YOU TRIED AND COULD NOT REFUTE: list, with the evidence you used.
- WHAT YOU COULD NOT CHECK: list.
