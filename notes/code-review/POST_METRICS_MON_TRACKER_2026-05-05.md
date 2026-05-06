# Post-METRICS-MON Carry-Forward Tracker

<!-- markdownlint-disable MD013 -->

**Project:** Juniper ML (cross-repo)
**File Name:** `notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md`
**Description:** Single-source tracker for items that survived the close of the METRICS-MON program (juniper-ml#192) and the subsequent 27-finding observability audit (juniper-ml#195). Captures the soak-window calibration work, alertmanager production wire-up, log-only-severity gate-lift gating, deferred bucket re-evaluation, the snap-confined `amtool` validation gap, the deferred TRAIN-ARCH-01 mini-batch design, and any items found while drafting this tracker. The intent is that the next agent or human picking this up has one document to start from.
**Author:** Paul Calnon
**Version:** 0.1.0
**License:** MIT
**Date:** 2026-05-05
**Status:** ACTIVE — items remain open. This document is updated in-place as items close, then retired to `notes/legacy/` once §5 (closure log) is full and §2 has zero open rows.

**Source documents (must read first when picking this up):**

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) §6 (residual follow-ups)
- [`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md`](OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md) §5 (consolidated action items)
- [`../observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md`](../observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md) §4 (3.2 state)
- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 (cross-repo)
- juniper-deploy `notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §4 (rotation), §7 (limitations) (cross-repo)
- juniper-cascor `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5.4 (D.2 acceptance) (cross-repo)

---

## 1. Purpose

