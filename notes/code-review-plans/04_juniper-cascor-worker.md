# juniper-cascor-worker — Metrics & Monitoring Code Review Plan

**Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-cascor-worker/`
**Target file once distributed**: `juniper-cascor-worker/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
**Inherits**: `00_ECOSYSTEM_ROADMAP.md`
**Created**: 2026-04-24
**Phase**: B — Core service (run alongside juniper-cascor)

---

## 1. Scope

Metrics & monitoring surface of juniper-cascor-worker (distributed
candidate-training worker). In-scope:

- Per-worker metrics emitted with task results (correlation, success,
  epochs_completed, all_correlations)
- Heartbeat protocol (cadence, payload)
- Registration capabilities snapshot (CPU, GPU, versions)
- Self-instrumentation (or absence thereof — process metrics)
- Logging substrate
- Tests for the above
- WebSocket connection lifecycle as it affects metric delivery

Out-of-scope: candidate training algorithm, tensor numerics, mTLS
correctness beyond its impact on metric delivery.

---

## 2. Pre-existing evidence (from initial survey)

### 2.1 Surface inventory

**Per-task result** (`worker.py:247–262`, `task_executor.py:92–94`):
- `correlation` (float)
- `success` (bool)
- `epochs_completed` (int)
- `best_corr_idx` (int)
- `all_correlations` (list[float] per epoch — **unbounded list**)
- `numerator` / `denominator` normalization factors
- `error_message` on failure (string repr of exception)

**Heartbeat** (`worker.py:152–167`, default 10 s):
- `worker_id` + `timestamp` only
- **No** task throughput, queue depth, or resource state

**Registration** (`worker.py:278–291`):
- CPU cores, GPU availability/name, Python/PyTorch/NumPy versions, OS
- One-shot at startup; no periodic refresh

**Result delivery**:
- JSON message `MSG_TYPE_TASK_RESULT` followed by binary tensor frames
  (`worker.py:264–268`)
- ACK logged at DEBUG (`worker.py:188–190`); no retry / no error path
  if ACK is missing

### 2.2 Configuration

| Env var | Default | Effect |
|---------|---------|--------|
| `CASCOR_SERVER_URL` | (required) | WS URL of orchestrator |
| `CASCOR_AUTH_TOKEN` | (optional) | Auth |
| `CASCOR_HEARTBEAT_INTERVAL` | 10 s | Heartbeat cadence |
| `CASCOR_TASK_TIMEOUT` | 3600 s | Max task duration |
| `CASCOR_TLS_CERT/KEY/CA` | (optional) | mTLS |
| reconnect base / max | 1 s / 60 s | Exponential backoff |

**Note**: env var prefix is bare `CASCOR_*` — inconsistent with the
ecosystem's `JUNIPER_CASCOR_*` convention. Cross-cutting concern; see
ecosystem roadmap §5.3.

### 2.3 Process model

- WebSocket mode (default): single async loop + thread pool for training
- Legacy mode: multiprocessing fork-server (deprecated, retained)

### 2.4 Dependencies

- `websockets>=11.0`, `torch>=2.0.0`, `numpy>=1.24.0`
- **No** Prometheus, structlog, psutil, GPUtil, nvidia-ml-py
- **No** httpx fallback — pure WS only

### 2.5 Tests

- `TestHeartbeatLoop` (`test_worker_agent.py:328–373`)
- `TestBuildCapabilities` (`test_worker_agent.py:49–69`)
- `_handle_task_assign` indirectly (`test_worker_agent.py:461–527`)
- All tests `@pytest.mark.unit`; **no integration tests against a real
  orchestrator**

### 2.6 Already-suspected findings

