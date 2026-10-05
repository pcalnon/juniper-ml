# Thread Handoff — Recurrence × Equities: W5.1 note consensus-reviewed (GO upheld, three rounds), P1 wave 1 merged, wave 2 next

- **Date**: 2026-10-05
- **Session**: "equities recurrence" (juniper-ml worktree `.claude/worktrees/misty-kindling-pascal`, main `a0a120d5`)
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_recurrence-equities-p0-executed-go-verdict-p1-next.md`
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (**v1.4.0** in this handoff's PR)
- **W5.1 note**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` (**v1.1.2**, review complete)
- **Consensus record**: `notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md` (new, complete)

---

## Handoff goal

Continue the recurrence × equities arc from the plan `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.4.0): Phase 1 wave 2 in the plan's dependency order, the two remaining wave-1 merges if they have not landed, then W1.11's code half; the owner rulings the plan now lists are the owner's.

### Completed so far (all merged unless stated)

- **Consensus review of the W5.1 note — complete, three rounds** (procedure `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; record `notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md`; lane reports, reconciler JSONs and Lane A3's fresh-stack evidence under `reports/2026-10-05_recurrence-equities-cv-consensus/`). **GO and the R5 band numbers survived every re-measurement; the note's v1.0.0 explanations did not**:
  - the audited −18,081 was solved on a **second mint of the same `dataset_id`** (Scenario B, checksum `037baab7`, `.amp/in/scratch/data-store/`): yfinance omitted the action columns and `equities/generator.py` zero-filled `dividend` / `split_ratio` silently; re-solving on that file reproduces every audited digit. The checksum IS content-level. **F-P8 re-filed Major**, W5.7 gains an `actions_present` guard.
  - the digits are reproducible (bitwise across processes and a fresh stack); the "rounding at cond 1e32" story is withdrawn.
  - cause of record: the service-default readout applied to a chronologically drifting input, both necessary, `ridge 0` the amplifier; an embargoed in-era control (`reconciler-rederive-b1r2.json` F15) is the in-support evidence; (b) stays withdrawn; `cost_basis` is an exactly-constant raw feature.
  - W5.8's preferred option (`default_ridge → gcv` alone) measures **−247**; only gcv **and** per-fold standardisation pass (−0.195 / −0.019, by abstaining), gated on a response flag (**W5.10**); a default-readout change is **W5.11**. W5.9 becomes at-ceiling / null-model reporting (GCV's optimum is the null model in 3 of 5 RFF folds).
  - R5 recommendation of record: `cv_r2 ∈ [−1.0, +0.5]` **and** `cv_r2_std ≤ 0.5`, both `gate`, row-scoped; the v1.0.0 `train_r2` row withdrawn (could never fire); re-measure on W5.2's train + val pool before W5.4 encodes it (fold 4 of today's full-view CV is the entire `test` partition + 107 `val` rows).
- **Plan v1.4.0**: F-SCI1 statement corrected; F-P8 Major; W5.8 / W5.9 rewritten, W5.10 / W5.11 added; W5.4 band amended; W5.2 → W5.3 / W5.4 and W5.10 → W5.8 edges; W1.1 / W1.3 Details corrected; "Applied pending ruling" paragraph (R2, R3, R8); status table and M0 updated.
- **P1 wave 1**: W1.4 juniper-data-client#222 (float32 enforcement per recommended R2; downstream census clean; the validator is `contract.py:45-135`, the audit's anchor was wrong); W1.3 juniper-recurrence#191 (`target=` API + W1.4 mirror, **default `auto`** — a `reg` default 422s every juniper-data synthetic because they emit `y_*` only; R8's alternative applied pending re-ruling); W1.6 / W1.7 juniper-canopy#722 (version from `GET /openapi.json` — health carries none; documented contract floor, canopy
  never imports the client; **display half still open**, `refresh_model_versions` has no caller); W1.1(a) + W1.8 juniper-data#451 (R3 read as "refuse when `purchase_date` is ≥ 1 weekday after `start_date` under `drop`"; no `generator_version` bump); W1.12 juniper-deploy#242 + juniper-recurrence#193 (mount, preflight, smoke script, tracked `recurrence-snapshots/.gitkeep`; the published 0.5.0 image predates the snapshot routes, so the smoke passes against a `be081fa` build only until W1.13 moves the pin).
  Every squash verified file-by-file; worktrees and local branches removed.
