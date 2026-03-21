# juniper-canopy: External Cascor Integration Plan

**Version**: 2.0.0
**Date**: 2026-03-21
**Status**: Validated

---

## Overview

This plan covers the design and phased implementation of external cascor support in juniper-canopy. The goal is to allow juniper-canopy to discover, connect to, monitor, and control an independently running juniper-cascor process without disrupting that process's ongoing operation.

---

## Codebase Analysis Summary

### juniper-canopy (Current State)

**Architecture**: FastAPI + Dash hybrid on port 8050. FastAPI serves REST/WebSocket APIs; Dash provides the interactive UI mounted as a WSGI app.

**Backend modes**:

| Mode | Activation | Status |
|------|-----------|--------|
| DemoBackend | `CASCOR_DEMO_MODE=1` or no `CASCOR_SERVICE_URL` | Fully implemented (all controls) |
| ServiceBackend | `CASCOR_SERVICE_URL` env var set | Partially implemented (start/stop only) |

**Service mode gaps** (currently returns errors or is missing):
- `pause_training()` / `resume_training()` / `reset_training()` — stubs return `{"ok": False, "error": "...not yet supported..."}`
- `apply_params(**params)` — not delegated to cascor service
- No auto-discovery of running cascor processes
- No non-destructive connection (`self.network` sentinel not populated on attach)
- No state synchronization on connect (metrics history, topology, params, training status)
- Graceful disconnection is effectively already working (does not call `stop_training()` on cascor), but WebSocket relay task needs clean close

**Key files**:
- `src/backend/__init__.py` — Backend factory (`create_backend()`, sync)
- `src/backend/cascor_service_adapter.py` — Wraps `juniper-cascor-client`; has `_training_stream` and `_relay_task` but no `_control_stream`
- `src/backend/service_backend.py` — `ServiceBackend` adapter
- `src/backend/demo_backend.py` — `DemoBackend` adapter
- `src/backend/protocol.py` — `BackendProtocol` interface (uses `apply_params(**params)` signature)
- `src/backend/training_monitor.py` — Contains `TrainingState` class (NOT in `training_state_machine.py`)
- `src/main.py` — FastAPI lifespan; already probes cascor health at startup (lines 151–163); calls `create_backend()` synchronously
- `src/settings.py` — Pydantic settings; `cascor_service_url: Optional[str] = None` exists; `_check_cascor_service_url` validator handles legacy env var; `demo_mode: bool` field (resolved via `_check_legacy_demo_mode` validator)
- `src/health.py` — `probe_dependency()` uses `urllib.request` (not `httpx`)

### juniper-cascor (Current State)

**Architecture**: FastAPI REST + WebSocket API on port 8200. Single training thread in `ThreadPoolExecutor`. Candidate training via `multiprocessing`.

**Full API surface already implemented**:
- `POST /v1/training/start` — Start training
- `POST /v1/training/stop` — Stop training
- `POST /v1/training/pause` — Pause training
- `POST /v1/training/resume` — Resume training
- `POST /v1/training/reset` — Reset
- `GET /v1/training/status` — Current state machine state
- `GET /v1/training/params` — Current training parameters
- `GET /v1/network` — Network info
- `GET /v1/network/topology` — Topology structure
- `GET /v1/network/stats` — Weight statistics
- `GET /v1/metrics/history` — **Already implemented** (metrics router, NOT training router)
- `WS /ws/training` — Real-time metrics push
- `WS /ws/control` — Command acknowledgment

**Key implementation details**:
- `TrainingLifecycleManager` has `_training_lock: threading.Lock`
- `TrainingMonitor.metrics_buffer: deque = deque(maxlen=10000)` already exists
- `get_metrics_history()` already exists on `TrainingLifecycleManager`
- Route injection pattern: `lifecycle = _get_lifecycle(request)` (NOT FastAPI `Depends()`)
- Return pattern: `success_response(data)` (NOT `ResponseEnvelope` in decorator)
- Router prefixes: `APIRouter(prefix="/training")` mounted under `/v1`

**Actual gaps** (genuinely missing):
- No `PATCH /v1/training/params` endpoint for runtime parameter updates
- `TrainingLifecycleManager` has no `update_params()` method
- `CascadeCorrelationConfig` is mutable but not retained on the manager after `create_network()` — must modify `self.network` attributes directly

**Key files**:
- `src/api/app.py` — FastAPI factory, lifespan
- `src/api/lifecycle/manager.py` — `TrainingLifecycleManager`; `_training_lock: threading.Lock`
- `src/api/lifecycle/monitor.py` — `TrainingMonitor`; `metrics_buffer: deque(maxlen=10000)`
- `src/api/lifecycle/state_machine.py` — `TrainingStateMachine`
- `src/api/routes/training.py` — Training endpoints; uses `_get_lifecycle(request)` injection
- `src/api/routes/network.py` — Network endpoints
- `src/api/routes/metrics.py` — Metrics endpoints including `GET /v1/metrics/history`
- `src/api/models/training.py` — `TrainingStartRequest`, `DatasetSource`, `InlineDataset`, `TrainingStatus`

