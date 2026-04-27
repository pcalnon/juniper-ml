# R1.2 — Health Probe Semantics + Status-Code Propagation

**Status:** PROPOSED (awaiting review before implementation)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-27
**Roadmap item:** [METRICS_MONITORING_ROADMAP_2026-04-25.md §R1.2](METRICS_MONITORING_ROADMAP_2026-04-25.md)
**Seed findings:** seed-02 (`/health/ready` returns 200 when degraded), seed-03 (liveness probe is a no-op)
**Composite severity:** 4 (release-blocking)
**Affected repos:** juniper-data, juniper-cascor, juniper-canopy, juniper-deploy
**Predecessor PRs (merged 2026-04-27):** juniper-data#49, juniper-cascor#143, juniper-canopy#178 (R1.1 cardinality)

---

## 1. Problem statement

The current health-probe surface across the three Juniper server applications has two correctness defects:

1. **`/health/ready` returns HTTP 200 even when `overall="degraded"`** — load balancers and Kubernetes readiness probes cannot use the status code to drive traffic shedding. They must parse the JSON body, which Kubernetes does not do. Result: a service with a known-unhealthy dependency continues to receive traffic.

2. **`/health/live` is a no-op** — every server's liveness endpoint returns `{"status": "alive"}` unconditionally. If the application has wedged (event-loop frozen, training process deadlocked, Dash worker stuck), the liveness probe still passes and the orchestrator never restarts the pod.

Compounding these defects, the Helm chart in juniper-deploy has **inconsistent probe-path wiring**: some readiness probes point at `/v1/health` (the combined/no-op endpoint) instead of `/v1/health/ready`. So even when a fix lands in the apps, the orchestrator may not benefit unless Helm is updated in lockstep.

This design closes all three issues with one coordinated change.

---

## 2. Goals

- Liveness probe accurately reflects "process is responsive on its primary code path."
- Readiness probe HTTP status code is sufficient to drive Kubernetes / LB / nginx upstream decisions without parsing the body.
- The contract is identical across cascor, canopy, and data, so downstream tooling (probe wiring, dashboards, runbooks) does not have per-service exceptions.
- Existing `/v1/health` (combined) endpoint preserves current behavior — backwards compatible.
- Helm probes are corrected and aligned with the new contract in the same release.

## 3. Non-goals

- Bidirectional probing (cascor probing canopy, etc.) — that's R2.3 (seed-15).
- Worker liveness — that's R1.3 (seed-04).
- Shared probe-model library — that's R2.1 (seed-06).
- Async-safe `urlopen()` replacement in canopy probe — that's R4.2 (seed-10). However, R4.2 lands easily on top of R1.2 if scheduled adjacently.

---

## 4. Contract definition

### 4.1 `/v1/health` (combined; unchanged)

Backwards-compatibility endpoint. **No semantic change.** Returns `{"status": "ok", "version": <semver>}` with HTTP 200. Always succeeds while the process can respond. Existing dashboards and external integrations keep working.

### 4.2 `/v1/health/live` (liveness — strengthened)

**Purpose:** Detect a wedged process the orchestrator should restart.

**Behavior:**

- Run a per-service "liveness tick" (see §5 per-service paths) with a strict timeout.
- If the tick completes successfully within budget → **HTTP 200**, body `{"status": "alive", "tick": "<service>", "duration_ms": <int>}`.
- If the tick fails or times out → **HTTP 503**, body `{"status": "unresponsive", "tick": "<service>", "error": "<short reason>", "duration_ms": <int>}`.

**Tick budget:** 250 ms wall-clock. Helm `timeoutSeconds` stays at 5–10 so the wrapper has headroom. The tick must not perform network I/O — it exercises only in-process state.

**Idempotency:** Tick must be safe to call at the configured `periodSeconds` (10–15 s) and must not allocate or block more than incidentally.

### 4.3 `/v1/health/ready` (readiness — corrected status codes)

**Purpose:** Tell orchestrator whether to send traffic to this pod.

**Status semantics:**

| Internal `overall` | Meaning                                                                                | HTTP code | Body `status` |
|--------------------|----------------------------------------------------------------------------------------|:---------:|---------------|
| `ready`            | All required dependencies healthy                                                      |    200    | `"ready"`     |
| `degraded`         | All required deps healthy; at least one **optional** dep unhealthy or `not_configured` |    200    | `"degraded"`  |
| `unready`          | At least one **required** dep unhealthy                                                |    503    | `"unready"`   |

