# Juniper ML v0.4.0 Release Notes

**Release Date:** 2026-04-09
**Version:** 0.4.0
**Codename:** Microservices Platform & Release Convergence
**Release Type:** MINOR

---

## Overview

This release converges three months of development across the Juniper ecosystem into a coherent meta-package update. It bumps client extras to track the latest released versions of every Juniper client (`juniper-data-client>=0.4.0`, `juniper-cascor-client>=0.3.0`, `juniper-cascor-worker>=0.3.0`), introduces a complete microservices startup/shutdown layer (`juniper_plant_all.bash` / `juniper_chop_all.bash`), full systemd integration (`juniper-all.target` + `juniper-all-ctl`), the V2 worktree cleanup orchestrator with CWD-safe session continuity, a suite of CasCor REST API query utilities, and the `claude_interactive.bash` (`claudey`) interactive launcher.

It also incorporates the cross-project release-prep code review and remediation plan that drove the coordinated v0.6.0 / v0.4.0 / v0.3.0 / v0.2.0 releases across the rest of the ecosystem.

> **Status:** STABLE — All extras pin to released, tagged versions of their respective Juniper packages.

---

## Release Summary

- **Release type:** MINOR
- **Primary focus:** Microservices orchestration layer, systemd integration, ecosystem version convergence
- **Breaking changes:** No (extras minimum versions raised; downstream consumers using older versions should upgrade)
- **Priority summary:** Latest client extras + complete plant/chop/systemd workflow + V2 worktree cleanup + cross-project release prep

---

## Cumulative Phase Status

| Phase | Items | Status |
| ----- | ----- | ------ |
| Microservices startup/shutdown overhaul | 1 wave | ✅ Complete |
| Systemd integration (Phase 2) | 1 wave | ✅ Complete |
| Cascor-worker systemd integration (Phase 3) | 1 wave | ✅ Complete |
| Cross-project release prep — Phase 1 (Critical) | 10 items | ✅ Complete |
| Cross-project release prep — Phase 2 (High) | 18 items | ✅ Complete |
| Cross-project release prep — Phase 3 (Medium) | 19 items | ✅ Complete (1 deferred for future logging refactor) |

---

## What's New

### Microservices Orchestration Layer

A pair of bash scripts that start and stop every juniper service from a single entry point with health checks, conda environment activation, and PID file management.

- `util/juniper_plant_all.bash` — Microservices startup script with health checks, conda environment activation, and PID file management
- `util/juniper_chop_all.bash` — Microservices shutdown script with graceful SIGTERM/SIGKILL escalation, PID file parsing, and orphaned worker cleanup

### Systemd Integration

Both `plant` and `chop` scripts now support a `--systemd` mode that delegates to `systemctl --user` instead of managing PID files directly. Companion artifacts:

- `scripts/juniper-all-ctl` — Management CLI script wrapping common systemd operations
- `scripts/juniper-all.target` — Systemd target unit grouping all juniper services
- Cascor-worker integration into the systemd target and the startup/shutdown scripts (Phase 3)

### V2 Worktree Cleanup Orchestrator

- `util/worktree_cleanup.bash` — V2 automated worktree cleanup orchestrator with CWD-safe session continuity (eliminates the "CWD-trap" bug where removing the current worktree leaves the shell with no valid working directory)
- `tests/test_worktree_cleanup.py` — Regression tests for argument parsing, dry-run mode, and error handling

### Worktree Management Utilities

- `util/worktree_new.bash` — Create a new worktree from a branch with consistent naming
- `util/worktree_activate.bash` — Activate (cd into) an existing worktree
- `util/worktree_close.bash` — Close a single worktree cleanly
- `util/worktree_wipeout.bash` — Bulk-remove worktrees matching a pattern

### CasCor REST API Query Utilities

Quick command-line wrappers for common cascor REST endpoints:

- `util/get_cascor_status.bash` — `GET /v1/training/status`
- `util/get_cascor_metrics.bash` — `GET /v1/metrics`
- `util/get_cascor_history.bash` — `GET /v1/metrics/history?count=10`
- `util/get_cascor_network.bash` — `GET /v1/network`
- `util/get_cascor_topology.bash` — `GET /v1/network/topology`

### Interactive Claude Launcher

- `scripts/claude_interactive.bash` — Interactive Claude Code agent launcher (`claudey` symlink at repo root)

### Cross-Project Documentation

- Cross-project regression analysis, remediation plans, and development roadmaps in `notes/`
- `notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` — full findings with file:line references
- `notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` — phased execution plan with fix details
- `notes/code-review/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md` — prioritized roadmap that drove this release cycle

---

## Bug Fixes

### CI `dependency-docs` Job Path

**Problem:** CI `dependency-docs` job referenced `scripts/generate_dep_docs.sh`, but the script had been moved to `util/` as part of the directory reorganization. The job was failing on every run.

**Solution:** Updated `.github/workflows/ci.yml` to reference `util/generate_dep_docs.sh`.

**Files:** `.github/workflows/ci.yml:244`

### `juniper_chop_all.bash` PID File Parsing

**Problem:** PID file parsing used `read -d ''` (whitespace splitting), which mangled multi-word PID file lines and dropped entries silently. A `done < PID_FILE` redirect on the for-loop further confused the iteration semantics.

**Solution:**

- Replaced `read -d ''` with `mapfile -t JUNIPER_PIDS < "$PID_FILE"` (line-oriented parsing)
- Removed the contradictory `done < PID_FILE` redirect from the for-loop iterating over the already-populated array

**Files:** `util/juniper_chop_all.bash:275-325`

### `juniper_chop_all.bash` Defaults

**Problem:** `KILL_WORKERS` defaulted to `"1"` (kill orphaned workers) and `SIGTERM_TIMEOUT` defaulted to `"10"`, but the documented behavior was opposite/different. Operators got surprises.

**Solution:**

- `KILL_WORKERS` default changed from hardcoded `"1"` to `"0"` to match documented behavior
- `SIGTERM_TIMEOUT` default changed from hardcoded `"10"` to environment-variable-driven `"15"` to match documented behavior
- Worker search term narrowed from `"cascor"` to `"juniper-cascor-worker"` to prevent false-positive matches against the cascor backend

**Files:** `util/juniper_chop_all.bash:69-71,82,84`

### CI Test Inclusion

**Problem:** `tests/test_worktree_cleanup.py` was added to the repo but not registered in the CI test suite, so regressions could land undetected.

**Solution:** Added `python3 -m unittest -v tests/test_worktree_cleanup.py` to the CI test job.

**Files:** `.github/workflows/ci.yml:109-110`

### Other Fixes

- PID reference fixes in `juniper_plant_all.bash`
- Test script paths updated after the `scripts/` → `util/` migration

---

## Changes

### Optional Dependency Extras

Bumped minimum versions to track the latest released versions of each Juniper client:

| Extra package           | Old constraint | New constraint | What's new                                                                |
| ----------------------- | -------------- | -------------- | ------------------------------------------------------------------------- |
| `juniper-data-client`   | `>=0.3.0`      | `>=0.4.0`      | Batch operations, dataset versioning                                      |
| `juniper-cascor-client` | `>=0.1.0`      | `>=0.3.0`      | Worker monitoring, snapshot management, dataset retrieval, testing module |
| `juniper-cascor-worker` | `>=0.1.0`      | `>=0.3.0`      | WebSocket-based agent, TLS/mTLS, deprecates legacy BaseManager mode       |

### Documentation

- `AGENTS.md` updated to v0.4.0 with comprehensive structure documentation, CI/CD pipeline details, and worktree/handoff procedures
- Moved worktree management and documentation utilities from `scripts/` to `util/`