### juniper-cascor-client (Current State)

**REST client** (`JuniperCascorClient`):
- Wraps all existing endpoints
- HTTP helpers: `_get()`, `_post()`, `_delete()` — no `_patch()` exists
- Retry strategy `allowed_methods`: `["GET", "POST", "DELETE", "PUT"]` — PATCH not included
- `client.reset_training()` (NOT `reset()`) — important name
- `get_metrics_history(count: Optional[int] = None)` already exists

**Fake client** (`FakeCascorClient`):
- Pattern: `threading.Lock` + `_check_closed()` + `_maybe_raise_error()`
- `get_metrics_history()` already exists
- `get_network()` raises `JuniperCascorNotFoundError` when no network loaded

**Actual gaps** (genuinely missing):
- No `update_params(params: dict) -> dict` method on `JuniperCascorClient`
- No `_patch()` helper method
- "PATCH" not in retry strategy `allowed_methods`
- No `update_params()` on `FakeCascorClient`

---

## Requirements Mapping

| Requirement | Gap | Phase |
|------------|-----|-------|
| SR-1: Detect running cascor on launch | Auto-discovery not implemented | Phase 1 |
| SR-2: Connect to discovered cascor | Service mode exists but requires explicit URL | Phase 1 |
| SR-3: Non-destructive connection | `self.network` sentinel not populated on attach without `create_network()` | Phase 1 |
| SR-4: Retrieve metrics from cascor | Metrics stream + history already work once connected | Phase 1 (state sync) |
| SR-5: Display metrics | Already works once connected | Phase 1 (unblocked by SR-4) |
| SR-6: Retrieve parameters from cascor | `GET /v1/training/params` exists | Phase 1 |
| SR-7: Display parameters | Already works once SR-6 is synced | Phase 1 (unblocked by SR-6) |
| SR-8: Apply parameter changes | Not implemented in service mode; cascor endpoint missing | Phase 2 |
| SR-9: Live visualizations (topology, etc.) | Topology works; history already available | Phase 1 |
| SR-10: Training controls (all) | pause/resume/reset are stubs in service mode | Phase 2 |
| SR-11: Canopy stop doesn't stop cascor | Already graceful (no `stop_training()` called on shutdown) | Phase 3 (verify + test) |
| SR-12: Multiple start/stop cycles | Discovery + non-destructive attach covers this | Phase 1 |

---

## Phased Implementation Plan

### Phase 1: Foundation — Auto-Discovery, Non-Destructive Connection, State Sync

**Priority**: CRITICAL — Enables all other phases

#### 1.1 Cascor Auto-Discovery

**Constraint**: `create_backend()` is a **synchronous** function and must remain synchronous (12 existing tests call it synchronously). Discovery logic must live in `main.py`'s lifespan (which is already async), not inside `create_backend()`.

**Architecture**:
1. Lifespan in `src/main.py` runs discovery before calling `create_backend()`
2. If discovery finds cascor, sets `settings.cascor_service_url` (or passes URL directly)
3. `create_backend()` is called synchronously as before; it reads the URL from settings

**New file**: `src/discovery.py`

```python
import urllib.request
import asyncio
from typing import Optional

DEFAULT_DISCOVERY_PORTS = [8200]

async def probe_cascor_url(url: str, timeout: float = 2.0) -> bool:
    """
    Probe a URL for a running cascor instance.
    Uses urllib.request via executor to avoid blocking the event loop.
    Returns True if cascor responds with {"status": "alive"} at /v1/health/live.
    """
    def _probe() -> bool:
        try:
            req = urllib.request.Request(f"{url}/v1/health/live")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    return False
                import json
                body = json.loads(resp.read())
                return body.get("status") == "alive"
        except Exception:
            return False

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _probe)

async def discover_cascor(
    host: str = "localhost",
    ports: list[int] = DEFAULT_DISCOVERY_PORTS,
    timeout: float = 2.0,
) -> Optional[str]:
    """
    Probe well-known ports for a running cascor instance.
    Returns the first responding URL, or None.
    """
    for port in ports:
        url = f"http://{host}:{port}"
        if await probe_cascor_url(url, timeout=timeout):
            return url
    return None
```

**Changes to `src/main.py`** (lifespan, before `create_backend()` call):

