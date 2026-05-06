# METRICS-MON Phase R5 — Entry Plan

**Date:** 2026-05-02
**Author:** Paul Calnon
**Status:** 🟡 Plan — open for review.
**Phase:** R5 (SLO/SLI catalog + scrape manifests + Grafana dashboards + alerting).
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §8.
**Companion:** [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md) and [`METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md`](METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md) (the patterns this plan follows).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. Purpose

Phase R4 closed 2026-05-02 (juniper-ml#186): every histogram has documented per-boundary rationale, the data-client surface is observable through Prometheus closures, the worker heartbeat carries training-loop instrumentation, and the request-id chain spans the canopy/cascor → data-client → data hop. Phase R5 is the **production-observability deliverable** — turning the metric / probe / log surface that R1–R4 built into a usable operator experience: explicit SLOs, validated scrape configuration, working Grafana dashboards, and burn-rate alerting tied to the SLOs.

R5 is **partially seeded** in juniper-deploy already:

- `prometheus/prometheus.yml` — scrape configs for the 3 servers + alertmanager wiring.
- `prometheus/alert_rules.yml` — alert groups (`juniper_service_health`, `juniper_error_rates`, plus others).
- `grafana/provisioning/dashboards/` — 4 dashboards (juniper-canopy.json, juniper-cascor.json, juniper-data.json, juniper-overview.json).
- `alertmanager/alertmanager.yml` — routing config.
- `k8s/helm/` — Helm charts for the 3 services.

So R5 is largely **rationalization + extension** rather than greenfield: align the existing artifacts against an explicit SLO catalog, surface the new R4 metrics (R4.3 data-client closure metrics, R4.4 worker training-loop fields, R4.5 POST cache-hit counter), re-bucket the 2 R4.1-flagged cascor histograms, and replace any implicit-threshold alerts with burn-rate alerts derived from SLOs.

This plan **sequences the 4 R5 sub-tracks** (plus the gating MetricsAuthMiddleware question raised by R2.1 and the 2 R4.1 re-bucketing flags), resolves eight open questions before any implementation lands, and pins the Phase R5 exit criteria. The goal is to enter post-R5 production with **every alert traceable to an SLO, every dashboard panel keyed to a documented metric, and every scrape target known to be emitting the right shape**.

---

## 2. The 4 sub-tracks (plus gating items)

| ID | Repo(s) | Composite | What | Cross-repo coupling | Existing artifact? |
|---|---|:---:|---|---|---|
| **R5.1** | juniper-deploy (+ optional cascor re-bucket) | 3 | SLO/SLI catalog for the 3 servers + worker. Per service: availability SLI (success ratio over rolling window), latency SLI (histogram quantile against R4.1 buckets), saturation SLI (resource gauge). Tie metric definitions to SLIs. **Includes:** ratify or reshape the 6 R4.1-documented histogram bucket layouts; **re-bucket** the 2 cascor histograms R4.1 flagged (`broadcast_send_duration_seconds`, `command_handler_seconds`). | None at the doc layer; the cascor re-bucket needs a small juniper-cascor production-code PR (covered as R5.1b). | New doc; no prior catalog. |
| **R5.1b** | juniper-cascor | 1 | Re-bucket the 2 R4.1-flagged histograms per the proposed sub-millisecond layout in [`juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`](https://github.com/pcalnon/juniper-cascor/blob/main/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md) §4. Removes the "tentative pending R5.1" markers on those 2 HELP strings; the other 4 markers (cascor inference + replay + canopy WS latency + data generation) stay and migrate to "ratified by R5.1" wording instead. | Couples to R5.1 SLO catalog (the re-bucketed layout must bracket the cascor inference SLO target). | Production code change; no new metric, no new label. |
| **R5.2** | juniper-deploy | 2 | Validate `prometheus/prometheus.yml` covers every R1–R4 metric; add scrape configs for any new endpoints (e.g. cascor-worker `/v1/health` from R1.3); decide on ServiceMonitor CRD adoption (Q4); pin the `MetricsAuthMiddleware` question (Q5). Existing scrape config is the starting point, not the starting line. | If Q5 resolves to "lift to shared lib", touches juniper-observability + the 3 servers (4 PRs). Default no-coupling. | Existing scrape config — extend, don't replace. |
| **R5.3** | juniper-deploy | 3 | Refresh the 4 Grafana dashboards to surface every R4-shipped metric: R4.3 data-client closure metrics on the canopy dashboard; R4.4 worker training-loop fields on the cascor dashboard; R4.5 POST cache-hit panels on the data dashboard. Cross-cutting "Juniper Overview" dashboard surfaces the 4 SLO burn-rates as the headline tile. Decide JSON-committed vs jsonnet-build (Q6). | None. | 4 existing dashboards; refresh each, add SLO-burn tile to overview. |
| **R5.4** | juniper-deploy | 3 | Replace threshold-based alerts in `alert_rules.yml` with burn-rate alerts derived from R5.1 SLOs. Multi-window multi-burn-rate alert pattern (page on 1h × 14.4 burn AND 6h × 6 burn). Keep `ServiceDown` / `ServiceRestartLoop` as is (those are health alerts, not SLO alerts). | None. Coupled internally to R5.1 SLO catalog (alerts derive from SLOs). | Existing alert rules — refactor, don't replace. |
| **gating** | juniper-observability + 3 servers | 1–4 | **MetricsAuthMiddleware** question (raised 2026-04-28 from R2.1 design Q3): does the per-service `/metrics` IP allowlist (currently juniper-data only, SEC-16) belong in the shared `juniper-observability` lib? Decide as part of R5.2 (Q5). | If "yes" → 1 lib PR + 2 server adoption PRs (cascor, canopy). If "no, keep per-service" → 1 doc PR in juniper-deploy/notes/. | — |

**Total**: 5 sub-tracks (4 + R5.1b), **~7–11 PRs** (range depends on Q4 ServiceMonitor scope and Q5 MetricsAuthMiddleware lift).

---

## 3. Open questions and resolutions

### Q1. R5.1 — SLO methodology: direct user-facing or all-internal?

**Trade-off:**

- **(a) Direct user-facing only**: define SLOs for the surfaces a real user (researcher, ops, CI consumer) interacts with — canopy dashboard liveness, juniper-data POST latency, cascor inference latency. **Skip** internal-machine surfaces (worker → cascor heartbeats, data-client → data RPC). Smaller catalog, easier to maintain; matches the "user-facing SLO" Google SRE convention.
- **(b) All metrics get SLOs**: SLO every histogram, every counter, every gauge. Maximalist; produces 30+ SLOs across the 6 services; high maintenance overhead; some SLOs would be self-referential (worker heartbeat SLO — if worker is dead, who'd see the alert?).
- **(c) User-facing primary + internal-supporting**: 5–6 user-facing SLOs as the "release-blocking" set; a separate secondary set of internal-supporting SLIs (heartbeat freshness, registry size) tracked but not directly alertable. Hybrid; biggest catalog but cleanest operational discipline.

**Resolution: (c) — user-facing primary + internal-supporting.** R5.4 alerts only fire on user-facing SLO breach (page on-call); internal-supporting SLIs surface in dashboards but route to log-only severity. Splits the "wakes someone up at 3am" decision cleanly. Estimated catalog: 5 primary + 8 supporting = ~13 SLIs.

### Q2. R5.1b — Re-bucket scope: handle in R5.1 doc PR or carve out separately?

**Trade-off:**

- **(a) Bundle re-bucket into the R5.1 doc PR** (one juniper-deploy PR + one juniper-cascor PR sequenced). Smaller blast radius per PR but tightly couples the doc + code change.
- **(b) Separate R5.1 doc + R5.1b cascor code PR**, land in either order. The re-bucket can ship before the SLO catalog if the proposed sub-millisecond layout in `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §4 is accepted as-is.

**Resolution: (b) — separate R5.1 + R5.1b.** The re-bucketing is a localized code change with its own test impact (existing histogram tests need bucket-count updates). Splitting it into R5.1b lets it land independently of the SLO catalog text and reuses the proven "schema-similar fan-out" pattern from R4.1. Land R5.1b before R5.1 if R5.1 SLO catalog needs to reference the new bucket layout; otherwise either order works.

### Q3. R5.1 — SLO catalog authoring location: juniper-deploy or per-service?

**Trade-off:**

- **(a) Single juniper-deploy doc** (`notes/SLO_CATALOG_2026-05-XX.md`). Centralized; matches where alerts and dashboards live.
- **(b) Per-service docs** in each repo's `notes/observability/`, with a juniper-deploy index pointing at them. Closer to the metric definitions but harder for ops to read end-to-end.
- **(c) juniper-deploy primary + per-service appendix** linking back. Hybrid, double-maintenance.

**Resolution: (a) — single juniper-deploy doc.** Roadmap §8 already proposed this location. Operators read SLOs from juniper-deploy alongside the alert rules and dashboards; per-service authoring would split the SLO definition from the alerting derivation. The R4.1 per-service histogram-rationale docs already sit in each repo's `notes/observability/` — they remain the authority on bucket choice; the juniper-deploy SLO doc references them for justification.

### Q4. R5.2 — Scrape strategy: ServiceMonitor CRDs (Prometheus Operator) or raw configs?

**Trade-off:**

- **(a) Raw `scrape_configs` in `prometheus.yml`** (current state). Works against any Prometheus installation; no Operator dependency.
- **(b) ServiceMonitor CRDs** in `k8s/helm/`. Required if running on Prometheus Operator (a common production deployment); duplicates the raw config for non-Operator setups.
- **(c) Both** — keep raw config for docker-compose / non-k8s; add ServiceMonitor CRDs in helm for Operator deployments.

**Resolution: (c) — both.** docker-compose remains the supported "small-deploy" target (per `juniper-deploy/AGENTS.md`); k8s + Operator is the production target. Maintaining both is acceptable cost — the configs are short and the duplication is mechanical (templated from the same scrape interval / timeout / target list constants in `.env.example`).

### Q5. R5.2 — MetricsAuthMiddleware: lift to shared lib or keep per-service?

This is the **gating issue raised 2026-04-28 from R2.1 design Q3** that R5 was tasked with resolving.

**Trade-off:**

- **(a) Lift to `juniper-observability` shared lib.** Cascor and canopy adopt it via the same R2.1 import path; eliminates per-service drift. Cost: 1 lib PR + 2 server adoption PRs + new minor release.
- **(b) Keep per-service.** juniper-data has SEC-16 (IP allowlist) because its `/metrics` returns dataset-related metrics that could leak access patterns; cascor and canopy have no such sensitive surface and don't need an allowlist. Document the rationale in juniper-deploy/notes/.
- **(c) Lift only the mechanism (middleware class + trusted-IPs config primitive); keep per-service the decision to mount it.** Best of both — discoverable in the shared lib, opt-in per service.

**Resolution: (b) — keep per-service, document rationale.** Cascor and canopy don't need an IP allowlist on `/metrics` (no sensitive surface; production scrape will use ServiceMonitor with k8s NetworkPolicy for access control). Lifting the middleware for one consumer (data) bloats the shared lib without payoff. Document the asymmetry in juniper-deploy/notes/ as part of R5.2; if a future cascor/canopy use case emerges, revisit. Decision-rationale doc replaces a multi-PR fan-out.

### Q6. R5.3 — Dashboard format: JSON committed or jsonnet build?

**Trade-off:**

- **(a) JSON committed** (current state — 4 dashboards in `grafana/provisioning/dashboards/*.json`). Drop-in for Grafana provisioning; large JSON diffs on edits; hard to factor common panels.
- **(b) jsonnet build pipeline** producing the JSON at deploy time. Easier to factor common panels (e.g. one "service-up + error-rate" panel template applied to all 3 servers); requires a build step (CI + local).
- **(c) grafonnet** (Grafana's own jsonnet library) — same as (b) but with Grafana's blessed primitives.

**Resolution: (a) — keep JSON committed.** 4 dashboards is below the threshold where jsonnet's factoring win pays for the build complexity. A future R6 phase (if dashboards proliferate beyond ~10) can revisit. R5.3's job is to refresh the 4 existing JSONs to surface the new R4 metrics; introducing a build pipeline doubles the PR scope without immediate payoff.

### Q7. R5.4 — Alerting: burn-rate or threshold-based?

**Trade-off:**

- **(a) Burn-rate alerts** derived from SLOs. Multi-window multi-burn-rate (MWMBR) pattern: page on (1h × 14.4 burn AND 6h × 6 burn) for fast-burn; (6h × 6 AND 24h × 3) for slow-burn. Catches both sudden outages (1h) and slow degradations (24h) without separate thresholds. Industry standard for SLO-driven alerting.
- **(b) Threshold-based alerts** (current state): "error rate > 5% for 5 min". Easier to write, harder to tune; produces flappy alerts on low-traffic services.
- **(c) Hybrid** — burn-rate for SLO-coupled alerts; threshold for health alerts (`ServiceDown`, `ServiceRestartLoop`).

**Resolution: (c) — hybrid.** Burn-rate is the right tool for SLO breach detection; threshold is the right tool for "service is gone" health alerts (you don't compute burn-rate against a missing service). Existing `juniper_service_health` alert group stays threshold-based; existing `juniper_error_rates` and any new latency/availability alerts move to burn-rate keyed off the R5.1 SLO targets.

### Q8. Sequencing — strict serial or some parallel?

**Trade-off:**

- **(a) Strict serial: R5.1 → R5.1b → R5.2 → R5.3 → R5.4.** Each PR can reference the previous. Slowest.
- **(b) Some parallel: R5.1 + R5.1b serializes; R5.2 + R5.3 can land in parallel (both consume R5.1 outputs but don't conflict); R5.4 gates on R5.1.** Fastest.
- **(c) R5.1 + R5.2 in parallel (R5.2 doesn't need the SLO doc to validate scrape configs); R5.3 + R5.4 serial after R5.1.** Mixed.

**Resolution: (b).** R5.2 (scrape configs) only needs to know which metrics exist; that's already settled by R1–R4 + R4.1 docs. R5.3 (dashboards) can refresh the 4 existing dashboards in parallel (one PR per dashboard, shipping the new R4 metrics). R5.4 (alerts) needs R5.1 SLO targets to derive burn-rate thresholds — gate on R5.1 only.

---

## 4. Sequencing — what gates what?

**Wave 1 (parallelizable, no inter-PR coupling):**

- **R5.1b** (juniper-cascor): re-bucket 2 histograms. 1 PR.
- **R5.2** (juniper-deploy): scrape config validation + ServiceMonitor CRDs + MetricsAuthMiddleware decision-doc. 1 PR (or 2 if Q5 unexpectedly resolves to lift).
- **R5.3** (juniper-deploy): 4 dashboard refreshes. 1 PR (single juniper-deploy PR touching all 4 JSONs is cleaner than 4 separate PRs).

**Wave 2 (gated on R5.1):**

- **R5.1** (juniper-deploy): SLO catalog. 1 PR.
- **R5.4** (juniper-deploy): burn-rate alerts derived from R5.1 SLOs. 1 PR. Lands after R5.1.

**Closure:**

- Phase R5 close note in juniper-ml roadmap §8. 1 PR.

**Recommended landing order:** Wave 1 (3 PRs in parallel) → R5.1 → R5.4 → close. **Total**: 7 PRs base case (no MetricsAuthMiddleware lift, single juniper-deploy R5.3 PR). Estimated wall-clock at the prior cadence (~5 PRs/day): **1.5–2 working days end-to-end**.

---

## 5. Phase R5 exit criteria

R5 is done when **all** of the following hold:

1. **R5.1**: `juniper-deploy/notes/SLO_CATALOG_2026-05-XX.md` exists, defining 5 primary user-facing SLOs (per Q1 (c)) plus 8 internal-supporting SLIs. Every SLO references the metric (and label set) it's measured against, the rolling window, the target, and the alert that fires on breach.
2. **R5.1b**: `cascor_ws_broadcast_send_duration_seconds` and `cascor_ws_command_handler_seconds` re-bucketed per the proposed sub-millisecond layout. HELP strings updated to "(R5.1-ratified)" or equivalent. The other 4 R4.1 markers ("tentative pending R5.1") on the remaining histograms also get updated to ratified-or-reshaped wording.
3. **R5.2**: `prometheus/prometheus.yml` covers every metric R1–R4 emit. ServiceMonitor CRDs present in `k8s/helm/` for the 3 servers (per Q4 (c)). MetricsAuthMiddleware-asymmetry rationale doc lives at `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (per Q5 (b)).
4. **R5.3**: 4 Grafana dashboards refreshed; every new R4 metric surfaces somewhere; "Juniper Overview" gets an SLO burn-rate tile.
5. **R5.4**: Burn-rate alerts derived from R5.1 SLOs in `prometheus/alert_rules.yml`; threshold-based health alerts (`ServiceDown`, `ServiceRestartLoop`) preserved (per Q7 (c)).
6. **§9 status table**: every R5 row flipped to **done** with PR refs.
7. **§8 close note**: a "Phase R5 status (2026-05-XX): ✅ COMPLETE" subsection mirroring the R3/R4 close notes.

After R5 closes, the **METRICS-MON program is complete**. Any subsequent observability work moves to a new program — operational tuning, additional service onboarding, or an R6-style ergonomics-only follow-up.

---

## 6. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|:---:|---|
| R5.1 SLO targets are over-aggressive or under-aggressive on first authoring (no production traffic baseline) | High | Mark every SLO target in the catalog as **"initial — to revisit after 30-day soak"**. Don't trip alerts on first 30 days until burn-rate calibration is verified against actual traffic. |
| R5.1b re-bucket invalidates existing tests pinning specific bucket counts | Medium | The R4.1 doc references existing tests; pre-search for `_count` / `_bucket` assertions in cascor's WS test suite before authoring R5.1b. Update tests in the same PR. |
| R5.2 ServiceMonitor CRDs require a Prometheus Operator install for CI to validate | Medium | Skip CI validation of ServiceMonitor YAML beyond `kubectl apply --dry-run=client`; full validation is deployment-time only. Document the gap in R5.2's exit criteria. |
| R5.3 dashboard JSON diffs are hard to review (Grafana's auto-generated JSON is verbose) | Medium | Per-PR scope to one dashboard at a time, OR ship as a single PR with screenshots of before/after attached. |
| R5.4 burn-rate alert thresholds flap under low-traffic periods (development clusters) | Medium | MWMBR pattern (per Q7) inherently handles low-traffic via the long-window arm; document that single-window burn-rate is forbidden. Threshold-based health alerts (`ServiceDown`) cover the "no traffic at all" case. |
| Q5 (MetricsAuthMiddleware) decision turns out wrong — a future cascor/canopy use case needs the allowlist | Low | The shared lib already exports the primitives needed (RequestIdMiddleware, PrometheusMiddleware) so adding `MetricsAuthMiddleware` later is a non-breaking addition. Decision is reversible at low cost. |

---

## 7. Out of scope for R5

- **Distributed tracing** (OpenTelemetry, Jaeger). The R4.6 X-Request-ID propagation is the only correlation primitive METRICS-MON ships; full distributed tracing is a separate program.
- **Log aggregation** (Loki, Elasticsearch). R4.7's structured-WARNING test confirms the worker emits Loki-parseable lines, but standing up a Loki instance is deployment-side work outside METRICS-MON's metric-monitoring focus.
- **APM** (application performance monitoring). Out of scope; R5 sticks to Prometheus + Grafana + Alertmanager.
- **Synthetic monitoring** (blackbox probes against `/v1/health/live` from outside the cluster). Operationally useful but a separate sub-program; R5 covers the in-cluster scrape-and-alert loop only.
- **Cost analytics** (Prometheus storage cost dashboards). Out of scope; R5 produces the metric surface, not the cost analysis of the metric surface.
- **Worker training-quality observability** (correlation gradient norms, candidate diversity). R4.4 explicitly carved this out as a separate "training-quality observability" track.

---

## 8. Cross-track dependencies

- **R5.1 ↔ R5.4**: R5.4 burn-rate alerts derive from R5.1 SLO targets. Hard dependency — R5.4 lands after R5.1.
- **R5.1 ↔ R5.1b**: R5.1's SLO targets for the 2 cascor flagged histograms must use the *re-bucketed* layout from R5.1b. R5.1b should land first, OR R5.1 should reference the post-R5.1b layout explicitly with a forward-pointer. Either order works; sequencing is a coordination preference, not a correctness requirement.
- **R5.3 ↔ R4.x**: R5.3 dashboards consume the R4-shipped metrics (R4.3 data-client, R4.4 worker, R4.5 POST cache-hit). All R4 metrics are live (R4 closed); no rolling deployment concern.
- **R5.2 ↔ R5.3**: R5.3 dashboards query metrics that R5.2 scrape configs surface. Today's `prometheus.yml` already scrapes the 3 servers, so existing metrics are available; R5.3 doesn't strictly gate on R5.2 unless a *new* scrape target is added.

---

## 9. Reference: existing juniper-deploy artifacts as the starting point

R5 is **rationalization + extension** rather than greenfield. Existing artifacts that R5 PRs modify rather than replace:

| File | R5 sub-track that touches it | What changes |
|---|---|---|
| `prometheus/prometheus.yml` | R5.2 | Validate coverage; add scrape for any new endpoint (cascor-worker `/v1/health` from R1.3). |
| `prometheus/alert_rules.yml` | R5.4 | `juniper_service_health` group preserved; `juniper_error_rates` + new SLO-derived groups become burn-rate. |
| `alertmanager/alertmanager.yml` | R5.4 (minor) | Routing tweaks for SLO severity classes. |
| `grafana/provisioning/dashboards/juniper-overview.json` | R5.3 | Add SLO burn-rate headline tile. |
| `grafana/provisioning/dashboards/juniper-canopy.json` | R5.3 | Add R4.3 data-client metrics panels. |
| `grafana/provisioning/dashboards/juniper-cascor.json` | R5.3 | Add R4.4 worker training-loop fields panels. |
| `grafana/provisioning/dashboards/juniper-data.json` | R5.3 | Add R4.5 POST cache-hit panel. |
| `k8s/helm/` | R5.2 | Add ServiceMonitor CRDs per Q4 (c). |
| `notes/SLO_CATALOG_2026-05-XX.md` | R5.1 | New file. |
| `notes/METRICS_AUTH_RATIONALE.md` | R5.2 | New file (Q5 (b) decision rationale). |

---

## Appendix A — PR-count reconciliation

| Wave | Sub-track | PRs |
|---|---|---|
| 1 | R5.1b (cascor) | 1 |
| 1 | R5.2 (juniper-deploy: scrape + ServiceMonitor + MetricsAuth doc) | 1 |
| 1 | R5.3 (juniper-deploy: 4 dashboard refresh) | 1 |
| 2 | R5.1 (juniper-deploy: SLO catalog) | 1 |
| 2 | R5.4 (juniper-deploy: burn-rate alerts) | 1 |
| 3 | Phase R5 close note (juniper-ml) | 1 |

**Range**: 6 PRs base case → up to 9 PRs if Q5 unexpectedly resolves to "lift MetricsAuthMiddleware" (1 lib PR + 2 server adoption PRs) or if R5.3 ends up split per-dashboard.
