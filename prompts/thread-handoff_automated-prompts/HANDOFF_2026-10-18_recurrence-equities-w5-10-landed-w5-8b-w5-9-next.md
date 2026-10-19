# Thread Handoff — Recurrence × Equities: W5.10 landed (the train / crossval responses carry the resolved readout hyperparameters); W5.8 (B) + W5.9 are next

- **Date**: 2026-10-18
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/proud-mixing-jellyfish`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-floor-0-6-1-landed-compose-pin-ruling-and-p5-next.md` (juniper-ml#2244; its step 1 updated by the concurrent juniper-ml#2246, which recorded the Compose pin following to 0.6.1 as plan **v1.7.3**)
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, **v1.7.4** (lands with this handoff; this session's revision was drafted as 1.7.3 and renumbered when #2246 landed first)

---

## Handoff goal

Continue the arc from plan v1.7.4. **Every M1 landing is on `main`** (the Compose pin followed to 0.6.1 in juniper-deploy#251, `b645acfd`, recorded by #2246) and **P5 has started: W5.10 is on juniper-recurrence `main`** (juniper-recurrence#208, `ac329d57`), in `[Unreleased]`. The next development thread is **W5.8 (B) + W5.9** for recurrence 0.7.0 / model 0.5.0, which W5.10 unblocked; W5.2, W5.4 and W5.7 alongside per the plan. The W0.1 service-core half and the parent `Juniper/AGENTS.md` paragraph are still open from the predecessor; the W1.12 / W1.11 smokes on the 0.6.1 image are owed from #2246's landing on a host whose Docker reaches GHCR.

## Completed this session

- **W5.10 landed**: juniper-recurrence#208, two GitHub-signed commits (`c04271dd` the feature, `e185d133` a log-line fix), squash-merged as `ac329d57`. The owner's 2026-10-18 acceptance, first in the P5 order of work; the plan allows it in a 0.6.x ahead of W5.8.
  - `juniper_recurrence/schemas.py`: `ReadoutDiagnostics` (`readout`, `theta`, `ridge_mode`, `ridge_selected`, `gamma`, `gcv_at_edge`, `null_model`), a **required** `diagnostics` field on `TrainResponse` and on each `CrossValFoldModel`. On both flags `null` means *not determined*, never *false*.
  - `juniper_recurrence/_readout.py`: `readout_diagnostics(model)`, the one place a fitted model's resolved values are read (`model.theta`; the live readout's `ridge` / `gamma`; the requested mode from the immutable spec, `model._readout_spec.ridge`). `gcv_at_edge` is derived from the selected λ against `juniper_recurrence_model.readouts._GCV_GRID`'s floor / ceiling (`None` if the model hides the grid). `null_model` is read from the fitted readout's `null_model_` attribute, else `None`; a readout's own `gcv_at_edge_` wins over the derivation. **That is the W5.9 contract**: model 0.5.0 sets `gcv_at_edge_` / `null_model_` on the fitted readout (the trailing-underscore fit-diagnostic convention the MLP rung uses for `n_epochs_` / `stopped_reason_`), and the service picks them up with no further change.
  - `routers/crossval.py`: the per-fold factory keeps each fold's model (`fold_models[fold_index]`; the executor's `FoldResult` carries metrics only) and the block is read off each after the run; `_to_response` zips folds and blocks `strict=True`. `routers/training.py`: the block on the response. `state.py`: `set_crossval(result, dataset, diagnostics)` and a 4-tuple `crossval_status()`, so `GET /v1/crossval/status` re-serves the blocks. `main.py`: the `train` CLI prints the block under `Readout:`. README and CHANGELOG `[Unreleased]` / Added. The model package is unchanged; no number changes; additive on the wire.
  - Tests: `juniper-recurrence/tests/test_readout_diagnostics.py` (21 tests, 23 cases); `pyproject.toml` gained the N806 per-file ignore for it. Suite on turing: **339 passed, coverage 98.29 %** (gate 90 %); `ruff check .`, `ruff format --check` and the ASYNC audit clean.
  - **CodeQL on the PR**: two `py/log-injection` threads (alerts 52 / 53) on the two new log lines, because each carried `descriptor["dataset_id"]`. `main` already holds 17 open alerts of that class on the pre-existing lines (#1–#17, all dated 2026-08-14), so the precedent would have been to resolve; instead `e185d133` moved the request value out of the new entries (the `complete` line beside each already names the dataset) and the threads were replied to and resolved by GraphQL. `util/safe_merge.py` refused once on the unresolved threads (`required checks are green but GitHub will not merge`), then merged the new head.
- **Plan v1.7.4** (this PR): Status line, W5.10 row (both cells), W5.9 row (the attribute contract), P5 status row, the W5.8 (B) dependency row, a new "Progress 2026-10-18, turing W5.10 session" block, change-log row. Applied by `util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py --merge-sha ac329d57` (new; `--check` reports state; anchored on #2246's v1.7.3 text).
- **Memory** `turing-recurrence-test-venv` (new): the recipe for running the recurrence suite on turing (a scratch venv over `JuniperPython` with the six local juniper trees editable; `--system-site-packages` supplies fastapi / numpy / pydantic / pytest / torch).

## Remaining work (in order)

1. **W5.8 (B) + W5.9** (recurrence 0.7.0 / model 0.5.0; plan W5.8 Details for the measured numbers and the order): W5.9 in the model — in `_gcv_select`, detect λ at the ceiling and the null-model optimum beyond it (GCV of the intercept-only fit, `n·‖yc‖² / (n − 1)²`, below the best grid value), WARNING, and set `gcv_at_edge_` / `null_model_` on the fitted `LinearReadout` / `RFFReadout` — **the attribute names W5.10 reads**; then W5.8 (B): `Settings.default_ridge: "gcv"` plus train-fold-only standardisation inside `LinearReadout` only when `ridge != 0.0` (the `ridge = 0` conformance path byte-identical), `conf/experiments/irregular-sine-rff.yaml:20` in the same PR, CHANGELOG "Changed" with the measured numbers (−247 / −192 / −0.195). Route test: a bare `/v1/crossval` on the E-H artifact aggregates above −1 **and** reports the selected λ (W5.10's block carries it).
2. **W5.2** (grouped chronological CV through model-core `order=` / `groups=`), **W5.4** (the acceptance facility in juniper-ml, then the R5 band after W5.2's re-measurement; round 3 of the CV-blowup note's review first), **W5.7** (juniper-data, with the F-P8 guard). P2–P4 alongside.
3. **A recurrence 0.6.x cut** carrying W5.10 if W5.8 (B) + W5.9 are not close: proposal PR (version, CHANGELOG, AGENTS.md rows) → ceremony → the owner's `pypi` gate, as for 0.6.1. The juniper-ml `[recurrence]` floor does not need to move for it.
4. **The W1.12 snapshot and W1.11 canopy smokes on the 0.6.1 image** (owed from juniper-deploy#251 per #2246; a host whose Docker reaches GHCR, not turing; the image differs from 0.6.0's in package metadata only).
5. **Owner: the W0.1 service-core half** and **the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph** (both as in the predecessor handoff).
6. **Owner: restore and refresh the juniper-recurrence checkout.** This session restored `/Users/pcalnon/Development/python/Juniper/juniper-recurrence` to its pristine `main` (`cad03ed5`) files after the merge, so a plain pull brings W5.10 in:

   ```bash
   ! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only
   ```

7. **Follow-ups still open**: the juniper-recurrence-client docstrings (`client.py:414`, `:522`) list the response fields without `diagnostics` — a client-package doc touch with its own CHANGELOG line; juniper-canopy#735–#738 and #751; juniper-ml#2210, #2211; juniper-deploy#250; the GraphQL body-cap measurement for `ARCHIVE_B64_MAX_DEFAULT`; `docs/REFERENCE.md:177`'s pins sentence; `docs/QUICK_START.md`'s sample `pip list`.

## Key context (traps, all still in force)

- **No signing on turing**: `util/open_signed_pr.py` (branch + signed commit + PR), `util/push_signed_commit.py --expected-head <full sha>` for a follow-up commit on the branch (both take `--commit-body-file`, where the attribution trailer goes), `util/safe_merge.py --pr N --repo <repo> --execute` to merge (run with `run_in_background`; it refuses on unresolved review threads, which resolve via GraphQL `resolveReviewThread` — reply first with the reason). The link was idle this session; every commit landed first try.
- **CodeQL review threads block the merge helper**, not GitHub's rollup. For a `py/log-injection` on a new log line, prefer removing the request value from the line over resolving; `main`'s pre-existing alerts of that class are the precedent either way.
- **Running the recurrence suite on turing**: memory `turing-recurrence-test-venv`. CI runs `ruff check .` over the whole package dir including `tests/`, and the per-file N806 ignores in `pyproject.toml` must name any new test module that uses `X`.
- **Sibling-repo edits**: edit in the checkout, test, land by API, then restore the files from pristine copies (kept in the scratchpad) so the owner's pull is clean. The worktree guard refuses `git -C` on siblings, the heredoc + `chmod` + `nohup` compound, and `sed … $VAR` (memory `worktree-guard-refusals`); write scripts with the Write tool and run `nohup /bin/bash <script> > <log> 2>&1` alone.
- **Concurrent sessions edit the plan.** Fetch `origin/main`, fast-forward, re-run the edit script (`--check` first); branch from current `main`. This session's revision was drafted as 1.7.3 while juniper-ml#2246 claimed 1.7.3 for the Compose pin; the fast-forward refused with the local plan edit in place, so: restore the plan from HEAD, fast-forward, renumber the script's version strings and re-anchor its Status-line and change-log edits on the newer text, re-apply. Check `gh pr list --repo pcalnon/juniper-ml` for an open `docs(recurrence): plan vX` PR before writing a revision.
- **Merge approvals do not carry over.** This session's covered juniper-recurrence#208 and the plan v1.7.4 / handoff PR.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -3 origin/main                                              # the v1.7.4 PR on top of 8d027bbf (#2246)
grep -n 'Version\*\*: 1.7.4' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
python3 util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py --merge-sha ac329d57 --check   # applied 8, pending 0, change-log row present
gh pr view 208 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '{state,sha:.mergeCommit.oid}'   # MERGED ac329d57
gh api repos/pcalnon/juniper-recurrence/contents/juniper-recurrence/juniper_recurrence/schemas.py --jq .content | base64 -d | grep -c 'class ReadoutDiagnostics'   # 1
gh api "repos/pcalnon/juniper-recurrence/code-scanning/alerts?state=open&ref=refs/heads/main&per_page=100" --jq '[.[] | select(.rule.id=="py/log-injection")] | length'   # 17, all created 2026-08-14 -- none from #208
```

## Git status at handoff

- **juniper-ml worktree** `proud-mixing-jellyfish`: branch `worktree-proud-mixing-jellyfish`, at `8d027bbf` = `origin/main` (juniper-ml#2246). Local modifications are exactly the plan (v1.7.4), `util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py` and this handoff, pushed as a signed commit through the API; nothing is committed locally.
- **juniper-recurrence checkout** `/Users/pcalnon/Development/python/Juniper/juniper-recurrence`: on `main` at `cad03ed5`, files restored to pristine after the merge (step 6 pulls W5.10 in).
- **Open PRs on juniper-ml** at handoff: #2247 (turing B7, unrelated).
- **Scratch** (session-specific, gone with the sandbox): the venv, the W5.10 edit script `apply_w510.py`, the pristine and edited copies, the two PR bodies.

## Documents created or modified this session

- **juniper-recurrence** (juniper-recurrence#208, merged): `juniper-recurrence/juniper_recurrence/schemas.py`, `_readout.py`, `state.py`, `main.py`, `routers/crossval.py`, `routers/training.py`; `juniper-recurrence/tests/test_readout_diagnostics.py` (new); `juniper-recurrence/pyproject.toml`, `README.md`, `CHANGELOG.md`.
- **juniper-ml**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.4); `util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py` (new); this file.
- **Referenced**: the predecessor handoff above; `util/open_signed_pr.py`; `util/push_signed_commit.py`; `util/safe_merge.py`; `util/ad-hoc/2026-10-19_plan_v1_7_3_compose_pin_followed.py` (juniper-ml#2246, the revision this follows) and `util/ad-hoc/2026-10-18_plan_v1_7_2_recurrence_floor_landed.py` (the pattern); `juniper-recurrence-model/juniper_recurrence_model/readouts.py` (`_GCV_GRID`, `_gcv_select`, the W5.9 site).
