# Phase 2 Implementation Plan: systemd Service Management

**Date**: 2026-04-06
**Author**: Claude Code
**Parent Document**: `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (Section 10, Phase 2)
**Status**: Plan -- pending approval

---

## 1. Context

Phase 1 (commit `03aec86`, PR #103 merged) overhauled the bash startup/shutdown scripts with health checks, error handling, and configurable paths. Phase 2 adds systemd user service units and management CLIs so all three services can be managed via `systemctl --user` with OS-native process supervision (auto-restart, journalctl logging, resource limits).

Work spans 4 repos: juniper-canopy (fix existing), juniper-data (new), juniper-cascor (new), juniper-ml (target + plant/chop integration).

---

## 2. Design Decisions

### 2.1 juniper-cascor bind address

**Decision**: Bind to `127.0.0.1:8200` (settings default).

The 8201 port seen in `launch_cascor.bash` and `juniper_plant_all.bash` is a Docker host-mapping convention. In systemd mode there is no Docker port mapping; the service binds directly. The `.env` file can override to 8201 or `0.0.0.0` via `JUNIPER_CASCOR_PORT` and `JUNIPER_CASCOR_HOST` without modifying the unit file.

### 2.2 juniper-all.target: Wants= vs Requires=

**Decision**: Use `Wants=` (not `Requires=`).

`Wants=` means "start these but do not fail if one fails." The three services are loosely coupled -- juniper-canopy degrades gracefully without cascor, cascor can run without canopy. `Requires=` would cause the entire target to fail if any single service fails to start, which is inappropriate.

### 2.3 Plant/chop systemd mode activation

**Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

The flag is explicit and discoverable at invocation time. The env var allows persisting the preference in shell profiles. The flag takes precedence; the env var is the fallback.

### 2.4 CLI naming convention

**Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

The name `juniper-ctl` is ambiguous -- it sounds like it controls all of Juniper. The pattern `juniper-{service}-ctl` is self-documenting. A backward-compat symlink `juniper-ctl -> juniper-canopy-ctl` preserves muscle memory.

New CLI scripts: `juniper-data-ctl`, `juniper-cascor-ctl`, `juniper-all-ctl`.

### 2.5 Resource limits

| Service        | MemoryMax | CPUQuota | Rationale                                     |
|----------------|-----------|----------|-----------------------------------------------|
| juniper-data   | 2G        | 200%     | Dataset serving, moderate memory              |
| juniper-cascor | 4G        | 400%     | Neural network training, CPU/memory intensive |
| juniper-canopy | 2G        | 200%     | Dashboard serving (existing)                  |

### 2.6 Security hardening

All service files use the same hardening pattern as the existing canopy service:

- `NoNewPrivileges=true`
- `ProtectSystem=strict`
- `ProtectHome=read-only`
- `ReadWritePaths=` for service-specific writable directories
- `PrivateTmp=true`
- `ProtectControlGroups=true`
- `ProtectKernelModules=true`
- `ProtectKernelTunables=true`

### 2.7 Step 2.7 (configurable paths) -- already done

Paths in `juniper_plant_all.bash` and `juniper_chop_all.bash` are already configurable via environment variables from Phase 1. No additional work needed.

---

## 3. Worktree Strategy

Create `feature/systemd-phase2` branch + worktree in each affected repo. Use existing juniper-ml worktree (`vivid-herding-star`).

```bash
/home/pcalnon/Development/python/Juniper/worktrees/
  juniper-canopy--feature--systemd-phase2--YYYYMMDD-HHMM--<hash>
  juniper-data--feature--systemd-phase2--YYYYMMDD-HHMM--<hash>
  juniper-cascor--feature--systemd-phase2--YYYYMMDD-HHMM--<hash>
