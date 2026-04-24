# juniper-cascor-client — Metrics & Monitoring Code Review Plan

**Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-cascor-client/`
**Target file once distributed**: `juniper-cascor-client/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
**Inherits**: `00_ECOSYSTEM_ROADMAP.md`
**Created**: 2026-04-24
**Phase**: C — Consumers (run after juniper-cascor)

---

## 1. Scope

Metrics & monitoring surface of juniper-cascor-client (HTTP + WebSocket
client library for juniper-cascor). In-scope:

- REST methods that fetch metrics/status/topology
- `CascorTrainingStream` async WebSocket consumer
- `CascorControlStream` and command framing relevant to delivery acks
- Client-side parsing/validation of metric payloads (or absence thereof)
- Retry, timeout, reconnect logic affecting metric delivery to callers
- Tests for all of the above

Out-of-scope: CasCor algorithm, server-side training behavior, server
contract definition (owned by juniper-cascor review).

---

## 2. Pre-existing evidence (from initial survey)

### 2.1 Surface inventory

**REST** (`client.py`):
- `get_metrics()` → `/v1/metrics` (lines 242–244)
- `get_metrics_history(count)` → `/v1/metrics/history` (lines 246–255)
- `get_topology()` → `/v1/network/topology` (lines 164–166)
- `get_training_status()` → `/v1/training/status` (lines 216–218)

**WebSocket** (`ws_client.py`):
- `CascorTrainingStream` (lines 21–150)
- Callback API: `on_metrics`, `on_topology`, `on_state`, `on_cascade_add`,
  `on_event`
- Async iter `stream()` generator (lines 70–78)
- **No reconnection**; `ConnectionClosed` exits dispatch loop (79–80)
- **No exponential backoff** for streams

### 2.2 Configuration

| Setting | Default | Source |
|---------|---------|--------|
| `base_url` | `http://localhost:8200` | `constants.py` |
| `ws_url` | `ws://localhost:8200` | `constants.py` |
| `DEFAULT_REQUEST_TIMEOUT` | 30 s | `constants.py:28` |
| `DEFAULT_SET_PARAMS_TIMEOUT` | 1.0 s | `constants.py:111` (fast-fail per design D-01) |
| `DEFAULT_CONTROL_STREAM_TIMEOUT` | 30.0 s | `constants.py:92` |
| `JUNIPER_CASCOR_API_KEY` | env-only | `constants.py:85` |
| HTTP retry | 3 / 0.5 backoff / [502,504] | `constants.py:29–32` |

**Note**: server runs on port 8201 (host) / 8200 (container) per parent
CLAUDE.md; default `8200` matches container — verify caller deployment
patterns are consistent.

### 2.3 Dependencies

- `requests>=2.28.0`, `urllib3>=2.0.0`
- `websockets>=11.0` (no upper pin — API-stability risk)
- **No** Pydantic / TypedDict / dataclass — all payloads
  `Dict[str, Any]`

### 2.4 Tests

- `TestMetricsEndpoints` (3 tests; `test_client.py:226`)
- `test_get_topology` (`test_client.py:140–144`)
- WS callback tests (5 tests; `test_ws_client.py:111–152`)
- WS stream iteration test (`test_ws_client.py:70–91`)
- `test_fake_client.py` scenario coverage (XOR converged, two-spiral,
  empty network)
- All mocked; **no integration tests against a live server**

### 2.5 Already-suspected findings

| # | Hypothesis | File:line |
|---|------------|-----------|
| H1 | Metrics payloads parsed as raw `Dict[str, Any]` — no Pydantic / TypedDict / dataclass; schema drift silent until use | client.py / ws_client.py |
| H2 | `CascorTrainingStream.stream()` exits cleanly on `ConnectionClosed` but does NOT reconnect | `ws_client.py:79–80` |
| H3 | `CascorControlStream` fails pending commands on disconnect; no exponential backoff | `ws_client.py:336` |
| H4 | No client-side instrumentation (no per-request latency, no error rates, no circuit state) | (absent) |
| H5 | Metrics fields accessed by key without presence validation — `KeyError` risk | client.py |
| H6 | DEVELOPER_CHEATSHEET training-stream schema example is incomplete (missing `val_loss`, `val_accuracy`, `hidden_units`) | docs/DEVELOPER_CHEATSHEET.md |
| H7 | No timeout tests (e.g. 31 s delay vs 30 s timeout) | tests |
| H8 | No concurrent `set_params` test under MAX_PENDING_COMMANDS=256 | tests |
| H9 | No metrics-history pagination boundary tests | tests |
| H10 | No integration tests against a live cascor instance | tests |
| H11 | `websockets>=11.0` unpinned upper bound — potential breakage on major release | pyproject.toml:32 |
| H12 | No client-server compatibility matrix documented — consumers can't tell which client version pairs with which cascor server version | docs |

---

### 2.6 Audit corrections (2026-04-24)

- All `:line` citations verified.
- `py.typed` marker confirmed present.
- `mypy strict = true` confirmed in pyproject.toml.
- The `juniper_cascor_client.testing` module IS exported in
  `setuptools.packages.find` and discoverable in the wheel — useful
  for downstream consumer tests. Plan should preserve this contract.
