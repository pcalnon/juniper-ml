# Handoff: Overtoad rename repair -- #2606 rebuilt and validated; upload after the peers' ml PRs land

**Date**: 2026-11-23 (written about 22:10Z)
**From**: session 9d3fff65 (worktree `juniper-ml/.claude/worktrees/crispy-forging-falcon`, named
"overtoad-rename-repair-ml-2606-recurrence-deploy-next")
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_overtoad-rename-repair-ml-2606-recurrence-deploy-next.md`
(untracked in this worktree)
**Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md` (rulings 1-8, state at ~21:45Z)

---

## Goal

Continue the Overtoad rename PR repair: **regenerate juniper-ml#2606 on the main that includes ml#2618,
ml#2619 and guard 1.4.0, validate, upload, follow CI, message the peers, merge.** The owner granted merge
approval for this arc's PRs in session 9d3fff65; re-confirm it with the owner before merging #2606, because
a handoff cannot carry an approval (memory `feedback_headless_merge_approval_policy.md`).

## Completed this session

- **Merged** (safe_merge or the armed net): ml#2608 (sentry<3), canopy#832, canopy#830, data#547,
  cascor#774, data-client#268, cascor-client#202, worker#236, harcot#28, ml#2609 (22:05Z, `874ddefd`; its
  CodeQL thread fixed by `82a10e63`). **Closed** ml#2605 (ruling 8).
- **deploy#281 repaired by deploy#285** (merged 21:37Z, `aae1d78f`): 5 technical tokens restored.
- **recurrence#237 repaired by recurrence#238** (merged 21:38Z, `85be5fd7`): its only collateral, the
  `juniper-recurrence-client/CLAUDE.md` symlink, restored through a GitHub-signed `revertPullRequest` plus a
  signed restore of the other 21 files. Verified mode 120000 on recurrence main. Its publish template copies
  are left to the one-artifact ports (ruling 3).
- **#2606 audit and rulings 5-8** (owner, ~20:45Z): rebuild on main; keep the 349 new ad-hoc scripts with
  identifiers fixed; restore the 4 new handoffs' text; close #2605.
- **#2606 rebuild built and validated** on main `cbb13154` (this worktree, detached HEAD; v3 applied:
  1,691 tracked files modified + 354 generated new files; report `$S/rebuild_applied_cbb13154_v4.tsv`):
  symbol-loss 0 findings, docs-additions OK, doc links PASSED, every regression suite passes except the 4
  documented local-only ones (`test_workflow_script_paths`, `test_a0_restore_scripts`,
  `test_e2e_f037_render_census`, `test_replay_redrive_stack_refusal`: TMPDIR-in-a-checkout fixtures);
  pre-commit passes on all 2,056 upload files (v2's only failure, shellcheck SC2034 on two renamed bash
  `local` declarations, is fixed in v3 by the shell rule; v3's nine changed shell files and the nine tools
  re-checked: pass). The full suite list ran on v1; v2/v3 differ only in the requirements domain (now main's
  bytes), bold field labels, 3 anchors, 3 test literals and 9 shell files: re-run the full list after the
  final regeneration anyway.

## Remaining work

