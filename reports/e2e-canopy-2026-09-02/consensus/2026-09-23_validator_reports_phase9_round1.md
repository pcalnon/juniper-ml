<!-- markdownlint-disable -->

# Phase 9 consensus, round 1 -- canopy#676 (idle cuts) and F-CANOPY-055's first fix

Verbatim final reports of the four round-1 lanes, 2026-09-23 (juniper-ml notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9). Each lane was briefed separately and none saw another's report. Briefs: reports/e2e-canopy-2026-09-02/drafts/ (F-055) and the session scratchpad (cuts).

## Lane A -- canopy#676 measurements

*agent `afab4bfc720240789` · round 1 · last-assistant-text (not resumed) · 17083 chars*

| measurement | claimed | re-derived | MATCH/MISMATCH/NO ARTIFACT | evidence (command + key output) |
|---|---|---|---|---|
| M1 (tree identities, preamble) | The PR head `f4d864df` has the same tree as `78c057e2`, and the `src/` trees of 78c057e2 and ce78e0de are identical | Same tree `624b574d…` for f4d864df and 78c057e2. Same `src/` tree `4938f685…` in ce78e0de, 78c057e2 and f4d864df. ce78e0de and 78c057e2 differ only in `CHANGELOG.md` | MATCH | `git rev-parse f4d864df^{tree} 78c057e2^{tree} ce78e0de:src 78c057e2:src f4d864df:src`. `git diff --stat f4d864df 78c057e2` is empty. `git diff --stat ce78e0de 78c057e2` gives `CHANGELOG.md \| 6 +++++-` |
| M1a (rebuild diff) | `git diff 723ee812 668380ec` and `git diff 3a6dea95 ce78e0de` are identical over `src/frontend/ docs/ src/tests/unit/` once `index` and `@@` lines are removed | Identical, context lines included. Both diffs are 324 lines raw and 311 after stripping. Both commits touch the same 7 files | MATCH | `grep -v -E '^(index \|@@)'` on each diff, then `cmp` exits 0. Both have sha256 `718958221bd402d7…` (files `m1_orig.diff` and `m1_rebuilt.diff` in the scratch dir `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneA_cuts.iVwNcF/`) |
| M1b (CHANGELOG at PR head) | canopy `CHANGELOG.md` at f4d864df vs 3a6dea95: 31 lines added, 0 deleted, one entry, placed after "their hover hint." and before "- **The replay controls never applied" | 31 added, 0 deleted, in one hunk (`@@ -133,6 +133,37 @@`). It is one top-level bullet with 5 sub-bullets at lines 136-166 of f4d864df:`CHANGELOG.md`. Line 135 is "their hover hint." and line 167 is "- **The replay controls never applied". Those two anchors are adjacent (135/136) in 3a6dea95. The entry sits under `## [Unreleased]` / `### Fixed` | MATCH | `git diff --numstat 3a6dea95 f4d864df -- CHANGELOG.md` gives `31 0`. `git show f4d864df:CHANGELOG.md \| grep -n …` gives lines 135, 136 and 167 |
| M1c (CHANGELOG history) | ce78e0de added 27 lines; 78c057e2 added "one sentence" | ce78e0de: 27 added, 0 deleted. 78c057e2: 5 added, 1 deleted — one line rewrapped and **three** sentences added ("Against its parent … across two live checks (…)." / "The first scored consistent (X/C 0.76)." / "The second ran on a host at a load average of 8–13 and scored inconsistent, one window 2% slower than both neighbours (X/C 0.79)."). Net +4 gives 31. The original 668380ec added 28 lines: the same 27 content lines plus a trailing blank, placed at the top of `### Fixed` | Line counts MATCH; "one sentence" MISMATCH (it is three) | `git diff --numstat` gives `27 0` for 3a6dea95..ce78e0de and `5 1` for ce78e0de..78c057e2. Comparing the added lines of the original and the rebuild with `diff` shows only `28d27 < +` |
| M2 (snapshot) | `src/tests/regression/snapshots/metrics_panel.txt` differs from the parent only by removal of `Interval(id='metrics-panel-update-interval', interval=1000, n_intervals=0), `, and ce78e0de's code generates it | Character level: one change, a 76-character deletion. `parent.replace(target,'',1) == ce78e0de` is True. The target occurs once in the parent and zero times in ce78e0de. `Interval(` count goes from 3 to 2. 723ee812→668380ec shows the same single deletion. Generation: `test_panel_layout_snapshots.py` gives 2 PASSED at ce78e0de, and the parent-extract control gives 2 PASSED | MATCH | `difflib.SequenceMatcher` over `git show <c>:…metrics_panel.txt`. `git archive ce78e0de \| tar -x`, then `mkdir logs`, then from `src`: `conda run -n JuniperCanopy1 python -m pytest tests/regression/test_panel_layout_snapshots.py -q -p no:cacheprovider -rA` gives `PASSED …[metrics_panel]` and `PASSED …[dataset_plotter]`. They passed rather than skipped (the test skips only when the baseline is missing). After the run the baseline blob is still `e61fc59c…`, the committed one. `--co -s` printed `src_dir=<extract>/src`, so the main canopy checkout was not imported |
| M3 (falsification) | `src/tests/unit/frontend/test_idle_dispatch_cuts.py`: 9/9 pass at ce78e0de. On 3a6dea95, 7 fail and 2 pass (`test_the_drain_is_not_in_the_tab_gate`, `test_no_pending_callback_can_hold_the_gate`). The consumer test names exactly `['metrics-panel-update-interval']` | **ce78e0de: 9 PASSED** (every_interval_has_a_consumer, metrics_panel_has_no_update_interval, drain_ships_disabled, one_writer_of_disabled…, drain_is_not_in_the_tab_gate, no_pending_callback_can_hold_the_gate, gate_is_the_registered_function, disabled_unless_a_session_exists, register_callbacks_still_builds_on_a_bare_app). **3a6dea95 with the copied file** (blob `ad0cb566…`, same as ce78e0de's): the two named tests PASSED and the other 7 FAILED, each on its intended assertion, with no import or collection errors | MATCH | Same pytest command on each extract. Parent failure messages: `…: ['metrics-panel-update-interval']`; `'metrics-panel-update-interval' not in {…}`; `assert None is True`; `0 writers of …disabled`; `no WEIGHT_DRAIN_GATE_JS` (twice); `assert False`. Node was found at `/home/pcalnon/.nvm/versions/node/v24.13.1/bin/node`, so the node test ran rather than skipped. Log: `m3_parent.log` in the scratch dir |
| M4a (verdicts) | The stored `verdicts` in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth/reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_idle_cuts_live_check_rebuilt_ce78e0de.json` follow from the rule in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth/util/ad-hoc/2026-09-23_idle_cuts_live_check.py` | Recomputed: STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT, X_over_C_p50 0.79 (0.78932), ERRORS_no_worse True. This equals the stored set. The per-window `dead_present`, `drain_disabled` and `drain_ticks_10s` values, re-derived from the raw `start`/`after_10s` records (script lines 122-123), match the stored ones in all 5 windows | MATCH | Script lines 188-206 run verbatim with `python3 -c` over `…_rebuilt_ce78e0de.json`. X1 3912.6 < min(C1, C2) = 5336.9 holds. X2 5415.8 < min(C2, C3) = 5275.5 fails. X2 > max(C2, C3) = 5336.9, so INCONSISTENT. The first-run `2026-09-23_idle_cuts_live_check.json` also recomputes to its stored set: CONSISTENT, 0.76 |
| M4b (served commits) | C windows serve 3a6dea95…, X windows ce78e0de… | C1, C2, C3: `3a6dea95dcbe717e598f5d32a9774e4779dde842`. X1, X2: `ce78e0de681b8e3000f482360e1f680514e92d6f` | MATCH | `serving.git_sha` in `…_rebuilt_ce78e0de.json`. Independently corroborated (see instrument finding 7) |
| M4c (per-window L p50 / n) | (report) | C1 7115.1 ms / 109; X1 3912.6 / 170; C2 5336.9 / 127; X2 5415.8 / 136; C3 5275.5 / 131. Drain ticks per 10 s: C 5, 7, 7; X 0, 0. Console errors: 0 in every window. Session path: enabled after 1.7 s with 5 ticks, disabled after 2.5 s with 0 ticks | n/a | Values taken from `…_rebuilt_ce78e0de.json` |
| M5 (instrument adequacy) | STRUCTURE and SESSION PASS mean the drain is gated and the dead timer is gone | No false-PASS route exists for `drain_disabled` or for the SESSION enable/disable legs. Two routes to a hollow pass exist in the code: 0 ticks from a missing node, and dead-timer "absence" from an unpopulated `paths.strs`. The raw records rule out the first for this run, and the second is excluded within each window. `write.ok` is not evidence of a Store change, and the verdict does not use it | MATCH for this run, with the gaps listed below | See INSTRUMENT FINDINGS |
| M6 (full suite) | `src/tests/unit/` + `src/tests/regression/` at ce78e0de: 6806 passed, 4 skipped, 0 failed | 95 progress lines. `.` = 6806, `s` = 4, and there are no F/E/x/X characters. 94×72 + 42 = 6810, and the last line reads `[100%]`. The `-ra` summary has only `SKIPPED [4] tests/regression/test_candidate_visibility.py: Requires running server`. Collecting the same paths at ce78e0de gives 287 files and **6810** tests, 9 of them from test_idle_dispatch_cuts.py | Count MATCH; the "at ce78e0de" part is corroborated only indirectly | Character count with `python3 -c` over `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/cuts_full_suite.log`. `pytest tests/unit/ tests/regression/ --collect-only -q` on the ce78e0de extract (collection only, no run), saved as `m6_collect_ce78.txt` in the scratch dir |

**INSTRUMENT FINDINGS** (line numbers refer to `2026-09-23_idle_cuts_live_check.py`)
1. **`drain_disabled` cannot read True when the path is missing.** For an id absent from `paths.strs`, PROBE (line 98) returns `{present:false}` with no `disabled` key. For a path that does not resolve (the null break at line 97), it returns `{present:true}`, also with no key. Line 123 then gets None from `.get("disabled")`, and line 190 requires `is True`. The only way to read True is `node.props.disabled === true`.
   - Remaining gap: PROBE never checks `node.props.id === id`, so a path that resolved to the wrong node would be read without complaint. Not observed here.
   - A missing `window.store` makes PROBE return null (line 94), and line 122 then raises. That failure is loud, not a false pass.
2. **`drain_ticks_10s == 0` can come from a missing node.** Line 123 computes `(s1.n or 0) - (s0.n or 0)`, which is 0 if the drain is gone at the second probe or `n_intervals` is undefined. Line 190 does not check `present` at that probe; only the `drain_disabled is True` conjunct forces the node to exist at the first one.
   - In `…_rebuilt_ce78e0de.json` both X windows' raw `after_10s` record is `{present:true, n:0, disabled:true}`, so this hollow route did not occur. The raw record settles what the verdict code alone would not.
3. **`dead_present` means "key is in `paths.strs`", not "the node exists"** (line 98). If `paths.strs` were absent it falls back to `{}` (line 95), and that reads as "dead timer removed", which is exactly the X-side pass condition.
   - Within each X window this is covered: the drain has to resolve through the same `strs` map with `disabled:true`.
   - The C windows (same PROBE, parent build) are the positive control. The dead timer is present there and ticks 5-6 times per 10 s.
4. **The session write's `ok` can be true without the Store changing.** `SETPROPS` in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth/util/ad-hoc/e2e_f039_supersession_test.py` (lines 86-89) returns `ok:true` as soon as `memoizedProps.setProps(payload)` returns without throwing, on the first fiber with a matching id. Nothing reads the Store back.
   - The verdict (line 194) never uses `ok`. The Store change is inferred only from the drain flipping (lines 133-137, 145-149).
   - That inference is sound only because the gate is the sole writer of `…weight-drain.disabled`, with `replay-player-session.data` as its sole Input. M3's `test_one_writer_of_disabled_and_it_is_the_clientside_gate` establishes this.
   - A write that did not land leaves the drain disabled, which gives FAIL, not a false PASS.
5. **SESSION tick legs.**
   - `ticks_10s_enabled` (lines 139-141) cannot be inflated by a missing node; the result would be ≤ 0.
   - `ticks_10s_cleared == 0` (lines 151-153) passes without evidence if the node is missing at both reads. `session_path` stores only the differences, with no raw `n` or `present`, so `…_rebuilt_ce78e0de.json` cannot rule this out; it can only be argued improbable.
   - SESSION passed exactly at its threshold: `ticks_10s_enabled = 5` against `>= 5`. The first run had 6.
6. **Tick counts are store updates, not timer fires.** In the C windows the 500 ms drain registered 5-7 increments per 10 s and the 1000 ms dead timer 5-6, against nominal 20 and 10. The rule only needs > 0, so this is adequate. But the "ticked at 2 Hz" in `CHANGELOG.md` is the configured period, not what the idle page actually delivered.
7. **`git_sha` is a launch-time environment stamp.** `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth/util/ad-hoc/2026-09-04_canopy_verify_instance.bash` (lines 107-108) sets `JUNIPER_CANOPY_GIT_SHA` from `git -C "$SRC_DIR" rev-parse HEAD`. It has no dirty-tree check, and a caller can pre-set it. `serving_commit` in `e2e_w3_params_driver.py` (lines 96-126) reads it back from `/v1/health`. I corroborated it without connecting to the ports:
   - `ss -ltnpH` shows pid 3746650 on :8055 and pid 3754863 on :8056.
   - Their `/proc/<pid>/cwd` are `…/worktrees/juniper-canopy--control--main--20260923-1423--3a6dea95/src` (HEAD 3a6dea95) and `…/worktrees/juniper-canopy--perf--idle-dispatch-cuts-v2--20260923-1418--3a6dea95/src` (HEAD now 78c057e2, whose `src/` tree equals ce78e0de's).
   - `git status --porcelain -- src` is empty in both. No tracked `src/` file is newer than its process start.
   - The process starts (19:23:58Z and 19:24:07Z) match the `build_date` stamps.

**ANYTHING ELSE THAT LOOKS WRONG**
1. **"stop clears it" does not hold on the cascor-backed path.** This is from reading the code; I did not drive it live. The claim appears in `CHANGELOG.md` and in the new comment in `src/frontend/components/replay_player_panel.py` at ce78e0de.
   - `_merge_session` returns `dict(session)` updated with `data` whenever the control response is non-empty (`replay_player_panel.py:837-843`). The `stop → {"snapshot_id": None}` branch (849-852) is reached only when `data` is falsy.
   - `_invoke_replay_control` passes the whole `resp.json()` through (374), and canopy's route returns the adapter result (`src/main.py:3021-3027`).
   - cascor's stop returns `{"status": "stopped", "snapshot_id": <id>}` (`/home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/lifecycle/manager.py:5765`).
   - So after a real Stop the session keeps a truthy `snapshot_id`, and the gate keeps the drain running until the page reloads. That is the parent's behaviour, so it is not a regression.
   - The only stop test (`src/tests/unit/frontend/test_replay_player_panel.py:251-253`) passes `data=None`. The live SESSION leg cannot see this either, because it writes `{snapshot_id: null}` directly (script line 142).
   - The replay-start writer does set the key: `hdf5_snapshots_panel.py:1321`, `session.setdefault("snapshot_id", …)`.
2. **The 78c057e2 sentence pools two different build pairs.** The first live check (`2026-09-23_idle_cuts_live_check.json`) served 668380ec against 723ee812, not the PR's commits.
   - 723ee812 is not an ancestor of 3a6dea95. `git diff --shortstat 723ee812 3a6dea95 -- src/` gives 22 files, +2013/-302, including metrics_panel.py and dashboard_manager.py.
   - The only live check of the PR's code (`…_rebuilt_ce78e0de.json`) scored INCONSISTENT. "Three of four windows" is 2 of 2 on the other pair plus 1 of 2 on the PR pair.
   - "One window 2% slower than both neighbours": X2 is +1.48% against C2 and +2.66% against C3 (+2.1% against their mean).
   - "Load average of 8–13": NO ARTIFACT. The script records no load and neither JSON contains one.
3. **C1 is the outlier window.** It measured 7115.1 ms against 5336.9 and 5275.5 for C2 and C3. It started 40 s after the last write to `cuts_full_suite.log` (file time 19:30:05Z; C1 `read_at` 19:30:45Z).
   - The full suite ran inside the worktree the X leg was serving from, while it served. `src/tests/regression/test_x7_demo_mode_honesty.py` wrote demo snapshot records into that tree's ignored `src/snapshots/snapshot_history.jsonl` between 19:25:58Z and 19:29:48Z. This is likely harmless, since the launcher points the leg's snapshot dir elsewhere.
   - Without C1, X/C is 0.88 instead of 0.79. The INCONSISTENT verdict does not depend on C1.
4. **"VERDICT RULE -- FIXED BEFORE THE FIRST RUN" is UNTRACEABLE.** `2026-09-23_idle_cuts_live_check.py` and `2026-09-23_idle_cuts_live_check.json` entered git together in juniper-ml squash commit 51993b37 (2026-09-23T17:07:01Z). That is about 3.5 h after the first run's windows (13:34:45Z to 13:44:24Z). The JSON records only the script's filename, no hash. That the committed rule reproduces both stored verdict sets shows consistency, not ordering.
5. **`cuts_full_suite.log` has no commit stamp.** "At ce78e0de" rests on two things only: the 6810 count at ce78e0de (the parent lacks the 9 new tests, and 7 of them fail there), and the test side effects landing in the X worktree while its HEAD was ce78e0de (78c057e2 was committed at 19:43:28Z). The trailing `exit=0` comes from the wrapper, and which command's status it captured is not recorded.
6. **f4d864df's signature is not verified locally.** `%G?` shows `E`: a `gpgsig` header is present and the committer is GitHub, but the key is not in the local keyring. "GitHub-signed" is plausible but unverified here.

**Changed**: no repository files. All scratch output (the `x_ce78/` and `x_3a6d/` extracts, `m1_*.diff`, `m3_parent.log`, `m6_collect_ce78.txt`) is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneA_cuts.iVwNcF/`. No script files were created; all analysis was inline `python3 -c`.

---

## Lane B -- canopy#676 adversarial

*agent `aae8b0fd4ecd654a3` · round 1 · last-assistant-text (not resumed) · 10840 chars*

- **VERDICT: MERGE-WITH-FIXES**

- **FINDINGS**

  1. **MAJOR. Refutes claim 2's "stop clears `snapshot_id`", and with it claim 1's practical contract that the drain "runs only while a replay session exists".**
     - **Where the claim is made:** `src/frontend/components/replay_player_panel.py:566-567` @ce78e0de, and the CHANGELOG line "The snapshots panel writes the session on POST `/replay`, and stop clears it."
     - **The mechanism:** `_merge_session` checks `if data:` (lines 837-843) before its `stop` branch (lines 849-852). So stop clears the session only when the control response has no body.
     - **A successful stop always has a body:**
       - `_invoke_replay_control` returns `{"success": True, "data": resp.json()}` on a 200 (lines 373-374).
       - The proxy returns the adapter result unchanged (`src/main.py:3011-3028`).
       - That result is `CascorClient._post`'s full envelope (`src/backend/cascor_service_adapter.py:2379-2381`; installed `juniper_cascor_client/client.py:565` `return response.json()`).
       - Cascor's stop payload is `{"snapshot_id", "operation", "action", "result", "fsm_state"}` (juniper-cascor `origin/main:src/api/routes/snapshots.py:497`).
     - **Executed:** `/tmp/claude-1000/.../scratchpad/laneB_probe_stop.py` drives the registered `dispatch_control` with a mocked 200 carrying that envelope. Output:
       - `session after a successful Stop: {'snapshot_id': 'snap_1', 'fsm_state': 'REPLAYING', 'status': 'success'}`
       - `render_session` keeps the active view, badge `REPLAYING`
       - `gate(disabled) after Stop: false`
     - **Nothing else clears the session.** The `replay_stopped` broadcast (`main.py:3026`) has no frontend consumer (grep across src).
     - **The only stop test uses a shape the live route never produces:** `src/tests/unit/frontend/test_replay_player_panel.py:252` passes `_merge_session(session, "stop", {}, None)`.
     - **Effect:** after the first Stop in a page, the drain ticks at 2 Hz for the rest of that page's life. That is the parent's behaviour, so the cut quietly disappears for any page that has used replay. The player also stays active with a stale REPLAYING badge; that part predates this PR.
     - **Fix:**
       - Preferred: handle `stop` before `if data:` in `_merge_session`, and add a test using the real envelope, plus one asserting the gate disables after it.
       - Minimum: remove "stop clears it" from the comment and the CHANGELOG, say the drain stays on after a Stop, and file the stop defect.

  2. **MINOR. Refutes the stated data path behind claim 2** ("weights reach the JS ring buffer only while a replay session streams them"; test docstring lines 14-15). No such stream exists today.
     - **The only producer** is the `metrics` handler at `src/frontend/assets/ws_dash_bridge.js:228-232`.
     - **Where the browser's frames come from:** it connects only to canopy's `/ws/training` (`websocket_client.js:569`). That endpoint (`main.py:757`) sends only `initial_status`, `state` and pong. All `metrics` arrive through `websocket_manager.broadcast`.
     - **Canopy drops the key.** The service relay rebuilds every metrics payload from a fixed key set (`cascor_service_adapter.py:763-766` → `_to_dashboard_metric`, lines 1950-1973). Executed: the output keys are `['epoch','eval_metrics','metrics','network_topology','phase','timestamp']`, and `weights survives relay: False`.
     - **Cascor never sends it.** On cascor `origin/main` (f7a6d57), `_emit_frame` (`manager.py:1034-1071`) adds no `weights`. `git grep -c "weights_at("` returns 1, the definition at line 1018, so it has no caller. The g-3 commits the design record cites (d85c9ddd, dbc25277) are not in the local cascor object store.
     - **Demo mode has no replay** (501 from `_require_service_adapter`, `main.py:2960-2970`).
     - **So:** the drain has never had anything to drain. "Nothing a user sees changes" is true, but because nothing flows, not for the reason given.
     - **Latent risk if the stream is ever restored:**
       - The gate keys on this page's session, but `broadcast` goes to every connection (`websocket_manager.py:706`).
       - Other tabs, and a page reloaded mid-replay (the session Store is memory-scoped, line 120), would buffer weights and never drain them. Network Evolution (`network_evolution.py:164,185`) would then differ from the parent.
       - Entries that arrive after a session clears would be flushed into the *next* session when the gate enables. Decision Boundary would then render the previous session's `buffer[-1]` (`decision_boundary.py:243-247`).
     - **Fix:** say plainly in the comment, CHANGELOG and docstring that the stream is dead end to end, and file the CAN-015g defect (emitter never wired; relay strips `weights`). Alternatively remove the drain. If it stays, have the gate discard `_replayWeightBuffer` when it switches from disabled to enabled.

  3. **NIT. Dangling reference.** `replay_player_panel.py:140` names "`_weight_drain_gate` in `register_callbacks`", but `git grep` finds that name only in this comment. The gate is `WEIGHT_DRAIN_GATE_JS` (line 78), registered at lines 578-583. Fix: name the constant.

  4. **NIT. Refresh-rate promises in docs and config still point at settings nothing reads (brief item d).**
     - The stale entries:
       - `conf/app_config.yaml:170` `metrics_update_interval_ms: 1000`
       - `conf/app_config.yaml:181` `update_interval_ms: 1000  # Milliseconds between automatic updates`
       - `docs/USER_MANUAL.md:1344` "Performance Tuning … `update_interval_ms: 2000  # Slower updates (less CPU)`"
     - No source reads any of these keys (`git grep` over `src/`, excluding tests, is empty).
     - The init log at `metrics_panel.py:353` still reports `update_interval=…ms`.
     - This predates the PR, and the CHANGELOG's "two docs rows" wording is accurate. Fix: mark or delete the keys, and drop the value from the log line.

  5. **NIT. Limits of the class test (claim 5 is correctly scoped).**
     - The consumer check is purely structural, so it would not have caught the drain itself, the timer that actually cost the latency, because the drain has a consumer.
     - An Interval with a pattern-matching (dict) id would be counted as dead: `_consumers` compares a dict with the served string id (test file line 102). The `sorted()` at line 115 would then raise `TypeError` rather than report it. None exist today.
     - Fix: `sorted(..., key=str)`, and compare ids in their stringified form.

- **CLAIMS YOU TRIED AND COULD NOT REFUTE**
  - **Claim 1 and item (b).** Built-app probe (`scratchpad/laneB_probe_deps.py`, `DashboardManager({})`, `/_dash-dependencies`, 178 callbacks):
    - Exactly one writer of `replay-player-panel-weight-drain.disabled`: clientside, Input `replay-player-session.data`, no State, `prevent_initial_call` False.
    - The layout has `disabled=True` and `interval=500`.
    - The drain is not in `_GATED_POLL_INTERVALS` (`dashboard_manager.py:463-487`; probe returns `[]`).
    - Every `set_props` target in the assets and Python is a different store; none is the drain or the session.
  - **Claim 3.** Both session writers carry an `@hash` (`...data@ae21…` from the hdf5 confirm, `...data@3f2f…` from `dispatch_control`). In `dash_renderer.dev.js` (dash 4.2.0):
    - `splitIdAndProp` keeps `data@<hash>` as the property (lines 5895-5903, used at 6395), and `getOutputs`/`resolveDeps` pass it through unchanged (1742, 1768-1778).
    - The closure walk looks up `inputMap[id]["data@<hash>"]`, which never exists (1544-1553, 1617-1632).
    - `getReadyCallbacks` keys on `combineIdAndProp` (1539-1543, 1633-1664), so the gate's plain `replay-player-session.data` is never blocked.
    - The gate does fire after such writes: the server keys its response by `clean_property_name` (`dash/_callback.py:592`, `dash/_utils.py:307-308`).
  - **Claim 4.**
    - No exact reference to `metrics-panel-update-interval` in the built deps (probe `[]`), in the frozen tree outside the new test, or in the parent tree outside the regression snapshot.
    - `git log -G 'component_id\}-update-interval'` finds only b64f6dfa (the 2025-12-12 import), where the timer already had no Input.
    - The legacy prototype's `metrics_panel.py:241` also has no consumer.
    - `metrics-store-interval` drives `metrics-panel-metrics-store.data`, which matches REFERENCE.md. The "1 Hz REST rebuild" at `metrics_panel.py:1100` refers to that poll.
  - **Claim 2's consumer and start-path statements.**
    - Decision Boundary short-circuits without a session (`decision_boundary.py:243-244`).
    - The JS cap is 100 (`ws_dash_bridge.js:31,229-231`).
    - The snapshots panel is the only UI path that starts a replay, and it writes a truthy `snapshot_id` (`hdf5_snapshots_panel.py:1316-1325`; cascor's unified payload carries it).
    - Keying on `snapshot_id` rather than `playing` is correct: with a real body, play and pause never update `playing` (lines 837-843).
  - **Item (e).**
    - The walk finds all 17 Intervals (one per `dcc.Interval(` site in src), including those under `dbc.Tabs` → `dbc.Tab`. An independent walk that also descends dict props finds the same 17.
    - A dead Interval injected into the Replay tab is flagged (`['laneb-probe-dead-interval']`, `scratchpad/laneB_probe_mutation.py`).
    - The one runtime rebuild of the tab bar (`suppress_cascade_tabs`, `dashboard_manager.py:2735-2742`) reuses the same ids, and the gate re-fires on the rebuilt Store.
  - **Tests.**
    - The new test file passes on the extract (9 passed).
    - `test_panel_layout_snapshots.py` and `test_replay_player_panel.py` pass (43 passed).
    - CI runs `src/tests/unit/` on ubuntu and macOS runners (`ci.yml:235-237`), so the new file is selected, node test included.
  - **Scope.** PR head f4d864df equals ce78e0de plus a CHANGELOG change only (`git diff --stat`), and the juniper-ml evidence files it cites exist on `origin/main`.

- **WHAT YOU COULD NOT CHECK**
  - **The latency figures** (42% and 32%, and the head's live-check sentence). They need a live canopy, and the brief rules out starting one on this loaded host.
  - **The stop and gate behaviour in a real browser.** My evidence is the registered callbacks driven with a mocked HTTP layer, plus the renderer source.
  - **The "ticked on every tab" premise.** Whether dbc.Tabs 2.0.4 mounts inactive tab panes is taken from the author's A/B.
  - **The parent-commit test counts**, which were assigned to another lane.
  - **Whether g-3 exists on an unfetched remote cascor branch.** No network fetch was made.

  Nothing in any repo was modified. The probes are all in the session scratchpad: `laneB_probe_deps.py`, `laneB_probe_walk.py`, `laneB_probe_stop.py`, `laneB_probe_mutation.py`, `laneB_probe_exact.py`, and the extract `laneB_extract/`.

---

## Lane A -- F-055 fix 1 measurements

*agent `ab18f7cdbe70c81b2` · round 1 · last-assistant-text (not resumed) · 15239 chars*

| measurement | claimed | re-derived | verdict | evidence |
|---|---|---|---|---|
| M1a: fix side (884d22fb) | All tests in the four files pass. | 103 of 103 pass: f055 7, poll_gating 45, stage2 42, idle_dispatch_cuts 9. Nothing was skipped. Node v24.13.1 ran both `test_watchdog_behaviour_under_node` tests. | MATCH | I extracted with `git -C /home/pcalnon/Development/python/Juniper/juniper-canopy archive 884d22fb` into `$S/fix`, then ran `mkdir logs` and `conda run -n JuniperCanopy1 python -m pytest <4 files> -p no:cacheprovider -rA --junitxml=$S/fix_junit.xml`. `$S` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneA.UzPRF5`. |
| M1b: parent side (ce78e0de plus the 3 fix test files) | 19 of 94 fail and 75 pass, with the 19 named. The metrics-store TestStrandWatchdog, node test included, passes on both sides. | **19 failed and 75 passed.** By file: f055 5 failed / 2 passed, poll_gating 13 / 32, stage2 1 / 41. The failing set is exactly the claimed set: the 5 `TestStatusBarRidesItsOwnGuardedLane` tests, all 9 `TestStatusBarStrandWatchdog` tests, `test_registry_ids_all_exist_in_layout`, `test_exactly_one_writer_per_disabled_prop`, `test_gate_writes_every_registered_interval`, `test_source_registry_matches_the_spec` and `test_global_lane_shape_is_pinned`. Everything else passes: both `TestPremisesHoldOnBothSides` tests, `TestStrandWatchdog` 8 of 8 including the node test, and idle_dispatch_cuts 9 of 9. | MATCH | Blob hashes check out: copied test files 012dbf71, 47e15ee3, a4d5f6ab; parent `dashboard_manager.py` a30a225b, `canopy_constants.py` a0818f68. Imports resolve to the extract. Each failure message is the expected one, e.g. "status-bar-interval appears 0 times in the layout" and "fast lane drifted: [..., 'update_unified_status_bar']". Per-test results are in `$S/parent_junit.xml`. |
| M2(i): delete the `running=` line | Should be caught. | 1 fails: f055 `test_the_feeder_stops_its_own_clock_while_in_flight`. | CAUGHT | `$S/mut_i_junit.xml` |
| M2(ii): Input back to `fast-update-interval` | Should be caught. | 4 fail: f055 `test_the_feeder_rides_its_own_lane`, f055 `test_no_other_callback_takes_the_lane_as_an_input`, stage2 `test_global_lane_shape_is_pinned`, and idle `TestEveryIntervalHasAConsumer::test_every_interval_has_a_consumer`. | CAUGHT | `$S/mut_ii_junit.xml` |
| M2(iii): register as `(_STATUS_BAR_INTERVAL, "metrics")` | Should be caught. | 2 fail: f055 `test_the_lane_is_registered_as_a_global_lane` and poll_gating `test_source_registry_matches_the_spec`. | CAUGHT | `$S/mut_iii_junit.xml` |
| M2(iv): both watchdogs use `__metricsStoreDisabledSince` | Should be caught. | 9 fail (4 `TestStrandWatchdog`, 5 `TestStatusBarStrandWatchdog`), **all at `_js`**: "expected 1 inline script for 84a3df8f…, found 2". Both timeouts are 30000, so the two JS sources become byte-identical and Dash gives them one function name. With the collision removed (the same mutation plus `STATUS_BAR_STRAND_TIMEOUT_MS=30001`), exactly 1 test fails, `test_the_two_watchdogs_keep_separate_clocks`, with "the watchdogs share a clock". | CAUGHT, but incidentally | `$S/mut_iv_junit.xml`, `$S/mut_iv_b_run.txt` |
| M2(v): `<` changed to `<=` in the watchdog JS | Should be caught. | 2 fail: `test_watchdog_behaviour_under_node` for both lanes ("At index 3 diff: 'NU' != False"). No other test fails. | CAUGHT, only when node is present | `$S/mut_v_junit.xml` |
| M2(vi): delete the status-bar tuple from the watchdog loop | Should be caught. | 9 fail: `test_exactly_one_writer_per_disabled_prop` plus 8 `TestStatusBarStrandWatchdog` tests (all except the constant-only threshold test). | CAUGHT | `$S/mut_vi_junit.xml` |
| M3a: `2026-09-23_status_bar_apply_census_f055_parent_8056.json` | NEVER-APPLIES: 30 delivered, 31 watched, 0 executed, 0 latency changes. sha = parent. | `_baseline_verdict(30, 0, 0)` = NEVER-APPLIES. Recounting latency-display entries in `store_changes` gives 0. sha is ce78e0de. | MATCH | I pulled `_baseline_verdict` out of `2026-09-23_status_bar_apply_census.py` (lines 156-161) with AST and applied it to the raw fields. The rule code is unchanged against 51993b37 (the working-tree diff is docstring only). `$W` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth`. |
| M3b: `2026-09-23_status_bar_apply_census_f055_fix_8057.json` (60 s) | VOID: 7 delivered, 9 watched, 8 executed, 7 latency changes. | `_baseline_verdict(7, 8, 7)` = VOID, since 7 < 10. Recount gives 7. Latency-display changes come a mean 8.69 s apart. | MATCH | Same method. |
| M3c: `2026-09-23_status_bar_apply_census_f055_fix_8057_150s.json` | APPLIES, predicted 12-25 delivered. CHANGELOG says "20 delivered, 20 executed". | `_baseline_verdict(20, 20, 19)` = APPLIES (ratio 1.0). Recount gives 19. Mean change interval 8.04 s. DOM shows "Completed — early stopped" / "76", matching the server (epoch 76). | MATCH | Same method. The runs were one browser at a time, in order (read_at 19:50:26Z, 19:52:30Z, 19:55:09Z; the drive began 19:59:30Z). |
| M3d: `serving.git_sha` of each census leg | :8056 is the parent, :8057 is the fix. | ce78e0de, 884d22fb, 884d22fb. Confirmed on the live processes through /proc, read-only, without touching the ports:<br>- :8056 is pid 3754863, cwd `…/worktrees/juniper-canopy--perf--idle-dispatch-cuts-v2--20260923-1418--3a6dea95/src`, env `GIT_SHA=ce78e0de`, started 19:24:07Z (the commit is 19:22:07Z).<br>- :8057 is pid 4160757, cwd `…/worktrees/juniper-canopy--fix--f055-status-bar-running-guard--20260923-1425--ce78e0de/src`, env `GIT_SHA=884d22fb`, started 19:49:58Z (the commit is 19:49:27Z).<br>- Both worktrees are clean now. The source files that are served predate launch, apart from one comment-only file on the parent line (`replay_player_panel.py`).<br>- Both fix transcripts carry the same pid and build_date, so the leg did not restart between runs. | MATCH | `ss -ltnp`; `readlink /proc/<pid>/cwd`; SHA / BUILD_DATE / DEMO_MODE read from environ; `ps lstart`; `git status`; file mtimes. |
| M3e: the premises the fix commit cites | 36 of 36 delivered, 0 executed; wire p50 1.16 s (0.21-3.08); a 20 s period makes the bar apply. | Baseline 36/36/0 with median 1.16 s (min 0.212, max 3.075). Slowed window: `_slowed_verdict(7, 8, 6)` = APPLIES. | MATCH | `2026-09-23_status_bar_period_arm_8055.json`, `2026-09-23_status_bar_apply_census_8055.json` |
| M4a: fix leg :8058 | ALLOW LANDS at 13.0 s, DENY RETURNS at 7.8 s, BAR APPLIES. | The AST-extracted `_verdicts` reproduces the recorded verdicts exactly: 28 of 28 samples are live (running and flag on), the first `False` is at 13.0 s, the first deny-window `True` is at 7.8 s, and the bar reads "Running" at every running sample. | MATCH | `2026-09-23_f055_f025_allow_arm_demo_drive.json` against `2026-09-23_f055_f025_allow_arm_demo_drive.py` lines 125-148. |
| M4b: parent leg :8059 | LANDS at 19.7 s, RETURNS at 2.7 s, APPLIES. | Recomputed identically. The bar showed its layout default "Stopped" / "0" for the first 10 samples (0.1-18.5 s). | MATCH, but the drive **does not discriminate** fix from parent | Same files. |
| M4c: `serving.git_sha` of the drive legs | fix and parent | Fix is 884d22fb. **Parent is 78c057e2, not ce78e0de.** 78c057e2 is a child of ce78e0de that changes only CHANGELOG.md (`git diff --stat ce78e0de 78c057e2`). | MATCH for the fix; code-identical for the parent | Both demo legs are down now, so the sha is from the transcript only; no /proc check was possible. |
| M5a: census `executed_entries` | Required analysis | Can it read 0 when the bar applied? No. Can it read non-zero when nothing applied? Yes, but only for network-level failures. | ADEQUATE, one false-positive path | See INSTRUMENT FINDINGS 1-2. |
| M5b: drive `button_disabled` | Required analysis | Can it read False without the gate having applied? No. | ADEQUATE | See INSTRUMENT FINDINGS 4. |

INSTRUMENT FINDINGS

1. **How the census counts executed entries** (`2026-09-23_status_bar_apply_census.py`, citing dash-renderer 4.2.0 `dash_renderer.dev.js`, the same source as the served min bundle):
   - The census subscribes to `window.store` (census line 142; renderer 3798) after the renderer's own StoreObserver (358).
   - The StoreObserver's notify runs the observers synchronously (374-388). So by the time the census listener sees the add-to-executed dispatch, `removeExecutedCallbacks` (2627) has already run.
   - The census therefore sees an entry in `executed` only during nested dispatches, which Redux delivers to every listener (46377-46382). Those are:
     - `applyProps` dispatching `updateProps` (2475) inside `if (data !== undefined)` (2498). Every in-window 200 response with data is counted this way.
     - A synchronous `onError` dispatch (7248-7256).
   - No false zero:
     - An apply that happened before install is outside the window by design. The parent's `install.initial` already held the layout defaults ("Stopped", latency ""), so nothing had applied before install either.
     - `window.store` was live in all three runs: 3570, 4249 and 12206 store notifications.
     - I built both extracts. Exactly one callback's output contains `status-indicator.style`, and its output key is byte-identical on parent and fix; only the Inputs and `running` differ.
2. **Census false positives and rule coupling.**
   - Not counted: 204 responses (`resolve({})`, 978-981) and HTTP-error responses, because `handleAsyncError` dispatches those asynchronously (7237-7246).
   - Counted even though nothing applied: a network failure. `handleError` (987-998) produces `{error}` (1438-1449), and the `onError` dispatch for it is synchronous. It would show up as an executed entry with no wire response.
   - `executed` can therefore exceed `delivered`. The 60 s fix run has 8 against 7; that is a window edge or such a failure, and the record cannot tell which.
   - The APPLIES arm of `_baseline_verdict` (line 161) does not require any latency-display change. The 150 s APPLIES is corroborated separately by 19 changes, which is a lower bound because identical consecutive strings do not register (line 139).
   - The rule's `>= 10` delivered threshold with a 60 s window cannot score a lane that clocks itself at about 8 s. The 150 s re-run changed the window after a VOID. That change is disclosed, and the rule code did not change.
3. **`serving.git_sha` is a claim, not proof.** It is `git -C $SRC_DIR rev-parse HEAD` taken at launch, with no dirty-tree check (`2026-09-04_canopy_verify_instance.bash` lines 107-108). The /proc checks in M3d back it up for :8056 and :8057 only.
4. **The drive's `button_disabled` reading is sound** (`2026-09-23_f055_f025_allow_arm_demo_drive.py` line 88).
   - dbc 2.0.4 `Button` renders a real `<button>` unless an href is set (`_=u&&!l`, `as:_?_n:"button"`) and passes `disabled` through (`dash_bootstrap_components.min.js`).
   - Canopy's button has no href and ships `disabled=True` (`dashboard_manager.py` lines 1457-1466 at 884d22fb).
   - Its only writer is the feeder, which returns a bool or `no_update`, never None (6967-6969, 7285-7287).
   - No callback writes `children` of any ancestor (sidebar-col, then sidebar-meta-params-card, sidebar-nn-section, nn-subsection-collapse, sidebar-nn-spiral-dataset, ctx-spiral-dataset-collapse). No JS asset touches the button.
   - So a False reading means an applied feeder response. A missing element reads None, which cannot count as LANDS (line 127) but would count toward NEVER (130-131). No None values occurred.
5. **The drive's BAR rule is weak** (line 139): a single apply at mount satisfies it. The per-sample `step_text` is the stronger evidence: 10 changes from 13.0 s on the fix, 11 from 19.7 s on the parent. The drive records no latency (lines 114-122), so its conditional prediction for the parent cannot be judged from its own transcript.

ANYTHING ELSE THAT LOOKS WRONG

1. **The drive is not evidence for the fix.** Both legs reach LANDS, RETURNS and APPLIES. The canopy `CHANGELOG.md` at cf6fb1dc says the parent landed "because a demo page is fast enough for the old lane". Nothing in `2026-09-23_f055_f025_allow_arm_demo_drive.json` measures that, and the parent's bar sat at its defaults for the first 18.5 s. Two further points:
   - The legs ran under unequal load. The parent leg was training throughout the fix leg's drive (epoch 237 when its own drive began); the fix leg was stopped during the parent's drive.
   - The CHANGELOG's "13 s after page load" is measured from `t0`, which is set after `open_dashboard` and `ensure_no_modal` return (drive lines 165-171). It is a lower bound.
2. Mutation (iv) is caught only through the hash collision from equal timeouts. Mutation (v) is caught only by the `skipif(NODE is None)` node test, so on a host without node nothing catches it; I did not check whether CI has node. Mutation (iii) is not caught by `TestRunningGuardsNeverContendWithTheTabGate`, because that test takes its tab set from the test file's own spec rather than the source registry.
3. **The guard can defeat the Apply clamp** (by reading, not measured). `runningOff` is written unconditionally in `completeJob` (renderer 925-936; `sideUpdate` 746-805).
   - If Apply is clicked while a status-bar request is in flight, the clamp's `true` (gate line 2487) is overwritten with `false` when the request completes. The lane then keeps polling for the rest of the apply.
   - The comment at `dashboard_manager.py` line 476, "conflict only in the window … mid-fetch", understates this.
   - On the parent, the bar rode the clamped fast lane with no guard. No test pins guard against clamp.
   - The commit message's "the tab gate never writes it" is also wrong. The fused gate writes `status-bar-interval.disabled` on every tab change (lines 2487, 2493-2494), and `test_gate_writes_every_registered_interval` asserts that write.
4. **The watchdog's safety margin is thinner than stated** (by reading).
   - The watchdog samples only on the 5 s slow tick and fires after 7 consecutive disabled samples, even if they span several requests.
   - The 30 s margin is argued against the 3.08 s wire round trip (the comment on `STATUS_BAR_STRAND_TIMEOUT_MS` in `canopy_constants.py`). But the guard holds the lane until the page processes the response. `2026-09-23_idle_cuts_live_check_rebuilt_ce78e0de.json` puts the p50 of that at 7115 ms and 3913 ms.
   - A release while a request is genuinely in flight, costing one evicted response, is therefore possible. It was not observed: the 150 s census shows 20 watched and 20 executed.
5. **Stale ports in the drive's docstring.** `2026-09-23_f055_f025_allow_arm_demo_drive.py` names :8057 and :8058, but the run used :8058 for the fix and :8059 for the parent. :8057 is the non-demo census leg (`DEMO_MODE=0` in its environ).
6. **Minor wording.** The docstring of `2026-09-23_status_bar_apply_census.py` says "the DOM at both ends". The starting value is the Redux store's `install.initial`, not DOM text.
7. No repository file was created or modified. All scratch work is under `$S`. `git status` in the two canopy worktrees may have refreshed their index stat cache; no tracked content was touched.

---

## Lane B -- F-055 fix 1 adversarial

*agent `a5a8c9722c7f1b4bf` · round 1 · last-assistant-text (not resumed) · 13401 chars*

VERDICT: DO-NOT-MERGE

The fix does what it claims when nothing touches the lane. But three ordinary things re-enable the lane while a request is in flight: a tab switch, the end of an Apply, and the fix's own strand watchdog. After any of them the bar goes back to F-055's symptom (responses delivered, none applied), often for minutes. Canopy was not run (forbidden); the evidence is the frozen code, the dash 4.2.0 renderer source, and a synthetic Dash app that copies the fix's wiring.

Where things are:
- `$S` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneB_f055.Iywb95` holds every script and result below.
- The canopy repo was only read (`git archive`/`show`/`diff`); nothing was edited or committed.
- Renderer line numbers are in `dash/dash-renderer/build/dash_renderer.dev.js` in the JuniperCanopy1 env.
- The repro is `$S/repro_f055.py`: headless Chromium on 127.0.0.1:18655. It has a 1 s lane, a server feeder with the same `running=` guard, the gate's exact expression for a global lane, and optionally the status-bar watchdog JS copied verbatim from the built fix app. Applies are recorded from the page itself, not from the Dash callback queue.

FINDINGS

1. **BLOCKER — the guard can be defeated, and one defeat keeps repeating (refutes claims 1 and 2).**
   - **Refuted text:** "the next tick cannot evict the response" (`dashboard_manager.py:1962-1964`). "It cannot contend with the tab gate, because this lane is never tab-gated" (`:4064-4065`, `:478-481`, `CHANGELOG.md:179`).
   - **The gate writes this lane on every fire.** It returns `clamped || (tab !== null && tab !== activeTab)` for every lane (`:2481-2496`), which is `false` for this lane whenever no Apply is running. In the built app, callback #91 writes `status-bar-interval.disabled`.
   - **The gate fires often:**
     - at mount (`prevent_initial_call=False`, `:2496`);
     - on every `active_tab` write: a user click, the CAN-016a restore (`:4290-4317`), the tutorial trigger (`:4266`), `hdf5_snapshots_panel.py:1270`;
     - on every `apply-in-flight` write (`:4189-4213`, `:5661`, `:9148`).
   - **Why one write evicts.** Re-enabling the Interval starts a fresh timer, so it ticks one second later (dcc `Interval.react.js` `handleTimer`). If the request is still in flight, that tick re-requests the feeder, the renderer evicts the in-flight one (`:3027`), and its response is dropped (`:2697-2704`).
   - **Why it repeats.** The evicted request is not aborted. When it finishes, `completeJob()` still re-enables the lane (`:925-937`, called at `:970`/`:979`/`:983`; there is no check that the request is still current). That re-enables the lane under its successor, and the cycle continues. The fix's own tests name this hazard at `test_poll_gating.py:438-440` ("an evicted request releasing the guard mid-flight").
   - **Repro results:**

     | Setup | Latency per request (R) | Result |
     |---|---|---|
     | Guard only, no gate (control) | 3 s | 7 of 7 applied, one request every R + 1.0 s |
     | Gate included, with its mount call | 3 s | 0 of 51 applied from page load; each later gate fire added another interleaved request chain |
     | Gate without its mount call | 7-8 s (matches the ~8 s live cycle) | 4 of 4 applied, then **one tab click 3.0 s into a request → 0 of 28 applied over ~120 s** |

   - **How long it lasts** (`$S/cascade_sim.py`, 2000 perturbations per row):

     | Dispatch-to-completion time r | Median time to next applied response | Over 60 s |
     |---|---|---|
     | 6.9-7.6 s (the reported live band) | 352 s | 74% (54% over 5 min) |
     | 5-9 s | 22.5 s | 18% |
     | 1.5-3.1 s | 2.9 s | 0% |

     The longer the round trip, the worse the fix does, and the live measurement puts it at the bad end.
   - **Fix:** stop using the Interval's `disabled` prop as the guard.
     - Pace the feeder with a handshake: a clientside pacer on the 1 s lane issues a new request token only after the feeder's own ack output (echoing the token) has applied, or after a stale-timeout. Then drop `running=` and the watchdog for this lane.
     - If the guard is kept, at minimum the gate must return `no_update` for global lanes unless the Apply clamp itself changed (use `callback_context.triggered_id`), including on its mount call. The Apply-release path stays exposed and would have to be accepted explicitly.
     - Add a real-renderer test in the style of `repro_f055.py`: switch tab mid-flight and assert the next response applies within N seconds.

2. **BLOCKER at the reported live cadence (MAJOR if live latency jitter is wide) — the watchdog fires on lanes that never stranded (refutes claim 3).**
   - **Refuted text:** `canopy_constants.py:446-449`, that 30 s is safely above any round trip, so the watchdog won't re-enable mid-flight.
   - **Why it misfires.** The watchdog samples every 5 s (`dashboard_manager.py:2559`, `SLOW_UPDATE_INTERVAL_MS=5000`). It resets only when a sample happens to see the lane enabled (`:2541-2545`). A healthy lane is enabled for only about 1 s per cycle, shorter than the 5 s sampling gap, so seven disabled samples in a row are routine. It then writes `false` mid-flight, which is Finding 1's trigger.
   - **Repro, watchdog only, no user action.** In these runs no request ever failed, so every watchdog write was a false fire.
     - R = 3-5 s, 240 s: 5 fires (at 57.83, 92.83, 152.83, 187.83 and 232.83 s), each with a request in flight and none longer than 5 s. Three of them caused evictions: 17 of 56 responses dropped.
     - R = 7-8 s: 13 of 13 applied, then a mid-flight re-enable at about 118 s and 0 of 21 applied afterwards.
     - A second R = 7-8 s run had no fire in 200 s (23 of 23 applied). The fires are random, not constant.
   - **Rate model** (`$S/watchdog_alias_sim.js`, the verbatim JS): at r = 6.9-7.6 s, 37-44 false fires per hour, 29-33 of them evicting. It stays at 15-35 per hour even if the enabled window stretches to 4 s.
   - **No-interaction model** (`$S/no_interaction_sim.js`): at r ≈ 7 s, the bar's last applied response is over 20 s old for 91% of wall time with tight jitter, and 11-26% with wide jitter.
   - **Pre-existing on the other lane.** The parent's metrics-store watchdog has the same predicate; this commit extends it to the status bar.
   - **Fix:** detect a strand by lack of progress, not by sampled state. Add `State(lane, 'n_intervals')`, reset the clock whenever it changes, and fire only when the lane is disabled AND `n_intervals` hasn't moved for the full timeout. Add a node test with a healthy periodic lane (r = 7 s, 1 s enabled, 5 s samples) that expects zero fires. The handshake in Finding 1 makes the watchdog unnecessary.

3. **MAJOR — the Apply clamp does not silence this lane (refutes "the CAN-000 apply clamp silences it", `dashboard_manager.py:478-479`, `CHANGELOG.md:178`).**
   - If a request is in flight when Apply is clicked (about 88% of the time at the live cadence), its completion re-enables the lane under the clamp. The status bar then keeps polling through the Apply.
   - Repro: Apply was clicked at 37.233 s. Request 6 was then dispatched at 44.504 s while the clamp was still armed. The release at 48.255 s landed mid-flight, and 0 of 24 responses applied afterwards.
   - **Fix:** the handshake covers it. Failing that, read `apply-in-flight` as State in the feeder and return `no_update` while it's armed.

4. **MAJOR — the tests pass (104 of 104) on code that fails when run in a browser.**
   - `test_poll_gating.py:406-408` exempts global lanes because they supposedly share `disabled` "with the apply clamp alone". That's false: the gate also takes `active_tab` as an Input (`:2494`), so every tab switch writes the lane.
   - The node test's sequence (`:336-349`) never presents a healthy lane whose enabled windows fall between samples. The threshold test (`:315-321`) cannot catch false fires.
   - `test_f055_status_bar_own_lane.py:32-33` leaves "does a response apply in a browser" to the census. The census bullet in the CHANGELOG is still a placeholder (Finding 6).
   - The tests are not vacuous for the subtle reverts the brief named; mutation runs catch all three. `running=` on the wrong prop: 1 failure. Lane registered with a tab: 2 failures. Both watchdogs on one clock: 9 failures. Against the parent, 19 of 94 fail, matching the CHANGELOG.
   - Gap: nothing forbids another callback from writing `status-bar-interval.n_intervals`, which would also re-request the feeder mid-flight. The EXCLUSIVE check (`test_f055:114-119`) looks at Inputs only.
   - **Fix:** add the real-renderer tests (tab switch mid-flight, an Apply spanning a request, 10 minutes idle with the watchdog), the healthy-lane watchdog test, and a check that nothing writes the lane's `n_intervals`. Rewrite `:406-408`.

5. **MINOR — "this is not a slowdown" (`canopy_constants.py:427-428`) is false.** Re-enabling restarts a full one-second timer, so the cycle is (dispatch to completion) + at least 1 s. The control run shows exactly R + 1.0 s; the live leg was 7.9-8.6 s. The Live Switch enabling and flag flips now land up to one cycle late. Fix: describe the 1 s as a floor and state the measured cadence.

6. **NIT — `CHANGELOG.md:192` ships a literal `- <<FILL-LIVE>>` placeholder.** Fill it with the live result or remove it.

7. **NIT — the comment's list of outcomes that restore the lane is incomplete (`dashboard_manager.py:2503-2505`).** A 200 response whose body fails to parse also skips `completeJob`: `res.json().then` at `:939` has no rejection handler. That strands the guard and leaves the request holding a renderer slot until the watchdog recovers it. The watchdog does bound it, so only the comment needs amending.

CLAIMS I TRIED AND COULD NOT REFUTE
- **Claim 4 (nothing else rides the lane).** In the built app (`$S/dump_callbacks.py`), only #85, the feeder, takes `status-bar-interval.n_intervals` as an Input, and it is that callback's only Input. The lane's only other writers are #91 and #93, both on `disabled`; nothing writes `n_intervals`.
- **The mount call can't evict by itself.** `running` is applied when the request is dispatched (`:818-821`, via `:1330`). A tick that arrives before dispatch just merges with the pending request (`:2987-3010`). The gate's mount write is the hazard, per Finding 1.
- **No page re-render re-requests the feeder.** None of its 11 output components, nor the lane, sits under any of the 142 containers that callbacks re-render (`$S/rerender_check.py`).
- **Re-enabling doesn't tick immediately.** The first tick comes one period later.
- **Other outcomes still restore the lane.** Prevented (204) and non-OK responses still run `completeJob` (`:979`, `:983`). Only network failures don't (`:987-998`). The feeder never raises PreventUpdate and catches every exception (`:7274-7303`).
- **The lane can't be left disabled forever.** Every writer of `true` has a bounded release: the Apply release (`:5661`), the E-3 watchdog (`:4218-4233`, on an interval the gate never touches), `completeJob`, and the strand watchdog (the slow lane it rides has no guard). The gate and watchdog agree on `Boolean(...)` of `apply-in-flight`, which only ever holds `{in_flight, since}` or `false`.
- **(c) The watchdog refactor is equivalent.** Whitespace-normalized, the metrics-store JS is identical to the parent's, and the status-bar JS differs only in the clock name (`$S/compare_watchdog_js.py`). The two function names are distinct (84a3df8f… vs ebbc2e81…). The two output ids share the same Inputs-only hash (`dash/_utils.py:151-163`) but name different components, so they don't collide. The node test's expected sequence matches the parent's behaviour.
- **(d) Starvation and budget are unchanged.** The poller budget counts the feeder as one global poller before and after, and `test_poller_budget.py` passes. The feeder holds at most one renderer slot. The fast lane's remaining consumers read no feeder output.
- **(e) Nothing depends on a 1 Hz cadence.** `training-status-store` has no Input consumer anywhere in `src`, and the feeder is the only writer of the Live Switch gate.
- **Canopy uses the HTTP transport** (`dash.Dash(...)` at `:621-628` has no websocket option), the same path as the repro.
- **CI runs the node test.** GitHub-hosted runners with no container, and a negative marker selector (`.github/workflows/ci.yml:114-129`, `:235-237`).

WHAT I COULD NOT CHECK
- **Canopy's own mount order.** The feeder can dispatch immediately (`:1664` checks only Inputs), while the gate waits behind the CAN-016a restore chain. Whether the gate's first write lands mid-flight on canopy is unverified; in the synthetic app it does.
- **The r ≈ 7 s figure is your live claim, not my measurement,** and Findings 1-2 scale with it and with its jitter. The repro produces r with server latency, whereas on canopy it is mostly main-thread delay. F-055 itself shows that ordering still evicts.
- **Real watchdog sampling jitter** under canopy's 12-slot pressure is modelled, not measured.
- **The census transcripts,** which I did not read, to stay independent. I can't say whether that window included a tab switch, an Apply or a watchdog fire.
- **Suggested live check:** a census on a live leg with a tab switch and an Apply mid-flight, plus at least 10 minutes idle, counting applied against delivered responses.

---
