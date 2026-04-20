# Canopy-Cascor Interface: Code Review and Documentation Plan

**Version**: 1.0.0
**Date**: 2026-04-08
**Author**: Claude Code (Opus 4.6)
**Owner**: Paul Calnon
**Status**: ACTIVE
**Companion Documents**:

- Analysis: `CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md`
- Roadmap: `CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md`

---

## 1. Purpose

This plan outlines the phases, steps, and tasks needed to complete a comprehensive code review and documentation of the Canopy-Cascor interface, followed by remediation of identified issues.

---

## 2. Plan Overview

### 2.1 Phases

| Phase | Name                               | Duration | Status          |
|-------|------------------------------------|----------|-----------------|
| 0     | Prior Art Assessment               | 0.5 day  | **COMPLETE**    |
| 1     | Codebase Exploration and Discovery | 1 day    | **COMPLETE**    |
| 2     | Deep-Dive API and Model Analysis   | 1 day    | **COMPLETE**    |
| 3     | Interface Contract Mapping         | 1 day    | **COMPLETE**    |
| 4     | Discrepancy Identification         | 0.5 day  | **COMPLETE**    |
| 5     | Comprehensive Documentation        | 1 day    | **COMPLETE**    |
| 6     | Remediation Planning               | 0.5 day  | **COMPLETE**    |
| 7     | Validation and Finalization        | 0.5 day  | **IN PROGRESS** |

### 2.2 Scope

**In scope**:

- All REST API endpoints between canopy and cascor
- All WebSocket protocol messages and handlers
- All data structures, models, and types in the interface
- The juniper-cascor-client library as the intermediary
- All transformation, mapping, and normalization functions
- All constants, defaults, and configuration values
- All code locations where interface data is created, transformed, or consumed
- Naming convention analysis across all three repos
- Cross-side requirement asymmetry analysis

**Out of scope**:

- Internal cascor ML algorithm implementation (except where it produces interface data)
- Internal canopy UI implementation (except where it consumes interface data)
- juniper-data integration (separate interface)
- Docker/Kubernetes deployment mechanics
- CI/CD pipeline internals

---

## 3. Phase 0: Prior Art Assessment

### 3.1 Objective

Inventory and assess existing analysis documents to avoid duplication and build on prior findings.

### 3.2 Tasks

- [x] Read `FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (2,406 lines, 20 issues, implementation record)
- [x] Read `CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (38 findings, CR-006 through CR-076)
- [x] Read `CASCOR_COMPREHENSIVE_CODE_REVIEW_PLAN_2026-04-04.md` (methodology)
- [x] Read `CASCOR_BACKEND_REFERENCE.md` from canopy docs
- [x] Assess git history since prior analyses (2026-03-28 to 2026-04-08)
- [x] Identify remediation PRs and their status

### 3.3 Findings

