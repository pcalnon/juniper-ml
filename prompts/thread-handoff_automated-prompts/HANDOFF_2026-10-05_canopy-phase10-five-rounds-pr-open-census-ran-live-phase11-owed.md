# HANDOFF 2026-10-05 — P2 canopy Lane A: Phase 10 landed through five consensus rounds (PR opened from `docs/canopy-e2e-phase10`); the F-058 census v2 ran live; recording it as Phase 11 is owed

> **SUPERSEDED 2026-10-08** by `HANDOFF_2026-10-08_canopy-phase11-landed-f058-live-f068-filed-redesign-next.md`, which the
> session in worktree `dreamy-fluttering-kite` wrote after finishing this file's item 2 (Phase 11, six consensus rounds).
> Phase 11 corrected three of this file's figures for the first census run, so trust the ledger, not this file:
> - the lane "disabled 0.3–2.0 s" at a fire;
> - "3" fires cascading;
> - the triggers "1.3–3.4 s late through the renderer queue".

**Written**: 2026-10-05 by the session in juniper-ml worktree `.claude/worktrees/clever-juggling-spring`, at a phase
boundary, before its PR was opened. **Not consensus-validated.**
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (authoritative for P2;
its items 2 and 3 now carry this session's status). It supersedes
`HANDOFF_2026-10-04_canopy-phase10-round3-fix-pass-owed-then-land-census-v2-ready.md`.
**Merge approval**: the owner granted it in this session for this session's PRs. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-05_canopy-phase10-five-rounds-pr-open-census-ran-live-phase11-owed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried, so ask before the first merge.

**Completed:**

- **Phase 10 of the ledger** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) went through five
  consensus rounds. Round 5 changed no number, disposition or action, so the review ended there.
  - Rounds 3 to 5 restated F-CANOPY-067 as "P2 pending a live drive". By source its zeros persist in the Full History
    and Between Hidden Units views, which would make it P1.
  - Item 18's drives were rebuilt so they can show persistence: unfixed `main`, the recurrence leg up, a second page
    held in Full History, canopy restarts checked in canopy's log.
  - F-CANOPY-064's Phase 1 capture holds one mostly hidden Accuracy marker. W1-09 stays FAIL.
  - Counts: 78 findings, 53 fixed, 1 accepted, 2 withdrawn, 22 open (0 P0, 6 P1, 16 P2).
  - Each correction pass is a replayable script, `util/ad-hoc/2026-10-04_phase10_ledger_round{1..5}_corrections.py`.
    Rounds 3 to 5 write their own Consensus records. The reports are in
    `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round{1..5}.md`.
- **The Phase 10 PR** was opened from branch `docs/canopy-e2e-phase10` (signed commits through
  `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py`). Find it with `gh pr list --head docs/canopy-e2e-phase10
  --state all`. This file is in it.
- **The F-058 census v2 ran live**, on a verify leg on `:8052` (canopy `main` `60ae1870`, idle cascor, about 25 min),
  after its synthetic check passed 6 of 6 under its final file names.
  - The strand watchdog fired FALSELY 13 times, about 31 an hour. At each fire the lane had been disabled 0.3–2.0 s,
    against its 30 s threshold. The cause is aliasing: it samples every 5 s while the feeder cycles every ~4.9 s.
  - Each false fire re-enabled the lane mid-request. 3 of them started eviction cascades of 2, 11 and 4 lost
    responses, each ending by itself. 18 of 307 responses were evicted; one was at page load, by the gate's mount
    write.
  - The scripted triggers landed 1.3–3.4 s late, through the renderer's queue, so they did not test the claim.
  - Everything is OUTSIDE the repo, in `/home/pcalnon/Development/python/Juniper/backups/2026-10-05_f058_census_v2_final/`:
    the six scripts `2026-10-04_f058_census_v2_{shim,synth_app,synth_check,live,debug_probe,analyze}.py`, and in
    `run/` the transcript (`2026-10-05_census_live.json`), the run log, the leg's log, host load, the synthetic
    check's output and `2026-10-05_RESULTS.md`. Read the results note first.
- **MEMORY.md was back under the load limit**: 25,695 → 24,880 characters (`util/ad-hoc/2026-10-05_memory_index_compaction.py`).
  It still sits close to the ~25,000-character limit.

**Remaining, in order:**

