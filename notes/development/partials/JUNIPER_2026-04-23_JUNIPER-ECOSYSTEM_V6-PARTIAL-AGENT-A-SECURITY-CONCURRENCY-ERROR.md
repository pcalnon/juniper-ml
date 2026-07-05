# V6 Partial — Agent A: Security, Concurrency, Error Handling

**Sections Covered**: 4 (Security), 17 (Concurrency), 18 (Error Handling)
**Generated**: 2026-04-22
**Source Verification**: All items verified against live codebase

---

### Issue Remediations, Section 4

#### SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel

**Current Code**: `juniper_data/api/security.py:59` — `return api_key in self._api_keys` (Python set membership)
**Root Cause**: Set membership test short-circuits on first matching character position, leaking key length/prefix via response timing.
**Cross-References**: SEC-01 = JD-SEC-02

**Approach A — hmac.compare_digest Loop**:
- *Implementation*: Replace `api_key in self._api_keys` with a loop: `return any(hmac.compare_digest(api_key, k) for k in self._api_keys)`. Import `hmac` from stdlib.
- *Strengths*: Constant-time comparison per key; stdlib-only, no new deps; trivial 3-line change.
- *Weaknesses*: O(n) in number of configured keys (acceptable — typically 1-5 keys).
- *Risks*: Negligible — `hmac.compare_digest` is battle-tested.
- *Guardrails*: Add unit test asserting constant-time behavior with valid/invalid keys of same length.

**Recommended**: Approach A because it's a 3-line stdlib fix with zero risk.

---

#### SEC-02: Rate Limiter Memory Unbounded — DoS Vector

**Current Code**: `juniper_data/api/security.py:116` — `self._counters: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))` with no eviction.
**Root Cause**: Each unique client key (IP) creates a permanent entry; attacker can exhaust memory by rotating source IPs.

**Approach A — TTLCache Replacement**:
- *Implementation*: Replace `defaultdict` with `cachetools.TTLCache(maxsize=10_000, ttl=window_seconds)`. Add `cachetools` to dependencies.
- *Strengths*: Automatic expiry and size cap; well-maintained library; drop-in replacement.
- *Weaknesses*: Adds external dependency.
- *Risks*: Minimal — cachetools is widely used and lightweight.
- *Guardrails*: Log warning when cache reaches 80% capacity; add max-size to Settings class.

**Approach B — OrderedDict with Periodic Cleanup**:
- *Implementation*: Use `collections.OrderedDict` with timestamp tracking. Add `_maybe_cleanup()` method that evicts entries older than `window_seconds`, called every N requests.
- *Strengths*: No new dependencies; follows cascor's `ConnectionRateLimiter._maybe_cleanup` pattern.
- *Weaknesses*: Manual cleanup logic; slightly more code.
- *Risks*: Cleanup frequency tuning needed.
- *Guardrails*: Cap at 10k entries with hard eviction of oldest.

**Recommended**: Approach A because `cachetools.TTLCache` is purpose-built for this exact use case.

---

#### SEC-03: No Per-IP WebSocket Connection Limiting (cascor)

**Current Code**: `src/api/settings.py:27-28` — only `ws_max_connections: 50` (global cap), no per-IP limit.
**Root Cause**: Cascor's WebSocket settings lack the per-IP limiting that canopy already implements via `max_connections_per_ip`.

**Approach A — Add per-IP Setting and Enforcement**:
- *Implementation*: Add `ws_max_connections_per_ip: int = 5` to cascor's `Settings` class. In WebSocket accept handlers (`worker_stream.py`, `training_stream.py`), add `check_per_ip_limit()` check before accepting, mirroring canopy's `websocket_manager.py:269-283` pattern.
- *Strengths*: Consistent with canopy's proven implementation; configurable via env var.
- *Weaknesses*: Requires touching multiple WS endpoint handlers.
- *Risks*: Must handle IPv6 and proxy `X-Forwarded-For` correctly.
- *Guardrails*: Log per-IP rejections at WARNING level; include IP in structured log for monitoring.

**Recommended**: Approach A because canopy's implementation is already proven and the pattern can be directly reused.

---

#### SEC-04: Sync Dataset Generation Blocks Event Loop

**Current Code**: `juniper_data/api/routes/datasets.py:107` — `arrays = generator_class.generate(params)` — synchronous call in async handler.
**Root Cause**: Generator computation (potentially CPU-intensive) runs on the async event loop thread, blocking all concurrent requests.
**Cross-References**: CONC-04, JD-PERF-01, BUG-JD-10

