# Handoff: Overtoad rename PR repair -- juniper-ml#2606, recurrence#237 and deploy#281 next

**Date**: 2026-11-23 (written at about 19:40Z)
**From**: session crispy-forging-falcon (worktree `juniper-ml/.claude/worktrees/crispy-forging-falcon`)
**Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md` in the juniper-ml project memory dir

---

## Goal

Continue repairing the owner's 2026-11-20 "owner -> Overtoad" rename PRs and the failing checks they
caused. Next: **juniper-ml#2606**, then the two rename PRs that already MERGED (juniper-recurrence#237,
juniper-deploy#281), then CI follow-through and the owner's merge list.

### Owner rulings (2026-11-23, this session's dialogs; quoted option labels)

1. juniper-ml: **"Fix #2606 only"**. Do not carry #2605 forward; closing it is the owner's call.
2. Records: **"Revert edits to records (Recommended)"**. Archived release notes, handoffs, reports and
   study records keep their original text. The rename applies to living docs, code comments and config.
3. Template: **"Propagate via cascor re-pin"**. cascor#772 merges first. Agreed with the one-artifact-ports
   session: client rename PRs DROP their `publish*.yml` and `test_publish_one_artifact.py` edits, and its
   ports re-pin every copy after cascor#772 merges.
4. B914: **"Merge the literals (Recommended)"**. Never suppress, never pin.
5. Symlinks: **"Rebuild as one signed commit (Recommended)"**, for cascor#772, data#547 and canopy#830.
   The signed-commit API cannot write a symlink, and canopy's Gitleaks scans every commit in the PR.
   That ruling covers those three PRs only; ASK before rebuilding #2606 the same way.

### Root cause (all rename PRs)

The rename was a blind `sed`-style substitution over every file, sometimes without `g` (partial lines),
and in juniper-ml also `Owner -> The Overtoad`. It hit code identifiers (sequence-safety LOST),
`/repos/{owner}/{repo}` placeholders, "ownership", technical owners, symlinks (`sed -i` writes a copy over
the link), byte-pinned files, hash-locked records and filename references. Every PR also edited
AGENTS.md without bumping `**Last Updated**:`.

## Completed (every commit GitHub-signed and verified)

| PR | State at 19:25Z | What |
|----|-----------------|------|
| juniper-ml#2608 | green | cap `sentry-sdk<3` in `juniper-observability/pyproject.toml` (3.0.0, PyPI 2026-11-23 09:30Z, removed `send_default_pii`) |
| canopy#832 | running | B914 literal merges (47) + bugbear floor `>=26.11.22`. **The only repo really exposed** (flake8 7.3.0) |
| cascor#774, data-client#268, cascor-client#202, cascor-worker#236, juniper-ml#2609 | running / green | B914 merges, PREVENTIVE: these run flake8 7.1.1, where bugbear 26.11.22 cannot install, so B914 never runs. cascor#774 has a follow-up re-extracting 3 `juniper-cascor-model/` copies (`juniper-cascor-model/tests/test_drift.py` pins them to `src/`) plus a black re-join. #2609 adds `util/ad-hoc/2026-11-23_b914_merge_literals.py` |
| cascor-worker#234 `aec01e80`, cascor-client#201 `bd5bda71`, data-client#267 `8a1646d1`, harcot#28 `2611c4a7` | all green; harcot CLEAN | rename repaired by a follow-up commit |
| cascor#772 `31136d64`, data#547 `aec59c69`, canopy#830 `c93c1e84` | cascor/data pending; canopy red on B914 only (needs #832) | rebuilt as ONE commit on the PR's base. Old heads kept at `backup/task-owner-is-the-overtoad-1e6e877a` / `-81d0d991` / `-d68af0ee` |

## Remaining work

1. **juniper-ml#2606** (branch `worktree-humming-stargazing-papert`; head `0658e854` when last read, so re-read it first).
   - Failing checks: AGENTS date, `CI — juniper-observability` (sentry 3; fixed once #2608 merges and the
     branch is updated), Release-Train Archive Guard (edits under `notes/releases/`, so revert the records),
     Sequence Safety (29 LOST: `owner_of`, `heading_owner`, `test_owner_option_shapes_the_url` ...),
     Documentation Links, Regression Tests and CodeQL (not yet examined).
   - Regression Tests: `tests/test_thread_handoff_archive.py` flags two non-canonical
     `HANDOFF_2026-11-16__…` names (double underscore) and handoff references whose filenames contain
     "owner". CI stops at the first failing suite, so run the whole list locally (`docs/REFERENCE.md`
     "Running every suite").
   - **Audit the conflict resolutions first, `docs/REFERENCE.md` before anything else** (owner's request).
     #2606 replays main's history as 111 commits, carries 354 files that #2605 lacks (mostly `util/ad-hoc/`
     plus 60 handoff prompts), and its `docs/REFERENCE.md` differs from #2605's by about 4,700 lines.
   - main has moved: #2610 (plan v1.15.17, `docs/REFERENCE.md` 0.6.78 row, 30 ad-hoc scripts) and #2614
     merged. Re-substitute `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`
     and `docs/REFERENCE.md` on the new main.
   - Tool globs for juniper-ml. Records: `notes/releases/*`, `notes/history/*`, `notes/legacy/*`,
     `notes/pull_requests/*`, `prompts/thread-handoff_automated-prompts/*`, `reports/*`. Pinned:
     `.github/workflows/publish*.yml`, `tests/test_publish_one_artifact.py` (sha256-pinned).
   - NEW record files that #2606 adds have no base to restore. Ask the owner.
   - Message the one-artifact successor before arming or merging #2606.
2. **juniper-recurrence#237** (merged 22:31Z, `93a28202`) and **juniper-deploy#281** (merged 22:43Z,
   `552756a1`). Diff each merge against its first parent for the same collateral; `git show --raw` reveals
   `120000 -> 100644`. Open repair PRs against current main.
3. **CI follow-through.**
   - **cascor#772 MERGED 2026-11-23 19:35:14Z (`e9c86f83`); the one-artifact successor already knows.** It runs in
     worktree `ethereal-munching-peacock` as `one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772 [ffffd3]`
     and continues
     `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md`.
     Next it opens the cascor sweep PR `fix/publish-one-artifact-sweep` (11 files; no overlap with cascor#774),
     then one port PR per repo: canopy, data, data-client, cascor-client, cascor-worker, recurrence and juniper-ml.
     It messages before arming anything that touches a file an open rename PR touches. **Message it before
     arming or merging ml#2606**, because the ml port also touches juniper-ml's `publish*.yml` and
     `tests/test_publish_one_artifact.py`.
   - After canopy#832 merges: `update-branch` canopy#830, and comment `@dependabot rebase` on canopy#831.
4. **Owner merges** (headless-merge policy: only on the owner's explicit approval per PR). Suggested order:
   #2608 and canopy#832 first (cascor#772 already merged at 19:35Z); then the other rename PRs
   after `update-branch`. The preventive B914 PRs can merge in any order, or close.
5. **Owner decisions to surface.**
   - Cut a juniper-observability 0.4.3 carrying the sentry cap.
   - Cap sentry in cascor, data and canopy, whose floors are an uncapped `sentry-sdk>=2.0.0`. cascor's
     `main.py` also passes `send_default_pii` itself.

## Key context and traps

- **The recursive sed also edited uncommitted files in worktrees** under `juniper-ml/.claude/worktrees/`
  that existed on 11-20 (this one had about 110). The juniper-ml PRIMARY checkout carries it too. Run
  `git status` before any whole-file upload. Saved: `tmp/b914/crispy-worktree-rename-collateral-plus-b914.patch`.
- `createCommitOnBranch` cannot write a symlink or set an exec bit, so a rebuild leaves those paths untouched.
- My first B914 pre-commit check in four sibling repos was VACUOUS: a relative `--list` path with
  `cwd=<sibling>` raised FileNotFoundError (exit 1), and my filter printed "all passed". Use absolute
  paths, and treat any non-zero exit as a failure.
- `"" in "abc"` is True: guard every character-class membership test. `ast` columns are UTF-8 bytes;
  `tokenize` columns are characters.
- harcot study manifests hash `study.yaml`. The original text was recovered by hash
  (`tmp/rename/harcot_manifest_check.py`); do the same for any hashed record.
- Repair-tool rules worth knowing: "X owner" with a qualifying noun or adjective is technical, "owner of"
  is technical, and `owner-<verb>` is the person.

## Files

- **Created**: `util/ad-hoc/2026-11-23_b914_merge_literals.py` (in #2609);
  `util/ad-hoc/2026-11-23_overtoad_rename_repair.py` (UNTRACKED, not in any PR; commit it with the #2606
  repair; `--self-test` covers 33 cases); `tmp/pr-triage/*`, `tmp/b914/*` and `tmp/rename/*` launchers
  and logs in this worktree (gitignored; keep under the retention rule); this handoff.
- **Changed in PRs**: listed in the table above.

## Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/crispy-forging-falcon
python3 util/ad-hoc/2026-11-23_overtoad_rename_repair.py --self-test      # 33 cases, 0 failures
python3 util/ad-hoc/2026-11-23_b914_merge_literals.py --self-test         # 18 merge + 5 refusal cases
python3 tmp/pr-triage/ci_status.py                                        # every tracked PR's checks
gh pr view 2606 -R pcalnon/juniper-ml --json headRefOid,mergeStateStatus
git -C ../../../../juniper-cascor ls-remote origin 'refs/heads/backup/*'  # one backup ref per rebuilt PR
```

## Git status

- Branch `worktree-crispy-forging-falcon` at `81b8eaf7` (behind main).
- Uncommitted: 74 `tests/*.py` B914 merges (the content of #2609); untracked: the two tools above.
- Sibling worktrees in `Juniper/worktrees/`: six `*--fix--b914-merge-literals--*` and seven
  `*--fix--overtoad-rename-repair--20261123-0700--*` (detached at the OLD PR heads). Remove each after
  its PR merges (`notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`).
