# HANDOFF — canopy E2E arc: the fast lane is the fault, the fixture lost and re-grown, the relay found dead — and five validators refuting four of the claims

**Date**: 2026-09-08, corrected 2026-09-09 after round-1 validation · **Session**: <https://claude.ai/code/session_01SRNxcTzvA9M8nK1E54uSPv>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hashed-enchanting-puddle`
**Branch**: `docs/canopy-e2e-2026-09-08-f035-measured` — **created at commit time**; while this document was
being written the work lived uncommitted in the worktree named above, on `worktree-hashed-enchanting-puddle`.
juniper-ml PR **#1861**

**Documents REFERENCED** (the ecosystem convention in `/home/pcalnon/Development/python/Juniper/AGENTS.md`
§ Cross-Project Conventions requires the filename on every citation, because more than one document is cited):

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — the finding ledger, the arc's document of record; this session added **Phase 5 — 2026-09-08** at its end
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` — the row matrix; its §4 scripts are canonical for step detail
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — §3 sized this document's validation (§11)
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — this document's template
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_canopy-e2e-arc-f035-cause-found-and-outstanding-work.md` — the handoff this session inherited; its §0 item 2 came true exactly (a serving commit nobody had recorded), and its item 4's *outcome* came true by a
different route — the fixture was destroyed by a reboot plus tmpfs, not by the `POST /v1/network` that item named
- `util/ad-hoc/README.md` — the instrument inventory, with a new section for this session's tools

**Documents CHANGED by this session**: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, `util/ad-hoc/README.md`, `docs/REFERENCE.md`,
`util/isolated_stack.bash`, `tests/test_isolated_stack_script.py`, `util/ad-hoc/2026-09-04_canopy_verify_instance.bash`,
`util/ad-hoc/e2e_w3_params_driver.py`, `util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py`,
`util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py`, `reports/e2e/CURRENT_RUN_ID`, and this file. **Added**: nine
instruments under `util/ad-hoc/` (all dated `2026-09-08_`), `reports/e2e/20260908T000000Z/`, and **37** evidence
files under `reports/e2e-canopy-2026-09-02/` (`transcripts/2026-09-08_*`, `shots/2026-09-08_*`). **In juniper-cascor**:
PR #632 (`fix/snapshot-restore-seed-numpy-scalar`, two API-signed commits `3885fb91` + `0754e2e2` plus **three** server-side
update-branch merges — `3ea505e`, `51bbaddf`, `0c3b3e47`, as `main` moved under it), **MERGED 2026-09-09T01:24:12Z as
`5eb6f144`** by the auto-merge net `safe_merge.py` armed.

---

## 0. PREFLIGHT — read before anything else

