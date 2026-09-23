# HANDOFF — decision 11's release train is cut; six PyPI gates await the owner, two trains remain

**Date**: 2026-09-09 (**re-evaluated 2026-09-22/23 in §10**: §1–§4 are CLOSED, and every §5 row now has a disposition or a ticket) · **Session**: <https://claude.ai/code/session_014FMjGiN9yK9ppfkUiBnao5>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fancy-marinating-nova`
**Branch**: `worktree-fancy-marinating-nova` (at `origin/main`; no PR of its own — every change this
session shipped as an API-signed PR, see §0.1)
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_partition-arc-decision-11-shipped-and-the-release-train.md`
(its §2 invariant, §3 straggler table and §6 traps still hold; this document supersedes its §1 next
actions and §4 release table).

**Documents REFERENCED** (the ecosystem convention in
`/home/pcalnon/Development/python/Juniper/AGENTS.md` § Cross-Project Conventions requires the filename
on every citation, because more than one document is cited):

- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — design of record
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — rollout plan; **§9 is
  the live register**
- `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` — §11, the release ceremony
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — this document's template
- `util/release_train/registry.yaml`, `util/release_train/{detect,propose,ceremony}.py` — the instrument

**Documents CHANGED by this session** (juniper-ml): `juniper-model-core/juniper_model_core/crossval/splits.py`,
`juniper-model-core/CHANGELOG.md`, `util/ad-hoc/2026-09-08_push_signed_commit.py`,
`util/ad-hoc/2026-09-08_changelog_insert.py` (all in #1829); `util/ad-hoc/2026-09-08_bump_version_carriers.py`,
`util/ad-hoc/2026-09-08_insert_after_line.py` and this file (the handoff PR, §8);
`notes/releases/RELEASE_NOTES_{juniper-data-client_v0.5.0,juniper-data_v0.14.0,juniper-cascor_v0.11.0,juniper-canopy_v0.7.0,juniper-recurrence-model_v0.3.0,juniper-recurrence-client_v0.3.0}.md`
(the ceremonies opened one exempt archive PR each, #1838–#1842 and #1844; all six were green but BEHIND
on the contended main, so they were closed and their six files re-landed as ONE exempt PR, #1847).
Sibling repos: §1's table.

---

## 0. PREFLIGHT

1. **Local `git commit` HANGS in this environment.** `commit.gpgsign=true` with a YubiKey-resident
   key; a `timeout 40 git commit --allow-empty` exits 124. Every commit this session went through the
   GitHub API (`createCommitOnBranch`, GitHub-signed): `util/open_signed_pr.py` for a new branch,
   `util/ad-hoc/2026-09-08_push_signed_commit.py` for a follow-up commit on an existing one. Do not
   run `git commit`, `git tag` or `gh release create --verify-tag` locally; do not `git push`.
2. **Six packages are on TestPyPI, cut as GitHub Releases, and parked at the `pypi` environment
   gate.** That gate is the owner's, never the session's (memory `feedback_deploy_approvals_paul_manages`).
   Until each is approved, `pip install` from PyPI still serves the pre-decision-11 versions and
   `POST /v1/crossval` in a PyPI-installed juniper-recurrence stays broken. The run URLs are in §2.
3. **`util/release_train/propose.py` and `ceremony.py` read the sibling checkouts on disk as inputs.**
   `git -C /home/pcalnon/Development/python/Juniper/<repo> pull --ff-only origin main` before EVERY
   run, or the whole-file API commit carries stale content. All five siblings were at `origin/main`
   at handoff (§8).
4. **The sub-agents this session spawned were killed by a session rate limit mid-task**, twice.
   They had already opened their PRs; their worktrees were removed after merge. If you spawn agents,
   give them private scratch paths — one overwrote my `scratchpad/commit_body.txt`
   (memory `reference_headless_commit_signing_hangs_use_api_commits`).
5. **Correction to the predecessor's §1: decision 5 IS implemented.** It said cascor's CLI has "zero
   `X_val`" because it grepped `src/main.py`; the plumbing is `src/spiral_problem/spiral_problem.py:1346-1440`
   (cascor#622 carves `train 0.8 / val 0.1 / test 0.1`, `_SPIRAL_PROBLEM_VAL_RATIO = 0.1`, and passes
   `x_val` to `fit()`). What remains unimplemented is **V-3, the measurement**, which cascor 0.11.0's
   changelog says out loud. Decision 12 is still unimplemented (`partition_provenance`: zero hits).
6. **Environment**: conda envs `JuniperCascor1` / `JuniperCanopy1` / `JuniperData`; canopy python needs
   `env -u LD_LIBRARY_PATH`; juniper-recurrence has no env. The worktree-isolated command guard refuses
   `sed` programs (`Nr file`, `a\`), loops that call `gh`/`git`, `$var` paths handed to `python`/`sed`,
   `env -u` inside loops, and here-docs — use the four `util/ad-hoc/2026-09-08_*.py` helpers instead.

---

## 1. Goal statement

Continue the decision-11 release train (design §9.5). **Wave 1 is cut: six of eight trains are at the
owner's PyPI gate.** Remaining: the owner's six approvals; the recurrence app's floor bump + 0.5.0;
juniper-ml's floors + 0.8.0; the documentation that records the released versions.

**Merged and verified this session** (each read back from `origin/main` or the GitHub API):

| repo | PR | what |
| --- | --- | --- |
| juniper-cascor | #631 | CHANGELOG entries for #614/#616/#620/#621/#622/#623/#625/#618/#629 — filed under `### Removed` so the renderer marks the release BREAKING |
| juniper-cascor | #635 | **0.11.0** bump (propose.py) |
| juniper-data-client | #193 | `[Unreleased]` and three docs said `"full"` stayed in `NPZ_SPLITS`; straggler S-3 |
| juniper-data-client | #194 | **0.5.0** bump + 16 carriers (`__init__`, twelve `Version:` headers, three docs headers) + the pip-audit CI fix (§6) |
| juniper-data | #386 | decision-11 `### Removed` entry (re-cut of #384, which #385 conflicted); straggler S-8 |
| juniper-data | #389 | **0.14.0** bump + `juniper_data/__init__.py` fallback literal |
| juniper-canopy | #602 | `juniper-data-client` ceiling `<0.6.0` (a hand-made follow-on: canopy's pin is in an extra, so the train opens none) |
| juniper-canopy | #604 | **straggler S-6 FIXED**: sequence installs were train-only since #369; `_whole_dataset` concatenates (1-D safe), restores entity-major order via `ticker_code_*`; S-4 doc |
| juniper-canopy | #606 | **0.7.0** bump + three fallback literals (`src/__init__.py`, `juniper_canopy/__init__.py`, `resolve_app_version`) |
| juniper-recurrence | #152 | stragglers S-5a/S-5b/S-5c/S-7: `DatasetRef.split` is `Literal["train","val","test","full"]` (422 at the edge), `--split` help names `val`, READMEs/docstring stop naming `_full`; model CHANGELOG gets its `derive_full_split` entry |
| juniper-recurrence | #156 | app `juniper-data-client` ceiling `<0.6.0` (train follow-on) |
| juniper-recurrence | #158 | **juniper-recurrence-model 0.3.0** bump |
| juniper-recurrence | #161 | **juniper-recurrence-client 0.3.0** bump + sub-package `AGENTS.md` header |
| juniper-ml | #1829 | straggler S-2 (`crossval/splits.py` docstring) + two release-train helpers |
| juniper-ml | #1847 | the six notes-archive files in one exempt PR (auto-merge armed); #1838–#1842 and #1844 closed in its favour |

