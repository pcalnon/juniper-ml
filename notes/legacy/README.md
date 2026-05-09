# notes/legacy/ — Archive Index

**Purpose**: Consolidated archive of completed plans, designs, audits, roadmaps,
and procedure notes from across the juniper-ml lifecycle. Documents land here
once their tracked work is closed (shipped, deferred-with-link, or formally
cancelled). This directory replaces the prior split between `notes/backups/`
and `notes/history/` (consolidated 2026-05-05) and additionally absorbs the
post-METRICS-MON observability program close-out (2026-05-05).

**Editing policy**: archived docs are preserved as historical reference. Do not
edit the body; if a doc needs updating, write a successor in `notes/` and link
back. The only acceptable edits to docs already in this directory are the
"STATUS YYYY-MM-DD: COMPLETED" banner that records the archive event.

**Doc-link validator**: this directory is excluded from
`util/check_doc_links.py` via `--exclude legacy`. Pre-existing relative links
inside archived docs (e.g. to `../AGENTS.md` or sibling files) may be stale;
that is intentional.

---

## Archive index by program / topic

### METRICS-MON program (2026-04-25 — 2026-05-03)

The juniper-ml ecosystem's first explicit, end-to-end observability discipline.
9 calendar days, 78 PRs across 8 repos, 5 phases (R1 cardinality / R2 shared lib /
R3 test coverage / R4 ergonomic / R5 SLO+dashboards+alerts). Closed by
juniper-ml#192 on 2026-05-03. Archived 2026-05-05 via the post-program doc-reorg PR.

