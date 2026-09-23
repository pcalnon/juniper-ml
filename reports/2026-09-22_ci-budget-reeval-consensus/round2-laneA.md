# CI-budget re-evaluation -- consensus round 2, Lane A -- re-derive the new figures

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `d873aed6`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

**Round 2, Lane A: ml#2017 at `d873aed6`**

I re-derived all five items with my own scripts. I did not run the reprobe, and I edited no tracked file. Most of the corrections hold. I found two major defects and five minor ones. Nothing changes a budget or an owner decision. The run used about 395 REST calls and about 60 GraphQL calls.

### 1. Lockfile census: confirmed, except one overstatement
Route: GraphQL PRs by head branch plus force-push events, the REST run list for the branch (90 runs), and each opening run's attempt 1 and its job count.
- 19 PRs. 18 opened by `github-actions` (#325–#1932), and #1970 by `juniper-release-train`. ✓
- 13 parked. `r2a_lockfile_attempt1.py` → `{('action_required',): 12, ('failure',): 1}`, every one with 0 jobs. #1806 flipped to `failure` at 13:59:38Z, the second it was reopened. ✓
- 12 were released by attempt 2 with `triggering_actor=pcalnon`, which then ran 1–18 jobs. #1806 was released by close/reopen. ✓
- #1970's five opening runs ran jobs on attempt 1 (counts `[1,19,1,1,1]`), all as `juniper-release-train[bot]`. ✓
- **#1139 is wrong as worded.** Its opening commit got no run: `runs?head_sha=ea30c105…` → `{"runs":[],"total":0}`. But the owner's merge-from-main push `5d343118` (2026-08-18 21:43Z) got two successful `pull_request` runs. So "no `pull_request` run at all" is true of 4 PRs, not 5.
- Could this have read differently? Yes: #1970 shows jobs, so the check can tell parked from executed.

### 2. Soak census: confirmed, except the PR count
Route: PR-first. GraphQL took 70 PRs → 212 commits (including force-pushed ones) → Actions check suites → the soak job; logs came from REST. It found all 199 CI runs the REST list shows since 00:37:10Z, so the enumeration is complete.
- **At the census point** (between 20:45Z and 21:22Z):
  - runs, logs and files: 191 runs; 12 unreadable, all cancelled, each followed within 10 min by a newer run on the same PR; 17 with no markdown changed; 162 examined 367 files. ✓
  - findings: 30 runs flagged, 9 distinct findings, exactly the claimed 2 true and 7 false. ✓
  - flagged at the final head: exactly #1969, #1973, #1976, #1980, #1983, #1992, #2007, #2009. ✓
- **57 PRs, not 56.** #1971 was closed without merging and had 2 examined runs. `commits/c76098b9…/pulls` and `commits/f53aba46…/pulls` both return `[]`, so the reprobe's way of finding PRs cannot see it.
- **"7 of the 56 merges" counts PRs as merges.** Of the 57 PRs, 50 are merged, 6 are open (#2004, #2012, #2013, #2015, #2017, #2020) and 1 is closed.
- **Now** (about 23:15Z): 199 runs, 13 unreadable, 19 idle, 167 examined, 381 files, 59 PRs, still 30 flagged. The 8 new runs were created 21:22Z–23:14Z and none has findings. Two of them predate 21:40Z, so the census was taken before 21:22Z.
- The comma claim holds: the annotation on check-run 106257046490 is titled `Markdown structure C1-C4 (advisory`.

### 3. Alarm: confirmed
- `pr-budget-alarm.yml` is on the default branch of all nine repos. The Slack step's condition, `if: steps.count.outputs.level != 'OK'`, is the same everywhere. The siblings differ from ml only by the louder warning inside that step, and ml's file has not changed since `a34a31a8`.
- Since 09-17: 6 scheduled runs per repo, 0 breaches.
- ml's full history: 54 runs, with 8 breaches on 08-06, 08-07, 08-25, 08-27, 08-28, 08-29, 09-04 and 09-05. ✓ `SLACK_WEBHOOK_URL` is set on ml only. ✓
- One weakness: when the PR query fails, the count step writes `level=OK`, so a skipped Slack step can also mean "query failed". I checked annotations and no run has "Could not list open PRs". The annotation read does work, because it picked up the runner's NOTICE annotations.

### 5. Spans: confirmed
Route: GraphQL check suites (all check-runs, not just the latest), required contexts from `rules/branches/main`, and only PRs merged before 21:40Z.
- cascor: 24 required contexts, 29 healthy heads (#647 unhealthy, first pass 379 s). The sorted tail is `[1615, 1717, 1735, 1743, 2221]`, so p90 = 1717 and max = 2221 (#660).
- Margins: recurrence 2000 − 1666 = 334 s (#152) is thinner than cascor-worker 2400 − 2059 = 341 s (#183). ✓
- **All nine rows reproduce exactly.** ml's row reproduces on the window as it stood at census time, #1981–#2014. The later readings (857, 1061) and then (733, 1061) also reproduce.
- My read of the latest check-run per workflow run reproduces canopy's 33,299 s and recurrence's 9,886 s, so this route would have shown different numbers if they were there.
- The three raised maxima (data#405, data-client#206, deploy#211) were each a single healthy pass: every run on attempt 1, no required context repeated. Their spans read the same on the latest-only view.
- The burst: data#405, data-client#206 and cascor#660 all ran between 13:10:05Z and 13:56:00Z. ✓
- Queue shares: 64 / 80 / 82 %. Under the definition the documents actually state (required jobs only), data-client is 81 %.

### 4. Consistency across the files
Agree everywhere they appear:
- all nine p90/max pairs and the per-row head counts
- the budgets, the "four at the ceiling" count, and the 334 / 341 / 711 s margins
- the queue ranges and the burst
- canopy#653 (failed 10:08Z; two jobs re-run from 19:01Z), recurrence#175 and the unhealthy heads
- the 166 test suites
- the soak figures 9 / 2 / 7

Disagreements:

| Fact | Where it is wrong | Reality |
|---|---|---|
| Independent reproduction | `tests/test_safe_merge.py`: "all eight rows exactly"; `docs/REFERENCE.md`: "every row" | Round 1's own record (`laneA2/lane_a2_evidence.json`, 20:51Z) has ml at 857/1061. The handoff's "8 of 9, the ninth is juniper-ml" is the correct statement. |
| How to re-measure | `KillResilienceTest` docstring: "Re-measure with …v2.py -n 30" and the inline comment "v2 instrument, n=30"; `util/safe_merge.py`: "re-run the v2 tool with `-n 30`" | The handoff says "first-pass, never raw v2". |
| cascor-client head count | `test_safe_merge.py`: "28 clean heads" | 30 healthy (as `util/safe_merge.py` and the handoff say, and as I measure). |
| ml window label | `util/safe_merge.py` and `test_safe_merge.py`: "#1981-#2015" | #2015 is still open. The window was #1981–#2014. |
| "5 got no `pull_request` run at all" | `lockfile-update.yml`, the walkthrough, the runbook, handoff Item 8 | Wrong for #1139 (see item 1). |
| "13 healthy heads" set aside by an "any repeat" rule | handoff (traps and corrections); by implication `test_safe_merge.py` and the v2 docstring | In the same windows, an any-repeat rule would set aside 21 heads, 16 of them healthy, each repeating only `Guard PR base branch`. 18 and 13 fit the old rule, which only dropped heads with a re-run of the same check after it. |
| Soak "56 PRs" and "7 of the 56 merges" | handoff, What moved item 4 | 57 PRs, of which 50 merged. |

### Defects, ranked
**Major**
1. **The test and `util/safe_merge.py` still say to re-measure with raw v2.** Following them would pin canopy at 33,299 s and recurrence at 9,886 s, which no budget can satisfy. That is the exact failure this PR corrects. Fix: point both at `util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py first-pass`, and say the head count per row is in `MEASURED_SPANS`.
2. **Two files claim independent reproduction that round 1 did not achieve for juniper-ml.** Fix: "Round 1 reproduced 8 of 9; juniper-ml's (910, 2005) was reproduced in round 2 on the window #1981–#2014." The handoff's de-escalator paragraph needs the same qualification.

**Minor**
3. #1139: say "5 got no run at opening; #1139 got runs only after the owner's push `5d343118`".
4. Change 56 → 57 PRs and "7 of the 56 merges" → "7 of 57 PRs (50 merged)". The trap "ask commits/<sha>/pulls" should add that it returns `[]` for a PR closed without merging.
5. In `test_safe_merge.py`, change "28 clean heads" to "30 healthy heads".
6. Change "#1981-#2015" to "#1981-#2014" in both files.
7. Describe the superseded rule as "a sequential re-run of the same check", or keep "any repeat" and quote 16 healthy heads instead of 13.

**Nits:** the recurrence#175 re-run came 2.7 h later, not 2.5 h (19:15:53Z → 21:59:28Z). Eight PRs were flagged at their final head, 7 of them falsely, so "blocked 7 merges" means 7 wrong blocks. The queue-share measure counted any job, while the text says required jobs.

**Changed:** none of the eight files under review.

**Created (untracked):** in `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round2-laneA/`:
- `r2a_common.py`
- `r2a_lockfile.py`, `r2a_lockfile_attempt1.py`
- `r2a_alarm_files.py`, `r2a_alarm_runs.py`
- `r2a_soak.py`, `r2a_soak_analyse.py`
- `r2a_spans.py`, `r2a_max_heads.py`, `r2a_queue_share.py`, `r2a_repeats.py`
- `r2a_misc.py`, `r2a_compare_a2.py`

The raw outputs are in the session scratchpad.
