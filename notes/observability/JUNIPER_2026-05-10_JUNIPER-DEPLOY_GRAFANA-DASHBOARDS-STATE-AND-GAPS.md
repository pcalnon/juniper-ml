# Grafana Dashboards — State, Gaps, and Remediation Options

- **Author**: Paul Calnon
- **Date**: 2026-05-10
- **Scope**: Full picture of Grafana dashboards (and their wiring) across the Juniper ecosystem, derived from `notes/` references in `juniper-ml`.
- **Source corpus**: 48 markdown files under `juniper-ml/notes/` containing the substring `grafana` (case-insensitive). Most authoritative inputs: `JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md`, `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md`, `code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md`, `observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md`, `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md`, `legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, `JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md`.

> ⚠️ This document is a snapshot of `notes/` claims. It does **not** verify by reading `juniper-deploy/` directly. Treat all named files/paths in `juniper-deploy/` as load-bearing claims to spot-check before acting.

---

## 1. Current State

### 1.1 Provisioned Dashboards

Four Grafana dashboards are claimed to ship in `juniper-deploy/grafana/provisioning/dashboards/`:

| File                    | Purpose                                                 | Recent additions                                                                 |
|-------------------------|---------------------------------------------------------|----------------------------------------------------------------------------------|
| `juniper-overview.json` | Cross-service home dashboard; SLO burn-rate headline    | 4 SLO burn tiles (R5.4)                                                          |
|                         | -- tiles keyed off R5.4 alert expressions.              |                                                                                  |
| `juniper-cascor.json`   | Training service: epochs, loss, accuracy, hidden units, | R4.4 worker training-loop fields (`last_task_duration_seconds`,                  |
|                         | -- candidate correlation, WS health, worker registry.   | -- `recent_task_durations_seconds`, `gpu_utilization_pct`) — `juniper-deploy#46` |
| `juniper-canopy.json`   | Dashboard service: HTTP, render, data-client closure    | R4.3 data-client closure panels                                                  |
|                         | -- metrics.                                             | -- (`juniper_canopy_data_client_requests_total{method,status_class,error_type}`  |
|                         |                                                         | -- + duration histogram) — `juniper-deploy#46`                                   |
| `juniper-data.json`     | Dataset generation service: HTTP, generation latency,   | R4.5 POST cache-hit panel                                                        |
|                         | -- cache size, error rate.                              | -- (`juniper_data_dataset_post_total{cache="hit"\|"miss"}`)                      |

Provisioning mechanism: `dashboard-providers.yml` in the same directory; reload on container restart or SIGHUP.

#### 1.1.1 Dashboard Access