```python
# Within lifespan(), before create_backend():
if not settings.demo_mode and not settings.cascor_service_url:
    if settings.cascor_discovery.enabled:
        discovered_url = await discover_cascor(
            host=settings.cascor_discovery.host,
            ports=settings.cascor_discovery.ports,
            timeout=settings.cascor_discovery.timeout_seconds,
        )
        if discovered_url:
            logger.info(f"Auto-discovered cascor at {discovered_url}")
            settings.cascor_service_url = discovered_url
# create_backend() reads settings.cascor_service_url as before
backend = create_backend()
```

**New settings** (`src/settings.py`):

```python
class CascorDiscoverySettings(BaseModel):
    """Settings for auto-discovery of running cascor instances."""
    enabled: bool = True
    host: str = "localhost"
    ports: list[int] = [8200]
    timeout_seconds: float = 2.0

class Settings(BaseSettings):
    # ... existing fields ...
    cascor_discovery: CascorDiscoverySettings = CascorDiscoverySettings()
```

**IMPORTANT — Backward compatibility**: All existing `create_backend()` tests must continue to pass. Tests that expect demo mode when `CASCOR_SERVICE_URL` is unset must set `JUNIPER_CANOPY_CASCOR_DISCOVERY__ENABLED=false` in their environment, OR mock `discover_cascor()`. The test fixture must be updated accordingly.

New environment variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `JUNIPER_CANOPY_CASCOR_DISCOVERY__ENABLED` | `true` | Enable auto-discovery |
| `JUNIPER_CANOPY_CASCOR_DISCOVERY__HOST` | `localhost` | Host to probe |
| `JUNIPER_CANOPY_CASCOR_DISCOVERY__PORTS` | `[8200]` | Ports to probe (JSON list) |
| `JUNIPER_CANOPY_CASCOR_DISCOVERY__TIMEOUT_SECONDS` | `2.0` | Probe timeout |

#### 1.2 Non-Destructive Connection

**Context**: `CascorServiceAdapter.__init__()` does NOT call `create_network()`. However, `ServiceBackend.start_training()` checks `if self._adapter.network is None` — without calling `attach_to_existing()`, the `network` property returns `None` even when cascor has a live network, causing incorrect behavior in any `network`-dependent code path.

**Changes to `src/backend/cascor_service_adapter.py`**:

```python
def attach_to_existing(self) -> bool:
    """
    Attempt to attach to an already-running cascor session.
    Does NOT call create_network() or modify any cascor state.
    Returns True if an existing network was found.
    The 'network' property queries the client on each access,
    so there is nothing to cache — this call confirms existence only.
    """
    try:
        self._client.get_network()  # Raises JuniperCascorNotFoundError if no network
        self._attached_to_existing = True
        logger.info("Attached to existing cascor network (non-destructive mode)")
        return True
    except JuniperCascorNotFoundError:
        self._attached_to_existing = False
        return False
    except Exception as exc:
        logger.warning(f"Failed to probe cascor for existing network: {exc}")
        self._attached_to_existing = False
        return False
```

**Changes to `src/backend/service_backend.py`** (`initialize()` method):

```python
async def initialize(self) -> None:
    """Initialize service backend, attaching to existing cascor if possible."""
    await self._adapter.connect()  # Existing: checks client.is_ready()
    # Try to attach to existing network before any create_network() call
    has_existing_network = self._adapter.attach_to_existing()
    if has_existing_network:
        logger.info("ServiceBackend: Attached to existing cascor network")
        # Sync state from cascor
        await self._sync_state_from_cascor()
    # Start metrics relay regardless
    await self._adapter.start_metrics_relay()
```

#### 1.3 State Synchronization on Connect

**New file**: `src/backend/state_sync.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SyncedState:
    is_training: bool
    status: str          # "Stopped", "Started", "Paused", "Completed", "Failed"
    phase: str           # "Idle", "Output", "Candidate", "Inference"
    current_epoch: int
    params: dict
    topology: Optional[dict]
    metrics_history: list[dict]

class CascorStateSync:
    """
    Synchronizes canopy's local TrainingState from a running cascor instance.
    Called once on attach to ensure canopy displays accurate state immediately.
    """

    def __init__(self, client):
        self._client = client

    def sync(self, metrics_limit: int = 500) -> SyncedState:
        """Fetch current cascor state. Caps metrics history at metrics_limit entries."""
        status_response = self._client.get_training_status()
        # Response has top-level "is_training" and nested "training_state"
        is_training = status_response.get("is_training", False)
        training_state = status_response.get("training_state", {})

        params = {}
        topology = None
        try:
            params = self._client.get_training_params()
        except Exception:
            pass
        try:
            topology = self._client.get_topology()
        except Exception:
            pass

        metrics_history = []
        try:
            metrics_history = self._client.get_metrics_history(count=metrics_limit)
        except Exception:
            pass

        return SyncedState(
            is_training=is_training,
            status=training_state.get("status", "Stopped"),
            phase=training_state.get("phase", "Idle"),
            current_epoch=training_state.get("current_epoch", 0),
            params=params,
            topology=topology,
            metrics_history=metrics_history,
        )

    def apply(self, synced: SyncedState, training_state) -> None:
        """Apply synced cascor state to canopy's TrainingState object."""
        training_state.update_state(
            status=synced.status,
            phase=synced.phase,
            current_epoch=synced.current_epoch,
        )
```

