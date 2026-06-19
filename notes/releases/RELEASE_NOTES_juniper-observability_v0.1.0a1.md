# juniper-observability v0.1.0a1 — alpha (R2.1.1 / METRICS-MON seed-06) — Release Notes (archived)

> Archived verbatim from the GitHub Release [`juniper-observability-v0.1.0a1`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.0a1) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

juniper-observability v0.1.0a1 — alpha (R2.1.1 / METRICS-MON seed-06)

  First public release of the shared observability library. Alpha
  release; consumer migration begins with juniper-data (R2.1.2),
  followed by promotion to stable 0.1.0 once the data migration
  soaks for one release cycle.

  Public API (20 symbols, re-exported from juniper_observability):
    - DependencyStatus, ReadinessResponse, probe_dependency
    - JuniperJsonFormatter, configure_logging
    - RequestIdMiddleware, request_id_var, PrometheusMiddleware
    - get_prometheus_app, set_build_info, configure_sentry
    - UNMATCHED_ENDPOINT_LABEL, READINESS_HEADER,
      LIVENESS_TICK_BUDGET_MS, LIVENESS_STALENESS_SECONDS,
      HEADER_X_REQUEST_ID
    - DEFAULT_LOG_FORMAT_PLAIN, LOG_FORMAT_JSON,
      DEFAULT_SENTRY_TRACES_SAMPLE_RATE
    - __version__

  Reconciled signatures (vs. per-repo originals):
    - configure_sentry: superset signature with send_pii=False
      keyword-only default; SEC-10 _strip_sensitive_headers
      before_send hook always installed.
    - ReadinessResponse.timestamp: tz-aware UTC; closes the
      juniper-cascor naive-datetime.now() drift identified during
      R1.2 implementation (BUG-JD-06 equivalent).

  Verification at release time:
    - 56/56 tests pass at 100% coverage (138/138 statements).
    - python -m build produces clean sdist + wheel.
    - twine check passes both artifacts.

  Source PR: pcalnon/juniper-ml#155 (merged 2026-04-28 as f0fb496)
  Design:    notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md
  Roadmap:   notes/code-review/METRICS_MONITORING_ROADMAP_2026-04-25.md §R2.1

## What's Changed
* docs: mark Canopy-Cascor interface Phase 3 COMPLETE by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/113
* docs: mark Canopy-Cascor interface Phase 4 MOSTLY COMPLETE by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/114
* docs: resolve Phase 1 deferred items in interface roadmap by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/115
* docs: revert premature NEW-01 / set_params / P5-RC-05 resolution claims by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/116
* docs: add Canopy-Cascor WebSocket & Messaging Architecture analysis by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/117
* refactor: hardcoded values cleanup (Waves 3-6) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/118
* fix(ci): pip-audit --skip-editable + repair 7 active broken doc links by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/119
* chore(ci): add workflow_dispatch trigger to publish.yml by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/121
* docs: mark hardcoded values refactor roadmap complete by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/120
* Worktree nifty purring allen by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/122
* docs: WebSocket migration development proposals (21-file funnel) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/123
* docs: mark Canopy-Cascor interface Phase 4 MOSTLY COMPLETE by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/124
* docs: resolve Phase 1 deferred items in Canopy-Cascor interface roadmap by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/125
* docs: mark Canopy-Cascor interface Phase 3 COMPLETE by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/126
* ci: bump actions/upload-artifact from 7.0.0 to 7.0.1 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/127
* ci: bump anthropics/claude-code-action from 1.0.89 to 1.0.93 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/128
* ci: bump actions/cache from 5.0.4 to 5.0.5 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/129
* docs: mark Canopy-Cascor interface Phase D COMPLETE (R5-01 §S10) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/130
* ci: bump pypa/gh-action-pypi-publish from 1.13.0 to 1.14.0 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/131
* ci: bump anthropics/claude-code-action from 1.0.93 to 1.0.101 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/132
* docs(roadmap): mark Phase 4A (XREPO-01/01b/01c + DC-01/02/03) implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/133
* docs: mark Track 1 Phase 1A security items as implemented (juniper-da… by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/134
* docs: mark Phase 2A items implemented (BUG-CC-03, BUG-CC-11, BUG-CC-18/ROBUST-01) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/135
* docs(roadmap): mark Track 2 Phase 2B-2E implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/140
* docs: mark Phase 2B items implemented (BUG-JD-01..04) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/136
* docs(roadmap): mark Phase 4B (XREPO-02/CC-02, XREPO-09, XREPO-11) implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/137
* docs: mark Track 1 Phase 1B/1C/1D security items implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/138
* docs: mark Track 1 Phases 1B/1C/1D security items implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/139
* docs(roadmap): mark Phase 4C (ERR-01, ERR-02, CW-01, CW-06) implemented by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/141
* docs: mark Track 3 Phase 3A items implemented (CONC-04/BUG-JD-10, CONC-07/BUG-CN-11) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/142
* docs(roadmap): mark Track 4 Phase 4D + 4E implemented and add CW-05-FOLLOWUP by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/143
* Worktree smooth floating umbrella by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/144
* docs: mark Track 3 Phase 3C items implemented (BUG-CN-09, BUG-CN-10, CONC-08, CONC-09) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/145
* docs(metrics-mon): mark R1.1 complete; add R1.2 probe-semantics design by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/146
* docs: mark Track 3 Phase 3D items implemented (CONC-10, CONC-12/BUG-JD-11, BUG-CN-01) — Track 3 complete by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/147
* docs(notes): archive Apr 8 release-readiness review documents (review only) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/148
* chore: cleanup_session_worktrees.py script + doc-link hygiene (move deprecated cheatsheet to history) by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/149
* docs(metrics-mon): mark R1.2 complete; add R1.3 worker-heartbeat design by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/150
* ci: bump anthropics/claude-code-action from 1.0.101 to 1.0.107 by @dependabot[bot] in https://github.com/pcalnon/juniper-ml/pull/151
* docs(roadmap): mark Track 5A/5B/5C complete + document open 5D/5E/5F items by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/152
* docs(metrics-mon): mark R1.3 main work done; add R2.1 shared-obs lib design by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/153
* docs(roadmap): mark Track 6B/6C complete; surface 6A partial state by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/154
* feat(observability): add juniper-observability package (alpha 0.1.0a0) — R2.1.1 by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/155
* docs(roadmap): 6D code-state audit — 10 shipped, 4 blocked, 8 open by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/156
* docs(roadmap): mark R2.1.1 alpha source merged; flag publish gate by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/157
* docs(roadmap): re-classify CAN-013 as blocked on cascor algorithm work by @pcalnon in https://github.com/pcalnon/juniper-ml/pull/158


**Full Changelog**: https://github.com/pcalnon/juniper-ml/compare/v0.4.0...juniper-observability-v0.1.0a1