- `TestCascorTrainingStream` is at lines 13–153 (the WS callback
  tests live inside this class); plan §2.4's "111–152" range is the
  callback-method block within that class. Substantively accurate.

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk public client surface; record drift.
2. Build a payload-shape catalog: REST endpoint / WS message type → keys
   accessed by client → keys actually emitted by server (cross-reference
   `juniper-cascor` review's metric catalog).
3. Build a resilience matrix: each public method × {timeout, network
   error, server 5xx, malformed payload, server restart} → behavior.

### Phase 2 — Functionality verification

1. Spin up a live `juniper-cascor` instance (or use the
   `juniper_cascor_client.testing` fakes if integration is too heavy).
2. Exercise each metrics endpoint; verify behavior matches docs.
3. Open a WS stream; restart the cascor server mid-stream; verify
   `ConnectionClosed` propagation behavior. Confirm H2.
4. Inject malformed JSON on WS; confirm whether client crashes, logs,
   or silently drops.

### Phase 3 — Test-suite audit

1. Full run:
   ```bash
   cd juniper-cascor-client
   pytest tests/ -v --tb=short \
     --cov=juniper_cascor_client --cov-report=term-missing
   ```
2. Inventory the 80% fail-under threshold — verify it's still met.
3. Verify each metric/topology test asserts the value/shape, not just
   dict-truthiness.
4. Catalog missing test scenarios (H7–H10).

### Phase 4 — Issue classification

Apply ecosystem framework §3.1–3.2.

### Phase 5 — Remediation design

See §5.

### Phase 6 — Validation

1. Land remediations on a worktree branch.
2. Re-run unit suite.
3. Cross-repo: confirm `juniper-canopy` integration tests still pass with
   the updated client (canopy depends on this lib).

### Phase 6.5 — CI/CD review (added)

1. Read `.github/workflows/ci.yml`; record matrix and coverage gate.
2. Add a CI job that exercises `websockets` next-major to detect
   API drift before consumers break (mitigates H11).
3. Add (or schedule) cross-repo smoke job that pairs latest
   juniper-cascor server with this client — mitigates H12.

### Phase 7 — Documentation

1. Update `DEVELOPER_CHEATSHEET.md` schema examples (addresses H6).
2. Update `CLAUDE.md` if API surface changed.
3. CHANGELOG entry.

---

## 4. Deliverables

| File | Contents |
|------|----------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan |
| `REVIEW_FINDINGS.md` | Findings register |
| `REVIEW_VALIDATION.md` | Test logs + integration evidence |
| `PAYLOAD_SCHEMA_AUDIT.md` | Phase 1 §2 output |

---

## 5. Remediation framework — preliminary design notes

### H1 + H5 (untyped metrics payloads)

**Options**:

- **Option A** — Add Pydantic models for every metrics payload; expose
  parsed objects from `get_metrics()`/`get_metrics_history()`/WS
  callbacks. Pros: schema enforced at the boundary; IDE autocomplete;
  drift caught immediately. Cons: tight coupling to server schema —
  every server-side field addition requires a client release.
- **Option B** — Use TypedDict for documentation-only typing; keep raw
  dicts at runtime. Pros: minimal wire change; no validation cost.
  Cons: no runtime enforcement; drift still silent.
- **Option C** — Light-weight runtime validation: `assert_metrics_keys()`
  helper that raises a structured `JuniperCascorSchemaError` when
  required keys are missing. Pros: catches drift at the boundary
  without locking schema. Cons: only catches missing keys, not type
  drift.

**Provisional recommendation**: **Option A** with Pydantic v2 in
`extra='allow'` mode — strict on documented fields, tolerant of new
ones the server adds. Best balance of safety and forward-compat.

### H2 + H3 (no reconnect / no backoff on WS)

**Options**:

- **Option A** — Built-in reconnection inside `CascorTrainingStream`:
  on `ConnectionClosed`, exponential backoff up to a max; resume from
  last-seen sequence (requires server cooperation — paired with the
  juniper-cascor `server_session_id` recommendation in plan 03).
  Pros: callers don't write boilerplate; correct by default.
  Cons: behavior change; existing callers' error-handling assumptions
  may break.
- **Option B** — Provide a `RetryingStream` wrapper as opt-in; keep
  `CascorTrainingStream` semantics unchanged.
  Pros: backward-compatible.
  Cons: opt-in default → most callers will lose reconnection.
- **Option C** — Document the gap clearly and shift responsibility to
  the caller. Pros: no code change. Cons: same problem at every
  caller site.

**Provisional recommendation**: **Option A**, with a `reconnect=False`
opt-out for callers who want raw behavior.

### H4 (no client-side instrumentation)

**Provisional**: matches recommendation in `02_juniper-data-client.md`
H2/H3 — add a request/event hook protocol, consistent across both
client libraries. Cross-cutting decision; coordinate via synthesis.

### H11 (unpinned `websockets`)

**Provisional**: pin `websockets>=11.0,<13.0` (or whatever the current
tested upper). Test against the next major in CI on a separate matrix
job before bumping the cap.

(Other hypotheses receive full remediation blocks during the actual
review.)

---

## 6. Tooling & commands

```bash
cd juniper-cascor-client
pip install -e ".[dev]"

# Full suite
pytest tests/ -v --tb=short \
  --cov=juniper_cascor_client --cov-report=term-missing

# Targeted observability paths
pytest tests/test_client.py::TestMetricsEndpoints \
       tests/test_ws_client.py -v

# Live integration smoke (requires juniper-cascor running)
JUNIPER_CASCOR_BASE_URL=http://localhost:8201 \
  python -c "from juniper_cascor_client import CascorClient; \
             import json; print(json.dumps(CascorClient().get_metrics(), indent=2))"
```

---

## 7. Owner / sign-off

- Plan owner: (assign during distribution)
- Reviewer: (assign during distribution)
- Sign-off blocked on: ecosystem roadmap §6.1 + downstream juniper-canopy
  smoke pass.