1. **Land the Phase 10 PR** if it has not merged. Run `python3 util/wait_for_checks.py` against it, ask the owner,
   then run `python3 util/safe_merge.py --execute` and read its `MERGED` line, not its exit code. The owner's sweeper
   may arm or merge it unseen, so check its state first.
2. **Phase 11: record the census.** On a fresh branch from `main`:
   - copy the six scripts into `util/ad-hoc/`;
   - put the run artifacts under `reports/e2e-canopy-2026-09-02/` (for example `f058-census-v2/`), with
     `RESULTS.md` as the evidence README;
   - write the ledger's Phase 11 (F-CANOPY-058 confirmed live, with the watchdog's false fires as the trigger),
     and decide whether those false fires are a new finding (F-CANOPY-068?) or part of F-CANOPY-058;
   - run consensus rounds until one changes nothing, then open a PR.
   - The live script's `--adhoc-dir` defaults to its own directory, which is right once it is in `util/ad-hoc/`.
3. **Item 4, the F-CANOPY-055 + F-CANOPY-058 redesign.** It must account for the watchdog's sampling, not only for
   the `running=` guard.
4. Then items 5 and 7 and the owner batch O2–O16, from the parent. New owner question: does a shipped CHANGELOG or
   design-plan promise count as "documented" under plan §6.3? If it does not, F-CANOPY-065 becomes P2. Phase 10's
   Still owed item 23: tell the defect-register arc that F-CANOPY-063 is its "Nothing was loaded" id.

**Traps learned:**

- **A scripted Dash trigger reaches the page 1.3–3.4 s late,** through the renderer's queue (FIFO). Fire a census
  trigger when a request enters `watched`. Score it as "a re-enable while a request is in flight, whose response
  lands after the next request enters", not inside a fixed horizon.
- **The welcome modal intercepts clicks.** Run `e2e_f027_redrive.ensure_no_modal` first, then click tabs with a DOM
  click. `open_tab` waits 3.5 s, which spoils any timing.
- **A dated `util/ad-hoc` file cannot be imported.** Load it by path and register it in `sys.modules` first.
- **A verify leg from a tarball tree needs `JUNIPER_CANOPY_GIT_SHA`.** Read the served SHA back off `/v1/health`.
  The trio's cascor refuses the leg's control stream by origin; that is expected.
- **`pre-commit run --files` skips untracked files.** Stage them, then run plain `pre-commit run`.
- **The worktree guard refuses** `sed` with variable arguments, `$(…)` inside compound git commands, and loops.
  Split such commands, or use the Read tool.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase10 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 78 / 53 / 1 / 2 / 22; P1 6; P2 16
ls /home/pcalnon/Development/python/Juniper/backups/2026-10-05_f058_census_v2_final/run/
ss -ltnH | grep -E ':(8101|8202|8051|8052) '              # the trio up (never touch it); 8052 down
wc -m ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md
```

## Git state

- juniper-ml: branch `docs/canopy-e2e-phase10` in worktree `clever-juggling-spring`. Its PR is open; see the
  verification commands for its number and state.
- canopy, cascor and data: no branches. They were read at the pins `1b2dd438`, `95cdc562` and `29be6d35`, and canopy
  `main` `60ae1870` was read from a tarball for the census.
- The verify leg is down. The trio (`:8051`, `:8101`, `:8202`) was never touched.

## Changed by this session (since the 10-04 handoff)

- **Created:**
  - this file;
  - `util/ad-hoc/2026-10-04_phase10_ledger_round{3,4,5}_corrections.py`;
  - `util/ad-hoc/2026-10-05_memory_index_compaction.py`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round{3,4,5}.md`;
  - `reports/e2e-canopy-2026-09-02/drafts/lane10R{4,5}_phase10_ledger_brief.md`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (items 2 and 3);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` (the P2 row);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_canopy-phase10-round3-fix-pass-owed-then-land-census-v2-ready.md`
    (SUPERSEDED banner).
- **Outside the repo:**
  - `backups/2026-10-05_f058_census_v2_final/` (the census, above);
  - auto-memory: `MEMORY.md`, `project_canopy_ws_badge_red_herring_2026-05-10.md` (SUPERSEDED banner),
    `reference_fork_drift_gate_cannot_express_canopy.md` and `project_duplicati_yamaguchi_arc_2026-09-08.md` (a fact
    each, moved from the index).
