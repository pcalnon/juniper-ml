# Requirements — status: deferred

**Total entries**: 8

**By priority**: P1=1 | P2=4 | P3=3

**By category**: OBS=3 | ARCH=2 | TEST=1 | SEC=1 | PERF=1

**By owner**: ml=3 | dat=3 | dep=1 | cas=1

---

### JR-DEP-OBS-007 — Replace log-only burn-rate alert severity with paging severity after 30-day soak period.

**Status**: deferred  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 918-932)

**Detail**:

All numeric SLO targets in §3 are initial and provisional. R5.4 ships burn-rate alerts in
log-only severity. After 30-day production soak window (target 2026-06-15), compare actual
burn rates against targets, tighten or relax as needed, and lift log-only severity to paging
for §3.1, §3.2, §3.5 (which have all pre-conditions met today).

### JR-CAS-TEST-006 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-ML-SEC-029 — Per-command HMAC deferred indefinitely.

**Status**: deferred  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 70-70)

**Notes**:

Settled position C-33 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-012 — Re-bucket cascor_ws_command_handler_seconds for better SLO breach-detection precision post-soak.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 173-182)

**Detail**:

G7 - 50 ms SLO target sits one bucket below 100 ms +inf cap, limiting breach-detection precision.
Deferred to R5.1c post-soak calibration per juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md.

### JR-ML-ARCH-259 — Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: deferred  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 61-61)

**Notes**:

Settled position C-24 from R3-03 table; cross-round consensus consolidation

### JR-DAT-OBS-007 — Continuous profiling (Grafana Pyroscope, Prometheus, OpenTelemetry) deferred until production deployment.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 493-516)

**Notes**:

RD-017 (DATA-020). Deferred. Partially addressed with Prometheus + Sentry in commit 830a0ef.

### JR-DAT-PERF-001 — GPU acceleration (CuPy, JAX, PyTorch) deferred until >1M points or >30s generation time.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 468-490)

**Notes**:

RD-016 (DATA-019). Deferred. PyTorch no longer a dependency. CUDA not in CI.

### JR-DAT-ARCH-001 — IPC architecture (gRPC, message queue, shared memory, WebSocket) deferred until REST bottleneck or >100MB datasets.

**Status**: deferred  **Priority**: P3  **Category**: ARCH  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 438-465)

**Notes**:

RD-015 (DATA-018). Deferred. REST migration success reduced urgency.

