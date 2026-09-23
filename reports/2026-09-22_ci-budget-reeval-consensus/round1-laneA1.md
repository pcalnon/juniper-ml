# CI-budget re-evaluation -- consensus round 1, Lane A1 -- history and timelines (git, PR and Actions history only)

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

# Lane A1 report: git history, PR, Actions and timeline data

The re-evaluation's PR numbers, merge SHAs, dates and diff attributions all check out, and the soak and span figures mostly reproduce. Two claims are materially wrong: the lockfile mechanism correction rests on 4 of 18 lockfile PRs, and the proposed C4 fix cannot deliver the backtest result the document promises.

- **Artifact under review:** the frozen round-1 copy (`HANDOFF_frozen_round1.md`) of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`, plus ml#2017 at `53d05121`.
- **Also referenced:** `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` (called "the walkthrough" below).
- **Changed:** no documents. I added ten read-only, untracked scripts under `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneA1/` (`a1_*.py`). Their outputs are in `scratchpad/laneA1/`.
- **Forbidden sources:** the reprobe script and `round1/claims/` were never read. I pulled ml#2017's diff per file with the reprobe script excluded.

## 1. Closure and attribution claims: all CONFIRMED

`a1_pr_ancestry.py` compares `gh api pulls/N` merge SHAs with `git merge-base --is-ancestor <sha> origin/main` (tip `d0582a21`). Each SHA matches its PR and is an ancestor of main:

| PR | Merge SHA | Merged (UTC) | Notes |
|---|---|---|---|
| #1862 | `244f8348` | 09-10 00:13:15 | |
| #1880 | `db627616` | 09-10 | |
| #1944 | `2f8653c6` | 09-16 01:03 | |
| #1946 | `668ae575` | 09-16 | Adds `util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py`; not cited in the document |
| #1955 | `e7c191c1` | 09-18 00:37:10 | |
| #1886 | `7f533b4d` | 09-11 | |
| #1963 | `2804d494` | 09-19 | Adds the walkthrough |
| #1851 | `3cab4783` | 09-09 | |

What each PR actually contains, from `git show <sha> -- <file>` and `git log -S`:

- **ml#1944** has `OWNER RULED 2026-09-15: the VALUE STANDS at 3300` in `util/safe_merge.py`.
  - It also has the App-token arm in `lockfile-update.yml`: `create-github-app-token`, gated on `vars.RELEASE_TRAIN_APP_ID`, with the token passed to create-pull-request.
  - It has the C2/C3/C4 and exit-2 fixes, and both dated-ZERO lines. `git log -S` points only to `2f8653c6`, at `ci.yml:1061` and `docs/REFERENCE.md:3145` at `e3186919`.
- **ml#1955** withdraws "base 6". **ml#1880** carries "WITHDRAWN 2026-09-10" for both rationales. **ml#1851** raised ml 1500→2800 and recurrence 700→2000.
- **Item 10:**
  - `git grep -i -e wait -e 1800 -e DEFAULT_TIMEOUT` over the walkthrough at `e3186919` finds nothing.
  - `d0582a21:util/wait_for_checks.py:492` still has `default=DEFAULT_TIMEOUT` (1800).
  - The suite appears at `REFERENCE.md:2923`, placed there by ml#1886.
- **Item 6:** 1127 tracked `*.md` and 0 dangling symlinks at `e3186919`. As a control, the same script finds exactly 10 dangling at `6ccf80fa`.
- **Item 9:**
  - `pr-budget-alarm.yml` is on all nine default branches.
  - Each of the eight siblings has 6 scheduled runs from 09-17 to 09-22, all success, with 0 warning or failure annotations.
  - `SLACK_WEBHOOK_URL` exists on juniper-ml only.
  - My first pass read recurrence as "0 runs" because the script swallowed an API error. A direct query returned `total_count` 6, and the fixed script now reports errors instead of zeroing them.
- **Also confirmed:**
  - The anchor window `e3186919..d0582a21` holds 3 docs PRs (#2011, #2014, #2016), none touching a named file.
  - The root TODO file is gone (deleted by ml#1969).
  - v2 fetches `check-runs?per_page=100` with no filter, so the default `latest` applies.
  - None of the cited PR numbers is fabricated.

## 2. Lockfile claims

`a1_lockfile_runs.py` reads each run's `attempts/1/jobs` `total_count` and `attempts/1` conclusion.

- **#1970: CONFIRMED.** Opened 08:26:01Z by `juniper-release-train[bot]`. Its 5 opening-commit `pull_request` runs had 1/19/1/1/1 jobs on attempt 1. It also had 3 later pcalnon runs on a merge commit, so "all 5 of its runs" is loose wording.
- **The four pre-fix PRs: CONFIRMED.** All 12 runs had 0 jobs on attempt 1. Attempt 1 concluded `action_required` for #1304, #1517 and #1932, and `failure` for #1806's three.
- **#1806: PARTIAL.** Closed 13:59:37Z and reopened 13:59:38Z. The runs' `updated_at` is 13:59:38Z, the reopen second, so the API cannot say whether the close or the reopen flipped them. pcalnon's runs at 13:59:40Z did run (18/1/1 jobs).
- **#1932: CONFIRMED.** The runs went to attempt 2, `triggering_actor` pcalnon, with no reopen event.
- **The census is REFUTED.** `gh pr list --head chore/lockfile-update --state all` returns **18** PRs opened by github-actions (#325 through #1932), not 4.
  - 13 have parked runs.
  - 5 (#325, #328, #339, #389, #1139) have **no `pull_request` run at all**. Two independent queries agree: by `head_sha`, and a branch-plus-event list of 71 runs whose earliest is 06-15.
  - #1139's 08:10–08:40 window shows only the scheduled run.
  - So "suppressed" did happen on this repo as recently as 2026-08-17.
  - Also, #1304, #1517 and #421–#1057 were released by owner re-run too. That is 12 of 13 parked PRs; only #1806 used close/reopen.

## 3. Advisory-soak findings

`a1_soak_findings.py` reads the job logs with echoed script lines dropped. `a1_soak_census.py` works from the Actions run list, not a PR list. `a1_soak_adjudicate.py` compares `M^1:file` with `M:file` at each merge commit.

**Totals:**
- 30 warned runs: CONFIRMED. The census of 191 CI heads since `e7c191c1` finds exactly 30, all within the 9 named PRs (3+1+5+6+2+2+3+7+1).
- 184 total runs: CONSISTENT. The count was 177 when `e3186919` merged and 185 when ml#2017 opened.
- The 11/17/156 split was not verified.
- "Once per head" has one exception (one head carried 2 soak runs).

**True findings, both real:**
- **ml#1999:** C3 fired at exactly `ea4c3596`, `25c001bd` and `276db114`. At `276db114` the `(sink-a)` list item sits between the table and its last two rows, so they render as prose. `7bc30e7b` fixed it, and merge `43980f13` has the rows back inside the table.
- **ml#1969:** the file has mode 100755 and a `#!/usr/bin/env bash` first line.