1. **`uptime -s` before trusting any leg.** The legs of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_canopy-e2e-arc-f035-cause-found-and-outstanding-work.md` were all gone: the host rebooted at 2026-09-07 23:12
   local, `/tmp` is tmpfs, and the trio + verify leg run under `nohup` from `/tmp/juniper-e2e`. cascor's network lives in its
   process. **The fixture now has a 48-unit snapshot** — `snapshot_20260908T123427Z` — and a 52-unit one, `snapshot_20260909T002658Z`; the 09-05
   pre-growth one is `snapshot_20260905T103912Z`. Restore = `POST /v1/snapshots/<id>/resume` (keeps uuid + history, lands in
   `RESUME_READY`), then `POST /v1/training/dataset` (`spirals/1000/0.25/1.5/2`) and PATCH the cap before `start`. **Snapshot
   after every growth.**
2. **Confirm juniper-cascor#632 is merged** (`gh api repos/pcalnon/juniper-cascor/pulls/632 --jq '{merged,merged_at}'`). Until
   it is on `main`, any cascor that resumes a snapshot dies at its first candidate phase (F-CASCOR-003) and drops every
   WebSocket subscriber on its first broadcast (F-CASCOR-004). The `:8202` leg in `/tmp/juniper-e2e` runs the fix worktree
   (`worktrees/juniper-cascor--fix--snapshot-restore-seed-numpy-scalar--20260908-0725--d39d5370`, whose *working tree* carries
   both commits — `/v1/health` reports the branch base `d39d537…` because the stamp reads `git rev-parse HEAD`, and the second
   commit exists only on GitHub). **Do not delete that worktree while the leg runs.**
3. **Every leg now reports the commit it serves** on `/v1/health` (`git_sha`), and every driver prints it (`serving:` line). Quote
   that, not a checkout. `:8051` (the trio, launched before the stamp existed) reports `null` — it was launched from the primary
   at `eb05021`; `:8052` reports `eb05021d…`.
4. **The fixture is re-grown, not the 09-05 one, and it is now 52 units.** Same uuid `1cd15120…`; 2/48/2/1324 after the two
   morning windows (different weights from the 09-05 48 for the eight units grown today) and **2/52/2/1538** after the third,
   `COMPLETED`, epoch 56, 66 metrics rows. `candidate_patience` was 2000 during every growth window and is back at **50**. The
   52 state is `snapshot_20260909T002658Z`.
5. **Environment**: canopy python is `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python`.
   **Every browser instrument defaults to `http://127.0.0.1:8051`, NOT `:8052`** — they all read
   `util/ad-hoc/e2e_w3_params_driver.py`'s `CANOPY = os.environ.get("JUNIPER_E2E_CANOPY_URL", "http://127.0.0.1:8051")`.
   `:8051` is the trio leg and a **different build** (`/v1/health` reports version 0.4.0, `git_sha null`) from the `:8052`
   worktree leg every 09-08 measurement used. **Export `JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052` or measure the wrong
   leg** — the failure this arc has already paid for twice. (An earlier draft of this handoff said the default was `:8052`;
   round-1 validation caught it.)
6. **Read every "FIXED" and "PASS" below with §8's table beside it.** Five independent validators read this record before it
   was committed and refuted or downgraded eight of its claims; Phase 5 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` carries the corrections, and the wording
   here has been brought into line.

---

## 1. Goal statement

Continue the juniper-canopy E2E validation arc. Ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
matrix `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.