**Cascor states handled during sync**:
- `Stopped` / `Idle` — Show stopped state; all start controls active
- `Started` / training active — Show live metrics; pause/stop active
- `Paused` — Show paused state; resume/stop active
- `Completed` — Show completed state; reset active
- `Failed` — Show error state

---

### Phase 2: Service Mode Feature Completion

**Priority**: HIGH

#### 2.1 Cascor: Runtime Parameter Update Endpoint

**File**: `juniper-cascor/src/api/routes/training.py`

Add `PATCH /v1/training/params` following the exact existing pattern:

```python
@router.patch("/params")
async def update_training_params(
    request: Request,
    params: TrainingParamUpdateRequest,
) -> dict:
    """
    Update runtime-modifiable training parameters.
    Parameters safe to update without restart: learning_rate, candidate_learning_rate,
    correlation_threshold, candidate_pool_size.
    Parameters requiring reset: max_hidden_units, epochs_max.
    """
    lifecycle = _get_lifecycle(request)
    updated = lifecycle.update_params(params.model_dump(exclude_none=True))
    return success_response(updated)
```

**File**: `juniper-cascor/src/api/lifecycle/manager.py`

Add `update_params()` — must use `self.network` (not a stored `_config`):

```python
def update_params(self, params: dict) -> dict:
    """
    Thread-safe update of runtime-modifiable training parameters.
    Modifies the live network's attributes directly.
    """
    with self._training_lock:
        if self.network is None:
            raise ValueError("No network exists — create a network first")
        for key, value in params.items():
            if hasattr(self.network, key):
                setattr(self.network, key, value)
        return self.get_training_params()
```

**File**: `juniper-cascor/src/api/models/training.py`

Add alongside existing models:

```python
class TrainingParamUpdateRequest(BaseModel):
    """Runtime-modifiable training parameters. All fields optional (PATCH semantics)."""
    learning_rate: Optional[float] = None
    candidate_learning_rate: Optional[float] = None
    correlation_threshold: Optional[float] = None
    candidate_pool_size: Optional[int] = None
    max_hidden_units: Optional[int] = None  # Takes effect on next hidden unit add
    epochs_max: Optional[int] = None
```

**Thread-safety note**: `learning_rate` and similar scalar fields can be safely set on `self.network` while the training thread is running, as long as the optimizer is re-queried each epoch (which the cascor implementation does). Fields like `max_hidden_units` affect the cascade trigger condition — they are safe to update at any point as they are only checked at cascade evaluation time.

#### 2.2 Cascor: Metrics History — Already Implemented

> **NO ACTION REQUIRED** — `GET /v1/metrics/history` already exists in `src/api/routes/metrics.py`. `TrainingMonitor.metrics_buffer` is already a `deque(maxlen=10000)`. `JuniperCascorClient.get_metrics_history(count=None)` already exists. This section of the plan is complete as-is.

The only relevant detail: `TrainingMonitor.on_training_start()` calls `self.metrics_buffer.clear()` — so history reflects only the current training run, not prior runs in the same cascor session.

#### 2.3 Cascor Client: Add `update_params()`

**File**: `juniper-cascor-client/juniper_cascor_client/client.py`

Step A — Add `_patch()` helper and "PATCH" to `allowed_methods`:

```python
def __init__(self, ...):
    # ... existing code ...
    retry = Retry(
        total=self._retries,
        backoff_factor=0.5,
        status_forcelist=[502, 504],
        allowed_methods=["GET", "POST", "DELETE", "PUT", "PATCH"],  # Add PATCH
    )
    # ...

def _patch(self, path: str, **kwargs) -> dict:
    """PATCH helper — same pattern as _post()."""
    return self._request("PATCH", path, **kwargs)
```

Step B — Add `update_params()`:

```python
def update_params(self, params: dict) -> dict:
    """Update runtime-modifiable training parameters. PATCH /v1/training/params"""
    return self._patch("/training/params", json=params)["data"]
```

**File**: `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py`

Add `update_params()` following the existing lock + guard pattern:

```python
def update_params(self, params: dict) -> dict:
    with self._lock:
        self._check_closed()
        self._maybe_raise_error("update_params")
        # Update fake params store
        self._params.update(params)
        return dict(self._params)
```

**Version bump**: `pyproject.toml` `0.1.0` → `0.2.0` (additive feature addition).

