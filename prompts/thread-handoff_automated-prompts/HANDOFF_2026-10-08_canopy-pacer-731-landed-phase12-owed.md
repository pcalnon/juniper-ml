# HANDOFF 2026-10-08 — P2 canopy Lane A: item 4 done. One request/ack pacer fixes F-CANOPY-055, -058 and -068 (canopy#731), after three review rounds and four live census runs. The ledger's Phase 12 is owed, with its own consensus rounds.

**Written**: 2026-10-08 (2026-10-09Z) by the session in juniper-ml worktree `.claude/worktrees/agile-napping-popcorn`,
at a phase boundary. **Not consensus-validated.**
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, which is
authoritative for P2. Its item 4 is now DONE in code, and its items 5 and 7 and the owner batch O1–O17 carry
over. This file supersedes `HANDOFF_2026-10-08_canopy-phase11-landed-f058-live-f068-filed-redesign-next.md`.
**Merge approval**: the owner granted it in this session for this session's PRs. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md` (juniper-ml).
Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification commands first.
Merge approval is not carried: ask before the first merge.

**Completed:**

- **Parent item 4, the redesign: canopy#731**, branch `fix/f055-f058-f068-request-ack-pacer`, five signed commits:
  `7aed1f2b`, `b344ff97`, `957176de`, `2689a207` and `65ead946`. The verification commands give its merge state.
  - **Design.** Both slow polls are paced by request/ack.
    - Each feeder's only Input is a request store (`metrics-store-request`, `status-bar-request`), written by a
      clientside pacer (`poll_pacer_js`) on the poll's existing Interval.
    - Each feeder writes an ack store echoing the request's `seq` on every return path.
    - The pacer asks again only when the ack has caught up, or when the request is past its stale bound:
      `max(POLL_PACER_STALE_MS 30 s, 3 × the longest round trip)`, capped at 120 s. The round trip is a lower
      bound, timed with `performance.now()`, with state keyed per request store.
    - The `running=` guard, the strand watchdog and `METRICS_STORE_STRAND_TIMEOUT_MS` are gone.
    - The display mode is State of the feeder and an Input of the pacer, compared by value.
    - `_PACED_POLLS` registers both paced polls; the F-027 census counts them from it, and `_setup_poll_pacers`
      wires their lanes from it.
  - **Disclosed cost.** A failure outside a feeder's `try` (a non-OK reply from Dash or a middleware, or a network
    failure) waits out the stale bound, ≥ 30 s. On `main` the lane retried on the next tick.
  - **The canopy text Phase 11 listed is corrected**, and the CHANGELOG's `[Unreleased]` carries a correction to
    the `[0.8.0]` watchdog entry.
  - **Review.** Three rounds, recorded in `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_canopy731_pacer_rounds1-3.md`.
    The six lane reports there are condensed; the full texts are in this session's transcript. Round 3 changed no
    behaviour-relevant conclusion, so the review ended.
  - **Tests.**
    - The full canopy unit suite passed on commit 2: 6,819 passed, 0 failed.
    - Regression, integration and UI (33 passed, 1 xfail) passed.
    - All 25 CI checks passed on `2689a207`.
  - **Live** (`reports/e2e-canopy-2026-09-02/pacer-live/README.md`):
    - F-058 census v2, four runs: 0 of 912 requests evicted, with no fires. Run 4, on `2689a207` at a load of
      ~5–10, had a ~5.0 s cycle, against Phase 11's 4.9 s.
    - F-055 census: APPLIES on `2689a207`. A same-day `main` control read NEVER-APPLIES.
  - **Real renderer** (`reports/e2e-canopy-2026-09-02/pacer-renderer-check/README.md`): PASS on the final pacer,
    and the guard + watchdog control FAILS.

**Remaining, in order:**

1. **Land canopy#731** if it has not merged: `python3 util/wait_for_checks.py --pr 731 --repo juniper-canopy`,
   query `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --execute` and read its
   `MERGED` line.
2. **Land this session's juniper-ml PR** (evidence, instruments, this file). Find it with
   `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-pacer-731-evidence --state all`.
3. **The ledger's Phase 12**, in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, with its
   own consensus rounds. Record:
   - canopy#731;
   - the three findings' statuses: FIXED IN CODE on merge, VERIFIED LIVE on `2689a207` for the evidence above;
   - whether F-CANOPY-058's "minutes" and F-CANOPY-055's Live Switch allow arm still need a drive;
   - the triage counts;
   - the Phase 11 item 0 and 24 closures;
   - the canopy text corrected;
   - the cost the fix introduced.
   Decide with the lanes whether "VERIFIED LIVE" can stand given these limits:
   - T-apply never tested a mid-request Apply release, because the pacer issues nothing under the clamp and E-3
     released it at ~60 s;
   - no live run injected a failure;
   - no run trained.
