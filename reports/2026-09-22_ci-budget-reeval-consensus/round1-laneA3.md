# CI-budget re-evaluation -- consensus round 1, Lane A3 -- file content and execution

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

## Lane A3 report: `HANDOFF_frozen_round1.md` and ml#2017

Of the six assigned checks, all are confirmed except five low-to-medium defects, ranked at the end.

**Setup.** My entry point was file content plus running the repo's own tools. I ran `git fetch origin` in this worktree only. The worktree's ten #2017 paths are byte-identical to 53d05121 (`git diff --stat 53d05121 -- <10 paths>` is empty). #2017 is **OPEN** at 53d05121 and unmerged (`gh pr view 2017`). None of these files moved between e3186919 and d0582a21 (current main). I edited no tracked file, did not run the reprobe, and did not read the round-1 claims.

### 1. File-content claims at e3186919 — CONFIRMED
Read with `laneA3/show_lines.py e3186919 <path>` and `git grep`:
- **`ci.yml:1061`**: "`main` measures ZERO structural problems as of 2026-09-15".
- **`docs/REFERENCE.md:3145`**: "`main` measured **zero** structural problems from 2026-09-15".
- **`docs/REFERENCE.md:2923`**: runs `tests/test_markdown_structure_screen.py`, inside "### Running every suite" (heading at :2753).
- **Stale literal gone**: `git grep -c '102 structural'` exits 1 at both e3186919 and 53d05121.
- **`util/safe_merge.py` on main**:
  - `:297` "OWNER RULED 2026-09-15" sits on the cascor-client row.
  - `:259` "TWO JUSTIFICATIONS WITHDRAWN 2026-09-10" covers the within-span/pre-start justification and the contention story.
  - `:312` "WITHDRAWN 2026-09-10: 'Unlike ml this is NOT a contention artifact.'"
  - So there are three rationales under two markers. Both rationales that item 5 names are marked.
- **Budgets row**: `docs/REFERENCE.md:3291` reads "Budgets: ml 1500, … deploy/recurrence 700", while `safe_merge.py` has ml 2800 and recurrence 2000.
- **`lockfile-update.yml` header**:
  - Before: "GitHub suppresses them…".
  - After: "CREATED but parked at `action_required` with ZERO jobs … 4 of 4 … #1304/#1517/#1806/#1932".
  - The text is confirmed. The API facts inside it are UNVERIFIABLE by my lane (not attempted).
- **Supporting claims, also confirmed**:
  - `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` has zero hits for waiter / wait_for_checks / 1800 / "item 10".
  - `md_structure_check.py:79` reads "RATIFICATION WITHDRAWN 2026-09-16" (the base-6 withdrawal).
  - `____TODO__DO-ME-AFTER-REBOOT____` is absent from main's root.
  - `notes/backup_tests_pre-and-post_reboot.md` is mode 100755 and starts with `#!/usr/bin/env bash`.
  - The five files changed in e3186919..d0582a21 include none the re-evaluation names.

### 2. Waiter change — CONFIRMED
- **Tests**: `python3 -m unittest -v tests/test_wait_for_checks.py tests/test_safe_merge.py` ran 124 tests, OK, exit 0, no skips.
- **Mutation check**: `2026-09-22_wait_budget_mutation_check.py` exits 0. The control is green and all 5 mutants are killed by real assertion failures. It mutates temp copies only.
- **Code read** (`resolve_timeout` and `main()`):
  - An explicit `--timeout` wins; it tests `is not None`, so 0 is honoured.
  - Omitted, it `exec_module`s `safe_merge.py` and calls `timeout_for`. `safe_merge.py` has only constants at module level, so loading it has no side effects.
  - Any exception gives `FALLBACK 1800s -- …`.
  - The `wait budget:` stderr line prints only when `--timeout` is omitted.
  - `timeout` and `timeout_source` are added to the result.
