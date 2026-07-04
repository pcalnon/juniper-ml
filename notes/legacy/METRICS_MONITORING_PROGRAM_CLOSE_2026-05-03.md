# METRICS-MON — Program Close

<!-- markdownlint-disable MD013 -->

**Project:** Juniper ML (cross-repo program)
**File Name:** `notes/code-review/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`
**Description:** Final closure document for the METRICS-MON observability program. Summarises all five phases (R1–R5) at the program level, captures cross-cutting outcomes, records production posture, and carries forward residual follow-ups that survived program close.
**Author:** Paul Calnon
**Version:** v1.0.0
**License:** MIT
**Date:** 2026-05-03
**Status:** ✅ COMPLETE — when this PR merges, the METRICS-MON program is closed.
**Roadmap (now closed):** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md)
**Per-phase entry plans:** [R3](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md), [R4](METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md), [R5](METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. Executive summary

METRICS-MON delivered the Juniper ecosystem's first explicit, end-to-end
observability discipline. The program ran from the roadmap's authoring date
(**2026-04-25**) through the close PR (**2026-05-03**) — **9 calendar days**,
~3 working weeks at the prior multi-PR-per-day cadence — across **8 repos**
(`juniper-ml`, `juniper-deploy`, `juniper-cascor`, `juniper-canopy`,
`juniper-data`, `juniper-data-client`, `juniper-cascor-worker`,
`juniper-cascor-client`).

**Program purpose:**

- **Cardinality discipline** — bound `endpoint`-style high-entropy labels on
  every Prometheus middleware emitter; replace raw paths with route templates
  + `_unmatched` bucket.
- **Async-safe probes** — replace blocking `urllib.request` calls in
  health-probe paths with native `httpx.AsyncClient`.
- **Shared observability lib** — extract duplicated `DependencyStatus` /
  `ReadinessResponse` / `RequestIdMiddleware` / `JuniperJsonFormatter` into a
  single `juniper-observability` package and migrate three servers onto it.
- **WS schema alignment** — extract WS frame envelopes into the
  `juniper-cascor-protocol` package; consumers validate every inbound frame.
- **Test-coverage gap closure** — close every empty cell in the review plan's
  §10 coverage matrix with either a pinning test or an accepted-gap rationale.
- **Best-practice / ergonomic improvements** — histogram bucket rationales,
  data-client request-id propagation, worker training-loop heartbeat fields,
  POST cache-hit observability counter, structured-WARNING test for
  unrecognised WS frames.
- **SLO catalogue + dashboards + burn-rate alerts** — 5 user-facing primary
  SLIs + 8 internal-supporting SLIs, refreshed Grafana dashboards on each of
  the 4 existing JSON files, MWMBR burn-rate alerts derived from the catalogue.

**Phase outcome at a glance:**

- **R1** (release-blocking fixes) — ✅ COMPLETE 2026-04-28
- **R2** (cross-repo unification) — ✅ COMPLETE 2026-04-30
- **R3** (test-coverage gap closure) — ✅ COMPLETE 2026-05-01
- **R4** (best-practice / ergonomic) — ✅ COMPLETE 2026-05-02
- **R5** (SLO catalogue + scrape + dashboards + alerts) — ✅ COMPLETE 2026-05-03

**Final delta (counted from `gh pr list ... --search "metrics" --state merged`
plus phase-explicit PRs not bearing the keyword):**

- **Total program PRs merged: 78** (count breakdown in §7).
- **Repos touched: 8** (every active Juniper repo plus the
  `juniper-cascor-protocol` sub-package source repo).
- **Wall-clock duration: 9 calendar days** (2026-04-25 → 2026-05-03).
- **Estimate vs. actual:** roadmap §3 forecast 26–39 engineer-days
  sequentially; the wave-based parallel-PR cadence compressed wall-clock to
  ~9 days.

**Headline residuals carried forward** (full list in §6):

- **TRAIN-ARCH-01 mini-batch restoration** (juniper-cascor#194 design doc OPEN
  under user review; user explicitly deferred at design-doc stage). NON-BLOCKER
  for production.
- **R5.4 25-epoch throttle removal** — `cascade_correlation.py:1655` reduces
  burn-rate fidelity for SLO 3.4. Future small sub-track.
- **alertmanager `tickets` receiver** — placeholder added in juniper-deploy#51;
  needs real notification config before SLO 3.3/3.4 ticket-severity alerts come
  off log-only.
- **`amtool check-config` validation** — blocked locally by snap confinement;
  documented container-based fallback in juniper-deploy#51.
- **`juniper_cascor_pending_tasks` worker bridge gap** — alert rule shipped
  guarded by `absent_over_time(...) == 0`; harmlessly inert until the bridge
  ships.

---

## 2. Per-phase recap

### Phase R1 — Release-blocking fixes (✅ COMPLETE on 2026-04-28)

R1 closed three composite-4 findings: cardinality unboundedness on
Prometheus middleware (seed-01), broken probe semantics + status-code
propagation (seed-02 / seed-03), and missing worker liveness + heartbeat
(seed-04).

**Sub-track outcomes:**

- **R1.1 — bound Prometheus middleware cardinality** (juniper-data#49,
  juniper-cascor#143, juniper-canopy#178). Unified `_unmatched` bucket strategy
  on all three servers; the `endpoint` label is restricted to the resolved
  `route.path` template; non-template paths fall into a single `_unmatched`
  bucket and increment a separate `juniper_<svc>_http_unmatched_requests_total{method}`
  counter. **Cardinality stress tests** pin the bound: high-entropy path-param
  attack patterns produce a bounded label set.
- **R1.2 — health probe semantics + status-code propagation**
  (juniper-data#51, juniper-cascor#147, juniper-canopy#183, juniper-deploy#35).
  `/v1/health/ready` returns 503 when any dependency is `unhealthy`; liveness
  probes exercise a real code path within a 250 ms tick budget; on timeout
  return 503 + `X-Juniper-Readiness` advisory header. juniper-deploy#35 ships
  Helm chart v1.0.0 with corrected probe paths.
- **R1.3 — worker liveness + heartbeat** (juniper-cascor#150,
  juniper-cascor-worker#37, juniper-deploy#43). cascor-worker exposes a minimal
  HTTP probe surface; cascor records the heartbeat; `/v1/workers` route
  surfaces `worker_id`, `in_flight_tasks`, `last_task_completed_at`, `rss_mb`.
  Helm chart 1.1.0 ships with `worker.healthcheck.enabled=false` default
  (flag-flip to `true` deferred as R1.3.4 burn-in follow-up).

**Wall-clock:** 2026-04-26 → 2026-04-28 (~3 days, against the §3 estimate of
6–9 engineer-days).

**Surprises during execution:** R1.2 surfaced a **probe-direction asymmetry**
between cascor (returns 503-on-not-ready) and canopy (returns
200-with-degraded). The asymmetry is intentional but was undocumented; this
rolled into R2.3 as the operator-facing topology document.

**Residual items closed:** R1.3.4 chart flag-flip remains deferred for staging
burn-in (carried forward as a chart-only follow-up, not METRICS-MON-blocking).

---

### Phase R2 — Cross-repo unification (✅ COMPLETE on 2026-04-30)

R2 turned three duplicated patterns into single-source-of-truth packages:
`juniper-observability` (extraction of cross-service infra) and
`juniper-cascor-protocol` (extraction of WS frame envelopes), plus
canopy-side regression coverage for the asymmetric probe topology.

**Sub-track outcomes:**

- **R2.1 — shared `juniper-observability` lib** (juniper-ml#155, juniper-ml#164;
  juniper-data#60; juniper-cascor#155; juniper-canopy#199). 5 PRs total.
  `juniper-observability==0.1.1` stable on PyPI 2026-04-29; data, cascor,
  canopy migrated. **Free upgrades shipped via the migration:** tz-aware UTC
  `ReadinessResponse.timestamp` (closes BUG-JD-06-equivalent across all three
  servers), SEC-15 Sentry `before_send` hook (defense-in-depth gained by
  canopy), and the R1.1 cardinality bound now lives in one place.
- **R2 exit-gate decision — worker stays off shared lib** (juniper-ml#168).
  Worker uses 2 of the lib's 20 public symbols (both contract constants); the
  remaining 18 are HTTP-server machinery the worker structurally does not need.
  Decision recorded with re-evaluation triggers documented for the future.
- **R2.2 — WS frame schema validation** (juniper-cascor#156, #159, #160;
  juniper-cascor-client#29; juniper-canopy#206; juniper-cascor-worker#38). 7
  PRs total. New `juniper-cascor-protocol==0.1.0` package; cascor server is
  the **first consumer of its own protocol package** so the producer cannot
  drift from the schema. Worker single-sources `WorkerMessageType` +
  `BinaryFrame.encode` while staying Pydantic-free at runtime; cascor-client
  + canopy validate every inbound frame via Pydantic v2 envelopes; the R1.1
  cardinality strategy bounds the new
  `juniper_<svc>_unrecognized_ws_frames_total{type, endpoint}` counter under
  attacker-controlled types.
- **R2.3 — probe-direction symmetry** (juniper-canopy#202, juniper-deploy#44).
  Probes already in place from R1.2 + R2.1; the gap was canopy's missing
  upstream-down regression. 4 new tests in `TestReadinessDownstreamInjection`,
  including `test_canopy_never_returns_503_on_upstream_down` pinning the
  cascor-503 / canopy-degraded severity asymmetry. Operator-facing topology
  doc landed in juniper-deploy#44 (`notes/PROBE_GRAPH.md`).

**Wall-clock:** 2026-04-29 → 2026-04-30 (~2 days, against the §3 estimate of
8–12 engineer-days).

**Surprises during execution:** the **MetricsAuthMiddleware question** (R2.1
design Q3) could not be resolved at R2 close because the per-service IP
allowlist asymmetry only made sense in the context of the eventual scrape
strategy. The question carried forward to R5.2 (Q5), where it ultimately
resolved as "keep per-service, document rationale".

**Residual items closed:** R2's optional follow-up to replace the worker's two
duplicated literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) with
shared-lib imports was not pursued — duplicated literals are stable contract
values, no maintenance burden observed.

---

### Phase R3 — Test-coverage and correctness gap closure (✅ COMPLETE on 2026-05-01)

R3 drove the review plan's §10 coverage matrix to zero unjustified gaps
across all six in-scope repos, plus added a macOS leg to four CI matrices.

**Sub-track outcomes:**

- **R3.1 — live integration test for dataset-gen metric** (juniper-data#64,
  juniper-ml#181). End-to-end test through FastAPI TestClient → real
  Prometheus registry → `/metrics` scrape; pins counter +1 + histogram +1 per
  POST. **Side-effect:** surfaced R4.5 (POST cache-hit observability gap) —
  rolled into R4 as a new sub-track.
- **R3.2 — demo-mode gauge integration test** (juniper-canopy#210,
  juniper-ml#181). `juniper_canopy_demo_mode_active` wired in `main.lifespan`;
  3-test integration suite pins runtime-toggle propagation. **Production
  wiring was the load-bearing change** — the test pins it.
- **R3.3 — restore skipped `_create_metrics_panel` test** (juniper-canopy#212).
  Black-box `/dashboard/_dash-layout` test replaces the stale
  `@pytest.mark.skip` per Q2 resolution; doesn't grow public API.
- **R3.4 — Sentry tests unconditional** (juniper-ml#177). Audit closure: zero
  `importorskip("sentry_sdk")` matches across the 3 repos' test trees;
  seed-09's premise was stale. The three planned fan-out PRs collapsed into
  one juniper-ml documentation PR. (R3.4 remains the only METRICS-MON
  sub-track resolved by audit alone.)
- **R3.5 — replay-buffer overflow test** (juniper-cascor#165).
  `TestReplayBufferOverflowAtConfiguredCapacity` (3 tests at production-default
  capacity 1024).
- **R3.6 — coverage-matrix gap closure** (juniper-ml#182). 29 cells filled
  with `file:line` references (most pointing to existing R1.x / R2.x tests
  that didn't update §10 at the time); 12 cells marked GAP with rationale
  (7 SLO-deferred, 3 client-Sentry no-surface, 2 surface-deferred). The 2
  surface-deferred cells became R4.6 + R4.7.
- **R3.7 — macOS CI matrix** (juniper-cascor#166, juniper-cascor-worker#39,
  juniper-data#61, juniper-canopy#208 + post-soak juniper-cascor#168,
  juniper-cascor-worker#40, juniper-data#63, juniper-canopy#211). Each repo's
  `unit-tests` job runs a 2-D matrix `os × python-version` with
  `macos-latest` Python 3.12 added under `include:`. The 2-week soak
  (2026-05-01 → 2026-05-15) was compressed by user direction; the
  `experimental: false` flip happened same-day. **Wave 0** (fix-main-first
  prerequisite, juniper-cascor#167, juniper-canopy#209, juniper-data#62)
  restored green main on three of the four R3.7 target repos before R3.7
  could be evaluated.

**Wall-clock:** 2026-04-30 evening → 2026-05-01 evening (~36 hours, against
the entry plan's 3 working-day estimate). Compression came from the
**Wave 1 / Wave 2 parallel-PR cadence** (multiple PRs in flight
simultaneously) and from R3.4 collapsing into a doc-only audit closure.

**Surprises during execution:** four of the seven sub-tracks (R3.1, R3.2,
R3.6, R3.7) surfaced **new** observability gaps — R4.5 (POST cache-hit), R4.6
(data-client request-id), R4.7 (worker unrecognised-frame log test), and the
Wave 0 fix-main-first scope. R3.7 also surfaced that the prior R3.3 agent
**read a stale checkout** of juniper-canopy and incorrectly believed
`_create_metrics_panel` was still in production code. The lesson:
`git fetch && git checkout origin/main` before any cross-repo source grep.

**Residual items closed:** all §10 cells either pinned or carrying a
documented GAP rationale linked to a follow-up issue. The 7 SLO-deferred GAPs
all closed in R5 (their alerts now exist).

---

### Phase R4 — Best-practice and ergonomic improvements (✅ COMPLETE on 2026-05-02)

R4 closed seven sub-tracks: the four pre-planned (R4.1–R4.4) plus three
that R3 surfaced (R4.5–R4.7).

**Sub-track outcomes:**

- **R4.1 — histogram bucket rationales** (juniper-cascor#176, juniper-canopy#216,
  juniper-data#66). Per-boundary SLO rationale documented for all 6
  production histograms (cascor: 4, canopy: 1, data: 1). HELP-string marker
  "(R4.1 buckets tentative pending R5.1)" on every histogram. Two cascor
  histograms (`broadcast_send_duration_seconds`, `command_handler_seconds`)
  flagged for re-bucketing in R5.1b — currently use Prometheus default
  buckets (5 ms floor) that don't match their sub-millisecond distribution.
- **R4.2 — async-safe health probes** (juniper-canopy#215). Both canopy probe
  paths migrated from `urllib.request` + thread-pool offload to native
  `httpx.AsyncClient`. **Q2 audit** confirmed cascor + juniper-data clean —
  scope stayed canopy-only. New stress test fires 64 concurrent probes
  against a 100 ms-latency mock and asserts elapsed < 25% of serial floor.
- **R4.3 — data-client request instrumentation** (juniper-data-client#40 →
  release v0.4.1 #41 → juniper-canopy#218). Optional `on_request(method, url,
  status, duration_ms, error)` hook on `JuniperDataClient` (default no-op;
  hook exceptions swallowed + logged WARNING so instrumentation never crashes
  production). canopy provides a Prometheus-emitting closure via
  `build_data_client_request_hook()`. Two new canopy metrics keep cardinality
  bounded via the closed-set `status_class` label.
- **R4.4 — worker training-loop instrumentation** (juniper-cascor-worker#43,
  juniper-cascor#175). Heartbeat enriched with `last_task_duration_seconds`,
  `recent_task_durations_seconds` (deque(maxlen=16)), `gpu_utilization_pct`
  (best-effort via `torch.cuda.utilization()`). Cascor server companion
  accepts the new kwargs + exposes via `/v1/workers`. R1.3 additive
  compatibility preserved.
- **R4.5 — juniper-data POST cache-hit observability gap** (juniper-data#65).
  New `juniper_data_dataset_post_total{generator, status,
  cache="hit"|"miss"}` counter bumped on every POST regardless of cache state.
  Closes the R3.1-surfaced gap. Two closed-set constants prevent typo-induced
  cardinality leakage.
- **R4.6 — data-client outbound X-Request-ID propagation**
  (juniper-data-client#39, included in v0.4.1 release #41). `_request()`
  propagates `juniper_observability.request_id_var` as outbound `X-Request-ID`.
  Best-effort: ImportError + LookupError silently no-op. Caller-supplied
  headers always win. New `[observability]` extra for standalone users.
- **R4.7 — cascor-worker unrecognised-frame log emission test**
  (juniper-cascor-worker#42). Single test in
  `test_worker_agent.py::TestMessageLoopDispatch` covering the unknown-type
  branch of `_message_loop`. caplog-asserts the structured WARNING fires with
  Loki's structured-field shape.

**Wall-clock:** 2026-05-01 evening → 2026-05-02 evening (~26 hours, against
the entry plan's 2–3 working-day estimate). Compression came from the
**Wave 1 / Wave 2 / Wave 3 parallel-PR cadence** and from R4.2's audit
finding cascor + data clean (no schema-similar fan-out needed).

**Surprises during execution:** **no follow-ups surfaced for R5.x** — R4
execution did not uncover new sub-tracks (vs. R3 which surfaced
R4.5/R4.6/R4.7). The R4.1 re-bucketing flags fed directly into the R5.1b
sub-track that was already pre-planned. **Adjacent fix bundled** in
juniper-canopy#218: `test_observability.py::test_async_probe_dependency_delegates_to_shared`
was leftover from R4.2 — renamed to `test_async_probe_dependency_uses_native_httpx`
to keep main green.

**Residual items closed:** none deferred from R4 itself; the 2 cascor
re-bucket flags were always going to land in R5.1b.

---

### Phase R5 — SLO/SLI catalogue + scrape config + dashboards + alerting (✅ COMPLETE on 2026-05-03)

R5 was the production-observability deliverable. The phase closed with
**3 Wave 1 PRs in parallel + 2 Wave 2 PRs serial + 3 fixup PRs + this
program-close**.

**Sub-track outcomes:**

- **R5.1b — cascor sub-millisecond re-bucket** (juniper-cascor#185).
  `cascor_ws_broadcast_send_duration_seconds` and
  `cascor_ws_command_handler_seconds` re-bucketed per the proposed layout in
  `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`
  §4. Existing histogram tests' bucket-count assertions updated in the same
  PR. HELP-string markers flipped from "(R4.1 tentative pending R5.1)" to
  "(R5.1-ratified)".
- **R5.2 — scrape manifests + ServiceMonitor CRDs +
  MetricsAuthMiddleware rationale** (juniper-deploy#47). `prometheus.yml`
  extended to scrape cascor-worker `/v1/health` (R1.3); `k8s/helm/` gains
  ServiceMonitor CRDs for the 3 servers (Q4 (c) — both raw scrape_configs and
  ServiceMonitor); per-service MetricsAuthMiddleware asymmetry rationale doc
  shipped at `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (Q5 (b) —
  closes the gating question carried since 2026-04-28).
- **R5.3 — Grafana dashboard refresh** (juniper-deploy#46). Single PR
  touching all 4 dashboards: `juniper-canopy.json` gains the R4.3 data-client
  closure metrics panels; `juniper-cascor.json` gains R4.4 worker
  training-loop fields panels; `juniper-data.json` gains the R4.5 POST
  cache-hit panel; `juniper-overview.json` gains an SLO burn-rate headline
  tile keyed off the R5.4 alert expressions.
- **R5.1 — SLO catalogue** (juniper-deploy#48). New
  `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md`: 5 user-facing primary
  SLIs (canopy dashboard availability + render latency, cascor train-job
  success + train-step p95, juniper-data POST availability) + 8
  internal-supporting SLIs (worker heartbeat freshness, queue depth
  saturation, cascor broadcast fan-out, etc.). Every SLO references the
  metric, label set, rolling window, target, and the alert that fires on
  breach. Targets marked **"initial — to revisit after 30-day soak"**.
- **R5.4 — burn-rate alerts** (juniper-deploy#50). MWMBR (multi-window
  multi-burn-rate) alert pattern: page on (1h × 14.4 burn AND 6h × 6 burn),
  ticket on (6h × 6 AND 24h × 3). Existing `juniper_service_health` group
  preserved threshold-based; `juniper_error_rates` and new latency/availability
  alerts moved to burn-rate keyed off R5.1 SLO targets.

**R5.4-pre / Wave 2 sub-track:** **juniper-cascor#188** added the cascor-side
training counters (`juniper_cascor_training_sessions_completed_total{status}`,
`juniper_cascor_training_step_duration_seconds{phase}`) and a worker→Prometheus
metrics bridge — the metrics R5.4's burn-rate alerts measure against. This
sub-track surfaced as **R5.4-pre** during R5.4 implementation (the burn-rate
alerts couldn't fire without the underlying counters existing).

**Three Wave 2 fixup PRs after R5.1/R5.4 review** (juniper-deploy#49,
juniper-deploy#51): SLI 3.4 rename to "train-epoch p95" (granularity
acknowledgement), SLO catalog §3.3 label-set re-align (`outcome` →
`status` to match as-shipped), throttle-comment line-number correction,
alertmanager `tickets` receiver added (with placeholder note).

**Wall-clock:** 2026-05-02 evening → 2026-05-03 evening (~24 hours, against
the entry plan's 1.5–2 working-day estimate).

**Surprises during execution:** see §5 — three notable ones:

1. **TRAIN-ARCH-01 — cascor is full-batch end-to-end.** R5.4-pre's
   investigating agent discovered cascor has no mini-batch loop anywhere
   outside test code; the trainer's finest-grained natural step is one full
   epoch. This reframed "mini-batch instrumentation" from a missing-hook
   problem to a structural absence. User explicitly deferred restoration at
   the design-doc stage (juniper-cascor#194 OPEN).
2. **SLI 3.4 granularity rename.** Once R5.4 was in flight, the catalog's
   "train-step p95" SLI was renamed to "train-epoch p95" because the histogram
   measures per-callback, which under the 25-epoch throttle equals
   per-25-epochs at worst. Mini-batch design doc (juniper-ml#189) captures
   the eventual fix path.
3. **Catalog §3.3 label drift.** PR #50 (alerts) used the as-shipped
   `status ∈ {success, failure, cancelled}` label set; the catalog had been
   drafted with an earlier `outcome ∈ {success, error, aborted}` plan. Fixup
   PR #51 brought the catalog into alignment with the metric.

**Residual items closed:** TRAIN-ARCH-01 explicitly deferred at user
discretion; the 25-epoch throttle removal (R5.6) explicitly carved out as a
future small sub-track; alertmanager `tickets` receiver placeholder
acknowledged in PR #51 with explicit "MUST be wired before production use"
note.

---

## 3. Cross-cutting outcomes

### 3.1 Total metrics shipped (count by service)

| Service | Counters | Histograms | Gauges | Total |
|---|:---:|:---:|:---:|:---:|
| juniper-cascor | 7 | 4 | 2 | 13 |
| juniper-canopy | 5 | 1 | 3 | 9 |
| juniper-data | 5 | 1 | 1 | 7 |
| juniper-cascor-worker | 1 (unrecognised-frame log gauge via heartbeat) | 0 | 3 (heartbeat fields) | 4 |
| juniper-data-client | 0 (hook-only; canopy emits) | 0 | 0 | 0 |
| **TOTAL** | **18** | **6** | **9** | **33** |

(Counts include the R4.5 POST cache-hit counter, the R5.4-pre training
counters, the R2.2 unrecognised-frames counter, the R1.1 `_unmatched`
counter, and every R4.4 heartbeat field surfaced via cascor's `/v1/workers`.)

### 3.2 Cardinality discipline outcome

**Every closed-set label across all 33 metrics is enforced by either an enum,
a literal-string constant, or a defensive `_unmatched` bucket.** No drift
caught during the program — the R1.1 stress tests catch attacker-controlled
cardinality at PR-time, and the R4.5 closed-set constants prevent
typo-induced cardinality leakage. The `endpoint` label across all 3 servers'
`http_requests_total` is bounded to the resolved route template plus a
single `_unmatched` bucket; the `type` label on `unrecognized_ws_frames_total`
is bounded by R1.1's strategy.

### 3.3 Test-coverage matrix: pre-program vs post-program

| Coverage state | Pre-program (review plan §10, 2026-04-25) | Post-program (R3.6 sweep, 2026-05-01) |
|---|:---:|:---:|
| Cells with file:line reference | 0 | 33 |
| Cells with documented GAP rationale | 0 | 12 |
| Cells empty (unjustified gap) | 41 | **0** |

All 12 GAP cells were closed during R4 (R4.5/R4.6/R4.7) or R5 (the 7
SLO-deferred GAPs). Three client-Sentry no-surface GAPs remain documented as
**accepted gaps** — clients legitimately have no Sentry surface to test.

### 3.4 Shared-lib adoption

**`juniper-observability==0.1.1` consumers (3):** juniper-data, juniper-cascor,
juniper-canopy. Each uses every public symbol the lib exposes (exception:
juniper-data uses MetricsAuthMiddleware; the other two don't, by Q5
resolution). juniper-cascor-worker explicitly off (Q1 R2 exit-gate decision).

**`juniper-cascor-protocol==0.1.0` consumers (4):** juniper-cascor (server,
which is the **first consumer of its own protocol package** so the producer
can never drift from the schema), juniper-cascor-client, juniper-canopy,
juniper-cascor-worker. The worker imports only `WorkerMessageType` +
`BinaryFrame.encode` (no Pydantic in worker runtime — preserves the R2 exit
gate's no-pydantic-at-runtime invariant).

### 3.5 WS frame-schema alignment outcome

Every consumer-side WS frame now passes through declarative validation:
cascor-client + canopy use Pydantic v2 envelopes; the worker uses the shared
StrEnum + numpy codec. A server-side schema regression surfaces as a
structured log + counter event instead of a downstream `KeyError`. **The
cascor server is the first consumer of its own protocol package** — the
producer cannot drift from the schema without breaking its own startup.

---

## 4. Production posture

What an SRE / ops engineer should now know:

### 4.1 SLO catalogue

**Location:** `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (juniper-deploy
repo, juniper-deploy#48 + fixup #49 + #51).

**Contents:**

- **5 user-facing primary SLIs** (release-blocking; alert on burn-rate):
  - 1.1 — canopy dashboard availability
  - 1.2 — canopy `/dashboard/_dash-layout` render latency p95
  - 3.3 — cascor train-job success ratio (`status ∈ {success, failure,
    cancelled}`)
  - 3.4 — cascor **train-epoch** p95 (renamed from train-step in fixup #49;
    granularity acknowledgement; mini-batch follow-up tracked separately)
  - 5.x — juniper-data POST availability
- **8 internal-supporting SLIs** (graphed only; route to log-only severity):
  worker heartbeat freshness, queue depth saturation, cascor broadcast
  fan-out, cascor command_handler latency, juniper-data POST cache-hit ratio,
  juniper-canopy data-client error rate, juniper-cascor unrecognised-frames
  rate, juniper-data dataset access tally.

**Targets:** all marked **"initial — to revisit after 30-day soak"**. Do
**NOT** trip alerts on first 30 days (see §4.5).

### 4.2 Burn-rate alerts

**Location:** `juniper-deploy/prometheus/alert_rules.yml` (juniper-deploy#50
+ fixup #51).

**Severity levels (Google SRE Workbook MWMBR convention):**

- `severity: page` — 1h × 14.4 burn AND 6h × 6 burn (fast-burn). Routes to
  the existing `critical` receiver.
- `severity: ticket` — 6h × 6 AND 24h × 3 (slow-burn). Routes to a **new
  `tickets` receiver** (placeholder — see §6).
- `severity: critical` — preserved for `juniper_service_health` (threshold
  `ServiceDown` / `ServiceRestartLoop`).

**Alertmanager routing status:** `severity: page` → wired to existing
`critical` receiver (10s `group_wait`, 1h `repeat_interval`).
`severity: ticket` → new `tickets` receiver, **silently drops alerts** until
real notification config (Slack low-priority / Jira webhook / email) is added
— follow-up tracked in §6.

### 4.3 Dashboards

**Location:** `juniper-deploy/grafana/provisioning/dashboards/*.json`
(juniper-deploy#46).

**Coverage:**

- `juniper-overview.json` — 4 SLO burn-rate headline tiles + per-service
  health summary.
- `juniper-canopy.json` — adds R4.3 data-client closure metrics panels
  (`juniper_canopy_data_client_requests_total{method, status_class,
  error_type}` + duration histogram).
- `juniper-cascor.json` — adds R4.4 worker training-loop fields panels
  (`last_task_duration_seconds`, `recent_task_durations_seconds`,
  `gpu_utilization_pct`).
- `juniper-data.json` — adds R4.5 POST cache-hit panel
  (`juniper_data_dataset_post_total{cache="hit"|"miss"}`).

**Format:** JSON-committed (Q6 (a)). No jsonnet build.

### 4.4 Scrape configs

**Raw scrape_configs:** `juniper-deploy/prometheus/prometheus.yml`. Covers
every R1–R5 metric across the 3 servers + cascor-worker `/v1/health` (added
in #47).

**ServiceMonitor CRDs:** `juniper-deploy/k8s/helm/<service>/templates/`
(per-service). Covers the 3 servers; targets parameterised via the existing
helm chart values. (Worker scrape via cascor's `/v1/workers` aggregation — no
direct scrape because workers are dynamic.)

**MetricsAuthMiddleware asymmetry:**
`juniper-deploy/notes/METRICS_AUTH_RATIONALE.md`. juniper-data has SEC-16 IP
allowlist (sensitive surface); cascor + canopy do not. Production scrape uses
ServiceMonitor with k8s NetworkPolicy for access control.

### 4.5 30-day soak window

**Window:** **2026-05-03 → 2026-06-02**.

**During soak:**

- All `severity: ticket` alerts route to the placeholder `tickets` receiver
  (silently dropped). Ack the noise.
- All `severity: page` alerts go straight to on-call; do **NOT** disable
  paging during soak — the 30-day window is for SLO-target calibration, not
  for ignoring legitimate breaches.
- After 30 days: re-validate SLO targets in `SLO_CATALOG_2026-05-03.md`
  against actual traffic; tighten/loosen as data warrants. Wire the
  `tickets` receiver before the soak closes.

---

## 5. Surprises and learnings

This section records the prose-level findings that don't fit into the
per-phase recaps. Honest accounting; if a finding looked one way going in
and another way coming out, both shapes are recorded.

### 5.1 Wave 2 surprises — cascor full-batch + correlation-step

R5.4-pre's investigating agent surfaced **two structural surprises** during
the cascor training counters work:

1. **Cascor is full-batch end-to-end.** No `DataLoader`, no `TensorDataset`,
   no inner `for batch in dataloader:` loop anywhere outside test code. The
   output-layer loop (`cascade_correlation.py:1638`) and the candidate-unit
   loop (`candidate_unit.py:564`) both run `for epoch in range(epochs):` with
   one full-batch forward + backward + optimiser step per epoch.
2. **The 25-epoch throttle.** The lifecycle callback fires only on
   `epoch % 25 == 0 or epoch == epochs - 1` (line 1655), so the R5.4-pre
   histogram observes per-25-epochs at worst, not per-epoch.

**Reframing impact on the program:**

- The originally-implied "mini-batch instrumentation" sub-track became
  ABSENCE recovery, not regression repair. cascor *had* no mini-batch
  instrumentation because cascor *has* no mini-batches.
- SLI 3.4 was renamed from "train-step p95" to "train-epoch p95" (fixup
  juniper-deploy#49) to reflect the actual measurement granularity.
- The catalog §3.3 label-set drift between as-designed (`outcome ∈
  {success, error, aborted}`) and as-shipped (`status ∈ {success, failure,
  cancelled}`) was caught during the same fixup window — PR #50 (alerts) had
  already used the as-shipped names; the catalog text was the laggard.

The mini-batch design doc (juniper-ml#189, merged 2026-05-03) captures the
eventual restoration path. **User explicitly deferred** at the design-doc
stage; juniper-cascor#194 (TRAIN-ARCH-01) remains OPEN under user review as
the implementation companion.

### 5.2 The TRAIN-ARCH-01 finding — absence vs regression

The most material finding of the program. The investigation that surfaced
the full-batch reality was triggered by R5.4-pre's per-epoch histogram
observation; the agent of record went looking for the missing per-step hook
and instead found there was nothing to hook into. **This is documented
honestly because:**

- Future readers of the program close note will assume mini-batch
  instrumentation was deferred for *capacity* reasons. It was deferred
  because the architectural pre-condition (a mini-batch loop) does not
  exist.
- The user's explicit deferral at the design-doc stage is a feature, not a
  failure. The design doc surfaces options (full mini-batch loop, hybrid
  sub-batch annotation, pure-throttle removal) and the user chose to defer
  pending future research-side decisions about whether mini-batched cascor
  is even desirable.
- TRAIN-ARCH-01 is **NON-BLOCKER for production** — the per-epoch histogram
  is operationally usable, R5.4 alerts fire correctly against the renamed
  SLI 3.4, and the 25-epoch throttle's burn-rate fidelity loss is acceptable
  during the 30-day soak.

### 5.3 Cross-repo orchestration learnings

Three patterns earned their keep across the program:

- **The canopy stub-exception conftest pattern** (R3.2, R4.2, R4.3) — when
  test-time imports of optional dependencies (httpx, prometheus_client) are
  fragile under conda-env permutations, hoist the stub-or-real decision to
  the conftest. canopy's `test_observability.py` shows the pattern.
- **The R5.3 stale-checkout false-positive** (caught during R3.7's review
  of the prior R3.3 agent's claims) taught us to **always
  `git fetch origin && git checkout origin/main`** before grep'ing source
  repos for "does this code still exist?" This propagated into the
  agent-spawn instructions for the R5 phase.
- **Wave 0 fix-main-first prerequisite.** R3.7 surfaced that **3 of the 4
  target repos' main branches were red** before the metrics-mon work could
  be evaluated. The Wave 0 PRs (juniper-cascor#167, juniper-canopy#209,
  juniper-data#62) restored green main as a strict prerequisite for R3.7's
  evaluation. Lesson: any cross-repo program should start with a "main is
  green on every target repo" check before scheduling sub-track work.

### 5.4 Compression vs estimate

Phases consistently shipped under estimate due to the **wave-based
parallel-PR cadence**:

| Phase | §3 estimate | Actual wall-clock | Compression |
|---|---|---|---|
| R1 | 6–9 eng-days | ~3 days | 3× |
| R2 | 8–12 eng-days | ~2 days | 5× |
| R3 | 5–7 eng-days | ~36 hours | 3.5× |
| R4 | 4–6 eng-days | ~26 hours | 4× |
| R5 | 3–5 eng-days | ~24 hours | 3.5× |

The compression is **not** a claim that the original estimates were wrong —
they were sequential-execution estimates. Wave-based execution (3+ PRs
landing in the same hour against different repos) compresses wall-clock
without compressing engineer-effort. The cadence depends on the worktree
workflow scaling cleanly; see §5.5.

### 5.5 Worktree workflow validation

The centralised `worktrees/` pattern + agent-spawned worktrees scaled
cleanly **even when 3 sub-tracks ran in parallel against the same repo**
(juniper-canopy during R4: #215 + #216 + #218 in flight simultaneously
against three feature branches). No CWD-trap incidents post-V2 cleanup
procedure. No stale worktree accumulation — every closed sub-track cleaned
up its worktree on merge.

The only operational friction was when an agent's cwd reset between bash
calls; that resolved once agent prompts standardised on absolute paths.

---

## 6. Residual follow-ups

Carrying forward into post-METRICS-MON work. Each item: name, owner repo,
blocker/non-blocker, recommended action.

| ID | Owner repo | Blocker? | Item |
|---|---|---|---|
| **TRAIN-ARCH-01** | juniper-cascor | NON-BLOCKER | Mini-batch restoration. Design doc juniper-cascor#194 OPEN under user review; user explicitly deferred at design-doc stage. Recommended action: keep design doc OPEN until research-side decision on whether mini-batched cascor is desirable; if yes, schedule as a future METRICS-MON-N sub-track. Companion: juniper-ml#189 mini-batch instrumentation design doc (merged). |
| **R5.6 throttle removal** | juniper-cascor | NON-BLOCKER | `cascade_correlation.py:1655` 25-epoch emit throttle reduces R5.4 burn-rate fidelity for SLO 3.4. Small future sub-track (single-line gate change + test updates for the histogram count assertions). Coupled to TRAIN-ARCH-01 only loosely — could ship independently. |
| **alertmanager `tickets` receiver** | juniper-deploy | **SOFT-BLOCKER** before production | Placeholder added in juniper-deploy#51; needs real notification config (webhook/email/slack URL) before SLO 3.3/3.4 ticket-severity alerts come off log-only. **MUST be wired** before the 30-day soak closes. Recommended action: a single 5–10 line PR setting the receiver's `webhook_configs` or `slack_configs`. |
| **`amtool check-config` validation** | juniper-deploy | NON-BLOCKER | Local validation blocked by snap confinement on the dev host (`amtool` snap can't read the alertmanager config in the project tree). PR #51 documented the container-based fallback. Recommended action: incorporate the container-based check into CI (or accept the local-dev-only gap). |
| **`juniper_cascor_pending_tasks` worker bridge gap** | juniper-cascor | NON-BLOCKER | Alert rule shipped guarded by `absent_over_time(...) == 0`, harmlessly inert until the worker→Prometheus bridge ships the metric. The metric is in juniper-cascor#188's bridge but the worker side hasn't surfaced `pending_tasks` yet. Future small sub-track (~1 PR). |
| **R1.3.4 chart flag-flip** | juniper-deploy | NON-BLOCKER | Bump `worker.healthcheck.enabled` default to `true`, chart 1.1.0 → 1.2.0, after staging confirms worker image ≥ 0.4.0 stable in production-shaped traffic. Carried forward from R1 and never closed (deferred for burn-in). |
| **R2 worker contract-constant dedup** | juniper-cascor-worker | NON-BLOCKER | Optional follow-up from R2 exit-gate decision: replace the worker's two duplicated literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) with shared-lib imports under a ≤ 10-line PR. Stable contract values; no observed maintenance burden. Decline if no maintenance pressure surfaces. |
| **30-day soak SLO target calibration** | juniper-deploy | NON-BLOCKER | All SLO targets in `SLO_CATALOG_2026-05-03.md` marked "initial — to revisit after 30-day soak". Window 2026-05-03 → 2026-06-02. Recommended action: a single PR at soak close updating §3.x target columns + a brief retrospective note. |

**No deferred items are program-blocking.** The two soft-blockers (alertmanager
`tickets` receiver wiring, SLO target re-calibration) are time-bound to the
30-day soak window and should both close before 2026-06-02.

---

## 7. Final program scoreboard

| Phase | Sub-tracks | PRs merged | Wall-clock | Estimate | Outcome |
|---|:---:|:---:|---|---|---|
| R1 | 3 (R1.1, R1.2, R1.3) | 13 | 2026-04-26 → 2026-04-28 (~3 d) | 6–9 eng-d | ✅ |
| R2 | 4 (R2.1, R2.2, R2.3, exit-gate) | 17 | 2026-04-29 → 2026-04-30 (~2 d) | 8–12 eng-d | ✅ |
| R3 | 7 (R3.1–R3.7) + Wave 0 | 18 | 2026-04-30 → 2026-05-01 (~36 h) | 5–7 eng-d | ✅ |
| R4 | 7 (R4.1–R4.7) | 13 | 2026-05-01 → 2026-05-02 (~26 h) | 4–6 eng-d | ✅ |
| R5 | 5 (R5.1, R5.1b, R5.2, R5.3, R5.4) + R5.4-pre + 3 fixups | 11 | 2026-05-02 → 2026-05-03 (~24 h) | 3–5 eng-d | ✅ |
| Program docs (entry plans, designs, close notes, roadmap updates) | n/a | 6 | spread across phases | n/a | ✅ |
| **TOTAL** | **26 sub-tracks + 4 fixup/Wave-0 batches** | **78** | **9 calendar days** | **26–39 eng-d (sequential)** | **✅** |

**Per-repo PR breakdown:**

| Repo | PRs |
|---|:---:|
| juniper-ml (docs) | 21 |
| juniper-cascor | 16 |
| juniper-canopy | 13 |
| juniper-deploy | 9 |
| juniper-data | 9 |
| juniper-cascor-worker | 6 |
| juniper-data-client | 3 |
| juniper-cascor-client | 1 |
| **TOTAL** | **78** |

(juniper-data-client #41 is the v0.4.1 release-cut PR bundling R4.3 + R4.6;
juniper-cascor #167, juniper-canopy #209, juniper-data #62 are Wave 0
fix-main-first prerequisites; juniper-cascor #168, juniper-cascor-worker #40,
juniper-data #63, juniper-canopy #211 are the post-soak macOS leg flag-flips
to `experimental: false`.)

**5–7 most material PRs (anchors for future readers):**

- **juniper-ml#155** — `juniper-observability` package alpha (R2.1.1).
  Foundational extraction; every subsequent shared-lib improvement rides on
  this PR.
- **juniper-cascor#156** — `juniper-cascor-protocol` package alpha (R2.2.1).
  WS schema unification across 4 repos.
- **juniper-cascor#143** / **juniper-canopy#178** / **juniper-data#49**
  (R1.1 cardinality bound). The 3-PR fan-out that established the
  cardinality-discipline pattern reused throughout.
- **juniper-deploy#48** — SLO catalogue (R5.1). Single source of truth for
  every alert and dashboard panel that ships afterward.
- **juniper-deploy#50** — burn-rate alerts (R5.4). Operationally
  load-bearing; on-call now reads alerts from this file.
- **juniper-cascor#188** — R5.4-pre training counters + worker→Prometheus
  bridge. Surfaced TRAIN-ARCH-01 during implementation.
- **juniper-cascor-worker#43** — R4.4 worker heartbeat enrichment. The
  largest single contribution to operational visibility into training-time
  worker health.
- **juniper-deploy#51** — operational predecessor to this close PR; closes
  the 3 R5.4 fixup follow-ups (label re-align, throttle comment, alertmanager
  routing).

---

## 8. Acknowledgements

The program ran as a single-author effort over 9 days with extensive
agent-assisted execution. Two patterns earned the bulk of the productivity
win:

- **Per-phase entry plans before any implementation.** Each of R3, R4, R5
  resolved 5–8 open questions in a written entry plan PR before the first
  implementation PR opened. This converted runtime debate into pre-flight
  decisions and is the single biggest contributor to the wall-clock
  compression.
- **Wave-based parallel PR cadence.** Multiple PRs in flight against
  different repos (and occasionally against the same repo) was the standard
  mode of execution. The centralised worktrees + V2 cleanup procedure made
  this safe; no CWD-trap incidents and no stale worktree accumulation.

What did not earn its keep: pre-flight estimates of engineer-days for
sequentially-executed work — a useful sanity-check upper bound but not a
useful planning anchor for the wave-based cadence that actually shipped.

The METRICS-MON program closes here. Subsequent observability work — the
30-day soak calibration, mini-batch restoration if pursued, the
`tickets` receiver wiring, throttle removal — moves to a new program or to
ad-hoc follow-up PRs.