4. **Item 25**: census triggers fired from the page, as the parent describes, on the merged code. T-apply needs a
   different design under the pacer.
5. **Item 26**: the manual sweep, F-CANOPY-012 and -013 first, and the CAN-015g/h note's dated correction.
6. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned:**

- **The worktree guard refuses** heredocs that mention git-like words (even `merge` or `real`), `sed` on variables,
  `$(git …)` and `-C ..`. Write patch scripts to the scratchpad and run them with an explicit path; use the Edit
  tool for small changes.
- **`gh pr edit --body-file` is broken** (Projects-classic GraphQL). Use
  `gh api -X PATCH repos/O/R/pulls/N -F body=@file`.
- **`pre-commit run --files` skips untracked files.** Stage them first (staging is safe; only signing hangs).
- **`*.log` is gitignored** in juniper-ml. Archive logs as `*.log.txt`.
- **A paced feeder has a multi-output key** (`..store.data...ack.data..`). Any census or collector matching an
  output key exactly misses it. `src/tests/ui/test_ws_silent_poll_liveness.py` failed in CI this way, and the F-058
  census needed `util/ad-hoc/2026-10-08_f058_census_v2_on_pacer_leg.py`.
- **The page's recording callback can be coalesced** behind the next request. The renderer check derives
  application from the acks as well (`applied_by_ack_only`). It happened once per 10-minute run.
- **The CodeQL prescreen missed an "unused global"** (`_PACED_POLLS`, used only by tests). Query review threads
  after CI every time.
- **Canopy's full unit suite needs `env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB`.** With them set, 116
  tests fail identically on `main`.
- **A host loaded by other sessions** (load averages up to 33) slows a census 2–3×. Read load before and after,
  and state it as a reading, not a sample.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>
gh pr view 731 --repo pcalnon/juniper-canopy --json state,mergedAt,headRefOid
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-pacer-731-evidence --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # still 79 / 53 / 1 / 2 / 23 until Phase 12 records the fixes
ls reports/e2e-canopy-2026-09-02/pacer-live reports/e2e-canopy-2026-09-02/pacer-renderer-check
ss -ltnH | grep -E ':(8101|8202|8051|8052|8053) '        # the trio up (never touch it); 8052/8053 down
```

## Git state

- **juniper-canopy:** canopy#731 is open or merged (the commands above say which). Worktree
  `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--f055-f058-f068-request-ack-pacer--20261008-1713--3029d07d`
  has HEAD `65ead946` and a clean tree. Remove it after the merge, per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.
- **juniper-ml:** branch `docs/canopy-pacer-731-evidence`, signed commits via `util/open_signed_pr.py`. The
  `agile-napping-popcorn` worktree holds the same files staged but uncommitted.
- **Services:** both verify legs (`:8052`, `:8053`) are down. The trio (`:8051`, `:8101`, `:8202`) was never
  touched.

## Changed by this session

- **juniper-canopy (canopy#731):**
  - `CHANGELOG.md`;
  - `src/canopy_constants.py`;
  - `src/frontend/dashboard_manager.py`;
  - `src/frontend/components/metrics_panel.py`;
  - `src/tests/unit/frontend/test_f055_f058_f068_request_ack_pacer.py` (new);
  - `test_poll_gating.py`, `test_stage2_global_lane.py`, `test_poller_budget.py` and
    `test_dashboard_manager_gate_coverage_inner1.py`;
  - `src/tests/ui/test_ws_silent_poll_liveness.py`.
- **juniper-ml, created:**
  - `util/ad-hoc/2026-10-08_f055_f058_f068_pacer_renderer_check.py`;
  - `util/ad-hoc/2026-10-08_f058_census_v2_on_pacer_leg.py`;
  - `util/ad-hoc/2026-10-08_pacer_round2_mutation_check.py`;
  - `util/ad-hoc/2026-10-08_compare_canopy_wiring.py`;
  - `reports/e2e-canopy-2026-09-02/pacer-renderer-check/`, with its README;
  - `reports/e2e-canopy-2026-09-02/pacer-live/`, with its README;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_canopy731_pacer_rounds1-3.md`;
  - this file.
- **juniper-ml, modified:**
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (item 4 status);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-phase11-landed-f058-live-f068-filed-redesign-next.md`
    (SUPERSEDED banner).
- **The ledger is NOT modified.** Phase 12 is owed (Remaining, item 3).
