# Ecosystem Prometheus metric catalog

**Companion to**: `00_ECOSYSTEM_ROADMAP.md` §5.7
**Created**: 2026-04-24 (Phase D extraction)
**Status**: Reference table — verify against `main` HEAD before
relying on specific line numbers.

---

## 1. Purpose

A single-source table of every Prometheus instrument defined across
the three FastAPI services (juniper-data, juniper-cascor,
juniper-canopy). The three client/worker libraries do not expose
Prometheus surfaces (see `07_ENV_VAR_INVENTORY.md` §8–§9 and
`04_juniper-cascor-worker` §2.1 for their emitted fields).

---

## 2. Conventions

- **Type**: `C` = Counter, `G` = Gauge, `H` = Histogram, `I` = Info.
- **Emitted?**: `yes` = called from production code path;
  `NO` = defined in `observability.py` but **never called** outside
  test files; `yes (test)` = only test callsites.
- **Cardinality**: enumerated = small fixed set, bounded = known upper
  bound, unbounded = depends on raw input (risk).

---

## 3. TL;DR — the scariest cross-cutting finding

**Of 38 metrics defined across the ecosystem, ~20 are never emitted
from production code** — they exist as declarations in
`observability.py` with no callsites outside test files. Breakdown:

| Service | Defined | Actually emitted | Defined-but-unused |
|---------|---------|------------------|--------------------|
| juniper-data | 6 | 3 (HTTP × 2 + build) | **3** (dataset generation × 2 + cached gauge — H1 already flags) |
| juniper-cascor | 26 | 2 (HTTP middleware only) + 1 conditional build | **23** (8 training/inference + 15 WS Phase-0) |
| juniper-canopy | 6 | 3 (HTTP × 2 + build) | **3** (WS connections gauge + WS messages counter + demo-mode gauge) |
| **TOTAL** | **38** | **~9** | **~29** |

