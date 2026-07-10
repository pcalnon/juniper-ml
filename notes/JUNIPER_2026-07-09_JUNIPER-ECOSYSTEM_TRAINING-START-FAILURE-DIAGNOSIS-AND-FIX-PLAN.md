# Training-Start Failure — Diagnosis and Fix Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: juniper-canopy, juniper-cascor, juniper-deploy, juniper-ml (launcher)
**Author**: Paul Calnon (investigation by Claude Code)
**Date**: 2026-07-09
**Status**: Diagnosed and live-verified; fix plan in flight (PR-A / PR-B / PR-C below)

---

## 1. Executive Summary

The Juniper stack cannot start training from the Canopy dashboard on a freshly-launched stack — silently in the trivial case, and with an apparently-hung Start button in the fully-determined case. Three independent defects were identified and **verified against the live on-host stack**:

1. **Primary (blocks all training, Docker and on-host): nothing creates the cascor network anymore.** Since cascor's `auto_start` default was flipped to disabled (the intentional move to user-activated training), a fresh cascor boots with no network object. Every start path requires one, and no code path creates one.
2. **Amplifier (why it is silent): canopy reports these failures as success at every layer.** The REST route returns HTTP 200 `{"status": "started", "ok": false, ...}` and broadcasts "Training started successfully"; the WebSocket command handler wraps the failed result in a `status: "success"` envelope. The Phase D §S10 error-surfacing machinery never fires because it only reacts to error envelopes / non-2xx responses.
3. **Secondary (the "authentication loop", on-host only): control-WS Origin mismatch.** Canopy's WS client presents `Origin: http://<hostname>:8050` (e.g. `http://yamaguchi:8050`); cascor's `/ws/control` allowlist default admits localhost forms only. The connection is rejected 403 every 30 s forever. This does **not** block training start (start is REST) — it kills hot `set_params` over WS and produces the log spam that suggested an auth loop.

The dataset-staging half of the workflow works correctly: the staged spiral dataset reached cascor and was verified pending. The only missing ingredient in the user flow was the network object — and the failure to create it was masked by defect 2.

---

## 2. Reported Symptoms

Reported 2026-07-09 against both launch paths (docker compose `make up`, and `util/juniper_plant_all.bash` on-host). All services healthy at startup; provenance doctor FRESH across images.

| Case | Steps | Observed |
|------|-------|----------|
| Trivial | Clean launch → click **Start Training** | Button flips to active (`⏳ Start Training...`), returns to idle after ~15 s. No training, no error shown. |
| Fully determined | Clean launch → Dataset View → select Spiral, noise 0.1 → **Apply Parameters** → **Apply Dataset** → **Stop & Restart with new dataset** → **Start** | "Apply Parameters" shows *Failed to apply (502)* (both for invalid 0.125 and valid 0.1 noise). Start button goes active and appears to stay active indefinitely. No training. |
| Logs | on-host canopy log | `Control stream supervisor disconnected (Failed to connect to ws://localhost:8201/ws/control: server rejected WebSocket connection: HTTP 403), reconnecting in 30s` repeating forever; `Failed to fetch canopy params: No network created` every 5 s. |

---

## 3. Evidence Chain

### 3.1 Log evidence (session of 2026-07-09, 19:50 launch)

Canopy `logs/juniper-canopy_2026-07-09_1950.log`:

- `19:50:32` — `ServiceBackend: no existing cascor network found (will create on start)` — the promise that is no longer honored anywhere.
- `19:50:32` onward — control-stream 403 loop begins (backoff 1 s → 2 s → 5 s → 10 s → 30 s, then 30 s forever; still running 45+ minutes later).
- `19:51:05` — `Control command received: start (backend=service, id=ac8797cf-…)` — the trivial-case click. **No subsequent error, timeout, or start-related line.**
- `19:54:17`, `19:54:39` — `WS set_params failed, falling back to REST for hot params` — the two Apply Parameters clicks.
- `19:55:12` — `Dataset staged: {'nn_dataset_type': 'spirals', 'nn_dataset_elements': 1000, 'nn_dataset_noise': 0.1, …}`.
- `19:55:27` — `Cold-swap restart with staged dataset` — logged **only when the POST returned HTTP 200** (see 4.2).
- `19:56:08` — `Control command received: start (backend=service, id=f7ae9a9a-…)` — the determined-case click. Again nothing after it.

