# Juniper Project — Outstanding Development Items with Remediation Analysis

- **Date**: 2026-04-22
- **Version**: 6.0.0
- **Status**: Current — Remediation analysis complete with validated multi-approach strategies for all ~300 identified items
- **Scope**: All incomplete development work across the Juniper ecosystem, with 1-3 remediation approaches per item including implementation sketches, strengths/weaknesses, risks, and guardrails
- **Sources**:
  - v5.0.0 validated document (10-agent audit: 5 repo-focused + 5 cross-cutting concern agents)
  - Live codebase verification across all 8 repositories (juniper-cascor, juniper-canopy, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy, juniper-ml)
  - 5-agent remediation analysis (Agent A: Security/Concurrency/Error Handling; Agent B: Active Bugs; Agent C: Cross-Repo/Clients/API; Agent D: Code Quality/Housekeeping/Performance/Config; Agent E: Dashboard/WebSocket/Infrastructure/CasCor/Deploy/Testing)
  - Source files: all `src/`, `api/`, `juniper_data/`, `juniper_cascor_client/`, `juniper_cascor_worker/` directories; all `pyproject.toml`, `docker-compose.yml`, `values.yaml`, `.github/workflows/` configs
  - Documentation: all `notes/development/`, `notes/code-review/`, `AGENTS.md` files across ecosystem

---

## Table of Contents

