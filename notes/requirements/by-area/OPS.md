# Requirements — OPS

**Area**: operations / runbooks / on-call — runbook documents, incident response

**Total entries**: 10

**By status**: proposed=7 | shipped=2 | rejected=1

**By priority**: P0=2 | P1=2 | P2=6

**By owner**: ml=6 | dep=2 | ccl=2

---

### JR-DEP-OPS-001 — Fix critical AGENTS.md documentation errors: Grafana password, rate limiting defaults.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 9-26)

**Detail**:

Phase 1 (P0 priority, blocks other work). Step 1.1: Replace GRAFANA_ADMIN_PASSWORD
default 'admin' with GF_SECURITY_ADMIN_PASSWORD__FILE referencing Docker secret.
Step 1.2: Update JUNIPER_CASCOR_RATE_LIMIT_ENABLED and CANOPY_RATE_LIMIT_ENABLED
defaults from false to true (matches docker-compose.yml).

### JR-ML-OPS-001 — Phase B-pre gate (after Day 6) requires 8 criteria: all M-SEC-NN landed, audit logger, 24h staging, risk sheet.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-06_ops_phasing_risk.md` (lines 79-110)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 850-870)

**Detail**:

1. M-SEC-01 landed (Day 4)
2. M-SEC-01b landed (Day 4)
3. M-SEC-02 landed (Day 5)
4. M-SEC-03 landed (Day 5)
5. M-SEC-04 + M-SEC-05 + M-SEC-10 landed (Day 6)
6. Audit logger exporting counters
7. Staging deployment ≥ 24h (calendar-day gap recommended)
8. Runbook published + RISK-15 marked "in production" in risk tracking sheet

**Notes**:

All 8 must be true before Phase D PR eligible. Per R0-06 §3.2. Non-parallelizable gate.

### JR-CCL-OPS-001 — Configure Dependabot for automated weekly dependency updates.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-ML-OPS-002 — Every phase must have kill-switch feature flag; TTF (time to fallback) documented.

**Status**: proposed  **Priority**: P1  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-02_risk_minimized_safety_first.md` (lines 29-47)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1044-1046)

**Detail**:

Phase A: no feature flag (additive SDK method, cannot be disabled).
Phase A-server: no feature flag (seq is infrastructure, not a feature).
Phase B: disable_ws_bridge=True → forces REST polling. TTF ~2 min.
Phase C: use_websocket_set_params=False (default) → falls back to REST. TTF ~2 min.
Phase D: disable_ws_control_endpoint=True → buttons force REST. TTF ~5 min.
Phase B-pre auth: ws_security_enabled=False (or JUNIPER_CANOPY_DISABLE_WS_AUTH=true per naming debate in §14 D5). TTF ~2 min. Local dev only—never set in prod.

**Notes**:

Kill switches are non-optional per R1-02 §1.2 principle #2. All documented in day rollback sections.

### JR-CCL-OPS-002 — Set line length to 512 for all linters (black, isort, flake8) per Juniper ecosystem standard.

**Status**: shipped  **Priority**: P2  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21); ecosystem standard convention

### JR-ML-OPS-003 — Shadow traffic: rejected.

**Status**: rejected  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 68-68)

**Notes**:

Settled position C-31 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-004 — Error-budget burn-rate rule operationally binding.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 79-79)

**Notes**:

Settled position C-42 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-005 — Kill switch MTTR ≤5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 76-76)

**Notes**:

Settled position C-39 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-006 — Total effort: 13.5 expected engineering days / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 73-73)

**Notes**:

Settled position C-36 from R3-03 table; cross-round consensus consolidation

### JR-DEP-OPS-002 — Update AGENTS.md with directory layout, security architecture, CI pipeline, network topology.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 29-143)

**Detail**:

Phase 2 (P1 priority) add missing major sections: directory layout, security architecture
(networks, container hardening, secrets), CI/CD pipeline (4 jobs, multi-repo checkout, pinned actions),
Docker Compose profiles (profile-to-service mapping), network architecture, Makefile targets.
Phase 3 complete existing sections: expand service ports table, key files table, dependency graph,
environment variables, essential commands. Phase 4 update metadata, add documentation index, testing architecture.

