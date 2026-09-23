# CI-budget re-evaluation -- consensus round 2, Lane B -- find what the round-1 fixes broke

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `d873aed6`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

**Round 2, Lane B: review of the round-1 corrections on ml#2017 (`53d05121..d873aed6`)**

The corrections introduced a failing check and several new errors, so all three areas need at least one fix before merge (verdicts at the end). Paths below are relative to `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/`, whose tracked files match `d873aed6`. "Handoff" means `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`.

**What passes:** `tests/test_wait_for_checks.py` plus `tests/test_safe_merge.py` (124 tests, OK). The mutation check kills 6 of 6 mutations. The `waiter`, `settings` and `structure` probes exit 0. The suites that read `ci.yml` and the lockfile workflow pass. The new warning title is valid (no `,`, `:`, `%` or line breaks), and nothing parses it.

### Findings, most severe first

1. **[Med] Correction (h) made the PR fail a check.**
   - `Verify AGENTS.md Last Updated` fails on `d873aed6` (job 106974402254): *"changes AGENTS.md but does not bump '**Last Updated**:' (still 2026-09-21)"*.
   - `53d05121` never touched `AGENTS.md`; the 165→166 edit did.
   - It is not one of the 17 required contexts and Quality Gate is green, so it doesn't block the merge.
   - **Fix:** set `**Last Updated**: 2026-09-22`.