- **Memory**: index compacted to 18 KB via hub files; the wrong "checksum is container-level" memory replaced by `reference_dataset_id_does_not_pin_content_two_mints_differed.md`; the stale-sibling-primary trap recorded in `reference_stale_local_checkout_clobbers_your_own_work.md`; the arc memory `project_recurrence_equities_p0_arc_2026-10-04.md` updated.

### Remaining work (in order)

1. **Two wave-1 merges, if not landed when you start** (verify first — the outgoing session left them on CI): **juniper-recurrence#192** (W1.5 service half: `operation_id` on train / 409 / status, terminal `failed`, `expect_operation_id` on predict and `POST /v1/model/snapshots`, `JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS` default 120, "one caller per service" runbook; the busy 409 `detail` is now an **object**; three signed commits, two carrying `Allow-Symbol-Loss: method:AppState.status` — merge
   with the repo's DEFAULT squash message so the waiver reaches main; after the squash confirm main's `schemas.py` carries `metrics_scope` **and** `operation_id`; worktree `/home/pcalnon/Development/python/Juniper/worktrees/juniper-recurrence--feat--w1-5-operation-id-timeouts--20261005-0828--2c34805c`); **juniper-ml#2164** (W1.9 / W1.10, opened by its agent; read its PR body, merge when green, then confirm `tests/test_ci_test_wiring_drift.py` still passes on main and remove its worktree under
   `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--feat--w1-9-w1-10-*`).
2. **Wave 2** (task-executor agents, one per item, briefed against #192's PR body "API" section): juniper-canopy W1.2 (recommended R7: seed beats generic defaults, explicit edits beat the seed, effective-request preview) + W1.5 canopy half (poll status by `operation_id` after `ReadTimeout`; never `succeeded` blindly; read `RecurrenceStatus.model_present`, not `state == "trained"` — `restored` does not mean a canopy-started fit finished); juniper-ml W1.5 driver half (`dataset_create_timeout_seconds` separate
   from `max_wall_seconds`; `expect_operation_id` on predict; runbook); the W1.7 display half. Cursor draft canopy#704 pins the old 401 wording and must adopt #722's.
3. **W1.11 code half** (floor-bump and pin PRs as drafts; deploy smoke green against a `main` checkout of juniper-data) — the publication half (0.17.0) and **W1.13** are the owner's. Note the published recurrence 0.5.0 image lacks the snapshot routes W1.12 mounts.
4. **Owner items** (not yours to decide; keep the plan's "Applied pending ruling" paragraph current): dates; R1–R8 confirmation (R2, R3 applied as recommended; R8 applied as its alternative); R5 (the note's §3.4); W5.8 (B) vs W5.11; W5.9 / W5.10; F-P8 Major + W5.7 guard; W1.14; release placement of W5.8 / W5.10 (0.6.0 vs 0.7.0); the W0.1 service-core half (`JuniperCascor1` still serves service-core 0.5.0 under the `>=0.6.0,<0.8.0` pin; a live cascor on `:8202` imports from it).
5. Keep the plan's status table and change log current (next version 1.5.0) as wave 2 lands.

### Key context