**Approach A — asyncio.to_thread Wrapper**:
- *Implementation*: Replace `arrays = generator_class.generate(params)` with `arrays = await asyncio.to_thread(generator_class.generate, params)`.
- *Strengths*: Single-line change; Python 3.9+ stdlib; non-blocking.
- *Weaknesses*: Thread pool has limited concurrency (default 40 threads).
- *Risks*: Thread-safety of generator classes must be verified (generators appear stateless).
- *Guardrails*: Add timeout via `asyncio.wait_for()` to prevent runaway generation.

**Recommended**: Approach A because it's a one-line fix addressing the root cause directly.

---

#### SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy)

**Current Code**: `/ws/training` and `/ws/control` endpoints in `canopy/src/main.py` accept WebSocket connections without checking `Origin` header.
**Root Cause**: Missing Origin validation allows malicious web pages to connect to the WebSocket endpoints using the victim's browser session.

**Approach A — Origin Validation Middleware**:
- *Implementation*: Add `validate_origin(websocket, allowed_origins)` function that checks `websocket.headers.get("origin")` against a configurable allowlist. Call before `websocket.accept()` in all WS endpoints. Add `ws_allowed_origins: list[str] = ["http://localhost:8050"]` to canopy Settings.
- *Strengths*: Standard CSWSH mitigation; configurable per deployment.
- *Weaknesses*: Must maintain origin allowlist across environments.
- *Risks*: Overly restrictive origins can break legitimate cross-origin dashboards.
- *Guardrails*: Default to localhost origins for development; require explicit config for production.

**Recommended**: Approach A because Origin validation is the standard defense against CSWSH.

---

#### SEC-06: No Auth on Canopy WS Endpoints

**Current Code**: Canopy WebSocket endpoints (`/ws/training`, `/ws/control`) accept unauthenticated connections.
**Root Cause**: WebSocket authentication was not implemented when endpoints were added.

**Approach A — Token-Based WS Auth**:
- *Implementation*: Accept auth token via `Sec-WebSocket-Protocol` header subprotocol negotiation. Validate against canopy's API key settings before `websocket.accept()`. Reject with 403 if invalid.
- *Strengths*: Standards-compliant; doesn't expose token in URL.
- *Weaknesses*: Requires client-side changes to pass auth header.
- *Risks*: Must coordinate with cascor-client and dashboard JavaScript code.
- *Guardrails*: Support opt-in via settings: `ws_auth_enabled: bool = False` initially, toggled to `True` when all clients updated.

**Recommended**: Approach A because it avoids the query-param exposure problem (see SEC-13).

---

#### SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest

**Current Code**: `TrainingStartRequest` — `_ALLOWED_TRAINING_PARAMS` whitelist filters key names but values remain `Dict[str, Any]`.
**Root Cause**: Value types/ranges are not validated, allowing injection of arbitrary objects.

**Approach A — Pydantic Field Validators**:
- *Implementation*: Define a `TrainingParams` Pydantic model with typed fields for each allowed param (e.g., `learning_rate: float = Field(gt=0, le=10.0)`). Replace `params: Dict[str, Any]` with `params: TrainingParams`.
- *Strengths*: Compile-time type safety; automatic validation; self-documenting API.
- *Weaknesses*: Requires defining all valid parameter ranges upfront.
- *Risks*: Must keep in sync with cascor algorithm's actual parameter requirements.
- *Guardrails*: Add `model_config = ConfigDict(extra="forbid")` to reject unknown params.

**Recommended**: Approach A because Pydantic validation is the project's standard pattern for request models.

---

#### SEC-10: Sentry `send_default_pii=True` (juniper-data)

**Current Code**: Sentry configuration sets `send_default_pii=True`, leaking API keys in request headers to Sentry.
**Root Cause**: Default PII setting was enabled during development and never disabled.

**Approach A — Disable Default PII**:
- *Implementation*: Change `send_default_pii=True` to `send_default_pii=False`. Add a `before_send` hook to explicitly strip `X-API-Key` and `Authorization` headers from event data.
- *Strengths*: Simple config change; `before_send` provides defense-in-depth.
- *Weaknesses*: May lose some debugging context in Sentry events.
- *Risks*: Negligible.
- *Guardrails*: Log a sample (non-PII) of Sentry events locally to verify no data loss.

**Recommended**: Approach A because PII leakage to third-party services is an unacceptable default.

---

#### SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler

**Current Code**: `src/snapshots/snapshot_serializer.py:828` — `pickle.loads(python_state_bytes)` with `# trunk-ignore(bandit/B301)` comment.
**Root Cause**: Arbitrary code execution via crafted pickle payload in snapshot files.

