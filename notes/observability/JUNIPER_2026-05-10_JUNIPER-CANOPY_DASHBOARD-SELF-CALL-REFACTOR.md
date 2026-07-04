# Canopy Dashboard Self-Call Refactor — Deferred Design

**Author**: Paul Calnon
**Date**: 2026-05-10
**Status**: Deferred. Required in the future when one or more trigger conditions are met (see §6).
**Related PRs**:
- `pcalnon/juniper-canopy#265` — Option B (X-API-Key injection) shipped 2026-05-10
- `pcalnon/juniper-canopy/notes/...` — Option C (this design)

This document captures the design, trade-offs, and trigger conditions for replacing canopy's Dash-dashboard HTTP self-calls with direct in-process function calls. It is the long-term resolution of the Bug 4 class — Option B (X-API-Key injection in HTTP self-calls) is the stepping-stone fix that ships first; this refactor is deferred behind it because the immediate operational pain is the auth-broken dashboard, not the perf cost.

---

## 1. What the architecture looks like today

The Dash dashboard runs in the same Python process as canopy's FastAPI app. Browser-side Dash callbacks fire in response to interval triggers (timers) or user interactions. Each callback runs **server-side** in the canopy process (Flask's WSGI worker thread pool, sitting inside FastAPI/Starlette).

Roughly 44 of these callbacks shape their work as:

```python
url = self._api_url("/api/status")  # -> "http://127.0.0.1:8050/api/status"
response = requests.get(url, headers=internal_api_headers(), timeout=...)
data = response.json()
return html.Div(...)  # rendered to browser
```

So every panel refresh: callback → `requests` → loopback TCP socket → uvicorn → Starlette routing → SecurityMiddleware → request-id → CORS → Prometheus → FastAPI route handler → JSON serialize → wire → `requests` parse → callback continues.

The FastAPI route handler itself is in the same process and the same module tree as the callback; nothing about the data needs to leave the process.

## 2. What Option C looks like

Drop the HTTP indirection. The Dash callbacks call the route-handler functions directly:

```python
# Before
url = self._api_url("/api/status")
response = requests.get(url, headers=internal_api_headers(), timeout=...)
data = response.json()

# After
from api.status import get_status      # FastAPI route handler
data = get_status(request_state)       # direct Python call, returns dict
```

For async route handlers:

```python
import asyncio
data = asyncio.run(get_status_async(request_state))
# or
data = self._call_async(get_status_async, request_state)  # via a thread-bridge helper
```

## 3. Why we did Option B first

