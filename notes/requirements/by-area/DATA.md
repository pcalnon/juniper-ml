# Requirements — DATA

**Area**: data-pipeline — dataset generation, NPZ contracts, ingestion

**Total entries**: 13

**By status**: proposed=9 | shipped=4

**By priority**: P0=4 | P2=9

**By owner**: ml=9 | dat=4

---

### JR-DAT-DATA-001 — All 7 storage backends implemented and tested: memory, localfs, cached, redis, hf, postgres, kaggle.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-015 complete. All implementations present.

### JR-DAT-DATA-002 — All 8 generators registered in GENERATOR_REGISTRY: spiral, xor, gaussian, circles, checkerboard, csv_import, mnist, arc_agi.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-17.md` (lines 29-32)

**Notes**:

Status verified as shipped. All 8 confirmed in api/routes/generators.py. RD-001.

### JR-DAT-DATA-003 — Lifecycle management supports tagging, TTL, expiration via DatasetMeta (tags, ttl_seconds, expires_at).

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-016 complete.

### JR-DAT-DATA-004 — NPZ contract guarantees 6 array keys with float32 dtype and one-hot label encoding.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

Foundational data contract enforced by E2E tests.

### JR-ML-DATA-001 — Canopy metrics normalization must maintain dual-format backward compatibility (nested + flat metric keys).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_plan.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1371-1382)

**Detail**:

Phase H: test test_normalize_metric_produces_dual_format before any audit PR.
test_normalize_metric_nested_topology_present, test_normalize_metric_preserves_legacy_timestamp_field.
Write consumer audit doc listing every consumer of nested vs flat keys across canopy frontend.
Explicit recommendation: do NOT remove either format without landing this test first.

**Notes**:

RISK-01. Phase H (Day 12) regression gate. Must not ship Phase B without test in place.

### JR-ML-DATA-002 — JD-PERF-01: Sync `generator.generate()` Blocks Event Loop.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3534-3538)

### JR-ML-DATA-003 — JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3541-3555)

### JR-ML-DATA-004 — JD-PERF-03: `list_versions` Loads All Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3558-3569)

### JR-ML-DATA-005 — JD-PERF-04: No Connection Pooling for Postgres.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3572-3586)

### JR-ML-DATA-006 — JD-PERF-05: Readiness Probe Filesystem Glob.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3589-3593)

### JR-ML-DATA-007 — JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3485-3507)

### JR-ML-DATA-008 — JD-SEC-02: API Key Comparison Not Constant-Time (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3510-3518)

### JR-ML-DATA-009 — JD-SEC-03: Rate Limiter Memory Unbounded (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3521-3529)