**Approach A — RestrictedUnpickler**:
- *Implementation*: Create `class JuniperUnpickler(pickle.Unpickler)` that overrides `find_class()` to only allow `torch.*`, `numpy.*`, `collections.*`, `builtins.{dict,list,tuple,set,frozenset,int,float,str,bool,bytes,complex}`. Replace `pickle.loads(data)` with `JuniperUnpickler(io.BytesIO(data)).load()`.
- *Strengths*: Blocks arbitrary code execution while allowing legitimate torch/numpy deserialization; stdlib-only.
- *Weaknesses*: Allowlist must be maintained as torch/numpy evolve.
- *Risks*: Existing snapshots with custom classes will fail to load (breaking change for existing snapshot files).
- *Guardrails*: Add migration tool to re-serialize existing snapshots; log blocked class access attempts.

**Approach B — Switch to safetensors Format**:
- *Implementation*: Replace pickle-based serialization with `safetensors` library for tensor data, JSON for metadata.
- *Strengths*: Eliminates pickle entirely; safetensors is designed for secure ML model serialization.
- *Weaknesses*: Significant refactor; breaks all existing snapshots; new dependency.
- *Risks*: safetensors may not support all torch state dict types.
- *Guardrails*: Dual-format support during migration with deprecation warnings for pickle format.

**Recommended**: Approach A for immediate security fix; Approach B as long-term migration target.

---

#### SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy)

**Current Code**: `src/main.py:2109-2127` — `/ws` endpoint has API key auth but misses `validate_origin()` and `check_per_ip_limit()` that `/ws/training` and `/ws/control` implement.
**Root Cause**: Inconsistent security application — generic endpoint was added later without copying security checks from established endpoints.

**Approach A — Apply Consistent Security Checks**:
- *Implementation*: Add `validate_origin()` and `check_per_ip_limit()` calls to `/ws` handler, matching the pattern from `/ws/training` and `/ws/control`.
- *Strengths*: Trivial copy-paste of existing security logic; consistent behavior.
- *Weaknesses*: Code duplication (mitigated by future refactor to shared decorator).
- *Risks*: None — these checks are already proven on other endpoints.
- *Guardrails*: Extract common WS security checks into a shared `_validate_ws_connection()` helper.

**Recommended**: Approach A because consistency with existing endpoints is the minimum viable fix.

---

#### SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`)

**Current Code**: `src/main.py:2392` — `authkey` accepted as query parameter, logged by web servers, saved in browser history/referrer.
**Root Cause**: Authentication was implemented via query params for convenience during development.

**Approach A — Sec-WebSocket-Protocol Header**:
- *Implementation*: Accept auth token via `Sec-WebSocket-Protocol` subprotocol negotiation header instead of query param. Client sends `Sec-WebSocket-Protocol: bearer, <token>`, server validates and echoes accepted subprotocol.
- *Strengths*: Not logged in URL; not visible in browser history/referrer; standard approach.
- *Weaknesses*: Requires client-side code changes.
- *Risks*: Must coordinate with all callers.
- *Guardrails*: Support both methods during deprecation period with warning log for query-param usage.

**Approach B — POST-based Token Exchange**:
- *Implementation*: Client POSTs credentials to `/api/remote/auth`, receives a short-lived token, then connects WS with the token.
- *Strengths*: Clean separation of auth and connection; tokens can be short-lived.
- *Weaknesses*: Two-step connection flow adds latency and complexity.
- *Risks*: Token storage and expiry management needed.
- *Guardrails*: Token TTL ≤ 60 seconds; single-use tokens.

**Recommended**: Approach A because it's simpler and doesn't require additional infrastructure.

---

#### SEC-14: Internal Exception Messages Leaked to Clients

**Current Code**: `src/main.py:996, 2055, 2076, 2371, 2411` — 5 endpoints return `str(e)` in JSON responses.
**Root Cause**: Exception messages may contain internal paths, library versions, or connection strings.

**Approach A — Generic Error Responses**:
- *Implementation*: Replace `str(e)` with generic messages like `"Internal server error"`. Log the full exception at ERROR level server-side with request context.
- *Strengths*: Prevents information disclosure; proper separation of concerns.
- *Weaknesses*: Reduces client-side debugging information.
- *Risks*: Negligible — detailed errors should never leak to clients.
- *Guardrails*: Include a unique error ID in the response that correlates with server logs.

**Recommended**: Approach A because information disclosure to clients is a standard security anti-pattern.

---

#### SEC-15: Cascor Sentry `send_default_pii=True`

**Current Code**: `src/api/observability.py:176` and `src/main.py:129` — both init sites set `send_default_pii=True`.
**Root Cause**: Same issue as SEC-10 but in cascor; API keys leak in headers to Sentry.

**Approach A — Disable and Add before_send Filter**:
- *Implementation*: Set `send_default_pii=False` at both init sites. Add `before_send` callback to strip sensitive headers (`X-API-Key`, `Authorization`).
- *Strengths*: Same proven approach as SEC-10 fix.
- *Weaknesses*: Minor loss of debugging context.
- *Risks*: None.
- *Guardrails*: Verify with Sentry test event that no PII leaks after change.

