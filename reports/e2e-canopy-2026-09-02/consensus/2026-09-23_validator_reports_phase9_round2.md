<!-- markdownlint-disable -->

# Phase 9 consensus, round 2 -- canopy#676 corrections (Lane B2)

Verbatim final report of the round-2 lane (a fresh agent, briefed only on the round-1 corrections; the script's round-1 slot is that agent's first and only report), 2026-09-23. Ledger: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9.

## Lane B2 -- canopy#676 round 2

*agent `a47f080dd2d65e271` · round 1 · last-assistant-text (not resumed) · 11301 chars*

**VERDICT: MERGE-WITH-FIXES.** The corrections change no behaviour, the tests still pass, and the body of each corrected claim holds up. What fails is the record: one MAJOR and six MINOR findings, all about text.

Two things moved during the review, and the findings account for both:
- **PR body:** it was rewritten at 20:09:51Z (GraphQL `userContentEdits`), after my first read. Everything below is against the current body (9,784 chars). That rewrite already fixed "stop clears it", the Network Evolution clause, the "three of four" pooling, "single commit" and "`src/` tree is `ce78e0de`'s".
- **cascor `origin/main`:** another session fetched it from `f7a6d57` to `0e016a7` (#678) at 20:22:52Z. The replay code is unchanged, so every conclusion holds at both heads. Line numbers below are for `0e016a7`.

**FINDINGS**

1. **MAJOR — the ledger records these claims cite do not exist.**
   - Attacked: `replay_player_panel.py:573` "both recorded in that ledger (Phase 9)"; canopy `CHANGELOG.md:156` "recorded in the juniper-ml E2E ledger"; PR body "so it is recorded in the ledger instead" and "(… are recorded in the ledger)".
   - Evidence:
     - `git log --all -S "## Phase 9" -- notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` returns nothing.
     - A grep for `^## Phase 9` across the main checkout and every `.claude/worktrees/*` and `worktrees/juniper-ml--*` copy exits 1.
     - The ledger's last heading is `:7865` (Phase 8). Its live-check bullet (`:8344-8351`) records only run 1 (`668380ec`, X/C 0.76).
     - Run 2's numbers, now in `CHANGELOG.md:147-148`, exist only in `2026-09-23_idle_cuts_live_check_rebuilt_ce78e0de.json`, which is untracked (`??`).
     - The ledger on `origin/main` has no match for `_merge_session`, `echoes the id` or `weights_at`, and nothing on the config-key NIT (`app_config.yaml` / `USER_MANUAL`).
   - Fix: land juniper-ml Phase 9 and commit the run-2 transcript before canopy#676 merges. Otherwise reword the three sentences into the future tense and drop "(Phase 9)".
   - Changes an action (merge sequencing) and a disposition: the Stop defect is left unfixed on the strength of a record that doesn't exist.

2. **MINOR — "runs only while a replay session exists" survives next to the corrected Stop limit.**
   - Attacked: the PR title (canopy uses `squash_merge_commit_title=COMMIT_OR_PR_TITLE`, so this becomes the commit title on `main`), `CHANGELOG.md:150`, `replay_player_panel.py:566`, `test_idle_dispatch_cuts.py:17`, and the PR-body table row. That row also says "fills only while a replay session streams weights", which contradicts the body's own "The drain has never had anything to drain".
   - Evidence:
     - The built app has exactly two writers of `replay-player-session.data`: the snapshots confirm click and the control dispatch (probe).
     - The confirm click always sets a truthy id (`hdf5_snapshots_panel.py:1321`). `_merge_session` returns `{"snapshot_id": None}` only for an empty body (`:847-861`).
     - So against cascor the gate opens once per page and closes only on reload, even after cascor's session has ended.
     - The live check's "disabled in 1.8 s / 2.5 s" came from a synthetic `setProps` clear (`idle_cuts_live_check.py:142`). No production writer ever does that against cascor.
   - Fix: say "runs once this page has started a replay (against cascor, until reload)" in all five places.
   - Changes an action (wording, including the title).

3. **MINOR — older comments now contradict the corrections.**
   - `replay_player_panel.py:116-117` still says the Store is "cleared on stop".
   - `:34-35` says "WebSocket events … update the Store". No such writer exists (probe above).
   - `:537-542`, the drain's own comment, says the steady-state cost "is dominated by JSON serialization of one or two recent weight events". That contradicts `:568` and `:577`.
   - `ws_dash_bridge.js:25-26` and `:218-220` say weights are "set by g-3's `_ReplaySession._emit_frame`". cascor's `_emit_frame` (`manager.py:1214-1223`) sets none.
   - Fix: correct them in the same commit. Changes an action.

4. **MINOR — the Stop mechanism is misattributed.**
   - Attacked: "and cascor's stop echoes the id" (`CHANGELOG.md:154`, `:575`, PR body, the `2fa134f8` message).
   - Evidence:
     - The panel receives cascor's whole envelope: canopy's route (`main.py:3021,3027`), the adapter (`:2379`) and the client's `response.json()` pass it through unchanged.
     - The echo sits at `data.snapshot_id` and `data.result.snapshot_id` (`routes/snapshots.py:497,501`), which `_merge_session` never reads. It copies the old session and overlays any non-empty body (`:846-851`).
     - Probe on the PR head: with the echo, `'snap_A'`; with the echo removed, `'snap_A'`; with an empty body, `None`.
   - Fix: "…only when the stop response is empty, and the proxied cascor envelope never is." The recorded fix direction should be "clear on a successful stop".
   - Changes an action (the fix direction).

5. **MINOR — a squash merge puts the refuted text from commit 1 on `main`.**
   - Evidence:
     - `gh api repos/pcalnon/juniper-canopy` shows `squash_merge_commit_message=COMMIT_MESSAGES`, and canopy#670's squash body (`48074653`) is its commit messages.
     - `f4d864df`'s message still says "fills only while a replay session streams weights".
     - It also says "three of four … across two live checks" (the pooling), "load average 8-13" (no artifact), and has the subject "ticked at 2 Hz".
   - Fix: collapse to one signed commit carrying the corrected message. The PR is a draft with no auto-merge armed, so this is cheap now.
   - Changes an action (merge procedure).

6. **MINOR — both X/C figures in the CHANGELOG include the outlier window C1.**
   - Attacked: `CHANGELOG.md:148-149` "(X/C 0.79) on a loaded host … (X/C 0.76)".
   - Evidence (probe over both transcripts):
     - C1 is the slowest window in both runs (7115.1 and 6335.5 ms).
     - Without C1, X/C is 0.8790 (run 2) and 0.8042 (run 1).
     - Run 1's C1 began 27 s after its leg's `JUNIPER_CANOPY_BUILD_DATE` stamp.
     - The PR body calls C1 an outlier and quotes 0.88, but the CHANGELOG, which ships, quotes 0.79 alone.
     - The transcripts have no load field at all, so "on a loaded host" has no artifact behind it.
   - Fix: drop X/C from the CHANGELOG, or give both figures. Drop "loaded host" unless a load record is committed.
   - Changes numbers.

7. **MINOR (latent) — after the `key=str` fix, the CLASS test misreports pattern-matching Intervals as dead.**
   - Attacked: `test_idle_dispatch_cuts.py:116` "a pattern-matching (dict) id must be reported".
   - Evidence:
     - `_consumers` (`:102-103`) compares the layout's dict id against `_dash-dependencies`, where Dash stores the id as a JSON string.
     - Probe: an Interval consumed by exact id `'{"index":7,"type":"tick"}'` is reported dead. Wildcard-consumed Intervals are also reported dead.
     - Before the fix this case crashed with `'<' not supported between 'dict' and 'dict'`. Now it confidently says a live timer ticks for nothing.
     - It is latent: all 17 of today's Intervals have string ids.
   - Fix: compare against `json.dumps(id, sort_keys=True, separators=(",", ":"))` and handle wildcards, or fail with an honest "unsupported" message.
   - Changes an action (test code).

8. **NIT — the forward-looking comment at `:578-581`.** The mechanism holds.
   - "Another tab buffers weights it never drains" contradicts the next clause: that page drains them when it opens its own session.
   - "Another tab" there means another browser page, while "every tab" at `:567` means a dashboard tab.
   - It omits the consumers a user would see. Network Evolution renders the buffer with no session check (`network_evolution.py:164-168`). At session open, Decision Boundary would render `buffer[-1]`, possibly another page's session, against this page's dataset (`decision_boundary.py:242-247`).
   - The carry-over between sessions is partly pre-existing: the drain is the store's only writer and nothing ever clears the store (probe).
   - Changes wording only.

9. **NIT — "`weights_at` has no caller"** (`CHANGELOG.md:140-141`, PR body). It has two test callers (`test_replay_weight_cache.py:275,284`). Say "no production caller", and cite `_emit_frame` as the direct evidence. Changes wording only.

10. **NIT — "answered a third slower than it had to"** (`CHANGELOG.md:136`) against the test docstring's "cost … a third of its response latency" (`:2`). These are different quantities (a 25% cut against a 33% cut). The A/B cuts of −41.9% and −32.3% mean the page was 72% and 48% slower. Changes the headline number.

**CORRECTIONS I TRIED AND COULD NOT REFUTE**
- **No replay weight reaches the page.**
  - cascor's `_emit_frame` sends no weights (`:1214-1223`).
  - canopy's relay rebuilds `metrics` payloads without the key (`cascor_service_adapter.py:763-766`, `:1867`, `:1942`).
  - The bridge buffers weights only from `metrics` frames (`ws_dash_bridge.js:217-237`).
  - Demo mode has no replay (`main.py:2968`) and sends no `weights`.
  - This holds whichever cascor is deployed.
- **The Stop behaviour.** `_merge_session` clears only on an empty body, and cascor's stop echoes the id (`manager.py:6085`). The session Store is memory-scoped (`:120`) with two writers, so "until the page reloads" and "keeps its session view" both hold.
- **The broadcast and the buffer.** The broadcast reaches every connection when no channel is given (`websocket_manager.py:706-712`). The bridge caps at 100 entries, dropping the oldest (`:229-232`). The drain has no session filter (`:545-557`). Decision Boundary ignores the buffer without a session (`:243`).
- **All the numbers reproduce:** +1.48% / +2.66% (the "1.5–2.7%"), 0.7893, 0.7602, 0.8790, X1 at −45.01% / −26.69% (beat both), INCONSISTENT under the rule, the A/B's −41.9% / −32.3%, and about 0.6 Hz delivered.
- **Provenance.** "The same change" holds: the `src`+`docs` diffs match outside hunk headers and the regenerated snapshot. `f4d864df` is `ce78e0de` plus three CHANGELOG sentences. Both commits are GitHub-verified.
- **`WEIGHT_DRAIN_GATE_JS`** exists (`:78`) and is registered (`:587-592`).
- **(d) `key=str` changes nothing today.**
  - All 17 Interval ids are strings, `sorted == sorted(key=str)`, and none is dead.
  - At the PR head, 9 of 9 tests pass.
  - At the parent `3a6dea95` with the head's test file, 7 fail and 2 pass (the premise pins). CLASS names exactly `['metrics-panel-update-interval']`.
- **(e) The CHANGELOG renders correctly.** markdown-it (CommonMark) renders `CHANGELOG.md:136-172` as one top-level item with six sub-items, directly before `:173` "The replay controls never applied".

**WHAT I COULD NOT CHECK**
- The host-load readings (7.89 / 13.10) and "C1 started 40 s after the test suite": no artifact exists for either.
- The running cascor on `:8202` and any live browser behaviour: off-limits. The weights claims are verified from source only.
- CI on `2fa134f8`: 15 pass, 4 pending, 5 skipping. The PR is a draft and behind `main`.
- An uncommitted Phase 9 anywhere other than the on-disk ledger copies.

**Changed:** nothing in any repo. My probes and extracts are in the session scratchpad (`laneB2_head.YGoT0Z/`, `laneB2_parent.neABH1/`).

---
