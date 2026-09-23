# HANDOFF — canopy E2E arc: F-CANOPY-035 read out of the renderer, FIXED and merged, and the defect that was hiding behind it

**Date**: 2026-09-10 · **Session**: <https://claude.ai/code/session_01SDwaTPuGgzypx9f1tE1ahB>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/glittery-wondering-cosmos`
**PRs**: juniper-canopy **#613 MERGED** (`b792256`) · juniper-ml **#1878 MERGED** (`c732e631`) · juniper-canopy **#614** (the strand repair round-1 validation forced)
**Validated**: rounds 1 and 2 run; the document **FAILED both**. Round 2 overturned the DISPOSITION —
see §9. Read §9 before trusting anything in §1–§6.

**Documents REFERENCED** (the ecosystem convention in `/home/pcalnon/Development/python/Juniper/AGENTS.md`
§ Cross-Project Conventions requires the filename on every citation, because more than one is cited):

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — the finding ledger, the arc's
  document of record; this session added **Phase 6 — 2026-09-10** at its end
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` — the row matrix
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_canopy-e2e-arc-f035-supersession-measured-and-the-relay-drop.md`
  — the handoff this session inherited; its §3 item 1 is now closed
- `util/ad-hoc/README.md` — the instrument inventory, with a new section for this session's five tools