| Concern | Option B (HTTP + X-API-Key) | Option C (direct call) |
|---|---|---|
| Closes the immediate Bug 4 breakage | yes | yes |
| Change surface | 1 helper module + 44 call-site appends | 44 call-sites rewritten + per-handler shim + import surgery |
| Risk of breaking unrelated panels | low (mechanical edit) | medium (each handler's deps must be reconstructed) |
| Async/sync impedance handling | none needed | required for async FastAPI handlers |
| FastAPI Depends() injection rewiring | none needed | required for handlers that use Depends |
| Per-call overhead removed | no | ~1–4 ms |
| Threadpool double-occupancy removed | no | yes |
| Metric noise from synthetic traffic removed | no | yes |

Option B is the right ROI now. The dashboard is mostly single-user / low-frequency; the throughput win from C is small in absolute terms and the change surface is 3–4× larger.

## 4. The cost of staying on Option B

These are real but not yet load-bearing:

1. **Per-call latency** — ~1–4 ms HTTP overhead per panel refresh. For a 10-panel dashboard refreshing at 1 Hz, that's ~10–40 ms/s of CPU spent on self-traffic plumbing. Invisible to a single user; matters under concurrent users.
2. **Threadpool contention** — every Option-B self-call occupies *two* worker slots simultaneously: the Dash callback thread blocking on `requests.get`, plus the FastAPI worker handling its own request. Effective concurrency is halved relative to Option C.
3. **Metric pollution** — `PrometheusMiddleware` counts every self-call as a real HTTP request. A meaningful fraction of `juniper_canopy_http_requests_total`, `juniper_canopy_http_request_duration_seconds`, and the corresponding Grafana panels is currently the dashboard talking to itself. SLO calibration and burn-rate alerts are calibrated against a metric stream that includes synthetic internal traffic.
4. **Stack-trace clarity** — errors raised in the route handler get wrapped in `requests.RequestException` at the call site, which obscures the original traceback. Direct calls preserve full Python frames across the boundary.
5. **CPU** — JSON serialize + deserialize round-trip per call. A few percent of one core in steady state on a busy dashboard. Negligible single-user; relevant if the dashboard ever runs on a constrained host.

## 5. Implementation surface

When Option C lands, it touches roughly these axes:

### 5.1 Inventory of self-call sites

`src/frontend/dashboard_manager.py` (~19) plus 9 component modules (~25 more). Each call has the shape `requests.X(self._api_url(<path>), <kwargs>)`. The destination path determines which FastAPI handler is the target.

A `path → handler` map is the prerequisite work: it's mechanical but tedious because handlers are scattered across `src/api/`.

### 5.2 Sync vs. async handlers

Inspect each route handler's `def` vs `async def`:

- **Sync handler from sync Dash callback**: trivial — just call it.
- **Async handler from sync Dash callback** (most common): need an event-loop bridge. Three options, in increasing complexity:
  - `asyncio.run(handler(...))` — clean but creates a new event loop per call, expensive.
  - A canopy-owned background event loop + `asyncio.run_coroutine_threadsafe`. Better perf, requires a small `loop_bridge.py` helper.
  - Migrate the Dash callback to async-aware (Dash supports async callbacks as of dash >= 2.16, but the framework's threading model is still primarily sync).
- **Async handler from async Dash callback** (rare today): direct `await`. Cleanest.

### 5.3 FastAPI dependency injection

Route handlers that take `Request`, `Depends(get_settings)`, `BackgroundTasks`, `Response`, `HTTPException`, etc. need their dependencies constructed manually at the direct call-site. Two strategies:

- **Refactor handler to plain function** — move FastAPI-specific bits into a thin wrapper. Underlying business logic becomes callable directly.
- **Reconstruct dependencies at call-site** — `get_settings()` is idempotent and cached, so calling it directly is fine. `Request` is harder; usually the dashboard doesn't need a real Request object, but if any handler reads `request.headers` or `request.state`, that's a refactor.

The right pattern is option 1 — push the business logic down a layer (call it `core/<feature>.py`), keep the FastAPI layer thin, and both the route and the Dash callback can call the core function.

### 5.4 Middleware-derived state

Some handlers may implicitly depend on:

- **`request_id` ContextVar** set by `RequestIdMiddleware` — used for log correlation. Direct calls won't have a request_id unless the Dash callback sets one.
- **Auth principal** set by `SecurityMiddleware` — used to authorize access. Direct calls from the dashboard implicitly run as "internal trust"; we'd need to decide whether dashboard callbacks have unconditional access or whether they assume a synthetic admin principal.
- **Rate limiter counters** decremented by `SecurityMiddleware` — direct calls don't go through rate limiting. Probably fine (dashboard is trusted), but worth a `# noqa: rate-limit-bypass` style note.

### 5.5 Lifecycle and startup ordering

The dashboard's `requests.get` self-calls today implicitly wait for FastAPI startup (the request returns 503 / connection refused before startup). Direct calls bypass this — the dashboard can call a handler before `app.startup` hooks ran. The Dash callback layer needs to wait on the same readiness signal that the deploy stack's `/v1/health/ready` waits on.

### 5.6 Tests

Today, dashboard-callback tests use `unittest.mock.patch("requests.get")` to stub responses. Option C breaks all of these. Migration:

- Tests that exercise the *callback* logic but don't need the real handler should mock the handler function directly.
- Tests that exercise the *handler* logic from inside a callback should be moved into the handler's own test module.

This is healthy — the two concerns become testable independently — but it is a real migration cost (~50 callsites of `patch("requests.get")` per a quick `git grep`).

### 5.7 Per-component shim

To keep the change incremental, introduce a `frontend/internal_api.py::internal_call(path, method="GET", body=None)` helper that maps `path → handler` and delegates. Then call-sites change from:

```python
response = requests.get(self._api_url("/api/status"), headers=..., timeout=...)
data = response.json()
```

to:

```python
data = internal_call("/api/status")
```

This decouples the migration: implement the dispatch inside `internal_call`, swap call sites mechanically, and individual handlers can be migrated to direct-call one at a time inside the helper while everything else keeps working.

## 6. Trigger conditions for promoting Option C from deferred to active

Don't do Option C "because it's cleaner." Do it when one or more of the following becomes real:

1. **Concurrent-user dashboard exhausts the Flask threadpool.** Symptom: `werkzeug` logs `[WARNING] WSGI request queue full` or panels stall waiting for callbacks. Today the dashboard is essentially single-user.
2. **SLO calibration becomes meaningfully off because of self-traffic.** Symptom: burn-rate alerts firing for self-traffic, or `juniper_canopy_http_request_duration_seconds` p95 dominated by self-traffic to the point that user-facing latency SLIs are obscured. Audit suggestion: split metrics by `source={internal,external}` label first; if internal is >30% of traffic, Option C becomes attractive.
3. **A panel's refresh rate needs to drop below ~500 ms.** The ~1–4 ms HTTP overhead becomes a meaningful fraction of the per-call budget. Today panels refresh at 1–5 s; sub-second refresh isn't on any roadmap.
4. **Test mock churn.** If we're regularly patching `requests.get` in new tests, the indirection's debt is growing. Tracking heuristic: more than ~20% of new canopy tests touch `patch("requests.get")`.
5. **Stack-trace obscurity costs an incident.** If we ever have a real post-mortem where the cause was hidden behind `requests.RequestException`, that's a trigger.
6. **The dashboard moves to a different deployment topology** — e.g., separate Dash process from FastAPI process. In that case Option C is impossible (the callbacks really do need to make a network call to reach the API); the helper from §5.7 becomes the only point of indirection and Option B remains the right shape.

## 7. Out of scope for this document

- **Switching the dashboard to client-side data fetching** (browser hits `/api/status` directly). Different architectural shift; would obviate the entire self-call problem but introduces a CORS / cookie / API-key-in-browser security surface that the current "server-side rendered Dash" model deliberately avoids.
- **Replacing Dash entirely** with a different frontend stack. Out of scope.
- **Threadpool tuning** (raising Flask's worker count). A short-term mitigation if §6.1 triggers but Option C isn't ready yet; not a permanent fix.

## 8. References

- Option B: `pcalnon/juniper-canopy#265` (PR with `frontend/internal_api.py` + 44 site injection)
- Bug 4 capture: `juniper-ml/notes/observability/IMAGE_BUILD_BUGS_2026-05-10.md` (Bug 4 section, if/when added)
- Canopy middleware: `juniper-canopy/src/middleware.py` and `juniper-canopy/src/canopy_constants.py` (`EXEMPT_PATHS`, `EXEMPT_PATH_PREFIXES`)
- FastAPI handlers entrypoint: `juniper-canopy/src/main.py:223+` (mounts) and `juniper-canopy/src/api/` (handler modules)
- Dash callback layer: `juniper-canopy/src/frontend/dashboard_manager.py` (orchestrator) and `juniper-canopy/src/frontend/components/` (panel components)
- Performance analysis underlying the trade-off table: in-session conversation 2026-05-10 ("Estimate option B vs C perf effect")

---

## TL;DR

Option B (X-API-Key injection in HTTP self-calls) ships *now*, in `juniper-canopy#265`. It closes the auth-broken-dashboard bug with the smallest possible surface.

Option C (drop the HTTP indirection, call handlers directly) is the *correct* long-term shape — better latency tail, no threadpool double-occupancy, no synthetic metric traffic, clearer stack traces — but it's a real refactor (~3–4× the surface of Option B) and the operational pain it solves is not yet present. Triggers in §6. Implementation sketch in §5. Don't do it until at least one trigger is met.
