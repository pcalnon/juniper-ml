# Thread handoff — canopy E2E arc, Phase 8 closed: F-CANOPY-054 fixed (canopy#670), F-CANOPY-055 filed, the idle cuts measured but not yet a PR

**Written**: 2026-09-23, at a phase boundary. Canopy#670 had merged and the juniper-ml Phase 8 ledger PR had been
opened (see "State at handoff"). The thread had run long: one compaction had already happened, and three
review rounds had run.

---

## Goal statement (paste this as the new thread's first prompt)

Continue the canopy E2E validation arc from Phase 8 of the ledger,
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` ("Still owed after this phase").

**Completed in the 2026-09-23 thread:**

- **F-CANOPY-054 FIXED: canopy#670, merged 2026-09-23 16:25Z as `48074653`.** The replay block runs as ONE clientside
  callback that takes its events from values.
  - v1 `c0530279` → v2 `85415f3c` → v3 `a967a5bd` → text-only `683372b5`.
  - **Three review rounds**, archived verbatim in
    `reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_round{1,2,3}.md`:
    - round 1 refuted "a clientside callback cannot be evicted": a request waiting in `prioritized` is
      replaced by the next tick's request without its trigger;
    - round 2 found D1: v2's "a triggered button applies at least once" applied one click twice;
    - round 3 gave MERGE.
  - Evidence (all `util/ad-hoc/2026-09-23_f054_*`):
    - a paired contention clean room: v1 dropped 5, v2 held 48/48;
    - Lane B's clean room on v2 and v3: `double_pause` UNDONE 3/3 on v2, HELD 3/3 on v3;
    - Lane A2's independent harness: v1 0/5, v2 5/5;
    - live checks: 14/14 clicks during playback on v2 and on v3;
    - mutation check v3: 20/20 caught by behaviour.
- **F-CANOPY-055 FILED (P1, OPEN): the top status bar never applies.**
  - `update_unified_status_bar` rides the shared 1 Hz `fast-update-interval` with no `running=` guard, and
    every response is evicted. `2026-09-23_status_bar_apply_census.py` scored NEVER-APPLIES on two legs.
  - Its period arm (the lane at 20 s on the same page) APPLIES, and the bar reached the server's epoch 76.
  - Its 11 outputs include the Live Dataset Switch gate, so **F-CANOPY-025 is inferred regressed**.
- **Idle dispatch cuts measured; they are NOT yet a PR.**
  - Parking the 2 Hz weight drain cut the idle page's response latency L by about a third (two A/B runs,
    in opposite orders).
  - The dead 1 Hz metrics-panel timer is hygiene only.
  - The live check against a control: STRUCTURE PASS, SESSION PASS, X/C 0.76.
  - The branch is `perf/idle-dispatch-cuts` at local commit `668380ec`, built on `723ee812`.
- **dash 4.2.0's callback priority is INERT.** `getPriority` returns `"0"` for every callback: its first
  pass is `filter(c => touched)` (`dash_renderer.dev.js:1598`; `:1508` is `ramda/es/filter.js`), which drops
  its own start callback. So `prioritized` is FIFO. Found independently by Lanes A2 and B; the memory
  note `reference_dash_renderer_12_slot_starvation.md` is corrected.
- **The juniper-ml PR from branch `docs/canopy-e2e-phase8-f054-f055`** records all of it: the ledger's
  Phase 8, seven matrix rows moved to `85415f3c`, the scripts, transcripts and archives. Check it is
  merged: `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase8-f054-f055 --state all`.

**Remaining, in order:**

1. **Rebuild the cuts PR on `main`.**
   - Cherry-pick `668380ec` from the cuts worktree onto a fresh worktree of `main`.
   - The one-line snapshot `src/tests/regression/snapshots/metrics_panel.txt` WILL conflict. Regenerate
     it; do not hand-merge it.
   - Re-run `util/ad-hoc/2026-09-23_idle_cuts_live_check.py` with the control leg on `main` and the cuts
     leg on the new head.
   - Open it with `util/open_signed_pr.py`, then merge with `util/safe_merge.py`.
2. **Fix F-CANOPY-055** with F-035's pattern (the ledger's F-055 entry has the design):
   - a dedicated global interval for the feeder, with `running=`;
   - registered in `_GATED_POLL_INTERVALS` beside `metrics-store-interval`;
   - covered by #614's watchdog.

   F-027's objection to #657 does not apply, because this lane is not tab-gated. Verify with the census,
   its rule unchanged, and drive F-CANOPY-025's allow arm on a leg whose training may be started.
3. **Re-derive the starvation mechanism under FIFO** (still-owed item 12). F-027's "terminal renders lose
   arbitration" is refuted. Correct canopy's `dashboard_manager.py` comment once the mechanism is known.
4. **The rest of the ledger's still-owed list**:
   - F-053's latency regression hunt;
   - F-004's contract (owner);
   - `FULL_HISTORY_POLL_TICK_MODULUS`;
   - #613's guard;
   - F-049 and #674;
   - CAN-015's loop;
   - M-CANDIDATES-10/-11;
   - the replay-drives-no-chart owner question;
   - F1 (pause at the current index on a slider trigger equal to `slider_w`).
5. **`MEMORY.md` compaction.** It is ~26 KB against a 24.4 KB load limit, so the tail is cut off at load;
   the target is 20 KB. RETIRE entries into topic files; never strip hooks. Snapshot the link SET first
   and compare sets after, not counts.

**Key context:**

- **Consensus procedure:** `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
  Brief round N on the corrections only; freeze the artifact as a local commit and have lanes read git
  OBJECTS; archive per round with `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py` (a
  resumed agent appends to the same transcript).