#### 2.4 Canopy: Implement All Service Mode Training Controls

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

Replace stubs with real cascor API calls. Note: client method is `reset_training()` not `reset()`.

```python
def pause_training(self) -> dict:
    result = self._client.pause_training()
    return {"ok": True, "data": result}

def resume_training(self) -> dict:
    result = self._client.resume_training()
    return {"ok": True, "data": result}

def reset_training(self) -> dict:
    result = self._client.reset_training()  # NOT reset()
    self._attached_to_existing = False
    return {"ok": True, "data": result}
```

For parameter updates — reconcile with `BackendProtocol.apply_params(**params)` signature:

```python
# In CascorServiceAdapter:
def apply_params(self, **params) -> dict:
    """Forward param updates to cascor. Maps canopy nn_*/cn_* names to cascor format."""
    mapped = _map_canopy_params_to_cascor(params)
    if not mapped:
        return {"ok": True, "data": {}}
    result = self._client.update_params(mapped)
    return {"ok": True, "data": result}

def _map_canopy_params_to_cascor(params: dict) -> dict:
    """
    Map canopy's nn_*/cn_* parameter namespace to cascor API parameters.
    Keys not in the mapping are silently skipped (canopy-only params
    like nn_spiral_rotations, nn_dataset_elements have no cascor equivalent).
    """
    MAPPING = {
        "nn_learning_rate": "learning_rate",
        "nn_max_hidden_units": "max_hidden_units",
        "cn_pool_size": "candidate_pool_size",
        "cn_correlation_threshold": "correlation_threshold",
        # Add mappings as cascor exposes additional runtime-modifiable params
    }
    return {MAPPING[k]: v for k, v in params.items() if k in MAPPING}
```

**File**: `juniper-canopy/src/backend/service_backend.py`

Update the stub `apply_params()` to delegate to the adapter:
```python
async def apply_params(self, **params) -> dict:
    return self._adapter.apply_params(**params)
```

---

### Phase 3: Graceful Lifecycle Management

**Priority**: HIGH

#### 3.1 Graceful Disconnection (Verify + Test)

**Current state**: `ServiceBackend.shutdown()` already calls only `stop_metrics_relay()` and `adapter.shutdown()`. `adapter.shutdown()` calls `client.close()` (closes HTTP session) and does NOT call `stop_training()` or `delete_network()` on cascor. **The graceful disconnection requirement is already met by the existing implementation.**

**Action needed**: Verify this is correct and write tests that confirm it. Add an explicit log statement to make this guarantee visible:

```python
async def shutdown(self) -> None:
    """Disconnect from cascor. Training continues unaffected."""
    logger.info("Canopy shutting down — disconnecting from cascor (cascor continues running)")
    await self._adapter.stop_metrics_relay()
    await self._adapter.shutdown()
    # Note: We intentionally do NOT call stop_training() or delete_network() here.
    # The cascor process continues independently after canopy exits.
```

**`disconnect_streams_only()` note**: The adapter has `_training_stream` and `_relay_task` but no `_control_stream`. The plan's `disconnect_streams_only()` should only address the training stream / relay task. The existing `stop_metrics_relay()` method already handles this — no new method needed.

#### 3.2 Multiple Start/Stop Cycles

The Phase 1 discovery + non-destructive attach flow handles this: each canopy startup goes through discovery → probe → attach without modifying cascor state. No additional implementation needed beyond what Phase 1 delivers.

#### 3.3 WebSocket Reconnection

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

Add reconnect loop around the relay task:

```python
async def _relay_with_reconnect(self) -> None:
    """Subscribe to cascor's training stream with automatic reconnection."""
    backoff = [1, 2, 5, 10, 30]
    attempt = 0
    # Convert http:// URL to ws:// for WebSocket client
    ws_url = self._base_url.replace("http://", "ws://").replace("https://", "wss://")

    while self._relay_enabled:
        try:
            async with CascorTrainingStream(ws_url) as stream:
                attempt = 0
                async for message in stream:
                    await self._handle_stream_message(message)
        except Exception as exc:
            if not self._relay_enabled:
                break
            delay = backoff[min(attempt, len(backoff) - 1)]
            logger.warning(f"Cascor stream disconnected ({exc}). Reconnecting in {delay}s")
            attempt += 1
            await asyncio.sleep(delay)
```

---

### Phase 4: Testing

**Priority**: HIGH (required for correctness validation and regression prevention)

#### 4.1 Canopy: New Unit Tests

Tests go in `src/tests/unit/`. Follow existing `monkeypatch` + `pytest.fixture` + `FakeCascorClient` patterns. Use `asyncio_mode = "auto"` (already configured in `pyproject.toml`).

