# Thread Handoff — Recurrence × Equities: P0 executed, P5 verdict GO, P1 is next

- **Date**: 2026-10-04
- **Session**: "equities recurrence" (juniper-ml worktree `rosy-coalescing-pelican`)
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.3.0)
- **Consensus record of the plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`
- **Measurement note (W5.1 §1–§2)**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`

---

## Handoff goal

Continue the recurrence × equities development path from the plan `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.3.0). Phase 0 is executed except for two items named below; the P5 go/no-go is **GO**; Phase 1 starts next, in the dependency order the plan's "What's Next" gives.

### Completed so far (all merged unless stated)

- **W0.8 + W0.9 measured, verdict GO** — `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` (juniper-ml#2130). The E-H configuration (RFF, ridge 1.0, 256 features, median gamma) on the frozen artifact `equities_seq-6.0.0-15505731cba5b86d` gives eval r² −0.115 (per fold −0.08 … −0.26); the service defaults (linear, ridge 0.0) give −20,345 on the same artifact.
  Cause: candidate (a) — an unregularised min-norm solve on a design of numerical rank 113–161 of 242 with condition number 1e22–1e32. Theta (c) refuted (91.0 every fold); normalisation (b) refuted as the lever (makes ridge-0 worse, −4.3e12); per-fold standardisation (d) not implicated.
  Evidence: `reports/2026-10-04_recurrence-equities-cv-matrix/`; instruments: `util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py`, `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py`.
- **W0.1 model half** — `juniper-recurrence-model` 0.3.0 installed editable (from the primary checkout, `--no-deps`) into `JuniperCascor1`; `derive_full_split` imports; bench 37/37 as served; `/v1/crossval` 200 without `PYTHONPATH`. Recipe recorded in `juniper-recurrence/AGENTS.md` (juniper-recurrence#189). **Service-core half deferred** (see Key context).
- **W0.6 + W0.7 service half** — juniper-recurrence#190: CLI `train --params/--params-file`, `TrainResponse.metrics_scope: "in_sample"`.
- **W0.5 + W0.7 canopy half** — juniper-canopy#702: 4xx `detail` reaches the log, `completion_reason` and the status bar (tooltip when the 120-char label cuts it); panel titled "in-sample (train split)". 5xx details deliberately NOT shown (F-S10).
- **W0.3 + W0.4** — juniper-ml#2145 (re-land of #2131 after a CHANGELOG conflict with #2134): manifest `phases` record, `outcome: degraded` derived from it, non-zero exit (the plan's recommended R6 applied pending the owner's ruling), `degraded` in `TERMINAL_OUTCOMES`, `_headline_metrics` reads `final_metrics.r2` / `crossval.eval_aggregate.r2` / `eval_std.r2` / `n_windows`.
- **Scenario-A re-run** on main `3420a1a5` + repaired env: the equities cell is `succeeded`, all four phases `ok`, `cv_r2 −0.1153`, `train_r2 0.1163`, exit 0; `REPORT.md` says `2 succeeded, 0 degraded`. Evidence under `reports/2026-10-04_recurrence-equities-cv-matrix/scenario-a-rerun/` (this handoff's PR).
- **W0.2** — juniper-ml#2139, merged at `d31b7c21` (`util/recurrence_env_preflight.bash`, both launchers, `--skip-env-preflight` / `JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1`). From now on the launcher refuses `JuniperCascor1` on the service-core line until W0.1's second half lands.
- Plan v1.3.0: F-SCI1 resolved; F-P8 (meta `checksum` is container-level) and F-S10 (5xx relays a padded API key) added; W5.8, W5.9, W1.14 proposed; W1.1 bundle fixed to `normalize_features: false` plus the model half; status table and M0 live.

### Remaining work (in order)

1. **P0 is closed except W0.1's service-core half.** All five P0 code PRs are merged (juniper-recurrence#189, #190; juniper-canopy#702; juniper-ml#2145, #2139) and the agents' worktrees and local branches are removed. Start by confirming `main` carries them (commands below); there is no P0 PR to wait on.
   Then update the plan's W0.2 status row to Done and remove the preflight agent's worktree (`/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--feat--p0-recurrence-env-preflight--20261004-1601--cf711cf4`, branch `feat/p0-recurrence-env-preflight`).
2. **Owner items, in the plan's order**: milestone dates (M0 2026-10-24 … M4 2027-01-15); R6 (W0.3 applied the recommendation — confirm or re-rule); R2, R3, R7, R8 before W1.4 / W1.8 / W1.2 / W1.3; R1 optional; acceptance of proposed W5.8 (`default_ridge 0.0` → `gcv`, or linear-rung standardisation), W5.9 (GCV grid tops out at 1000, selected in 15 of 20 folds), W1.14 (F-S10).
   **W0.1 service-core half**: `JuniperCascor1` still serves `juniper-service-core` 0.5.0 (module 0.4.0) under the app's `>=0.6.0,<0.8.0` pin; the recipe in `juniper-recurrence/AGENTS.md` names the command; a live cascor on `:8202` (canopy E2E stack, up since 2026-09-22) imports from that env, so the owner decides when.
3. **Consensus review of the W5.1 note** (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`) under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` before R5 is ruled. The note recommends the E-H band `cv_r2 ∈ [−1.0, +0.5]`, `mode: gate`, and a `report`-mode `train_r2 ≤ 0.9` overfit flag.
4. **Phase 1**, dependency order per the plan: juniper-data-client (W1.4 validator gaps, R2) → juniper-recurrence-model (W1.3 target selection, R8; W1.4 mirror) → juniper-recurrence (W1.5 service half: `operation_id`, terminal `failed`, `expect_operation_id`, `juniper_data_timeout_seconds`) → juniper-canopy (W1.2 schema-filtered params + preview, R7; W1.5 canopy half; W1.6; W1.7) → juniper-ml (W1.5 driver half; W1.9 recorded CLI path + rerun parity; W1.10 snapshots/log env).
   In parallel: juniper-data (W1.1a docs — now mergeable; W1.8, R3; W1.11 release 0.17.0 + floors) and juniper-deploy (W1.11 pins + smoke; W1.12 snapshot mount). W1.13 publications last. One PR per repo per item is fine; the task-executor agents did P0 well with the briefs' mechanics (worktree, no `git commit`, `open_signed_pr.py`, `wait_for_checks.py`).
5. Update the plan's status table and M0/M1 rows as items land; keep every change in the change log (next version 1.4.0).

### Key context

- **Headless mechanics that held**: `git commit` hangs (YubiKey) — every commit went through `util/open_signed_pr.py` (new branch) or `util/push_signed_commit.py`; merges through `util/safe_merge.py --execute` (read its `MERGED`/`REFUSED` line, not the exit code); `gh api -X PUT …/update-branch` for a BEHIND PR.
  When main inserts into `CHANGELOG.md` at the same point after an update-branch, re-land from current main with `git merge-file` + a theirs-then-ours resolver (ml#2131 → #2145; memory `reference_changelog_conflict_signed_update_branch.md`).
- **Running the E-H suite from a `.claude/worktrees/` checkout** needs `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` (the suite's `base_config` walks to a sibling repo) and the env's `bin` on `PATH` (the `save_model` CLI re-run, F-D4). Once #2139 is merged, the launcher **refuses `JuniperCascor1`** on the service-core line until the W0.1 service-core half lands; pass `JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1` to run anyway (loud WARNING in `logs/launch.log`).
- **Do not quote the audited digits as reproducible**: −18,081 (2026-10-03) and −20,345 (2026-10-04) are the same ill-posed measurement on byte-identical arrays. The dataset id did pin the content; the meta `checksum` differs between mints because it hashes the NPZ container (F-P8).
- **"Sane" is not "skill"**: cv_r² ≈ −0.1 on next-day log returns is the efficient-market ceiling. The sane configuration is the E-H one; the bundle W1.1(a) documents must carry the model half (`readout: rff`, `ridge: 1.0`, `rff_features: 256`, `rff_gamma: median`) — the dataset half alone does not decide the outcome.
- **Approvals do not carry over.** The merge approval for this arc's PRs was granted in this session only; the successor needs its own.
- **Rejected approaches**: pushing a resolved CHANGELOG onto a conflicting PR branch (two different insertions at one point still conflict — measured before); re-running the matrix through the HTTP route only (it cannot return theta, gamma, ridge or memory-state ranges, so the matrix runs in-process through the service's own `build_lmu_regressor` + `LMURegressor.fit`, and its fidelity to the route was checked to every printed digit).

## Verification commands for the successor

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or a fresh worktree of main
git log --oneline -6                                       # expect #2145, #2134, #2130 … and #2139 once merged
gh pr view 2139 --repo pcalnon/juniper-ml --json state,mergedAt,mergeStateStatus
gh pr list --repo pcalnon/juniper-ml --state open --search "p0"   # expect nothing from this arc
/opt/miniforge3/envs/JuniperCascor1/bin/python -s -m pip check | grep -i juniper   # expect exactly the service-core line until W0.1's second half
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python   # expect exit 1 (service-core) until then
python3 -m unittest -q tests/test_run_suite.py tests/test_run_experiment.py tests/test_recurrence_env_preflight.py
```