| # | Hypothesis | File:line |
|---|------------|-----------|
| H1 | Task result ACK fire-and-forget — no retry / no detection if dropped | `worker.py:188–190` |
| H2 | No task execution timing instrumentation (no duration, no throughput) | `task_executor.py:111–131`, `worker.py:247–262` |
| H3 | Heartbeat carries no health state (no queue depth, no event-loop blocking, no thread-pool saturation indicator) | `worker.py:152–167` |
| H4 | Connection loss between `send_json(result)` and `send_bytes(tensors)` → partial result undetectable | `worker.py:264–268` |
| H5 | `error_message` truncated to `str(e)` — no structured error code | `worker.py:261` |
| H6 | Resource snapshot one-shot at registration; no periodic CPU/GPU refresh | `worker.py:278–291` |
| H7 | Legacy mode (CandidateTrainingWorker) emits zero metrics | `worker.py:351–467` |
| H8 | `all_correlations` list unbounded per task (epochs × candidates) — memory/wire size growth | `task_executor.py:92–94` |
| H9 | Env var prefix `CASCOR_*` violates ecosystem convention `JUNIPER_CASCOR_*` | `config.py:88–121`, `constants.py:89–95` |
| H10 | mTLS cert paths read once at startup; no rotation / no error if file rotated under foot | `ws_connection.py:68` |
| H11 | No integration test against a real / mock orchestrator (only unit tests) | tests |
| H12 | No test for metric loss during disconnect/reconnect | tests |
| H13 | No test for dropped result ACK | tests |
| H14 | No timing/latency measurement tests | tests |
| H15 | No GPU OOM / CPU saturation resource-exhaustion tests | tests |
| H16 | No TODO/FIXME markers in source for metrics — no institutional acknowledgement of gaps | source |
| H17 | AGENTS.md "Project Overview" makes no mention of observability expectations | docs |
| H18 | Logging is plain-text only (`%(asctime)s [%(levelname)s] %(name)s: %(message)s`); no structured/JSON option, no log aggregation hook. Limits centralized log analytics. | logging config in `worker.py` / `cli.py` |
| H19 | `CASCOR_AUTH_TOKEN` accepted only via env var (no secret-file path). DEBUG logs may leak token if not audited. | `config.py`, `ws_connection.py` |
| H20 | **Legacy manager env vars still in the code** (`CASCOR_MANAGER_HOST`/`_PORT`, `CASCOR_AUTHKEY`, `CASCOR_NUM_WORKERS`, `CASCOR_MP_CONTEXT`). Dead for current WS mode but still read from env. Confuses operators; review-time decision to deprecate. | `constants.py:134–138`, `config.py:116–120` |
| H21 | **Deprecated alias `CASCOR_API_KEY`** exists for `_AUTH_TOKEN` — document sunset path alongside the worker's ecosystem-convention migration (H9). | `constants.py:128` |

---

### 2.7 Audit corrections (2026-04-24)

- All `:line` citations in §2.1–§2.5 verified.
- **H7 phrasing refined**: legacy mode (`CandidateTrainingWorker`) is
  a queue-based consumer; metric content sent via `result_queue.put()`
  is whatever the queue producer writes. Plan should read "no explicit
  metric emission contract" rather than "emits zero metrics".
- **H6 expansion**: `torch.cuda.memory_allocated()` and
  `torch.cuda.max_memory_allocated()` provide GPU memory metrics with
  **zero new dependencies**. Can be added even before deciding on
  optional `nvidia-ml-py`.
- **H17 confirmed**: AGENTS.md has no Observability section; metrics
  mentioned only in passing.

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk emitted metrics catalog against `main`.
2. Document the WS frame protocol used for result delivery (JSON + binary
   tensor sequence): exact framing, expected ordering, error semantics.
3. Cross-reference orchestrator side (`juniper-cascor` worker
   coordinator) to confirm the contract is mutually documented.

### Phase 2 — Functionality verification

1. Spin up a mock orchestrator (or a real `juniper-cascor` instance);
   run a worker; capture wire traffic.
2. Verify heartbeat cadence matches `CASCOR_HEARTBEAT_INTERVAL`.
3. Inject failures: kill connection mid-result, drop ACK on orchestrator
   side, deliver malformed task — observe worker behavior. Confirm or
   refute H1, H4.
4. Run a long task (hours); inspect memory growth (`all_correlations`
   accumulation — confirms H8).

### Phase 3 — Test-suite audit

1. Full run:
   ```bash
   cd juniper-cascor-worker
   pytest tests/ -v --tb=short \
     --cov=juniper_cascor_worker --cov-report=term-missing
   ```
2. Inventory gaps in test categories (no integration tests is the
   headline gap).
3. Verify each test on metric paths actually asserts the value/shape.

### Phase 4 — Issue classification

Apply ecosystem framework §3.1–3.2.

### Phase 5 — Remediation design

See §5.

### Phase 6 — Validation

1. Land remediations.
2. Re-run unit suite; add integration tests to cover H11–H15.
3. Cross-repo smoke against `juniper-cascor` orchestrator.

### Phase 6.5 — Security & secret-handling review (added)

1. Audit DEBUG log output for `CASCOR_AUTH_TOKEN` leak (H19);
   suppress the value at the logger level via a filter.
