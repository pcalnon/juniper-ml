# Round 1 Proposal R1-04: Operational Runbook — Day-by-Day Execution

**Angle**: Step-by-step runbook an engineer can execute from Day 1
**Author**: Round 1 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 1 consolidation — input to Round 2
**Inputs consolidated**: R0-01 (frontend), R0-02 (security), R0-03 (cascor backend), R0-04 (SDK set_params), R0-05 (testing), R0-06 (ops/phasing/risk)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 0. Pre-flight (before Day 1)

This is the one-time setup every engineer picking up the work must perform before touching a keyboard. **Do not skip.** Every later day assumes these items are true.

### 0.1 Read the background

- [ ] Read the architecture doc (`juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md`) §0-§5 for the motivation and latency model.
- [ ] Skim §6 (reconnect protocol), §7 (GAP-WS-NN list), §9 (phase plan), §10 (risks).
- [ ] Read R0-01 §3.2 (Option B drain pattern), R0-02 §4.1/§4.2 (Origin + CSRF), R0-03 §3 (replay buffer), R0-04 §4 (SDK set_params), R0-05 §4 (test plan), R0-06 §3 (phase ordering).
- [ ] If a project-local runbook conflicts with this doc, this runbook wins for tactical steps but the project-local doc wins for tooling paths.

### 0.2 Confirm repo state

Run these in parallel from any working directory:

```bash
# Main branches clean?
cd /home/pcalnon/Development/python/Juniper/juniper-cascor            && git status
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client     && git status
cd /home/pcalnon/Development/python/Juniper/juniper-canopy            && git status
cd /home/pcalnon/Development/python/Juniper/juniper-ml                && git status
```

- [ ] All four repos report `working tree clean` on `main`.
- [ ] All four repos have `git pull --ff-only origin main` up to date.
- [ ] Record the HEAD SHAs in a scratch note; you will reference them in PR descriptions for rebase tracking.

### 0.3 Conda environments

```bash
conda env list | grep -E 'JuniperCascor|JuniperCanopy|JuniperData'
```

- [ ] `JuniperCascor`, `JuniperCanopy`, `JuniperData` all present.
- [ ] `conda activate JuniperCanopy && python -c 'import dash, plotly; print(dash.__version__, plotly.__version__)'` — record for FR-RISK-03 (Plotly 2.x required for `extendTraces(maxPoints)`).
- [ ] `conda activate JuniperCanopy && python -c 'import pytest_playwright; from dash.testing.application_runners import import_app' ` — `dash_duo` + Playwright available.
- [ ] `playwright install chromium` has been run at least once in this env.

### 0.4 Baseline test runs (green before you start)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor        && bash src/tests/scripts/run_tests.bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client && pytest tests/ -q
cd /home/pcalnon/Development/python/Juniper/juniper-canopy        && pytest src/tests -q
```

- [ ] All three suites green. If anything is red on main, fix or file an issue before starting — do NOT carry a pre-existing failure into a phase PR.

### 0.5 Worktree policy

Per `Juniper/CLAUDE.md`, every day's work uses a git worktree under `/home/pcalnon/Development/python/Juniper/worktrees/`. The naming convention is `<repo>--<branch>--<YYYYMMDD-HHMM>--<shorthash>`. Commands below will show the exact `git worktree add` invocation for each day.

### 0.6 Cross-repo coordination reminder

The merge order is **non-negotiable** (from R0-06 §8.1):

```
cascor-client Phase A  (PyPI publish, wait 2-5 min)
        ↓
cascor Phase A-server + Phase B-pre          ─┐
                                              │ merge in this order
cascor Phase B (seq + replay buffer)         ─┤
                                              │
canopy Phase B-pre (security)                ─┤
                                              │
canopy Phase B (browser bridge + I + F)     ─┤
                                              │
canopy Phase C (adapter + flag off)         ─┤
                                              │
canopy Phase D (control buttons)            ─┘   ← blocked until B-pre green in prod
```

Use GitHub merge queue where available.

### 0.7 Disagreements carried forward from R0 inputs

Before starting Day 1, acknowledge these resolved-by-this-runbook tactical choices (see §14 for full list):

- **rAF coalescer shipped disabled** in Phase B per R0-01 disagreement #1.
- **`set_params` timeout default 1.0s** per R0-04 disagreement #12.1.
- **Phase B-pre effort 1.5-2 days**, not 1 day per R0-02 disagreement #9.1.
- **Origin allowlist defaults to concrete list**, not empty, per R0-02 disagreement #9.3.
- **Phase A-server carved out** from Phase B per R0-03 §7.1 so canopy has a stable server contract to iterate against.

---

## 1. Day 1 — Phase A: juniper-cascor-client `set_params` SDK method

**Goal**: land the additive WebSocket `set_params` method on `CascorControlStream`, refactor to a single background recv task with per-request correlation, ship to PyPI.
**Source**: R0-04 §4, §9.1; arch doc §9.1.
**Repo**: `juniper-cascor-client`.
**Estimated hours**: 6-8.

### 1.1 Pre-flight checklist

- [ ] `git -C /home/pcalnon/Development/python/Juniper/juniper-cascor-client status` → clean.
- [ ] `git -C /home/pcalnon/Development/python/Juniper/juniper-cascor-client fetch origin main && git -C /home/pcalnon/Development/python/Juniper/juniper-cascor-client log --oneline -5 origin/main` — record top SHA as `BASE_SHA_A`.
- [ ] `pypi.org/project/juniper-cascor-client` tab open — know the current published version.

### 1.2 Branch and worktree

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
git fetch origin main
WT_NAME="juniper-cascor-client--ws-migration--phase-a-set-params--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add \
    "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}" \
    -b ws-migration/phase-a-set-params \
    origin/main
cd "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}"
```

- [ ] `git branch --show-current` prints `ws-migration/phase-a-set-params`.

### 1.3 Edits

**File: `juniper_cascor_client/ws_client.py`** (see R0-04 §4.5 for the full shape)

- [ ] Add instance attrs to `CascorControlStream.__init__`:
  - `self._pending: Dict[str, asyncio.Future[Dict[str, Any]]] = {}`
  - `self._recv_task: Optional[asyncio.Task] = None`
  - `self._recv_lock = asyncio.Lock()` (for future-proofing)
- [ ] In `connect()`, after the existing handshake, start `self._recv_task = asyncio.create_task(self._recv_loop())`.
- [ ] Implement `_recv_loop()`:
  - Loop `await self._ws.recv()`, parse JSON, read `data.request_id`, pop future, `future.set_result(envelope)`.
  - Wrap entire loop in `try/except Exception`: on unhandled exception log ERROR, then `set_exception(JuniperCascorClientError("recv task crashed: ..."))` on every pending future (see R0-04 R04-06).
- [ ] In `disconnect()`, cancel `_recv_task`, drain `_pending` with `set_exception(JuniperCascorConnectionError("disconnected"))`.
- [ ] Add `async def set_params(self, params, *, timeout=1.0, request_id=None)` with the docstring from R0-04 §4.1 and the flow from R0-04 §4.5 (register future → send frame → `wait_for` → pop on all paths).
- [ ] In the final `except asyncio.TimeoutError`, raise `JuniperCascorTimeoutError(f"set_params ack not received within {timeout}s")` and ALWAYS `self._pending.pop(request_id, None)` in `finally`.
- [ ] Preserve the existing generic `command()` method — internally route through the same correlation map (generate `request_id` if caller omitted).
- [ ] Add latency stash `envelope["_client_latency_ms"] = (t_acked - t_sent) * 1000` using `time.monotonic()` before `return`.

**File: `juniper_cascor_client/constants.py`**

- [ ] Add `WS_MSG_TYPE_COMMAND_RESPONSE = "command_response"` if not already present.

**File: `juniper_cascor_client/testing/fake_ws_client.py`** (per R0-05 §3.3 minimal extensions)

- [ ] Add `on_command(name, handler)` method that registers per-command reply handlers.
- [ ] Auto-scaffold a `command_response` reply when the fake receives `start/stop/pause/resume/set_params` and no override handler is registered.
- [ ] Do NOT enable any other optional mode (`with_seq`, `enforce_api_key`, etc.) yet — those land with later phases.

**File: `tests/test_ws_client_set_params.py`** (new)

- [ ] Add the six tests from arch doc §9.1 + R0-04 §10.1 A1-A9 / R0-05 §4.2:
  - `test_set_params_round_trip`
  - `test_set_params_timeout`
  - `test_set_params_validation_error`
  - `test_set_params_reconnection_queue`
  - `test_set_params_concurrent_correlation`
  - `test_set_params_caller_cancellation`
  - `test_command_legacy_still_works` (regression gate)
  - `test_set_params_no_request_id_first_match_wins` (transition window)

**File: `CHANGELOG.md`**

- [ ] Add under `### Added`: `CascorControlStream.set_params(params, timeout=1.0, request_id=None) — WebSocket parameter update (GAP-WS-01). Additive; does not deprecate REST update_params.`
- [ ] Add under `### Changed`: `CascorControlStream now uses a background recv task with per-request correlation (additive — existing command() API unchanged).`

**File: `pyproject.toml`**

- [ ] Bump version minor: `X.Y.Z → X.(Y+1).0`.

### 1.4 Tests

- [ ] `pytest tests/test_ws_client_set_params.py -v` → all 8 tests green.
- [ ] `pytest tests/ -q` → full suite green (regression gate).
- [ ] `pytest tests/ --cov=juniper_cascor_client --cov-report=term-missing` → new SDK code ≥ 90% line coverage (R0-05 §9.1).
- [ ] `ruff check .` / `black --check .` / `isort --check .` per repo's linters.

### 1.5 Commit and PR

- [ ] `git add -A && git status` → review file list, drop any accidental edits.
- [ ] Commit with:
  ```
  feat(ws-client): add CascorControlStream.set_params (GAP-WS-01)

  Adds an async set_params(params, *, timeout=1.0, request_id=None) method
  to the WebSocket control stream. Refactors the recv path to a background
  task + per-request correlation map so multiple set_params calls can be
  in flight concurrently. Existing command() API unchanged.

  Closes GAP-WS-01.
  ```
- [ ] `git push -u origin ws-migration/phase-a-set-params`.
- [ ] `gh pr create --title 'feat(ws-client): add CascorControlStream.set_params (GAP-WS-01)' --body "$(cat <<'EOF'
## Summary
- Adds WebSocket set_params method to CascorControlStream with per-request correlation
- Refactors recv path to background task; existing command() API preserved
- Ships with the 8 unit tests from arch doc §9.1 + regression gate

## Test plan
- [x] pytest tests/test_ws_client_set_params.py green
- [x] pytest tests/ green (regression)
- [x] coverage ≥ 90% on new code
- [ ] PyPI publish after merge
EOF
)"`
- [ ] Monitor CI (`gh pr checks --watch`).

### 1.6 Post-merge verification

- [ ] PR merges to `main`; tag is created automatically (or manually via `git tag vX.Y.0 && git push --tags`).
- [ ] GitHub release workflow publishes to PyPI. Wait 2-5 minutes for index propagation.
- [ ] Verify from another shell: `pip index versions juniper-cascor-client | head -1` shows the new version.
- [ ] Record the new version as `SDK_VERSION_A` for Day 10 dep pin bump.

### 1.7 Rollback

If a P0 regression is found post-merge:

```bash
# Revert the merge commit (NOT amend — create a new commit per user's git policy)
gh pr create --title 'revert: phase A set_params (regression <issue#>)' \
  --body 'Reverts PR #<n>; SDK callers should pin juniper-cascor-client==<previous-version>'
```

- [ ] Yank the PyPI release ONLY if the regression is "installs but will not import" — otherwise leave it up and publish a fix-forward patch. Yanking is destructive per PEP 592; prefer fix-forward.

---

## 2. Day 2 — Phase A-server (cascor): seq field + replay buffer skeleton

**Goal**: ship commits 1-4 of R0-03 §7.1 — add `seq` field plumbing, replay buffer, 0.5s send timeout, `replay_since()` primitive. **No training_stream.py wiring yet.**
**Source**: R0-03 §3, §5.2, §7.1 (commits 1-4).
**Repo**: `juniper-cascor`.
**Estimated hours**: 6-8.