## Git status at handoff

- juniper-ml: worktree `rosy-coalescing-pelican` on `main` at `3420a1a5` plus this handoff's uncommitted doc changes (the plan's status rows, F-S10/W1.14, the note's §1.4, `reports/…/scenario-a-rerun/`, this file), which go out as one docs PR from this session. Nothing staged; nothing else uncommitted.
- juniper-recurrence `main` with #189 and #190 merged; juniper-canopy `main` with #702 merged; juniper-ml `main` at `d31b7c21` (#2139) with #2130, #2145 below it. All four agent worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/` and their local branches are removed; `git worktree prune` run in each repo.
- Experiment stack `20261004T210331Z-491a` torn down; the suite run `e-h-recurrence-real-data-20261004T221425Z` tore its own stacks down.

## Validation results worth carrying

| Check | Result |
| --- | --- |
| E-H replay (HTTP) | eval r² agg −0.1153, std 0.0735; RMSE 0.0186 |
| Service defaults (HTTP, same artifact) | −20,345 (fold 0 −93,606) |
| In-process matrix fidelity | identical to HTTP on both cells |
| Theta per fold, all 24 cells | 91.0 |
| Linear design rank / cond (raw) | 113–161 of 242 / 1e22–1e32 |
| Bench as served | 37 passed |
| Suite re-run | 2 succeeded, 0 degraded; `cv_r2 −0.1153` recorded |