**Recommended**: Approach A — identical to SEC-10 fix for consistency.

---

#### SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware

**Current Code**: `juniper_data/api/app.py:121` — Prometheus metrics endpoint mounted as ASGI sub-app, bypassing `SecurityMiddleware`.
**Root Cause**: ASGI sub-app mounts are not processed by router-level middleware.

**Approach A — Wrap Metrics App with Auth**:
- *Implementation*: Create a thin ASGI wrapper around the Prometheus app that checks for a metrics-specific API key or allows only from configured trusted IPs (e.g., Prometheus scraper IP).
- *Strengths*: Prevents unauthorized metrics scraping; minimal code.
- *Weaknesses*: Must configure scraper IP/key.
- *Risks*: Blocking Prometheus scraper if misconfigured.
- *Guardrails*: Default to allowing localhost; log blocked scrape attempts.

**Approach B — Move to Router-Level Endpoint**:
- *Implementation*: Replace ASGI sub-app mount with a regular FastAPI route (`@app.get("/metrics")`) that goes through the standard middleware chain.
- *Strengths*: Consistent auth for all endpoints; no special handling needed.
- *Weaknesses*: Prometheus client library may not integrate cleanly as a route handler.
- *Risks*: Must ensure Prometheus text format response is correct.
- *Guardrails*: Test with Prometheus scraper after migration.

**Recommended**: Approach A because it's less invasive and metrics endpoints commonly have separate auth.

---

#### SEC-17: Snapshot `snapshot_id` Path Param Unchecked Traversal Chars

**Current Code**: `src/api/lifecycle/manager.py:883-904` and `src/api/routes/snapshots.py:48-64` — no regex rejecting `../` or special characters in `snapshot_id`.
**Root Cause**: Insufficient input validation on user-supplied path parameter; glob-then-filter approach limits exposure but violates defense-in-depth.

**Approach A — Regex Validation**:
- *Implementation*: Add `snapshot_id: str = Path(pattern=r"^[a-zA-Z0-9_-]+$")` to the FastAPI path parameter declaration, or validate with `re.fullmatch(r"[a-zA-Z0-9_-]+", snapshot_id)` at the start of the handler.
- *Strengths*: Simple regex; blocks all traversal attempts at API boundary.
- *Weaknesses*: May need to accommodate snapshot IDs with additional characters (e.g., dots, colons).
- *Risks*: Existing snapshots with non-conforming IDs would become inaccessible.
- *Guardrails*: Audit existing snapshot IDs to determine actual character set before applying regex.

**Recommended**: Approach A because input validation at the API boundary is the correct defense-in-depth layer.

---

#### SEC-18: `_decode_binary_frame` No Bounds Check on Malformed Binary Data

**Current Code**: `juniper_cascor_worker/worker.py:330-343` — trusts header-encoded `ndim`, `shape`, `dtype_len` without bounds checking before `np.frombuffer`.
**Root Cause**: Binary frame parser trusts server-sent header fields; crafted frames can cause OOM via unbounded numpy allocation.

**Approach A — Bounds Validation**:
- *Implementation*: Add validation before numpy operations: `assert ndim <= 10`, `assert math.prod(shape) * dtype_itemsize <= 1_073_741_824` (1GB), `assert dtype_len <= 64`. Raise `ValueError` on violation.
- *Strengths*: Prevents OOM attacks; validates all three attack vectors; simple arithmetic checks.
- *Weaknesses*: Requires determining reasonable bounds for each field.
- *Risks*: Legitimate large tensors could be rejected — but 1GB per frame is generous.
- *Guardrails*: Make bounds configurable via worker settings; log rejected frames at WARNING.

**Recommended**: Approach A because bounds checking on untrusted binary input is essential.

---

### Issue Remediations, Section 17

#### CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager

**Current Code**: `websocket_manager.py:278-282` — `current = self._per_ip_counts.get(source_ip, 0)` then `self._per_ip_counts[source_ip] = current + 1` without lock.
**Root Cause**: Non-atomic read-modify-write on shared dict allows two concurrent connections from same IP to both pass the limit check.
**Cross-References**: Canopy-specific, no other section refs.

**Approach A — asyncio.Lock**:
- *Implementation*: Add `self._ip_lock = asyncio.Lock()` to `__init__`. Wrap `check_per_ip_limit()` and `_decrement_ip_count()` in `async with self._ip_lock:`.
- *Strengths*: Correct for async context; minimal overhead for low-contention lock.
- *Weaknesses*: Requires making both methods async.
- *Risks*: Lock contention under extreme connection rates (unlikely).
- *Guardrails*: Add test with concurrent connect/disconnect to verify atomicity.