1. Open your web browser and go to [Grafana Local Dashboards](http://localhost:3000/).
    - The default HTTP port that Grafana listens to is 3000 unless you have configured a different port.
2. On the sign-in page, enter admin for both the username and password.
    - Click Sign in.
    - If successful, you’ll see a prompt to change the password.
3. Click OK on the prompt and change your password.

#### 1.1.2 Docker Provisioning Access

The pre-configured Grafana dashboards are already provisioned.
With the deploy stack up, Grafana auto-loads them on container start.

```bash
# Option 1: flag
docker compose --profile observability up -d

# Option 2: env var
COMPOSE_PROFILES=observability docker compose up -d

# Option 3: combine with another profile
docker compose --profile dev --profile observability up -d

# Troubleshooting Startup problems:
docker compose --profile observability logs grafana | grep -iE 'provisioning|dashboard|error'
```

#### 1.1.3 Docker provisioning backend for Grafana

Live access

- Grafana: <http://127.0.0.1:3001> — login admin / `REDACTED`
- Prometheus: <http://127.0.0.1:9090>
- Cascor API: <http://127.0.0.1:8201>
- Data API: <http://127.0.0.1:8100>
- Canopy dashboard: <http://127.0.0.1:8050/dashboard>
- juniper-alertmanager on its default port
- 4 networks created

Two Grafana-volume gotchas surfaced during this validation that are noting:

1. Grafana's admin password file is read once — only on first init when sqlite is empty. Subsequent restarts use the password stored in the grafana-data volume. To rotate, either docker volume rm juniper-deploy_grafana-data (destructive) or docker exec juniper-grafana grafana-cli admin reset-admin-password "$NEW_PW" (non-destructive).
2. git rm --cached on previously-tracked-but-now-gitignored files removes them from working trees on git pull — the local secrets/*.txt files vanished after PR #66 merged. make prepare-secrets recreates the empty placeholders; the populated values must be restored from .env.secrets.enc. Worth flagging in any rotation runbook.

Things you should know:

1. Your existing Grafana for Juniper Project applications running as systemd services is on port :3000.
2. The possibility of a port collision is a real concern.
    - Both Grafanas can't bind :3000.
    - The docker stack owns :3001
    - The systemd service stack owns :3000

### 1.2 Prometheus Scrape Wiring

Configured in `juniper-deploy/prometheus/prometheus.yml`. Globals: `scrape_interval=15s`, `evaluation_interval=15s`, `scrape_timeout=10s`, 30-day retention.

| Job              | Target                        | Interval | Auth                                     |
|------------------|-------------------------------|----------|------------------------------------------|
| `juniper-data`   | `juniper-data:8100/metrics`   | 10s      | IP-allowlist via `MetricsAuthMiddleware` |
| `juniper-cascor` | `juniper-cascor:8200/metrics` | 10s      | None (internal network)                  |
| `juniper-canopy` | `juniper-canopy:8050/metrics` | 15s      | None (internal network)                  |
| `prometheus`     | self at :9090                 | default  | —                                        |

`juniper-cascor-worker` is **not** scraped directly; it is bridged through cascor's `/v1/workers` endpoint via `WorkerRegistryCollector`.

### 1.3 Recording & Alert Rules

- **Recording rules** (`juniper-deploy/prometheus/alert_rules.yml` lines 1–63) precompute request rates, error ratios, p50/p95/p99 latency, and epoch rates so dashboards don't pay raw-histogram cost on every refresh.
- **Alert rules** span 8 base groups (`juniper_service_health`, `juniper_error_rates`, `juniper_latency`, `juniper_training`, `juniper_data_operations`, `juniper_infrastructure`), 5 `juniper_slo_*` groups (multi-window multi-burn-rate per R5.4), and 4 `juniper_threshold_*` groups.
- **SLO catalogue**: single source of truth at `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` — 5 user-facing primary SLIs + 8 internal-supporting SLIs.

### 1.4 Alertmanager

`juniper-deploy/alertmanager/alertmanager.yml` lines 39–65 define 3 receivers:

- `critical` (1h repeat) — wired to existing alert paths (severity `critical|page`).
- `tickets` (12h repeat) — **placeholder, no notification config** (severity `ticket`, used by R5.4 slow-burn alerts).
- `default` (4h repeat) — **placeholder, no notification config** (everything else).

### 1.5 Network Topology

Prometheus joins `backend`, `data`, `frontend`, `monitoring` networks to reach every service. Grafana and Alertmanager are confined to `monitoring`; they read services through Prometheus.

### 1.6 Canopy Dash UI (orthogonal, not Grafana)

Canopy renders a separate **Dash (Plotly)** dashboard at `/dashboard` with 14 tabs (`dashboard_manager.py:1331–1411`). This is real-time research UI — no overlap or conflict with the Grafana dashboards above.

---

## 2. Gaps, Problems, and Issues

The notes consistently identify the following open issues. The first three are **operationally meaningful** (broken panels or silent alerts); the rest are quality/correctness debt.

### G1. Stale dashboard panels (7 broken)

**Source**: `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` §3.12.

- 3 cascor inference panels query `juniper_cascor_inference_*` metrics that were removed by OBS-WIRE-01 (`juniper-cascor#204`). Result: "no data" overlays in `juniper-cascor.json`.
- 4 worker-bridge "pending" placeholder text panels were never replaced with real PromQL after the worker bridges shipped (`juniper-cascor#188`, `#218`).
- An in-flight branch `audit-fixup/stale-dashboard-panels` exists as of 2026-05-06.

### G2. Alertmanager `tickets` and `default` receivers silently drop

**Source**: `code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` §3.2; `observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md` §4.

- Both receivers exist as no-op placeholders. Any alert routed to `default` (warning/info fall-through, finding B.1) or `tickets` (R5.4 slow-burn) is dropped without notice.
- **Soft blocker**: must be wired before lifting log-only severity on SLOs 3.3/3.4 at the **2026-06-02 soak-close** (POST_METRICS_MON_TRACKER §3.3, §3.4).
- OBS-ROUTE-01 is the proposed fix track (A9_AND_3_2_STATE_ANALYSIS §5.2).

### G3. `juniper_data_datasets_cached` Gauge has no production caller

**Source**: `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` §3.11.

- Defined in `juniper-data/api/observability.py`, exercised by mocks in tests, but never emitted at any cache mutation site. Audit Dim A missed it (grep was cascor/canopy-heavy).
- User direction (2026-05-06): **wire**, do not remove. In-flight sister PR exists.

### G4. ~11 dead `cascor_ws_*` metrics (audit finding A.9)

**Source**: `observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md` §3.

Defined in `juniper-cascor/src/api/observability.py` lines 443–633 with **zero production callers**. Two were wired by OBS-WIRE-01 (`#204`, merged 2026-05-03):

- `cascor_ws_broadcast_send_duration_seconds`
- `cascor_ws_command_handler_seconds`

Still dead (per §3.1–§3.12): `cascor_ws_seq_current`, `cascor_ws_replay_buffer_occupancy`, `cascor_ws_replay_buffer_capacity`, `cascor_ws_resume_requests_total`, `cascor_ws_resume_replayed_events`, `cascor_ws_broadcast_timeout_total`, `cascor_ws_state_throttle_coalesced_total`, `cascor_ws_broadcast_from_thread_errors_total`, `cascor_ws_connections_active`, `cascor_ws_command_responses_total`, `cascor_ws_seq_gap_detected_total` (server-side detection deemed infeasible).

§3.15 explicitly verifies **no dashboard, recording rule, or alert references** any of these metrics — i.e., removing them would break nothing visible. OBS-WIRE-02 (§5.1) is the proposed wire-them-all PR.

### G5. Canopy middleware order skews per-request labels

**Source**: `JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` §4.3, finding C.1.

`PrometheusMiddleware` is added after `RequestIdMiddleware` at `main.py:312`, so under FastAPI's LIFO outer-first execution it runs **before** the request-id ContextVar is set. Cascor and data have the correct order.

### G6. Cascor `training_step_duration_seconds` only ever has `phase="output"`

**Source**: `JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` §4.1.6, finding A.6.

The SLO catalogue PromQL filters `phase=~"input|candidate|output"`, but the metric is hard-coded to `phase="output"` at `manager.py:1328`. Either drop the (effectively constant) `phase` label or add input/candidate emission sites.

### G7. WS-handler histogram bucket tightness

**Source**: `JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` §4.4, finding D.2.

`cascor_ws_command_handler_seconds` 50 ms SLO target sits one bucket below the 100 ms `+inf` cap → limited breach-detection precision. Deferred to R5.1c post-soak calibration per `juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md` §5.4.

### Cross-document contradictions

None found within the Grafana/observability scope. Audit Dim A's inventory aligns with `SLO_CATALOG`, `alert_rules.yml`, and dashboard JSON. The only intentional deferral is A.9.

---

## 3. Options & Analysis

For each gap above, this section enumerates 2–4 options, weighs them, and recommends one. Effort is rough order-of-magnitude.

### G1. Stale dashboard panels — Options

| # | Option                                                   | Effort | Strengths              | Weaknesses             | Risks                  | Guardrails                                 |
|---|----------------------------------------------------------|--------|------------------------|------------------------|------------------------|--------------------------------------------|
| A | Land in-flight `audit-fixup/stale-dashboard-panels` PR:  | S      | Single PR, single      | Re-uses same dashboard | Wrong PromQL ships     | Add a **dashboard-lint** check             |
|   | -- replace 3 inference panels with current `cascor_ws_*` |        | -- revert, fast fix    | -- JSON ergonomics; no | -- & one notices       | -- (jsonschema + `promtool query instant`) |
|   | -- panels (if wired), replace 4 place-holder texts with  |        | -- for visible bug.    | -- structural cleanup. | -- until incident.     | --  in CI for                              |
|   | -- real PromQL bridged from `WorkerRegistryCollector`.   |        |                        |                        |                        | -- `juniper-deploy/grafana/**/*.json`.     |
| B | Delete the stale panels; defer replacement until         | XS     | Removes operator       | Loses dashboard        | Operators chase        | Note removal in dashboard description      |
|   | -- OBS-WIRE-02 wires the real metrics.                   |        | -- confusion           | -- real-estate;        | -- removed signals     | --  block.                                 |
|   |                                                          |        | -- immediately.        | -- signals retreat.    | -- during incidents.   |                                            |
| C | Convert the 7 panels into Grafana Alert/State panels     | M      | Single source of truth | Larger change surface; | Breaks unrelated       | Mirror the panel set in a staging          |
|   | -- keyed off recording rules instead of raw metrics.     |        | -- (recording rules),  | -- recording rule      | -- panels if recording | -- dashboard first.                        |
|   |                                                          |        | -- survive  rename.    | -- maturity varies.    | -- rule names drift.   |                                            |

**Recommendation: A.** It's already in flight and fixes the actual bug. Pair with the CI guardrail below to prevent regression. C is correct long-term but out of scope for "fix what is currently broken."

**New guardrail (regardless of option):** add a `juniper-deploy` CI lane that runs `promtool check rules` on `alert_rules.yml` and a JSON schema + `promtool query instant` smoke test on each dashboard panel's PromQL against a synthetic Prometheus, so future metric removals fail loud.

### G2. Alertmanager silent receivers — Options

| # | Option | Effort | Strengths | Weaknesses | Risks | Guardrails |
|---|--------|--------|-----------|------------|-------|------------|
| A | **Email-via-Gmail SMTP for both `default` and `tickets`** as immediate wiring (OBS-ROUTE-01); upgrade `critical` to PagerDuty later (OBS-ROUTE-02). | S | Unblocks 2026-06-02 soak; uses existing SOPS-encrypted creds; no new vendor. | Email is high-noise for warning fall-through; no on-call paging escalation. | Inbox flood; alert fatigue. | Apply `group_by`, `group_wait=30s`, `repeat_interval=12h`/`4h` already configured; add an **inhibit rule** so `critical` suppresses lower severities on the same `service`+`instance`. |
| B | Stand up Alertmanager → Slack webhook (`#juniper-alerts`) for both placeholder receivers. | S | Better triage UX, threading, ack-via-emoji workflows. | Requires a new Slack webhook + maintenance; no formal ack/runbook link. | Slack outage = silent drop again. | Pair Slack with a tiny dead-man-switch alert that fires every 30 min; if it stops, page on-call. |
| C | Wire to PagerDuty for everything immediately. | M | Real on-call pipeline, escalations, runbook attach. | Cost per service; ticket-severity alerts shouldn't page. | Page fatigue from `tickets` severity. | PagerDuty service-per-severity; ticket severity to "low-urgency" service that auto-resolves. |
| D | Do nothing; remove the placeholder receivers and stop routing alerts there (drop SLO 3.3/3.4 burn rules). | XS | Reduces silent-failure surface to zero. | Loses the alerts altogether; violates the SLO program close-out. | Soft regression of R5.4 burn-rate program. | None — this is the path of giving up the SLI. |

**Recommendation: A, then C in a follow-up.** A is shippable in days, satisfies the soak-close blocker, and Gmail SMTP is already in scope (per Memory: gmail tooling is configured). C is the right destination but requires procurement and an on-call rota; queue it as OBS-ROUTE-02 for after the public-release window.

### G3. `juniper_data_datasets_cached` dead Gauge — Options

| # | Option | Effort | Strengths | Weaknesses | Risks | Guardrails |
|---|--------|--------|-----------|------------|-------|------------|
| A | Wire emission at every cache mutation site in juniper-data (user-directed, in flight). | S | Honors user direction; gives a real cache-utilization signal for `juniper-data.json`. | One more mutation hook to keep in sync with cache implementation. | Drift between Gauge and actual cache size. | Add a unit test that asserts `Gauge.value == len(cache)` after each operation; cover `set`/`delete`/`evict`. |
| B | Remove the metric and its dashboard panel. | XS | Eliminates dead-metric debt. | Contradicts user direction; loses observability into POST cache health. | Users lose insight at exactly the time R4.5 added cache-hit visibility. | None — declined. |
| C | Replace Gauge with a `Counter` of mutations and let dashboards compute derivative. | S | Simpler emit semantics (no `len(cache)` reads on hot path). | Loses absolute size; harder to reason about leaks. | Cardinality if labelled per-cache. | Keep cache name as a single label; cap dimensions. |

**Recommendation: A.** It matches user direction, the work is already started, and the test guardrail makes drift visible immediately.

### G4. Dead `cascor_ws_*` metrics (A.9) — Options

| # | Option | Effort | Strengths | Weaknesses | Risks | Guardrails |
|---|--------|--------|-----------|------------|-------|------------|
| A | **OBS-WIRE-02**: wire all 9 viable helpers in one PR (per §5.1); remove `cascor_ws_seq_gap_detected_total` and `cascor_ws_connections_active` (`endpoint` label) as not feasible. | M | Closes A.9 cleanly; gives WS resume/replay/throttle observability. | Larger PR; touches 4 cascor source files; needs careful test coverage on resume path. | Subtle behavior change in WS broadcast path. | Land behind a feature flag (`JUNIPER_CASCOR_WS_METRICS_FULL=1`) initially; flip default after one soak window. |
| B | Remove all 11 dead metrics now; add back if/when needed. | S | Reduces metric inventory; eliminates dead-code grep noise. | Loses any chance of historical data on resume/replay; future re-add will not have backfill. | Re-add later costs more than wiring now. | Move definitions into an `unwired/` module so the intent is preserved. |
| C | Wire only the cheapest 2 (replay buffer occupancy + capacity) and remove the rest. | S | Quick visible win with negligible risk. | Punts on the resume/replay metrics that are most useful for incident triage. | Same as B for the metrics dropped. | Same as B for the dropped subset. |
| D | Defer entirely; A.9 is documented and harmless. | XS | No effort. | Continues the dead-code drag and audit re-discovery cost. | Audit fatigue, reviewer churn. | None. |

**Recommendation: A, behind a flag.** The metrics are designed; wiring is local; the flag bounds rollout risk. C is a defensible "minimum viable progress" if A's review surface is too large for the current week — in that case do C first and queue the rest.

### G5. Canopy middleware order — Options

| # | Option                                         | Effort | Strengths            | Weaknesses            | Risks                           | Guardrails                       |
|---|------------------------------------------------|--------|----------------------|-----------------------|---------------------------------|----------------------------------|
| A | Swap `add_middleware` order at                 | XS     | One-line fix; aligns | None notable.         | Subtle: any code relying on the | Add unit test: assert request-id |
|   | -- `main.py:312` so `PrometheusMiddleware`     |        | -- canopy with       |                       | -- current ordering breaks.     | -- header is present in metric   |
|   | -- is added first, `RequestIdMiddleware` last. |        | -- cascor and data.  |                       |                                 | -- labels for exemplar request.  |
| B | Read request-id explicitly inside              | S      | Decouples ordering.  | Duplicates request-id | Drift between header parsers.   | Extract a single parsing helper  |
|   | -- `PrometheusMiddleware` rather than          |        |                      | -- parsing logic.     |                                 | -- into `juniper-observability`. |
|   | -- via ContextVar.                             |        |                      | -- parsing logic.     |                                 |                                  |
| C | Defer; document the limitation                 | XS     | No code change.      | Metrics keep          | Incident triage harder.         | None.                            |
|   | -- in the SLO catalogue.                       |        |                      | -- mis-labelling      |                                 |                                  |

**Recommendation: A.** Trivial fix; matches the other services; the test prevents future regression.

### G6. `training_step_duration_seconds` `phase` label — Options

| # | Option | Effort | Strengths | Weaknesses | Risks | Guardrails |
|---|--------|--------|-----------|------------|-------|------------|
| A | Drop the `phase` label entirely; update SLO PromQL and dashboard panels. | S | Truthful metric; less cardinality. | Loses the option to add input/candidate slices later without a metric rename. | Stale alerts referencing `phase=...`. | `promtool check rules` in CI catches stale label refs. |
| B | Add `phase="input"` and `phase="candidate"` emission sites at the corresponding training stages. | M | Honors original SLO design; richer attribution. | Real code surface in `manager.py`; needs test coverage. | Mis-classifying steps inflates one phase. | Add unit tests asserting expected `phase` per training stage. |
| C | Defer; carry the discrepancy as known. | XS | No code change. | SLO PromQL silently mis-targets. | Burn-rate alerts fire wrong. | None. |

**Recommendation: B.** The SLO design intent was three phases; dropping the label silently de-scopes a published SLI. B is more work but it's the only option that keeps the catalogue honest. If schedule pressure dictates A, do A in the *same PR* that updates `SLO_CATALOG_2026-05-03.md` so the catalogue and metric are never out of sync.

### G7. WS-handler histogram buckets — Options

| # | Option                                           | Effort | Strengths                         | Weaknesses                                  | Risks                                          | Guardrails                                              |
|---|--------------------------------------------------|--------|-----------------------------------|---------------------------------------------|------------------------------------------------|---------------------------------------------------------|
| A | Re-bucket `cascor_ws_command_handler_seconds`    | S      | Better breach-detection precision | Histogram cardinality grows slightly.       | Older series in TSDB lose bucket-comparable    | Note bucket change in `HISTOGRAM_BUCKETS_RATIONALE.md`; |
|   | -- with one or two extra steps between 50 ms     |        | -- around the SLO target.         |                                             | -- history at the boundary.                    | -- pair with a recording-rule rename so dashboards      |
|   | -- and 100 ms (e.g., 60, 75, 90).                |        |                                   |                                             |                                                | -- switch over cleanly.                                 |
| B | Defer to R5.1c post-soak calibration as planned. | XS     | Calibrated against real traffic.  | Operates with a known precision gap.        | If the SLO is breached during soak,            | Document the precision gap in the `juniper-overview`    |
|   |                                                  |        |                                   | -- until soak ends.                         | -- root-cause is fuzzy.                        | -- panel description.                                   |
| C | Switch to a `Summary` (client-side quantiles).   | M      | Direct quantile readings.         | Summaries don't aggregate across instances; | Misleading aggregate in multi-replica deploys. | None.                                                   |
|   |                                                  |        |                                   | -- loses breach attribution per replica.    |                                                |                                                         |

**Recommendation: B.** Calibration against real traffic (per the rationale doc's §5.4 acceptance) beats an ungrounded re-bucket. Promote this to A only if the soak surfaces a mis-classification.

---

## 4. Cross-cutting recommendations

These apply regardless of which per-gap option you pick.

1. **Add a dashboard/alert lint lane to `juniper-deploy` CI.** Run `promtool check rules` on `alert_rules.yml` + `recording_rules.yml`, JSON-schema-validate each dashboard, and (cheap) extract every PromQL expression and `promtool query instant` it against a synthetic Prometheus that has the recording-rule-defined series. This single guardrail closes G1 permanently and catches future metric renames at PR time instead of operator triage time.
2. **Single-source the SLO catalogue → dashboard tile mapping.** Add a small generator script in `juniper-deploy` that reads `SLO_CATALOG_2026-05-03.md`'s machine-readable section and emits the headline tiles in `juniper-overview.json`. Today these are hand-synced; G6's "drop a label" risk drops out of view if generated.
3. **Adopt a `register_or_reuse` pattern for any new metric** (already canonical via `juniper-observability`; see Memory). Apply when wiring G3 and G4-A so duplicate registration during reload doesn't blow up the collector.
4. **Document the 4-dashboard inventory in `docs/REFERENCE.md`** in this repo with screenshots and the SLO each panel ladders to. Today the dashboards are documented only inside `juniper-deploy/notes/`; they are invisible to anyone consuming the public `juniper-ml` docs.

---

## 5. Status snapshot (as of 2026-05-09 per source notes)

| Component                                  | Status                         | Operationally blocking?       | Target                                                  |
|--------------------------------------------|--------------------------------|-------------------------------|---------------------------------------------------------|
| 4 provisioned dashboards                   | Live; R5.3 refresh shipped     | No                            | —                                                       |
| Prometheus scrape wiring (4 jobs)          | Live                           | No                            | —                                                       |
| Recording + R5.4 burn-rate alert rules     | Live                           | No                            | SLO calibration at soak-close 2026-06-02                |
| Cascor WS metrics (A.9) — 9 helpers dead   | Open                           | No                            | OBS-WIRE-02 (recommended G4-A)                          |
| Alertmanager `default`/`tickets` receivers | Placeholder, silently dropping | **Yes (soft, by 2026-06-02)** | OBS-ROUTE-01 (recommended G2-A)                         |
| Stale dashboard panels (7)                 | In-flight fix                  | **Yes (operational)**         | `audit-fixup/stale-dashboard-panels` (recommended G1-A) |
| `juniper_data_datasets_cached` dead Gauge  | In-flight wire                 | No                            | Sister PR (recommended G3-A)                            |
| Canopy middleware order (request-id)       | Open                           | No                            | C.1 PR (recommended G5-A)                               |
| Training-step `phase` label discrepancy    | Open                           | No                            | A.6 PR (recommended G6-B)                               |
| WS-handler bucket precision                | Open, deferred                 | No                            | R5.1c post-soak (recommended G7-B)                      |

---

## 6. Files referenced (for direct follow-up reading)

- `JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md` §4.1–§4.5
- `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md`
- `code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` §3.2, §4.1.6, §4.3, §4.4
- `code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` §3.3, §3.4, §3.11, §3.12
- `observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md` §3.1–§3.15, §4, §5.1, §5.2
- `legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md` §4.1, §4.3
- `JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md`
- (cross-repo, claimed) `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md`
- (cross-repo, claimed) `juniper-deploy/grafana/provisioning/dashboards/{juniper-overview,juniper-cascor,juniper-canopy,juniper-data}.json`
- (cross-repo, claimed) `juniper-deploy/prometheus/{prometheus.yml,alert_rules.yml,recording_rules.yml}`
- (cross-repo, claimed) `juniper-deploy/alertmanager/alertmanager.yml`
- (cross-repo, claimed) `juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md` §5.4