- [1. Purpose and Methodology](#1-purpose-and-methodology)
- [2. Validation Summary](#2-validation-summary)
- [3. Items Previously Incomplete — Now Fixed](#3-items-previously-incomplete--now-fixed)
- [4. Security Issues](#4-security-issues)
- [5. Active Bugs (Confirmed Still Present)](#5-active-bugs-confirmed-still-present)
- [6. Code Quality and Cleanup](#6-code-quality-and-cleanup)
- [7. Dashboard Enhancements](#7-dashboard-enhancements)
- [8. WebSocket Migration (R5-01 Remaining Phases)](#8-websocket-migration-r5-01-remaining-phases)
- [9. Microservices and Infrastructure](#9-microservices-and-infrastructure)
- [10. CasCor Algorithm and Feature Enhancements](#10-cascor-algorithm-and-feature-enhancements)
- [11. Cross-Repository Alignment Issues](#11-cross-repository-alignment-issues)
- [12. Housekeeping and Broken References](#12-housekeeping-and-broken-references)
- [13. juniper-deploy Outstanding Items](#13-juniper-deploy-outstanding-items)
- [14. juniper-data Outstanding Items](#14-juniper-data-outstanding-items)
- [15. Client Library Outstanding Items](#15-client-library-outstanding-items)
- [16. Performance Issues](#16-performance-issues-v4-new-section)
- [17. Concurrency and Thread Safety Issues](#17-concurrency-and-thread-safety-issues-v5-new)
- [18. Error Handling and Robustness](#18-error-handling-and-robustness-v5-new)
- [19. Testing and CI/CD Gaps](#19-testing-and-cicd-gaps-v5-new)
- [20. Configuration and Dependency Issues](#20-configuration-and-dependency-issues-v5-new)
- [21. API Contract and Protocol Issues](#21-api-contract-and-protocol-issues-v5-new)
- [22. Source Document Lineage (v5.0.0 - v1.0.0)](#22-source-document-lineage-v500---v100)
- [23. Validation Methodology (v6.0.0 - v1.0.0)](#23-validation-methodology-v600---v100)

---

## 1. Purpose and Methodology

This document consolidates all **currently incomplete** development work across the Juniper ecosystem, **with detailed remediation analysis for every identified item**.
It extends v5.0.0 (300 items from 10-agent audit) with a **5-agent remediation analysis** that provides 1-3 validated approaches per item, including implementation sketches, strengths/weaknesses, risks, and guardrails.

**Validation method (v4.0.0)**:
Five specialized audit agents independently performed deep code analysis of the live codebases, using file reads, grep pattern searches, and structural analysis.
Each agent verified existing v3 items and identified new issues.
Findings were deduplicated and cross-validated before integration.

**Validation method (v5.0.0)**:
Five additional specialized agents audited **cross-cutting concerns** across all 8 repositories simultaneously: concurrency/threading, error handling/robustness, test coverage/CI, configuration/dependencies, and API contracts/protocol correctness.
This complementary approach identified ~70 new items that per-repo audits missed.
See [Section 23](#23-validation-methodology-v600---v100) for details.

**Remediation analysis method (v6.0.0)**:
Five remediation agents performed deep source code analysis across all 8 repositories, verified each identified issue against the live codebase, and developed 1-3 remediation approaches per item.
Each approach includes an implementation sketch, strengths, weaknesses, risks, and guardrails.
Cross-references between sections were validated to prevent duplicate remediation work.
See [Section 23](#23-validation-methodology-v600---v100) for the agent assignment breakdown.

**Status legend**:

| Symbol | Meaning                                         |
|--------|-------------------------------------------------|
| ✅     | Fixed since last consolidation (newly resolved) |
| 🔴     | Still open — confirmed not implemented          |
| ⚠️     | Partially fixed — some elements still missing   |
| 🐛     | Bug confirmed still present                     |
| 🔵     | Deferred — explicitly decided to defer          |

---

## 2. Validation Summary

| Category                      | v4 Open | v5 Fixed | v5 Still Open | v5 New (v5) | Running Total |
|-------------------------------|---------|----------|---------------|-------------|---------------|
| Security                      | 16      | 0        | 16            | +0          | 16            |
| Active Bugs (cascor)          | 15      | 0        | 15            | +3          | 18            |
| Active Bugs (canopy)          | 10      | 0        | 10            | +2          | 12            |
| Active Bugs (data)            | 9       | 0        | 9             | +2          | 11            |
| Active Bugs (data/clients)    | 7       | 0        | 7             | +0          | 7             |
| Dashboard Augmentation        | 5       | 0        | 5             | +0          | 5             |
| WebSocket Migration           | 16      | 0        | 16            | +0          | 16            |
| Infrastructure                | 7       | 0        | 7             | +0          | 7             |
| Deploy Infrastructure         | 26      | 0        | 26            | +3          | 29            |
| Cross-Repo Alignment          | 14      | 0        | 14            | +5          | 19            |
| Housekeeping                  | 24      | 0        | 24            | +0          | 24            |
| CasCor Enhancements           | 9       | 0        | 9             | +0          | 9             |
| Code Quality                  | 30      | 0        | 30            | +0          | 30            |
| Client Libraries              | 29      | 0        | 29            | +0          | 29            |
| Performance                   | 7       | 0        | 7             | +0          | 7             |
| Concurrency (v5 new)          | —       | —        | —             | +9          | 9             |
| Error Handling (v5 new)       | —       | —        | —             | +10         | 10            |
| Testing/CI (v5 new)           | —       | —        | —             | +17         | 17            |
| Configuration/Deps (v5 new)   | —       | —        | —             | +16         | 16            |
| API/Protocol (v5 new)         | —       | —        | —             | +10         | 10            |
| **Grand total (v5)**          | **~230**| **0**    | **~230**      | **+~70**    | **~300**      |

---

## 3. Items Previously Incomplete — Now Fixed

### Issue Identification Tables, Section 3

#### 3.1 Fixed in v1–v3 (carried forward)

| Item                                            | Source                                 | Repo   | Evidence                                                                                                                |
|-------------------------------------------------|----------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------|
| **Task 2 Ph1**: Metadata-only graceful handling | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `dataset_plotter.py:361-364` — renders `"Dataset loaded (metadata only)"` empty plot                                    |
| **Task 1A**: Validation loss/accuracy overlays  | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:1449` — `_add_validation_overlay()` for val_loss (L1378) and val_accuracy (L1623)                     |
| **Task 1C**: Learning rate metric card          | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:441` — LR card with `_update_learning_rate_handler()` at L1041                                        |
| **Task 1D**: Phase duration display             | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:157` — `phase-duration` ID; `_update_phase_duration_handler()` at L1082                               |
| **Phase C**: WebSocket `set_params`             | juniper-ml R5-01                       | canopy | `settings.py:182` — `use_websocket_set_params: bool = True`; `cascor_service_adapter.py:454,642` routes via WS          |
| **Phase D**: WS control buttons                 | juniper-ml R5-01                       | canopy | `settings.py:186` — `enable_ws_control_buttons: bool = True`; `dashboard_manager.py:1898` registers clientside callback |
| **Task 2 Ph2**: Dataset data endpoint           | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `cascor_service_adapter.py:989` — `get_dataset_data()` delegates to client                                              |
| **Per-IP connection cap (canopy)**              | juniper-ml R5-01                       | canopy | `settings.py:99` — `max_connections_per_ip: int = 5`; `websocket_manager.py:269-291` enforces                           |
| **OPT-3**: Persistent output layer              | juniper-cascor dev record              | cascor | `cascade_correlation.py:1603-1607` — intentional fresh nn.Linear per call (documented design decision)                  |

#### 3.2 Newly confirmed fixed in v4

| Item                                    | v3 ID  | Repo   | Evidence                                                                                                                                                               |
|-----------------------------------------|--------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Request body limit for chunked encoding | SEC-08 | cascor | `src/api/middleware.py:58-89` — `RequestBodyLimitMiddleware` now stream-reads POST/PUT/PATCH bodies when Content-Length absent; caps at `_MAX_REQUEST_BODY_BYTES`      |
| Worker `worker_id` server-generated     | SEC-09 | cascor | `src/api/websocket/worker_stream.py:159-164` — server generates `worker_id = f"worker-{uuid.uuid4().hex[:12]}"`. Client-supplied value is stored as `client_name` only |

---

## 4. Security Issues

### Issue Identification Tables, Section 4

#### 4.1 Original items (v3) — status updated

| ID     | Severity   | Repository     | Description                                                   | File                                      | Status (v4)                                                                                                                 |
|--------|------------|----------------|---------------------------------------------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| SEC-01 | **HIGH**   | juniper-data   | API key comparison not constant-time — timing side-channel    | `juniper_data/api/security.py:59`         | 🔴 Confirmed — `api_key in self._api_keys` (set membership)                                                                 |
| SEC-02 | **MEDIUM** | juniper-data   | Rate limiter memory unbounded — DoS vector                    | `juniper_data/api/security.py`            | 🔴 Confirmed — no eviction, TTL, or max-size                                                                                |
| SEC-03 | **MEDIUM** | juniper-cascor | No per-IP WebSocket connection limiting                       | `src/api/settings.py`                     | 🔴 Confirmed — only `ws_max_connections: 50` (global)                                                                       |
| SEC-04 | **LOW**    | juniper-data   | Sync dataset generation blocks event loop                     | `juniper_data/api/routes/datasets.py:107` | 🔴 Confirmed                                                                                                                |
| SEC-05 | **HIGH**   | juniper-canopy | Cross-Site WebSocket Hijacking (CSWSH) — no Origin validation | `/ws/training`, `/ws/control`             | 🔴 Confirmed                                                                                                                |
| SEC-06 | **MEDIUM** | juniper-canopy | No auth on canopy WS endpoints                                | WebSocket endpoints                       | 🔴 Confirmed                                                                                                                |
| SEC-07 | **MEDIUM** | juniper-cascor | Unvalidated `params` dict in `TrainingStartRequest`           | `TrainingStartRequest`                    | ⚠️ Partial fix — `_ALLOWED_TRAINING_PARAMS` whitelist filters key names at `training.py:36-52`, values are `Dict[str, Any]` |
| SEC-08 | ~~MEDIUM~~ | juniper-cascor | ~~Request body limit bypassed by chunked encoding~~           | `src/api/middleware.py:58-89`             | ✅ Fixed — `RequestBodyLimitMiddleware` now caps chunked bodies (see note below)                                            |
| SEC-09 | ~~MEDIUM~~ | juniper-cascor | ~~Worker `worker_id` client-supplied without validation~~     | `src/api/websocket/worker_stream.py:159`  | ✅ Fixed — server generates `worker_id`, client value stored as `client_name`                                               |
| SEC-10 | **LOW**    | juniper-data   | Sentry `send_default_pii=True`                                | Sentry configuration                      | 🔴 Confirmed                                                                                                                |

> **SEC-08 partial reopening**: While the middleware caps body size, it uses `await request.body()` (line 86) which reads the *full* body into memory before checking size. A malicious chunked body larger than RAM but smaller than OS socket buffer could cause memory exhaustion. See BUG-CC-15 below.

#### 4.2 New security issues (v4)

| ID     | Severity   | Repository     | Description                                                   | File(s)                                           | Evidence                                                                                                          |
|--------|------------|----------------|---------------------------------------------------------------|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| SEC-11 | **HIGH**   | juniper-cascor | `pickle.loads` HDF5 snapshot data w/o `RestrictedUnpickler`   | `src/snapshots/snapshot_serializer.py:828`        | `pickle.loads(python_state_bytes)`: arbitrary code exec, crafted snapshots; `# trunk-ignore(bandit/B301)` comment |
| SEC-12 | **HIGH**   | juniper-canopy | `/ws` generic endpoint: no Origin validation, per-IP limit    | `src/main.py:2109-2127`                           | API key auth, miss `validate_origin()`, `check_per_ip_limit()` implemented by: `/ws/training`, `/ws/control`      |
| SEC-13 | **HIGH**   | juniper-canopy | Auth secrets exposed: query params via `/api/remote/connect`  | `src/main.py:2392`                                | `authkey` accepted query parameter: logged by web servers, saved browser history/referrer                         |
| SEC-14 | **MEDIUM** | juniper-canopy | Internal exception messages leaked to clients via `str(e)`    | `src/main.py:996, 2055, 2076, 2371, 2411`         | 5 endpoints return `str(e)` in JSON responses — may expose paths, library versions, connect strings               |
| SEC-15 | **MEDIUM** | juniper-cascor | Cascor sentry `send_default_pii=True` (same as SEC-10)        | `src/api/observability.py:176`, `src/main.py:129` | Both init sites set `send_default_pii=True` — API keys leak in headers to Sentry                                  |
| SEC-16 | **MEDIUM** | juniper-data   | `/metrics` Prometheus endpoint bypasses auth middleware       | `juniper_data/api/app.py:121`                     | Mounted ASGI sub-app: `SecurityMiddleware` for router-dispatched requests, not mounts                             |
| SEC-17 | **MEDIUM** | juniper-cascor | Snapshot `snapshot_id` path param, unchecked traversal chars  | `src/api/lifecycle/manager.py:883-904`,           | No regex rejecting `../`, special characters; glob-then-filter limits exposure, violates defense-in-depth         |
|        |            |                |                                                               | `src/api/routes/snapshots.py:48-64`               |                                                                                                                   |
| SEC-18 | **MEDIUM** | cascor-worker  | `_decode_binary_frame` no bounds check, malformed binary data | `juniper_cascor_worker/worker.py:330-343`         | Trusts header-encoded `ndim`, `shape`, `dtype_len`, no bounds check: crafted frame, cause OOM via `np.frombuffer` |

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
- *Risks*: Overly restrictive access may break monitoring.
- *Guardrails*: Default to localhost-only access; configurable via Settings.

**Recommended**: Approach A because unauthenticated metrics endpoints leak operational data.

---

#### SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal

**Current Code**: `src/api/lifecycle/manager.py:883-904`, `src/api/routes/snapshots.py:48-64`.
**Root Cause**: No regex rejecting `../` or special characters; glob-then-filter limits exposure but violates defense-in-depth.

**Approach A — Input Validation + Path Resolution Check**:

- *Implementation*: Add `re.fullmatch(r"[a-zA-Z0-9_-]+", snapshot_id)` in route handler. Also verify `resolved_path.is_relative_to(snapshots_dir)`.
- *Strengths*: Layered defense; blocks traversal at input and resolution.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Return 400 for invalid IDs; log attempt at WARNING.

**Recommended**: Approach A — same pattern as JD-SEC-01.

---

#### SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker)

**Current Code**: `juniper_cascor_worker/worker.py:330-343` — trusts header-encoded `ndim`, `shape`, `dtype_len`.
**Root Cause**: Crafted frame can cause OOM via `np.frombuffer` with attacker-controlled shape.

**Approach A — Bounds Validation**:

- *Implementation*: Validate `ndim <= 10`, `total_elements <= 100_000_000`, `dtype_len <= 32` before `np.frombuffer`. Reject with `ProtocolError` if exceeded.
- *Strengths*: Prevents OOM; minimal performance overhead.
- *Weaknesses*: Must choose reasonable limits.
- *Risks*: Overly restrictive limits may reject legitimate large tensors.
- *Guardrails*: Make limits configurable via constants; log rejections.

**Recommended**: Approach A because unbounded deserialization is a standard DoS vector.

---

## 5. Active Bugs (Confirmed Still Present)

### Issue Identification Tables, Section 5

#### 5.1 juniper-cascor

| ID        | Severity   | Description                                                            | File(s)                                                            | Evidence                                                                                                      |
|-----------|------------|------------------------------------------------------------------------|--------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| BUG-CC-01 | **MEDIUM** | `create_topology_message()` not fully implemented:                     | `src/api/websocket/messages.py:72`                                 | Defined and exported but zero production callers                                                              |
|           |            | -- topology changes never broadcast via WS                             |                                                                    |                                                                                                               |
| BUG-CC-02 | **MEDIUM** | `cascade_add` correlation hardcoded to `0.0`                           | `src/api/lifecycle/manager.py:427-430`                             | `monitor.on_cascade_add(hidden_unit_index=i, correlation=0.0)` — actual correlation is lost                   |
| BUG-CC-03 | **MEDIUM** | `or` fallback bugs for falsy values in spiral_problem.py               | `src/spiral_problem/spiral_problem.py:600-608,1250-1262,1411-1419` | `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` silently overridden             |
| BUG-CC-04 | **LOW**    | Version strings inconsistent across file headers                       | `src/main.py` (0.3.1), `cascade_correlation.py` (0.3.2),           | All three disagree                                                                                            |
|           |            |                                                                        | -- `pyproject.toml` (0.4.0)                                        |                                                                                                               |
| BUG-CC-05 | **LOW**    | `remote_client_0.py` has hardcoded old monorepo path                   | `src/remote_client/remote_client_0.py:16`                          | `sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")`                       |
| BUG-CC-06 | **LOW**    | 32 test files have hardcoded `sys.path.append` to old monorepo         | `src/tests/` (32 files)                                            | Stale path references from pre-polyrepo era                                                                   |
| BUG-CC-07 | **MEDIUM** | `TrainingMonitor.current_phase` never updated by state machine         | `src/api/lifecycle/monitor.py:157`, `manager.py:272,395$,433`      | Manually set as str$ing, not managed by `TrainingStateMachine.phase` — can drift                              |
| BUG-CC-08 | **MEDIUM** | Undeclared global `shared_object_dict`                                 | Shared memory module                                               | Fails static analysis, fragile — relies on implicit global state                                              |
| BUG-CC-09 | **MEDIUM** | `validate_training_results` uninitialized variable when `max_epochs=0` | Training validation                                                | Causes crash when `max_epochs=0` — variable referenced before assignment                                      |
| BUG-CC-10 | **MEDIUM** | `validate_training`: `value_output`/`value_loss`/`value_accuracy`      | `src/cascade_correlation/cascade_correlation.py:4444`              | Variables only assigned inside `if x_val is not None` branch;                                                 |
|           |            | -- not initialized for no-validation-data path                         |                                                                    | -- verbose log at L4444 references them on else path — `UnboundLocalError` at VERBOSE log level               |
| BUG-CC-11 | **MEDIUM** | `_init_content_list` walrus operator precedence bug in `utils.py`      | `src/utils/utils.py:208`                                           | `content := _init_content_list(...) is not None` assigns `True`/`False` to `content`,                         |
|           |            |                                                                        |                                                                    | -- not the list — subsequent `.append()` raises `AttributeError`                                              |
| BUG-CC-12 | **MEDIUM** | `load_dataset` uses `yaml.safe_load` instead of `torch.load`           | `src/utils/utils.py:90-92`                                         | Changed from `torch.load` to `yaml.safe_load` but expects torch tensor keys: function is broken.              |
|           |            |                                                                        |                                                                    | -- This is **NOT** dead code. This code hasn't yet been fully implemented and/or integrated.                  |
| BUG-CC-13 | **MEDIUM** | `RateLimiter._counters` never pruned — unbounded memory growth         | `src/api/security.py:107`                                          | No expired entries cleaned; `ConnectionRateLimiter` has `_maybe_cleanup`, `RateLimiter` does not              |
| BUG-CC-14 | **LOW**    | `HandshakeCooldown._rejections` never pruned for non-blocked IPs       | `src/api/websocket/control_security.py:88,108-114`                 | Entries persist forever if IPs fail & never reach block threshold: minor mem leak                             |
| BUG-CC-15 | **MEDIUM** | `RequestBodyLimitMiddleware` reads full body before size check         | `src/api/middleware.py:86`                                         | `body = await request.body()`: body in mem before check `len(body) > self._max_bytes`: SEC-08 partial         |
| BUG-CC-16 | **MEDIUM** | `_last_state_broadcast_time` unprotected cross-thread R/W              | `src/api/lifecycle/manager.py:151-155`                             | Two concurrent callers can both pass throttle check and broadcast simultaneously (v5 new)                     |
| BUG-CC-17 | **MEDIUM** | `_extract_and_record_metrics()` split-lock — duplicate metric emission | `src/api/lifecycle/manager.py:453-495`                             | Lock released between reading and writing high-water-mark; duplicate metrics possible (v5 new)                |
| BUG-CC-18 | **HIGH**   | Dummy candidate results on double training failure — silent corruption | `src/cascade_correlation/cascade_correlation.py:1930-1962`         | When parallel AND sequential fallback both fail, dummy zero-correlation candidate installed silently (v5 new) |

#### 5.2 juniper-canopy

| ID        | Severity   | Description                                             | File(s)                                                      | Evidence                                                                                                                      |
|-----------|------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| BUG-CN-01 | **HIGH**   | `_stop.clear()` race: `_perform_reset()` w/o lock       | `src/demo_mode.py:1614-1618`                                 | `_stop.clear()` at L1617 and `_pause.clear()` at L1618 outside lock block (lock covers L1615-1616)                            |
| BUG-CN-02 | **HIGH**   | DashboardManager god class (3,232 lines)                | `src/frontend/dashboard_manager.py`                          | 3,232 lines, 81 `def` functions — still growing                                                                               |
| BUG-CN-03 | **MEDIUM** | 226 `hasattr` guards, tests skip test logic             | `src/tests/` (226 occurrences)                               | Verified exact count: 226                                                                                                     |
| BUG-CN-04 | **MEDIUM** | `_api_base_url` hardcoded to `127.0.0.1`                | `cascor_service_adapter.py`                                  | Breaks in Docker/remote deployments                                                                                           |
| BUG-CN-05 | **MEDIUM** | Service populate param values w/ int defaults           | Parameter UI                                                 | UI shows incorrect values for params cascor doesn't expose                                                                    |
| BUG-CN-06 | **MEDIUM** | 1 Hz state throttle drops terminal transitions          | State update handling                                        | Fast Started→Failed→Stopped leaves dashboard showing Started forever                                                          |
| BUG-CN-07 | **LOW**    | Duplicate `APP_VERSION` assignment in module            | `src/main.py:90-93` and `src/main.py:110-113`                | Two identical `try/except` blocks for version extraction — copy-paste error                                                   |
| BUG-CN-08 | **MEDIUM** | `_demo_snapshots` list grows unbounded: demo mode       | `src/main.py:1345, 1444`                                     | `insert(0, snapshot)` with no cap or eviction — memory leak proportional to snapshot frequency                                |
| BUG-CN-09 | **MEDIUM** | `WebSocketManager.active_connections` not thread safe   | `src/communication/websocket_manager.py:178,239,304-310,446` | `broadcast_from_thread()` reads bg threads, `connect()`/`disconnect()` mod: `RuntimeError: Set changed size during iteration` |
| BUG-CN-10 | **LOW**    | `message_count` increment not atomic                    | `src/communication/websocket_manager.py:375`                 | `self.message_count += 1` not thread-safe — inaccurate statistics under concurrent broadcasts                                 |
| BUG-CN-11 | **MEDIUM** | `regenerate_dataset` mutates state without lock         | `src/demo_mode.py:1660-1676`                                 | train_x, train_y, epoch, loss mutated without `_lock` — training thread sees partial state (v5 new)                           |
| BUG-CN-12 | **LOW**    | `config_manager._load_config()` returns {} on any error | `src/config_manager.py:147-149`                              | Catches all exceptions including programming errors, returns empty config silently (v5 new)                                   |

#### 5.3 juniper-data

| ID        | Severity   | Description                                                        | File(s)                          | Evidence                                                                                                                     |
|-----------|------------|--------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| BUG-JD-01 | **MEDIUM** | `batch_export` builds entire ZIP in memory — OOM risk              | `api/routes/datasets.py:416-434` | Large dataset exports accumulate entire ZIP in memory before sending response                                                |
| BUG-JD-02 | **MEDIUM** | `delete()` TOCTOU race condition — non-atomic check-then-unlink    | `storage/local_fs.py`            | Time-of-check to time-of-use race between existence check and file deletion                                                  |
| BUG-JD-03 | **MEDIUM** | `update_meta` writes without temp file — partial data exposure     | `storage/local_fs.py:221-226`    | Confirmed: `meta_path.write_text(...)` directly, while `save()` uses atomic temp-file-replace at L80-101                     |
| BUG-JD-04 | **MEDIUM** | Deterministic IDs with `seed=None` → stale cache returns           | `core/dataset_id.py`             | When seed is None, generated dataset ID is deterministic causing stale cache hits                                            |
| BUG-JD-05 | **LOW**    | `_version_lock` is class variable — won't work across workers      | `storage/base.py:23`             | Confirmed: `_version_lock = threading.Lock()` at class level — per-process, not per-cluster                                  |
| BUG-JD-06 | **LOW**    | `ReadinessResponse.timestamp` uses naive `datetime.now()`          | `api/models/health.py:24`        | All other timestamps use `datetime.now(UTC)`; this one produces local-time timestamps                                        |
| BUG-JD-07 | **MEDIUM** | `record_dataset_generation()` defined but never called             | `api/observability.py:218-229`   | Prometheus metrics `dataset_generations_total` and `generation_duration_seconds` never recorded from route handlers          |
| BUG-JD-08 | **LOW**    | `record_access()` defined but never called from API layer          | `storage/base.py:125-135`        | `access_count` and `last_accessed_at` fields never populated; TTL-based expiration by access won't work                      |
| BUG-JD-09 | **MEDIUM** | High-cardinality Prometheus labels from parameterized routes       | `api/observability.py:98`        | `endpoint = request.url.path` captures full path with dataset IDs — unbounded label cardinality; Prometheus OOM risk         |
| BUG-JD-10 | **HIGH**   | ALL storage operations block async event loop (extends JD-PERF-01) | `api/routes/datasets.py:98-424`  | get_meta, save, batch_export, batch_update_tags — all synchronous in async handlers; blocks ALL concurrent requests (v5 new) |
| BUG-JD-11 | **LOW**    | `record_access` TOCTOU race on access_count increment              | `storage/base.py:125-135`        | Two concurrent requests read same count, both increment, one lost (v5 new)                                                   |

### Issue Remediations, Section 5

#### Issue Remediations, Section 5 — juniper-cascor

#### BUG-CC-01: `create_topology_message()` Not Fully Implemented

**Current Code**: `src/api/websocket/messages.py:72` — function defined and exported but has zero production callers.
**Root Cause**: Topology change broadcasting was planned but never wired into lifecycle events (cascade_add, network creation).

**Approach A — Wire into Lifecycle Events**:

- *Implementation*: Call `create_topology_message()` from `manager.py` after each `on_cascade_add()` and network structure change. Broadcast via `_ws_manager.broadcast_from_thread()`.
- *Strengths*: Completes planned functionality; dashboards get real-time topology updates.
- *Weaknesses*: Must define topology message payload schema; may increase WS traffic.
- *Risks*: Large networks may produce oversized topology messages (see GAP-WS-18).
- *Guardrails*: Add message size check before broadcast; throttle topology broadcasts to max 1/second.

~~**Approach B — Remove Dead Code**:~~

<strike>

- *Implementation*: Delete `create_topology_message()` if topology WS broadcasting is not on the current roadmap.
- *Strengths*: Reduces dead code; clearer codebase.
- *Weaknesses*: Must re-implement when topology broadcasting is needed.
- *Risks*: None.
- *Guardrails*: Document removal in CHANGELOG.
</strike>

**Recommended**: Approach A because topology broadcasting is planned for upcoming releases. This is **NOT** dead code.  This is code that hasn't yet been fully implemented and/or integrated.

---

#### BUG-CC-02: `cascade_add` Correlation Hardcoded to `0.0`

**Current Code**: `src/api/lifecycle/manager.py:427-430` — `monitor.on_cascade_add(hidden_unit_index=i, correlation=0.0)` — actual correlation value is not passed.
**Root Cause**: The actual candidate correlation is computed inside the training loop but not propagated to the lifecycle manager callback.

**Approach A — Pass Actual Correlation**:

- *Implementation*: Modify the monkey-patched `train_one_cascade_step` wrapper to capture the correlation value from the `CandidateUnit.best_correlation` attribute after training, and pass it through to `on_cascade_add()`.
- *Strengths*: Accurate metric reporting; enables correlation-based monitoring.
- *Weaknesses*: Requires understanding cascade training internals to extract correlation.
- *Risks*: Candidate correlation may not be easily accessible from the lifecycle layer.
- *Guardrails*: Add test asserting non-zero correlation in cascade_add events.

**Recommended**: Approach A because hardcoded metrics undermine monitoring value.

---

#### BUG-CC-03: `or` Fallback Bugs for Falsy Values in spiral_problem.py

**Current Code**: `src/spiral_problem/spiral_problem.py:600-608,1250-1262,1411-1419` — `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` silently overridden.
**Root Cause**: Python `or` short-circuits on falsy values (`False`, `0`, `0.0`, `""`), making it impossible to explicitly set parameters to these valid values.

**Approach A — Explicit `is not None` Checks**:

- *Implementation*: Replace all `param or self.param or DEFAULT` patterns with `param if param is not None else (self.param if self.param is not None else DEFAULT)`.
- *Strengths*: Correctly handles `False`, `0`, and other falsy-but-valid values.
- *Weaknesses*: More verbose code.
- *Risks*: Must audit all `or` chains in the file (~15 locations).
- *Guardrails*: Add unit tests for each parameter with falsy values (`False`, `0`, `0.0`).

**Recommended**: Approach A because this is a standard Python anti-pattern with a well-known fix.

---

#### BUG-CC-04: Version Strings Inconsistent Across File Headers

**Current Code**: `src/main.py` (0.3.1), `cascade_correlation.py` (0.3.2), `pyproject.toml` (0.4.0) — all three disagree.
**Root Cause**: File header versions are manually maintained and were not updated during release.

**Approach A — Single Source of Truth**:

- *Implementation*: Remove version strings from all file headers. Use `importlib.metadata.version("juniper-cascor")` at runtime. Single version in `pyproject.toml`.
- *Strengths*: Eliminates version drift; standard Python packaging practice.
- *Weaknesses*: Loses per-file version history in headers.
- *Risks*: Must update all files with stale headers.
- *Guardrails*: Add pre-commit hook or CI check that no file contains `Version: 0.` headers.

**Recommended**: Approach A because multiple version sources inevitably drift.

---

#### BUG-CC-05: `remote_client_0.py` Hardcoded Old Monorepo Path

**Current Code**: `src/remote_client/remote_client_0.py:16` — `sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")`.
**Root Cause**: Legacy code from pre-polyrepo era not updated.
**Cross-References**: CLN-CC-01, HSK-02 — entire `remote_client/` directory slated for deletion.

**Approach A — Delete Only the Stale Remote Client File**:

- *Implementation*: Delete `src/remote_client/remote_client_0.py` files. This file is stale and has been superseded by juniper-cascor-worker.
- *Strengths*: Surgically Removes only the Stale File.  Avoids any unexpected side effects.
- *Weaknesses*: None — remote_client_0.py file is unused.
- *Risks*: None.
- *Guardrails*: Verify zero callers/imports of remote_client_0.py file before deletion.

~~**Approach B — Delete Directory**:~~

<strike>

- *Implementation*: Delete `src/remote_client/` entirely (3 files). Superseded by juniper-cascor-worker.
- *Strengths*: Removes all legacy issues at once.
- *Weaknesses*: None — code is unused.
- *Risks*: None.
- *Guardrails*: Verify zero callers/imports before deletion.
</strike>

**Recommended**: Approach A because the entire directory is NOT dead code. The remote_client_0.py file is stale and can be removed, but the remote_client.py source file will still be used.

---

#### BUG-CC-06: 32 Test Files Have Hardcoded `sys.path.append` to Old Monorepo

**Current Code**: `src/tests/` — 32 files with stale `sys.path.append` references.
**Root Cause**: Legacy monorepo path references not updated during polyrepo migration.

**Approach A — Remove and Fix Imports**:

- *Implementation*: Remove all `sys.path.append` lines from test files. Ensure tests run via `pytest` from project root (which adds `src/` to path automatically via `pyproject.toml` config).
- *Strengths*: Clean imports; standard test discovery.
- *Weaknesses*: Must verify all 32 files still pass after removal.
- *Risks*: Some tests may rely on the path manipulation for imports.
- *Guardrails*: Run full test suite after removal; fix any import errors.

**Recommended**: Approach A because sys.path manipulation in test files is fragile and unnecessary with proper package configuration.

---

#### BUG-CC-07: `TrainingMonitor.current_phase` Never Updated by State Machine

**Current Code**: `src/api/lifecycle/monitor.py:157`, `manager.py:272,395,433` — `current_phase` manually set as string, not managed by `TrainingStateMachine.phase`.
**Root Cause**: Phase tracking is split between manual string assignment and the state machine, allowing drift.

**Approach A — Delegate to State Machine**:

- *Implementation*: Remove `monitor.current_phase` manual assignments. Instead, have `TrainingStateMachine.set_phase()` notify the monitor via callback. Monitor reads phase from state machine only.
- *Strengths*: Single source of truth for phase; eliminates drift.
- *Weaknesses*: Requires wiring callback from state machine to monitor.
- *Risks*: Must verify all phase transitions are captured by the state machine.
- *Guardrails*: Add assertion in monitor that `current_phase == sm.phase` at key checkpoints.

**Recommended**: Approach A because dual-source phase tracking is inherently error-prone.

---

#### BUG-CC-08: Undeclared Global `shared_object_dict`

**Current Code**: Shared memory module — relies on implicit global state for `shared_object_dict`.
**Root Cause**: Module-level global variable created at import time, not properly declared or documented.

**Approach A — Explicit Module-Level Declaration**:

- *Implementation*: Add explicit `shared_object_dict: dict = {}` declaration at module level. Add type annotations and docstring explaining purpose and thread-safety requirements.
- *Strengths*: Passes static analysis; documents intent.
- *Weaknesses*: Still uses global state (architectural concern).
- *Risks*: Minimal for declaration fix.
- *Guardrails*: Add `__all__` export if the dict is part of public API.

**Recommended**: Approach A as immediate fix; consider encapsulating in a class for future refactor.

---

#### BUG-CC-09: `validate_training_results` Uninitialized Variable When `max_epochs=0`

**Current Code**: Training validation — variable referenced before assignment when `max_epochs=0`.
**Root Cause**: Variables only initialized inside a loop that doesn't execute when `max_epochs=0`.

**Approach A — Pre-initialize Variables**:

- *Implementation*: Add `result = None` (or appropriate default) before the loop. Add early return with validation message if `max_epochs <= 0`.
- *Strengths*: Prevents crash; handles edge case explicitly.
- *Weaknesses*: None.
- *Risks*: Must determine correct default for `max_epochs=0` (should it be an error?).
- *Guardrails*: Add unit test with `max_epochs=0` input.

**Recommended**: Approach A because uninitialized variables are crashes waiting to happen.

---

#### BUG-CC-10: `validate_training` Validation Variables Not Initialized for No-Validation-Data Path

**Current Code**: `src/cascade_correlation/cascade_correlation.py:4444` — `value_output`/`value_loss`/`value_accuracy` only assigned inside `if x_val is not None` branch; referenced in else path at VERBOSE log level.
**Root Cause**: Conditional variable initialization without corresponding else-branch defaults.

**Approach A — Pre-initialize with Defaults**:

- *Implementation*: Add `value_output = None`, `value_loss = None`, `value_accuracy = None` before the `if x_val` block. Guard the VERBOSE log with `if value_loss is not None:`.
- *Strengths*: Prevents `UnboundLocalError`; clear semantics for missing validation data.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test exercising training without validation data at VERBOSE log level.

**Recommended**: Approach A because this is a straightforward initialization fix.

---

#### BUG-CC-11: Walrus Operator Precedence Bug in `utils.py`

**Current Code**: `src/utils/utils.py:208` — `content := _init_content_list(...) is not None` assigns `True`/`False` to `content`, not the list.
**Root Cause**: Missing parentheses; `is not None` has higher precedence than `:=`.

**Approach A — Add Parentheses**:

- *Implementation*: Change to `(content := _init_content_list(...)) is not None`.
- *Strengths*: One-character fix; restores intended behavior.
- *Weaknesses*: None.
- *Risks*: None — this is unambiguously a bug.
- *Guardrails*: Add unit test calling the code path to verify `content` is a list.

**Recommended**: Approach A because this is a definitive bug with a trivial fix.

---

#### BUG-CC-12: `load_dataset` Uses `yaml.safe_load` Instead of `torch.load`

**Current Code**: `src/utils/utils.py:90-92` — changed from `torch.load` to `yaml.safe_load` but expects torch tensor keys.
**Root Cause**: Function modification and integration was unfinished which has left the function in a broken state. The load_dataset function is **NOT** dead code. Instead, the load_dataset function is code that has been incompletely implemented and/or integrated.

~~**Approach A — Delete the Function**:~~

<strike>

- *Implementation*: Remove `load_dataset()` since it has zero callers and is fundamentally broken.
- *Strengths*: Removes dead code and broken functionality.
- *Weaknesses*: None — no callers.
- *Risks*: None.
- *Guardrails*: Grep for any references before deletion.
</strike>

**Approach B — Finish Implementing yaml.safe_load in the Function**:~~

- *Implementation*: Finish implementing `load_dataset()` since it has zero callers and is fundamentally broken.
- *Strengths*: Completes implementation of unfinished code and corrects currently broken functionality.
- *Weaknesses*: None — no callers currently implemented.
- *Risks*: Introduction of regressions.
- *Guardrails*: Add additional testing to verify functionality and ensure that regressions have not occurred.

**Approach C — Revert and Implement torch.load in the Function**:~~

- *Implementation*: Remove the yaml.save_load calls from `load_dataset()`, and revert the function back to its earlier state that uses torch.load.
- *Strengths*: Completes implementation of unfinished code, and corrects currently broken functionality.
- *Weaknesses*: None — no callers currently implemented.
- *Risks*: Introduction of regressions.
- *Guardrails*: Add additional testing to verify functionality and ensure that regressions have not occurred.

**Recommended**: Excluding Approach A because this function is **NOT** dead code.  Consider Approach B or C because the load_dataset code has not yet been fully implemented and/or integrated. Prefer Approach B because yaml.safe_load presents fewer security concerns than torch.load in the production environment.

---

#### BUG-CC-13: `RateLimiter._counters` Never Pruned — Unbounded Memory Growth

**Current Code**: `src/api/security.py:107` — `self._counters: dict[str, tuple[int, float]] = defaultdict(...)` with no cleanup.
**Root Cause**: No expired-entry eviction mechanism; unlike `ConnectionRateLimiter` which has `_maybe_cleanup()`.

**Approach A — Add `_maybe_cleanup()` Method**:

- *Implementation*: Copy `_maybe_cleanup()` pattern from `ConnectionRateLimiter`. Call periodically (e.g., every 100 requests). Evict entries older than `2 * window_seconds`.
- *Strengths*: Follows existing codebase pattern; bounded memory.
- *Weaknesses*: Periodic cleanup has amortized cost.
- *Risks*: Minimal.
- *Guardrails*: Cap `_counters` dict at 10k entries hard limit.

**Recommended**: Approach A because the pattern already exists in the same file.

---

#### BUG-CC-14: `HandshakeCooldown._rejections` Never Pruned for Non-Blocked IPs

**Current Code**: `src/api/websocket/control_security.py:88,108-114` — entries persist forever if IPs fail but never reach block threshold.
**Root Cause**: Pruning only occurs for blocked IPs that expire; non-blocked IPs with failed attempts accumulate indefinitely.

**Approach A — Periodic Full Pruning**:

- *Implementation*: Add `_maybe_cleanup()` that iterates `_rejections` and removes entries older than `cooldown_seconds * 2`. Call on every `record_rejection()`.
- *Strengths*: Prevents slow memory leak; consistent with BUG-CC-13 fix pattern.
- *Weaknesses*: Minor overhead per rejection.
- *Risks*: None.
- *Guardrails*: Log pruning events at DEBUG level.

**Recommended**: Approach A for consistency with the `_maybe_cleanup()` pattern.

---

#### BUG-CC-15: `RequestBodyLimitMiddleware` Reads Full Body Before Size Check

**Current Code**: `src/api/middleware.py:86` — `body = await request.body()` reads full body into memory before checking `len(body) > self._max_bytes`.
**Root Cause**: Despite the docstring claiming streaming, the no-Content-Length path still uses `await request.body()` which allocates the full body.

**Approach A — Streaming Read with Size Tracking**:

- *Implementation*: Replace `body = await request.body()` with a streaming read: `chunks = []; size = 0; async for chunk in request.stream(): size += len(chunk); if size > self._max_bytes: return 413; chunks.append(chunk); request._body = b"".join(chunks)`.
- *Strengths*: Rejects oversized bodies early; never allocates more than `_max_bytes` + one chunk.
- *Weaknesses*: Slightly more complex code; must set `request._body` for downstream compatibility.
- *Risks*: Must ensure Starlette's `request.body()` cache is properly populated.
- *Guardrails*: Add test with body > limit using chunked transfer encoding.

**Recommended**: Approach A because this is the intended design per the middleware's own docstring.

---

#### BUG-CC-16: `_last_state_broadcast_time` Unprotected Cross-Thread R/W

**Current Code**: `src/api/lifecycle/manager.py:151-155` — see CONC-02.
**Root Cause**: Unprotected shared mutable state between threads.
**Cross-References**: BUG-CC-16 = CONC-02

**Approach A**: See CONC-02 remediation (threading.Lock guard).
**Recommended**: See CONC-02.

---

#### BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission

**Current Code**: `src/api/lifecycle/manager.py:453-495` — see CONC-03.
**Root Cause**: Lock scope too narrow, allowing duplicate emissions.
**Cross-References**: BUG-CC-17 = CONC-03

**Approach A**: See CONC-03 remediation (single lock scope).
**Recommended**: See CONC-03.

---

#### BUG-CC-18: Dummy Candidate Results on Double Training Failure — Silent Corruption

**Current Code**: `src/cascade_correlation/cascade_correlation.py:1930-1962` — see ROBUST-01.
**Root Cause**: Silent installation of known-bad candidate data.
**Cross-References**: BUG-CC-18 = ROBUST-01

**Approach A**: See ROBUST-01 remediation (raise explicit error).
**Recommended**: See ROBUST-01.

---

#### Issue Remediations, Section 5 — juniper-canopy

#### BUG-CN-01: `_stop.clear()` Race — `_perform_reset()` Without Lock

**Current Code**: `src/demo_mode.py:1614-1618` — `_stop.clear()` at L1617 and `_pause.clear()` at L1618 outside lock block (lock covers only L1615-1616).
**Root Cause**: Event clears are not protected by the lock, so the training thread can observe `is_running=False` but `_stop` still set.

**Approach A — Move Inside Lock Block**:

- *Implementation*: Move `self._stop.clear()` and `self._pause.clear()` inside the `with self._lock:` block (before or after `self.is_running = False`).
- *Strengths*: Atomic state transition; trivial 2-line move.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test that performs rapid start/stop cycles to verify no race.

**Recommended**: Approach A because this is a trivial 2-line fix.

---

#### BUG-CN-02: DashboardManager God Class (3,232 Lines)

**Current Code**: `src/frontend/dashboard_manager.py` — 3,232 lines, 81 `def` functions.
**Root Cause**: Organic growth without refactoring; all dashboard logic accumulated in single class.

**Approach A — Progressive Extraction**:

- *Implementation*: Extract logical groups into component classes: `LayoutManager`, `CallbackRegistry`, `MetricsDisplayManager`, `ControlPanelManager`. Keep `DashboardManager` as a facade delegating to extracted components.
- *Strengths*: Incremental; testable components; reduced cognitive load.
- *Weaknesses*: Large effort (L); risk of breaking tightly coupled callbacks.
- *Risks*: Dash callback registration may resist clean decomposition.
- *Guardrails*: Maintain integration tests throughout; extract one component at a time.

**Approach B — Dash Pages/Multi-Page App**:

- *Implementation*: Migrate to Dash Pages architecture where each dashboard tab is a separate page module.
- *Strengths*: Framework-supported decomposition; natural code splitting.
- *Weaknesses*: Major architectural change; learning curve.
- *Risks*: Shared state between pages may need redesign.
- *Guardrails*: Prototype with one page before full migration.

**Recommended**: Approach A because it's incremental and lower risk.

---

#### BUG-CN-03: 226 `hasattr` Guards in Tests Skip Test Logic

**Current Code**: `src/tests/` — 226 occurrences of `hasattr` guards.
**Root Cause**: Tests use `hasattr` to check for attributes that may not exist on mock/fake objects, silently skipping test assertions.

**Approach A — Remove Guards, Fix Mocks**:

- *Implementation*: Remove `hasattr` guards and ensure mock/fake objects have all required attributes. Tests should fail loudly when expectations aren't met.
- *Strengths*: Tests actually test what they claim; catches regressions.
- *Weaknesses*: Significant effort to fix 226 locations.
- *Risks*: Many tests may start failing, revealing hidden test quality issues.
- *Guardrails*: Prioritize by test file; fix in batches of 10-20 guards.

**Recommended**: Approach A because tests that silently skip assertions provide false confidence.

---

#### BUG-CN-04: `_api_base_url` Hardcoded to `127.0.0.1`

**Current Code**: `cascor_service_adapter.py` — hardcoded localhost URL.
**Root Cause**: Local development convenience that breaks in Docker/remote deployments.

**Approach A — Use Settings Class**:

- *Implementation*: Read `_api_base_url` from `Settings.cascor_service_url` (already exists in settings). Remove hardcoded value.
- *Strengths*: Configurable per environment; follows existing settings pattern.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Default to `http://127.0.0.1:8200` for backward compatibility.

**Recommended**: Approach A because the settings infrastructure already exists.

---

#### BUG-CN-05: Service Populate Param Values with Int Defaults

**Current Code**: Parameter UI — shows incorrect default values for parameters cascor doesn't expose.
**Root Cause**: UI populates missing parameter values with int defaults (0) rather than indicating "not available".

**Approach A — Mark Unavailable Params**:

- *Implementation*: Use `None` or a sentinel value for unavailable parameters. Display as "N/A" or "—" in the UI. Only show editable values for parameters confirmed via `/v1/network` response.
- *Strengths*: Accurate UI; prevents users from submitting invalid defaults.
- *Weaknesses*: Must handle `None` in parameter submission logic.
- *Risks*: Existing code may not handle `None` parameter values.
- *Guardrails*: Add CSS styling to visually distinguish unavailable parameters.

**Recommended**: Approach A because showing incorrect defaults misleads users.

---

#### BUG-CN-06: 1 Hz State Throttle Drops Terminal Transitions

**Current Code**: State update handling — fast Started→Failed→Stopped transitions within 1 second result in dashboard showing "Started" permanently.
**Root Cause**: Throttle discards intermediate state updates, including terminal transitions.
**Cross-References**: Also tracked as GAP-WS-21.

**Approach A — Always Send Terminal States**:

- *Implementation*: Skip throttle check for terminal states (FAILED, STOPPED, COMPLETED, ERROR). Only throttle non-terminal (STARTED, PAUSED, IN_PROGRESS) states.
- *Strengths*: Terminal states always reach dashboard; simple condition check.
- *Weaknesses*: Burst of terminal transitions possible (unlikely).
- *Risks*: Negligible — terminal transitions are inherently low-frequency.
- *Guardrails*: Add test simulating rapid state transitions including terminal states.

**Recommended**: Approach A because terminal states must never be dropped.

---

#### BUG-CN-07: Duplicate `APP_VERSION` Assignment

**Current Code**: `src/main.py:90-93` and `src/main.py:110-113` — two identical `try/except` blocks for version extraction.
**Root Cause**: Copy-paste error during development.

**Approach A — Remove Duplicate**:

- *Implementation*: Delete the first `try/except` block (lines 90-93). Keep the second one.
- *Strengths*: Removes dead code; trivial fix.
- *Weaknesses*: None.
- *Risks*: None — both blocks are identical.
- *Guardrails*: Verify with grep that `APP_VERSION` is assigned exactly once after fix.

**Recommended**: Approach A because duplicate assignments are noise.

---

#### BUG-CN-08: `_demo_snapshots` List Grows Unbounded in Demo Mode

**Current Code**: `src/main.py:1345,1444` — `insert(0, snapshot)` with no cap or eviction.
**Root Cause**: No maximum size enforced on the snapshots list; memory leak proportional to snapshot frequency.

**Approach A — Cap with `maxlen`**:

- *Implementation*: Use `collections.deque(maxlen=100)` instead of `list`. Or add `if len(self._demo_snapshots) > MAX_SNAPSHOTS: self._demo_snapshots.pop()` after insert.
- *Strengths*: Bounded memory; configurable via settings.
- *Weaknesses*: Oldest snapshots are silently discarded.
- *Risks*: Must choose appropriate max size (100 is generous for demo mode).
- *Guardrails*: Add `max_demo_snapshots: int = 100` to Settings class; log when cap is reached.

**Recommended**: Approach A because unbounded growth is a memory leak by definition.

---

#### BUG-CN-09: `WebSocketManager.active_connections` Not Thread Safe

**Current Code**: `src/communication/websocket_manager.py:178,239,304-310,446` — `broadcast_from_thread()` reads from background threads while `connect()`/`disconnect()` modify from the main thread.
**Root Cause**: Python `set` is not thread-safe for concurrent iteration and modification; `RuntimeError: Set changed size during iteration`.

**Approach A — threading.Lock**:

- *Implementation*: Add `self._connections_lock = threading.Lock()` to `__init__`. Wrap all `active_connections` mutations (`add`, `discard`) and iterations (`for conn in active_connections`) in `with self._connections_lock:`.
- *Strengths*: Correct thread-safety; standard Python pattern.
- *Weaknesses*: Lock contention during broadcast (but broadcasts are already serialized).
- *Risks*: Must cover all access sites (4+ locations).
- *Guardrails*: Use `copy()` for iteration: `with lock: snapshot = self.active_connections.copy()` then iterate snapshot outside lock.

**Recommended**: Approach A because set-size-changed-during-iteration is a known crash.

---

#### BUG-CN-10: `message_count` Increment Not Atomic

**Current Code**: `src/communication/websocket_manager.py:375` — `self.message_count += 1` not thread-safe.
**Root Cause**: Compound increment (read-modify-write) is not atomic in Python.

**Approach A — Use threading.Lock**:

- *Implementation*: Protect `self.message_count += 1` with the same `_connections_lock` from BUG-CN-09 fix (or add a dedicated counter lock).
- *Strengths*: Correct; consistent with BUG-CN-09 fix.
- *Weaknesses*: Minor overhead.
- *Risks*: None.
- *Guardrails*: Since this is statistics-only, accept minor inaccuracy if lock contention is a concern.

**Recommended**: Approach A because it's covered by the same lock as BUG-CN-09.

---

#### BUG-CN-11: `regenerate_dataset` Mutates State Without Lock

**Current Code**: `src/demo_mode.py:1660-1676` — see CONC-07.
**Root Cause**: State mutation outside lock; training thread sees partial updates.
**Cross-References**: BUG-CN-11 = CONC-07

**Approach A**: See CONC-07 remediation (extend lock scope).
**Recommended**: See CONC-07.

---

#### BUG-CN-12: `config_manager._load_config()` Returns {} on Any Error

**Current Code**: `src/config_manager.py:147-149` — see ERR-12.
**Root Cause**: Overly broad exception handler masks programming errors.
**Cross-References**: BUG-CN-12 = ERR-12

**Approach A**: See ERR-12 remediation (narrow exception types).
**Recommended**: See ERR-12.

---

#### Issue Remediations, Section 5 — juniper-data

#### BUG-JD-01: `batch_export` Builds Entire ZIP in Memory — OOM Risk

**Current Code**: `api/routes/datasets.py:416-434` — entire ZIP built in memory before sending response.
**Root Cause**: Uses `io.BytesIO()` to build ZIP, accumulating all dataset files in memory.

**Approach A — Streaming ZIP Response**:

- *Implementation*: Use `zipfile.ZipFile` with `StreamingResponse`. Write ZIP entries one at a time, yielding chunks to the HTTP response via a generator. Use `zipfile.ZIP_STORED` (no compression) for streaming compatibility.
- *Strengths*: Constant memory usage regardless of export size; handles arbitrarily large exports.
- *Weaknesses*: No compression (ZIP_STORED); slightly more complex code.
- *Risks*: Must ensure ZIP format compatibility with clients.
- *Guardrails*: Add `Content-Disposition` header for download filename; test with 100+ datasets.

**Approach B — Temporary File on Disk**:

- *Implementation*: Write ZIP to a temporary file via `tempfile.NamedTemporaryFile`, then stream from disk.
- *Strengths*: Supports compression; simpler than streaming ZIP.
- *Weaknesses*: Requires disk space; temporary file cleanup needed.
- *Risks*: Disk space exhaustion for very large exports.
- *Guardrails*: Use `tempfile` with auto-cleanup; check available disk space before export.

**Recommended**: Approach A because streaming eliminates both memory and disk concerns.

---

#### BUG-JD-02: `delete()` TOCTOU Race Condition

**Current Code**: `storage/local_fs.py` — time-of-check to time-of-use race between existence check and file deletion.
**Root Cause**: `if path.exists(): path.unlink()` is non-atomic; file can be deleted between check and unlink.

**Approach A — Atomic Delete Pattern**:

- *Implementation*: Replace check-then-delete with: `try: path.unlink() except FileNotFoundError: pass` (idempotent delete). Return `True` if unlink succeeded, `False` if FileNotFoundError.
- *Strengths*: Atomic; idempotent; no race condition possible.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Apply to both metadata and NPZ file deletion.

**Recommended**: Approach A because try/except is the standard TOCTOU fix for file operations.

---

#### BUG-JD-03: `update_meta` Writes Without Temp File — Partial Data Exposure

**Current Code**: `storage/local_fs.py:221-226` — `meta_path.write_text(meta_json)` directly, while `save()` uses atomic temp-file-replace at L80-101.
**Root Cause**: Inconsistent use of atomic write pattern; direct write can leave partial file on crash.

**Approach A — Atomic Write Pattern**:

- *Implementation*: Use same pattern as `save()`: write to `meta_path.with_suffix('.tmp')`, then `os.replace(tmp_path, meta_path)`. `os.replace` is atomic on POSIX.
- *Strengths*: Crash-safe; consistent with existing `save()` pattern.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Wrap in try/finally to clean up temp file on error.

**Recommended**: Approach A because the atomic pattern already exists in the same module.

---

#### BUG-JD-04: Deterministic IDs with `seed=None` → Stale Cache Returns

**Current Code**: `core/dataset_id.py` — when seed is None, generated dataset ID is deterministic causing stale cache hits.
**Root Cause**: Dataset ID generation doesn't account for the absence of a seed, producing identical IDs for different generation requests.

**Approach A — Include Timestamp or UUID in ID**:

- *Implementation*: When `seed is None`, include `uuid.uuid4().hex[:8]` or `datetime.now(UTC).isoformat()` in the ID hash input.
- *Strengths*: Unique IDs per request; no cache collisions.
- *Weaknesses*: Same parameters no longer produce cacheable results (desired behavior with no seed).
- *Risks*: Breaks clients relying on deterministic IDs for unseeded requests.
- *Guardrails*: Document that `seed=None` means non-deterministic; test ID uniqueness.

**Recommended**: Approach A because deterministic IDs for non-deterministic generation is semantically wrong.

---

#### BUG-JD-05: `_version_lock` Is Class Variable — Won't Work Across Workers

**Current Code**: `storage/base.py:23` — `_version_lock = threading.Lock()` at class level — per-process, not per-cluster.
**Root Cause**: Class-level lock only protects within a single process; multiple workers have independent locks.

**Approach A — Document Limitation**:

- *Implementation*: Add docstring noting that `_version_lock` is per-process and multi-worker deployments require external locking (e.g., Redis lock, file lock, or database SERIALIZABLE transactions).
- *Strengths*: Honest about limitations; guides operators.
- *Weaknesses*: Doesn't actually fix the issue.
- *Risks*: None.
- *Guardrails*: Single-worker deployment is the current default and is safe.

**Approach B — File-Based Locking**:

- *Implementation*: Use `fcntl.flock()` on a lock file in the storage directory for cross-process locking.
- *Strengths*: Works across processes on same host; no external deps.
- *Weaknesses*: Doesn't work across hosts; POSIX-only.
- *Risks*: Lock file cleanup on crash.
- *Guardrails*: Use `O_CREAT` flag for auto-creation; timeout on lock acquisition.

**Recommended**: Approach A for now; Approach B when multi-worker deployment is implemented.

---

#### BUG-JD-06: `ReadinessResponse.timestamp` Uses Naive `datetime.now()`

**Current Code**: `api/models/health.py:24` — uses `datetime.now()` instead of `datetime.now(UTC)`.
**Root Cause**: Inconsistency with other timestamp usage across the project.

**Approach A — Use UTC Timestamp**:

- *Implementation*: Change `datetime.now()` to `datetime.now(UTC)`. Import `UTC` from `datetime`.
- *Strengths*: Consistent with all other timestamps; timezone-aware.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add linting rule to catch `datetime.now()` without timezone.

**Recommended**: Approach A because it's a one-line fix for consistency.

---

#### BUG-JD-07: `record_dataset_generation()` Defined but Never Called

**Current Code**: `api/observability.py:218-229` — Prometheus metrics `dataset_generations_total` and `generation_duration_seconds` never recorded.
**Root Cause**: Metric recording function was implemented but never wired into route handlers.

**Approach A — Wire into Route Handlers**:

- *Implementation*: Call `record_dataset_generation(generator_name, duration)` from the `create_dataset` route handler after successful generation. Use `time.monotonic()` for duration measurement.
- *Strengths*: Activates existing metrics; enables monitoring.
- *Weaknesses*: Minor code change in route handler.
- *Risks*: None.
- *Guardrails*: Verify metrics appear in `/metrics` endpoint after wiring.

**Recommended**: Approach A because the function already exists — it just needs to be called.

---

#### BUG-JD-08: `record_access()` Defined but Never Called

**Current Code**: `storage/base.py:125-135` — `access_count` and `last_accessed_at` fields never populated.
**Root Cause**: Access tracking function implemented but never wired into API layer.

**Approach A — Wire into GET Handlers**:

- *Implementation*: Call `record_access(dataset_id)` from `get_dataset_artifact` and `get_dataset_meta` route handlers.
- *Strengths*: Enables access-based TTL expiration; minimal code change.
- *Weaknesses*: Adds I/O to read paths (metadata write on every access).
- *Risks*: Performance impact on high-frequency reads.
- *Guardrails*: Make access recording async (via `asyncio.to_thread`); consider sampling (record every Nth access).

**Recommended**: Approach A with sampling guardrail to avoid performance impact.

---

#### BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes

**Current Code**: `api/observability.py:98` — `endpoint = request.url.path` captures full path with dataset IDs.
**Root Cause**: Using full URL path as Prometheus label creates unbounded cardinality (one label per dataset ID).

**Approach A — Use Route Template**:

- *Implementation*: Replace `request.url.path` with `request.scope.get("path", request.url.path)` or manually extract the route pattern (e.g., `/v1/datasets/{dataset_id}`).
- *Strengths*: Fixed cardinality (one label per route template); prevents Prometheus OOM.
- *Weaknesses*: Must handle Starlette's route resolution.
- *Risks*: Middleware may not have access to resolved route.
- *Guardrails*: Add cardinality alert in Prometheus for metrics exceeding 100 unique label values.

**Recommended**: Approach A because unbounded Prometheus label cardinality is a known production incident cause.

---

#### BUG-JD-10: ALL Storage Operations Block Async Event Loop

**Current Code**: `api/routes/datasets.py:98-424` — see CONC-04.
**Root Cause**: Synchronous storage operations in async handlers.
**Cross-References**: BUG-JD-10 = CONC-04

**Approach A**: See CONC-04 remediation (asyncio.to_thread wrapper).
**Recommended**: See CONC-04.

---

#### BUG-JD-11: `record_access` TOCTOU Race on access_count Increment

**Current Code**: `storage/base.py:125-135` — see CONC-12.
**Root Cause**: Non-atomic read-modify-write.
**Cross-References**: BUG-JD-11 = CONC-12

**Approach A**: See CONC-12 remediation (atomic increment under lock).
**Recommended**: See CONC-12.

---

## 6. Code Quality and Cleanup

### Issue Identification Tables, Section 6

#### 6.1 juniper-cascor — Stale Code Removal

| ID        | Priority | Description                                                                                                    | File(s)                                                                      | Effort       |
|-----------|----------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|--------------|
| CLN-CC-01 | **P2**   | Delete stale file from `remote_client/` directory (`remote_client_0.py`) — superseded by juniper-cascor-worker | `src/remote_client/remote_client_0.py`                                       | 10 min       |
| CLN-CC-02 | **P2**   | Delete stale `check.py` duplicate (600 lines) — copy of spiral_problem.py                                      | `src/spiral_problem/check.py`                                                | 10 min       |
| CLN-CC-03 | **P2**   | Remove 9 local `import traceback` in cascade_correlation.py — uncomment line 64 top-level import               | `cascade_correlation.py:64,2270,2804,3775,3840` + other files                | 30 min       |
| CLN-CC-04 | **P2**   | Enable mypy strict mode                                                                                        | `pyproject.toml`                                                             | M            |
| CLN-CC-05 | **P2**   | Legacy spiral code — ~20 trivial getter/setter methods, no `@deprecated` markers                               | `src/spiral_problem/spiral_problem.py` (53 methods)                          | M            |
| CLN-CC-06 | **P3**   | Remove "Roll" concept in CandidateUnit                                                                         | candidate_unit.py                                                            | 🔵 Deferred  |
| CLN-CC-07 | **P3**   | Candidate factory refactor — all creation through `_create_candidate_unit()`                                   | cascade_correlation.py                                                       | Analysis Req |
| CLN-CC-08 | **P3**   | Remove commented-out code blocks                                                                               | Multiple files                                                               | M            |
| CLN-CC-09 | **P3**   | Line length reduction to ~~120~~ 512 characters                                                                | Multiple files                                                               | 🔵 Deferred  |
| CLN-CC-10 | **P2**   | `utils.py:238` — fix broken `check_object_pickleability` function (uses `dill` not in deps)                    | `src/utils/utils.py:238`                                                     | S            |
| CLN-CC-11 | **P2**   | `snapshot_serializer.py:~756` — extend optimizer support (per in-code TODO)                                    | `snapshot_serializer.py`                                                     | M            |
| CLN-CC-12 | **P2**   | `.ipynb_checkpoints` directories committed to repository                                                       | `src/cascade_correlation/.ipynb_checkpoints/`, `src/candidate_unit/`, `src/` | 10 min       |
| CLN-CC-13 | **P2**   | `sys.path.append` at module level in `cascade_correlation.py:69`                                               | `src/cascade_correlation/cascade_correlation.py:69`                          | S            |
| CLN-CC-14 | **P3**   | Empty `# TODO :` headers in 18+ files (boilerplate noise)                                                      | Multiple file headers                                                        | 🔵 Deferred  |
| CLN-CC-15 | **P3**   | `_object_attributes_to_table` return type annotation wrong (`str` but returns `list`/`None`)                   | `src/utils/utils.py:197`                                                     | S            |

#### 6.2 juniper-canopy — Code Quality

| ID        | Priority | Description                                                                     | Evidence                                                                          | Effort |
|-----------|----------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|--------|
| CLN-CN-01 | **P2**   | `theme-table` CSS class never implemented                                       | No `.theme-table` in any CSS file                                                 | S      |
| CLN-CN-02 | **P2**   | NPZ validation only in DemoMode, not ServiceBackend                             | `_validate_npz_arrays()` exists only in `demo_mode.py:767`                        | S      |
| CLN-CN-03 | **P2**   | Performance test suite minimal — only 1 test file                               | `src/tests/performance/test_button_responsiveness.py` only                        | M      |
| CLN-CN-04 | **P2**   | JuniperData-specific error handling missing                                     | Only cascor-client errors caught; no juniper-data-client error classes            | M      |
| CLN-CN-05 | **P3**   | DashboardManager extraction (3,232 → component classes)                         | Blocked by R5-01 Phase B stability                                                | L      |
| CLN-CN-06 | **P2**   | Re-enable remaining MyPy disabled codes (7 codes)                               | 7 MyPy error codes currently suppressed                                           | M      |
| CLN-CN-07 | **P2**   | Real backend path test coverage                                                 | No tests exercise real CasCor paths — all use fakes/mocks                         | M      |
| CLN-CN-08 | **P2**   | Convert skipped integration tests (4 files with `requires_server`)              | 4 test files with `requires_server` skip marker                                   | M      |
| CLN-CN-09 | **P2**   | main.py coverage gap (84% vs 95% target)                                        | `main.py` at 84% coverage                                                         | S      |
| CLN-CN-10 | **P2**   | `main.py` is 2,543 lines — second god file                                      | 65 functions/methods; 30+ route handlers in a single file                         | L      |
| CLN-CN-11 | **P2**   | `metrics_panel.py` is 1,790 lines — third god file                              | 18 `@app.callback` decorators in single file                                      | L      |
| CLN-CN-12 | **P2**   | `network_visualizer.py:1512` — active TODO indicating logging error bug         | `# TODO: this is throwing a logging error` on `_create_new_node_highlight_traces` | S      |
| CLN-CN-13 | **P3**   | `demo_mode.py:938` — deprecated `_generate_spiral_dataset_local()` still called | `@deprecated` but called as fallback at L554 and L1667                            | S      |
| CLN-CN-14 | **P3**   | `np.random.seed(42)` sets global numpy seed in `demo_mode.py:960`               | Mutates global RNG state; affects all concurrent `np.random` users                | S      |

#### 6.3 juniper-data — Code Quality (v4 new)

| ID        | Priority | Description                                                            | Evidence                                                                   | Effort |
|-----------|----------|------------------------------------------------------------------------|----------------------------------------------------------------------------|--------|
| CLN-JD-01 | **P2**   | `python-dotenv` is hard dependency for optional ARC-AGI feature        | `pyproject.toml` requires it; only used in `__init__.py:get_arc_agi_env()` | S      |
| CLN-JD-02 | **P2**   | `FakeDataClient.close()` destroys data, unlike real client             | `testing/fake_client.py:762-766` — clears `_datasets` on close             | S      |
| CLN-JD-03 | **P3**   | Module-level `create_app()` at `app.py:142` — import-time side effects | Reads env vars and creates middleware at import time                       | M      |

### Issue Remediations, Section 6

#### Issue Remediations, Section 6 — juniper-cascor

#### CLN-CC-01: Delete Legacy `remote_client/` Directory

**Current Code**: `src/remote_client/` — 3 files, superseded by juniper-cascor-worker.
**Root Cause**: Legacy code from pre-polyrepo era not cleaned up.
**Cross-References**: CLN-CC-01 = HSK-02

**Approach A — Delete Only the Stale Remote Client File**:

- *Implementation*: Delete `src/remote_client/remote_client_0.py` files. This file is stale and has been superseded by juniper-cascor-worker.
- *Strengths*: Surgically Removes only the Stale File.  Avoids any unexpected side effects.
- *Weaknesses*: None — remote_client_0.py file is unused.
- *Risks*: None.
- *Guardrails*: Verify zero callers/imports of remote_client_0.py file before deletion.

~~**Approach B — Delete Directory**:~~

<strike>

- *Implementation*: `git rm -r src/remote_client/`. Update `.gitignore` if needed.
- *Strengths*: 10-minute cleanup; removes 3 files of dead code.
- *Weaknesses*: None.
- *Risks*: None — zero callers verified.
- *Guardrails*: Grep for `remote_client` imports before deletion.
</strike>

**Recommended**: Approach A because the entire directory is NOT dead code. The remote_client_0.py file is stale and can be removed, but the remote_client.py source file will still be used.

---

#### CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines)

**Current Code**: `src/spiral_problem/check.py` — 600-line copy of spiral_problem.py.
**Root Cause**: Stale duplicate from development; never referenced.
**Cross-References**: CLN-CC-02 = HSK-03

**Approach A — Delete File**:

- *Implementation*: `git rm src/spiral_problem/check.py`.
- *Strengths*: 10-minute cleanup.
- *Weaknesses*: None.
- *Risks*: None — zero callers.
- *Guardrails*: Verify no imports reference `check.py`.

**Recommended**: Approach A — trivial deletion.

---

#### CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py

**Current Code**: `cascade_correlation.py:64,2270,2804,3775,3840` + other files — 9 local `import traceback` scattered throughout; line 64 has the top-level import commented out.
**Root Cause**: Developers added local imports during debugging; never cleaned up.

**Approach A — Uncomment Top-Level, Remove Local Imports**:

- *Implementation*: Uncomment `import traceback` at line 64. Remove all 9 local `import traceback` statements.
- *Strengths*: Clean imports; follows Python convention of top-level imports.
- *Weaknesses*: None.
- *Risks*: None — traceback is stdlib.
- *Guardrails*: Run tests after change.

**Recommended**: Approach A — 30-minute cleanup.

---

#### CLN-CC-04: Enable mypy Strict Mode

**Current Code**: `pyproject.toml` — mypy not in strict mode.
**Root Cause**: Strict mode was deferred during initial development.

**Approach A — Incremental Strict Mode**:

- *Implementation*: Enable strict mode with per-module overrides: `[mypy] strict = true` then `[mypy-module] ignore_errors = true` for modules not yet compliant. Fix one module at a time.
- *Strengths*: Catches type errors; incremental migration.
- *Weaknesses*: Large effort (M); many existing violations.
- *Risks*: May uncover real bugs during migration.
- *Guardrails*: Track compliance percentage; fix highest-impact modules first.

**Recommended**: Approach A because incremental migration is manageable.

---

#### CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated

**Current Code**: `src/spiral_problem/spiral_problem.py` — 53 methods, ~20 trivial getters/setters with no deprecation markers.
**Root Cause**: Legacy code with Java-style accessors, no Python property pattern.

**Approach A — Add @deprecated Markers**:

- *Implementation*: Mark unused getters/setters with `@deprecated("Use property directly")`. Remove after one release cycle.
- *Strengths*: Warns consumers; tracks deprecated API surface.
- *Weaknesses*: Effort to identify which methods are still called.
- *Risks*: Deprecation warnings may be noisy.
- *Guardrails*: Grep for all method usages across codebase before deprecating.

**Recommended**: Approach A as first step; follow with deletion of confirmed-unused methods.

---

#### CLN-CC-06: Remove "Roll" Concept in CandidateUnit

**Current Code**: `candidate_unit.py` — Roll concept in CandidateUnit.
**Root Cause**: Legacy concept no longer relevant to algorithm.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document. Low priority; address when CandidateUnit is refactored.

---

#### CLN-CC-07: Candidate Factory Refactor

**Current Code**: Candidate creation scattered; should go through `_create_candidate_unit()`.
**Root Cause**: Organic code growth without factory pattern enforcement.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document.

---

#### CLN-CC-08: Remove Commented-Out Code Blocks

**Current Code**: Multiple files contain commented-out code.
**Root Cause**: Code commented out during development, never removed.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document.

---

#### CLN-CC-09: Line Length Reduction to 120 Characters

**Current Code**: Multiple files exceed 120 char lines.
**Root Cause**: Project convention is 512 chars; 120 is a stricter standard.

**Approach A — Deferred**: 🔵 Explicitly deferred. Note: Project convention is 512 chars per AGENTS.md.

---

#### CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps

**Current Code**: `src/utils/utils.py:238` — uses `dill` library which is not in dependencies.
**Root Cause**: Function references `dill` but it's not declared as a dependency.

**Approach A — Add dill**:

- *Implementation*: Add `dill` to optional dependencies
- *Strengths*: Resolves the broken import while maintaining the functionality.
- *Weaknesses*: Adding deps for a utility function may be overkill.
- *Risks*: None.
- *Guardrails*: Add tests as necessary to validate functionality and ensure no regressions.

**Approach B — Remove Function**:

- *Implementation*: Remove the function if unused.
- *Strengths*: Resolves the broken import.
- *Weaknesses*: Loses this functionality.
- *Risks*: None.
- *Guardrails*: Grep for callers to determine if function is used.

**Recommended**: Add `dill` as an optional dependency.

---

#### CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO)

**Current Code**: `snapshot_serializer.py:~756` — TODO for extended optimizer support.
**Root Cause**: Only a subset of optimizers are serialized; others are silently skipped.

**Approach A — Add Missing Optimizer Support**:

- *Implementation*: Extend serialization to cover all PyTorch optimizer types (Adam, AdamW, SGD, RMSprop). Use generic `optimizer.state_dict()` approach.
- *Strengths*: Complete snapshot coverage; enables optimizer persistence.
- *Weaknesses*: Must test each optimizer type.
- *Risks*: New optimizers may have non-serializable state.
- *Guardrails*: Add parametrized test for each supported optimizer.

**Recommended**: Approach A because incomplete serialization silently loses optimizer state.

---

#### CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository

**Current Code**: `src/cascade_correlation/.ipynb_checkpoints/`, `src/candidate_unit/`, `src/` — checkpoint directories in repo.
**Root Cause**: `.gitignore` missing `.ipynb_checkpoints` entry.

**Approach A — Remove and Ignore**:

- *Implementation*: `git rm -r --cached */.ipynb_checkpoints/`. Add `.ipynb_checkpoints/` to `.gitignore`.
- *Strengths*: 10-minute cleanup; prevents future commits.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify removal with `git status`.

**Recommended**: Approach A — trivial cleanup.

---

#### CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py

**Current Code**: `src/cascade_correlation/cascade_correlation.py:69` — `sys.path.append(...)`.
**Root Cause**: Legacy monorepo path manipulation.

**Approach A — Remove and Fix Imports**:

- *Implementation*: Remove `sys.path.append` line. Fix any imports that relied on it to use package-relative imports.
- *Strengths*: Clean imports; no runtime path mutation.
- *Weaknesses*: Must verify all affected imports.
- *Risks*: Import failures if dependencies aren't properly installed.
- *Guardrails*: Run tests after removal; fix any ImportError.

**Recommended**: Approach A because sys.path manipulation is fragile.

---

#### CLN-CC-14: Empty `# TODO :` Headers in 18+ Files

**Current Code**: Multiple file headers have empty `# TODO :` comments.
**Root Cause**: Boilerplate template included empty TODO sections.

**Approach A — Remove Empty TODOs**:

- *Implementation*: `grep -rl "# TODO :" src/ | xargs sed -i '/^# TODO :$/d'`.
- *Strengths*: Reduces noise; trivial.
- *Weaknesses*: None.
- *Risks*: Must not remove non-empty TODOs.
- *Guardrails*: Only remove lines matching exactly `# TODO :` (with nothing after).

**Recommended**: Approach A — trivial cleanup, but this action is **Deferred**.

---

#### CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong

**Current Code**: `src/utils/utils.py:197` — annotated as `-> str` but returns `list` or `None`.
**Root Cause**: Type annotation not updated when function was modified.

**Approach A — Fix Annotation**:

- *Implementation*: Change return type to `-> Optional[list]` or the actual return type.
- *Strengths*: Correct type annotation; mypy compliance.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Run mypy on the file after fix.

**Recommended**: Approach A — one-line fix.

---

#### Issue Remediations, Section 6 — juniper-canopy

#### CLN-CN-01: `theme-table` CSS Class Never Implemented

**Current Code**: No `.theme-table` in any CSS file.
**Root Cause**: CSS class referenced in templates but never defined.

**Approach A — Implement References**:

- *Implementation*: Add `.theme-table` CSS rules.
- *Strengths*: Completes partially implemented code and incompletely integrated reference.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Grep for all `theme-table` references.

~~**Approach B — Remove References**:~~

<strike>

- *Implementation*: Remove all HTML references to the `.theme-table` class.
- *Strengths*: Resolves dead reference.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Grep for all `theme-table` references.
</strike>

**Recommended**: Approach A — Complete implementation since styling is needed.

---

#### CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend

**Current Code**: `_validate_npz_arrays()` exists only in `demo_mode.py:767`.
**Root Cause**: Validation not extracted to shared utility.

**Approach A — Extract to Shared Module**:

- *Implementation*: Move `_validate_npz_arrays()` to a shared `validation.py` module. Call from both DemoMode and ServiceBackend.
- *Strengths*: Consistent validation; DRY.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test for validation in service backend path.

**Recommended**: Approach A because inconsistent validation is a reliability gap.

---

#### CLN-CN-03: Performance Test Suite Minimal

**Current Code**: Only `test_button_responsiveness.py`.
**Root Cause**: Performance testing not prioritized.

**Approach A — Expand Test Suite**:

- *Implementation*: Add tests for: callback execution time, WebSocket message throughput, dashboard render time, memory usage during long sessions.
- *Strengths*: Catches performance regressions; establishes baselines.
- *Weaknesses*: Medium effort.
- *Risks*: Flaky tests if timing-dependent.
- *Guardrails*: Use relative thresholds (e.g., "no more than 2x baseline") not absolute times.

**Recommended**: Approach A because performance testing prevents silent regressions.

---

#### CLN-CN-04: JuniperData-Specific Error Handling Missing

**Current Code**: Only cascor-client errors caught; no data-client error classes.
**Root Cause**: Error handling only implemented for cascor-client.

**Approach A — Add Data-Client Error Handling**:

- *Implementation*: Import and catch `DataClientError` (or equivalent) in service adapter. Add appropriate error messages and fallback behavior.
- *Strengths*: Resilient to data service errors.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test simulating data service errors.

**Recommended**: Approach A because unhandled data-client errors crash the dashboard.

---

#### CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes)

**Current Code**: `src/frontend/dashboard_manager.py` — 3,232 lines.
**Root Cause**: God class accumulated all dashboard logic.
**Cross-References**: Related to BUG-CN-02.

**Approach A — Progressive Extraction**:

- *Implementation*: Same as BUG-CN-02 Approach A. Extract component classes incrementally.
- *Strengths*: Testable components; reduced cognitive load.
- *Weaknesses*: Large effort (L).
- *Risks*: Tightly coupled Dash callbacks resist decomposition.
- *Guardrails*: Maintain integration tests; one component at a time.

**Recommended**: Approach A — incremental extraction.

---

#### CLN-CN-06: Re-enable Remaining MyPy Disabled Codes

**Current Code**: 7 MyPy error codes currently suppressed.
**Root Cause**: Codes disabled during development to bypass type errors.

**Approach A — Fix Types and Re-enable**:

- *Implementation*: Fix underlying type errors for each suppressed code, then remove suppression. One code at a time.
- *Strengths*: Better type safety; catches bugs.
- *Weaknesses*: Must fix all violations per code.
- *Risks*: Some codes may be suppressed for valid reasons.
- *Guardrails*: Document any codes that must remain suppressed with justification.

**Recommended**: Approach A — incremental, one code at a time.

---

#### CLN-CN-07: Real Backend Path Test Coverage

**Current Code**: No tests exercise real CasCor paths; all use fakes/mocks.
**Root Cause**: Integration tests not written.

**Approach A — Add Integration Tests**:

- *Implementation*: Add tests with `requires_server` marker that exercise real CascorServiceAdapter with a running cascor instance.
- *Strengths*: Validates real integration; catches API contract issues.
- *Weaknesses*: Requires running server in CI.
- *Risks*: Flaky tests from network/server issues.
- *Guardrails*: Use Docker-based test fixtures; skip if server unavailable.

**Recommended**: Approach A because unit tests with fakes cannot catch integration issues.

---

#### CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`)

**Current Code**: 4 test files with `requires_server` skip marker.
**Root Cause**: Tests written but never run in CI.

**Approach A — Add CI Integration Job**:

- *Implementation*: Add a CI job that starts cascor/data via Docker, runs `requires_server` tests, tears down.
- *Strengths*: Existing tests become valuable.
- *Weaknesses*: CI complexity.
- *Risks*: Docker-in-CI setup.
- *Guardrails*: Run as optional (non-blocking) CI step initially.

**Recommended**: Approach A because existing tests should be exercised.

---

#### CLN-CN-09: main.py Coverage Gap (84% vs 95% Target)

**Current Code**: `main.py` at 84% coverage.
**Root Cause**: Large file with many untested paths.

**Approach A — Targeted Test Addition**:

- *Implementation*: Identify uncovered lines via `coverage html`. Write tests for highest-impact uncovered paths (error handlers, edge cases).
- *Strengths*: Focused effort on coverage gaps.
- *Weaknesses*: 95% target may be aspirational for a 2,543-line file.
- *Risks*: Some paths may be difficult to test without refactoring.
- *Guardrails*: Set intermediate target (90%) before pushing to 95%.

**Recommended**: Approach A with intermediate target of 90%.

---

#### CLN-CN-10: `main.py` Is 2,543 Lines — Second God File

**Current Code**: `src/main.py` — 65 functions/methods; 30+ route handlers.
**Root Cause**: All route handlers in a single file.

**Approach A — Extract Route Modules**:

- *Implementation*: Extract routes into modules: `routes/training.py`, `routes/datasets.py`, `routes/websocket.py`, `routes/health.py`. Import and mount in `main.py`.
- *Strengths*: Smaller files; organized by domain; testable independently.
- *Weaknesses*: Large effort (L).
- *Risks*: Dash callback registration may complicate extraction.
- *Guardrails*: Extract one route group at a time; maintain full test suite.

**Recommended**: Approach A — incremental extraction by route group.

---

#### CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File

**Current Code**: 18 `@app.callback` decorators in single file.
**Root Cause**: All metric panel callbacks in one file.

**Approach A — Extract by Metric Type**:

- *Implementation*: Split into `training_metrics.py`, `candidate_metrics.py`, `validation_metrics.py`.
- *Strengths*: Organized by domain; manageable file sizes.
- *Weaknesses*: Large effort (L); callback cross-dependencies.
- *Risks*: Dash callback registration order may matter.
- *Guardrails*: Extract one metric group at a time.

**Recommended**: Approach A — incremental extraction.

---

#### CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug

**Current Code**: `# TODO: this is throwing a logging error` on `_create_new_node_highlight_traces`.
**Root Cause**: Known logging error in visualization code not fixed.

**Approach A — Fix Logging Error**:

- *Implementation*: Investigate and fix the logging error. Likely a string format issue or incorrect log level.
- *Strengths*: Removes known bug; clean logs.
- *Weaknesses*: Must investigate root cause.
- *Risks*: None.
- *Guardrails*: Add test that triggers the code path and verifies no logging error.

**Recommended**: Approach A because active TODOs indicating bugs should be fixed.

---

#### CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called

**Current Code**: `demo_mode.py:938` — `@deprecated` but called as fallback at L554 and L1667.
**Root Cause**: Deprecated function kept as fallback when JuniperData service is unavailable.

**Approach A — Remove After Ensuring JuniperData Reliability**:

- *Implementation*: Remove the deprecated function and its fallback calls once JuniperData service reliability is sufficient. Until then, keep but rename to `_generate_spiral_dataset_fallback()`.
- *Strengths*: Clean code once JuniperData is reliable.
- *Weaknesses*: Can't remove until service dependency is stable.
- *Risks*: Removing fallback too early breaks demo mode when data service is down.
- *Guardrails*: Track JuniperData availability metrics before removal.

**Recommended**: Approach A — No longer needed as a fallback; data service is production-stable.

---

#### CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed

**Current Code**: `demo_mode.py:960` — mutates global RNG state.
**Root Cause**: Global seed set for reproducibility but affects all concurrent numpy users.

**Approach A — Use `np.random.default_rng(42)` Local Generator**:

- *Implementation*: Replace `np.random.seed(42)` with `rng = np.random.default_rng(42)`. Use `rng` for all random operations instead of module-level `np.random`.
- *Strengths*: Isolated RNG; thread-safe; reproducible.
- *Weaknesses*: Must update all `np.random.*` calls to `rng.*`.
- *Risks*: Slight API differences between module-level and Generator methods.
- *Guardrails*: Test reproducibility with same seed.

**Recommended**: Approach A because global seed is a numpy anti-pattern.

---

#### Issue Remediations, Section 6 — juniper-data

#### CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature

**Current Code**: `pyproject.toml` requires `python-dotenv`; only used in `__init__.py:get_arc_agi_env()`.
**Root Cause**: Hard dependency for a feature that's rarely used.

**Approach A — Move to Optional Extra**:

- *Implementation*: Move `python-dotenv` to `[project.optional-dependencies] arc-agi = ["python-dotenv"]`. Add conditional import with graceful fallback.
- *Strengths*: Smaller base install; explicit feature dependency.
- *Weaknesses*: Users must install extra for ARC-AGI.
- *Risks*: Breaking change if users rely on dotenv being available.
- *Guardrails*: Add helpful error message when dotenv not installed but ARC-AGI requested.

**Recommended**: Approach A because hard dependencies for optional features bloat installs.

---

#### CLN-JD-02: `FakeDataClient.close()` Destroys Data

**Current Code**: `testing/fake_client.py:762-766` — `close()` clears `_datasets`.
**Root Cause**: Fake treats `close()` as "destroy all state" instead of "release resources".

**Approach A — Don't Clear Data on Close**:

- *Implementation*: Remove `self._datasets.clear()` from `close()`. Only clear network resources (if any).
- *Strengths*: Matches real client behavior; tests can verify state after close.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add separate `reset()` method for tests that need clean state.

**Recommended**: Approach A because close() should release resources, not destroy data.

---

#### CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects

**Current Code**: `app.py:142` — `create_app()` called at import time.
**Root Cause**: App creation happens during import, reading env vars and creating middleware.

**Approach A — Lazy Initialization**:

- *Implementation*: Move `create_app()` call into a `get_app()` function or guard with `if __name__ == "__main__":`. Use `functools.lru_cache` for singleton behavior.
- *Strengths*: No import-time side effects; testable configuration.
- *Weaknesses*: Must update ASGI server config (uvicorn import path).
- *Risks*: ASGI server must call `get_app()` instead of importing `app`.
- *Guardrails*: Use uvicorn factory pattern: `uvicorn.run("module:get_app", factory=True)`.

**Recommended**: Approach A because import-time side effects break testing and configuration.

---

## 7. Dashboard Enhancements

### Issue Identification Tables, Section 7

#### 7.1 Critical and High-Priority Enhancements (v3.0.0)

| ID           | Severity     | Description                                                                        | Status                                                                   |
|--------------|--------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| CAN-CRIT-001 | **CRITICAL** | Decision boundary non-functional in production/service mode                        | ⚠️ Partially resolved — core logic present but not wired in service mode |
| CAN-CRIT-002 | **CRITICAL** | Save/Load snapshot in adapter — prevents training session recovery in service mode | ⚠️ Scope reduced — blocked on `/v1/snapshots/*` API                      |
| CAN-HIGH-005 | **MEDIUM**   | Remote worker status dashboard                                                     | 🔴 NOT STARTED                                                           |
| KL-1         | **MEDIUM**   | Dataset scatter plot empty in service mode (known limitation)                      | 🔴 Known limitation                                                      |
| CAN-DEF-008  | **LOW**      | Advanced 3D node interactions                                                      | 🔵 Deferred                                                              |

#### 7.2 Canopy Enhancement Backlog (CAN-000 through CAN-021)

All items 🔴 NOT STARTED unless otherwise noted. (Full table unchanged from v3 — see CAN-000 through CAN-021.)

| ID       | Module            | Description                                                               | Priority |
|----------|-------------------|---------------------------------------------------------------------------|----------|
| CAN-000  | Meta Param Menu   | Periodic updates pause when Apply Parameters button active                | P2       |
| CAN-001  | Training Metrics  | Training Loss time window toggle/dropdown                                 | P3       |
| CAN-002  | Training Metrics  | Custom rolling time window for Training Loss graph                        | P3       |
| CAN-003  | Training Metrics  | Retain candidate pool data per node addition; expandable "Previous Pools" | P3       |
| CAN-004  | Meta Param Tuning | New Tab for all exposed meta parameters                                   | P3       |
| CAN-005  | Meta Param Tuning | Pin/Unpin meta params from Tuning Tab to left side menu                   | P3       |
| CAN-006  | Meta Param Tuning | Network train epoch count parameter                                       | P3       |
| CAN-007  | Meta Param Tuning | Candidate pool training epoch count parameter                             | P3       |
| CAN-008  | Meta Param Tuning | Candidate pool node count parameter                                       | P3       |
| CAN-009  | Meta Param Tuning | Correlation threshold parameter                                           | P3       |
| CAN-010  | Meta Param Tuning | Optimizer type meta parameter                                             | P3       |
| CAN-011  | Meta Param Tuning | Activation function meta parameter                                        | P3       |
| CAN-012  | Meta Param Tuning | Number of top candidate nodes to select                                   | P3       |
| CAN-013  | Meta Param Tuning | Candidate node integration mode                                           | P3       |
| CAN-014  | Training Metrics  | Snapshot captures tuning values throughout training                       | P3       |
| CAN-015  | Training Metrics  | Snapshot replay with live tuning → new training session                   | P3       |
| CAN-016a | All               | Save/Load dashboard layout state                                          | P3       |
| CAN-016b | Dataset           | Import/Generate new dataset (file, URL, REST)                             | P3       |
| CAN-017  | All               | Tooltips on all dashboard controls                                        | P3       |
| CAN-018  | All               | Right-click tutorial descriptions with doc links                          | P4       |
| CAN-019  | All               | Walk-through style tutorial with highlighted steps                        | P4       |
| CAN-020  | All               | Show network at specific hierarchy level                                  | P4       |
| CAN-021  | All               | Show network in population (ensemble view)                                | P4       |

### Issue Remediations, Section 7

#### CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode

**Current Code**: Core decision boundary logic present but not wired in service mode.
**Root Cause**: Decision boundary visualization was developed for demo mode only; service mode adapter doesn't provide required data.

**Approach A — Wire into Service Backend**:

- *Implementation*: Add `get_decision_boundary_data()` to `CascorServiceAdapter` that fetches network weights and computes boundary grid server-side (or delegates to cascor API). Wire into existing visualization callback.
- *Strengths*: Completes planned functionality; key visual feature.
- *Weaknesses*: Compute-intensive for large networks; requires cascor API support.
- *Risks*: Performance impact on cascor service during boundary computation.
- *Guardrails*: Cache boundary data; compute on-demand only; throttle to max 1 computation/second.

**Recommended**: Approach A because decision boundary is a critical dashboard feature.

---

#### CAN-CRIT-002: Save/Load Snapshot in Adapter — Blocked on `/v1/snapshots/*` API

**Current Code**: Scope reduced — blocked on cascor snapshot API endpoints.
**Root Cause**: Cascor snapshot REST endpoints not implemented yet.

**Approach A — Implement Cascor Snapshot API First**:

- *Implementation*: Implement `/v1/snapshots/save`, `/v1/snapshots/load`, `/v1/snapshots/list`, `/v1/snapshots/delete` in cascor. Then wire canopy adapter.
- *Strengths*: Enables training session recovery; complete snapshot workflow.
- *Weaknesses*: Cascor API work required first; medium-large effort.
- *Risks*: API design must support all snapshot use cases.
- *Guardrails*: Design API spec before implementation; review with canopy team.

**Recommended**: Approach A — implement cascor API as prerequisite.

---

#### CAN-HIGH-005: Remote Worker Status Dashboard

**Current Code**: Not started.
**Root Cause**: Feature not yet implemented.

**Approach A — Worker Status Panel**:

- *Implementation*: Add new dashboard tab showing connected workers (from `/v1/workers` API), their status, assigned tasks, and health. Subscribe to worker WS events for real-time updates.
- *Strengths*: Visibility into distributed training; operational monitoring.
- *Weaknesses*: Requires cascor worker coordinator API.
- *Risks*: Worker coordinator API may not expose all needed data.
- *Guardrails*: Start with read-only status display; add management controls later.

**Recommended**: Approach A.

---

#### KL-1: Dataset Scatter Plot Empty in Service Mode

**Current Code**: Known limitation — dataset visualization unavailable in service mode.
**Root Cause**: Service adapter doesn't provide raw dataset arrays needed for scatter plot.

**Approach A — Fetch Data via API**:

- *Implementation*: Add `get_dataset_preview(n=1000)` to service adapter that fetches a subset of training data from cascor's dataset endpoint. Display in scatter plot.
- *Strengths*: Functional scatter plot in service mode.
- *Weaknesses*: Network overhead for data transfer.
- *Risks*: Large datasets may be slow to transfer.
- *Guardrails*: Limit preview to 1000 points; cache on client side.

**Recommended**: Approach A.

---

#### CAN-DEF-008: Advanced 3D Node Interactions

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document. Low priority (P4).

---

#### CAN-000 through CAN-021: Enhancement Backlog (22 items)

All items are 🔴 NOT STARTED feature enhancements. Brief remediation notes:

#### CAN-000: Periodic Updates Pause When Apply Parameters Active

**Approach A**: Add `_apply_in_progress` flag. Pause polling intervals while parameters dialog is open. Resume on Apply or Cancel.
**Recommended**: Approach A — UI state management.

#### CAN-001/CAN-002: Training Loss Time Window Toggle/Custom Rolling Window

**Approach A**: Add Plotly `xaxis.range` slider for time window. Store window preference in client state.
**Recommended**: Combined implementation as time window feature.

#### CAN-003: Retain Candidate Pool Data Per Node Addition

**Approach A**: Store candidate pool metrics in list indexed by node addition count. Add expandable "Previous Pools" UI section.
**Recommended**: Approach A.

#### CAN-004 through CAN-013: Meta Parameter Tuning Tab (10 items)

**Approach A**: Create new `MetaParameterTuningPanel` component with all meta parameters. Each param gets a slider/input with range validation. Pin/unpin to side menu via user preference store.
**Recommended**: Implement as a cohesive feature, not individual items.

#### CAN-014/CAN-015: Snapshot Tuning Capture and Replay

**Approach A**: Extend snapshot format to include current parameter values. Add replay UI that restores parameters and optionally starts new training.
**Recommended**: Approach A — requires CAN-CRIT-002 (snapshot API) first.

#### CAN-016a/CAN-016b: Save/Load Layout + Import/Generate Dataset

**Approach A**: Use browser localStorage for layout state. Add file upload and REST-based dataset import.
**Recommended**: Independent features; implement separately.

#### CAN-017/CAN-018/CAN-019: Tooltips, Right-Click Tutorials, Walk-Through

**Approach A**: Add `dcc.Tooltip` components. Right-click context menus with doc links. Walk-through using `dash-intro-js` or similar library.
**Recommended**: Progressive implementation by priority (tooltips first).

#### CAN-020/CAN-021: Hierarchy Level and Population Views

**Approach A**: Extend network visualizer to support hierarchy filtering and ensemble/population display.
**Recommended**: P4 priority; implement when multi-hierarchical CasCor (CAS-008) is available.

---

## 8. WebSocket Migration (R5-01 Remaining Phases)

### Issue Identification Tables, Section 8

#### 8.1 Phases Now Complete

(Unchanged from v3 — Phases 0-cascor, A-SDK, B-pre-a, B, C, D all ✅ Complete.)

#### 8.2 Phases Still Incomplete

| Phase | Goal                                           | Status                                         | Priority | Effort |
|-------|------------------------------------------------|------------------------------------------------|----------|--------|
| E     | Backpressure pump tasks                        | 🔴 NOT STARTED — conditional on telemetry data | P3       | M      |
| F     | Heartbeat jitter                               | 🔴 NOT STARTED                                 | P3       | S      |
| G     | Integration tests (cascor `set_params` via WS) | 🔴 NOT STARTED                                 | P2       | M      |
| H     | `_normalize_metric` audit                      | 🔴 NOT STARTED                                 | P3       | S      |

#### 8.3 Critical Individual Gaps (from WebSocket Architecture Review)

(All 12 items unchanged from v3 — GAP-WS-16 through GAP-WS-32 + Phase B-pre-b. All 🔴 NOT STARTED.)

| ID            | Priority | Description                                                                                  | Status         |
|---------------|----------|----------------------------------------------------------------------------------------------|----------------|
| GAP-WS-16     | **P0**   | `/api/metrics/history` polling bandwidth bomb (~3 MB/s per dashboard tab)                    | 🔴 NOT STARTED |
| GAP-WS-14     | **P1**   | Plotly must use `extendTraces` with `maxPoints` — full figure rebuild is 80-200ms            | 🔴 NOT STARTED |
| GAP-WS-15     | **P1**   | Browser-side rAF coalescing needed for 50Hz candidate events                                 | 🔴 NOT STARTED |
| GAP-WS-13     | **P1**   | Lossless reconnect via sequence numbers and replay buffer — events lost during disconnect    | 🔴 NOT STARTED |
| GAP-WS-25     | **P1**   | WebSocket-health-aware polling toggle — both WS+REST run simultaneously causing duplicates   | 🔴 NOT STARTED |
| GAP-WS-26     | **P1**   | Visible connection status indicator (green/yellow/red badge)                                 | 🔴 NOT STARTED |
| GAP-WS-18     | **P1**   | Topology message can exceed 64 KB silently causing connection teardown                       | 🔴 NOT STARTED |
| GAP-WS-21     | **P1**   | 1 Hz state throttle drops terminal transitions (correctness bug)                             | 🔴 NOT STARTED |
| GAP-WS-28     | **P2**   | Multi-key `update_params` torn-write race                                                    | 🔴 NOT STARTED |
| GAP-WS-31     | **P2**   | Unbounded reconnect cap — stops after 10, dashboards left open permanently stop reconnecting | 🔴 NOT STARTED |
| GAP-WS-32     | **P2**   | Per-command timeouts and orphaned-command resolution                                         | 🔴 NOT STARTED |
| Phase B-pre-b | **P1**   | CSWSH/CSRF on `/ws/control` — NOT STARTED (required before Phase D default-on)               | 🔴 NOT STARTED |

### Issue Remediations, Section 8

#### Phase E: Backpressure Pump Tasks

**Current Code**: Not started — conditional on telemetry data.
**Root Cause**: Requires measuring actual WS message throughput before designing backpressure.

**Approach A — Implement with Telemetry**:

- *Implementation*: Add WS send queue depth metrics. Implement backpressure: when queue > threshold, drop low-priority messages (metrics before state, state before topology). Use priority queue for WS send buffer.
- *Strengths*: Prevents client overwhelm; prioritizes critical messages.
- *Weaknesses*: Message loss for low-priority events.
- *Risks*: Priority tuning requires production telemetry.
- *Guardrails*: Default threshold conservative (1000 messages); counter for dropped messages.

**Recommended**: Approach A after gathering telemetry data.

---

#### Phase F: Heartbeat Jitter

**Approach A — Add Random Jitter**:

- *Implementation*: Add `±10%` random jitter to heartbeat interval: `interval * (0.9 + random.random() * 0.2)`.
- *Strengths*: Prevents thundering herd from synchronized heartbeats.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Keep within ±10% of configured interval.

**Recommended**: Approach A — trivial addition.

---

#### Phase G: Integration Tests for `set_params` via WS

**Approach A — End-to-End Test**:

- *Implementation*: Write integration test: connect WS, send `set_params`, verify parameter change via `/v1/network` GET. Use `requires_server` marker.
- *Strengths*: Validates the full param update flow.
- *Weaknesses*: Requires running server.
- *Risks*: Flaky if server slow to apply params.
- *Guardrails*: Retry with backoff on GET verification; timeout at 10s.

**Recommended**: Approach A.

---

#### Phase H: `_normalize_metric` Audit

**Approach A — Comprehensive Audit**:

- *Implementation*: Audit all `_normalize_metric` callsites. Verify each metric name maps correctly to the canonical name. Document metric naming conventions.
- *Strengths*: Ensures consistent metric names across dashboard.
- *Weaknesses*: Manual audit effort.
- *Risks*: None.
- *Guardrails*: Add unit test for each metric normalization.

**Recommended**: Approach A.

---

#### GAP-WS-16: `/api/metrics/history` Polling Bandwidth Bomb (~3 MB/s)

**Current Code**: REST polling for metrics history; ~3 MB/s per dashboard tab.
**Root Cause**: Polling-based architecture transfers all history on every poll.

**Approach A — WS Push with Delta Updates**:

- *Implementation*: Replace polling with WS subscription. Server pushes only new metric entries since client's last sequence number. Client appends to local buffer.
- *Strengths*: ~99% bandwidth reduction; real-time updates.
- *Weaknesses*: Requires WS subscription management.
- *Risks*: Must handle reconnection and catch-up.
- *Guardrails*: Keep REST endpoint as fallback; add sequence-based delta API.

**Recommended**: Approach A because 3 MB/s per tab is unsustainable.

---

#### GAP-WS-14: Plotly `extendTraces` with `maxPoints` Limit

**Current Code**: Full figure rebuild on each update (80-200ms).
**Root Cause**: Replacing entire figure data instead of appending to existing traces.

**Approach A — Use `extendTraces`**:

- *Implementation*: Use Plotly.js `Plotly.extendTraces(divId, update, traceIndices, maxPoints)` via clientside callback. Set `maxPoints` to limit (e.g., 10000).
- *Strengths*: ~10x rendering speedup; bounded memory.
- *Weaknesses*: Requires Dash clientside callback.
- *Risks*: Must handle trace initialization and reset.
- *Guardrails*: Add `maxPoints` to Settings; default 10000.

**Recommended**: Approach A because full figure rebuild at 50Hz is prohibitively expensive.

---

#### GAP-WS-15: Browser-Side rAF Coalescing for 50Hz Candidate Events

**Approach A — requestAnimationFrame Batching**:

- *Implementation*: Buffer incoming WS events. Process batch once per `requestAnimationFrame` (~60fps). Use latest value for each metric (skip intermediate).
- *Strengths*: Prevents 50Hz DOM updates; smooth animations.
- *Weaknesses*: Slight message delivery latency.
- *Risks*: None.
- *Guardrails*: Max batch size 100; flush timer for low-frequency events.

**Recommended**: Approach A.

---

#### GAP-WS-13: Lossless Reconnect via Sequence Numbers and Replay Buffer

**Approach A — Sequence-Based Replay**:

- *Implementation*: Client sends last-received sequence number on reconnect. Server replays from sequence N+1 using replay buffer. Already partially implemented in cascor (`ws_replay_buffer_size: 1024`).
- *Strengths*: No event loss during brief disconnects.
- *Weaknesses*: Buffer overflow loses old events.
- *Risks*: Replay buffer size must accommodate typical disconnect durations.
- *Guardrails*: Log replay events at DEBUG; alert on buffer overflow.

**Recommended**: Approach A — partially implemented, needs client-side integration.

---

#### GAP-WS-25: WebSocket-Health-Aware Polling Toggle

**Approach A — Health-Aware Fallback**:

- *Implementation*: When WS is healthy, disable REST polling. On WS disconnect, enable REST polling. On WS reconnect, disable polling again. Use `WSHealthMonitor` component.
- *Strengths*: Eliminates duplicate data; reduces load.
- *Weaknesses*: Must handle transition periods.
- *Risks*: Brief gap during toggle.
- *Guardrails*: 5-second overlap during transition to prevent data gaps.

**Recommended**: Approach A.

---

#### GAP-WS-26: Visible Connection Status Indicator

**Approach A — Status Badge Component**:

- *Implementation*: Add `ConnectionStatusBadge` component: green (connected), yellow (reconnecting), red (disconnected). Position in dashboard header.
- *Strengths*: User visibility into connection state.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Include tooltip with connection details.

**Recommended**: Approach A.

---

#### GAP-WS-18: Topology Message >64KB Causes Connection Teardown

**Approach A — Message Chunking**:

- *Implementation*: Add topology message size check. If >64KB, split into chunks with sequence header: `{"chunk": 1, "total": 3, "data": ...}`. Client reassembles.
- *Strengths*: Handles arbitrarily large topologies.
- *Weaknesses*: Chunking protocol complexity.
- *Risks*: Chunk reassembly failures.
- *Guardrails*: Fallback to REST fetch if chunked delivery fails.

**Approach B — Topology Compression**:

- *Implementation*: Compress topology JSON with zlib before WS send. Client decompresses.
- *Strengths*: Simple; typically 5-10x compression for JSON.
- *Weaknesses*: CPU overhead for compression.
- *Risks*: Client must support decompression.
- *Guardrails*: Only compress messages > 10KB.

**Recommended**: Approach B for simplicity; Approach A for guaranteed delivery.

---

#### GAP-WS-21: 1 Hz State Throttle Drops Terminal Transitions

**Cross-References**: Same as BUG-CN-06.
**Approach A**: See BUG-CN-06 remediation (always send terminal states).
**Recommended**: See BUG-CN-06.

---

#### GAP-WS-28: Multi-Key `update_params` Torn-Write Race

**Approach A — Atomic Parameter Update**:

- *Implementation*: Server applies all params from a single `update_params` message atomically (within a lock). No partial application.
- *Strengths*: Consistent parameter state.
- *Weaknesses*: Lock contention during training.
- *Risks*: Must not block training thread.
- *Guardrails*: Queue param updates; apply between training steps.

**Recommended**: Approach A.

---

#### GAP-WS-31: Unbounded Reconnect Cap — Stops After 10

**Approach A — Infinite Reconnect with Backoff**:

- *Implementation*: Remove max reconnect limit. Use exponential backoff with cap (e.g., max 5 minutes between attempts). Add configurable `max_reconnect_interval`.
- *Strengths*: Dashboards never permanently lose connection.
- *Weaknesses*: Persistent retries on permanently dead servers.
- *Risks*: Resource usage from retry polling.
- *Guardrails*: Show user notification after 10 failures; continue retrying silently.

**Recommended**: Approach A.

---

#### GAP-WS-32: Per-Command Timeouts and Orphaned-Command Resolution

**Approach A — Command Timeout with Cleanup**:

- *Implementation*: Add per-command timeout (default 30s). On timeout, resolve pending future with `TimeoutError`. Clean up command from pending map. Log orphaned commands.
- *Strengths*: Prevents indefinite hangs; clean resource management.
- *Weaknesses*: Must choose appropriate timeout per command type.
- *Risks*: Premature timeout on slow operations.
- *Guardrails*: Configurable per-command timeouts; log timeouts at WARNING.

**Recommended**: Approach A.

---

#### Phase B-pre-b: CSWSH/CSRF on `/ws/control`

**Cross-References**: Related to SEC-05.
**Approach A**: Apply same Origin validation as SEC-05 fix specifically to `/ws/control`.
**Recommended**: Implement alongside SEC-05.

---

## 9. Microservices and Infrastructure

(Sections 9.1, 9.2, 9.3 unchanged from v3 — carried forward.)

### Issue Identification Tables, Section 9

#### 9.1 Completed Phases

| Phase   | Description                                          | Status      |
|---------|------------------------------------------------------|-------------|
| Phase 1 | Critical startup/shutdown fixes (plant/chop scripts) | ✅ Complete |
| Phase 2 | systemd service units + ctl scripts (all 4 services) | ✅ Complete |
| Phase 3 | Worker Dockerfile, docker-compose, systemd           | ✅ Complete |
| Phase 4 | Kubernetes Helm chart (23 templates)                 | ✅ Complete |

#### 9.2 Phase 5: Observability & Hardening — INCOMPLETE

| Step | Task                                             | Status               | Evidence                                                          |
|------|--------------------------------------------------|----------------------|-------------------------------------------------------------------|
| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |
| 5.2  | Define alert rules for service availability      | ✅ Complete          | `alert_rules.yml` has 6 rule groups, 12 real alerts               |
| 5.3  | Standardize health endpoints across all services | 🔴 NOT STARTED       | Health endpoint formats differ across services                    |
| 5.4  | Volume backup/restore documentation              | 🔴 NOT STARTED       | No backup docs exist                                              |
| 5.5  | Startup validation test suite                    | 🔴 NOT STARTED       | No startup script tests in juniper-ml                             |

#### 9.3 Microservices Architecture Roadmap (Phases 5–9)

| Phase | Description                                           | Status                                               |
|-------|-------------------------------------------------------|------------------------------------------------------|
| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |
| 6     | Client Library Fakes                                  | ✅ Complete (FakeCascorClient, FakeDataClient)       |
| 7     | Docker Compose Demo Profile                           | ✅ Complete (demo profile in juniper-deploy)         |
| 8     | Enhanced Health Checks with Dependency Status         | ⚠️ Partial — some services have dependency reporting |
| 9     | Configuration Standardization (Pydantic BaseSettings) | ✅ Complete for cascor and data; canopy migrated     |

### Issue Remediations, Section 9

#### 5.1: AlertManager Receivers — Placeholders Only

**Approach A — Configure Real Receivers**:

- *Implementation*: Add Slack webhook URL and/or email SMTP config to `alertmanager.yml`. Keep placeholders for unused channels.
- *Strengths*: Functional alerting.
- *Weaknesses*: Requires external service config.
- *Risks*: Webhook URL must be kept secret.
- *Guardrails*: Use environment variables for webhook URLs.

**Recommended**: Approach A.

---

#### 5.3: Standardize Health Endpoints

**Cross-References**: Related to API-01, API-02, XREPO-13.
**Approach A**: Standardize all health endpoints to `{"status": "ok", "version": "x.y.z", "service": "name"}`. See API-01/API-02 remediations.
**Recommended**: See API-01/API-02.

---

#### 5.4: Volume Backup/Restore Documentation

**Approach A — Create Documentation**:

- *Implementation*: Write `docs/BACKUP_RESTORE.md` covering: Docker volume backup (`docker cp`/`docker volume`), data directory backup, snapshot backup, restore procedures.
- *Strengths*: Operational documentation; disaster recovery.
- *Weaknesses*: Documentation effort.
- *Risks*: None.
- *Guardrails*: Test restore procedure in staging.

**Recommended**: Approach A.

---

#### 5.5: Startup Validation Test Suite

**Approach A — Add Service Startup Tests**:

- *Implementation*: Create tests that verify each service starts correctly: health endpoint responds, correct version reported, configuration loaded properly.
- *Strengths*: Catches startup regressions.
- *Weaknesses*: Requires running services in CI.
- *Risks*: Flaky if services slow to start.
- *Guardrails*: Health check polling with timeout.

**Recommended**: Approach A.

---

## 10. CasCor Algorithm and Feature Enhancements

(All items unchanged from v3 — all 🔴 NOT STARTED.)

### Issue Identification Tables, Section 10

#### 10.1 Training Control

| ID      | Description                                                | Priority |
|---------|------------------------------------------------------------|----------|
| CAS-002 | Separate epoch limits for full network and candidate nodes | P3       |
| CAS-003 | Max train session iterations meta parameter                | P3       |
| CAS-006 | Auto-snap best network when new best accuracy achieved     | P3       |

#### 10.2 Algorithm Enhancements

| ID      | Description                                           | Priority |
|---------|-------------------------------------------------------|----------|
| ENH-006 | Flexible optimizer system (Adam, SGD, RMSprop, AdamW) | P3       |
| ENH-007 | N-best candidate layer selection                      | P3       |

#### 10.3 Network Architecture

| ID      | Description                                              | Priority |
|---------|----------------------------------------------------------|----------|
| CAS-008 | Network hierarchy management (multi-hierarchical CasCor) | P4       |
| CAS-009 | Network population management (ensemble approaches)      | P4       |

#### 10.4 Serialization & Validation

| ID      | Description                                                              | Priority |
|---------|--------------------------------------------------------------------------|----------|
| ENH-001 | Comprehensive serialization test suite (7 remaining tests)               | P2       |
| ENH-002 | Hidden units checksum validation (SHA256)                                | P2       |
| ENH-003 | Tensor shape validation during load                                      | P2       |
| ENH-004 | Enhanced format validation (`_validate_format()`)                        | P2       |
| ENH-005 | Refactor candidate unit instantiation (factory method)                   | P2       |
| ENH-008 | Worker cleanup improvements (SIGKILL fallback)                           | P2       |

#### 10.5 Storage & Infrastructure

| ID         | Description                                                          | Priority       |
|------------|----------------------------------------------------------------------|----------------|
| CAS-005    | Extract common dependencies to modules (cascor + worker shared code) | P3             |
| CAS-010    | Snapshot vector DB storage (indexed by UUID)                         | P4             |
| —          | Shared memory startup sweep for stale `juniper_train_*` blocks       | P3             |
| —          | `/v1/snapshots/*` API endpoints (4) — deferred, blocks CAN-CRIT-002  | P2             |
| P3-NEW-003 | GPU/CUDA support for training                                        | P4 (XL effort) |
| —          | Large file refactoring (no file > 2000 lines)                        | P3             |
| —          | Auto-generated API docs (MkDocs/Sphinx)                              | P3             |

### Issue Remediations, Section 10

All CasCor enhancement items are feature requests. Brief remediation approaches:

#### CAS-002/CAS-003: Separate Epoch Limits and Max Iterations

**Approach A**: Add `network_max_epochs`, `candidate_max_epochs`, `max_iterations` to training parameters. Enforce in training loop.
**Recommended**: Approach A — parameter additions.

#### CAS-006: Auto-Snap Best Network

**Approach A**: Track best accuracy in training loop. Auto-save snapshot when new best achieved. Add `auto_snapshot_best: bool = True` setting.
**Recommended**: Approach A.

#### ENH-006/ENH-007: Flexible Optimizer and N-Best Candidate Selection

**Approach A**: Create `OptimizerFactory` supporting Adam/SGD/RMSprop/AdamW. For N-best: train candidate pool, rank by correlation, install top-N.
**Recommended**: Approach A — separate features.

#### CAS-008/CAS-009: Hierarchy and Population Management

**Approach A**: P4 priority. Design architecture for multi-hierarchical CasCor and ensemble approaches. Implement after core algorithm stabilizes.
**Recommended**: Deferred — design phase only.

#### ENH-001 through ENH-005, ENH-008: Serialization and Validation

**Approach A**: Implement remaining 7 serialization tests (ENH-001). Add SHA256 checksum (ENH-002), shape validation (ENH-003), format validation (ENH-004). Refactor candidate factory (ENH-005). Add SIGKILL fallback for worker cleanup (ENH-008).
**Recommended**: Approach A — implement as a serialization hardening sprint.

#### CAS-005, CAS-010, and Other Storage Items

**Approach A**: Extract shared code to `juniper-core` package (CAS-005). Snapshot vector DB (CAS-010) is P4. Shared memory sweep, snapshot API, GPU support, file refactoring, API docs — implement per priority.
**Recommended**: Prioritize by dependency graph; CAS-005 enables other items.

---

## 11. Cross-Repository Alignment Issues

### Issue Identification Tables, Section 11

#### 11.1 Original items (v3)

| ID        | Severity     | Repositories           | Description                                                                                                    | Evidence                                                              |
|-----------|--------------|------------------------|----------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| XREPO-01  | **CRITICAL** | data-client ↔ data     | Generator name `"circle"` vs server's `"circles"` — client requests will fail with 400                         | `juniper_data_client/constants.py:90` — `GENERATOR_CIRCLE = "circle"` |
| XREPO-01b | **CRITICAL** | data-client ↔ data     | `GENERATOR_MOON = "moon"` — server has **no moon generator** at all                                            | `juniper_data_client/constants.py:91`                                 |
| XREPO-01c | **MEDIUM**   | data-client ↔ data     | Client missing constants for 5 server generators: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi` | Only `spiral`, `xor`, `circle`, `moon` defined                        |
| XREPO-02  | **MEDIUM**   | cascor-client          | 503 not in `RETRYABLE_STATUS_CODES` — transient unavailability not retried                                     | `constants.py:31` — `RETRYABLE_STATUS_CODES = [502, 504]`             |
| XREPO-03  | **MEDIUM**   | cascor-client          | No `FakeCascorControlStream` — testing gap for WS control                                                      | `testing/` has FakeClient and FakeTrainingStream only                 |
| XREPO-04  | **MEDIUM**   | cascor-worker ↔ cascor | Protocol constants alignment is manual — no CI automation for bit-identity verification                        | Wave 5 verified, but cascor change could silently break worker        |
| XREPO-05  | **MEDIUM**   | cascor ↔ canopy        | State name inconsistency — UPPERCASE vs title-case vs FSM constants                                            | Different repos use different casing for same training states         |
| XREPO-06  | **MEDIUM**   | cascor ↔ canopy        | `epochs_max` default discrepancy — cascor 10,000 vs API 200 vs canopy 1,000,000                                | Three different defaults for the same parameter across the stack      |
| XREPO-07  | **MEDIUM**   | cascor-client          | `command()` vs `set_params()` message format inconsistency — `command()` never sends `type` field              | Wire protocol mismatch between the two methods                        |

#### 11.2 New cross-repo issues (v4)

| ID       | Severity   | Repositories           | Description                                                                                            | Evidence                                                                                         |
|----------|------------|------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| XREPO-08 | **MEDIUM** | cascor-client          | Three distinct WS message formats: `send_command()`, `command()`, and `set_params()` all differ        | `ws_client.py:99` (no type), `:232` (no type), `:280-285` (has `type: "command"`) — inconsistent |
| XREPO-09 | **MEDIUM** | data-client ↔ data     | Client `create_dataset()` missing `tags` and `ttl_seconds` parameters from server API                  | Server `CreateDatasetRequest` has 8 fields; client only sends 6 — `tags`/`ttl_seconds` dropped   |
| XREPO-10 | **MEDIUM** | data-client            | `FakeDataClient` metadata schema diverges from real server response structure                          | Fake uses `"n_full"` key, flat meta structure; real returns full `DatasetMeta` Pydantic model    |
| XREPO-11 | **MEDIUM** | data-client            | Client retries non-idempotent mutations (POST, DELETE)                                                 | `RETRY_ALLOWED_METHODS = ["HEAD", "GET", "POST", "PATCH", "DELETE"]` — can create duplicates     |
| XREPO-12 | **MEDIUM** | cascor-worker          | `y` tensor received from server but never used in training task                                        | `task_executor.py:35` documents key `y` but L74-75 only use `candidate_input`/`residual_error`   |
| XREPO-13 | **MEDIUM** | cascor ↔ data ↔ canopy | Health endpoint `status` value inconsistency: cascor/data return `"ok"`, canopy returns `"healthy"`    | `cascor/health.py:27`, `canopy/main.py:694-705` (v5 new)                                         |
| XREPO-14 | **MEDIUM** | cascor-client ↔ cascor | FakeClient state consts use different vocab: `"idle"`/`"training"` vs server's `"STOPPED"`/`"STARTED"` | `testing/constants.py:39-43` vs server `state_machine.py:21-29` (v5 new)                         |
| XREPO-15 | **MEDIUM** | all services           | Error response format inconsistent — three different JSON error shapes across services                 | cascor: `{"status":"error","error":{}}` + `{"detail":""}`, data: `{"detail":""}`,                |
|          |            |                        |                                                                                                        | -- canopy: `{"error":"","detail":"","status_code":500}` (v5 new)                                 |
| XREPO-16 | **MEDIUM** | data ↔ data-client     | Client missing methods for 4 server endpoints: filter, stats, cleanup-expired, individual tags         | Server has routes; client has no corresponding methods (v5 new)                                  |
| XREPO-17 | **LOW**    | cascor ↔ cascor-client | `candidate_progress` WS message broadcast by server but not in client constants, no callback           | `messages.py:102-109` — server sends it; client has no handler (v5 new)                          |

### Issue Remediations, Section 11

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

**Current Code**: `juniper_data_client/constants.py:90` — `GENERATOR_CIRCLE = "circle"`. Server uses `"circles"`.
**Root Cause**: Client constant written from naming intuition, not copied from server registry.
**Cross-References**: XREPO-01 = DC-01

**Approach A — Fix Client Constant**:

- *Implementation*: Change `GENERATOR_CIRCLE = "circles"` in constants.py. Add deprecation alias: `GENERATOR_CIRCLE_LEGACY = "circle"`. Update `GENERATOR_DESCRIPTION_CIRCLE` and fake_client.py keys.
- *Strengths*: Simplest fix; aligns client with server truth.
- *Weaknesses*: Breaking change for downstream code using the constant.
- *Risks*: Downstream callers using the string literal `"circle"` won't be caught.
- *Guardrails*: Deprecation alias for one release cycle; update CHANGELOG; add CI test that verifies client constants match server registry.

**Recommended**: Approach A because the server is the source of truth.

---

#### XREPO-01b: `GENERATOR_MOON = "moon"` — Server Has No Moon Generator

**Current Code**: `juniper_data_client/constants.py:91` — `GENERATOR_MOON = "moon"`. Server has no moon generator.
**Root Cause**: Client defined a generator constant for a server-side generator that was never implemented.
**Cross-References**: XREPO-01b = DC-02

**Approach A — Remove from Client**:

- *Implementation*: Remove `GENERATOR_MOON` and `GENERATOR_DESCRIPTION_MOON` from constants.py. Add deprecation note in CHANGELOG.
- *Strengths*: Eliminates guaranteed-failure code path.
- *Weaknesses*: Breaking change for any code referencing the constant.
- *Risks*: Minimal — calls using this constant already fail with 400.
- *Guardrails*: Keep as deprecated alias for one release; log warning on use.

**Approach B — Implement Server-Side MoonGenerator**:

- *Implementation*: Add `MoonGenerator` to juniper-data using `sklearn.datasets.make_moons()`.
- *Strengths*: Fulfills client expectation; adds useful dataset type; meets feature requirements.
- *Weaknesses*: More effort; adds sklearn dependency if not present.
- *Risks*: Must define parameter schema consistent with other generators.
- *Guardrails*: Add integration test between client and server for moon generator.

**Recommended**: Approach B to meet feature requirements.

---

#### XREPO-01c: Client Missing Constants for 5 Server Generators

**Current Code**: Only `spiral`, `xor`, `circle`, `moon` defined. Server also has: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`.
**Root Cause**: Client constants were not updated when new server generators were added.
**Cross-References**: XREPO-01c = DC-03

**Approach A — Add Missing Constants**:

- *Implementation*: Add `GENERATOR_GAUSSIAN = "gaussian"`, `GENERATOR_CHECKERBOARD = "checkerboard"`, `GENERATOR_CSV_IMPORT = "csv_import"`, `GENERATOR_MNIST = "mnist"`, `GENERATOR_ARC_AGI = "arc_agi"` with corresponding descriptions.
- *Strengths*: Complete client coverage; prevents hardcoded string usage.
- *Weaknesses*: Must keep in sync going forward.
- *Risks*: None.
- *Guardrails*: Add CI test that compares client generator constants with server registry.

**Recommended**: Approach A because comprehensive constants prevent hardcoded strings.

---

#### XREPO-02: 503 Not in `RETRYABLE_STATUS_CODES`

**Current Code**: `cascor-client/constants.py:31` — `RETRYABLE_STATUS_CODES = [502, 504]`.
**Root Cause**: 503 (Service Unavailable) — the most common transient error — was omitted from the retry list.
**Cross-References**: XREPO-02 = CC-02

**Approach A — Add 503**:

- *Implementation*: Change to `RETRYABLE_STATUS_CODES = [502, 503, 504]`.
- *Strengths*: One-line fix; handles service restarts and deployments.
- *Weaknesses*: None.
- *Risks*: None — 503 is definitionally transient.
- *Guardrails*: Add 429 (Too Many Requests) while at it, with Retry-After header support.

**Recommended**: Approach A because 503 is the canonical retryable status code.

---

#### XREPO-03: No `FakeCascorControlStream` — Testing Gap for WS Control

**Current Code**: `testing/` has `FakeClient` and `FakeTrainingStream` only.
**Root Cause**: Control stream fake was not implemented when the control stream was added.
**Cross-References**: XREPO-03 = CC-03

**Approach A — Implement FakeCascorControlStream**:

- *Implementation*: Create `FakeCascorControlStream` in `testing/fake_control_stream.py` following the pattern of `FakeTrainingStream`. Support `command()`, `set_params()`, and canned responses.
- *Strengths*: Enables unit testing of control stream consumers; consistent API.
- *Weaknesses*: Must keep in sync with real `CascorControlStream` API.
- *Risks*: Fake may drift from real implementation over time.
- *Guardrails*: Add `FakeControlStream` to the testing `__init__.py` exports; add conformance tests.

**Recommended**: Approach A because testing fakes are essential for downstream consumers.

---

#### XREPO-04: Protocol Constants Alignment Is Manual

**Current Code**: Worker protocol constants manually copied from cascor; no CI verification.
**Root Cause**: No automated check that worker and cascor protocol constants are identical.

**Approach A — CI Verification Script**:

- *Implementation*: Add CI step that imports both cascor and worker protocol constants and asserts equality. Use `pytest` parameterized test or a standalone verification script.
- *Strengths*: Automated drift detection; catches misalignment on every PR.
- *Weaknesses*: Requires both packages importable in CI environment.
- *Risks*: CI setup complexity.
- *Guardrails*: Run as part of worker CI; fail on any mismatch.

**Approach B — Shared Protocol Package**:

- *Implementation*: Extract protocol constants to a shared `juniper-protocol` package imported by both.
- *Strengths*: Single source of truth; impossible to drift.
- *Weaknesses*: New package to maintain; adds dependency.
- *Risks*: Over-engineering for ~20 constants.
- *Guardrails*: Start with CI verification (Approach A); migrate to shared package if constants grow.

**Recommended**: Approach A because CI verification catches drift with minimal infrastructure.

---

#### XREPO-05: State Name Inconsistency — UPPERCASE vs Title-Case vs FSM Constants

**Current Code**: Different repos use different casing for training states (e.g., `"STOPPED"` vs `"Stopped"` vs `"stopped"`).
**Root Cause**: No canonical state name convention was established when multiple repos implemented state tracking.

**Approach A — Standardize to UPPERCASE**:

- *Implementation*: Define canonical state names in cascor (the source of truth): `STOPPED`, `STARTED`, `PAUSED`, `FAILED`, `COMPLETED`. All clients normalize received states to uppercase. Add constants to cascor-client.
- *Strengths*: Single canonical form; consistent across ecosystem.
- *Weaknesses*: Breaking change for canopy/client code using other casing.
- *Risks*: Must update all state comparisons across repos.
- *Guardrails*: Case-insensitive comparison during migration period.

**Recommended**: Approach A because the server should define canonical state names.

---

#### XREPO-06: `epochs_max` Default Discrepancy

**Current Code**: cascor default 10,000 vs API 200 vs canopy 1,000,000.
**Root Cause**: Each component independently chose a "reasonable" default without coordination.

**Approach A — Cascor as Authority**:

- *Implementation*: Use cascor's `epochs_max` from `/v1/network` response as the default everywhere. Canopy reads from API response; cascor-client documents the server default.
- *Strengths*: Single source of truth; defaults always match server.
- *Weaknesses*: Requires API call to get default (canopy can cache).
- *Risks*: API may be unreachable during initial UI render.
- *Guardrails*: Use cascor default (10,000) as fallback in canopy; log when using fallback.

**Recommended**: Approach A because the server owns the parameter definition.

---

#### XREPO-07: `command()` vs `set_params()` Message Format Inconsistency

**Current Code**: `command()` never sends `type` field; `set_params()` includes `type: "command"`.
**Root Cause**: Two methods were implemented at different times without consistent envelope design.
**Cross-References**: XREPO-07 = CC-06, XREPO-08

**Approach A — Standardize Envelope Format**:

- *Implementation*: Both methods should send consistent envelope: `{"type": "command", "command": "...", ...}` for commands and `{"type": "set_params", "params": {...}}` for param updates.
- *Strengths*: Consistent wire protocol; server can dispatch by `type` field.
- *Weaknesses*: Breaking change if server relies on format differences.
- *Risks*: Must coordinate with server-side message parsing.
- *Guardrails*: Version the WS protocol; server supports both old and new format during migration.

**Recommended**: Approach A because consistent message envelopes are essential for protocol reliability.

---

#### XREPO-08: Three Distinct WS Message Formats

**Current Code**: `ws_client.py:99` (no type), `:232` (no type), `:280-285` (has `type: "command"`).
**Root Cause**: Methods added at different times without protocol specification.
**Cross-References**: XREPO-08 extends XREPO-07

**Approach A**: See XREPO-07 remediation (standardize envelope format).
**Recommended**: See XREPO-07.

---

#### XREPO-09: Client `create_dataset()` Missing `tags` and `ttl_seconds`

**Current Code**: Server `CreateDatasetRequest` has 8 fields; client only sends 6.
**Root Cause**: Client method not updated when server API added `tags` and `ttl_seconds`.

**Approach A — Add Missing Parameters**:

- *Implementation*: Add `tags: Optional[List[str]] = None` and `ttl_seconds: Optional[int] = None` to `create_dataset()` method. Include in request body when not None.
- *Strengths*: Full API parity; enables all server features.
- *Weaknesses*: None.
- *Risks*: None — new optional parameters are backward compatible.
- *Guardrails*: Add test calling with tags and ttl_seconds; verify server receives them.

**Recommended**: Approach A because missing API parameters are straightforward to add.

---

#### XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server

**Current Code**: Fake uses `"n_full"` key and flat meta structure; real returns full `DatasetMeta` Pydantic model.
**Root Cause**: Fake was written against an early API version and never updated.

**Approach A — Align Fake Schema**:

- *Implementation*: Update `FakeDataClient` to return metadata matching `DatasetMeta` Pydantic model structure. Import `DatasetMeta` or replicate its fields.
- *Strengths*: Tests exercise realistic API responses; catches schema-dependent bugs.
- *Weaknesses*: Fake becomes more complex.
- *Risks*: Must maintain schema alignment as DatasetMeta evolves.
- *Guardrails*: Add conformance test that validates fake metadata matches real schema.

**Recommended**: Approach A because fakes that diverge from reality make tests unreliable.

---

#### XREPO-11: Client Retries Non-Idempotent Mutations (POST, DELETE)

**Current Code**: `RETRY_ALLOWED_METHODS = ["HEAD", "GET", "POST", "PATCH", "DELETE"]` — includes POST and DELETE.
**Root Cause**: Retry configuration doesn't distinguish between idempotent and non-idempotent methods.

**Approach A — Remove Non-Idempotent Methods**:

- *Implementation*: Change to `RETRY_ALLOWED_METHODS = ["HEAD", "GET", "PUT"]`. POST, PATCH, DELETE should not be auto-retried.
- *Strengths*: Prevents duplicate creation/deletion; standard HTTP semantics.
- *Weaknesses*: Callers must implement their own retry logic for mutations.
- *Risks*: May break callers relying on auto-retry for mutations.
- *Guardrails*: Add `retry_non_idempotent: bool = False` option for explicit opt-in.

**Recommended**: Approach A because retrying POST/DELETE can cause data corruption.

---

#### XREPO-12: `y` Tensor Received but Never Used in Worker

**Current Code**: `task_executor.py:35` documents key `y` but L74-75 only use `candidate_input`/`residual_error`.
**Root Cause**: Server sends `y` tensor but worker training only needs candidate input and residual error.

**Approach A — Document and Optionally Remove**:

- *Implementation*: If `y` is intentionally unused (residual_error replaces it), document in protocol spec and optionally stop sending it to save bandwidth. If `y` should be used, fix the training logic.
- *Strengths*: Clarity on protocol intent; potential bandwidth savings.
- *Weaknesses*: Protocol change requires coordination.
- *Risks*: Future training algorithms may need `y`.
- *Guardrails*: Add `include_targets: bool = True` to server config; default True for backward compat.

**Recommended**: Approach A — investigate whether `y` is needed, then document decision.

---

#### XREPO-13: Health Endpoint `status` Value Inconsistency

**Current Code**: cascor/data return `"ok"`, canopy returns `"healthy"`.
**Root Cause**: No standardized health response format across services.
**Cross-References**: XREPO-13 = API-01

**Approach A**: See API-01 remediation below.
**Recommended**: See API-01.

---

#### XREPO-14: FakeClient State Constants Use Different Vocabulary

**Current Code**: `testing/constants.py:39-43` uses `"idle"`/`"training"` vs server's `"STOPPED"`/`"STARTED"`.
**Root Cause**: Fake constants defined independently of server state machine.
**Cross-References**: XREPO-14 = API-04

**Approach A — Align with Server Constants**:

- *Implementation*: Change fake constants to match server: `STATE_STOPPED = "STOPPED"`, `STATE_STARTED = "STARTED"`, etc. Import from a shared constants module if available.
- *Strengths*: Tests exercise realistic state values.
- *Weaknesses*: Breaking change for tests using old constants.
- *Risks*: Must update all test assertions.
- *Guardrails*: Add deprecation aliases for old names.

**Recommended**: Approach A because fake/real vocabulary mismatch masks integration bugs.

---

#### XREPO-15: Error Response Format Inconsistent

**Current Code**: Three different JSON error shapes across services.
**Root Cause**: Each service implemented error responses independently.
**Cross-References**: XREPO-15 = API-05

**Approach A**: See API-05 remediation below.
**Recommended**: See API-05.

---

#### XREPO-16: Client Missing Methods for 4 Server Endpoints

**Current Code**: Server has filter, stats, cleanup-expired, individual tags routes; client has no corresponding methods.
**Root Cause**: Client was not updated when server API was extended.
**Cross-References**: XREPO-16 = API-07

**Approach A — Add Missing Client Methods**:

- *Implementation*: Add `filter_datasets()`, `get_stats()`, `cleanup_expired()`, `update_tags()` methods to data-client matching server API signatures.
- *Strengths*: Complete API coverage; enables all server features from client.
- *Weaknesses*: Must maintain parity as API evolves.
- *Risks*: None — additive changes only.
- *Guardrails*: Add integration tests for each new method; update FakeDataClient to include them.

**Recommended**: Approach A because missing client methods force users to make raw HTTP calls.

---

#### XREPO-17: `candidate_progress` WS Message Not in Client Constants

**Current Code**: `messages.py:102-109` — server broadcasts it; client has no handler.
**Root Cause**: Server-side message type added without corresponding client update.
**Cross-References**: XREPO-17 = API-06

**Approach A — Add to Client Constants and Handler**:

- *Implementation*: Add `MSG_CANDIDATE_PROGRESS = "candidate_progress"` to cascor-client constants. Add optional callback handler in training stream.
- *Strengths*: Enables progress tracking for candidate training phase.
- *Weaknesses*: Must define callback interface.
- *Risks*: None — additive change.
- *Guardrails*: Default to no-op handler; add to FakeTrainingStream.

**Recommended**: Approach A because unhandled server messages are silently lost.

---

---

## 12. Housekeeping and Broken References

### Issue Identification Tables, Section 12

#### 12.1 Original items (v3)

| ID     | Repository     | Description                                                                              | Priority |
|--------|----------------|------------------------------------------------------------------------------------------|----------|
| HSK-01 | juniper-canopy | 3 broken symlinks in `notes/development/` pointing to deleted juniper-ml files           | P3       |
| HSK-02 | juniper-cascor | `src/remote_client/` directory still exists (3 files) — superseded by cascor-worker      | P2       |
| HSK-03 | juniper-cascor | `src/spiral_problem/check.py` — 600-line stale duplicate                                 | P2       |
| HSK-04 | juniper-cascor | 32 test files with hardcoded `sys.path.append` to old monorepo paths                     | P2       |
| HSK-05 | cascor-client  | AGENTS.md header version 0.3.0, package is 0.4.0                                         | P3       |
| HSK-06 | juniper-data   | AGENTS.md header version 0.5.0, package is 0.6.0                                         | P3       |
| HSK-07 | cascor-client  | File headers (constants.py, testing/*) show versions 0.1.0–0.3.0 (should be 0.4.0)       | P3       |
| HSK-08 | data-client    | `tests/conftest.py` version header says 0.3.1, project is 0.4.0                          | P3       |
| HSK-09 | cascor-client  | Unfinished code: `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes never referenced | P3       |
| HSK-10 | juniper-ml     | `scripts/test.bash` outdated/non-functional — references removed `nohup.out`             | P3       |
| HSK-11 | juniper-ml     | `wake_the_claude.bash` `DEBUG="${TRUE}"` hardcoded ON — noisy output                     | P2       |
| HSK-12 | juniper-ml     | `NOHUP_STATUS=$?` captures fork status (always 0) — dead error check                     | P3       |
| HSK-13 | juniper-canopy | 169 hardcoded ThemeColors remain — MED-026 rollout deferred until hardcoded colors fixed | P3       |

#### 12.2 New housekeeping items (v4)

| ID     | Repository    | Description                                                                                                              | Priority |
|--------|---------------|--------------------------------------------------------------------------------------------------------------------------|----------|
| HSK-14 | juniper-ml    | `resume_session.bash` contains hardcoded session UUID — one-time-use script committed as permanent                       | P3       |
| HSK-15 | juniper-ml    | `util/global_text_replace.bash` is a no-op — search==replace identical strings; misspelled `KIBAB`                       | P3       |
| HSK-16 | juniper-ml    | `util/kill_all_pythons.bash` uses `sudo kill -9` on ALL Python processes indiscriminately                                | P2       |
| HSK-17 | juniper-ml    | `util/worktree_new.bash` hardcodes branch/repo names and conda env; has stray `}` in error msg                           | P3       |
| HSK-18 | juniper-ml    | `util/worktree_close.bash` hardcodes default identifier — not reusable without args                                      | P3       |
| HSK-19 | juniper-ml    | Stale files in repo root: `bla`, `juniper_cascor.log`, `juniper-project-pids.txt`, `JuniperProject.pid`, `.mcp.json.swp` | P3       |
| HSK-20 | juniper-ml    | `claude_interactive.bash:17` `DEBUG="${TRUE}"` hardcoded — forces `--dangerously-skip-permissions`                       | P2       |
| HSK-21 | juniper-ml    | `wake_the_claude.bash:53` stale TODO comment — `debug_log` already writes to stderr                                      | P3       |
| HSK-22 | juniper-ml    | `wake_the_claude.bash:547` TODO — model parameter accepted but never validated                                           | P3       |
| HSK-23 | juniper-ml    | `scripts/juniper-all-ctl:38` cascor port defaults to 8200 (container port) vs host port 8201                             | P3       |
| HSK-24 | cascor-client | Unused constants: `ERROR_PRONE_INITIAL_HIDDEN_UNITS` / `ERROR_PRONE_INITIAL_EPOCH` not yet used                          | P3       |

### Issue Remediations, Section 12

#### HSK-01: 3 Broken Symlinks in canopy `notes/development/`

**Current Code**: Symlinks pointing to deleted juniper-ml files.
**Root Cause**: Source files removed; symlinks not cleaned up.

**Approach A — Remove Broken Symlinks**:

- *Implementation*: `find notes/development/ -xtype l -delete` in canopy repo.
- *Strengths*: 5-minute cleanup.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify symlinks are indeed broken before deletion.

**Recommended**: Approach A — trivial cleanup.

---

#### HSK-02: `src/remote_client/` Directory Still Exists

**Cross-References**: HSK-02 = CLN-CC-01
**Approach A**: See CLN-CC-01 remediation.

---

#### HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate

**Cross-References**: HSK-03 = CLN-CC-02
**Approach A**: See CLN-CC-02 remediation.

---

#### HSK-04: 32 Test Files with Hardcoded `sys.path.append`

**Cross-References**: Related to BUG-CC-06
**Approach A**: See BUG-CC-06 remediation.

---

#### HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0

**Current Code**: AGENTS.md shows version 0.3.0.
**Root Cause**: Document version not updated during release.

**Approach A — Update Version**:

- *Implementation*: Change version in AGENTS.md header to match `pyproject.toml`.
- *Strengths*: 1-minute fix.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add CI check comparing AGENTS.md version with pyproject.toml.

**Recommended**: Approach A — trivial update.

---

#### HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0

**Approach A**: Same as HSK-05 — update version header.
**Recommended**: Approach A.

---

#### HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0

**Approach A**: Update all file headers to current version, or remove file-level version headers (see BUG-CC-04 approach).
**Recommended**: Remove file-level versions in favor of single source in pyproject.toml.

---

#### HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1

**Approach A**: Same as HSK-07 — update or remove file-level version.
**Recommended**: Same approach.

---

#### HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client

**Current Code**: Class attributes never referenced.
**Root Cause**: Mapping tables defined but never used.

~~**Approach A — Delete Dead Code**:~~

<strike>

- *Implementation*: Remove `_STATE_TO_FSM` and `_STATE_TO_PHASE` attributes.
- *Strengths*: Cleaner code.
- *Weaknesses*: None.
- *Risks*: None — zero references.
- *Guardrails*: Grep for any references before deletion.
</strike>

**Approach B --

- *Implementation*: Implement and integrate the `_STATE_TO_FSM` and `_STATE_TO_PHASE` attributes.
- *Strengths*: Complete code implementation.
- *Weaknesses*: Possible Regression Introduction.
- *Risks*: None — zero current references.
- *Guardrails*: Grep for any references and add additional testing to validate expected functionality and to identify any regressions.

**Recommended**: Approach B — These attributes are **NOT** dead code. They are incompletely implemented code and should be fully implementated and integrated.

---

#### HSK-10: `scripts/test.bash` Outdated/Non-Functional

**Current Code**: References removed `nohup.out` file.
**Root Cause**: Script not updated when `nohup.out` was removed.

**Approach A — Update Script**:

- *Implementation*: Update script to use current test infrastructure including `pytest` commands.
- *Strengths*: Working script.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Check if script is referenced anywhere, and add tests if necessary to ensure script functions correctly.

~~**Approach B — Delete Script**:~~

<strike>

- *Implementation*: Delete script because it is superseded by `pytest` commands.
- *Strengths*: Removed script.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Check if script is referenced anywhere.
</strike>

**Recommended**: Approach A — update this script because it is being used.

---

#### HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON

**Current Code**: `scripts/wake_the_claude.bash` — `DEBUG="${TRUE}"` hardcoded.
**Root Cause**: Debug mode left on during development.
**Cross-References**: Related to HSK-20.

**Approach A — Use Environment Variable Default**:

- *Implementation*: Change `DEBUG="${TRUE}"` to `DEBUG="${DEBUG:-false}"`. Respects env var; defaults to off.
- *Strengths*: Configurable; quiet by default.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Document `DEBUG=true` usage in script comments.

**Recommended**: Approach A — one-line fix.

---

#### HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0)

**Current Code**: Dead error check capturing nohup fork status.
**Root Cause**: `$?` after `nohup &` captures the fork status (always 0), not the command result.

**Approach A — Remove Dead Check**:

- *Implementation*: Remove the `NOHUP_STATUS` check since it's always 0.
- *Strengths*: Removes misleading code.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### HSK-13: 169 Hardcoded ThemeColors Remain in canopy

**Current Code**: 169 hardcoded theme color values instead of using ThemeColors class.
**Root Cause**: MED-026 ThemeColors rollout was deferred.

**Approach A — Incremental ThemeColors Migration**:

- *Implementation*: Replace hardcoded colors with `ThemeColors.*` constants in batches of 10-20 per PR.
- *Strengths*: Consistent theming; centralized color management.
- *Weaknesses*: Large effort across 169 locations.
- *Risks*: Visual regressions if colors don't match.
- *Guardrails*: Visual comparison screenshots before/after each batch.

**Recommended**: Approach A — incremental migration by component.

---

#### HSK-14: `resume_session.bash` Contains Hardcoded Session UUID

**Current Code**: One-time-use script committed with hardcoded session UUID.
**Root Cause**: Script was used once and committed without parameterization.

**Approach A — Parameterize Script**:

- *Implementation*: Make the UUID a required parameter (`$1`) for the script.
- *Strengths*: Makes the script reusable.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Approach B — Delete Script**:

- *Implementation*: Delete the script.
- *Strengths*: One time script removed.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A — parameterize for reuse.

---

#### HSK-15: `util/global_text_replace.bash` Is a No-Op

**Current Code**: Search == replace are identical strings; also has misspelled `KIBAB`.
**Root Cause**: Script was used once with specific values; committed without cleanup.

**Approach A — Fix Script for Reuse**:

- *Implementation*: Parameterize search/replace as `$1` and `$2` for the script.
- *Strengths*: Provides a Functional utility.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Fix `KIBAB` → `KEBAB` if keeping.

**Approach B — Delete Script**:

- *Implementation*: Delete the script.
- *Strengths*: Deleting the script removes noise.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None.

**Recommended**: Approach A — parameterize for reuse.

---

#### HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes

**Current Code**: Indiscriminate kill of all Python processes.
**Root Cause**: Emergency utility not scoped to Juniper processes.

**Approach A — Scope to Juniper Processes**:

- *Implementation*: Filter by process name or CWD: `pgrep -f "juniper" | xargs kill`. Add confirmation prompt. Remove `sudo` (user processes only).
- *Strengths*: Safe; targeted; no collateral damage.
- *Weaknesses*: May miss Juniper processes with non-standard names.
- *Risks*: None (safer than current).
- *Guardrails*: Add `--dry-run` mode; list processes before killing.

**Recommended**: Approach A because killing ALL Python processes is dangerous.

---

#### HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names

**Current Code**: Hardcoded branch names and conda env; stray `}` in error message.
**Root Cause**: Script written for one-time use; not parameterized.

**Approach A — Parameterize**:

- *Implementation*: Accept branch, repo, and conda env as parameters. Fix stray `}`.
- *Strengths*: Reusable across repos.
- *Weaknesses*: Must update callers.
- *Risks*: None.
- *Guardrails*: Add `--help` usage output.

**Recommended**: Approach A.

---

#### HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier

**Current Code**: Not reusable without args due to hardcoded defaults.
**Root Cause**: Same as HSK-17 — one-time script not parameterized.

**Approach A — Require Parameters**:

- *Implementation*: Make identifier a required parameter. Error if not provided.
- *Strengths*: Explicit; reusable.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add usage help.

**Recommended**: Approach A.

---

#### HSK-19: Stale Files in Repo Root

**Current Code**: `bla`, `juniper_cascor.log`, `juniper-project-pids.txt`, `JuniperProject.pid`, `.mcp.json.swp`.
**Root Cause**: Development artifacts committed or generated but not gitignored.

**Approach A — Delete and Gitignore**:

- *Implementation*: `git rm` the stale files. Add patterns to `.gitignore`: `*.log`, `*.pid`, `*.swp`, `bla`.
- *Strengths*: Clean repo root; prevents future commits.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify none of the files are used by any script.

**Recommended**: Approach A — trivial cleanup.

---

#### HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded

**Current Code**: Forces `--dangerously-skip-permissions` when DEBUG is on.
**Root Cause**: Debug mode hardcoded on.
**Cross-References**: Related to HSK-11.

**Approach A — Same as HSK-11**:

- *Implementation*: Change to `DEBUG="${DEBUG:-false}"`.
- *Strengths*: Same fix pattern.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### HSK-21: `wake_the_claude.bash:53` Stale TODO Comment

**Current Code**: TODO says `debug_log` should write to stderr — but it already does.
**Root Cause**: TODO not removed after implementation.

**Approach A — Remove TODO**:

- *Implementation*: Delete the stale TODO comment.
- *Strengths*: Removes noise.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None.

**Recommended**: Approach A — 30-second fix.

---

#### HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated

**Current Code**: `--model` parameter accepted but never validated against valid model list.
**Root Cause**: Validation TODO never implemented.

**Approach A — Add Validation**:

- *Implementation*: Validate `--model` against known Claude model names. Error on invalid model.
- *Strengths*: Catches typos; clearer errors.
- *Weaknesses*: Must maintain valid model list.
- *Risks*: New models added before list updated.
- *Guardrails*: Use warning instead of error to avoid blocking new models.

**Recommended**: Approach A with warning (not error) for unknown models.

---

#### HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201

**Current Code**: Port defaults to 8200 but Docker maps cascor to host port 8201.
**Root Cause**: Script uses container port instead of host port.

**Approach A — Default to 8201**:

- *Implementation*: Change default port to 8201 (host port). Add comment explaining container vs host port.
- *Strengths*: Works correctly for local development.
- *Weaknesses*: Wrong inside container (but script runs on host).
- *Risks*: None.
- *Guardrails*: Make port configurable via env var.

**Recommended**: Approach A.

---

#### HSK-24: Unused Constants in cascor-client

**Current Code**: The `ERROR_PRONE_INITIAL_HIDDEN_UNITS` and `ERROR_PRONE_INITIAL_EPOCH` constants are never used.
**Root Cause**: Constants defined but never referenced.

**Approach A — Complete Implementation**:

- *Implementation*: Complete implementation and integration of these constants.
- *Strengths*: Correct code that is not incomplete.
- *Weaknesses*: Possible Regressions.
- *Risks*: None — zero references.
- *Guardrails*: Add additional tests to validate expected functionality and to ensure no regressions are introduced.

~~**Approach B — Delete**:~~

<strike>

- *Implementation*: Remove both constants by commenting these lines out.
- *Strengths*: Cleaner code.
- *Weaknesses*: None.
- *Risks*: None — zero references.
- *Guardrails*: Grep before deletion.
</strike>

**Recommended**: Approach A because this code is currently unfinished.

---

## 13. juniper-deploy Outstanding Items

### Issue Identification Tables, Section 13

#### 13.1 Infrastructure Bugs (Confirmed Still Present)

| ID        | Severity   | Description                                                                                                                      | Evidence                                                    |
|-----------|------------|----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:110` vs `:99`                           |
| DEPLOY-02 | **HIGH**   | AlertManager service missing from docker-compose.yml — `prometheus.yml:34` references `alertmanager:9093` but no service defined | `alertmanager/alertmanager.yml` exists but never used       |
| DEPLOY-03 | **HIGH**   | Prometheus alert/recording rules not mounted — only `prometheus.yml` is volume-mapped, rules files unreachable inside container  | `docker-compose.yml:422` — single file mount, not directory |
| DEPLOY-04 | **MEDIUM** | K8s canopy deployment missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars                 | Helm templates                                              |
| DEPLOY-05 | **MEDIUM** | K8s Redis `auth.enabled: false` — no authentication                                                                              | `values.yaml:306`                                           |
| DEPLOY-06 | **MEDIUM** | K8s Grafana admin password is empty string default                                                                               | `values.yaml:334`                                           |
| DEPLOY-07 | **MEDIUM** | No resource limits on any Docker Compose service                                                                                 | Planned for v0.3.0, not implemented                         |
| DEPLOY-08 | **MEDIUM** | Cascor and canopy ports bound to `0.0.0.0` (externally accessible)                                                               | `docker-compose.yml:128-129,297-298`                        |
| DEPLOY-09 | **MEDIUM** | Worker auth token not via Docker secrets                                                                                         | Worker authentication token passed as plain env var         |
| DEPLOY-10 | **MEDIUM** | Demo variants lack security hardening                                                                                            | Demo compose profiles use relaxed security settings         |
| DEPLOY-11 | **LOW**    | `JUNIPER_DATA_API_KEYS` defaults to empty — auth disabled by default                                                             | Empty default means API key auth is effectively off         |
| DEPLOY-12 | **LOW**    | `wait_for_services.sh` uses hardcoded ports instead of env vars                                                                  | Port numbers hardcoded in health check script               |

#### 13.2 New infrastructure issues (v4)

| ID        | Severity   | Description                                                                                                       | Evidence                                                                                      |
|-----------|------------|-------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| DEPLOY-13 | **HIGH**   | `canopy-dev` network isolation prevents data access — on `frontend` only, but juniper-data on `backend`+`data`    | `docker-compose.yml:391-392` — dev profile is broken, canopy-dev cannot reach juniper-data    |
| DEPLOY-14 | **MEDIUM** | Prometheus rule files not mounted into container (extends DEPLOY-03 with specific fix)                            | Only `prometheus.yml` file is volume-mounted; needs `./prometheus:/etc/prometheus:ro`         |
| DEPLOY-15 | **MEDIUM** | Helm chart default values use `latest` image tags for all 4 services                                              | `values.yaml:27,86,163,227` — non-reproducible deployments                                    |
| DEPLOY-16 | **MEDIUM** | `kube-prometheus-stack.grafana.adminPassword` empty in values.yaml                                                | `values.yaml:334` — if kube-prometheus-stack enabled, Grafana installs with empty password    |
| DEPLOY-17 | **LOW**    | CI compose validation missing worker build context stubs                                                          | `.github/workflows/ci.yml:163-170` — only 3 of 4 Dockerfiles stubbed, 3 of 7 secrets          |
| DEPLOY-18 | **LOW**    | Prometheus container has no healthcheck                                                                           | `docker-compose.yml:410-428` — Grafana may start before Prometheus is ready                   |
| DEPLOY-19 | **LOW**    | Grafana container has no healthcheck                                                                              | `docker-compose.yml:433-453`                                                                  |
| DEPLOY-20 | **LOW**    | Redis has no persistence volume — data lost on restart                                                            | `docker-compose.yml:458-467` — acceptable for cache, should be documented                     |
| DEPLOY-21 | **LOW**    | `canopy-demo` and `canopy-dev` missing Redis dependency                                                           | Full canopy depends on Redis; demo/dev profiles don't include it                              |
| DEPLOY-22 | **LOW**    | `Dockerfile.test` uses unpinned `python:3.12-slim`                                                                | No digest or patch version pin — non-reproducible test builds                                 |
| DEPLOY-23 | **LOW**    | No Helm chart linting in CI                                                                                       | CI validates Docker Compose but doesn't run `helm lint` or `helm template`                    |
| DEPLOY-24 | **HIGH**   | Helm values.yaml missing `JUNIPER_DATA_URL` and `CASCOR_SERVICE_URL` for canopy — K8s canopy can't reach services | `values.yaml` canopy env section — only SERVER, RATE_LIMIT, LOG, SENTRY, METRICS set (v5 new) |
| DEPLOY-25 | **HIGH**   | Helm values.yaml missing `CASCOR_SERVER_URL` for worker — worker fails to start in K8s                            | `values.yaml` worker env — only `CASCOR_HEARTBEAT_INTERVAL` set (v5 new)                      |
| DEPLOY-26 | **MEDIUM** | Helm values.yaml missing `JUNIPER_DATA_URL` for cascor — cascor can't locate data service in K8s                  | `values.yaml` cascor env — `main.py` treats missing `JUNIPER_DATA_URL` as fatal (v5 new)      |

#### 13.3 Unimplemented Roadmap Items (carried from v3)

| ID           | Planned Version | Description                                              | Status                                                             |
|--------------|-----------------|----------------------------------------------------------|--------------------------------------------------------------------|
| DEPLOY-RD-01 | 0.3.0           | Production compose profile with resource limits          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-02 | 0.3.0           | TLS termination via reverse proxy                        | 🔴 NOT DONE                                                        |
| DEPLOY-RD-03 | 0.5.0           | Scheduled weekly integration tests                       | 🔴 NOT DONE                                                        |
| DEPLOY-RD-04 | 0.5.0           | Container image security scanning (Trivy/Grype)          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-05 | —               | Phase 2 systemd service units                            | 🔴 ENTIRELY UNSTARTED — no `systemd/` directory                    |
| DEPLOY-RD-06 | —               | Docker integration CI job (build + start + health check) | 🔴 Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from CI |
| DEPLOY-RD-07 | —               | SOPS multi-key per environment (SOPS-002)                | 🔴 Deferred to Phase 5                                             |
| DEPLOY-RD-08 | —               | Docker secrets + SOPS integration (SOPS-014)             | 🔴 Deferred to Phase 5                                             |

### Issue Remediations, Section 13

#### DEPLOY-01: Docker Secret Name/Path Mismatch

**Current Code**: `docker-compose.yml:110` uses `juniper_data_api_key` (singular); app expects `juniper_data_api_keys` (plural).
**Root Cause**: Naming inconsistency between compose secret name and application config.

**Approach A — Fix Secret Name to Plural**:

- *Implementation*: Change `docker-compose.yml` secret name from `juniper_data_api_key` to `juniper_data_api_keys` to match application expectation.
- *Strengths*: One-line fix; matches app config.
- *Weaknesses*: Must update any deployment scripts referencing old name.
- *Risks*: Existing deployments must update.
- *Guardrails*: Document change in CHANGELOG.

**Recommended**: Approach A — trivial naming fix.

---

#### DEPLOY-02: AlertManager Service Missing from docker-compose.yml

**Current Code**: `prometheus.yml:34` references `alertmanager:9093`; config file exists but no compose service.
**Root Cause**: AlertManager config was created but service definition never added to compose.

**Approach A — Add AlertManager Service**:

- *Implementation*: Add alertmanager service to docker-compose.yml: image `prom/alertmanager`, ports `9093`, volume mount `./alertmanager:/etc/alertmanager`, network `backend`.
- *Strengths*: Complete monitoring stack.
- *Weaknesses*: Additional container resource usage.
- *Risks*: Must configure real receivers (see 5.1).
- *Guardrails*: Add healthcheck; include in monitoring profile.

**Recommended**: Approach A.

---

#### DEPLOY-03/DEPLOY-14: Prometheus Rules Not Mounted

**Current Code**: `docker-compose.yml:422` — only `prometheus.yml` file mounted, not rules directory.
**Root Cause**: Single file mount; rules files exist in `prometheus/` directory but aren't accessible in container.

**Approach A — Mount Entire Directory**:

- *Implementation*: Change from `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro` to `./prometheus:/etc/prometheus:ro`.
- *Strengths*: All config files accessible; includes alert_rules.yml, recording_rules.yml.
- *Weaknesses*: Entire directory mounted (acceptable for config).
- *Risks*: None.
- *Guardrails*: Verify `prometheus.yml` references use correct paths after mount change.

**Recommended**: Approach A — one-line fix.

---

#### DEPLOY-04: K8s Canopy Missing Service URL Env Vars

**Approach A — Add to Helm Values**:

- *Implementation*: Add `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` to canopy deployment env in `values.yaml`.
- *Strengths*: Canopy can reach dependent services in K8s.
- *Weaknesses*: None.
- *Risks*: Must use correct K8s service DNS names.
- *Guardrails*: Use Helm templating: `http://{{ .Release.Name }}-data:8100`.

**Recommended**: Approach A.

---

#### DEPLOY-05 through DEPLOY-12, DEPLOY-15 through DEPLOY-23: Infrastructure Items

Brief remediations for remaining deploy items:

- **DEPLOY-05**: Add `auth.enabled: true` and `auth.password` to Redis values.yaml.
- **DEPLOY-06**: Set non-empty Grafana admin password via Helm values secret.
- **DEPLOY-07**: Add `deploy.resources.limits` to each compose service.
- **DEPLOY-08**: Bind to `127.0.0.1` instead of `0.0.0.0` for local-only services.
- **DEPLOY-09**: Use Docker secrets for worker auth token (same as compose secrets).
- **DEPLOY-10**: Add security hardening to demo profiles (rate limiting, auth).
- **DEPLOY-11**: Set non-empty `JUNIPER_DATA_API_KEYS` default; require explicit disable.
- **DEPLOY-12**: Use env vars for ports in `wait_for_services.sh`.
- **DEPLOY-13**: Add `canopy-dev` to both `frontend` and `backend` networks.
- **DEPLOY-15**: Pin image tags to specific versions (e.g., `0.4.0`) instead of `latest`.
- **DEPLOY-16**: Same as DEPLOY-06 for kube-prometheus-stack.
- **DEPLOY-17**: Stub all 4 Dockerfiles and 7 secrets in CI validation.
- **DEPLOY-18/19**: Add healthchecks for Prometheus and Grafana containers.
- **DEPLOY-20**: Document Redis persistence limitation; acceptable for cache.
- **DEPLOY-21**: Add Redis dependency to demo/dev profiles.
- **DEPLOY-22**: Pin `python:3.12-slim` to digest or patch version.
- **DEPLOY-23**: Add `helm lint` and `helm template` to CI.

#### DEPLOY-24/25/26: Helm Missing Critical Env Vars

**Approach A — Add Missing Env Vars**:

- *Implementation*: Add `JUNIPER_DATA_URL` to canopy and cascor sections. Add `CASCOR_SERVER_URL` to worker section of `values.yaml`.
- *Strengths*: Services can discover each other in K8s.
- *Weaknesses*: None.
- *Risks*: Must use correct K8s service DNS names.
- *Guardrails*: Use Helm templating for dynamic service discovery.

**Recommended**: Approach A — critical for K8s deployments.

---

#### DEPLOY-RD-01 through DEPLOY-RD-08: Roadmap Items

All roadmap items are 🔴 NOT DONE. Brief approaches:

- **DEPLOY-RD-01**: Create `docker-compose.production.yml` overlay with resource limits, health checks, restart policies.
- **DEPLOY-RD-02**: Add nginx/traefik reverse proxy service for TLS termination.
- **DEPLOY-RD-03**: Add GitHub Actions scheduled workflow for weekly integration tests.
- **DEPLOY-RD-04**: Add Trivy/Grype container scanning to CI.
- **DEPLOY-RD-05**: Create `systemd/` directory with unit files for all 4 services.
- **DEPLOY-RD-06**: Implement Docker integration CI: build → start → health check → teardown.
- **DEPLOY-RD-07/08**: SOPS multi-key and Docker secrets integration — deferred to Phase 5.

---

## 14. juniper-data Outstanding Items

### Issue Identification Tables, Section 14

#### 14.1 Security Issues (Confirmed Still Present)

| ID        | Severity   | File                        | Description                                                                                                                                                         |
|-----------|------------|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can escape storage directory. |
| JD-SEC-02 | **MEDIUM** | `api/security.py:59`        | API key comparison not constant-time — timing side-channel (SEC-01 from prior audit, still present)                                                                 |
| JD-SEC-03 | **MEDIUM** | `api/security.py:116`       | Rate limiter memory unbounded — no eviction/TTL (SEC-02 from prior audit, still present)                                                                            |

#### 14.2 Performance Issues

| ID         | Severity   | File                                | Description                                                                                                                              |
|------------|------------|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| JD-PERF-01 | **HIGH**   | `api/routes/datasets.py:107`        | Sync `generator.generate()` blocks async event loop. Needs `asyncio.to_thread()`.                                                        |
| JD-PERF-02 | **MEDIUM** | `storage/base.py:261,317`           | `filter_datasets`/`get_stats` load ALL metadata on every call — O(n) disk reads.                                                         |
| JD-PERF-03 | **MEDIUM** | `storage/base.py:169`               | `list_versions` loads all metadata then filters in Python. No DB-level filtering for Postgres.                                           |
| JD-PERF-04 | **MEDIUM** | `storage/postgres_store.py:125-127` | No connection pooling — `psycopg2.connect()` called per operation. Confirmed: `close()` is a no-op for "connection-per-request pattern". |
| JD-PERF-05 | **MEDIUM** | `api/routes/health.py:57`           | Readiness probe does filesystem glob on every call — `len(list(storage_path.glob("*.npz")))` is O(n) per probe (v4 new)                  |

#### 14.3 Deferred Roadmap Items

| ID     | Description                             | Status      |
|--------|-----------------------------------------|-------------|
| RD-008 | Fix SIM117 test code violations         | 🔵 DEFERRED |
| RD-015 | IPC Architecture (ZeroMQ/shared-memory) | 🔵 DEFERRED |
| RD-016 | GPU Acceleration for large datasets     | 🔵 DEFERRED |
| RD-017 | Continuous Profiling infrastructure     | 🔵 DEFERRED |

### Issue Remediations, Section 14

#### 14.1 — Security Issues (juniper-data)

#### JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths

**Current Code**: `storage/local_fs.py:52-58` — `dataset_id` concatenated directly into filesystem paths via `self._base_path / f"{dataset_id}{META_FILE_SUFFIX}"`.
**Root Cause**: User-supplied `dataset_id` not sanitized; `../` sequences can escape storage directory.

**Approach A — Input Validation**:

- *Implementation*: Add `re.fullmatch(r"[a-zA-Z0-9_-]+", dataset_id)` validation in `_meta_path()` and `_npz_path()` (or at API layer). Reject with 400 if invalid.
- *Strengths*: Defense-in-depth at storage layer; blocks all traversal attempts.
- *Weaknesses*: Must verify dataset ID format used by `dataset_id.py` generator.
- *Risks*: Existing datasets with non-conforming IDs would become inaccessible.
- *Guardrails*: Also add `resolved_path.resolve().is_relative_to(self._base_path)` check as secondary defense.

**Approach B — Path Resolution Check**:

- *Implementation*: After constructing path, verify `path.resolve().is_relative_to(self._base_path)`.
- *Strengths*: Catches traversal regardless of character set; defense-in-depth.
- *Weaknesses*: Check is after path construction (less ideal than input validation).
- *Risks*: None.
- *Guardrails*: Combine with Approach A for layered defense.

**Recommended**: Both Approach A and B together — validate input AND verify resolved path.

---

#### JD-SEC-02: API Key Comparison Not Constant-Time (data)

**Current Code**: `api/security.py:59` — `return api_key in self._api_keys`.
**Root Cause**: Same as SEC-01 — set membership test is not constant-time.
**Cross-References**: JD-SEC-02 = SEC-01

**Approach A**: See SEC-01 remediation (hmac.compare_digest loop).
**Recommended**: See SEC-01.

---

#### JD-SEC-03: Rate Limiter Memory Unbounded (data)

**Current Code**: `api/security.py:116` — no eviction/TTL on `_counters`.
**Root Cause**: Same as SEC-02 — no entry eviction.
**Cross-References**: JD-SEC-03 = SEC-02

**Approach A**: See SEC-02 remediation (TTLCache or periodic cleanup).
**Recommended**: See SEC-02.

---

#### 14.2-14.3 — Performance and Roadmap Items (juniper-data)

#### JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

**Cross-References**: JD-PERF-01 = SEC-04 = CONC-04
**Approach A**: See SEC-04/CONC-04 remediation (asyncio.to_thread).

---

#### JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata

**Current Code**: `storage/base.py:261,317` — O(n) disk reads on every call.
**Root Cause**: No indexing or caching of metadata.

**Approach A — In-Memory Metadata Cache**:

- *Implementation*: Maintain in-memory metadata index updated on save/delete. Filter and stats operate on cached data.
- *Strengths*: O(1) queries after initial load.
- *Weaknesses*: Memory usage proportional to dataset count.
- *Risks*: Cache invalidation on external file changes.
- *Guardrails*: Periodic cache refresh; cache size limit.

**Recommended**: Approach A.

---

#### JD-PERF-03: `list_versions` Loads All Metadata

**Approach A — DB-Level Filtering for Postgres**:

- *Implementation*: Override `list_versions()` in `PostgresStore` with SQL query filtering. Keep filesystem implementation as-is for LocalFS.
- *Strengths*: Efficient for Postgres; no regression for LocalFS.
- *Weaknesses*: Dual implementation.
- *Risks*: None.
- *Guardrails*: Test both storage backends.

**Recommended**: Approach A.

---

#### JD-PERF-04: No Connection Pooling for Postgres

**Current Code**: `psycopg2.connect()` per operation; `close()` is a no-op.
**Root Cause**: Connection-per-request pattern without pooling.

**Approach A — Connection Pool**:

- *Implementation*: Use `psycopg2.pool.SimpleConnectionPool` or `psycopg_pool.ConnectionPool` (psycopg3). Set min/max connections.
- *Strengths*: Reuse connections; reduced latency.
- *Weaknesses*: Pool management lifecycle.
- *Risks*: Must handle pool exhaustion.
- *Guardrails*: Max pool size configurable via Settings; timeout on pool acquisition.

**Recommended**: Approach A.

---

#### JD-PERF-05: Readiness Probe Filesystem Glob

**Cross-References**: JD-PERF-05 = PERF-JD-01
**Approach A**: See PERF-JD-01 remediation.

---

#### RD-008/RD-015/RD-016/RD-017: Deferred Roadmap Items

All 🔵 DEFERRED. No immediate remediation required.

---

## 15. Client Library Outstanding Items

### Issue Identification Tables, Section 15

#### 15.1 juniper-cascor-client

| ID    | Severity   | Description                                                                                                 | Status             |
|-------|------------|-------------------------------------------------------------------------------------------------------------|--------------------|
| CC-01 | **MEDIUM** | `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out               | 🔴 Open            |
| CC-02 | **MEDIUM** | 503 not in `RETRYABLE_STATUS_CODES`                                                                         | 🔴 Open (XREPO-02) |
| CC-03 | **MEDIUM** | No `FakeCascorControlStream`                                                                                | 🔴 Open (XREPO-03) |
| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                              | 🔴 Open            |
| CC-05 | **LOW**    | CI doesn't test Python 3.14 (classified in pyproject.toml)                                                  | 🔴 Open            |
| CC-06 | **MEDIUM** | `command()` never sends `type` field — wire protocol inconsistency with `set_params()`                      | 🔴 Open (XREPO-07) |
| CC-07 | **MEDIUM** | NpzFile resource leak in data-client — `np.load(BytesIO())` never closed                                    | 🔴 Open            |
| CC-08 | **LOW**    | WebSocket auto-reconnection not implemented — long training runs silently lose WS                           | 🔴 Open            |
| CC-09 | **MEDIUM** | `CascorTrainingStream.stream()` no `json.JSONDecodeError` handling — malformed JSON crashes stream          | 🔴 Open (v4 new)   |
| CC-10 | **MEDIUM** | `CascorControlStream.connect()` no `json.JSONDecodeError` handling — leaks untyped error                    | 🔴 Open (v4 new)   |
| CC-11 | **MEDIUM** | `CascorControlStream.command()` direct path — no `json.JSONDecodeError` handling                            | 🔴 Open (v4 new)   |
| CC-12 | **MEDIUM** | `CascorControlStream._recv_loop()` no `json.JSONDecodeError` — single bad message fails ALL pending futures | 🔴 Open (v4 new)   |
| CC-13 | **LOW**    | `_recv_loop` silently drops non-correlated server messages (state changes, errors, heartbeats)              | 🔴 Open (v4 new)   |
| CC-14 | **LOW**    | `_handle_response()` calls `response.json()` unconditionally — fails on non-JSON 2xx bodies                 | 🔴 Open (v4 new)   |
| CC-15 | **MEDIUM** | No TLS/SSL configuration support on WS streams (unlike worker which has full mTLS support)                  | 🔴 Open (v4 new)   |
| CC-16 | **LOW**    | `FakeCascorClient.wait_for_ready()` returns `True` immediately — no timeout testing possible                | 🔴 Open (v4 new)   |
| CC-17 | **LOW**    | `FakeCascorClient.wait_for_ready()` missing `self._lock` — thread safety gap                                | 🔴 Open (v4 new)   |

#### 15.2 juniper-data-client

| ID    | Severity     | Description                                                                                    | Status              |
|-------|--------------|------------------------------------------------------------------------------------------------|---------------------|
| DC-01 | **CRITICAL** | `GENERATOR_CIRCLE = "circle"` — server has `"circles"` (plural)                                | 🔴 Open (XREPO-01)  |
| DC-02 | **CRITICAL** | `GENERATOR_MOON = "moon"` — server has no moon generator                                       | 🔴 Open (XREPO-01b) |
| DC-03 | **MEDIUM**   | Missing constants for 5 server generators                                                      | 🔴 Open (XREPO-01c) |
| DC-04 | **MEDIUM**   | `FakeDataClient` masks generator name bugs — accepts invalid names                             | 🔴 Open             |
| DC-05 | **MEDIUM**   | `FakeDataClient` missing lifecycle methods (`filter_datasets`, `get_stats`, `cleanup_expired`) | 🔴 Open (v4 new)    |

#### 15.3 juniper-cascor-worker

| ID    | Severity   | Description                                                                                          | Status                                                |
|-------|------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker      | ⚠️ Partially fixed — `_parse_json()` catches but      |
|       |            |                                                                                                      | -- `receive_json()` at `ws_connection.py:184` doesn't |
| CW-02 | **MEDIUM** | `requirements.lock` includes CUDA packages (~2-4GB image bloat)                                      | 🔴 Open                                               |
| CW-03 | **LOW**    | No integration tests (marker defined, zero tests use it)                                             | 🔴 Open                                               |
| CW-04 | **MEDIUM** | Timeout error sends `candidate_uuid: ""` instead of actual UUID                                      | 🔴 Open                                               |
| CW-05 | **MEDIUM** | Dynamic import `from candidate_unit.candidate_unit import CandidateUnit` — fragile, no version check | 🔴 Open                                               |
| CW-06 | **MEDIUM** | `receive_json()` in `ws_connection.py:184` — no `json.JSONDecodeError` catch (registration crash)    | 🔴 Open (v4 new)                                      |
| CW-07 | **MEDIUM** | No validation of `tensor_manifest` keys against received binary frames — deadlock risk               | 🔴 Open (v4 new)                                      |
| CW-08 | **MEDIUM** | `task_executor.py:12` top-level `import torch` — first-task latency from deferred torch import       | 🔴 Open (v4 new)                                      |

### Issue Remediations, Section 15

#### Issue Remediations, Section 15 — juniper-cascor-client

#### CC-01: `_recv_loop` Catches Bare `Exception`

**Current Code**: `_recv_loop` catches bare `Exception`, swallowing programming errors; pending futures time out.
**Root Cause**: Overly broad exception handling intended for network errors also catches bugs.

**Approach A — Narrow Exception Types**:

- *Implementation*: Catch `(websockets.ConnectionClosed, json.JSONDecodeError, OSError)` instead of bare `Exception`. Let `TypeError`, `AttributeError`, etc. propagate to the future.
- *Strengths*: Bugs surface immediately via future exceptions; network errors handled gracefully.
- *Weaknesses*: Must enumerate all expected network error types.
- *Risks*: Unexpected network errors may crash the recv loop.
- *Guardrails*: Add `except Exception as e: logger.exception("Unexpected error"); raise` as last handler.

**Recommended**: Approach A because bare Exception catches hide programming errors.

---

#### CC-04: `set_params()` Method Not Documented in AGENTS.md

**Current Code**: Method exists but not documented in architecture section.
**Root Cause**: Documentation not updated when method was added.

**Approach A — Update AGENTS.md**:

- *Implementation*: Add `set_params()` to the WebSocket client methods section of cascor-client's AGENTS.md.
- *Strengths*: Complete documentation; trivial.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A — documentation update.

---

#### CC-05: CI Doesn't Test Python 3.14

**Current Code**: pyproject.toml classifies 3.14 but CI matrix doesn't include it.
**Root Cause**: CI matrix not updated when 3.14 classifier was added.
**Cross-References**: CC-05 = CI-01

**Approach A**: See CI-01 remediation (add 3.14 to CI matrix).
**Recommended**: See CI-01.

---

#### CC-06: `command()` Never Sends `type` Field

**Current Code**: See XREPO-07.
**Cross-References**: CC-06 = XREPO-07

**Approach A**: See XREPO-07 remediation.
**Recommended**: See XREPO-07.

---

#### CC-07: NpzFile Resource Leak in data-client

**Current Code**: `np.load(BytesIO())` returns NpzFile that is never closed.
**Root Cause**: `np.load()` returns a file-like object that holds resources; not closing it leaks file handles.

**Approach A — Context Manager**:

- *Implementation*: Use `with np.load(BytesIO(data)) as npz:` to ensure cleanup, or add explicit `npz.close()` in a `finally` block.
- *Strengths*: Proper resource management; prevents file handle leaks.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test verifying no resource warnings.

**Recommended**: Approach A because resource leaks accumulate in long-running processes.

---

#### CC-08: WebSocket Auto-Reconnection Not Implemented

**Current Code**: WS connection is one-shot; no reconnection on disconnect.
**Root Cause**: Auto-reconnection was not implemented in the initial WS client.

**Approach A — Exponential Backoff Reconnection**:

- *Implementation*: Add `auto_reconnect: bool = True` and `max_reconnect_attempts: int = 10` to stream constructors. On `ConnectionClosed`, attempt reconnection with exponential backoff (1s, 2s, 4s, ..., max 60s).
- *Strengths*: Resilient to transient disconnections; configurable.
- *Weaknesses*: Complex state management during reconnection.
- *Risks*: Must handle message replay on reconnect (see GAP-WS-13).
- *Guardrails*: Emit `on_reconnect` callback; cap attempts; log each attempt.

**Recommended**: Approach A because long training runs should survive transient network issues.

---

#### CC-09/CC-10/CC-11/CC-12: JSONDecodeError Not Handled in WS Code (4 locations)

**Current Code**: 4 locations in cascor-client WS code where `json.loads()` or `response.json()` can throw unhandled `JSONDecodeError`.
**Root Cause**: Malformed server messages not handled — single bad message crashes entire stream/connection.

**Approach A — Centralized JSON Parsing**:

- *Implementation*: Add `_parse_ws_message(raw: str) -> dict` helper that wraps `json.loads()` with `try/except json.JSONDecodeError`. Log malformed messages at WARNING. Return `None` or raise typed `MalformedMessageError`.
- *Strengths*: DRY; consistent handling across all 4 locations; single bad message doesn't crash stream.
- *Weaknesses*: Must decide how to handle `None`/error in each caller.
- *Risks*: Silently dropping messages could mask protocol issues.
- *Guardrails*: Counter for malformed messages; alert if rate exceeds threshold.

**Recommended**: Approach A because centralized parsing prevents 4 identical try/except blocks.

---

#### CC-13: `_recv_loop` Silently Drops Non-Correlated Server Messages

**Current Code**: Messages without correlation IDs (state changes, errors, heartbeats) are silently discarded.
**Root Cause**: `_recv_loop` only matches messages to pending futures by correlation ID; other messages have no handler.

**Approach A — Event Callback System**:

- *Implementation*: Add `on_event: Optional[Callable[[dict], None]]` callback. Non-correlated messages are passed to this callback instead of being dropped.
- *Strengths*: Enables consumers to handle state changes, errors, heartbeats.
- *Weaknesses*: Callback must be thread-safe if recv loop runs in separate thread.
- *Risks*: Callback exceptions could crash recv loop.
- *Guardrails*: Wrap callback in try/except; log errors but don't crash loop.

**Recommended**: Approach A because silently dropped messages hide important server events.

---

#### CC-14: `_handle_response()` Calls `response.json()` Unconditionally

**Current Code**: Fails on non-JSON 2xx bodies (e.g., 204 No Content).
**Root Cause**: Assumes all successful responses have JSON bodies.

**Approach A — Check Content-Type**:

- *Implementation*: Check `response.headers.get("content-type", "")` before calling `response.json()`. For non-JSON responses or 204, return `None` or the raw text.
- *Strengths*: Handles all response types correctly.
- *Weaknesses*: Minor additional logic.
- *Risks*: None.
- *Guardrails*: Add test with 204 response.

**Recommended**: Approach A because not all 2xx responses have JSON bodies.

---

#### CC-15: No TLS/SSL Configuration Support on WS Streams

**Current Code**: WS streams use plain `ws://`; worker has full mTLS support.
**Root Cause**: TLS not implemented in cascor-client WS streams.

**Approach A — Add SSL Context Parameter**:

- *Implementation*: Add `ssl: Optional[ssl.SSLContext] = None` parameter to stream constructors. Pass to `websockets.connect(uri, ssl=ssl_context)`.
- *Strengths*: Enables encrypted WS connections; consistent with worker.
- *Weaknesses*: Must manage SSL certificates.
- *Risks*: Certificate validation may reject self-signed certs.
- *Guardrails*: Default to `None` (no TLS) for backward compat; document TLS setup.

**Recommended**: Approach A because TLS support is essential for production deployments.

---

#### CC-16: `FakeCascorClient.wait_for_ready()` Returns True Immediately

**Current Code**: `wait_for_ready()` returns `True` without delay — no timeout testing possible.
**Root Cause**: Fake doesn't simulate server readiness delay.

**Approach A — Add Configurable Delay**:

- *Implementation*: Add `ready_delay: float = 0.0` to FakeClient constructor. `wait_for_ready()` sleeps for `ready_delay` before returning. Add `is_ready: bool = True` flag for simulating unavailable server.
- *Strengths*: Enables timeout testing; configurable behavior.
- *Weaknesses*: Minor complexity increase.
- *Risks*: None.
- *Guardrails*: Default to instant (backward compat).

**Recommended**: Approach A because fakes should support error/edge-case testing.

---

#### CC-17: `FakeCascorClient.wait_for_ready()` Missing `self._lock`

**Current Code**: `wait_for_ready()` accesses shared state without lock.
**Root Cause**: Lock not used consistently in fake implementation.

**Approach A — Add Lock**:

- *Implementation*: Add `with self._lock:` around `wait_for_ready()` state access.
- *Strengths*: Thread-safe; consistent with other locked methods.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Review all FakeClient methods for lock consistency.

**Recommended**: Approach A — trivial fix.

---

#### Issue Remediations, Section 15 — juniper-data-client

#### DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles"

**Cross-References**: DC-01 = XREPO-01
**Approach A**: See XREPO-01 remediation.

---

#### DC-02: GENERATOR_MOON = "moon" — No Server Generator

**Cross-References**: DC-02 = XREPO-01b
**Approach A**: See XREPO-01b remediation.

---

#### DC-03: Missing Constants for 5 Server Generators

**Cross-References**: DC-03 = XREPO-01c
**Approach A**: See XREPO-01c remediation.

---

#### DC-04: `FakeDataClient` Masks Generator Name Bugs

**Current Code**: Fake accepts any generator name, including invalid ones.
**Root Cause**: Fake doesn't validate generator names against known valid values.

**Approach A — Validate Against Known Generators**:

- *Implementation*: Add generator name validation in `FakeDataClient.create_dataset()` that rejects names not in `VALID_GENERATORS` set.
- *Strengths*: Tests catch generator name bugs; matches real server behavior.
- *Weaknesses*: Must maintain valid generators list.
- *Risks*: None.
- *Guardrails*: Import valid generators from constants or define a shared list.

**Recommended**: Approach A because fakes that accept invalid input hide bugs.

---

#### DC-05: `FakeDataClient` Missing Lifecycle Methods

**Current Code**: `FakeDataClient` missing `filter_datasets`, `get_stats`, `cleanup_expired`.
**Root Cause**: Fake not updated when server API was extended.

**Approach A — Add Missing Methods**:

- *Implementation*: Implement `filter_datasets()`, `get_stats()`, `cleanup_expired()` in `FakeDataClient` with in-memory filtering logic.
- *Strengths*: Enables testing of all client methods.
- *Weaknesses*: In-memory implementation may not match server semantics exactly.
- *Risks*: Divergence between fake and real behavior.
- *Guardrails*: Add conformance tests; document any behavioral differences.

**Recommended**: Approach A because missing fake methods prevent testing.

---

#### Issue Remediations, Section 15 — juniper-cascor-worker

#### CW-01: `receive_json()` Doesn't Catch JSONDecodeError

**Current Code**: `ws_connection.py:184` — `receive_json()` doesn't handle malformed server messages.
**Root Cause**: JSON parsing assumed to always succeed.

**Approach A — Add JSONDecodeError Handling**:

- *Implementation*: Wrap `json.loads()` in try/except, log malformed message at WARNING, raise typed `ProtocolError`.
- *Strengths*: Prevents crash on single bad message.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test with malformed JSON.

**Recommended**: Approach A — straightforward defensive coding.

---

#### CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat)

**Current Code**: Lock file includes CUDA/GPU packages in base requirements.
**Root Cause**: Lock file generated on a system with CUDA installed; CUDA packages included in resolved dependencies.

**Approach A — Separate CPU/GPU Requirements**:

- *Implementation*: Create `requirements-cpu.lock` and `requirements-gpu.lock`. Use `--extra-index-url` for PyTorch CPU-only builds. Default Dockerfile uses CPU lock.
- *Strengths*: Slim CPU images (~500MB vs ~4GB); GPU support available via separate build.
- *Weaknesses*: Two lock files to maintain.
- *Risks*: Must ensure CPU and GPU dependencies don't conflict.
- *Guardrails*: CI builds and tests both CPU and GPU images.

**Recommended**: Approach A because 2-4GB image bloat impacts deployment time and cost.

---

#### CW-03: No Integration Tests

**Current Code**: `integration` marker defined but zero tests use it.
**Root Cause**: Integration tests were planned but never written.

**Approach A — Add Basic Integration Tests**:

- *Implementation*: Write 3-5 integration tests: worker registration, task receipt, binary frame decoding, result submission, graceful disconnect. Use `requires_server` marker.
- *Strengths*: Validates end-to-end worker flow; catches protocol regressions.
- *Weaknesses*: Requires running cascor server in CI (or use fixtures).
- *Risks*: CI complexity.
- *Guardrails*: Run separately from unit tests; skip if server not available.

**Recommended**: Approach A because zero integration tests is a significant gap.

---

#### CW-04: Timeout Error Sends `candidate_uuid: ""` Instead of Actual UUID

**Current Code**: Error response on timeout sends empty string for `candidate_uuid`.
**Root Cause**: UUID not captured/passed to error handling path.

**Approach A — Pass UUID to Error Handler**:

- *Implementation*: Capture `candidate_uuid` at task start. Include in timeout error response.
- *Strengths*: Server can correlate timeout errors with specific candidates.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test verifying UUID in error response.

**Recommended**: Approach A because empty UUID prevents error correlation.

---

#### CW-05: Dynamic Import `from candidate_unit.candidate_unit import CandidateUnit`

**Current Code**: `task_executor.py` uses dynamic import without version check.
**Root Cause**: CandidateUnit is imported from cascor's source tree via sys.path manipulation.

**Approach A — Package Dependency**:

- *Implementation*: Publish `juniper-cascor-core` package with shared types (CandidateUnit). Worker depends on it via pyproject.toml.
- *Strengths*: Proper dependency management; version pinning; no sys.path.
- *Weaknesses*: New package to maintain.
- *Risks*: Must extract CandidateUnit without breaking cascor.
- *Guardrails*: Version pin to compatible range; CI tests with latest cascor-core.

**Approach B — Copy and Vendoring**:

- *Implementation*: Vendor (copy) `candidate_unit.py` into worker package. Add version comment.
- *Strengths*: Simple; no new package.
- *Weaknesses*: Manual sync required; drift risk.
- *Risks*: Vendored copy may become stale.
- *Guardrails*: Add CI check comparing vendored file hash with source.

**Recommended**: Approach A for clean architecture; Approach B as interim solution.

---

#### CW-06: `receive_json()` in Registration Path — No JSONDecodeError Catch

**Current Code**: `ws_connection.py:184` — registration response parsing.
**Root Cause**: Same as CW-01 but in registration-specific path.

**Approach A**: Same fix as CW-01 applies.
**Recommended**: See CW-01.

---

#### CW-07: No Validation of `tensor_manifest` Keys Against Received Binary Frames

**Current Code**: Worker expects binary frames matching manifest keys but doesn't validate alignment.
**Root Cause**: No cross-check between manifest keys and received frame identifiers.

**Approach A — Manifest Validation**:

- *Implementation*: After receiving all binary frames, verify that keys match `tensor_manifest`. Raise `ProtocolError` if mismatch. Add timeout for incomplete manifests.
- *Strengths*: Prevents deadlock on missing frames; catches protocol violations.
- *Weaknesses*: Minor overhead.
- *Risks*: None.
- *Guardrails*: Timeout at 2x expected frame count duration.

**Recommended**: Approach A because unvalidated manifests cause silent deadlocks.

---

#### CW-08: Top-Level `import torch` — First-Task Latency

**Current Code**: `task_executor.py:12` — `import torch` at module level.
**Root Cause**: Torch import takes 2-5 seconds; imported at module level even before first task.

**Approach A — Lazy Import**:

- *Implementation*: Move `import torch` inside `execute_task()` method. Use `functools.lru_cache` on a helper to avoid repeat imports.
- *Strengths*: Worker starts faster; torch loaded only when needed.
- *Weaknesses*: First task has import latency (but this is already the case).
- *Risks*: None.
- *Guardrails*: Pre-import torch in a background thread during idle time.

**Recommended**: Approach A because module-level heavy imports slow startup.

---

---

## 16. Performance Issues (v4 new section)

Issues identified through deep code analysis that impact runtime performance.

### Issue Identification Tables, Section 16

#### 16.1 juniper-canopy

| ID         | Severity   | Description                                                        | File(s)                                                              | Evidence                                                                  |
|------------|------------|--------------------------------------------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------------|
| PERF-CN-01 | **MEDIUM** | 33 of 50 Dash callbacks missing `prevent_initial_call=True`        | `metrics_panel.py` (14), `candidate_metrics_panel.py` (7), 12 others | 33 unnecessary callback executions on every dashboard load                |
| PERF-CN-02 | **LOW**    | f-string logging in hot paths (71 occurrences in demo_mode + main) | `src/demo_mode.py` (20), `src/main.py` (51)                          | String interpolation evaluated even when log level suppresses the message |

#### 16.2 juniper-cascor

| ID         | Severity   | Description                                                             | File(s)                                | Evidence                                                                                                  |
|------------|------------|-------------------------------------------------------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------|
| PERF-CC-01 | **MEDIUM** | Blocking `torch.save`/`torch.load` in async-adjacent code paths         | `src/api/lifecycle/manager.py:870,894` | Synchronous HDF5 I/O called from async REST handlers — blocks all concurrent requests during snapshot ops |
| PERF-CC-02 | **LOW**    | `replay_since` scans entire replay buffer O(n) on every resume request  | `src/api/websocket/manager.py:248`     | Linear scan of 1024-entry deque; binary search would be O(log n)                                          |
| PERF-CC-03 | **LOW**    | `_broadcast_training_state` uses `hasattr` check instead of proper init | `src/api/lifecycle/manager.py:153`     | `hasattr(self, "_last_state_broadcast_time")` on every call                                               |

#### 16.3 juniper-data

| ID         | Severity   | Description                                                  | File(s)                   | Evidence                                                               |
|------------|------------|--------------------------------------------------------------|---------------------------|------------------------------------------------------------------------|
| PERF-JD-01 | **MEDIUM** | Readiness probe does filesystem glob on every call           | `api/routes/health.py:57` | `len(list(storage_path.glob("*.npz")))` is O(n) per probe              |
| PERF-JD-02 | **MEDIUM** | High-cardinality Prometheus labels from parameterized routes | `api/observability.py:98` | `endpoint = request.url.path` with dataset IDs — unbounded cardinality |

### Issue Remediations, Section 16

#### PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`

**Current Code**: `metrics_panel.py` (14), `candidate_metrics_panel.py` (7), 12 others — 33 unnecessary initial callback executions.
**Root Cause**: Default `prevent_initial_call=False` causes every callback to fire on page load.

**Approach A — Add `prevent_initial_call=True`**:

- *Implementation*: Add `prevent_initial_call=True` to all 33 callback decorators where initial call is not needed.
- *Strengths*: Faster page load; reduced initial CPU; simple decorator change.
- *Weaknesses*: Must verify each callback doesn't need initial execution.
- *Risks*: Some callbacks may depend on initial call for setup.
- *Guardrails*: Test each callback group after change; revert any that break.

**Recommended**: Approach A because 33 unnecessary callback fires is measurable performance waste.

---

#### PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences)

**Current Code**: `demo_mode.py` (20), `main.py` (51) — string interpolation evaluated even when log level suppresses.
**Root Cause**: Using f-strings instead of lazy `%s` formatting in log calls.

**Approach A — Use Lazy Formatting**:

- *Implementation*: Change `logger.debug(f"Value: {val}")` to `logger.debug("Value: %s", val)`.
- *Strengths*: No interpolation when log level is above DEBUG; standard practice.
- *Weaknesses*: 71 locations to change.
- *Risks*: None.
- *Guardrails*: Add flake8 plugin to catch future f-string logging.

**Recommended**: Approach A for hot paths; lower priority for cold paths.

---

#### PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths

**Current Code**: `src/api/lifecycle/manager.py:870,894` — synchronous HDF5 I/O from async REST handlers.
**Root Cause**: Snapshot operations block the event loop during I/O.

**Approach A — asyncio.to_thread Wrapper**:

- *Implementation*: Wrap `torch.save()` and `torch.load()` calls in `await asyncio.to_thread(...)`.
- *Strengths*: Non-blocking; minimal code change.
- *Weaknesses*: Thread pool limits concurrent snapshot operations.
- *Risks*: Thread-safety of torch save/load must be verified.
- *Guardrails*: Add timeout for snapshot operations.

**Recommended**: Approach A because blocking I/O in async handlers impacts all concurrent requests.

---

#### PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n)

**Current Code**: `src/api/websocket/manager.py:248` — linear scan of 1024-entry deque.
**Root Cause**: No index on replay buffer by sequence number.

**Approach A — Binary Search**:

- *Implementation*: Since sequence numbers are monotonically increasing, use `bisect.bisect_left` on the deque.
- *Strengths*: O(log n) instead of O(n); simple.
- *Weaknesses*: `bisect` doesn't directly support deque (convert to list or use custom key).
- *Risks*: Minimal — 1024 entries is small even for O(n).
- *Guardrails*: Benchmark before/after to verify improvement.

**Recommended**: Approach A as a nice-to-have; low priority since N ≤ 1024.

---

#### PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check

**Current Code**: `src/api/lifecycle/manager.py:153` — `hasattr(self, "_last_state_broadcast_time")` on every call.
**Root Cause**: Attribute not initialized in `__init__`; `hasattr` used as workaround.

**Approach A — Initialize in `__init__`**:

- *Implementation*: Add `self._last_state_broadcast_time = 0.0` to `__init__`. Remove `hasattr` check.
- *Strengths*: Faster; cleaner; proper initialization.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Covered by CONC-02 fix.

**Recommended**: Approach A — trivial fix, covered by CONC-02 remediation.

---

#### PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call

**Current Code**: `api/routes/health.py:57` — `len(list(storage_path.glob("*.npz")))` per probe.
**Root Cause**: Counting all datasets on every health check; O(n) per probe.

**Approach A — Cache Dataset Count**:

- *Implementation*: Maintain a cached dataset count updated on save/delete. Health probe reads cached value.
- *Strengths*: O(1) per probe; accurate within save/delete cycle.
- *Weaknesses*: Cache may be stale if files are modified outside the application.
- *Risks*: Minimal for health probes.
- *Guardrails*: Refresh cache periodically (every 60s) as fallback.

**Approach B — Simplified Readiness Check**:

- *Implementation*: Replace glob with a simpler check: `storage_path.exists() and storage_path.is_dir()`.
- *Strengths*: O(1); simpler; sufficient for readiness.
- *Weaknesses*: Doesn't verify data accessibility.
- *Risks*: Probe may report ready when storage is corrupted.
- *Guardrails*: Keep liveness separate from readiness.

**Recommended**: Approach B because readiness probes should be fast and simple.

---

#### PERF-JD-02: High-Cardinality Prometheus Labels

**Current Code**: `api/observability.py:98` — `endpoint = request.url.path`.
**Root Cause**: Full URL path used as label, including dataset IDs.
**Cross-References**: PERF-JD-02 = BUG-JD-09

**Approach A**: See BUG-JD-09 remediation (use route template).
**Recommended**: See BUG-JD-09.

---

## 17. Concurrency and Thread Safety Issues (v5 new)

Issues identified through cross-cutting concurrency analysis across all repositories.

### Issue Identification Table, Section 17

| ID      | Severity   | Repository     | Description                                                                           | File(s)                                | Evidence                                                           |
|---------|------------|----------------|---------------------------------------------------------------------------------------|----------------------------------------|--------------------------------------------------------------------|
| CONC-01 | **HIGH**   | juniper-canopy | `_per_ip_counts` check-then-act race in WebSocketManager — no lock on check+decrement | `websocket_manager.py:278-282,289-292` | Concurrent connect/disconnect can corrupt per-IP tracking          |
| CONC-02 | **MEDIUM** | juniper-cascor | `_last_state_broadcast_time` unprotected cross-thread R/W                             | `manager.py:151-155`                   | Two callers can both pass throttle check simultaneously            |
| CONC-03 | **MEDIUM** | juniper-cascor | `_extract_and_record_metrics` split-lock — duplicate emissions                        | `manager.py:453-495`                   | Lock released between read and write of high-water-mark            |
| CONC-04 | **HIGH**   | juniper-data   | ALL storage operations block async event loop (extends JD-PERF-01)                    | `datasets.py:98-154,259,277,377-424`   | get_meta, save, batch ops are synchronous in async handlers        |
| CONC-07 | **MEDIUM** | juniper-canopy | `regenerate_dataset` mutates state without lock                                       | `demo_mode.py:1660-1676`               | Training thread sees partially updated dataset                     |
| CONC-08 | **LOW**    | juniper-canopy | `is_running` reads/writes inconsistently locked                                       | `demo_mode.py:1151,1293,1398,1478`     | Boolean check-then-act not atomic                                  |
| CONC-09 | **MEDIUM** | juniper-cascor | Fire-and-forget `asyncio.create_task` without stored reference                        | `app.py:137,142`                       | Startup tasks silently swallowed on exception; GC'd references     |
| CONC-10 | **LOW**    | juniper-cascor | Health monitor deregister/assign race window                                          | `coordinator.py:379-408`               | Task assigned to worker about to be deregistered — 120s delay risk |
| CONC-12 | **LOW**    | juniper-data   | `record_access` TOCTOU on access_count increment                                      | `base.py:125-135`                      | Concurrent access increments can lose counts                       |

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

**Recommended**: Approach A for immediate fix (highest-priority performance issue); Approach B should be documented and added as a longer-term fix.

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

## 18. Error Handling and Robustness (v5 new)

Issues identified through cross-cutting error handling analysis across all repositories.

### Issue Identification Table, Section 18

| ID        | Severity   | Repository            | Description                                                                                        | File(s)                                                 |
|-----------|------------|-----------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| ERR-01    | **MEDIUM** | juniper-data-client   | `response.json()` unguarded against JSONDecodeError on all 13 public methods                       | `client.py:215-531`                                     |
| ERR-02    | **MEDIUM** | juniper-cascor-client | `response.json()` unguarded in `_request()` — ValueError escapes                                   | `client.py:366`                                         |
| ERR-06    | **LOW**    | juniper-cascor        | `raise HTTPException` without `from e` — loses exception context (6 locations)                     | `routes/network.py:31,52`, `training.py:89,109,121,170` |
| ERR-07    | **LOW**    | juniper-data          | `raise HTTPException` without `from e` — broad except masks programming errors as 400              | `datasets.py:90`                                        |
| ERR-08    | **LOW**    | juniper-data          | `str(e)` in batch create error response — information disclosure                                   | `datasets.py:342-348`                                   |
| ERR-09    | **MEDIUM** | juniper-cascor        | `remote_client_0.process_tasks()` catches all exceptions, only prints — silent failure             | `remote_client_0.py:73-74`                              |
| ERR-12    | **LOW**    | juniper-canopy        | `config_manager._load_config()` silently returns {} on any exception                               | `config_manager.py:147-149`                             |
| ERR-13    | **LOW**    | juniper-data          | `arc_agi` generator silently falls back on any exception — masks auth/network errors               | `generator.py:95-98`                                    |
| ERR-14    | **MEDIUM** | juniper-cascor-client | `CascorMetricsStream.stream()` swallows ConnectionClosed — caller can't detect disconnect          | `ws_client.py:79-80`                                    |
| ROBUST-01 | **HIGH**   | juniper-cascor        | Dummy candidate results on double training failure — zero-correlation candidate installed silently | `cascade_correlation.py:1930-1962`                      |

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
- *Guardrails*: Note: `remote_client_0.py` is in `src/remote_client/` which is slated for deletion (CLN-CC-01/HSK-02). Fix is moot if file is deleted.

**Recommended**: Approach A, but prioritize CLN-CC-01 (deleting the file) as the real fix.

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

## 19. Testing and CI/CD Gaps (v5 new)

Issues identified through cross-cutting test coverage and CI analysis across all repositories.

### Issue Identification Table, Section 19

| ID        | Severity   | Category     | Repository     | Description                                                                         |
|-----------|------------|--------------|----------------|-------------------------------------------------------------------------------------|
| CI-01     | **HIGH**   | CI/CD        | cascor-client  | CI doesn't test Python 3.14 — consumers (cascor, canopy) run on 3.14                |
| CI-02     | **HIGH**   | CI/CD        | cascor-worker  | CI doesn't test Python 3.14 — cascor (consumer) runs on 3.14                        |
| CI-03     | **HIGH**   | CI/CD        | juniper-deploy | 1,177 lines of tests exist but CI runs ZERO of them                                 |
| CI-04     | **MEDIUM** | CI/CD        | cascor-client  | Missing dedicated weekly security-scan.yml — vulnerability detection gap            |
| CI-05     | **MEDIUM** | CI/CD        | cascor-client  | Missing lockfile-update.yml workflow — stale dependencies accumulate                |
| CI-06     | **MEDIUM** | CI/CD        | juniper-deploy | No coverage configuration at all — tests exist but coverage never measured          |
| CI-07     | **LOW**    | CI/CD        | cascor, worker | Inconsistent GitHub Actions artifact upload/cache versions across repos             |
| COV-01    | **MEDIUM** | Coverage     | juniper-deploy | Tests exist but zero coverage infrastructure (no `[tool.coverage]`, no `--cov`)     |
| COV-02    | **MEDIUM** | Coverage     | juniper-canopy | No per-module coverage gate (juniper-data enforces 85% per-module)                  |
| COV-04    | **LOW**    | Coverage     | juniper-data   | Coverage gate mismatch — CI comment says 95%, actual `COVERAGE_FAIL_UNDER` is 80%   |
| TQ-01     | **MEDIUM** | Test Quality | juniper-cascor | 10+ tests with no assertions — fire-and-forget test methods inflate counts          |
| TQ-02     | **MEDIUM** | Test Quality | juniper-canopy | 149 `time.sleep` calls in tests — excessive hard-coded waits, flakiness risk        |
| TQ-03     | **MEDIUM** | Test Quality | cascor-worker  | Config validation tests have no assertions — pass as long as no exception           |
| TQ-04     | **LOW**    | Test Quality | juniper-cascor | 139 `hasattr` guards in tests (similar to canopy's 226 tracked in BUG-CN-03)        |
| TQ-05     | **LOW**    | Test Quality | juniper-canopy | 10 unit tests import httpx — actually integration-level tests                       |
| CI-SEC-01 | **HIGH**   | Security CI  | cascor-client  | No weekly security scan — supply chain vulnerability window for widely-consumed lib |
| CI-SEC-02 | **LOW**    | Security CI  | juniper-deploy | No security scanning at all (shell scripts, Python helpers unaudited)               |

### Cross-Repo CI Feature Matrix

| Feature              | cascor | canopy | data | data-client | cascor-client | cascor-worker | deploy | juniper-ml |
|----------------------|--------|--------|------|-------------|---------------|---------------|--------|------------|
| Pre-commit           | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | ✅     | ✅         |
| Unit Tests in CI     | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | ❌     | ✅         |
| Coverage Gate        | 80%    | 80%    | 80%+ | 80%         | 80%           | 80%           | ❌     | —          |
| Per-Module Coverage  | —      | ❌     | ✅   | —           | —             | —             | —      | —          |
| Python 3.14 CI       | ✅     | ✅     | ✅   | ✅          | ❌            | ❌            | —      | —          |
| Gitleaks             | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| Bandit SAST          | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| pip-audit            | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| Weekly security-scan | ✅     | ✅     | ✅   | ✅          | ❌            | ✅            | —      | ✅         |
| Docker smoke test    | ✅     | ✅     | ✅   | —           | —             | —             | —      | —          |

### Issue Remediations, Section 19

#### CI-01: cascor-client CI Doesn't Test Python 3.14

**Current Code**: CI matrix missing 3.14; consumers run on 3.14.
**Root Cause**: CI not updated when 3.14 support was classified.

**Approach A — Add 3.14 to CI Matrix**:

- *Implementation*: Add `"3.14"` to the Python version matrix in `.github/workflows/ci.yml`.
- *Strengths*: Catches 3.14 incompatibilities before consumer deployment.
- *Weaknesses*: Longer CI runs.
- *Risks*: 3.14 may not be available in CI runner images (use `actions/setup-python@v5`).
- *Guardrails*: Allow 3.14 failures initially (non-blocking).

**Recommended**: Approach A.

---

#### CI-02: cascor-worker CI Doesn't Test Python 3.14

**Approach A**: Same as CI-01 — add 3.14 to matrix.
**Recommended**: Approach A.

---

#### CI-03: juniper-deploy CI Runs ZERO Tests

**Current Code**: 1,177 lines of tests exist but never run in CI.
**Root Cause**: Pytest job not configured in deploy CI workflow.

**Approach A — Add Pytest Job**:

- *Implementation*: Add `pytest tests/ -v --tb=short` job to `.github/workflows/ci.yml`.
- *Strengths*: Existing tests become useful; catches regressions.
- *Weaknesses*: May require test dependencies.
- *Risks*: Tests may fail if they depend on Docker.
- *Guardrails*: Run unit tests only (skip Docker-dependent tests in CI).

**Recommended**: Approach A because 1,177 lines of untested tests provide zero value.

---

#### CI-04: Missing Weekly security-scan.yml for cascor-client

**Approach A — Create Workflow**:

- *Implementation*: Copy `security-scan.yml` from juniper-cascor or juniper-ml. Add pip-audit and dependabot for cascor-client.
- *Strengths*: Closes supply chain vulnerability window.
- *Weaknesses*: Weekly cadence may miss urgent CVEs.
- *Risks*: None.
- *Guardrails*: Also enable Dependabot security alerts.

**Recommended**: Approach A.

---

#### CI-05: Missing lockfile-update.yml for cascor-client

**Approach A — Create Workflow**:

- *Implementation*: Add scheduled workflow to update `requirements.lock` and open PR on changes.
- *Strengths*: Prevents stale dependencies.
- *Weaknesses*: Auto-PRs may be noisy.
- *Risks*: Updates may break compatibility.
- *Guardrails*: Auto-PR requires passing CI before merge.

**Recommended**: Approach A.

---

#### CI-06: juniper-deploy No Coverage Configuration

**Approach A — Add Coverage Config**:

- *Implementation*: Add `[tool.coverage]` to `pyproject.toml`. Add `--cov` flag to pytest command. Set initial threshold at 50%.
- *Strengths*: Measurable test coverage; improvement tracking.
- *Weaknesses*: Low initial threshold.
- *Risks*: None.
- *Guardrails*: Gradually increase threshold.

**Recommended**: Approach A.

---

#### CI-07: Inconsistent GitHub Actions Versions Across Repos

**Approach A — Standardize Versions**:

- *Implementation*: Align all repos to same versions of `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, etc.
- *Strengths*: Consistent CI behavior; easier maintenance.
- *Weaknesses*: Coordination across 8 repos.
- *Risks*: Version upgrades may break workflows.
- *Guardrails*: Test one repo first; roll out to others.

**Recommended**: Approach A.

---

#### COV-01: Deploy Tests Exist but Zero Coverage

**Cross-References**: COV-01 = CI-06.
**Approach A**: See CI-06 remediation.

---

#### COV-02: Canopy No Per-Module Coverage Gate

**Approach A — Add Per-Module Coverage**:

- *Implementation*: Add `[tool.coverage.run] source = ["src"]` and module-level minimums in `pyproject.toml`.
- *Strengths*: Prevents coverage regression per module.
- *Weaknesses*: Setup effort.
- *Risks*: Some modules may be below threshold.
- *Guardrails*: Start with 60% per-module; increase gradually.

**Recommended**: Approach A.

---

#### COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%

**Approach A — Align Documentation**:

- *Implementation*: Update CI comment to match actual `COVERAGE_FAIL_UNDER=80`. Or raise threshold if 95% is the real target.
- *Strengths*: Consistent documentation.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A — fix documentation to match reality.

---

#### TQ-01: 10+ Tests with No Assertions (cascor)

**Approach A — Add Assertions**:

- *Implementation*: Review each assertion-free test. Add appropriate assertions (return values, state changes, exception types).
- *Strengths*: Tests actually verify behavior.
- *Weaknesses*: Must understand test intent.
- *Risks*: Some tests may be deliberately assertion-free (smoke tests).
- *Guardrails*: Mark intentional smoke tests with `# smoke test` comment.

**Recommended**: Approach A.

---

#### TQ-02: 149 `time.sleep` Calls in canopy Tests

**Approach A — Replace with Event-Based Waits**:

- *Implementation*: Replace `time.sleep(n)` with `wait_for_condition(lambda: ..., timeout=n)` helper. Poll condition every 50ms.
- *Strengths*: Tests run faster; less flaky.
- *Weaknesses*: Must identify correct condition for each wait.
- *Risks*: Some waits may be for side effects without observable conditions.
- *Guardrails*: Keep timeout as upper bound; reduce gradually.

**Recommended**: Approach A — incremental replacement.

---

#### TQ-03: Worker Config Validation Tests with No Assertions

**Approach A — Add Assertions**:

- *Implementation*: Add assertions verifying config values after validation.
- *Strengths*: Tests verify behavior.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### TQ-04: 139 `hasattr` Guards in cascor Tests

**Approach A**: Same pattern as BUG-CN-03 — remove guards, fix mocks.
**Recommended**: See BUG-CN-03 remediation.

---

#### TQ-05: 10 Unit Tests Import httpx (Integration-Level)

**Approach A — Re-Classify as Integration Tests**:

- *Implementation*: Move tests using `httpx` to `tests/integration/` directory. Apply `requires_server` marker.
- *Strengths*: Correct test classification; clear expectations.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Run in separate CI job.

**Recommended**: Approach A.

---

#### CI-SEC-01: No Weekly Security Scan for cascor-client

**Cross-References**: CI-SEC-01 = CI-04.
**Approach A**: See CI-04 remediation.

---

#### CI-SEC-02: No Security Scanning in juniper-deploy

**Approach A — Add Basic Scanning**:

- *Implementation*: Add `shellcheck` to CI for shell scripts. Add `bandit` scan for Python helpers. Add container image scanning with Trivy.
- *Strengths*: Basic security hygiene.
- *Weaknesses*: May produce false positives.
- *Risks*: None.
- *Guardrails*: Start with warning-only mode.

**Recommended**: Approach A.

---

## 20. Configuration and Dependency Issues (v5 new)

Issues identified through cross-cutting configuration and dependency analysis across all repositories.

### Issue Identification Table, Section 20

| ID     | Severity   | Category              | Repository     | Description                                                                                         | Evidence                                                        |
|--------|------------|-----------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| CFG-01 | **HIGH**   | Missing Dependency    | juniper-canopy | `torch` imported unconditionally but missing from dependencies — demo mode crashes on install       | `demo_backend.py:45` imports torch; not in pyproject.toml       |
| CFG-02 | **MEDIUM** | Unnecessary Dep       | juniper-cascor | `sentry-sdk` in core deps but only used when `SENTRY_SDK_DSN` is set                                | Should be in optional `observability` extra                     |
| CFG-03 | **MEDIUM** | Env Var Inconsistency | juniper-cascor | `SENTRY_SDK_DSN` (main.py) vs `JUNIPER_CASCOR_SENTRY_DSN` (Settings) — two env vars for one feature | `main.py:58` vs `settings.py:189`                               |
| CFG-04 | **MEDIUM** | Config Bypass         | juniper-cascor | `JUNIPER_DATA_URL` read via raw `os.getenv`, bypasses Settings class — no validation                | `app.py:121,185,253`, `health.py:56`                            |
| CFG-05 | **MEDIUM** | Env Var Conflict      | juniper-cascor | `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — both needed for full log level control           | `constants.py:580` vs `settings.py:116`                         |
| CFG-06 | **LOW**    | Naming                | cascor-worker  | `CASCOR_*` env prefix inconsistent with ecosystem `JUNIPER_*` convention                            | `constants.py:126-138` — 13 env vars use bare `CASCOR_*`        |
| CFG-07 | **MEDIUM** | Port Inconsistency    | Cross-repo     | Port 8200 vs 8201 confusion — cascor binds 8200, Docker maps to 8201, clients default to 8200       | cascor-client, canopy default to 8200; Docker host port is 8201 |
| CFG-08 | **LOW**    | Config Inconsistency  | Cross-repo     | Rate limiting defaults differ — data enabled, cascor/canopy disabled by default                     | Local dev has no rate limits; production does — behavioral gap  |
| CFG-09 | **MEDIUM** | Unsafe Default        | juniper-canopy | `audit_log_path` defaults to `/var/log/canopy/audit.log` — requires root, crashes non-root deploys  | `settings.py:172` — `audit_log_enabled: True` default           |
| CFG-12 | **LOW**    | Build Config          | cascor-worker  | `setuptools>=82.0` vs `>=61.0` everywhere else — unnecessary constraint                             | `pyproject.toml:2`                                              |
| CFG-13 | **LOW**    | Unnecessary Dep       | juniper-canopy | `python-dotenv` in core deps but never imported — pydantic-settings handles `.env`                  | No `import dotenv` in canopy `src/`                             |
| CFG-14 | **LOW**    | Stale Constraint      | juniper-canopy | `juniper-cascor-client>=0.1.0` allows outdated incompatible versions (current is 0.4.0)             | juniper-ml requires `>=0.3.0`                                   |
| CFG-16 | **LOW**    | Config Bypass         | juniper-canopy | `CASCOR_DEMO_MODE` read directly, bypasses Settings deprecation validator                           | `backend/__init__.py:66`                                        |

### Issue Remediations, Section 20

#### CFG-01: `torch` Imported but Missing from canopy Dependencies

**Current Code**: `demo_backend.py:45` imports torch; not in canopy's `pyproject.toml`.
**Root Cause**: torch imported unconditionally but never declared as dependency.

**Approach A — Add torch to Dependencies**:

- *Implementation*: Add `torch>=2.0` to canopy's `pyproject.toml` dependencies or optional extras `[demo]`.
- *Strengths*: Explicit dependency; install doesn't fail at runtime.
- *Weaknesses*: Large dependency (~2GB).
- *Risks*: May conflict with other PyTorch versions in environment.
- *Guardrails*: Use optional extra `[demo]` if torch is only needed for demo mode.

**Recommended**: Approach A with `[demo]` optional extra to avoid bloating base install.

---

#### CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally

**Current Code**: `sentry-sdk` in cascor core deps but only when `SENTRY_SDK_DSN` is set.
**Root Cause**: SDK always installed even when Sentry is not configured.

**Approach A — Move to Optional Extra**:

- *Implementation*: Move to `[project.optional-dependencies] observability = ["sentry-sdk"]`. Conditional import with graceful fallback.
- *Strengths*: Smaller base install; explicit opt-in.
- *Weaknesses*: Users must install extra for Sentry.
- *Risks*: Existing deployments with Sentry need to update install command.
- *Guardrails*: Clear error message when DSN is set but SDK not installed.

**Recommended**: Approach A because optional features should use optional dependencies.

---

#### CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars

**Current Code**: `main.py:58` reads `SENTRY_SDK_DSN`; `settings.py:189` reads `JUNIPER_CASCOR_SENTRY_DSN`.
**Root Cause**: Two different code paths independently added Sentry support with different env var names.

**Approach A — Consolidate to Settings**:

- *Implementation*: Remove raw `os.getenv("SENTRY_SDK_DSN")` from `main.py`. Use only `settings.sentry_dsn` which reads `JUNIPER_CASCOR_SENTRY_DSN`. Add alias for backward compat.
- *Strengths*: Single source of truth; validated via Settings.
- *Weaknesses*: Breaking change for deployments using `SENTRY_SDK_DSN`.
- *Risks*: Must update deployment configs.
- *Guardrails*: Settings validator reads both env vars, preferring `JUNIPER_CASCOR_SENTRY_DSN`.

**Recommended**: Approach A because dual env vars is confusing and error-prone.

---

#### CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings

**Current Code**: `app.py:121,185,253`, `health.py:56` — raw `os.getenv()` calls bypass Settings validation.
**Root Cause**: URL was added before Settings class was comprehensive.

**Approach A — Move to Settings Class**:

- *Implementation*: Add `juniper_data_url: Optional[str] = None` to Settings. Replace all `os.getenv("JUNIPER_DATA_URL")` with `settings.juniper_data_url`.
- *Strengths*: Validated; documented; visible in Settings dump.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Use `AliasChoices` for both env var names if needed.

**Recommended**: Approach A because all config should go through Settings.

---

#### CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed

**Current Code**: `constants.py:580` reads `CASCOR_LOG_LEVEL`; `settings.py:116` reads `JUNIPER_CASCOR_LOG_LEVEL`.
**Root Cause**: Legacy env var name not migrated to ecosystem prefix convention.

**Approach A — Consolidate with Alias**:

- *Implementation*: Use `JUNIPER_CASCOR_LOG_LEVEL` as primary. Add `CASCOR_LOG_LEVEL` as deprecated alias via `AliasChoices` in Settings. Log deprecation warning when old name is used.
- *Strengths*: Backward compatible; ecosystem-consistent.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Remove deprecated alias after one release cycle.

**Recommended**: Approach A.

---

#### CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention

**Current Code**: `cascor-worker/constants.py:126-138` — 13 env vars use bare `CASCOR_*`.
**Root Cause**: Worker predates the ecosystem `JUNIPER_*` prefix convention.

**Approach A — Add `JUNIPER_` Prefix with Aliases**:

- *Implementation*: Support both `JUNIPER_CASCOR_WORKER_*` and `CASCOR_*` via `AliasChoices`. Deprecate old prefix.
- *Strengths*: Ecosystem-consistent; backward compatible.
- *Weaknesses*: 13 env vars to alias.
- *Risks*: Must update deployment configs eventually.
- *Guardrails*: Deprecation warnings on old prefix usage.

**Recommended**: Approach A.

---

#### CFG-07: Port 8200 vs 8201 Confusion

**Current Code**: Cascor binds 8200; Docker maps to host 8201; clients default to 8200.
**Root Cause**: Docker port mapping creates confusion between container and host ports.

**Approach A — Document and Standardize Defaults**:

- *Implementation*: Document the port mapping clearly in AGENTS.md and client READMEs. Client defaults to 8200 (correct for direct connections); add note about Docker mapping.
- *Strengths*: Clarifies confusion; no breaking changes.
- *Weaknesses*: Port confusion persists for new developers.
- *Risks*: None.
- *Guardrails*: Consider changing Docker host port to 8200 for consistency.

**Recommended**: Approach A because changing ports has deployment impact.

---

#### CFG-08: Rate Limiting Defaults Differ Across Services

**Current Code**: Data has rate limiting enabled; cascor/canopy disabled by default.
**Root Cause**: Each service independently configured rate limiting defaults.

**Approach A — Document Default Differences**:

- *Implementation*: Document rate limiting defaults in each service's AGENTS.md and in deployment guide. Note that production should enable rate limiting on all services.
- *Strengths*: Clear documentation; no behavioral changes.
- *Weaknesses*: Doesn't fix the inconsistency.
- *Risks*: None.
- *Guardrails*: Add rate limit config to deployment templates.

**Recommended**: Approach A because different defaults may be intentional per-service.

---

#### CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root

**Current Code**: `settings.py:172` — `audit_log_enabled: True` with `/var/log/canopy/audit.log` default.
**Root Cause**: Default path requires root permissions; crashes non-root deployments.

**Approach A — User-Space Default**:

- *Implementation*: Change default to `~/.local/share/canopy/audit.log` or `./logs/audit.log`. Create directory if needed.
- *Strengths*: Works without root; follows XDG convention.
- *Weaknesses*: Different path than production systems expect.
- *Risks*: None.
- *Guardrails*: Document production path in deployment guide.

**Approach B — Make Audit Log Optional**:

- *Implementation*: Change `audit_log_enabled: bool = False`. Require explicit opt-in.
- *Strengths*: No path issues by default.
- *Weaknesses*: Audit logging off by default.
- *Risks*: Production may miss enabling audit log.
- *Guardrails*: Log warning at startup if audit logging disabled.

**Recommended**: Approach A because audit logging should work out-of-the-box.

---

#### CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere

**Current Code**: Worker requires `setuptools>=82.0`; all others use `>=61.0`.
**Root Cause**: Unnecessarily restrictive constraint.

**Approach A — Align to `>=61.0`**:

- *Implementation*: Change worker's `setuptools>=82.0` to `>=61.0` (or whatever is actually required).
- *Strengths*: Consistent; reduces install friction.
- *Weaknesses*: None if 61.0 is sufficient.
- *Risks*: Must verify no 82.0-specific features are used.
- *Guardrails*: Test build with setuptools 61.0.

**Recommended**: Approach A — trivial version constraint fix.

---

#### CFG-13: `python-dotenv` in canopy Core Deps but Never Imported

**Current Code**: `python-dotenv` in canopy deps; no `import dotenv` in `src/`.
**Root Cause**: Dependency added speculatively or pydantic-settings handles `.env` natively.

**Approach A — Remove from Dependencies**:

- *Implementation*: Remove `python-dotenv` from canopy's `pyproject.toml`.
- *Strengths*: Smaller dependency set; removes unused package.
- *Weaknesses*: Must verify pydantic-settings doesn't need it (it doesn't — uses its own `.env` reader).
- *Risks*: None.
- *Guardrails*: Test settings loading after removal.

**Recommended**: Approach A because unused dependencies are bloat.

---

#### CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions

**Current Code**: Canopy allows cascor-client 0.1.0+ (current is 0.4.0).
**Root Cause**: Version constraint not tightened as API evolved.

**Approach A — Tighten Constraint**:

- *Implementation*: Change to `juniper-cascor-client>=0.3.0` (minimum compatible version per juniper-ml).
- *Strengths*: Prevents installation of incompatible versions.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Align with juniper-ml's constraint.

**Recommended**: Approach A — one-line fix.

---

#### CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings

**Current Code**: `backend/__init__.py:66` reads `CASCOR_DEMO_MODE` via raw `os.getenv`.
**Root Cause**: Config bypass for demo mode detection.

**Approach A — Route Through Settings**:

- *Implementation*: Read from `Settings.demo_mode` instead of raw `os.getenv`. Settings already has demo mode detection.
- *Strengths*: Consistent configuration access; validated.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify Settings includes demo mode detection.

**Recommended**: Approach A because all config should go through Settings.

---

## 21. API Contract and Protocol Issues (v5 new)

Issues identified through cross-cutting API contract and protocol correctness analysis.

### Issue Identification Table, Section 21

| ID       | Severity   | Category        | Repositories          | Description                                                                                                             |
|----------|------------|-----------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------|
| API-01   | **MEDIUM** | Health Endpoint | cascor, data, canopy  | Health `status` value inconsistent: cascor/data return `"ok"`, canopy returns `"healthy"`                               |
| API-02   | **LOW**    | Health Endpoint | cascor, data, canopy  | Health response schema diverges — canopy returns 7 fields, cascor/data return 2                                         |
| API-03   | **HIGH**   | State Machine   | cascor, canopy        | Canopy FSM lacks auto-reset from FAILED/COMPLETED on START — training unrestartable in demo mode without explicit RESET |
| API-04   | **MEDIUM** | Testing         | cascor-client, cascor | FakeClient state constants use different vocabulary: `"idle"` vs `"STOPPED"`, `"training"` vs `"STARTED"`               |
| API-05   | **MEDIUM** | Error Handling  | all services          | Error response format inconsistent — three different JSON error shapes across services                                  |
| API-06   | **LOW**    | Protocol        | cascor, cascor-client | `candidate_progress` WS message broadcast by server, not in client constants, no callback handler                       |
| API-07   | **MEDIUM** | API Coverage    | data, data-client     | Client missing methods for 4 server endpoints: filter, stats, cleanup-expired, individual tags                          |
| API-08   | **LOW**    | Protocol        | cascor-client, cascor | `set_params` includes extraneous `type:command` field; `command()` does not — asymmetric envelopes                      |
| API-09   | **MEDIUM** | API Contract    | juniper-cascor        | HTTPException errors bypass ResponseEnvelope — dual error format in same API                                            |
| PROTO-01 | **LOW**    | Protocol        | canopy, cascor        | Canopy `/ws/control` accepts `reset` parameter not in cascor's control protocol                                         |

### Issue Remediations, Section 21

#### API-01: Health `status` Value Inconsistent

**Current Code**: cascor/data return `"ok"`, canopy returns `"healthy"`.
**Root Cause**: No standardized health response schema.
**Cross-References**: API-01 = XREPO-13

**Approach A — Standardize to `"ok"`**:

- *Implementation*: Change canopy to return `"ok"`. Document standard health response: `{"status": "ok", "version": "x.y.z"}`.
- *Strengths*: Consistent across all services; simple string change.
- *Weaknesses*: Breaking change for canopy health check consumers.
- *Risks*: Load balancer/orchestrator health checks may depend on `"healthy"`.
- *Guardrails*: Check Docker and K8s health check configs before changing.

**Recommended**: Approach A because `"ok"` is the majority convention.

---

#### API-02: Health Response Schema Diverges

**Current Code**: Canopy returns 7 fields, cascor/data return 2.
**Root Cause**: Each service independently defined its health response.

**Approach A — Standardize Minimal Schema**:

- *Implementation*: Define shared schema: `{"status": "ok", "version": "x.y.z", "service": "name"}`. Additional fields are optional and service-specific.
- *Strengths*: Consistent base schema; extensible.
- *Weaknesses*: Canopy must restructure response.
- *Risks*: Consumers depending on canopy-specific fields may break.
- *Guardrails*: Keep canopy-specific fields as optional extras.

**Recommended**: Approach A because a shared base schema enables consistent monitoring.

---

#### API-03: Canopy FSM Lacks Auto-Reset from FAILED/COMPLETED on START

**Current Code**: Demo mode FSM cannot restart training from FAILED or COMPLETED state without explicit RESET.
**Root Cause**: FSM transition table doesn't include FAILED→STOPPED or COMPLETED→STOPPED transitions.

**Approach A — Add Auto-Reset Transitions**:

- *Implementation*: Add transitions: FAILED + START → STOPPED → STARTED, and COMPLETED + START → STOPPED → STARTED. Implement as composite transition: auto-reset then start.
- *Strengths*: Intuitive UX; users can click Start without manual Reset.
- *Weaknesses*: Implicit state transitions may surprise API consumers expecting explicit reset.
- *Risks*: Must preserve training state cleanup during auto-reset.
- *Guardrails*: Log auto-reset at INFO level; emit WebSocket event for state change.

**Recommended**: Approach A because requiring manual reset after failure is poor UX.

---

#### API-04: FakeClient State Constants Different Vocabulary

**Cross-References**: API-04 = XREPO-14
**Approach A**: See XREPO-14 remediation.

---

#### API-05: Error Response Format Inconsistent

**Current Code**: Three different error shapes: cascor `{"status":"error","error":{}}`, data `{"detail":""}`, canopy `{"error":"","detail":"","status_code":500}`.
**Root Cause**: Each service independently defined error responses.
**Cross-References**: API-05 = XREPO-15

**Approach A — Standardize Error Envelope**:

- *Implementation*: Define shared error format: `{"error": {"code": "ERROR_CODE", "message": "Human-readable", "detail": {}}}`. Implement via shared middleware or exception handler.
- *Strengths*: Consistent error handling in clients; single parsing path.
- *Weaknesses*: Breaking change for all services.
- *Risks*: Must coordinate across 3 services.
- *Guardrails*: Phase rollout: add new format alongside old; clients handle both; remove old after migration.

**Recommended**: Approach A because inconsistent error formats multiply client complexity.

---

#### API-06: `candidate_progress` WS Message Not in Client Constants

**Cross-References**: API-06 = XREPO-17
**Approach A**: See XREPO-17 remediation.

---

#### API-07: Client Missing Methods for 4 Server Endpoints

**Cross-References**: API-07 = XREPO-16
**Approach A**: See XREPO-16 remediation.

---

#### API-08: `set_params` Includes Extraneous `type:command` Field

**Current Code**: `set_params` sends `{"type": "command", ...}` while `command()` does not.
**Root Cause**: Inconsistent message envelope construction.
**Cross-References**: API-08 relates to XREPO-07/XREPO-08

**Approach A**: See XREPO-07 remediation (standardize envelope format).
**Recommended**: See XREPO-07.

---

#### API-09: HTTPException Errors Bypass ResponseEnvelope

**Current Code**: Cascor HTTPException responses don't go through ResponseEnvelope wrapper, creating dual error format.
**Root Cause**: FastAPI's default HTTPException handler returns `{"detail": "..."}`, not the project's `ResponseEnvelope` format.

**Approach A — Custom Exception Handler**:

- *Implementation*: Register `@app.exception_handler(HTTPException)` that wraps the response in `ResponseEnvelope(status="error", error={"code": exc.status_code, "message": exc.detail})`.
- *Strengths*: Consistent error format; all errors go through same envelope.
- *Weaknesses*: Must handle all HTTPException subclasses.
- *Risks*: None.
- *Guardrails*: Test with 400, 401, 403, 404, 500 status codes.

**Recommended**: Approach A because dual error formats cause client parsing failures.

---

#### PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol

**Current Code**: Canopy accepts `reset` command but cascor's control protocol doesn't define it.
**Root Cause**: Canopy added `reset` for demo mode without corresponding server-side support.

**Approach A — Document as Canopy Extension**:

- *Implementation*: Document `reset` as a canopy-specific extension to the control protocol. Add to protocol specification.
- *Strengths*: Clarifies intent; doesn't require server changes.
- *Weaknesses*: Protocol divergence between services.
- *Risks*: Clients may expect `reset` to work on cascor (it doesn't).
- *Guardrails*: Add note in client docs that `reset` is canopy-only.

**Recommended**: Approach A because `reset` is valid for demo mode and doesn't need server support.

---

## 22. Source Document Lineage (v5.0.0 - v1.0.0)

This document was produced by cross-referencing source documents across the Juniper ecosystem:

### v5.0.0 Analysis Changes

The source documents cross-referenced by the 5, v5.0.0 validation agents include the following:

- Documants include the first 33 documents from the original v3 list
- Documents #34 from the original v3 list was excluded: `PARALLEL_CANDIDATE_TRAINING_FIX_PLAN.md`
- A new file, labeled document #34 has, been included in the new v5 list: `OPT5_SHARED_MEMORY_PLAN.md`

### v4.0.0 Per-Repository Validation Sources

| Source                               | Method                                    | Scope                                              |
|--------------------------------------|-------------------------------------------|----------------------------------------------------|
| Live codebase: juniper-cascor        | File reads, grep, structural analysis     | All `src/` files, `pyproject.toml`, tests          |
| Live codebase: juniper-canopy        | File reads, grep, structural analysis     | All `src/` files, `pyproject.toml`, tests          |
| Live codebase: juniper-data          | File reads, grep, structural analysis     | All `juniper_data/` files, `pyproject.toml`, tests |
| Live codebase: juniper-data-client   | File reads, grep, structural analysis     | All `juniper_data_client/` files, tests            |
| Live codebase: juniper-cascor-client | File reads, grep, structural analysis     | All `juniper_cascor_client/` files, tests          |
| Live codebase: juniper-cascor-worker | File reads, grep, structural analysis     | All `juniper_cascor_worker/` files, tests          |
| Live codebase: juniper-deploy        | File reads, compose analysis, Helm review | All compose files, Dockerfiles, Helm chart, CI     |
| Live codebase: juniper-ml            | File reads, shellcheck, CI analysis       | All scripts, utilities, workflows, tests           |

### v3.0.0 Cross-Referenced Source Documents (34 total)

| #  | Document                                                                            | Repository     |
|----|-------------------------------------------------------------------------------------|----------------|
| 1  | `notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md`                              | juniper-ml     |
| 2  | `notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md`                              | juniper-cascor |
| 3  | `notes/development/CONSOLIDATED_DEVELOPMENT_HISTORY.md`                             | juniper-canopy |
| 4  | `notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md`                                 | juniper-ml     |
| 5  | `notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md`                             | juniper-ml     |
| 6  | `notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md`                  | juniper-ml     |
| 7  | `notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md`                | juniper-ml     |
| 8  | `notes/development/CODE_REVIEW_AUDIT_PLAN_2026-04-12_R5-01-aligned.md`              | juniper-canopy |
| 9  | `notes/development/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-12_R5-01-aligned.md`     | juniper-canopy |
| 10 | `notes/development/CODE_REVIEW_PLAN_2026-04-12_R5-01-aligned.md`                    | juniper-canopy |
| 11 | `notes/development/MICROSERVICES_PHASE4_PLAN_2026-04-06.md`                         | juniper-ml     |
| 12 | `notes/development/MICROSERVICES_PHASE3_PLAN_2026-04-06.md`                         | juniper-ml     |
| 13 | `notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md`                 | juniper-ml     |
| 14 | `notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_PLAN_2026-04-06.md`            | juniper-ml     |
| 15 | `notes/development/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md`              | juniper-canopy |
| 16 | `notes/development/PHASE_B_IMPLEMENTATION_PLAN.md`                                  | juniper-ml     |
| 17 | `notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-*.md`                | juniper-ml     |
| 18 | `notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-*.md`                           | juniper-ml     |
| 19 | `notes/code-review/RELEASE_DEVELOPMENT_ROADMAP_2026-04-*.md`                        | juniper-ml     |
| 20 | `notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-*.md`                    | juniper-ml     |
| 21 | `notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-*.md`                          | juniper-ml     |
| 22 | `notes/code-review/CASCOR_COMPREHENSIVE_CODE_REVIEW_PLAN_2026-04-*.md`              | juniper-ml     |
| 23 | `notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-*.md`                    | juniper-ml     |
| 24 | `notes/code-review/CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md`                  | juniper-ml     |
| 25 | `notes/development/R5-01_canonical_development_plan.md`                             | juniper-ml     |
| 26 | `notes/development/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md`                | juniper-canopy |
| 27 | `notes/development/IMPLEMENTATION_PLAN.md`                                          | juniper-canopy |
| 28 | `notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md`                                  | juniper-cascor |
| 29 | `notes/development/CONVERGENCE_THRESHOLD_ANALYSIS.md`                               | juniper-cascor |
| 30 | `notes/development/PRE-DEPLOYMENT_ROADMAP-2.md`                                     | juniper-cascor |
| 31 | `notes/development/PERFORMANCE_TESTING_PLAN.md`                                     | juniper-cascor |
| 32 | `notes/development/JUNIPER_MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP_AUDIT.md` | juniper-cascor |
| 33 | `notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md`              | juniper-cascor |
| 34 | `notes/development/PARALLEL_CANDIDATE_TRAINING_FIX_PLAN.md`                         | juniper-cascor |

### v1.0.0–v2.0.0 Primary Sources

| # | Document                              | Location                            | Date       | Items                                   |
|---|---------------------------------------|-------------------------------------|------------|-----------------------------------------|
| 1 | `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | `juniper-ml/notes/development/`     | 2026-04-17 | 91+ items from 16 source documents      |
| 2 | `CONSOLIDATED_DEVELOPMENT_HISTORY.md` | `juniper-canopy/notes/development/` | 2026-04-17 | 99+ issues from 16 source documents     |
| 3 | `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | `juniper-cascor/notes/development/` | 2026-04-17 | ~120 items from 12 source documents     |
| 4 | `DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` | `juniper-ml/notes/development/`     | 2026-04-19 | 70+ findings from deep audit of 5 repos |

---

## 23. Validation Methodology (v6.0.0 - v1.0.0)

### v6.0.0 Remediation Analysis Process

Version 6.0.0 extends the v5.0.0 validated issue inventory with a **5-agent remediation analysis**. Each agent performed deep source code analysis across the relevant repositories, verified each identified issue against the live codebase, and developed 1-3 remediation approaches per item. Each approach includes an implementation sketch, strengths, weaknesses, risks, and guardrails. Cross-references between sections were validated to prevent duplicate remediation work.

#### v6.0.0 Agents (Remediation Analysis)

| Agent   | Focus Area                                                                                 | Sections Covered               | Items Analyzed |
|---------|--------------------------------------------------------------------------------------------|--------------------------------|----------------|
| Agent A | Security, Concurrency, Error Handling                                                      | 4, 17, 18                      | ~33            |
| Agent B | Active Bugs (cascor, canopy, data), Data Security                                          | 5, 14.1                        | ~44            |
| Agent C | Cross-Repo Alignment, Client Libraries, API/Protocol                                       | 11, 15, 21                     | ~56            |
| Agent D | Code Quality, Housekeeping, Performance, Configuration                                     | 6, 12, 16, 20                  | ~76            |
| Agent E | Dashboard, WebSocket, Infrastructure, CasCor, Deploy, Data Performance/Roadmap, Testing/CI | 7, 8, 9, 10, 13, 14.2-14.3, 19 | ~120           |

#### Key Cross-References Validated

| Item A    | Item B    | Relationship                                            |
|-----------|-----------|---------------------------------------------------------|
| SEC-01    | JD-SEC-02 | Same issue (API key timing) in data security context    |
| XREPO-01  | DC-01     | Same issue (generator name mismatch) in client context  |
| BUG-CC-16 | CONC-02   | Same issue (broadcast time race) in concurrency context |
| BUG-CC-17 | CONC-03   | Same issue (split-lock metrics) in concurrency context  |
| BUG-JD-10 | CONC-04   | Same issue (async blocking) in concurrency context      |
| BUG-CN-11 | CONC-07   | Same issue (state mutation) in concurrency context      |

#### Remediation Analysis Statistics

| Metric                                   | Count |
|------------------------------------------|-------|
| Total items analyzed                     | ~300  |
| Items with Approach A only               | ~180  |
| Items with Approach A + B                | ~80   |
| Items with Approach A + B + C            | ~10   |
| Items deferred (🔵)                      | ~15   |
| Items cross-referenced to other sections | ~25   |

---

### v5.0.0 Validation Process

Version 5.0.0 extends the v4.0.0 per-repository audit with a second wave of **cross-cutting concern agents** — 5 agents that each audited ALL 8 repositories through a specific analytical lens. This complementary approach catches issues that span repository boundaries and require understanding of system-wide patterns.

#### v5.0.0 Agents (Cross-Cutting Concerns)

| Agent    | Focus Area                                         | Repositories | New Findings |
|----------|----------------------------------------------------|--------------|--------------|
| Agent 6  | Concurrency, threading, async correctness          | All 8        | 9            |
| Agent 7  | Error handling, exception safety, robustness       | All 8        | 10           |
| Agent 8  | Test coverage, test quality, CI/CD completeness    | All 8        | 17           |
| Agent 9  | Configuration, dependencies, environment variables | All 8        | 13           |
| Agent 10 | API contracts, protocol correctness, integration   | All 8        | 10           |

#### Key Changes from v4.0.0 -> v5.0.0

| Change Type              | Count   | Details                                                                                                    |
|--------------------------|---------|------------------------------------------------------------------------------------------------------------|
| Items confirmed FIXED    | 0       | No additional items resolved between v4 and v5                                                             |
| New bugs                 | 8       | BUG-CC-16–18, BUG-CN-11–12, BUG-JD-10–11                                                                   |
| New deploy issues        | 3       | DEPLOY-24–26 (Helm missing critical env vars for K8s)                                                      |
| New cross-repo issues    | 5       | XREPO-13–17 (health status, FakeClient vocabulary, error shapes, missing methods, candidate_progress)      |
| New concurrency issues   | 9       | CONC-01–12 (per-IP race, throttle race, split-lock, async blocking, state mutation, fire-and-forget tasks) |
| New error handling       | 10      | ERR-01–14, ROBUST-01 (JSONDecodeError gaps, silent failures, dummy training results)                       |
| New testing/CI gaps      | 17      | CI-01–07, COV-01–04, TQ-01–05, CI-SEC-01–02                                                                |
| New configuration issues | 13      | CFG-01–16 (torch missing dep, Sentry dual env, port confusion, audit log root crash)                       |
| New API/protocol issues  | 10      | API-01–09, PROTO-01 (FSM auto-reset, health inconsistency, error format, missing client methods)           |
| **Total new items (v5)** | **~70** | Deduplicated across 5 cross-cutting agents                                                                 |

#### Cumulative Audit Statistics

| Version | Method                      | Agents | New Items Found | Cumulative Total |
|---------|-----------------------------|--------|-----------------|------------------|
| v1–v2   | Document cross-reference    | 3      | 69              | 69               |
| v3      | 34-document cross-reference | 5      | ~85             | ~145             |
| v4      | Per-repo codebase audit     | 5      | ~83             | ~230             |
| v5      | Cross-cutting concern audit | 5      | ~70             | **~300**         |

#### Severity Distribution (v5 new items only)

| Severity | Count | Highlights                                                                                                                            |
|----------|-------|---------------------------------------------------------------------------------------------------------------------------------------|
| HIGH     | 8     | ROBUST-01 (dummy training results), API-03 (FSM auto-reset), CFG-01 (torch missing), BUG-CC-18, CONC-01/04, CI-01/02/03, DEPLOY-24/25 |
| MEDIUM   | 35    | Config env var conflicts, port confusion, JSONDecodeError gaps, race conditions, test quality, error formats                          |
| LOW      | 27    | Config bypass, naming inconsistencies, missing assertions, minor protocol asymmetries                                                 |

### Previous Validation Processes (v0.0.4 - v0.0.1)

#### v4.0.0 Agents (Per-Repository Focus)

| Agent   | Focus Area                          | Repositories                                 | Findings |
|---------|-------------------------------------|----------------------------------------------|----------|
| Agent 1 | Backend server security & bugs      | juniper-cascor                               | 18       |
| Agent 2 | Dashboard UI, performance, security | juniper-canopy                               | 15       |
| Agent 3 | Data service & client library       | juniper-data, juniper-data-client            | 19       |
| Agent 4 | Client SDK & distributed worker     | juniper-cascor-client, juniper-cascor-worker | 17       |
| Agent 5 | Infrastructure, scripts, CI/CD      | juniper-deploy, juniper-ml                   | 25       |

#### v3.0.0 Agents (Full Documents Deep Audit and Validation)

- juniper-cascor-client: 93.52% coverage, 4 medium issues, all notes work complete
- juniper-cascor-worker: 91.47% coverage, 5 medium issues, all notes work complete
- juniper-data: 1 high security (path traversal), 1 high perf (blocking async), 4 deferred roadmap items
- juniper-data-client: 2 critical bugs (generator name mismatch), all notes work complete
- juniper-deploy: 3 high infrastructure bugs (AlertManager missing, rules not mounted, secret mismatch), 8 unimplemented roadmap items

#### v1.0.0 - v2.0.0 Agents (Initial Documents Validation and Analysis)

- Cascor validation: 15 items checked → 12 still open, 3 now fixed
- Canopy validation: 16 items checked → 6 now fixed, 4 still open, 3 partially fixed
- Ecosystem validation: 13 items checked → 0 fixed, 8 still open, 3 partially fixed

---

*End of outstanding development items document (v6.0.0 — validated via 10-agent audit with 5-agent remediation analysis: ~300 items with 1-3 remediation approaches each across 8 repositories).*
