# Handoff: R-OBS-SC-2 follow-ups. cascor 0.14.0 and canopy 0.10.0 are published and pinned, plan v1.15.16 is merged, and cascor's one-artifact publish fix has landed. The ports to the other repos, two release-train gaps and plan v1.15.17 remain

**Written**: 2026-11-15, finished 13:04Z (`date -u`), by session `b9dfa450`. In `ListAgents` it is
`r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next`, ref `4bad1a`; its worktree is
`.claude/worktrees/humble-humming-flask`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md` (juniper-ml#2574).

**The record**: plan v1.15.16 (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, juniper-ml#2588) records everything up to 2026-11-15 ~06:07Z. This file covers what came after, and what remains. Every state fact below was read from `gh`, PyPI or the disk between 05:41Z and 13:10Z. `[moves]` marks state that an armed merge or the owner changes.

## Owner rulings this session (verbatim; times from the transcript, `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py b9dfa450`)

- **Merge approval**: "merge approval granted", with "continue work arc from handoff: …". It is per-session and does not carry over.
- **Directive** (typed 05:14:10Z): "this needs to be fixed. deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again."
- **Dialog 1** (asked 05:17:06Z, answered 05:24:49Z; plan v1.15.16 records it):
  - cascor 0.14.0: "Approve as is, verify after (Recommended)";
  - Fix scope: "cascor, then every other (Recommended)". Its option text: one PR per repo, the shared build wherever the audit finds a per-job rebuild, and the hash check in every publish workflow, canopy's included; "I merge each once green, under this session's merge approval";
  - Parent docs: "Edit it once both publish (Recommended)".
- **Dialog 2** (asked 06:27:42Z, answered 11:47:38Z; NOT yet in the plan). Its question was which recovery the ports should adopt for an expired `pypi` gate:
  - option 1: re-run the PyPI job within 30 days, else cut a new patch;
  - option 2: a tag dispatch that republishes TestPyPI's exact files.

  The answer, verbatim: "attempt option 2 first. if that fails, within 30 days, fall back to option 1, part 1, pypi job re-run. if option 1, part 1, fails or if greater than 30 days, revert to option 1, part 2, cut a new patch version".

## Completed this session

- **Published and verified.**
  - The owner approved canopy 0.10.0's gate (on PyPI from 05:17Z) and cascor 0.14.0's (05:24Z).
  - `util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py` at 05:41:45Z: 0 failed checks.
    - canopy: PyPI's files equal TestPyPI's by sha256.
    - cascor: PyPI's files are a second build with every member identical (wheel `b70f3d39…` vs `c5c9a5dc…`).
  - Both images were pulled by digest and run with no network. Each holds juniper-observability 0.4.2 and juniper-service-core 0.7.2.
- **juniper-deploy#278** merged 05:48:57Z (`db7b7cb4`). It pins cascor 0.14.0 in two services and canopy 0.10.0 in three, plus both helm tags. Every push in this arc went through the plan's §9 pre-push gate (`util/ad-hoc/2026-11-15_pre_push_gate_run.bash`).
- **The parent `Juniper/AGENTS.md`** was edited at 05:49:09Z by `util/ad-hoc/2026-11-15_parent_agents_released_paragraph_cascor_0_14_0_canopy_0_10_0.py`: sha256 `f3f69b34…` became `3009c3f4…`. The backups are in `juniper-ml/tmp/2026-11-15-parent-agents-md-backup/`; the 11-14 backup's copy is in `tmp/2026-11-14-parent-agents-md-backup/`.
- **Plan v1.15.16, juniper-ml#2588**, merged 06:59:44Z (`95d321d5`): 25 files.
  - It applies two independent reviews (fact-check: 1 BLOCKER, 3 MAJOR; adversarial: 1 BLOCKER, 9 MAJOR).
  - The six reviews and the five-PR fix pass are archived in `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/`.
- **juniper-cascor#763** was merged by `pcalnon` at 11:26:51Z (`a1b0409d`).
  - One build job keeps the dist plus `SHA256SUMS` for 90 days.
  - TestPyPI and PyPI receive the same artifact.
  - A JSON sha256 check runs after the TestPyPI upload, again before the PyPI upload, and after it.
  - This applies to `publish.yml`, `publish-cascor-model.yml` and `publish-protocol.yml`.
- **juniper-cascor#767** (follow-up; `[moves]`: it was being merged at writing). An independent Opus review of #763 said "merge after fixes", and #767 applies all of them:
  - the build job reuses attempt 1's artifact on a re-run;
  - `id-token: write` moves to the two publish jobs only;
  - the owner's recovery ladder: a `workflow_dispatch` "republish TestPyPI's files" job that never builds, then "Re-run failed jobs" within 30 days, then a new patch;
  - two test gaps closed, and the docs corrected.

  Its second commit carries `Allow-Symbol-Loss:` lines, so the squash must keep GitHub's default message (`util/safe_merge.py` does). `update-branch` ran at ~13:03Z, and safe_merge is running: `tmp/cascor-767/safe_merge_767.log` in this worktree.

## Remaining work (goal)

Continue the R-OBS-SC-2 follow-ups: port the one-artifact publish fix, then record it.

1. **First turn**:
   - Confirm #767 MERGED: `gh pr view 767 --repo pcalnon/juniper-cascor --json state,mergeCommit`. Read the log's `MERGED` line; exit 0 is not proof.
   - Ask the owner for merge approval, naming the PRs below.
2. **The ports.** This is dialog 1's "every other". Make one PR per repo, copying the five template steps from cascor `main` after #767, with dialog 2's ladder in each. The audit (18 publishers in 8 repos) is `util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py`; its last output is `tmp/cascor-publish-artifact/audit_run3.txt` in worktree `agent-a54a0a279acc3a863`.
   - **Shared build plus checks** (both jobs rebuild today): juniper-data (keep `notify-consumers`, `needs: pypi`), juniper-data-client (drop `skip-existing`), juniper-cascor-client, juniper-cascor-worker.
   - **Checks only** (one artifact already): drop `skip-existing` and raise retention from 7 to 90 days.
     - juniper-canopy: its build job needs an `if:` release guard once the dispatch exists.
     - juniper-recurrence's three publishers: dist in `<pkg>/dist`.
     - juniper-ml's `publish.yml` and its six `publish-<pkg>.yml`. Its suites pin publish-workflow text: run `ci.yml`'s full list, including `tests/test_publish_subpackage_workflows.py` and `tests/test_publish_testpypi_verify.py`.
   - **For every port**:
     - keep the job names "Publish to TestPyPI" / "Publish to PyPI" (`util/release_train/ceremony.py:611`), and keep "pypi" out of the republish job's name;
     - give each one an independent review, then green CI, then merge with `util/safe_merge.py`.
3. **Release-train gaps (juniper-ml)**:
   - (a) A failed build job now classifies as `HALT_PUBLISH`, which files only a note, instead of `HALT_TESTPYPI`, which files an issue. Add a build-failed halt with a fixture, or get the owner's acceptance.
   - (b) `ceremony.py:811` reads only release-event runs, so it never sees a successful republish dispatch.
4. **Plan v1.15.17.** Record:
   - dialog 2;
   - #763 and #767, and both reviews;
   - the audit (4 rebuild per job, 12 use `skip-existing`, none checked sha256 before #763);
   - the ports;
   - the ceremony gaps;
   - **finding**: juniper-ci-tools 0.9.1 on PyPI (`1dc8e01e…`) differs from TestPyPI (`ade363e8…`), because run 38045867684's attempt 2 re-ran its build;
   - **unverified**: whether the PyPI trusted publishers are environment-bound (it needs the owner's PyPI login).
5. **Land the uncommitted scripts with plan v1.15.17**, after pre-commit and the §9 gate. They are in `.claude/worktrees/agent-a54a0a279acc3a863/`:
   - `util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py`;
   - `…_cascor_one_artifact_publish_edits.py`, `…_cascor_one_artifact_followup_tree.py` and `…_cascor_one_artifact_live_index_rehearsal.py`;
   - `util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/` (10 files).

   Keep its `tmp/cascor-publish-artifact/` (644 MB of evidence) under the retention rule.
6. **Housekeeping, worktree by worktree, on the owner's word.** The lists in both 11-15 handoffs stand. Add:
   - this worktree: its `tmp/` holds `deploy-pin/`, `plan-pr/`, `v1-15-16/`, `review-a/`, `review-b/`, `review-763/` and `cascor-767/`;
   - `agent-a54a0a279acc3a863`: do not remove it until item 5 lands.

**Still open with the owner**:
- the juniper-deploy stack's restart;
- the trio's environment upgrade, then the per-environment probe (ruling 6 of 2026-11-13);
- juniper-deploy's `juniper-recurrence:0.8.0` pin (0.8.1 is published);
- A1's open limbs: the data-client and cascor F-S10 fixes, P6 OD-2, canopy#685 call (a), and a W1.14 port for the host recurrence legs;
- canopy-primary pulls (O13);
- a cascor 0.12.0–0.14.0 fix-forward;
- a pointer from the v2 draft to the rulings;
- launching the 0.4.3 design session from `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`.

## Key context (new this session)

- **The isolation guard reads "git" inside words**: a scanner named after git, `.github/` paths, `git -C`, `$(git …)`, and heredocs that hold git commands. Put those arguments in a script or file. The §9 gate runs through `util/ad-hoc/2026-11-15_pre_push_gate_run.bash PAYLOAD_DIR`, with `files/`, `text/`, `added/` and per-part `accept.<part>.txt` files: the scanner refuses an `--accept` that names no current finding.
- **Transcripts move between `~/.claude/projects/*/` directories**: `1b4fec84`'s moved at ~03:20Z. Find them by session-id prefix glob.
- **The owner can merge a PR while you are still preparing its follow-up**: #763 merged while its review fixes were in flight. Re-read a PR's state before every push.
- **An isolated agent's worktree is removed once it goes idle with no changes.** A resumed agent then works in YOUR worktree.
- **Dialog 2 held the session from 06:27Z to 11:47Z.** Ask with background, and only when nothing time-critical is pending.

## Verification commands (one per call)

```bash
gh pr view 767 --repo pcalnon/juniper-cascor --json state,mergedAt,mergeCommit
gh pr view 2588 --repo pcalnon/juniper-ml --json state,mergedAt                      # MERGED 2026-11-15T06:59:44Z
gh pr view 278 --repo pcalnon/juniper-deploy --json state,mergedAt                   # MERGED 2026-11-15T05:48:57Z
python3 -I util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py   # 0 failed check(s)
sha256sum /home/pcalnon/Development/python/Juniper/AGENTS.md                         # 3009c3f4… unless edited since
python3 -I util/ad-hoc/2026-11-15_r_obs_sc_2_followups_record_reprobe.py             # 221 PASS at 06:07Z; later moves expected
python3 -I util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py b9dfa450                # two dialogs
```

## Git status (2026-11-15 13:04Z)

This worktree, branch `worktree-humble-humming-flask`, sits at `91e16a50`. Its tracked edits and new files are what #2588 landed, so they equal `main`'s copies. This file is new and lands through its own one-file PR. Nothing is staged.

## Documents referenced / changed

- **Referenced**:
  - the predecessor handoff named above;
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`;
  - `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`;
  - `notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md` and `notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.
- **Changed by this session**:
  - in juniper-ml, through #2588:
    - the plan;
    - `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/` (14 files);
    - ten `util/ad-hoc/2026-11-15_*` tools: the writer, the re-probe, the archive tool, the verify tool, the image probe, the lock-moves tool, the deploy-pin tool, the gate driver, the token triage and the parent-edit tool;
  - in juniper-deploy, through #278: `docker-compose.yml`, `k8s/helm/juniper/values.yaml` and `CHANGELOG.md`;
  - in juniper-cascor, through #763 and #767: `.github/workflows/publish.yml`, `publish-cascor-model.yml`, `publish-protocol.yml`, `src/tests/unit/test_publish_one_artifact.py`, `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`, `CHANGELOG.md`, `AGENTS.md`, `docs/ci_cd/MANUAL.md`, `docs/ci_cd/REFERENCE.md`, `docs/ci_cd/QUICK_START.md` and `docs/DEVELOPER_CHEATSHEET.md`;
  - the parent `Juniper/AGENTS.md`, which is unversioned;
  - `juniper-ml/tmp/2026-11-14-parent-agents-md-backup/` and `juniper-ml/tmp/2026-11-15-parent-agents-md-backup/`;
  - this file.
