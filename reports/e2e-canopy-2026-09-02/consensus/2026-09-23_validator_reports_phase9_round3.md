<!-- markdownlint-disable -->

# Phase 9 consensus, round 3 -- canopy#676 round-2 corrections (Lane B3)

Verbatim final report of the round-3 lane (a fresh agent, briefed only on the round-2 corrections; the script's round-1 slot is that agent's first and only report), 2026-09-23. Ledger: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9. Brief: reports/e2e-canopy-2026-09-02/drafts/laneB3_cuts_brief.md.

## Lane B3 -- canopy#676 round 3

*agent `a43a64bd6e6752f9c` · round 1 · last-assistant-text (not resumed) · 9886 chars*

**VERDICT: MERGE-WITH-FIXES.** Only text needs fixing: the squash commit message and the PR description. The round-2 corrections broke no code, test or behaviour. The code diff is comments and the docstring plus the one intended test assertion, and every corrected mechanism sentence re-derives from source.

All canopy paths are at `4b4cfb16` (tree `cbe19d67`, the same as `040dc5c1`). Cascor paths are at local `origin/main` `0e016a7c`, not fetched. "The ledger" is juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `origin/main` `8d187b5f`. "§4" is §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

## FINDINGS

**1. MINOR: the squash body's "(two rounds; prose corrections only)" is false on both counts.**
- Both rounds changed test code:
  - Round 1: `8990f65c:…/test_idle_dispatch_cuts.py:115` has a plain `sorted(...)`, which became `sorted(..., key=str)` at `c360fb53:…:117`.
  - Round 2: it added the dict-id assertion at `test_idle_dispatch_cuts.py:120-121`.
- This is round 3. The in-flight ledger commit `800c20bb` is titled "…cuts rebuilt and reviewed (3 rounds)…", so main's history and the ledger will disagree.
- **Fix:** reword to "three rounds; prose corrections plus two test-only changes", or drop the parenthetical. That needs a new signed commit with the same tree.
- **Changes a number:** yes, but only the round count in the squash body. **Action:** yes, a reword before merge. **Disposition:** no.

**2. MINOR: the PR description still carries the text rounds 1 and 2 corrected.** The repo squashes with `COMMIT_MESSAGES`/`COMMIT_OR_PR_TITLE`, no auto-merge is armed and the PR is a draft, so the body does not land on main. Still wrong:
- "answered a third slower than it had to" (item 10).
- The table says "runs only while a replay session exists" (item 2).
- "cascor's stop echoes the id" (item 4). Cascor does echo the id, but only inside `data` (`snapshots.py:497`). The overlay at `replay_player_panel.py:851-856` applies the envelope's top level `{status, data, meta}` (`common.py:60-73`, `:123`), which has no `snapshot_id`, so the id survives either way. The same bullet also gives no F-CANOPY-056 ID.
- "`weights_at` has no caller on cascor `main`" (item 9). Tests call it at `test_replay_weight_cache.py:275` and `:284`.
- "this PR's parent, `main` `3a6dea95`" is now `0254a7ec`. I re-ran the count there and 7 of 9 still hold.
- "CI's path scope" omits `src/tests/contract/` and `src/tests/performance/` (`ci.yml:235-237`), and the 6806 count predates the rebase and both correction rounds.
- "all seven files": the PR now touches eight, because round 2 added `ws_dash_bridge.js`.
- "the third cut the census listed": the census named two (`…E2E-VALIDATION-EVIDENCE.md:8318`). The third was on the ledger's list (`:7842-7845`), and `CHANGELOG.md:176` correctly says "ledger".
- Provenance still describes two commits (`f4d864df`/`2fa134f8`) and "No behaviour changes". There is now one commit, `4b4cfb16`, GitHub-verified with reason `valid`.
- "Round 2 … running at the time of writing" is stale.
- It keeps the X/C figures (0.76/0.79/0.88) and the host-load prose that round 2 dropped from the CHANGELOG. The arithmetic is correct (I recomputed it from the transcripts), so keep or drop them deliberately.
- **Changes a number:** yes, in the body only (7→8 files, parent SHA, 2→1 commits). **Action:** yes, refresh the body, which the brief anticipates. **Disposition:** no.

**3. NIT: the round-2 sweep ("everywhere") missed survivors in PR-touched files.**
- `replay_player_panel.py:75`: "disabled unless a replay session exists" (a definition clause follows).
- `test_idle_dispatch_cuts.py:138`: the assertion message says "enables it while a replay session exists".
- `test_idle_dispatch_cuts.py:193`: the test name `test_disabled_unless_a_session_exists`.
- `ws_dash_bridge.js:113-115`: "extracted from a replay `epoch_end` event (see g-3 emitter)". This contradicts the squash body's "comments that claimed cascor emits weights … are corrected".
- `ws_dash_bridge.js:28`: the inserted sentence leaves "Each carries…" with no antecedent.
- **Fix:** reword. **Changes a number/disposition/action:** no.

