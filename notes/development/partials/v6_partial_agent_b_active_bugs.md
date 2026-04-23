# V6 Partial — Agent B: Active Bugs

**Sections Covered**: 5.1 (cascor bugs), 5.2 (canopy bugs), 5.3 (data bugs), 14.1 (data security)
**Generated**: 2026-04-22
**Source Verification**: Key items verified against live codebase

---

### Issue Remediations, Section 5 — juniper-cascor

#### BUG-CC-01: `create_topology_message()` Not Fully Implemented

**Current Code**: `src/api/websocket/messages.py:72` — function defined and exported but has zero production callers.
**Root Cause**: Topology change broadcasting was planned but never wired into lifecycle events (cascade_add, network creation).

**Approach A — Wire into Lifecycle Events**:
- *Implementation*: Call `create_topology_message()` from `manager.py` after each `on_cascade_add()` and network structure change. Broadcast via `_ws_manager.broadcast_from_thread()`.
- *Strengths*: Completes planned functionality; dashboards get real-time topology updates.
- *Weaknesses*: Must define topology message payload schema; may increase WS traffic.
- *Risks*: Large networks may produce oversized topology messages (see GAP-WS-18).
- *Guardrails*: Add message size check before broadcast; throttle topology broadcasts to max 1/second.

**Approach B — Remove Dead Code**:
- *Implementation*: Delete `create_topology_message()` if topology WS broadcasting is not on the current roadmap.
- *Strengths*: Reduces dead code; clearer codebase.
- *Weaknesses*: Must re-implement when topology broadcasting is needed.
- *Risks*: None.
- *Guardrails*: Document removal in CHANGELOG.

**Recommended**: Approach A if topology broadcasting is planned for upcoming releases; Approach B otherwise.

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

**Approach A — Delete Directory**:
- *Implementation*: Delete `src/remote_client/` entirely (3 files). Superseded by juniper-cascor-worker.
- *Strengths*: Removes all legacy issues at once.
- *Weaknesses*: None — code is unused.
- *Risks*: None.
- *Guardrails*: Verify zero callers/imports before deletion.

**Recommended**: Approach A because the entire directory is dead code.

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
**Root Cause**: Function was modified incorrectly and is now broken. Zero production callers (dead code).

**Approach A — Delete the Function**:
- *Implementation*: Remove `load_dataset()` since it has zero callers and is fundamentally broken.
- *Strengths*: Removes dead code and broken functionality.
- *Weaknesses*: None — no callers.
- *Risks*: None.
- *Guardrails*: Grep for any references before deletion.

**Recommended**: Approach A because fixing dead code is wasteful; deletion is correct.

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

### Issue Remediations, Section 5 — juniper-canopy

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
- *Implementation*: Delete the second `try/except` block (lines 110-113). Keep the first one.
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

### Issue Remediations, Section 5 — juniper-data

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

### Issue Remediations, Section 14.1

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

*End of Agent B partial — 18 cascor bugs + 12 canopy bugs + 11 data bugs + 3 data security items = 44 items covered*
