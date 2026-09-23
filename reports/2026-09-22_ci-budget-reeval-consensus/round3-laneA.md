# CI-budget re-evaluation -- consensus round 3, Lane A -- re-derive the new figures

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `f0b3cc73`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

ml#2017 merged while round 3 was still running, and the soak re-read's figures are the 00:33 UTC state, not 00:50. Seven of the nine claims hold as stated; claim 1 is partial, and claim 9 shows the files agree with each other but share the wrong timestamp.

**Budget used:** about 456 REST calls (447 from my scripts, about 9 by hand or through the waiter) and about 20 GraphQL calls.

**File names used below** (all paths relative to the worktree):
- `HANDOFF…slack-deficit.md` = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`
- `…WALKTHROUGH.md` = `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`
- `…RUNBOOK.md` = `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`
- `ci.yml` and `lockfile-update.yml` are under `.github/workflows/`; `REFERENCE.md` is `docs/REFERENCE.md`.

## Verdicts

1. **PARTIAL (soak re-read).**
   - **How I bounded it:** `ci.yml` pull_request runs created from 2026-09-18T00:37:10Z (ml#1955's merge) to 2026-09-23T00:50:00Z. I counted every attempt's soak check-run and matched only expanded log values. Five runs created after 00:50 were excluded, and no attempt started after the cutoff.
   - **As of 00:50:** 214 check-runs across 212 workflow runs, 13 logs unreadable (all cancelled, HTTP 404), 19 with no markdown changes, and 182 that examined 434 files on 65 PRs (58 merged, 6 open, #1971 closed). 33 runs had findings; 10 distinct findings.
   - **The claimed 210 / 178 / 429 / 62 (56/5/1) match exactly with a 00:33:00 cutoff.** The gap is four clean runs: #2027 at 00:33:18, #2028 at 00:34:12 and 00:41:19, #2029 at 00:41:36. The findings counts do not change.
   - **Could it read differently:** yes, and it did. A 21:22 cutoff reproduces round 1's census exactly (191 / 12 / 17 / 162 / 367 / 57 PRs, 30 flagged, 9 distinct), so round 2's "57, not 56" correction stands.
2. **CONFIRMED (#2024).**
   - `git show --unified=0 200409f5` shows `-### F. Dropped…` replaced by `+### F. Found…` in place.
   - Soak job 106984241508 on the final head 3e7a860b932d1cc3db00056d24c39d1197dd94a2 flagged C4 on that file. The PR merged at 23:55:23Z.
   - `git grep dropped-by-this-document origin/main` finds nothing.
   - Over the merge diffs, the pairing rule clears 11 of 11 lost headings and a substring rule clears 3 of 11; #2024 is cleared only by pairing.
3. **CONFIRMED (juniper-ml first-pass).**
   - The ruleset has 17 required contexts. The last 30 merged PRs as of 00:33 are #1991–#2026: 30 healthy, p90 680, max 1061 (#2003). There were no duplicates and no legacy statuses, so neither rule was exercised.
   - Window #1981–#2014 gives (910, 2005) whether you take 30 heads (excluding #2004, which merged at 23:32) or all 31.
   - `REPO_TIMEOUTS` has juniper-ml at 2800, which is above 2720.
