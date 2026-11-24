# Handoff: R-OBS-SC-2 follow-ups, group D. R46 and R48 merged; R47, R49, R45 (data, cascor) and R52 gating; next is canopy's R45, then R50 and R51

**Written**: 2026-11-24, ~03:00Z (`date -u` read 02:53Z while writing), by session `21952abc`. In `ListAgents` it is
`r-obs-sc-2-remaining-tasks-inventory-landed-group-d-r45-r53-next`, ref `5774a5`. Its worktree is
`.claude/worktrees/declarative-jumping-wreath`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_r-obs-sc-2-remaining-tasks-inventory-landed-group-d-r45-r53-next.md`
(juniper-ml#2619).

**The task list**: `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
inventory), § 3 for group D. This file adds only what the inventory does not hold.

**Merge approval**: the Overtoad granted it at this session's start (2026-11-23). It is per-session, so ask again.

## Done, and in flight (check each state first)

| Item | PR | State at handoff |
| --- | --- | --- |
| R46: cascor's docs no longer call `/docs`, `/openapi.json`, `/redoc` auth-exempt (API reference row, `AGENTS.md`, `docs/testing/REFERENCE.md`) | juniper-cascor#778 | MERGED 02:09:03Z, `a68dd84e` |
| R48: canopy drift-workflow comments | juniper-canopy#838 | MERGED 02:26:21Z, `aa54edb6` |
| R49: the register's §2.3 compare row (service-core 0.7.1 shipped the fix; wheel read) | juniper-ml#2623 | gating under `safe_merge.py` |
| R47: canopy `conf/conda_environment_cpu.yaml` dash 4.4.1 + `comm`, `janus` rows | juniper-canopy#839 | gating |
| R45: telemetry test on every FastAPI (cascor) | juniper-cascor#779 | gating |
| R45 (data), plus data's `AGENTS.md` docs-exempt lines (R46's sibling, new) | juniper-data#551 | gating |
| R52: service-core `create_app` passes the five-switch `telemetry=` opt-out | juniper-ml#2627 | gating |

- **R49's second half needed nothing**: ml#2576's merged diff already rewrote `docs-full-check.yml`'s comment,
  though its body said it was left. The comment matches the workflows (only `docs-full-check.yml:110` clones siblings).
- **R47**: the file is a `conda list --export` spec, not an env YAML; 39 rows are `pypi_0`. The dry-run solve
  (`tmp/group-d/r47_conda_dryrun.py`, `CONDA_PKGS_DIRS` in `tmp/`) links all 251 conda rows as pinned.
- **R45/R52 evidence**: `tmp/group-d/r45_mutation_check.py` (11 source mutants x FastAPI 0.137.0, each env's own, and
  0.163.1, a `pip install --target` overlay at `tmp/group-d/overlay-fastapi-0.163.1`). Every new test fails on all
  22 runs and passes the baselines; the ported tests skip on 0.137.0 and miss a dropped `auto_configure` on 0.163.1.
  Full test files pass under both. recurrence `main`'s 485 tests pass against the edited service-core under both.
  An independent Opus review found no BLOCKER/MAJOR; its fixes are applied (`tmp/group-d/review/outcome.md`).
- **e59506** (`overtoad-rename-repair-2606-rebuilt-validated-upload-after-peer-prs`) holds ml#2606 until flood-4's
  guard 1.4.0 merges (~04:30Z) and builds it after #2623. If #2623 lands after ~04:15Z, message it the state.

## Remaining work (goal)

Continue the R-OBS-SC-2 follow-ups, group D:

1. **Watch the five gating PRs to MERGED** (read `gh pr view N --json state,mergedAt`; `safe_merge` exit 0 is not a
   merge). Re-run `util/safe_merge.py --execute` if one ends "head moved" after an update-branch.
2. **canopy R45**, staged in `tmp/group-d/clones/juniper-canopy`, after #839 merges (both carry `CHANGELOG.md`):
   - `cd` the clone, `git fetch -q --depth 1 origin main`; check that `git diff origin/main --stat` shows only
     `src/tests/unit/test_main_import_and_lifespan.py` and `CHANGELOG.md` (R45 entry) beyond #839's content.
   - Read `tmp/group-d/r45_mut_canopy_3.txt` (the re-run after the review fixes; running at handoff): want 24 `ok`.
   - Re-run canopy's file under both FastAPIs (the first re-run collided with that mutation run): the canopy lines of
     `tmp/group-d/r45_full_files.bash`.
   - Fill `{precommit}`, `{seq}`, `{canopy_full}` in `tmp/group-d/r45/canopy/pr_body.md`, then
     `bash tmp/group-d/preupload.bash tmp/group-d/r45/canopy tmp/group-d/clones/juniper-canopy 'src/**/*.py'`, then
     `python3 tmp/group-d/upload_pr.py tmp/group-d/r45/canopy tmp/group-d/clones/juniper-canopy --repo juniper-canopy --branch test/telemetry-opt-out-every-fastapi`.