**Recommended**: Approach A because asyncio.Lock is the standard solution for async check-then-act races.

---

#### CONC-02: `_last_state_broadcast_time` Unprotected Cross-Thread R/W

**Current Code**: `manager.py:151-155` — `now = time.monotonic()` + `if hasattr(self, "_last_state_broadcast_time") and now - self._last_state_broadcast_time < self._state_throttle_interval: return` — no lock around read/write of `_last_state_broadcast_time`.
**Root Cause**: Multiple threads can pass the throttle check simultaneously and broadcast duplicate state messages.
**Cross-References**: CONC-02 = BUG-CC-16

**Approach A — threading.Lock Guard**:
- *Implementation*: Add `self._broadcast_lock = threading.Lock()` to `__init__`. Wrap lines 151-155 in `with self._broadcast_lock:`.
- *Strengths*: Thread-safe throttle check; prevents duplicate broadcasts.
- *Weaknesses*: Adds contention point on broadcast path.
- *Risks*: Negligible — broadcast frequency is ≤1 Hz.
- *Guardrails*: Initialize `_last_state_broadcast_time` in `__init__` to eliminate `hasattr` check.

**Recommended**: Approach A because it directly fixes the race with minimal overhead.

---

#### CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission

**Current Code**: `manager.py:453-495` — Lock at line 464 released after reading history (line 474); lock re-acquired at line 494 to update high-water-mark. Between these locks, duplicate emissions possible.
**Root Cause**: Lock scope doesn't cover the full read-process-write cycle, creating a window where two callers read the same `_last_emitted_history_len` and both emit the same metrics.
**Cross-References**: CONC-03 = BUG-CC-17

**Approach A — Single Lock Scope**:
- *Implementation*: Extend the initial lock to cover the entire method: read high-water-mark, emit metrics, update high-water-mark all within one `with self._metrics_lock:` block.
- *Strengths*: Eliminates race window entirely; simplifies code.
- *Weaknesses*: Holds lock during metric emission (potentially slow if many new entries).
- *Risks*: Lock hold time increases proportional to new entries per call.
- *Guardrails*: Cap batch size (e.g., max 100 entries per call) to bound lock duration.

**Approach B — Compare-and-Swap Pattern**:
- *Implementation*: Use lock only briefly: read `_last_emitted_history_len`, release lock, process outside lock, then re-acquire lock and only update if `_last_emitted_history_len` hasn't changed. If changed, discard work (another caller handled it).
- *Strengths*: Minimal lock hold time; correct deduplication.
- *Weaknesses*: Wasted work if contention occurs.
- *Risks*: More complex logic.
- *Guardrails*: Log discarded duplicate work at DEBUG level.

**Recommended**: Approach A because simplicity outweighs the minor lock-hold concern for sub-second operations.

---

#### CONC-04: ALL Storage Operations Block Async Event Loop (juniper-data)

**Current Code**: `datasets.py:98-154,259,277,377-424` — `store.get_meta()`, `store.save_versioned()`, `store.batch_export()` etc. all synchronous in async handlers.
**Root Cause**: Storage layer is synchronous (filesystem/Postgres I/O); async handlers call synchronous methods directly, blocking the event loop.
**Cross-References**: CONC-04 = BUG-JD-10 = JD-PERF-01 = SEC-04

**Approach A — asyncio.to_thread for All Storage Calls**:
- *Implementation*: Wrap every storage call with `await asyncio.to_thread(store.method, args)`. Apply to `get_meta`, `save`, `save_versioned`, `delete`, `get_artifact`, `batch_export`, `update_meta`, `batch_update_tags`, `filter_datasets`, `get_stats`.
- *Strengths*: Unblocks event loop for all concurrent requests; minimal refactor; no storage API changes needed.
- *Weaknesses*: Thread pool size limits concurrent storage operations (default 40).
- *Risks*: Thread-safety of storage layer must be verified (uses threading.Lock already, so should be safe).
- *Guardrails*: Add `asyncio.wait_for(timeout=30)` to prevent indefinite hangs.

**Approach B — Async Storage Layer**:
- *Implementation*: Rewrite storage layer using `aiofiles` for filesystem and `asyncpg` for Postgres.
- *Strengths*: True async I/O; no thread pool overhead; better scalability.
- *Weaknesses*: Major refactor of storage layer; new dependencies.
- *Risks*: Significant development effort; regression risk.
- *Guardrails*: Feature-flag async backend; run parallel with sync for comparison.

**Recommended**: Approach A for immediate fix (highest-priority performance issue); Approach B as long-term target.

---

#### CONC-07: `regenerate_dataset` Mutates State Without Lock