**Documents CHANGED by this session**: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, `util/ad-hoc/README.md`, and
this file. **Added**: five instruments under `util/ad-hoc/` (all `2026-09-10_*`) and 14 evidence artifacts
under `reports/e2e-canopy-2026-09-02/transcripts/`. **In juniper-canopy**: `src/canopy_constants.py`,
`src/frontend/dashboard_manager.py`, `src/tests/unit/frontend/test_poll_gating.py`,
`src/tests/unit/frontend/test_stage2_global_lane.py` (PR #613, merged as `b792256`).

---

## ★ RE-EVALUATED 2026-09-22 — read this first; it supersedes §0, §2, §3 and §5 below

**Session**: <https://claude.ai/code/session_0171uABjF34XxFiu1n1L9wcG> · worktree
`juniper-ml/.claude/worktrees/lively-humming-pixel`. **Evaluated against**:

- canopy `main` `9bffaba1` (v0.8.1). `origin/main` has since moved to `886147b5`, canopy#656, which
  touches only the dataset-availability gate;
- cascor `05c13d5` (v0.11.0);
- juniper-data 0.15.0.

The full record is **Phase 7** of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
(the ledger). The verbatim validator reports are under `reports/e2e-canopy-2026-09-02/consensus/`.

**Verdict: outstanding work remained, and most of it is now done.** Every §3 item was resolved,
measured, or superseded. Along the way:

- **Filed and fixed the same day**:
  - F-CANOPY-053 (P1): the Candidate Metrics panel never applied a periodic write. A regression since
    `f9defb4`; canopy#657.
- **Closed**:
  - F-CANOPY-048: the replay block's two-callback cycle; canopy#658.
  - F-CANOPY-052, closed on the row's own script, with its mechanism corrected.
  - F-CANOPY-038, in behaviour.
  - F-CASCOR-004: juniper-cascor#674.
- **Filed, open**: F-CANOPY-054 (P2), unmasked by #658.
- **Refuted before it shipped**: the first F-053 fix design, which would have re-broken F-CANOPY-027.

**Documents CHANGED by this re-evaluation**:

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 7, plus in-place
  corrections to the F-CANOPY-038, -048, -052 and F-CASCOR-004 headers and the 09-08 F-038 passage;
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-CANDIDATES-01..07/-09 and
  M-METRICS-11..16/-18;
- `util/ad-hoc/README.md`;
- `util/isolated_stack.bash` and `tests/test_isolated_stack_script.py`: the aged-venv rebuild;
- this file.

**Added**:

- 17 files under `util/ad-hoc/2026-09-22_*`: 14 scripts, plus Lane B's three #674 probes in
  `2026-09-22_pr674_laneB/`;
- repairs to `2026-09-08_replay_block_redrive.py`, `e2e_f027_slots.py` and `e2e_w3_params_driver.py`;
- 49 evidence artifacts under `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_*`;
- the verbatim validator reports under `reports/e2e-canopy-2026-09-02/consensus/`.

### §3, item by item

| # | item (this document's §3) | status 2026-09-22 |
|---|---|---|
| 1 | run M-CANDIDATES-07's own script against a leg serving #618 | **DONE.** RENDER **PASS 4/4** on `9bffaba1`, all 30 candidate points, 4.8–12.5 s, so **F-CANOPY-052 is FIXED**. Its recorded mechanism was also corrected: its own wire census shows the callback was never dispatched, which is a readiness block, not eviction. THEME **FAIL 3/3** at F-CANOPY-004's 16 s contract: `theme-state` lands about 20 s after the toggle and the figure re-themes at about 30 s. The row stays FAIL on that new cause |
| 2 | M-METRICS-11..16/-18: (a) why `update_replay_ui` did not apply; (b) fix the probe | **(b) DONE**: the probe waits for the fill, scores each step on its own read, refuses vacuous passes, and counts server-side writes. **(a) ANSWERED**: `update_replay_ui` is never *ready*. It and `handle_replay_controls` form a two-callback cycle, and dash-renderer's cycle breaker fires only when nothing else is pending, which canopy's pollers never allow. Evidence: A and the play label were in `requested` in 6471/6471 queue samples, B in 4030/6471 from the click. A clean room locked 3/3 with the cycle plus an always-pending callback, against 3/3 live without the cycle. Lane B confirmed this with 30 variant runs and corrected the explanation: the lock needs the cycle plus a callback pending at every pass. **-18 goes BLOCKED → FAIL** on `9bffaba1`. **Fixed by canopy#658** (the two callbacks merged into one), verified live at `2f2f5040`: six of seven rows PASS at the 16 s settle. **M-METRICS-13 still FAILs, on the new F-CANOPY-054**: a late `replay_tick` response undoes the pause |
| 3 | the three sibling consumers: measure, then demote or fix the writer | **SUPERSEDED by F-CANOPY-053 (P1).** The consumers are not "surviving on a margin": their writer's periodic writes NEVER apply (0/225 at the 1000 ms period, 23/24 at 10 000 ms), and the consumers are readiness-blocked behind it. It is a **regression since `f9defb4`**, where the rows were proven live on 2026-08-24. The first fix design (`running=` on the lane) was **refuted**: on this tab-gated lane it would re-break F-CANOPY-027. canopy#657 was redesigned instead: a 10 s period, write only real changes, hold the last good value. **Merged as `d7d641b9`** and verified live on `17588539`: the rows track the server with a ~10–20 s lag, and the lane stays gated off-tab (11/11 samples) |
| 4 | F-CASCOR-004 / F-CANOPY-049 | cascor half: **FIXED, juniper-cascor#674 merged as `f9818b01`** after two review rounds. Round 1 found a false asyncio ERROR on 3.14 and a 1006-for-1011 on the sans-I/O stack Docker runs, and both were fixed. Round 2 had the live probe pass on both stacks. The drop probe's transport-counter rule ran for the first time and returned STATE-RECEIVED on `main`, as predicted; the NumPy trigger is gone. **F-CANOPY-049 is untouched** |
| 5 | the 27–37 s full-history regression | **MEASURED**: the full refetch lands every **32.4 s** (p50, n=3) against about 5 s before #613, with the guarded lane cycling every 6.5 s. Recommendation, not taken: `FULL_HISTORY_POLL_TICK_MODULUS` → 1 |
| 6 | the ~4–5 s re-enable overhead | **EXPLAINED BY MEASUREMENT.** It is the page's response-delivery latency: p50 5.09 s at idle against a ~30 ms network leg. A CPU profile shows the main thread 0.1% idle, 85% of it in dash-renderer's dispatch bookkeeping |
| 7 | re-baseline after #614/#618 | **DONE by construction.** Every leg used on 09-10 and 09-11 is gone; everything was re-measured on `main` |
| 8 | Phase 5 items 3/5/6/7/9 | 3 → the Candidate Metrics rows re-driven one tab per browser (F-053). 5 → the M-DATASET-17..26 owner question stands. 6 → retired: F-035 is closed on source + clean room, and the dispatch probe's verdict strings are quoted nowhere. 7 → **F-CANOPY-038 FIXED** in behaviour (1 carried + 10 `no_update` per 90 s; test gap stands). 9 → the M-TOPOLOGY-16 fade half is still owed |

### §0 PREFLIGHT is stale — what is true now

- **No legs on `:8052/:8053/:8054`.** The trio stopped cleanly on 2026-09-19. It was relaunched from the
  primaries with `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper bash util/isolated_stack.bash --up`.
  The script derives the wrong root from a `.claude/worktrees` checkout. It also now rebuilds a data venv
  that systemd-tmpfiles aged into an empty skeleton.
- **Fixture 2/68/2, uuid `1cd15120…`, 116 metrics rows**, with snapshots
  `snapshot_20260922T{194346Z,195609Z,202310Z}` and `snapshot_20260923T003754Z` (the 68-unit one). **A resumed snapshot restores the network but NOT the
  metrics history**, which lives in cascor's process. After any relaunch, run one window with
  `util/ad-hoc/2026-09-22_fixture_grow.py --to <N+2>`.
- **Browser harness**:
  - `JUNIPER_E2E_BROWSER_GPU=1` gives the host GPU; the default is SwiftShader.
  - Keep concurrent browsers at 3 or fewer: canopy's per-IP WS cap is 5, and validators hit 403s.
  - `JUNIPER_E2E_CANOPY_URL` must still be exported.

### Still owed, in order

1. **F-CANOPY-054** (P2, new): make `replay_tick` clientside, or version the state so the server refuses
   a stale tick. Then re-drive M-METRICS-13. Folding the tick into the merged callback is NOT a fix:
   same-identity eviction would drop the ticks.
2. **M-CANDIDATES-10/-11**: now re-drivable, since cards exist on `main`. CAN-015's replay-player loop is
   the latent trigger shape F-048's review named, exempted by name in canopy#658's cycle test.
3. **Hunt the F-053 regression**: what across the 132 commits `f9defb4 → 9bffaba1` raised the page's
   latency. Profile both builds; take a dispatch-rate census by source.
4. **Cheap cuts to the dispatch rate** (round 2's list):
   - the dead 1 Hz `metrics-panel-update-interval`, which nothing consumes;
   - the ungated 500 ms `replay-player-panel-weight-drain`;
   - `/api/state` rewrites whose only change is `timestamp`.
   Then re-profile idle against the 0.1% baseline. The structural remedy remains the WS migration
   (JR-CAN-PERF-004), e.g. via `dash_clientside.set_props`.
5. **The top status bar**: one-browser measurement, then file or fold. It is a candidate fourth writer
   of the same class, observed frozen only under WS-refused, multi-browser conditions.
6. **Owner: re-evaluate F-CANOPY-004's contract.** Interaction re-render was measured at 22–30 s against
   ≤16 s, and idle latency L at p50 5 s.
7. `FULL_HISTORY_POLL_TICK_MODULUS` → 1: a decision, with the measurement ready.
8. **canopy#613's guard, source-derived and not observed**:
   - `runningOff` from a mid-fetch completion overwrites the CAN-000 apply clamp;
   - an EVICTED request's `completeJob` re-enables the lane during its successor's flight, so #614's
     "self-healing, bounded to one cycle" is wrong.
9. **F-CANOPY-049** (canopy's half of F-CASCOR-004): distinguish a heartbeat from a payload.
10. **#674 review follow-ups**: the same swallow-and-forget pattern lives in juniper-service-core's
    WebSocket manager (`juniper_service_core/websocket/manager.py`) and in canopy's browser-facing
    `src/communication/websocket_manager.py`.
11. Unchanged: the M-DATASET-17..26 owner question, the M-TOPOLOGY-16 fade half, and F-038's
    browser-level test gap.

### Verify the starting state (replaces §5)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml          # or a fresh worktree
python3 util/ad-hoc/e2e_finding_triage.py --note notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | tail -6
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md   # 20
gh pr view 657 -R pcalnon/juniper-canopy --json state,mergedAt; gh pr view 674 -R pcalnon/juniper-cascor --json state,mergedAt
ss -ltn | grep -E ':(8051|8101|8202)\b'; curl -s http://127.0.0.1:8051/v1/health | grep -o '"git_sha":"[0-9a-f]*"'
curl -s http://127.0.0.1:8202/v1/network            # uuid 1cd15120…, hidden_units 62
```

Expected output:

- ledger: **65 findings — 47 fixed / 1 accepted / 2 withdrawn / 15 open (0 P0, 2 P1, 13 P2)**;
- matrix: **298 rows, BLOCKED 20**;
- canopy `main` carries #657 (`d7d641b9`) and #658 (`9fbd697a`);
- cascor `main` carries #674 (`f9818b01`).

The `:8202` cascor leg still serves `05c13d5`, which is BEFORE #674. Relaunch it before any cascor WS
measurement.

### Traps learned this session

1. **The wire tells the two renderer mechanisms apart.** Responses delivered but never applied means
   eviction (F-035, F-053's writer). No request at all means a readiness block (F-052, F-053's consumers,
   F-048). An A/B that stops a trigger cannot separate them, because it lifts both.
2. **`running=` on a TAB-GATED interval defeats the gate.** It releases in `completeJob()` after every
   run, including the 204 `no_update` ones at load and on tab changes. #613 was safe only because its
   lane is global.
3. **A verdict predicate can be mis-specified even when fixed before the run.** "Label shows ⏸" is not
   "label changed", and a mount-time run had already set ⏸. The run was recorded INDETERMINATE, and a
   corrected rule was fixed before a fresh run. Never re-score archived data.
4. **An expected-result cell can state CONTENT while its verdict was scored on LIVENESS.** Mount defaults
   satisfy "Pool size; default `0`". The criterion that was applied must be written into the row.
5. Relaunch traps: a resumed snapshot has no history; `/tmp` ages files, not directories; the per-IP WS
   cap is 5.

---

## 0. PREFLIGHT

1. **`uptime -s` before trusting any leg.** The host has not rebooted since **2026-09-07 23:12**, so every
   leg from Phase 5 was still up when this session ran. `/tmp` is tmpfs; a reboot destroys `/tmp/juniper-e2e`
   and the fixture lives in cascor's process.
2. **There are now TWO canopy verify legs and they are different builds.** `:8052` serves `eb05021d`
   (**before** the fix) and `:8053` serves `eab7cf43` (**after**). Neither is the trio's `:8051`, whose
   browser instruments still default to it — **`JUNIPER_E2E_CANOPY_URL` must be exported for every probe**,
   the failure this arc has paid for three times now.
3. **canopy `main` already carries the fix** (`b792256`), plus the strand repair once **#614** lands. The
   `:8053` leg was launched from the fix worktree
   `worktrees/juniper-canopy--fix--f035-metrics-store-running-guard--20260910-0459--8cfb29ac`. Its HEAD is
   **`6f04da6e`**, not `eab7cf43` (the commit was amended after the leg launched), and its files were
   rewritten **9 minutes after the process started** — so the leg is executing `eab7cf43`'s bytes while the
   tree on disk is byte-identical to `main`. The `eab7cf43 → main` delta is 22 lines across 2 files and
   **every one is a comment**, so the leg is functionally main's fix; that is proven by content, not by the
   stamp. **Do not delete that worktree while `:8053` runs.**
4. **The fixture is untouched.** uuid `1cd15120…`, 2/52/2/1538, `COMPLETED`, epoch 56, **66 metrics rows**
   (`output` 54 / `candidate` 12). Snapshots `snapshot_20260905T103912Z` (40), `…20260908T123427Z` (48),
   `…20260909T002658Z` (52). No growth run was done this session.

---

## 1. Goal statement

Continue the juniper-canopy E2E validation arc. Ledger
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, matrix
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.

State: **63 findings — 42 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 3 P1, 15 P2)**; it was
62 / 41 / 1 / 2 / 18 with 4 open P1. Matrix **298 rows, 296 verdicted** (the known slash-enumeration
artifact — both `M-PARAMETERS-01/02/03` rows carry PASS in the matrix itself), **21 BLOCKED**. Count
BLOCKED with a pattern that has **no trailing pipe**, or `C2.10-03`'s `BLOCKED (F-CANOPY-025)` is missed
and you get 20.

**What this session settled.** F-CANOPY-035's mechanism, read out of the shipped dash-renderer bundle
(`dash_renderer.dev.js`, unminified in `JuniperCanopy1`, dash 4.2.0) rather than inferred from behaviour:
`:2698` discards a response whose callback has left `watched`; `:3027` evicts a `watched` entry the instant
the same identity appears in `requested` (`concat(watched, requested)` grouped by `getUniqueIdentifier`,
each group sliced `[0:-1]`, `requested` concatenated LAST). `getUniqueIdentifier` hashes **one callback's
own** inputs/outputs/state, so the other nine fast-lane callbacks are different identities and **cannot**
evict it — which separates self-eviction from fast-lane promotion starvation **at the source**, and is what
the inherited handoff's §3 item 1 asked for.

**The displacing event is the TICK creating a `requested` entry**, not the next HTTP request. Every prior
measurement on this finding — and this session's first one — used the HTTP boundary, which is why the
ledger carried four numbers read as evidence *against* the mechanism. Three were boundary errors; the
fourth (`everSeen: {watched: 1}` — two concurrent entries never observed) is what the mechanism
**predicts**, because the eviction is synchronous with the insertion.

**What closed it** — corrected after validation. The **source reading** (`:2698`, `:3027`, and
`getUniqueIdentifier`'s contents, all independently re-verified in round 1) and the **clean room**, an
~80-line app with no canopy at all that reproduces the defect and shows `running=` fixing it. The
dose-response is a supporting correlate and **not** the load-bearing evidence: its verdict was
structurally forced, and neither of its two fills is attributable to the long period (§9, C2).

**The fix (canopy#613, merged).** `update_metrics_store` gets its own `dcc.Interval` and
`running=[(Output(<that interval>,"disabled"), True, False)]`, which stops this callback re-requesting over
itself **on its own clock** — not, as first written, "structurally impossible" full stop (§9, C1 and the
two unmeasured holes there). Live: the store went from **0 across a 90 s window and 52 pre-control
full-payload responses** to filling **7.3 s after observer install**, with the fast lane still ticking at
its delivered ~0.51 Hz (not the nominal 1 Hz — §9, C5).

**What this session did NOT get, and got WRONG.** M-CANDIDATES-07 is still **FAIL**, and the reason is
not what this session filed. The candidate loss figure rendered in 2 of 6 loads and that was filed as
**F-CANOPY-052**, "the defect the empty store was masking". Round 2 established it is **the same defect**:
`update_loss_plot` took the training-state store as an Input, that store is rewritten every second with a
value that always differs, and the renderer evicts the in-flight invocation exactly as it did for the
metrics store. Re-disposed **P2 → P1**, fixed in **canopy#618**. Measured 1/3 with the re-trigger running
vs **3/3 with it stopped** (§9, R1).

---

## 2. State at handoff

| | |
|---|---|
| Findings ledger | **63 — 42 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 4 P1, 14 P2)** — F-CANOPY-052 re-disposed P2 → P1 on 2026-09-11 |
| Matrix rows | 298, 296 verdicted / **21 BLOCKED**; M-CANDIDATES-07 FAIL — **never yet driven against canopy#618**, which is the fix for its cause |
| cascor fixture | uuid `1cd15120…`, 2/52/2/1538, `COMPLETED`, 66 metrics rows (`output` 54 / `candidate` 12) |
| Services | `:8051` canopy (trio, `git_sha null`, v0.4.0) · `:8052` canopy `eb05021d` v0.6.0 — **the BEFORE leg** · `:8053` canopy `eab7cf43` v0.6.0 — **the AFTER leg** · `:8101` data 0.13.0 · `:8202` cascor `d39d537` (dirty; content-proven identical to merged `5eb6f144`) · `:8050`/`:8201`/`:8211` Docker deploy stack — do not touch |
| PRs | juniper-canopy **#613 MERGED** `b792256` · juniper-ml **#1878 MERGED** `c732e631` · juniper-canopy **#614** (strand repair, round 1) · juniper-canopy **#618** (the F-052 trigger demotion, round 2) |
| Product code changed | juniper-canopy only — #613, #614 (the strand defect #613 introduced), #618 (the consumer #613 left evicted). No cascor, no data. |

---

## 3. What is still owed (in order) — RE-ORDERED by round 2

**Read §9 first.** The previous ordering put the most expensive item first and it was misdirected; the
two cheapest and highest-value items were buried behind it.

1. ~~Re-drive M-CANDIDATES-07 against a leg serving canopy#618.~~ **DONE 2026-09-11 — the fix holds.**
   Leg `:8054` at `a5cbdcd1`: the control arm renders **3/3** (was 1/3 on `:8053`), `loss_plot_responses: 1`
   every run. The row is still not scored PASS — this drive measures the figure, not the row's full
   script. **Owed: run the matrix's own M-CANDIDATES-07 script against `:8054`.**
2. ~~M-METRICS-11..16/-18 re-drive.~~ **DONE 2026-09-11, and it decoupled F-CANOPY-048 from
   F-CANOPY-035.** The store filled during the run (`initial` 0 → `final` **66**) and the replay UI still
   read `0 / 0` with `max_index 0`, while the data-independent rows (-13 play toggle, -16 speed) failed
   too. So F-048 is the sole blocker for all seven; the index rows are no longer downstream of an empty
   store. **Owed: (a) why `update_replay_ui` did not apply on the fill — it takes `metrics-store.data` as
   an INPUT (`metrics_panel.py:1086`), so the fill is a trigger it received; the claimed-Input promotion
   block is still only a hypothesis; (b) FIX THE PROBE — it reads the store ONCE before driving and scores
   the index rows on that stale value, which on a fixed leg mis-attributes them to F-035.**
3. **The sibling sweep is DONE — decide what to do about the three it found.** `update_status_display`
   (`:283`), `update_epoch_progress` (`:303`) and `update_pool_info` (`:322`) each take that same 1 Hz
   store as their **only** Input, so all three are structurally exposed to the identical eviction. They
   are **not** currently broken: they build a badge, a progress figure and a text block, so their round
   trip stays under the re-request period, while `update_loss_plot` built a Plotly figure and lost. That
   is a margin nobody chose and nobody measures — any change that slows one of them flips it to
   intermittent-blank with no error anywhere. Measure the three round trips, then either demote the
   Inputs (as canopy#618 did) or fix the WRITER: `fetch_training_state` returns unconditionally for this
   store while identity-suppressing its OTHER output in the same function. Recorded in Phase 6 as a
   latent risk, deliberately **not** filed as a finding — nothing observed is broken.
4. **F-CASCOR-004 / F-CANOPY-049** — unchanged and untouched. cascor: log in `_send_json`, `close()` in
   `broadcast`'s drop path. canopy: **not** a new liveness rule — `StreamHealth` already degrades after
   60 s and `cascor_service_adapter.py` re-arms it every 30 s off cascor's transport pings.
   `util/ad-hoc/2026-09-08_cascor_ws_drop_probe.py`'s transport-counter rule has still **never** run.
5. **The 27–37 s full-history regression** (§9, R5) — quantify it and decide whether
   `FULL_HISTORY_POLL_TICK_MODULUS` moves. Needs a full-mode round-trip measurement nobody has taken.
6. **The fix's ~4–5 s re-enable overhead** — measured, unexplained, and now less urgent than it looked:
   it is a cadence cost, while item 5 is a 5–7× staleness regression on the same surface.
7. **Re-baseline after #614 and #618 merge.** Every `:8053` number in this record then describes a
   superseded build. Either relaunch the AFTER leg or mark them.
8. **Phase 5's items 3, 5, 6, 7 and 9** are untouched.

## 4. Instruments added (all `util/ad-hoc/2026-09-10_*`)

| instrument | answers |
|---|---|
| `2026-09-10_f035_unopposed_response_test.py` | per-response bracket: did THIS response land, and could anything evict it. **Read the docstring** — its first verdict used the wrong boundary and is marked superseded |
| `2026-09-10_f035_trigger_period_sweep.py` | the dose-response that closed the mechanism |
| `2026-09-10_f035_running_guard_cleanroom.py` | reproduce with no canopy; test `running=` as the fix |
| `2026-09-10_f035_fix_wiring_check.py` | the fix's six wiring properties, off the BUILT app |
| `2026-09-10_f035_downstream_consumer_probe.py` | F-CANOPY-052: data or render, and does the consumer fire |

---

## 5. Verify the starting state

**These numbers are the state AFTER juniper-ml#1878 merges.** Until then `main` reads 62 / 41 / 1 / 2 / 18
with 4 open P1 — if you see that, the record has not landed yet, not been reverted.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or a fresh worktree
uptime -s                                                 # after 2026-09-07 23:12 → the legs below are gone
gh api repos/pcalnon/juniper-canopy/pulls/613 --jq '{merged,merge_commit_sha}'   # true, b792256…
gh api repos/pcalnon/juniper-ml/pulls/1878   --jq '{state,merged}'
python3 util/ad-hoc/e2e_finding_triage.py --note notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | tail -8
python3 util/ad-hoc/e2e_row_coverage.py | head -4        # "remaining: 2" is the KNOWN artifact
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md   # 21 — no trailing pipe
ss -ltn | grep -E ':(8051|8052|8053|8101|8202)\b'
curl -s http://127.0.0.1:8053/v1/health | grep -o '"git_sha":"[0-9a-f]*"'   # eab7cf43… — the FIXED leg
curl -s http://127.0.0.1:8052/v1/health | grep -o '"git_sha":"[0-9a-f]*"'   # eb05021d… — the BEFORE leg
curl -s http://127.0.0.1:8202/v1/network                                     # uuid 1cd15120…, hidden_units 52
grep 'WS emission summary' /tmp/juniper-e2e/logs/juniper-cascor.log | tail -1   # N active connections, N > 0
```

---

## 6. Traps (new; Phase 5's still apply)

1. **The renderer's eviction boundary is neither the HTTP request NOR the tick timestamp — it is the
   contents of `requested`/`watched` at the reducer pass that resolves the call.** The HTTP boundary is
   wrong at the head (a `requested` entry from an earlier tick still evicts) and the tick boundary is wrong
   at the tail (the check happens at APPLY time, measured 0.7–7.0 s after the response arrives). **Both
   boundaries returned `SUPERSESSION-INSUFFICIENT` in this session** — the corrected run did not overturn
   the first, and an earlier draft of this handoff implied it had (§9, C10). Neither verdict is sound; the
   mechanism rests on the source reading and the clean room, not on these runs.
2. **A `dcc.Interval` does not tick at its nominal rate under load.** 54 ticks per 90 s at a 1000 ms
   period, ~0.6 Hz. Read the gap from observed `n_intervals` transitions, never from the constant.
3. **~~Forcing a store change destroys the data you are testing.~~ FALSE — and this is the trap to learn
   from.** The claim was that `window_size: 40` drops the candidate rows because they "sit EARLY". Against
   the live fixture they are at **indices 53–64 of 66**, and a last-40 window keeps **all twelve**. The
   force did not remove them, and the `RENDER-STILL-DEAD` result it was invented to explain away stands
   **unexplained**. Keep `--no-force` for rate observations anyway (a forced arm is a different treatment),
   but the lesson is the general one: an inconvenient result got an invented mechanism instead of a
   measurement, and nobody checked the fixture until round-1 validation did.
4. **On a FIXED leg the store fills during page load**, so an observer installed after the tab settle reads
   it already full and records no transition. Use `--early-observer`.
5. **`e2e_finding_triage.py` reads only the LAST 170 characters** of a finding's bold header
   (`tail = body[-170:]`). A `FIXED` placed early in a long header is invisible and the finding still
   counts as open. Put the disposition at the END. (Also: the header must be a bold `**F-… — …**` line at
   column 0 — an `###` heading is not counted at all.)
6. **`running=` is not on the `callback_map` entry.** `dash/_callback.py:326` puts it on the callback SPEC,
   in `app._callback_list`, which is what is served as `_dash-dependencies`. A test that asserts it off
   `callback_map` silently reads `None` and passes for the wrong reason.
7. **Force-resetting a PR branch closes the PR.** Pushing the branch back to `main` to rewrite a commit
   made GitHub auto-close canopy#613 (zero commits at that instant); it reopened cleanly via
   `gh api -X PATCH …/pulls/613 -f state=open` once the new commit landed. Expect it; do not re-cut.
8. **`open_signed_pr.py --commit-body-file` takes a BODY, not a full message.** Passing the whole message
   duplicates the subject line, and juniper-canopy's `squash_merge_commit_message` is `COMMIT_MESSAGES`, so
   the duplicate would reach `main`.
10. **Verify the ENCLOSING FUNCTION, not just the line.** This is the error that shipped a live defect
   to `main`. `:1113` was checked and does dispatch `runningOff` on an error path — but it is inside
   `_handleWebsocketCallback`, a transport the callback never takes. The line did what was claimed; it was
   not on the code path. Three documents asserted the guarantee. Before citing a renderer line, establish
   which function contains it and which branch reaches it — §1's whole mechanism rests on three such reads.
11. **An inconvenient result is where invented mechanisms get in.** `RENDER-STILL-DEAD` was explained away
   with "the candidate rows sit EARLY so the force dropped them" — a claim nobody checked against the
   fixture, and false (they sit at indices 53–64 of 66). The general form: when a result contradicts the
   working hypothesis, the next step is a measurement, not a story.
12. **`state.callbacks` has a reader already, and it was RETIRED on a positive control.**
   `util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py` reads `getState().callbacks` via
   `store.subscribe`. It returns the same `RETIRED-BEFORE-EXECUTION` verdict for a store that provably
   works, and it perturbs the page (`JSON.stringify` on every entry of every list, every notify). Do not
   rebuild it; do not trust it without a positive control that can come out negative.

13. **`2026-09-08_append_signed_commit.py` reports a network failure as "branch not found".** A TLS
   handshake timeout printed `REFUSED: branch … not found`. Re-check the ref before believing it.

---

## 7. Repository state at handoff

**juniper-ml** — **#1878 is MERGED** as `c732e631`, carrying **23 files** (3 modified, 20 added) in **two**
signed commits: `fcb3ad8b` (19 added + 3 modified) and `20e121d2` (this handoff). Both were created
through the GitHub API — a local commit hangs on a YubiKey touch that never comes in a headless session.
The round-1 corrections to the ledger, the matrix, this file and
`util/ad-hoc/2026-09-10_f035_downstream_consumer_probe.py` are a **separate, later** change; check whether
they have landed before assuming the numbers here are the ones on `main`.

**juniper-canopy** — `main` at `b792256` carries the F-CANOPY-035 fix. **#614 is the strand repair** that
round-1 validation forced (a network-level fetch failure permanently disables the guarded Interval); check
its state before reading `:8053`'s behaviour as final, since that leg predates it. The fix worktree
`juniper-canopy--fix--f035-metrics-store-running-guard--20260910-0459--8cfb29ac` is clean at HEAD
**`6f04da6e`** and **is serving `:8053`** — do not remove it while that leg runs. Its branch
`fix/f035-metrics-store-running-guard` was deleted on merge. The strand repair has its own worktree,
`juniper-canopy--fix--f035-running-guard-strand-repair--20260910-2002--b7922569`.

**juniper-cascor / juniper-data** — untouched.

---

## 8. Validation status — TWO rounds run, and this document failed both

Per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, sized to the
top-right cell (six of seven escalators). **Round 1** — three Lane A reviewers at distinct entry points —
produced 10 corrections and one live code defect (canopy#614). **Round 2** — two Lane B reviewers on
opposing briefs, run on the round-1-corrected text as §2 requires — overturned the **disposition**, found
**two errors introduced by round 1's own fix pass**, and found that the control round 1 declared untouched
is confounded.

**What survived both rounds**: the eviction mechanism. Re-verified from the bundle by a reviewer who read
`getUniqueIdentifier` independently, reproduced in a canopy-free clean room, and demonstrated a third time
by the F-052 A/B — the only genuinely single-variable measurement in the set. **Nothing was reverted.**

A third round is **not** owed on the termination rule (§4: stop when a round produces no finding that
changes a number, a disposition, or an action) — but round 2 changed all three, so its own corrections are
unreviewed. Treat §9 R1–R7 as the least-audited text here.

---

## 9. Corrections (read before §1–§6)

### Round 2 — the disposition was wrong

| # | as written | what round 2 found |
|---|---|---|
| R1 | F-CANOPY-052 is "a second defect the empty store was masking", P2 | **It is F-CANOPY-035's mechanism**, one callback downstream. `update_loss_plot` took the training-state store as an Input; that store is written off a 1000 ms interval **unconditionally**, and `/api/state` carries a per-call `timestamp` so the value always differs. Re-`requested` at ~1 Hz under one `getUniqueIdentifier` → `:3027` evicts, `:2698` discards. **Measured: 1/3 with the tick running, 3/3 with it stopped.** Re-disposed **P1**; fixed in canopy#618 |
| R2 | "F-CANOPY-035 FIXED" | **fixed for ONE victim.** The store was repaired; the consumer that reads it was left evicted. With F-052 at P2 this also produced "canopy has zero open P1" while a panel was blank on two thirds of loads |
| R3 | the remaining split is "never fired vs fired and returned `no_update`" | **the second branch is impossible in the source** — `update_loss_plot` has two returns and neither is `no_update`. And "zero traces AND zero annotations" is reachable only as the `dcc.Graph` mount default (no `figure=` prop), which is proof no output was ever applied |
| R4 | still-owed item 1: build a `store.subscribe` reader of `getState().callbacks`, "no probe in this arc has ever built" one | **it exists** — `2026-09-07_f035_callback_lifecycle_probe.py`, 25 KB, documented in this ledger ~6,000 lines earlier — and was **retired on a positive control**. The item would have cost a successor a day |
| R5 | the fix's only cost is the ~4–5 s cadence overhead | #613 also moved the tick `FULL_HISTORY_POLL_TICK_MODULUS` counts, so full-history refetch went **~5 s → ~27–37 s**. Named in canopy#614 and nowhere here |
| R6 | round 1's "the clean room varies only `running=`, on a shared lane" | **false** — one Interval, one callback: a *dedicated* lane, and the `plain` arm **is** a dedicated lane without the guard, which never filled. Round 1 discarded the arm supporting half the shipped fix |
| R7 | round 1's C4, "the wire census **excludes** 'fired and was not applied'" | too strong — the census swallows unparseable responses (`except Exception: return`, **no `unparsed` counter**) and attaches ~5 s after navigation. And that branch is the one that was happening |
| R8 | "Before / after, **matched legs**", three times | **false.** `eb05021d → eab7cf43` is 39 files / 3726 insertions / 12 commits, with **442 insertions in `dashboard_manager.py` alone** — 8× the fix's delta, in the file that registers every callback. Struck; it is suggestive, not a control |

### Round 1 — the counts and one live defect

| # | as first written | what round 1 found |
|---|---|---|
| C1 | "`running=` … so a failed fetch cannot strand the poller" | **FALSE, and a live defect.** `:1113` is in `_handleWebsocketCallback`. On the HTTP path `runningOff` comes only from `completeJob()`; `handleError` rejects without it, so a **network failure strands the poll for the life of the page**. Repaired in canopy#614 |
| C2 | the dose-response "closed it" | **structurally forced** (ascending + stop-on-land ⇒ its falsifier is unreachable), and neither fill is attributable to the long period; 0 of 37 long-period invocations landed anything |
| C3 | "the 12 candidate entries sit EARLY" | **FALSE** — indices 53–64 of 66. `RENDER-STILL-DEAD` was unexplained, not contaminated (and R1 now explains it) |
| C5 | "fast lane still ticking at 1 Hz" | **0.507 Hz** — the error this document's own trap 2 warns against |
| C6 | "~7.3 s … NOT period-bound" | one of two 1000 ms runs cited; the other gives 5.5 s. n_treated = 1, treatment never verified as delivered |
| C7 | "2 of 5" | **2 of 6** |
| C8 | "the consumer fired exactly once" | 1 in one rendering run, **2** in the other |
| C9 | "53 responses … none applied" | **52** pre-control |
| C10 | trap 1 attributed the verdict to the boundary error | the corrected boundary returned **the same verdict**; neither is sound |

**Instrument defects, recorded because the artifacts stay in the tree**: the tick boundary is computed
against `fast-update-interval` on all three `:8053` runs; `LAND_WINDOW_S = 2.0` is calibrated on
round-trip rather than a measured **6.95 s** apply latency; all three post-fix runs ran `--no-control`
while two print "the instrument's own control failed"; and `2026-09-10_f035_fix_wiring_check.py` archives
nothing (and its "exactly one writer" assertion goes red once #614 lands).

**One charge cleared**: the `paths.strs` reader is not hiding duplicates — a live layout census finds zero
duplicate ids anywhere.
