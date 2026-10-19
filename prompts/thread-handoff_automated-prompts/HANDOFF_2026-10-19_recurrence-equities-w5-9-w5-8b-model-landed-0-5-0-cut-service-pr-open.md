# Thread Handoff — Recurrence × Equities: W5.9 and the W5.8 (B) model half landed, model 0.5.0 cut; the service half is open and waits on PyPI

- **Date**: 2026-10-19
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/enumerated-petting-brook`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-w5-10-landed-w5-8b-w5-9-next.md` (juniper-ml#2248)
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, **v1.7.5** (lands with this handoff)

---

## Handoff goal

Continue the arc from plan v1.7.5. **P5's model work is on `main` and released**: W5.9 (the GCV edge / null-model flags) and the W5.8 (B) model half (train-fold standardisation on the linear rung for any non-zero ridge) landed in juniper-recurrence#209, and **juniper-recurrence-model 0.5.0** was proposed (#210) and cut (Release `juniper-recurrence-model-v0.5.0` cut at `99ae4a7b` (archive juniper-ml#2252 on auto-merge); publish run 39188895311 parked at PENDING_PYPI_APPROVAL, https://github.com/pcalnon/juniper-recurrence/actions/runs/39188895311). **The W5.8 (B) service half is open as juniper-recurrence#212** (`default_ridge: "gcv"`, floor `>=0.5.0`); its CI installs the model from PyPI, so it merges once 0.5.0 is on the index, and recurrence 0.7.0 follows. Then W5.2, W5.4 and W5.7 per the plan.

## Completed this session

- **juniper-recurrence#209 merged** as `d6a81eb4` (model package only; `util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py` applied it):
  - `readouts.py`: `_gcv_select` returns a `_GCVSelection` (`coef`, `ridge`, `gcv_best`, `gcv_null`, `at_edge`, `null_model`), evaluating the intercept-only GCV `n·‖yc‖² / (n − 1)²` (the λ → ∞ limit) and logging a WARNING at a grid edge or a null-model optimum; `LinearReadout` / `RFFReadout` expose `gcv_at_edge_` / `null_model_` (the names W5.10's `readout_diagnostics` reads; `None` after a fixed-ridge fit and after `from_state`; not persisted). `LinearReadout` standardises `M` with the train-fold mean / std for `ridge > 0` and `"gcv"`, persists `mean` / `std` beside `coef` with a `standardized` descriptor flag (a pre-0.5.0 state predicts on the raw block), and leaves `ridge = 0.0` byte-identical to 0.4.0. `model.py`'s docstring no longer promises every `ridge=` is pre-DP-3-identical. CHANGELOG Changed + Added; README.
  - Tests: 13 new in `tests/test_readouts.py`, 3 in `tests/test_lmu_model.py`; `test_loads_pre_dp3_format_npz`'s fixture is now a raw-block ridge solve (what a pre-DP-3 file held). Suite 215 passed, coverage 98.30 %; `ruff check` clean (`tests/test_lmu_grid_invariance.py`'s format drift is pre-existing; CI runs `ruff check` only).
- **Model 0.5.0**: proposal juniper-recurrence#210 merged as `99ae4a7b` (`propose.py --execute --cross-repo` on the tree at `d6a81eb4`: `_version.py`, CHANGELOG `[0.5.0] - 2026-10-19`, the AGENTS.md table row). The follow-on ceiling-bump PR #211 it also opened was closed as superseded (the service PR raises the floor). Ceremony `--execute --cross-repo --target-sha 99ae4a7b…` on the tree at that commit: Release `juniper-recurrence-model-v0.5.0` cut at `99ae4a7b` (archive juniper-ml#2252 on auto-merge); publish run 39188895311 parked at PENDING_PYPI_APPROVAL, https://github.com/pcalnon/juniper-recurrence/actions/runs/39188895311.
- **The W5.8 (B) service half opened as juniper-recurrence#212** (`util/ad-hoc/2026-10-19_apply_w5_8b_service.py`): `Settings.default_ridge: "gcv"`; floors `juniper-recurrence-model>=0.5.0,<0.6.0` (base, `[torch]`, `[bench-torch]`) and the image lock `==0.5.0` with a header paragraph; `conf/experiments/irregular-sine-rff.yaml` `service.default_ridge: gcv`; `tests/test_settings.py`; `tests/test_readout_diagnostics.py` (the bare request on both routes reports `ridge_mode: gcv` and its λ; a deployment opting back to `0.0`; the model's flags taken verbatim, so `null_model` is a boolean on GCV fits; the two fallback-derivation tests clear the readout's own flag); README; CHANGELOG Changed. App suite on model 0.5.0: all passed, coverage 98.29 %; ruff clean.
- **Acceptance measured** with `util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py` (new) on the E-H artifact that is on turing at `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/equities_seq-6.0.0-15505731cba5b86d.npz`, through the route's own `build_lmu_regressor` / `readout_diagnostics` per fold: the old default **−2.1e4** (embargo 2; −2.3e4 with the route's default embargo 0); `"gcv"` on model 0.5.0 **−0.195** (−0.190), λ = 1000 at the ceiling and `null_model: true` in every fold — lane B2's −0.195 reproduced. JSON rows in the scratchpad only.
- **Plan v1.7.5** (`util/ad-hoc/2026-10-19_plan_v1_7_5_w5_9_w5_8b_landed.py --service-pr N --release "…"`): Status line, W5.8 and W5.9 rows (both cells), P5 status row, the W5.8 (B) dependency row, a Progress 2026-10-19 block, change-log row.
- **Memory**: `release-train-follow-on-pr` (new); `turing-recurrence-test-venv` gained the scratch-copy overlay recipe (the owner's checkout was never touched this session).

## Remaining work (in order)

1. **Owner: approve the `pypi` gate** on the model 0.5.0 publish run (Release `juniper-recurrence-model-v0.5.0` cut at `99ae4a7b` (archive juniper-ml#2252 on auto-merge); publish run 39188895311 parked at PENDING_PYPI_APPROVAL, https://github.com/pcalnon/juniper-recurrence/actions/runs/39188895311). Then verify the index: `curl -s https://pypi.org/pypi/juniper-recurrence-model/json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["info"]["version"], d["info"]["requires_dist"])'` — `requires_dist` must equal 0.4.0's (the lock header asserts it).
2. **Merge juniper-recurrence#212** once 0.5.0 is on PyPI: re-run its CI if it ran red before the publish (`gh pr checks`; `gh api -X PUT repos/pcalnon/juniper-recurrence/pulls/212/update-branch` or a re-run of the failed workflow), then `python3 util/safe_merge.py --pr 212 --repo juniper-recurrence --execute` (needs its own merge approval).
3. **Cut recurrence 0.7.0**: tarball at the service PR's merge sha into a scratch ecosystem root; `detect.py --json --package juniper-recurrence`; `propose.py --dry-run` then `--execute --cross-repo` (close any `deps/…-ceiling-*` follow-on it opens in juniper-recurrence-client or canopy only if a floor raise supersedes it); merge the proposal; tarball at its merge sha; wait for `ci-recurrence-app.yml` on `main` to be green; `ceremony.py --execute --cross-repo --target-sha <40-char>`; the owner's `pypi` gate. Then the juniper-ml `[recurrence]` floor and the Compose pin are owner rulings again (the extras currently admit `<0.7.0`).
4. **W5.2** (grouped chronological CV), **W5.4** (the acceptance facility; round 3 of the CV-blowup note's review first; then the R5 band), **W5.7** (juniper-data, with the F-P8 guard). P2–P4 alongside.
5. **Owner: the W0.1 service-core half** and **the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph** (add juniper-recurrence-model 0.5.0 once published; otherwise as in the predecessor).
6. **Owner: refresh the juniper-recurrence checkout** (untouched this session, still at `cad03ed5`): `! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`.
7. **Follow-ups still open**: the W1.12 / W1.11 smokes on the 0.6.1 image (a host whose Docker reaches GHCR); the juniper-recurrence-client docstrings (`client.py:414`, `:522`) lacking `diagnostics`; juniper-canopy#735–#738 and #751; juniper-ml#2210, #2211; juniper-deploy#250; the GraphQL body-cap measurement for `ARCHIVE_B64_MAX_DEFAULT`; `docs/REFERENCE.md:177`'s pins sentence; `docs/QUICK_START.md`'s sample `pip list`.

## Key context (traps, all still in force)

- **No signing on turing**: `util/open_signed_pr.py` (branch + signed commit + PR; `--commit-body-file` for the attribution trailer), `util/push_signed_commit.py --expected-head <full sha>` for a follow-up commit, `util/safe_merge.py --pr N --repo <repo> --execute` with `run_in_background` to merge. The link was healthy this session (19 Mbps up / 47 down by `networkQuality -s`); every commit landed first try.
- **Work on a scratch copy, not the owner's checkout**: `rsync -a --exclude .git` the checkout into the scratchpad, overlay the files `gh api repos/pcalnon/juniper-recurrence/compare/<checkout sha>...<main sha>` lists (fetched via `contents/<path>?ref=<sha>`), build the venv per memory `turing-recurrence-test-venv` against the scratch trees. Edit scripts must treat "`new` present once" as applied — an insertion edit keeps its anchor, so "`old` absent" is the wrong test (this session duplicated test blocks once that way).
- **The app's CI installs juniper-recurrence-model from PyPI** (`pip install -e ".[test]"`), so a service change that needs a new model floor cannot merge before the model is published: model PR → proposal → ceremony → gate → service PR.
- **The release train**: `propose.py --execute --cross-repo` also opens a floor-preserving ceiling-bump follow-on in each escaped consumer repo (memory `release-train-follow-on-pr`). The ceremony needs the tree at the target commit under `--ecosystem-root` and HALTs (dry-run shows it only with `--cross-repo --json`) until that commit's `main` CI workflow has completed green — wait with `gh run watch <id>` after the proposal merges.
- **The worktree guard** refuses `sed … $VAR` and `git -C` on siblings; spell paths literally (memory `worktree-guard-refusals`).
- **Concurrent sessions edit the plan**: fetch, fast-forward, re-run the edit script (`--check` first); `gh pr list --repo pcalnon/juniper-ml --search "docs(recurrence): plan"` before numbering.
- **Merge approvals do not carry over.** This session's covered juniper-recurrence#209, #210, the ceremony's archive PR and the plan v1.7.5 / handoff PR. juniper-recurrence#212 needs its own.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
grep -n 'Version\*\*: 1.7.5' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
gh pr view 209 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '{state,sha:.mergeCommit.oid}'   # MERGED d6a81eb4
gh pr view 210 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '{state,sha:.mergeCommit.oid}'   # MERGED 99ae4a7b
gh release view juniper-recurrence-model-v0.5.0 --repo pcalnon/juniper-recurrence --json tagName,targetCommitish   # 99ae4a7b…
curl -s https://pypi.org/pypi/juniper-recurrence-model/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])'   # 0.5.0 once the gate is approved
gh pr view 212 --repo pcalnon/juniper-recurrence --json state,mergeStateStatus
gh api repos/pcalnon/juniper-recurrence/contents/juniper-recurrence-model/juniper_recurrence_model/readouts.py --jq .content | base64 -d | grep -c 'null_model_'   # > 0
```

## Git status at handoff

- **juniper-ml worktree** `enumerated-petting-brook`: branch `worktree-enumerated-petting-brook`, at `origin/main` as fast-forwarded this session. Local modifications are exactly the plan (v1.7.5), the four new `util/ad-hoc/` scripts (`2026-10-19_apply_w5_9_w5_8b_model.py`, `2026-10-19_apply_w5_8b_service.py`, `2026-10-19_w5_8b_eh_acceptance.py`, `2026-10-19_plan_v1_7_5_w5_9_w5_8b_landed.py`) and this handoff, pushed as a signed commit through the API; nothing is committed locally.
- **juniper-recurrence checkout**: untouched, still at `cad03ed5` (step 6 pulls everything in).
- **Scratch** (session-specific, gone with the sandbox): the venv, the scratch copy with both halves applied, the two ecosystem roots, the manifests, the PR bodies, the acceptance JSON.

## Documents created or modified this session

- **juniper-recurrence** (#209, merged): `juniper-recurrence-model/juniper_recurrence_model/readouts.py`, `model.py`; `tests/test_readouts.py`, `tests/test_lmu_model.py`; `CHANGELOG.md`, `README.md`. (#210, merged): `juniper_recurrence_model/_version.py`, `CHANGELOG.md`, the repo `AGENTS.md`. (#212, open): `juniper-recurrence/juniper_recurrence/settings.py`, `pyproject.toml`, `requirements.lock`, `tests/test_settings.py`, `tests/test_readout_diagnostics.py`, `README.md`, `CHANGELOG.md`; `conf/experiments/irregular-sine-rff.yaml`.
- **juniper-ml**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.5); `util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py`, `util/ad-hoc/2026-10-19_apply_w5_8b_service.py`, `util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py`, `util/ad-hoc/2026-10-19_plan_v1_7_5_w5_9_w5_8b_landed.py` (all new); `notes/releases/RELEASE_NOTES_juniper-recurrence-model_v0.5.0.md` (the ceremony's archive PR); this file.
- **Referenced**: the predecessor handoff; `reports/2026-10-05_recurrence-equities-cv-consensus/laneB2.md` Appendix A and `reconciler-rederive.json`; `util/release_train/propose.py`, `ceremony.py`; `juniper-recurrence/juniper_recurrence/_readout.py` (the W5.10 contract).