**Current Code**: `demo_mode.py:1660-1676` — `self.network.train_x`, `train_y`, `current_epoch`, `current_loss`, `current_accuracy` mutated without `_lock` at lines 1668-1672. Lock only used at line 1673 for `metrics_history.clear()`.
**Root Cause**: State mutation outside lock means the training thread can read partially updated state (e.g., new `train_x` with old `train_y`).
**Cross-References**: CONC-07 = BUG-CN-11

**Approach A — Extend Lock Scope**:
- *Implementation*: Move `with self._lock:` to cover lines 1664-1675 (dataset assignment through metrics clear).
- *Strengths*: Prevents partial-state reads by training thread; simple lock scope extension.
- *Weaknesses*: Holds lock during dataset generation (potentially slow).
- *Risks*: Must verify training thread also acquires `_lock` when reading these fields.
- *Guardrails*: Add assertion that `is_running == False` at entry (already checked at line 1660-1661).

**Recommended**: Approach A because the lock is already used for related state and scope extension is trivial.

---

#### CONC-08: `is_running` Reads/Writes Inconsistently Locked

**Current Code**: `demo_mode.py:1151,1293,1398,1478` — `self.is_running` checked outside lock in some paths, set inside lock in others.
**Root Cause**: Boolean check-then-act on `is_running` is not atomic; race between check and subsequent action.

**Approach A — Consistent Lock Usage**:
- *Implementation*: Wrap all reads and writes of `self.is_running` in `with self._lock:`. Use a helper property: `@property def running(self) -> bool: with self._lock: return self.is_running`.
- *Strengths*: Correct synchronization; consistent access pattern.
- *Weaknesses*: Adds lock acquisition overhead on reads (negligible for boolean).
- *Risks*: Must identify all access sites (4+ locations).
- *Guardrails*: Grep for all `is_running` references to ensure complete coverage.

**Recommended**: Approach A because consistent locking is the correct fix for shared mutable state.

---

#### CONC-09: Fire-and-Forget `asyncio.create_task` Without Stored Reference

**Current Code**: `app.py:137,142` — `asyncio.create_task(_auto_start_training(...))` and `asyncio.create_task(_auto_start_canopy(...))` — task references not stored.
**Root Cause**: Without stored references, task exceptions are silently swallowed and tasks can be garbage-collected.

**Approach A — Store Task References**:
- *Implementation*: Store references: `app.state.startup_tasks = [asyncio.create_task(_auto_start_training(...))]`. Add exception callback: `task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)`.
- *Strengths*: Surfaces task exceptions; prevents GC; allows graceful shutdown cancellation.
- *Weaknesses*: Must manage task lifecycle in shutdown handler.
- *Risks*: Minimal.
- *Guardrails*: Cancel stored tasks during lifespan shutdown; log any task failures.

**Recommended**: Approach A because storing task references is a Python asyncio best practice.

---

#### CONC-10: Health Monitor Deregister/Assign Race Window

**Current Code**: `coordinator.py:379-408` — task can be assigned to a worker that is about to be deregistered, creating a 120s delay before task reassignment.
**Root Cause**: No atomic check-and-assign for worker availability during task assignment.

**Approach A — Lock-Protected Assignment**:
- *Implementation*: Use a single lock that covers both worker health status check and task assignment. Worker deregistration must also acquire this lock before removing the worker.
- *Strengths*: Eliminates race window; tasks are only assigned to confirmed-healthy workers.
- *Weaknesses*: Adds contention between assignment and health monitoring.
- *Risks*: Lock hold time during assignment must be short.
- *Guardrails*: Add `worker.is_active` check immediately before task dispatch as defense-in-depth.

**Recommended**: Approach A because the 120s delay impact justifies the minor contention overhead.

---

#### CONC-12: `record_access` TOCTOU on access_count Increment

**Current Code**: `base.py:125-135` — two concurrent requests read same count, both increment, one lost.
**Root Cause**: Non-atomic read-modify-write on access counter without synchronization.
**Cross-References**: CONC-12 = BUG-JD-11

**Approach A — Atomic Increment Under Lock**:
- *Implementation*: Use the existing `_version_lock` (or add a dedicated `_access_lock`) around the entire read-increment-write sequence.
- *Strengths*: Correct; simple; follows existing locking pattern.
- *Weaknesses*: `_version_lock` is per-process, not per-cluster (as noted in BUG-JD-05).
- *Risks*: Minimal — access counting is informational.
- *Guardrails*: Accept best-effort counting for multi-process deployments; document limitation.

**Recommended**: Approach A because per-process locking is sufficient for single-instance deployments.

---

### Issue Remediations, Section 18

#### ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client)

**Current Code**: `juniper_data_client/client.py:215-531` — all 13 public methods call `response.json()` without catching `json.JSONDecodeError`.
**Root Cause**: Non-JSON responses (e.g., HTML error pages from reverse proxies, 502 gateway errors) cause untyped `JSONDecodeError` to escape to callers.