| Test File | Coverage |
|-----------|---------|
| `src/tests/unit/test_cascor_discovery.py` | `probe_cascor_url()` success/failure, `discover_cascor()` finds first responding port, returns None when none found, integration with lifespan (mock discover) |
| `src/tests/unit/test_non_destructive_connection.py` | `attach_to_existing()` when network exists (True), when no network (False), when connection error (False, no raise) |
| `src/tests/unit/test_state_sync.py` | `CascorStateSync.sync()` for all cascor statuses (Stopped/Started/Paused/Completed/Failed), `apply()` calls `update_state()` with correct kwargs, partial failures (topology 404) don't crash sync |
| `src/tests/unit/test_service_controls.py` | Pause/resume/reset delegated to client in service mode; `reset_training()` (not `reset()`) is called; `_attached_to_existing` cleared after reset |
| `src/tests/unit/test_service_apply_params.py` | Param name mapping (nn_*/cn_* → cascor format); unknown params silently skipped; `update_params()` on client called with mapped dict |
| `src/tests/unit/test_graceful_disconnection.py` | `ServiceBackend.shutdown()` does NOT call `stop_training()` or `delete_network()`; only `stop_metrics_relay()` and `client.close()` are called |
| `src/tests/unit/test_backend_factory.py` (update) | Existing tests unchanged; add: factory uses `ServiceBackend` when `cascor_service_url` is pre-set by discovery in lifespan |

**Discovery test backward compatibility**: Existing tests that expect `DemoBackend` when `CASCOR_SERVICE_URL` is unset must continue to pass. The discovery function is only called from the lifespan, not from `create_backend()`. Tests that call `create_backend()` directly bypass discovery entirely and remain unaffected.

#### 4.2 Cascor: New Unit Tests

Tests go in `src/tests/unit/api/` to match existing API test convention.

| Test File | Coverage |
|-----------|---------|
| `src/tests/unit/api/test_api_runtime_params.py` | `PATCH /v1/training/params` — valid params update network attrs; unknown params skipped; 404 when no network; `_training_lock` acquired during update |
| `src/tests/unit/test_training_params_model.py` | `TrainingParamUpdateRequest` — all fields optional; None values excluded from `model_dump(exclude_none=True)` |

#### 4.3 Cascor Client: New Tests

| Test File | Coverage |
|-----------|---------|
| `tests/test_client_update_params.py` | `update_params()` sends PATCH to `/training/params`; response data extracted correctly; `_patch()` helper delegates correctly |
| `tests/test_fake_client_update_params.py` | `FakeCascorClient.update_params()` updates internal state; follows lock + guard pattern |

#### 4.4 Integration Tests

**New file**: `juniper-canopy/src/tests/integration/test_external_cascor_e2e.py`

Full lifecycle integration (marked `@pytest.mark.requires_cascor @pytest.mark.integration`):

```python
@pytest.mark.requires_cascor
@pytest.mark.integration
class TestExternalCascorLifecycle:
    """
    End-to-end tests requiring a live cascor on localhost:8200.
    cascor must be running and healthy before these tests execute.
    """

    async def test_canopy_discovers_cascor_without_service_url(self): ...
    async def test_non_destructive_attach_preserves_network(self): ...
    async def test_state_sync_reflects_cascor_training_status(self): ...
    async def test_pause_via_canopy_pauses_cascor(self): ...
    async def test_resume_via_canopy_resumes_cascor(self): ...
    async def test_param_update_via_canopy_applied_to_cascor(self): ...
    async def test_canopy_shutdown_does_not_stop_cascor(self): ...
    async def test_multiple_canopy_attach_detach_cycles(self): ...
    async def test_metrics_history_loaded_on_connect(self): ...
```

#### 4.5 Regression Tests

| Test File | Coverage |
|-----------|---------|
| `src/tests/unit/test_demo_mode_regression.py` | Demo mode selected when `CASCOR_DEMO_MODE=1`; demo mode selected when no URL and discovery disabled; all existing demo controls work |
| `src/tests/regression/test_service_start_stop_regression.py` | Start/stop still work in service mode after all changes |

---

### Phase 5: Configuration Updates

**Priority**: MEDIUM

#### 5.1 Canopy Settings (additions)

**File**: `juniper-canopy/src/settings.py`

```python
class CascorDiscoverySettings(BaseModel):
    """Settings for auto-discovery of running cascor instances."""
    enabled: bool = True
    host: str = "localhost"
    ports: list[int] = [8200]
    timeout_seconds: float = 2.0

# In Settings class:
cascor_discovery: CascorDiscoverySettings = CascorDiscoverySettings()
```

No changes needed to `cascor_service_url` field — the existing `_check_cascor_service_url` validator handles the legacy env var. Do NOT add `Field(alias=...)` — it conflicts with the validator pattern.

#### 5.2 Cascor Settings (optional)

