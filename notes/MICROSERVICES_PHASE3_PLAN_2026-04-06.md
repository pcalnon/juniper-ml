# Phase 3: Worker Deployment & Container Integration

**Version**: 1.0.0
**Date**: 2026-04-06
**Status**: Planning
**Branch**: worktree-vivid-herding-star

## Context

juniper-cascor-worker is the only distributed Juniper component with zero deployment infrastructure — no Dockerfile, no systemd unit, no Docker Compose entry. Phase 1 (P0 startup/shutdown fixes) and Phase 2 (systemd units for data/cascor/canopy) are complete. Phase 3 fills this gap so the worker can be deployed via Docker Compose or systemd, matching the patterns established in the other services.

Design specs: `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` sections 6.2, 9.8, 9.9, 10.

---

## Prerequisites

### Clean up Phase 2 worktrees

Three stale worktrees from completed Phase 2 PRs:

- `juniper-canopy--feature--systemd-phase2--20260406-1312--2bd2f601`
- `juniper-cascor--feature--systemd-phase2--20260406-1312--231d4721`
- `juniper-data--feature--systemd-phase2--20260406-1312--dc751c9b`

Remove each with `git worktree remove`, delete remote branches, prune.

### Create Phase 3 worktrees

Create worktrees with branch `feature/phase3-worker-deployment` in:

1. **juniper-cascor-worker** — for Dockerfile, requirements.lock, .dockerignore, systemd unit, ctl script, health probe
2. **juniper-deploy** — for docker-compose.yml worker service entry

---

## Implementation Steps

### Step 3.1: Dockerfile (`juniper-cascor-worker/Dockerfile`)

Multi-stage build matching ecosystem patterns:

**Stage 1 (builder):**

- Base: `python:3.14-slim`
- Install torch CPU-only separately: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- Install locked deps: `pip install -r requirements.lock`
- Copy source and install package: `pip install --no-deps .`

**Stage 2 (runtime):**

- Base: `python:3.14-slim`
- Create non-root `juniper` user (UID/GID 1000)
- Copy site-packages and console script from builder
- Set env vars: `CASCOR_SERVER_URL` default, `CASCOR_HEARTBEAT_INTERVAL`
- Health check: process-based (see Step 3.5)
- `ENTRYPOINT ["juniper-cascor-worker"]`
- `CMD ["--server-url", "ws://juniper-cascor:8200/ws/v1/workers"]`

**Key patterns to match:**

- `--no-cache-dir` on all pip installs
- `pip install --upgrade pip wheel setuptools` before deps
- Layer caching: deps before source copy
- No `EXPOSE` (worker is a client, not a server)

### Step 3.2: requirements.lock (`juniper-cascor-worker/requirements.lock`)