Cascor `logs/juniper-cascor_2026-07-09_1950.log`:

- **No `POST /v1/training/start` was ever received.** Only status/params/history GETs.
- Two `PATCH /v1/training/params` → **404 Not Found** (lines 381, 412) — the REST fallbacks of the two Apply Parameters clicks; 404 body is "No network created". Canopy's `/api/set_params` maps the failure to the 502 seen in the UI.
- Three `POST /v1/training/dataset` → **200 OK** — dataset staging works.
- From the prior session's log (`_1856`), the explicit rejection reason: `juniper_cascor.api.websocket.control_security - INFO - Control WS: origin 'http://yamaguchi:8050' not in allowlist — rejecting`.

### 3.2 Live probes (2026-07-09 ~20:51 CDT, against the running stack)

```text
GET  http://localhost:8201/v1/network
  → HTTP 404 {"status":"error","error":{"code":"HTTP_404","message":"No network created",...}}

POST http://localhost:8201/v1/training/start          (direct to cascor)
  → HTTP 409 {"status":"error","error":{"code":"HTTP_409",
              "message":"Training cannot be started: No network created",...}}

POST http://localhost:8050/api/train/start            (canopy, browser-equivalent)
  → HTTP 200 {"status":"started","ok":false,"error":"No network created"}    ← success theater

WS handshake http://localhost:8201/ws/control, Origin: http://localhost:8050  → HTTP 101 (accepted)
WS handshake http://localhost:8201/ws/control, Origin: http://yamaguchi:8050  → HTTP 403 (rejected)

GET  http://localhost:8201/v1/training/dataset/pending
  → {"pending":{"dataset_type":"spirals","n_samples":1000,"noise":0.1,"rotations":1.5,"n_spirals":2}}

GET  http://localhost:8201/v1/dataset
  → {"loaded": false}
```

Cascor tells the truth (409). Canopy converts the same failure into HTTP 200 "started". The staged dataset is present and pending; no data is loaded; no network exists.

---

## 4. Root Causes

### 4.1 Defect 1 — no network-creation path (primary)

- Cascor `auto_start` now defaults to disabled: `juniper-cascor/src/api/settings.py:75` (`_JUNIPER_CASCOR_API_AUTO_START_DEFAULT = _JUNIPER_CASCOR_API_AUTO_START_DISABLED`; field at `:394`). Auto-start was the only mechanism that created a network (+ spiral dataset) at boot. In juniper-deploy, only the **demo** profile re-enables it (`docker-compose.yml:409`); the full profile — what `make up` runs — does not. The on-host launcher never set it.
- Canopy `ServiceBackend.start_training` hard-fails when no network exists instead of creating one — `juniper-canopy/src/backend/service_backend.py:91-92`:

  ```python
  if self._adapter.network is None:
      return ControlResult(ok=False, error="No network created")
  ```

  This contradicts its own startup log ("will create on start", `service_backend.py:280`).
- The creation plumbing exists — `CascorServiceAdapter.create_network` (`backend/cascor_service_adapter.py:581`) → `POST /v1/network` — but has **zero callers** outside demo mode.
- Cascor's lifecycle enforces the same precondition server-side (`api/lifecycle/manager.py:1862-1863`) and consumes a staged/pending dataset only *inside* `start_training` (`manager.py:1895-1897`) — one step past the network check that can never pass.

Consequence: on a fresh cascor, **every** start path is guaranteed to fail — UI button (WS), UI button REST fallback, cold-swap restart, and direct `POST /v1/training/start`.

### 4.2 Defect 2 — failures reported as success ("success theater")

- REST: `POST /api/train/start` ignores the backend result entirely — `juniper-canopy/src/main.py:3057-3075`. It broadcasts `create_control_ack_message("start", True, "Training started successfully")` and returns `{"status": "started", **result}` with HTTP 200 even when `result == {"ok": False, "error": "No network created"}`. Verified live (§3.2). `pause` / `resume` / `stop` share the pattern (`main.py:3078+`).
- WebSocket: the `/ws/control` command handler wraps any non-raising result in a `status: "success"` envelope — `main.py:934-952`. `ControlResult` is a `TypedDict` (`backend/protocol.py:127`), so the failure detail rides along as `data={"ok": false, "error": ...}` inside a success envelope.
- The Phase D §S10 error-surfacing (danger-alert on failed control commands; `frontend/dashboard_manager.py:109-258` clientside JS + `notes/` design of 2026-06-14) keys off **error envelopes and non-2xx responses only** — both of which the layers above convert to success. The optimistic button state is therefore kept, and only the timeout sweeper (`_handle_button_timeout_and_acks_handler`, `dashboard_manager.py:5535`) eventually resets the button. Nothing is ever shown to the user.
- The cold-swap callback (`restart_with_new_dataset`, `dashboard_manager.py:4192-4218`) logs *"Cold-swap restart with staged dataset"* on any HTTP 200 — so the 19:55:27 log line records a start that never happened.

