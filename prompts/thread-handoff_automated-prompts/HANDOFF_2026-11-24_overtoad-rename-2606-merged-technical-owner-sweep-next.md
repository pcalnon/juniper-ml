# Handoff: Overtoad rename repair -- ml#2606 MERGED; the technical-owner sweep next

**Date**: 2026-11-24 (written about 05:25Z)
**From**: session 635b868c (ListAgents ref e59506, named "overtoad-rename-repair-2606-rebuilt-validated-upload-after-peer-prs"),
working in worktree `juniper-ml/.claude/worktrees/crispy-forging-falcon` (entered with EnterWorktree)
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_overtoad-rename-repair-2606-rebuilt-validated-upload-after-peer-prs.md` (on main via ml#2624)
**Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md` (states at 02:20Z, 04:20Z and DONE 05:06Z), `reference_ci_merge_mechanics_hub.md` (new code-scanning line)

---

## Goal

ml#2606 renamed some TECHNICAL "owner" tokens, Unix file and directory ownership, to "Overtoad". Put those back
to "owner" in ONE signed follow-up PR, review every candidate, and have the backup session (`a8a87d`,
"backup-phase-d-record-landed-…") review the hunks in its files before merging. Re-confirm merge approval with
the owner first: a handoff cannot carry an approval (memory `feedback_headless_merge_approval_policy.md`).

## Completed this session

- **ml#2624 MERGED** 02:38:05Z (`43a24183`): it archived both rename-repair handoffs of 2026-11-23, and the Sources
  row of `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` now names the first.
- **ml#2606 MERGED** 05:06:27Z as `5a04914448091479a56f4c94ac918fcd08bbe4af` (squash of `1f9884a5`, 2,085 files):
  - Order agreed with the peers: guard 1.4.0 (ml#2625), R52 (ml#2627), R49 (ml#2623), then #2606, armed alone while
    every live juniper-ml session held its merges.
  - Uploaded as 10 signed commits on main `9194bfb8`.
  - `df43dbba` fixed 7 CodeQL findings in the arc's own tools (6 file-not-closed, 1 empty-except); CodeQL's bot
    resolved its threads.
  - `1f9884a5` kept `util/ad-hoc/2026-10-05_gate_regression.py` at main's bytes: see Traps.
- **Post-merge check**: 2,084 files equal the local rebuild. The register and `juniper-service-core/CHANGELOG.md`
  merged three-way and differ from #2623's and #2627's commits by renamed tokens only. `CLAUDE.md` is still a
  symlink (mode 120000), and AGENTS.md reads `**Last Updated**: 2026-11-24`. Main's post-merge runs on `5a049144`:
  all 9 succeeded by 05:24Z, including CI/CD Pipeline, CodeQL Analysis and Post-Merge Main Verification.
- **Rebuild-tool rules added** (`util/ad-hoc/2026-11-23_pr2606_rebuild.py`, now on main):
  - `is_word_mention`: a quoted "owner" on a line that already says "Overtoad" names the word.
  - FIXUPS for `tests/test_headless_signing_preflight.py`: its literals assert bash CODE text, which stays main's.
  - `KEEP_MAIN`: files kept at main's bytes for merge protection.
- **Validation of the final tree** (on `a4d9e9c8`; the tree on `9194bfb8` is byte-identical):
  - symbol-loss: 0 findings in 1,433 files; the docs screen failed nothing; doc links pass;
  - pre-commit: all 2,086 files pass, with no file rewritten;
  - all 262 suites pass except the 4 local-only ones (the same 25 tests as the v2 baseline).
- **Peers told #2606 merged and their holds lifted**: `5774a5` (R-OBS-SC-2), `f9fa6e` (flood-4, whose #2626 was DRAFT
  for the hold), `a8a87d` (backup) and `ffffd3` (one-artifact).

## Remaining work

1. **Review the candidates.** `tmp/rename-repair-s2/unix_owner_candidates_5a049144.tsv` (this worktree) lists 563
   tokens in 199 files that #2606 renamed and whose ±45-character window holds ownership vocabulary. The net is
   broad, and most hits are the person ("the owner's YubiKey"). Regenerate it with
   `python3 tmp/rename-repair-s2/unix_owner_candidates.py <worktree> 515e16a0… 5a049144… <out.tsv>`.
   - **Known technical**, from session a8a87d, with line numbers on main `5a049144`:
     - `util/ad-hoc/2026-11-23_backup_slowdown_evidence.py:18` "(type, mode, Overtoad)"
     - `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` :275 "change
       Overtoad", :489 "every volume's Overtoad", :643 "mode and Overtoad", :803 "`/etc/duplicati/env`'s Overtoad"
     - `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` :424 "changed Overtoad",
       :1736 header "The Overtoad:group" (should read "Owner:group"), :2296 and :2311 "env file's Overtoad",
       :2728 "the copy's Overtoad", :2850 "change Overtoad"
   - **Also known**: `.github/workflows/ci.yml:1224` "(path, mode, Overtoad -- never content)".
   - **Blind spots that produced these** (in `classify`, `util/ad-hoc/2026-11-23_overtoad_rename_repair.py`):
     - a possessive before the token: in "file's owner" the before-word regex captures "s";
     - attribute lists: "mode, owner", "mode and owner";
     - verbs: "change owner";
     - an "Owner:group" header.
   - **Keep** "-owned", "re-owned" and "owned by". a8a87d confirmed #2606 left those correct.
