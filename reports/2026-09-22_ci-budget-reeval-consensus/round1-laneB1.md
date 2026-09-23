# CI-budget re-evaluation -- consensus round 1, Lane B1 -- omission and executability

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

**Lane B1 review, round 1 (lens: omission, completeness, executability).** The re-evaluation cannot be run as written. It also repeats the failure it diagnoses: a PR that is still open is summarised as having closed items.

Short names used below: HANDOFF is the frozen `…/round1/HANDOFF_frozen_round1.md`. WALKTHROUGH is `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`.

### 1. CRITICAL — the "closed" items depend on ml#2017, which has not merged, and the prompt never says so
- **Where:** the HANDOFF banner ("It is closed by ml#2017", "ml#2017 re-pins them"), §1 block 1 STATE, and item row 10.
- **What is wrong:** ml#2017 is still OPEN and auto-merge is not armed (`gh pr view 2017`). The reprobe script is not on main: `git cat-file -e origin/main:util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py` answers "exists on disk, but not in 'origin/main'". Main's copy of the HANDOFF also has no Re-evaluation section. So a fresh session's first preflight step fails, and item 10 plus the three re-pinned budgets are still live on main.
- **Why it matters:** the 09-09 original guarded exactly this case for #1862 ("Until it merges … NOT closed"). The re-evaluation dropped that guard.
- **Fix:** add `gh pr view 2017 --json state,mergeCommit` to PREFLIGHT. If it has not merged, item 10 and the re-pins are still open, and landing ml#2017 (with Paul's approval) becomes step 0. Reword "closed by" as "closes when ml#2017 merges".

### 2. MAJOR (critical if the owner says yes) — owner decision 2 has no mechanism, and both written mechanisms produce a check that can never fail
- **Where:** block 1, OWNER 2; the sentence "Promoted as it stands, it would have failed 7 PRs".
- **What is wrong:**
  - `.github/workflows/ci.yml:1627-1628` says to promote by "dropping the `|| true` below". The step contains no `|| true`.
  - WALKTHROUGH §7 item 2 (lines 277-279) says to drop the trailing `exit 0` (`ci.yml:1700`). The step would still exit 0: its last command is the `if [ "$rc" -ne 0 ]; then echo …; fi` at `ci.yml:1695`, which returns 0 whichever way it goes.
  - Promoted by either recipe, the check fails zero PRs, not seven.
- **Fix:** before the owner is asked, correct both recipes to `exit "$rc"`. Decide how the refusal code 2 and the early `exit 0` paths behave.

### 3. MAJOR — the spec for NON-OWNER item 1 cannot meet its own acceptance test
- **Where:** "C4 must accept a heading whose old text survives inside a renamed one … drop the 8 false ones."
- **What the merge diffs show:**
  - #1973 does survive: "0.6 Owner decisions still owed" became "… — NONE, as of 2026-09-21".
  - #1976 (`739a233c`) does not: "…environment repair — owner has not ruled, asked 3+ times" became "~~…environment repair~~ — MOOT…".
  - #1992 (`3b656b57`) does not: the heading's claim was rewritten.
  - #1983 (`78e36d8e`) does not: "two of three copies" became "three of four", a factual correction rather than a status marker.
  - #2009 (`c4a67481`): 3 of its 5 headings do not survive ("DECISION REQUIRED" became "RULED", and "(recommended)" was dropped twice).
- **Result:** the spec clears 2 of the 6 false C4 findings.
- **Cause the HANDOFF leaves out:** these findings come from ml#1944's own C4 fix, which compares heading texts. #1976's heading count rose from 23 to 30 and C4 still reported 2 LOST. So item 4's "CLOSED" fix created the largest class of false positives.
- **Ownership:** loosening C4 trades against the owner's Decision E, so this item may need an owner ruling rather than being session work.
- **Fix:** restate the spec (for example, match on heading level plus section number or ID, ignoring strike-through). List all 8 false findings with their heads. Flag the Decision E trade-off.

### 4. MAJOR — the evidence cited for item 10 cannot tell fixed from unfixed
- **Where:** row 10 cites the `waiter` probe. PREFLIGHT says "Each probe prints what could have made it read differently."
- **What is wrong:**
  - `probe_waiter` compares the constant `DEFAULT_TIMEOUT = 1800`, which the fix did not change, against `REPO_TIMEOUTS`.
  - Run on the fixed tree it prints "8 of 9". With the pre-fix budgets from `git show e3186919:util/safe_merge.py` it is also 8 of 9.
  - Neither `waiter` nor `settings` prints a could-it-read-differently line.
- **Fix:** have the probe call `resolve_timeout(repo)` and report the source. Cite `TimeoutResolutionTest` as the evidence instead.