- Prior analysis is thorough and well-validated (7 Phase 3 proposals → 4 Phase 4 → 2 Phase 5 → Final synthesis)
- 14 of 20 P5-RC issues have been resolved via FIX-A through FIX-K
- Cascor code review produced 38 additional findings (CR-006 through CR-076)
- Significant PR-based remediation work since 2026-03-28 (PRs #104-#118)
- Key remaining issues: CR-006 (max_iterations), CR-007 (state machine), CR-008 (set_params), metrics granularity

---

## 4. Phase 1: Codebase Exploration and Discovery

### 4.1 Objective

Identify all interface touchpoints across the three codebases.

### 4.2 Tasks

- [x] Read AGENTS.md for juniper-canopy (700+ lines)
- [x] Read AGENTS.md for juniper-cascor (600+ lines)
- [x] Explore juniper-cascor-client source structure
- [x] Launch parallel exploration agents:
  - Agent 1: Cascor API models, routes, WebSocket, lifecycle
  - Agent 2: Canopy backend adapters, protocol, state sync, frontend consumers
  - Agent 3: Cascor-client library methods, models, WebSocket client
- [x] Verify current state of files modified by prior fixes (Agent 4)

### 4.3 Interface Touchpoints Discovered

| Component                      | Count | Examples                                                                                                               |
|--------------------------------|-------|------------------------------------------------------------------------------------------------------------------------|
| REST endpoints (cascor)        | 22    | `/v1/network`, `/v1/training/*`, `/v1/metrics/*`                                                                       |
| WebSocket endpoints (cascor)   | 3     | `/ws/training`, `/ws/control`, `/ws/v1/workers`                                                                        |
| Pydantic request models        | 3     | `NetworkCreateRequest`, `TrainingStartRequest`, `TrainingParamUpdateRequest`                                           |
| Response envelope              | 1     | `ResponseEnvelope`                                                                                                     |
| Client methods                 | 30+   | `JuniperCascorClient.*`                                                                                                |
| Canopy adapter transformations | 5     | `_normalize_metric`, `_to_dashboard_metric`, `_transform_topology`, `_normalize_status`, `_CANOPY_TO_CASCOR_PARAM_MAP` |
| Dashboard consumers            | 10+   | `MetricsPanel`, `NetworkVisualizer`, `ParametersPanel`, etc.                                                           |

---

## 5. Phase 2: Deep-Dive API and Model Analysis

### 5.1 Objective

Document every field in every data structure that crosses the interface boundary.

### 5.2 Tasks

- [x] Document all cascor Pydantic request models field-by-field
- [x] Document all cascor response payload schemas
- [x] Document WebSocket message builder functions and schemas
- [x] Document cascor TrainingState fields and their update sources
- [x] Document cascor CascadeCorrelationConfig fields
- [x] Document cascor constants affecting the interface

---

## 6. Phase 3: Interface Contract Mapping

### 6.1 Objective

Map the complete data contract from source to destination across all paths.

### 6.2 Tasks

- [x] Trace metrics data flow: cascor monitor → WS/REST → client → adapter → dashboard
- [x] Trace topology data flow: cascor manager → REST → client → adapter → visualizer
- [x] Trace parameter flow: dashboard → adapter → client → cascor manager
- [x] Trace state flow: cascor state machine → WS/REST → adapter → state sync → dashboard
- [x] Map all field name translations at each boundary
- [x] Document the transformation pipeline for each data type

---

## 7. Phase 4: Discrepancy Identification

### 7.1 Objective

Identify all naming, type, default, and behavioral discrepancies between the two sides.

### 7.2 Tasks

- [x] Cross-reference field names between cascor and canopy
- [x] Compare default values across constant chains
- [x] Identify parameters present on one side but not the other
- [x] Identify dead or non-functional mappings
- [x] Verify status/phase string conventions across repos
- [x] Check for validation asymmetries

### 7.3 Key Discrepancies Found

1. **`max_iterations`** — canopy has UI, constants, settings; cascor has nothing (CR-006)
2. **`epochs_max` defaults** — cascor constant: 10,000; cascor API: 200; canopy: 1,000,000
3. **`max_hidden_units` defaults** — cascor: 100; canopy: 1,000
4. **Topology field names** — cascor: `input_size`/`output_size`; canopy: `input_units`/`output_units`
5. **Metrics field names** — cascor: `loss`/`accuracy`; canopy canonical: `train_loss`/`train_accuracy`
6. **Status format** — cascor enum: UPPERCASE; WS broadcast: Title-case; canopy: case-insensitive
7. **`patience` ↔ `nn_growth_convergence_threshold`** — semantic mismatch (P5-RC-12b)

---

## 8. Phase 5: Comprehensive Documentation

### 8.1 Objective

Write the definitive interface documentation.

### 8.2 Deliverable

`CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md` containing:

- [x] Executive summary and interface health assessment
- [x] Architecture overview with component and data flow diagrams
- [x] Complete REST API contract (22 endpoints)
- [x] WebSocket protocol contract (3 endpoints, message schemas)
- [x] Field-level data contract breakdown (5 major structures)
- [x] Canopy-side interface components (6 modules documented)
- [x] Cascor-side interface components (4 modules documented)
- [x] Cascor-client library documentation (30+ methods)
- [x] Naming convention discrepancy register
- [x] Complete mapping/translation function inventory
- [x] Code instantiation and usage location register
- [x] High-level code walkthrough (3 flows)
- [x] Detailed operational code walkthrough (3 pipelines)
- [x] Cross-side requirements asymmetry analysis
- [x] Current issue registry (open + resolved)
- [x] Explanatory diagrams (6 diagrams)

---

## 9. Phase 6: Remediation Planning

### 9.1 Objective

Develop detailed remediation options for all open issues.

### 9.2 Tasks

- [x] Classify open issues by severity and effort
- [x] Develop multiple remediation approaches for critical issues (CR-006, CR-007, CR-008)
- [x] Analyze strengths, weaknesses, risks, and guardrails for each approach
- [x] Provide recommended approaches with rationale
- [x] Create tiered development roadmap with dependencies
- [x] Write remediation details into analysis document

### 9.3 Remediation Summary

| Tier                        | Issues                             | Total Effort | Priority |
|-----------------------------|------------------------------------|--------------|----------|
| Tier 0: Critical Interface  | CR-006, CR-007, CR-008             | 5-6 days     | P0-P1    |
| Tier 1: Security            | CR-023, CR-024, CR-025, CR-026     | 2-3 days     | P1-P2    |
| Tier 2: Metrics Granularity | Appendix G (5 items)               | 8-12 days    | P2       |
| Tier 3: Architecture        | P5-RC-05, P5-RC-14, P5-RC-18, KL-1 | 9-14 days    | P3-P4    |

---

## 10. Phase 7: Validation and Finalization

### 10.1 Objective

Validate all work performed, correct any issues, and finalize deliverables.

### 10.2 Tasks

- [x] Verify analysis document completeness against prompt requirements
- [x] Cross-reference with prior analysis for consistency
- [ ] Validate current-state findings against live codebase (pending agent results)
- [ ] Review and correct any inaccuracies found
- [ ] Commit documentation to worktree
- [ ] Create pull request for documentation additions

### 10.3 Validation Checklist

| Requirement                          | Document Section   | Status       |
|--------------------------------------|--------------------|--------------|
| Data contracts                       | §5                 | **Complete** |
| Code promises                        | §6, §7, §8         | **Complete** |
| Interface agreements                 | §3, §4             | **Complete** |
| APIs                                 | §3 (REST), §4 (WS) | **Complete** |
| Developer expectations               | §14                | **Complete** |
| High-level walkthroughs              | §12                | **Complete** |
| Detailed walkthroughs                | §13                | **Complete** |
| Field breakdowns with types/defaults | §5                 | **Complete** |
| Constants class locations            | Appendix B         | **Complete** |
| Naming discrepancies                 | §9                 | **Complete** |
| Complete data structure list         | Appendix A         | **Complete** |
| Instantiation locations              | §11                | **Complete** |
| Mapping classes/translators          | §10                | **Complete** |
| Cross-side requirement asymmetries   | §14                | **Complete** |
| Explanatory diagrams                 | Appendix C         | **Complete** |
| Remediation options                  | §16                | **Complete** |
| Development roadmap                  | §17                | **Complete** |

---

*End of Code Review and Documentation Plan:*