- **End to end** (all read-only):
  - ml#2016: stderr `wait budget: 2800s (measured budget for juniper-ml (safe_merge.py timeout_for))`; JSON `timeout: 2800`.
  - deploy#211: 1400.
  - `--timeout 5`: 0 bytes on stderr, source `--timeout`.
  - A lone copy of the file: `FALLBACK 1800s … FileNotFoundError`.
  - `--help` shows the new default text.
- **Callers**: `safe_merge.py:802` always passes `--timeout`. `bot_pr_merge_sweep.py` passes 150. `watch_prs_until_terminal.bash` passes `$PER_PR_TIMEOUT` (default 2400), so the new stderr line cannot pollute its `2>&1` JSON parse. The shepherd never invokes the waiter.
- **"Eight of nine"** holds under both main's budgets and the PR's.

### 3. Budget re-pin — CONFIRMED
`laneA3/budget_repin_matrix.py e3186919 53d05121` builds four temp trees:

| safe_merge.py | test file | result |
|---|---|---|
| main | PR | exit 1, 6 failures, exactly data / data-client / deploy, in both pins, lower bound only ("2400 not greater than 2589", "2400 … 2565", "700 … 965") |
| PR | PR | 78 OK |
| main | main | 78 OK (confirms the pin "stayed green") |
| PR | main | deploy's upper bound fails (1400 > 1048), so the table and test must move together, and they do |

All nine rows agree across `MEASURED_SPANS`, the 09-22 `REPO_TIMEOUTS` comments, the new REFERENCE.md row, the `KillResilienceTest` docstring and the frozen artifact. That covers the 4×p90 windows, the mids (4596 / 4372 / 1382), the clean-head counts where stated twice, and all nine budgets being in-window. The one exception is defect 3.

### 4. Slack table — CONFIRMED for 8 of 9 rows; juniper-ml PARTIAL
- **Headroom**: `2026-08-26_p5_fleet_state.py` exits 0. All nine headrooms match the table. `Memory Budget` is required on all nine.
- **SHAs**: every sibling's local `origin/main` equals the census SHA (canopy 9bffaba1, cascor 05c13d55, cascor-client 0366f4f1, recurrence 749e7a35, data-client f7494ff1, data 6c81cc4c, worker 48a523e6, deploy 13ee87aa; ml d0582a21).
- **Growth**: `measure-growth … --days 30 --ref origin/main` reproduces 8 rows exactly (growing commits, p90, max, slack, margin).
- **juniper-ml**: headroom 9727, p90 427, max 498 and margin +7727 are confirmed. I read **22** growing commits and a start of **36,960**, where the table says 24 and the prose says 36,792 (defect 2).
- **juniper-data via the API, no clone** (`laneA3/api_growth_crosscheck.py`): 11 commits, 24,965 → 26,479, 4 grew (+767, +18, +1304, +558), 2 shrank, p90 = max = 1304. Exact match.
- **Also confirmed**: "four negative"; "seven of nine have ≤4 growing commits"; `SLACK_FLOOR = 2000` at `p5_cut.py:65` and `p5_promote_ready.py:64`; and REFERENCE.md's "do not start a relocation because headroom < `max`".
- **Instrument note**: git reads a date-only `--since` at the current time of day, so the window moves during the day. Demonstrated: at 15:44 CDT, a576a90a (08-23 15:22 CDT) falls outside the window and 6e33d1dd (17:32 CDT) falls inside.