**Required vs optional** is decided per service in §5.

**Header:** `X-Juniper-Readiness: ready|degraded|unready` mirrors the body, so probe logs and `kubectl get pods` can surface state without curl-piping into jq.

**Backwards compat:** `degraded` continues to return 200 (LB keeps traffic flowing). The breaking change is that **previously-passing `unhealthy` deps now return 503**. Helm `failureThreshold` (currently 3–5) absorbs transient blips; only sustained unhealth shifts traffic.

---

## 5. Per-service implementation specifications

### 5.1 juniper-data

**Liveness tick (`/v1/health/live`):**

- Sync stat the storage directory configured by `settings.storage_path`. If path resolves to a directory → tick OK. (No file I/O beyond `Path.is_dir()`.)
- Optional: also assert the FastAPI app's `state` carries `settings`, proving config injection completed.

**Readiness deps:**

| Dep             | Required? | Probe                                  | Healthy condition          |
|-----------------|:---------:|----------------------------------------|----------------------------|
| Dataset storage |  **Yes**  | `Path(settings.storage_path).is_dir()` | dir exists and is readable |

Single-required-dep service. `degraded` is unreachable; only `ready` or `unready`.

### 5.2 juniper-cascor

**Liveness tick (`/v1/health/live`):**

- Read the `lifecycle` attribute from `request.app.state` and call a new `lifecycle.is_alive() -> bool` accessor. Implementation: returns `True` if the lifecycle manager's monotonic heartbeat counter has incremented within the last `2 × periodSeconds` (i.e., the training loop's monitor callback is firing).
- The heartbeat counter is bumped inside `TrainingMonitor` on every state transition AND on a per-second timer tick maintained by the training loop. If both stop, liveness fails.

**Readiness deps:**

| Dep                                       |               Required?                | Probe                                       | Healthy condition |
|-------------------------------------------|:--------------------------------------:|---------------------------------------------|-------------------|
| Lifecycle manager                         |                **Yes**                 | `app.state.lifecycle is not None`           | not None          |
| JuniperData (when `JUNIPER_DATA_URL` set) | **Yes** if URL set, **N/A** if not set | HTTP `GET /v1/health/live` with 2 s timeout | 2xx               |

When `JUNIPER_DATA_URL` is unset (local dev), data dep is skipped entirely (not "optional, degraded"); `not_configured` collapses to `ready`.

### 5.3 juniper-canopy

**Liveness tick (`/v1/health/live`):**

- Verify the WebSocket manager's `connections_active` gauge is reachable (i.e., the manager is mounted). Pure in-process attribute fetch.
- Verify the Dash app object is bound to `app.state.dash_app` (if Dash is the dashboard backend in current configuration).

**Readiness deps:**

| Dep               | Required? | Probe                                         | Healthy condition |
|-------------------|:---------:|-----------------------------------------------|-------------------|
| JuniperData       | Optional  | `GET <data_url>/v1/health/live` 2 s timeout   | 2xx               |
| JuniperCascor     | Optional  | `GET <cascor_url>/v1/health/live` 2 s timeout | 2xx               |
| WebSocket manager |  **Yes**  | `app.state.websocket_manager is not None`     | not None          |

Canopy is a dashboard. With both data and cascor down, canopy is still useful to operators (shows cached state, logs in). So the upstreams are optional → `degraded` when unhealthy. Only the in-process WebSocket manager being unbound makes canopy actually unable to serve, so it's the sole required dep.

---

## 6. Coordinated juniper-deploy Helm changes

The Helm chart currently has these issues; **all must be fixed in lockstep with the app PRs.**

| Service        | Current liveness path | Current readiness path       | Fix                                                          |
|----------------|-----------------------|------------------------------|--------------------------------------------------------------|
| juniper-data   | `/v1/health`          | `/v1/health`                 | liveness → `/v1/health/live`; readiness → `/v1/health/ready` |
| juniper-cascor | `/v1/health`          | `/v1/health/ready` (correct) | liveness → `/v1/health/live`                                 |
| juniper-canopy | `/v1/health`          | `/v1/health`                 | liveness → `/v1/health/live`; readiness → `/v1/health/ready` |

