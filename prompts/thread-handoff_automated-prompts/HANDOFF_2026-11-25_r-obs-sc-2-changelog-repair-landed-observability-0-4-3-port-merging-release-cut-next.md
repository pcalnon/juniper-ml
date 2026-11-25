# Handoff: R-OBS-SC-2 follow-ups. The CHANGELOG repair (ml#2646) landed and the 0.4.3 port (ml#2647) is green and merging; R21 and R23 done; cutting juniper-observability 0.4.3 is next

**Written**: 2026-11-25, 00:43Z to 02:35Z (`date -u`), by session `031e862f`.
- In `ListAgents` it is `cosmic-percolating-kazoo-49`, ref `80dd2d`.
- Its worktree is `.claude/worktrees/cosmic-percolating-kazoo`.

**Predecessor**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_r-obs-sc-2-group-d-r45-done-r50-r51-ml-2637-r53-and-owner-items-next.md`
(juniper-ml#2639).

**The task list** is `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
inventory). Its section "Checked and changed, 2026-11-24" (juniper-ml#2650) holds the rulings, the times and the
findings below in full. This file adds only what the next session needs to act.

**Merge approval**: the Overtoad granted it for session 031e862f at 21:24:29Z. It is per-session, so ask again.

## Done (check each state first)

| Item | PR / action | State at handoff |
| --- | --- | --- |
| CHANGELOG released-section repair (the Overtoad's ruling of 21:29Z) | juniper-ml#2646 | MERGED 23:58:21Z, `c38f4e5d` |
| R14: `configure_sentry` on sentry-sdk 2.x and 3.x, `<4` cap | juniper-ml#2647 | OPEN at 02:35Z, every check green on `d3e05d85` (both SDK lanes and CodeQL); a `safe_merge` retry was running (below) |
| The inventory update, plus the R-OBS-SC-3 start prompt's 0.4.4 addendum | juniper-ml#2650 | OPEN at 02:35Z, auto-merge net armed on `338059f1` |
| R21: `JuniperData` and `JuniperCanopy1` upgraded to observability 0.4.2 and service-core 0.7.2 | pip, 22:30Z | done; records in this worktree's `tmp/cosmic/r21/` |
| R23: the juniper-ml primary back on `main` | the Overtoad, 21:22:29Z | done (the primary's reflog) |

**The Overtoad's rulings of 2026-11-24.** Times come from the transcript.

- 21:29:24Z:
  - cut a new juniper-observability release that admits sentry-sdk 3.x;
  - upgrade the applicable envs;
  - the primary is back on `main`;
  - repair released CHANGELOG sections.
- 22:26:46Z:
  - the release is **0.4.3**, and R-OBS-SC-3 becomes **0.4.4**;
  - **both** majors are supported, `>=2.35.0,<4`;
  - R15: **port the consumers** to 3.x.

## Remaining work (goal)

1. **Merge ml#2647, then ml#2650, then this file's PR**, one at a time. Read `gh pr view N --json state,mergedAt`,
   because `safe_merge` exit 0 is not a merge.
   - **`main` moved every 20–30 minutes on 2026-11-25**, about one CI run, so each PR kept going BEHIND.
     `util/safe_merge.py` refused ml#2647 and ml#2650 after three re-syncs ("went BEHIND 3 times"), and a 3000 s run
     timed out (exit 3). Retry when `main` is quieter, and never start two of these at once: each merge sends the
     other BEHIND.
   - **No `ci-observability.yml` job is a required check on `main`.** Before merging ml#2647, read that both
     `Test (Python 3.13)` (3.x) and `Test (Python 3.13, sentry-sdk 2.x)` are `success` on its current head. At
     02:35Z they were green on `d3e05d85`, the last commit with content. The later heads are GitHub's update-branch
     merges.
   - To change ml#2647's content, re-cut it with `tmp/cosmic/sentry3/reset_2647.py`, which pins the branch tip and
     base, rather than appending a commit: the repo squashes with every commit's message.
2. **Propose juniper-observability 0.4.3**, after ml#2647 merges.
   - Run from a CLEAN checkout at `origin/main`: this worktree after a re-home, or an export of `origin/main`.
     `detect.py` diffs through the GitHub API.
   - Commands:
     `python3 util/release_train/detect.py --repo-root . --package juniper-observability --json > tmp/manifest.json`,
     then `python3 util/release_train/propose.py --manifest tmp/manifest.json --package juniper-observability --repo-root .`.
     Read the dry run, then add `--execute`. Its proposal commit is signed via `createCommitOnBranch`.
   - The proposal PR is gate 1, and merging it needs the new session's merge approval. Check that its `## [0.4.3]`
     section holds ml#2647's entries.
3. **The ceremony**, per `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11.7.
   - `ceremony.py --dry-run`, then the notes preview (`util/ad-hoc/2026-09-12_ceremony_notes_preview.py`), then
     `--execute --target-sha <full 40-char sha>`.
   - It opens the archive PR (`notes/releases/RELEASE_NOTES_juniper-observability_v0.4.3.md`), cuts the Release
     `juniper-observability-v0.4.3`, and parks at the `pypi` environment.
   - **Gate 2 is the Overtoad's: never approve it.** Hand over the run URL. A Release body cannot be re-cut, so read
     the preview first.
   - `RELEASE_TRAIN_MODE` is unset (404 on 2026-11-24), so the daily cron only reports.
4. **After PyPI serves 0.4.3** (read `/pypi/juniper-observability/0.4.3/json`, not the aggregate endpoint):
   - **R21, second pass**: the same two envs to 0.4.3. `tmp/cosmic/r21/upgrade.bash` shows the pattern: a dry run
     first, pinned versions. Keep `sentry-sdk<3`, because cascor's own init still breaks on 3.x until R15.
   - **R22**: re-run the per-lock probe in each env, with six DSNs blank and FastAPI's telemetry recorded. Read
     `util/ad-hoc/2026-11-09_lock_round_2_probe.py`: its steps 3–5 run against an existing interpreter.
     `JuniperData`'s interpreter is `python3.14t`, the env's only tree in use. For `JuniperCascor1`, record the
     primary commit its editable installs run.
   - **R15**, one PR per repo into `[Unreleased]`: `juniper-observability>=0.4.3` and a `<4` cap on each sentry-sdk
     floor (cascor `pyproject.toml:151`, canopy `:251`, data `:142`).
     - cascor's bootstrap init (`src/main.py:231-249`) also passes `traces_sample_rate=1.0`,
       `profile_session_sample_rate=1.0` and `profile_lifecycle="trace"`. `configure_sentry` has no parameter for
       these, so the port is a design choice: call `configure_sentry` and drop profiling, or keep a version-aware
       init. Ask the Overtoad.
5. **R53** waits for the session that prepares service-core 0.8.0. Leave it.
6. **Raise with the Overtoad, do not act**:
   - `200f0ce5` wrote a 0.4.0 note into the released `[0.3.0]` bullet; it may be a real misfiling.
   - juniper-canopy's `POST /api/remote/connect` body field `authkey` reaches Sentry on 2.x today (DSNs blank).
   - Five proxy headers carry the client address without `send_pii`.
   - Make the observability CI required?
   - The Overtoad's own branch commit `c8f4d884` renames handoffs to `HANDOFF_<date>__<description>.md`. It is not on
     `main`, and no document states the convention.
7. A **handoff PR** for the next file (only that file).

## Key context

- **Upload path** (this worktree's `tmp/group-d/`, re-pointed here):
  - `preupload.bash DIR CLONE SCOPE...`, then `upload_pr.py DIR CLONE --repo R --branch B`.
  - Use `.` as CLONE for juniper-ml.
  - **A gate accept key embeds the line number.** After any edit above a finding, the entry goes stale and the gate
    errors "names no current finding": re-derive the key and re-read the line.
- **`main` moves under you**: other sessions' fetches update the shared `origin/main`. Re-check it right before each
  upload, and re-home with `util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py`.
- **The isolation guard** refuses compound shells naming git or `.github`, and heredoc-plus-run. Write scripts with
  the Write tool.
- **ml#2647's evidence**, all in this worktree's `tmp/`:
  - the fork's build: `cosmic/sentry3/`;
  - the reviews: `review/reprobe/`, `review/adversarial/`, `review/round2/`, `review/round3/`;
  - the merged-code runs: `cosmic/suites/merged-r3/`, `cosmic/dbprobe/`, `cosmic/attacks/`.
  - Venvs: `tmp/cosmic/sentry3/venv-{2.35.0,2.76.0,3.0.0,3.0.0-py313}` (run from `juniper-observability/` with
    `python -m pytest`); `tmp/review/reprobe/venv-db-{2.76.0,3.0.0}` (sqlalchemy, fakeredis).
  - Final counts: 299 passed, 13 skipped on 2.35.0 and 2.76.0; 305 / 7 on 3.0.0 (py3.14, py3.13); `sentry.py` 100%.
  - On 2.x it is byte-identical to `main` (130/130 runs).
  - Keep all of `tmp/` under the retention rule.
- **The CHANGELOG repair**: a walk that starts after the misfilings passes `--accept c38f4e5d`. The next cut's
  `--since v0.11.5` walk reports 8 findings without it, 0 with it.
- **CodeQL failed ml#2647's first head** with alert 1134, `py/clear-text-logging-sensitive-data`. It fired on a
  `print` of the probe's variable `secret`, which held only JSON paths. CodeQL judges sensitive data by name, and
  `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` predicted 0. Renaming the variable to `marker_paths` fixed it
  (`d3e05d85`).
- **Memories saved** this session: sentry-sdk 3.0.0's redesign; the gate accept-key line drift; the CodeQL name
  heuristic.

## Verification commands (one per call)

```bash
gh pr view 2646 --repo pcalnon/juniper-ml --json state,mergedAt   # MERGED 2026-11-24T23:58:21Z
gh pr view 2647 --repo pcalnon/juniper-ml --json state,mergedAt,headRefOid
gh pr view 2650 --repo pcalnon/juniper-ml --json state,mergedAt
python3 util/ad-hoc/2026-11-24_released_section_drift.py --since v0.11.5 --at origin/main --accept 40815bb4 --accept c38f4e5d   # 0 open
curl -s https://pypi.org/pypi/juniper-observability/json | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])'   # 0.4.2 until the cut
```

## Git status (02:35Z)

- This worktree, branch `worktree-cosmic-percolating-kazoo`, is at HEAD `c38f4e5d`; `origin/main` had moved to
  `9515871e` or later.
- The port's seven files are uncommitted, equal to ml#2647's content (`d3e05d85`, the probe rename included). So are
  the inventory and the start prompt, equal to ml#2650's.
- Re-home with `util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py` once both merge, and the edits fold into
  `main`.
- This file is new.

## Documents referenced / changed

- **Referenced**:
  - the predecessor;
  - `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`;
  - `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§11.7);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`.
- **Changed, through PRs**:
  - `CHANGELOG.md` and `util/ad-hoc/2026-11-24_changelog_released_section_repair.py` (ml#2646);
  - `juniper-observability/juniper_observability/sentry.py`, `juniper-observability/tests/test_sentry.py`,
    `juniper-observability/pyproject.toml`, `juniper-observability/CHANGELOG.md`, `juniper-observability/README.md`,
    `.github/workflows/ci-observability.yml` and `util/ad-hoc/2026-11-24_sentry_sdk_major_wire_probe.py` (ml#2647);
  - `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` and
    `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` (ml#2650);
  - this file.
