# Handoff — Cursor flood-3 follow-ups: five fixes merged, three releases on PyPI, juniper-ci-tools 0.9.1 at the PyPI gate

**Date**: 2026-10-10
**Arc**: Cursor flood-3 disposition (2026-10-08) and the owner-requested follow-ups (2026-10-08 and 2026-10-10)
**Record of the arc**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`. Its §4 lists the defects, §8 the open items and §9 the PRs, and it was last updated by ml#2206.

---

## Goal

Continue the Cursor flood-3 follow-up arc. Everything the owner asked for is done except three closing items:

- the juniper-ci-tools 0.9.1 PyPI gate, which only the owner approves;
- the ci-tools notes-archive PR ml#2205 merging;
- a final status touch of §8 of the flood-3 record (`notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`).

After that, the open §4 defects are a backlog for the owner to prioritise. None of them has been requested.

## Completed (verified on `main`, GitHub or PyPI)

- **Disposition, 2026-10-08.** 116 Cursor flood-3 draft PRs across eight repos were each merged, carried into a merged consolidation PR, superseded, or closed as incorrect. The record is above, opened by ml#2185 and updated by ml#2194 and ml#2206.
- **`ANTHROPIC_API_KEY`.** It is set in all seven repos that lacked it:
  - juniper-data-client, juniper-cascor-client and juniper-cascor-worker on 2026-10-08;
  - juniper-data, juniper-cascor, juniper-canopy and juniper-deploy on 2026-10-10.

  Only juniper-ml had it before. Each time the value came from the owner's shell `ANTHROPIC_API_KEY` (validated first: `GET /v1/models` returned 200). It was written to a 0600 dotenv file on tmpfs, set with `gh secret set -f`, and the file was shredded. The value never appeared in argv or output.
- **The data-client `t` / `dt` check** is accepted as written (owner ruling, §4 of the record).
- **Five defects fixed.** Everything is merged, and a post-merge blob comparison reads SAME:
  - `FailedAuthThrottle.check()` grew one entry per client IP. Fixed by ml#2187 (juniper-service-core), juniper-cascor#710 and juniper-data#476. juniper-data held a third copy that the record had not named. Each copy has its own regression test, and each test fails against the old code with `assert 1000 == 0`.
  - `util/worktree_cleanup.bash` printed an empty "commits would be lost" list. Fixed by ml#2187 (version 1.1.1).
  - Canopy's `lockfile-update.yml` comment described `[dependabot skip]` backwards. Fixed by juniper-canopy#730. The tag itself stays on purpose, because each Dependabot rebase re-runs the regen.
  - Sequence Safety was documented as advisory although it is a required check. Fixed by ml#2187, juniper-cascor#710, juniper-cascor-client#178, juniper-cascor-worker#207, juniper-data#476, juniper-canopy#730, juniper-deploy#244, juniper-recurrence#194 and juniper-data-client#231. cascor#710 also corrected the CodeQL claims, since cascor requires `Analyze (python)`.
  - juniper-ci-tools read a `#` comment inside a fenced code block as a heading. Fixed by ml#2187 with a CommonMark-fence-aware screen.
- **Released and on PyPI.** The owner approved each gate, and `/pypi/<pkg>/<ver>/json` returned 200 on 2026-10-10:

  | package | version | bump PR | notes PR | also |
  |---|---|---|---|---|
  | juniper-observability | 0.4.1 | ml#2186 | ml#2188 | |
  | juniper-service-core | 0.7.1 | ml#2189 | ml#2193 | |
  | juniper-data | 0.17.0 | data#477 | ml#2191 | GHCR image tags `0.17.0`, `0.17` and `latest` |

  The security template's advisory placeholders were filled after each cut, in both the GitHub Release body (`gh release edit`) and the archived notes.
- **juniper-ci-tools 0.9.1.** Bump ml#2204 merged at `be3314dc`. Release `juniper-ci-tools-v0.9.1` was cut at 2026-10-10T10:42:59Z. Build and TestPyPI are green, and `Publish to PyPI` waits at the `pypi` environment in run 38045867684.

## Remaining work

1. **Owner:** approve run 38045867684's `pypi` gate. Never approve it from a session, even though `current_user_can_approve` reads `true` (memory `feedback_deploy_approvals_paul_manages.md`). Afterwards, confirm `https://pypi.org/pypi/juniper-ci-tools/0.9.1/json` returns 200. The eight consumer repos pin `>=0.9.0,<0.10.0`, so their next install picks it up with no change.
2. **ml#2205** (`release-notes/juniper-ci-tools-v0.9.1`, the archive of `notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.9.1.md`) is armed for squash auto-merge, and the shepherd was still running at handoff. Confirm it is MERGED. If it is still BEHIND, run `util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo pcalnon/juniper-ml --pr 2205`.
3. **Record touch, after items 1 and 2.** §8 of the record still lists "approve the `pypi` gate of the juniper-ci-tools 0.9.1 release" as an owner decision. Mark it resolved. Open it as a docs-only PR through `util/open_signed_pr.py`, which makes the GitHub-signed commit.
4. **Open §4 defects.** Backlog only; the owner has not asked for these.
   - juniper-ml:
     - `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py` exits 1 when every column is constant.
     - `2026-10-05_rerun_after_actions_outage.py:55` aborts on a dict-shaped `components`.
     - The stale-docs bundle in row "stale on `main`, outside every PR", which includes the `--params` claims in `run_experiment.py`.
     - `2026-10-04_replay_redrive.py` has a dead `if not snap:` check.
   - juniper-data and juniper-data-client: the `pr-budget-alarm.yml` header claims a `jq` failure only warns.
   - juniper-data:
     - The Quality Gate passes when an optional lane is cancelled.
     - The cheatsheet links a moved anchor in `AGENTS.md`.
     - `docs/ci_cd/CICD_MANUAL.md:456` says CodeQL doesn't block, and the cheatsheet's workflow list is missing entries.
   - data-client, cascor-client and cascor-worker: a latent `base64` failure in `lockfile-update.yml`.
   - juniper-recurrence: `memory-budget.yml:23-25` says Memory Budget is not required, but it is.
   - cascor-client, cascor-worker, deploy and recurrence: the `main-verify.yml` header describes the catch-up base wrongly.
   - juniper-cascor:
     - `docs/ci_cd/BRANCH_PROTECTION.md` lists 6 of the 24 required checks.
     - `ci.yml:988` and `conf/memory_budget.json:36` say there is no `docs/REFERENCE.md`.
     - `docs/DOCUMENTATION_OVERVIEW.md:811-812` has stamps that #709 put inside a template.
   - All repos: the `claude.yml` header says the key is "set at the org level".
   - Optional: add a `tests/test_service_fork_drift.py` guard for the throttle fix. It needs a defect-register `APD-` row filed under the register's five-touch protocol first.
5. **Cleanup.**
   - 12 `juniper-ml/.claude/worktrees/agent-*` worktrees and `worktrees/juniper-ml--flood3-docs-assembly--20261008` remain from 2026-10-08. A worktree-isolated session cannot `git -C` sibling juniper-ml worktrees. The owner's command for them is in the 2026-10-08 report; everything in them is on `main`.
   - This session's worktree `.claude/worktrees/melodic-hugging-rabin` holds only copies of files that are already on `main`.
6. **Not this arc's:** ml#2190, another session's draft that raises the `[servers]` floor to `juniper-data>=0.17.0`. Its precondition, 0.17.0 on PyPI, now holds.

## Key context and traps

- **Merge approval** covered this arc's fixes and releases only. It does not carry over. Ask again for any new work (memory `feedback_headless_merge_approval_policy.md`).
- **Release-train traps.** These are in memory `reference_release_train_ceremony_traps_2026-09-09.md`, items 1–6 of the 2026-10-08 section:
  - Run `detect.py --local-git`. API mode counts repo-wide `feat:` commits, so it proposes minor wrongly.
  - `propose.py` misses some version carriers: observability's `tests/test_public_api.py` pin and data's `__init__.py` fallback.
  - Date proposals by the UTC day CI runs on. juniper-data's `AGENTS.md` gate rejects a future date.
  - The ceremony can report `PENDING_PYPI_APPROVAL` early. Read the run's `pending_deployments` instead.
- **Worktree-isolated session limits.** These are refused:
  - loops, `$(…)` or pipes around `git` / `gh`;
  - piping into `gh`, which is why secrets go through `gh secret set -f <0600 dotenv>`;
  - `git -C <sibling juniper-ml worktree>`.

  Allowed: `git worktree add|remove <centralized path>` with no `-C`, and `git -C <other repo>`.
- **Commits** go only through GraphQL `createCommitOnBranch`: `util/open_signed_pr.py` and `util/push_signed_commit.py`. A local `git commit` hangs on the YubiKey. Split uploads over about 300 KB; the API can return HTTP 499 or 502.

## Verification commands

```bash
gh pr view 2205 --repo pcalnon/juniper-ml --json state,mergeStateStatus
gh run view 38045867684 --repo pcalnon/juniper-ml --json jobs --jq '.jobs[] | .name + " " + .status + " " + (.conclusion // "")'
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ci-tools/0.9.1/json
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-data/0.17.0/json
gh secret list --repo pcalnon/juniper-deploy | grep ANTHROPIC_API_KEY
```

## Git status at handoff

- juniper-ml `main` is at `94c75d27` (ml#2206) or later.
- The only open branches from this arc are `release-notes/juniper-ci-tools-v0.9.1` (ml#2205) and this handoff's PR branch.
- The session worktree `melodic-hugging-rabin` is detached at `81d3fbb3` with uncommitted copies of files now on `main`. Nothing is staged and nothing in it is unique.