### 2.1 Pre-flight checklist

- [ ] cascor `main` is clean and pulled.
- [ ] `BASE_SHA_A_SERVER = $(git -C /home/pcalnon/Development/python/Juniper/juniper-cascor rev-parse origin/main)`.
- [ ] Phase A SDK PR (Day 1) is **not** a dependency for this day — cascor has no cascor-client import. These can run in parallel.

### 2.2 Branch and worktree

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin main
WT_NAME="juniper-cascor--ws-migration--phase-a-server-seq--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add \
    "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}" \
    -b ws-migration/phase-a-server-seq \
    origin/main
cd "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}"
conda activate JuniperCascor
```

### 2.3 Edits

**Commit 1 — `src/api/websocket/messages.py`**

- [ ] Add optional `seq: int | None = None` parameter to every message builder function.
- [ ] `seq` serializes as a top-level field when present; omitted when `None` (backward compat).
- [ ] Update any builder signature tests to cover the new parameter.

**Commit 2 — `src/api/websocket/manager.py`** (the main WebSocketManager work)

- [ ] Add imports: `uuid`, `time`, `collections.deque`, `contextlib`.
- [ ] Add new instance attrs in `__init__`:
  ```python
  self._seq_lock = asyncio.Lock()
  self._next_seq: int = 0
  self._replay_buffer: deque[tuple[int, dict]] = deque(maxlen=replay_buffer_size)
  self.server_instance_id: str = str(uuid.uuid4())
  self.server_start_time: float = time.time()
  ```
- [ ] Add `replay_buffer_size: int = 1024` as constructor param; wire through from `Settings.ws_replay_buffer_size`.
- [ ] Add `_pending_connections: Set[WebSocket] = set()` for the two-phase registration (actual promotion logic lands in Day 3, but the set lives on the manager from here).
- [ ] Implement `async def _assign_seq_and_append(self, message: dict) -> dict` per R0-03 §3.2 (hold `_seq_lock`, assign seq, append to deque, mutate-in-place).
- [ ] Route `broadcast()` and `broadcast_from_thread()` through `_assign_seq_and_append` **before** iterating `_active_connections`.
- [ ] Update `connect()` to include `server_instance_id`, `server_start_time`, `replay_buffer_capacity` in the personal `connection_established` frame (this frame is sent via `send_personal_message`, bypassing the replay buffer).
- [ ] Add a DEBUG-gated assertion `assert "seq" in message` at the entry to the live fan-out loop (R0-03 §3.2 invariant).

**Commit 3 — `src/api/websocket/manager.py` `_send_json` timeout (RISK-04 quick fix)**

- [ ] Wrap the existing `await websocket.send_json(message)` call in `asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds)`.
- [ ] Default `ws_send_timeout_seconds = 0.5` in `Settings`.
- [ ] On `asyncio.TimeoutError` / `WebSocketDisconnect`, log INFO and return `False` so the caller prunes.

**Commit 4 — `src/api/websocket/manager.py` `replay_since()`**

- [ ] Implement `async def replay_since(self, last_seq: int) -> list[dict]` per R0-03 §3.3 (copy-under-lock pattern).
- [ ] Add `class ReplayOutOfRange(Exception)` with `requested` and `oldest_available` attrs.
- [ ] `replay_since` raises `ReplayOutOfRange` if `last_seq < oldest_seq - 1`.
- [ ] `last_seq >= newest_seq` returns `[]`.
- [ ] `last_seq == oldest_seq - 1` returns the full buffer (boundary case).

**File: `src/config/settings.py`**

- [ ] Add `ws_replay_buffer_size: int = Field(default=1024, ge=256, le=16384)`.
- [ ] Add `ws_send_timeout_seconds: float = Field(default=0.5, gt=0.0, le=5.0)`.

**File: `src/tests/unit/api/test_websocket_replay_buffer.py`** (new)

Add tests from R0-05 §4.1 "Phase B (sequence numbers + replay buffer)":
- [ ] `test_seq_monotonically_increases_per_connection`
- [ ] `test_seq_increments_across_all_message_types`
- [ ] `test_seq_assigned_on_loop_thread` (using `broadcast_from_thread`)
- [ ] `test_seq_lock_does_not_block_broadcast_iteration` (R0-03 §3.2 Option 2 validation)
- [ ] `test_replay_buffer_bounded_1024`
- [ ] `test_replay_buffer_copy_under_lock`
- [ ] `test_replay_since_happy_path` — broadcast 50, `replay_since(10)` returns 39
- [ ] `test_replay_since_out_of_range` — broadcast 2000, `replay_since(10)` raises
- [ ] `test_replay_since_empty` — `replay_since(50)` returns `[]`
- [ ] `test_replay_since_boundary_oldest_minus_one`

**File: `src/tests/unit/api/test_websocket_manager.py`** (extend)

- [ ] `test_connection_established_advertises_server_instance_id`
- [ ] `test_connection_established_advertises_replay_buffer_capacity`
- [ ] `test_send_json_0_5s_timeout` — with a `asyncio.Future` that never resolves, `_send_json` returns False in ~0.5s.
- [ ] `test_broadcast_from_thread_exception_does_not_leak_seq` (GAP-WS-29).

### 2.4 Tests

- [ ] `pytest src/tests/unit/api/test_websocket_replay_buffer.py -v` → green.
- [ ] `pytest src/tests/unit/api/test_websocket_manager.py -v` → green.
- [ ] `bash src/tests/scripts/run_tests.bash` → full cascor suite green.
- [ ] `pytest src/tests/unit/api/ --cov=src/api/websocket --cov-report=term-missing` → new paths covered.

### 2.5 Commit and PR

- [ ] Split into **4 separate commits** (one per R0-03 commit 1-4) for reviewability. Each commit must be green independently — verify by cherry-picking:
  - `git checkout --detach origin/main && git cherry-pick <c1> && pytest ... && git cherry-pick <c2> && pytest ...`
- [ ] Messages:
  - `feat(ws): add optional seq field to message builders`
  - `feat(ws): add replay buffer, server_instance_id, _assign_seq_and_append (GAP-WS-13 scaffolding)`
  - `fix(ws): wrap _send_json in 0.5s timeout (GAP-WS-07 quick fix, RISK-04)`
  - `feat(ws): add WebSocketManager.replay_since + ReplayOutOfRange (GAP-WS-13)`
- [ ] Push `ws-migration/phase-a-server-seq`.
- [ ] Open PR titled `feat(ws): Phase A-server scaffolding (seq, replay buffer, send timeout)`.
- [ ] PR body cross-references GAP-WS-13, GAP-WS-07, GAP-WS-29, RISK-04.

### 2.6 Post-merge verification

- [ ] CI green on cascor main.
- [ ] Deploy to local dev cascor (`conda activate JuniperCascor && python -m juniper_cascor.main`) and verify via curl:
  ```bash
  curl -s http://localhost:8201/v1/health | jq
  # WebSocket handshake includes connection_established with server_instance_id
  ```
- [ ] Record new `WebSocketManager.server_instance_id` length (should be 36-char UUID).

### 2.7 Rollback

- [ ] The 4 commits are independently revertable. If commit 3 (send timeout) is problematic, `git revert <sha>` that single commit — the replay buffer and seq work stay.
- [ ] No runtime config flag yet (commits are additive; no behavior change until Day 3 wires the handler).

---

## 3. Day 3 — Phase A-server (cascor): training_stream resume handler + state coalescer + protocol errors

**Goal**: ship commits 5-9 of R0-03 §7.1 — two-phase registration, resume handler, `/api/v1/training/status` snapshot_seq, state throttle coalescer, `broadcast_from_thread` exception logging, `/ws/control` protocol error responses.
**Source**: R0-03 §5.1, §6.1, §6.2, §6.3, §7.1 (commits 5-9).
**Repo**: `juniper-cascor`.
**Estimated hours**: 6-8.

### 3.1 Pre-flight checklist

- [ ] Day 2 PR merged to cascor main.
- [ ] Local dev cascor restarts cleanly with the new manager attrs.
- [ ] `ReplayOutOfRange` is importable from `src.api.websocket.manager`.

### 3.2 Branch and worktree

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin main
WT_NAME="juniper-cascor--ws-migration--phase-a-server-handlers--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add \
    "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}" \
    -b ws-migration/phase-a-server-handlers \
    origin/main
cd "/home/pcalnon/Development/python/Juniper/worktrees/${WT_NAME}"
```

### 3.3 Edits

**Commit 5 — `src/api/websocket/manager.py` two-phase registration helpers**

- [ ] Add `async def connect_pending(self, ws: WebSocket) -> bool` — accepts, sends `connection_established`, adds to `_pending_connections` (NOT `_active_connections`).
- [ ] Add `async def promote_to_active(self, ws: WebSocket) -> None` — atomic move from pending to active under `_seq_lock` (per R0-03 §8.4 lock strategy).
- [ ] Ensure `disconnect()` removes from BOTH sets.

**Commit 5 — `src/api/websocket/training_stream.py` resume handler**

- [ ] Rewrite the handler per the full flow in R0-03 §6.1:
  1. `ws_authenticate` (existing; untouched by this commit — Day 4 adds Origin).
  2. `manager.connect_pending(ws)`.
  3. `asyncio.wait_for(ws.receive_json(), timeout=5.0)` for an optional resume frame.
  4. Branch on `first_frame.get("type")`:
     - `"resume"` → check `server_instance_id`, call `replay_since()`, emit `resume_ok` + replayed messages OR `resume_failed` (server_restarted / out_of_range / malformed_resume).
     - Anything else → route through normal handler as if it had arrived in the main loop.
     - Timeout → treat as fresh client.
  5. `manager.promote_to_active(ws)`.
  6. `send_personal_message(initial_status)`.
  7. Main inbound loop with `handle_training_inbound` dispatcher.
- [ ] `handle_training_inbound` handles `ping` → `pong`, rejects unknown types with `{"type": "error", "data": {"error": "unexpected message type"}}` — does NOT close.
- [ ] Document the initial_status race in a code comment (R0-03 §6.1 "initial_status race").

**Commit 6 — `src/api/training/router.py` (or equivalent) `snapshot_seq` on status endpoint**

- [ ] One-line change: in `/api/v1/training/status` handler, add `async with manager._seq_lock: payload["snapshot_seq"] = manager._next_seq - 1` and `payload["server_instance_id"] = manager.server_instance_id`.

**Commit 7 — `src/lifecycle/manager.py:133-136` state throttle → debounced coalescer (GAP-WS-21)**

- [ ] Replace the drop filter with a coalescer per R0-03 §7.1 commit 7:
  - Buffer latest pending state.
  - Flush at most once per second.
  - Bypass throttle for terminal transitions (`Failed`, `Stopped`, `Completed`).
  - Schedule flush via asyncio call_later or thread-safe bridge.

**Commit 8 — `src/api/websocket/manager.py` `broadcast_from_thread` exception handling (GAP-WS-29)**

- [ ] Attach a `done_callback` to the scheduled future that logs any exception at ERROR.
- [ ] Wrap the scheduled coroutine body in `try/finally` that closes the coroutine on failure paths.

**Commit 9 — `src/api/websocket/control_stream.py` protocol error responses (GAP-WS-22)**

- [ ] Wrap `ws.receive_json()` in `try/except json.JSONDecodeError: close(1003)`.
- [ ] Reject missing `command` field with `{status: "error", error: "missing command field"}` (no close).
- [ ] Existing unknown-command handling retained; add traceback log for handler exceptions.
- [ ] Frame > 64 KB already framework-level; add a unit test anyway.

**File: `src/tests/unit/api/test_websocket_control.py`** (extend)