2. **Build a targeted restore tool** in `util/ad-hoc/`. The rebuild tool works from #2606's old head and no longer
   applies. Given a reviewed list of `path:line` plus the token's occurrence index, the new tool should:
   - restore exactly that token from `515e16a0`'s line on current main's text;
   - refuse a line that differs beyond the token.
   Never touch records, pinned files, symlinks, the requirements domain or `KEEP_MAIN` files.
3. **Validate**: doc links (`--exclude tmp`); both screens via `git stash create`; pre-commit on the changed files;
   and the suites that read them, or the full list (~18 min) with
   `python3 util/ad-hoc/2026-11-23_run_ci_regression_suites.py --checkout . --out tmp/...`.
4. **PR**: open it with `util/open_signed_pr.py`, building each whole file from the SAME main as the branch base.
   Re-probe main just before `--execute`: if main moves between the read and the upload, the commit's parent is
   the newer main and the upload reverts it. Name every changed document in the body, and add `## Requirements`
   "References: none". Message a8a87d with the PR number.
5. **Merge**: message the live juniper-ml sessions to hold; then run
   `python3 util/safe_merge.py --pr N --repo juniper-ml --timeout 3300 --execute` in the background.
6. **Owner decisions to surface**:
   - R14 and R15, the sentry-sdk<3 caps (note rows R14/R15; session 5774a5's line holds them);
   - canopy#831 (Dependabot, BLOCKED);
   - main's CodeQL high alerts #1059/#1060 in `util/ad-hoc/2026-10-05_gate_regression.py`: fix or dismiss.
7. **MEMORY.md** is 23.5 KB, against the owner's 20 KB target. Retire closed arcs' lines into
   `project_closed_arcs_hub.md` and never strip hooks. The PostToolUse hook asks on every edit.
8. **Archive this handoff**: it is untracked here. Land it with the sweep PR or a `docs(handoff)` PR.

## Key context and traps

- **Merge protection.** main's ruleset has `strict=true` with 17 required contexts, and a `code_scanning` rule
  (CodeQL: `security_alerts_threshold: high_or_higher`, `alerts_threshold: errors`). A PR too large for CodeQL to
  diff counts EVERY open alert in every changed file as new. Edit no file that holds main's high or error alerts:
  list them first with `code-scanning/alerts?ref=refs/heads/main&state=open`.
- **Lane etiquette that worked**: agree an order, message each live session to hold, and get a "hold done" back.
  #2623 lost 3 cycles before that; #2606 then merged on its first green.
- **Command guard**: a `.github/` path, `<(git …)`, or `$(…)` with git in a chained command is refused. Put such
  steps in scripts under `tmp/rename-repair-s2/`, which holds `compare_to_ref.py`, `codeql_threads.py` and
  `watch_2606.py`, or run them as plain commands.
- **Evidence to keep** (retention rule):
  - `tmp/rename-repair-s2/` in this worktree;
  - the rebuild reports `rebuild_applied_*.tsv` in session 9d3fff65's scratchpad
    (`juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/9d3fff65-37dd-41e8-8fe6-7f66872deb14/scratchpad/`).

## Files

- **Changed in PRs**: ml#2624 (2 handoffs and the R-OBS-SC-2 note). ml#2606, which also carries the arc's 9 tools,
  with this session's edits to `util/ad-hoc/2026-11-23_pr2606_rebuild.py`, `…_pr2606_upload.py`,
  `…_overtoad_rename_repair.py` and `…_run_ci_regression_suites.py`.
- **Created, untracked here**: this handoff, and `tmp/rename-repair-s2/{regen,mention_lines,codeql_moved,codeql_threads,compare_to_ref,watch_2606,unix_owner_candidates}.py`
  with their outputs.
- **Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md`, `reference_ci_merge_mechanics_hub.md` and
  `MEMORY.md` (the arc's line).

## Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/crispy-forging-falcon
git log -1 --format='%h %s'          # 5a049144 (detached; later main is fine after a fetch)
git status --porcelain | wc -l        # 1: this handoff (untracked)
gh pr view 2606 -R pcalnon/juniper-ml --json state,mergeCommit   # MERGED 5a049144
wc -l tmp/rename-repair-s2/unix_owner_candidates_5a049144.tsv    # 563
```

## Git status

Detached HEAD at `5a049144` (main at writing). Branch `worktree-crispy-forging-falcon` still points at `81b8eaf7`.
Nothing is staged and there are no local commits. The only untracked file outside `tmp/` is this handoff.
