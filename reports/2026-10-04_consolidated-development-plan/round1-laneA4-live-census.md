# Round 1 — Lane A4 (live-state census)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-1 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round1-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- Instrument: GitHub REST through `gh api`: pulls, check-runs (latest run per check name), `actions/jobs/<id>/logs`, compare, commits (`path=` and `since=`), releases, `git/matching-refs`, issue timeline, repo events, `search/issues`, and Actions secret names (names only). PyPI JSON API (`pypi.org/pypi/<pkg>/json`). No GraphQL. measured_at 2026-10-04T21:27:25Z–21:40:38Z.
- Entry point: GitHub and PyPI live state. I built the census before reading the plan (sha256 `05d7a571d00e617d`, verified at start).
- Sample:
  - 10 repos: the 9 named, plus juniper-k8s (private, visible).
  - 13 open PRs.
  - 17 PyPI packages.
  - 15 tag-to-main compares, plus path-scoped counts for 8 sub-packages.
  - The 18 cited issues/PRs, plus ml#2101, #2104, #2113, #2115, data#422, #434 and canopy#684.
  - The data fix-forward branch.

## Census

**Open PRs** (21:27Z; re-probed 21:39:51Z). There are none in data, data-client, cascor, cascor-client, cascor-worker, deploy, recurrence or k8s.

| PR | Author / state | Created (10-04) | CI on head | Mergeable |
| --- | --- | --- | --- | --- |
| ml #2119, #2121, #2122, #2125, #2128 | cursor[bot], draft | 11:05–19:37 | green (22/22 each) | behind |
| ml #2124 | cursor[bot], draft | 19:18 | RED: pre-commit ×3 (mypy `var-annotated` + bandit B106) + Quality Gate | behind |
| ml #2127 | cursor[bot], draft | 19:36 | RED: black + B105 | behind |
| ml #2129 | cursor[bot], draft | 19:37 | RED: B105 | behind |
| **ml #2130** | pcalnon, **ready, auto-merge ARMED** | **21:34:49** | 20 ok / 5 running (21:40Z) | blocked |
| canopy #698, #700 | cursor[bot], draft | 11:03, 11:05 | green (23/23, 24/24) | behind |
| canopy #699 | cursor[bot], draft | 11:05 | **5 runs only**: test suite never ran | **dirty** |
| canopy #701 | cursor[bot], draft | 11:08 | **5 runs only**: test suite never ran | behind |

**PyPI and unreleased commits** (21:29–21:33Z). "ahead" counts whole-repo commits; "path" counts commits touching the package directory since the tag.