1. **Wait for the three peer PRs** (agreed by message; do not regenerate or arm before them):
   - ml#2619 (session 2222e504 [9660dc], R-OBS-SC-2 inventory): **MERGED 2026-11-23 22:48:05Z,
     `5d22fbe93841489a7bf7ad2a9240ab306d5c9207`** (that session's message). Done.
   - ml#2618 (flood-4 session 10 [f9fa6e], D-14): **MERGED 2026-11-23 22:31:17Z,
     `eeaa191c34fb2a11e8f241d62365d4007400ff0d`**. Done.
   - **Only guard 1.4.0 remains.** The owner has ruled on it (land it naming every still-open spelling, keep
     the 3 s cap); flood-4 session 10 is rebuilding it on main, PR expected about 2 h after 23:00Z. It changes
     `CHANGELOG.md`, `docs/REFERENCE.md`, `tests/test_claude_agent_guard{,_brace_cap}.py`,
     `util/claude_agent_guard.py` and adds 11 `util/ad-hoc/2026-11-16_flood4r2_r18-guard_*.py` (not #2606's
     `..._val_r18-guard-code_*` files). That session (or its successor, whose handoff names this line) messages
     the merge commit; it offered to yield or hold if #2606 is ready first. The rebuild re-derives any file #2606
     added that main now has from main's text, so a peer's verified copy is never overwritten.
   - Guard 1.4.0 (same session, after the owner answers it): it rewrites `util/claude_agent_guard.py`.
2. **Reset and regenerate** in this worktree (all git in this worktree; the guard refuses other worktrees):
   ```bash
   S=<this session's scratchpad: juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/9d3fff65-37dd-41e8-8fe6-7f66872deb14/scratchpad>
   python3 util/ad-hoc/2026-11-23_pr2606_rebuild.py --worktree . --old-base x --old-head x --today x --reset "$S/rebuild_applied_cbb13154_v4.tsv"
   git fetch origin main && git checkout --detach origin/main
   python3 util/ad-hoc/2026-11-23_pr2606_rebuild.py --worktree . --old-base 81b8eaf7 --old-head 0658e854 \
     --today "$(date -u +%F)" $(cat "$S/rebuild_original_args.txt") --report "$S/rebuild_applied_<main8>.tsv" --apply
   ```
   `rebuild_original_args.txt` holds the four `--original` transcript versions (`$S/handoffs/h{5,6,8,9}.orig`).
3. **Validate again**: `juniper-check-doc-links ... --exclude tmp --cross-repo skip` (AGENTS.md invocation);
   `git stash create` then both screens with `--base HEAD --head <sha>` (memory
   `reference_sequence_safety_local_repro.md`); `python3 util/ad-hoc/2026-11-23_run_ci_regression_suites.py
   --checkout . --out tmp/rename-repair-s2/regress_<main8>` (~60 min); pre-commit with
   `git add -N --pathspec-from-file=...` first (`xargs` into git is refused).
4. **Upload**: `python3 util/ad-hoc/2026-11-23_pr2606_upload.py --worktree . --old-head 0658e8549e45b59b4ba83550524d73b4b4b570b3 --report "$S/rebuild_applied_<main8>.tsv" --extra <each of the 9 tools in tmp/rename-repair-s2/upload_tools.txt>`
   (dry run first; then `--execute`; ~10 signed commits of 4 MB; backup ref, temp branch, blob verification,
   one force ref update). Undo the intent-to-add first (the tool refuses any status other than ` M`).
   Exclude `util/ad-hoc/2026-11-23_b914_merge_literals.py` (on main via #2609).
5. **PR**: set title and body with `gh api -X PATCH repos/pcalnon/juniper-ml/pulls/2606 -f title=... -F body=@tmp/rename-repair-s2/pr2606_body.md`
   (`gh pr edit` is broken on gh 2.46). Update its counts and the validation lines first.
6. **CI**: CodeQL reports pre-existing alerts whose fingerprints the rename moved; check each against main's
   open alerts (`code-scanning/alerts?ref=refs/heads/main`), reply with that evidence and resolve the thread.
   The 2 high-severity ones (`util/ad-hoc/2026-10-05_gate_regression.py` 415/417) are open on main.
7. **Message before arming**: flood-4 session 10 and the one-artifact successor (session ffffd3, worktree
   ethereal-munching-peacock; it asked for this at ~22:55Z; its cascor sweep is juniper-cascor#777, and one port
   PR per repo follows; it ports `publish*.yml` and `tests/test_publish_one_artifact.py`, which the rebuild never
   touches). It believed data#547 was still open; it was told #547 merged at 20:39:16Z (`2ad7b7b5`). Then
   `util/safe_merge.py --pr 2606 --repo juniper-ml --execute` in the background, after the owner re-confirms.
8. **Owner decisions to surface**: R14 (which observability release carries the sentry cap; 0.4.3 is
   reserved for R-OBS-SC-3, plan v1.15.17) and R15 (sentry<3 caps in cascor, data, canopy), both in
   `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (ml#2619);
   canopy#831 (Dependabot, green, outside this arc's approval).
9. **Archive**: both handoffs in this worktree are untracked; land them in a `docs(handoff)` PR. In the same
   PR, make the Sources row of `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`
   name the predecessor handoff by its filename: it now reads "the rename-repair line's handoff of 2026-11-23 …
   not archived", because `tests/test_thread_handoff_archive.py` fails a notes/ file that cites an unarchived
   `HANDOFF_*.md`. MEMORY.md is 23.7 KB (target 20 KB: retire entries, never strip hooks).

## Key context and traps

- **The rebuild never copies the old head's version of a file main has**, so main's newer text cannot be
  reverted; the upload sits on the exact main it was generated from, so a later main can only conflict.
- Rules learned from the full suite run (in the tool): the requirements domain stays main's bytes
  (`TECHNICAL_DOMAINS`: "owner" is the owning repo's field, `_META_RE` parses `**Owner**:`); bold field
  labels are technical; `tests/test_fleet_supervisor_contract.py` needs lowercase literals (`FIXUPS`);
  same-file anchors follow renamed headings (`remap_anchors`); in shell files only comment text is renamed
  (`shell_comment_start`: `local x owner` declared a variable). A NEW failing suite after regeneration is
  most likely another lowercased comparison or a field label: fix the rule in the tool, never the output.
- Peers' new text says "owner" on purpose (they write as main does); the regeneration renames it.
- The worktree-isolation guard refuses any command whose text contains `git` in a complex form, including
  `.github/` paths, `git/trees` URLs, `xargs` into git and a cwd below the worktree root (memory
  `reference_worktree_isolated_session_command_refusals.md`, 2026-11-23 additions).
- Local-only noise: never leave other repos' files under this worktree's `tmp/` while the suites run
  (`test_release_train_registry` walks for `pyproject.toml`).

## Files

- **Created (untracked here, upload with #2606)**: `util/ad-hoc/2026-11-23_rename_pr_damage_audit.py`,
  `util/ad-hoc/2026-11-23_pr2606_rebuild.py`, `util/ad-hoc/2026-11-23_pr2606_upload.py`,
  `util/ad-hoc/2026-11-23_transcript_file_original.py`, `util/ad-hoc/2026-11-23_symlink_regressions.py`,
  `util/ad-hoc/2026-11-23_deploy_281_technical_restore.py`, `util/ad-hoc/2026-11-23_recurrence_237_symlink_restore.py`,
  `util/ad-hoc/2026-11-23_run_ci_regression_suites.py`; plus the predecessor's
  `util/ad-hoc/2026-11-23_overtoad_rename_repair.py`; this handoff; `tmp/rename-repair-s2/` (lists, logs, the
  #2606 body draft `pr2606_body.md`).
- **Changed in PRs**: deploy#285, recurrence#238, ml#2609 (`util/ad-hoc/2026-11-23_b914_merge_literals.py`).
- **Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md`, `reference_worktree_isolated_session_command_refusals.md`,
  new `reference_signed_symlink_restore_via_revert_pr.md`, `MEMORY.md`.

## Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/crispy-forging-falcon
git log -1 --format='%h %s'                 # cbb13154 (detached) until you regenerate
git status --porcelain | cut -c1-2 | sort | uniq -c   # 1691 " M", 366 "??" (354 generated + 9 tools + b914 tool + 2 handoffs)
gh pr view 2606 -R pcalnon/juniper-ml --json headRefOid,mergeStateStatus   # still 0658e854 (not uploaded)
for n in 2618 2619; do gh pr view $n -R pcalnon/juniper-ml --json state,mergeCommit; done
python3 util/ad-hoc/2026-11-23_overtoad_rename_repair.py --self-test     # 33 cases, 0 failures
```

## Git status

Detached HEAD at `cbb13154` (branch `worktree-crispy-forging-falcon` still at `81b8eaf7`); the applied
v3 rebuild is uncommitted; nothing staged (no intent-to-add entries); no local commits.