**File**: `juniper-cascor/src/api/settings.py`

The `metrics_buffer` is currently hardcoded at `deque(maxlen=10000)`. If configurability is wanted (low priority):

```python
metrics_history_size: int = Field(default=10000, description="Metrics history buffer size")
```

This is optional — the existing hardcoded value is sufficient for the requirements.

---

## Dependency Summary

### Package Version Updates Required

| Package | Current | Required | Reason |
|---------|---------|---------|--------|
| `juniper-cascor-client` | `0.1.0` | `0.2.0` | New `update_params()` method |
| `juniper-canopy` optional dep on cascor-client | `>=0.1.0` | `>=0.2.0` | Needs new client methods |

### No New Package Dependencies

All needed packages already present:
- HTTP probing: `urllib.request` (stdlib) — avoids new dependencies
- `juniper-cascor-client` already in canopy's optional deps
- `asyncio` stdlib for executor-based sync→async bridging

---

## Files Changed Summary

### juniper-cascor

| File | Change Type | Description |
|------|-------------|-------------|
| `src/api/routes/training.py` | Modify | Add `PATCH /v1/training/params` using `_get_lifecycle(request)` and `success_response()` patterns |
| `src/api/lifecycle/manager.py` | Modify | Add `update_params()` using `setattr(self.network, key, value)` with `_training_lock` |
| `src/api/models/training.py` | Modify | Add `TrainingParamUpdateRequest` model |
| `src/tests/unit/api/test_api_runtime_params.py` | New | Runtime param update tests |
| `src/tests/unit/test_training_params_model.py` | New | Model validation tests |

### juniper-cascor-client

| File | Change Type | Description |
|------|-------------|-------------|
| `juniper_cascor_client/client.py` | Modify | Add `_patch()` helper, `update_params()`, add "PATCH" to `allowed_methods` |
| `juniper_cascor_client/testing/fake_client.py` | Modify | Add `update_params()` following lock+guard pattern |
| `pyproject.toml` | Modify | Version `0.1.0` → `0.2.0` |
| `tests/test_client_update_params.py` | New | Client update_params tests |
| `tests/test_fake_client_update_params.py` | New | Fake client tests |

### juniper-canopy

| File | Change Type | Description |
|------|-------------|-------------|
| `src/discovery.py` | New | `probe_cascor_url()`, `discover_cascor()` |
| `src/settings.py` | Modify | Add `CascorDiscoverySettings` nested model |
| `src/main.py` | Modify | Add discovery step in lifespan before `create_backend()` |
| `src/backend/cascor_service_adapter.py` | Modify | Add `attach_to_existing()`, `_relay_with_reconnect()`, `apply_params(**kwargs)`, `_map_canopy_params_to_cascor()`, implement pause/resume/reset |
| `src/backend/service_backend.py` | Modify | Update `initialize()` for non-destructive attach + state sync; update `apply_params()` to delegate; add log to `shutdown()` |
| `src/backend/state_sync.py` | New | `CascorStateSync`, `SyncedState` dataclass |
| `src/tests/unit/test_cascor_discovery.py` | New | Discovery tests |
| `src/tests/unit/test_non_destructive_connection.py` | New | Non-destructive attach tests |
| `src/tests/unit/test_state_sync.py` | New | State sync tests |
| `src/tests/unit/test_service_controls.py` | New | Pause/resume/reset service mode tests |
| `src/tests/unit/test_service_apply_params.py` | New | Service mode param update tests |
| `src/tests/unit/test_graceful_disconnection.py` | New | Graceful shutdown tests |
| `src/tests/unit/test_demo_mode_regression.py` | New | Demo mode regression |
| `src/tests/integration/test_external_cascor_e2e.py` | New | Full lifecycle integration tests |

---

## Prioritized Implementation Order (Revised)

1. **[CRITICAL] cascor-client: Add `_patch()`, `update_params()`, `"PATCH"` to retry** — unblocks canopy param updates
2. **[CRITICAL] cascor: Add `PATCH /v1/training/params` + `update_params()` on manager** — enables runtime param changes
3. **[CRITICAL] canopy: Add `src/discovery.py` + `CascorDiscoverySettings`** — SR-1 auto-discovery
4. **[CRITICAL] canopy: Update `main.py` lifespan for discovery** — SR-1/SR-2
5. **[CRITICAL] canopy: Add `attach_to_existing()` in adapter** — SR-3 non-destructive connect
6. **[CRITICAL] canopy: Add `CascorStateSync` + `state_sync.py`** — SR-4/SR-6/SR-7
7. **[CRITICAL] canopy: Update `ServiceBackend.initialize()` for non-destructive attach + state sync** — ties it together
8. **[HIGH] canopy: Implement pause/resume/reset in service adapter** — SR-10
9. **[HIGH] canopy: Implement `apply_params()` delegation + param mapping** — SR-8
10. **[HIGH] canopy: Add reconnect loop for training stream** — SR-12 robustness
11. **[HIGH] canopy: Add log to `shutdown()` confirming graceful disconnect** — SR-11 verification
12. **[MEDIUM] All tests** — Written alongside each step
13. **[LOW] cascor: Make metrics_history_size configurable** — Optional enhancement