The METRICS-MON program closed on 2026-05-03 (juniper-ml#192) after shipping 78 PRs across 8 repos in 9 calendar days. The post-close audit (juniper-ml#195) captured 27 follow-up findings; six of those plus other audit-driven items have since been closed (most notably OBS-WIRE-01 in cascor, OBS-ROUTE-01 in juniper-deploy#60, and the final E.6 cap in juniper-cascor#221). What remains is a small set of carry-forward items that share three properties:

1. They are time-bound to the 30-day soak window (`2026-05-03 → 2026-06-02`) or to a downstream calibration follow-up.
2. They have explicit gating relationships with each other — for example, lifting the R5.4 log-only-severity gate requires both target calibration (item §3.1) **and** real alertmanager credentials (item §3.3).
3. They are easy to lose track of because the program close note lives alongside dozens of other phase entry-plan and design documents and is not consulted weekly.

This tracker exists so that the next agent or human acting on the soak-close can find every open item in one place, with concrete next actions, verification commands, and trigger dates. **Do not** treat this document as the source of truth for the program itself — it is a scoreboard for items derived from §6 of the program-close note and §5 of the audit doc, and it points back to those documents for context.

When an item closes, log it in §5 with the closing PR + date and remove the row from §2; sub-section §3.* can be left in place (with a status flip) for posterity, or pruned in a doc-cleanup PR if it muddies the scoreboard.

---

## 2. Top-priority items

| ID | Title | Severity | Owner repo | Target / trigger | Blocker for | Status | Action checklist |
|----|-------|:--------:|------------|------------------|-------------|:------:|------------------|
| **CALIB-01** | T+30d SLO target calibration | P3 | juniper-deploy | 2026-06-02 (window close) → 2026-06-15 (catalog revisit deadline) | LIFT-01 (gate lift) | open | Pull p50/p95/p99 over the 30-day window; ratify or open a calibration PR adjusting `SLO_CATALOG_2026-05-03.md` §3 targets and the burn-rate factors in `prometheus/alert_rules.yml`. |
| **R5.1c-BUCKETS** | Cascor sub-ms bucket re-evaluation | P2 | juniper-cascor | After CALIB-01 ratifies | LIFT-01 (cleaner SLO 4.4 burn precision) | open | If the calibrated SLO 4.4 target stays in 25–100 ms, ship `_WS_SUB_MS_LATENCY_BUCKETS_V2` with `0.025` and `0.2` boundaries (per `HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5.4). Otherwise re-evaluate. |
| **OBS-ROUTE-CRED** | Alertmanager `tickets` receiver — real-credentials rotation | P1 (soft-blocker) | juniper-deploy | Before LIFT-01 (and ≤ 2026-06-02 for soak-close coverage) | LIFT-01 | open | Run `notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §4.1 against real Gmail / SMTP credentials; rotate every `CHANGE_BEFORE_PRODUCTION_USE` placeholder in `alertmanager.yml` and `.env.secrets.enc`; re-encrypt; force-recreate the alertmanager container; smoke-test with §5.5 of the runbook. |
| **LIFT-01** | R5.4 alert log-only-severity gate lift | P1 | juniper-deploy | Gated on CALIB-01 + OBS-ROUTE-CRED | (terminal) | blocked | Edit `prometheus/alert_rules.yml` to flip the burn-rate alert annotations from log-only commentary to live paging severities for §3.1 / §3.2 / §3.5; §3.3 / §3.4 wait on Q1 + Q2 from the catalog. Update `SLO_CATALOG_2026-05-03.md` §2.6 caveat status. |
| **AMTOOL-CI** | `amtool check-config` snap-confinement gap | P3 | juniper-deploy | No hard date | LIFT-01 quality (not blocker) | open | Add a CI job (or extend an existing one) running `docker run --rm -v "$(pwd)/alertmanager:/cfg:ro" --entrypoint amtool prom/alertmanager:v0.27.0 check-config /cfg/alertmanager.yml`. Reference: runbook §5.3 + §7. |
| **TRAIN-ARCH-01** | Cascor mini-batch restoration | P3 (user-discretion) | juniper-cascor | No date — user gate | (none) | deferred | Do **not** pre-empt. Design doc `juniper-cascor` PR #194 (merged 2026-05-03 as design-only). Surface as input at next observability planning meeting; if research-side ratifies, schedule as a future TRAIN-ARCH or METRICS-MON-N sub-track. |
| **R5.6-THROTTLE** | Cascor 25-epoch emit throttle removal | P3 | juniper-cascor | No date — coupled to Q4 of TRAIN-ARCH-01 | TRAIN-ARCH-01 (sequencing) | deferred | Single-line gate change in `cascade_correlation.py:1655` (the `epoch % 25 == 0 or epoch == epochs - 1` guard) + adjust the histogram-count assertions in test code. Useful as a separate small PR once per-step granularity is in scope. |
| **R1.3.4-FLAG** | Helm chart `worker.healthcheck.enabled` default flip | P3 | juniper-deploy | After staging confirms worker image ≥ 0.4.0 stable in production-shaped traffic | (none) | deferred | Bump `worker.healthcheck.enabled` default to `true`, chart `1.1.0 → 1.2.0` per Helm chart version convention; carried forward from R1 phase. |
| **R2-WORKER-DEDUP** | juniper-cascor-worker contract-constant dedup | P3 | juniper-cascor-worker | No date — opportunistic | (none) | deferred | Replace the worker's two duplicated literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) with shared-lib imports under a ≤ 10-line PR. Decline if no maintenance pressure surfaces. |
| **WORKER-PENDING-TASKS** | `juniper_cascor_pending_tasks` worker→Prometheus bridge gap | P3 | juniper-cascor | No date — independent | (none) | open | Wire a `pending_tasks` gauge into `WorkerRegistryCollector` (`juniper-cascor/src/api/workers/metrics.py`); the §4.2 SLI catalog alert is already shipped guarded by `absent_over_time(...) == 0` so it stays inert until the gauge appears. |

**Severity tally**: P1 = 2 · P2 = 1 · P3 = 7 · Total = **10**.

---

## 3. Per-item detail sections

### 3.1 CALIB-01 — T+30d SLO target calibration

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Background.** The R5.1 SLO catalog (juniper-deploy `notes/SLO_CATALOG_2026-05-03.md`) deliberately picked conservative initial targets (e.g. canopy 99.5% availability over 30 d, canopy p95 < 500 ms over 7 d, cascor train-job 99.0%, train-epoch p95 < 5 s, data-service 99.5%) without any production traffic baseline. §2.6 explicitly marks every target *"initial — to revisit after 30-day soak"*. R5.4's burn-rate alerts ship in **log-only severity** for the first 30 days; once a baseline exists, the targets get tightened or relaxed and then the alerts move to paging severity (LIFT-01).

The catalog itself flags 2026-06-15 in §6 Q6 as the revisit deadline. The 30-day soak window opens 2026-05-03 and closes 2026-06-02; the 2026-06-02 → 2026-06-15 buffer is intentional (lets data settle, lets the agent doing the calibration look at a clean 30-day series rather than one ending mid-day).

**Concrete actions.**

1. On or shortly after 2026-06-02, query the canopy / cascor / juniper-data Prometheus instance for the eight catalog SLIs:
   - §3.1 `juniper_canopy_http_requests_total` availability ratio (5xx vs 2xx-3xx)
   - §3.2 `juniper_canopy_http_request_duration_seconds_bucket` p95 (via `histogram_quantile`)
   - §3.3 `juniper_cascor_training_sessions_completed_total{status}` success ratio
   - §3.4 `juniper_cascor_training_step_duration_seconds_bucket` p95
   - §3.5 `juniper_data_dataset_post_total{status}` availability ratio
   - §4.1 `juniper_cascor_worker_heartbeat_age_seconds`
   - §4.4 `juniper_cascor_ws_command_handler_seconds_bucket` p95
   - §4.5 `juniper_canopy_data_client_request_duration_ms_bucket` p95
2. Compute p50/p95/p99 over `[2026-05-03, 2026-06-02]`. Use a `5m` rate window inside the `histogram_quantile` aggregation per the catalog's PromQL.
3. For each SLI, decide: **ratify** the existing target (no PR), **tighten** (current target is already met with headroom), or **relax** (current target is breached even under nominal traffic). Document the decision in a calibration retrospective note alongside the catalog.
4. Open a single juniper-deploy PR updating the §3 target columns + §2.6 caveat status. The same PR also drives the burn-rate-factor edits in `prometheus/alert_rules.yml` (the `(1 - slo_target) * 14.4` style factors).

**Verification — closed when:**

- `notes/SLO_CATALOG_2026-05-03.md` §2.6 caveat is updated (or the doc is renamed to drop the `_2026-05-03` suffix and carry a "ratified" status block).
- A calibration retrospective note exists alongside the catalog with the observed-vs-target tables.
- `LIFT-01` becomes unblocked on the CALIB-01 axis (still gated on OBS-ROUTE-CRED).

**Cross-references.** juniper-deploy PRs #48 / #49 / #50 / #51 (initial catalog + Wave-2 fixups) · catalog §6 Q6 (revisit deadline 2026-06-15) · audit doc §5 P3 row 3.1.

**Trigger / due date.** **2026-06-02** (window close) → **2026-06-15** (catalog revisit deadline). Recommend running a `/schedule` agent for 2026-06-03 as the first nudge.

---

### 3.2 R5.1c-BUCKETS — Cascor sub-ms bucket re-evaluation

**Severity:** P2 · **Owner repo:** juniper-cascor · **Status:** open (depends on CALIB-01)

**Background.** Audit finding D.2 (P2) flagged that the catalog §4.4 SLO target `p95 < 50 ms` for `juniper_cascor_ws_command_handler_seconds` sits one bucket below the `+inf` cap of the current `_WS_SUB_MS_LATENCY_BUCKETS` layout. The cascor `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5.4 audit-acceptance note explicitly defers the bucket-headroom adjustment to **R5.1c (post-soak)** for three reasons: (i) tightening before calibration risks doing the work twice, (ii) `_WS_SUB_MS_LATENCY_BUCKETS` is shared with `broadcast_send_duration_seconds`, so any split has wider blast radius than D.2 alone warrants, (iii) operational impact during soak is bounded because the alerts are log-only.

**Concrete actions.**

1. Wait for CALIB-01 to land. If the calibrated §4.4 target stays in the 25–100 ms band:
2. Open a juniper-cascor PR introducing `_WS_SUB_MS_LATENCY_BUCKETS_V2` in `src/api/observability.py` with `0.025` and `0.2` added boundaries (and the constant rename so the re-bucket is a clearly-tracked event in tests).
3. Update `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5 to reference V2 and the closure of the §5.4 acceptance.
4. Bump cascor R4.1 boundary-pin tests for both `command_handler_seconds` and `broadcast_send_duration_seconds`.

If the calibrated target lands outside 25–100 ms, do not ship V2 blindly — re-evaluate boundary choice with the new target.

**Verification — closed when:**

- `cascor_ws_command_handler_seconds` HELP string drops the `(R4.1 buckets tentative pending R5.1)` suffix.
- `_upper_bounds` boundary-pin tests cover the new boundaries.
- Audit doc §4.4 D.2 row gets a closure annotation.

**Cross-references.** Audit doc §5 P2 row D.2 · cascor `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5.4.

**Trigger / due date.** No fixed date — fires off CALIB-01 ratification, expected mid- to late-June 2026.

---

### 3.3 OBS-ROUTE-CRED — Alertmanager `tickets` receiver real-credentials rotation

**Severity:** P1 (soft-blocker) · **Owner repo:** juniper-deploy · **Status:** open

**Background.** OBS-ROUTE-01 (juniper-deploy#60, merged 2026-05-05) closed audit findings 3.2 (P1) and B.1 (P3) by wiring the alertmanager `default` / `critical` / `tickets` receivers to an SMTP email path. The credentials shipped are **placeholders**: `alertmanager/alertmanager.yml` carries `CHANGE_BEFORE_PRODUCTION_USE` literals for `to:`, `smtp_from`, `smtp_auth_username`; `.env.secrets.enc` (SOPS / age-encrypted) carries placeholder values for `ALERTMANAGER_SMTP_PASSWORD`, `ALERTMANAGER_SMTP_USER`, `SMTP_FROM_DOMAIN`, `TICKET_ALERT_RECIPIENT_EMAIL`, `CRITICAL_ALERT_RECIPIENT_EMAIL`, `DEFAULT_ALERT_RECIPIENT_EMAIL`; `secrets.example/alertmanager_smtp_password.txt` contains the literal string `CHANGE_BEFORE_PRODUCTION_USE`.

The OBS-ROUTE-01 runbook (`juniper-deploy/notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md`) §4.1 documents the rotation procedure in full. §7 of that runbook explicitly lists "Placeholder credentials shipped" as the headline known limitation.

Until rotation happens, every alertmanager email path is non-functional; this is the SOFT-BLOCKER for LIFT-01.

**Concrete actions.**

1. Provision real SMTP credentials. Recommended path is a Gmail account with an app password (matches the SMTP shape that OBS-ROUTE-01 wired); if the user prefers PagerDuty or Slack instead, that is OBS-ROUTE-02 territory and out of scope here.
2. Run runbook §4.1 step 1: `sops -d --input-type dotenv --output-type dotenv .env.secrets.enc > .env.secrets`
3. Edit `.env.secrets`: rotate `ALERTMANAGER_SMTP_USER`, `ALERTMANAGER_SMTP_PASSWORD`, `SMTP_FROM_DOMAIN`, all three recipient emails. Re-encrypt: `bash util/sops-encrypt.sh .env.secrets .env.secrets.enc && rm .env.secrets`.
4. Mirror the password into `secrets/alertmanager_smtp_password.txt` (gitignored) per runbook §4.1 step 4. Set `ALERTMANAGER_SMTP_PASSWORD_FILE=./secrets/alertmanager_smtp_password.txt` in the host environment.
5. Edit `alertmanager/alertmanager.yml` non-secret literals in-place (alertmanager has no env-var interpolation): `global.smtp_smarthost`, `global.smtp_from`, `global.smtp_auth_username`, and the `to:` field on each receiver. Replace every `CHANGE_BEFORE_PRODUCTION_USE`.
6. `docker compose --profile observability up -d --force-recreate alertmanager`
7. Send synthetic alert per runbook §5.5 and confirm an email lands.

**Verification — closed when:**

- `grep -R 'CHANGE_BEFORE_PRODUCTION_USE' alertmanager/ secrets.example/` returns no live references in `alertmanager.yml` (the `secrets.example/alertmanager_smtp_password.txt` file may stay as the example fixture).
- Synthetic alert from runbook §5.5 produces an email in the configured inbox.
- A short rotation-record note (date, who, which receivers) lives alongside the runbook (`notes/ALERTMANAGER_ROTATION_HISTORY.md` or appended to the runbook §4 — author's choice).

**Cross-references.** juniper-deploy#51 (Wave-2 placeholder receivers introduced) · juniper-deploy#60 (OBS-ROUTE-01 wire-up, MERGED 2026-05-05) · juniper-ml#197 (state-analysis Option B that drove the SMTP path).

**Trigger / due date.** **Before LIFT-01.** Recommended completion **≤ 2026-06-02** so that the soak-window ratification has a working notification path.

---

### 3.4 LIFT-01 — R5.4 alert log-only-severity gate lift

**Severity:** P1 · **Owner repo:** juniper-deploy · **Status:** blocked (gated on CALIB-01 + OBS-ROUTE-CRED)

**Background.** Per `SLO_CATALOG_2026-05-03.md` §2.6 ("Provisional-targets caveat"), every R5.4 burn-rate alert ships in *log-only severity* for the first 30 days. The same §2.6 wording is repeated in §3.1, §3.2, §3.4, §3.5 and explicitly notes that paging severity is gated on (a) the soak-window calibration (CALIB-01) and (b) functional alertmanager routing (OBS-ROUTE-01 wired the routing layer; OBS-ROUTE-CRED provisions real notification paths). §3.3 and §3.4 additionally wait on catalog Q1 (cascor train-job completion counter — already shipped via juniper-cascor#188) and Q2 (per-mini-batch instrumentation — TRAIN-ARCH-01, deferred).

**Concrete actions.**

1. After CALIB-01 ratifies (or adjusts) the targets and OBS-ROUTE-CRED proves a working email path, open a juniper-deploy PR.
2. In `prometheus/alert_rules.yml`, audit every alert that currently carries the *log-only* annotation comment per §2.6 and flip the annotation to remove the caveat. The alert `severity:` labels (`page` / `ticket`) stay — those map to the alertmanager receivers OBS-ROUTE-01 wired.
3. Update `SLO_CATALOG_2026-05-03.md` §2.6 to either remove the caveat or flip its status to "lifted on YYYY-MM-DD".
4. §3.3 and §3.4: lift only if Q1 and Q2 have closed (Q1 is closed; Q2 is TRAIN-ARCH-01 which is deferred — therefore §3.4 paging stays gated on TRAIN-ARCH-01 unless the user explicitly accepts per-epoch granularity as final).
5. Verify with `promtool check rules prometheus/alert_rules.yml` and re-run the routing smoke from the OBS-ROUTE-01 runbook §5.3.

**Verification — closed when:**

- §2.6 of the SLO catalog reads "lifted" or its successor wording.
- A synthetic burn-rate alert at `severity: page` fires and produces an email at the configured `critical` recipient.
- A synthetic burn-rate alert at `severity: ticket` fires and produces an email at the `tickets` recipient.

**Cross-references.** Catalog §2.6, §3.1–§3.5 · `prometheus/alert_rules.yml` (lines 686, 1034 carry inline references to the log-only-equivalent severity) · OBS-ROUTE-01 PR juniper-deploy#60.

**Trigger / due date.** Fires when CALIB-01 + OBS-ROUTE-CRED both close. Realistic window: **2026-06-15 — 2026-06-30**.

---

### 3.5 AMTOOL-CI — `amtool check-config` snap-confinement gap

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Background.** Local validation of `alertmanager/alertmanager.yml` is blocked by snap confinement on the dev host: the `amtool` snap can't read files outside `~/snap/amtool/...`. OBS-ROUTE-01 documented the container-form workaround in `ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §5.3 and §7: `docker run --rm -v "$(pwd)/alertmanager:/cfg:ro" --entrypoint amtool prom/alertmanager:v0.27.0 check-config /cfg/alertmanager.yml`. The workaround works locally and in CI; what's missing is a CI job that actually runs it on every PR that touches the alertmanager config.

**Concrete actions.**

1. Add a job to the appropriate juniper-deploy GitHub Actions workflow (likely `.github/workflows/ci.yml` or a new `.github/workflows/observability-validation.yml`) that runs:
   ```bash
   docker run --rm -v "$(pwd)/alertmanager:/cfg:ro" \
     --entrypoint amtool prom/alertmanager:v0.27.0 \
     check-config /cfg/alertmanager.yml
   ```
2. Trigger the job on PRs touching `alertmanager/**` and on `main` push.
3. Optionally extend with `amtool config routes test` smoke for each `severity` value (mirroring runbook §2 smoke output).

**Verification — closed when:** The CI job exists and gates merges that break alertmanager config.

**Cross-references.** Runbook §5.3, §7 · OBS-ROUTE-01 PR juniper-deploy#60 (validation evidence in PR body).

**Trigger / due date.** No hard date. Worth scheduling alongside CALIB-01 since the calibration PR will mutate alertmanager-adjacent thresholds and CI is the cheapest insurance.

---

### 3.6 TRAIN-ARCH-01 — Cascor mini-batch restoration

**Severity:** P3 (user-discretion) · **Owner repo:** juniper-cascor · **Status:** deferred

**Background.** Discovered during R5.4-pre when an agent looking for the missing per-step hook found there was nothing to hook into: cascor is **full-batch end-to-end** (`cascade_correlation.py:1638` and `candidate_unit.py:564` use `for epoch in range(epochs):` with one full-tensor forward + backward + step). Git archaeology proved this is **absence, not regression** — the initial commit `2076d21` was already full-batch, and every legacy variant in `juniper-legacy/` matches.

The design doc `juniper-cascor` PR #194 (`notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md`, merged 2026-05-03) captures two key constraints: (i) cascade-correlation algorithmically requires full-batch for the *candidate phase* — `_calculate_correlation` (`candidate_unit.py:878–950`) computes Pearson via `output.mean()` / `error.mean()` as population statistics, so mini-batching produces biased gradient estimators; (ii) output-trainer mini-batching is *feasible* and proposed under `use_mini_batch: bool = True` / `mini_batch_size: int = 256` knobs restricted to the output trainer.

**The user explicitly paused at the design-doc stage.** This is a user-discretion item; do not pre-empt.

**Concrete actions (when un-deferred).** A 3–4 PR sub-track: constants → config → output trainer + tests → optional convergence-equivalence test. Open questions Q1 (default-flip timing), Q4 (per-epoch vs per-step metrics emit), Q5 (auto-scale `output_epochs` when mini-batch enabled) need user resolution before the entry plan is written.

**Verification — closed when:** The user explicitly closes the design doc OPEN status, or the implementation sub-track ships and is merged.

**Cross-references.** juniper-cascor#194 (design doc, merged as design-only) · juniper-ml#189 (parallel mini-batch instrumentation design doc) · juniper-cascor#188 (R5.4-pre, the work that triggered the discovery) · audit doc §5 P3 row 3.3.

**Trigger / due date.** **None — strict user-discretion item.** Surface as input at the next observability planning meeting.

---

### 3.7 R5.6-THROTTLE — Cascor 25-epoch emit throttle removal

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** deferred

**Background.** `cascade_correlation.py:1655`'s lifecycle callback fires only on `epoch % 25 == 0 or epoch == epochs - 1`, so the R5.4-pre `training_step_duration_seconds` histogram observes per-25-epochs at worst, not per-epoch. This caps R5.4 burn-rate fidelity for SLO 3.4. Coupled to TRAIN-ARCH-01 only loosely — could ship independently if per-epoch granularity is desirable on its own.

**Concrete actions.** Single-line gate change (drop the `epoch % 25 == 0` modulo) + adjust the histogram-count assertions in cascor test code that currently bake in the 25-epoch divisor. Likely ≤ 50-line PR including tests.

**Verification — closed when:** The throttle is gone, tests pass against the new emission cadence, and the SLO 3.4 burn-rate alert's per-epoch fidelity is documented in the catalog.

**Cross-references.** Program-close note §5.1 · catalog §6 Q5 · audit doc §5 P3.

**Trigger / due date.** None — opportunistic. May get pulled in if TRAIN-ARCH-01 unblocks (Q4 of that design doc covers the per-step vs per-epoch metric emit policy).

---

### 3.8 R1.3.4-FLAG — Helm chart `worker.healthcheck.enabled` default flip

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** deferred

**Background.** Carried forward from R1; never closed (deferred for burn-in). The healthcheck implementation shipped in worker image ≥ 0.4.0; the chart still defaults `worker.healthcheck.enabled: false` to avoid breaking older worker images.

**Concrete actions.**

1. Confirm production has been on worker image ≥ 0.4.0 stable for an agreed burn-in window (recommend matching the SLO soak window — i.e. confirm at CALIB-01 time).
2. Edit `k8s/helm/juniper/values.yaml` flipping `worker.healthcheck.enabled` default to `true`.
3. Bump chart `version` from `1.1.0` to `1.2.0` (per the Juniper Helm chart version convention: `Chart.yaml` `version` and `appVersion` must match the app's semver).
4. Update the CHANGELOG and chart README.

**Verification — closed when:** A new chart version is published with the flag default flipped and the worker pod's healthcheck section is present in `helm template` output.

**Cross-references.** Program-close note §6 row R1.3.4 · Helm chart version convention (auto-memory `project_helm_version_convention`).

**Trigger / due date.** Couple to CALIB-01 — by then the soak data confirms worker stability under production-shaped traffic.

---

### 3.9 R2-WORKER-DEDUP — juniper-cascor-worker contract-constant dedup

**Severity:** P3 · **Owner repo:** juniper-cascor-worker · **Status:** deferred

**Background.** Optional follow-up from R2 exit-gate decision: the worker has two duplicated literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) that could be sourced from the shared `juniper-observability` lib. Stable contract values; no observed maintenance burden. Decline if no maintenance pressure surfaces.

**Concrete actions.** ≤ 10-line PR replacing the two literals with shared-lib imports. Update worker tests to import from the shared lib path. No semver bump expected; the literals' values do not change.

**Verification — closed when:** `grep -rn 'LIVENESS_TICK_BUDGET_MS\|READINESS_HEADER' juniper-cascor-worker/src/` shows only one definition site (the import) and the shared-lib source.

**Cross-references.** Program-close note §6 · R2 entry plan + R2 exit-gate decision.

**Trigger / due date.** None — opportunistic. Decline if not under-pressure.

---

### 3.10 WORKER-PENDING-TASKS — `juniper_cascor_pending_tasks` worker→Prometheus bridge gap

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** open

**Background.** `SLO_CATALOG_2026-05-03.md` §4.2 (cascor pending-task queue depth) references `juniper_cascor_pending_tasks` which **does not yet exist**. The §4.2 alert in `prometheus/alert_rules.yml` is shipped guarded by `absent_over_time(...) == 0` so it stays harmlessly inert until the metric appears. R5.4-pre (juniper-cascor#188) shipped `WorkerRegistryCollector` at `juniper-cascor/src/api/workers/metrics.py` exposing worker heartbeat fields as Prometheus gauges; pending-task queue depth is the remaining §4.2 gap.

**Concrete actions.**

1. Extend `WorkerRegistryCollector.collect()` to emit a `juniper_cascor_pending_tasks` gauge (label: `worker_id` or aggregate, per cardinality discipline — see catalog §2.7).
2. Source the value from the worker coordinator's pending-task queue depth.
3. Update unit tests for the collector.
4. Update catalog §6 Q3 status: §4.2 closure removes the `absent_over_time` guard or leaves it as defensive (author's discretion).

**Verification — closed when:** `curl -s http://localhost:8201/metrics | grep juniper_cascor_pending_tasks` returns a non-empty line, and the §4.2 alert evaluates to a non-`absent_over_time`-suppressed truth value under a synthetic queue-depth scenario.

**Cross-references.** Catalog §4.2, §6 Q3 · juniper-cascor#188 (`WorkerRegistryCollector` introduction).

**Trigger / due date.** None — independent small sub-track. Useful at any time; pairs naturally with WS metric wire-ups already shipped via OBS-WIRE-01.

---

## 4. Process notes

### 4.1 How this tracker is updated as items close

When an item closes:

1. Remove its row from §2 (or flip the `Status` column to `closed (PR #N)` if you prefer to keep historical visibility).
2. Add a row to §5 (closure log) with the closing PR URL and date.
3. Optionally prune the §3 sub-section (or flip its status banner). For the first 30 days, **leave the §3 sub-sections in place** so a returning reader sees the full context; after 30 days from item-close, the §3 sub-section can be pruned in a doc-cleanup PR.

### 4.2 When new items are added

This tracker accepts new items in three cases:

- **Audit follow-ups** — if a new audit (e.g. a 2026-Q3 observability re-audit) surfaces findings whose action sits beyond a single PR, add them here with a fresh ID.
- **Soak-window discoveries** — if the 30-day soak surfaces a metric series that's silently broken or a target that's plainly wrong, file it here so the calibration PR (CALIB-01) has somewhere to point.
- **User-explicit deferrals** — if the user explicitly defers a sub-track at the design-doc stage (as TRAIN-ARCH-01 was), capture it here so it doesn't drift out of context.

Do **not** use this tracker for in-flight work; that belongs in entry plans / phase docs / PR descriptions. The tracker is for items that are *between phases*.

### 4.3 When the tracker itself can be retired

Retire when either:

- §2 has zero open rows for ≥ 30 days, **or**
- A successor tracker (e.g. `POST_METRICS_MON_TRACKER_2026-09-01.md` for a 2026-Q3 program close) supersedes it.

Retirement procedure: `git mv notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md notes/legacy/` in a doc-only PR; leave a tombstone link in any document that references this tracker.

---

## 5. Closure log

| Item ID | Closed by PR | Closed on | Verification | Notes |
|---------|--------------|-----------|--------------|-------|
| _(none yet)_ | | | | |

---

## 6. References

### Primary

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) §6 — residual follow-ups (juniper-ml#192)
- [`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md`](OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md) §5 — consolidated action items (juniper-ml#195)
- [`../observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md`](../observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md) §4 — finding 3.2 state and Option B recommendation (juniper-ml#197)

### Cross-repo

- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline
- juniper-deploy `notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §4 (rotation), §5.5 (synthetic alert), §7 (limitations / OBS-ROUTE-02 successor)
- juniper-deploy `prometheus/alert_rules.yml` — burn-rate alert authority; lines around 686 and 1034 carry the log-only-severity inline notes
- juniper-cascor `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §5.4 — D.2 audit acceptance and R5.1c plan
- juniper-cascor `notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md` — TRAIN-ARCH-01 design doc

### Closing PRs that motivated this tracker (reference only)

- juniper-ml#192 — METRICS-MON program close (2026-05-03)
- juniper-ml#195 — Observability audit (2026-05-03)
- juniper-deploy#60 — OBS-ROUTE-01 alertmanager wire-up (MERGED 2026-05-05; placeholder credentials)
- juniper-cascor#221 — Final E.6 audit follow-up: WorkerRegistry size cap + WS handshake rejection plumbing (MERGED 2026-05-05)

---

<!-- markdownlint-enable MD013 -->