```

juniper-ml changes go in the existing `vivid-herding-star` worktree on branch `worktree-vivid-herding-star`.

---

## 4. Execution Order

| Order | Step      | Repo           | Files                                                                                | Depends On  |
|-------|-----------|----------------|--------------------------------------------------------------------------------------|-------------|
| 1     | Setup     | all 3          | Create worktrees                                                                     | Nothing     |
| 2     | 2.3       | juniper-canopy | Fix `juniper-canopy.service`, rename `juniper-ctl` -> `juniper-canopy-ctl` + symlink | Worktree    |
| 3a    | 2.1 + 2.4 | juniper-data   | New `juniper-data.service` + `juniper-data-ctl`                                      | Worktree    |
| 3b    | 2.2 + 2.5 | juniper-cascor | New `juniper-cascor.service` + `juniper-cascor-ctl`                                  | Worktree    |
| 4     | 2.6       | juniper-ml     | New `juniper-all.target` + `juniper-all-ctl`                                         | 2.3, 3a, 3b |
| 5     | 2.8       | juniper-ml     | Modify `juniper_plant_all.bash` + `juniper_chop_all.bash`                            | 4           |
| 6     | Docs      | juniper-ml     | Update analysis document Phase 2 status                                              | 5           |
| 7     | PRs       | all            | Commit, push, create PRs in each repo                                                | 6           |

Steps 3a and 3b can be done in parallel.

---

## 5. File Specifications

### 5.1 juniper-canopy changes (Step 2.3)

**Fix** `scripts/juniper-canopy.service`:

```diff
- #   - conda environment "JuniperPython" with all dependencies installed
+ #   - conda environment "JuniperCanopy" with all dependencies installed
```

```diff
- ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050
+ ExecStart=/opt/miniforge3/envs/JuniperCanopy/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050
```

**Rename** `scripts/juniper-ctl` -> `scripts/juniper-canopy-ctl`:

- Update file header: `File Name: juniper-canopy-ctl`
- Update usage display: `juniper-canopy-ctl` in usage() function

**Add symlink** `scripts/juniper-ctl` -> `juniper-canopy-ctl`

### 5.2 juniper-data.service (Step 2.1)

**New file**: `juniper-data/scripts/juniper-data.service`

```ini
# =============================================================================
# juniper-data — systemd User Service Unit
#
# Installation:
#   mkdir -p ~/.config/systemd/user
#   cp scripts/juniper-data.service ~/.config/systemd/user/
#   systemctl --user daemon-reload
#   systemctl --user enable juniper-data
#   systemctl --user start juniper-data
#
# Logs:
#   journalctl --user -u juniper-data -f
#
# Prerequisites:
#   - conda environment "JuniperData" with all dependencies installed
#   - .env file configured in the project root (see .env.example)
# =============================================================================

[Unit]
Description=Juniper Data — Dataset Generation & Management Service
Documentation=https://github.com/pcalnon/juniper-data
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Development/python/Juniper/juniper-data
EnvironmentFile=-%h/Development/python/Juniper/juniper-data/.env
ExecStart=/opt/miniforge3/envs/JuniperData/bin/python -m juniper_data --host 0.0.0.0 --port 8100
Restart=on-failure
RestartSec=5

# Resource limits
MemoryMax=2G
CPUQuota=200%%

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/Development/python/Juniper/juniper-data/logs
ReadWritePaths=%h/Development/python/Juniper/juniper-data/data
PrivateTmp=true
ProtectControlGroups=true
ProtectKernelModules=true
ProtectKernelTunables=true

[Install]
WantedBy=default.target
```

### 5.3 juniper-data-ctl (Step 2.4)

**New file**: `juniper-data/scripts/juniper-data-ctl`

Modeled on `juniper-canopy/scripts/juniper-ctl` with:

- `SERVICE="juniper-data"`
- `HEALTH_URL="http://localhost:${JUNIPER_DATA_PORT:-8100}/v1/health/ready"`
- Same commands: start, stop, restart, status, logs, health, resources
- Same color support, error handling, resource monitoring

### 5.4 juniper-cascor.service (Step 2.2)

**New file**: `juniper-cascor/scripts/juniper-cascor.service`

```ini
# =============================================================================
# juniper-cascor — systemd User Service Unit
#
# Installation:
#   mkdir -p ~/.config/systemd/user
#   cp scripts/juniper-cascor.service ~/.config/systemd/user/
#   systemctl --user daemon-reload
#   systemctl --user enable juniper-cascor
#   systemctl --user start juniper-cascor
#
# Logs:
#   journalctl --user -u juniper-cascor -f
#
# Prerequisites:
#   - conda environment "JuniperCascor" with all dependencies installed
#   - .env file configured in the project root (see .env.example)
#   - juniper-data service running (or JUNIPER_DATA_URL set)
# =============================================================================

[Unit]
Description=Juniper CasCor — Cascade Correlation Neural Network Training Service
Documentation=https://github.com/pcalnon/juniper-cascor
After=network-online.target juniper-data.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Development/python/Juniper/juniper-cascor/src
EnvironmentFile=-%h/Development/python/Juniper/juniper-cascor/.env
ExecStart=/opt/miniforge3/envs/JuniperCascor/bin/python server.py
Restart=on-failure
RestartSec=5