- [ ] `test_resume_replays_events_after_last_seq`
- [ ] `test_resume_failed_out_of_range`
- [ ] `test_resume_failed_server_restarted`
- [ ] `test_resume_missing_fields_malformed`
- [ ] `test_first_frame_not_resume_is_treated_as_fresh`
- [ ] `test_snapshot_seq_atomic_with_state_read`
- [ ] `test_state_coalescer_passes_terminal_transitions`
- [ ] `test_state_coalescer_buffers_non_terminal`
- [ ] `test_control_stream_malformed_json_closes_1003`
- [ ] `test_control_stream_missing_command_field_error_response`

### 3.4 Tests

- [ ] `pytest src/tests/unit/api/ -v` → green.
- [ ] `pytest src/tests/unit/lifecycle/ -v` → state coalescer tests green.
- [ ] `bash src/tests/scripts/run_tests.bash` → full suite green.

### 3.5 Commit and PR

- [ ] 5 commits (one per R0-03 commit 5-9). Each independently green.
- [ ] Open PR `feat(ws): Phase A-server handlers (resume, snapshot_seq, coalescer, protocol errors)`.
- [ ] Cross-reference GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29.

### 3.6 Post-merge verification

- [ ] Smoke test against local dev cascor:
  ```bash
  python -c "
  import asyncio, websockets, json
  async def main():
      async with websockets.connect('ws://localhost:8201/ws/training') as ws:
          frame = json.loads(await ws.recv())
          assert frame['type'] == 'connection_established'
          assert 'server_instance_id' in frame['data']
          assert 'replay_buffer_capacity' in frame['data']
          await ws.send(json.dumps({'type': 'resume', 'data': {'last_seq': 0, 'server_instance_id': frame['data']['server_instance_id']}}))
          resp = json.loads(await ws.recv())
          assert resp['type'] in ('resume_ok', 'resume_failed')
          print('OK:', resp)
  asyncio.run(main())
  "
  ```

### 3.7 Rollback

- [ ] Each commit is revertable. Commit 7 (state coalescer) is the most behaviorally-impactful; if it causes state-event regressions, revert it alone.
- [ ] Resume handler can be bypassed by clients not sending `type: "resume"` as the first frame. Existing clients (which do not know about resume) continue working.

---

## 4. Day 4 — Phase B-pre (cascor + canopy): Origin allowlist

**Goal**: land M-SEC-01 (canopy) + M-SEC-01b (cascor parity) Origin validation with shared helper. This is the first of **three** days of Phase B-pre work.
**Source**: R0-02 §4.1, §6.1, §6.3, §7.1; arch doc §2.9.2.
**Repos**: `juniper-cascor` + `juniper-canopy`.
**Estimated hours**: 6-8.

### 4.1 Pre-flight checklist

- [ ] Day 3 cascor PR merged.
- [ ] Phase B-pre effort estimate is 1.5-2 days per R0-02 §9.1 — this is day 1 of 2-3.
- [ ] Two worktrees will be opened today, one per repo.

### 4.2 Branch and worktrees

```bash
# cascor side
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin main
WT_CASCOR="juniper-cascor--ws-migration--phase-b-pre-origin--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add \
    "/home/pcalnon/Development/python/Juniper/worktrees/${WT_CASCOR}" \
    -b ws-migration/phase-b-pre-origin \
    origin/main

# canopy side
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git fetch origin main
WT_CANOPY="juniper-canopy--ws-migration--phase-b-pre-origin--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add \
    "/home/pcalnon/Development/python/Juniper/worktrees/${WT_CANOPY}" \
    -b ws-migration/phase-b-pre-origin \
    origin/main
```

### 4.3 Edits — cascor

**IMPL-SEC-01 / IMPL-SEC-02 — `src/api/websocket/origin.py` (new)**

- [ ] Extract the existing `worker_stream.py:41-44` pattern into `validate_origin(ws, allowlist) -> bool`.
- [ ] Rules from R0-02 §4.1:
  - Case-insensitive on scheme + host, exact on port.
  - Strip trailing slash before compare.
  - `null` origin always rejected.
  - `*` in allowlist NOT supported.
- [ ] Pre-accept `HTTPException(403)` path preferred; fallback to `ws.accept(); ws.close(code=1008)` with opaque reason `"Authentication failed"` (M-SEC-06).

**IMPL-SEC-02 — `src/tests/unit/api/test_websocket_origin.py` (new)**

- [ ] Matrix: exact match / case-insensitive host / trailing slash / null origin / port mismatch / scheme mismatch / wildcard rejection / empty allowlist = reject all.

**IMPL-SEC-03 / IMPL-SEC-04 — wire into handlers**

- [ ] Call `validate_origin` at the entry of `training_stream_handler` and `control_stream_handler` in `src/api/app.py:338-339` (or wherever the handlers are wired).
- [ ] Add `Settings.ws_allowed_origins: list[str] = [...]` with the R0-02 §4.1 default list (both http and https localhost + 127.0.0.1 + port 8050 + port 8201).
- [ ] Env var `JUNIPER_WS_ALLOWED_ORIGINS` (semicolon-separated or JSON).

### 4.4 Edits — canopy

**IMPL-SEC-10 — `src/backend/ws_security.py` (new module)**

- [ ] Copy the cascor `validate_origin` helper (do NOT cross-import — cascor is not a canopy dependency).
- [ ] Unit-tested in `src/tests/unit/test_ws_security_origin.py` with the same matrix.

**IMPL-SEC-11 — wire into `src/main.py`**

- [ ] At `/ws/training` and `/ws/control` route handlers, call `validate_origin(ws, settings.allowed_origins)` BEFORE `await ws.accept()`.
- [ ] On reject: raise `HTTPException(403)` pre-accept.
- [ ] Log at WARNING with `{origin, remote_addr, path, user_agent}` (CRLF-escaped per §4.6 rule 10 — save full escaping for Day 6 when audit logger lands).

**IMPL-SEC-12 — `src/config/settings.py`**

- [ ] Add `allowed_origins: list[str] = Field(default=["http://localhost:8050", "http://127.0.0.1:8050", "https://localhost:8050", "https://127.0.0.1:8050"])`.
- [ ] Env var `JUNIPER_WS_ALLOWED_ORIGINS`.

**Tests — `src/tests/security/test_ws_security.py` (new)**

- [ ] `test_origin_validation_rejects_third_party_pages` (M-SEC-01).
- [ ] `test_origin_validation_accepts_whitelisted_origins`.
- [ ] `test_missing_origin_header_rejected`.
- [ ] `test_origin_case_sensitivity_scheme_host_port`.

### 4.5 Tests

- [ ] cascor: `pytest src/tests/unit/api/test_websocket_origin.py -v` → green.
- [ ] cascor: `bash src/tests/scripts/run_tests.bash` → full cascor suite green.
- [ ] canopy: `pytest src/tests/unit/test_ws_security_origin.py src/tests/security/test_ws_security.py -v` → green.
- [ ] canopy: `pytest src/tests/ -q` → full canopy suite green.

### 4.6 Commit and PR

**cascor PR:**
- [ ] Commit: `feat(ws-security): add Origin allowlist to training/control streams (M-SEC-01b)`.
- [ ] Push + `gh pr create --title 'feat(ws-security): Origin allowlist parity (M-SEC-01b)'`.

**canopy PR:**
- [ ] Commit: `feat(ws-security): add Origin allowlist to /ws/training and /ws/control (M-SEC-01)`.
- [ ] Push + `gh pr create --title 'feat(ws-security): Origin validation (M-SEC-01)'`.

**Coordination**: merge cascor PR first (no dependency order strictly required, but cascor-first matches §8.1 of R0-06).

### 4.7 Post-merge verification

- [ ] Restart both services locally.
- [ ] From a non-allowlisted "origin" (use `curl` with `--header "Origin: http://evil.example"` to `/ws/control`): assert HTTP 403.
- [ ] From allowlisted origin: handshake succeeds.
- [ ] Log line with rejected origin visible in canopy's WARNING log.

### 4.8 Rollback

- [ ] `Settings.allowed_origins=["*"]` is NOT supported (by design). Rollback is `JUNIPER_WS_ALLOWED_ORIGINS` set to a superset that includes the problem origin.
- [ ] Full code revert: revert the PRs. The dashboard goes back to "no Origin check."

---

## 5. Day 5 — Phase B-pre (canopy): cookie session + CSRF first-frame + per-frame size caps

**Goal**: land M-SEC-02 (cookie session + CSRF) + M-SEC-03 (size caps) on canopy, plus IMPL-SEC-43 (`close_all()` lock fix) if not already on main.
**Source**: R0-02 §4.2, §4.4, §6.4, §6.5, §8.12; arch doc §2.9.2.
**Repos**: `juniper-canopy` (primarily), `juniper-cascor` (size caps).
**Estimated hours**: 7-9. This is day 2 of 2-3 for Phase B-pre.

### 5.1 Pre-flight checklist

- [ ] Day 4 Origin PRs merged and verified in dev.
- [ ] Check whether canopy already uses `starlette.middleware.sessions.SessionMiddleware`: `grep -R 'SessionMiddleware' src/`. If yes, IMPL-SEC-14 is a no-op.
- [ ] Check whether `src/main.py` has a session secret env var.

### 5.2 Branch and worktrees

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git fetch origin main
WT="juniper-canopy--ws-migration--phase-b-pre-auth--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-b-pre-auth origin/main
```

Open a parallel cascor worktree if the size-cap changes need to land in cascor too (they do — IMPL-SEC-19..23).

### 5.3 Edits — canopy

**IMPL-SEC-14 — SessionMiddleware**

- [ ] If not present, add to `src/main.py`:
  ```python
  from starlette.middleware.sessions import SessionMiddleware
  app.add_middleware(
      SessionMiddleware,
      secret_key=settings.session_secret_key,
      https_only=False,  # auto-detect from X-Forwarded-Proto later
      same_site="strict",
      path="/",
  )
  ```
- [ ] Add `session_secret_key: SecretStr` to settings; load from `JUNIPER_CANOPY_SESSION_SECRET`.
- [ ] On startup, if the secret is blank, log CRITICAL and refuse to start in production (`ws_security_enabled=True`).

**IMPL-SEC-15 — `/api/csrf` endpoint**

- [ ] `@app.get("/api/csrf")` returns `{"csrf_token": request.session.get("csrf_token") or mint_new()}`.
- [ ] Mint-on-first-request: `request.session["csrf_token"] = secrets.token_urlsafe(32)`.
- [ ] Rotate on every hour of sliding activity (store `csrf_minted_at` alongside).
- [ ] Use `hmac.compare_digest` for all compares — document in code comment.

**IMPL-SEC-16 — CSRF first-frame check on `/ws/training` + `/ws/control`**

- [ ] After `ws.accept()` (and after Origin check), call:
  ```python
  try:
      first = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
  except asyncio.TimeoutError:
      await ws.close(code=4001, reason="Authentication failed")
      return
  if first.get("type") != "auth" or not hmac.compare_digest(
      first.get("csrf_token", ""),
      session_csrf_token,
  ):
      await ws.close(code=4001, reason="Authentication failed")
      return
  ```
- [ ] After successful auth, continue to the existing handler (which on `/ws/training` becomes the resume-frame path from Day 3's cascor work; canopy relays this to cascor as a separate adapter connection — see §4.7 of R0-02 for the sequence).

**IMPL-SEC-17 — Dash page template CSRF injection**

- [ ] In the canopy Dash layout initialization, inject `window.__canopy_csrf = "<token>"` as a `<script>` tag. **Do NOT store in localStorage** (XSS-exfiltratable).
- [ ] Template render-time embedding avoids a `/api/csrf` round-trip on first load (R0-02 §8.2 mitigation).

**IMPL-SEC-18 — `websocket_client.js` auth frame**

- [ ] In `assets/websocket_client.js`, after `onopen`, read `window.__canopy_csrf` and send `{"type": "auth", "csrf_token": "..."}` immediately.
- [ ] Continue with normal subscription after the auth frame is accepted (no explicit ack from server in the frame-level protocol; the absence of `4001` close is the implicit ack).

**IMPL-SEC-19..22 — per-frame size caps (canopy)**

- [ ] Audit every `ws.receive_*()` call in `src/main.py`. Add `max_size` per R0-02 §4.4 control 1 table:
  - `/ws/training` inbound → 4 KB
  - `/ws/control` inbound → 64 KB
  - (outbound → 128 KB — defer to Day 11 when needed for GAP-WS-18 topology chunking)

**IMPL-SEC-43 — `close_all()` lock fix (GAP-WS-19)**

- [ ] If `WebSocketManager.close_all()` in cascor does NOT already hold `self._lock` (R0-03 §11 says it does on main, but verify), wrap the body in `async with self._lock:`.

### 5.4 Edits — cascor (size caps + auth adapter acceptance)

**IMPL-SEC-20..23 — per-frame size caps (cascor)**

- [ ] `training_stream.py` → `max_size=4096` on receive.
- [ ] `control_stream.py` → keep 64 KB cap (regression test).

**IMPL-SEC-38 — synthetic adapter auth frame (open question — R0-02 §11 Q2-sec)**

- [ ] **Punt for today**. R0-02 flags this as a decision-gate item. This runbook's position: the canopy adapter sends `{"type": "auth", "csrf_token": "<hmac-of-api-key>"}` synthetically when connecting to cascor, avoiding the `X-Juniper-Role: adapter` branch. Document as TODO in the adapter and do not block Day 5 on it.

### 5.5 Tests

**canopy**
- [ ] `src/tests/unit/test_ws_security_auth.py` (new):
  - `test_first_frame_must_be_auth_type`
  - `test_csrf_token_validates_against_session`
  - `test_csrf_token_uses_hmac_compare_digest` (patch `hmac.compare_digest` to assert it was called)
  - `test_session_cookie_httponly_secure_samesitestrict`
  - `test_localStorage_bearer_token_not_accepted`
- [ ] `src/tests/unit/test_ws_security_size_limits.py`:
  - `test_oversized_frame_rejected_with_1009` per endpoint
- [ ] `src/tests/integration/test_ws_security_cswsh.py` (Playwright):
  - `test_cswsh_from_evil_page_cannot_start_training` (the full CSWSH regression)

**cascor**
- [ ] `src/tests/unit/api/test_websocket_size_limits.py` — 1-byte-over-cap test per endpoint.

### 5.6 Commit and PR

- [ ] canopy commit series:
  - `feat(ws-security): SessionMiddleware + /api/csrf endpoint (M-SEC-02 part 1)`
  - `feat(ws-security): CSRF first-frame check on /ws/training and /ws/control (M-SEC-02 part 2)`
  - `feat(ws-security): per-frame size caps (M-SEC-03)`
  - `feat(ws-security): inject CSRF token into Dash template; websocket_client.js auth frame`
- [ ] cascor commit: `feat(ws-security): add per-frame size caps on training_stream and assert control_stream cap (M-SEC-03)`
- [ ] Both PRs reference the same Phase B-pre tracking issue.

### 5.7 Post-merge verification

- [ ] Local dev stack:
  - Start canopy; open dashboard; confirm WebSocket connects, no console errors.
  - `curl -i -H "Origin: http://localhost:8050" http://localhost:8050/api/csrf` returns `{"csrf_token": "..."}` and sets a `SameSite=Strict HttpOnly` session cookie.
  - Drop the CSRF token (e.g., browser dev console `delete window.__canopy_csrf`) and reconnect: assert close code 4001 within 5 s.
- [ ] Check canopy startup log for the session-secret-missing CRITICAL.

### 5.8 Rollback

- [ ] Kill switch: `JUNIPER_CANOPY_WS_SECURITY_ENABLED=false` (or `JUNIPER_CANOPY_DISABLE_WS_AUTH=true` per R0-02 §9.4 naming debate). MUST log a loud CRITICAL at startup and the runbook MUST document "local dev only — never set in prod."
- [ ] Full revert: revert the Day 5 PRs. Origin check from Day 4 stays. The `/ws/control` is then Origin-protected only — CSWSH is still blocked but second-line defense is gone.

---

## 6. Day 6 — Phase B-pre finish: rate limit, idle timeout, audit logger, per-IP cap

**Goal**: complete Phase B-pre by landing M-SEC-04, M-SEC-05, M-SEC-10, and the audit logger. This is day 3 of 2-3. After today, Phase B-pre gate is green and Phase B can start.
**Source**: R0-02 §4.5, §4.6, §6.2, §6.7, §6.8, §7.1-7.4.
**Repo**: primarily `juniper-cascor` (per-IP cap and rate limit on WebSocketManager) + `juniper-canopy` (audit logger + idle timeout).
**Estimated hours**: 6-8.

### 6.1 Pre-flight checklist

- [ ] Day 5 CSRF + size caps merged.
- [ ] Full dev stack reboots cleanly with auth.
- [ ] `JUNIPER_CANOPY_WS_SECURITY_ENABLED=true` working in dev.

### 6.2 Branches

Two parallel branches, one per repo.

```bash
# cascor — per-IP cap + rate limit
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
WT_C="juniper-cascor--ws-migration--phase-b-pre-rate-cap--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT_C}" -b ws-migration/phase-b-pre-rate-cap origin/main

# canopy — audit logger + idle timeout
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
WT_K="juniper-canopy--ws-migration--phase-b-pre-audit--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT_K}" -b ws-migration/phase-b-pre-audit origin/main
```

### 6.3 Edits — cascor (per-IP cap + rate limit)

**IMPL-SEC-05..09 — per-IP cap**

- [ ] `WebSocketManager.__init__`: `self._per_ip_counts: Dict[str, int] = {}`, reuse `self._lock`.
- [ ] In `connect()`: before `accept()`, under `async with self._lock:` increment and check `ws_max_connections_per_ip` (default 5).
- [ ] In `disconnect()`: decrement in a `finally:` block.
- [ ] `test_per_ip_cap_enforced`: 6 connects from same IP, 6th rejected with 1013.
- [ ] `test_per_ip_counter_decrements_on_disconnect`: cycle 10 connect/disconnect pairs, final count == 0.
- [ ] `test_per_ip_counter_decrements_on_exception`: exception inside handler still decrements.
- [ ] `test_per_ip_map_purged_when_count_reaches_zero`.

**IMPL-SEC-29 — leaky-bucket rate limit**

- [ ] New `src/api/websocket/rate_limit.py` module: per-connection leaky bucket, capacity 10, refill 10/s.
- [ ] `control_stream_handler` consumes a token per command frame (per rules in R0-02 §4.5).
- [ ] On empty bucket: reply `{"type": "command_response", "data": {"status": "rate_limited", "retry_after": 0.3}}`; do NOT close.
- [ ] `test_command_rate_limit_10_per_sec`: 15 commands in 1 s, first 10 succeed, rest rate-limited.
- [ ] `test_rate_limit_response_is_not_an_error_close`.

**Bonus — one-resume-per-connection micro-control**

- [ ] In `training_stream.py` resume handler, record a connection-scoped `resumed_once: bool`. A second `resume` frame closes with 1003 per R0-02 §4.5 control 6.

### 6.4 Edits — canopy (audit logger + idle timeout + metrics)

**IMPL-SEC-32..35 — audit logger**

- [ ] New `src/backend/audit_log.py` module: `canopy.audit` logger with JSON formatter + `TimedRotatingFileHandler(when="midnight", backupCount=90)` + gzip compression.
- [ ] `AUDIT_SCRUB_ALLOWLIST = frozenset(SetParamsRequest.model_fields.keys())` auto-derived (Day 7 adds the schema).
- [ ] `audit_log.ws_control(event, ...)` wraps the JSON fields from R0-02 §4.6 rules 1-11: session_id hash, remote_addr, origin, endpoint, command, request_id, params_keys, params_scrubbed (before/after), result, seq.
- [ ] CRLF escape every user-controlled string field at write-time (rule 10).
- [ ] `audit_log.ws_auth(event, ...)` for auth success/failure/origin reject.
- [ ] Config: `Settings.audit_log_path`, `Settings.audit_log_retention_days`.

**Wire it in**
- [ ] Control stream handler calls `audit_log.ws_control(...)` on every inbound command.
- [ ] Auth/origin/cookie failures call `audit_log.ws_auth(...)`.

**IMPL-SEC-30 — idle timeout**

- [ ] Wrap the `receive_text()` main loop in `asyncio.wait_for(..., timeout=120)` per control and training stream handlers.
- [ ] On `asyncio.TimeoutError`, close with 1000 "Normal Closure".
- [ ] Heartbeat from Day 11 (Phase F) will reset the timer — safe for now because heartbeat ships later but idle timeout is defensible alone.

**IMPL-SEC-36 — Prometheus counters**

- [ ] Use `prometheus_client` if canopy already has it (check `pyproject.toml`); else add a minimal counter module.
- [ ] Counters from R0-02 §4.6: `canopy_ws_auth_failure_total{reason}`, `canopy_ws_command_total{command, status}`, `canopy_ws_rate_limited_total`, `canopy_ws_per_ip_rejected_total`, `canopy_ws_origin_rejected_total`, `canopy_ws_frame_too_large_total`.
- [ ] Histogram `canopy_ws_auth_latency_ms`.

**Tests**
- [ ] `src/tests/unit/test_audit_log.py`: scrubber redacts non-allowlist keys; logs are JSON-parseable; CRLF escaped.
- [ ] `src/tests/integration/test_ws_security_resume_rate.py`: one-resume-per-connection enforcement.
- [ ] `src/tests/unit/test_ws_security_idle_timeout.py`: connection closed with 1000 after 120 s of silence (use patched timeout).

### 6.5 Tests

- [ ] cascor: `pytest src/tests/unit/api/test_websocket_per_ip_cap.py src/tests/unit/api/test_websocket_rate_limit.py -v` → green.
- [ ] canopy: `pytest src/tests/unit/test_audit_log.py src/tests/integration/test_ws_security_resume_rate.py -v` → green.
- [ ] Phase B-pre gate — run the full Phase B-pre checklist from R0-02 §5.1 / §7.4:
  ```bash
  # cascor
  pytest src/tests/unit/api/ -k 'origin or size_limits or per_ip or rate_limit or control_security' -v
  # canopy
  pytest src/tests/security/ src/tests/unit/test_ws_security_*.py src/tests/integration/test_ws_security_*.py -v
  ```
- [ ] All 13 criteria from R0-02 §5.1-§5.2 pass.

### 6.6 Commit and PR

- [ ] cascor PR: `feat(ws-security): per-IP cap + command rate limit + resume frame rate limit (M-SEC-04, M-SEC-05)`.
- [ ] canopy PR: `feat(ws-security): audit logger + idle timeout + prom counters (M-SEC-07 extended, M-SEC-10)`.
- [ ] Both reference the same Phase B-pre closing issue.

### 6.7 Post-merge verification

