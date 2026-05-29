# Juniper Stack Regression Analysis — 2026-05-27

**Author**: Paul Calnon (with Claude Opus 4.7 sub-agent investigation)
**Date**: 2026-05-27
**Repos involved**: juniper-cascor, juniper-cascor-client, juniper-canopy, juniper-deploy
**Stack state at investigation**: docker compose "Up 2 hours"; all containers report `healthy`; canopy training/operational status shows error, WS reconnect loop, Dataset View save / generate / launch fail.

---

## 1. Executive Summary

Three concurrent regressions land in the same observable user surface (the canopy Dataset View tab + the dashboard's "training status" badge). Container health checks pass because each individual service's `/v1/health` endpoint is fine; the failure is at the **cross-service integration layer**.

| # | Layer | Root cause | User-visible symptom | Severity |
|---|---|---|---|---|
| **RC-1** | `juniper-cascor` server / `juniper-cascor-client` WS client | Cascor `/ws/control` fail-closes when no `Origin` header is sent. The canopy-side client (`CascorControlStream` in `juniper-cascor-client`) **does not set an Origin header** on the upgrade request. Cascor's allowlist is hard-coded (no env-var override) to `localhost:8050`. Canopy connects from the container hostname → no Origin → 403. Worker `/ws/v1/workers` deliberately *rejects* Origin (machine-to-machine) so it succeeds. | "WS in reconnect loop" (every 30s); "training/operational status error" (Control Stream Supervisor never connects → dashboard never sees realtime cascor state) | **Critical** — primary cause of the user's report |
| **RC-2** | `juniper-canopy` adapter | `CascorServiceAdapter.get_dataset_swap_events()` calls `self._client._request("GET", "/v1/history/dataset_swaps", …)`, but `juniper-cascor-client` already prepends `/v1` (via `API_VERSION_PATH`) to every `_request` path. Effective URL becomes `/v1/v1/history/dataset_swaps` → cascor 404. | "Backend rejected dataset_swap events fetch: Not Found" log spam + missing dataset-swap event timeline in canopy UI | **Minor** — cosmetic + log noise; doesn't break primary flows |
| **RC-3** | `juniper-deploy` secrets wiring (latent risk; currently masked) | Compose declares two parallel mounts — `juniper_cascor_api_keys` (plural, JSON-list) and `juniper_cascor_api_key` (singular, raw) — and `secrets.example/*.txt` placeholder files. The on-disk asymmetry between `secrets/` (mostly 0-byte) and `secrets.example/` (placeholder JSON list) plus the partial `.env.local` override pattern can produce a state where canopy and cascor disagree on the key format (canopy sends the placeholder, cascor's accept-list is empty → 401). In the current live stack, both ended up resolving to the same `secrets.example/` JSON-list file, so HTTP auth coincidentally works. Once Paul (or `make prepare-secrets`) populates one side without the other, RC-3 surfaces. | None in current stack; would surface as "canopy → cascor 401 on every /v1/* call" after the next partial secrets rotation. | **Latent (high risk if not addressed)** |

**Bottom line**: The user's report is RC-1's full cascade plus RC-2's log spam. Fixing RC-1 alone restores the Dataset View tab's save / generate / launch flows because the buttons depend on the supervisor's connection state for their enable / disable signal and for the post-action state echo.

---

## 2. Reproduction (verbatim commands)

```bash
# Symptom 1: canopy /api/status returns 401 (correct — requires X-API-Key)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8050/api/status
# -> 401  {"detail":"Missing API key. Provide X-API-Key header."}

# Symptom 2: canopy /api/status with the deployed placeholder key -> 200
curl -s -H "X-API-Key: CHANGE_BEFORE_PRODUCTION_USE" http://localhost:8050/api/status
# -> 200  {"is_training":false,...,"pending_dataset":null}
#   ==> CANOPY HTTP AUTH WORKS. Not a regression.

# Symptom 3: canopy /api/dataset (proxies through to cascor) with key -> 200
curl -s -H "X-API-Key: CHANGE_BEFORE_PRODUCTION_USE" http://localhost:8050/api/dataset
# -> 200  {"loaded":false}
#   ==> CANOPY → CASCOR HTTP PROXY WORKS. Not a regression.

# Symptom 4: cascor /ws/control upgrade -> 403 (the actual regression)
docker logs juniper-cascor 2>&1 | grep "Control WS"
# -> 2026-05-27 ... Control WS: no Origin header — rejecting (fail-closed)
# -> WebSocket /ws/control" 403
# -> connection rejected (403 Forbidden)

# Symptom 5: canopy supervisor stuck in reconnect loop
docker logs juniper-canopy 2>&1 | grep -c "Control stream supervisor disconnected"
# -> high count, every 30s

# Symptom 6: double /v1/v1 path
docker logs juniper-cascor 2>&1 | grep "/v1/v1"
# -> 172.20.0.3 - "GET /v1/v1/history/dataset_swaps HTTP/1.1" 404 Not Found
```

---

## 3. RC-1 — Cascor `/ws/control` Origin Fail-Closed Regression

### 3.1 What the regression is

`juniper-cascor` rejects every `/ws/control` upgrade with HTTP 403 because the upgrade carries no `Origin` header and the server-side validator (introduced in PR [#129](https://github.com/pcalnon/juniper-cascor/pull/129) — *feat(ws): control-path security — origin validation, rate limiting, cooldown (P8)*) is intentionally fail-closed against the empty-Origin case.

### 3.2 Server-side evidence (juniper-cascor)

- **Emit point** — `juniper-cascor/src/api/websocket/control_security.py:30`:
  ```python
  logger.info("Control WS: no Origin header — rejecting (fail-closed)")
  ```
- **Allowlist source** — `juniper-cascor/src/api/settings.py:291-297`:
  ```python
  ws_control_allowed_origins: list[str] = [
      "http://localhost:8050",
      "http://127.0.0.1:8050",
      "https://localhost:8050",
      "https://127.0.0.1:8050",
  ]
  ```
- **Live-container introspection** (cross-check inside the running juniper-cascor container):
  ```
  >>> get_settings().ws_control_allowed_origins
  ['http://localhost:8050', 'http://127.0.0.1:8050',
   'https://localhost:8050', 'https://127.0.0.1:8050']
  ```
- **No env-var hook** — the `ws_control_allowed_origins` field has no `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` env mapping; the list is a hard-coded default.
- **Introducing commit**: `daacb6d1fb3f0d1161e8f262249190b34016ada6` — *feat(ws): control-path security — origin validation, rate limiting, cooldown (P8) (#129)* — 2026-04-13.
- **Sister worker endpoint policy is the opposite** — `juniper-cascor/src/api/websocket/worker_stream.py:42-45`:
  ```python
  # Reject connections with Origin header (Section 12.3 — workers are M2M)
  if websocket.headers.get("origin"):
      await websocket.close(code=4003, reason="Origin header not allowed on worker endpoint")
      return
  ```
  This asymmetry is intentional (workers are server-to-server; the dashboard control plane was modeled as browser-originated). It explains why **workers reconnect cleanly** (`worker-1` log: "Registered as worker 88c2a286-…") while **the control supervisor 403s every 30s**.

### 3.3 Client-side evidence (juniper-cascor-client + juniper-canopy)

- **Canopy supervisor** — `juniper-canopy/src/backend/cascor_service_adapter.py:126-130`:
  ```python
  self._stream = CascorControlStream(
      base_url=self._ws_url,
      api_key=self._api_key,
  )
  await self._stream.connect()
  ```
- **WS connect** — `juniper-cascor-client/juniper_cascor_client/ws_client.py:309-316`:
  ```python
  async def connect(self) -> None:
      """Connect to the /ws/control endpoint."""
      url = f"{self.base_url}{WS_CONTROL_PATH}"
      extra_headers = {}
      if self.api_key:
          extra_headers[API_KEY_HEADER_NAME] = self.api_key
      try:
          self._ws = await websockets.connect(url, additional_headers=extra_headers)
  ```
  No `origin=` kwarg is set. The Python `websockets` library will **not** auto-emit an `Origin` header from a non-browser caller. Cascor receives the upgrade with `Origin: <missing>` → `control_security.py:30` → 403.

### 3.4 Why test coverage didn't catch it

- `juniper-cascor/src/tests/unit/api/test_control_security.py:31-33` explicitly tests the no-Origin case **expecting rejection** — so the policy is correctly pinned.
- Integration tests inside cascor's own pytest suite monkeypatch the test WS to inject `Origin: http://localhost:8050`, which **masks** the canopy-side gap: there is no test exercising the *real* canopy → cascor handshake (i.e. an integration test that boots both servers, runs the canopy adapter's `CascorControlStream.connect()` against a real cascor, and asserts the upgrade succeeds).
- juniper-cascor-client likewise has no test that fails when the connect lacks an Origin and the server rejects.

### 3.5 Cascade onto user-visible symptoms

The control supervisor is the canonical realtime channel for:

- training-status events (epoch / phase / FSM transitions)
- candidate-pool snapshot pushes
- dataset-swap acknowledgements
- network-mutation broadcasts

Without it, the canopy dashboard backend never receives the post-action echo for save / generate / launch button clicks, so the UI either (a) stays in "pending" forever, (b) flips to error after a UI-side timeout, or (c) reverts the form to its pre-click state. From the user's perspective: "I clicked save and nothing happened" → "I can't save dataset changes". Same story for generate and launch.

---

## 4. RC-2 — Double `/v1/v1` Dataset Swap Path Bug

### 4.1 Failure

```
juniper-cascor INFO:  172.20.0.3 - "GET /v1/v1/history/dataset_swaps HTTP/1.1" 404 Not Found
juniper-canopy ERROR: get_dataset_swap_events failed: Not Found
juniper-canopy WARNING: Backend rejected dataset_swap events fetch: Not Found
```

### 4.2 Code locations

- **Canopy caller** — `juniper-canopy/src/backend/cascor_service_adapter.py:1069`:
  ```python
  result = self._client._request("GET", "/v1/history/dataset_swaps", params=params)
  ```
- **Client prepends `/v1` already** — `juniper-cascor-client/juniper_cascor_client/client.py:83, 356`:
  ```python
  # __init__
  self.api_url = f"{self.base_url}{API_VERSION_PATH}"   # API_VERSION_PATH = "/v1"
  ...
  # _request
  url = f"{self.api_url}{path}"   # -> http://cascor:8200/v1 + /v1/history/dataset_swaps
  ```
- **Real URL** sent on the wire: `http://juniper-cascor:8200/v1/v1/history/dataset_swaps` → cascor router has no `/v1/v1/...` mount → 404.

### 4.3 Why it didn't ship break-detection

- Canopy `cascor_service_adapter.get_dataset_swap_events` returns `[]` on exception via a broad `try / except` that swallows the 404 and logs a warning. The UI panel that consumes it gracefully shows "no events," so functional tests don't surface the bug.
- No unit / integration test asserts that `_request("GET", path, …)` is invoked with a `/v1`-less path; reviewers see `/v1/history/...` and assume that's the routed path. The fact that *every other* `cascor_service_adapter` callsite passes `/dataset`, `/network`, `/training/status` (no `/v1` prefix) is the actual contract.

### 4.4 Fix surface

Single-line edit in `cascor_service_adapter.py:1069`:

```diff
- result = self._client._request("GET", "/v1/history/dataset_swaps", params=params)
+ result = self._client._request("GET", "/history/dataset_swaps", params=params)
```

Plus a regression test in `juniper-canopy/src/tests/unit/backend/` that monkeypatches `_request` and asserts the path argument starts with `/history/`, not `/v1/`.

---

## 5. RC-3 — Latent: Asymmetric Secrets Wiring in juniper-deploy

### 5.1 What is true in the live stack right now

Both canopy and cascor mounted the *same* file content for `juniper_cascor_api_keys`: 33 bytes containing the JSON-list `["CHANGE_BEFORE_PRODUCTION_USE"]\n` (sourced from `secrets.example/juniper_cascor_api_keys.txt`). cascor's `_parse_api_keys` validator (added in PR [juniper-cascor#311](https://github.com/pcalnon/juniper-cascor/pull/311) — 2026-05-27 14:14 CDT) sees the bare string with no commas and returns `['["CHANGE_BEFORE_PRODUCTION_USE"]']` — a one-element list whose single element is the *literal* JSON-list string. Canopy sends the same literal as `X-API-Key`; it matches; cascor returns 200. HTTP auth works **by coincidence of identical placeholder rendering**.

Live-container introspection inside cascor:
```
>>> get_settings().api_keys
['["CHANGE_BEFORE_PRODUCTION_USE"]']
```
Curl confirmation:
```
curl -H 'X-API-Key: ["CHANGE_BEFORE_PRODUCTION_USE"]' http://localhost:8201/v1/dataset -> 200
curl -H 'X-API-Key: CHANGE_BEFORE_PRODUCTION_USE'   http://localhost:8201/v1/dataset -> 401 Invalid API key
```

### 5.2 Why it's a latent risk anyway

- `juniper-deploy/secrets/juniper_cascor_api_keys.txt` is on-disk **0 bytes** (created empty by an earlier `make prepare-secrets` invocation), while `secrets.example/juniper_cascor_api_keys.txt` is 33 bytes (JSON-list placeholder). Whether cascor mounts the 0-byte or the 33-byte file depends entirely on whether the launching shell exported `JUNIPER_CASCOR_API_KEYS_FILE=./secrets/juniper_cascor_api_keys.txt` (or used `--env-file .env.local`).
- The `.env.local` override pattern documented in memory (`reference_juniper_deploy_local_secrets_env_2026-05-10`) only overrides a *subset* of `*_FILE` env vars. If a developer runs `make monitor` directly (which loads only `.env.observability`), every secret falls back to `secrets.example/` defaults. If they run `docker compose --env-file .env.local up`, the *partial* override produces an asymmetric mount (canopy holds the example placeholder, cascor's accept-list is the empty file → "auth disabled" on cascor but "auth required" on canopy from canopy's perspective).
- The canopy `internal_api_headers()` helper (PR [juniper-canopy#265](https://github.com/pcalnon/juniper-canopy/pull/265)) only injects the *canopy* key on dashboard self-calls. Browser-side AJAX (if any callsite still uses raw `fetch()` instead of routing through the Dash callback) would skip the helper entirely and 401. This is the user's "can't save dataset changes" symptom **if** the Dash callbacks ever degrade to client-side fetch (which is a stated Phase D / future-frontend risk in `notes/CAN_013_INTEGRATION_MODE_DESIGN.md`).
- The juniper-deploy PR cluster on 2026-05-27 (#87 → #93) was specifically iterating on the secrets shape (raw vs JSON-list; populated vs empty placeholder; what `make prepare-secrets` emits). The system is in an actively-evolving state and is one mis-touched secret file away from breaking again.

### 5.3 Recommended scope

Out of scope for the immediate fix (the live stack works HTTP-auth-wise). In scope for RC-3 follow-up:

1. Standardize on a single placeholder shape (the comma-CSV form `key1,key2` works for both cascor's new `_parse_api_keys` and the historic juniper-data parser; JSON-list works only post-cascor#311).
2. Document the exact `--env-file` pattern that aligns canopy + cascor + data + worker secrets symmetrically.
3. Have `make prepare-secrets` either populate *all* compose-referenced secret files or none; today it touches a strict subset (memory: `project_make_prepare_secrets_incomplete_2026-05-10`).
4. Add a deploy-side acceptance test that brings up the stack and asserts canopy → cascor /v1/dataset returns 200 with the chosen placeholder.

---

## 6. Why Container Healthchecks Are Misleading

| Container | Healthcheck | Passes? | Why integration is still broken |
|---|---|---|---|
| `juniper-cascor` | `GET /v1/health` from localhost inside container | ✅ | `/v1/health` is `EXEMPT_PATH_PREFIXES`; doesn't exercise auth or `/ws/control` |
| `juniper-canopy` | `GET /v1/health` from localhost inside container | ✅ | Same — exempt path, no upstream check |
| `juniper-data` | `GET /v1/health` | ✅ | Independent of canopy ↔ cascor link |
| `juniper-cascor-worker` | `GET /v1/health/ready` (added in juniper-deploy#89) | ✅ | Reaches all the way to the WS to cascor, but workers use `/ws/v1/workers` which **rejects** Origin (no fail-closed gap) → workers register fine |

**Action**: add an integration healthcheck on canopy that probes the supervisor's `is_connected` state (currently exposed via the dashboard but not via `/v1/health`). If the supervisor has been disconnected for > 60s, the healthcheck should fail. This would have caught RC-1 within one minute of the supervisor going down. Tracked as deploy-side follow-up.

---

## 7. Affected User-Facing Symptoms → Root Cause Map

| User report | Root cause | Cascade path |
|---|---|---|
| "canopy training/operational status is error" | RC-1 | Supervisor disconnect → dashboard backend's `_ServiceTrainingMonitor.is_training` falls back to REST polling but the FSM-status badge widget waits on the WS `state_change` event for its source of truth; without it, the widget displays the configured "stale data" error state. |
| "ws fails to connect, appears to be in reconnection loop" | RC-1 | Direct: `cascor_service_adapter.py:144-149` `ControlStreamSupervisor._connect_loop` logs "Control stream supervisor disconnected" every 30s. |
| "unable to save dataset related changes to meta-parameters" | RC-1 (cascade) | Dataset View save handler sends `set_params` through the supervisor's WS path (`cascor_service_adapter.py:114-119`). With supervisor disconnected, `set_params` raises `JuniperCascorConnectionError("Control stream not connected")` → form error. |
| "unable to generate a new dataset based on the new meta-parameters" | RC-1 (cascade) | Same — the generate button's Dash callback chains save → generate; save fails first. |
| "unable to launch cascor network training from canopy" | RC-1 (cascade) | Launch sends `command` through the supervisor; supervisor down → command error. |
| Background log: `Backend rejected dataset_swap events fetch: Not Found` | RC-2 | Direct: double `/v1` path → cascor 404. |
| (Not user-reported, but latent) inter-service 401 after partial secrets rotation | RC-3 | Asymmetric mount + non-uniform placeholder shape. |

---

## 8. Pinpoint Source Locations & Commits

### 8.1 Files that need to change (preview of fix surface)

- **`juniper-cascor-client/juniper_cascor_client/ws_client.py:316`** — extend `CascorControlStream.connect()` (and the sibling at line 124) to accept and forward an `origin` parameter to `websockets.connect`.
- **`juniper-cascor-client/juniper_cascor_client/ws_client.py:294-303`** — extend `CascorControlStream.__init__` to take `origin: Optional[str] = None` and read default from `JUNIPER_CASCOR_WS_ORIGIN` (or similar) env var.
- **`juniper-canopy/src/backend/cascor_service_adapter.py:126-130`** — pass `origin=<configured>` when constructing `CascorControlStream`.
- **`juniper-canopy/src/backend/cascor_service_adapter.py:1069`** — strip the leading `/v1` from the `get_dataset_swap_events` path.
- **`juniper-canopy/src/config/settings.py`** (or wherever canopy Settings live) — expose a `cascor_ws_origin: str = "http://juniper-canopy:8050"` (with env-var alias) so deploy can override.
- **`juniper-cascor/src/api/settings.py:291-297`** — change `ws_control_allowed_origins` from a hard-coded literal to a field with env-var alias `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` so deploy can extend the list without rebuilding the image.
- **`juniper-deploy/docker-compose.yml`** — add `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://juniper-canopy:8050,http://localhost:8050,http://127.0.0.1:8050` (or equivalent) to the cascor service env block, and `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://juniper-canopy:8050` to the canopy service env block.

### 8.2 Commits and PRs that landed the regression / surrounding context

| When | Repo | PR | Role |
|---|---|---|---|
| 2026-04-13 | juniper-cascor | #129 (commit `daacb6d`) | Introduced `control_security.py`; the Origin fail-closed policy. *Caused RC-1.* |
| 2026-05-10 | juniper-canopy | #265 | Added `internal_api_headers()`; injected key into 44 dashboard self-call sites. *Masks RC-3 as long as both sides use the same placeholder.* |
| 2026-05-26 | juniper-cascor | #309 | Isolated Settings from developer's local `.env`. *Background context for why test envs are now reproducible.* |
| 2026-05-27 | juniper-cascor | #311 | `_parse_api_keys` accepts None / empty / csv / list. *Stops the restart loop; works in concert with the JSON-list placeholder.* |
| 2026-05-27 | juniper-deploy | #87 | Populate cascor auth token + mount `juniper_cascor_api_keys`. *Set up the current mount layout.* |
| 2026-05-27 | juniper-deploy | #91 / #92 / #93 | Iterated on placeholder shape (JSON-list vs raw). *Why both files now have the JSON-list literal.* |
| (none yet) | juniper-cascor-client | — | No PR has ever added `origin=` to `CascorControlStream`. *RC-1's client-side gap.* |

---

## 9. Confidence and Outstanding Questions

- **High confidence**: RC-1 root cause and fix surface (every step from emit-point to canopy-call-site was inspected; live container introspection corroborates each layer).
- **High confidence**: RC-2 root cause (single-line bug, confirmed by reading both sides of the URL concatenation).
- **High confidence**: RC-3 latent risk (corroborated by direct file inspection inside both containers + on the deploy host).
- **Medium-low confidence open question**: whether the dashboard widget's "training/operational status error" display is a *deliberately rendered* error state when the supervisor is down (suggesting a status callback path) or an *uninitialized* state. Doesn't affect remediation — RC-1 fix will resolve either case — but is worth a follow-up note in canopy's frontend status-badge component to confirm and add a test.
- **Open question**: should the cascor `/ws/control` policy keep fail-closed against missing Origin, or should it (a) require a header-or-API-key pair (any of the two is enough) or (b) accept an explicit `Origin: http://juniper-canopy:8050` injected by canopy? The remediation plan presents both. Recommended approach is "explicit Origin from canopy + env-driven allowlist on cascor" (no policy weakening; just makes the allowlist deployment-aware).

---

## 10. References

- `juniper-cascor/src/api/websocket/control_security.py:30`
- `juniper-cascor/src/api/websocket/worker_stream.py:42-45`
- `juniper-cascor/src/api/settings.py:291-297` (allowlist)
- `juniper-cascor-client/juniper_cascor_client/ws_client.py:294-326` (control stream)
- `juniper-cascor-client/juniper_cascor_client/client.py:83, 356` (`/v1` prepending)
- `juniper-canopy/src/backend/cascor_service_adapter.py:121-152` (supervisor reconnect loop)
- `juniper-canopy/src/backend/cascor_service_adapter.py:1069` (double-`/v1` bug)
- `juniper-canopy/src/security.py:79` (`Missing API key` emit)
- `juniper-canopy/src/middleware.py:70-150` (SecurityMiddleware)
- `juniper-canopy/src/main.py:287-289` (middleware registration)
- `juniper-deploy/docker-compose.yml:147-208` (cascor service block)
- `juniper-deploy/docker-compose.yml:364-412` (canopy service block)
- `juniper-deploy/docker-compose.yml:640-662` (top-level secrets block)

Companion plan document: [`STACK_REGRESSION_REMEDIATION_PLAN_2026-05-27.md`](STACK_REGRESSION_REMEDIATION_PLAN_2026-05-27.md).
