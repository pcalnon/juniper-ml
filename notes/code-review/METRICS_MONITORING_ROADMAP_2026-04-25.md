# Juniper Metrics & Monitoring — Development Roadmap

> **STATUS: PROGRAM CLOSED 2026-05-03 — see [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) for closure summary.**
> All five phases R1–R5 ✅ COMPLETE. 78 PRs across 8 repos in 9 calendar days. Residuals carried forward (TRAIN-ARCH-01, alertmanager `tickets` receiver, R5.6 throttle removal, 30-day soak calibration) tracked in the close note §6.

**Status:** ✅ CLOSED 2026-05-03 (was: PROPOSED)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-25
**Scope:** Metrics, monitoring, observability, telemetry, health surface
**Repos in scope (6):** juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client
**Companion documents:**

- [METRICS_MONITORING_ANALYSIS_2026-04-25.md](METRICS_MONITORING_ANALYSIS_2026-04-25.md) — current-state baseline
- [METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) — review methodology

---

## 1. Purpose

This roadmap turns the review's **findings** (METRICS-MON-NNN) into a **prioritized, sequenced, owner-attributable** body of work. The roadmap is consumed by the implementation phase that follows the review; it is not the review itself.

The roadmap exists so that, once the review is signed off, work can be picked up in order without re-arguing priority, scope, or sequencing.

---

## 2. Sequencing principles

1. **Composite severity first.** Composite ≥ 4 findings (per §4 of the review plan) are release-blocking and lead the queue.
2. **Architectural before logical before cosmetic.** When two findings have equal severity, the architectural one ships first to prevent rework.
3. **Cross-repo before single-repo.** Shared remediations that eliminate duplicated bugs ship before single-repo fixes that would otherwise drift.
4. **Upstream before downstream.** Cascor (server) before cascor-client/worker (consumers); data before data-client; canopy is consumer-side and ships last in any cluster it depends on.
5. **Tests pinned to the same PR.** No fix merges without the test that prevents regression.
6. **Each phase ends green.** Every repo's full test suite passes between phases.

---

## 3. Phase overview

| Phase | Title                                                       | Composite severity served | Effort (eng-days, est.) | Repo blast radius                           |
|-------|-------------------------------------------------------------|:-------------------------:|:-----------------------:|---------------------------------------------|
| R1    | Release-blocking fixes                                      | 4–5                       | 6–9                     | cascor, canopy, data, worker                |
| R2    | Cross-repo unification (architectural)                      | 3–4                       | 8–12                    | cross-repo + new shared lib                 |
| R3    | Test-coverage and correctness gap closure                   | 3                         | 5–7                     | all six                                     |
| R4    | Best-practice and ergonomic improvements                    | 2                         | 4–6                     | all six                                     |
| R5    | Observability for SLOs, scrape config, dashboards           | 2–3                       | 3–5                     | juniper-deploy + per-repo metric definitions|

Total estimate: **26–39 engineer-days** if executed sequentially. R3 and R4 have parallel sub-tasks that can compress wall-clock time.

---

## 4. Phase R1 — Release-blocking fixes

**Trigger:** Phase 7 of the review plan completes.
**Exit:** All composite ≥ 4 findings closed; all in-scope test suites pass; PRs merged to main.

### R1.1 Bound Prometheus middleware cardinality (seed-01)

**Repos:** cascor, canopy, data
**Composite:** 4
**Approach (recommended after Phase 5 design):** Restrict the `endpoint` label to the resolved `route.path` template; under unmatched routes, emit a single bucket `"_unmatched"` and increment a separate counter `juniper_<svc>_http_unmatched_requests_total`. Reject any non-template fallback path.
**Worktrees:** one per repo.
**Tests:** Cardinality stress test sending requests with high-entropy path params; assert label set never exceeds N buckets.

### R1.2 Health probe semantics + status-code propagation (seed-02, seed-03)

**Repos:** cascor, canopy, data
**Composite:** 4
**Approach:** `/health/ready` returns 503 when any dependency is `unhealthy` and 200 with `Status: degraded` only when partial degradation is documented as acceptable. Liveness probes must exercise a real code path (e.g., dataset cache read for data, training-loop tick check for cascor, dashboard render hook for canopy) within a strict timeout; on timeout return 503.
**Coordination:** Helm chart probe wiring in juniper-deploy may need updating in lockstep.
**Tests:** Probe contract tests with simulated dependency failures; integration test that LB withdraws traffic on degraded.

### R1.3 Worker liveness + heartbeat (seed-04)

**Repo:** cascor-worker
**Composite:** 4
**Approach:** Add a minimal HTTP server (or expose health over the existing WS connection as a `worker_heartbeat` frame) emitting `worker_id`, `in_flight_tasks`, `last_task_completed_at`, `rss_mb`. Cascor records the heartbeat; `/v1/workers` route exposes it. Reaper marks worker dead if heartbeat older than threshold.
**Coordination:** Cascor-side route additions; cascor-client may surface worker liveness in CLI.
**Tests:** Worker heartbeat emission unit test; cascor-side staleness-detection test; integration test with simulated worker death (SIGSTOP).

**Phase R1 exit gate:** All four R1 work-items merged. Full test suites green per repo. Roadmap §6 status table reflects R1 = complete.

---

## 5. Phase R2 — Cross-repo unification

### R2.1 Shared `DependencyStatus` / `ReadinessResponse` library (seed-06)

**Composite:** 3
**Approach (recommended):** Promote the duplicated models into a new package `juniper-observability` published from juniper-ml's repo (or as a new sibling repo if owners prefer). Pin from cascor, canopy, data. Eliminate three copies; future changes happen in one place.
**Trade-off:** Adds a new package and dependency edge; pre-empts drift cost.
**Sequencing:** Ship the new package first (PyPI alpha), then migrate consumers in dependency order: data → cascor → canopy.
**Tests:** Per-repo regression test that the migrated model is wire-compatible with the previous shape (`pydantic.BaseModel.model_dump()` snapshot equality).

### R2.2 WS frame schema validation in consumers (seed-05)

