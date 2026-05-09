# METRICS-MON R2 Exit Gate — Decision: `juniper-cascor-worker` and the shared `juniper-observability` library

**Decision date:** 2026-04-29
**Author:** Paul Calnon
**Status:** ✅ Decided — **do not migrate now**; adopt **only** the two R1.2 contract constants.
**Companion:** [`METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) §5 Q5; [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §5 R2 gating issue.

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. The question

When R2.1 was scoped (juniper-ml#155, 2026-04-28) we deferred a Q5: **should `juniper-cascor-worker` adopt the shared `juniper-observability` lib?** The R2 phase exit gate requires that question to be answered before R2 is closed.

The R2.1.1 design captured three decision criteria:

a. Is **Starlette's transitive footprint** acceptable in the slim worker image?
b. Does the worker **benefit** from shared `RequestIdMiddleware` / `JuniperJsonFormatter` consistency?
c. Would adoption **simplify cross-cutting bug fixes** that have already had to land twice (worker + servers)?

This note resolves all three on evidence collected after R2.1.5 (the canopy migration) shipped.

---

## 2. The worker's observability surface today

| Surface | Where it lives | Lines | Duplicated with shared lib? |
|---|---|---:|---|
| HTTP/1.1 health server (`/v1/health`, `/v1/health/live`, `/v1/health/ready`) | `juniper_cascor_worker/http_health.py` | 357 | **No** — hand-rolled on `asyncio.start_server`; the shared lib does not provide a server (just middleware for FastAPI/Starlette consumers). |
| `LIVENESS_TICK_BUDGET_MS = 250` | `juniper_cascor_worker/constants.py:102` | 1 | **Yes** — exact same literal in `juniper_observability.LIVENESS_TICK_BUDGET_MS`. |
| `READINESS_HEADER = "X-Juniper-Readiness"` | `juniper_cascor_worker/http_health.py:38` | 1 | **Yes** — exact same string in `juniper_observability.READINESS_HEADER`. |
| `LIVENESS_STALENESS_SECONDS` | (not used — no heartbeat-staleness gate; the worker's tick consults WS-connection state directly) | — | n/a |
| `sample_rss_mb()` | `juniper_cascor_worker/http_health.py:320` | ~30 | **No** — platform-branched (Linux kB / macOS bytes). The shared lib has no equivalent. |
| stdlib `logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")` | `juniper_cascor_worker/cli.py:57` | 1 | **Equivalent** — shared `DEFAULT_LOG_FORMAT_PLAIN` is `"%(asctime)s [%(levelname)s] %(name)s: %(message)s"` (character-for-character). |
| `JuniperJsonFormatter` / structured JSON logging | — | — | **Not used.** Worker emits plain-text logs only. |
| `RequestIdMiddleware` / `request_id_var` | — | — | **Not used.** Worker has no incoming HTTP request flow that would carry a request id (health probes are not business logic). |
| `PrometheusMiddleware`, `get_prometheus_app`, `set_build_info`, training metrics | — | — | **Not used.** Worker exposes no `/metrics` endpoint. |
| `configure_sentry`, SEC-15 `before_send` hook | — | — | **Not used.** Worker has no Sentry integration. |
| `DependencyStatus` / `ReadinessResponse` Pydantic models | — | — | **Not used.** Worker's `/v1/health/ready` body is hand-rolled `json.dumps({"status": "ready", "service": "juniper-cascor-worker"})` — by design it has no `dependencies`, `details`, `version`, or `timestamp` fields because the worker is a leaf in the dependency graph (no upstream deps to probe). |

**Net duplication that actually crossed the seam:** 2 literal constants out of the lib's 20-symbol public API.

---

## 3. Resolution against each criterion

### 3.1 (a) Starlette + Pydantic transitive footprint

The R1.3 design explicitly chose `asyncio.start_server` over FastAPI / Starlette to keep the worker image slim ([R1.3 design §5.1 Option C](METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md)). That decision is two weeks old and was made for sound reasons.

Adopting `juniper-observability` adds these as transitive deps to the worker:

- `pydantic>=2.0` (~12 MB compiled wheel)
- `starlette>=0.27` (~250 KB)
- `anyio` + `sniffio` + `idna` (~2 MB combined)

In absolute terms: ~14 MB of additional Python on top of the worker's existing torch dependency (~700 MB). In relative terms: 2%. **Acceptable on size grounds**, but only meaningful if there is a benefit to spend it on.

### 3.2 (b) Cross-cutting consistency benefit

| Shared symbol | Worker uses it? | Would consistency help? |
|---|---|---|
| `JuniperJsonFormatter` | No | Marginal — the worker has no log shipper that requires JSON parsing. The plain-text format already matches the shared `DEFAULT_LOG_FORMAT_PLAIN`. |
| `RequestIdMiddleware` / `request_id_var` | No | None — the worker's HTTP surface is probe-only; there is no business request to correlate. |
| `PrometheusMiddleware` / `UNMATCHED_ENDPOINT_LABEL` | No | None — no `/metrics` mount. |
| `DependencyStatus`, `ReadinessResponse` | No | **Negative** — adopting the shared model would force a wire-format change. The worker's leaf position in the graph means `dependencies={}` / `details={}` would always be empty, adding ~50 bytes of noise per probe response that orchestrators would parse and discard. |
| `probe_dependency` | No | None — the worker has no upstream to probe. |
| `configure_sentry`, SEC-15 hook | No | None — worker has no Sentry. |
| `LIVENESS_TICK_BUDGET_MS` | Yes (duplicated literal) | **Modest** — pulling from the lib closes the only genuine duplication. |
| `READINESS_HEADER` | Yes (duplicated literal) | **Modest** — same. |

**Verdict:** The 18 symbols the worker doesn't use cost transitive deps for zero ergonomic gain; the 2 it does use are stable constants that haven't changed since R1.2 shipped (2026-04-27).

### 3.3 (c) Cross-cutting bug history

We checked the four cross-cutting fixes that landed in the shared lib (or its R2.1.x consumer migrations) and asked: did any of them require a parallel patch in the worker?

| Cross-cutting fix | Required worker patch? |
|---|---|
| **BUG-JD-06 / tz-aware UTC `ReadinessResponse.timestamp`** (R2.1 §5.3, fixed in lib + cascor + canopy) | **No.** Worker's `/v1/health/ready` body has no `timestamp` field. |
| **SEC-15 `before_send` Sentry hook** (cross-service standard since R2.1.5) | **No.** Worker has no Sentry. |
| **R1.1 cardinality bound on Prometheus `endpoint` label** (`UNMATCHED_ENDPOINT_LABEL`) | **No.** Worker has no Prometheus middleware. |
| **R1.2 readiness 503-on-not-ready + `X-Juniper-Readiness` header** | **Yes** — but the worker shipped this independently in R1.3 (juniper-cascor-worker#37) using the same constants. The shared lib was alpha-only at that point so direct adoption was not yet possible. Going forward, if the contract changes the worker would need to chase. |
| **R1.3 worker HTTP probe surface itself** | n/a — this is the worker's own design; the shared lib was deliberately scoped to not include an HTTP server. |

**Net:** 1 of 5 cross-cutting items would have benefited from shared-lib adoption, and that one (R1.2 contract constants) was already absorbed into the worker via the same literal values without operational pain.

---

## 4. Decision

**Do not migrate `juniper-cascor-worker` to the shared `juniper-observability` lib at this time.**

**Rationale:**

1. The worker uses 2 of the lib's 20 public symbols — both stable contract constants.
2. The other 18 symbols are server-side machinery the worker structurally does not need (it has no FastAPI app, no `/metrics` mount, no Sentry, no upstream dependencies to probe, no incoming HTTP business requests to correlate).
3. None of the cross-cutting bug fixes in the R2.1 program required a parallel worker patch; the only contract item that touched both (R1.2 readiness header) was absorbed via literal duplication that has not drifted.
4. The R1.3 design's "keep the image slim" rationale (Option C, `asyncio.start_server`) remains valid — pulling in starlette + pydantic to gain access to two string constants is the wrong trade.

### 4.1 Selective adoption (deferred follow-up)

Optional, low-risk follow-up — **recommended but not blocking R2 closure**:

> Replace the literals in `juniper_cascor_worker/constants.py` and `juniper_cascor_worker/http_health.py` with imports from `juniper_observability` (the **only** lib symbols the worker would import). This adds the transitive dep cost for one purpose: making the contract constants single-sourced.

If pursued, this becomes a tiny worker PR (≤ 10 lines net change) under a separate ticket. **It is not required to close R2.** A reasonable counter-position is "two literal constants are not worth the dep edge" — both choices defensible.

### 4.2 Re-evaluation triggers

The decision should be revisited if **any** of the following becomes true:

- The worker grows a `/metrics` endpoint (would need `PrometheusMiddleware` + `set_build_info`).
- The worker grows a Sentry integration (would benefit from SEC-15 hook).
- The worker starts probing an upstream dependency (would benefit from `probe_dependency`).
- A cross-cutting bug requires a parallel patch in the worker for the second time.
- The shared lib changes a contract constant (`LIVENESS_TICK_BUDGET_MS` or `READINESS_HEADER`) without coordination.

Each trigger should reopen this question; the current "no" is **not** load-bearing past those triggers.

---

## 5. R2 phase exit

With this question resolved, the R2 phase exit gate from the roadmap is:

> **Phase R2 exit gate:** Shared lib published; probes symmetric; WS frames validated in clients/workers; all suites green.

Status:

- ✅ **Shared lib published** — `juniper-observability==0.1.1` on PyPI 2026-04-29 (R2.1).
- ✅ **Worker adoption decision** — this note (R2 gating issue, raised from R2.1 design Q5).
- ⬜ **Probes symmetric** (R2.3) — not started.
- ⬜ **WS frame schema validation in clients/workers** (R2.2) — not started.
- ⬜ **All suites green** — passes per-PR; cross-repo orchestration not gated here.

**R2.1 sub-track is closed; R2.2 and R2.3 remain open.** The gating question that this note resolves is independent of R2.2/R2.3 progress and does not block them.

---

## 6. Action items

1. ✅ Update [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §5 R2 gating issue: link to this note; mark **decided**.
2. Optional, deferred: open a worker PR replacing the two literal constants with `juniper_observability` imports.
3. ✅ No worker code changes required to close R2 phase exit gate on the worker-adoption question.
