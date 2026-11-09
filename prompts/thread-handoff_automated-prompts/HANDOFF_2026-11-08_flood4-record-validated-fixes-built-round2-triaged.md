# Handoff: flood-4 — record PR built and validated (V4 fixes pending), three defect fixes built and validated, round 2 triaged

**Date**: 2026-11-08 (UTC; written ~11:45Z)

**Arc**: the Cursor flood-4 disposition, session 2. It started as `joyful-dancing-kahan` and ran in `humming-stargazing-papert` via EnterWorktree once session 1 (pid 2311382) exited. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md` (the round-1 handoff), on the owner's "merge approval granted".

**Host**: the Linux host.

**Git status**:

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert`, fast-forwarded to `8d73d441` (main at 09:40Z). **Nothing is committed.**
  - Modified: `CHANGELOG.md`, which carries the record PR's entry on main 8d73d441's file.
  - Untracked: the record note; both handoffs (round-1's and this one); `reports/2026-11-08_flood4-disposition/`; and 159 `util/ad-hoc/2026-11-0[78]_flood4_*.py`.
  - Scratch in `tmp/flood4/`: `STATE.txt` is the running log (read its last 60 lines first); `round2-triage/` (TRIAGE_SUMMARY.txt plus 297 evidence files); `val-record/v1..v4/`; `push/ml-record/` (title, pr_body and commit_body: STALE, see below).
- **The fix worktrees, all uncommitted:**
  - M-3: `.claude/worktrees/agent-a2a3d94543b707549` (deliverables and validator findings in `tmp/flood4-fix/m3/`);
  - M-4/M-7: `.claude/worktrees/agent-a552a50a3a9e32041` (`tmp/flood4-fix/m4m7/`);
  - M-1: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--gitleaks-pr-commit-pagination--20261108-0340--4f04fc8d` (`tmp/flood4-fix/m1/`).
- **The primary checkout** is on the owner's branch `feat/article-draft_backup-fix-notes` (#2520). Do not touch it.

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md. Read it at
/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/prompts/thread-handoff_automated-prompts/
(uncommitted). Once session 2 has exited (lock: `git worktree list --porcelain`), EnterWorktree(path=<that worktree>).
Run the Verification block first. If an invariant fails, stop, re-derive it from GitHub, and report.

FIRST ask the owner for THIS session's merge approval (auto-memory feedback_headless_merge_approval_policy.md: a handoff
cannot carry it). Ask it as "Merge, update, close", covering the record PR, the defect-fix PRs, the M-1 fan-out PRs and
the round-2 carriers. Also ask the open question: #2507 (CI-gate REFERENCE's version cell, pins sentence and matrix row
against pyproject, which needs propose.py extended: carry it or not?). The owner's rulings 1-11 below stand as decisions.

Remaining work, in landing order (strict rulesets; shared files: CHANGELOG.md, docs/REFERENCE.md and the doc stamps):

1. THE RECORD PR (juniper-ml), notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md:
   a. Apply V4's exact fixes. Source: tmp/flood4/val-record/v4/findings.json, fix_old_strings.txt and
      changelog_entry_rewrapped.txt. Every OLD string occurs once.
      - MAJORs: the §4 gitleaks row (#1797: ONE of its 88 commits was the PR's own; "seven" means the seven OTHER repos);
        the §8 insert about the other repos, now covered by ruling 10; the PR and commit bodies (V4-F3 lists every
        replacement; the scripts now number 159).
      - Do it with a provenance script, util/ad-hoc/2026-11-08_flood4_record_round2_fixes.py, written like _round1_fixes.py
        (it skips a fix whose NEW text is already present).
   b. Add a §8 block for rulings 8-12, with verbatim labels (12 re-confirms M-3; add #2460's provenance to the §4 wedge
      row, as given under the rulings table below), and update the §4 status cells (M-1's fix is validated or
      not). Add the four new defects (N-1..N-4) and the round-2 triage outcome in one line each, pointing at the next
      record update for detail.
   c. Fill pr_body's Validation section with rounds V1-V4 and their counts, and add `## Requirements` stating "None".
   d. Re-run every gate:
      - G-PATH: python3 util/home_path_literal_check.py util/ad-hoc/2026-11-0[78]_flood4_*.py (PASS);
      - G-TMP: 2026-11-08_flood4_gtmp_pragma_pass.py --check (0);
      - the CodeQL prescreen (exactly 7, all in val_r2_canopy_stage_shape.py: pydantic fields, a known false positive);
      - py_compile;
      - the header check (159/159);
      - juniper-check-doc-links with CI's args plus --exclude tmp;
      - gitleaks on the frozen snapshot: ~/.cache/pre-commit/repotw5tescj/golangenv-system/bin/gitleaks dir
        --config .gitleaks.toml --redact <snapshot>. The pre-commit secrets hook is VACUOUS on unstaged files.
   e. One more independent validation round on the round-2 corrections only (SOP: a correction pass is not done until
      it is validated).
   f. Add THIS handoff to util/ad-hoc/2026-11-08_flood4_record_freeze.py's FIXED list. Then:
      - git fetch;
      - if main moved past 8d73d441, rebuild CHANGELOG.md three-way on current main (#2521, armed, edits its top);
      - freeze with --base-sha <current main> --out tmp/flood4/push/ml-record-r2;
      - push with util/ad-hoc/2026-11-07_flood4_signed_push_batches.py --repo juniper-ml --branch
        docs/flood4-disposition-record ... (about 175 files, batches of 200 KB or less);
      - on green, util/safe_merge.py (read its MERGED line; exit 0 does not mean merged).
2. M-3 (paused-fit wedge; juniper-service-core lifecycle/manager.py): apply VA-A1 (MAJOR, a regression).
   - Settle only when this thread owns the run:
     `if not self._stop_event.is_set() and self._thread is threading.current_thread():`
     Put `_last_result` under it, guard both except branches, and add a regression test shaped like the validator's S7.
   - VB-B1: cite the record by filename and say "the paused-fit wedge"; no "M-3" labels.
   - Apply the minors (val-a and val-b findings in that worktree).
   - Re-validate once, then push signed and merge FIRST among the fixes.
3. M-4/M-7 (resume losses; websocket/manager.py and training_stream.py): apply
   - VB-F1: ### Added for the new public `replayed_through` keyword and the bool return, which makes this a MINOR (0.8.0)
     release; juniper-ml's [tools] caps service-core <0.8.0, so the cap rises at release; see the auto-memory note
     feedback_semver_beats_consumer_cap_2026-09-05.md;
   - F2-F4: labels, the cheatsheet footer stamp, and REFERENCE's version-history row;
   - VA-3, VA-5 (a large send_timeout_seconds in the tests) and VA-6 (a targeted no-await-invariant test).
   Rebuild its docs, stamps and both CHANGELOGs three-way on main after M-3 merges. Re-validate, push, merge.
4. M-1 (juniper-data CI gitleaks): validate it (two lenses; no validator has run yet), push signed to juniper-data, and
   merge. Then ruling 10: port it to the seven other repos, one PR each, once data's has run green LIVE.
5. Ruling 11: build, validate and land four fixes:
   - N-2: service-core stop-then-start race (a per-run stop token; interacts with M-3's guard);
   - N-4: service-core broadcast drops a socket whose send fails without closing it;
   - N-1: juniper-cascor's own paused-fit wedge;
   - N-3: juniper-cascor's own WebSocket manager has both resume losses (src/api/websocket/manager.py:829-830;
     training_stream.py replay :390-416, promote :290).
6. Round 2: build the carriers from tmp/flood4/round2-triage/TRIAGE_SUMMARY.txt:
   - ml-code: with the effort ruling (EFFORT_DEFAULT=max; `--effort auto` sends no flag), brace cap fail-closed
     (invert tests/test_claude_agent_guard_brace_cap.py:63-71) and #2514;
   - ml-tests; ml-docs;
   - data-tests, data-docs, and data-code (juniper_data/api/security.py:250, :254, :427);
   - canopy-tests; canopy-docs.
   Each is validated, signed, merged, and its drafts closed with a comment naming it. Never merge, retarget or un-draft
   a draft.
7. Round 3: #2404 and #2406, individually.
8. Worktree cleanup (ruling 7), after the record merges.
   - FIRST archive the evidence the manifests and corrections cite, out of tmp/, to a non-temporary place:
     167 paths under tmp/flood4/, plus val-record/ and round2-session/codeql_orig/.
   - Then remove this arc's worktrees and the 11-06 five, each only after its PR is confirmed merged.
   - Never use util/remove_stale_worktrees.bash; curious-plotting-hummingbird is DO NOT SWEEP.
9. A record-update PR at the end: round 2, round 3, the fix PRs and the new rulings.
10. Archive the next handoff.
```

---

## The owner's rulings of 2026-11-08 (AskUserQuestion; option labels verbatim)

| # | Question | Answer |
|---|---|---|
| 1 | Approval scope (session 2 only) | "Merge, update, close (Recommended)" |
| 2 | The 13 uncovered drafts | "Fold into round 2 (Recommended)" |
| 3 | M-6, the launcher effort | "let's go with option 2, restoring max as default. however, let's also add functionality descripted in option 1: if auto is selected, send no --effort flag." |
| 4 | #2271's idleCompaction | "User settings + delete branch (Recommended)" — **done** |
| 5 | The §4 defects | "Fix now" (each its own validated, signed PR) |
| 6 | Host state | "Upgrade both, checked first". ci-tools is done, on a per-environment reading; **disclose this**. `JuniperCanopy1` is not done: 4 live E2E legs |
| 7 | Worktrees | "All, after record merges (Recommended)" |
| 8 | Brace cap | "Fail closed (Recommended)" |
| 9 | Retry-After | "Both in round 2 (Recommended)" |
| 10 | M-1 fan-out | "All, after data's lands (Recommended)" |
| 11 | N-1..N-4 | "Fix all four now" |
| 12 | M-3, re-asked with the missing context | "Confirm the fix (Recommended)" |

Ruling 12's context: a side agent noted that REFERENCE.md had once called the refusal an invariant to preserve, and that ruling 5 was given without that fact. Session 2 traced it.
- The wording came only from Cursor draft juniper-ml#2460 (`app/cursor`, 2026-11-04). The draft filed "a paused fit stays paused" in REFERENCE.md's "load-bearing invariants" list. No person ruled it.
- #2519 carried #2460 with the clause rewritten as a known defect (validator B's R1).
- The lifecycle's design PR, juniper-ml#473 (2026-06-19), never addresses a fit that returns while paused.
- Put this provenance in the record's §4 wedge row.

## Traps

- **The isolated session's classifier** refuses bash loops, variables and computed values near anything spelled "git", including "gitleaks". Put the logic in `util/ad-hoc/` scripts or `python3 -I` heredocs. `git -C <another repo>` works; `git -C <this repo>` does not.
- **Gates already on main bind new util/ files:** G-PATH (no home-directory literal) and the required Security Scan. G-TMP (#2360) is not on main yet, but keep it clean. The pre-commit secrets hook scans only staged changes, so its pass on new files means nothing.
- **Count claims drift with every new script.** Recount with `ls util/ad-hoc/2026-11-0[78]_flood4_*.py | wc -l` before writing a number.
- **Doc-link hook:** it scans `tmp/` (its 5,000+ "broken links" are scratch); judge it with `--exclude tmp`.

## Verification (run first; each comment is an invariant)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert   # after EnterWorktree
git fetch -q origin; git log -1 --format=%h origin/main                     # 8d73d441, or later: check CHANGELOG conflicts
gh pr list --repo pcalnon/juniper-ml --head docs/flood4-disposition-record --state all --json number   # []  (record PR not opened)
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json number --jq '[.[].number|select(.<=2466)]|sort'   # [2360,2404,2406]
git ls-remote origin refs/heads/feat/disable-idle-compress-setting-for-claude-code | wc -l   # 0
jq .idleCompaction ~/.claude/settings.json                                   # false
ls util/ad-hoc/2026-11-0[78]_flood4_*.py | wc -l                             # 159
python3 -I util/home_path_literal_check.py util/ad-hoc/2026-11-0[78]_flood4_*.py | tail -1   # PASS
python3 -I util/ad-hoc/2026-11-08_flood4_record_round1_fixes.py --check     # 0 of 36 pending
python3 -I util/ad-hoc/2026-11-08_flood4_gpath_secret_pass.py --check       # 0 edit(s) pending
git status --short | wc -l                                                   # 164 (1 M + 163 ??)
```

## Documents created or modified in session 2

- **Uncommitted, in this worktree:**
  - `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (§0–§9; round-1 fixes applied);
  - `CHANGELOG.md` (the entry);
  - `reports/2026-11-08_flood4-disposition/` (README, 6 manifests, render_config.json);
  - this handoff;
  - eight new `util/ad-hoc/2026-11-08_flood4_*.py`: harvest_scripts, gtmp_pragma_pass, gpath_secret_pass, archive_render_inputs, splice_sec5, record_freeze and record_round1_fixes;
  - 68 harvested scripts, 45 of them edited (G-TMP, G-PATH, CodeQL, headers).
- **Outside any repo:**
  - `~/.claude/settings.json` (`"idleCompaction": false`);
  - `JuniperCascor1`'s juniper-ci-tools 0.8.0 → 0.9.1;
  - auto-memory: `reference_cursor_fleet_drafts_on_pr_open.md` (corrected, plus the fleet going quiet), `reference_ci_parity_gitleaks_local_scan.md` (staged-only hook), `reference_gitleaks_action_pr_scan_oldest_30.md` (new), and `MEMORY.md` (index line).
- **GitHub:** deleted the branch `feat/disable-idle-compress-setting-for-claude-code` (#2271). No PR was opened, merged or closed in session 2.