4. **CONFIRMED (#1139).** ea30c105 has zero workflow runs of any event; its only check suite is Cursor's (neutral). 5d343118 (parents ea30c105 and 50b91725, author pcalnon) got CI/CD Pipeline and CodeQL on pull_request, both successful.
5. **CONFIRMED (#1806).** Timeline: closed 13:59:37Z, reopened 13:59:38Z. The three parked runs have `updated_at` 13:59:38Z and zero jobs on attempt 1. The runs created at 13:59:40Z ran 18, 1 and 1 jobs.
6. **CONFIRMED (Cursor PRs).**
   - On juniper-ml the Cursor app has 100 closed-unmerged PRs from the window: 97 on cursor/ branches and 3 on test/ (#1728, #1729, #1732). The cursor/ ones closed 65 on 09-05 and 32 on 09-06.
   - Fleet-wide it is 138 (ml 100, data 30, canopy 8). The Search API gives the same 138 and 100, and no Cursor PR from the window is still open.
7. **CONFIRMED (alarm).**
   - juniper-ml has 54 runs: 46 OK, 4 WARN, 4 ALARM, dated 08-06 to 09-05. The Slack step succeeded on all 8 breaches, and no run lacks its level line.
   - Each of the eight siblings has 6 runs since 09-17, all OK, with the Slack step skipped.
   - In the workflow on main, the failed-query branch exits before the level line is printed.
8. **CONFIRMED (watcher).**
   - Both merged PRs print DONE. The waiter's stderr reads `wait budget: 2800s (measured budget for juniper-ml …)`, and the JSON carries `timeout` 2800 with a measured `timeout_source`; data#405 resolves to 3300.
   - Merging stderr into stdout breaks the JSON parse (`2>&1 | jq -e .` returns 5; stdout alone returns 0), so keeping them apart matters.
   - The TIMEOUT line was checked by reading the code only; merged PRs never reach it.
9. **Cross-file:** see the table below.

## Findings

**MAJOR 1 (action) — ml#2017 merged before round 3 finished.**
- It merged at 2026-09-23T01:17:13Z as 7b226ca0, by pcalnon. The head was 6f17aea5, which is f0b3cc73 plus one CodeQL line in `r2a_spans.py`.
- `HANDOFF…slack-deficit.md` on main is now false in two places. Lines 53–55 say ml#2017 "lands only once § Validation record … records every consensus round as complete". Lines 945–946 say round 3 is "in progress; this subsection is completed before merge".
- **Fix:** a follow-up PR against main that completes the Round 3 subsection, adds 6f17aea5 to "Between rounds 2 and 3" (lines 939–943), and carries findings 2 and 3.

**MAJOR 2 (number) — the soak re-read is labelled 00:50 but holds the 00:33 figures.**
- Affected: `HANDOFF…slack-deficit.md` lines 115–117, 674–680 and 954 ("62 PRs"), and `ci.yml` lines 1627–1630.
- **Fix:** relabel these "2026-09-23 00:33 UTC", or restate them as 214 / 13 / 19 / 182 examined 434 files on 65 PRs (58/6/1) / 33 / 10, with "8 wrong blocks in 65 PRs".
- Line 28 of the handoff and `…WALKTHROUGH.md` lines 285–286 are true at 00:50 as written. The promote/don't-promote verdict does not change.

**MAJOR 3 (action) — NON-OWNER 1 cannot pass its own acceptance for #1983 as written.**
- Rule (b) at `HANDOFF…slack-deficit.md` lines 146–149 keeps flagging a heading "whose OLD anchor is still linked from any tracked file".
- `util/ad-hoc/2026-09-21_register_close_cascor005.py:56`, which #1983 itself added as its link-migration helper, contains `OLD_ANCHOR = "[…](#apd-cascor-005--api-key-comparison-short-circuits-on-match-in-two-of-three-copies)"`. The register itself links the new anchor.
- Line 167 of the handoff, added in the round-2 fix, requires "the 8 false findings must clear", which a literal implementation of (b) cannot do.
- Line 704, "No in-repo link pointed at any old anchor", holds only for markdown.
- **Fix:** scope rule (b) to markdown links in tracked `*.md` files, and name the script string at line 704.

**MINOR 4.** Lines 663 ("191 runs") and 674 ("210 runs") of the handoff count check-runs, not workflow runs (189 and 208; one run had 3 attempts). Say "soak check-runs".

**MINOR 5.** `tests/test_safe_merge.py:38` says "round 1 matched seven exactly", while handoff lines 650 and 914 say "8 of 9 repos". Both are true, over different denominators. Add "(of the eight pinned rows)".

**MINOR 6.** #1981–#2014 now contains 31 merged PRs; the 30-head window excluded #2004. Note this at handoff line 651 and `util/safe_merge.py:312` so the pair can be reproduced.

## Cross-file table (at f0b3cc73)

| Figure | Sites | Status |
|---|---|---|
| Soak "00:50" with 62 / 210 / 178 / 429 / 56 / 5 | handoff lines 115–117, 674–680, 954; `ci.yml` 1627–1630 | Agree with each other; wrong for 00:50 (MAJOR 2) |
| 10 findings: 2 true, 8 false (6 C4, 2 C2) | handoff lines 28–29, 115–119, 679–680; `ci.yml` 1628–1632; `…WALKTHROUGH.md` 285–286 | Consistent and true |
| (910, 2005) on #1981–#2014; (680, 1061) at 00:33; 2720; 80 s | handoff lines 181–183, 649–656; `safe_merge.py` 312–317; `test_safe_merge.py` 55–61, 78; `REFERENCE.md` 3291 | Consistent |
| 5 got no run at opening, including #1139 (runs came later on 5d343118); 13 parked; #1806 released by close/reopen | handoff lines 570–578; `lockfile-update.yml` 18–25; `REFERENCE.md` 3831; `…WALKTHROUGH.md` 85–89; `…RUNBOOK.md` 985–991 | Consistent |
| 97 / 65 / 32 / 100 / 3 / 138 | handoff lines 131–133, 779–781 | Consistent |
| 54 runs; 4 WARN + 4 ALARM; 6 runs each | handoff lines 85–91, 583–592 | Consistent |
| Old flat 2400 s was below six of nine budgets | handoff lines 601–602; watcher line 47 | Consistent |
| Round-1 match count | `test_safe_merge.py:38` vs handoff lines 650, 914 | Wording only (MINOR 5) |

Round 3 changes a NUMBER / DISPOSITION / ACTION: yes -- NUMBER (the soak re-read is the 00:33 state, not 00:50) and ACTION (#2017 merged with round 3 unrecorded, so a follow-up PR is needed, and NON-OWNER 1's rule (b) must be scoped to markdown); the not-yet-promote disposition stands.

**Changed:** nothing tracked. **Created**, all under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round3-laneA/`:
- `r3a_common.py`
- `r3a_soak_fetch.py`
- `r3a_soak_analyse.py`
- `r3a_c4_rules.py`
- `r3a_old_anchor_links.py`
- `r3a_first_pass.py`
- `r3a_lockfile_1139_1806.py`
- `r3a_lockfile_followup.py`
- `r3a_cursor_prs.py`
- `r3a_alarm.py`
- `soak_raw.json`, `soak_parsed.json`
- `cache/` (API responses and job logs), `__pycache__/`

Also `wfc_stderr.txt` in the session scratchpad.