`docker-compose.yml` healthchecks (line 105, 157, 238 etc.) currently hit `/v1/health` directly via `urllib.request.urlopen`. Compose has no live/ready distinction — keep these on `/v1/health` (they're effectively "is the container alive at all"). No change to compose.

**Probe timing budgets (unchanged from current):** `failureThreshold: 3–5`, `timeoutSeconds: 5–10`, `periodSeconds: 10–15`. The 250 ms tick fits comfortably; the 2 s upstream-probe timeout fits within the 5 s readiness budget.

---

## 7. Implementation sequence

Per the roadmap rule "upstream before downstream":

| Order | Repo           | Branch                                | What ships                                                                  |
|-------|----------------|---------------------------------------|-----------------------------------------------------------------------------|
| 1     | juniper-data   | `metrics-mon-seed-02-probe-semantics` | Liveness tick + readiness 503-on-unready                                    |
| 2     | juniper-cascor | `metrics-mon-seed-02-probe-semantics` | `lifecycle.is_alive()` heartbeat + liveness tick + readiness 503-on-unready |
| 3     | juniper-canopy | `metrics-mon-seed-02-probe-semantics` | WS-manager-bound liveness tick + readiness 503-on-unready                   |
| 4     | juniper-deploy | `metrics-mon-seed-02-probe-paths`     | Helm chart probe-path corrections (after all three apps merged)             |

Order matters: if Helm flips first, liveness/readiness paths point at endpoints whose new behavior hasn't shipped — possible probe failure on apply. Apps first, then Helm. Each app PR is independently mergeable because the existing endpoints are unchanged in path; the new endpoints (`/live` already exists as a no-op, `/ready` already returns body) just gain stricter behavior.

---

## 8. Backwards compatibility

| Audience               | What changes                                                      | Mitigation                                                                                                                                                                   |
|------------------------|-------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| External monitoring    | `/v1/health/ready` may now return 503 instead of 200              | Documented in PR body and CHANGELOG; existing alerting rules that page on `status:"degraded"` text continue to fire because body still contains `degraded`/`unready` strings |
| Helm chart consumers   | Probe paths corrected in `values.yaml` defaults                   | Major chart version bump; release notes call out the wiring change                                                                                                           |
| Compose users          | No change — compose still hits `/v1/health` (ok)                  | n/a                                                                                                                                                                          |
| Existing dashboards    | None directly — body schema preserved; status code is new info    | n/a                                                                                                                                                                          |
| `kubectl describe pod` | New `X-Juniper-Readiness` header surfaces in probe failure detail | Reduces RCA time                                                                                                                                                             |

---

## 9. Testing matrix

Each repo's PR must add tests covering:

| Behavior to assert                                               | data | cascor | canopy |
|------------------------------------------------------------------|:----:|:------:|:------:|
| Liveness 200 when tick succeeds                                  | ✓    | ✓      | ✓      |
| Liveness 503 when tick raises                                    | ✓    | ✓      | ✓      |
| Liveness 503 when tick exceeds 250 ms budget                     | ✓    | ✓      | ✓      |
| Liveness body includes `tick` and `duration_ms` keys             | ✓    | ✓      | ✓      |
| Readiness 200 when all required deps healthy                     | ✓    | ✓      | ✓      |
| Readiness 503 when a required dep unhealthy                      | ✓    | ✓      | ✓      |
| Readiness 200 with `degraded` when optional dep unhealthy        | —    | —      | ✓      |
| Readiness `not_configured` (e.g. unset URL) collapses to `ready` | —    | ✓      | ✓      |
| `X-Juniper-Readiness` header matches body status                 | ✓    | ✓      | ✓      |
| Heartbeat staleness triggers liveness 503 (cascor only)          | —    | ✓      | —      |

`—` = not applicable for that service.

For juniper-deploy:

- `helm template` snapshot test confirms each deployment's `livenessProbe.httpGet.path == "/v1/health/live"` and `readinessProbe.httpGet.path == "/v1/health/ready"`.
- One end-to-end test (in `tests/`) asserts a deployed cascor pod with simulated upstream-data unhealthiness yields readiness 503 via `kubectl exec`.

---

## 10. Risks and mitigations

| Risk                                                                              | Likelihood | Mitigation                                                                                                                                    |
|-----------------------------------------------------------------------------------|:----------:|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Liveness 503 trips Helm `failureThreshold` and pods restart-loop                  |   Medium   | Stage in `values-demo.yaml` first; widen `failureThreshold` to 6 if production observes flap; tick budget 250 ms is conservative              |
| Readiness 503 takes pods out of LB rotation when a transient upstream blip occurs |   Medium   | `failureThreshold: 3` already requires 30 s sustained failure (10 s period) before traffic withdrawal — same as today's body-based monitoring |
| Helm path correction lands before app PRs merge                                   |    Low     | Merge order enforced (apps first, Helm last); juniper-deploy PR explicitly references all three app PRs as merged                             |
| Heartbeat coupling adds new failure mode in cascor                                |    Low     | Heartbeat is a single counter increment per loop iteration; failure mode is "counter not incrementing" which IS the symptom we want to detect |
| New `X-Juniper-Readiness` header collides with existing custom header             | Negligible | Header name is service-specific                                                                                                               |

---

## 11. Test fixtures and helpers

A shared fixture pattern (per-repo, not yet a shared lib — that's R2.1) for simulating "tick failure":

```python
# pytest helper — applied per repo
@pytest.fixture
def slow_tick(monkeypatch):
    """Force the liveness tick to exceed budget so readiness/liveness can be tested."""
    async def _slow(*args, **kwargs):
        await asyncio.sleep(1.0)  # > 250 ms budget
        return None
    monkeypatch.setattr("<module>._liveness_tick", _slow)
    return _slow
```

Each repo's PR includes its variant. After R2.1, this can be promoted to a shared test util.

---

## 12. Decision log

- **Why `_unmatched`-style label vs `unready` body status?** Label values must be stable for Prometheus; body strings can be richer. We use `unready` (not `unhealthy`) in the body to mirror the probe contract terminology rather than the dependency-level `DependencyStatus.status` enum.
- **Why 250 ms tick budget?** Headroom against the 5 s readiness `timeoutSeconds`; well below the 10 s liveness timeout. Pure in-process work should complete in < 10 ms; the 250 ms cap catches CPU starvation and event-loop stalls.
- **Why optional vs required deps split?** Canopy must remain useful in degraded mode (operator console access during partial outage). Data and cascor are the actual data-plane services where unhealthy upstream means the pod cannot do its job.
- **Why not implement async upstream probes here?** That's R4.2 (blocking `urlopen` in async). Slipping it in here expands blast radius. Sequencing R4.2 right after R1.2 closes the gap quickly.

---

## 13. Open questions before kickoff — RESOLVED 2026-04-27

1. **Canopy liveness anchor:** `app.state.websocket_manager` is the required dep. (Confirmed; design unchanged.)
2. **Cascor heartbeat plumbing:** `TrainingMonitor` does **not** expose a usable monotonic counter. Add a fresh `_liveness_counter: int` on the lifecycle object, incremented on (a) every `TrainingMonitor` state transition and (b) a per-second timer tick maintained by the training loop. `lifecycle.is_alive()` consults the counter timestamp.
3. **juniper-deploy chart version bump:** **Major** — `values.yaml` defaults change for `livenessProbe.httpGet.path` and (for data + canopy) `readinessProbe.httpGet.path`. Operators with overridden `values-*.yaml` files are unaffected; operators relying on chart defaults must re-render.
4. **Change notices:** Per-repo `CHANGELOG.md` entry under each repo's "Unreleased" section. Wording cross-references the design doc and the four PR numbers (one per repo) so readers can follow the rollout.

---

## 14. Acceptance criteria

R1.2 is **done** when:

- All three app PRs (data, cascor, canopy) merged with the new tick + 503-on-unready contract.
- juniper-deploy chart PR merged with corrected probe paths.
- All four PRs have tests covering §9 matrix; coverage matrix entry in [METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md §10](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) updated.
- AGENTS.md / CLAUDE.md per repo updated to document the new probe contract.
- Roadmap §9 row R1.2 status flips to **done** with PR links.
- A short retrospective note added to `notes/code-review/` summarizing what shipped and any deferred items spawned.
