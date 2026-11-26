# R-OBS-SC-2 Follow-ups: Remaining Tasks

**Project**: Juniper (ecosystem-wide)
**Owner**: Paul Calnon
**Status**: Working inventory, 2026-11-23. It feeds plan v1.15.18 of
`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, which the one-artifact line owns. It does
not replace the plan.
**Date**: 2026-11-23
**Updated**: 2026-11-26, by session cf970cdc ("Checked and changed, 2026-11-26" below); before that 2026-11-24, by
session 031e862f

---

## What this is

Every remaining task of the R-OBS-SC-2 follow-ups arc, including its one-artifact publish sub-line, with its source
(file:line), lane, status, blocker and next action:

- groups A and B wait on the Overtoad;
- group C belongs to live peer sessions;
- group D is work a session can do now without a new ruling;
- group E lists entries the plan still holds open that are done or superseded.

- **Compiled** 2026-11-23, 21:14Z to 21:45Z (`date -u`), read-only, by an inventory agent of session `2222e504`
  (`r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next` [9660dc], worktree `curried-frolicking-boot`).
  That session then checked it and updated it (next section).
- **"Overtoad" = "owner".** Text written or rewritten after 2026-11-20 may say either; both mean the same person.
- **Line numbers** cite the files as they stood at juniper-ml `origin/main` = `b2aa9026` (21:14Z), unless the source
  is a worktree file. Re-read any of them with `git show b2aa9026:<path> | sed -n '<N>p'`.

## Checked and changed after compilation (session 2222e504, 2026-11-23 21:45Z to 22:30Z)

- **Re-measured by the session.**
  - cascor#772 is MERGED (19:35:14Z, merge `e9c86f83`, head `31136d64`).
  - The juniper-ml primary's HEAD is `refs/heads/task/owner-is-the-overtoadgit` at `6e230a6d`, the branch of
    ml#2605 (CLOSED 20:54:14Z).
  - `JuniperCascor1`'s editable observability and service-core finders point into that checkout. Its two packages
    carry "Overtoad" only in docstrings ("Overtoadship"), so the code it would import is intact; which commit the trio
    restart runs is still R23.
  - The six older backups' recorded sha256 are in sources written before the blind pass:
    `…parent-agents-cascor-0-13-0.md:92`, `…parent-agents-edited-owner-items-next.md:23` and
    `…DEVELOPMENT-PLAN.md:677`.
  - The consumer sentry lines R15 and R57 cite are confirmed on each `main`: cascor `pyproject.toml:151`, canopy
    `:251`, data `:142`, cascor `src/main.py:236`.
- **R56 done.** `util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py` restored all six files to their recorded
  sha256 (dry run, `--execute`, then a re-run printing six `ORIGINAL`). With the 2026-11-14/15 three, every
  parent-`AGENTS.md` backup in juniper-ml's primary `tmp/` is verbatim again.
- **R57 done**, in this document's PR: a dated addendum in the 0.4.3 start prompt, after its "The paths:" list.
- **R55 answered, and moved to group C.**
  - `_DECLARES_RE` at `tests/test_pyproject_extras.py:91-92` pins the release named in the sentence above the matrix
    to `pyproject.toml`.
  - Nothing checks that the paragraph says the current row tracks `pyproject.toml` between a floor PR and its release.
  - The plan routes the question through the flood-4 session, which is live again
    (`flood4-session9-paused-pause-fix-landed-guard-and-d14-ready` [f9fa6e]). R54 moves there too.
- **Counts after the update**: A 19, B 8, C 19, D 11 (R56 and R57 done, so **9 open: R45 to R53**), E 8.

## Checked and changed, 2026-11-24 (session 031e862f, from 21:24Z)

- **Group D is done except R53.** Each PR was read MERGED with `gh pr view`:
  - R45: data#551 (03:15:27Z), cascor#779 (03:16:14Z), canopy#840 (12:45:23Z, `7935ce3a`);
  - R46: cascor#778 (02:09:03Z, `a68dd84e`);
  - R47: canopy#839 (03:07:53Z, `cf25e4ea`);
  - R48: canopy#838 (02:26:21Z, `aa54edb6`);
  - R49: ml#2623 (04:32:26Z, `515e16a0`). The workflow comment half was already done by ml#2576 (`6befa3ba`);
  - R50 and R51: ml#2637 (15:58:10Z, `0a05e8a2`);
  - R52: ml#2627 (04:15:52Z, `6d528300`; ships with service-core 0.8.0).
  - R54 (ml#2635, 14:51:35Z) and R55 (ml#2631, 13:06:28Z) were done by the flood-4 line.
- **The Overtoad's rulings of 2026-11-24.** Times are this session's transcript, the first timestamped entry of each.
  - 21:24:29Z: merge approval, for this session.
  - 21:29:24Z, four answers:
    - R14: "let's cut a new release for juniper-observability and update the cap for sentry-sdk to include 3.x";
    - R21: "let's upgrade all applicable conda environments to use latest observability and service-core versions";
    - R23: "juniper-ml checkout has been restored to main";
    - the CHANGELOG findings: "released sections should be repaired".
  - 22:26:46Z (AskUserQuestion, asked 21:37:19Z):
    - the release is **0.4.3**, and R-OBS-SC-3 moves to **0.4.4**;
    - it supports **both** majors, `>=2.35.0,<4`;
    - R15: **port the consumers** to 3.x.
- **R23 done by the Overtoad.** The primary's reflog shows a checkout of `main` at 21:22:29Z, then a fast-forward to
  `f41b1d07` at 21:22:45Z. The task branch's tip `c8f4d884` (21:21:31Z, pushed, PR ml#2605 closed) renames five
  handoff files to `HANDOFF_<date>__<description>.md`, to flag the most recent in each work arc. It is not on `main`,
  and no document states that convention.
- **R21 done at 22:30Z** (`tmp/cosmic/r21/` in worktree `cosmic-percolating-kazoo`: before/after freezes, dry runs,
  diffs).
  - `JuniperData` (its `python3.14t`, the env's only tree in use) and `JuniperCanopy1` (`python3.13`) moved from
    observability 0.4.0 and service-core 0.5.0 to **0.4.2** and **0.7.2**. Nothing else changed: sentry-sdk stayed at
    2.54.0 and 2.62.0, held below 3 by a constraint.
  - `pip check` is unchanged: clean in `JuniperData`; `JuniperCanopy1` keeps its pre-existing `torch 2.11.0+cpu` /
    `setuptools<82` line.
  - `JuniperCascor1`'s editable installs map to the primary's `juniper-observability/` and `juniper-service-core/`,
    now on `main`, and import 0.4.2 and 0.7.2. pip's dist-info still reads 0.4.1 and 0.7.1.
  - The same environments take 0.4.3 once it is on PyPI.
- **R22 is unblocked** (R21, R23), and runs once the environments hold 0.4.3, so its record is of the final state.
- **R14 in progress**: the port is ml#2647. On 3.x, `configure_sentry` passes:
  - `data_collection`: user and cookies follow `send_pii`; the seven headers and the two address headers are denied;
    no frame locals, SQL parameters, redis arguments or request bodies; queue, GenAI, MCP and GraphQL data only with
    `send_pii`;
  - `before_send_span`;
  - the logging integration, with `attach_stacktrace=False`.
  The hooks apply 2.x's `EventScrubber` denylist, which 3.0.0 deleted. Another major initialises nothing.
  - Two independent round-1 reviews found two blockers, both measured on the wire, and their fixes are merged: the
    unset `data_collection` defaults (a SQL bind parameter and a redis value under `send_pii=False`), and the deleted
    scrubber.
  - A round-2 review of the merged fixes found a third blocker (2.x's PII denylist), a 2.x over-redaction and a consumer-test break; all fixed, and a round-3 review checked those fixes (ml#2647's body).
  - The release proposal and the ceremony follow; the `pypi` gate is the Overtoad's.
- **R15 ruled: port.** It follows 0.4.3's PyPI publication, because each consumer's floor moves to
  `juniper-observability>=0.4.3` and each sentry-sdk floor gains `<4`.
  - juniper-cascor's bootstrap `sentry_sdk.init` (`src/main.py:231-249` on `main`) also passes
    `profile_session_sample_rate=1.0`, `profile_lifecycle="trace"` and `traces_sample_rate=1.0`, which
    `configure_sentry` has no parameter for.
  - A re-init that installs only `_strip_sensitive_headers` leaves traces unscrubbed on either major (the adversarial
    review's scenario 4).
  - data (`juniper_data/api/app.py:46`) and canopy (`src/main.py:312`) call only `configure_sentry`.
- **R20**: the start prompt keeps its file name. Its addendum of 2026-11-24 records the move to 0.4.4 and what 0.4.3
  already does on 3.x.
- **The CHANGELOG ruling: ml#2646** (merge `c38f4e5d`).
  - Seven bullets moved verbatim: each to the release whose tag first contains it, under the category its author
    filed it in.
  - A walk that starts after the misfilings reads the moves as findings: one from v0.7.1, two from v0.8.0, and eight
    from v0.11.5, the next cut's window. **Pass `--accept c38f4e5d`** to `util/ad-hoc/2026-11-24_released_section_drift.py`,
    as for `40815bb4`.
  - At least 24 of the 59 findings left from v0.2.0 are the tool's false positives: the v0.2.1 and v0.3.0 tags sit on
    the branches that `c0dc4092` (PR #7) and `9cea64c5` (PR #61) merged, off `main`'s first parent.
  - Open for the Overtoad: `200f0ce5` wrote a 0.4.0 rename note into the released `[0.3.0]` bullet.
- **New pre-existing findings for the Overtoad** (equal on both majors; R-OBS-SC-3's channels):
  - juniper-canopy's `POST /api/remote/connect` body field `authkey` reaches Sentry on `main` today, in `request.data`
    on 2.x, because 2.x's denylist does not match it. The DSNs are blank (XC-SENTRY (b)), so nothing is sent.
  - The client address reaches Sentry without `send_pii` through five other proxy headers: `Forwarded`,
    `X-Client-IP`, `CF-Connecting-IP`, `True-Client-IP`, `X-Cluster-Client-IP`.
  - Sentry Logs carry logging extras raw.
- **Counts after the update**: A 19 (R14 and R15 ruled), B 8 (R21 and R23 done), C 19, D 11 (R53 open), E 8.

## Checked and changed, 2026-11-26 (session cf970cdc, from 01:16Z)

- **Merged since the 2026-11-24 update**, each read with `gh pr view`:
  - ml#2647, R14's port: 2026-11-25 10:41:26Z, merge `b54f961b`, head `042030b6`. Every check on that head
    succeeded, `Test (Python 3.13)` (3.x), `Test (Python 3.13, sentry-sdk 2.x)` and `Analyze (python)` among them.
  - ml#2650, this document's 2026-11-24 update: 12:09:30Z, `dbe9ab30`.
  - ml#2655, session 031e862f's handoff: 20:37:00Z, `0b53d2ab`.
- **The Overtoad's rulings of 2026-11-26** (AskUserQuestion, asked 01:33:42Z, answered 01:47:02Z):
  - merge the 0.4.3 proposal, ml#2666, and run the ceremony to cut the Release. The approval also covers this
    session's docs-only PRs (this update and the handoff);
  - the Release lists the three pre-existing exposures below as its Known Issues, each re-measured on the wire first,
    in place of the renderer's fixed "None known at time of release.";
  - **R15 for juniper-cascor: add profiling to `configure_sentry`.** A later juniper-observability release gains
    profiling keyword arguments, and cascor's port waits for it and keeps its profiling. juniper-data and
    juniper-canopy call only `configure_sentry`, so their ports can follow 0.4.3 on PyPI.
- **The proposal: ml#2666, MERGED 01:47:50Z, merge `b9442e3c`** (branch `release/juniper-observability-v0.4.3`).
  - `detect.py`'s GitHub path proposed minor / 0.5.0, from repo-wide `feat:` commits; `--local-git` proposed the
    ruled patch / 0.4.3. The manifest is the GitHub path's with only `proposed_bump` and `proposed_version`
    rewritten, after asserting that the two manifests differ in nothing else `propose.py` reads.
  - Commit 1 (`549da41f`, `propose.py`): `pyproject.toml`, `_version.py`, and the CHANGELOG move to
    `[0.4.3] - 2026-11-26`. Commit 2 (`d1901c04`): the carriers `propose.py` misses, `tests/test_public_api.py`'s
    pin and per-release paragraph, and README § Status's floor, now `>=0.4.3`.
  - Before it opened, `util/ad-hoc/2026-10-21_simulate_release_proposal.py` ran 17 suites with 0 regressed, and the
    package's tests on the simulated copy gave 305 passed / 7 skipped on sentry-sdk 3.0.0 and 299 / 13 on 2.76.0.
    The branch's five files equal that copy byte for byte. Every check on `d1901c04` passed (29 success, 5 neutral,
    1 skipped).
- **The Known Issues, measured** by `util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py` against
  `main`'s package (0.4.3), on sentry-sdk 2.35.0, 2.76.0 and 3.0.0, under both `send_pii` values:
  - the client's address in `Forwarded`, `X-Client-IP`, `CF-Connecting-IP`, `True-Client-IP` and
    `X-Cluster-Client-IP` reaches the error event and the transaction on both 2.x, and the error event and the
    server span on 3.0.0;
  - canopy's body field `authkey` reaches `request.data` of the error event and of the transaction on both 2.x. On
    3.0.0 it is not sent: there are no bodies;
  - a log record's `extra` fields (`api_key`, `detail`) reach the Sentry Log's attributes on all three.
  - **Two corrections to the 2026-11-24 record.** The `authkey` reaches 2.x transactions too, not only error events.
    And the R15 bullet's "`configure_sentry` has no parameter for" holds only for the two profiling options:
    `configure_sentry` takes `traces_sample_rate` (`juniper-observability/juniper_observability/sentry.py:436`,
    default 0.1).
  - The DSNs are still blank: juniper-deploy's compose file defaults each `*_SENTRY_DSN` to empty, its Helm values
    set `""`, and its `secrets.example/cascor_sentry_dsn.txt` holds a placeholder.
  - The Release's text is held in `util/ad-hoc/2026-11-26_observability_0_4_3_known_issues_notes.py`.
- **The cut: Release `juniper-observability-v0.4.3`, published 02:04:23Z**, after the merge commit's `ci.yml` push run
  (45738156851) completed `success` at 02:03:42Z.
  - `ceremony.py --execute --target-sha b9442e3c… --release-date 2026-11-26 --monitor-timeout 30`. The tag is a
    commit ref on `b9442e3c`. The Release is not a draft or a prerelease, and `releases/latest` stays `v0.11.5`
    (`--latest=false`).
  - The body the ceremony rendered equalled the body reviewed before the cut, byte for byte, in the Release and in
    the archive branch's file. Then the Known Issues went into both: signed commit `3cb84a0e` on
    `release-notes/juniper-observability-v0.4.3` (atop the ceremony's `76855285`), and `gh release edit`. Both read
    back equal to the filled text.
  - The archive PR, ml#2667, added one file, `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.3.md`, and
    auto-merged at 02:19:08Z (`fcbc5d3c`). The file on `main` equals the filled text and the live Release body.
  - The publish run is 45739959764 (`release`, `b9442e3c`, created 02:04:26Z). **It waits at the `pypi` gate, gate 2,
    the Overtoad's**, read by hand at 02:05:47Z:
    - `Build and Validate` and `Publish to TestPyPI` succeeded, `Publish to PyPI` is `waiting`, and
      `pending_deployments` names `pypi`;
    - TestPyPI serves 0.4.3: the wheel (sha256 `4817790d…`) and the sdist (`14c6c7db…`), with
      `sentry-sdk[fastapi]<4,>=2.35.0` on the `sentry` and `test` extras;
    - PyPI answers 404 for 0.4.3 until the gate is approved;
    - the deadlines, from the run's creation: day 30, 2026-12-26, is the last day to re-run it and the cap on its
      wait at the gate; day 35, 2026-12-31, is when GitHub cancels it. The workflow carries the republish job, so
      §11.8's rung 1 of `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` applies after
      either.
- **Open, unchanged**: R21's second pass and R22 follow 0.4.3 on PyPI, which waits on gate 2, the Overtoad's. R53
  waits for the session that prepares service-core 0.8.0. R15 follows PyPI for data and canopy, and the profiling
  release for cascor.
  - The profiling arguments add to `configure_sentry`'s public signature, which SemVer counts as a minor, while
    R-OBS-SC-3 is ruled 0.4.4: the release that carries them needs its number ruled.

## Sources (aliases used in the tables; each alias is the tail of the filename)

| Alias | File |
| --- | --- |
| `…DEVELOPMENT-PLAN.md` | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.17) |
| `…PLAN-V2.md` | `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md` (draft; unchanged since ml#2550, `cac25098`, 2026-11-13T00:01:52Z) |
| `…land-after-cascor-772.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md`. The `modular-gathering-squirrel` working copy is byte-identical to main's (both sha256 `73caa01d…`; the copy's mtime is 20:58:22Z), so it holds no later state. |
| `…recurrence-deploy-next.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_overtoad-rename-repair-ml-2606-recurrence-deploy-next.md` (the rename-repair line's handoff of 2026-11-23, by peer 301392; archived on 2026-11-24, by the PR that changed this row, from the copy that was untracked in `.claude/worktrees/crispy-forging-falcon/` (mtime 19:56:37Z), so every line cited here is unchanged) |
| `…seven-worktrees-archived.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_r-obs-sc-2-owner-items-recurrence-pin-0-8-1-seven-worktrees-archived.md` (this worktree's copy; landed by ml#2616, MERGED 21:20:22Z) |
| `…guard-cuts-plan-next.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md` (extra source: housekeeping and findings lists) |
| `…guard-pr-plan-v1-15-16-next.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md` (extra source: the housekeeping list the plan points at) |
| `…landed-ports-plan-v1-15-17-next.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md` (extra source: predecessor of `…seven-worktrees-archived.md`) |
| `…parent-agents-cascor-0-13-0.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md` (extra: a backup sha256 record) |
| `…parent-agents-edited-owner-items-next.md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-01_recurrence-equities-apd-ml-002-closed-parent-agents-edited-owner-items-next.md` (extra: a backup sha256 record) |
| `…SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` | `prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` (the R-OBS-SC-3 start prompt) |
| `…PYPI-PUBLISH-PROCEDURE.md` | `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` |
| `…CURSOR-FLOOD-4-DISPOSITION.md` | `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` |
| `…DEFECT-REGISTER.md` | `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` |
| archive README | `juniper-ml/tmp/worktree-archive-2026-11-23/README.md` (primary's `tmp/`) |

## Probes (all 2026-11-23, UTC; read-only)

| ID | What | When | How |
| --- | --- | --- | --- |
| P1 | State of every PR the sources name, and each publishing repo's open PRs | 21:22:51Z–21:23:26Z | `tmp/arc/agent_probe_prs.bash` (`gh pr view`, `gh pr list`) |
| P2 | Newest 3 Releases per publishing repo; PyPI's newest version of 17 packages; presence of observability 0.4.3, service-core 0.8.x, data 0.18.0/0.17.2, data-client 0.6.1 | 21:24:44Z–21:25:20Z | `tmp/arc/agent_probe_releases_pypi.bash` (`gh release list`, PyPI JSON) |
| P3 | The trio's installed observability / service-core / sentry-sdk (dist-info names) | 21:25:25Z | `ls` of each env's site-packages |
| P4 | The juniper-ml primary that `JuniperCascor1` imports (HEAD, dirtiness, version strings, editable targets) | 21:25:44Z | `tmp/arc/agent_probe_primary.bash` (`git --no-optional-locks`, read-only) |
| P5 | Listening service ports (8050–8053, 8058, 8059, 8100, 8101, 8200–8202) and Juniper containers | 21:28:31Z | `ss -ltnH` (exit 0), `docker ps -a` |
| P6 | The source lines the findings cite, re-read on each repository's `main` | 21:28:55Z–21:30Z | `tmp/arc/agent_probe_hygiene_lines.bash`, `tmp/arc/agent_probe_test_paths.bash` (`gh api …/contents`) |
| P7 | Progress markers of the one-artifact sweep in `ethereal-munching-peacock` | 21:29:48Z | `ls` of its `tmp/sweep/` |
| P8 | Files of ml#2606 (all pages), data#547 and canopy#830 in publish paths | 21:31Z, 21:38:39Z | `gh api --paginate …/pulls/N/files` |
| P9 | Parent-AGENTS.md backups (all six older files, the three restored ones), leftover housekeeping items, kept worktrees | 21:33:18Z | `tmp/arc/agent_older_backups_inverse_check.py`, `sha256sum`, `du`, `test -d`; recorded hashes via `tmp/arc/agent_probe_backup_records.bash` |
| P10 | canopy#685, recurrence#203, cascor#690 | 21:38:16Z | `gh pr view` |

Verbatim excerpts of the probe outputs are in the appendix.

## 1–2. The inventory, by group

Status says **open**, **done**, **superseded** or **in progress**, then the evidence. "As documented" means not
re-probed here. Counts at compilation: **A 19, B 8, C 17, D 13, E 8** (65 rows); for the counts after the update, see
"Checked and changed after compilation" above.

### A. Decisions only the Overtoad can make

| ID | Task | Source | Lane | Status | Blocked by | Next concrete action |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | Rule whether a fix-forward is owed for juniper-cascor 0.12.0–0.14.0, all cut ahead of P3-05 and P3-08 (with R-CASCOR's own timing, A5's D-5) | `…DEVELOPMENT-PLAN.md:1169`, `:1394-1395`, `:923`, `:1367`; `…seven-worktrees-archived.md:76` | Overtoad decision | open. Newest cascor Release `v0.14.0` (2026-11-15T01:28:19Z) and PyPI 0.14.0 (P2); cascor#690 MERGED 2026-09-25 (P10) | P3-05 and P3-08 have no PR and no session (`…PLAN-V2.md:152`, as documented) | Ask at the mid-wave sitting (`…DEVELOPMENT-PLAN.md:1394-1395`) |
| R2 | Rule who may pull the juniper-canopy primary (O13) | `…DEVELOPMENT-PLAN.md:1169`, `:648`, `:683`, `:1367`, `:1583` | Overtoad decision | open; as documented | — | Ask; ruling 7's wording for the juniper-ml primary (`:682-683`) is the model |
| R3 | A1 limb: accept or decline the data-client F-S10 source fix (no header value in the error text; raise without the cause), and its vehicle (R-DC-PATCH 0.5.1, R-DC-PATCH-6 0.6.1) | `…DEVELOPMENT-PLAN.md:1170`, `:1377`, `:698-701`, `:709`, `:1043-1044` | Overtoad decision | open. PyPI juniper-data-client newest 0.6.0, no 0.6.1 (P2) | — | Rule at §6 A1 (`:1363`) |
| R4 | A1 limb: accept or decline a cascor F-S10 fix (cascor's loader returns the env-var key unstripped) | `…DEVELOPMENT-PLAN.md:1170`, `:702`, `:709`, `:1377`, `:923` | Overtoad decision | open. No cascor Release after `v0.14.0` (P2); 0.14.0 names no F-S10 fix (`:923`, as documented) | — | Rule at §6 A1 |
| R5 | A1 limb: P6 OD-2, the order of APD-ML-003..006 | `…DEVELOPMENT-PLAN.md:1170`, `:1377`, `:331` | Overtoad decision | open; as documented | — | Rule at §6 A1 (one owner menu) |
| R6 | A1 limb: ratify or revert canopy#685's call (a), whose kept 4xx detail passes cascor's 409 text | `…DEVELOPMENT-PLAN.md:1170`, `:1363`, `:1377` | Overtoad decision | open. canopy#685 MERGED 2026-09-24T23:24:14Z (P10) | — | Rule at §6 A1 |
| R7 | A1 limb: whether host recurrence legs take a validated local port of W1.14 (to `be081fae`) or run unfixed | `…DEVELOPMENT-PLAN.md:1170`, `:1377`, `:902-907` | Overtoad decision | open. W1.14 = recurrence#203, MERGED 2026-10-17T06:07:10Z (P10) | — | Rule at §6 A1; any port passes its own S0.11 tests first (`:907-908`) |
| R8 | XC-SENTRY (a): a Sentry-side scrubbing rule for the key pattern, covering Sentry Logs as well as events | `…DEVELOPMENT-PLAN.md:513`, `:518`, `:522`, `:779`; `…PLAN-V2.md:221` | Overtoad decision | open. Whether any such rule exists is not recorded (`…PLAN-V2.md:221`); not re-probed | — | The Overtoad chooses (a) or not; it stays in force until 0.4.3 reaches running services (`…DEVELOPMENT-PLAN.md:518`) |
| R9 | XC-SENTRY (b) for the services other than the trio: blank DSNs at their next start (the juniper-deploy stack, any canopy E2E leg) | `…DEVELOPMENT-PLAN.md:514`, `:522`, `:527-528`, `:1799` | Overtoad decision | open. Nothing runs to apply it to: 0 Juniper containers, no listener on any service port (P5); the 2026-11-12 read found the deploy containers' DSN variables empty (`:527`) | — | Rule (b) for the deploy stack before R25's bring-up |
| R10 | Whether the v2 draft gets a pointer to the 2026-11-09..15 rulings, and whether v2 becomes the planning surface (v2 §6.4 item 20) | `…DEVELOPMENT-PLAN.md:1160-1161`, `:1171`, `:40`; `…PLAN-V2.md:424`, `:14` | Overtoad decision | open. v2 unchanged since ml#2550 (git log at `b2aa9026`) | — | Ask; a pointer should use the corrected stale-line list (Gaps 10) |
| R11 | Limiter wall clock: a clock stepped backwards makes the wait read above the window in all four copies, which read `time.time()`; candidate fix `time.monotonic()`; with B-9 (canopy's `_evict_expired` answers differently) | `…DEVELOPMENT-PLAN.md:1146-1147` | Overtoad decision | open; P6 re-read on main: data `juniper_data/api/security.py:257`, cascor `src/api/security.py:234`, canopy `src/security.py:273` (`_evict_expired` at `:234`), service-core `juniper_service_core/security.py:250` | — | Ask (the plan's "Next: the Overtoad") |
| R12 | WebSocket control `retry_after` and `HandshakeCooldown.get_block_remaining` round to one decimal, so a wait under 50 ms reads `0.0` | `…DEVELOPMENT-PLAN.md:1149-1150`; `…guard-cuts-plan-next.md:265-267` | Overtoad decision | open; P6: cascor `src/api/websocket/control_security.py:81`, `:154`; service-core `juniper_service_core/websocket/control_security.py:112`, `:185` | flood-4's answer of 2026-11-12 23:34:04Z chose "WebSocket gaps beside N-4", which names other gaps (`…DEVELOPMENT-PLAN.md:1150`) | Ask (the plan's "Next: the Overtoad") |
| R13 | `tests/test_release_train_registry.py` walks the checkout for `pyproject.toml` without skipping `tmp/`, so 3 tests fail locally when `tmp/` holds one | `…DEVELOPMENT-PLAN.md:1151` | Overtoad decision | open; P6: `ml_root.rglob("pyproject.toml")` at `:180` (docstring `:176`) | — | Ask, or have the Overtoad confirm the 2026-10-26 scope ruling already covers it (Gaps 14) |
| R14 | sentry-sdk 3.0.0 removed `send_default_pii`: release ml#2608's `<3` cap in a juniper-observability patch, choose its number (0.4.3 is reserved for R-OBS-SC-3), and say whether R-OBS-SC-3 ports `sentry.py` to 3.x | `…recurrence-deploy-next.md:86`; `…seven-worktrees-archived.md:56-60`, `:73`; `juniper-observability/CHANGELOG.md:9-17`; `…DEVELOPMENT-PLAN.md:1036`, `:1501` | Overtoad decision | **ruled** 2026-11-24 (21:29Z, 22:26Z): 0.4.3 supports sentry-sdk 2.x and 3.x (`>=2.35.0,<4`); R-OBS-SC-3 moves to 0.4.4; the port is ml#2647. Was: open. ml#2608 MERGED 20:50:42Z (`b2aa9026`, P1); PyPI observability newest 0.4.2, no 0.4.3 (P2); sentry-sdk 3.0.0 on PyPI since 09:30:33Z (P2); `juniper_observability/sentry.py:182` passes `send_default_pii` (P6) | — | Rule the cut and its number; a session then proposes it (`util/release_train/propose.py`), and the Overtoad approves the `pypi` gate |
| R15 | Cap `sentry-sdk` below 3 in juniper-cascor, juniper-data and juniper-canopy, whose floors are uncapped; cascor's own `sentry_sdk.init` passes `send_default_pii` | `…recurrence-deploy-next.md:87-88` | Overtoad decision | **ruled** 2026-11-24 (22:26Z): port the consumers to 3.x (cascor's bootstrap init; `juniper-observability>=0.4.3`; a `<4` cap on each sentry-sdk floor), after 0.4.3 is on PyPI. Was: open; P6: cascor `pyproject.toml:151` and canopy `:251` `sentry-sdk>=2.0.0`, data `:142` `sentry-sdk[fastapi]>=2.0.0`, cascor `src/main.py:236` `send_default_pii=False` | — | Rule: a cap PR in each now, or the cap in each next release PR (as ruling 1 of 2026-11-09 did for the floors, `…DEVELOPMENT-PLAN.md:1090`) |
| R16 | Remove `giggly-foraging-sunbeam` (its `tmp/` 6.3 GB), `sparkling-percolating-meadow` and `agent-a54a0a279acc3a863`, eligible since ml#2610 landed their scripts | `…seven-worktrees-archived.md:65-67`; `…DEVELOPMENT-PLAN.md:1172`; `…landed-ports-plan-v1-15-17-next.md:86` | Overtoad decision | open; all three present (P9) | — | The Overtoad's word per worktree; then a session archives each `tmp/` (flagged as possibly substituted) and removes the tree |
| R17 | Remove `juniper-ml/tmp/retry-after-guard-ssq1mano` (the fork-drift guard's scratch: `M1`–`M3`, `R1`–`R2` per repository) | `…guard-pr-plan-v1-15-16-next.md:75`; `…DEVELOPMENT-PLAN.md:1172` | Overtoad decision | open; present, 21 MB, 69 entries (P9). Absent from the archive README and from `…seven-worktrees-archived.md:29-38` (Gaps 4) | — | The Overtoad's word; then archive or delete under the retention rule |
| R18 | Retention of `juniper-ml/tmp/worktree-archive-2026-11-23/` (946 MB): "keep until the Overtoad rules this R-OBS-SC-2 evidence no longer needed" | archive README (its Retention line); `…seven-worktrees-archived.md:37-38` | Overtoad decision | open; as documented | — | Rule once plan v1.15.18 (R39) has recorded what the archive backs |
| R19 | When juniper-recurrence's next release (and juniper-data's 0.18.0) carry the second lock round and raise the floors to `juniper-observability>=0.4.2`, `juniper-service-core>=0.7.2` (ruling 1 of 2026-11-09) | `…DEVELOPMENT-PLAN.md:1090`, `:1074`, `:1077`, `:879`, `:1838` | Overtoad decision | open; no question asked for recurrence. P6: data `pyproject.toml:102`, `:117` and recurrence `juniper-recurrence/pyproject.toml:68`, `:102` still floor 0.4.1 / 0.7.1; newest Releases data `v0.17.1`, recurrence `juniper-recurrence-v0.8.1` (P2) | data: R-DATA-2's own gates (P3-03, P3-09; another path) | Ask whether recurrence cuts a release for the lock (its image has no Sentry path, `:1077`) |

### B. Actions only the Overtoad can take

| ID | Task | Source | Lane | Status | Blocked by | Next concrete action |
| --- | --- | --- | --- | --- | --- | --- |
| R20 | Launch the R-OBS-SC-3 (0.4.3) design session from its start prompt (ruling 4 of 2026-11-13) | `…DEVELOPMENT-PLAN.md:1167`, `:523`, `:1142`, `:1501`; `…seven-worktrees-archived.md:74-75` | Overtoad action | open; its release is now **0.4.4** (ruling of 2026-11-24, 22:26Z; the prompt's addendum of that day). Was: open. No 0.4.3 design under `notes/` at `b2aa9026`; "not launched" (`…seven-worktrees-archived.md:75`) | Best after R14 (its number) and R57 (the prompt's sentry-sdk 3 facts) | Launch from `…SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` |
| R21 | Upgrade the trio's environments: `JuniperData` (its `python3.14t`) and `JuniperCanopy1` to observability 0.4.2 and service-core 0.7.2, keeping `sentry-sdk<3` | `…DEVELOPMENT-PLAN.md:1168`, `:867-875`, `:1396`; `…seven-worktrees-archived.md:70-73` | Overtoad action | **done** 2026-11-24 22:30Z (session 031e862f, on the Overtoad's ruling of 21:29Z): `JuniperData` and `JuniperCanopy1` hold observability 0.4.2 and service-core 0.7.2, sentry-sdk unchanged; `JuniperCascor1` imports the primary's `main`; a second pass follows 0.4.3. Was: open; P3: `JuniperData` observability 0.4.0, service-core 0.5.0, sentry-sdk 2.54.0; `JuniperCanopy1` 0.4.0, 0.5.0, 2.62.0 | — | Record the versions, then upgrade with a `sentry-sdk<3` constraint (published 0.4.2 admits 3.x). The trio is stopped (P5), so no stop is needed |
| R22 | Re-run the per-lock probe in each upgraded environment and record it (ruling 6 of 2026-11-13), six DSNs blank, FastAPI's telemetry setting recorded | `…DEVELOPMENT-PLAN.md:874-875`, `:521`, `:1104`, `:867` | unowned session work | unblocked 2026-11-24 (R21, R23 done); runs once the environments hold 0.4.3 | — | After R21: run the probe per environment, name each interpreter, and record the commit the editable installs run, not pip's version |
| R23 | Settle what `JuniperCascor1` imports at the trio restart: the juniper-ml primary is on the closed ml#2605's branch, not `main`, and only the Overtoad may switch it (ruling 7 of 2026-11-13: session pulls only "on `main` and clean", never a branch switch) | `…DEVELOPMENT-PLAN.md:520`, `:682-683`, `:875`; `…recurrence-deploy-next.md:92-94` | Overtoad action | **done** by the Overtoad 2026-11-24: checkout of `main` 21:22:29Z, fast-forward to `f41b1d07` 21:22:45Z (the primary's reflog). Was: open (new; P4): HEAD is `refs/heads/task/owner-is-the-overtoadgit` at `6e230a6d` (committed 10:54:59Z; HEAD file changed 2026-11-20 22:48Z); version strings on disk 0.4.2 / 0.7.2; ml#2605 CLOSED unmerged 20:54:14Z (P1) | — | The Overtoad returns the primary to `main` or names the commit the restart runs; sessions may then pull it under ruling 7 |
| R24 | Restart the trio on the recorded probe, on P3-05, with the six Sentry DSNs blank | `…DEVELOPMENT-PLAN.md:1168`, `:874`, `:516`, `:1410` | Overtoad action | open; trio stopped (no listener on `:8101`, `:8202`, `:8051`, P5) | R22; R23; P3-05 (no PR or session, `…PLAN-V2.md:152`) | Restart once R22's record exists and P3-05 is met |
| R25 | Bring up (it is no longer a restart) the juniper-deploy stack on its pins: cascor 0.14.0 and canopy 0.10.0 (deploy#278), recurrence 0.8.1 (deploy#284), data 0.17.1 | `…DEVELOPMENT-PLAN.md:1165`, `:878`, `:1256`, `:1401`; `…seven-worktrees-archived.md:68-69` | Overtoad action | open; 0 Juniper containers (`docker ps -a`, P5); deploy#278 and deploy#284 MERGED (P1) | R9 (the DSN policy for these services) | The Overtoad brings the stack up with the DSNs R9 decides |
| R26 | Check whether the PyPI trusted publishers are bound to the `pypi` environment (needs the Overtoad's PyPI login) | `…DEVELOPMENT-PLAN.md:1219-1220`, `:1256`, `:1403`; `…land-after-cascor-772.md:248` | Overtoad action | open; as documented (the evidence: cascor 0.14.0's and data 0.17.1's PyPI files, and canopy 0.10.0's TestPyPI files, carry `environment: null`, `:1219`) | — | The Overtoad reads each project's trusted-publisher settings on PyPI and reports |
| R27 | Grant merge approval (per session) to session ffffd3 for the cascor sweep PR and the seven port PRs | `…land-after-cascor-772.md:10-11`, `:142-148`, `:203` | Overtoad action | unknown (per-session; not re-probed) | — | Answer ffffd3's request when its first PR is green |

### C. Session work a live peer owns

| ID | Task | Source | Lane | Status | Blocked by | Next concrete action |
| --- | --- | --- | --- | --- | --- | --- |
| R28 | Fix pass 3: the checker (R4-2 MAJOR, R4-3, R4-4's checker part, R4-6, NITs) and the writer (R4-4, the CHANGELOG and test-comment NITs, #767's unreleased `CHANGELOG` entry corrected in place); regenerate tree `cascor-r4`; re-run the tests, both mutation proofs, the checker proof, the 15 port simulations and the r2/r4 mutants | `…land-after-cascor-772.md:19`, `:78-85` | session ffffd3 (one-artifact sweep) | in progress (P7): `tmp/sweep/cascor-r4/` exists in `ethereal-munching-peacock` (mtime 21:28:04Z), `FIXPASS3_BRIEF.md` 19:55:43Z; completion not read | — | Finish; every R4 mutant must FAIL |
| R29 | Round-5 review of the checker's interdiff (`2feceecf…` to the new checker) and the cascor interdiff | `…land-after-cascor-772.md:86-87` | session ffffd3 (one-artifact sweep) | brief written (`ROUND5_BRIEF.md` 19:57:14Z, P7); result not read | R28 | Run it; a clean round 5 clears R30 |
| R30 | Open and land the cascor sweep PR `fix/publish-one-artifact-sweep` (11 files), built on a fresh clone of cascor `main` | `…land-after-cascor-772.md:89-148`; `…DEVELOPMENT-PLAN.md:1253`; `…recurrence-deploy-next.md:72-78` | session ffffd3 (one-artifact sweep) | open, not opened: no PR with that head, in any state (P1). Its gate cleared: cascor#772 MERGED 19:35:14Z as `e9c86f83`, from the rebuilt head `31136d64` (P1) | R29; R27 | Diff the regenerated tree against `cascor-r3/work-after772`, which was built on #772's OLD head `1e6e877a` (`:107-108`; load-bearing now), then gate, PR, merge |
| R31 | Port to juniper-canopy (`publish.yml`): one `cd`, `pyproject.toml` read through a sparse checkout under `$GITHUB_WORKSPACE`; test `src/tests/unit/test_publish_one_artifact.py:494` in `JuniperCanopy1` | `…land-after-cascor-772.md:149-165`, `:190`; `…DEVELOPMENT-PLAN.md:1254` | session ffffd3 (one-artifact sweep) | open; no PR (P1). canopy#830 MERGED 21:05:44Z, touching only `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py` among publish paths (P8) | R30 | Writer, gate, PR, the 2026-11-23 checker, review, CI, merge (`:195-203`) |
| R32 | Port to juniper-data (`publish.yml`): the tag through `env: RELEASE_TAG`; R4-5's `find_spec`; NORMALIZED digest pins (SWEEP item 23); env `JuniperData` | `…land-after-cascor-772.md:166`, `:180-182`, `:192-194` | session ffffd3 (one-artifact sweep) | open; no PR (P1). data#547 MERGED 20:39:16Z, with a 2-line docstring change to `juniper_data/tests/unit/test_publish_one_artifact.py` (P8; Gaps 12) | R30 | As R31, from `main` after #547 |
| R33 | Port to juniper-data-client: the version file read under `$GITHUB_WORKSPACE`; R4-5; normalized digests | `…land-after-cascor-772.md:167-168`, `:180-182`, `:193-194` | session ffffd3 (one-artifact sweep) | open; no PR (P1); rename #267 and B914 #268 MERGED (P1) | R30 | As R31 |
| R34 | Port to juniper-cascor-client: `env: RELEASE_TAG`; R4-5; normalized digests | `…land-after-cascor-772.md:166`, `:180-182`, `:193-194` | session ffffd3 (one-artifact sweep) | open; no PR (P1); #201 and #202 MERGED (P1) | R30 | As R31 |
| R35 | Port to juniper-cascor-worker: `env: RELEASE_TAG`; R4-5; normalized digests | `…land-after-cascor-772.md:166`, `:180-182`, `:193-194` | session ffffd3 (one-artifact sweep) | open; no PR (P1); #234 and #236 MERGED (P1) | R30 | As R31 |
| R36 | Port to juniper-recurrence (3 publishers): the version file under `$GITHUB_WORKSPACE`; no digest pins; `juniper-recurrence-model/tests/test_publish_smoke_pins.py:47`; #237's "Overtoad" comments at `publish-recurrence-app.yml:204`, `:598` | `…land-after-cascor-772.md:151`, `:167`, `:191`; `…DEVELOPMENT-PLAN.md:1211`, `:1239` | session ffffd3 (one-artifact sweep) | open; no PR (P1) | R30; coordinate with R43 (same three files) | As R31; message 301392 before arming |
| R37 | Port to juniper-ml (7 publishers): the F2 edits in `publish.yml`; config-tools and doc-tools with `python -c` last; R4-1 (retarget `tests/test_publish_testpypi_verify.py:86-90` and `tests/test_publish_subpackage_workflows.py:92-98` to the new job, "not found" fails, TestPyPI permissions at `:237`); R4-5 for ci-tools and observability; normalized digests; and the ecosystem runbook §11.8 | `…land-after-cascor-772.md:152`, `:167-179`, `:187-189`; `…PYPI-PUBLISH-PROCEDURE.md:680-712` | session ffffd3 (one-artifact sweep) | open; no PR (P1) | R30; R42 (ml#2606 edits `publish.yml`, `tests/test_publish_testpypi_verify.py`, `tests/test_publish_env_policy_drift.py`, P8); R44 | Message 301392 before arming; acceptance: no new skip in the publish tests |
| R38 | The done-when check: the 2026-11-23 checker passes all 15 ports and cascor's 3 on each repository's `main`; a copy of `verify_all_mains.bash` that calls the new checker | `…land-after-cascor-772.md:206-207` | session ffffd3 (one-artifact sweep) | open | R30–R37 | Run on every `main` after the last port merges |
| R39 | Plan v1.15.18, written on a fresh clone of `main`: the sweep PR, reviews 1, 2, 4 and 5 with fix passes 1–3, the ports, SWEEP items 28 (M5) and 29 (N6); plus the 9660dc line's results and findings, group E below, and this file's Gaps | `…land-after-cascor-772.md:208-215`; `…seven-worktrees-archived.md:46-61`; `…DEVELOPMENT-PLAN.md:1255` | session ffffd3 (one-artifact sweep) | open; `main`'s plan is v1.15.17 (`b2aa9026`) | R30–R38 for its facts; R42 (ml#2606 also edits the plan, P8) | Take in group E and Gaps 1–9 as well (Gaps 7) |
| R40 | Land the 6 sweep scripts (`tmp/arc/sweep_scripts.sha256` in `ethereal-munching-peacock`), and promote or archive round 3's proof tools; CodeQL prescreen and pre-commit first | `…land-after-cascor-772.md:217-224`, `:265-274` | session ffffd3 (one-artifact sweep) | open; as documented | — | With R39 |
| R41 | Keep `ethereal-munching-peacock` until R40 lands and its `tmp/` is archived; then its removal is the Overtoad's word | `…land-after-cascor-772.md:279-281`; `…seven-worktrees-archived.md:66-67` | session ffffd3 (one-artifact sweep) | open; present (P9) | R40 | Archive its `tmp/`, then ask |
| R42 | Repair juniper-ml#2606 (the rename PR) without reverting main's newer files; message ffffd3 before arming or merging it | `…recurrence-deploy-next.md:48-67`, `:78-80`; `…land-after-cascor-772.md:229` | session 301392 (rename repair) | OPEN, head `0658e854`, no auto-merge (P1); 2,767 files, among them `.github/workflows/publish.yml`, `tests/test_publish_testpypi_verify.py`, `tests/test_publish_env_policy_drift.py`, `util/release_train/ceremony.py`, `tests/test_release_train_ceremony.py`, the plan, `docs/REFERENCE.md`, `juniper-observability/CHANGELOG.md`, `juniper-observability/tests/test_sentry.py` (P8) | — | Re-substitute on the current `main` (after ml#2608's `[Unreleased]` entry and ml#2616); agree the order with R37 and R39 |
| R43 | Repair the collateral of juniper-recurrence#237 (and deploy#281); #237 rewrote comment lines in recurrence's three publishers | `…recurrence-deploy-next.md:68-70`; `…DEVELOPMENT-PLAN.md:1238-1239` | session 301392 (rename repair) | open; #237 MERGED 2026-11-20T22:31:29Z, deploy#281 22:43:41Z; no repair PR open in either repository (P1) | — | Open the repair PRs; agree the order with R36 |
| R44 | ml#2609 (B914 literal merges) edits `tests/test_publish_subpackage_workflows.py` and `tests/test_publish_testpypi_verify.py`, which R37 edits too | `…land-after-cascor-772.md:236-239`; `…recurrence-deploy-next.md:42` | session 301392 (rename repair) | OPEN, auto-merge armed (P1); the other five B914 PRs MERGED 20:34Z–21:17Z (P1) | — | Let it merge before R37 is built, or rebase R37 onto it |

### D. Session work nobody owns, doable now without a new ruling

| ID | Task | Source | Lane | Status | Blocked by | Next concrete action |
| --- | --- | --- | --- | --- | --- | --- |
| R45 | A telemetry test that reads `app.extra["telemetry"]`, which runs below FastAPI 0.142, where the ported tests skip (the fix pass's A-4) | `…DEVELOPMENT-PLAN.md:1145` | Hygiene T6 | **done**: data#551, cascor#779, canopy#840 (2026-11-24). Was: open; P6: data `juniper_data/tests/unit/test_api_app.py:64`, cascor `src/tests/unit/api/test_api_app.py:44`, canopy `src/tests/unit/test_main_import_and_lifespan.py:330` still `importorskip` | — | One PR per repository (§3) |
| R46 | cascor's API reference lists `/docs`, `/openapi.json` and `/redoc` as exempt; `EXEMPT_PATHS` exempts only health and `/metrics` (B-10) | `…DEVELOPMENT-PLAN.md:1148` | Hygiene T6 | **done**: cascor#778 (2026-11-24; data's `AGENTS.md` lines in data#551). Was: open; P6: `docs/api/JUNIPER_CASCOR_API_REFERENCE.md:113`; `src/api/middleware.py:16`, `:20` | — | Doc PR in juniper-cascor (§3) |
| R47 | canopy's `conf/conda_environment_cpu.yaml:47` pins `dash=3.3.0`, below `pyproject.toml:56`'s `dash>=4.0.0` | `…DEVELOPMENT-PLAN.md:1156` | Hygiene T6 | **done**: canopy#839 (2026-11-24; dash 4.4.1). Was: open; P6: both lines as cited | — | PR in juniper-canopy (§3) |
| R48 | canopy's `.github/workflows/juniper-data-schema-drift.yml:40-41` says it fires "only once juniper-data's notify matrix lists juniper-canopy" | `…DEVELOPMENT-PLAN.md:1157` | Hygiene T6 | **done**: canopy#838 (2026-11-24). Was: open; P6: `:40-41` as cited (and `:46` "yet in that matrix"); data's `notify-consumers.yml:78` lists canopy | — | Comment-only PR (§3) |
| R49 | Two stale texts ml#2576 left: the register's §2.3 compare row (service-core's "latest published wheel, 0.7.0 … still short-circuits") and `docs-full-check.yml`'s "THIS is where that gate actually bites" | `…DEVELOPMENT-PLAN.md:1162` | Hygiene T6 | **done**: ml#2623 (2026-11-24), the register row; ml#2576 had rewritten the workflow comment. Was: open; P6: `…DEFECT-REGISTER.md:279`; `.github/workflows/docs-full-check.yml:253` | — | One juniper-ml PR (§3) |
| R50 | `util/ad-hoc/2026-09-23_released_section_drift.py` sees only the first of ml#2360's two misfiling kinds (a bullet under a released section), not a wrong category | `…DEVELOPMENT-PLAN.md:1155`; `…guard-cuts-plan-next.md:268-270` | Hygiene T6 | **done**: ml#2637 (2026-11-24), `util/ad-hoc/2026-11-24_released_section_drift.py`; its eight pre-arc findings repaired by ml#2646 | — | A dated successor (§3) |
| R51 | `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py` prints `answered None` when an answer's last entry is an untimed `api-request-blob` copy | `…DEVELOPMENT-PLAN.md:1163`, `:1106` | Hygiene T6 | **done**: ml#2637 (2026-11-24), `util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py` | — | A dated successor that reads the first timestamped entry (§3) |
| R52 | juniper-service-core's app factory passes no `telemetry=`, and recurrence (uncapped `fastapi>=0.110`) builds with it (A-5) | `…DEVELOPMENT-PLAN.md:1144` | unowned session work | **done**: ml#2627 (2026-11-24), in service-core's `[Unreleased]`. Was: open; P6: `juniper_service_core/app.py:56` `app = FastAPI(` with no `telemetry`; recurrence `juniper-recurrence/pyproject.toml:55` | — | A PR into service-core's `[Unreleased]` (ships with 0.8.0) (§3) |
| R53 | Before service-core 0.8.0 (a minor), widen every `<0.8.0` cap (juniper-ml `[tools]`, data, recurrence, cascor, canopy); P2-09's and P12-28's service-core halves ride the same release | `…DEVELOPMENT-PLAN.md:1154`, `:1072` | unowned session work | open; PyPI service-core newest 0.7.2, no 0.8.x (P2); P6: data `pyproject.toml:117`, recurrence `juniper-recurrence/pyproject.toml:68`, cascor `:118`, canopy `:135` all `<0.8.0` | None formally; cap PRs land before 0.8.0's Release (§5's rule) | Do it as part of preparing 0.8.0, which no session owns (§3) |
| R54 | `…CURSOR-FLOOD-4-DISPOSITION.md` §8 stops at ruling 14 | `…DEVELOPMENT-PLAN.md:1158-1159` | flood-4 session f9fa6e (live again on 2026-11-23; moved from group D) | **done**: ml#2635 (2026-11-24) carries rulings 15–48. Was: open; §8 lists rulings 1–14; the file last changed in `734aab58`, 2026-11-09 (git log at `b2aa9026`) | — | Add rulings 15 onward from the transcripts (§3) |
| R55 | Re-read whether ml#2579 / ml#2581 brought a check that the paragraph above the compatibility matrix in `docs/REFERENCE.md` says the current row tracks `pyproject.toml` between a floor PR and its release | `…DEVELOPMENT-PLAN.md:1152-1153` | flood-4 session f9fa6e (moved from group D) | **done**: ml#2631 (2026-11-24; flood-4 ruling 48) pins the paragraph with a test. Was: answered 2026-11-23 by session 2222e504: `_DECLARES_RE` (`tests/test_pyproject_extras.py:91-92`) pins the release the sentence above the matrix names; nothing checks that the paragraph says the current row tracks `pyproject.toml` between a floor PR and its release. ml#2579 and #2581 MERGED, #2507 CLOSED (P1) | — | The flood-4 session takes the question to the Overtoad, as `…DEVELOPMENT-PLAN.md:1152` routes it |
| R56 | Restore the six older parent-`AGENTS.md` backups the blind pass rewrote (`juniper-ml/tmp/2026-10-29-parent-agents-md-backups/`, `…/2026-11-01-parent-agents-md-backup/`, `…/2026-11-07-parent-agents-md-backup/`) | `…DEVELOPMENT-PLAN.md:677`, `:2547`, `:2550`; `…parent-agents-cascor-0-13-0.md:92`; `…parent-agents-edited-owner-items-next.md:23` | unowned session work | **done** 2026-11-23 by `util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py` (session 2222e504): all six restored to their recorded sha256 (`6ffd7604`, `79b17d5e`, `5082c9c8`, `29e375ff` twice, `48e2568a`), each rewritten file kept beside it as `*.substituted-2026-11-20`; a re-run prints six `ORIGINAL` | — | Plan v1.15.18 records it (R64 follows) |
| R57 | Add the sentry-sdk 3.0.0 facts and ml#2608's cap to the 0.4.3 start prompt, as a dated addendum | `…seven-worktrees-archived.md:56-60`, `:74-75`; `…SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md:63-64`, `:73-74` | unowned session work | **done** 2026-11-23 in this document's PR: a dated addendum after the prompt's "The paths:" list | — | R14 still sets the release number |

### E. Entries the plan still lists as open that are done or superseded (plan v1.15.18 must record them)

| ID | Task | Source | Lane | Status | Blocked by | Next concrete action |
| --- | --- | --- | --- | --- | --- | --- |
| R58 | "the Overtoad's answer to the rename-repair session's 'Symlinks' question, which gates juniper-cascor#772" (and "#772 … opened once #772 merges") | `…DEVELOPMENT-PLAN.md:1243`, `:1252-1253`, `:1403` | session ffffd3 (one-artifact sweep) | done: answered "Rebuild as one signed commit (Recommended)" (`…recurrence-deploy-next.md:24-26`); cascor#772 MERGED 2026-11-23T19:35:14Z as `e9c86f83`, head `31136d64`, by its armed auto-merge (P1) | — | Record in v1.15.18 (R39) |
| R59 | "whether juniper-deploy's `juniper-recurrence:0.8.0` (`docker-compose.yml:598`) moves to 0.8.1" | `…DEVELOPMENT-PLAN.md:879`, `:1138`, `:1166`, `:1256`, `:1401`, `:1584` | session ffffd3 (one-artifact sweep) | done: deploy#284 MERGED 20:55:09Z as `7e996845` (P1); `--fail-on-stale` exit 0 (`…seven-worktrees-archived.md:21-28`) | — | Record |
| R60 | "the worktree housekeeping" and "Session … [9660dc] holds those items and the worktree housekeeping. None is done." | `…DEVELOPMENT-PLAN.md:1172`, `:1257`, `:1401` | session ffffd3 (one-artifact sweep) | done in part: seven worktrees and four branches removed 20:45:52Z and archived (`…seven-worktrees-archived.md:29-38`); R59 done; left: R16, R17, R18, R41 | — | Record; carry R16–R18 |
| R61 | "The parent's prior copy is safe in `juniper-ml/tmp/2026-11-14-parent-agents-md-backup/AGENTS.md.before-2026-11-14-edit`" | `…DEVELOPMENT-PLAN.md:1172` | session ffffd3 (one-artifact sweep) | false from 2026-11-20 (substituted) until restored on 2026-11-23 (`…seven-worktrees-archived.md:39-44`); now `90df2783`, `f3f69b34`, `3009c3f4`, and the live parent `3009c3f4` (P9) | — | Record |
| R62 | The rename census: "Eight were open at 12:03Z …"; "At 12:57Z juniper-ml#2605, juniper-cascor#772 and juniper-canopy#830 were open with auto-merge armed, and juniper-ml#2606 and juniper-data#547 were open without it"; juniper-harcot#28 open | `…DEVELOPMENT-PLAN.md:1240`, `:1246` | session ffffd3 (one-artifact sweep) | superseded (P1): cascor#772, canopy#830 (21:05:44Z), data#547 (20:39:16Z), harcot#28 (20:39:13Z) MERGED; ml#2605 CLOSED unmerged 20:54:14Z; ml#2606 OPEN | — | Record |
| R63 | `JuniperCascor1` "imports the primary at `eeb5c694`" on `main` | `…DEVELOPMENT-PLAN.md:520`, `:875`, `:1078` | session ffffd3 (one-artifact sweep) | superseded (P4): the primary is at `6e230a6d` on `task/owner-is-the-overtoadgit` | — | Record; carry R23 |
| R64 | "both versions are in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`" (`29e375ff…` → `48e2568a…`), and the 2026-11-01 pair | `…DEVELOPMENT-PLAN.md:677`, `:2547`, `:2550` | session ffffd3 (one-artifact sweep) | contradicted on disk (P9): the 2026-11-07 files hash `e3575215` / `b0a3ae8c` (substituted) | R56 | Record after R56 |
| R65 | "the juniper-deploy stack's cascor, canopy and data containers run with empty DSNs"; "Not probed: the four canopy E2E legs (`:8052`, `:8053`, `:8058`, `:8059`), listening on 2026-11-15" | `…DEVELOPMENT-PLAN.md:527-528`, `:1799` | session ffffd3 (one-artifact sweep) | superseded (P5): no Juniper container exists, and no leg listens | — | Record; R9 and R25 carry what remains |

## 3. Group D: the files a fix touches, and how to verify it

Every run of a service or suite below sets the six Sentry DSN variables to `""`
(`util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py`; `…DEVELOPMENT-PLAN.md:525`). Every upload goes through
`util/open_signed_pr.py` and the pre-push gate; merges need the Overtoad's per-session approval.

- **R45 (telemetry test below FastAPI 0.142).**
  - Files: juniper-data `juniper_data/tests/unit/test_api_app.py` (beside `:60-69`); juniper-cascor
    `src/tests/unit/api/test_api_app.py` (beside `:40-49`); juniper-canopy `src/tests/unit/test_main_import_and_lifespan.py`
    (beside `:324-335`); each repository's `CHANGELOG.md` `[Unreleased]`.
  - Verify: the new test runs, without a skip, under a FastAPI below 0.142 (recurrence's lock holds 0.141.1, so a scratch
    venv can use that) and under the locked FastAPI; it fails when `telemetry=` is removed from the app (mutation);
    data in `JuniperData`'s `python3.14t`, cascor in `JuniperCascor1` with `env -u JUNIPER_CASCOR_LOG_DIR`, canopy in
    `JuniperCanopy1`.
- **R46 (cascor's exempt-path doc).**
  - Files: juniper-cascor `docs/api/JUNIPER_CASCOR_API_REFERENCE.md:113` (drop `/docs`, `/openapi.json`, `/redoc`, and
    name APD-DATA-024's reason, as `src/api/middleware.py:20` does); `CHANGELOG.md` `[Unreleased]`.
  - Verify: the doc's list equals `EXEMPT_PATHS` at `src/api/middleware.py:16`; `juniper-check-doc-links --exclude tmp`;
    markdownlint through pre-commit.
- **R47 (canopy's conda dash pin).**
  - Files: juniper-canopy `conf/conda_environment_cpu.yaml:47` (a dash 4.x conda-forge build; check
    `dash-bootstrap-components` at `:48` against it).
  - Verify: a dry-run solve of the file (`conda env create --dry-run -f conf/conda_environment_cpu.yaml`) admits
    `pyproject.toml:56`'s `dash>=4.0.0`; no environment is changed.
- **R48 (canopy's drift-workflow comment).**
  - Files: juniper-canopy `.github/workflows/juniper-data-schema-drift.yml:38-46` (comments only).
  - Verify: actionlint; data's `.github/workflows/notify-consumers.yml:78` lists `juniper-canopy`; canopy's workflow
    tests, if any pin the text.
- **R49 (two stale texts from ml#2576).**
  - Files: juniper-ml `…DEFECT-REGISTER.md:279` (the §2.3 table row; leave the dated close note at `:1648-1656` as
    history) and `.github/workflows/docs-full-check.yml:253` (the comment).
  - Verify: `python3 -m unittest tests/test_service_fork_drift.py` (the guard that names `APD-ECO-016`), the doc-link
    check with `--exclude tmp`, actionlint, and the regression list in `ci.yml` for the touched suites.
- **R50 (released-section drift successor).**
  - Files: a new `util/ad-hoc/2026-11-2X_released_section_drift.py` (the 2026-09-23 script stays as provenance), with
    a test or self-test.
  - Verify: on `CHANGELOG.md` at the parent of `48b66130` (ml#2558's merge, which repaired the misfiling) it flags
    one bullet under a released section and five wrong-category entries; at `48b66130` and on `main` it flags none.
- **R51 (Overtoad-answers successor).**
  - Files: a new `util/ad-hoc/2026-11-2X_r_obs_sc_2_owner_answers.py` (the 2026-11-09 script stays as provenance).
  - Verify: for transcript `218ff61e` it prints ruling 7 of 2026-11-13 as answered at 10:10:51Z, and for `7d425759`
    2026-11-14T22:10:39Z (`…DEVELOPMENT-PLAN.md:1106`); every other answer the old tool prints is unchanged.
- **R52 (service-core telemetry opt-out).**
  - Files: juniper-ml `juniper-service-core/juniper_service_core/app.py:56` (data#454's opt-out); a test beside the
    app-factory tests in `juniper-service-core/tests/`; `juniper-service-core/CHANGELOG.md` `[Unreleased]`.
  - Verify: the service-core suite under the locked FastAPI and under 0.141.1; juniper-recurrence's suite against the
    edited service-core (it builds its app with `create_app`).
- **R53 (the `<0.8.0` caps, with 0.8.0's preparation).**
  - Files: juniper-ml `pyproject.toml` (`[tools]`'s `juniper-service-core>=0.7.2,<0.8.0`) and the tables that mirror it
    (`AGENTS.md`'s extras table, `docs/REFERENCE.md`); juniper-data `pyproject.toml:117`; juniper-recurrence
    `juniper-recurrence/pyproject.toml:68`; juniper-cascor `pyproject.toml:118`; juniper-canopy `pyproject.toml:135`.
  - Verify: each consumer's suite against service-core `main` (its `[Unreleased]` changes `promote_to_active`'s
    signature); juniper-ml `tests/test_pyproject_extras.py`; each cap PR merges before 0.8.0's Release.
- **R54 (flood-4 record §8).**
  - Files: juniper-ml `…CURSOR-FLOOD-4-DISPOSITION.md` §8 (`:261-314`), rulings 15 onward, ruling 17 as one ruling over
    four fixes (`…DEVELOPMENT-PLAN.md:1158`).
  - Verify: each ruling's label and time from its transcript; the CHANGELOG lines that cite them (cascor `:244` at
    `v0.14.0`, canopy `:156` and `:221` at `v0.10.0`) agree; the doc-link check.
- **R55 (the matrix paragraph check).**
  - Files: read ml#2579's and ml#2581's diffs, `tests/test_pyproject_extras.py`, `docs/REFERENCE.md` § Ecosystem
    Compatibility; a fix, if the Overtoad wants one, adds a test there.
  - Verify: a test fails when the paragraph above the matrix stops saying the current row tracks `pyproject.toml`.
- **R56 (older parent backups).**
  - Files: a new `util/ad-hoc/2026-11-2X_restore_older_parent_agents_backups.py` that writes only under
    `juniper-ml/tmp/2026-10-29-parent-agents-md-backups/`, `…/2026-11-01-parent-agents-md-backup/` and
    `…/2026-11-07-parent-agents-md-backup/`, keeping each rewritten file beside it as `*.substituted-2026-11-20`.
  - Expected prefixes: `pre-edit-2026-10-27T22-35Z` `6ffd7604`, `after-first-edit-2026-10-29T20-30Z` `79b17d5e`
    (`…parent-agents-cascor-0-13-0.md:92`); `before-deploy-pin-edit` `5082c9c8`, `after-deploy-pin-edit` `29e375ff`
    (`…parent-agents-edited-owner-items-next.md:23`); `before-juniper-ml-0-11-4-edit` `29e375ff`,
    `after-juniper-ml-0-11-4-edit` `48e2568a` (`…DEVELOPMENT-PLAN.md:677`).
  - Verify: a dry run prints six "would restore"; after `--execute`, a re-run prints six "ORIGINAL";
    `python3 -I tmp/arc/agent_older_backups_inverse_check.py` shows each file's current prefix equal to the expected one.
  - The Write tool refuses the primary's paths from a worktree-isolated session; today's restore wrote through Bash.
- **R57 (the 0.4.3 prompt).**
  - Files: juniper-ml `…SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`, a dated addendum after `:73-74` (or a successor
    prompt): sentry-sdk 3.0.0 (PyPI 2026-11-23T09:30:33Z) has no `send_default_pii` and no `sentry_sdk.scrubber`;
    main's `juniper-observability/pyproject.toml:35`, `:44` cap `<3` (ml#2608, unreleased); the consumers' uncapped
    floors (cascor `pyproject.toml:151`, canopy `:251`, data `:142`) and cascor `src/main.py:236`.
  - Verify: each fact against PyPI's JSON and `main`; the doc-link check.

## 4. Gaps and contradictions

1. **cascor#772 and "Symlinks" (a source contradicted by a measured state).** `…DEVELOPMENT-PLAN.md:1243`, `:1252`
   and `:1403`, and `…land-after-cascor-772.md:95-101`, hold #772 open, blocked and gated on the unanswered "Symlinks"
   question. The question was answered "Rebuild as one signed commit (Recommended)" (`…recurrence-deploy-next.md:24-26`),
   and #772 MERGED at 19:35:14Z (P1) from a REBUILT head, `31136d64`. The sweep's comparison base,
   `cascor-r3/work-after772`, was built on the old head `1e6e877a` (`…land-after-cascor-772.md:55`, `:91`), so the
   regenerate-and-diff step at `:107-108` is now where any difference shows.
2. **What `JuniperCascor1` would run (measured; no source has it).** `…DEVELOPMENT-PLAN.md:520`, `:875` and `:1078`
   say it imports the juniper-ml primary at `eeb5c694` on `main` (read 2026-11-15); `…seven-worktrees-archived.md:71-72`
   says it "runs editable 0.4.1 / 0.7.1", which are pip's dist-info versions (`lib/python3.14`; the 0.4.0 / 0.5.0
   dist-infos sit in the dead `lib/python3.13` tree, P3). P4 found the primary on `task/owner-is-the-overtoadgit` at
   `6e230a6d`, the head of ml#2605, which closed unmerged at 20:54:14Z. Ruling 7 of 2026-11-13 lets a session pull that
   primary only on `main` and clean, so neither the trio restart's record nor a session pull can proceed until the Overtoad
   moves it (R23). The substitution there reached only docstrings in the two shared packages
   (`prometheus_helpers.py:278`, `lifecycle/manager.py:306`, `:318`, "Overtoadship"), all committed.
3. **The older parent backups (measured).** `…DEVELOPMENT-PLAN.md:677`, `:2547` and `:2550` say both versions of the
   2026-11-01 and 2026-11-07 parent edits are in `juniper-ml/tmp/`; all six files there and in the 2026-10-29 directory
   were rewritten on 2026-11-21 00:22–00:24Z (directory mtimes) and no longer match their records (P9).
   `…seven-worktrees-archived.md:39-44` restored only the three 2026-11-14 / 2026-11-15 files and does not mention
   these. The same inverse restores all six with proof (R56).
4. **A housekeeping item dropped between handoffs.** `…guard-pr-plan-v1-15-16-next.md:75` lists
   `juniper-ml/tmp/retry-after-guard-ssq1mano`, and `…DEVELOPMENT-PLAN.md:1172` points at that list. Neither today's
   housekeeping (`…seven-worktrees-archived.md:29-38`), its "Still open" list (`:63-77`) nor the archive README names
   it; it is still there (P9; R17).
5. **Two claims on juniper-observability 0.4.3.** `…DEVELOPMENT-PLAN.md:1036` and `:1501`, and the start prompt's
   title, reserve 0.4.3 for R-OBS-SC-3; `…recurrence-deploy-next.md:86` asks the Overtoad to "Cut a juniper-observability
   0.4.3 carrying the sentry cap". `juniper-observability/CHANGELOG.md:9-17` on `main` already holds the cap under
   `[Unreleased]`, so the next cut carries it whichever number it takes (R14). **Resolved 2026-11-24**: the
   Overtoad gave 0.4.3 to the sentry-sdk 3.x port (which replaces the `<3` cap with `<4`) and moved R-OBS-SC-3 to 0.4.4.
6. **The 0.4.3 start prompt predates sentry-sdk 3.0.0.** `…SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md:73-74` asks for
   "the sentry-sdk floor each option needs" and names no ceiling; `…seven-worktrees-archived.md:56-60`, `:75` says the
   new release "changes its ground"; no source assigns the prompt's update (R57).
7. **v1.15.18's scope.** `…seven-worktrees-archived.md:46` sends its findings to "plan v1.15.18, which the one-artifact
   line owns", but that line's own brief for v1.15.18 (`…land-after-cascor-772.md:208-224`) lists only the sweep, its
   reviews, the ports and SWEEP items 28 and 29. Without a hand-off, deploy#284, the housekeeping, the restored
   backups, the three findings (blind-pass reach, sentry-sdk 3.0.0, 447 registered worktrees) and group E stay
   unrecorded.
8. **ml#2606 overlaps more than the sources say.** `…land-after-cascor-772.md:229` lists `publish.yml`, the plan and
   `ceremony.py`. P8 found 2,767 files, including `tests/test_publish_testpypi_verify.py` and
   `tests/test_publish_env_policy_drift.py` (R37's files), `juniper-observability/CHANGELOG.md` and
   `juniper-observability/tests/test_sentry.py` (ml#2608's files, merged since), `docs/REFERENCE.md` and the plan (R39).
9. **ml#2605.** `…land-after-cascor-772.md:230` says "do not merge or close it"; `…recurrence-deploy-next.md:17` says
   closing it is the Overtoad's call. It is CLOSED unmerged (20:54:14Z, P1), which fits the second, but its branch is still
   the juniper-ml primary's HEAD (item 2).
10. **The v2 draft's stale lines.** `…DEVELOPMENT-PLAN.md:1161` cites `…PLAN-V2.md` `:398-399` for "round 2's Q1 to Q4
    as open"; in the file (unchanged since 2026-11-13) Q1–Q4 sit at `:395-398`, and `:399` is "whether that session may
    cut juniper-ml 0.11.5". Also stale and unlisted: `:362` and `:363` (cascor "Unnumbered" and canopy "The second
    cut", both waiting on "Q2"), `:377` ("Each consumer's newest Release predates its second lock PR", false for cascor
    0.14.0 and canopy 0.10.0), and `:391` ("P3's follow-up session holds one"). v2 itself cites "§7.4, item 20" at
    `:14` for an item that sits in §6.4 (`:421-424`).
11. **"Restart" is now a bring-up.** `…DEVELOPMENT-PLAN.md:878`, `:1165`, `:1256` and `:1401` say restart; no Juniper
    container exists (P5; `…seven-worktrees-archived.md:68-69`).
12. **data#547 kept a publish-test edit.** `…recurrence-deploy-next.md:20-22` says the client rename PRs drop their
    `test_publish_one_artifact.py` edits; data#547 merged with two docstring lines changed in
    `juniper_data/tests/unit/test_publish_one_artifact.py` (P8). It pins no digest, so it is harmless, but R32 starts
    from it.
13. **Hygiene rows without IDs.** `…DEVELOPMENT-PLAN.md:1015` says "Appendix A lists every hygiene row"; none of
    v1.15.16's seven "Next: Hygiene (T6)" findings (`:1145`, `:1148`, `:1155`, `:1156`, `:1157`, `:1162`, `:1163`)
    appears in Appendix A (`:1809-1908`; 0 matches).
14. **R13's routing.** `…DEVELOPMENT-PLAN.md:1151` sends the `tmp/` walk to the Overtoad while citing the Overtoad's
    2026-10-26 ruling that a scan chooses its scope; the cited lines are now `:176` (docstring) and `:180`
    (`ml_root.rglob`), not `:178` and `:180`.
15. **The runbook is outside the sweep's named docs.** `…PYPI-PUBLISH-PROCEDURE.md:680-712` (§11.8) describes rung 1
    without ruling 1 of 2026-11-16's gate and the install check inside the TestPyPI job; the swept template moves both.
    `…land-after-cascor-772.md:149-207` does not name this file among the ml port's docs (R37).
16. **Nobody is named to verify the first Release through the swept workflows.** No Release has run the one-artifact
    workflows (newest: canopy `v0.10.0`, 2026-11-15T01:41:30Z, P2), and no source assigns checking that the first one
    gives PyPI TestPyPI's sha256.
17. **Recorded, not tasks.** The historical TestPyPI/PyPI differences (`…DEVELOPMENT-PLAN.md:1213-1217`) cannot be
    fixed ("an index never takes a second file under a name it holds"). The 447 registered worktrees
    (`…seven-worktrees-archived.md:61`) have no task attached.
18. **Out of this arc, named so they are not lost.** canopy legs `:8052` and `:8053` writing their logs under the
    system temp directory against the 2026-10-26 directive (`…DEVELOPMENT-PLAN.md:1084`, "not this arc's"; no leg
    listens now, P5); R-DATA-2's own gates (P3-03, P3-09); S0.11's
    relay tests; P3-05 and P3-08, which gate R24 and R1 but have no PR or session (`…PLAN-V2.md:152`); rename-only items
    of `…recurrence-deploy-next.md` (canopy#831's rebase, new record files in #2606).
19. **State that moved after the sources were written** (not contradictions): ml#2616 MERGED 21:20:22Z (`cbb13154`);
    cascor#774 21:17:44Z; five of six B914 PRs merged, ml#2609 open (`…land-after-cascor-772.md:236` lists all six as
    open); the 9660dc line's "waits on 'Cleanup' and 'Recur. pin'" (`…land-after-cascor-772.md:247`) was answered by
    20:33Z (`…seven-worktrees-archived.md:13-17`).

## Appendix: probe output excerpts (verbatim, trimmed)

P1 (21:22:51Z–21:23:26Z):

```text
juniper-cascor 772 MERGED merged=2026-11-23T19:35:14Z ... automerge=armed head=task/owner-is-the-overtoad@31136d64 mergeCommit=e9c86f83
juniper-cascor 774 MERGED merged=2026-11-23T21:17:44Z ... head=fix/b914-merge-literals@c3f7d74b mergeCommit=829af03d
juniper-ml 2605 CLOSED merged=- closed=2026-11-23T20:54:14Z ... head=task/owner-is-the-overtoadgit@6e230a6d
juniper-ml 2606 OPEN merged=- closed=- ... automerge=none head=worktree-humming-stargazing-papert@0658e854
juniper-ml 2608 MERGED merged=2026-11-23T20:50:42Z ... mergeCommit=b2aa9026
juniper-ml 2609 OPEN merged=- closed=- ... automerge=armed head=fix/b914-merge-literals@82a10e63
juniper-ml 2610 MERGED merged=2026-11-23T14:14:46Z ... mergeCommit=f00859f0
juniper-ml 2614 MERGED merged=2026-11-23T18:56:36Z ... mergeCommit=f74642b3
juniper-ml 2616 MERGED merged=2026-11-23T21:20:22Z ... mergeCommit=cbb13154
juniper-canopy 830 MERGED merged=2026-11-23T21:05:44Z ... mergeCommit=1e504572
juniper-canopy 832 MERGED merged=2026-11-23T20:34:35Z ... mergeCommit=3216001b
juniper-data 547 MERGED merged=2026-11-23T20:39:16Z ... mergeCommit=2ad7b7b5
juniper-data-client 268 MERGED merged=2026-11-23T21:00:23Z
juniper-cascor-client 202 MERGED merged=2026-11-23T21:00:36Z
juniper-cascor-worker 236 MERGED merged=2026-11-23T21:03:31Z
juniper-recurrence 237 MERGED merged=2026-11-20T22:31:29Z ... mergeCommit=93a28202
juniper-deploy 281 MERGED merged=2026-11-20T22:43:41Z ... mergeCommit=552756a1
juniper-deploy 284 MERGED merged=2026-11-23T20:55:09Z ... mergeCommit=7e996845
juniper-harcot 28 MERGED merged=2026-11-23T20:39:13Z ... mergeCommit=dd3b0bd3
=== the cascor sweep branch and any port branch ===
(no PR with head fix/publish-one-artifact-sweep, any state)
open PRs in the 8 publishing repos and deploy: only dependabot/lockfile PRs, ml#2615 (local test runner), ml#2609, ml#2606, cascor#776 (WS resume table); no port PR
```

P2 (21:24:44Z–21:25:20Z):

```text
juniper-ml v0.11.5 2026-11-13T10:24:18Z ; juniper-cascor v0.14.0 2026-11-15T01:28:19Z ; juniper-canopy v0.10.0 2026-11-15T01:41:30Z
juniper-data v0.17.1 2026-10-10T20:37:25Z ; juniper-data-client v0.6.0 ; juniper-cascor-client v0.8.0 ; juniper-cascor-worker v0.6.1
juniper-recurrence juniper-recurrence-v0.8.1 2026-11-04T23:38:03Z
PyPI: juniper-observability 0.4.2 (2026-11-09T09:51:35Z) ; juniper-service-core 0.7.2 ; juniper-ml 0.11.5 ; juniper-cascor 0.14.0 ;
      juniper-canopy 0.10.0 ; juniper-data 0.17.1 ; juniper-data-client 0.6.0 ; juniper-recurrence 0.8.1 ; sentry-sdk 3.0.0 (2026-11-23T09:30:33Z)
no juniper-observability 0.4.3, no juniper-service-core 0.8.x, no juniper-data 0.18.0 / 0.17.2, no juniper-data-client 0.6.1
```

P3 (21:25:25Z):

```text
JuniperData/lib/python3.14t: juniper_observability-0.4.0, juniper_service_core-0.5.0, sentry_sdk-2.54.0
JuniperCanopy1/lib/python3.13: juniper_observability-0.4.0, juniper_service_core-0.5.0, sentry_sdk-2.62.0
JuniperCascor1/lib/python3.13 (dead tree): 0.4.0, 0.5.0, sentry_sdk-2.58.0 ; lib/python3.14: 0.4.1 and 0.7.1 (editable), sentry_sdk-2.58.0
```

P4 (21:25:44Z):

```text
HEAD file: ref: refs/heads/task/owner-is-the-overtoadgit  -> 6e230a6d (2026-11-23 04:54:59 -0600)
modified/untracked under juniper-observability/ and juniper-service-core/: 0 ; modified tracked files, whole primary: 5
version strings: 0.4.2 (observability), 0.7.2 (service-core); both editable installs point at the primary's package dirs
```

P5 (21:28:31Z): `ss -ltnH` exit 0, no listener on 8050–8053, 8058, 8059, 8100, 8101, 8200–8202; `docker ps -a`: 0
Juniper containers.

P9 (21:33:18Z):

```text
2026-10-29 .../AGENTS.md.after-first-edit-2026-10-29T20-30Z: now 7965b7a1 inverse 79b17d5e overtoad_count=7
2026-10-29 .../AGENTS.md.pre-edit-2026-10-27T22-35Z:         now e9542d3c inverse 6ffd7604 overtoad_count=7
2026-11-01 .../AGENTS.md.after-deploy-pin-edit:              now e3575215 inverse 29e375ff overtoad_count=7
2026-11-01 .../AGENTS.md.before-deploy-pin-edit:             now 92560657 inverse 5082c9c8 overtoad_count=7
2026-11-07 .../AGENTS.md.after-juniper-ml-0-11-4-edit:       now b0a3ae8c inverse 48e2568a overtoad_count=7
2026-11-07 .../AGENTS.md.before-juniper-ml-0-11-4-edit:      now e3575215 inverse 29e375ff overtoad_count=7
restored: 90df2783, f3f69b34, 3009c3f4 ; live Juniper/AGENTS.md 3009c3f4
retry-after-guard-ssq1mano: 21M ; present: giggly-foraging-sunbeam, sparkling-percolating-meadow, agent-a54a0a279acc3a863, ethereal-munching-peacock
```