### Dependencies

- Dependabot CI action version bumps:
  - `anthropics/claude-code-action`: 1.0.62 → 1.0.89
  - `actions/cache`: 4.2.3 → 5.0.4
  - `actions/upload-artifact`: 6.0.0 → 7.0.0
  - `actions/download-artifact`: 8.0.0 → 8.0.1

---

## Upgrade Notes

This is a backward-compatible release. The minimum versions of the optional dependency extras have been raised; consumers installing extras will pull the new versions automatically.

```bash
# Standard install paths
pip install --upgrade juniper-ml==0.4.0
pip install --upgrade "juniper-ml[clients]==0.4.0"
pip install --upgrade "juniper-ml[worker]==0.4.0"
pip install --upgrade "juniper-ml[all]==0.4.0"
```

### Adopting the Microservices Orchestration Layer

```bash
# Start every juniper service in PID-file mode
util/juniper_plant_all.bash

# Or use systemd if you prefer
util/juniper_plant_all.bash --systemd

# Stop everything
util/juniper_chop_all.bash
util/juniper_chop_all.bash --systemd
```

### Adopting the V2 Worktree Cleanup

```bash
util/worktree_cleanup.bash \
  --old-worktree "$OLD_WORKTREE_DIR" \
  --old-branch "$OLD_BRANCH" \
  --parent-branch main
```

See `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` for the full procedure.

---

## Known Issues

- **Phase 3 task 3.1 deferred (intentional):** The duplicate constant-echo lines in `util/juniper_chop_all.bash` (around lines 73-75 and 84-85) are kept in place as future debug/verbose logging placeholders. They will be wrapped at the Debug/Verbose level when a robust logging solution is added in a future release. Not a functional issue.

---

## What's Next

### Planned for v0.5.0

- Robust logging framework for the bash utility scripts (replaces the duplicate echo placeholders called out above)
- Continued ecosystem version convergence as juniper-data, juniper-cascor, and juniper-canopy ship their next releases

### Roadmap

See [Release Development Roadmap](../code-review/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md) for the cross-project view of release-prep progress.

---

## Cross-Ecosystem Context

This release ships alongside the following coordinated ecosystem releases:

| Repo                   | Version | Status                              |
| ---------------------- | ------- | ----------------------------------- |
| juniper-data           | 0.6.0   | Released 2026-04-09                 |
| juniper-data-client    | 0.4.0   | Released 2026-04-09                 |
| juniper-cascor-client  | 0.3.0   | Released 2026-04-09 (backfill)      |
| juniper-cascor-worker  | 0.3.0   | Released 2026-04-09 (backfill)      |
| juniper-deploy         | 0.2.1   | Released 2026-04-09                 |
| **juniper-ml**         | **0.4.0** | **This release**                  |

---

## Contributors

- Paul Calnon

---

## Version History

| Version | Date       | Description                                                                                              |
| ------- | ---------- | -------------------------------------------------------------------------------------------------------- |
| 0.1.0   | 2026-02-22 | Initial `juniper` meta-package with optional dependency extras                                           |
| 0.2.0   | 2026-02-27 | Renamed to `juniper-ml`, raised Python minimum to >=3.12                                                 |
| 0.2.1   | 2026-03-06 | `wake_the_claude.bash` launcher with session ID security fixes                                           |
| 0.3.0   | 2026-03-12 | Claude tooling suite (conda/worktree/branch helpers), `eval` removal                                     |
| 0.4.0   | 2026-04-09 | Microservices orchestration, systemd integration, V2 worktree cleanup, cross-project release prep, latest client extras |

---

## Links

- [Full Changelog](../../CHANGELOG.md)
- [Cross-Project Code Review](../code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md)
- [Release Preparation Plan](../code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md)
- [Release Development Roadmap](../code-review/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md)
- [Previous Release: v0.3.0](RELEASE_NOTES_v0.3.0.md)