Historical note: the May 2026 "Start-Training 401" fix (canopy#414/#415) verified that the request *passed auth* (HTTP 200). Because of this defect, an HTTP 200 does not imply a started training run — which is how the broken start path survived subsequent audits.

### 4.3 Defect 3 — control-WS Origin mismatch on host (the "auth loop")

- Canopy's default WS Origin is derived from the machine hostname: `_default_cascor_ws_origin()` returns `http://{socket.gethostname()}:8050` — `juniper-canopy/src/settings.py:58-86`. The docstring itself documents that this is *"wrong for connecting"* in host-mode dev and prescribes `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://localhost:8050`.
- Cascor's `/ws/control` allowlist default admits only localhost forms — `juniper-cascor/src/api/settings.py:448-456`; validation in `api/websocket/control_security.py:20-36`.
- juniper-deploy pre-aligns both ends (`docker-compose.yml:251` and `:635`), so containerized runs are unaffected. The on-host launcher `juniper-ml/util/juniper_plant_all.bash` sets **neither**, so every host launch produces the 30 s 403 reconnect loop.
- Fallout: hot-parameter pushes over WS always fail and fall back to REST (`cascor_service_adapter.py:805-813`), which then 404s for lack of a network (defect 1) → the UI's *Failed to apply (502)*. Log noise every 30 s misreads as an authentication loop. Training start is unaffected by this defect (start is REST).

### 4.4 Interaction map

| Symptom | Defect 1 | Defect 2 | Defect 3 |
|---------|----------|----------|----------|
| Trivial Start: silent no-op | cause | hides it | — |
| Determined Start: no training, button appears stuck | cause | hides it, keeps optimistic button state | — |
| Apply Parameters → 502 | cause of the 404 underneath | — | forces WS → REST fallback |
| 30 s WS 403 reconnect log spam | — | — | cause |
| `Failed to fetch canopy params: No network created` every 5 s | cause | — | — |

---

## 5. Immediate Unblock (no code changes)

Against a running stack:

```bash
# 1. Create a network sized for the pending/default 2-spiral dataset
curl -X POST http://localhost:8201/v1/network \
     -H 'Content-Type: application/json' \
     -d '{"input_size": 2, "output_size": 2}'

# 2. Click "Start Training" in the dashboard (or POST /v1/training/start).
#    Cascor consumes the pending staged dataset on start.
```

For the origin loop, relaunch canopy with `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://localhost:8050` (PR-C automates this).

---

## 6. Fix Plan

Triad shape: this document (diagnosis / design-of-record) + three code PRs. Defects land as separate PRs per repo convention.

### PR-A — canopy: propagate ControlResult failures (correctness; fixes defect 2)

- `/ws/control` handler (`main.py` ~931-975): when the executed command returns a dict with `ok is False`, send a `command_response` **error** envelope carrying the backend error text (e.g. `No network created`) instead of a success envelope. Success envelope only for `ok` truthy/absent (demo-backend compatibility).
- `/api/train/start|pause|resume|stop|reset`: when the backend result has `ok is False`, return **409** with the error detail and broadcast a failure ack (`create_control_ack_message(cmd, False, error)`), not "Training started successfully".
- Effect: the existing §S10 machinery starts working as designed — WS error → clientside promise rejection → REST fallback → 409 → dismissable danger alert; button state resets promptly.
- Tests: unit tests for both dispatch layers (ok=False → error envelope / 409; ok=True and demo-shape results → unchanged).
- Acceptance: `POST /api/train/start` on a network-less cascor returns 409 with `No network created`; the dashboard surfaces a visible error; no "Training started successfully" broadcast/log on failure.

### PR-B — canopy: Start creates the network (and default dataset) when none exists (fixes defect 1)

- `ServiceBackend.start_training` (or an adapter-level orchestration it calls): when `adapter.network is None`:
  1. Determine the dataset that the start will use: cascor's pending staged dataset if present; else the currently-loaded dataset; else stage canopy's default dataset config (spiral defaults — the documented "default selection for model and dataset" in the trivial case).
  2. Derive `input_size` / `output_size` from that dataset config (mirroring cascor's generator shape contract, e.g. spirals → `(2, n_spirals)`), `create_network`, then start. Unknown/unsupported dataset types fail loudly with an actionable error (surfaced by PR-A).
- Honors the existing "will create on start" contract at `service_backend.py:280`.
- Tests: fresh-cascor start creates network + starts; staged-dataset start uses staged dims; existing-network start path unchanged.
- Acceptance: on a fresh stack (no snapshot, auto-start off), clicking **Start Training** trains — both the trivial case (defaults) and the determined case (staged dataset consumed).
- **Confirm-defaults UX** (trivial case should present the model/dataset defaults and ask for confirmation before starting): designed as a follow-up increment on top of PR-B (modal on Start when no network/dataset exists yet, listing model + dataset defaults with Confirm/Cancel). If its dashboard-layout footprint grows the PR materially (UI snapshot regen, harness updates), it splits into its own PR-D rather than delaying the correctness fix. Decision recorded in the PR description.

### PR-C — juniper-ml: on-host launcher aligns the control-WS Origin (fixes defect 3)

- `util/juniper_plant_all.bash`: export `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` (default `http://localhost:8050`, env-overridable like the existing `JUNIPER_CASCOR_HOST`/`PORT` knobs) on the canopy launch line. This is the exact override canopy's own settings docstring prescribes for host-mode dev.
- Extend the launcher regression test to assert the export.
- Alternative considered (deferred, canopy-side): default `cascor_ws_origin` to `http://localhost:8050` whenever the configured cascor service URL host is loopback — would make any host launcher correct with zero configuration. Worth a canopy follow-up; PR-C fixes the supported entry point now.

### Follow-ups (documented, not in this round)

- **PR-D (canopy)**: confirm-defaults modal if split out of PR-B (see above).
- **Cold-swap button error surfacing**: `restart_with_new_dataset` currently only warns to the log on non-200; with PR-A it will at least keep the pending banner open on failure. A visible alert would be better.
- **`juniper_canopy_unrecognized_ws_frame` / `juniper_cascor_client_unrecognized_ws_frame` warnings**: observed periodically on the training stream; benign in this incident but undiagnosed — deserves its own look.
- **Control-stream reconnect posture**: the supervisor retries forever at 30 s on a *policy* rejection (403). Consider distinguishing policy rejections (log once at ERROR with remediation hint, back off harder) from transient failures. Note cascor's handshake cooldown blocks an IP after 10 rejections/60 s (`control_security.py:76+`) — the 30 s cadence stays safely under it, but tighter loops would trip it.
- **Cascor-side alternative** (not chosen): `POST /v1/training/start` could auto-create the network from the post-generation data shape. Architecturally cleaner (single source of truth for dims) but a larger API-contract and FSM change; canopy-side orchestration uses only existing endpoints.

---

## 7. Verification Plan

- **Unit/regression**: each PR carries tests as listed; full suites run per repo (`pytest` per canopy AGENTS.md; `python3 -m unittest` suites in juniper-ml).
- **E2E (isolated, does not disturb a running stack)**: second cascor+canopy pair on alternate ports (e.g. 8202/8051) from the PR worktrees:
  - PR-A branch: Start with no network → visible danger alert, 409 in network tab, button resets; no success broadcast.
  - PR-B branch: trivial Start on fresh instances → network created, spiral trained; determined case → staged dataset consumed.
  - PR-C: launcher smoke — canopy env contains the origin export; control-stream connects (no 403 loop) on host.
- **Docker parity**: after canopy PRs merge and images rebuild, `make up` (full profile) trivial-case Start must train. The demo profile (auto-start) remains unchanged.

---

## 8. Session Artifacts

- Live-verified on the on-host stack launched 2026-07-09 19:50 CDT (canopy/cascor/data logs `*_2026-07-09_1950.log`).
- Immediate-unblock recipe delivered to the operator (§5) — note it mutates the running cascor (creates a network); harmless.
- Memory note: `training-start-failure-diagnosis-2026-07-09` (Claude Code project memory).