| Package | PyPI (uploaded) | Tag → main |
| --- | --- | --- |
| juniper-data | 0.16.0 (09-24 18:35:42Z) | v0.16.0 +9 |
| juniper-cascor | 0.11.0 (09-10) | v0.11.0 +57 |
| juniper-canopy | 0.8.1 (09-18) | v0.8.1 +58 |
| juniper-recurrence | 0.5.0 (09-11) | +21; app path +8, including #190 |
| juniper-ml | 0.10.0 (09-23) | v0.10.0 +72 |
| juniper-observability | 0.4.0 (06-14) | path +11 (ml#2086, APD-OBS-001..004) |
| juniper-service-core | 0.7.0 (08-31) | path +3 (#1974, ml#2086) |
| juniper-cascor-model | 0.1.0 (06-14) | path +15 |
| others | data-client 0.5.0, cascor-client 0.8.0, worker 0.6.1, recurrence-model/-client 0.3.0, ci-tools 0.9.0, doc-tools 0.1.2, model-core 0.3.2, config-tools 0.1.0 | Fix commits only in **worker** (#198) and **config-tools** (#1237); deploy v0.3.0 +18 (fixes #231–#233) |

- **Latest upload and Release anywhere.** The latest PyPI upload is juniper-data 0.16.0 at 2026-09-24T18:35:42Z. The latest GitHub Release is data v0.16.0, published 2026-09-24T08:52:14Z. No version tag is newer than its latest Release.
- **Merges to `main` since 2026-10-03T00:00Z:**
  - ml: 13 (#2109–#2118, #2120, #2123, #2126; head `cf711cf4`).
  - canopy: 7 (#689, #692, #693, #694, #695, #696, #697; head `1b2dd438`).
  - recurrence: 2 (**#189 at 21:19:20Z, #190 at 21:22:34Z**; head `2c34805c`).
  - data: 2 (#444, #445).
  - data-client: 2 (#217, #218).
  - cascor: 1 (#697 deps; head `95cdc562`).
  - k8s: 1 direct push (`cae6330b`, 10-03 19:17:50Z).
  - Others: 0.
- **Cited items.**
  - OPEN: recurrence#182; ml#2062, #2064, #2065, #2034; cascor#573, #679, #582, #677; canopy#661; data#409, #423, #424, #432; data-client#213.
  - CLOSED: recurrence#178 (10-03 10:16:15Z).
  - MERGED: cascor#690 (09-25 02:06Z), canopy#685 (09-24 23:24Z).
- **Data branch.** `fix/conditional-requests-round4-followups` exists. Its head is `94ce8b1f` (09-25 01:46Z), it is 2 ahead / 6 behind `main` (merge base `0f0f7e0e` = #438), it changes 15 files, and no PR has ever used it as a head.

## Findings (plan claims contradicted or missing)

| ID | Severity | Plan location | Plan says | Live state (command → result, time) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| A4-1 | MAJOR | §2 P12 row; §3 XC-P12; §4 Wave 2 (P12 lane); §7.2; Scope inputs | P0 is in flight. Route R6, the APD-ML menu and #685(a) "before its PRs open". P12-08 (after XC-PRESERVE i) → P12-09 (T4) → M0. P12-08/09 are queued as load-generating runs. The input is the P12 plan v1.2.0. | Search plus `pulls/{n}` → recurrence#189 (W0.1 recipe) merged 21:19:20Z, and recurrence#190 (W0.6 + W0.7: `train --params`, `TrainResponse.metrics_scope`) merged 21:22:34Z. **ml#2130** opened 21:34:49Z: "W0.8 replay and W0.9 matrix measured, P5 verdict GO". It moves the P12 plan to v1.3.0 and adds the W5.1 note, 2 `util/ad-hoc` scripts and 9 report files. It is ready, auto-merge is armed, and its CI was still running at 21:40:38Z. Its body says the measurement used stack run `20261004T210331Z-491a` (started 21:03Z, inside the window §1.3 calls not quiet). It also says ml's P0 code lands as "W0.2; W0.3 + W0.4" PRs from executor agents. No `feat/p0*` or `fix/p0*` ref exists yet on ml or canopy (21:39Z). | Mark W0.1 (docs half), W0.6 and W0.7 merged, and W0.8/W0.9 measured pending ml#2130. Remove P12-08/09 from §7.2 and Wave 2, or recast them as validating #2130's measurement, including P12-09's own consensus review. Add #190 to R-RECURRENCE's "Carries", since it changes the API schema. Retarget XC-P12 at W0.2–W0.5 and treat it as urgent: W0.3 needs R6, and W0.4 is APD-ML-002. The owner should decide whether to hold armed #2130 for that review. |
| A4-2 | MINOR | §3 XC-FLEET (canopy) | "#701 is clean". No CI state is given for any canopy draft. | `issues/{701,699}/events` → `automatic_base_change_succeeded` 11:15:04Z: both were stacked on #697's branch. Their heads carry 5 check-runs: 2 image builds, the manifest skipped, and the base guard (failure 11:05–11:09Z, success 11:15Z). **The test suite never ran.** #699 is `dirty`. #701's copies of #697's files are blob-identical to `main` (`78e3a3a6`, `377f3bb4`); #699's test file is not (`2dd0b3d0`). | "#701: content matches `main`; CI has never run, so it needs a push to trigger it. #699: in conflict and CI never ran." |
| A4-3 | MINOR | §3 XC-FLEET; §8 row 3 ("one open PR per file") | Each draft is dispositioned on its own. | `pulls/{n}/files` → 7 of 8 ml drafts edit `docs/REFERENCE.md` (all but #2129). #2121, #2124 and #2127 edit `ci.yml`. #2121, #2122 and #2125 edit `CHANGELOG.md`. All 8 are `behind`. | Order the dispositions per file. Merging the green #2121 forces six others to rebase. |
| A4-4 | MINOR | Success metrics; §2 P4 | 8 packages carry unreleased fixes. | Compare and path commits → juniper-cascor-worker has #198 (`.env.example` guessable `CASCOR_AUTHKEY`) and 8 commits since v0.6.1. juniper-config-tools has #1237 (`py.typed`) since v0.1.0. juniper-deploy has #231–#233 since Release v0.3.0. data-client and cascor-client have only docs, test, CI and deps commits. | State the unit ("fixes that reach a published artifact") and recount: 10 PyPI packages, 11 with deploy. Or name the exclusions. Whether #198's file ships in the wheel was not checked. |
| A4-5 | NIT | §3 XC-P12 worktree list | Four P0 worktrees. | W0.1 had a fifth branch, `docs/p0-w01-jupitercascor1-repair-recipe` (#189, now deleted). The recurrence P0 worktree persists locally after #190 merged. | Note both. The worktree becomes an XC-CLEAN candidate after XC-PRESERVE. |

## Checked and holds

- **Overview.**
  - Nothing has been published to PyPI and no GitHub Release has been cut since 2026-09-24.
  - There are 12 Cursor drafts (ml 8, canopy 4), and none was armed at 21:40Z.
  - canopy#694, #696 and #697 are merged and unreleased.
- **XC-FLEET ml CI.** Each red PR fails exactly as the plan says, per its job log:
  - #2129: B105 (job 111514476529).
  - #2124: mypy + B106 (job 111510923723).
  - #2127: black + B105 (job 111514353390).

  #2121 is green. #2125's body says "Do not merge #2122". #698 and #700 have identical titles.
- **§5.**
  - Every "current" version matches PyPI.
  - The commit counts hold: 58 for canopy, 57 for cascor, and 15 touching cascor-model.
  - Each release's listed PRs are on `main` and after its tag:
    - R-DATA: #436, #437, #438, #440.
    - R-CASCOR: #659, #672, #680, #683, #689, #690.
    - R-CANOPY-A: #678, #683, #685, #694, #696, #697.
    - R-OBS-SC: ml#2086 is not in obs v0.4.0, which is 2167 commits behind it.
- **§10.**
  - cascor `main` is `95cdc562`.
  - Data `main` is 9 commits ahead of v0.16.0.
  - The fix-forward is 2 ahead / 6 behind, at `94ce8b1f`, with no PR.
  - Data's lock pins starlette 1.7.0 and pydantic 2.13.5. Recurrence's lock pins starlette 1.6.0.
  - data#422 (`ce436819`) is an ancestor of v0.16.0.
  - recurrence#178 closed on data run 37114403856, whose event is `workflow_dispatch`.
  - juniper-k8s was last pushed 10-03 19:17:58Z.
  - ml#2117 is `8b6edddd`, merged 11:16:52Z.
- **§2.**
  - ml#2110, #2101 and #2104 are merged.
  - Every cited issue's state matches the plan's usage.
  - None of the 5 image repos has a repo-level Docker Hub secret (Wave 4 still waits).
  - `wip/backup-phase-a` is absent from the remote.

## Could not check

- GHCR images (no `read:packages`), and environment-level secrets.
- Host state: backups, the experiment stack, clamscan, the frozen `.amp/in/` artifact. Whether ml#2130 used the frozen id is therefore unverified.
- Whether cascor-worker's `.env.example` ships in the wheel.
- The P12 session's rulings, the ledger and register counts, and the CI budgets.

## What this report cannot support

- **It is a snapshot.** It covers 21:27–21:41Z. The plan's snapshot ended at 21:18Z, so A4-1 is drift after the plan was written, not an error at the time. It still changes actions, and armed ml#2130 may merge within minutes.
- **Counts are commits.** Under squash merges a commit is a PR. Path counts filter by committer date from the tag commit, which is sound because `main` is linear, but ancestry is proven only for data#422 and ml#2086.
- **Draft content was not reviewed.** It was compared only by blob identity.