Also merged (07:41Z, after the table was first written): juniper-recurrence#159 — app
`juniper-recurrence-model` ceilings `<0.4.0` (dependencies, `[torch]`, `[bench-torch]`); it went BEHIND
four times as this contended lane moved and was refreshed with `update-branch` each time. **No PR of
this arc is open in a sibling repo at handoff.** Closed unmerged: juniper-data#384 (superseded by #386),
juniper-recurrence#155 (anyio fix; another session's #154 landed the identical filter six minutes
earlier).

**Next actions, in order.** (1) Owner approves the six gates in §2. (2) §3 — the app's floor bump and
0.5.0, then juniper-ml's floors and 0.8.0. (3) §4 — documentation. (4) §5 — carried forward.

---

## 2. Six deployments pending owner approval

Each run is parked with `Publish to TestPyPI = success` and `Publish to PyPI = waiting`. TestPyPI serves
the version (HTTP 200 on `https://test.pypi.org/pypi/<pkg>/<ver>/json`); PyPI does not yet (404).

| package | Release | publish run (approve here) | archive file (all six in juniper-ml#1847) |
| --- | --- | --- | --- |
| juniper-data-client 0.5.0 | `v0.5.0` | <https://github.com/pcalnon/juniper-data-client/actions/runs/34322900465> | `RELEASE_NOTES_juniper-data-client_v0.5.0.md` |
| juniper-data 0.14.0 | `v0.14.0` | <https://github.com/pcalnon/juniper-data/actions/runs/34322906502> | `RELEASE_NOTES_juniper-data_v0.14.0.md` |
| juniper-cascor 0.11.0 | `v0.11.0` | <https://github.com/pcalnon/juniper-cascor/actions/runs/34322913355> | `RELEASE_NOTES_juniper-cascor_v0.11.0.md` |
| juniper-canopy 0.7.0 | `v0.7.0` | <https://github.com/pcalnon/juniper-canopy/actions/runs/34322919025> | `RELEASE_NOTES_juniper-canopy_v0.7.0.md` |
| juniper-recurrence-model 0.3.0 | `juniper-recurrence-model-v0.3.0` | <https://github.com/pcalnon/juniper-recurrence/actions/runs/34323535743> | `RELEASE_NOTES_juniper-recurrence-model_v0.3.0.md` |
| juniper-recurrence-client 0.3.0 | `juniper-recurrence-client-v0.3.0` | <https://github.com/pcalnon/juniper-recurrence/actions/runs/34324270593> | `RELEASE_NOTES_juniper-recurrence-client_v0.3.0.md` |

The ceremony's `detect` reads "released" from PyPI, so every row reads `BUMPED_NOT_RELEASED` until the
gate is approved, then `UP_TO_DATE`. The gate also has a 5-minute wait timer; approval during the timer
proceeds when it expires. **Order of approval does not matter for these six** — no floor among them
points at another (the app's floor bump is §3a and comes after).

---

## 3. The two trains still to run, in dependency order

**3a. juniper-recurrence (app) 0.5.0** — #159 is merged; needs `juniper-recurrence-model 0.3.0` **on
PyPI** (the app lane runs `pip install -e ".[test]"`, which resolves the model from PyPI, so a floor at an
unpublished version is red CI). Then, as ONE PR: `juniper-recurrence/pyproject.toml` floors
`juniper-recurrence-model>=0.3.0,<0.4.0` in `dependencies`, `[torch]` and `[bench-torch]`, plus an app
CHANGELOG `### Changed` bullet ("requires juniper-recurrence-model 0.3.0 — `derive_full_split` is what keeps
`POST /v1/crossval` alive on post-#369 artifacts"). No lockfile in this repo. Merge, pull, then
`propose.py --package juniper-recurrence --execute --cross-repo` (bumps `_version.py`, the app CHANGELOG,
the root `AGENTS.md` **Version** header 0.4.0 → 0.5.0 and the app row; `scripts/check_version_drift.py`
checks all three), merge, pull, ceremony (tag `juniper-recurrence-v0.5.0`). juniper-ml's `<0.5.0` cap on
the app moves in 3b.

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only origin main
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper \
  --package juniper-recurrence --json > /tmp/m.json
python3 util/release_train/propose.py --manifest /tmp/m.json --package juniper-recurrence --repo-root . \
  --ecosystem-root /home/pcalnon/Development/python/Juniper --cross-repo --release-date $(date -u +%F)   # dry-run first; then --execute
```

**3b. juniper-ml 0.8.0** — after ALL seven are on PyPI (floors resolve nothing otherwise). One PR
carrying the pin and its lockstep artifacts — `tests/test_pyproject_extras.py` asserts exact strings and
`ExtrasDocsLockstepTest` asserts the four tables:

| file | lines | change |
| --- | --- | --- |
| `pyproject.toml` | 30, 47, 48, 49 | `juniper-data-client>=0.5.0`, `juniper-canopy>=0.7.0`, `juniper-cascor>=0.11.0`, `juniper-data>=0.14.0` |
| `pyproject.toml` | 67, 68, 69 | `juniper-recurrence-model>=0.3.0,<0.4.0`, `juniper-recurrence>=0.5.0,<0.6.0`, `juniper-recurrence-client>=0.3.0,<0.4.0` |
| `tests/test_pyproject_extras.py` | 108, 115–117, 131–133 | the same seven strings |
| `AGENTS.md` | 362, 364, 367 + `**Last Updated**` | extras table rows |
| `README.md` | 85, 87, 90 | extras table rows |
| `docs/QUICK_START.md` | 58, 60, 63 | extras table rows |
| `docs/REFERENCE.md` | 105, 108–110, 118–120; 168–172 | split-column rows; add a `0.8.x` compatibility-matrix row |
| `CHANGELOG.md` | `[Unreleased]` | one `### Changed` bullet naming the seven floors and why |

Then `propose.py --package juniper-ml --execute` (in-repo: it also folds the meta ceiling co-changes),
merge, ceremony (`publish.yml`, tag `v0.8.0`). Line numbers are as of `b26acd62`; re-grep, other
sessions edit `AGENTS.md` daily.

**Optional**: `juniper-model-core` 0.3.2 — the S-2 docstring is fixed on main but the published 0.3.1
wheel is stale. `detect` will offer it as a patch. Also UNRELEASED per `detect` but outside this arc:
`juniper-cascor-model` 0.2.0, `juniper-observability` 0.5.0.

---

## 4. Documentation owed once the wheels are on PyPI

- juniper-ml `docs/REFERENCE.md` ~`:5848` ("Decision 11 SHIPPED") — add the released versions; ~`:5900`
  — the model-core docstring is fixed on main (#1829); ~`:5901` — S-6 is FIXED (canopy#604); the version
  history table ~`:7161`.
- `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:317` and `:769` — same.
- `/home/pcalnon/Development/python/Juniper/AGENTS.md` § Data Contract — add "released as juniper-data
  0.14.0 / data-client 0.5.0 / cascor 0.11.0 / canopy 0.7.0 / recurrence-model 0.3.0 /
  recurrence-client 0.3.0 …" (unversioned file: edit in place, no PR).
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §9 — release status row.
- The SemVer ruling's last step (memory `feedback_semver_beats_consumer_cap_2026-09-05`): verify each
  **published** wheel in a clean venv, not the checkout — e.g. `pip install juniper-data-client==0.5.0`
  and read `NPZ_SPLITS`; `pip install juniper-recurrence-model==0.3.0` and import `derive_full_split`.

---

## 5. Carried forward (unchanged from the predecessor unless noted)

| item | state |
| --- | --- |
| S-1 hf/kaggle stores (two-way cut, `*_full`, `generator_version="1.0.0"`) | documented in juniper-data 0.14.0's changelog as a known gap; product decision open |
| S-2 | fixed on main (#1829); published model-core wheel stale |
| S-3, S-4, S-5a/b/c, S-6, S-7, S-8 | **all fixed** (#193, #604, #152, #604, #152, #386) |
| plan R-2 / R-9 / S-5 / S-7 (canopy#559 OPEN), Chunk 5, Chunk 7 (re-baseline + snapshot provenance) | undisposed |
| Decision 12 (`partition_provenance`) | unimplemented; design §9.6.3 / §9.6.6 |
| Decision 5 | **implemented** (PREFLIGHT 5); V-2 / V-3 unmeasured, stated in cascor 0.11.0's notes |

---

## 6. Traps this session added (memory `reference_release_train_ceremony_traps_2026-09-09` has the long form)

- **data-client's Security Scans job fails on every version bump**: `pip freeze | grep` misses the PEP 660
  editable line, pip-audit audits the unpublished version. Fixed in #194 with
  `pip list --format=freeze --exclude juniper-data-client`. juniper-data's grep did not trip.
- **`propose.py` bumps `pyproject`/`_version.py`/CHANGELOG/root `AGENTS.md` only.** Carriers it misses:
  data-client `__init__.py` + twelve `Version:` headers (three spellings) + three docs headers; data and
  canopy `__init__.py` fallbacks; canopy `resolve_app_version()` and `juniper_canopy/__init__.py`;
  recurrence-client's sub-package `AGENTS.md`. `2026-09-08_bump_version_carriers.py` prepares them with
  an exact-count guard.
- **The ceremony gate reads the newest COMPLETED main run**; a concurrency-cancelled run halts it. Wait
  for the merge commit's own run. juniper-data's `ci.yml` never runs on push to main (gate passes on a
  weeks-old success).
- **The ceremony monitor died on a transient API timeout AFTER cutting juniper-data's Release** (exit 2).
  Verify `gh release view`, the archive PR and the publish run's jobs; never re-cut.
- **A proposal PR's CHANGELOG hunk sits at the top of `[Unreleased]`** and conflicts with any other PR
  adding an entry there; a superset follow-up commit does NOT resolve it (git sees two different inserts
  at one anchor) — re-cut from current main (data#384 → #386).
- **`gh pr merge --auto` on an already-green PR merges immediately** (data-client#193 did) — arm only
  after the review. A PR reading `CLEAN` with auto-merge armed merges within ~3 minutes on its own; a
  manual `gh pr merge` in that window races it ("Base branch was modified") harmlessly.
- **anyio 4.15 broke the recurrence app lane at collection** (`anyio.abc.BlockingPortal` deprecation under
  warnings-as-errors); fixed by #154 (another session) — re-run the dup-guard right before opening.
- **canopy main went red once on a timing flake** (`test_x7_loop_responsiveness` on the 3.13 job only,
  the other three matrix jobs green); the next main run cleared it. Check the failing test name before
  treating a red main as a defect.
- The predecessor's §6 traps (CodeQL threads, squash-first-commit, `Allow-Symbol-Loss`, `gh` 2.46
  `pr edit`) all still apply.

---

## 7. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fancy-marinating-nova
git fetch -q origin && git status --short && git log --oneline -1 origin/main
# Every sibling PR of this arc should read MERGED; a control that must resolve:
gh pr view 159 --repo pcalnon/juniper-recurrence --json state,mergedAt --jq '"\(.state) \(.mergedAt)"'   # MERGED 2026-09-09T07:41:24Z
# Gate state per package (waiting = still the owner's; success = approved). Control: the run id must resolve.
gh run view 34322900465 --repo pcalnon/juniper-data-client --json jobs --jq '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)"'
gh run view 34324270593 --repo pcalnon/juniper-recurrence   --json jobs --jq '.jobs[] | "\(.name)\t\(.status)\t\(.conclusion)"'
# PyPI truth (200 once approved; TestPyPI is already 200 for all six):
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-recurrence-model/0.3.0/json
curl -s -o /dev/null -w '%{http_code}\n' https://test.pypi.org/pypi/juniper-recurrence-model/0.3.0/json
# Train view (exit 1 whenever anything is not UP_TO_DATE -- normal):
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper \
  --package juniper-data-client --package juniper-data --package juniper-cascor --package juniper-canopy \
  --package juniper-recurrence-model --package juniper-recurrence-client --package juniper-recurrence
# The consolidated archive PR (exempt; auto-merge armed) -- expect MERGED, else update-branch it:
gh pr view 1847 --repo pcalnon/juniper-ml --json state,mergedAt,mergeStateStatus
```

---

## 8. Git status at handoff

This worktree is at `origin/main` (`b26acd62` when written) with the handoff PR's three files
(this file, `util/ad-hoc/2026-09-08_bump_version_carriers.py`, `util/ad-hoc/2026-09-08_insert_after_line.py`)
uploaded through the API — the local copies are untracked, never committed locally. No local branch
carries work. The five sibling primary checkouts
(`/home/pcalnon/Development/python/Juniper/{juniper-data-client,juniper-data,juniper-cascor,juniper-canopy,juniper-recurrence}`)
are clean on `main` and were pulled to `origin/main` before the last propose/ceremony run; pull again
before trusting them. The four agent worktrees this session created under
`/home/pcalnon/Development/python/Juniper/worktrees/` were removed and pruned after their PRs merged;
the three `*--feature--drop-full-family--20260905-*` worktrees inherited from 2026-09-05 were left
alone, as before.

---

## 9. What this evidence cannot support

- **No wheel has been installed from PyPI**: the "released" claim is TestPyPI + a waiting PyPI job. The
  SemVer ruling's last step — verify the *published* wheel in a clean venv — is owed after approval (§4).
- **The recurrence app's `Literal` split narrowing (#152) had one pre-existing local failure**
  (`test_docs_require_auth_when_enabled`, service-core 0.5.0 installed locally vs `>=0.6.0` required); CI
  ran with a fresh install and was green. Not a defect of #152.
- **Wave 1 releases carry whatever else was on each `main` at bump time** (cascor#632-class fixes
  from other sessions that merged before the bump are in; those that merged after are not). The
  changelog is the record; nothing was hand-selected.
- **No consensus validation was run on this document** (the session limit terminated four sub-agents;
  spawning five more was not attempted). Treat §3's line numbers and §5's dispositions as claims to
  re-derive with §7.

---

## 10. RE-EVALUATION 2026-09-22/23: the release this document awaited has shipped, and every §5 row is dispositioned

**Session**: <https://claude.ai/code/session_01WGFQ3uJtGMBygmuwxSSat4> ·
**Worktree**: `juniper-ml/.claude/worktrees/rippling-wobbling-torvalds` ·
**Branch**: `worktree-rippling-wobbling-torvalds`, fast-forwarded to `origin/main` `ba035cc9`. Every
change shipped as an API-signed PR.

**Documents REFERENCED** (more than one, so every reference carries its filename):

- this file;
- its successor `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md`
  (its §8 is the 2026-09-21 re-evaluation, and §8.7 its disposition table);
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`, the design of record;
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`, the plan (§6 chunks, §7
  risks, §9 findings, §10 release record);
- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`, new: the Decision 12
  specification;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md`,
  new: this session's own handoff, which carries the goal for the next thread.

**Documents CHANGED in juniper-ml** (all in juniper-ml#2043): this file (header and §10); the 2026-09-12 successor
(a correction under its §8.4); the spec and its script
`util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py` (both new); `docs/REFERENCE.md` (the
Decision 12 and hf/kaggle entries under "What actually remains"); the plan (a dated update after §10's
"Still open" list); and the 2026-09-23 handoff (new).

### 10.1 This file's own claims, re-derived

| claim | state on 2026-09-22/23 |
| --- | --- |
| §2: six PyPI gates await the owner | **All approved.** Each is on PyPI with a 2026-09-10 upload: data-client 0.5.0, data 0.14.0, cascor 0.11.0, canopy 0.7.0, recurrence-model 0.3.0, recurrence-client 0.3.0 |
| §3a: recurrence app 0.5.0 | On PyPI (2026-09-11) |
| §3b: juniper-ml 0.8.0 | On PyPI (2026-09-11), since superseded by 0.9.0 (2026-09-22) |
| §3: model-core 0.3.2 (optional) | On PyPI (2026-09-11) |
| §4: documentation | Done by the successor, whose header lists the files |

The PyPI latest has since moved to juniper-data **0.15.0** (2026-09-22), canopy 0.8.1 (09-18) and
juniper-ml 0.9.0 (09-22).

### 10.2 §5 row by row: the residue the successor dropped

The successor's carried-forward table (`HANDOFF_2026-09-12_…` §3, re-derived in its §8.1) kept three
of §5's rows: S-1, Decision 12 and plan §9 S-7. It dropped the rest with no disposition. A shipped item
and a dropped item read identically in a summary, so each was re-derived from source:

| §5 item | disposition | evidence |
| --- | --- | --- |
| S-1 hf/kaggle stores | Owner ruled 2026-09-22: **conform** → juniper-data#422, **merged 2026-09-23 as `ce436819`**, closing #411. Not yet released | The ruling is recorded in #422's description (its first paragraph). #411's own body still calls the decision open |
| S-2 | Released in model-core 0.3.2 | PyPI |
| S-3 … S-8 (straggler scheme) | Fixed; unchanged | §5 above |
| plan R-2, consumers accept silently | **Done** | cascor `src/api/lifecycle/manager.py:3701` (at `f6ee8de`) `def _resolve_validation_split`: refuses by default; `X_test` promotion only behind `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT`, warning that metrics are SELECTED-ON |
| plan R-9, harness rejects validation | **Done** (ml#1761) | `util/experiments/run_experiment.py` `RECURRENCE_SPLITS`; `tests/test_run_experiment.py` `test_recurrence_bad_dataset_split_rejected` |
| plan §9 S-5, juniper-ml homes | **Done**: no stale site | `util/snapshot_attribute.py` rebuilds the whole view by `np.vstack`; `prompts/agent_templates/data/ecosystem.yaml` `npz_contract` lists six keys |
| plan §9 S-7 → canopy#559 | Owner ruled 2026-09-22: **advisory check** → juniper-canopy#663 (a re-cut of #659, which was closed), **merged 2026-09-23 as `cc3588a8`**, closing #559. Not yet released | — |
| Chunk 5, §6.2 compensation | **Had been silently dropped** → juniper-data#424, with an owner question | canopy `src/validation_gate.py:50` disables "Fill synthetically" pending it |
| Chunk 7 (a) plots / attribution | **Done** (see S-5) | — |
| Chunk 7 (b) design §7 snapshot provenance | **Done.** This is NOT Decision 12: cascor tags every run's metrics | `manager.py:2035` `metrics["split"] = self._reported_split_name()` |
| Chunk 7 (c) re-baseline, decision 4 | **Not started** → juniper-ml#2034 | — |
| Decision 12 | Ruled 2026-09-03 → tracked juniper-data#423. Spec v1 written; review round 1 rated it **UNSOUND as written**, so it is **not ratifiable** until v2 folds the findings | `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` §14; published in juniper-ml#2043 |
| Decision 5 | Implemented (cascor#622) | — |
| V-2 | **Measured 2026-08-29**; see 10.4 item 1 | design §8 |
| V-3 | Unmeasured → juniper-cascor#677 | cascor 0.11.0 CHANGELOG |
| cascor#582, the arc's founding issue | Still OPEN (last touched 2026-08-29), although #616, #620 and #622 shipped its fix in 0.11.0 | **Owner: close it, with V-3 (#677) as the residue?** |

### 10.3 The successor's §8 findings (N-1 to N-6), today

- **N-1, the bench `*_full` break**: fixed (recurrence#177). Its root cause, recurrence#178, is
  addressed by recurrence#181 and juniper-data#426, which another session merged on 2026-09-23 with the
  event `juniper-data-published`. This session's parallel recurrence#180 and juniper-data#425 were
  **closed as superseded**. Two residual gaps are posted on #178: a second dispatch cancels the first,
  and a 204 does not prove a listener. #178 is still open. **The one end-to-end attempt failed on
  token scope.** juniper-data run 35808713744 (2026-09-23 02:01Z) re-sent 0.15.0's dispatch and got
  `403 Resource not accessible by personal access token`. `CROSS_REPO_DISPATCH_TOKEN` reaches data,
  cascor and canopy, but not juniper-recurrence. The fix is the owner's (10.5).
- **N-2, unreleased majors**: **closed.**
  - juniper-data 0.15.0 is on PyPI (2026-09-22), with `equities` and `equities_seq` at `VERSION 5.0.0`,
    read from the wheel. data#410 is closed.
  - Delivery: recurrence#179 widened the bench caps to `<0.16.0` (merged). juniper-deploy pins the
    `0.15.0` image (`docker-compose.yml:164,517`, helm `values.yaml:40`). juniper-ml#2033 floors
    `[servers]` at `juniper-data>=0.15.0` and bumps to 0.10.0: **merged, not released**. PyPI still
    serves juniper-ml 0.9.0 with `>=0.14.0`.
- **N-3, canopy floor**: closed. juniper-ml 0.9.0's METADATA carries `juniper-canopy>=0.8.1`.
- **N-4, README pins**: fixed (ml#1972).
- **N-5, hf/kaggle stores**: **fixed on main** by juniper-data#422 (merged 2026-09-23 as `ce436819`).
  **Not released**: PyPI juniper-data 0.15.0 still ships the two-way stores. See 10.5.
- **N-6, cascor `__version__`**: **fixed on main** by cascor#672 (merged 2026-09-23). That PR also
  found `api.models.common._API_VERSION`, the `meta.version` of every enveloped API response, stale at
  `0.6.0`. **Not released**: PyPI cascor 0.11.0 still ships the literal.

### 10.4 Corrections to documents of record

1. **§5 of this file** says "V-2 / V-3 unmeasured". V-2 was measured on 2026-08-29: the design's §8
   reports +0.0088, 95 % CI [−0.0136, +0.0311]. Only V-3 is owed.
2. **`HANDOFF_2026-09-12_…` §8.4 (N-5) and juniper-data#411** say "the `1.0.0` stamp is hashed into
   `dataset_id` … the floor protects by accident". That was **false for the stores**. Until #422, only
   the generator route hashed the version (`juniper_data/core/dataset_id.py:23`, called from
   `api/routes/datasets.py:150`), and the stores built `hf-<name>-<rows>`. What kept them apart was the
   `hf-` / `kaggle-` namespace and the absence of any caller. That is still true of every released
   wheel up to 0.15.0. juniper-data#422 (merged 2026-09-23 as `ce436819`, unreleased) moved the stores
   onto `generate_dataset_id` (`storage/external_partition.py:140`).
3. **canopy `src/demo_mode.py`'s comment** says "rank is not what `validate_npz_contract` answers". The
   helper does classify by `X_train`'s rank. The actual reason it cannot gate is that it fails closed.
   Corrected by juniper-canopy#663 (merged 2026-09-23 as `cc3588a8`).
4. **`HANDOFF_2026-09-12_…` §3 / §8.1** dropped eight of this file's §5 items without a disposition.
   10.2 dispositions every one of them.

### 10.5 In flight, and outstanding

**This session's PRs: all merged.** The owner granted merge approval for them in this session's task request. That grant is per-session and does not carry forward to a successor. Each merge went through `util/safe_merge.py` after every required context was green on the head that merged.

- juniper-data#422, **merged 2026-09-23 06:22Z as `ce436819`**, closing #411. It conforms the stores:
  - three partitions, no `*_full`, `VERSION 3.0.0`;
  - ids via `generate_dataset_id`, with the marker `"unshuffled"` in place of a null seed;
  - train-only normalisation (decision 7), found by grounding the spec (its F-2);
  - plain-JSON parameters, and ratios validated before any download.

  It was reviewed in two adversarial rounds plus a consumer-graph lane, and CI passed 22 required
  contexts. **BREAKING for store callers**: a lone `train_ratio=0.9` now raises before any download.
- juniper-canopy#663, advisory `validate_npz_contract`, **merged 2026-09-23 07:12Z as `cc3588a8`**,
  closing #559. It went BEHIND while waiting; the gate re-synced it, and the armed auto-merge net
  merged it on green.
- Both CHANGELOG entries landed under `[Unreleased]`, not under a released heading. That was checked
  on each repo's `main` after the merge.
- juniper-ml#2043 carries the Decision 12 spec, its verification script, this §10, the 2026-09-12
  handoff's correction, and the `docs/REFERENCE.md` and partition-plan updates.

**Owner decisions:**

- Release cuts, which are the owner's:
  - cascor, to ship #672;
  - juniper-data, to ship #422 (BREAKING for store callers, so the release notes must say so);
  - canopy, to ship #663;
  - juniper-ml 0.10.0 (#2033).
- juniper-data#424: does §6.2's "generate the shortfall" survive decision 9, or should canopy's
  disabled option be retired?
- The Decision 12 spec's OQ-1, OQ-2, OQ-3, OQ-5 and OQ-6 (OQ-4 is answered by #422). **Not yet**:
  ruling on v1 would ratify a design that review round 1 rated unsound. Its §14 R-2 notes that §8.3 and §9.4
  already presume OQ-2's answer.
- Close cascor#582?
- **Widen `CROSS_REPO_DISPATCH_TOKEN`** (a fine-grained PAT held in juniper-data). Add
  `pcalnon/juniper-recurrence` to its repository access with **Contents: Read and write**. Until then,
  every juniper-data release shows a red `Notify consumer repos` job after a successful publish. The
  `pypi` job, not the run, is the publish verdict.

**Agent-doable:**

- **Decision 12 spec v2.** Fold the 14 unfolded findings in §14 of
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` into §1–§13: B-1 to B-7
  (soundness) and R-1 to R-7 (executability). Four are blockers: B-1, B-2, B-3 and R-1. (C-1 to C-4
  were citation fixes, already applied.) Then run a
  **fresh** review round on v2, freezing the artifact while it runs. Round 1's lanes do not carry
  over, because they reviewed a different document.
- juniper-data#429: **every `arc_agi` artifact is unloadable through data-client**. `task_ids` is an
  object array, and the client loads with `allow_pickle=False`; reproduced. The cached store also
  swallows the error. Fix: a unicode array plus a fleet `allow_pickle=False` round-trip guard.
- juniper-data-client#211: `notify-downstream` sends with a bare `curl`, so a failed dispatch reports
  success.
- recurrence#178:
  - the two residual gaps: the concurrency group, and polling for the dispatched run after the 204;
  - after the owner widens the token, re-run
    `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.15.0`, and expect a
    `repository_dispatch` run in juniper-recurrence.
- juniper-ml#2034 (decision 4) and juniper-cascor#677 (V-3).
- **Done in juniper-ml#2043**: once #422 had merged, `docs/REFERENCE.md`'s hf/kaggle entry and the "still open"
  list in §10 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` were
  updated. Both are dated additions; the old text stands as history.
- Minor, noted but not ticketed:
  - The fallback `__version__` literals in juniper-data (`0.14.0` at 0.15.0) and cascor-worker (`0.6.0`
    at 0.6.1) are stale. Installed metadata is correct, so only an uninstalled checkout sees them.
  - juniper-recurrence `data.py:77`'s comment, and the docstring at `:69-71`, promise `ValueError`.
    A `KeyError` can escape instead, from data-client's `contract.py:72`
    (`arrays[f"{NPZ_KEY_X}_train"]`).
  - cascor's `publish.yml` TestPyPI check imports from the checkout, not from the artifact.

### 10.6 Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/rippling-wobbling-torvalds
git fetch -q origin && git status --short && git log --oneline -1 origin/main
gh pr view 422 --repo pcalnon/juniper-data    --json state,mergedAt,headRefOid
gh pr view 663 --repo pcalnon/juniper-canopy  --json state,mergedAt,headRefOid
gh issue view 178 --repo pcalnon/juniper-recurrence --json state --jq .state
# PyPI truth: what is released versus merged-and-waiting
curl -s https://pypi.org/pypi/juniper-ml/json     | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"   # 0.9.0 until 0.10.0 is cut
curl -s https://pypi.org/pypi/juniper-cascor/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"   # 0.11.0 until #672 ships
```

### 10.7 Consensus record

- **Round 1, the six code PRs.** Lane A (factual) was killed by the session limit before reporting.
  Lane B (adversarial) and Lane C (consumer graph) reported.
  - Lane C's two "MAJOR, live" version-drift findings were re-probed and **downgraded**: both literals
    are `PackageNotFoundError` fallbacks, and installed metadata is correct.
  - Lane B found the #422 defects fixed in `4574d7e1`: the unseeded-ID leak, the numpy-seed crash and
    validation after the download. It also found the #659 defects fixed in #663.
- **Round 2 (Lane B), on the corrections.** #663 **survives**. #422 had minor residuals, fixed in
  `11e45297`: float32 ratios validated before conversion, and non-JSON parameter types.
- **Spec grounding found two defects.** F-2, the decision-7 leak in the stores, is fixed in #422. F-1
  is filed as juniper-data#429.
- **CI found what no lane did.** canopy's unit lane runs without juniper-data-client (the conftest
  injects a stub), so #663's first tests passed only on a dev box that has the client. Fixed by a
  faithful fake plus a fake-versus-real agreement test. Re-verified on the merged head under a
  simulated stub: the new file plus the eight `test_demo_mode*.py` suites and `test_sequence_dataset_viz.py`
  gave 177 passed and 1 skipped (the agreement test, with its reason). With the real client: 178 passed.
  The mutation check on the final test file: 8 of 10 cases fail against pre-change `main`.
- **Spec review round 1** (2026-09-23; three independent lanes, each told to refute):
  - **S1 (citations)**: three wrong citations, fixed in place.
  - **S2 (soundness)**: **UNSOUND** in identity, versioning and legality. The choice of encoding and
    the digest's construction held; B-5 (the dtype allowlist) and B-6 (canonical JSON not enforced)
    are MAJOR findings against the same area. Seven findings, three of them blockers:
    - the legality table refuses the stores' post-fix `fit_scope: "train"`;
    - an unknown `schema_version` bypasses G1–G4;
    - the id binding is skipped for every unseeded **generator** artifact.
  - **S3 (executability)**: executable with gaps. Its blocker is §9.5's consumer census. It missed
    juniper-ml's raw `/artifact` plot loaders and recurrence's in-process bench.
  - **Disposition.** The session re-verified every finding against code and recorded it in the
    spec's §14. None is folded in, following the partition plan's §9 precedent: in-place correction
    during an open review is what produced that plan's v2/v3 defects. The spec's Status now reads
    "not ready for ratification".
- **Handoff validation lane H1** (2026-09-23, on frozen copies of this §10, the 2026-09-12
  correction and the spec's §14; told to refute): **1 refuted, 13 imprecise, about 125 held**.
  - **Refuted**: this §10 said the dispatch token's reach into juniper-recurrence was "unproven".
    Run 35808713744 had already disproven it with a 403 (10.3 N-1). This session had found the same
    thing in parallel and corrected the live text before the lane reported.
  - **Imprecise**, all applied:
    - line drift (`manager.py:3658` → `:3701`);
    - the arc_agi condition in spec §14 B-1;
    - "unseeded" → "unseeded generator";
    - "the encoding held" narrowed to the choice of encoding;
    - five, not six, open owner questions;
    - a fourth wrong citation (spec C-4);
    - R-7's missing locations;
    - bench's scope in R-1;
    - the evidence for the S-1 ruling (#422's description, not #411);
    - two section pointers;
    - the recurrence docstring line;
    - a tense ("only the generator route hashes" was true until #422).
  - **State that moved during the lane**: #422 merged while the lane ran, so every "once #422 merges"
    line was stale by the time it reported.

### 10.8 What this evidence cannot support

- **No end-to-end `repository_dispatch` has succeeded.** The one attempt showed that the token does
  **not** reach juniper-recurrence (403). Nothing yet shows that the receiver fires on a real
  dispatch. #181's own CI ran the bench on a `pull_request` event, not on `repository_dispatch`.
- **#422's stores were exercised with mocked sources only.** No real Hub or Kaggle download ran.
- **The Decision 12 spec is a proposal, and round 1 found it unsound as written** (its §14). Neither
  its verification script's 15 passes nor its golden vectors say anything about the defects in §14.
  They exercise the encoding and the digest's construction. The gate's identity, version and legality
  logic, and its enforcement of canonical JSON and the dtype allowlist, exist only as prose. Its OQs
  are the owner's, and are not ripe until v2.
- **"Merged" is not "released".** #422, #663, cascor#672 and ml#2033 are on `main` only. Until the
  owner cuts releases, PyPI serves the behaviour this §10 calls fixed.
- **"Released" in 10.1 means "on PyPI"** (HTTP 200 and upload time). Nothing here re-verified the
  behaviour of those wheels. The successor's §8.5 did that for seven of the nine.