3. **R50**: a dated successor of `util/ad-hoc/2026-09-23_released_section_drift.py`. A wrong category cannot be read
   from one snapshot: compare a merge's CHANGELOG with the PR head's (the predecessor's rule, "a read of the category
   headings against the parent of any long-lived PR's merge"). ml#2360's merge is `187e3258`; the repair rode in
   ml#2558 (`48b66130`). Define the inputs first, then the inventory's verify.
4. **R51**: a dated successor of `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py` that reads the first
   timestamped entry (inventory § 3).
5. **R53** waits for the session that prepares service-core 0.8.0. Leave it.
6. A **handoff PR** for this file (only this file).

Raise, do not act: **R14** (no observability release carries ml#2608's `<3` cap; a fresh `[sentry]` install takes
sentry-sdk 3.0.0), **R23** (the juniper-ml primary is on `task/owner-is-the-overtoadgit`, ruling 7), **R21**
(the trio upgrade needs `sentry-sdk<3`).

## Key context

- **Upload path**: shallow clones under `tmp/group-d/clones/` (inside this worktree), edits there, then
  `tmp/group-d/preupload.bash` (base export, gate payload, §9 gate, sequence-safety probe) and
  `tmp/group-d/upload_pr.py` (reads `title.txt`, `paths.txt`, `commit_body.txt`, `pr_body.md`). The probe needs a
  `tmp/` dir in the clone. Fetch the clone's `origin/main` before every upload.
- **The isolation guard** refuses `git -C`, `$(cat …)` beside a `.github` path, and multi-step shells; put steps in a
  `tmp/group-d/` script. Gate findings so far were pre-existing non-credentials (conda build strings, an env table's
  `None`); read each with `util/ad-hoc/2026-10-05_masked_finding_shape.py` before accepting it.
- **FastAPI facts** (the reviewer read every cached wheel 0.100.0-0.165.0): `**extra` until 0.143.3; `_telemetry`
  from 0.142.0; an omitted `auto_configure` is `True` on 0.142.x and `FASTAPI_OTEL_AUTO_CONFIGURE` from 0.143.0.
  Newest is 0.165.0 (2026-11-18), same merge code as 0.163.1. The three envs hold 0.137.0; the locks pin 0.163.1.
  No CI lane runs below 0.142.
- **The service-core worktree copy**: `JuniperCascor1`'s editable service-core points at the primary; prepend this
  worktree's `juniper-service-core/` to `PYTHONPATH` (verified to win).

## Verification commands (one per call)

```bash
gh pr view 778 --repo pcalnon/juniper-cascor --json state,mergedAt     # MERGED 2026-11-24T02:09:03Z
gh pr view 838 --repo pcalnon/juniper-canopy --json state,mergedAt     # MERGED 2026-11-24T02:26:21Z
gh pr view 2623 --repo pcalnon/juniper-ml --json state,mergedAt
gh pr view 839 --repo pcalnon/juniper-canopy --json state,mergedAt
gh pr view 779 --repo pcalnon/juniper-cascor --json state,mergedAt
gh pr view 551 --repo pcalnon/juniper-data --json state,mergedAt
gh pr view 2627 --repo pcalnon/juniper-ml --json state,mergedAt
```

## Git status (~02:55Z)

This worktree, branch `worktree-declarative-jumping-wreath`, HEAD `ca976240`, `origin/main` `43a24183`. Uncommitted:
the register (R49, carried by #2623), `juniper-service-core/` app, test and CHANGELOG (R52, carried by #2627), and
this file (its own PR). `tmp/group-d/` (gitignored) holds the clones, overlays, scripts, logs and PR inputs; keep it
under the retention rule.

## Documents referenced / changed

- **Referenced**: the predecessor; the inventory; `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`
  (v1.15.17, :1144-1163); `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/five-prs-validation-fixpass-round-1.md`
  (A-4, A-5); `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md`
  (:268-270, :298-299); `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
- **Changed, through PRs**: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (#2623);
  `juniper-service-core/juniper_service_core/app.py`, `juniper-service-core/tests/test_app.py`,
  `juniper-service-core/CHANGELOG.md` (#2627); in the sibling repos, cascor `AGENTS.md`, `CHANGELOG.md`,
  `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`, `docs/testing/REFERENCE.md`, `src/tests/unit/api/test_api_app.py`;
  canopy `.github/workflows/juniper-data-schema-drift.yml`, `conf/conda_environment_cpu.yaml`, `CHANGELOG.md`;
  data `AGENTS.md`, `CHANGELOG.md`, `juniper_data/tests/unit/test_api_app.py`; and this file.
