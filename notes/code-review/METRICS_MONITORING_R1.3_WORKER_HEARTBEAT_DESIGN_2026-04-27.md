# R1.3 — Worker Liveness + Heartbeat Enrichment

**Status:** PROPOSED (awaiting review before implementation)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-27
**Roadmap item:** [METRICS_MONITORING_ROADMAP_2026-04-25.md §R1.3](METRICS_MONITORING_ROADMAP_2026-04-25.md)
**Seed finding:** seed-04 (no worker liveness or heartbeat instrumentation)
**Composite severity:** 4 (release-blocking)
**Affected repos:** juniper-cascor-worker, juniper-cascor, juniper-deploy
**Predecessors merged 2026-04-27:**
- juniper-data#51, juniper-cascor#147, juniper-canopy#183, juniper-deploy#35 (R1.2 probe semantics)

---

## 1. Problem statement

The cascor-worker pod has **two distinct gaps** the orchestrator cannot work around:

1. **No HTTP health endpoint.** The Helm chart wires worker liveness/readiness as `exec: kill -0 1`, which only verifies that PID 1 exists. A wedged event loop, a deadlocked task executor, or a stuck WebSocket reconnect loop all leave PID 1 alive — Kubernetes never restarts the pod, and operators discover the failure only when a task times out client-side.

2. **Sparse heartbeat payload.** The worker→cascor heartbeat (`MSG_TYPE_HEARTBEAT`) carries `worker_id` and `timestamp` only. Cascor's `WorkerRegistry` can detect "worker last spoke N seconds ago" but cannot answer the diagnostic questions that drive runbook decisions: *Is the worker idle? How many tasks are in flight? When did it last complete one? Is it OOM-bound?* These answers belong in the heartbeat, not in a separate query path.

A third, smaller gap surfaces when the first two are fixed: cascor's `/v1/workers` route exposes a worker list but does not yet surface the enriched fields, so the heartbeat enrichment is invisible to operators until the read path is updated.

This design closes all three.

---

## 2. Goals

- Worker pod is liveness-checked and readiness-checked by Kubernetes via `httpGet`, not `kill -0 1`.
- Heartbeat payload carries enough state for runbook decisions without separate RPCs.
- Cascor's worker registry stores the enriched fields; `/v1/workers` surfaces them.
- The change is consistent with R1.2: liveness tick within a strict budget; readiness 503-on-not_ready; `X-Juniper-Readiness` header.
- No new heavy dependency on the worker (it stays a slim compute agent).

## 3. Non-goals

- Worker training-loop instrumentation (per-epoch timing, GPU utilization details) — that's R4.4 and rides on top of this change.
- Replacing the WS heartbeat with HTTP polling — keep the WS channel as the primary cascor↔worker liveness signal; HTTP is for k8s and external monitoring.
- Bidirectional probes (cascor probing worker via HTTP) — workers are ephemeral; pull-based discovery would couple cascor too tightly to k8s.

---

## 4. Contract changes

### 4.1 New worker-side HTTP endpoints

The worker exposes a small HTTP server on a dedicated port (default `8210`, configurable via `CASCOR_WORKER_HEALTH_PORT`):

| Endpoint            | Behavior                                                                                                                  | Status codes |
|---------------------|---------------------------------------------------------------------------------------------------------------------------|:------------:|
| `GET /v1/health`    | Backwards-compatible no-op. `{"status": "ok", "worker_id": "<id-or-null>", "version": "<ver>"}`                            | 200 always   |
| `GET /v1/health/live` | Tick (in-process, ≤ 250 ms): WS connection bound AND heartbeat loop bumped a counter within the last `2 × heartbeat_interval` seconds. Returns `{"status": "alive", "tick": "juniper-cascor-worker", "duration_ms": N}`. | 200 / 503    |
| `GET /v1/health/ready` | Required deps: WS connected AND registration handshake completed (i.e., `MSG_TYPE_REGISTRATION_ACK` received). Returns `{"status": "ready" | "not_ready", ...}` with `X-Juniper-Readiness` header. | 200 / 503    |

The worker is a **leaf** in the dependency graph — it has no upstream services to probe — so `degraded` is unreachable for the worker. Only `ready` and `not_ready` are emitted.

### 4.2 Enriched heartbeat payload

`build_heartbeat()` (cascor side) and the worker-side `_heartbeat_loop()` body both gain four fields:

```python
{
    "type": "heartbeat",
    "worker_id": "<id>",
    "timestamp": 1745816400.123,
    # NEW (R1.3):
    "in_flight_tasks": 0,            # int — count of tasks the worker is currently executing
    "last_task_completed_at": 1745816350.0,  # float|null — unix ts of most recent task completion
    "rss_mb": 412.7,                 # float — resident set size, in MB
    "tasks_completed": 1234,         # int — running total since worker start (existing-on-cascor; now reported)
    "tasks_failed": 12,              # int — running total since worker start
}
```

Backwards compatibility: cascor's `WorkerRegistration` already has `tasks_completed`, `tasks_failed`, `active_task_id`, `last_heartbeat`. The new fields slot in without changing existing semantics. Older workers that don't send the new fields are accepted with default values (`in_flight_tasks=0`, `last_task_completed_at=None`, `rss_mb=None`).

### 4.3 Cascor `/v1/workers` route surfaces new fields

The route's `_serialize_worker()` helper now includes the enriched fields. Operators see the full picture in one GET.

---

## 5. Worker-side implementation specification

### 5.1 HTTP listener — three options

**Option A — FastAPI + uvicorn (heavyweight, consistent).**

- Pro: same stack as juniper-data / cascor / canopy.
- Con: adds ~10 MB of dependencies to the slim worker image.
- Risk: FastAPI startup time on small VMs adds 200–400 ms to worker boot.

**Option B — aiohttp.web (medium).**

- Pro: lighter than FastAPI; works natively with the worker's asyncio loop.
- Con: new dependency; the project doesn't already use aiohttp.

**Option C — `asyncio.start_server` + minimal HTTP/1.1 handler (recommended).**

- Pro: zero new dependencies. The worker already runs an asyncio loop. ~50 lines of code in a new module `juniper_cascor_worker/http_health.py`.
- Con: hand-rolled handler must reject malformed requests safely. Mitigated by: (a) only accepting `GET` on two paths, (b) rejecting any body, (c) bounded read with a strict timeout, (d) bind to localhost-only by default with explicit opt-in to listen on 0.0.0.0 for k8s probes via `CASCOR_WORKER_HEALTH_BIND` env var.
- Risk: subtle protocol bugs. Mitigated by a unit test suite that exercises malformed requests, oversize headers, and concurrent connections.

**Recommendation: Option C.** The endpoint surface is intentionally tiny (two GET paths returning small JSON bodies) and the cost of pulling in FastAPI/aiohttp for that is disproportionate. We retain the option to swap the implementation if the surface grows.

### 5.2 Tick mechanics

Worker maintains a `_liveness_counter: int` and `_liveness_last_tick_at: float` updated every time the heartbeat loop sends a message OR a task completes (success or failure). The tick:

```python
def _liveness_tick(self) -> None:
    if self._connection is None or not self._connection.connected:
        raise RuntimeError("websocket connection not bound")
    stale_after = 2 * self.config.heartbeat_interval
    if (time.monotonic() - self._liveness_last_tick_at) > stale_after:
        raise RuntimeError(f"heartbeat counter stale (> {stale_after}s)")
```

Mirrors the cascor lifecycle pattern from R1.2 §5.2.

### 5.3 Resource sampling for `rss_mb`

Use `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0` on Linux (kilobytes → MB). On macOS the unit is bytes; provide a one-line platform branch. **Never** require a heavy dep like `psutil` for this — it's a cross-platform API smell and we'd be adding it for a single field.

### 5.4 Task accounting fields

Worker maintains:

- `_in_flight_tasks: int` — incremented when a task starts, decremented when it ends (use `try/finally` so failures still decrement).
- `_last_task_completed_at: float | None` — set to `time.time()` at task completion or failure.
- `_tasks_completed: int`, `_tasks_failed: int` — counters bumped on terminal task state.

Reads of these fields for the heartbeat must be cheap (plain reads on attributes). They live on the `Worker` instance, protected by the asyncio event loop's single-thread guarantee — no lock needed.

### 5.5 Graceful shutdown

On `SIGTERM`, the worker:

1. Stops accepting new tasks (existing behavior).
2. Drains in-flight tasks (existing behavior).
3. Sends a final heartbeat with `in_flight_tasks=0` to confirm clean drain.
4. Stops the HTTP health listener last so k8s sees readiness 503 → withdraws traffic before the WS connection closes.