- **canopy squashes with `COMMIT_MESSAGES`.** `safe_merge.py` sends no body, so the `Allow-Symbol-Loss`
  trailers survive. Never merge with a custom body.
- **Before landing, check `auto_merge` on your own PR.** On 2026-09-23, #670 was found armed at 13:18:44Z
  under the `pcalnon` account, by no command in this session, carrying v1's stored body. It was disarmed.
- **The worktree shell guard refuses `$(...)`, xargs, computed sed/awk and `cd X && git`.** Use plain
  `git -C <path> …`, and pass file lists literally.
- **`/tmp` inode exhaustion.**
  - At 98% on 2026-09-23. Three other sessions' scratch dirs held ~655k inodes: `798c2868…` (412k),
    `b71ebef9…` (155k), `ca1055b2…` (88k).
  - It crashed a reviewer's Chromium twice. A redrive page logged `net::ERR_INSUFFICIENT_RESOURCES` at load.
  - Check it with `df -i /tmp` before any browser run.

## Verification commands (run first)

```bash
gh api repos/pcalnon/juniper-canopy/pulls/670 --jq '{merged, merge_commit_sha}'
python3 util/ad-hoc/e2e_finding_triage.py | tail -8      # 66 findings; 15 open; P1: F-CANOPY-055, F-CASCOR-001, F-CASCOR-002
curl -s http://127.0.0.1:8055/v1/health | python3 -c "import json,sys; print(json.load(sys.stdin)['git_sha'][:8])"   # a967a5bd (v3) until taken down
curl -s http://127.0.0.1:8056/v1/health | python3 -c "import json,sys; print(json.load(sys.stdin)['git_sha'][:8])"   # 668380ec (the cuts)
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--perf--idle-dispatch-cuts--20260923-0830--723ee812 log --oneline -1   # 668380ec
df -i /tmp | tail -1
```

## State at handoff

- **juniper-ml:** session worktree `.claude/worktrees/partitioned-twirling-stream`, branch
  `worktree-partitioned-twirling-stream`, based on `main` `91da4b0e`. The Phase 8 PR was opened from
  `docs/canopy-e2e-phase8-f054-f055` through the signed-commit API.
- **canopy worktrees:**
  - `juniper-canopy--fix--f054-replay-block-clientside--20260923-0036--2f973ca2` (#670, merged): clean
    it up per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`, and only on the merge signal.
  - `juniper-canopy--perf--idle-dispatch-cuts--20260923-0830--723ee812`: local commit `668380ec`, never
    pushed. KEEP it.
- **Legs:** `:8055` serves `a967a5bd` and `:8056` serves `668380ec`. Take them down with
  `bash util/ad-hoc/2026-09-04_canopy_verify_instance.bash down <port>` when no longer needed. The trio
  (`:8101` data, `:8202` cascor fixture 2/68/2) is untouched and must stay so. Never touch `:8051`.