# Resource limits (higher for training workloads)
MemoryMax=4G
CPUQuota=400%%

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/Development/python/Juniper/juniper-cascor/logs
ReadWritePaths=%h/Development/python/Juniper/juniper-cascor/data
ReadWritePaths=%h/Development/python/Juniper/juniper-cascor/src/cascor_snapshots
PrivateTmp=true
ProtectControlGroups=true
ProtectKernelModules=true
ProtectKernelTunables=true

[Install]
WantedBy=default.target
```

### 5.5 juniper-cascor-ctl (Step 2.5)

**New file**: `juniper-cascor/scripts/juniper-cascor-ctl`

Modeled on `juniper-canopy/scripts/juniper-ctl` with:

- `SERVICE="juniper-cascor"`
- `HEALTH_URL="http://localhost:${JUNIPER_CASCOR_PORT:-8200}/v1/health/ready"`
- Same commands: start, stop, restart, status, logs, health, resources

### 5.6 juniper-all.target (Step 2.6)

**New file**: `juniper-ml/scripts/juniper-all.target`

```ini
# =============================================================================
# juniper-all.target — systemd User Target Unit
#
# Groups all Juniper microservices for coordinated start/stop.
#
# Installation:
#   mkdir -p ~/.config/systemd/user
#   cp scripts/juniper-all.target ~/.config/systemd/user/
#   systemctl --user daemon-reload
#   systemctl --user enable juniper-all.target
#
# Usage:
#   systemctl --user start juniper-all.target   # start all services
#   systemctl --user stop juniper-all.target    # stop all services
#
# Prerequisites:
#   - All three service units installed in ~/.config/systemd/user/:
#     juniper-data.service, juniper-cascor.service, juniper-canopy.service
# =============================================================================

[Unit]
Description=Juniper — All Microservices
Documentation=https://github.com/pcalnon/juniper-ml
Wants=juniper-data.service juniper-cascor.service juniper-canopy.service
After=juniper-data.service juniper-cascor.service juniper-canopy.service

[Install]
WantedBy=default.target
```

### 5.7 juniper-all-ctl (Step 2.6)

**New file**: `juniper-ml/scripts/juniper-all-ctl`

Thin wrapper that operates on the target and all three services:

- `start/stop/restart`: operates on `juniper-all.target`
- `status`: iterates all three services with `systemctl --user status`
- `logs`: combined `journalctl --user -u juniper-data -u juniper-cascor -u juniper-canopy -f`
- `health`: calls each service's health endpoint
- `resources`: shows resource usage for all three

### 5.8 Plant/chop --systemd mode (Step 2.8)

**Modify** `juniper-ml/util/juniper_plant_all.bash`:

Add near the top after configurable paths:

```bash
USE_SYSTEMD="${USE_SYSTEMD:-0}"
if [[ "${1:-}" == "--systemd" ]]; then
    USE_SYSTEMD=1
    shift
fi
```

If systemd mode: `systemctl --user start` each service sequentially, reuse existing `wait_for_health()` after each, then exit. Skip all nohup/PID/conda logic.

**Modify** `juniper-ml/util/juniper_chop_all.bash`:

Same flag parsing. If systemd mode: `systemctl --user stop` in reverse order (canopy, cascor, data), then exit. Skip PID file logic.

---

## 6. Verification

1. `shellcheck` on all new/modified bash scripts
2. `pre-commit run` in each affected repo
3. For each service: install unit -> `systemctl --user daemon-reload` -> start -> health check -> stop
4. Test `systemctl --user start juniper-all.target` starts/stops all three
5. Test `juniper_plant_all.bash --systemd` and `juniper_chop_all.bash --systemd`
6. Existing juniper-ml tests still pass (`test_wake_the_claude.py`, `test_check_doc_links.py`, `test_worktree_cleanup.py`)

---

## 7. Notes

- **User linger**: For systemd user services to persist after logout, `loginctl enable-linger <username>` must be run. Note in installation instructions.
- **Conda env activation**: Service files use the conda env's Python binary directly (`/opt/miniforge3/envs/JuniperData/bin/python`) rather than `conda activate`. This avoids needing to source conda.sh in systemd context.
- **Secrets in .env**: The cascor `.env` contains API keys. The `EnvironmentFile` directive loads these into the service environment. File permissions should be `chmod 600 .env`.
- **EnvironmentFile dash prefix**: The `-` prefix in `EnvironmentFile=-.../.env` makes the file optional -- systemd won't fail if it's missing.

---

*End of Phase 2 Plan*:
