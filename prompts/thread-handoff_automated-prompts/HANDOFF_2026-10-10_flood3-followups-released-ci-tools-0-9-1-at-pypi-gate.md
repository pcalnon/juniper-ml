# Handoff — Cursor flood-3 follow-ups: five fixes merged, three releases on PyPI, juniper-ci-tools 0.9.1 at the PyPI gate

**Date**: 2026-10-10
**Arc**: Cursor flood-3 disposition (2026-10-08) and the owner-requested follow-ups (2026-10-08 and 2026-10-10)
**Record of the arc**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, written `…FLOOD-3-DISPOSITION.md` below. Its §4 lists the defects, §8 the open items and §9 the files changed. ml#2206 last updated it.
**Validated**: by three independent validators, every finding re-probed before it was applied. See § Validation.

---

## Goal

Continue the Cursor flood-3 follow-up arc. Everything the owner asked for is done except two closing items:

- the juniper-ci-tools 0.9.1 PyPI gate, which only the owner approves;
- a final status touch of `…FLOOD-3-DISPOSITION.md` (header, §4, §8 and §9).

Two follow-ons need an owner decision and have not been requested:

- **Delivering the released fixes.** No running service has them yet (item 3).
- **The open defects in `…FLOOD-3-DISPOSITION.md` §4** (item 4).

## Completed (verified on `main`, GitHub or PyPI)

- **Disposition, 2026-10-08.** 116 flood-3 draft PRs across eight repos (115 from Cursor, plus one from Copilot, juniper-data#454) were each merged, carried into a merged consolidation PR, superseded, or closed as incorrect. ml#2185 opened `…FLOOD-3-DISPOSITION.md`, and ml#2194 and ml#2206 updated it.
- **`ANTHROPIC_API_KEY`.** It is set in the seven repos that run `claude.yml` and lacked it:
  - juniper-data-client, juniper-cascor-client and juniper-cascor-worker on 2026-10-08;
  - juniper-data, juniper-cascor, juniper-canopy and juniper-deploy on 2026-10-10.

  Only juniper-ml had it before. Each secret's `created_at` shows that: juniper-ml's is 2026-02-24, and the other seven are from 2026-10-08 or 2026-10-10. juniper-recurrence has no `claude.yml`, and no secret.

  Each time the value came from the owner's shell `ANTHROPIC_API_KEY`, validated first (`GET /v1/models` returned 200). It was written to a 0600 dotenv file on tmpfs, set with `gh secret set -f`, and the file was shredded.

  The value never appeared in output or in the transcript. It **was** in `curl`'s argv while the validation call ran, because that call passed `-H "x-api-key: ${ANTHROPIC_API_KEY}"`. The key traps below say how to avoid that.
- **The data-client `t` / `dt` check** is accepted as written (owner ruling; `…FLOOD-3-DISPOSITION.md` §4).
- **Five defects fixed.** Everything is merged, and the post-merge blob comparison read SAME at merge time.

  It was re-run on 2026-10-10 with `util/ad-hoc/2026-10-08_fleet_flood3_postmerge_verify.py --extra <repo>:<pr>` over all nine PRs, and nothing DIFFERS. Every code and test file is still SAME. The CHANGELOG, docs and `ci.yml` files that later commits touched read MOVED.

  The five fixes:
  - `FailedAuthThrottle.check()` grew one entry per client IP. Fixed by ml#2187 (juniper-service-core), juniper-cascor#710 and juniper-data#476. juniper-data held a third copy. Each copy has its own regression test, and each test fails against the old code with `assert 1000 == 0`.
  - `util/worktree_cleanup.bash` printed an empty "commits would be lost" list. Fixed by ml#2187 (version 1.1.1).
  - Canopy's `lockfile-update.yml` comment described `[dependabot skip]` backwards. Fixed by juniper-canopy#730. The tag stays on purpose, because each Dependabot rebase re-runs the regen.
  - Sequence Safety was documented as advisory although it is a required check. Fixed by ml#2187, juniper-cascor#710, juniper-cascor-client#178, juniper-cascor-worker#207, juniper-data#476, juniper-canopy#730, juniper-deploy#244, juniper-recurrence#194 and juniper-data-client#231. cascor#710 also corrected the CodeQL claims, since cascor requires `Analyze (python)`.
  - juniper-ci-tools read a `#` comment inside a fenced code block as a heading. Fixed by ml#2187 with a CommonMark-fence-aware screen.
- **Released and on PyPI.** The owner approved each gate, and `/pypi/<pkg>/<ver>/json` returned 200 on 2026-10-10:

  | package | version | bump PR | notes PR | also |
  |---|---|---|---|---|
  | juniper-observability | 0.4.1 | ml#2186 | ml#2188 | |
  | juniper-service-core | 0.7.1 | ml#2189 | ml#2193 | |
  | juniper-data | 0.17.0 | data#477 | ml#2191 | GHCR image tags `0.17.0`, `0.17` and `latest` |

  The advisory placeholders of `notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md` were filled after each cut. That covers each GitHub Release body (`gh release edit`) and each archive: `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md`, `…_juniper-service-core_v0.7.1.md` and `…_juniper-data_v0.17.0.md`.
- **juniper-ci-tools 0.9.1.**
  - Bump ml#2204 merged at `be3314dc`.
  - Release `juniper-ci-tools-v0.9.1` was cut at 2026-10-10T10:42:59Z.
  - The notes archive, ml#2205 (`notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.9.1.md`), merged at 11:09:10Z as `eb41ca60`, and the blob on `main` reads SAME.
  - Build and TestPyPI are green. `Publish to PyPI` waits at the `pypi` environment in run 38045867684, and the version endpoint returns 404 until it is approved.

## Remaining work

1. **Owner:** approve run 38045867684's `pypi` gate.
   - Never approve it from a session, even though `current_user_can_approve` reads `true` (memory `feedback_deploy_approvals_paul_manages.md`).
   - Afterwards, confirm `https://pypi.org/pypi/juniper-ci-tools/0.9.1/json` returns 200.
   - The eight consumer repos pin `juniper-ci-tools>=0.9.0,<0.10.0` in their workflows, with no lockfile pin, so their next CI install picks it up with no change.
2. **Record touch, after item 1.** Update `…FLOOD-3-DISPOSITION.md` in four places:
   - the header `**Updated**` line, which says 0.9.1 was "cut";
   - the §4 juniper-ci-tools row, to add "on PyPI (200)";
   - §8: resolve the bullet "Owner decision: approve the `pypi` gate of the juniper-ci-tools 0.9.1 release", refresh the ml#2190 bullet (item 6), and fix the "five-touch" wording (item 4);
   - §9: add this handoff's PR, ml#2208, and the touch PR itself.

   Open it as a docs-only PR through `util/open_signed_pr.py`, which makes the GitHub-signed commit.
3. **Owner decision: deliver the released fixes.** No running service has them yet.
   - **Every service lockfile pins the old versions**, `juniper-observability==0.4.0` and `juniper-service-core==0.7.0`:
     - juniper-data `requirements.lock:88,90`, on `main` and at tag `v0.17.0`. The image installs that lock (`Dockerfile:33`), so GHCR `juniper-data:0.17.0` ships observability 0.4.0, which still captures Sentry frame locals. `notes/releases/RELEASE_NOTES_juniper-data_v0.17.0.md:256-259` says the fix waits on that floor being raised.
     - juniper-cascor `requirements.lock:63,65`, plus `requirements-cpu.lock` and `conf/requirements_ci.txt`.
     - juniper-canopy `requirements.lock:79,81`.
     - juniper-recurrence `juniper-recurrence/requirements.lock:70,74`.

     Every `pyproject.toml` range already admits 0.4.1 and 0.7.1, so a lock regeneration picks them up. Raising the floors to `>=0.4.1` and `>=0.7.1` makes that binding.
   - **Some fixes are on `main` but in no release:**
     - juniper-cascor#689, a non-ASCII key now gets a 401 instead of a 500 (merged 2026-09-25);
     - juniper-cascor#710, the throttle fix (merged 2026-10-08).

     Both postdate cascor 0.11.0 (PyPI, 2026-09-10), whose `src/api/security.py:61` still compares `str`. juniper-canopy 0.8.1 (2026-09-18) also compares `str` (`src/security.py:74`), while canopy's `main` compares bytes.
   - **What juniper-deploy runs.** Its `docker-compose.yml` runs cascor `0.11.0`, canopy `0.8.1`, recurrence `0.5.0` and data `0.17.0`.
   - **To deliver:** regenerate the locks, then cut releases for cascor, canopy and recurrence and a data patch. Merge approval for this arc does not cover that work.
4. **Open defects in `…FLOOD-3-DISPOSITION.md` §4.** Backlog only; the owner has not asked for these.
   - juniper-ml:
     - `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py` exits 1 when every column is constant.
     - `util/ad-hoc/2026-10-05_rerun_after_actions_outage.py:55` aborts on a dict-shaped `components`.
     - `util/ad-hoc/2026-10-04_replay_redrive.py` has a dead `if not snap:` check, and its `--snapshot` help says "instead of the newest".
     - The stale-docs bundle in the §4 row "stale on `main`, outside every PR". It includes the `--params` claims in `run_experiment.py`.
   - juniper-data and juniper-data-client: the `pr-budget-alarm.yml` header claims a `jq` failure only warns.
   - juniper-data:
     - The Quality Gate passes when an optional lane is cancelled.
     - `docs/DEVELOPER_CHEATSHEET.md` links `../AGENTS.md#adding-new-generators`, which has moved.
     - `docs/ci_cd/CICD_MANUAL.md:458` says CodeQL does not block.
     - `docs/DEVELOPER_CHEATSHEET.md:313`'s workflow list omits `sequence-safety.yml` and `main-verify.yml`.
   - A latent `base64` failure in `lockfile-update.yml`: `--arg contents "$(base64 -w0 …)"`, which `set -e` does not catch.
     - The row in `…FLOOD-3-DISPOSITION.md` §4 names data-client, cascor-client and cascor-worker.
     - Validation found the same unguarded line in juniper-data (`:178`), juniper-canopy (`:205`) and juniper-cascor (`:244-245`). Widen the row when touching it.
     - deploy, recurrence and juniper-ml do not have it.
   - juniper-recurrence: `memory-budget.yml:23-25` says Memory Budget is not required, but it is.
   - cascor-client, cascor-worker, deploy and recurrence: the `main-verify.yml` header describes the catch-up base wrongly. Only cascor-client's resolver is confirmed; the other three are unchecked.
   - juniper-cascor:
     - `docs/ci_cd/BRANCH_PROTECTION.md:28-55` lists 6 of the 24 required checks.
     - `:67` and `:69` there claim review requirements, but the ruleset requires 0 approvals and no code-owner review.
     - `ci.yml:988` and `conf/memory_budget.json:36` say there is no `docs/REFERENCE.md`.
     - `docs/DOCUMENTATION_OVERVIEW.md:811-812` has stamps that #709 put inside a template.
   - The `claude.yml` header says the key is "set at the org level", which no user-owned repo can have. It appears in `.github/workflows/claude.yml:11` of the seven sibling repos (juniper-deploy at `:12`) and in juniper-ml's template `notes/templates/ci/claude.yml:12`.
   - Tracked elsewhere: the empty cascor headline-accuracy columns, `APD-ML-002` in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9.
   - Optional: a `tests/test_service_fork_drift.py` guard for the throttle fix. Its gate needs an `APD-` id.
     - File the row in §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`. Closing it later takes that register's "five touches", which govern a close, not a filing.
     - `…FLOOD-3-DISPOSITION.md` §8 mislabels filing as the five-touch protocol. Correct it in item 2's touch.
5. **Cleanup.** The owner does this from the primary checkout `/home/pcalnon/Development/python/Juniper/juniper-ml`; a worktree-isolated session cannot `git -C` sibling worktrees.
   - **This session's 12 agent worktrees, and the docs-assembly worktree.** Each HEAD is a `main` ancestor (`d3971e10` or `959748c5`), so `git branch -d` succeeds. Without `--force`, `git worktree remove` refuses a dirty worktree; inspect any refusal before forcing it.

     ```bash
     for id in a100bc777b42dc7c9 a23bafc003f8464df a24622301ff896ea8 a4128fe01cdaa893a a7a72d3a2038d8599 ab08c82ec97ea71b1 ad24c58eec7505289 adb09f1610a62b08c ae3c35ae19e6f21d2 af41258dbcd4e55fe; do git worktree remove ".claude/worktrees/agent-$id" && git branch -d "worktree-agent-$id"; done   # the ten at d3971e10
     git worktree remove .claude/worktrees/agent-a621808cfbc0e59b3   # detached at 959748c5
     git worktree remove .claude/worktrees/agent-a8cedcf5971b0575b   # detached at 959748c5
     git worktree remove ../worktrees/juniper-ml--flood3-docs-assembly--20261008   # detached at 959748c5
     git worktree prune
     ```

   - **Leave other sessions' worktrees alone.** This session launched neither `agent-a0cc83f337e9b068d`, which holds ml#2190's branch, nor `agent-adf6f6f72c38b89d8`.
   - **This session's worktree, `.claude/worktrees/melodic-hugging-rabin`**, is detached at `81d3fbb3`.
     - Its 14 modified files and the untracked `util/ad-hoc/2026-10-08_run_ci_regression_suites.py` are all versions from `main`'s history, so nothing in it is unique.
     - Six are **older** than `main`: `.github/workflows/ci.yml`, `CHANGELOG.md`, `docs/REFERENCE.md`, `juniper-ci-tools/CHANGELOG.md`, `juniper-service-core/CHANGELOG.md` and `…FLOOD-3-DISPOSITION.md`. Never upload a file from it.
     - It is locked to this session (`locked claude session melodic-hugging-rabin`); the cleanup targets above are not. Once the session has ended and ml#2208 has merged, run `git worktree unlock` if the lock remains, then `git worktree remove --force`.
   - **Optional, owner's call:** 91 `cursor/*` head branches of closed, unmerged flood-3 PRs remain:
     - juniper-ml 47, juniper-canopy 22, juniper-data 13, juniper-cascor 6 and juniper-data-client 3;
     - the merged PRs' branches are already gone;
     - GitHub can restore a closed PR's branch.
6. **Not this arc's: ml#2190**, another session's PR, which raises juniper-ml's `[servers]` floor to `juniper-data>=0.17.0`.
   - It is not a draft, and squash auto-merge is armed, so it may merge unattended.
   - Its precondition, 0.17.0 on PyPI, holds.

## Key context and traps

- **Merge approval** covered this arc's fixes and releases only. It does not carry over. Ask again for any new work (memory `feedback_headless_merge_approval_policy.md`).
- **Release-train traps.**
  - Run `detect.py --local-git` (memory `reference_release_train_detect_repo_wide_feat.md`). API mode counts repo-wide `feat:` commits, so it proposes minor wrongly.
  - Memory `reference_release_train_ceremony_traps_2026-09-09.md`, 2026-10-08 section:
    1. `propose.py` misses version carriers that tests pin: observability's `tests/test_public_api.py` and data's `__init__.py` fallback.
    2. The security template's advisory placeholders ship unfilled, and the ceremony cannot fill them. Fill them after the cut, in the Release body and in the archive.
    3. The date gates bite near UTC midnight. juniper-data's `AGENTS.md` gate rejects a future date.
    4. The ceremony HALTs until the target commit's push CI completes. Then run `--execute --target-sha <sha>`.
    5. `--cross-repo` reads sibling files from `<ecosystem-root>/<repo>`, normally the primary checkout, which may be stale. Point it at a temp root of symlinks to fresh worktrees.
    6. `PENDING_PYPI_APPROVAL` can be reported early. Read the run's `pending_deployments` instead.
- **Worktree-isolated session limits.** These are refused:
  - loops or `$(…)` around `git` / `gh`;
  - a `python -c` that runs `git`;
  - piping into `gh`, which is why secrets go through `gh secret set -f <0600 dotenv>`;
  - `git -C <sibling juniper-ml worktree>`.

  Allowed: `git worktree add|remove <centralized path>` with no `-C`, `git -C <other repo>`, and `gh … --jq`. Piping `gh`'s output into `grep` ran in the validators' shells.
- **Never put a secret in argv.** Validate a key with `curl -H @<0600 header file>`, not `-H "x-api-key: ${VAR}"`, which expands into `curl`'s argv and is visible in `ps` (memory `reference_ps_cmdline_leaks_aescrypt_passphrase.md`).
- **Commits** go only through GraphQL `createCommitOnBranch`, via `util/open_signed_pr.py` or `util/push_signed_commit.py`. A local `git commit` hangs on the YubiKey. Split uploads over about 300 KB, because the API can return HTTP 499 or 502.
- **The Cursor fleet keeps running** by owner decision (`…FLOOD-3-DISPOSITION.md` §8). Every docs PR rewrites shared version stamps, so docs PRs conflict by construction, and consolidation is the default disposition for the next flood.

## Verification commands

```bash
gh api repos/pcalnon/juniper-ml/actions/runs/38045867684/pending_deployments --jq '.[].environment.name'   # "pypi" until the owner approves
gh run view 38045867684 --repo pcalnon/juniper-ml --json jobs --jq '.jobs[] | .name + " " + .status + " " + (.conclusion // "")'
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ci-tools/0.9.1/json   # 404 until published, then 200
gh pr view 2190 --repo pcalnon/juniper-ml --json state,isDraft,autoMergeRequest --jq '{state, isDraft, armed: (.autoMergeRequest != null)}'
gh secret list --repo pcalnon/juniper-deploy --json name --jq 'any(.[]; .name == "ANTHROPIC_API_KEY")'   # true; repeat per repo
git -C /home/pcalnon/Development/python/Juniper/juniper-data grep -n -E "juniper-(observability|service-core)==" origin/main -- requirements.lock   # item 3 (fetch first)
```

## Validation (consensus, 2026-10-10)

Three validators ran concurrently and independently against this PR's first commit (`587a9069`), each told to refute:

| Lens | Result |
|---|---|
| Re-probe every fact | 60 verified, 11 refuted, 2 unverified |
| Residue against `…FLOOD-3-DISPOSITION.md` §4, §8 and §9 and the open PRs | 6 missing, 5 misstated |
| Attack the conclusions and operability | 5 refuted, 5 risky |

The author re-probed every finding against git, GitHub or PyPI before applying it.

**Applied:**

- **Facts:**
  - ml#2205 merged; ml#2190 is not a draft;
  - the key's scope and the argv exposure;
  - "116" includes one Copilot PR;
  - "SAME" now reads SAME or MOVED, with none DIFFERS;
  - `CICD_MANUAL.md:458`.
- **Missing work:**
  - item 3: the released fixes reach no service, and cascor's and canopy's fixes are unreleased;
  - the full §4 backlog details;
  - the `base64` scope, widened to six repos;
  - the record-touch scope;
  - the fleet note.
- **Operability:**
  - the misattributed trap citations;
  - the cleanup ids, now inline;
  - the session-worktree warning;
  - the refused-command list;
  - verification commands that obey it;
  - every document named;
  - the filename's dots, now hyphens per Step 4 of `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.

**Corrected or settled on re-probe:**

- `agent-adf6f6f72c38b89d8` was proposed for the cleanup, but this session never launched it.
- The leftover-branch count of "47 juniper-ml and 22 canopy" is 91 across five repos.
- "Only juniper-ml had the key" was unverified from `updatedAt`, and `created_at` settles it.
- "Six files older than `main`" holds, and the untracked script is identical to `main`'s copy.

## Git status at handoff

- juniper-ml `main` is at `eb41ca60` (ml#2205) or later.
- The only open PR from this arc is ml#2208 (this handoff; branch `docs/handoff-flood3-followups-2026-10-10`). Its merge is manual, by the owner.
- The session worktree `melodic-hugging-rabin` is detached at `81d3fbb3`. Nothing is staged, and nothing in it is unique (item 5).