**4. NIT: two loose claims in the squash body.**
- "A live check of this build against its parent": the pair checked was `ce78e0de` against `3a6dea95` (the transcript's `serving.git_sha`). The PR's runtime files are identical to `4b4cfb16` except the docstring and comments. The parents differ only by #674's `dashboard_manager.py`; #677 on current main is comment-only. The claim holds in substance, so name the SHAs.
- "Two timers were half of the page's steady-state ticks": the census gives 3.0 of 6.6, which is 45% (`…_interval_census_c0530279.json`).
- **Changes a number/disposition/action:** no.

**5. NIT (process): F-CANOPY-056/057 are reserved only in the unpushed local commit `800c20bb`.**
- `git branch -r --contains 800c20bb` is empty. Juniper-ml main has only 054 and 055, no open juniper-ml PR touches the ledger, and `gh search prs` finds the IDs only in canopy#676.
- The WIP titles match canopy's usage, so there is no ID swap: 056 is "a Stop … keeps the replay session" (`800c20bb` ledger `:8686`), and 057 is "the replay-weight stream is not wired end to end" (`:8706`).
- **Changes an action:** no; it confirms the planned order (the ledger lands first).

**6. NIT (pre-existing, not from round 2): the dict-id refusal guards only the class test.**
- The sibling at `:127` crashes with `TypeError: unhashable type: 'dict'`.
- An Interval with no id raises `KeyError: 'id'` at `:120`.
- **Changes a number/disposition/action:** no.

## CORRECTIONS I COULD NOT REFUTE

1. **Ledger citations claim no more than an ID and a file.**
   - `CHANGELOG.md:161-165`, `replay_player_panel.py:119`, `:542`, `:577-580`, `ws_dash_bridge.js:28`, `:223`, the test docstring at `:17-18` and the squash body give only the IDs and the filename.
   - The citations of other ledger content point at things already on main: "Phase 8" (`…E2E-VALIDATION-EVIDENCE.md:7865`, with −41.9%/−32.3% at `:8329`) and "the third cut" (`:7842-7845`).
   - "filed in that ledger" (`:576`) becomes true when the ledger lands.
2. **"Runs only once this page has started a replay" holds.**
   - The gate (`:78`) enables the drain only when `snapshot_id` is truthy.
   - There are only two writers. `hdf5_snapshots_panel.py:1269` writes only after a successful replay (`:1301-1326`). `dispatch_control` does nothing without a `snapshot_id` (`:679-680`).
   - No `set_props` writer exists in the JS assets.
3. **The corrected stale comments are accurate.**
   - Module docstring `:34-35`, Store comment `:116-119` and drain comment `:539-544` all hold.
   - `_emit_frame` puts no weights key in its frame (`manager.py:1198-1234`). `weight_cache` has no production use outside `_ReplaySession`.
   - The canopy relay rebuilds metrics from a fixed key list (`cascor_service_adapter.py:763-766`, `:1910-1939`).
   - The demo-mode metrics payload has no `weights` key, and the bridge fills its buffer only from `data.weights` (`ws_dash_bridge.js:231-235`).
4. **The Stop mechanism holds.**
   - Canopy's route returns cascor's envelope verbatim: `main.py:3012-3027`, then `cascor_service_adapter.py:2379`, then client 0.8.0's `response.json()`.
   - Cascor's envelope is never empty (`common.py:111-123`), and error paths return `no_update` (`replay_player_panel.py:686-687`).
5. **The squash body's figures check out.**
   - 42%/32%: ledger `:8329`.
   - Run-2 p50s: X2 5415.8 ms against C2 5336.9 (+1.48%) and C3 5275.5 (+2.66%). That is INCONSISTENT under the script's rule `X2 > max(C2, C3)` (`idle_cuts_live_check.py:37-38`, `:199-201`).
   - STRUCTURE and SESSION PASS in both transcripts.
   - "7 of its 9 fail on the parent": I ran the head's test file on `0254a7ec` and got 7 failed, 2 passed. The class test named exactly `['metrics-panel-update-interval']`.
6. **X/C and "loaded host" are gone from the tree** (grep of `4b4cfb16`).
7. **The dict-id assertion behaves as described.**
   - Today there are 17 Intervals, all with string ids, so it cannot fire.
   - An injected `{"type":"probe","index":0}` Interval triggers it, whether unconsumed or consumed via `ALL`. Dash serves that id as `{"index":["ALL"],"type":"probe"}`, as the comment says.
8. **The forward-looking comment holds.** The relay broadcasts to every page (`:766`). `network_evolution.py:159-186` has no session check. `decision_boundary.py:242-250` is session-gated and reads `buffer[-1]`.
9. **"No production caller" holds** (grep of cascor `origin/main`).
10. **The headline "spent about a third" is consistent with −32.3%/−41.9%.**

**Tests I ran on the PR-head extract:**
- The three named files: 52 passed, including the node RULE test.
- The 4 suites that parse `ws_dash_bridge.js`: 111 passed. This mattered because round 2 edited that file's comments.
- 9 interval-related suites: 321 passed.
- The pinned pre-commit hooks were clean on all 8 PR files.

## WHAT I COULD NOT CHECK

- **CI on `4b4cfb16`:** both "Unit Tests + Coverage" lanes were still pending (the other 19 checks were green), and I ran no whole suites.
- **Ledger entries:** I read only the title lines of F-CANOPY-056/057 in the WIP, to stay independent of its consensus text.
- **Stop against a live cascor:** checked from source only, since I started no processes.
- **Node on CI runners:** `ci.yml` has no setup-node step, and the RULE test skips without node.
- **Fresher cascor:** I used local `origin/main` and did not fetch.

**Changed:** none; I stayed read-only. Scratch work is in `…/scratchpad/laneB3cuts.9xxSoB/` (extracts of both trees, a throwaway `git init` for pre-commit, run logs). The inline probes used `/opt/miniforge3/envs/JuniperCanopy1/bin/python` directly, because `conda run` rejects multi-line arguments.

---