Generate using `uv pip compile` (matching other repos' format) or create manually:

- Pin `numpy==2.4.4` and `websockets==16.0` (align with juniper-cascor)
- Exclude torch (installed separately in Dockerfile)
- Include transitive deps with `# via` comments

### Step 3.2b: .dockerignore (`juniper-cascor-worker/.dockerignore`)

Match juniper-data/.dockerignore pattern — exclude .git, .github, tests, docs, notes, IDE files, **pycache**, .serena, .claude, media files.

### Step 3.3: Docker Compose worker service (`juniper-deploy/docker-compose.yml`)

Add `juniper-cascor-worker` service:

```yaml
juniper-cascor-worker:
  build:
    context: ../juniper-cascor-worker
    dockerfile: Dockerfile
  profiles: ["full", "test"]
  environment:
    CASCOR_SERVER_URL: ws://juniper-cascor:8200/ws/v1/workers
    CASCOR_HEARTBEAT_INTERVAL: "10.0"
  depends_on:
    juniper-cascor:
      condition: service_healthy
  networks:
    - backend
  deploy:
    replicas: 2
  restart: unless-stopped
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
```

- **Profiles**: `full` and `test` only (not demo/dev — worker is for distributed training)
- **Network**: `backend` only (no external access needed — connects outbound to cascor)
- **Replicas**: 2 (demonstrates multi-worker capability)
- **Security**: Match existing `no-new-privileges` + `cap_drop: ALL`
- **No ports**: Worker is a client, doesn't expose ports

### Step 3.4: systemd unit + ctl script

**`juniper-cascor-worker/scripts/juniper-cascor-worker.service`:**

- Type=simple
- After=network-online.target, juniper-cascor.service
- WorkingDirectory=%h/Development/python/Juniper/juniper-cascor-worker
- EnvironmentFile=-%h/Development/python/Juniper/juniper-cascor-worker/.env
- ExecStart: `/opt/miniforge3/envs/JuniperCascor/bin/juniper-cascor-worker` (reuse JuniperCascor env — same torch/numpy deps)
- MemoryMax=4G, CPUQuota=400% (training workloads like cascor)
- Same security hardening as other units
- WantedBy=default.target

**`juniper-cascor-worker/scripts/juniper-cascor-worker-ctl`:**

- Match existing ctl script pattern (start/stop/restart/status/logs/resources)
- No `health` command initially — worker has no HTTP endpoint
- Could add health command that checks process liveness or heartbeat file

**Update `juniper-ml` systemd integration:**

- Add juniper-cascor-worker.service to `juniper-all.target` Wants list
- Add worker to `juniper-all-ctl` services array
- Add worker to `juniper_plant_all.bash` and `juniper_chop_all.bash` (both direct and systemd modes)

### Step 3.5: Health check mechanism

**Chosen approach: process-check-only (Phase 3 scope)**:

The worker is a WebSocket client with no HTTP server. A process-based check is the simplest approach that doesn't require modifying worker source code:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD pgrep -f "juniper.cascor.worker" > /dev/null || exit 1
```

**Future enhancement (separate PR):** File-based liveness probe where the worker writes a heartbeat timestamp file, and HEALTHCHECK checks file age. This would require modifying `juniper-cascor-worker` source (ws_connection.py heartbeat loop).

### Step 3.6: Testing & validation

1. `docker compose --profile full config` — validate compose syntax
2. `docker compose --profile full build juniper-cascor-worker` — verify Dockerfile builds
3. Verify systemd unit syntax: `systemd-analyze verify juniper-cascor-worker.service`
4. ShellCheck on ctl script
5. Pre-commit hooks pass on all modified files

---

## Files Modified (by repo)

**juniper-cascor-worker** (new worktree):

- `Dockerfile` (new)
- `requirements.lock` (new)
- `.dockerignore` (new)
- `scripts/juniper-cascor-worker.service` (new)
- `scripts/juniper-cascor-worker-ctl` (new)

**juniper-deploy** (new worktree):

- `docker-compose.yml` (modified — add worker service)

**juniper-ml** (current worktree):

- `scripts/juniper-all.target` (modified — add worker to Wants)
- `scripts/juniper-all-ctl` (modified — add worker to services)
- `util/juniper_plant_all.bash` (modified — add worker startup)
- `util/juniper_chop_all.bash` (modified — add worker shutdown)
- `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (modified — mark Phase 3 steps complete)

---

## Execution Order

1. Clean up Phase 2 worktrees
2. Create worktrees in juniper-cascor-worker and juniper-deploy
3. Implement Dockerfile + requirements.lock + .dockerignore (Step 3.1, 3.2, 3.2b)
4. Implement systemd unit + ctl script (Step 3.4)
5. Add Docker HEALTHCHECK (Step 3.5 — process-check)
6. Add worker to docker-compose.yml (Step 3.3)
7. Update juniper-ml systemd integration (juniper-all.target, juniper-all-ctl, plant_all, chop_all)
8. Validate (Step 3.6)
9. Update analysis document
10. Commit in each worktree, push, create PRs

---

## Design Decisions

1. **Health check scope**: Process-check now (simple, no worker code changes). File-based liveness probe deferred to a separate juniper-cascor-worker PR.
2. **Conda environment**: Worker systemd unit reuses JuniperCascor's Python (`/opt/miniforge3/envs/JuniperCascor/bin/`). Same torch/numpy/websockets dependencies. Dedicated JuniperCascorWorker env can be created later if needed.
3. **No `EXPOSE` in Dockerfile**: Worker is a WebSocket client — it connects outbound, doesn't listen on any port.
4. **No `health` command in ctl script**: Worker has no HTTP endpoint. The ctl script provides start/stop/restart/status/logs/resources only.
5. **Replicas: 2**: Docker Compose deploy replicas demonstrates multi-worker capability.
