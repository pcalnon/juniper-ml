# Handoff: R-OBS-SC-2 follow-ups, group D. R45 done in all three repositories (canopy#840), R50 and R51 landed as ml#2637; R53 and the Overtoad's items next

**Written**: 2026-11-24, 14:51Z to ~16:00Z (`date -u`), by session `9b9fc524`. In `ListAgents` it is
`r-obs-sc-2-group-d-r45-r49-r52-prs-gating-canopy-r45-r50-r51-next`, ref `007878`. Its worktree is
`.claude/worktrees/immutable-exploring-russell`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_r-obs-sc-2-group-d-r45-r49-r52-prs-gating-canopy-r45-r50-r51-next.md`
(juniper-ml#2628).

**The task list**: `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
inventory), § 3 for group D. This file adds only what that file does not hold.

**Merge approval**: the Overtoad granted it for this session and work arc (2026-11-24). It is per-session, so ask
again.

## Done (check each state first)

| Item | PR | State |
| --- | --- | --- |
| R47: canopy conda CPU env, dash 4.4.1 | juniper-canopy#839 | MERGED 03:07:53Z, `cf25e4ea` |
| R45 (data) | juniper-data#551 | MERGED 03:15:27Z, `6b734fd9` |
| R45 (cascor) | juniper-cascor#779 | MERGED 03:16:14Z, `b5b28dc3` |
| R52: service-core `create_app` telemetry opt-out | juniper-ml#2627 | MERGED 04:15:52Z, `6d528300` |
| R49: the register's §2.3 compare row | juniper-ml#2623 | MERGED 04:32:26Z, `515e16a0` |
| **R45 (canopy)** | juniper-canopy#840 | MERGED 12:45:23Z, `7935ce3a` |
| **R50 + R51**: two dated ad-hoc successors | juniper-ml#2637 | MERGED 15:58:10Z, `0a05e8a2` (re-cut once: Key context) |
| R55 (flood-4 line, ruling 48) | juniper-ml#2631 | MERGED 13:06:28Z, `9a9ef3fb` (session 17d26a's) |
| R54: §8 of `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, rulings 15–48 | juniper-ml#2635 | MERGED 14:51:35Z, `0a7c602c` (session 17d26a's) |

- **R45 canopy**: the predecessor's staged clone was rebased onto canopy `main` `cf25e4e`. `src/main.py` was
  unchanged, so its 22-run mutation result (24 `ok`) still applied. Its test file was re-run in full under FastAPI
  0.137.0 and 0.163.1. The predecessor's two overlay failures were a collision with its own in-place mutation run. The
  gate's two `CHANGELOG.md` findings sit on main's line 1639, an env-variable name the gate had already accepted on
  canopy#839, and were accepted again after a masked read.
- **R50** (`util/ad-hoc/2026-11-24_released_section_drift.py`, v0.4.0) follows every bullet through the first-parent
  history and judges it at `--at`. A bullet belongs to the first final release tag that contains the commit that added
  it, under the category it was filed under, with no words inserted after release. `--accept` records a ruling, and
  `--ignore-tag` drops a retired release. It meets the §3 check of
  `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`: 6 open at `48b66130^`, 0 at
  `48b66130`, 0 on main (re-run at `0a7c602c`).
- **R51** (`util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py`, v0.4.0) dates an answer from its first timestamped
  entry. Untimed `api-request-blob` copies made `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py` print
  `answered None`. It fixes `218ff61e` call 5
  (10:10:51.412Z), `7d425759` call 1 (2026-11-14T22:10:39.373Z), and the new `2222e504` call 1
  (2026-11-23T20:32:40.333Z).
- **Validation**: two independent reviewers (re-probe and adversarial) ran three rounds each; the fixes reached v0.4.0;
  48 source mutants are killed by the self-tests. Details in ml#2637's body.

## Remaining work (goal)

Continue the R-OBS-SC-2 follow-ups:

1. **Every PR above is MERGED**: confirm with the verification commands below. For any later merge, a checkout of
   juniper-ml at or after `c93914a7` (#2632) runs `util/safe_merge.py` with its review-thread probe fixed; an older one
   needs threads checked by hand.
2. **R53** still waits for the session that prepares service-core 0.8.0. Leave it.
3. **Group D is otherwise done**, and so are the two items routed to flood-4 (R54, R55). The next update of
   `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` should mark R45–R52, R54 and
   R55 done with the PRs above. That file's R54 row (line 170, "§8 lists rulings 1–14") is stale since ml#2635.
4. **Raise with the Overtoad, do not act** (re-probed 2026-11-24 ~14:57Z):
   - **R14**: PyPI's newest juniper-observability is still 0.4.2. No release carries ml#2608's `sentry-sdk<3` cap,
     and sentry-sdk 3.0.0 (2026-11-23) is the newest.
   - **R21**: `JuniperData` and `JuniperCanopy1` still hold observability 0.4.0 and service-core 0.5.0.
   - **R23**: the juniper-ml primary is still on `task/owner-is-the-overtoadgit` at `6e230a6d`. `JuniperCascor1`
     imports observability and service-core from that checkout, as editable installs.
   - **New (from R50)**: eight findings on seven bullets are misfiled in `CHANGELOG.md` on main, all from before this
     arc:
     - `abfdfecf` (the v0.9.0 cut) moved five bullets that shipped in 0.8.0 into `[0.9.0]`;
     - `4b13f318` put a 0.9.0 bullet under `[0.8.0]`;
     - `6b99f2ab` and `3d083988` (ml#295) each re-filed an Added bullet as Changed, ml#2360's shape.
     Whether to repair released sections is the Overtoad's call. ml#2637 touches no `CHANGELOG.md`.
5. A **handoff PR** for the next file (only that file).

## Key context

- **Upload path** (this worktree's `tmp/group-d/`, copied from the predecessor's and re-pointed here):
  - `preupload.bash DIR CLONE SCOPE` (base export, gate payload, §9 gate, sequence-safety probe), then
    `upload_pr.py DIR CLONE --repo R --branch B`.
  - DIR holds `title.txt`, `paths.txt`, `message.txt`, `commit_body.txt`, `pr_body.md` and, if needed,
    `accept.files.txt`.
  - A juniper-ml PR can use this worktree itself as CLONE (`.`) after `git fetch origin main`.
- **The isolation guard** refuses `git -C`, git inside loops or compound shells, and heredocs that name git. Put steps
  in a script under `tmp/`.
- **`util/safe_merge.py --repo` takes the bare repo name** (`juniper-canopy`), not `pcalnon/juniper-canopy`; the slug
  form fails with "error connecting to pcalnon".
- **R50's real-history runs**: `tmp/r50/verify_v040.bash` (24 cases, main pinned `c93914a7`; outputs under
  `tmp/r50/v040-final-out/`). R51's: `tmp/r51/compare_old_new.py` + `compare_blocks.py` over 13 sessions.
  Mutations: `tmp/r50r51/mutation_check_v040.py`. Reviewers' scripts and reports: `tmp/review-r50r51/` (no transcript
  text). Keep all of `tmp/` under the retention rule; the predecessor's `.claude/worktrees/declarative-jumping-wreath/tmp/group-d/`
  is the source of the copied tooling and its own evidence.
- **ml#2637's first `safe_merge` run was REFUSED** (15:37Z): two CodeQL "Statement has no effect" threads (alerts 1132,
  1133) on the `...` bodies of R50's `Releases` Protocol methods, which `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`
  does not model. The bodies are now docstrings, which changes no behaviour. The branch was re-cut as ONE signed commit
  on `main` (`96bcde88`, parent `ebfeea68`) by `util/ad-hoc/2026-10-08_fleet_flood3_reset_pr_branch.py`, through
  `tmp/r50r51/reset_ml2637.py`. This repo squashes with `COMMIT_MESSAGES`, so an appended fix commit would have put a
  second message in `main`'s history. On the re-cut commit, the self-test passed, all 48 mutants were still killed
  (`tmp/r50r51/mutation_check_v040_codeql_fix.txt`), pre-commit changed nothing, and the §9 gate passed. CodeQL's
  re-scan (15:49Z) marked both alerts `fixed` and resolved both threads itself (`github-advanced-security[bot]`).
- **Two memories saved** this session: difflib's autojunk collapses the ratio of long, moderately edited texts; a
  transcript answer has untimed `api-request-blob` copies. The CodeQL memory note also gained the Protocol `...` shape.

## Verification commands (one per call)

```bash
gh pr view 840 --repo pcalnon/juniper-canopy --json state,mergedAt    # MERGED 2026-11-24T12:45:23Z
gh pr view 2637 --repo pcalnon/juniper-ml --json state,mergedAt      # MERGED 2026-11-24T15:58:10Z (R50, R51)
gh pr view 2631 --repo pcalnon/juniper-ml --json state,mergedAt      # MERGED 2026-11-24T13:06:28Z (R55)
gh pr view 2635 --repo pcalnon/juniper-ml --json state,mergedAt      # MERGED 2026-11-24T14:51:35Z (R54)
python3 util/ad-hoc/2026-11-24_released_section_drift.py --since 957f0e94 --at 48b66130^   # 6 open, exit 1
python3 util/ad-hoc/2026-11-24_released_section_drift.py --since 957f0e94 --at origin/main # 0 open, exit 0
python3 util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py --self-test                    # all 19 checks passed
```

## Git status (~16:00Z)

This worktree, branch `worktree-immutable-exploring-russell`, fast-forwarded to `c93914a7`. The two R50/R51 files are
staged intent-to-add; their content equals what ml#2637 merged (`0a05e8a2`). This file is new and goes up in its own
PR.
`tmp/` (gitignored) holds `group-d/`, `r50/`, `r51/`, `r50r51/` and `review-r50r51/`.

## Documents referenced / changed

- **Referenced**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_r-obs-sc-2-group-d-r45-r49-r52-prs-gating-canopy-r45-r50-r51-next.md`
  (the predecessor); `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
  inventory); `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (§8, through ml#2635);
  `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`
  (v1.15.17, lines 1106, 1155, 1163); `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md`
  (line 298, the cut rule); `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/five-prs-validation-fixpass-round-1.md`
  (A-4).
- **Changed, through PRs**: juniper-canopy `src/tests/unit/test_main_import_and_lifespan.py`, `CHANGELOG.md`
  (canopy#840); juniper-ml `util/ad-hoc/2026-11-24_released_section_drift.py`,
  `util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py` (ml#2637); and this file.
