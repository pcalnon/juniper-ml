# V6 Partial — Agent C: Cross-Repo Alignment, Client Libraries, API/Protocol

**Sections Covered**: 11 (Cross-Repo), 15 (Client Libraries), 21 (API/Protocol)
**Generated**: 2026-04-22
**Source Verification**: Key items verified against live codebase

---

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
- *Strengths*: Fulfills client expectation; adds useful dataset type.
- *Weaknesses*: More effort; adds sklearn dependency if not present.
- *Risks*: Must define parameter schema consistent with other generators.
- *Guardrails*: Add integration test between client and server for moon generator.

**Recommended**: Approach A for immediate fix; Approach B as a follow-up feature.

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

### Issue Remediations, Section 15 — juniper-cascor-client

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

### Issue Remediations, Section 15 — juniper-data-client

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

### Issue Remediations, Section 15 — juniper-cascor-worker

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

*End of Agent C partial — 17 cross-repo items + 29 client items + 10 API items = 56 items covered (some cross-referenced)*