2. **[Med] Three documents disagree about the independent reproduction (the procedure's only de-escalator).**
   - `docs/REFERENCE.md:3291` says it "reproduced every row". `tests/test_safe_merge.py:38` says "all eight rows exactly". Handoff:570 says 8 of 9 repos, with juniper-ml the one that didn't match.
   - The handoff is right. Lane A2's committed evidence (`laneA2/lane_a2_evidence.json`, window #1982..#2016) reads ml 857/1061. My offline replay of `first_pass_of` on A2's cache matches every pinned row except ml.
   - The "p90 733" in `tests/test_safe_merge.py:53` and `util/safe_merge.py:307` appears in no committed evidence; A2 reads 857.
   - `tests/test_safe_merge.py:67` still says cascor-client had "28 clean heads"; `safe_merge.py` and the handoff say 30 healthy.
   - **Fix:** use one wording everywhere ("7 of 8 pinned rows; ml's window had moved"), and either cite the run behind 733 or use 857.

3. **[Med] Each side of the dissent has an unsupported premise, and OWNER DECISION 2 leans toward HOLD.**
   - "Every re-measure so far has only raised budgets" (`util/safe_merge.py:251`, handoff:85) is false by the file's own history. The 2026-09-08 fleet re-measure (#1828, `b26acd62`) lowered deploy and recurrence from the 2400 s default to 700 (`safe_merge.py:228-229`). Recurrence then needed 2000 the next day (#1851). That counterexample matters to the decision and is left out.
   - "That paragraph was narrowed on 2026-09-10 to PRE-start queue" (`safe_merge.py:247`): #1880 (`db627616`) did not edit that paragraph; it withdrew the ml entry's justification. It should be stated as an interpretation.
   - OWNER DECISION 2 (handoff:77-88) gives HOLD five quantified premises and SHIP only "the enforced rule and the precedent".
     - It omits the scope argument that `safe_merge.py` does record.
     - It omits the cost of HOLD: under the old budgets those three healthy PRs are refused, and the MERGING block says a refusal disarms the net.
     - No option says "keep the raises as shipped".

4. **[Med] The rewritten `waiter` probe still cannot tell the fixed CLI from the unfixed one.**
   - It calls `resolve_timeout()` directly and never goes through the CLI.
   - With `main()` reverted to the flat default (`round2-laneB/r2b_waiter_probe_mutation.py`), `probe waiter` exits 0 with "==" on all 10 rows.
   - So its printed line "could it read differently? yes -- a CLI still waiting a flat constant prints the same seconds…" is false. `TimeoutResolutionTest` does catch this mutation, so the code is fine; the probe's claim and the handoff's citation of it as evidence are not.
   - **Fix:** run `waiter.main([..., "--json"])` with `wait_for` stubbed, and read `timeout_source`.

5. **[Med-Low] `ci.yml` still tells readers the recipe this PR corrects.**
   - `ci.yml:1704` is the job-summary line every soak run prints: *"Promotion is a ruleset change, not a `needs:` edit."* A ruleset-only promotion is exactly the check that can never fail.
   - `ci.yml:1712` says the exit code "never left the log". But `ci.yml:1698` has written ``exit `${rc}` `` to the job summary all along; it only never reached the annotation.
   - `ci.yml:1626` says "THE SOAK HAS SINCE CONTRADICTED THE BACKTEST". Handoff:616 says "The 2026-09-16 backtest is not contradicted", from the same facts.

6. **[Low-Med] "5 got no `pull_request` run at all" is false for #1139, and the claim appears in five places** (the workflow header, the walkthrough, REFERENCE, the runbook, handoff:506).
   - #1139's opening commit `ea30c105` had no run. The owner's merge-main commit `5d343118` (2026-08-18) got two successful `pull_request` runs.
   - The claim is only true at opening, because the probe reads `commits[0]` only.
   - #1139 was released a third way (a push), which the release accounting doesn't mention. Evidence: `r2b_lockfile_norun_check.py`.

7. **[Low, not yet triggered] `first-pass` defects that would all lower a measured max.** None affect today's 270 heads: in the offline replay, only canopy#627 differs, by 1 s. But NON-OWNER 2 makes this the tool for future re-measures.
   - **Statuses fallback** (reprobe:352-354) adds one "execution" per status record, while its comment promises one per context. In `r2b_status_fallback_demo.py`, a pending-then-success status reads as unhealthy "=pending", with a 600 s span instead of the true 1200 s.
   - **Earliest vs newest.** It keeps the earliest-started run of each check; the waiter keeps the newest (`wait_for_checks.classify` `_recency`). A first run cancelled by concurrency and replaced by a success therefore gets its head dropped.
   - **No coverage guard.** A head missing required contexts is scored on a shorter span, and there is no minimum sample size. A2 checks both.
   - **`started_at=None`** runs are skipped, which promotes a later run to "first".

8. **[Low-Med] The `--json` guard misses the most likely mistake.**
   - If `$S` is unset, `/reprobe.json` passes the directory check, then the final write fails with PermissionError and exit 1. I reproduced this with the `waiter` probe; with `all` it would happen after about 2,500 API calls.
   - Handoff:56 says "the script refuses a missing one".
   - The preflight also omits `--fetch`, so `slack` reports UNMEASURABLE whenever a sibling repo's `origin/main` is stale.

9. **[Low] The alarm probe's "OK" also covers runs that measured nothing.**
   - It reads "OK" whenever the Slack step was skipped. That also happens when `gh pr list` failed (`pr-budget-alarm.yml:98-99` sets level=OK) or an earlier step failed.
   - It fetches only 50 runs with no pagination, and juniper-ml already has 54, so "every run's breach level" is false.
   - The "no breach since 09-17" conclusion still holds: in another lane's census, 0 of 94 OK runs were non-measurements.
   - "The one signal that works" (handoff:74) overclaims; the `level=` log line and the step summary also work without the webhook.

10. **[Low] Minor wording and provenance issues.**
    - Handoff:585, "7 of the 56 merges": the 56 are PRs examined, and #2004, #2012, #2013, #2015 and #2017 are open.
    - Handoff:613, "No false negatives found", describes a search for damage outside C1-C4, not missed C1-C4 findings.
    - The queue share is described as "no required job running" (`safe_merge.py:241`, `tests/test_safe_merge.py:602`, handoff:543), but `span_decompose.py` counts every job on the head.
    - `laneA2/queue_share.py` only works from a cache hard-coded to this session's `/tmp` scratchpad (`span_all_attempts.py:72`), so the 91-99% figures can't be reproduced after the session. I re-ran it from the cache and they match.
    - The ml rule "a window edge moving is not evidence…" is applied to one row only; this PR lowered the cascor (2561→2221) and canopy (2370→2174) pinned maxima by exactly a window move.
    - No mutation covers the `sys.modules` registration. Popping it in `finally` is safe.

### Round-1 findings that are lost or unresolved
- **Lost:** `util/ad-hoc/watch_prs_until_terminal.bash:53` still uses a flat 2400 s timeout, below 6 of the 9 budgets. No document mentions it.
- **Unresolved:** the backtest date (09-16 in `ci.yml:1618` and handoff:616, while the walkthrough is dated 09-17).
- **Not recorded:** the #1806 same-second close/reopen ambiguity. Handoff:508 now states it flatly.
- **Recorded properly:** release-train.yml, the budgets at the ceiling, and #1983. The 22%/15% estimate is gone, replaced by finding 10's denominator error.
- Handoff:769 still says round 2 is "in progress" and must be filled in before merge.

### Verdicts
- **Code:** SHIP `util/wait_for_checks.py` and `util/safe_merge.py`. FIX-FIRST the reprobe script (findings 4, 7's statuses fallback, and 8).
- **CI:** FIX-FIRST findings 1 and 5; each is about a one-line change.
- **Docs:** FIX-FIRST findings 2, 3 and 6, plus the round-2 placeholder.

**Changed:** no tracked files. I created six untracked scripts in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round2-laneB/`:
- `r2b_first_pass_offline.py`
- `r2b_waiter_probe_mutation.py`
- `r2b_status_fallback_demo.py`
- `r2b_lockfile_norun_check.py`
- `r2b_alarm_ok_audit.py`
- `r2b_soak_denominator.py`
