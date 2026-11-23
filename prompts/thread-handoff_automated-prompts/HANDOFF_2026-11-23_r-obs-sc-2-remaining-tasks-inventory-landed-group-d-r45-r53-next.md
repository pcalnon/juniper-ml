# Handoff: R-OBS-SC-2 follow-ups. The remaining-task inventory has landed and R56/R57 are done; next is group D's R45 to R53, one PR per repository

**Written**: 2026-11-23, finished ~22:30Z (`date -u`), by session `2222e504`. In `ListAgents` it is
`r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next`, ref `9660dc`. Its worktree is
`.claude/worktrees/curried-frolicking-boot`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_r-obs-sc-2-owner-items-recurrence-pin-0-8-1-seven-worktrees-archived.md`
(juniper-ml#2616, merged 21:20:22Z).

**The task list**: `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
inventory). It lists 65 tasks with sources, lanes and next actions. Its §3 gives, for each group-D item, the files a fix
touches and how to verify it. Start there. This file adds only what the inventory does not hold.

**Merge approval**: the Overtoad wrote "merge approval granted" at this session's start. It is per-session, so ask
again.

## Done this session (after the predecessor)

- **The inventory**, compiled read-only by an agent and then checked by this session. The checks: cascor#772 merged;
  the juniper-ml primary sits on ml#2605's closed branch; the backup hash records exist; the consumers' sentry lines
  are as cited. It lands with this file.
- **R56**: the six older parent-`AGENTS.md` backups (2026-10-29, 11-01, 11-07) were restored to their recorded sha256
  by `util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py`. A re-run prints six `ORIGINAL`.
- **R57**: a dated addendum in `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`
  covers sentry-sdk 3.0.0 and ml#2608's cap.
- **R55** was answered and moved, with R54, to the flood-4 session (live again as [f9fa6e]).

## Remaining work (goal)

Continue the R-OBS-SC-2 follow-ups: carry out group D's open items R45 to R53, one PR per repository.

1. **R46** (juniper-cascor, doc only) and **R48** (juniper-canopy, comments only): the cheapest two.
2. **R49** (juniper-ml): the defect register's §2.3 row `:279` and the `docs-full-check.yml:253` comment.
   Message 301392 first: ml#2606, rebuilt on `main`, touches both files.
3. **R47** (juniper-canopy `conf/conda_environment_cpu.yaml:47`): only after a dry-run solve admits `dash>=4.0.0` with
   `dash-bootstrap-components` at `:48`.
4. **R45**: a telemetry test that runs below FastAPI 0.142, in juniper-data, juniper-cascor and juniper-canopy.
   **R52**: juniper-service-core's app-factory opt-out, into `[Unreleased]`. Each needs a mutation check and an
   independent review.
5. **R50 and R51**: dated successors of the two `util/ad-hoc` tools, the last of the group.
6. **R53** waits until a session prepares service-core 0.8.0. Leave it.

The Overtoad's decisions and actions are inventory groups A and B (R1 to R27). Three are time-sensitive. Raise them,
do not act on them:

- **R14**: no juniper-observability release carries ml#2608's `<3` cap yet. A fresh `juniper-observability[sentry]`
  install resolves sentry-sdk 3.0.0, and `configure_sentry` with a DSN raises.
- **R23**: the juniper-ml primary, whose code `JuniperCascor1` imports, is on `task/owner-is-the-overtoadgit`, not
  `main`. Ruling 7 of 2026-11-13 lets only the Overtoad move it.
- **R21**: the trio upgrade needs a `sentry-sdk<3` constraint.

## Key context

- **Who owns what.**
  - [ffffd3] (the one-artifact sweep) owns R28 to R41, plan v1.15.18 included. Send it group E and this inventory's
    path for the plan.
  - [301392] (the rename repair) owns ml#2606, recurrence#237 and deploy#281's repairs.
  - [f9fa6e] owns R54 and R55.
- **Uploads.** `util/open_signed_pr.py` uploads whole files. Start every edit from `origin/main`'s current copy
  (`git show` or the contents API at an exact sha), never from a stale worktree or primary, and prove the base with a
  diff before you push.
- **The isolation guard** refuses `git -C <other>`, `git/` inside a `gh api` URL, `$(git …)`, and loops that mix git
  with `find`. Put such commands in a script under the worktree's `tmp/`. Mutations outside the worktree need the
  Overtoad's word.
- **Gates.** `util/ad-hoc/2026-11-15_pre_push_gate_run.bash PAYLOAD_DIR` runs the §9 gate. Read any finding with
  `util/ad-hoc/2026-10-05_masked_finding_shape.py` before you accept it. Run pre-commit after `git add -N` on new files.
  G5 wants paths from `$HOME`. `notes/` and `prompts/` are outside markdownlint.
- **Tests.** juniper-deploy's pytest drives live services: run named files only. Run each service's suite with the
  six Sentry DSNs blank (`util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py`).
- **`$?` after a pipe** is the last command's status. Use `${PIPESTATUS[0]}`.

## Verification commands (one per call)

```bash
gh pr view 2616 --repo pcalnon/juniper-ml --json state,mergedAt          # MERGED 2026-11-23T21:20:22Z
python3 -I util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py # six "ORIGINAL", exit 0
python3 -I util/ad-hoc/2026-11-23_restore_parent_agents_backups.py       # three "ORIGINAL", exit 0
gh pr view 772 --repo pcalnon/juniper-cascor --json state,mergedAt        # MERGED 2026-11-23T19:35:14Z
```

## Git status (2026-11-23 ~22:30Z)

This worktree, branch `worktree-curried-frolicking-boot`, sits at `81b8eaf7`, behind `origin/main`. Its new files and
the prompt edit land through the PR that carries this file. `tmp/arc/` (gitignored) holds the agent's draft
`inventory_agent.md`, its probe scripts and this session's checks, kept under the retention rule.

## Documents referenced / changed

- **Referenced**: the predecessor; the inventory; `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`
  (v1.15.17); `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md`;
  `.claude/worktrees/crispy-forging-falcon/prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_overtoad-rename-repair-ml-2606-recurrence-deploy-next.md`
  (untracked).
- **Changed, through the PR that carries this file**: the inventory (new);
  `util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py` (new);
  `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` (addendum); this file.
- **Changed, unversioned**: the six restored backups in `juniper-ml/tmp/2026-10-29-parent-agents-md-backups/`,
  `juniper-ml/tmp/2026-11-01-parent-agents-md-backup/` and `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`, each
  with its `*.substituted-2026-11-20` copy.