**False findings:** every one is a deliberate edit, not damage.
- The C4 hits are ruling or status renames in #1973, #1976, #1992 and #2009, plus a factual heading correction in #1983 ("two of three" → "three of four").
- The C2 hits are wrapped prose lines at #1980:343 (`git).`) and #2007:275 (`make`).
- **No in-repo anchor broke.** `git grep` for every lost heading's slug at merge and at `origin/main` finds only the `OLD_ANCHOR` constant in `util/ad-hoc/2026-09-21_register_close_cascor005.py`. The defect register links the new anchor.

## 4. Spot checks

`a1_span_spotcheck.py` recomputes each span from the ruleset and check-runs:

- **data#405 (2589 s), data-client#206 (2565 s), deploy#211 (965 s): CONFIRMED** as clean single passes. Every required context ran once and passed.
- **canopy#653: CONFIRMED.** 33,299 s, with the Quality Gate failing at 10:08:23Z and the Playwright job re-run at 19:01:43Z.
- **recurrence#175: CONFIRMED** at 9,886 s.
- **Mechanism caveat:** under `filter=latest` recurrence#175 keeps 59 of its 60 runs, including the first attempt's cancelled required contexts. Both spans are identical under `filter=all`.

## Defects, ranked

**Major**

1. **The lockfile mechanism correction rests on 4 of 18 PRs.**
   - "On this repo they are created and parked" (What moved 5), ml#2017's workflow header ("4 of 4 such PRs") and the walkthrough edit ("all four `GITHUB_TOKEN` PRs") are each contradicted by the 5 PRs with no run.
   - It replaces a partly-right statement with a partly-wrong one.
2. **The proposed C4 fix can't meet its own backtest.** "Accept a heading whose old text survives" matches only 3 of the 10 lost headings (#1973's 0.6, and #2009's Option A and 5.2A).
   - #1976's strikethrough splits the old text, and #1983, #1992 and #2009's §3/Option B/5.2B headings don't keep it.
   - So the rule clears 1 of the 5 C4 PRs, not "drop the 8 false ones".

**Minor**

3. **The distinct-finding count is keyed on message text.**
   - #1973 lost one heading, flagged at 5 heads. "Twice" comes from the heading count changing (31→38, then 31→39).
   - Keyed on the finding itself, the total is 9 per PR/file/check (2 true, 7 false) or 14 per lost line (2 true, 12 false).
   - The direction of the conclusion holds under either key.
4. The correction names only #1932 as released by re-run. 12 of 13 parked PRs were released that way.
5. #1806's "closing flipped" is not separable from the reopen at 1-second resolution.
6. "Closed by ml#2017" is premature. The PR is **OPEN**, and the handoff itself is not in its file list.
7. ml#1955's comment named `make` or `cd`, not `git`, so "the exact risk" fits #2007 only.
8. recurrence#175's tail is a separate later run, not a replaced attempt. Its "~743 s pass" also contained 4 failed and 5 cancelled required contexts.
9. #1983's heading edit is not a status rename.
10. The backtest is dated 2026-09-16 in `ci.yml` but 2026-09-17 in the document.
11. Item 7 omits its history: ml#1880 removed the stale figure, ml#1881 restored it, and ml#1886 removed it again.

**Not attempted:** the slack table, the p90/max figures other than the three raised maxima, the "0 problems" structure probe, and the `KillResilienceTest` fail-before-raise claim.

**Could each instrument have read differently?** Yes, in every case. Attempt-1 job counts read 19 on #1970. The anchor grep found a hit. The dangling-link control found 10. The soak's per-PR total cross-checked against an independent census, 30 = 30.