---

## 6. Cascor-side changes

### 6.1 `WorkerRegistration` enrichment

Add fields:

```python
@dataclass
class WorkerRegistration:
    # ... existing fields ...
    in_flight_tasks: int = 0
    last_task_completed_at: float | None = None
    rss_mb: float | None = None
```

`record_heartbeat()` becomes `record_heartbeat(in_flight_tasks=0, last_task_completed_at=None, rss_mb=None)` — keyword-only, with defaults so older workers' minimal heartbeats still register correctly.

### 6.2 `/v1/workers` serialization

`_serialize_worker()` includes the new fields. New keys in the JSON output; existing keys unchanged.

### 6.3 Stale-worker reaper

`WorkerRegistry.get_stale_workers(threshold_s)` already exists. No semantic change — it consults `last_heartbeat` only. The new fields are diagnostic, not used for staleness math.

---

## 7. Helm chart changes (juniper-deploy)

`worker-deployment.yaml`:

```yaml
# BEFORE (current main, after R1.2):
livenessProbe:
  exec:
    command: ["kill", "-0", "1"]
readinessProbe:
  exec:
    command: ["kill", "-0", "1"]

# AFTER (this PR):
livenessProbe:
  httpGet:
    path: /v1/health/live
    port: health
  initialDelaySeconds: 15
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 5
readinessProbe:
  httpGet:
    path: /v1/health/ready
    port: health
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
ports:
  - name: health
    containerPort: 8210
    protocol: TCP
```

`values.yaml` gains:

```yaml
worker:
  healthcheck:
    enabled: true
    port: 8210
    liveness:
      path: /v1/health/live
      initialDelaySeconds: 15
      periodSeconds: 15
      timeoutSeconds: 5
      failureThreshold: 5
    readiness:
      path: /v1/health/ready
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```

Chart version bump: `1.0.0 → 1.1.0` (minor; non-breaking — workers without the listener still pass `exec: kill -0 1` until the worker image upgrade lands, but operators must re-deploy after both worker image and chart upgrade).

Actually — the probe-path change is breaking for operators running an old worker image with a new chart. To avoid that: **gate the new probe via `worker.healthcheck.enabled`** with default `false` for the chart cut, then flip to `true` after the worker image with the listener is published. This lets operators upgrade in either order.

---

## 8. Implementation sequence

| Order | Repo                  | Branch                                   | What ships |
|-------|-----------------------|------------------------------------------|------------|
| 1     | juniper-cascor        | `metrics-mon-seed-04-worker-heartbeat`   | `WorkerRegistration` enrichment + `/v1/workers` serialization (accepts old + new heartbeat shapes) |
| 2     | juniper-cascor-worker | `metrics-mon-seed-04-worker-heartbeat`   | HTTP health listener + enriched heartbeat payload + task accounting |
| 3     | juniper-deploy        | `metrics-mon-seed-04-worker-probes`      | Helm chart probe wiring with `worker.healthcheck.enabled` flag (default `false` initially) |
| 4     | juniper-deploy        | follow-up                                | Flip `worker.healthcheck.enabled` default to `true` once the worker image with the listener is stable in staging |

Order is enforced because: cascor must accept the new fields **before** workers send them (forward compat); workers must implement the listener **before** Helm's httpGet probes become defaults. Step 4 is a separate flip to avoid coupling the cut from step 3 with the staging burn-in.

---

## 9. Backwards compatibility

| Audience                                  | Impact                                                    | Mitigation |
|-------------------------------------------|-----------------------------------------------------------|------------|
| Workers running the old image             | Send minimal heartbeat. Cascor accepts; new fields appear as null/0 in `/v1/workers`. | Keyword-default acceptance in `record_heartbeat()` |
| Cascor running the old image              | Receives enriched heartbeat from new worker. Unknown fields ignored by JSON unmarshaller (existing behavior). | n/a |
| Helm chart consumers                      | `worker.healthcheck.enabled=false` by default (step 3) avoids breaking pods running old worker images. | Explicit flip in step 4 after burn-in. |
| `kubectl describe pod` / k8s events       | New `httpGet` probe events appear once the flag flips.    | Documented in CHANGELOG. |
| Operators using `gh workers list`-style scripts | New JSON keys appear on `/v1/workers`; existing keys unchanged. | Document in cascor CHANGELOG. |

---