State: **62 findings — 41 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 4 P1, 14 P2)**; on 09-05 it was 55 / 37 / 1 / 1 / 16.
Matrix **298 rows, all 298 verdicted** — `e2e_row_coverage.py` says "296 / remaining 2" because it credits only the leading
token of the `M-PARAMETERS-01/02/03 PASS` slash enumeration in an old rowlog; both rows carry PASS in
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` itself.
**21 BLOCKED** (was 28: the six replay index/toggle rows became FAIL and M-TOPOLOGY-16 became PASS). Count them with a pattern
that also catches `BLOCKED (F-CANOPY-025)` at C2.10-03 — a bare `| BLOCKED |` grep misses that row and reports 20.

**What this session settled — and the one word it does not get to use.** `util/ad-hoc/2026-09-08_f035_supersession_test.py`
baselines the contended regime (39–40 responses each carrying 71 rows, store at 0), disables `fast-update-interval` via
`setProps`, and **the store fills within a couple of seconds and stays** — `APPLIED-UNCONTENDED`, in both replicates. So the
write lands the moment the fast lane is removed, and the fix belongs at the **trigger** (an Interval of its own, or clientside
gating), never `FAST_UPDATE_INTERVAL_MS`; **no canopy code is written**. What the test does **not** establish is the word
*supersession*: disabling that Interval removes **all ten** fast-lane callbacks at once, so it cannot separate "this callback
is superseded by its own next tick" from "promotion starvation under fast-lane contention" — the mechanism this repo already
documents for F-CANOPY-025. Both imply the same fix. The pre-registered discriminator (one hand-fired tick after the settle)
produced **zero** responses, so the verdict fired on the settle branch. The 09-07 `state.callbacks` lifecycle verdict is
withdrawn to *non-discriminating*: the same probe on the topology store returns the same `RETIRED-BEFORE-EXECUTION`, and it
perturbs the page it measures.

**What this session found.** Seven findings, all in Phase 5 of the ledger
(`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) — six filed 09-08, one added 09-09 by the validation,
and one of the six withdrawn the next day: **F-CASCOR-003** (every scalar HDF5 attribute restored as
a NumPy scalar — `/resume` died at the first candidate phase; FIXED, cascor#632), **F-CASCOR-004** (a broadcast that cannot be
serialised drops every training-stream subscriber silently, without a close frame; P1, OPEN — #632 removes today's trigger, not
the swallow-and-forget), **F-CANOPY-049** (canopy's relay reports that dead stream `healthy` indefinitely; P2, OPEN),
**F-CANOPY-048** (the replay controls never apply — the whole panel sits in a 1 Hz retrigger loop with the metrics store; P2,
OPEN; M-METRICS-11..16 FAIL), **F-E2E-008** (the `:8052` verify leg's control stream 403-looped since 09-04 and its pid file
protected nothing; FIXED here), **F-CANOPY-050** (the Candidate Metrics panel rendered nothing through a live candidate phase —
**WITHDRAWN 2026-09-09**, see §8), and **F-CANOPY-051** (canopy's persisted active tab is browser-**global**: one page's tab
selection silently moves every other page on the same browser, so a multi-page probe measures whichever tab was selected last;
P2/P3, OPEN, measured by `util/ad-hoc/2026-09-09_tab_crosstalk_probe.py`).

Then the relay repair sequence (`util/ad-hoc/2026-09-08_relay_repair_sequence.bash`). On the running leg the drop probe
printed **`INDETERMINATE`** — it saw no `state` frame but did see a `ping`, and its verdict rule at the time could not tell
those apart; **cascor's own log** is what showed the drop, `0 active connections` for the whole window
(`…_cascor_ws_summaries_window3.txt`). After the swap onto #632's tree
(`util/ad-hoc/2026-09-08_cascor_leg_swap.bash`) the same probe read **`STATE-RECEIVED`**, and the log's next summary reads
`state=8 … (3 active connections)`. The probe now reads `/v1/metrics/transport` instead of trusting pings, but **that rule has
never been exercised** — re-run it before relying on it as F-CASCOR-004's before/after. Then the third window, 48 → 52 with the
relay alive: **M-TOPOLOGY-16 → PASS** for the active half (55 `New Unit Edges` + one `New Unit Glow` trace, first seen at
t=89 s — 18.8 s *after* the run completed, at a 19–27 s sampling period), **F-CANOPY-036 FIXED at the server** (four
pool-history entries, `…_endpoint_evidence.txt`), and **F-CANOPY-026 FIXED for what it names** — `0m 18s` mid-phase against a
tz-aware `phase_started_at`, where the defect printed *300 minutes*. Read F-026's closure with its four caveats: only **one**
sample is mid-run, the probe's own rule scored it `STILL-OPEN` on a 16–26 s instrument skew, and **canopy#534's half was never
exercised** (it handles a naive timestamp; cascor emitted tz-aware).

**The single highest-value next action** is a canopy PR for F-CANOPY-035 at the trigger, with
`2026-09-08_f035_supersession_test.py`'s baseline as its before/after instrument. Second: cascor's `_send_json` must log and
`broadcast` must **close** a client it drops (F-CASCOR-004). Third, and harder than the 09-08 draft made it sound:
**F-CANOPY-049 is not "add a liveness rule"** — canopy's relay already degrades a stream after 60 s of silence and then
defeats its own rule by calling `mark_activity()` off cascor's transport pings every 30 s. The fix must tell a heartbeat from
a payload without re-breaking the idle-stream case that call was added for.

---

## 2. State at handoff

| | |
|---|---|
| Findings ledger | **62 — 41 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 4 P1, 14 P2)**; 09-05 was 55 / 37 / 1 / 1 / 16 |
| Matrix rows | 298, all verdicted / **21 BLOCKED** (M-METRICS-18, M-METRICS-27, M-CANDIDATES-10/-11, M-TOPOLOGY-11, M-EVOLUTION-07, M-BOUNDARIES-07, M-DATASET-03, M-DATASET-17..26, M-SNAPSHOTS-20/-21, **C2.10-03** which reads `BLOCKED (F-CANOPY-025)`); M-TOPOLOGY-16 is PASS on its active half |
| cascor fixture | uuid `1cd15120…`, **2/52/2/1538**, `COMPLETED`, epoch 56, 66 metrics rows; snapshots `snapshot_20260905T103912Z` (40), `snapshot_20260908T123427Z` (48), `snapshot_20260909T002658Z` (52) |
| Services | `:8051` canopy (trio, `eb05021`, git_sha null, **version 0.4.0**) · `:8052` canopy (worktree, `eb05021d`, 0.6.0 — **the leg every 09-08 measurement used**) · `:8101` data 0.13.0 · `:8202` cascor from the #632 worktree, **dirty**: `/v1/health` reports its BASE `d39d537` (a readme-renderer bump) while the merged fix rides uncommitted on top — content proven identical to `5eb6f144` by `util/ad-hoc/2026-09-09_verify_served_cascor_matches_merge.py` · `:8050`/`:8201`/`:8211` Docker deploy stack — do not touch |
| Run dir | `/tmp/juniper-e2e` (tmpfs — gone on reboot); pid files there are the reaper's protection key |
| PRs | juniper-cascor#632 **MERGED** (`5eb6f144`, 2026-09-09T01:24Z); juniper-ml **#1861** (signed commit `6efcce7d`) |
| Product code changed | juniper-cascor only (#632). No canopy code. |

---

## 3. What is still owed (in order)

1. **F-CANOPY-035 fix PR (canopy)** — at the trigger. Before/after with `2026-09-08_f035_supersession_test.py --baseline 30`
   (baseline alone is the measurement: writes carrying rows vs. store length). The ledger's F-035 entry
   (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) states **two** cautions, quoted here because an
   earlier draft of this handoff invented a third and dropped the first: (i) *"A faster handler is not obviously futile"* —
   against the measured 1.716 s gap the margin is ~0.11 s, so shaving the handler is untested, not ruled out; (ii) *"Do NOT
   raise `FAST_UPDATE_INTERVAL_MS`"* — it is the shared fast lane, two test files pin its membership and value, and
   `network_visualizer.py` derives M-TOPOLOGY-16's glow timing from it, so raising it silently rescales a row this arc owes.
   Before designing the fix, run one experiment that **separates supersession from fast-lane promotion starvation**; the
   09-08 test cannot, because it disables all ten fast-lane callbacks together.
2. **F-CASCOR-004 / F-CANOPY-049 fixes** — cascor: log in `_send_json`, `close()` in `broadcast`'s drop path (note the
   timeout branch *does* log today, and both branches already bump the `send_failures` counter `/v1/metrics/transport`
   serves). canopy: **not** a new liveness rule — `StreamHealth` already degrades after 60 s of silence, and
   `cascor_service_adapter.py` re-arms it every 30 s with `mark_activity()` driven by cascor's transport pings; the fix is to
   stop counting a heartbeat as a payload without re-breaking the idle-stream case that call exists for.
   `util/ad-hoc/2026-09-08_cascor_ws_drop_probe.py` is the intended before/after for the cascor half, but its transport-counter
   rule has never run — exercise it first.