This is the juniper-data H1 ("architecturally complete but
operationally hollow") problem **scaled to the whole ecosystem**.

Ecosystem synthesis must treat this as its own cross-cutting concern
(see `00_ECOSYSTEM_ROADMAP.md` §5.10 added below). The per-app plans
already flag pieces of this (data H1, cascor H14 indirectly, canopy
H15 indirectly); the extraction turns it from speculation into fact.

---

## 4. juniper-data — 6 metrics

| Metric | Type | Labels | Emitted? | Cardinality risk | Defined (file:line) | Emitted (file:line) |
|--------|------|--------|----------|------------------|---------------------|---------------------|
| `juniper_data_http_requests_total` | C | method, endpoint, status | yes | **endpoint** = raw path (unbounded) | observability.py:78–79 | observability.py:102 |
| `juniper_data_http_request_duration_seconds` | H | method, endpoint | yes | same | observability.py:83–86 | observability.py:103 |
| `juniper_data_dataset_generations_total` | C | generator, status | **NO** (H1 symptom) | bounded | observability.py:199–202 | observability.py:227 (helper; never called) |
| `juniper_data_dataset_generation_duration_seconds` | H | generator | **NO** | bounded | observability.py:204–208 | observability.py:229 (helper; never called) |
| `juniper_data_datasets_cached` | G | (none) | **NO** | n/a | observability.py:210–212 | observability.py:238 (helper; never called) |
| `juniper_data_build` | I | version, python_version | yes | enumerated | observability.py:180–181 | app.py:41 |

**Histogram buckets** (generation_duration): `(0.01, 0.05, 0.1, 0.25,
0.5, 1.0, 2.5, 5.0, 10.0, 30.0, +Inf)`

---

## 5. juniper-cascor — 26 metrics (highest-risk surface)

### 5.1 HTTP middleware (2 — both emitted)

| Metric | Type | Labels | Emitted? | Cardinality | Defined | Emitted |
|--------|------|--------|----------|-------------|---------|---------|
| `juniper_cascor_http_requests_total` | C | method, endpoint, status | yes | **endpoint** unbounded | observability.py:72–76 | :97 |
| `juniper_cascor_http_request_duration_seconds` | H | method, endpoint | yes | same | :77–81 | :98 |

HTTP histogram uses **default Prometheus buckets** (no custom config).

### 5.2 Training & inference (8 — **all NO**)

| Metric | Type | Labels | Emitted? | Defined |
|--------|------|--------|----------|---------|
| `juniper_cascor_training_sessions_active` | G | — | **NO** | :223–226 |
| `juniper_cascor_training_epochs_total` | C | phase | **NO** | :227–231 |
| `juniper_cascor_training_loss` | G | phase, loss_type | **NO** | :232–236 |
| `juniper_cascor_training_accuracy_ratio` | G | phase | **NO** | :237–241 |
| `juniper_cascor_hidden_units_total` | G | — | **NO** | :242–245 |
| `juniper_cascor_candidate_correlation` | G | — | **NO** | :246–249 |
| `juniper_cascor_inference_requests_total` | C | — | **NO** | :250–253 |
| `juniper_cascor_inference_duration_seconds` | H | — | **NO** | :254–258 |

**Training/inference histogram buckets**: `(0.001, 0.005, 0.01, 0.05,
0.1, 0.5, 1.0, 2.5, 5.0, +Inf)` — `constants_logging.py:280`.

### 5.3 WebSocket Phase 0 (15 — **all NO**)

| Metric | Type | Labels | Defined |
|--------|------|--------|---------|
| `cascor_ws_seq_current` | G | — | :348 |
| `cascor_ws_replay_buffer_occupancy` | G | — | :352 |
| `cascor_ws_replay_buffer_bytes` | G | — | :356 |
| `cascor_ws_replay_buffer_capacity_configured` | G | — | :360 |
| `cascor_ws_resume_requests_total` | C | outcome | :364 |
| `cascor_ws_resume_replayed_events` | H | — | :369 |
| `cascor_ws_broadcast_timeout_total` | C | type | :374 |
| `cascor_ws_broadcast_send_duration_seconds` | H | type | :379 |
| `cascor_ws_pending_connections` | G | — | :384 |
| `cascor_ws_state_throttle_coalesced_total` | C | — | :388 |
| `cascor_ws_broadcast_from_thread_errors_total` | C | — | :392 |
| `cascor_ws_seq_gap_detected_total` | C | — | :396 |
| `cascor_ws_connections_active` | G | endpoint | :400 |
| `cascor_ws_command_responses_total` | C | command, status | :405 |
| `cascor_ws_command_handler_seconds` | H | command | :410 |

**Notable**: naming is inconsistent — most use `cascor_ws_*` prefix
(no `juniper_` namespace) while training/inference metrics use
`juniper_cascor_*`. Naming-convention finding for synthesis.

**Resume-replayed buckets**: `(0, 1, 5, 25, 100, 500, 1024)`.
**Broadcast / command-handler buckets**: default Prometheus buckets.

### 5.4 Build (1 — conditionally emitted)

| Metric | Type | Labels | Emitted? | Defined |
|--------|------|--------|----------|---------|
| `juniper_cascor_build` | I | version, python_version | yes (if `metrics_enabled=true`) | :204–205 |

---

## 6. juniper-canopy — 6 metrics

| Metric | Type | Labels | Emitted? | Cardinality | Defined | Emitted |
|--------|------|--------|----------|-------------|---------|---------|
| `juniper_canopy_http_requests_total` | C | method, endpoint, status | yes | **endpoint** unbounded | observability.py:67 | :93 |
| `juniper_canopy_http_request_duration_seconds` | H | method, endpoint | yes | same | :72 | :94 |
| `juniper_canopy_build` | I | version, python_version | yes (startup) | enumerated | :170 | :171 (via `set_build_info`) |
| `juniper_canopy_websocket_connections_active` | G | channel | **NO** | enumerated | :189 | :214 (helper; no prod caller found) |
| `juniper_canopy_websocket_messages_total` | C | channel, type | **NO** | enumerated | :194 | :224 (helper; no prod caller found) |
| `juniper_canopy_demo_mode_active` | G | — | **NO** | n/a | :200 | :233 (helper; no prod caller found) |

Half the canopy surface is defined-but-unused — matches the cascor
pattern.

---

## 7. Cross-cutting observations

### 7.1 Naming convention drift

- `juniper_data_*` — clean (all metrics)
- `juniper_cascor_*` for training/inference/build/HTTP — clean
- `cascor_ws_*` (no `juniper_` prefix) for 15 of 26 cascor metrics —
  **inconsistent**; likely created during Phase 0 WS work without a
  naming review
- `juniper_canopy_*` — clean (all metrics)

**Synthesis decision**: pick one (rename the 15 to `juniper_cascor_ws_*`),
or document the split. Breaks dashboards on rename — plan a
deprecation period with dual emission.

### 7.2 Label cardinality

Every service's HTTP middleware uses `endpoint = request.url.path`
(raw). This is **the same bug in three places** (roadmap §5.7). Fix
is mechanical: `request.scope["route"].path` or FastAPI route template.

### 7.3 Defined-but-unused (the big one)

Of 26 cascor metrics, 24 have no production callsite. Of 6 canopy
metrics, 3 have no production callsite (the WS gauges/counters). Root
cause appears to be: emission helpers were defined in a standalone
observability module, but the training-loop / WebSocket-manager code
never imported and called them.

**Remediation options** (for ecosystem synthesis — not per-app plan):

- **Option A** — Wire the helpers into their natural emission sites
  (training loop emits training metrics, WS manager emits WS metrics).
  Pros: realizes the intended design. Cons: ~20 integration points;
  testing effort non-trivial.
- **Option B** — Delete the defined-but-unused metrics; declare the
  ecosystem's intended observability contract as "HTTP + build only"
  for this release; commit to A as a follow-up.
  Pros: removes 20+ lines of dead code now; truthful declarations.
  Cons: loses design signal; re-adding later requires the wiring
  work anyway.
- **Option C** — Mark unused metrics explicitly with a `_defined = True`
  convention or separate module, and emit a single warning at startup:
  "N metrics defined but not emitted in this build — see …".
  Pros: callers know; dashboards can be built against the design.
  Cons: doesn't fix anything, just makes the gap visible.

**Provisional recommendation**: **Option A** for the release cycle.
If Option A is out of scope, ship Option B and add Option A to the
backlog.

### 7.4 Endpoint-label correlation

juniper-canopy WS metrics label `channel` (`/ws/train`, `/ws/control`)
— correct enumerated cardinality. juniper-cascor WS metrics split
across `endpoint`, `type`, `command`, `outcome` labels — generally
enumerated. Good. HTTP middleware is the only unbounded surface.

---

## 8. Ties back to individual per-app plans (status)

| Plan | Finding | Status (post-Phase-E re-run) |
|------|---------|------------------------------|
| 01 data | §7.1 naming clean | No action beyond existing H1 |
| 01 data | §7.2 cardinality | Covered by H12 ✓ |
| 01 data | §7.3 dataset metrics unused | Covered by H1 + new H14 ✓ |
| 03 cascor | §7.1 `cascor_ws_*` naming drift | Added as **H18** ✓ |
| 03 cascor | §7.2 cardinality | Covered by H8 ✓ |
| 03 cascor | §7.3 23 unused metrics | Added as **H19** ✓ |
| 03 cascor | §7.4 default-bucket mismatch | Added as **H21** ✓ |
| 06 canopy | §7.3 3 unused metrics | Added as **H20** ✓ |

All catalog findings are now reflected in per-app plans.

---

## 9. Emitted-metric exposition coverage

Metrics that a scrape of `/metrics` on each service will **actually**
return (as of 2026-04-24 `main`):

- **juniper-data**: `juniper_data_http_{requests_total,
  request_duration_seconds}`, `juniper_data_build` (3 instruments)
- **juniper-cascor**: `juniper_cascor_http_{requests_total,
  request_duration_seconds}`, `juniper_cascor_build` (3 instruments)
- **juniper-canopy**: `juniper_canopy_http_{requests_total,
  request_duration_seconds}`, `juniper_canopy_build` (3 instruments)

**Practical implication**: any Grafana dashboard built today against
the declared metric names will show empty panels for training, WS,
dataset-generation, demo-mode, and cached-datasets.

---

## 10. Plan-update checklist — completed 2026-04-24

- [x] Plan 01 — H13 (env-var undercount), H14 (extraction confirms H1)
- [x] Plan 03 — H18 (`cascor_ws_*` naming drift), H19 (23 unused
  metrics), H20 (env-var undercount), H21 (default-bucket mismatch)
- [x] Plan 04 — H20 (legacy manager env vars), H21 (deprecated alias)
- [x] Plan 06 — H20 (3 unused metrics), H21 (env-var undercount —
  large security surface), H22 (audit-log path default)
- [x] Roadmap — §5.9 (defined-but-unused), §5.10 (prefix drift) added
- [x] Roadmap — §9 open questions extended with Option A/B/C and
  rate-limit-default decisions
- [x] Roadmap — §6.2 validation gates extended to require §5.9 and
  §5.10 decisions before sign-off