## 10. Testing matrix

| Behavior to assert                                                               | worker | cascor | deploy |
|----------------------------------------------------------------------------------|:------:|:------:|:------:|
| Worker HTTP listener binds and serves `GET /v1/health`                           | ✓      | —      | —      |
| Liveness 200 when WS connected + heartbeat counter fresh                         | ✓      | —      | —      |
| Liveness 503 when WS disconnected                                                | ✓      | —      | —      |
| Liveness 503 when heartbeat counter stale (> 2 × interval)                       | ✓      | —      | —      |
| Readiness 503 before registration ack received                                   | ✓      | —      | —      |
| Readiness 200 + `X-Juniper-Readiness=ready` after registration                   | ✓      | —      | —      |
| Malformed HTTP request rejected without crashing the worker                      | ✓      | —      | —      |
| Concurrent probe requests handled (both return 200 within tick budget)           | ✓      | —      | —      |
| Heartbeat payload includes new fields after task completion                      | ✓      | —      | —      |
| `WorkerRegistration` accepts heartbeat with new fields                           | —      | ✓      | —      |
| `WorkerRegistration` accepts heartbeat WITHOUT new fields (forward compat)       | —      | ✓      | —      |
| `/v1/workers` JSON includes new fields                                           | —      | ✓      | —      |
| `helm template` snapshot: worker Deployment uses `httpGet` when flag enabled     | —      | —      | ✓      |
| `helm template` snapshot: worker Deployment uses `exec` when flag disabled       | —      | —      | ✓      |
| `rss_mb` value is a non-negative float                                           | ✓      | —      | —      |
| Graceful shutdown sends final heartbeat with `in_flight_tasks=0`                 | ✓      | —      | —      |

---

## 11. Risks and mitigations

| Risk                                                                          | Likelihood | Mitigation |
|-------------------------------------------------------------------------------|:----------:|------------|
| Hand-rolled HTTP handler has a parser bug that hangs the worker               | Low        | Strict GET-only handler; bounded read with timeout; reject any non-trivial request; comprehensive malformed-request unit tests |
| HTTP listener bind conflicts with cascor pod on shared host                   | Low        | Default port `8210` (cascor uses 8200/8201); operators set via `CASCOR_WORKER_HEALTH_PORT` |
| `rss_mb` reading wrong unit on macOS                                          | Medium     | Platform branch in `_sample_rss_mb()`; unit test exercises both code paths via monkeypatch |
| Workers running old image lose HTTP probes when chart flag flips              | Medium     | Two-step rollout (steps 3 then 4 in §8); flag default `false` until burn-in |
| Heartbeat payload growth slows scaled-out worker pools (1000+ workers)        | Low        | Payload still < 200 bytes; cascor TLS connection cost dominates |
| Stale `last_task_completed_at` after worker reset confuses operators          | Low        | Explicit `null` when no task has completed since boot (not `0.0`) |

---

## 12. Open questions before kickoff

1. **HTTP listener choice (Option A/B/C)**: confirm Option C (`asyncio.start_server` + minimal handler), or override to A/B?
2. **Default health port (8210)**: confirm, or pick a different port?
3. **`rss_mb` on macOS**: do we test macOS at all in CI? If not, the platform branch can ship without a macOS unit test (assumed Linux-only).
4. **Two-step Helm rollout** (steps 3 + 4 in §8): acceptable, or prefer single PR with `worker.healthcheck.enabled=true` default?
5. **Chart version**: minor (`1.0.0 → 1.1.0`) or major (`1.0.0 → 2.0.0`) given the probe wiring changes? Probes are gated by the new flag; default behavior unchanged in step 3, so I'd argue minor.

---

## 13. Acceptance criteria

R1.3 is **done** when:

- juniper-cascor accepts both old and new heartbeat shapes; `/v1/workers` surfaces enriched fields. PR merged.
- juniper-cascor-worker exposes `/v1/health[/live|/ready]` on the configurable port; heartbeat payload enriched. PR merged.
- juniper-deploy chart adds `worker.healthcheck.enabled` flag with `httpGet` wiring; `helm template` snapshot test asserts both flag states. Chart bumped. PR merged.
- A follow-up PR flips the flag default after staging burn-in. PR merged.
- AGENTS.md / CLAUDE.md per repo updated with the new worker probe contract.
- Roadmap §9 R1.3 status flips to **done** with PR links.
