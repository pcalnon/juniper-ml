# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.0 cut and parked at the owner's PyPI gate; plan v1.7.14

**Date**: 2026-10-21
**Host**: turing (Darwin, Intel; no commit signing; bash 3.2). Every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-release-train-sees-pins-client-embargo-fixed-plan-v1-7-13.md` (juniper-ml#2301)
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.14** (this session, via `util/ad-hoc/2026-10-21_plan_v1_7_14_juniper_ml_0_11_0_cut.py --merge-sha 0b714d90 --ci-run 39575383844 --archive-pr 2307 --publish-run 39577119562`)

---

## Goal

Continue the arc from plan v1.7.14. **This session** (turing session 8) picked up the predecessor's step 1. The owner granted merge approval and approved cutting juniper-ml 0.11.0 at its start.

- **Pre-flight on `main` `fcaf5e0c`.** The predecessor's post-merge re-check passed: each of the two release-train CHANGELOG entries counts 1 on `origin/main`. `detect.py` read UNRELEASED_CHANGES → 0.11.0. `propose.py --dry-run --json` gave a PR body of 1,909 characters and a notes draft of 91,945 B, which is **122,596 B base64**. That is 2,404 B under the ceremony's 125,000 B cap; the predecessor measured 6,936 B of headroom before more `[Unreleased]` entries landed. Every pyproject pin change in the `v0.10.0..main` window is recorded in `[Unreleased]`.
- **A generator gap, caught before `--execute`.** `tests/test_pyproject_extras.py` `ReadmeCompatTableTest.test_compat_table_lead_in_names_current_version` requires README's "The pyproject pins matching `juniper-ml` X:" lead-in to name the pyproject version. `propose.py` edits only `pyproject.toml`, `CHANGELOG.md` and `AGENTS.md`, so the bare proposal fails Regression Tests with `'0.10.0' != '0.11.0'`; I reproduced that on a scratch copy. This was the first generated juniper-ml proposal since the guard landed (#1972); 0.10.0 was bumped by hand (#2033). **The generator is not fixed yet** (Remaining work, item 2).
- **juniper-ml#2306, merged as `0b714d90` at 09:14:13Z.** It carries three signed commits:
  - `1b0d95bf`: `propose.py --execute`'s own commit, branched from `fcaf5e0c`. Its diff was verified to be exactly the three expected hunks.
  - `decbd9d1`: `README.md`'s lead-in plus the new idempotent `util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py`.
  - `719e4d30`: `docs/REFERENCE.md`, all three edits written by that script:
    - the compatibility sentence names 0.11.0's `[recurrence]` ranges and keeps the 0.8.0–0.10.0 ranges, read from PyPI, as history;
    - a new `0.11.x` matrix row (data `>=0.17.0`, canopy `>=0.9.0`);
    - the stale `0.6.0` Version cell now says `0.11.0`.

  The 1,049,291 B upload landed on attempt 1. The link was 5 GHz ch 149 at SNR 10 dB with 0% loss to both the gateway and 1.1.1.1.

  The PR went BEHIND once during CI (#2305, two handoff prompts). `util/safe_merge.py` refreshed it server-side and merged it. At `0b714d90`, `[Unreleased]` is empty, and none of `[0.11.0]`'s 56 bullets appears in an earlier juniper-ml release's notes.
- **The cut.**
  - `detect.py` at `0b714d90` read BUMPED_NOT_RELEASED.
  - Main `ci.yml` run 39575383844 completed green at 09:26:24Z.
  - The final notes preview (`util/ad-hoc/2026-09-12_ceremony_notes_preview.py`) measured 91,522 B raw and **122,032 B base64, 2,968 B under the cap**, so no condensing was needed.
  - `ceremony.py --execute --cross-repo --target-sha 0b714d90fea5e687635412b6dd55bd2c823383d8` ended in **PENDING_PYPI_APPROVAL**:
    - Release `v0.11.0` (`--latest`; the tag is commit `0b714d90`), published 09:27:36Z;
    - archive PR juniper-ml#2307 (`notes/releases/RELEASE_NOTES_v0.11.0.md`, auto-merge armed; `util/safe_merge.py --pr 2307 --execute` was started in the background);
    - publish run **39577119562**: Build and Validate passed, Publish to TestPyPI passed (TestPyPI serves 0.11.0, wheel and sdist, 17 juniper requirements), and **Publish to PyPI is waiting at the `pypi` gate**.
- **Plan v1.7.14** updates the Status line, the Progress block (a session 8 bullet; Next rewritten) and the revision row. It lands in one PR with this handoff and the script.

## Remaining work, in order

1. **Owner: approve the juniper-ml 0.11.0 `pypi` gate.** The run is 39577119562 and the environment is `pypi` (id `12341743943`; it has a 5-minute wait timer). Approve on the run page ("Review deployments"), or run:
   `gh api -X POST repos/pcalnon/juniper-ml/actions/runs/39577119562/pending_deployments -F 'environment_ids[]=12341743943' -f state=approved -f comment='juniper-ml 0.11.0'`.
   The agent does not approve this gate (memory `pypi-gate-is-owner-only`). After the publish:
   - `python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"` should print `0.11.0`.
   - Check that `requires_dist` carries `juniper-recurrence<0.9.0,>=0.8.0`, `juniper-recurrence-model<0.7.0,>=0.6.0`, `juniper-data>=0.17.0` and `juniper-canopy>=0.9.0`.
   - Confirm #2307 merged; if it did not, run `python3 util/safe_merge.py --pr 2307 --repo juniper-ml --execute`.
   - The parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0) is the owner's: that file is not on turing.
