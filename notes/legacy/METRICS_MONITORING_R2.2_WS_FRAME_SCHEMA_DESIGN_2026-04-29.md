# METRICS-MON R2.2 Design — WebSocket frame schema validation in consumers

**Date:** 2026-04-29
**Author:** Paul Calnon
**Status:** 🟡 Design — open for review.
**Seed finding:** seed-05 (consumer-side WebSocket frames are accepted as opaque dicts; type drift between server and client only surfaces at runtime via downstream `KeyError`).
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §5 R2.2.
**Companion:** [`METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md), [`METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md`](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. Purpose

Today, every server-emitted WebSocket frame is structurally validated **only at the server** (via the typed builders in `juniper-cascor/src/api/websocket/messages.py` and `src/api/workers/protocol.py`). On the consumer side, frames are parsed via `json.loads(raw)` and dispatched on `message["type"]` with `dict.get(...)` access throughout. A schema regression introduced in cascor reaches the consumer's runtime as a downstream `KeyError` or silent missing-data, not a clean validation error. This design closes that gap.

R2.2 is the last open item in the METRICS-MON Phase R2 exit gate (after R2.1 shared lib, the R2 worker-adoption decision, and R2.3 probe-direction symmetry). After it ships, R2 closes and the program turns to R3 (test-coverage gaps), R4 (instrumentation), R5 (SLOs/scrape/dashboards).

---

## 2. Current state — by repo

### 2.1 The three WebSocket endpoints in `juniper-cascor`

| Endpoint | Direction | Wire format | Server emits |
|---|---|---|---|
| `/ws/training` | server → client (broadcast) | JSON envelope `{type, timestamp, data, seq?, emitted_at_monotonic?}` | `metrics`, `state`, `topology`, `event`, `cascade_add`, `candidate_progress`, `initial_metrics`, `chunked_message` |
| `/ws/control` | bidirectional | JSON envelope (no `seq`); inbound `{type:"command_in", command, command_id?, params?}`; outbound `{type:"command_response", data:{command, status, ...}}` + `{type:"connection_established"}` on connect | `command_response`, `connection_established`, `chunked_message` |
| `/ws/v1/workers` | bidirectional | JSON envelope + side-channel binary frames carrying numpy tensors | `task_assign`, `token_refresh`, `error`, `registration_ack`, `result_ack`, `connection_established`, `heartbeat` |

The training/control endpoints share an envelope shape; the worker endpoint does not (no `data` wrapping; flat top-level fields).

### 2.2 Server-side typed assets that already exist

- `juniper-cascor/src/api/websocket/messages.py` — typed dict-builder helpers (`create_metrics_message`, …). Returns `Dict[str, Any]`. **Not Pydantic; not exported as a package.**
- `juniper-cascor/src/api/workers/protocol.py` — `MessageType` `StrEnum`; `BinaryFrame.encode/decode`; `WorkerProtocol.build_*` builders; `WorkerProtocol.validate_task_result`, `validate_register`, `validate_tensors` imperative validators; `TaskAssignment` and `TaskResultMessage` `@dataclass`es with `to_dict`/`from_dict`. **Not Pydantic; not exported.**

Neither file is importable from outside the cascor source tree — both consumers (`juniper-cascor-client`, `juniper-cascor-worker`) re-derive their understanding of the protocol from string-literal constants in their own `constants.py` files.

### 2.3 Consumers today

| Consumer | Endpoint(s) consumed | Validation today |
|---|---|---|
| `juniper-cascor-client` (`ws_client.py`) | `/ws/training`, `/ws/control` | **None.** `json.loads(raw)` then `message.get("type", "")` for dispatch; `data` accessed as `message.get("data", {})`. No required-field check, no type check. Dependencies: `requests`, `urllib3`, `websockets`. **No pydantic.** |
| `juniper-canopy` (`backend/cascor_service_adapter.py` + WS subscriber paths) | `/ws/training`, `/ws/control` | **Minimal.** Parses JSON, dispatches by type string. Has `pydantic>=2.0.0` and `prometheus-client>=0.20.0` already as runtime deps. |
| `juniper-cascor-worker` (`ws_connection.py`, `worker.py`) | `/ws/v1/workers` | **Imperative.** `WorkerProtocol.validate_*` is duplicated as string-literal field checks in `worker.py`. The worker's own `_handle_task_assign` does manual `msg.get(...)` walks. Dependencies: `numpy`, `torch`, `websockets`. **No pydantic, no prometheus_client.** Per the [R2 exit-gate decision](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md), pydantic and starlette are intentionally not in the worker image. |

### 2.4 Why the asymmetry matters

The worker's protocol surface is **fundamentally different** from the broadcast envelope:

- **Worker frames carry side-channel binary tensors** decoded with numpy. The schema is "JSON envelope + N binary frames matching a tensor manifest". A pure JSON-schema validator cannot express this; the worker's existing imperative validators work for both halves.
- **Worker is by design a slim image**: numpy + torch + websockets only. Adding pydantic adds ~12 MB compiled wheel for a payload-validation purpose that the existing imperative validators already meet.
- **Worker is a producer too** — cascor server validates worker-emitted `task_result` via `WorkerProtocol.validate_task_result`. That stays unchanged regardless of where the schemas live.

By contrast, the training/control envelope is **pure JSON**: `{type, timestamp, data, seq?, emitted_at_monotonic?}` with type-specific `data` payloads. Pydantic v2 expresses this naturally and produces good error messages for free.

This pushes the design toward a **two-track approach** (R2.2.A and R2.2.B below).

---

## 3. Open questions and resolutions

The questions are framed so a reviewer can disagree on each independently.

### Q1. Where do the schemas live?

**Options considered:**

- **Q1.a — In `juniper-observability`.** Single shared lib already used by data, cascor, canopy.
  *Cons:* The observability lib is currently scoped to **cross-service infrastructure** (logging, metrics, health). WS protocol shape is **service-specific** (cascor's protocol, not a cross-service standard) — putting it in `juniper-observability` confuses the lib's scope. Worker would need pydantic to consume even just the `MessageType` enum, contradicting the [R2 exit-gate decision](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md).
- **Q1.b — Export from cascor server itself as a sub-package.** Cascor's `pyproject.toml` declares `juniper-cascor` as a single package; carving out `juniper_cascor.protocol.*` would force every consumer to install the full server package (FastAPI, lifecycle code, …). Wrong fit.
- **Q1.c — New `juniper-cascor-protocol` package.** A subdirectory of `juniper-cascor` (mirroring how `juniper-observability` is a subdirectory of `juniper-ml`). Published independently to PyPI. Pinned by cascor server, cascor-client, canopy. Worker is **not** required to pin it (see Q5).

**Resolution:** **Q1.c.** Schemas live in a new `juniper-cascor-protocol` package. Justification:

1. WS protocol is service-coupled to cascor; it does not belong in a cross-service observability lib.
2. The R2.1 publishing pattern (subdirectory + OIDC trusted publish) is proven and reusable.
3. Worker can opt out cleanly without contradicting R2 exit-gate decisions.
4. Consumers gain a small, focused dep edge instead of a large diffuse one.

### Q2. What's the package's surface?

**Resolution:**

```
juniper_cascor_protocol/
├── __init__.py             # Re-exports: MessageType (broadcast), WorkerMessageType (worker),
│                           # all envelopes, validate(...), UnrecognizedFrameError
├── envelope/               # /ws/training and /ws/control schemas
│   ├── __init__.py
│   ├── base.py             # BaseEnvelope (type, timestamp, data, seq?, emitted_at_monotonic?)
│   ├── training.py         # MetricsFrame, StateFrame, TopologyFrame, EventFrame,
│   │                       # CascadeAddFrame, CandidateProgressFrame, InitialMetricsFrame,
│   │                       # ChunkedMessageFrame
│   └── control.py          # CommandResponseFrame, ConnectionEstablishedFrame, etc.
├── worker/                 # /ws/v1/workers schemas — Pydantic-OPTIONAL
│   ├── __init__.py         # MessageType StrEnum re-exported (no pydantic touched)
│   ├── messages.py         # WorkerMessageType, optional Pydantic models on
│   │                       # the [pydantic] extra; plain dict + StrEnum surface
│   │                       # always available on the bare install
│   └── binary_frame.py     # BinaryFrame.encode/decode (numpy-only, no pydantic)
└── version.py              # __version__ — pinned by every consumer
```

**Two install profiles:**

| Install | Deps | Use case |
|---|---|---|
| `juniper-cascor-protocol` | `pydantic>=2.0` (envelope schemas use it), `numpy>=1.24` (binary frames) | cascor server, cascor-client, canopy |
| `juniper-cascor-protocol` (the worker imports only the StrEnum + BinaryFrame submodules; pydantic is never imported) | inherits `pydantic` as a transitive dep — **but worker's runtime never touches it** because lazy imports in `worker/__init__.py` load `WorkerMessageType` and `BinaryFrame` without crossing the envelope subpackage | cascor-worker |

**Note on the "transitive dep" concern:** because the worker only imports `from juniper_cascor_protocol.worker import WorkerMessageType, BinaryFrame`, Python never executes the envelope subpackage's pydantic imports. The on-disk pydantic wheel is present but **dormant**. Net cost to worker image: ~12 MB. This is a smaller footprint than the full `juniper-observability` install (~14 MB starlette + pydantic + anyio) and the value is concrete: the worker's `MessageType` enum + binary frame format become single-sourced.

### Q3. Worker scope — full pydantic or selective import?

**Resolution: selective import.** The worker imports **only** `WorkerMessageType` (StrEnum) and `BinaryFrame` (numpy-only) from `juniper_cascor_protocol.worker`. It does NOT import the envelope subpackage. It does NOT use Pydantic to validate inbound frames; the existing imperative validators stay.

This deliberately differs from the cascor-client + canopy adoption (which fully validates via Pydantic) because:

- The worker's existing imperative validators (`WorkerProtocol.validate_task_result`, `validate_tensors`) already do schema-level validation; a Pydantic rewrite would be a refactor without behavior change.
- The worker's binary-frame protocol is structurally not a JSON-only schema; pydantic would cover ~half of it.
- Keeping the worker pydantic-free at runtime preserves the R2 exit-gate decision rationale.

The benefit the worker gets from R2.2: **single-sourced `MessageType` enum** (eliminates the literal-string duplication in `juniper_cascor_worker/constants.py`) + **single-sourced `BinaryFrame` codec** (eliminates the parallel hand-rolled struct.unpack walk in `worker.py`).

### Q4. Counter naming and host services

**Roadmap text:** "Unrecognized frame types log + emit a `juniper_<svc>_unrecognized_ws_frames_total` counter (clients gain minimal observability surface here as a side effect of seed-05)."

**Resolution:**

| Consumer | Observability target | Counter name | Notes |
|---|---|---|---|
| cascor-client | New optional Prometheus dep, opt-in via `juniper-cascor-client[observability]` extra | `juniper_cascor_client_unrecognized_ws_frames_total{type, endpoint}` | Two labels: the unrecognized type string (capped to `_unmatched` if it's high-cardinality, per R1.1) and the endpoint (`training` or `control`). |
| canopy | Existing `prometheus-client` dep | `juniper_canopy_unrecognized_ws_frames_total{type, endpoint}` | Mounted on canopy's existing `/metrics` (R1.1 cardinality bound applies). |
| worker | **No Prometheus**. Structured log line only. | n/a | `logger.warning("juniper_cascor_worker_unrecognized_ws_frames", extra={"type": type_str, "worker_id": worker_id})` — parseable by log shippers (Loki, etc.) without adding a Prometheus dep. |

**Cardinality bounding (R1.1):** Unknown `type` values are attacker-influenced (a malicious server could emit garbage). The label is collapsed to the literal `_unmatched` after the first N=16 distinct values per process, mirroring the R1.1 strategy used for HTTP endpoint labels. This is implemented in `juniper-cascor-protocol`'s validation helper so every consumer gets the bound for free.

### Q5. Does R2.2 close R2 phase if the worker doesn't fully validate?

**Resolution: yes.** R2.2's stated goal is "frames validated in clients/workers". The worker has been validating its inbound frames imperatively since the original protocol shipped (`WorkerProtocol.validate_*`). What R2.2 adds is **single-sourcing the type enum + binary codec** (so cascor and worker cannot drift) and the **unrecognized-frame observability** (structured log line for worker, Prometheus counter for the JSON-envelope consumers). This satisfies the spirit of seed-05 (no silent drift) without forcing a Pydantic adoption that does not benefit the worker.

The roadmap §5 R2.2 text "import and validate every inbound frame" is honored: the worker imports the canonical `WorkerMessageType` enum and validates against it.

### Q6. Where do the cascor server's emit sites land?

**Resolution:** cascor server adopts `juniper-cascor-protocol` as a runtime dep and replaces:

- Dict-builder calls in `src/api/websocket/messages.py` with **construct + `.model_dump()`** of the corresponding Pydantic envelope.
- `src/api/workers/protocol.py` `MessageType` and `BinaryFrame` are **removed** in favor of imports from `juniper_cascor_protocol.worker`. The `WorkerProtocol.build_*` and `WorkerProtocol.validate_*` helpers stay (they're imperative for backwards compat) but are reduced to thin wrappers around the shared types.

Cascor becomes the **first consumer of its own protocol package**, which is the canonical pattern for protocol packages — the producer cannot drift from the schema because it imports it.

### Q7. Versioning policy

**Resolution:**

- `juniper-cascor-protocol` follows PEP 440 + Keep a Changelog (same as `juniper-observability`).
- Initial release: `0.1.0a0` (alpha). First stable: `0.1.0` after a soak with one consumer (cascor server, R2.2.2 below).
- Wire-compat: any **additive** envelope field (new optional kwarg) is a minor bump (`0.1.x` → `0.2.0`); any **removal or rename** is a major bump (`0.x.y` → `1.0.0`).
- Consumers pin `>=A.B,<A+1` in their pyprojects so the publishing pipeline cannot push a breaking change to production transitively.

---

## 4. Wire-compat implications

R2.2 is **wire-compat-preserving** by construction:

- The Pydantic models are derived from the existing dict shapes; field names match byte-for-byte.
- `BaseModel.model_dump(mode="python", by_alias=False)` produces a dict identical to the current `_build_envelope(...)` output (including the conditional `seq` and `emitted_at_monotonic` fields, achieved via `model_dump(exclude_none=True)`).
- Each migration PR (cascor server, cascor-client, canopy) ships a **wire-compat snapshot test** mirroring the R2.1 pattern: capture the JSON shape pre-migration, assert byte-equal post-migration.

---

## 5. Implementation sequence (PR list)

| # | Repo | Branch | What | Tests |
|---|---|---|---|---|
| 1 | juniper-cascor | `metrics-mon-seed-05-protocol-init` | Create `juniper-cascor-protocol/` subdirectory with envelope (Pydantic) + worker (StrEnum + BinaryFrame) modules. Mirror the R2.1 OIDC publish workflow (`publish-protocol.yml`). Publish `0.1.0a0` to TestPyPI then PyPI. | Unit tests for every public symbol; ≥ 95% coverage. Wire-compat snapshot capturing the byte-for-byte envelope shape. |
| 2 | juniper-cascor | `metrics-mon-seed-05-server-adopt` | Cascor server pins the alpha. Replaces `src/api/websocket/messages.py` dict-builders with `model.model_dump()`. Removes `MessageType` + `BinaryFrame` from `src/api/workers/protocol.py` (re-exports for backwards compat). | Existing tests + new envelope-roundtrip test. |
| 3 | juniper-ml | `metrics-mon-seed-05-protocol-stable` | Promote alpha → `0.1.0` after server soak. | Same unit suite. |
| 4 | juniper-cascor-client | `metrics-mon-seed-05-client-validate` | Pin `juniper-cascor-protocol>=0.1.0`. Replace `_dispatch` to validate inbound frames against the envelope union; on success call the registered callback; on failure log + (if `[observability]` extra installed) increment `juniper_cascor_client_unrecognized_ws_frames_total`. | Round-trip test (cascor emit → client validate → no errors); chaos test sends malformed frames and asserts they are rejected without crashing the consumer. |
| 5 | juniper-canopy | `metrics-mon-seed-05-canopy-validate` | Same as #4, plus mount the counter on the existing `/metrics` endpoint (canopy already has `prometheus-client`). | Same shape as #4. |
| 6 | juniper-cascor-worker | `metrics-mon-seed-05-worker-adopt` | Pin `juniper-cascor-protocol>=0.1.0`. Replace `MessageType` literals in `juniper_cascor_worker/constants.py` with imports from `juniper_cascor_protocol.worker`. Replace the binary-frame struct walk in `worker.py` with `juniper_cascor_protocol.worker.BinaryFrame.decode/encode`. Add structured log line on unrecognized frame types. **No Pydantic import in the worker's runtime.** | Existing tests + new test confirming the structured log line is emitted on unknown types. |
| 7 | juniper-ml | `metrics-mon-r2-2-roadmap-done` | Mark §9 R2.2 done; mark R2 phase exit gate fully closed. | n/a (doc-only). |

**Total: 7 PRs.** PRs #2, #4, #5, #6 each delete net Python LOC from their respective repos (the pre-existing duplicated literals + dict builders go away).

**Sequencing rationale:**

1. Schemas published first (`#1` alpha → `#3` stable).
2. Producer (cascor server) adopts before consumers so the snapshot tests are derived from a known-good emitter (`#2` between `#1` and `#3`).
3. Consumer adoption (`#4`–`#6`) is independent — they can land in any order against the stable release.
4. Roadmap closes after all consumers ship (`#7`).

---

## 6. Test plan

Per-repo test coverage required by Definition of Done:

| Test | Repo | Asserts |
|---|---|---|
| `test_envelope_roundtrip` | juniper-cascor-protocol | Every envelope class round-trips: `Frame.model_validate(frame.model_dump()) == frame`. |
| `test_unrecognized_type_collapses_to_unmatched` | juniper-cascor-protocol | Validation helper collapses unknown `type` strings to `_unmatched` after N=16 distinct values (R1.1 cardinality bound). |
| `test_binary_frame_codec_byte_compat` | juniper-cascor-protocol | `BinaryFrame.decode(BinaryFrame.encode(arr)) == arr` for shape × dtype matrix; rejects oversize frames; rejects malformed dtype strings. |
| `test_server_emits_byte_equal_to_pre_migration_snapshot` | juniper-cascor | Each `/ws/training` message type, captured pre-migration, re-emits byte-for-byte via the new `model.model_dump()` path. |
| `test_client_validates_inbound_metrics_frame` | juniper-cascor-client | Healthy frame from server passes validation; callback fires with the parsed model. |
| `test_client_chaos_malformed_frames` | juniper-cascor-client | Server sends garbled JSON / unknown type / missing required field — client logs + counter increments + does NOT raise. |
| `test_canopy_validates_inbound_state_frame` | juniper-canopy | Same shape as cascor-client variant, scoped to canopy's WS subscriber. |
| `test_worker_unrecognized_frame_log` | juniper-cascor-worker | Worker receives a frame with `type=garbage_value` — emits structured `WARNING` log with `type` + `worker_id` keys; processes no further; remains connected. |

---

## 7. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|:---:|---|
| New `juniper-cascor-protocol` package adds a fourth distribution from the polyrepo. | High (cost) | Reuse the `juniper-observability` publish workflow shape; no new infra. |
| Pydantic v2 model field defaults silently change wire output (e.g., `None` vs missing). | Medium | Snapshot tests with `model_dump(exclude_none=True)` capture the contract. |
| Worker's "lazy pydantic" import pattern breaks if a future refactor accidentally crosses the envelope subpackage. | Low | CI test in worker that asserts `pydantic` is not in `sys.modules` after worker startup. |
| Cardinality bound on the unknown-type label is wrong for high-traffic-but-known-unknown scenarios. | Low | The bound is per-process; benign typos still appear in logs even if the counter collapses. |
| Schemas drift from the wire format faster than consumers can adopt the new pin. | Medium | Versioning policy Q7: minor for additive, major for breaking. Consumers pin `>=A.B,<A+1`. |
| Pydantic v3 release lands during the rollout. | Low | The lib pins `pydantic>=2.0,<3.0` until the ecosystem migrates uniformly. |

---

## 8. Out of scope

- **Validation of WS commands sent by clients to server.** The server's existing input handling (in `control_stream.py` and `worker_stream.py`) stays. R2.2 is consumer-side validation of server-emitted frames.
- **Replacing the worker's binary-frame side-channel handling with a JSON-only protocol.** The worker emits/receives raw numpy buffers for performance; that stays.
- **Schema versioning negotiation in the WebSocket handshake.** Out of scope for R2.2; if a major version of the protocol ships later, a `connection_established` field can carry the protocol version for future negotiation.

---

## 9. Definition of done

R2.2 is done when:

- [ ] `juniper-cascor-protocol==0.1.0` is published to PyPI (R2.2.1 + R2.2.3).
- [ ] cascor server emits all WS frames via the shared models with byte-equal snapshots vs pre-migration (R2.2.2).
- [ ] cascor-client validates every inbound frame with a chaos test demonstrating malformed frames don't crash the consumer (R2.2.4).
- [ ] canopy validates every inbound frame with the same chaos coverage (R2.2.5).
- [ ] worker single-sources `WorkerMessageType` + `BinaryFrame` and emits the structured log line on unknown types (R2.2.6).
- [ ] Roadmap §9 R2.2 row is **done** (R2.2.7).
- [ ] R2 phase exit gate text in §5 of the roadmap reflects all four sub-items (R2.1, worker decision, R2.3, R2.2) closed.

After R2.2 ships, **METRICS-MON Phase R2 is complete**. The program turns to R3 (test-coverage gap closure) and R4 (instrumentation/best practices); R5 (SLOs/scrape/dashboards) gates on R3.

---

## 10. References

- [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §5 R2.2 — original scope.
- [`METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md`](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) — seed-05.
- [`METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) — pattern this design extends (subdirectory + OIDC publish + per-consumer wire-compat snapshot).
- [`METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md`](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md) — explains why the worker stays pydantic-free at runtime; this design honors that constraint via lazy/selective imports in Q3.
- `juniper-cascor/src/api/websocket/messages.py` — current dict-builder helpers being replaced.
- `juniper-cascor/src/api/workers/protocol.py` — current worker protocol surface (`MessageType` `StrEnum`, `BinaryFrame`, `WorkerProtocol`); `MessageType` + `BinaryFrame` move to the new package.
