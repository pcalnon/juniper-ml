# Requirements — OPS

**Area**: operations / runbooks / on-call — runbook documents, incident response

**Total entries**: 20

**By status**: proposed=16 | shipped=3 | rejected=1

**By priority**: P0=3 | P1=3 | P2=9 | P3=5

**By owner**: ml=11 | can=5 | dep=2 | ccl=2

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
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-06-OPS-PHASING-RISK.md` (lines 79-110)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 850-870)

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

### JR-ML-OPS-002 — Publish v7.0.1 hotfix to roadmap with verified fixes and shipped CAN-015g/h work.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md` (lines 232-242)

### JR-CCL-OPS-001 — Configure Dependabot for automated weekly dependency updates.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAN-OPS-001 — Startup regression analysis and fixes: JuniperData lifecycle, env var expansion, namespace collision, config convention mismatches.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/REGRESSION_ANALYSIS_STARTUP_FAILURE_2026-02-09.md` (lines 1-100)

**Detail**:

Root causes: RC-1 missing JuniperData service lifecycle management, RC-2 ${VAR:default} syntax unsupported by os.path.expandvars, RC-3 shell-to-Python environment namespace collision, RC-4 CASCOR_DEMO_MODE value convention mismatch. Fixes: script-level service management, custom config expansion, shell variable filtering, startup validation.

**PRs**: #146

### JR-ML-OPS-003 — Every phase must have kill-switch feature flag; TTF (time to fallback) documented.

**Status**: proposed  **Priority**: P1  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-02-RISK-MINIMIZED-SAFETY-FIRST.md` (lines 29-47)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1044-1046)

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

### JR-ML-OPS-004 — Shadow traffic: rejected.

**Status**: rejected  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 68-68)

**Notes**:

Settled position C-31 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-005 — Audit and update Juniper SOPS (Standard Operating Procedures) documentation.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SOPS_AUDIT_2026-03-02.md` (lines 1-100)

### JR-CAN-OPS-002 — Background coverage runs exceed 300s timeout, requiring CI harness tuning.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 35-35)

**Detail**:

Operational issue, not a code defect. Suggest increasing test harness timeout or optimizing coverage runner.

**Notes**:

Operational tuning only.

### JR-ML-OPS-006 — Error-budget burn-rate rule operationally binding.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 79-79)

**Notes**:

Settled position C-42 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-007 — Establish PyPI publish procedure: OIDC trusted publishing, semantic versioning, automated changelog.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (lines 1-50)

### JR-ML-OPS-008 — Kill switch MTTR ≤5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 76-76)

**Notes**:

Settled position C-39 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-009 — Total effort: 13.5 expected engineering days / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 73-73)

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

### JR-CAN-OPS-003 — Demo backend logs 'Invalid STOP command in current state' error on every teardown, creating noisy logs.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 32-32)

**Detail**:

Cosmetic issue; does not affect functionality. Fix by handling terminal state transitions more gracefully.

**Notes**:

Low priority; noise reduction only.

### JR-ML-OPS-010 — Document and automate manual PyPI setup procedures.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_MANUAL_SETUP_STEPS.md` (lines 1-100)

**Notes**:

Manual steps should be automated in publishing pipeline.

### JR-CAN-OPS-004 — Double initialization on fallback-to-demo path: backend.initialize() called twice (ISS-18).

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 667-683)

**Detail**:

ISS-18 LOW. In main.py:165-180, when CasCor probe fails and backend falls back to demo mode, backend.initialize() called once inside fallback block (line 177) and again unconditionally (line 180). For DemoBackend, initialize() calls self._demo.start() starting training simulation thread. Could start two threads or produce unexpected state. In practice, DemoBackend.initialize() appears idempotent, so code smell rather than active bug. Only affects fallback-to-demo path (cascor unreachable).

**Notes**:

Identified by v6. v5 confirmed asynccontextmanager runs sequentially so demo state sync executes correctly after fallback.

### JR-CAN-OPS-005 — Dual status normalization paths produce inconsistent representations (ISS-14 cosmetic inconsistency).

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 588-605)

**Detail**:

ISS-14 INFO. Two independent normalization paths exist: Path A (ServiceBackend.get_status()) uses .upper() comparison returning boolean flags (is_running, is_paused) plus raw fsm_status; Path B (relay callback _normalize_status()) returns title-case strings ("Training", "Paused"). Result: training_state may hold status="Started" while /api/status returns is_running=True and fsm_status="STARTED". Cosmetic inconsistency only, not functional blocker, but could confuse code comparing status strings from different sources.

**Notes**:

Identified by v4. Cross-source status comparison risk.

### JR-ML-OPS-011 — Transfer all Juniper repositories and PyPI packages from pcalnon to OvertoadResearch GitHub organization.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_DEPLOYMENT_PLAN.md` (lines 339-400)

**Detail**:

Phase 5: Create OvertoadResearch org on GitHub/PyPI, transfer repos with URL redirects, update git remotes/SSH, add org as PyPI maintainer, update OIDC configs.