- [ ] **Phase B-pre exit gate (R0-06 §3.2 items 1-8)**:
  - [ ] M-SEC-01 landed (Day 4).
  - [ ] M-SEC-01b landed (Day 4).
  - [ ] M-SEC-02 landed (Day 5).
  - [ ] M-SEC-03 landed (Day 5).
  - [ ] M-SEC-04 + M-SEC-05 + M-SEC-10 landed (Day 6).
  - [ ] Audit logger exporting counters.
  - [ ] Staging deployment ≥ 24h (this usually needs a calendar-day gap — schedule Day 7 to start at least 24h later if you're paranoid, or run Day 7 in parallel in a separate branch).
  - [ ] Runbook `juniper-canopy/notes/runbooks/ws-auth-lockout.md` published.
  - [ ] RISK-15 marked "in production" in the risk tracking sheet.

### 6.8 Rollback

- [ ] Per-IP cap: set `JUNIPER_WS_MAX_CONNECTIONS_PER_IP` very high (e.g., 1000) — effectively disables.
- [ ] Rate limit: `Settings.ws_rate_limit_enabled=False` (add this flag with the implementation).
- [ ] Audit log: rotate files out manually; the feature has no user-visible effect.
- [ ] Idle timeout: `Settings.ws_idle_timeout_seconds=0` disables.
- [ ] Full rollback: revert the Day 6 PRs. Phase B-pre gate criteria 1-5 stay green (Days 4-5 work).

---

## 7. Day 7 — Phase B (cascor): finalize seq ecosystem + cascor-side Phase B instrumentation

**Goal**: finalize cascor server changes needed for Phase B — `emitted_at_monotonic` for latency instrumentation, `replay_buffer_capacity` in `connection_established`, final polish of resume edge cases (R0-03 §8 scenarios).
**Source**: R0-03 §4.2, §6.3, §8, §9; arch doc §5.6.
**Repo**: `juniper-cascor`.
**Estimated hours**: 4-6.

### 7.1 Pre-flight

- [ ] Day 6 rate-limit PR merged.
- [ ] Phase B-pre gate green.
- [ ] Day 3's resume handler has been in main for ≥ 3 days of dev usage.

### 7.2 Branch

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
WT="juniper-cascor--ws-migration--phase-b-finalize--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-b-finalize origin/main
```

### 7.3 Edits

**`src/api/websocket/messages.py`** — `emitted_at_monotonic`

- [ ] Every message builder accepts and emits `emitted_at_monotonic: float = Field(default_factory=time.monotonic)`.
- [ ] Also emit `emitted_at_wall: float = time.time()` as advisory (clock sync helper for browser).
- [ ] `connection_established` continues to advertise `server_instance_id`, `server_start_time`, `replay_buffer_capacity`.

**Atomic snapshot endpoint** — verify Day 3 commit 6 is fully wired

- [ ] Add `test_snapshot_seq_monotonically_increases_across_broadcasts` (from R0-03 §10.1).
- [ ] Verify `/api/v1/training/status` response schema in an integration test.

**Observability — `src/api/websocket/metrics.py` (new)**

- [ ] Prom metrics from R0-03 §9.1:
  - `cascor_ws_connections_active`, `cascor_ws_connections_pending`
  - `cascor_ws_connections_total{endpoint, outcome}`
  - `cascor_ws_disconnects_total{endpoint, reason}`
  - `cascor_ws_broadcasts_total{type}`
  - `cascor_ws_broadcast_send_seconds{type}` histogram
  - `cascor_ws_replay_buffer_occupancy`
  - `cascor_ws_seq_current`
  - `cascor_ws_resume_requests_total{outcome}`
  - `cascor_ws_resume_replayed_events` histogram
  - `cascor_ws_command_responses_total{command, status}`

**Edge-case hardening from R0-03 §8**

- [ ] Verify §8.4 "replay buffer overflow during a live reconnect" pattern: promote under `_seq_lock`, deduplicate on client side.
- [ ] Add `test_concurrent_reconnect_live_replay_dedup_seq` integration test.
- [ ] Add assertion behind `CASCOR_DEV_ASSERTIONS=1` env var (§9.3): `_pending_connections.isdisjoint(_active_connections)`.

### 7.4 Tests

- [ ] `pytest src/tests/unit/api/ -v` green.
- [ ] `pytest src/tests/integration/api/ -k 'snapshot_seq or emitted_at'` green (new tests).
- [ ] `bash src/tests/scripts/run_tests.bash` full suite green.

### 7.5 Commit and PR

- [ ] `feat(ws): add emitted_at_monotonic + finalize Phase B server metrics (GAP-WS-24 part 1)`.
- [ ] PR merges to main. Cross-ref GAP-WS-24, GAP-WS-13, R0-03 §9.

### 7.6 Post-merge verification

- [ ] Local cascor emits metrics with `emitted_at_monotonic` visible in a raw WS capture.
- [ ] `/metrics` endpoint shows new counters.

### 7.7 Rollback

- [ ] `emitted_at_monotonic` field is additive; no behavioral impact. If it causes any serialization issue (unlikely — it's a float), revert the messages.py commit alone.

---

## 8. Day 8 — Phase B (canopy): drain callback wiring + dead JS cleanup

**Goal**: ship the Option B `ws-metrics-buffer` drain callback, delete `dashboard_manager.py:1490-1526` dead client, update topology/state drain callbacks to read from `window._juniperWsDrain`.
**Source**: R0-01 §3.2, §3.5; arch doc §9.3.
**Repo**: `juniper-canopy`.
**Estimated hours**: 7-9.

### 8.1 Pre-flight

- [ ] Phase B-pre in production (Day 4-6 landed).
- [ ] cascor emits `emitted_at_monotonic` (Day 7).
- [ ] Dash version ≥ what's needed for clientside callbacks (Option B does not require Dash 2.18+).
- [ ] **`dashboard_manager.py` refactor coordination (§11 Q4)**: check for open canopy PRs touching this file. Rebase after them if needed.

### 8.2 Branch

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
WT="juniper-canopy--ws-migration--phase-b-drain--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-b-drain origin/main
```

### 8.3 Edits

**`src/frontend/assets/ws_dash_bridge.js` (new, ~200 lines)**

- [ ] Copy the skeleton from R0-01 §3.2.1 verbatim.
- [ ] Module-scope closure with five `on(type, ...)` handlers (metrics, state, topology, cascade_add, candidate_progress) and `onStatus(...)`.
- [ ] Typed JS-side ring buffers with `MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`.
- [ ] **Bound-in-handler invariant**: every push does the splice-to-cap (R0-01 §3.2.5 is load-bearing for RISK-12 — do NOT move the cap into the drain callback).
- [ ] Expose ONE global: `window._juniperWsDrain` with `drainMetrics`, `drainState`, `drainTopology`, `drainCascadeAdd`, `drainCandidateProgress`, `peekStatus`, `_introspect`.
- [ ] Guard at top: `if (!window.cascorWS) { console.error(...); return; }`.
- [ ] **rAF coalescer scaffold disabled** per R0-01 disagreement #1: `_scheduleRaf = function() {}` (noop). Leave the code structure in a commented-out block for easy Phase B+1 enablement.
- [ ] Wrap every handler body in `try { ... } catch (e) { console.error('[ws_dash_bridge] ...', e); }` (FR-RISK-10).

**`src/frontend/assets/websocket_client.js` cleanup (§3.5.1)**

- [ ] Verify `onStatus()` emits `{connected, reason, reconnectAttempt, ts}`. Enrich if not.
- [ ] Add jitter: `delay = Math.random() * Math.min(30_000, 500 * Math.pow(2, attempt))`.
- [ ] Remove 10-attempt cap (GAP-WS-31) — retry forever at max 30s.
- [ ] Parse and store `server_instance_id` from `connection_established`.
- [ ] On reconnect, send `{type: "resume", data: {last_seq, server_instance_id}}` as first frame (AFTER the Day 5 auth frame — see R0-02 §4.7 sequence).
- [ ] Track `_lastSeq` monotonically; log WARN if out-of-order.
- [ ] Maintain a small FIFO ring of last ~256 events with `seq` for dedup.
- [ ] Delete `getBufferedMessages()` and any other helper with no callers.

**`src/frontend/dashboard_manager.py` — drain callback rewrite**

- [ ] **Delete lines 1490-1526**: the parallel raw-WebSocket clientside callback (GAP-WS-03). Replace with a comment pointing to this runbook + R0-01 §3.5.2.
- [ ] **Rewrite `ws-metrics-buffer` init callback** as the drain callback from R0-01 §3.2.2 (reads `window._juniperWsDrain.drainMetrics()`, merges with current store data, caps at 1000, returns `{events, gen, last_drain_ms}`).
- [ ] **Update `ws-topology-buffer` and `ws-state-buffer` drain callbacks** at `dashboard_manager.py:1531-1564` to call `window._juniperWsDrain.drainTopology()` / `drainState()`.
- [ ] Add new drain callbacks for `ws-cascade-add-buffer` and `ws-candidate-progress-buffer` (create the stores in the layout too).
- [ ] Add `ws-connection-status` drain callback per R0-01 §3.4.1 (peek-and-compare; `no_update` when unchanged).
- [ ] `grep -r '_juniper_ws_' src/frontend/` → 0 matches.
- [ ] `grep -r 'new WebSocket' src/frontend/` → 1 match, inside `websocket_client.js`.

**`src/frontend/components/metrics_panel.py` + `candidate_metrics_panel.py`** — `extendTraces` migration (defer to Day 9, but add `uirevision: "metrics-panel-v1"` today)

- [ ] For Day 8: just add the `uirevision` constant in the initial figure layout (1-line change per file). Plotly path rewrite lands Day 9.

### 8.4 Tests

**Unit (pytest)**
- [ ] `src/tests/unit/test_ws_dash_bridge.py` (new):
  - `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
  - `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
  - `test_ws_connection_status_store_reflects_cascorWS_status`
- [ ] `test_dashboard_manager_has_no_dead_websocket_references` — grep-based AC-19 from R0-01 §6.

**JS unit (Jest/Vitest if set up; else defer to E2E)**
- [ ] `assets/websocket_client.js`: jitter, uncapped retries, seq monotonicity, `_introspect`.
- [ ] `assets/ws_dash_bridge.js`: bound-in-handler cap, drain functions clear.

**dash_duo**
- [ ] `test_browser_receives_metrics_event`
- [ ] `test_chart_does_not_poll_when_websocket_connected` (will fully pass after Day 10 for the polling toggle, but the WS side must drive updates today)
- [ ] `test_ws_metrics_buffer_store_is_ring_buffer_bounded`

### 8.5 Commit and PR

- [ ] Split commits (each green independently):
  - `feat(canopy/ws): add ws_dash_bridge.js + _juniperWsDrain global (GAP-WS-04, GAP-WS-05)`
  - `chore(canopy/ws): cleanup websocket_client.js, delete dead raw-WS client (GAP-WS-02, GAP-WS-03)`
  - `feat(canopy/ws): rewrite ws-*-buffer drain callbacks (GAP-WS-04, GAP-WS-05)`
  - `feat(canopy/ws): add ws-connection-status drain callback (GAP-WS-26 part 1)`
- [ ] Push + `gh pr create --title 'feat(canopy/ws): Phase B browser bridge wiring (GAP-WS-02..05)'`.

### 8.6 Post-merge verification

- [ ] Dashboard loads; browser dev console shows `[ws_dash_bridge]` log lines only on errors.
- [ ] `window._juniperWsDrain._introspect()` at the browser console returns `{metricsSize, topology, state, ...}`.
- [ ] Plotly chart updates live (still via full figure replace until Day 9; visually OK).
- [ ] Browser WS frames in DevTools network panel show `seq` field.

### 8.7 Rollback

- [ ] Kill switch: `Settings.disable_ws_bridge=True` (add the flag in this PR) — forces REST polling code path. Document in `ws-bridge-debugging.md` runbook (Day 12).
- [ ] Full revert: the PR series. The dead-client deletion (GAP-WS-03) is behaviorally identical to before (the dead client never fired anyway).

---

## 9. Day 9 — Phase B (canopy): Plotly extendTraces migration + kill /api/metrics/history polling + connection indicator

**Goal**: replace `MetricsPanel.update_metrics_display()` server-side figure-replace with a clientside `extendTraces` callback. Wire the polling toggle (GAP-WS-16 + GAP-WS-25). Add the connection indicator badge (GAP-WS-26).
**Source**: R0-01 §3.3, §3.4; arch doc §9.3.
**Repo**: `juniper-canopy`.
**Estimated hours**: 6-8. **This is the P0 bandwidth-elimination day — the ~3 MB/s waste dies here.**

### 9.1 Pre-flight

- [ ] Day 8 drain callback wiring merged and in dev.
- [ ] Confirm Plotly version ≥ 2.x (supports `extendTraces(maxPoints)`): `python -c "import plotly; print(plotly.__version__)"`.
- [ ] Confirm `assets/ws_dash_bridge.js` loads in the browser console.

### 9.2 Branch

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
WT="juniper-canopy--ws-migration--phase-b-plotly--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-b-plotly origin/main
```

### 9.3 Edits

**`src/frontend/components/metrics_panel.py`**

- [ ] Add hidden `dcc.Store(id='metrics-panel-figure-signal')` to the panel layout (dummy output pattern per R0-01 §3.3.4).
- [ ] Replace `MetricsPanel.update_metrics_display()` callback body at `metrics_panel.py:648-670` with the clientside callback from R0-01 §3.3.2:
  - Input: `Output("metrics-panel-figure-signal", "data")`, `Input("ws-metrics-buffer", "data")`, `State("metrics-panel-figure-signal", "data")`.
  - Body: extract `epochs/losses/accs/vlosses/vaccs` from `buffer_data.events`; call `Plotly.extendTraces("metrics-panel-figure", update, [0,1,2,3], 5000)`; return `no_update`.
  - Guard with `document.getElementById('metrics-panel-figure')` check (FR-RISK-02).
  - Wrap body in `try { ... } catch (e) { ... return window.dash_clientside.no_update; }` (FR-RISK-10).
- [ ] Add 3-line comment block above the `clientside_callback` registration linking to R0-01 §3.3.4 explaining the dummy output pattern.
- [ ] Ensure initial figure layout has `uirevision="metrics-panel-v1"` (if not landed Day 8, add now).

**`src/frontend/components/candidate_metrics_panel.py`**

- [ ] Mirror the above for `candidate-metrics-panel-figure` with `maxPoints=5000`.

**`src/frontend/dashboard_manager.py` — polling toggle (GAP-WS-16 + GAP-WS-25)**

- [ ] Refactor `_update_metrics_store_handler` at `dashboard_manager.py:2388-2421` to read `ws-connection-status` via State:
  ```python
  @callback(
      Output("metrics-panel-metrics-store", "data"),
      Input("fast-update-interval", "n_intervals"),
      State("ws-connection-status", "data"),
      State("metrics-panel-metrics-store", "data"),
  )
  def _update_metrics_store_handler(n, ws_status, current_data):
      if ws_status and ws_status.get("connected"):
          return no_update  # WS driving
      if current_data is None:
          return requests.get(self._api_url("/api/metrics/history?limit=1000"), timeout=2).json()
      if (n % 10) != 0:
          return no_update  # slow fallback to 1 Hz
      return requests.get(self._api_url("/api/metrics/history?limit=1000"), timeout=2).json()
  ```
- [ ] Apply the same pattern to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. Enumerate all in the PR description.

**Connection indicator badge (GAP-WS-26)**

- [ ] New component `src/frontend/components/connection_indicator.py`:
  - `html.Div(id='ws-connection-indicator', className='ws-status-unknown')`.
  - Clientside callback reads `ws-connection-status.data` → toggles class `connected-green / reconnecting-yellow / offline-red / demo-gray`.
- [ ] Inject into dashboard layout.
- [ ] CSS rules in `assets/styles.css` (or appropriate existing stylesheet).

**Demo mode parity (RISK-08, GAP-WS-33)**

- [ ] In `src/backend/demo_mode.py`, after init, set `window.cascorWS` status to `{connected: true, mode: "demo"}` via `set_props` or the peek path.
- [ ] Verify dashboard's `ws-connection-status` reflects "demo".

### 9.4 Tests

- [ ] `dash_duo`:
  - `test_chart_updates_on_each_metrics_event` — emit 10 events, chart has ≥10 points.
  - `test_chart_does_not_poll_when_websocket_connected` — network interceptor captures 1 `/api/metrics/history` request over 5s (initial load).
  - `test_chart_falls_back_to_polling_on_websocket_disconnect` — kill WS, polling resumes.
  - `test_demo_mode_metrics_parity` (RISK-08 gate).
  - `test_connection_indicator_reflects_status`.
  - `test_memory_bounded_over_long_run` — 5000 events, chart data ≤5000, store ≤1000.
- [ ] Playwright:
  - `test_plotly_extendTraces_used_not_full_figure_replace` — instrument `Plotly.extendTraces` via `page.evaluate`.
  - `test_bandwidth_eliminated_in_ws_mode` — record network bytes on `/api/metrics/history`; target `< 400_000` over 10s (initial snapshot only). **This is the P0 acceptance criterion.**
  - `test_frame_budget_single_metric_event_under_17ms` — recording lane, not blocking (R0-05 §8.2).

### 9.5 Commit and PR

- [ ] Commits:
  - `feat(canopy/ws): migrate metrics panels to Plotly.extendTraces clientside (GAP-WS-14, RISK-10)`
  - `feat(canopy/ws): WS-aware polling toggle for metrics/state/topology handlers (GAP-WS-16, GAP-WS-25)`
  - `feat(canopy/ws): connection indicator badge + demo-mode parity (GAP-WS-26, GAP-WS-33, RISK-08)`
- [ ] PR title: `feat(canopy/ws): Phase B render path + P0 bandwidth kill (GAP-WS-14..16, GAP-WS-25..26)`.
- [ ] PR description MUST include the bandwidth measurement from `test_bandwidth_eliminated_in_ws_mode`.

### 9.6 Post-merge verification

- [ ] **P0 metric (the motivator)**: browser DevTools network tab → filter for `/api/metrics/history`. With WS connected, should see 1 request on page load and zero thereafter. Was ~30 per 3 seconds before.
- [ ] Pan/zoom the chart during live update → state is preserved (`uirevision` working).
- [ ] Chart does not "flash" on updates (extendTraces preserves existing SVG).
- [ ] Connection indicator badge shows green when healthy. Kill cascor → turns red within 1s.
- [ ] Demo mode dashboard shows gray "demo" badge.
- [ ] Overnight soak test: leave dashboard running for 12 hours, inspect browser heap (DevTools Memory) — should be bounded.

### 9.7 Rollback

- [ ] Kill switch: `Settings.disable_ws_bridge=True` forces REST polling (Day 8 flag).
- [ ] Partial rollback: revert just the polling-toggle commit → polling continues but WS path still drives charts; bandwidth returns to ~3 MB/s.
- [ ] Full revert: the 3 commits. Dashboard reverts to full figure replace + polling.

---

## 10. Day 10 — Phase C (canopy): adapter set_params routing + feature flag

**Goal**: ship the `_apply_params_hot` / `_apply_params_cold` split in `cascor_service_adapter.py`. Flag defaults False. Bump cascor-client dep pin to SDK_VERSION_A.
**Source**: R0-04 §5, §9.2; arch doc §9.4.
**Repo**: `juniper-canopy` (+ `juniper-ml` for extras pin).
**Estimated hours**: 6-8. **Phase C can ship without Phase B done** per R0-04 §5.4 — the fallback is unconditional. Schedule after Day 9 anyway so the feature flag has a consumer to flip to in staging.

### 10.1 Pre-flight

- [ ] SDK_VERSION_A is live on PyPI (Day 1 post-merge).
- [ ] Phase B cascor seq/replay work merged (Day 7).

### 10.2 Branch

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
WT="juniper-canopy--ws-migration--phase-c-adapter--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-c-adapter origin/main
```

### 10.3 Edits

**`pyproject.toml`**

- [ ] Bump `juniper-cascor-client>=${SDK_VERSION_A}`.

**`../juniper-ml/pyproject.toml`** (separate worktree if on a parallel task)

- [ ] Bump the same pin in the `[tool.poetry.extras]` or equivalent.

**`src/config/settings.py`**

- [ ] Add:
  ```python
  use_websocket_set_params: bool = Field(
      default=False,
      description="Phase C feature flag. When True, canopy's apply_params routes hot params through CascorControlStream.set_params over WebSocket. Default False pending §5.6 latency measurement.",
  )
  ```
- [ ] Env var: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS`.

**`src/backend/cascor_service_adapter.py`**

- [ ] Add class constants `_HOT_CASCOR_PARAMS` and `_COLD_CASCOR_PARAMS` (full enumeration from R0-04 §5.1).
- [ ] Refactor `apply_params(**params)` per R0-04 §5.1:
  - If flag False → `_apply_params_cold(mapped)` (preserves legacy).
  - If flag True → split hot/cold; unclassified keys default to REST with WARNING log.
  - Run hot FIRST, then cold.
- [ ] Implement `_apply_params_hot(mapped)`:
  - Check `self._control_stream is None or not self._control_stream.is_connected` → fall through to REST.
  - `asyncio.run_coroutine_threadsafe(self._control_stream.set_params(mapped, timeout=1.0), self._control_loop).result(timeout=2.0)`.
  - Catch `JuniperCascorTimeoutError`, `JuniperCascorConnectionError` → REST fallback with INFO log.
  - Catch `JuniperCascorClientError` → return `{"ok": False, "error": str(e)}` (do NOT fall back; surface server error).
- [ ] Implement `_apply_params_cold(mapped)` — extract existing REST body.
- [ ] **Ordering guarantee** (R0-04 §5.1 last paragraph): WS fires first, REST fires second.

**`_control_stream_supervisor` background task**

- [ ] Add per R0-04 §5.3:
  - Loop `while not self._shutdown.is_set()`: connect → `wait_closed()` → backoff `[1, 2, 5, 10, 30]`.
  - Launched alongside `_metrics_relay_task` in `start_metrics_relay()`.
  - Cancelled in `stop_metrics_relay()`.
  - `self._control_stream = None` when not connected (used by `_apply_params_hot` gate).

**Latency instrumentation (R0-04 §7)**

- [ ] In `_apply_params_hot`, read `envelope["_client_latency_ms"]` and observe `SET_PARAMS_LATENCY_MS.labels(transport="websocket")`.
- [ ] In `_apply_params_cold`, measure `time.monotonic()` delta and observe `SET_PARAMS_LATENCY_MS.labels(transport="rest")`.
- [ ] Histogram `canopy_set_params_latency_ms` with buckets `{5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000}` ms.

### 10.4 Tests

**`src/tests/unit/test_apply_params_routing.py` (new)** — from R0-04 §10.2 C1-C13:
- [ ] `test_apply_params_feature_flag_default_off` (C1, C3)
- [ ] `test_apply_params_hot_keys_go_to_websocket` (C4)
- [ ] `test_apply_params_cold_keys_go_to_rest` (C4)
- [ ] `test_apply_params_mixed_batch_split` (C8)
- [ ] `test_apply_params_hot_falls_back_to_rest_on_ws_disconnect` (C5)
- [ ] `test_apply_params_hot_falls_back_to_rest_on_timeout` (C6)
- [ ] `test_apply_params_hot_surfaces_server_error_no_fallback` (C7)
- [ ] `test_apply_params_unclassified_keys_default_to_rest_with_warning` (C9)
- [ ] `test_apply_params_preserves_public_signature` (C2)
- [ ] `test_apply_params_latency_histogram_labels_emitted` (C11)
- [ ] `test_control_stream_supervisor_reconnects_with_backoff` (C12)
- [ ] `test_control_stream_supervisor_shutdown_cancels_pending_futures` (C13)

**`src/tests/integration/test_param_apply_roundtrip_ws.py` (new, uses FakeCascorServerHarness)**
- [ ] `test_adapter_apply_params_hot_uses_websocket_roundtrip` (C10)
- [ ] `test_adapter_apply_params_cold_uses_rest`

### 10.5 Commit and PR

- [ ] Commits:
  - `chore(canopy): bump juniper-cascor-client>=${SDK_VERSION_A}`
  - `feat(canopy): add use_websocket_set_params feature flag`
  - `feat(canopy/adapter): split apply_params into hot/cold with WS routing (GAP-WS-01 consumer, Phase C)`
  - `feat(canopy/adapter): _control_stream_supervisor task + latency histograms`
- [ ] PR title: `feat(canopy): Phase C adapter set_params WebSocket routing (feature-flagged)`.
- [ ] PR description documents the flag remains False and why: §5.3.1 ack-vs-effect analysis.
- [ ] **Separate tiny PR**: `juniper-ml` extras pin bump. Must merge AFTER Phase C canopy PR.

### 10.6 Post-merge verification

- [ ] Dev: restart canopy; supervisor log shows connected state.
- [ ] Flip `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=true` in dev; drag a slider; observe in DevTools:
  - WS frame with `{"command": "set_params", ...}`.
  - Prom `canopy_set_params_latency_ms_bucket{transport="websocket"}` incrementing.
- [ ] Flag off: slider still works via REST path (regression gate).

### 10.7 Rollback

- [ ] **Primary kill switch**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` + canopy restart. TTF ~2 min (R0-04 §5.2).
- [ ] Code-level: the `_apply_params_cold` path is untouched from pre-refactor; reverting the adapter commit alone is zero-risk because the hot path is dead code when the flag is off.
- [ ] Revert extras pin bump last.

---

## 11. Day 11 — Phase D (canopy + cascor): control buttons over WebSocket + Phase F heartbeat/jitter

**Goal**: wire start/stop/pause/resume/reset buttons to `window.cascorControlWS.send(...)` with `command_id` correlation. Add browser-side jitter (F) if not already landed on Day 8.
**Source**: R0-01 §4 step 17 + R0-04 touches; arch doc §9.5.
**Repo**: `juniper-canopy` (+ minor cascor if `command_id` echo wasn't done Day 3).
**Estimated hours**: 5-7. **Phase D is BLOCKED on Phase B-pre in production.**

### 11.1 Pre-flight

- [ ] Phase B-pre in production ≥ 24h.
- [ ] All 8 Phase B-pre exit criteria green.
- [ ] Day 10 Phase C merged (control stream supervisor is the transport for Phase D buttons too).
- [ ] cascor echoes `command_id` (check test added Day 3 to `test_websocket_control.py`; if not, add here).

### 11.2 Branch

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
WT="juniper-canopy--ws-migration--phase-d-controls--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main)"
git worktree add "/home/pcalnon/Development/python/Juniper/worktrees/${WT}" -b ws-migration/phase-d-controls origin/main
```

### 11.3 Edits

**`src/frontend/components/training_controls.py` (or wherever the buttons live)**

- [ ] For each button (start/stop/pause/resume/reset), replace the REST POST callback body with a clientside callback that calls `window.cascorControlWS.send({command, command_id: uuidv4()})`.
- [ ] Fallback: if `window.cascorControlWS` is not connected, POST to `/api/train/{command}` (legacy path).
- [ ] Add `command_id` generation helper in `ws_dash_bridge.js`.
- [ ] Track pending commands in a JS-side map; mark button "pending verification" until `command_response` OR a matching `state` event lands (GAP-WS-13, RISK-13).

**cascor — ensure `command_id` echo (if not done Day 3)**

- [ ] In `control_stream.py`, accept optional `command_id` in inbound frames; echo in `command_response`. No validation — pass-through string.

**Phase F heartbeat + jitter (if not already landed)**

- [ ] `assets/websocket_client.js`: jitter was added Day 8. Verify.
- [ ] Add browser-side heartbeat: send `{"type": "ping"}` every 30s; expect `{"type": "pong"}` within 5s; close + reconnect on timeout.
- [ ] cascor `training_stream_handler` inbound dispatcher already handles `ping → pong` (Day 3 `handle_training_inbound`).

### 11.4 Tests

- [ ] Playwright:
  - `test_start_button_uses_websocket_command` — intercept WS, click start, see `{command: "start"}`.
  - `test_command_ack_updates_button_state` — fake replies success → button state updates.
  - `test_disconnect_restores_button_to_disabled`.
  - `test_csrf_required_for_websocket_start` — regression gate.
  - `test_orphaned_command_resolves_via_state_event` (RISK-13).
  - `test_ping_pong_reciprocity`.
  - `test_missing_pong_triggers_reconnect`.
- [ ] Canopy unit:
  - `test_training_button_handler_sends_websocket_command_when_connected`
  - `test_training_button_handler_falls_back_to_rest_when_disconnected`
  - `test_rest_endpoint_still_returns_200_and_updates_state` (GAP-WS-06 regression gate)

### 11.5 Commit and PR

- [ ] Commits:
  - `feat(canopy/controls): route start/stop/reset through WS with REST fallback (GAP-WS-32, RISK-13)`
  - `feat(canopy/ws): browser heartbeat ping/pong (GAP-WS-12, Phase F)`
  - `chore(cascor): echo command_id in command_response (if not already done)` (optional if Day 3 covered it)
- [ ] PR title: `feat(canopy): Phase D training control buttons over WebSocket + Phase F heartbeat`.
- [ ] **PR description must include Phase B-pre exit criteria status** per R0-06 §3.5.

### 11.6 Post-merge verification

- [ ] Click start on dashboard; DevTools WS frame shows `{command: "start", command_id: "..."}`.
- [ ] REST `/api/train/start` still works for curl clients (regression gate for GAP-WS-06).
- [ ] Kill WS mid-click; button falls back to REST without user-visible error.
- [ ] 24h in staging with no orphaned-command incidents (wait for canary cohort in §7.2 of R0-06).

### 11.7 Rollback

- [ ] `Settings.disable_ws_control_endpoint=True` (from R0-06 §5.2 emergency kill switch) disables `/ws/control` entirely; buttons force-fall back to REST. TTF ~5 min.
- [ ] Revert the PR → full REST behavior.

---

## 12. Day 12 — Phases E / H / I + tests / observability / docs polish

**Goal**: land the remaining gap items that can ship independently: Phase E pump-task backpressure (if desired, else keep the 0.5s quick fix), Phase H dual-format regression test + audit, Phase I asset cache busting.
**Source**: R0-03 §7.2; R0-01 §4 step 30 (Phase I); arch doc §9.6-§9.10.
**Repos**: `juniper-cascor` (E), `juniper-canopy` (H, I).
**Estimated hours**: 6-8. This day is optional if E is deferred per R0-03.

### 12.1 Phase I — asset cache busting (R0-01 §4 step 30, §9.10)

- [ ] In `juniper-canopy/src/main.py` (or wherever Dash `assets_url_path` is configured), configure a query-string content hash so browsers bust cache on new JS without hard refresh.
- [ ] Verify: load dashboard; view source; `assets/websocket_client.js?v=<sha>` visible.
- [ ] Test: `test_asset_url_includes_version_query_string` (Playwright).
- [ ] **This should have shipped with Day 8 Phase B** per R0-06 §3.6 — if it didn't, fold it in here.

### 12.2 Phase H — `_normalize_metric` dual-format regression gate + audit

**R0-05 §4.3 Phase H + R0-06 §3.6**:
- [ ] Add test `test_normalize_metric_produces_dual_format` in canopy unit tests BEFORE any audit PR.
- [ ] Add `test_normalize_metric_nested_topology_present`.
- [ ] Add `test_normalize_metric_preserves_legacy_timestamp_field`.
- [ ] Write the consumer audit doc at `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`:
  - List every consumer of nested vs flat metric keys across canopy frontend.
  - Explicit recommendation: do NOT remove either format without landing this test first.

### 12.3 Phase E — full pump-task backpressure (DEFERRED by default)

**R0-03 §7.2 recommends deferring**. Only ship if production telemetry from Day 9 shows RISK-04 / RISK-11 triggering.

If shipping:
- [ ] Follow R0-03 §5.2 pump-task design (`_ClientState` + per-client queue).
- [ ] Policy matrix from §5.2 wired via `Settings.ws_backpressure_policy ∈ {block, drop_oldest, close_slow}`.
- [ ] Tests per R0-05 §4.1 "Phase E" list.
- [ ] `ws-slow-client-policy.md` runbook in `juniper-cascor/notes/runbooks/`.

### 12.4 Docs and runbooks (R0-06 §10)

Create all the Phase-specific runbooks that haven't been landed yet:

- [ ] `juniper-canopy/notes/runbooks/ws-auth-lockout.md` (should exist from Day 6; verify).
- [ ] `juniper-canopy/notes/runbooks/ws-cswsh-detection.md`.
- [ ] `juniper-canopy/notes/runbooks/ws-bridge-debugging.md` (Day 8/9).
- [ ] `juniper-canopy/notes/runbooks/ws-memory-soak-test-procedure.md`.
- [ ] `juniper-canopy/notes/runbooks/ws-set-params-feature-flag.md` (how to flip; how to monitor).
- [ ] `juniper-canopy/notes/runbooks/ws-control-button-debug.md`.
- [ ] Each runbook uses the template from R0-06 §10 (Symptom / Impact / Triage / Mitigation / Root-cause / Escalation / Post-mortem link).

### 12.5 Observability — verify metrics + dashboard panels (R0-06 §6)

- [ ] Canopy Prometheus scrape shows:
  - `canopy_ws_auth_rejections_total{reason}`
  - `canopy_ws_oversized_frame_total`
  - `canopy_ws_delivery_latency_ms_bucket`
  - `canopy_ws_active_connections`
  - `canopy_ws_reconnect_total{reason}`
  - `canopy_rest_polling_bytes_per_sec` (target: >90% reduction)
  - `canopy_set_params_latency_ms_bucket{transport}`
- [ ] Cascor Prometheus scrape shows R0-03 §9.1 metrics.
- [ ] "WebSocket health" dashboard panel in canopy `docs/REFERENCE.md` rendered and showing real data.
- [ ] AlertManager rules from R0-06 §6.3 deployed.

### 12.6 Commit and PR

- [ ] Multiple small PRs, each independent:
  - `feat(canopy): Phase I asset cache busting (GAP-WS-25 adjacent)`
  - `test(canopy): Phase H dual-format regression gate (RISK-01)`
  - `docs(canopy): Phase H normalize_metric consumer audit`
  - `docs(juniper): WS migration runbooks (B-pre through D)`
  - (Optional) `feat(cascor): Phase E pump-task backpressure (GAP-WS-07 full fix)`

### 12.7 Post-merge verification

- [ ] All Phase B-I acceptance criteria from R0-05 §9 green in CI.
- [ ] All RISK-01..16 mitigations deployed per R0-06 §4 matrix.
- [ ] The P0 metric (`/api/metrics/history` polling bandwidth) is <1 MB total over a 10-second window (down from ~30 MB baseline).

### 12.8 Rollback

- [ ] Each PR is independently revertable.
- [ ] The P0 metric is the acceptance criterion; if it regresses after Day 9, the polling toggle commit (Day 9) is the first revert candidate.

---

## 13. Cross-repo coordination summary

**Merge-order summary** (enforced; merge queue where available):

```
1. cascor-client Phase A             (Day 1)
   ↓ PyPI publish + 2-5min
2. cascor Phase A-server part 1      (Day 2)
3. cascor Phase A-server part 2      (Day 3)
4. cascor  + canopy Phase B-pre Origin  (Day 4)
5. canopy Phase B-pre CSRF + sizes   (Day 5)
6. cascor + canopy Phase B-pre rate + audit (Day 6)
                               ── Phase B-pre gate closes here ──
7. cascor Phase B finalize           (Day 7)
8. canopy Phase B drain wiring       (Day 8)
9. canopy Phase B Plotly + polling kill (Day 9)
                               ── Phase B gate closes here ──
10. canopy Phase C adapter (flag off) (Day 10)
    juniper-ml extras pin bump       (Day 10 follow-up)
                               ── Phase C merged, flag off ──
11. canopy Phase D + Phase F heartbeat (Day 11) — BLOCKED until B-pre in prod
                               ── Phase D gate closes here ──
12. Phases H/I/E + docs              (Day 12)
```

**Release coordination notes (R0-06 §8.1, R0-04 §9.13)**:

- [ ] Every PR updates `CHANGELOG.md`.
- [ ] Every PR cross-references GAP-WS-NN, M-SEC-NN, and RISK-NN IDs it touches.
- [ ] Use squash-merge for linear history.
- [ ] Helm chart `version` + `appVersion` bumps match app semver bumps (user's global memory).
- [ ] SDK version bump is minor; canopy/cascor are patch unless new `seq` envelope fields (Phase B cascor → minor).
- [ ] After Phase D, pause 48h before flipping `use_websocket_set_params=True` in staging canary.

---

## 14. Reconciled disagreements (R0 cross-references)

These are resolutions of conflicts found in the R0 proposals. The runbook picks a side; downstream Rounds 2-5 can override.

| # | Conflict | R0 side A | R0 side B | Runbook resolution |
|---|---|---|---|---|
| D1 | rAF coalescer in Phase B | R0-01 §7 disagreement #1: ship scaffolded but DISABLED | arch doc §5.5: ship enabled | **Ship disabled (R0-01 wins)**. Scaffold in `ws_dash_bridge.js` as noop. Revisit in Phase B+1 if §5.6 instrumentation shows frame pressure. |
| D2 | `set_params` default timeout | R0-04 §12.1: 1.0s | arch doc §7.1: 5.0s | **1.0s (R0-04 wins)**. Matches GAP-WS-32 per-command table; 5s slider hang is visibly bad. Callers override explicitly. |
| D3 | Phase B-pre effort | R0-02 §9.1: 1.5-2 days | arch doc §9.2: 1 day | **Split across Days 4, 5, 6** = 2.5 days calendar. Session middleware + CSRF plumbing + audit logger are load-bearing. |
| D4 | Origin allowlist empty semantics | R0-02 §9.3: empty = reject-all (fail closed) | arch doc §2.9.2: ambiguous | **Empty = reject all (fail closed)**. Document prominently. |
| D5 | `disable_ws_auth` flag naming | R0-02 §9.4: `ws_security_enabled=True` (positive) | arch doc §2.9.2: `disable_ws_auth=False` (negative) | **Defer to Round 2**; runbook uses both names interchangeably for now. |
| D6 | Per-command HMAC | R0-02 §9.5: defer indefinitely | arch doc §2.9.2: optional | **Defer (R0-02 wins)**. Complexity > value inside an authenticated session. |
| D7 | NetworkVisualizer in Phase B scope | R0-01 §7 #3: defer to B+1 | arch doc §9.3: include | **Defer (R0-01 wins)** — NetworkVisualizer uses cytoscape not Plotly; `extendTraces` does not apply; bandwidth is ~3 KB/s not ~3 MB/s. Add the WS push wire but don't touch the cytoscape render path until Phase B+1. |
| D8 | `_update_metrics_store_handler` fallback cadence | R0-01 §7 #2: 1 Hz during disconnect | arch doc §6.3: unspecified | **1 Hz (R0-01 wins)**. `(n % 10) != 0` shortcut. |
| D9 | Frame budget: extendTraces mandate | R0-01 §7 #4: extendTraces for live, `Plotly.react` for snapshot | arch doc §5.5: always extendTraces | **R0-01 nuance wins** — §6.5.2 snapshot path uses `Plotly.react`, other paths use `extendTraces`. |
| D10 | `command_id` per-connection scoping | R0-02 §3.3 attack 5: scoped per-connection | arch doc §7.32: ambiguous | **Per-connection (R0-02 wins)** — `Dict[WebSocket, Dict[command_id, pending]]` never `Dict[command_id, pending]`. |
| D11 | `request_id` field in set_params | R0-04 §4.2: new additive field | arch doc §3.2.3: absent | **Add additive (R0-04 wins)**. Phase G server-side test must assert echo. SDK falls back to first-match-wins if server lags. |
| D12 | rate-limit bucket split (set_params vs destructive) | R0-02 §4.5: optional two-bucket | R0-02 §4.5: default single bucket | **Default single bucket** on Day 6. Split if production shows slider starvation. |
| D13 | Phase A-server vs Phase B monolith | R0-03 §7.1: carve Phase A-server | arch doc §9.3: one phase | **Carve (R0-03 wins)**. Days 2-3 = A-server; Day 7 = Phase B finalize; keeps cascor contract stable for canopy iteration. |
| D14 | 1 Hz state throttle replacement | R0-03 §7.1 commit 7: debounced coalescer | arch doc §9.3: not explicit | **Coalescer (R0-03 wins)** — bypass terminal transitions to fix the Started→Failed→Stopped race. |

---

## 15. Disagreements with R0 inputs (this runbook's additions)

### 15.1 Day 4 ships Origin before CSRF

**R0-02**: suggests landing M-SEC-01 + M-SEC-02 + M-SEC-03 as a single Phase B-pre wave (1 day in arch doc, 1.5-2 in R0-02).

**This runbook**: ships Origin alone on Day 4 because:
1. Origin is conceptually and code-wise isolated (no session middleware coupling).
2. It can be verified in production independently before the more complex CSRF work lands.
3. Ships as a strictly additive WARNING log for a few hours, letting ops catch any false-positive rejections before CSRF makes a false rejection user-visible.

**Cost**: one extra day. **Benefit**: rollback granularity.

### 15.2 Two-phase registration lands with cascor Day 3, not Day 7

**R0-03 §5.1**: the two-phase registration (pending set → active set) is part of the broadcaster design.

**This runbook**: lands the `_pending_connections` set on Day 2 (commit 2 — just the attr) and the full handler flow on Day 3 (commit 5). Day 7 is reserved for `emitted_at_monotonic` + observability.

**Rationale**: Day 3 already touches `training_stream.py` for the resume handler; the two-phase registration is the same surgery area. Bundling reduces merge conflict risk.

### 15.3 Phase I (asset cache busting) ships with Day 8 or Day 12

**R0-01 step 30**: Phase I ships with Phase B to ensure browsers pick up the new JS.

**R0-06 §3.6**: Phase I "can ship in the same PR as Phase B" but is also independent.

**This runbook**: prefer Day 8 (Phase B browser wiring is the natural home). If Day 8 PR grows unwieldy, defer to Day 12. Do NOT ship Phase B without Phase I in production — stale `websocket_client.js` will not understand `seq` and will not reconnect correctly.

### 15.4 Day 9's `test_bandwidth_eliminated_in_ws_mode` is the P0 acceptance gate

**R0-05 §9.3**: lists bandwidth measurement as one of many Phase B acceptance criteria.

**This runbook**: elevates it to **THE P0 gate**. If Day 9 ships and the /api/metrics/history bandwidth is not <400 KB over 10s, roll back the polling-toggle commit and debug before merging.

**Rationale**: the ~3 MB/s elimination is the single motivator for this entire migration per R0-01 §1, arch doc §1.2. Shipping Phase B without hitting it is shipping without the reason to ship.

### 15.5 Test marker split

**R0-05 §10 CI integration**: 3-lane split (fast/e2e/nightly).

**This runbook**: adopts verbatim but adds one additional lane:

- `markers = ["unit", "integration", "e2e", "latency", "security"]`.
- `security` lane runs on every PR touching `main.py`, `websocket/*.py`, or `assets/websocket_client.js` (R0-02 §5.5 exit criteria).
- `latency` lane is recording-only in CI, enforcing only locally.

---

## 16. Self-audit log

### 16.1 Pass 1 verification

- [x] Every phase from R0-06 §3 has at least one day assigned.
- [x] Every GAP-WS-NN mentioned in R0-01..06 is referenced in at least one day's edits.
- [x] Every M-SEC-NN (01..07, 10, 11) is assigned to Days 4-6.
- [x] Every RISK-NN (01..16) is referenced (either in edits, tests, rollback, or disagreements §14).
- [x] Merge order matches R0-06 §8.1.
- [x] All 12 days have: pre-flight, branch/worktree, edits, tests, commit, post-merge verification, rollback.
- [x] Feature flags (`disable_ws_bridge`, `use_websocket_set_params`, `ws_security_enabled`) documented with TTF.

### 16.2 Pass 2 corrections applied

1. **Day 4 originally bundled CSRF and Origin** — split per §15.1 to land Origin alone first. Rollback granularity and WARNING-log observation window both benefit.

2. **Day 5 was missing the `close_all()` lock fix (IMPL-SEC-43)** — added. R0-03 §11 claims it's already fixed on main; the runbook verifies instead of assuming.

3. **Day 9 had no explicit bandwidth acceptance criterion** — added `test_bandwidth_eliminated_in_ws_mode` as the P0 gate (§15.4). First draft listed it among many tests; second draft elevated it.

4. **Day 10 forgot to bump juniper-ml extras** — added as explicit follow-up commit. R0-06 §8.2 table lists it but earlier drafts of this runbook missed the step.

5. **Day 11 was missing heartbeat coordination with Day 6 idle timeout** — clarified that Day 11's `ping` resets Day 6's idle timer (see R0-02 §4.5 control 5 note).

6. **Phase B-pre gate criteria** (R0-06 §3.2 list of 8) — first draft only enumerated 5. Second pass added the runbook-published + 24h-staging + risk-sheet items.

7. **Day 8's drain callback rewrite was missing the deletion grep-verification** — added `grep -r '_juniper_ws_' src/frontend/` → 0 matches and `grep -r 'new WebSocket' src/frontend/` → 1 match as belt-and-suspenders regression tests (R0-01 AC-19, AC-20).

8. **Day 6 was missing the `canopy_ws_auth_latency_ms` histogram** — added per R0-02 §4.6 rules 11.

9. **Day 2's 4 commits were written as one commit** in the first draft — split per R0-03 §7.1 to match "each commit green independently" requirement. Verified cherry-pick workflow works.

10. **Day 10 had no idempotency discussion** — added a mention that the WS+REST ordering is "WS first then REST" per R0-04 §5.1 because `lifecycle._training_lock` serializes both on the server side.

11. **Day 11 PR description was missing the Phase B-pre status block** — added as required per R0-06 §3.5 exit gate.

12. **D14 (state throttle coalescer) was missing from §14 disagreements table** — the runbook picks R0-03's coalescer over the arch doc's silence, and the decision belongs in the disagreements list.

13. **Day 1's SDK `_client_latency_ms` was written as a public field** — corrected to private (leading underscore) per R0-04 §4.6 convention so callers treat it as SDK-internal metadata.

14. **Day 5 was missing IMPL-SEC-38 adapter synthetic auth frame discussion** — added as a TODO (deliberate punt) because R0-02 §11 flags it as a Round 2 decision. Do not block Day 5 on it.

15. **Day 9 rollback for partial polling-toggle revert was not spelled out** — added the "revert only the polling-toggle commit; WS still drives, bandwidth returns to ~3 MB/s" scenario.

### 16.3 Items NOT covered

- **Multi-tenant replay buffer isolation** (R0-02 §3.4 attack 4, §9.7) — out of scope for the migration; flagged as Q1-sec for post-migration.
- **Service Workers / WebAssembly Plotly** — out of scope (R0-01 §8.4).
- **Visual regression tests** — R0-05 §1 explicit non-goal.
- **Multi-browser (Firefox, WebKit)** — R0-05 §1 + R0-06 §9 Q2: Chromium-only for v1.
- **Real-cascor nightly smoke tests** — R0-05 §9.6 nightly lane; out of runbook day-scope.
- **User-research validation** — R0-06 §9 Q7: default is skip.

### 16.4 Scope discipline check

- Every day fits in 4-9 engineering hours. No day is accidentally a 2-day phase.
- Every day produces at least one merged PR.
- Every day has a rollback that is config-only OR single-commit-revert.
- Cross-repo coordination is explicit on Days 1 (cascor-client→PyPI→canopy), 4 (cascor+canopy parallel), 6 (cascor+canopy parallel), 10 (juniper-ml follow-up).
- The P0 motivator (3 MB/s kill) has a dedicated day (9) with a dedicated acceptance criterion.

### 16.5 Confidence assessment

- **High confidence** in Days 1, 2, 4, 5, 6, 8, 10: direct translations from R0 specs with file-level anchors.
- **Medium confidence** in Day 3: the two-phase registration + resume handler is a net-new control flow that R0-03 sketches but has not been prototyped.
- **Medium confidence** in Day 9: `extendTraces` clientside callback + polling toggle interacts with canopy's existing callback graph in ways that only a PR+CI cycle will fully expose.
- **Medium confidence** in Day 11: depends on Phase B-pre being stable in production AND Phase C supervisor being stable — neither is guaranteed by prior days.
- **Lower confidence** in Day 12 (Phase E pump task): R0-03 recommends deferring; the runbook marks it optional. Runbook's default is to SKIP Phase E on Day 12 unless production telemetry from Day 9 shows RISK-04/11 triggering.

### 16.6 Hand-off readiness

- [x] An engineer reading this on Monday morning can pick Day N, open the right worktree, and start editing by referring ONLY to this runbook + the referenced R0 sections.
- [x] Every day has a file list and a test invocation.
- [x] Every PR has a draft title and body hint.
- [x] Every rollback is reachable without a fresh design decision.
- [x] Cross-repo order is unambiguous.

---

**End of R1-04 operational runbook.**