**Approach A — Centralized JSON Parsing with Typed Error**:
- *Implementation*: Add a `_parse_response_json(response)` method that wraps `response.json()` in `try/except json.JSONDecodeError`, raising a custom `DataClientResponseError(f"Non-JSON response ({response.status_code}): {response.text[:200]}")`. Call from all 13 methods.
- *Strengths*: DRY; consistent error type; includes response body snippet for debugging.
- *Weaknesses*: Adds a new exception class to public API.
- *Risks*: Must update all call sites; callers catching generic Exception will still work.
- *Guardrails*: Add unit test with mock non-JSON response for each method.

**Recommended**: Approach A because centralized parsing eliminates 13 identical try/except blocks.

---

#### ERR-02: `response.json()` Unguarded in cascor-client `_request()`

**Current Code**: `juniper_cascor_client/client.py:366` — `response.json()` called without JSONDecodeError handling.
**Root Cause**: Same root cause as ERR-01 but in the cascor-client.

**Approach A — Wrap in _request()**:
- *Implementation*: Add `try/except json.JSONDecodeError` in the `_request()` method, raising `CascorClientError(f"Non-JSON response: {response.status_code}")`.
- *Strengths*: Single fix point (all public methods go through `_request()`); typed error.
- *Weaknesses*: None significant.
- *Risks*: Minimal.
- *Guardrails*: Include `response.text[:200]` in error message for debugging.

**Recommended**: Approach A because `_request()` is the central dispatch point.

---

#### ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor)

**Current Code**: `routes/network.py:31,52`, `training.py:89,109,121,170` — 6 locations where `raise HTTPException(...)` discards original exception via missing `from e`.
**Root Cause**: Missing `raise ... from e` syntax loses the exception chain, making debugging difficult.

**Approach A — Add `from e` Clause**:
- *Implementation*: Change all 6 locations from `raise HTTPException(...)` to `raise HTTPException(...) from e`.
- *Strengths*: Preserves exception chain in tracebacks; trivial change.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add linting rule (flake8 or ruff) to catch future instances.

**Recommended**: Approach A because it's a trivial fix with no downsides.

---

#### ERR-07: `raise HTTPException` Without `from e` — Broad Except Masks Programming Errors (data)

**Current Code**: `datasets.py:90` — broad `except` with `raise HTTPException(400)` masks programming errors as user errors.
**Root Cause**: Overly broad exception handler converts all errors (including bugs) into 400 responses.

**Approach A — Narrow Exception Types**:
- *Implementation*: Replace bare `except Exception` with specific types: `except (ValueError, ValidationError)` for user input errors (400), let programming errors propagate as 500.
- *Strengths*: Distinguishes user errors from bugs; allows bugs to surface in logs/monitoring.
- *Weaknesses*: Must identify all expected exception types.
- *Risks*: May initially miss some valid exception types, causing 500s.
- *Guardrails*: Log caught exceptions at WARNING; add a catch-all with ERROR logging above the specific handlers.

**Recommended**: Approach A because masking programming errors as 400s hides bugs.

---

#### ERR-08: `str(e)` in Batch Create Error Response — Information Disclosure (data)

**Current Code**: `datasets.py:342-348` — exception message included verbatim in API response.
**Root Cause**: Same pattern as SEC-14; internal error details leaked to clients.

**Approach A — Generic Error with Correlation ID**:
- *Implementation*: Replace `str(e)` with `"Dataset creation failed"`. Log full exception server-side with a unique correlation ID. Return correlation ID to client.
- *Strengths*: Prevents info disclosure; enables support debugging via correlation ID.
- *Weaknesses*: Client loses immediate error details.
- *Risks*: None.
- *Guardrails*: Include correlation ID in structured log entry.

**Recommended**: Approach A because information disclosure in error responses is a security anti-pattern.

---

#### ERR-09: `remote_client_0.process_tasks()` Catches All Exceptions, Only Prints

**Current Code**: `remote_client_0.py:73-74` — broad `except Exception` with `print(e)` only.
**Root Cause**: Legacy error handling pattern; exceptions are swallowed without proper logging or recovery.

**Approach A — Proper Logging and Re-raise**:
- *Implementation*: Replace `print(e)` with `logger.exception("Task processing failed")` and allow the exception to propagate or trigger graceful shutdown.
- *Strengths*: Proper structured logging; exceptions visible in monitoring.
- *Weaknesses*: None.
- *Risks*: Propagation may crash the process (which is correct — silent failure is worse).
- *Guardrails*: Note: `remote_client_0.py` is in `src/remote_client/` which is slated for deletion (CLN-CC-01/HSK-02). Fix is moot if directory is deleted.

**Recommended**: Approach A, but prioritize CLN-CC-01 (deleting the directory) as the real fix.

