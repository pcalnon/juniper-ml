# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.4 at the owner's `pypi` gate; plan v1.15.13

**Date**: 2026-11-06 UTC (this host's clock is local time, UTC−6)
**Session**: `61859b4a`, the Linux host, worktree `.claude/worktrees/moonlit-noodling-papert`. Commits are signed only through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`). Never use a local `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_recurrence-equities-0-8-1-published-owner-rulings-recorded-ml-floor-next.md` (landed by ml#2467). Start from this file. Its items 1–3 are done (below). Its items 4–6 carry forward unchanged.

---

## Goal

Continue the recurrence × equities arc: P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, at v1.15.13 once the PR carrying this file merges. Next:

1. Re-check that PR after it merges.
2. Finish juniper-ml 0.11.4 once the owner approves its `pypi` gate.

## Completed this session (2026-11-06)

- **Re-check of ml#2467 passed.** Plan v1.15.12, spec v0.2.2 and all six files are on `main` (`87181fed`). The predecessor worktree's differing plan and spec are stale tracked copies, v1.15.10 and v0.2.0, not unlanded work.
- **The owner ruled, in this session's AskUserQuestion:**
  - juniper-ml's `[recurrence]` floor: "PR now, then cut 0.11.4";
  - recurrence's smoke pin: "Fix + drift test";
  - and "merge approval granted" for this arc's PRs.
- **ml#2473 merged** (`84569b4a`): `[recurrence]` floors `juniper-recurrence>=0.8.1,<0.9.0`.
  - It touches seven files plus `util/ad-hoc/2026-11-06_raise_recurrence_floor_0_8_1.py`.
  - The PyPI pre-flight resolves `[recurrence]` in 32 packages and `[all]` in 95, on Python 3.12, 3.13 and 3.14.
- **juniper-recurrence#230 merged** (`3529dfd9`; all post-merge runs green).
  - `publish-recurrence-model.yml:173` now installs `juniper-model-core>=0.2.0,<0.4.0`.
  - New test `juniper-recurrence-model/tests/test_publish_smoke_pins.py`; it fails on the old pin.
  - The model CI's `changes` ERE and its `on.push.paths` now name the publish workflow.
  - Evidence: model 0.6.0's publish (run 39197693617, job 117883986182) installed model-core 0.1.0, printed pip's "incompatible" error, and passed.
- **juniper-ml 0.11.4 is cut and parked.**
  - `util/release_train/detect.py` proposed minor/0.12.0. Its rule makes any `### Changed` minor before 1.0, so the manifest was set to patch/0.11.4 by the owner's ruling, as for 0.11.2.
  - The proposal was ml#2482 (`957f0e94`). The co-change commit `faa2848e` used `util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py`.
  - Pre-cut checks all passed:
    - the proposal simulator regressed 0 suites;
    - the notes render as PATCH, breaking NO;
    - only #2473 and the bump touch wheel files since `v0.11.3`;
    - 0.11.3's section matches its archive.
  - Release `v0.11.4` was cut at 14:03:58Z on `957f0e94` (Latest), with archive PR ml#2497, armed.
  - **Publish run 42230617125 waits at the `pypi` gate**: Build and TestPyPI succeeded, and `pending_deployments` is `pypi`. TestPyPI's metadata carries `juniper-recurrence<0.9.0,>=0.8.1`.
- **O13 is narrowed** by the owner's answer of 09:40:25Z in session `0b8fa86a`. I checked it against that transcript (lines 2029 and 2033) before applying it. The ruling covers four primaries; who may pull the canopy primary stays open.
  - The canopy Phase 16 session (`canopy-phase16-round28-reports-in-pass-next`) asked for this and was acknowledged.
  - Plan v1.15.13 records it, via `util/ad-hoc/2026-11-06_consolidated_plan_v1_15_13_floor_0_11_4_o13_narrowed.py`.
- **R-DATA-2 is still blocked.** PyPI serves observability 0.4.1 and service-core 0.7.1, so R-OBS-SC-2 is not out, and juniper-data has no P3-03 or P3-09 PR.

## Remaining work, in order

1. **Re-check this PR after it merges.** Plan v1.15.13 must be on `main`, with the plan script and this handoff present. **Send the canopy Phase 16 session the PR number** if this session did not.
2. **After the owner approves run 42230617125:**
   - verify `https://pypi.org/pypi/juniper-ml/0.11.4/json`, using the version endpoint (the aggregate endpoint lags). `requires_dist` must carry `juniper-recurrence<0.9.0,>=0.8.1; extra == "recurrence"`, and the wheel sha256 must equal TestPyPI's;
   - confirm ml#2497 merged.
3. **Parent `Juniper/AGENTS.md`**: its RELEASED paragraph says "juniper-ml 0.11.3 … is the latest on PyPI".
   - The file is unversioned, so get the owner's word and back it up first, as `juniper-ml/tmp/2026-11-01-parent-agents-md-backup/` did.
   - Then add 0.11.4: the `[recurrence]` floor `>=0.8.1` and its publish run.
4. **Plan v1.15.14** records the publish: R-ML-RECURRENCE-FLOOR shipped (§5 row and the 2026-11-06 block).
5. **Carried from the predecessor**:
   - R-DATA-2 (plan §5: P3-03 → P3-09 → R-OBS-SC-2 on PyPI → data's second lock PR; widen recurrence's `[bench]` caps from `<0.18.0` first; carry D-07's retro-note);
   - P5 W4 (data-client caps to `<0.8.0`);
   - the owner's §6 A1 items (APD-ML OD-2, canopy#685 call (a), F-S10's three choices).
6. **Observed, not acted on**: `docs/QUICK_START.md`'s sample `pip list` shows `juniper-cascor 0.11.x`, below `[servers]`' `>=0.12.0`. It is a dated 0.10.0 sample; a refresh is the owner's call.

## Rules that held this session

- **Never the system temp dir.** The Write and Edit tools refuse the primary's `tmp/`, so use this worktree's `tmp/` (scratch in `tmp/s1/`; keep it until the plan PR lands). Bash may write the primary's `tmp/`, and the simulator's `--sim-dir` must lie there, outside the repo root.
- **The isolation guard refuses** compound commands with `.github` paths, jq `//` or loops. Put them in a script file.
- `~/.local/bin/yamllint` is a broken shim (deleted python3.13). Use the pre-commit cache's yamllint 1.35.1.
- **`safe_merge.py`: read the `MERGED` line**, not the exit status.
- **Paul approves every `pypi` gate.** Hand over the run URL and stop.

## Verification commands for the new thread

```bash
cd ~/Development/python/Juniper/juniper-ml
gh pr list --repo pcalnon/juniper-ml --search "v1.15.13" --state all
gh api repos/pcalnon/juniper-ml/actions/runs/42230617125/pending_deployments --jq '.[].environment.name'   # "pypi" until approved
curl -s https://pypi.org/pypi/juniper-ml/0.11.4/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'])"   # 404 until approved
gh pr view 2497 --repo pcalnon/juniper-ml --json state,mergedAt
grep -n "juniper-recurrence>=" pyproject.toml   # >=0.8.1
```

## Git state

- Branch `worktree-moonlit-noodling-papert` at `957f0e94` plus this session's three files, which land through the PR carrying this handoff as one signed API commit.
- `tmp/s1/` (ignored) holds the bodies, logs and the extracted recurrence tree.

## Documents created or modified by this PR

- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.12 → v1.15.13)
- `util/ad-hoc/2026-11-06_consolidated_plan_v1_15_13_floor_0_11_4_o13_narrowed.py` (new)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_recurrence-equities-0-11-4-at-pypi-gate-plan-v1-15-13.md` (this file)
- Outside the repo: memory `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description)
