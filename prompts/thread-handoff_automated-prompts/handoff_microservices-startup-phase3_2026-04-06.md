# Thread Handoff: Microservices Startup -- Begin Phase 3

**Handoff Date**: 2026-04-06
**From Thread**: Phase 2 systemd service management implementation
**Worktree**: `vivid-herding-star`
**Branch**: `worktree-vivid-herding-star`

---

Continue the Juniper Microservices Startup/Shutdown automation project -- starting **Phase 3: Worker Deployment & Container Integration (P1)** from `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`.

## Prior Threads Completed

### Phase 1 (P0 Critical Fixes) -- DONE

- Overhauled `util/juniper_plant_all.bash`: `wait_for_health()`, `check_port_available()`, `validate_conda_env()`, per-service Python binaries, `set -euo pipefail`, `trap cleanup_on_failure ERR`, configurable paths/timeouts via env vars.
- Overhauled `util/juniper_chop_all.bash`: `validate_pid()` via `/proc/<pid>/cmdline`, `graceful_stop()` with SIGTERM->SIGKILL, proper PID parsing, optional `KILL_WORKERS=1`, post-shutdown cleanup.
- Removed `util/get_cascor_dkdk.bash` (dead code).
- PR #103 merged.

### Phase 2 (P1 systemd & Service Management) -- DONE

- **juniper-canopy** (PR #136 merged): Fixed `JuniperPython` -> `JuniperCanopy` in `scripts/juniper-canopy.service`. Renamed `juniper-ctl` to `juniper-canopy-ctl` with backward-compat symlink.
- **juniper-data** (PR #35 merged): Created `scripts/juniper-data.service` (systemd user unit, 2G mem, 200% CPU) and `scripts/juniper-data-ctl` management CLI.
- **juniper-cascor** (PR #115 merged): Created `scripts/juniper-cascor.service` (systemd user unit, 4G mem, 400% CPU, `After=juniper-data.service`) and `scripts/juniper-cascor-ctl` management CLI.
- **juniper-ml**: Created `scripts/juniper-all.target` (groups all services via `Wants=`) and `scripts/juniper-all-ctl` (coordinated start/stop/status/health/logs/resources). Added `--systemd` flag (`USE_SYSTEMD=1` env var) to both `juniper_plant_all.bash` and `juniper_chop_all.bash`. Fixed pre-existing shellcheck warning and duplicate PID file check.
- Analysis document (`notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`) updated to v1.2.0 with Phase 2 marked completed.
- Implementation plan at `notes/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md`.

## Phase 3 Scope

**Goal**: Enable containerized deployment of the distributed worker (`juniper-cascor-worker`).

From Section 10 Phase 3 of the analysis document:

| Step | Task                                                                      | Files                                                         | Est. Complexity |
|------|---------------------------------------------------------------------------|---------------------------------------------------------------|-----------------|
| 3.1  | Create `juniper-cascor-worker/Dockerfile`                                 | `juniper-cascor-worker/Dockerfile`                            | Medium          |
| 3.2  | Create `requirements.lock` for worker                                     | `juniper-cascor-worker/requirements.lock`                     | Low             |
| 3.3  | Add worker service to `juniper-deploy/docker-compose.yml`                 | `juniper-deploy/docker-compose.yml`                           | Medium          |
| 3.4  | Create `juniper-cascor-worker.service` systemd unit                       | `juniper-cascor-worker/scripts/juniper-cascor-worker.service` | Medium          |
| 3.5  | Add health check endpoint to worker (optional HTTP sidecar or file-based) | `juniper-cascor-worker/`                                      | High            |
| 3.6  | Test worker in Docker Compose full and test profiles                      | `juniper-deploy/tests/`                                       | Medium          |

## Key Context

- **juniper-cascor-worker** is the only distributed component with zero deployment infrastructure (no Dockerfile, no systemd, no k8s). It has a CLI entry point (`juniper-cascor-worker` command), SIGINT/SIGTERM signal handling, two operating modes (WebSocket default, legacy BaseManager), TLS/mTLS support, and exponential backoff reconnection.
- The analysis document Section 6.2 and Section 9.8-9.9 contain detailed design specs for the worker Dockerfile and Docker Compose service definition.
- Worker connects to cascor via WebSocket at `ws://juniper-cascor:8200/ws/v1/workers` (Docker) or configurable URL.
- This work spans **juniper-cascor-worker** (Dockerfile, systemd unit) and **juniper-deploy** (compose service definition, testing).
- **Approach A (Incremental Fix)** is the chosen strategy (Section 9.4). Do not switch approaches.
- Step 3.5 (health check endpoint) is the most complex item -- the worker is a WebSocket client, not an HTTP server, so health checking requires either a file-based liveness probe, an HTTP sidecar, or extending the worker to serve a minimal health endpoint.

## Worktree State

- **Current worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/vivid-herding-star`
- **Branch**: `worktree-vivid-herding-star` (up to date with remote, clean working tree)
- **Phase 2 worktrees still exist** in `/home/pcalnon/Development/python/Juniper/worktrees/` (juniper-canopy, juniper-data, juniper-cascor `feature/systemd-phase2` worktrees). These should be cleaned up before starting Phase 3.
- **All 88 juniper-ml tests pass**, shellcheck clean, pre-commit hooks pass.

## Verification Commands

```bash
# Verify worktree state
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/vivid-herding-star
git status
git log --oneline -5

# Verify tests pass
python3 -m unittest -v tests/test_wake_the_claude.py tests/test_check_doc_links.py tests/test_worktree_cleanup.py

# Read the analysis document (Phase 3 section)
head -770 notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md | tail -20

# Read the worker AGENTS.md for project context
cat /home/pcalnon/Development/python/Juniper/juniper-cascor-worker/AGENTS.md

# Read the deploy AGENTS.md for compose context
cat /home/pcalnon/Development/python/Juniper/juniper-deploy/AGENTS.md

# Check Phase 2 worktrees that need cleanup
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep systemd

# Read the design specs for worker Dockerfile and compose service
sed -n '/### 9.8/,/### 9.9/p' notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md
sed -n '/### 9.9/,/---/p' notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md
```