| Date       | Doc                                                                               | Closing PR(s)         |
|------------|-----------------------------------------------------------------------------------|-----------------------|
| 2026-04-25 | `METRICS_MONITORING_ANALYSIS_2026-04-25.md`                                       | program (juniper-ml#192) |
| 2026-04-25 | `METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md`                                    | program (juniper-ml#192) |
| 2026-04-25 | `METRICS_MONITORING_REVIEW_STATUS_2026-04-25.md`                                  | program (juniper-ml#192) |
| 2026-04-25 | `METRICS_MONITORING_ROADMAP_2026-04-25.md` (program tracker)                      | program (juniper-ml#192) |
| 2026-04-27 | `METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`                              | R1.2 cluster          |
| 2026-04-27 | `METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md`                   | R1.3 cluster          |
| 2026-04-28 | `METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`               | R2.1 (juniper-ml#155 family) |
| 2026-04-29 | `METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md`                    | R2.2 family           |
| 2026-04-29 | `METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md`                   | R2 close              |
| 2026-04-30 | `METRICS_MONITORING_R3.4_SENTRY_AUDIT_CLOSURE_2026-04-30.md`                      | R3.4 (no work needed) |
| 2026-04-30 | `METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`                                  | R3 close (juniper-ml#182) |
| 2026-05-01 | `METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md`                                  | R4 close (juniper-ml#186) |
| 2026-05-02 | `METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`                                  | R5 close (juniper-ml#192) |
| 2026-05-03 | `METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md`              | bridges R5.4 -> future TRAIN-ARCH |
| 2026-05-03 | `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md` (program-close note)             | juniper-ml#192        |

> **Live tracker**: post-program residuals (TRAIN-ARCH-01, alertmanager `tickets`
> receiver, R5.6 throttle removal, 30-day SLO soak calibration, A.9 dead-metric
> cleanup, A.7 catalog prose drift) are tracked in
> `notes/POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel PR) and the
> `OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` audit doc still in
> `notes/code-review/`.

### Pre-METRICS-MON program archive (2026-03 — 2026-04, formerly `notes/history/`)

These documents were archived to `notes/history/` during the 2026-03 / 2026-04
documentation-audit work and consolidated into this directory on 2026-05-05.

#### AGENTS.md drift program (2026-04-02)

- `AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md`
- `AGENTS_MD_UPDATE_PLAN_2026-04-02.md`
- `AGENTS_MD_UPDATE_ROADMAP_2026-04-02.md`

#### Juniper-wide regression-cluster work (2026-04-02 / 2026-04-03)

- `CROSS_PROJECT_REGRESSION_ANALYSIS_2026-04-03.md`, `CROSS_PROJECT_REMEDIATION_PLAN_2026-04-03.md`
- `JUNIPER_REGRESSION_ANALYSIS_2026-04-02.md`, `JUNIPER_REGRESSION_DEVELOPMENT_ROADMAP.md`,
  `JUNIPER_REGRESSION_DEVELOPMENT_ROADMAP_2026-04-02.md`, `JUNIPER_REGRESSION_REMEDIATION_PLAN_2026-04-02.md`
- `REGRESSION_ANALYSIS_2026-04-02.md`, `REGRESSION_ANALYSIS_2026-04-03.md`
- `REGRESSION_DEVELOPMENT_ROADMAP_2026-04-02.md`, `REGRESSION_DEVELOPMENT_ROADMAP_2026-04-03.md`
- `REGRESSION_REMEDIATION_PLAN_2026-04-02.md`, `REGRESSION_REMEDIATION_PLAN_2026-04-03.md`

#### Canopy plans / fixes

- `CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md`, `CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md`
- `CANOPY_CONTEXTUAL_MENU_AND_CANDIDATE_TAB_DESIGN.md`, `CANOPY_DASHBOARD_DISPLAY_FIXES.md`
- `CANOPY_DEFERRED_AND_BACKLOG_PLAN.md`, `CANOPY_REGRESSION_ANALYSIS.md`
- `CANOPY_REPO_RENAME_MIGRATION_PLAN.md`, `CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md`

#### Cascor training analysis

- `CASCOR_TRAINING_FAILURE_ANALYSIS.md`

#### Dataset display bug cluster

- `DATASET_DISPLAY_BUG_ANALYSIS-FINAL.md`, `DATASET_DISPLAY_BUG_ANALYSIS.md`
- `DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN-FINAL.md`, `DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md`
- `DATASET_DISPLAY_FAILURE_ANALYSIS.md`, `DATASET_DISPLAY_FIX_PLAN.md`

#### Hard-coded values + integrated dashboard

- `HARDCODED_VALUES_ANALYSIS.md`, `HARDCODED_VALUES_REFACTOR_PLAN.md`, `HARDCODED_VALUES_REFACTOR_ROADMAP.md`
- `INTEGRATED_DASHBOARD_PLAN.md`

#### Pre-commit / shellcheck remediation

- `PRE-COMMIT_COMPLIANCE_REMEDIATION_PLAN.md`, `PRE_COMMIT_REMEDIATION_PLAN.md`, `PRE_COMMIT_SHELLCHECK_FIX_PLAN.md`

#### PyPI deployment

- `PYPI_DEPLOYMENT_PLAN.md`, `PYPI_MANUAL_SETUP_STEPS.md`

#### Security remediation cluster

- `JUNIPER_DEPLOY_PR14_SECURITY_REMEDIATION_PLAN.md`, `PR40_SECURITY_REMEDIATION_PLAN.md`
- `SECRETS_MANAGEMENT_ANALYSIS.md`, `SECURITY_AUDIT_PLAN.md`, `SECURITY_LOGGING_REMEDIATION_PLAN.md`,
  `SECURITY_REMEDIATION_PLAN.md`

#### SOPS

- `SOPS_AUDIT_2026-03-02.md`, `SOPS_IMPLEMENTATION_PLAN.md`

#### Test failures + wake-the-claude / launcher

- `FIX_PLAN_test_failures_2026-03-13.md`, `FIX_PLAN_wake_the_claude_session_validation_2026-03-14.md`
- `FIX_ROADMAP_EVAL_AND_DEBUG_LOG.md`, `SESSION_ID_VALIDATION_BUGFIX_PLAN.md`,
  `TEST_FAILURE_REMEDIATION_PLAN.md`, `wake_the_claude_failure_analysis.md`

#### Worktree procedures (V1 → V2)

- `WORKTREE_CLEANUP_PROCEDURE.md`, `WORKTREE_CLEANUP_PROCEDURE_V1.md`,
  `WORKTREE_CLEANUP_V2_PLAN.md`, `WORKTREE_SETUP_PROCEDURE.md`

#### Cascor bug list + assorted

- `cascor_ bug-list_2026-04.10.md`, `stack_overflow_answer.txt`
- `DEVELOPER_CHEATSHEET-ORIGINAL.md` (deprecated monolithic master cheatsheet)

### Pre-METRICS-MON backups archive (formerly `notes/backups/`)

Backups of in-flight design / fix-plan documents superseded by later versions
or by shipped work. Consolidated into this directory on 2026-05-05.

#### Canopy decision-boundary / external cascor

- `CANOPY_DECISION_BOUNDARY_FIX_PLAN.md`, `CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md`
- `CANOPY_EXTERNAL_CASCOR_PLAN.md`, `CANOPY_TEST_FAILURE_ANALYSIS.md`

#### Cascor concurrency + demo training error

- `CASCOR_CONCURRENCY_PLAN.md`, `CASCOR_CONCURRENCY_THREAD_HANDOFF_2026-03-18.md`
- `CASCOR_DEMO_TRAINING_ERROR_PLAN-OLD.md`, `CASCOR_DEMO_TRAINING_ERROR_PLAN-ORIG.md`,
  `CASCOR_DEMO_TRAINING_ERROR_PLAN.md`, `CASCOR_DEMO_TRAINING_ERROR_PLAN_1.md`
- `CASCOR_TENSOR_DIMENSION_MISMATCH_ANALYSIS.md`

#### Training stall / candidate quality root-cause cluster (2026-03-20)

- `ROOT_CAUSE_CANDIDATE_QUALITY_DEGRADATION.md`, `ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md`,
  `ROOT_CAUSE_SPIRAL_COMPLEXITY.md`
- `TRAINING_PERFORMANCE_ANALYSIS_2026-03-20.md`, `TRAINING_STALL_ANALYSIS.md`,
  `TRAINING_STALL_REMEDIATION_PLAN.md`
- `reconciliation_committed_vs_discarded.md`

---

## Quick stats

- Total archived docs (excluding this README): see `ls notes/legacy/ | wc -l`.
- Last consolidation: 2026-05-05 (post-METRICS-MON observability program close).
- Previous consolidation events:
  - 2026-04: `notes/history/` populated by the documentation audit.
  - 2026-03: `notes/backups/` populated as ad-hoc working-doc backups.