2. **Fix the generator gap**, so the next juniper-ml proposal is green as generated. In `util/release_train/propose.py`, when the bumped package is the meta (`juniper-ml`, `path: "."`), also rewrite `README.md`'s `The pyproject pins matching \`juniper-ml\` <old>:` line (the regex is `_COMPAT_LEAD_RE` in `tests/test_pyproject_extras.py`; `util/ad-hoc/2026-09-21_sync_readme_compat_table.py` renders the whole table). Then add it to `Files changed` and add a test in `tests/test_release_train_propose.py`. Run the `.py` fix's discrimination check: on `main`'s module the new test must fail. `docs/REFERENCE.md`'s matrix row and sentence stay a per-cut manual co-change; `util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py` is the pattern.
3. **Post-merge re-check** (memory `api-whole-file-uploads-rebase-on-main`). About an hour after #2306 merged, each of these should print 1:
   - `git show origin/main:README.md | grep -c 'pyproject pins matching .juniper-ml. 0.11.0'`
   - `git show origin/main:docs/REFERENCE.md | grep -c '^| 0.11.x '`

   A revert costs one re-run of `util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py` on a fresh `main` tree.
4. **Owner** (carried from the predecessor):
   - the juniper-recurrence-client 0.3.1 release (it carries juniper-recurrence#221's embargo fix), and whether to add `embargo_days`;
   - juniper-config-tools 0.2.0 for the typing marker (backfill its `[Unreleased]` first), or leave it;
   - the W0.1 service-core half;
   - juniper-data's next release carrying W5.7;
   - refreshing the juniper-recurrence and juniper-data checkouts (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data).
5. **Follow-ups** (carried):
   - the W1.12 / W1.11 smokes on the 0.8.0 image, on a host whose Docker reaches GHCR;
   - juniper-ml#2211: `save_model` via `POST /v1/model/snapshots` with `expect_operation_id` (juniper-ml 0.11.0 pins recurrence 0.8.0);
   - juniper-ml#2210: `per_run_timeout_seconds` against the summed driver budgets;
   - juniper-canopy#735–738 and #751; juniper-deploy#250;
   - the `ARCHIVE_B64_MAX_DEFAULT` runner-side measurement in `util/release_train/ceremony.py` (0.11.0's archive was 2,968 B under the cap);
   - optional: a first real run of the E-H suite with `--shared-equities-cache`.

## Landing rules learned this session

- **`propose.py --execute` uploads whole files built from the LOCAL `--repo-root`** onto a branch cut from main's live tip. Immediately before `--execute`, `git fetch origin main` and confirm `git rev-parse HEAD origin/main` agree; afterwards, check that `gh pr diff` shows only the generator's hunks.
- **Simulate the proposal before `--execute`.** Copy the tree to the scratchpad, apply the three edits, and run the suites that read the version, README or REFERENCE. That is how the README guard was found. Scratch scripts: `simulate_bump.py`, `run_suites.py`.
- **Put the co-changes on the proposal branch**, one signed commit per large file (`util/push_signed_commit.py --expected-head <head>`, `--commit-body-file` for the trailers). No CHANGELOG entry, because the notes were within 3 KB of the archive cap. The ceremony renders from `[0.11.0]`, and the `--target-sha` tag makes the tag window equal to the merge sha.
- **The release order that worked**: `safe_merge.py --execute` (it handled one BEHIND by itself) → `git reset --hard <merge sha>` on the worktree (after proving every local edit was in it) → re-detect → `gh run watch <ci run> --exit-status` → ceremony `--dry-run` → `--execute` (about 2 min from Release to the gate).
- Everything else is as in the predecessor: the `pypi` gate is the owner's; one plain command per call under the worktree guard; the dir-mode secret scan runs through a scratchpad wrapper.

## Verification commands for the new thread

```bash
gh pr view 2306 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'            # MERGED 0b714d90
gh pr view 2307 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'            # MERGED (archive) once its CI is green
gh run view 39577119562 --repo pcalnon/juniper-ml --json status,conclusion -q '.status + " " + .conclusion'                  # waiting -> completed success after the owner's approval
gh api repos/pcalnon/juniper-ml/git/ref/tags/v0.11.0 -q .object.sha                                                          # 0b714d90fea5e687635412b6dd55bd2c823383d8
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.10.0 until the gate, then 0.11.0
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.14
python3 util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py --check                                                    # every site "already at target", exit 0
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/rustling-sniffing-flurry` on branch `worktree-rustling-sniffing-flurry`, reset to `main` `0b714d90` after #2306 merged. Nothing is committed locally; every change landed through the API. The plan edit, this handoff and the v1.7.14 script are the working-tree changes that the plan PR carries. Once it merges, `git checkout -- . && git clean -fd` on the worktree is safe.
- The juniper-recurrence and juniper-data checkouts are untouched.

## Documents created or modified this session

- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.13 → v1.7.14)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md` (this file)
- `util/ad-hoc/2026-10-21_plan_v1_7_14_juniper_ml_0_11_0_cut.py` (new)
- juniper-ml#2306: `pyproject.toml`, `CHANGELOG.md`, `AGENTS.md` (the generator's commit); `README.md`, `docs/REFERENCE.md`; `util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py` (new)
- juniper-ml#2307 (the ceremony's archive PR): `notes/releases/RELEASE_NOTES_v0.11.0.md` (new)
- Referenced:
  - the predecessor handoff above;
  - `util/release_train/detect.py`, `util/release_train/propose.py` (`_execute_signed_pr`), `util/release_train/ceremony.py` (`ARCHIVE_B64_MAX_DEFAULT`, `open_archive_pr`);
  - `tests/test_pyproject_extras.py` (`ReadmeCompatTableTest`);
  - `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`, `util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py`, `util/ad-hoc/2026-09-12_ceremony_notes_preview.py`;
  - `util/ad-hoc/README.md` § Release-train ceremony preflight;
  - `notes/requirements/by-area/DEP.md` (JR-ML-DEP-042), `notes/requirements/by-area/OPS.md` (JR-ML-OPS-007).
