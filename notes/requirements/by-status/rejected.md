# Requirements — status: rejected

**Total entries**: 17

**By priority**: P0=3 | P1=5 | P2=9

**By category**: SEC=9 | DATA=2 | TRAIN=1 | API=1 | OBS=1 | ARCH=1 | UI=1 | OPS=1

**By owner**: ml=17

---

### JR-ML-SEC-011 — 3.3 Operating Mode Options for Microservices.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 388-438)

**Detail**:

#### Option 1: Runtime Feature Flag (Current Approach, Enhanced)

### JR-ML-SEC-012 — By Category.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 421-436)

### JR-ML-SEC-013 — `_create_optimizer` references undefined `OptimizerConfig` attributes — crashes on non-default optimizer types.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 648-680)

### JR-ML-SEC-058 — 4.0 Phase 2 Execution Results (2026-04-09).

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 336-360)

**Detail**:

`fix/interface-phase2-docs` in juniper-ml. All four issues were verified

### JR-ML-TRAIN-014 — 4.1 CR-023: Whitelist Training Start Parameters.

**Status**: rejected  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 360-378)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added

### JR-ML-SEC-059 — Issue Remediations, Section 18.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_a_security_concurrency_error.md` (lines 463-513)

**Detail**:

#### ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client)

### JR-ML-API-007 — Issue Remediations, Section 21.

**Status**: rejected  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 692-742)

**Detail**:

#### API-01: Health `status` Value Inconsistent

### JR-ML-DATA-007 — Task 2 (Dataset).

**Status**: rejected  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 374-381)

### JR-ML-OBS-059 — 1.2 Network Topology Visualization Issues.

**Status**: rejected  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 93-143)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

### JR-ML-DATA-010 — 2.6 juniper-data-client.

**Status**: rejected  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 348-359)

**Detail**:

| DC-01 | **High**   | `constants.py`           | 91–92   | Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server |

### JR-ML-SEC-119 — 2.7 juniper-deploy.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 359-369)

**Detail**:

| DD-01 | **High** | `docker-compose.yml`           | 129, 298, 349, 386 | Cascor and canopy ports bound to `0.0.0.0` — exposed to network (data correctly uses `127.0.0.1`)                |

### JR-ML-SEC-120 — 2A. Validation Loss/Accuracy Overlay Traces.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 74-88)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-ARCH-210 — 4.2 Cross-Section Checkbox Linking.

**Status**: rejected  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 234-257)

**Detail**:

- Uses `ctx.triggered_id` to determine which checkbox changed

### JR-ML-UI-024 — 7.5 Shutdown Signal Handling.

**Status**: rejected  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 453-468)

**Detail**:

All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown completed.

### JR-ML-SEC-121 — Issue Remediations, Section 15 — juniper-cascor-client.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 323-373)

**Detail**:

#### CC-01: `_recv_loop` Catches Bare `Exception`

### JR-ML-SEC-122 — Issue Remediations, Section 15 — juniper-cascor-worker.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 561-611)

**Detail**:

#### CW-01: `receive_json()` Doesn't Catch JSONDecodeError

### JR-ML-OPS-004 — Shadow traffic: rejected.

**Status**: rejected  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 68-68)

**Notes**:

Settled position C-31 from R3-03 table; cross-round consensus consolidation