---

#### ERR-12: `config_manager._load_config()` Returns {} on Any Error

**Current Code**: `config_manager.py:147-149` — catches all exceptions including programming errors, returns empty config silently.
**Root Cause**: Overly broad exception handler masks configuration errors.
**Cross-References**: ERR-12 = BUG-CN-12

**Approach A — Narrow Exception Types**:
- *Implementation*: Catch only `(FileNotFoundError, json.JSONDecodeError, PermissionError)` — legitimate config load failures. Let `TypeError`, `AttributeError`, etc. propagate.
- *Strengths*: Programming errors surface immediately; config file issues handled gracefully.
- *Weaknesses*: Must identify all legitimate failure modes.
- *Risks*: Previously-silenced errors may surface.
- *Guardrails*: Log caught exceptions at WARNING level; add fallback config path check.

**Recommended**: Approach A because silencing programming errors is a debugging anti-pattern.

---

#### ERR-13: `arc_agi` Generator Silent Fallback on Any Exception

**Current Code**: `generator.py:95-98` — all exceptions caught and silently fallen back to default behavior.
**Root Cause**: Intended to handle auth/network errors but catches programming errors too.

**Approach A — Narrow to Expected Failures**:
- *Implementation*: Catch only `(ConnectionError, TimeoutError, OSError, ImportError)` for network/auth failures. Let `TypeError`, `ValueError`, etc. propagate.
- *Strengths*: Network failures handled gracefully; bugs surface.
- *Weaknesses*: Must verify all expected error types from ARC-AGI data source.
- *Risks*: Newly surfaced errors during generation.
- *Guardrails*: Log all caught exceptions at WARNING with exception type for monitoring.

**Recommended**: Approach A because silent fallback masks real errors.

---

#### ERR-14: `CascorMetricsStream.stream()` Swallows ConnectionClosed

**Current Code**: `ws_client.py:79-80` — `ConnectionClosed` exception caught and stream silently ends.
**Root Cause**: Caller cannot distinguish between clean stream end and unexpected disconnection.

**Approach A — Expose Disconnect Reason**:
- *Implementation*: Re-raise `ConnectionClosed` as a typed `StreamDisconnectedError` (or yield a sentinel message `{"type": "disconnected", "reason": str(e)}`).
- *Strengths*: Callers can implement reconnection logic; clean API contract.
- *Weaknesses*: Changes public API behavior (breaking for callers that rely on silent end).
- *Risks*: Must update callers (primarily canopy).
- *Guardrails*: Deprecation period: log warning when ConnectionClosed occurs; add `raise_on_disconnect=False` parameter for backward compat.

**Approach B — Callback on Disconnect**:
- *Implementation*: Add optional `on_disconnect` callback parameter that is invoked when `ConnectionClosed` occurs before the stream generator exits.
- *Strengths*: Non-breaking; callers opt-in to disconnect handling.
- *Weaknesses*: Doesn't fix callers that don't register the callback.
- *Risks*: Minimal.
- *Guardrails*: Default callback logs at WARNING level.

**Recommended**: Approach A because silent swallowing of disconnects is the root cause of lost-connection bugs.

---

#### ROBUST-01: Dummy Candidate Results on Double Training Failure — Silent Corruption

**Current Code**: `cascade_correlation.py:1930-1962` — when parallel AND sequential fallback both fail, a dummy zero-correlation candidate is installed silently.
**Root Cause**: Error handling installs a known-bad candidate to avoid crashing, but this silently corrupts the network with meaningless data.
**Cross-References**: ROBUST-01 = BUG-CC-18

**Approach A — Raise Explicit Error**:
- *Implementation*: Replace dummy candidate installation with `raise CandidateTrainingError("Both parallel and sequential candidate training failed")`. Let the training loop handle the error (stop training, report failure to API).
- *Strengths*: Fails loudly; prevents network corruption; callers can implement recovery.
- *Weaknesses*: Training stops entirely on double failure.
- *Risks*: Double failure should be rare; stopping is correct behavior.
- *Guardrails*: Add retry logic at the training loop level with configurable max retries before abort.

**Approach B — Retry with Modified Parameters**:
- *Implementation*: On double failure, retry candidate training with reduced pool size and learning rate. Fail only after N total retries.
- *Strengths*: More resilient training; may recover from transient numerical issues.
- *Weaknesses*: More complex; may mask underlying algorithm problems.
- *Risks*: Retries may also fail, delaying the inevitable error.
- *Guardrails*: Cap retries at 3; log each retry attempt with parameters.

**Recommended**: Approach A because silent corruption is categorically worse than a clean failure.

---

*End of Agent A partial — 14 Security items + 9 Concurrency items + 10 Error Handling items = 33 items covered*