3. **M-CANDIDATES-09..11, re-driven ONE TAB AT A TIME** — the growth window with the relay alive was run (48 → 52) and the
   Candidate Metrics panel rendered nothing while canopy's server held the pool. That was filed as F-CANOPY-050 and
   **withdrawn the next day**: its proof of invocation was false (the pool-history route is a pure read; the accumulator is fed
   by canopy's WS ingestion), and **F-CANOPY-051** shows the probe's page had almost certainly drifted to the Network Topology
   tab, which gates the panel's poll off. `util/ad-hoc/2026-09-08_live_run_probe.py` opens three pages on ONE browser context
   and is unsound as written — give each page its own `browser.new_context()`, or drive one tab at a time, and **record each
   page's own `active_tab` in the artifact**. Also owed on the topology side: M-TOPOLOGY-16's fade half (select another node
   while the glow is up). Any further growth: `PATCH /v1/training/params {"max_hidden_units": N}` then
   `POST /v1/training/start` — **never `POST /v1/network`** — and snapshot after.
4. **F-CANOPY-048 fix (canopy)** — the controls never apply. State the mechanism as a **claimed-Input promotion block**, not
   the "1 Hz value-rewrite loop" the 09-08 draft described: `replay-slider.value` is an Output of `update_replay_ui`, which is
   queued behind the metrics store every tick, and dash-renderer will not promote `handle_replay_controls` while one of its
   Inputs is claimed by a pending callback. The loop story cannot be right, because the store never wrote during the run that
   found the defect (`metrics_store_len: 0` before and after every step). Re-drive with
   `2026-09-08_replay_block_redrive.py`.
5. **M-DATASET-17..26** — the `equities` extra is no longer the blocker (`/v1/generators` reports both equities generators
   available on `:8101`); the owner question from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_canopy-e2e-arc-f035-cause-found-and-outstanding-work.md`
   stands: which arm loads a sequence dataset.
6. **The dispatch probe's control under a rule fixed BEFORE the run** — two runs observed 3 dispatches naming the store and an
   independent read of `hidden_units: 48`; both verdict strings are artifacts of a rule changed afterwards (first list-only, so
   a dict scored `DISPATCHED-EMPTY`; then dict-aware, so the same data scored `APPLIED-THEN-LOST`). The counts are the
   measurement; neither string should be quoted.
7. **F-CANOPY-038** — measured: 34 store writes / 60 s, 33 identical, 0 `no_update`. An identity guard in
   `_update_metrics_store_handler` is the obvious fix; note it cannot suppress anything until one write has landed.

---

## 4. Instrument inventory (new this session; every browser one defaults to `:8051` — export `JUNIPER_E2E_CANOPY_URL`)

| instrument | answers |
|---|---|
| `util/ad-hoc/2026-09-08_f035_supersession_test.py` | **the F-035 discriminating test** (baseline / disable / settle / trigger / watch) |
| `util/ad-hoc/2026-09-08_live_run_probe.py` | one growth run, three tabs: M-CANDIDATES-09..11, F-026 pairs, M-TOPOLOGY-16, WS liveness; `--start` |
| `util/ad-hoc/2026-09-08_replay_block_redrive.py` | M-METRICS-11..16/-18 with every prop read via `paths.strs` |
| `util/ad-hoc/2026-09-08_cascor_ws_drop_probe.py` | does a state broadcast drop a raw subscriber (F-CASCOR-004) |
| `util/ad-hoc/2026-09-08_topology_store_dump.py` | the topology store's SHAPE beside the stats bar and graph |
| `util/ad-hoc/2026-09-08_cascor_leg_swap.bash` | restart the trio's cascor from a worktree by pid; stamps its SHA; points at the primary's snapshot root |
| `util/ad-hoc/2026-09-08_append_signed_commit.py` | one API-signed commit onto an EXISTING branch (what `open_signed_pr.py` refuses) |
| `util/ad-hoc/2026-09-08_post_growth_sequence.bash` | the COMPLETED-state instruments, one browser at a time |
| `util/ad-hoc/2026-09-08_relay_repair_sequence.bash` | drop probe → leg swap → probe → 48 → 52 growth → snapshot |
| `util/ad-hoc/2026-09-09_tab_crosstalk_probe.py` | **does a second page steal the first page's tab?** (F-CANOPY-051 — it does) |
| `util/ad-hoc/2026-09-09_verify_served_cascor_matches_merge.py` | content-identity proof for a leg running a DIRTY worktree |
| `util/ad-hoc/2026-09-09_capture_endpoint_evidence.bash` | the six endpoints Phase 5 cites, into one transcript |

Changed: `2026-09-04_canopy_verify_instance.bash` (protected run dir, SHA stamp, overridable origin), `e2e_w3_params_driver.py`
(`serving_commit()`), the dispatch probe (`--store`, dict-aware rule), the lifecycle probe (dict-aware read).

---

## 5. Verify the starting state

**These numbers are the state AFTER juniper-ml#1861 merges.** Until then `main` still reads 55 / 37 / 1 / 1 / 16 and 27
BLOCKED — if you see those, the record has not landed yet, not been reverted.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or a fresh worktree
uptime -s                                                 # if after 2026-09-08, every leg below is gone
gh api repos/pcalnon/juniper-cascor/pulls/632 --jq '{merged,merged_at}'
python3 util/ad-hoc/e2e_finding_triage.py --note notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | tail -8
python3 util/ad-hoc/e2e_row_coverage.py | head -4        # "remaining: 2" is the KNOWN slash-enumeration artifact
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md   # 21 — note NO trailing pipe, or C2.10-03's "BLOCKED (F-CANOPY-025)" is missed
ss -ltn | grep -E ':(8051|8052|8101|8202)\b'
curl -s http://127.0.0.1:8202/v1/network            # uuid 1cd15120-…, hidden_units 52
curl -s http://127.0.0.1:8052/v1/health | grep -o '"git_sha":"[0-9a-f]*"'   # eb05021d… — and export JUNIPER_E2E_CANOPY_URL to this leg
grep 'WS emission summary' /tmp/juniper-e2e/logs/juniper-cascor.log | tail -1   # "N active connections", N > 0 when the relays are alive
```

---

## 6. Traps (new; §13 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_canopy-e2e-arc-f035-cause-found-and-outstanding-work.md` still applies)

1. **A pid file protects only inside a protected root.** The reaper scans `JUNIPER_EXP_RUN_ROOT` and `JUNIPER_E2E_RUN_DIR` at
   depth 3; a pid file anywhere else is decoration.
2. **A worktree-run cascor resolves its snapshot root inside its own tree** and lists nothing; set
   `JUNIPER_CASCOR_SNAPSHOTS_DIR` (the swap script does).
3. **Equality hides a NumPy scalar.** Assert the type, and exercise the use that fails.
4. **"Healthy" from a relay that has received nothing for ten minutes is not a measurement**; read the server's active-connection
   count.
5. **An instrument's control must be positive before its zero means anything, and the control must be on the right tab** —
   per-tab poll lanes gate on `active_tab`.
6. **Sampling the renderer perturbs it.** `evaluate` on a topology page waits on a saturated main thread (~22 s a call); a
   Redux-notify sampler that stringifies every callback entry changes the race it measures.
7. **A background wait loop that `pgrep -f`s its own pattern never exits.** Wait on a file marker instead.
8. **`gh pr update-branch` does not exist in this `gh`**; `gh api -X PUT repos/…/pulls/N/update-branch` does, and the merge
   commit it makes is GitHub-signed.
9. **Two canopy pages in one browser context do not keep their own tabs** (F-CANOPY-051). The persisted tab lives in
   localStorage, which the context shares, and a clientside callback drives `active_tab` from it — so the last page to pick a
   tab moves all the others, and every per-tab poll lane silently gates off on the pages that drifted. One context per page.
10. **A `git_sha` stamp is a lie when the tree is dirty.** The `:8202` leg reports a commit that contains none of the fix it is
   running. Compare CONTENT (`2026-09-09_verify_served_cascor_matches_merge.py`), and record both legs' identity in every
   artifact — the browser probes record canopy's only.
11. **An instrument that scores its own subject can be wrong about it.** The live-run probe printed `STILL-OPEN` for F-026 on a
   16–26 s skew of its own making, and four screenshots of three pages produced two images. Reconstruct timings from the
   transcript before quoting a delta, and open a screenshot before citing it.

---

## 7. Repository state at handoff

**juniper-ml** — everything this session produced lands in ONE commit on `docs/canopy-e2e-2026-09-08-f035-measured`,
created through the GitHub API (a local commit hangs on a YubiKey touch that never comes in a headless session).
11 tracked files modified, 56 added:

- **modified**: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
  `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, `util/isolated_stack.bash`,
  `tests/test_isolated_stack_script.py`, `util/ad-hoc/2026-09-04_canopy_verify_instance.bash`,
  `util/ad-hoc/e2e_w3_params_driver.py`, `util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py`,
  `util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py`, `util/ad-hoc/README.md`, `docs/REFERENCE.md`,
  `reports/e2e/CURRENT_RUN_ID`.
- **added**: 12 instruments under `util/ad-hoc/` (nine `2026-09-08_*`, three `2026-09-09_*`),
  `reports/e2e/20260908T000000Z/` (3 files), 36 transcripts (31 dated 09-08, 5 added by the validation) and 4 screenshots under
  `reports/e2e-canopy-2026-09-02/`, and this handoff.
- **the screenshots are Git LFS**: their objects were uploaded with `lfs push --object-id origin <oid>` and the commit
  carries the POINTER text, because an API commit hands GitHub whatever bytes you give it and would otherwise store the
  PNG itself, breaking the LFS contract for that path. Two screenshots the 09-08 draft cited were byte-identical
  duplicates showing the wrong tab; they were deleted before commit.

**juniper-cascor** — nothing outstanding: #632 is merged (`5eb6f144`). Its worktree
`worktrees/juniper-cascor--fix--snapshot-restore-seed-numpy-scalar--20260908-0725--d39d5370` is still **dirty and still
serving `:8202`** — do not remove it while that leg runs, and remember its `/v1/health` names the wrong commit.

**juniper-canopy** — clean; no canopy code was written this session. Every canopy finding here is a filed defect, not a
fix, and the F-CANOPY-035 fix PR is the successor's first job.

---

## 8. Validation — this document FAILED round 1

Validated per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §3: three Lane A readers
at distinct entry points (this handoff; the raw artifacts; the code and tests) and two Lane B opposing briefs (that the record
overstates closure; that its mechanism claims would mislead). All five ran read-only against the live stack and the repo.
**They refuted or downgraded eight claims**, every one of which has been corrected here and in
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`:

| claim as first written | what the lanes found |
|---|---|
| "every browser instrument defaults to `:8052`" | the default is `:8051`, a different build — the one error that would silently corrupt the successor's next measurement |
| F-CANOPY-050: "its server side appends to the accumulator, so the callback ran" | false at source; the route is a pure read. Entry **withdrawn**; F-CANOPY-051 filed |
| F-CANOPY-035: "supersession, measured" | the intervention disables all ten fast-lane callbacks; supersession vs promotion starvation **not separated** |
| "the WS append path lands, so F-035 is the REST-poll regime's defect" | `metrics_live` read false at 4 of 5 samples; the writer is **unattributed**; reframe withdrawn |
| F-CANOPY-049: "the socket never raised, so liveness never saw a dead peer" | the relay has a 60 s stale rule and defeats it by re-arming off cascor's pings every 30 s |
| F-CANOPY-048: "a 1 Hz value-rewrite loop" | the store never wrote during that run; it is a claimed-Input promotion block |
| the drop probe "read DROPPED-SILENT" | the artifact says `INDETERMINATE`; the counters came from cascor's log, and the probe's new rule is unexercised |
| "every artifact carries the serving commit; item 7 closed" | the cascor stamp names a commit without the fix, and no browser artifact names cascor at all — **item 7 re-opened** |

Four cited numbers had been read live and never archived; they are now in
`reports/e2e-canopy-2026-09-02/transcripts/2026-09-09_endpoint_evidence.txt` and
`…/2026-09-09_cascor_ws_summaries_window3.txt`. Two screenshots cited as evidence were byte-identical duplicates showing the
wrong tab and have been removed.

**What survived all five lanes**: the F-035 falsification branches (only two callbacks Output that store, neither can blank it,
`omitted: 0`, and the loss figure's trace count moved 0 → 1 with the fill); F-CASCOR-004's source reading and its
millisecond-exact drop timeline; the replay-block request census; storestorm's 34 / 33 / 0; M-TOPOLOGY-16's 55 + 1 traces; and
every count, snapshot id, uuid, port and file inventory in the record.

A round 2 was not run: round 1's findings were accepted rather than contested, and the corrections are recorded above rather
than argued. A successor who wants the stronger form should re-validate the corrected document.
