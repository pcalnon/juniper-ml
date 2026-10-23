# Thread Handoff — Recurrence × Equities: model 0.6.0 published; #215 merged; recurrence 0.8.0 cut to the owner's `pypi` gate; the bench row (#219) landed; the 0.8.0 pins next (scripts ready)

**Date**: 2026-10-20
**Host**: turing (Darwin, Intel; no commit signing; bash 3.2) — every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py` / `util/ad-hoc/2026-10-17_push_signed_with_retry.py`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-model-0-6-0-gate-still-parked-docs-tidy-landed-215-refreshed.md` (juniper-ml#2284; written an hour before the owner cleared the gate, so its "still parked" is history)
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.11** (this session, via `util/ad-hoc/2026-10-20_plan_v1_7_11_recurrence_0_8_0_cut_bench_row_landed.py`)

---

## Goal

Continue the arc from plan v1.7.11. **This session** (one thread, merge approval granted at its start) ran the whole chain the predecessor had parked, once the owner approved the model 0.6.0 `pypi` gate mid-session:

- **Model 0.6.0 is on PyPI** (run 39197693617 green; `requires_dist` equals 0.5.0's).
- **juniper-recurrence#215** (W5.2 service half + the `[torch]` extra fix) merged as **`5e0e2b2e`**: its three red runs were re-fired with `gh run rerun <id> --failed`; one Test lane (3.13) failed once more on a stale PyPI CDN edge whose index still ended at 0.5.0 while 3.12 / 3.14 resolved 0.6.0 — a second `--failed` rerun cleared it; `util/safe_merge.py`'s armed auto-merge net merged it.
- **Recurrence 0.8.0 cut**: tree at `5e0e2b2e` → `detect.py --package juniper-recurrence --json` (UNRELEASED_CHANGES, minor) → `propose.py --dry-run` / `--execute --cross-repo` → **juniper-recurrence#220** merged as **`6a98515e`** (no consumer follow-on: juniper-ml is deferred by Q-META) → tree at `6a98515e` → **re-detect** (the pre-proposal manifest makes the ceremony plan nothing; the fresh one reads BUMPED_NOT_RELEASED) → `ceremony.py --execute --cross-repo --target-sha 6a98515e…`: Release `juniper-recurrence-v0.8.0` at `6a98515e`, archive PR **juniper-ml#2285** (auto-merge; refreshed once after #2284 moved main), publish run **39411081775 parked at the owner's `pypi` gate** (`PENDING_PYPI_APPROVAL`). The release notes carry the `[torch]` fix under Fixed.
- **The image published before the gate**: `publish-image.yml` run 39411081827 green on `release: published` (it installs the app from the tag's tree, only the model from PyPI). GHCR `0.8.0` / `0.8` / `latest` → index `sha256:f3bc2a4c1a6cee7d65a2589ddc955e7d9b6f2ad2a37db87bb83d1c9651cf854b`; linux/amd64 `sha256:481360f6494d8ecf040ec7234626b438ff184ee587d9d110abcd8a0df4ed2201`, linux/arm64 `sha256:79f1d241aeaee956c21d0c09ddceb4498dd29a3bb1942e4f20d57498ae52b735`; labels `version 0.8.0`, `revision 6a98515e41ecbc381d62bdd1ea5cbe6cc5f4a7b8` (read with an anonymous `ghcr.io/token` + `/v2/.../manifests/<tag>`, no docker).
- **juniper-recurrence#219** (the bench row) merged as **`87a28761`**: it went CONFLICTING on the CHANGELOG after #215 / #220. Recipe: push main's `juniper-recurrence/CHANGELOG.md` verbatim to the branch (signed), `update-branch`, tarball the merged head, re-run `util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py --root` (bench edits "already applied", the entry re-inserted under the fresh `[Unreleased]` as a new `### Changed`), push the file pinned to the merged head. Its Sequence Safety had been red since its first head: the symbol-loss screen's `WEAKENED` on `bench/datasets.py :: func:_full` (29 → 8 lines; its body moved into the new `_composed`). Waived with a signed commit whose body ends `Allow-Symbol-Loss: func:_full` (`push_signed_commit.py --commit-body`), carrying a one-sentence CHANGELOG note; the label is the WARN-only hatch and was not used.
- **Gate-independent, before the gate cleared**: juniper-ml#2283 (`5e8e8747`) merged `[Unreleased]`'s two `### Changed` headings and refreshed `docs/QUICK_START.md`'s pip-list block to what 0.10.0 resolves on 2026-10-20 (`[all]` 76 packages on 3.12 / 3.13 / 3.14, 18 `juniper-*` lines); the predecessor handoff landed as #2284 (`21a5c567`).
- **Prepared, not run** (both dry-checked against the live trees): `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py` and `util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py`.

## Remaining work, in order

1. **Owner**: approve the `pypi` gate on run 39411081775 (`juniper-recurrence-v0.8.0` at `6a98515e`; environment `pypi`, id 16691727515):
   `gh api -X POST repos/pcalnon/juniper-recurrence/actions/runs/39411081775/pending_deployments -f 'environment_ids[]=16691727515' -f state=approved -f comment='recurrence 0.8.0'`.
   Then verify the index: `python3 -I -c` against `https://pypi.org/pypi/juniper-recurrence/0.8.0/json` — `requires_dist` must carry `juniper-recurrence-model>=0.6.0,<0.7.0` and the `[torch]` extra `juniper-recurrence-model[torch]>=0.6.0,<0.7.0`.
2. **The juniper-ml `[recurrence]` pins** (owner rulings taken with merge approval, as for 0.7.0): on a worktree at `origin/main`, `python3 -I util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py --check` then without `--check` with `--preflight-result "<sentence>"` (run `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py --extra recurrence --extra all` first; expect `[recurrence]` 32 and `[all]` 76 packages with recurrence 0.8.0 / model 0.6.0 forced; the sentence goes into the CHANGELOG entry), then `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`, then `python3 -m unittest tests.test_pyproject_extras tests.test_global_text_search`; land the eight files (`pyproject.toml`, `tests/test_pyproject_extras.py`, `README.md`, `AGENTS.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, `CHANGELOG.md`, the script) — `docs/REFERENCE.md` and `CHANGELOG.md` as their own retried commits, each built from `git show origin/main:<path>` immediately before upload. The script sets `AGENTS.md`'s `Last Updated` to the run's UTC date and the pip-list "resolved to on" date (`--resolved-on`).
3. **The Compose pin** (juniper-deploy): fetch `gh api repos/pcalnon/juniper-deploy/tarball/main` into a scratch tree, `python3 -I util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py --root <tree> --ml-pr <step 2's PR> --index-digest sha256:f3bc2a4c1a6cee7d65a2589ddc955e7d9b6f2ad2a37db87bb83d1c9651cf854b --amd64-digest sha256:481360f6… --arm64-digest sha256:79f1d241… --publish-run 39411081827` (`--check` first), then `util/open_signed_pr.py --repo juniper-deploy` with the six files (`docker-compose.yml`, `README.md`, `docs/REFERENCE.md`, `scripts/test_recurrence_snapshots.sh`, `CHANGELOG.md`; the script lives in juniper-ml). Verify the image is still at that index digest first (`python3 -I <scratch>/ghcr_inspect.py 0.8.0`, or re-create it: anonymous token from `https://ghcr.io/token?scope=repository:pcalnon/juniper-recurrence:pull`, then `/v2/pcalnon/juniper-recurrence/manifests/0.8.0` with the OCI index Accept header).
4. **Plan v1.7.12** after the pins land (pattern: `util/ad-hoc/2026-10-19_plan_v1_7_8…` for the 0.7.0 pins); a handoff.
5. **Owner**: W0.1 service-core half (cascor restart recipe in juniper-recurrence/AGENTS.md); parent `Juniper/AGENTS.md` RELEASED paragraph (recurrence 0.8.0, model 0.6.0); juniper-data's next release carrying W5.7; refresh the juniper-recurrence and juniper-data checkouts (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data, behind #486).
6. Follow-ups: W1.12 / W1.11 smokes on the 0.8.0 image (a host whose Docker reaches GHCR); the juniper-recurrence-client `train` / `crossval` docstrings (`client.py:414`, `:522`) now owe `diagnostics` and `folding` (a client-package doc touch with its own CHANGELOG line); juniper-canopy#735–738, #751; juniper-ml#2210, #2211; juniper-deploy#250; the `ARCHIVE_B64_MAX_DEFAULT` measurement in `util/release_train/ceremony.py`; `docs/REFERENCE.md`'s pins sentence with the 0.11.x matrix row; optional: a first real run of the E-H suite with `--shared-equities-cache`.

## Landing rules learned this session

- **Re-detect after the proposal merges.** A manifest produced before the proposal says `UNRELEASED_CHANGES`; `ceremony.py` then plans *nothing* (`total 0`, no halt). Run `detect.py --json` against the tree at the proposal's merge sha and it reads `BUMPED_NOT_RELEASED`. Memory: `release-train-follow-on-pr`.
- **`propose.py` / `ceremony.py` cannot run under `python3 -I`** (`propose.py` imports its sibling `detect` from the script directory); plain `python3 util/release_train/<script>.py` works under the worktree guard.
- **A stale PyPI CDN edge can fail one matrix lane minutes after a publish**; `gh run rerun <id> --failed` once more, nothing else.
- **A bench-only juniper-recurrence PR trips the symbol-loss screen when a helper's body moves into a new function**; the enumerated `Allow-Symbol-Loss: func:<name>` trailer in a signed commit body (`push_signed_commit.py --commit-body`) is the waiver; it needs a real file change to ride on (a CHANGELOG sentence naming the restructure is the honest one).
- **The archive PR falls BEHIND whenever main moves before its CI finishes** (here #2284 landed first); one `update-branch` and its auto-merge fires. Re-check `mergeStateStatus`.
- Everything else as in the predecessor: the `pypi` gate is the owner's even with merge approval; worktree files direct-uploaded only while `origin/main` equals the worktree base (`CHANGELOG.md` / `docs/REFERENCE.md` / the plan as their own retried commits, built from `git show origin/main:<path>`); the worktree guard's refusals (one plain command per call, literal paths); gitleaks in `dir` mode on copies.

## Verification commands for the new thread

```bash
gh run view 39411081775 --repo pcalnon/juniper-recurrence --json status,conclusion
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-recurrence/json'))['info']['version'])"
gh release view juniper-recurrence-v0.8.0 --repo pcalnon/juniper-recurrence --json tagName,targetCommitish
gh pr view 2285 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'
gh pr view 219 --repo pcalnon/juniper-recurrence --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'   # MERGED 87a28761
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.11
python3 -I util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py --check   # exit 1 (pending) until the pins land
git show origin/main:pyproject.toml | grep -n 'juniper-recurrence'
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/elegant-hatching-minsky` on branch `worktree-elegant-hatching-minsky`, base `b9f9d38d`; nothing committed locally; every change landed through the API. Its modified / untracked files are all on `origin/main` once the plan / handoff PR merges; `git checkout -- . && git clean -fd` on the worktree is safe after that.
- juniper-recurrence and juniper-data checkouts untouched (juniper-data at `7465d5a4`, behind #486's `58c013e3`; juniper-recurrence now four merges behind).

## Documents created or modified this session

- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.10 → v1.7.11)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-model-0-6-0-published-recurrence-0-8-0-cut-bench-row-landed-0-8-0-pins-next.md` (this file)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-model-0-6-0-gate-still-parked-docs-tidy-landed-215-refreshed.md` (juniper-ml#2284)
- `util/ad-hoc/2026-10-20_tidy_unreleased_changed_and_quick_start_pip_list.py`, `CHANGELOG.md`, `docs/QUICK_START.md` (juniper-ml#2283)
- `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py`, `util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py`, `util/ad-hoc/2026-10-20_plan_v1_7_11_recurrence_0_8_0_cut_bench_row_landed.py` (new)
- `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.8.0.md` (juniper-ml#2285, by the ceremony)
- juniper-recurrence: #215 (merged), #220 (the proposal: `_version.py`, `CHANGELOG.md`, `AGENTS.md`), #219 (`bench/datasets.py`, `bench/run_benchmark.py`, `bench/test_bench_smoke.py`, `juniper-recurrence/CHANGELOG.md`)
- Referenced: the predecessor handoff above; `util/release_train/detect.py`, `propose.py`, `ceremony.py`; `util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py`