---

## Implementation Sequence

### Step 1: cascor-client changes
- Add `_patch()`, `update_params()`, "PATCH" in `allowed_methods`, `FakeCascorClient.update_params()`
- Bump to `0.2.0`
- Tests: `test_client_update_params.py`, `test_fake_client_update_params.py`

### Step 2: cascor changes
- Add `TrainingParamUpdateRequest` model
- Add `update_params()` on `TrainingLifecycleManager`
- Add `PATCH /v1/training/params` route
- Tests: `test_api_runtime_params.py`, `test_training_params_model.py`

### Step 3: canopy discovery
- Add `src/discovery.py`
- Add `CascorDiscoverySettings` to `settings.py`
- Update `main.py` lifespan
- Tests: `test_cascor_discovery.py`

### Step 4: canopy non-destructive attach + state sync
- Add `attach_to_existing()` to adapter
- Add `state_sync.py`
- Update `ServiceBackend.initialize()`
- Tests: `test_non_destructive_connection.py`, `test_state_sync.py`

### Step 5: canopy service mode controls
- Implement pause/resume/reset in adapter
- Implement `apply_params()` with mapping
- Update `ServiceBackend.apply_params()`
- Tests: `test_service_controls.py`, `test_service_apply_params.py`

### Step 6: canopy lifecycle & reconnect
- Add `_relay_with_reconnect()`
- Add log to `shutdown()`
- Tests: `test_graceful_disconnection.py`

### Step 7: regression + integration tests
- `test_demo_mode_regression.py`
- `test_external_cascor_e2e.py`
- Run full test suites for all three repos

### Step 8: version pins and PR creation
- Update canopy's `>=0.1.0` → `>=0.2.0` for cascor-client dep
- Create PRs in order: cascor → cascor-client → canopy

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Existing factory tests break from discovery | Low | High | Discovery lives in lifespan, NOT in `create_backend()` |
| Auto-discovery false positive (non-cascor on port 8200) | Low | Medium | Validate response body `{"status": "alive"}`, not just HTTP 200 |
| Thread-safety of `setattr(self.network, ...)` during training | Medium | Medium | Scalar fields are safe; loop-checked fields only evaluated at cascade time |
| `reset_training()` vs `reset()` method name | Low (now known) | Medium | Documented — client method is `reset_training()` |
| Demo mode regression from lifespan discovery | Low | High | `CASCOR_DEMO_MODE=1` checked before discovery is attempted |
| Metrics buffer cleared on `on_training_start()` | Low | Low | Documented behavior — history is per-run |
| WebSocket URL scheme conversion | Low | Medium | `http://` → `ws://` conversion in `_relay_with_reconnect()` |

---

## Acceptance Criteria

All of the following must be true before this work is considered complete:

- [ ] Canopy in normal mode auto-discovers cascor on localhost:8200 without `CASCOR_SERVICE_URL` being set
- [ ] Canopy connects to a running cascor without resetting or creating a new network
- [ ] Canopy displays accurate training state (epoch, status, phase) immediately on connect
- [ ] Canopy displays accurate parameter values from the running cascor
- [ ] Canopy displays accurate network topology from the running cascor
- [ ] Canopy displays metrics history from cascor
- [ ] Parameter changes from canopy UI are applied to the running cascor
- [ ] Pause issued from canopy pauses cascor training
- [ ] Resume issued from canopy resumes cascor training
- [ ] Stop issued from canopy stops cascor training
- [ ] When canopy is closed, cascor continues running unaffected
- [ ] Canopy can be restarted and re-attach to the same cascor session
- [ ] Demo mode is unaffected — all existing demo tests pass
- [ ] All existing cascor tests pass without regression
- [ ] All existing canopy tests pass without regression
- [ ] New tests achieve ≥80% coverage of new code
- [ ] Integration test `test_external_cascor_e2e.py` passes with a live cascor instance

---

## Worktree Strategy

Three worktrees required, one per repo with changes. Merge in dependency order.

| Repo | Branch | Purpose | Merge Order |
|------|--------|---------|------------|
| `juniper-cascor` | `feat/external-canopy-support` | PATCH params endpoint | 1st |
| `juniper-cascor-client` | `feat/external-canopy-support` | New client methods, version bump | 2nd |
| `juniper-canopy` | `feat/external-cascor` | All canopy changes | 3rd |