- **Headless mechanics that held** (same as P0): `git commit` hangs (YubiKey) — `util/open_signed_pr.py` / `util/push_signed_commit.py`; `util/safe_merge.py --execute` (read `MERGED` / `REFUSED`, never the exit code); `gh api -X PUT …/update-branch` for a BEHIND PR; `wait_for_checks.py`. Seven task-executors ran in parallel without collisions by owning disjoint packages; they sign `Co-Authored-By: Claude Opus 5.5` (their model) — accepted.
- **Sibling primaries are stale and must stay untouched** (the canopy E2E stack on `:8101` / `:8051` / `:8202` imports from them): recurrence `be081fae`, canopy `1b2dd438`, versus remotes well past them. **Every agent brief must say: `git -C <sibling> fetch origin` and `worktree add … origin/main`, never bare `main`, and `git diff origin/main -- <file>` before every whole-file upload.** Verify a primary with `gh api repos/pcalnon/<repo>/commits/main --jq .sha` against `git -C <sibling> rev-parse main`.
- **Worktree hook refusals** here: loops, variables around git / gh, `${PIPESTATUS}`, heredoc inside `&&`; plain single commands work; use the Write tool for files.
- **Running the E-H suite from a `.claude/worktrees/` checkout** needs `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, an absolute `--config` path, and `JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1` (the preflight refuses the service-core pin line until W0.1's second half).
- **Approvals do not carry over.** The merge approval for this arc was granted in this session only.
- **Rejected / settled**: a `reg` default for W1.3 (breaks the golden path); W5.8 option (i) alone (−247); extending `_GCV_GRID` (the optimum is the null model); the "rounding" explanation of the between-day digits; a `train_r2` band.

## Verification commands for the successor

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or a fresh worktree of main
git log --oneline -5                                   # expect this handoff's docs PR on top of a0a120d5
gh pr view 192 --repo pcalnon/juniper-recurrence --json state,mergeStateStatus,headRefOid
gh pr view 2164 --repo pcalnon/juniper-ml --json state,mergeStateStatus,headRefOid
gh pr list --repo pcalnon/juniper-canopy --state open --search "w1-2"   # wave 2 not yet started: expect nothing
/opt/miniforge3/envs/JuniperCascor1/bin/python -s -m pip check | grep -i juniper   # still exactly the service-core line
python3 -m unittest -q tests/test_run_suite.py tests/test_run_experiment.py tests/test_recurrence_env_preflight.py
```

## Git status at handoff

- juniper-ml: worktree `misty-kindling-pascal` on `main` at `a0a120d5`; this handoff's docs PR carries every uncommitted file (the three notes, this handoff, five `util/ad-hoc/2026-10-05_*` scripts, `reports/2026-10-05_recurrence-equities-cv-consensus/` minus its git-ignored `*.log` files). Nothing staged; nothing else uncommitted.
- Merged this session: juniper-data-client#222, juniper-deploy#242, juniper-recurrence#193, juniper-data#451, juniper-recurrence#191, juniper-canopy#722. On CI at handoff: juniper-recurrence#192 (safe-merge waiting), juniper-ml#2164 (one check pending).
- Worktrees remaining under `/home/pcalnon/Development/python/Juniper/worktrees/`: the #192 and #2164 ones (remove after their merges).

## Validation results worth carrying

| Check | Result |
| --- | --- |
| Fresh-stack rerun (Lane A3) | both replays, all 24 cells, all 10 conditioning rows **bitwise** identical to 2026-10-04 |
| Audited digits re-solved on the Scenario-B mint | fold 0 −83,451.610, aggregate −18,081.543 — exact |
| RFF seed sweep (rff/1.0, seeds 0–5) | −0.115 … −0.252, std 0.045; seed 0 is the best |
| `cv_r2_std` per seed | 0.071–0.191 (no false-fail at ≤ 0.5); one-outlier cell 8.75 |
| W5.8 options | (i) −247 / −35; (ii) −192; (i)+(ii) −0.195 / −0.019; rff/gcv −0.015; rff/1.0 −0.115 |
| In-era embargoed block (F15) | linear ridge 0 −1.8, ridge 1.0 −2.3, gcv −0.42; rff/1.0 −0.081 (chronological fold 2: −3.70) |
| Unit suites | 368 tests OK at session start |
