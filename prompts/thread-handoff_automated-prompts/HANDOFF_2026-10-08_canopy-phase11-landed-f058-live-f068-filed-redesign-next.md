# HANDOFF 2026-10-08 — P2 canopy Lane A: Phase 11 recorded through six consensus rounds (F-CANOPY-058 observed live; F-CANOPY-068 filed); next is item 4, one redesign for F-CANOPY-055, -058 and -068

> **SUPERSEDED 2026-10-08** by `HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md`. Its items 1 (#2183
> merged) and 2 (canopy#731) are done; items 3–5 carry there.

**Written**: 2026-10-08 by the session in juniper-ml worktree `.claude/worktrees/dreamy-fluttering-kite`, at a phase
boundary, as its PR was opened. **Not consensus-validated.**
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (authoritative for P2;
its items 3 and 4, its owner batch (now O1–O17) and its P3 dependency carry this session's status). It supersedes
`HANDOFF_2026-10-05_canopy-phase10-five-rounds-pr-open-census-ran-live-phase11-owed.md`.
**Merge approval**: the owner granted it in this session for this session's PRs. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-phase11-landed-f058-live-f068-filed-redesign-next.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried, so ask before the first merge.

**Completed:**

- **Phase 11 of the ledger** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) went through six
  consensus rounds (2026-10-05 to 10-08). Round 6 changed no number, disposition or action, so the review ended.
  - **The census.** The repaired F-058 census (v2) ran live twice, about 25 minutes each, on verify legs on `:8052`
    serving canopy `main` `60ae1870` and `c7876f5a`. cascor was idle, and the trio was read but never written.
  - **F-CANOPY-058 (P1) is observed live.** 29 of 611 feeder requests were evicted, in eight runs of 1 to 11.
    - Every evicted request's late completion released the `running=` guard while its successor was in flight.
    - The longest run held the chart for 34.8 s, against a 4.9 s median cycle.
    - A re-enable evicts only if the in-flight response has not landed when the next request is made. That was
      1.2–2.4 s after a fire or gate write, and 1.4–2.6 s after a late release within a run.
    - The stalls of minutes stay synthetic.
  - **F-CANOPY-068 is filed**: the metrics-store strand watchdog's false fires.
    - It fired 28 times in two runs, 31–36 an hour, every time mid-fetch, with the lane enabled for 11.0–14.9 s of
      the 30 s before.
    - Its rating is "P1 if a CHANGELOG's description of an internal mechanism counts as documented, else P2".
      canopy's CHANGELOG `[0.8.0]` describes the watchdog as firing after the lane is "continuously disabled".
    - The cause is inferred to be aliasing: it samples every 5 s against a ~4.9 s cycle. An in-phase replay gives a
      median of 9 and 7 fires per run, against 1 when the phase is random.
    - It is a finding of its own, because each fix leaves the other in place.
  - **Counts**: 79 findings, 53 fixed, 1 accepted, 2 withdrawn, 23 open (0 P0, 7 P1, 16 P2).
  - **The owner's §6.3 question has two limbs.** First, Phase 10's: does a CHANGELOG or design-plan promise count as
    documented? That decides F-CANOPY-065. Second, if it does: does that extend to a CHANGELOG's description of an
    internal mechanism? That decides F-CANOPY-068. Moving those two alone, the open P1/P2 counts are 7/16, 6/17 or
    5/18.
  - **The first limb may reach further.** F-CANOPY-057, -018 and -012 are within its reach. canopy's own manual may
    make F-CANOPY-012 and F-CANOPY-013 P1 with no ruling at all (Matrix effect and counts; item 26).
  - **Where things are:**
    - evidence: `reports/e2e-canopy-2026-09-02/f058-census-v2/` (README first);
    - the census: `util/ad-hoc/2026-10-04_f058_census_v2_*`;
    - the readers: `util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py` (`--self-test`, five cases) and
      `util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py`;
    - each round's pass: `util/ad-hoc/2026-10-0{5,8}_phase11_ledger_round{1..6}_corrections.py`;
    - the reports: `reports/e2e-canopy-2026-09-02/consensus/2026-10-0{5,8}_validator_reports_phase11_round{1..6}.md`.
- **The Phase 11 PR** was opened from branch `docs/canopy-e2e-phase11` as signed commits. Find it with
  `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase11 --state all`. This file is in it.
- **CodeQL was handled before opening.** `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` predicts the alerts that
  block a merge.
  - `--known-answer` reproduces ml#2157's 20 threads exactly, and it reports nothing on Phase 10's 33 merged scripts.
  - It predicted 63 alerts in 54 of the 118 archived lane probes.
  - `util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py --round rN` fixed them. Each touched probe's header says
    so.
- **Phase 10's item 23 is done.** No P3 session was running, so F-CANOPY-063 is recorded under item 11 of
  `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` and in the INDEX's P2 ↔ P3 row.

**Remaining, in order:**

1. **Land the Phase 11 PR** if it has not merged.
   - Run `python3 util/wait_for_checks.py` against it.
   - Query `reviewThreads(isResolved:false)`, because the prescreen only predicts CodeQL.
   - Ask the owner.
   - Then run `python3 util/safe_merge.py --execute` and read its `MERGED` line.
2. **Item 4 (ledger item 0's second half, Phase 11's item 24): one design for F-CANOPY-055, -058 and -068.**
   - Lane B's request/ack pacer takes the watchdog off the guarded lane. A design that keeps a watchdog must base it
     on progress, such as `n_intervals` or a request count.
   - Phase 11's "Still owed" lists the canopy text to correct.
   - canopy's CHANGELOG `[0.8.0]` needs a correcting entry.
   - Tests:
     - a real-renderer test of 10 idle minutes on a healthy lane whose cycle is near 5 s;
     - live, on the fix's leg, two 25-minute census runs with the release trace, expecting no false fire and no
       eviction run.
   - Before those live runs, make both readers compare a push-order walk of the lane records with their type
     selection.
3. **Item 25: census triggers fired from the page.**
   - Schedule each trigger as its own task when the shim sees `AddWatched` (`setTimeout(…, 0)`).
   - Timestamp it in the page.
   - Validate the method on the synthetic check first.
   - Then test the gate, a tab switch, the end of an Apply (with the clamp defeat) and a second-Input change, each in
     mid-request.
4. **Item 26: the manual sweep, without waiting for the ruling.** Check every open finding against canopy's manual,
   F-CANOPY-012 and F-CANOPY-013 first. Then, once the owner rules, sweep against the CHANGELOG and the design plans.
   Whatever the ruling, the CAN-015g/h design note's "every CAN-015g item has merged" needs a dated correction.
5. Then the parent's items 5 and 7, and the owner batch, O1–O17. O17 is the two-limbed question.

**Traps learned:**

- **The census shim stamps a record when its dispatch is entered and pushes it after the dispatch returns.** So an
  enclosing record re-logs a nested change at an earlier time (median ~22 ms, at most 327 ms). Read the lane from
  innermost records only (types `''` and `SET_LAYOUT`).
- **Scripted Playwright triggers took effect 1.3–4.2 s after they fired.** `CLICK_TAB` stamps the time after the
  click's own handling, so the transcript cannot split the driver's delay from the page's.
- **A usage-limit stop kills background lanes mid-review.** Resume them with SendMessage to their agent id, which keeps
  their context, and archive with the resume message as the marker.
- **A lane's slip report can be wrong about itself.** Round 6 re-attributed a bytecode write by comparing file
  modification times against transcript timestamps. Re-derive before recording.
- **Each round found one more open finding within the ruling's reach.** End that regress by having the "owed" item
  cover the whole sweep, and by telling lanes that another candidate is a finding only where the ledger states
  something false about it.
- **The worktree guard refuses** `$(…)` inside git commands, heredocs that mention git, and `sed` with variables. Split
  such commands, or use the Edit tool.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase11 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 79 / 53 / 1 / 2 / 23; P1 7; P2 16
python3 -B util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json --self-test | tail -1
python3 -B util/ad-hoc/2026-10-05_codeql_python_prescreen.py --known-answer | tail -1
ss -ltnH | grep -E ':(8101|8202|8051|8052) '              # the trio up (never touch it); 8052 down
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase11` in worktree `dreamy-fluttering-kite`, rebased onto `main` `d3971e10`
  before the signed upload. Its PR is open; the verification commands give its number and state.
  - The ledger's freezes (`1b7cf44b`, `b3c54692`, `7af6a381`, `adcba49f`, `684d70bc` and `da08f639`) are local,
    unsigned, pre-rebase commits. No remote holds them.
  - Each round's pass replays its freeze's successor from its predecessor, byte for byte.
- **canopy, cascor and data:** no branches. canopy `main` was read at `60ae1870` and `c7876f5a`, from tarballs and its
  object store.
- **Services:** the verify leg is down. The trio (`:8051`, `:8101`, `:8202`) was never touched.

## Changed by this session

- **Created:**
  - this file;
  - `reports/e2e-canopy-2026-09-02/f058-census-v2/`: the README, the first run's files (`2026-10-05_RESULTS.md`
    verbatim, the transcript, the census and canopy logs, host load, the synthetic check's output) and `run2/`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round{1,2}.md` and
    `2026-10-08_validator_reports_phase11_round{3,4,5,6}.md`;
  - `reports/e2e-canopy-2026-09-02/drafts/lane11*_phase11_ledger*brief.md` (11 briefs);
  - in `util/ad-hoc/`:
    - the census, `2026-10-04_f058_census_v2_{shim,synth_app,synth_check,live,debug_probe,analyze}.py`;
    - the readers, `2026-10-05_f058_census_v2_release_trace.py` and `2026-10-05_f058_watchdog_alias_replay.py`;
    - the six passes, `2026-10-0{5,8}_phase11_ledger_round{1..6}_corrections.py`;
    - `2026-10-08_phase11_round3_rederive.py` and `2026-10-05_archive_phase11_lane_probes.py`;
    - `2026-10-05_codeql_python_prescreen.py` and `2026-10-05_phase11_probes_codeql_fixes.py`;
    - the 118 archived lane probes, `2026-10-0{5,8}_phase11_r{1..6}_*.py`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 11; F-CANOPY-058's header, trigger
    bullet and Status; F-CANOPY-065's header; Phase 9's correction note;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: items 3 and 4, O17, and the
    P3 dependency;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row
    and the P2 ↔ P3 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`: item 11;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-05_canopy-phase10-five-rounds-pr-open-census-ran-live-phase11-owed.md`:
    the SUPERSEDED banner.
- **Outside the repo**, in auto-memory: `MEMORY.md`, `reference_running_guard_released_by_evicted_completion.md`,
  `project_canopy_e2e_validation_arc_2026-08-08.md` and `reference_codeql_unused_global_cascor.md`.