### 5. MAJOR — "use `rerun-split`, not raw v2" is handed on without the tool's bias
- **Where:** NON-OWNER 2; "That can only lower a max."
- **What is wrong:** I classified the frozen `claims/rerun_split.json` with `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB1/classify_rerun_setasides.py`.
  - The tool set aside 18 heads. 13 of them are only a success-then-success repeat of `Guard PR base branch` (for example cascor#656 at 1735 s and worker#188 at 809 s), not re-runs after a failure.
  - Each is dropped whole, including a valid pass.
  - Under the rule "budget > observed max", a lower max is the unsafe direction.
  - No set-aside head exceeded its repo's clean max on 09-22, so the new budgets stand. The problem is the instrument future sessions are told to use.
- **Fix:** measure the first-attempt span instead of dropping the head. Treat guard-only repeats as clean. Carry the tool's own MISCLASSIFY caveat into the prompt.

### 6. MAJOR — two load-bearing constraints were removed from block 1
- **Reproducibility of p90:** the open half of flood-2 §3 item 5 ("does not reproduce", listed in the original's §5) is gone.
  - p90 rose 1.56–1.90x in two weeks: data 955→1651, data-client 896→1545, deploy 262→450, recurrence 587→1114, worker 1010→1576.
  - Deploy's new 1400 fails the "≤4×p90" half if its p90 falls back to 262 (4×262 = 1048).
- **`TIMEOUT_CEILING`:** round 1 on 09-09 had to restore this after it was cut, and it is cut again.
  - canopy, cascor-client, data and data-client now all sit at 3300, so "raise mid-window" is used up for those four.
  - "cascor-worker is the thinnest" is true only of the margin to its budget.
- **Fix:** add both to NON-OWNER 2. Flag ceiling saturation as a future owner decision. The strict-policy audit's C-4/M-4 (batching merges) was the dropped reading for this.

### 7. MAJOR — the banner contradicts the prompt
- **Where:** banner, "Three items remain, all the owner's."
- **What is wrong:** block 1 and "What remains outstanding" each list two non-owner items. "All ten … closed or ruled" is also wrong for row 3, which the HANDOFF itself marks "Informational".
- **Fix:** say five items remain (three owner, two non-owner), plus landing ml#2017.

### 8. MAJOR — no git status and no staleness anchor (breaks `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` Step 3.3 and CLAUDE.md)
- **What the HANDOFF says:** §4 still reads branch `docs/handoff-2026-09-09-…`, "Five PRs open", and "~106 … ~128" worktrees.
- **Actual state:**
  - ml#2017 is on branch `fix/ci-budget-arc-2026-09-22-waiter-default-and-stale-budgets`, head 53d05121.
  - Worktree `ancient-yawning-biscuit` holds an unsigned local-only commit `18d3d5e3` ("never pushed") and three modified files.
  - There are now 140 worktree directories and 161 registered.
- **Also missing:** the "Do not remove worktrees" hazard (551 `.h5` files lost before). PREFLIGHT has no anchor like the original's `6ccf80fa..origin/main`; e3186919 appears only in the foot section.

### 9. MAJOR — MERGING is labelled "re-verified 2026-09-22", but only one setting was checked
- **What was checked:** the `settings` probe reads `allow_update_branch` only (False on all nine; I confirmed it).
- **What the section leaves out:**
  - Paul's per-PR merge approval, which a handoff cannot carry forward (`feedback_headless_merge_approval_policy.md`).
  - The shepherd never merges; it returns NOT-ARMED unless auto-merge is already armed (`2026-09-05_auto_merge_shepherd.py:188-189`).
  - The shepherd's own docstring says the settled policy is to try `safe_merge.py --execute` first.
  - WALKTHROUGH §6.3: `PUT /contents` does not sign, and `open_signed_pr.py` refuses an existing branch.
  - `--per-pr-timeout 2700` was proven when ml's slowest run was 773 s. It is now 2005 s.

### Minor
10. **"0 breaches … all nine repos" (OWNER 1).** On juniper-ml a breach goes to Slack with no annotation (`pr-budget-alarm.yml:148-166`), so the probe cannot see it there. Row 9 itself claims only the eight siblings.
11. **Preflight gaps.**
    - `all` is run without `--fetch`, and a STALE-LOCAL slack row exits 0.
    - `<scratch>` is never defined.
    - There is no guidance for exit 2, and the run makes about 2,500 REST calls while other sessions share the same token.
    - The script's docstring omits `rerun-split` and `settings`.
12. **Naming rule.** These role references in the foot section have no filename: lines 384, 401, 421, 479-481 ("walkthrough", "workflow header", "Both texts") and 526 ("the backup arc").
13. **Useful guidance left in the wrong block.** The relocation traps "remain correct" but now live only in the block marked "do not act on it". Block 1 also drops the `md_`/`markdown_` warning and the v1 warning.
14. **"Tight by owner decision" list changed without evidence.** "data and cascor-worker" silently drops data-client.
15. **Stale test count.** `AGENTS.md:69` says 165 suites. `ci.yml`, `docs/REFERENCE.md` and disk all have 166 (`2026-09-10_agents_md_test_list_drift.py`), so the second half of item 10 still leaves a stale count.
16. **No 09-22 "cannot support" line** (required by the consensus procedure §7). The soak's per-PR denominator is not reported; `prs_examined`=13 is a lower bound.
17. **Older loss this method could not see.** Flood-2 §3 item 11's "22 harvestable PRs whose production half is absent" (flood-2 disposition analysis §8) was never carried forward or closed. `grep "production half"` finds it only in the 09-05 and 09-07 documents.
18. **Rows 4 and 7 cite summaries rather than artifacts.** Row 4 cites "walkthrough §5", which contradicts the HANDOFF's own method. I re-checked row 4 and it holds (a missing path and a bad `--base` both exit 2). Row 7 cites two of the six sites that ml#1880 corrected.

**Changed:** `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB1/classify_rerun_setasides.py` (new, untracked, reads the frozen claim only). I also wrote scratch files `laneB1_*` in the scratchpad. Nothing was committed and nothing was written to GitHub.
