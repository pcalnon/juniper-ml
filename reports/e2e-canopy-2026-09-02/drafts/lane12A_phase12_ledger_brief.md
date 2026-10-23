# Lane 12-A brief — Phase 12 of the canopy E2E ledger, round 1: artifact-first re-derivation

You are Lane 12-A, an independent validator under §2 (Lane A) of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. You have not seen any other
lane's brief or verdict. Your entry point is the **artifacts first**, the ledger second.

## What is under review

The ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` as frozen at local commit `c626e847`
(worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-growing-breeze`, branch
`docs/canopy-e2e-phase12`). The diff against `main` (`0e144c3c`) is `git diff 0e144c3c c626e847 -- notes/` run from
that worktree. It adds **Phase 12** at the end of the ledger (`grep -n '^## Phase 12'`) and changes the headers and
first Status bullets of **F-CANOPY-055**, **F-CANOPY-058** and **F-CANOPY-068** (`grep -n '^\*\*F-CANOPY-0\(55\|58\|68\) '`).

Phase 12 records canopy#731 (the request/ack pacer) as the fix of those three findings, merged 2026-10-09 and shipped
in canopy 0.9.0, and marks them FIXED. It was written on a host with no live service: every number in it is claimed
to be re-derived from archived files with archived readers.

## Your job

Re-create every measurement and source claim in Phase 12 and in the three new Status bullets from the artifacts, with
your own reading before you run the repo's readers, and report where the ledger is wrong. Specifically:

1. **The live census numbers** (Phase 12 § "The live checks, re-derived", the first table): the four transcripts in
   `reports/e2e-canopy-2026-09-02/pacer-live/f058-census-run{1,2,3-v2,4-final}.json`. Write your own reader of the
   request records (answered / evicted / still in flight, in-flight medians, p90, max, the gate's writes, the clamp
   episode, fires), then compare with `python3 -B util/ad-hoc/2026-10-04_f058_census_v2_analyze.py <file>`. Check
   the 912 / 845 / 0 totals and the "8 or 9 gate writes per run" claim.
2. **The status-bar census** (second table): the four `2026-10-08_status_bar_apply_census_*.json` files. Verdicts,
   watched/executed, latency changes, what the bar showed.
3. **The renderer check** (§ "The real renderer"): the three `*_score.json` files and `*_run.json` in
   `reports/e2e-canopy-2026-09-02/pacer-renderer-check/`. Every cell of the table, including the stranded-request
   timings and the ack-derived counts.
4. **The served code claims**: `2026-10-08_final_leg_health_2689a207.json`, `2026-10-08_final_leg_dash_dependencies_2689a207.json`
   (no `running=` guard; one Input per feeder; 179 callbacks), and the README's account of runs 1–3.
5. **The GitHub claims**: canopy#731's commits (eight; which five are signed; the three merges; the head), its merge
   time and merge commit `25c5c887`, its review threads; canopy's CHANGELOG `[0.9.0]` at `main` (dated 2026-10-10?
   does it name the three findings, the stale bound, the cost, the `[0.8.0]` correction?); the v0.9.0 Release
   (published 2026-10-17T19:45:37Z? target `bd001153`?); PyPI's current juniper-canopy version; juniper-ml#2196's merge
   (`0174c3dd`, 2026-10-09T02:36:55Z) and its file list. Use `gh api` / `gh pr view` / `gh release view` and
   `curl -s https://pypi.org/pypi/juniper-canopy/json`. Read canopy source only through
   `gh api repos/pcalnon/juniper-canopy/contents/<path>?ref=<sha> -H "Accept: application/vnd.github.raw"`.
6. **The design description** (§ "The design, as merged"): check it against the merged code at `25c5c887`
   (`src/frontend/dashboard_manager.py`, `src/canopy_constants.py`): the pacer's rule, `extra` and `stale` precedence,
   the stale bound formula and cap, `performance.now()`, state keyed by request store, `_PACED_POLLS`,
   `_setup_poll_pacers`, the modulus counting requests, `prevent_initial_call=False` on `update_metrics_store`.
7. **The triage**: `python3 -B util/ad-hoc/e2e_finding_triage.py` on the frozen ledger: 79 / 56 / 1 / 2 / 20, P1 4
   (which four), P2 16.
8. **The text-corrected list** (§ "The canopy text corrected"): does each named site exist, changed, in #731's diff?
   (`gh pr diff 731 --repo pcalnon/juniper-canopy`.)

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/D227803E-A1C2-4957-9A7C-824C3F8B44BD/scratchpad/lane12A/`
  (create it). Run Python with `-B`. Do not run any git command that changes state. Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- The ledger's style: a claim is wrong only if the artifact says otherwise. A rounding or wording difference that
  changes no number, disposition or action is a NIT.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 12-A** (artifact-first re-derivation, round 1)` and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`.
Then a **TABLE** of claims re-derived (claim | re-derived | result MATCH/MISMATCH/holds | evidence). Then **FINDINGS**,
numbered, each with severity (BLOCKER / MAJOR / MINOR / NIT), the ledger text quoted, your evidence, the fix, and the
line "Changes a number, disposition or action? yes/no". Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one
line. Keep it under 14,000 characters.
