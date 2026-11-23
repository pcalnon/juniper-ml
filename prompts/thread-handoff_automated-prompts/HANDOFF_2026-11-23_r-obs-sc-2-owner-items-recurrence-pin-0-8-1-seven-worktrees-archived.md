# Handoff: R-OBS-SC-2's items left with the Overtoad. juniper-deploy#284 pins juniper-recurrence 0.8.1, and seven finished worktrees and four merged branches are archived and removed. The rest stays with the Overtoad

**Written**: 2026-11-23, finished 20:56Z (`date -u`), by session `2222e504`. In `ListAgents` it is
`r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next`, ref `9660dc`; its worktree is
`.claude/worktrees/curried-frolicking-boot`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md`.
Its items 1 to 5 were already done when this session started: the ports and both release-train gaps merged by
2026-11-16 (ml#2592, ml#2593 and the six sibling PRs), and plan v1.15.17 merged as ml#2610 on 2026-11-23. The
one-artifact line that did them continues from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-16_one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next.md`
and its successor (ml#2614). This session took only item 6 (housekeeping) and the "Still open with the Overtoad" list.

## The Overtoad's rulings this session (this session's AskUserQuestion, asked ~12:18Z, answered by 20:33Z)

- **Merge approval**: "merge approval granted", at session start. It is per-session.
- **Cleanup**: "Six finished worktrees, data worktree + 4 branches". The three one-artifact worktrees were not offered.
- **Recurrence pin**: "Move it now (Recommended)".

## Done

- **juniper-deploy#284** MERGED at 20:55:09Z (`7e996845`), by the auto-merge net that `util/safe_merge.py` armed, once
  the required checks were green. Against deploy `main` at 20:55Z, `--fail-on-stale` exits 0. It pins `juniper-recurrence` 0.8.0 -> 0.8.1 in `docker-compose.yml`, moves the five
  prose sites that named the pinned image, and adds a CHANGELOG entry. 0.8.1 changes no runtime: its
  `requirements.lock` and `Dockerfile` equal 0.8.0's, and the image (index `sha256:daf5cb97…`, revision `2a467adb`,
  pulled and run with no network) holds observability 0.4.1 and service-core 0.7.1. `--fail-on-stale` went from
  exit 1 to exit 0. The edits came from `util/ad-hoc/2026-11-23_deploy_pin_recurrence_0_8_1.py`, and the push passed
  the §9 pre-push gate. One acceptance was carried over from #278 after a fresh masked read: `docker-compose.yml:1204`,
  a secret-file path default, not a credential.