### 5. Structure count — CONFIRMED, and the instrument can fire
- `laneA3/structure_all_md.py` passes all 1127 tracked `*.md` paths (from `git ls-files -z`) as argv. Result: "structural problems: 0", "examined 1116 of 1127; 11 symlink aliases", real exit 0.
- The same holds on a `git archive` materialization of e3186919.
- `find . -path ./.git -prune -o -xtype l -print` prints nothing; 12 symlinks exist and all resolve.
- **Positive control**: the same screen run on `bcc89c45:docs/REFERENCE.md` (the ml#1746 damage) reports 2 swallowed H2s and exits 1. So the zero is a real measurement for that class. The screen's documented limit (fences nested in containers) remains.

### 6. `allow_update_branch` — CONFIRMED
`gh api repos/pcalnon/<repo>` returns a literal `false` on all nine, with `permissions.admin` true, so the field is authoritative.

### Extra checks
- **C4 finding on #2009 reproduced**: `md_structure_check.py --base 5c697282 <2 files>` exits 1 with "5 heading(s) LOST (count 19 -> 19)". All five are status renames, which confirms the false-positive class.
- **v2 defect is real in code**: v2 line 184 fetches `check-runs?per_page=100` with no `filter`, so the API default `latest` applies.
- **Alarm workflow**: `pr-budget-alarm.yml` is a blob on all nine repos' main.

**UNVERIFIABLE (not attempted; API work or another lane's entry point):** the soak counts (184 / 156 / 30); the raw 33,299 s and 9,886 s maxima; "clean single pass" for #405 / #206 / #211; the lockfile PRs' run attempts; the alarm's run history; `SLACK_WEBHOOK_URL`; and the commit attributions (2f8653c6, db627616, e7c191c1, and 244f8348's ancestry).

### Defects, ranked
1. **MEDIUM if the handoff merges before #2017; LOW if it ships inside it.** The artifact states item 10 is "closed on 2026-09-22 by ml#2017", that "ml#2017 re-pins them", and that "Nothing is urgent".
   - #2017 is OPEN, and main still has `default=DEFAULT_TIMEOUT` (1800), data 2400 and deploy 700 (`git grep … origin/main`).
   - The handoff file is not among #2017's ten files.
   - If the handoff merges alone, main records closures it does not carry, and three stale budgets stay live.
2. **LOW.** The juniper-ml slack row's "24 growing commits" and the prose's "shrank from 36,792" cannot come from the same window.
   - `laneA3/growth_window_edges.py` shows a b402bfab start gives 36,792 with **25** grew, and a 5a12a8c1 start gives 36,848 with **24**.
   - The reprobe calls the same `growth_stats`, so this is two runs at different times of day. No margin changes.
3. **LOW.** The PR's `util/safe_merge.py` comment says cascor-worker "clears the max by only 341 s -- the thinnest margin in the table", and the frozen artifact §1 says "cascor-worker is the thinnest".
   - In seconds, recurrence is thinner: 2000 − 1666 = **334 s**.
   - cascor-worker is thinnest only by ratio (1.166 against 1.200).
4. **LOW.** The fix criterion in §1 NON-OWNER WORK 1 ("C4 must accept a heading whose old text survives inside a renamed one") would not clear #2009.
   - 3 of its 5 renames drop old text, e.g. "(recommended)" and "DECISION REQUIRED — …".
   - The prescribed backtest would expose this.
5. **LOW (wording).** The `util/wait_for_checks.py` docstring says `REPO_TIMEOUTS` "is the only place the fleet's required-check spans are recorded".
   - `tests/test_safe_merge.py` calls `MEASURED_SPANS` "THE SINGLE SOURCE OF TRUTH FOR MEASURED CI SPANS".
   - REFERENCE.md names both.
- **Nit.** The walkthrough said the PR "does not trigger" workflows, not "suppressed". #2017 corrects it with an appended callout and leaves the original sentence in place.

**Changed**: no tracked file. **Created** (the six analysis scripts, in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneA3/`):
- `show_lines.py`
- `budget_repin_matrix.py`
- `growth_window_edges.py`
- `api_growth_crosscheck.py`
- `structure_all_md.py`
- `blob_screen.py`

**Referenced**: `HANDOFF_frozen_round1.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml`, `.github/workflows/lockfile-update.yml`, `util/safe_merge.py`, `util/wait_for_checks.py`, `tests/test_safe_merge.py`, `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`, `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md` (its ml#1746 finding motivated the positive control).