2. Decide whether to support a `CASCOR_AUTH_TOKEN_FILE` alternative
   (file path read at startup) for compatibility with k8s secret
   mounts.
3. Confirm mTLS cert paths are never logged; confirm cert-rotation
   behavior is documented (paths re-read at reconnect, or
   process-restart required — H10 paired finding).

### Phase 6.6 — CI/CD review (added)

1. Read `.github/workflows/*.yml`; record matrix coverage and
   whether worker integration tests (currently absent) are stubbed.
2. If a mock-orchestrator integration test is added during
   remediation (H11–H15), wire it into CI.

### Phase 7 — Documentation

1. Update worker `CLAUDE.md` / `AGENTS.md` with observability
   expectations (addresses H17).
2. CHANGELOG entry.

---

## 4. Deliverables

| File | Contents |
|------|----------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan |
| `REVIEW_FINDINGS.md` | Findings register |
| `REVIEW_VALIDATION.md` | Test logs + protocol-level evidence |
| `WORKER_PROTOCOL.md` | Wire-protocol doc (or pointer if it lives in cascor) |

---

## 5. Remediation framework — preliminary design notes

### H1 + H4 (ACK fire-and-forget + partial-result on disconnect)

These are the same root cause: lack of an at-least-once delivery
contract on result frames.

**Options**:

- **Option A** — Wrap result emission in a request/response with a
  bounded retry: send JSON+tensors, await ACK with timeout, retry up to
  N times; on exhaustion, persist to local outbox file and reconnect.
  Pros: at-least-once; no result loss on transient disconnect.
  Cons: complexity; orchestrator must dedupe by task_id.
- **Option B** — Single atomic message: pack JSON header + tensor blob
  into one binary frame (length-prefixed). Disconnect mid-frame is
  detectable (no partial application). Pros: simpler; no protocol
  state. Cons: large frames may stress WS framing.
- **Option C** — Accept best-effort delivery; add a metric
  `result_delivery_failures_total` and rely on the orchestrator to
  re-dispatch if the ACK never arrives. Pros: minimal change.
  Cons: still loses results; only adds visibility.

**Provisional recommendation**: **Option A** (at-least-once with outbox)
for production reliability; **Option B** as a simplification if the
outbox is too heavy. **Option C** alone is insufficient.

### H2 + H3 (no timing, no health state)

**Provisional**: extend the heartbeat payload to include:
`task_id_in_progress | None`, `task_started_at`, `tasks_completed_total`,
`tasks_failed_total`, `last_heartbeat_loop_lag_ms`. Add per-task
duration to result message. Add `psutil` (optional dependency) for
`cpu_percent`, `mem_percent` in heartbeat — gated on a flag so airgap
deployments can opt out.

### H7 (legacy mode emits zero metrics)

**Provisional**: confirm legacy mode is actually still used; if not,
mark for removal. If still used, port the new metric emission shape from
WebSocket mode. Severity depends on whether legacy mode is in production.

### H8 (`all_correlations` unbounded)

**Provisional**: cap to last-N (configurable, default 100) and emit a
`all_correlations_truncated_count` field if truncation occurred.
Alternatively, emit a histogram summary (min/max/mean/p50/p95) instead
of raw list.

### H9 (env var prefix)

**Cross-cutting** — see ecosystem roadmap §5.3. Per-app plan flags;
synthesis decides on a normalization plan (likely a deprecation cycle:
accept both `CASCOR_*` and `JUNIPER_CASCOR_*` for two minor releases,
then drop the bare form).

### H17 (no observability mention in AGENTS.md)

**Provisional**: add an "Observability" section to AGENTS.md once the
emission contract is finalized. Trivial effort; high documentation
value.

(Other hypotheses receive full remediation blocks during the actual
review.)

---

## 6. Tooling & commands

```bash
# Library lives in any Python env; no dedicated conda env
cd juniper-cascor-worker
pip install -e ".[dev]"

# Full unit suite
pytest tests/ -v --tb=short \
  --cov=juniper_cascor_worker --cov-report=term-missing

# Local smoke against running cascor (requires JuniperCascor service)
CASCOR_SERVER_URL=ws://localhost:8201/ws/workers \
  python -m juniper_cascor_worker --log-level DEBUG
```

---

## 7. Owner / sign-off

- Plan owner: (assign during distribution)
- Reviewer: (assign during distribution)
- Sign-off blocked on: ecosystem roadmap §6.1 + paired juniper-cascor
  protocol agreement.