- **Housekeeping** (`util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash`, run 20:45:52Z, re-verified after):
  - removed `logical-percolating-sparkle`, `foamy-squishing-floyd`, `toasty-prancing-karp`,
    `agent-a4c8d9de35bfc0d67`, `buzzing-growing-whale` and `humble-humming-flask`, with their local branches. Each
    one's work was checked against `main` file by file before removal;
  - removed the never-opened juniper-data worktree (`fix/rate-limit-retry-after-round-up` at `399eeffb`). It held an
    uncommitted Retry-After fix, superseded by juniper-data#537;
  - deleted the juniper-cascor and juniper-canopy primaries' `fix/fastapi-telemetry-opt-out` and
    `fix/rate-limit-retry-after-round-up` (#755, #757, #816, #817, all merged 11-13);
  - **archived first** in `juniper-ml/tmp/worktree-archive-2026-11-23/` (946 MB; `README.md`, one `MANIFEST.txt` per
    item, `deleted_branches.txt` with full shas). Each `tmp/` was moved, not deleted.
- **The parent `AGENTS.md` backups were restored.** The blind pass had rewritten all three backups in
  `juniper-ml/tmp/2026-11-1[45]-parent-agents-md-backup/`, so the plan's "the parent's prior copy is safe" was false
  on disk. The inverse ("The Overtoad" -> "Owner", then "Overtoad" -> "owner") reproduces each recorded sha256
  (`90df2783`, `f3f69b34`, `3009c3f4`). `util/ad-hoc/2026-11-23_restore_parent_agents_backups.py` restored them, and
  the rewritten bytes sit beside each as `*.substituted-2026-11-20`. The live `Juniper/AGENTS.md` is `3009c3f4`, never
  substituted.

## Findings (for plan v1.15.18, which the one-artifact line owns)

1. **The blind "owner -> Overtoad" pass also reached untracked and gitignored files** in every juniper-ml worktree that
   existed on 2026-11-20..22, not only the eight PRs. Each worktree had ~2,450 rewritten tracked files and 11
   symlinks materialized, every untracked file was rewritten, and so was much of `tmp/`. Before cleanup, the files
   under `tmp/` containing "Overtoad" numbered: giggly 59,976, agent-a54a0a 1,869, humble 161 and sparkling 24.
   - The 26 one-artifact scripts were rewritten in all three sibling copies. The one-artifact line restored them by
     the inverse, exact against their manifests, and landed them in ml#2610.
   - **Read pre-11-20 `tmp/` evidence as possibly substituted**, the archive above included, and prefer `gh`, `git`
     or the transcripts (they are intact).
2. **sentry-sdk 3.0.0** (PyPI 2026-11-23 09:30Z) has no `sentry_sdk.scrubber` and no `send_default_pii`, and its
   `_get_options` raises `TypeError` on an unknown option. `juniper_observability/sentry.py:182` passes
   `send_default_pii`, so `configure_sentry` with a DSN raises on a fresh install; a blank DSN returns early.
   ml#2608 (cap `<3`) merged at 20:50:42Z (`b2aa9026`); it reaches an install only with the next
   juniper-observability release. It bears on the 0.4.3 design prompt.
3. juniper-ml still registers **447 worktrees** after this cleanup.

## Still open with the Overtoad (re-read 2026-11-23 unless marked)

- **Newly eligible for cleanup, on the Overtoad's word**: `giggly-foraging-sunbeam` (`tmp/` 6.3 GB),
  `sparkling-percolating-meadow` and `agent-a54a0a279acc3a863`, now that ml#2610 has landed their scripts. NOT
  `ethereal-munching-peacock`: its line keeps it until plan v1.15.18 lands its sweep scripts.
- **The juniper-deploy stack**: no Juniper container exists at all (`docker ps -a`), so this is a bring-up, not only a
  restart.
- **The trio's environments**: `JuniperData` and `JuniperCanopy1` still hold observability 0.4.0 and service-core
  0.5.0. `JuniperCascor1` runs editable 0.4.1 / 0.7.1 from the juniper-ml primary beside stale 0.4.0 / 0.5.0
  dist-infos. Under ruling 6 of 2026-11-13, the per-environment probe follows the Overtoad's upgrade. Keep
  `sentry-sdk<3` until an observability release carries ml#2608's cap (finding 2).
- **Launching the 0.4.3 design session** from `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`:
  not launched, and finding 2 changes its ground.
- Not re-probed: canopy-primary pulls (O13), a cascor 0.12.0–0.14.0 fix-forward, A1's open limbs, the v2 draft's
  pointer, and the PyPI trusted-publisher check (plan §6).

## Key context

- **The isolation guard refuses `gh api` paths containing `git/`**, `$(…)` with git, and `cd` into another worktree.
  Put such commands in a script file. All mutations outside this worktree ran through one reviewed script, dry run
  first, on the Overtoad's word.
- **`$?` after a pipe reads the last command's status.** The first stale-check baseline printed `exit=0` through
  `| tail`; the real exit was 1. Use `${PIPESTATUS[0]}`.

## Verification commands (one per call)

```bash
gh pr view 284 --repo pcalnon/juniper-deploy --json state,mergedAt,mergeCommit
bash tmp/housekeeping/verify_after.bash        # in curried-frolicking-boot: 7 items gone, 4 kept worktrees present, archive hashes OK
python3 -I util/ad-hoc/2026-11-23_restore_parent_agents_backups.py   # three lines "ORIGINAL", exit 0
sha256sum ~/Development/python/Juniper/AGENTS.md                      # 3009c3f4… unless edited since
```

## Git status (2026-11-23 20:56Z)

This worktree, branch `worktree-curried-frolicking-boot`, sits at `81b8eaf7`. This file and the three
`util/ad-hoc/2026-11-23_*` scripts land through one PR. `tmp/` (gitignored) holds `housekeeping/` and `deploy-pin/`,
the probes, logs and the #284 payload. Nothing else is uncommitted.

## Documents referenced / changed

- **Referenced**: the predecessor and the 11-16 handoff named above;
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md`
  and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md`
  (housekeeping lists, parent sha256 records); `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`
  (v1.15.17, read only); `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`.
- **Changed**:
  - in juniper-deploy, through #284: `docker-compose.yml`, `README.md`, `docs/REFERENCE.md`, `docs/USER_MANUAL.md`,
    `scripts/test_recurrence_snapshots.sh` and `CHANGELOG.md`;
  - in juniper-ml, through this PR: `util/ad-hoc/2026-11-23_deploy_pin_recurrence_0_8_1.py`,
    `util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash`, `util/ad-hoc/2026-11-23_restore_parent_agents_backups.py`
    and this file;
  - unversioned: `juniper-ml/tmp/worktree-archive-2026-11-23/` (new) and the three restored backups in
    `juniper-ml/tmp/2026-11-14-parent-agents-md-backup/` and `juniper-ml/tmp/2026-11-15-parent-agents-md-backup/`.
