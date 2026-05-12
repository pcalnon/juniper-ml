# Requirements — juniper-cascor (cas)

**Total entries**: 46

**By status**: proposed=21 | shipped=24 | deferred=1

**By priority**: P0=11 | P1=15 | P2=16 | P3=4

**By category**: TRAIN=15 | TEST=8 | ARCH=6 | OBS=5 | API=4 | LOCK=2 | DOC=2 | TOOL=2 | PERF=2

---

### JR-CAS-LOCK-001 — Add missing PyYAML, h5py, pytest-cov, psutil dependencies to conda environment.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 256-306)

### JR-CAS-DOC-001 — Document that CascadeCorrelationNetwork is not thread-safe.

**Status**: shipped  **Priority**: P0  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 183-198)

### JR-CAS-TRAIN-001 — Fix candidate task parameter wiring: use correct dictionary keys (candidate_seed, candidate_epochs, candidate_learning_rate).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 235-273)

### JR-CAS-TRAIN-002 — Fix candidate training runtime errors (method name mismatch, pickling, parameter handling).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 94-122)

**Detail**:

Fix _train_candidate_worker → _train_candidate_unit method call mismatch; add __getstate__/__setstate__ to LogConfig and CascadeCorrelationConfig for multiprocessing pickling support; update CascadeCorrelationNetwork.__getstate__ to exclude log_config.

### JR-CAS-TRAIN-003 — Fix logger pickling error in multiprocessing (BUG-002).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 28-36)

**Detail**:

Enhance CascadeCorrelationNetwork and CascadeCorrelationPlotter __getstate__/__setstate__ methods for pickle support; verify CandidateUnit has pickling support.

### JR-CAS-TRAIN-004 — Fix multiprocessing completion logic that can hang indefinitely due to unreliable empty()/qsize() usage.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 59-99)

**Detail**:

Replace unreliable busy-wait loop using Manager queue empty()/qsize() with bounded timeout loop. Add worker liveness checks to detect crashed workers early. Exit immediately when all workers complete.

### JR-CAS-TRAIN-005 — Fix plotting subprocess to use spawn context instead of forkserver for reliable module import in child processes.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 342-386)

### JR-CAS-TRAIN-006 — Fix save_object() method TypeError due to argument count mismatch with _save_root_attributes().

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 200-232)

### JR-CAS-TRAIN-007 — Fix test random state restoration failures (BUG-001).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 18-26)

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-CAS-API-001 — Build FastAPI service layer for CasCor with REST endpoints and WebSocket streaming.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 728-735)

**Detail**:

Add 19 REST endpoints across 6 route files; WebSocket endpoints for real-time training streaming (/ws/training, /ws/control); TrainingLifecycleManager with thread-safe state machine and ThreadPoolExecutor; service entry point (server.py) alongside existing CLI (main.py).

### JR-CAS-ARCH-001 — CasCor must expose REST API for training lifecycle operations (19 endpoints).

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-735)

**Detail**:

FastAPI service layer with REST endpoints for all training lifecycle operations; WebSocket endpoints for real-time streaming (/ws/training, /ws/control); ThreadPoolExecutor for blocking training.

### JR-CAS-ARCH-002 — CasCor service API must serialize training access via lock or dedicated thread.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-674)

**Detail**:

CascadeCorrelationNetwork is NOT thread-safe. API layer must serialize access via a lock or run training in dedicated thread with message-passing interface.

### JR-CAS-TEST-002 — Create comprehensive test suite for serialization with 6+ test cases.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 38-51)

**Detail**:

Implement test_deterministic_training_resume, test_hidden_units_preservation, test_config_roundtrip, test_activation_function_restoration, test_torch_random_state_restoration, test_history_preservation.

### JR-CAS-TEST-003 — Create GitHub Actions CI/CD workflow with pytest, coverage, mypy, and linting.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 467-507)

### JR-CAS-ARCH-003 — Create juniper-cascor-client and juniper-cascor-worker installable packages with PyPI publishing.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1034-1047)

### JR-CAS-ARCH-004 — Decouple Canopy from CasCor via service client; remove direct imports and sys.path manipulation.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1208-1220)

**Detail**:

Implement CascorServiceAdapter for two-mode activation (demo/service); remove legacy CascorIntegration (~1,601 lines); remove sys.path manipulation; update configuration to use CASCOR_SERVICE_URL (port 8200).

### JR-CAS-TRAIN-008 — Expand format validation for HDF5 snapshot files.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 73-83)

**Detail**:

Check format name/version; validate required groups and datasets; verify hidden units consistency.

### JR-CAS-TRAIN-009 — Implement hidden units checksums for integrity verification.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 53-61)

### JR-CAS-TRAIN-010 — Implement shape validation for serialized network structure.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 63-71)

**Detail**:

Implement _validate_shapes() method; validate output layer and hidden units; call from load_network().

### JR-CAS-API-002 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-CAS-API-003 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-CAS-TEST-004 — Establish automated CI/CD pipeline with pytest, coverage, type checking, and linting.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 569-599)

### JR-CAS-TEST-005 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

### JR-CAS-OBS-002 — Define Prometheus histogram buckets for latency metrics per observability requirements.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-50)

**Notes**:

See histogram_rationale file for bucket selection rationale.

### JR-CAS-TRAIN-011 — Implement flexible optimizer system supporting Adam, SGD, RMSprop, AdamW.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

OptimizerConfig dataclass and _create_optimizer() method already exist in codebase.

### JR-CAS-TRAIN-012 — Implement N-best candidate selection (candidates_per_layer configuration).

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

_select_best_candidates() and add_units_as_layer() methods already exist.

### JR-CAS-TEST-006 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-CAS-PERF-001 — Add GPU/CUDA support for all tensor operations and training.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 885-912)

### JR-CAS-TEST-007 — Backward compatibility testing with old serialized snapshots.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

### JR-CAS-API-004 — CasCor service API must support separate network_epochs and candidate_epochs parameters.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 562-566)

**Notes**:

Requires API contract extension; juniper-cascor-client start_training() method update.

### JR-CAS-OBS-003 — Create baseline py-spy profiles for key operations to enable performance regression detection.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 850-854)

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

### JR-CAS-DOC-002 — Fix import alias mistake: datetime import uses pd instead of dt.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 362-366)

**Detail**:

Line 38 of cascade_correlation.py: 'import datetime as pd' should be 'import datetime as dt'. pd is conventionally pandas; using for datetime misleads developers.

### JR-CAS-TRAIN-013 — Fix validate_training_results None initialization bug in training loop.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 374-378)

**Detail**:

Variable initialized as None; if training loop doesn't execute (e.g. max_epochs=0), debug log crashes with AttributeError on .early_stop.

### JR-CAS-TEST-008 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-CAS-ARCH-005 — Remove direct absolute path hardcoding that breaks on non-development machines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 142-146)

**Notes**:

Use relative paths or environment-relative configuration.

### JR-CAS-ARCH-006 — Replace Path truthiness checks with explicit None checks.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 394-398)

**Detail**:

Path objects are always truthy even for empty strings. Use 'if x is None' instead of 'or' fallback patterns (lines 3015, 3096, 471).

### JR-CAS-TRAIN-014 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

### JR-CAS-TRAIN-015 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

### JR-CAS-PERF-002 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

### JR-CAS-LOCK-002 — Reconcile version across pyproject.toml, file headers, and API response metadata.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 820-824)

**Detail**:

Consider using single-source-of-truth version via importlib.metadata.version() instead of file header strings.

### JR-CAS-TOOL-002 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

