# Hardcoded Values Analysis — juniper-ml

**Version**: 0.3.0
**Analysis Date**: 2026-04-08
**Analyst**: Claude Code (Automated Code Review)
**Status**: PLANNING ONLY — No source code modifications

---

## Executive Summary

The juniper-ml repository is a **meta-package** with no importable Python application code.
Its hardcoded values are concentrated in **utility scripts** (bash) and **test files** (Python unittest).
Approximately **35 hardcoded values** were identified.
Most service port numbers in startup scripts are already environment-configurable.
The primary gaps are in CasCor API query utilities (hardcoded URLs), test timeouts, and one hardcoded absolute path.

---

## 1. Existing Constants Infrastructure

| Pattern                 | Status                                                                                    |
|-------------------------|-------------------------------------------------------------------------------------------|
| Python constants module | N/A (no application code)                                                                 |
| Bash config sourcing    | Partial — `juniper_plant_all.bash` and `juniper_chop_all.bash` use env vars with defaults |
| Test constants          | Inline literals in test files                                                             |

---

## 2. Hardcoded Values Inventory

### 2.1 CasCor API Query Utilities (`util/get_cascor_*.bash`) — NOT COVERED

| File                           | Value                                                | Context            | Proposed Fix                               |
|--------------------------------|------------------------------------------------------|--------------------|--------------------------------------------|
| `get_cascor_history.bash`      | `http://localhost:8201/v1/metrics/history?count=10`  | Full URL hardcoded | Use `${CASCOR_URL:-http://localhost:8201}` |
| `get_cascor_history-plus.bash` | `http://localhost:8201/v1/metrics/history?count=100` | Full URL hardcoded | Use `${CASCOR_URL}`                        |
| `get_cascor_metrics.bash`      | `http://localhost:8201/v1/metrics`                   | Full URL hardcoded | Use `${CASCOR_URL}`                        |
| `get_cascor_network.bash`      | `http://localhost:8201/v1/network`                   | Full URL hardcoded | Use `${CASCOR_URL}`                        |
| `get_cascor_status.bash`       | `http://localhost:8201/v1/training/status`           | Full URL hardcoded | Use `${CASCOR_URL}`                        |
| `get_cascor_topology.bash`     | `http://localhost:8201/v1/network/topology`          | Full URL hardcoded | Use `${CASCOR_URL}`                        |

### 2.2 Service Startup (`util/juniper_plant_all.bash`) — PARTIALLY COVERED

| Line  | Value         | Context                       | Status               |
|-------|---------------|-------------------------------|----------------------|
| 59-60 | `60`, `2`     | Health check timeout/interval | Env-configurable     |
| 86    | `"0.0.0.0"`   | juniper-data bind host        | Env-configurable     |
| 87    | `8100`        | juniper-data port             | Env-configurable     |
| 100   | `"localhost"` | juniper-cascor host           | **NOT configurable** |
| 101   | `8201`        | juniper-cascor port           | Env-configurable     |
| 116   | `8050`        | juniper-canopy port           | Env-configurable     |

### 2.3 Service Shutdown (`util/juniper_chop_all.bash`)

| Line | Value  | Context               | Status           |
|------|--------|-----------------------|------------------|
| 69   | `"10"` | SIGTERM timeout (sec) | Env-configurable |
| 70   | `"1"`  | Kill workers flag     | Env-configurable |

### 2.4 Worktree Cleanup (`util/worktree_cleanup.bash`) — NOT COVERED

| Line | Value                                      | Context               | Proposed Fix                                |
|------|--------------------------------------------|-----------------------|---------------------------------------------|
| 39   | `/home/pcalnon/Development/.../juniper-ml` | Absolute path         | Derive from `git rev-parse --show-toplevel` |
| 40   | `.claude/worktrees`                        | Relative worktree dir | Extract to variable                         |
| 52   | `"main"`                                   | Default parent branch | Already CLI-configurable                    |

### 2.5 Documentation Validator (`util/check_doc_links.py`) — PARTIALLY COVERED

| Line    | Value  | Context                           | Status                            |
|---------|--------|-----------------------------------|-----------------------------------|
| 107     | `5`    | Max traversal depth               | Defined as `_MAX_TRAVERSAL_DEPTH` |
| 125-126 | `3`    | Min repos for ecosystem detection | Inline literal                    |
| 212     | `1, 6` | Markdown heading level range      | Inline literals                   |

### 2.6 Test Files — NOT COVERED

| File                       | Line  | Value  | Context                     | Proposed Constant         |
|----------------------------|-------|--------|-----------------------------|---------------------------|
| `test_worktree_cleanup.py` | 26-27 | `30`   | Subprocess timeout (sec)    | `SCRIPT_TIMEOUT`          |
| `test_wake_the_claude.py`  | 67    | `2.0`  | Invocation log wait timeout | `INVOCATION_WAIT_TIMEOUT` |
| `test_wake_the_claude.py`  | 86    | `0.05` | Poll sleep interval         | `POLL_SLEEP_INTERVAL`     |
| `scripts/test.bash`        | 8, 19 | `12`   | Sleep between test runs     | `TEST_SLEEP_INTERVAL`     |

---

## 3. Coverage Summary

| Category            | Total   | Covered | Not Covered | Priority   |
|---------------------|---------|---------|-------------|------------|
| CasCor API URLs     | 6       | 0       | 6           | **HIGH**   |
| Service Ports/Hosts | 6       | 5       | 1           | **MEDIUM** |
| Worktree Config     | 3       | 1       | 2           | **MEDIUM** |
| Test Timeouts       | 4       | 0       | 4           | **LOW**    |
| Doc Validator       | 3       | 1       | 2           | **LOW**    |
| Service Shutdown    | 2       | 2       | 0           | —          |
| **TOTAL**           | **~35** | **~9**  | **~26**     | —          |

---

## 4. Remediation Approach

### Recommended: Environment Variables + Shared Config

1. **CasCor utilities**: Add `CASCOR_URL=${CASCOR_URL:-http://localhost:8201}` to each script
2. **Worktree cleanup**: Replace absolute path with `git rev-parse --show-toplevel`
3. **Test constants**: Add shared constants at top of test files or in a `tests/conftest.py`
4. **Shared script config**: Consider `util/config.sh` sourced by utility scripts

---

## 5. Files Requiring Modification

| File                               | Action                                      | Changes |
|------------------------------------|---------------------------------------------|---------|
| `util/get_cascor_*.bash` (6 files) | **MODIFY** — add env var default            | 6       |
| `util/worktree_cleanup.bash`       | **MODIFY** — derive path dynamically        | 2       |
| `util/juniper_plant_all.bash`      | **MODIFY** — make cascor host configurable  | 1       |
| `tests/test_worktree_cleanup.py`   | **MODIFY** — extract timeout constant       | 1       |
| `tests/test_wake_the_claude.py`    | **MODIFY** — extract timeout/poll constants | 2       |

---

## 6. Risk Assessment

| Risk                             | Likelihood | Impact | Mitigation                               |
|----------------------------------|------------|--------|------------------------------------------|
| CasCor URL change breaks queries | Very Low   | Low    | Default matches current value            |
| Worktree path detection fails    | Low        | Medium | Test `git rev-parse` in worktree context |
| Test timing changes              | Very Low   | Low    | Constants preserve current values        |