**Repos:** cascor-client, cascor-worker
**Composite:** 3
**Approach:** Cascor exposes its WS payload schemas as Pydantic models in a shared module; clients import and validate every inbound frame. Unrecognized frame types log + emit a `juniper_<svc>_unrecognized_ws_frames_total` counter (clients gain minimal observability surface here as a side effect of seed-05).
**Sequencing:** Schema export from cascor first (re-uses R2.1's shared lib if available), then consumer adoption.
**Tests:** Round-trip test: cascor emit → client validate → assert no errors; chaos test sends malformed frames and asserts they are rejected without crashing the consumer.

**Design (2026-04-29):** Open questions resolved in [`METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md`](METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md). Headlines: schemas live in a **new `juniper-cascor-protocol` package** (subdirectory of juniper-cascor; mirrors the R2.1 publish pattern), **not** in `juniper-observability` (keeps observability lib focused on cross-service infra; service-specific protocol shape belongs with the service). Worker imports only `WorkerMessageType` + `BinaryFrame` (no Pydantic in worker runtime — preserves the [R2 exit-gate decision](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md)); cascor-client + canopy fully validate every inbound frame against Pydantic v2 envelopes. Unrecognized frame counter (`juniper_<svc>_unrecognized_ws_frames_total{type, endpoint}`) on the JSON-envelope consumers, structured-log line on the worker (no Prometheus dep added). 7-PR sequence (alpha → server adopt → stable → 3× consumer adopt → roadmap close).

**Resolution (2026-04-30):** ✅ **Done.** All 7 PRs in the R2.2 sequence have shipped: juniper-cascor#156 (R2.2.1 alpha source), tag `juniper-cascor-protocol-v0.1.0a0` published 2026-04-29, juniper-cascor#159 (R2.2.2 server adopt), juniper-cascor#160 (R2.2.3 promote to `0.1.0` stable), tag `juniper-cascor-protocol-v0.1.0` published 2026-04-30, juniper-cascor-client#29 (R2.2.4 client validates with `[observability]` extra + R1.1-bounded counter + chaos test), juniper-canopy#206 (R2.2.5 canopy validates with own `juniper_canopy_*` counter), juniper-cascor-worker#38 (R2.2.6 worker single-sources enum + encode codec; structured log line; 6 subprocess-isolated tests pinning the no-pydantic-at-runtime invariant; SEC-18-hardened decoder kept local). The cascor server is the **first consumer of its own protocol package** so the producer cannot drift from the schema. **Outcome**: every consumer-side WS frame now passes through declarative validation (cascor-client + canopy use Pydantic, worker uses the shared StrEnum + numpy codec); a server-side schema regression surfaces as a structured log + counter event instead of a downstream KeyError; cardinality is bounded under attacker-controlled types via the R1.1 strategy.

### R2.3 Probe-direction symmetry (seed-15)

**Composite:** 2 (lifted to 3 if R1.2 reveals deeper issues)
**Approach:** All servers probe their declared upstream dependencies at health-ready time. Cascor probes data; data probes nothing (it is a leaf); canopy probes both. Document the probe graph in `juniper-deploy/notes/`.
**Tests:** Per-repo readiness test that injects a "down" upstream and asserts readiness reflects it.

**Resolution (2026-04-29):** ✅ **Done.** Probes already in place from R1.2 (cascor probes data; juniper-canopy#183) + R2.1 migrations (data leaf with storage probe; canopy probes both via shared lib). The remaining gap was canopy's missing regression test for upstream-down injection — closed in juniper-canopy#202 (4 new tests in `TestReadinessDownstreamInjection`, including an explicit `test_canopy_never_returns_503_on_upstream_down` regression guard pinning the deliberate cascor-503 / canopy-degraded severity asymmetry). Operator-facing topology + severity policy doc landed in juniper-deploy#44 (`notes/PROBE_GRAPH.md`).

**Phase R2 exit gate:** Shared lib published; probes symmetric; WS frames validated in clients/workers; all suites green.

**Phase R2 status (2026-04-30): ✅ COMPLETE.** All four sub-tracks have shipped:

- ✅ **R2.1** shared `juniper-observability` lib (5 PRs; data + cascor + canopy migrated; tz-aware UTC `ReadinessResponse.timestamp` + SEC-15 `before_send` hook now cross-service standards)
- ✅ **R2 exit-gate worker-adoption decision** (juniper-ml#168 — worker stays off the shared observability lib; selective adoption of contract constants left as optional follow-up)
- ✅ **R2.3** probe-direction symmetry (cascor / data / canopy / worker all probe their declared upstreams; cascor-503 vs canopy-degraded severity asymmetry documented in juniper-deploy#44 `notes/PROBE_GRAPH.md`)
- ✅ **R2.2** WS frame schema validation (7 PRs; new `juniper-cascor-protocol` package; cascor-client + canopy validate every inbound frame via Pydantic v2 envelopes; worker single-sources `WorkerMessageType` + `BinaryFrame.encode` while staying Pydantic-free at runtime; R1.1-bounded `juniper_<svc>_unrecognized_ws_frames_total` counter on JSON-envelope consumers; structured log line on the worker)

The METRICS-MON program now turns to **Phase R3** (test-coverage gap closure) and **Phase R4** (best-practice / instrumentation). **Phase R5** (SLO/SLI definition, scrape config, dashboards) remains gated on R3.

**Phase R2 gating issue (raised 2026-04-28 from R2.1 design Q5):** Before declaring R2 complete, evaluate whether **`juniper-cascor-worker` should adopt the shared `juniper-observability` lib** (currently the worker's `http_health.py` uses no FastAPI/Starlette to keep the image slim). Decision criteria: (a) is Starlette's transitive footprint acceptable in the worker container? (b) does the worker stand to benefit from the shared `RequestIdMiddleware` / `JuniperJsonFormatter` consistency? (c) would adopting the lib simplify any cross-cutting bug fixes that have already had to land twice (worker + servers)? Document the decision in a follow-up note in `notes/code-review/`.

**Resolution (2026-04-29):** ✅ Decided — **do not migrate now**. Worker uses 2 of the lib's 20 public symbols (both contract constants); the other 18 are HTTP-server machinery the worker structurally does not need (no FastAPI app, no `/metrics` mount, no Sentry, no upstream deps to probe, no incoming HTTP business flow). None of the R2.1 cross-cutting fixes (BUG-JD-06 tz-aware timestamp, SEC-15 Sentry hook, R1.1 cardinality bound) required a parallel worker patch. Re-evaluation triggers documented for the future. Optional follow-up: replace the two duplicated literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) with shared-lib imports under a separate ≤ 10-line PR. Full analysis: [`METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md`](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md).

---

## 6. Phase R3 — Test-coverage and correctness gap closure

**Entry plan (2026-04-30):** Open questions resolved in [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md). Headline decisions: **Q1** (R3.7) macOS leg uses `macos-latest` (ARM) with `continue-on-error: true` initial guard for 2 weeks; full unit coverage on macOS, no integration/perf/e2e on the new leg. **Q2** (R3.3) restore via **black-box dashboard layout test**, not by promoting `_create_metrics_panel` to the public API. **Q3** (R3.4) remove `importorskip("sentry_sdk")` — `sentry-sdk` is already a hard runtime dep on every server, so this only changes test installs. **Q4** (R3.6) coverage-matrix population folded into the per-track PRs (each closes its own row); residual GAPs closed in a single juniper-ml sweep PR after R3.1–R3.5 + R3.7 land. **Q5** (sequencing) **Wave 1 (parallelizable, 11 PRs)** → R3.1, R3.2, R3.3, R3.5 (single-repo) plus R3.4×3 (cascor + canopy + data) plus R3.7×4 (cascor + worker + data + canopy). **Wave 2 (gated)** → R3.6 sweep + roadmap close. ~3 working days end-to-end at the prior cadence.


### R3.1 Live integration test for dataset-gen metric (seed-08, BUG-JD-07)

**Repo:** juniper-data
**Composite:** 3
**Tests required:** End-to-end test that POSTs `/v1/datasets`, scrapes `/metrics`, asserts `juniper_data_dataset_generations_total{generator="<X>",status="success"}` incremented by 1 and the duration histogram observed exactly one sample.

### R3.2 Demo-mode gauge integration test (seed-11)

**Repo:** juniper-canopy
**Composite:** 2
**Tests required:** Integration test toggling demo mode and asserting `juniper_canopy_demo_mode_active` reflects within one update tick.

### R3.3 Restore skipped `_create_metrics_panel` test (seed-12)

**Repo:** juniper-canopy
**Composite:** 2
**Approach:** Either (a) expose the method on a public testable surface and unskip; or (b) replace with a black-box test against the dashboard layout endpoint that exercises the same code path. Decision recorded in finding remediation.

### R3.4 Sentry tests unconditional (seed-09)

**Repos:** cascor, canopy, data
**Composite:** 2
**Approach:** Make `sentry-sdk` a hard dev-dep; remove `importorskip`. Sentry hook tests run on every CI run.

**Resolution (2026-04-30):** ✅ **Already satisfied; no remediation needed.** Pre-implementation audit found **zero** `importorskip("sentry_sdk")` matches in any of the three repos' test trees — seed-09's premise is stale. The SEC-15 / SEC-10 hook tests already run unconditionally via `with patch("sentry_sdk.init")` (which fails at collection-time if `sentry-sdk` is missing — the desired loud-regression signal) and via `monkeypatch.setitem(sys.modules, "sentry_sdk", _FakeSentry)` (which runs even without real `sentry-sdk`). `sentry-sdk>=2.0.0` is also a hard runtime dep on every server. Three planned fan-out PRs collapse to one closure note. Full audit + future-proofing analysis: [`METRICS_MONITORING_R3.4_SENTRY_AUDIT_CLOSURE_2026-04-30.md`](METRICS_MONITORING_R3.4_SENTRY_AUDIT_CLOSURE_2026-04-30.md).

### R3.5 Replay-buffer overflow test (seed-07)

**Repo:** cascor
**Composite:** 2
**Tests required:** Drive `_PROJECT_API_METRICS_BUFFER_SIZE + 1` updates; assert oldest entry evicted, newest retained, no exception.

### R3.6 Coverage-matrix gap closure

**All repos.** For every cell marked **GAP** in §10 of the review plan, either close with a test (preferred) or document an accepted-gap rationale in the corresponding finding.

### R3.7 macOS CI matrix

**Resolution (2026-05-01):** ✅ **Done.** All 4 R3.7 PRs merged: juniper-cascor#166, juniper-cascor-worker#39, juniper-data#61, juniper-canopy#208. Each repo's `unit-tests` job now runs a 2-D matrix `os × python-version` with `macos-latest` Python 3.12 added under `include:` and `experimental: true`; job-level `continue-on-error: ${{ matrix.experimental == true }}` keeps the macOS leg non-blocking during the **2-week soak window (2026-05-01 → 2026-05-15)**. Repos with torch installs (worker, canopy, cascor) branch the wheel install (Linux uses CPU index, macOS uses default PyPI). Worker's first run was green on the macOS leg; cascor / canopy / data macOS legs run for the first time on this PR's post-merge tip and on subsequent PRs.

**Wave 0 (fix-main-first prerequisite, 2026-05-01).** Before the R3.7 PRs could be evaluated against a clean baseline, all 4 target repos' main branches were red across multiple workflows (Lockfile Freshness, Pre-commit, Unit Tests, Security Scans). Three Wave 0 PRs landed alongside R3.7 to restore green:

| Repo | Wave 0 PR | Failure surfaces fixed |
|---|---|---|
| juniper-cascor | [#167](https://github.com/pcalnon/juniper-cascor/pull/167) | trailing-whitespace + black + isort auto-fixes; `# noqa: C901` on `_apply_params_unlocked` (complexity 17, refactor deferred); `requirements.lock` regen; 5 cross-repo doc links rewritten to `https://github.com/pcalnon/...` URLs (validator does not support `--cross-repo skip`). |
| juniper-canopy | [#209](https://github.com/pcalnon/juniper-canopy/pull/209) | `requirements.lock` regen; 5 stale frontend tests (component count 12→13 for `network_evolution`, `_init_params_from_backend_handler` no_update tuple width 25→28 + applied-dict index 24→27, `_track_param_changes_handler` calls switched to `applied=` kwarg); new `.gitleaks.toml` allowlisting `conf/conda_environment*.yaml` (build-hash false positives) and `notes/mcp/*` (example API snippets). |
| juniper-data | [#62](https://github.com/pcalnon/juniper-data/pull/62) | `requirements.lock` regen; `test_metrics_endpoint_uses_route_template_for_dataset_path` 403 fixed by adding `"testclient"` to the local fixture's `metrics_trusted_ips` (mirrors `test_phase1d_security.TestSEC16MetricsAppIntegration`). |

juniper-cascor-worker's main was already green; no Wave 0 PR was required for that repo.

**Phase R3 exit gate:** Coverage matrix has zero unjustified gaps; all suites green.

### Phase R3 status (2026-05-01): ✅ COMPLETE

All 7 R3 sub-tracks closed. Wall-clock: **~36 hours** start (R3 entry plan #176 merged 2026-04-30 evening) → finish (R3.6 sweep PR opened 2026-05-01 evening), against the entry plan's original 3-working-day estimate. The compression came from the Wave 1 / Wave 2 parallel-PR cadence (multiple PRs in flight simultaneously) and from R3.4 collapsing into a documentation-only audit closure once a pre-implementation grep showed seed-09's premise was stale.

**Per-track outcome:**

- **R3.1** (juniper-data#64) — live `/v1/datasets` integration test pinning counter +1 + histogram +1 per POST through real `/metrics` scrape. **Side-effect**: surfaced R4.5 (POST cache-hit observability gap) — captured in §7 as a follow-up.
- **R3.2** (juniper-canopy#210) — `juniper_canopy_demo_mode_active` gauge wired in `main.lifespan` + 3-test integration suite pinning runtime-toggle propagation. Production wiring was the load-bearing change; the test pins it.
- **R3.3** (juniper-canopy#212) — black-box `/dashboard/_dash-layout` test replaces stale `_create_metrics_panel` skip per Q2 resolution.
- **R3.4** (juniper-ml#177) — audit closure, no remediation needed (zero `importorskip("sentry_sdk")` already, seed-09 stale).
- **R3.5** (juniper-cascor#165) — `TestReplayBufferOverflowAtConfiguredCapacity` (3 tests at production-default capacity 1024).
- **R3.6** (juniper-ml#<this PR>) — residual §10 matrix sweep: 29 cells filled with `file:line` references (most pointing to existing R1.x / R2.x tests that didn't update §10 at the time), 12 cells marked GAP with rationale (7 SLO-deferred to R4.1 + R5.1, 3 client-Sentry no-surface, 2 surface-deferred captured as R4.6 + R4.7).
- **R3.7** (juniper-cascor#166, juniper-cascor-worker#39, juniper-data#61, juniper-canopy#208 + post-soak juniper-cascor#168, juniper-cascor-worker#40, juniper-data#63, juniper-canopy#211) — macOS leg added to all 4 unit-tests matrices, 2-week soak compressed by user direction, then flipped to `experimental: false` to make the macOS leg required.

**Wave 0 (fix-main-first prerequisite)**: 3 PRs (juniper-cascor#167, juniper-canopy#209, juniper-data#62) restored green main on 3 of the 4 R3.7 target repos before the R3.7 PRs could be evaluated against a clean baseline. Documented in §6 R3.7's resolution paragraph.

**§10 matrix population**: starts as Wave 1 (juniper-ml#181 — 4 cells), completes as Wave 2 (juniper-ml#<this PR> — remaining 29 cells + 12 GAPs).

**Follow-ups surfaced during R3 execution** (captured as new R4 sub-tracks):

- **R4.5** — juniper-data POST cache-hit observability gap (surfaced by R3.1).
- **R4.6** — juniper-data-client outbound `X-Request-ID` header (surfaced by R3.6).
- **R4.7** — cascor-worker inbound unrecognized-frame log emission test (surfaced by R3.6).

**Next phase**: R4 (best-practice + ergonomic improvements) covers R4.1–R4.7. R5 (SLO catalog + scrape manifests + dashboards + alerting) gates on R3 — R3 closure unblocks R4 and R5 entry planning.

---

## 7. Phase R4 — Best-practice and ergonomic improvements

**Entry plan (2026-05-01):** Open questions resolved in [`METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md`](METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md). Headline decisions: **Q1** (R4.1) bucket-choice methodology is **(c) hybrid** — document current rationale now, mark each bucket as "tentative pending R5.1" in the metric HELP string so R5.1 has a clear update target. **Q2** (R4.2) scope is **(c) canopy + targeted audit** of cascor/data — fix the known offender, audit the others to mark either clean or fold into R4.2 as schema-similar PRs. **Q3** (R4.3) instrumentation hook shape is **(a) single callable** `on_request(method, url, status, duration_ms, error)` — minimal API; canopy wraps in a Prometheus-emitting closure. **Q4** (R4.4) heartbeat additions: **(a) append fields to R1.3 heartbeat payload** — pushgateway (c) explicitly rejected (inverts R2 worker-boundary decision). **Q5** (R4.5) counter shape: **(a) new `juniper_data_dataset_post_total{generator, status, cache="hit"|"miss"}` counter** — keeps R5.1 dashboards orthogonal vs forcing label arithmetic on `record_access`. **Q6** (R4.6) data-client request-id propagation: **(a) always-on opt-in via `juniper-observability` import** — canopy + cascor already depend on the lib via R2.1, propagation is free for them. **Q7** (R4.7): not blocked, joins Wave 1 as smallest-test PR. **Sequencing** — **Wave 1 (parallelizable, single-repo)**: R4.4 + R4.5 + R4.6 + R4.7 (4 PRs). **Wave 2 (audit + fan-out)**: R4.2 (with audit) + R4.1 (3 PRs) (4–6 PRs). **Wave 3 (coupled)**: R4.3 data-client → canopy adoption (2 PRs). **Closure**: Phase R4 close note (1 PR). Total ~10–14 PRs (range depends on R4.2 audit + optional R4.4 cascor companion). Estimated wall-clock at the prior cadence (~5 PRs/day): **2–3 working days**.

### R4.1 Histogram bucket rationales (seed-14)

**Repos:** cascor, canopy, data
**Composite:** 2
**Approach:** Per metric, document the SLO target each bucket boundary serves (e.g., 0.1s for "p95 < 100ms" SLO). Adjust bucket layout if no SLO maps to current buckets.

### R4.2 Async-safe health probes (seed-10)

**Repo:** canopy (verify others)
**Composite:** 2 (3 if blocking observed in production)
**Approach:** Replace `urllib.request.urlopen()` in async health-probe paths with `httpx.AsyncClient` (or equivalent). Add a stress test that fires N concurrent probes against a slow upstream and asserts event loop is not stalled (latency p99 within bound).

### R4.3 Data-client request instrumentation (seed-13)

**Repo:** juniper-data-client
**Composite:** 2
**Approach (recommended):** Optional instrumentation hook accepting a callable invoked on each request with `method, url, status, duration_ms, error`. Default no-op; canopy provides a Prometheus-emitting hook. Avoids forcing prometheus dep into a thin client.
**Tests:** Hook-firing unit test; canopy-side test that requests through the hook produce the expected counter increments.

### R4.4 Worker training-loop instrumentation

**Repo:** cascor-worker
**Composite:** 2
**Approach:** Per-task timing, RSS reporting, GPU utilization (if applicable) emitted as part of the heartbeat frame from R1.3. No new endpoint; reuses heartbeat surface.

### R4.5 juniper-data POST cache-hit observability gap (surfaced 2026-05-01 by R3.1)

**Repo:** juniper-data
**Composite:** 2
**Symptom:** `POST /v1/datasets` short-circuits in `api/routes/datasets.create_dataset` (lines 101–108) when `dataset_id` — a deterministic hash of `generator + version + params` — is already in the store. The route returns the cached `meta` and skips both `record_dataset_generation` (the generation-counter / duration-histogram path) and `record_access` (the latter is wired only into the GET handlers per BUG-JD-08). Result: a deterministic re-POST with identical params is **invisible** to all dataset-side metrics — no counter increment, no histogram observation, no access tally.

**Why it matters:** Production-shaped traffic patterns (e.g. juniper-cascor re-fetching a known `dataset_id` during retraining, a CI runner that POSTs the same spiral params on every test, or a deterministic load-test driver) will under-report request volume against the dataset surface. Capacity-planning queries against `juniper_data_dataset_generations_total` will undercount; access-pattern dashboards built on `record_access` will undercount the POST contribution; an SLO defined on either metric will be miscalibrated. The R3.1 live integration test discovered this when two identical POSTs only bumped the generation counter once (test now varies `noise` between calls to defeat the cache and exercise the metric path twice).

**Approach:** Two options, no preference yet — to be decided during R4 entry planning:

- **(a)** Add a new `juniper_data_dataset_post_total{generator, status, cache="hit"|"miss"}` counter bumped on every POST regardless of cache state. Keeps `record_dataset_generation` semantics unchanged (still counts only real generations); separates "request volume" from "generation work" cleanly. Smallest production-code delta.
- **(b)** Have the cache-hit branch call `record_access(dataset_id)` so POST + GET both contribute to the existing access counter. Conflates POST and GET request types but reuses existing instrumentation.

Option (a) preserves observability orthogonality (request volume vs work performed vs read access) and is the recommended starting point unless R5 dashboard work surfaces a strong reason to merge POST + GET access counts.

**Test:** Mirror the R3.1 live integration test pattern — POST the same params twice, assert the new POST counter increments by 2 and the generation counter increments by 1 (regression guard against the original bug).

### R4.6 juniper-data-client outbound X-Request-ID header (surfaced 2026-05-01 by R3.6)

**Repo:** juniper-data-client
**Composite:** 1
**Symptom:** `juniper_data_client._request()` does not emit an `X-Request-ID` header on outbound HTTP calls. juniper-data inherits `RequestIdMiddleware` from the shared `juniper-observability` lib (R2.1) and will *generate* a request-id when one isn't supplied, but that breaks correlation back to the caller's request chain (canopy → data-client → data, or cascor → data-client → data — the inbound canopy/cascor request-id is lost at the data-client boundary).

**Approach:** Plumb a request-id propagation hook through `_request()`. Two options:

- **(a)** Read `juniper_observability.request_id_var` at call time; if non-empty, copy into outbound `X-Request-ID`. Caller-side library opt-in via importing the lib at the call boundary. Smallest delta — no API change to data-client's public surface.
- **(b)** Accept an explicit `request_id: str | None = None` kwarg on each public method; when supplied, set the header. Pushes responsibility to consumers but keeps data-client free of an observability-lib runtime dep.

Option (a) is recommended — canopy and cascor both already depend on `juniper-observability` via R2.1, so the data-client opt-in is essentially free for the existing consumers.

**Test:** Unit test asserts the outbound HTTP call carries `X-Request-ID: <expected>` when `request_id_var` is set in the calling thread.

### R4.7 cascor-worker inbound unrecognized-frame log emission test (surfaced 2026-05-01 by R3.6)

**Repo:** cascor-worker
**Composite:** 1
**Symptom:** Worker production code in `juniper_cascor_worker/worker.py::CascorWorkerAgent._run` emits a structured WARNING `juniper_cascor_worker_unrecognized_ws_frame{type, worker_id}` on receipt of unknown server-emitted frame types (R2.2.6 invariant). `tests/test_protocol_alignment.py:102` pins the *outbound* enum-alignment contract (worker doesn't send unknown types to server) but no test exercises the *inbound* warning emission path — i.e. server sends a frame the worker doesn't recognize, worker logs the structured WARNING.

**Approach:** Drive the worker's `_run` message loop with a synthetic WebSocket message carrying an unknown `type` field; capture log records via `caplog`; assert the structured WARNING fires with the expected fields (`type=<unknown>`, `worker_id=<configured>`).

**Test:** Single unit test in `tests/test_worker_agent.py::TestMessageLoopDispatch` (line 383) — the dispatch loop is already exercised there for known types, this adds the unknown-type branch.

**Phase R4 exit gate:** All best-practice findings closed or accepted with documented rationale.

### Phase R4 status (2026-05-02): ✅ COMPLETE

All 7 R4 sub-tracks closed (R4.1–R4.7). Wall-clock: **~26 hours** start (R4 entry plan #183 merged 2026-05-01 evening) → finish (this PR opened 2026-05-02 evening), against the entry plan's 2–3 working-day estimate. The compression came from the Wave 1 / Wave 2 / Wave 3 parallel-PR cadence and from the R4.2 audit finding cascor + data clean (no schema-similar fan-out needed).

**Per-track outcome:**

- **R4.1** (juniper-cascor#176, juniper-canopy#216, juniper-data#66) — per-boundary SLO rationale documented for all 6 production histograms across the 3 servers (cascor: 4, canopy: 1, data: 1). HELP-string marker "(R4.1 buckets tentative pending R5.1)" on every histogram so operators reading `/metrics` see the forward-pointer to the rationale doc. Two cascor histograms (`broadcast_send_duration_seconds`, `command_handler_seconds`) explicitly flagged for re-bucketing in R5.1 — they currently use Prometheus default buckets (5 ms floor) which don't match their actual sub-millisecond distribution.
- **R4.2** (juniper-canopy#215) — both canopy probe paths (`health.probe_dependency`, `discovery.probe_cascor_url`) migrated from `urllib.request` + thread-pool offload to native `httpx.AsyncClient`. Q2 audit confirmed cascor + juniper-data clean (cascor's 2 `urllib.request` sites are startup-only; data has zero) — scope stayed canopy-only. New stress test fires 64 concurrent probes against a 100ms-latency mock and asserts elapsed wall-clock stays under 25% of the serial floor (catches blocking-call regression). `httpx>=0.27` added as canopy runtime dep.
- **R4.3** (juniper-data-client#40 → release v0.4.1 #41 → juniper-canopy#218) — the Wave 3 coupled pair plus a release-cut PR. data-client adds the optional `on_request(method, url, status, duration_ms, error)` instrumentation hook (default no-op; hook exceptions swallowed + logged at WARNING so instrumentation never crashes production paths). canopy provides a Prometheus-emitting closure via `build_data_client_request_hook()` and wires it into the `JuniperDataClient` construction at `demo_mode.py:890`. Two new canopy metrics (`juniper_canopy_data_client_requests_total{method, status_class, error_type}` + `juniper_canopy_data_client_request_duration_ms`) keep cardinality bounded via the closed-set `status_class` label.
- **R4.4 + R4.4b** (juniper-cascor-worker#43, juniper-cascor#175) — worker heartbeat payload enriched with `last_task_duration_seconds`, `recent_task_durations_seconds` (sliding window of 16, `deque(maxlen=...)`-bounded), `gpu_utilization_pct` (best-effort via `torch.cuda.utilization()`, None when no CUDA / NVML / torch). Cascor server-side companion accepts the new kwargs in `WorkerRegistration.record_heartbeat()` + `WorkerRegistry.heartbeat()`, exposes via `/v1/workers` JSON. Per-task wall-clock wraps the entire `_handle_task_assign` lifecycle so failed/timed-out tasks contribute to the percentile window. R1.3 additive-compatibility pattern preserved — older worker images stay compatible.
- **R4.5** (juniper-data#65) — new `juniper_data_dataset_post_total{generator, status, cache="hit"|"miss"}` counter bumped on every POST `/v1/datasets` regardless of cache state. Closes the observability gap surfaced by R3.1 (cache-hit POSTs were silently invisible to all dataset-side metrics). Two closed-set constants `POST_CACHE_HIT` / `POST_CACHE_MISS` prevent typo-induced cardinality leakage.
- **R4.6** (juniper-data-client#39, included in v0.4.1 release #41) — `_request()` propagates `juniper_observability.request_id_var` as outbound `X-Request-ID` header. Best-effort: ImportError (lib not installed standalone) and LookupError (ContextVar unset) silently no-op. Caller-supplied headers always win. New `[observability]` extra for standalone users; canopy/cascor get propagation transparently via existing R2.1 deps.
- **R4.7** (juniper-cascor-worker#42) — single test in `test_worker_agent.py::TestMessageLoopDispatch` covering the unknown-type branch of `_message_loop`. caplog-asserts the structured WARNING `juniper_cascor_worker_unrecognized_ws_frame` fires with `extra={"type", "worker_id"}` direct attributes (the format Loki and similar log shippers parse as structured fields). Closes the **partial** §10 cell from R3.6.

**Adjacent fix bundled (juniper-canopy#218):** `test_observability.py::test_async_probe_dependency_delegates_to_shared` was leftover from R4.2 (canopy#215) — that PR removed `_probe_dependency_sync` but missed updating this single test. Renamed to `test_async_probe_dependency_uses_native_httpx` and updated to patch `httpx.AsyncClient.get`. Side-fix in canopy#218 to keep main green.

**No follow-ups surfaced for R5.x.** R4 execution did not uncover new sub-tracks (vs. R3 which surfaced R4.5 / R4.6 / R4.7). The R4.1 re-bucketing flags on cascor's `broadcast_send_duration_seconds` + `command_handler_seconds` are R5.1 entry-plan inputs (covered by the existing R5.1 sub-track), not new work.

**Next phase**: **R5** (SLO/SLI catalog + scrape manifests + Grafana dashboards + alerting). R5 is the production-observability deliverable; gates on R3 + R4 (both now closed). R5.1 SLO catalog is the first sub-track and will:

- Define availability / latency / saturation SLIs per service.
- Ratify or reshape the 6 R4.1-documented histogram bucket layouts.
- Re-bucket the 2 cascor histograms R4.1 flagged (proposed sub-millisecond layout in `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` §4).

---

## 8. Phase R5 — SLO/SLI definition, scrape config, dashboards

**Entry plan (2026-05-02):** Open questions resolved in [`METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`](METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md). Headline decisions: **Q1** (R5.1) SLO methodology is **(c) user-facing primary + internal-supporting** — 5 user-facing SLIs (canopy dashboard availability + render latency, cascor train-job success + train-step p95, data-service POST availability) become release-blocking, 8 internal-supporting SLIs (worker heartbeat freshness, queue depth saturation, cascor broadcast fan-out, etc.) graphed but not alerted. **Q2** (R5.1b cascor sub-millisecond re-bucket) is **(b) separate from R5.1 doc PR** — code change in juniper-cascor lands in Wave 1 alongside the R5.1 catalog drafting; R5.1 doc references the new layout. **Q3** SLO catalog location is **(a) single juniper-deploy doc** at `notes/SLO_CATALOG_2026-05-XX.md` — single source of truth for ops + per-service AGENTS.md cross-links back. **Q4** scrape strategy is **(c) both raw scrape_configs + ServiceMonitor CRDs** in helm — covers docker-compose dev (existing prometheus.yml) and k8s production (helm/) without forcing one operator pattern. **Q5** (`MetricsAuthMiddleware`, the long-standing R2.1 design Q3) is **(b) keep per-service**, document rationale at `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` — closes the gating question that has been carried since 2026-04-28. **Q6** dashboard format is **(a) keep JSON committed** (no jsonnet build) — preserves the 4 existing Grafana dashboards (canopy/cascor/data/overview); R5.3 is rationalization + extension, not greenfield. **Q7** alerting style is **(c) hybrid** — burn-rate alerts (multi-window multi-burn-rate, MWMBR) for the 5 user-facing SLOs, threshold alerts for binary health (heartbeat-stale, scrape-down). **Q8** sequencing is **(b) Wave 1 parallel (R5.1b + R5.2 + R5.3) → Wave 2 (R5.1 → R5.4) → Closure**. **Sequencing** — **Wave 1 (parallel, no inter-dep)**: R5.1b cascor re-bucket + R5.2 scrape manifests + MetricsAuthMiddleware decision-doc + R5.3 4-dashboard refresh (3 PRs). **Wave 2 (serial, dep chain)**: R5.1 SLO catalog (depends on Wave 1 R5.1b) → R5.4 burn-rate alerts (depends on R5.1 SLI definitions) (2 PRs). **Closure**: Phase R5 close note + METRICS-MON program-end note (1–4 PRs depending on whether per-repo close-notes are bundled). Total ~6 base / up to 9 PRs (range covers optional per-repo close-notes). Estimated wall-clock at the prior cadence: **1.5–2 working days**. **METRICS-MON program ends after R5 closes.**

### R5.1 SLO/SLI catalog

**Location:** `juniper-deploy/notes/SLO_CATALOG_2026-04-25.md` (created during this phase).
**Approach:** For each service, define availability SLI (success ratio over rolling window), latency SLI (histogram quantile), and saturation SLI (resource gauge). Tie metric definitions to SLIs. Re-validate histogram bucket choices against SLO targets (revisits R4.1).

### R5.2 Prometheus / ServiceMonitor manifests

**Repo:** juniper-deploy
**Approach:** Confirm scrape configs hit each `/metrics` endpoint; pin scrape interval and label munging; emit `ServiceMonitor` CRDs if running on Prometheus Operator.

### R5.3 Grafana dashboards

**Repo:** juniper-deploy
**Approach:** One dashboard per service, plus a cross-cutting "platform overview" panel set. Dashboard JSON committed and validated by `jsonnet` build (if currently used) or pinned to a snapshot.

### R5.4 Alerting rules

**Repo:** juniper-deploy
**Approach:** PrometheusRule CRDs (or alertmanager config) for each release-blocking SLI. Alert on burn-rate, not on instantaneous threshold breach.

**Phase R5 exit gate:** SLOs documented and instrumented; deployment manifests reproduce dashboards from a clean checkout.

**Phase R5 gating issue (raised 2026-04-28 from R2.1 design Q3):** When R5 designs the per-service scrape allowlist strategy, **evaluate whether `MetricsAuthMiddleware` (currently juniper-data only, SEC-16 IP allowlist) belongs in the shared `juniper-observability` lib**. Decision criteria: (a) do other servers (cascor, canopy) need an equivalent IP allowlist on `/metrics`? (b) would Prometheus ServiceMonitor scrape policies obviate the per-service middleware entirely? (c) if it stays per-service, document the rationale in `juniper-deploy/notes/`.

---

## 9. Status tracker (updated through execution)

| Phase  | Item                         | Status             | Owner       | PR(s)                                         | Worktree | Notes                                                                                                                                   |
|--------|------------------------------|--------------------|-------------|-----------------------------------------------|----------|- ---------------------------------------------------------------------------------------------------------------------------------------|
| R1.1   | seed-01 cardinality          | **done**           | Paul Calnon | juniper-data#49, juniper-cascor#143,          | cleaned  | Unified `_unmatched` bucket + `http_unmatched_requests_total{method}` counter across all 3 servers (merged 2026-04-27)                  |
|        |                              |                    |             | juniper-canopy#178                            |          |                                                                                                                                         |
| R1.2   | seed-02/03 probe semantics   | **done**           | Paul Calnon | juniper-data#51, juniper-cascor#147,          | cleaned  | Liveness tick (250 ms budget), readiness 503-on-not_ready, `X-Juniper-Readiness`                                                        |
|        |                              |                    |             | juniper-canopy#183, juniper-deploy#35         |          | header, cascor lifecycle heartbeat counter, Helm chart v1.0.0 with corrected probe paths (merged 2026-04-27)                            |
| R1.3   | seed-04 worker heartbeat     | **main work done** | Paul Calnon | juniper-cascor#150, juniper-cascor-worker#37, | cleaned  | All 3 main PRs merged 2026-04-28. Chart 1.0.0→1.1.0 with `worker.healthcheck.enabled=false` default;                                    |
|        |                              |                    |             | juniper-deploy#43                             |          | worker HTTP listener + enriched heartbeat live; cascor accepts new fields.                                                              |
| R1.3.4 | flag-flip follow-up          | deferred (burn-in) |             |                                               |          | Bump `worker.healthcheck.enabled` default to `true`, chart 1.1.0→1.2.0,                                                                 |
|        |                              |                    |             |                                               |          | after staging confirms worker image ≥ 0.4.0 stable in production-shaped traffic.                                                        |
| R2.1   | seed-06 shared lib           | **done**           | Paul Calnon | juniper-ml#155, #164;                          | cleaned  | All 5 PRs merged. `juniper-observability` v0.1.1 stable on PyPI (2026-04-29). data, cascor, canopy all consume the shared lib;          |
|        |                              |                    |             | juniper-data#60; juniper-cascor#155;          |          | tz-aware `ReadinessResponse.timestamp` (closes BUG-JD-06-equivalent) and SEC-15 `before_send` hook (defense-in-depth, gained by         |
|        |                              |                    |             | juniper-canopy#199                            |          | canopy as a free upgrade) are now the cross-service standard. Wire-compat snapshot tests pin `/v1/health/ready` shape per consumer.     |
| R2.2   | seed-05 WS schema validation | **done**           | Paul Calnon | juniper-cascor#156, #159, #160;                | cleaned  | All 7 PRs merged 2026-04-30. `juniper-cascor-protocol==0.1.0` on PyPI; cascor server, cascor-client, canopy, worker all consume it.       |
|        |                              |                    |             | juniper-cascor-client#29; juniper-canopy#206; |          | Cascor-client + canopy validate every inbound frame via Pydantic envelopes with R1.1-bounded `juniper_<svc>_unrecognized_ws_frames_total` |
|        |                              |                    |             | juniper-cascor-worker#38                       |          | counter; worker single-sources `WorkerMessageType` + `BinaryFrame.encode` + emits structured log line on unknown types (no pydantic at runtime). |
| R2.3   | seed-15 probe symmetry       | **done**           | Paul Calnon | juniper-canopy#202, juniper-deploy#44         | cleaned  | All probes already in place from R1.2 + R2.1 work; canopy regression test for upstream-down injection added (4 new tests pinning the    |
|        |                              |                    |             |                                               |          | canopy-degraded / cascor-503 severity asymmetry); operator-facing topology + severity ref doc landed in juniper-deploy/notes/PROBE_GRAPH.md. |
| R3.1   | seed-08 dataset-gen e2e      | **done**           | Paul Calnon | juniper-data#64; juniper-ml#181               | cleaned  | `TestDatasetGenerationMetricsLive` (2 tests in `juniper_data/tests/integration/test_dataset_generation_metrics_live.py`) goes end-to-end |
|        |                              |                    |             |                                               |          | through FastAPI TestClient → real Prometheus registry → `/metrics` scrape; pins counter +1 + histogram +1 per POST. Cache-bypass        |
|        |                              |                    |             |                                               |          | discovery (POST short-circuit on cached `dataset_id` skips `record_dataset_generation`) captured as **R4.5** follow-up.                  |
| R3.2   | seed-11 demo-mode test       | **done**           | Paul Calnon | juniper-canopy#210; juniper-ml#181            | cleaned  | `TestDemoModeGauge` (3 tests in `src/tests/integration/test_demo_mode_gauge.py`) pins lifespan-hook wiring + runtime-toggle             |
|        |                              |                    |             |                                               |          | propagation through `/metrics`. Production wiring added in `main.py` lifespan: `set_demo_mode_active(backend.backend_type == "demo")`. |
| R3.3   | seed-12 restore skipped test | **done**           | Paul Calnon | juniper-canopy#212                            | cleaned  | Replaced stale `@pytest.mark.skip` on `test_create_metrics_panel` with `test_metrics_panel_appears_in_rendered_layout` — black-box      |
|        |                              |                    |             |                                               |          | test against `dashboard.app.server.test_client().get("/_dash-layout")`, asserting `metrics-panel` + `metrics-store` markers in the      |
|        |                              |                    |             |                                               |          | rendered layout JSON. Per Q2 resolution: doesn't grow public API.                                                                       |
| R3.4   | seed-09 Sentry unconditional | **done**           | Paul Calnon | juniper-ml#177                                 | cleaned  | Audit closure (no remediation): pre-implementation grep across cascor/canopy/data confirmed zero `importorskip("sentry_sdk")` already.  |
|        |                              |                    |             |                                               |          | Seed-09 premise was stale; the three planned fan-out PRs collapsed into one juniper-ml documentation PR.                                |
| R3.5   | seed-07 replay-buffer test   | **done**           | Paul Calnon | juniper-cascor#165                             | cleaned  | `TestReplayBufferOverflowAtConfiguredCapacity` (3 tests) added to `test_websocket_seq_replay.py`: drives capacity+1 broadcasts +        |
|        |                              |                    |             |                                               |          | far-overflow stress; reads capacity from `Settings(api_keys=()).ws_replay_buffer_size` (production default 1024). Verified locally.    |
| R3.6   | coverage-matrix gaps         | **done**           | Paul Calnon | juniper-ml#<this PR>                          | cleaned  | Residual sweep populates every empty §10 cell with either a `file:line` reference (29 cells filled — most pointing to existing R1.x /  |
|        |                              |                    |             |                                               |          | R2.x tests that didn't update §10 at the time) or a **GAP** rationale (12 cells: 7 SLO-deferred + 3 client-Sentry + 2 surface-deferred  |
|        |                              |                    |             |                                               |          | with R4.6 / R4.7 follow-ups). Phase R3 closed (see §6 close note).                                                                      |
| R3.7   | macOS CI matrix              | **done**           | Paul Calnon | juniper-cascor#166; juniper-cascor-worker#39;   | cleaned  | All 4 PRs merged 2026-05-01. Each repo's `unit-tests` job now runs a 2-D matrix `os × python-version` with `macos-latest` (Python 3.12) |
|        |                              |                    |             | juniper-data#61; juniper-canopy#208           |          | added under `include:` and `experimental: true`. Job-level `continue-on-error: ${{ matrix.experimental == true }}` keeps the macOS leg |
|        |                              |                    |             |                                               |          | non-blocking during the 2-week soak window (**2026-05-01 → 2026-05-15**). After the soak, flip `experimental` to `false` to make the   |
|        |                              |                    |             |                                               |          | macOS leg required. Worker / canopy / cascor branched the torch wheel install (Linux uses CPU index, macOS uses default PyPI).         |
|        |                              |                    |             |                                               |          | **Wave 0** (fix-main-first, prerequisite): all 4 repos' main branches were red prior to R3.7 merges. Wave 0 PRs landed alongside       |
|        |                              |                    |             |                                               |          | (juniper-cascor#167 — pre-commit + lockfile + cross-repo doc links; juniper-canopy#209 — lockfile + 5 frontend test stale-counts +     |
|        |                              |                    |             |                                               |          | gitleaks allowlist; juniper-data#62 — lockfile + `/metrics` test fixture testclient host) restored green main on every repo.           |
| R4.1   | seed-14 bucket rationales    | **done**           | Paul Calnon | juniper-cascor#176; juniper-canopy#216;        | cleaned  | 3 schema-similar PRs document per-boundary SLO rationale for all 6 production histograms (cascor: 4, canopy: 1, data: 1). HELP-string |
|        |                              |                    |             | juniper-data#66                               |          | marker "tentative pending R5.1" on every histogram. Two cascor histograms (`broadcast_send_duration_seconds`, `command_handler_seconds`)|
|        |                              |                    |             |                                               |          | flagged for re-bucketing in R5.1 — currently use Prometheus default buckets that don't match their sub-millisecond distribution.       |
| R4.2   | seed-10 async-safe probes    | **done**           | Paul Calnon | juniper-canopy#215                            | cleaned  | Both canopy probe paths (`health.probe_dependency`, `discovery.probe_cascor_url`) migrated from `urllib.request`+thread-pool offload  |
|        |                              |                    |             |                                               |          | to native `httpx.AsyncClient`. Q2 audit confirmed cascor + juniper-data clean — scope stayed canopy-only. Stress test fires 64        |
|        |                              |                    |             |                                               |          | concurrent probes against 100ms-latency mock; asserts elapsed < 25% of serial floor (catches blocking-call regression).                |
| R4.3   | seed-13 data-client hooks    | **done**           | Paul Calnon | juniper-data-client#40, #41 (v0.4.1 release); | cleaned  | Optional `on_request(method, url, status, duration_ms, error)` hook on `JuniperDataClient` (default no-op). Canopy provides            |
|        |                              |                    |             | juniper-canopy#218                            |          | Prometheus-emitting closure via `build_data_client_request_hook()`; wires it into `demo_mode.py:890`. Two new canopy metrics with     |
|        |                              |                    |             |                                               |          | closed-set `status_class` label keep cardinality bounded. Hook exceptions swallowed + logged WARNING (instrumentation never crashes).  |
| R4.4   | worker training-loop instr   | **done**           | Paul Calnon | juniper-cascor-worker#43;                      | cleaned  | Worker heartbeat enriched with `last_task_duration_seconds`, `recent_task_durations_seconds` (deque(maxlen=16)),                       |
|        |                              |                    |             | juniper-cascor#175 (R4.4b accept)             |          | `gpu_utilization_pct` (best-effort via `torch.cuda.utilization()`). Cascor server companion accepts new kwargs in record_heartbeat()  |
|        |                              |                    |             |                                               |          | + exposes via `/v1/workers`. Per-task wall-clock wraps full lifecycle so failed/timed-out tasks contribute to percentile window.       |
| R4.5   | data POST cache-hit obs gap  | **done**           | Paul Calnon | juniper-data#65                               | cleaned  | New `juniper_data_dataset_post_total{generator, status, cache="hit"|"miss"}` counter bumped on every POST regardless of cache state.  |
|        |                              |                    |             |                                               |          | Closes the R3.1-surfaced gap: cache-hit POSTs were silently invisible to all dataset-side metrics. Two closed-set constants prevent   |
|        |                              |                    |             |                                               |          | typo-induced cardinality leakage. 3 new integration tests pin counter +2 / generations +1 for two identical POSTs.                     |
| R4.6   | data-client X-Request-ID     | **done**           | Paul Calnon | juniper-data-client#39, #41 (v0.4.1 release)  | cleaned  | `_request()` propagates `juniper_observability.request_id_var` as outbound `X-Request-ID` header. Best-effort: ImportError +          |
|        |                              |                    |             |                                               |          | LookupError silently no-op. Caller-supplied headers always win. New `[observability]` extra for standalone users; canopy/cascor get   |
|        |                              |                    |             |                                               |          | propagation transparently via existing R2.1 deps. 4 unit tests pin set / unset / caller-wins / standalone paths.                       |
| R4.7   | worker unrecognized-frame log| **done**           | Paul Calnon | juniper-cascor-worker#42                       | cleaned  | Single test in `test_worker_agent.py::TestMessageLoopDispatch` covers the unknown-type branch of `_message_loop`. caplog-asserts the  |
|        |                              |                    |             |                                               |          | structured WARNING `juniper_cascor_worker_unrecognized_ws_frame` fires with `extra={"type", "worker_id"}` direct attributes (Loki's   |
|        |                              |                    |             |                                               |          | structured-field shape). Closes the **partial** §10 cell from R3.6.                                                                    |
| R5.1   | SLO catalog                  | not started        |             |                                               |          |                                                                                                                                         |
| R5.2   | scrape manifests             | not started        |             |                                               |          |                                                                                                                                         |
| R5.3   | Grafana dashboards           | not started        |             |                                               |          |                                                                                                                                         |
| R5.4   | alerting rules               | not started        |             |                                               |          |                                                                                                                                         |

---

## 10. Cross-cutting risks during execution

| Risk                                                                            | Mitigation                                                                           |
|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Shared lib (R2.1) blocks every consumer and slips                               | Ship it as alpha pre-release; consumers pin range; allow incremental migration       |
| Probe-semantics change (R1.2) trips Helm probe failure thresholds and pages SRE | Roll out in staging first; coordinate with juniper-deploy probe-threshold update     |
| Cardinality fix (R1.1) suppresses metrics needed by existing dashboards         | Keep `_unmatched` bucket; emit deprecation warning on raw-path label use for one rel |
| Worker heartbeat (R1.3) introduces new failure mode (heartbeat itself fails)    | Heartbeat failure is best-effort logged; absence treated as soft-degraded, not down  |
| Test-suite expansion balloons CI time                                           | Mark new perf/cardinality tests `@pytest.mark.performance` and gate weekly, not PR   |

---

## 11. Per-repo execution checklist

When picking up an item, the engineer must:

1. **Read the finding** (METRICS-MON-NNN in §9 of the review plan).
2. **Read the recommendation** (Phase 5 output).
3. **Create a worktree** under `/home/pcalnon/Development/python/Juniper/worktrees/` per the project Worktree Setup procedure.
4. **Branch name**: `metrics-mon-<NNN>-<short-slug>` (e.g., `metrics-mon-001-cardinality-fallback`).
5. **Implement + test in the same PR**; do not split fix from test.
6. **Pre-commit must pass.** Do not bypass.
7. **Open PR** against the affected repo's main; cite finding ID in title and body.
8. **After merge**: Worktree Cleanup V2 (`util/worktree_cleanup.bash`).
9. **Update §9 status tracker** in this roadmap.

---

## 12. Definition of done (per item)

An item is **done** when:

- PR is merged to the affected repo's main.
- The associated test exists, runs in CI, and asserts the corrected behavior.
- The finding's status in the review plan is moved to `RESOLVED` with a link to the PR.
- The roadmap §9 row is updated with PR link, owner, and resolution notes.
- If the item changed an AGENTS.md / CLAUDE.md contract, that file is updated in the same PR.

A **phase** is **done** when:

- All items in the phase are done.
- Full test suites pass for every affected repo (no errors, no warnings, no criteria failures).
- A phase summary is appended to this roadmap describing scope shipped, deferred items (with new IDs), and any newly-discovered findings.

---

## 13. Review-to-roadmap traceability

Every roadmap item references one or more findings. No roadmap work is performed without a corresponding finding. New findings discovered during implementation are added to §9 of the review plan first, then a new roadmap row is created. This prevents scope drift.

---

## 14. Closure of the roadmap

The roadmap is **closed** when:

- All phases R1–R5 are done.
- A retrospective document `notes/code-review/METRICS_MONITORING_RETROSPECTIVE_<date>.md` is written summarizing what shipped, what slipped, and what should be added to the next review's baseline.
- The next review's baseline document is opened (or this document is re-baselined for an incremental review).

### Roadmap status (2026-05-03): ✅ CLOSED

All five phases R1–R5 shipped between 2026-04-25 (this roadmap's authoring) and 2026-05-03 (program-close PR), spanning **9 calendar days**, **78 PRs**, and **8 repos** (juniper-ml, juniper-cascor, juniper-canopy, juniper-data, juniper-deploy, juniper-data-client, juniper-cascor-worker, juniper-cascor-client). The program-close note at [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) replaces the planned `METRICS_MONITORING_RETROSPECTIVE_<date>.md` retrospective: it summarizes what shipped per-phase, captures the cross-cutting outcomes (33 metrics shipped, cardinality discipline enforced, 3-consumer adoption of `juniper-observability`, 4-consumer adoption of `juniper-cascor-protocol`, every WS frame validated), records production posture (SLO catalog, burn-rate alerts, dashboards, scrape configs, 30-day soak window), surfaces honest learnings (TRAIN-ARCH-01 absence vs regression, SLI 3.4 granularity rename, Wave 0 fix-main-first prerequisite), and carries 8 residual follow-ups forward — none program-blocking; the two soft-blockers (alertmanager `tickets` receiver wiring, SLO target re-calibration) are time-bound to the 30-day soak (closes 2026-06-02). No incremental-review re-baselining is opened: subsequent observability work moves to ad-hoc follow-up PRs or a new program.
