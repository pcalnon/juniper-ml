# Requirements — juniper-deploy (dep)

**Total entries**: 29

**By status**: proposed=26 | shipped=2 | deferred=1

**By priority**: P0=5 | P1=15 | P2=9

**By category**: OBS=12 | DEP=6 | SEC=5 | OPS=2 | TOOL=2 | TEST=2

---

### JR-DEP-OBS-001 — Add juniper_cascor_training_sessions_completed_total counter with closed-set outcome labels.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 808-827)

**Detail**:

juniper_cascor_training_sessions_completed_total does not exist as of 2026-05-03.
Cascor currently exposes only training_sessions_active (Gauge) and training_epochs_total (Counter).
Recommendation: add counter with closed-set outcome ∈ {success, error, aborted} bumped from
training-loop completion handler. ~50 lines, R5.4 PR or separate R5.5a sub-track.

### JR-DEP-OBS-002 — Create Grafana dashboards for CasCor training, Data throughput, and Canopy requests.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 75-119)

**Detail**:

Phase 1 (v0.2.0) observability hardening. Three new dashboards: (1) cascor-training.json
with epoch progress, loss, hidden unit additions, latency histogram; (2) data-service.json
with generation rate, request count by endpoint, response time percentiles, error rate;
(3) canopy-requests.json with HTTP rate, WS connections, response codes, page load times.
Dashboard provider already watches provisioning directory; new JSON files auto-load.

### JR-DEP-OBS-003 — Create Prometheus alerting rules for health, latency, error rate, and restart loop.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 111-119)

**Detail**:

Phase 1. Create prometheus/alerts.yml with recording and alerting rules: service health
endpoint down > 2 min, request error rate > 5%, P95 latency > 2s, container restart loop.
Wire into prometheus/prometheus.yml via rule_files directive. Add Grafana alert contact
point configuration to provisioning.

### JR-DEP-OPS-001 — Fix critical AGENTS.md documentation errors: Grafana password, rate limiting defaults.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 9-26)

**Detail**:

Phase 1 (P0 priority, blocks other work). Step 1.1: Replace GRAFANA_ADMIN_PASSWORD
default 'admin' with GF_SECURITY_ADMIN_PASSWORD__FILE referencing Docker secret.
Step 1.2: Update JUNIPER_CASCOR_RATE_LIMIT_ENABLED and CANOPY_RATE_LIMIT_ENABLED
defaults from false to true (matches docker-compose.yml).

### JR-DEP-OBS-004 — Ship Prometheus burn-rate alerting rules derived from SLO targets with MWMBR pattern.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 102-140)

**Detail**:

Implement Multi-Window Multi-Burn-Rate alerts for the 5 user-facing SLOs (§3).
Fast-burn (5m/1h @ 14.4×) and mid-burn (30m/6h @ 6×) page on-call.
Slow-burn (2h/24h @ 3×) and long-burn (6h/72h @ 1×) create tickets only.
Internal-supporting SLIs (§4) emit log-only-severity alerts with same MWMBR shape.

### JR-DEP-OBS-005 — Define and catalogue 5 user-facing and 8 internal-supporting SLO/SLI targets for the Juniper observability stack.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 1-50)

**Detail**:

The SLO catalog is the single source of truth for Juniper SLOs. User-facing SLIs
(canopy availability, canopy render latency, cascor train-job success, cascor train-epoch p95,
data POST availability) are release-blocking with tight SLO targets. Internal-supporting SLIs
(worker heartbeat freshness, cascor pending-task queue, broadcast fan-out p95, command-handler
p95, data-client request latency, data-client error rate, dataset cache-hit ratio, http 5xx rate)
are graphed but not paging.

**Notes**:

SLO targets are provisional pending 30-day soak (§2.6). Burn-rate alerting uses
Multi-Window Multi-Burn-Rate pattern. Several forward-references to R5.3/R5.4 designs.

### JR-DEP-OBS-006 — Maintain health-readiness probe topology as a DAG with asymmetric severity policies.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 1-87)

**Detail**:

Canopy probes both cascor and data, returns 200 degraded (dashboard stays visible).
Cascor probes data (when URL set), returns 503 not_ready (gates traffic). Data probes
storage only, returns 503 not_ready. Worker probes nothing externally. Topology is
intentionally a DAG to avoid cascading false-503s. Regression tests pin both policies.
Document in repo readiness handlers.

**Notes**:

Closes METRICS-MON R2.3 seed-15. Operator runbook in §6.

### JR-DEP-OBS-007 — Replace log-only burn-rate alert severity with paging severity after 30-day soak period.

**Status**: deferred  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 918-932)

**Detail**:

All numeric SLO targets in §3 are initial and provisional. R5.4 ships burn-rate alerts in
log-only severity. After 30-day production soak window (target 2026-06-15), compare actual
burn rates against targets, tighten or relax as needed, and lift log-only severity to paging
for §3.1, §3.2, §3.5 (which have all pre-conditions met today).

### JR-DEP-DEP-001 — Add juniper-cascor-worker service to docker-compose.yml under full profile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 154-180)

**Detail**:

Phase 3 (v0.4.0) worker integration. Add juniper-cascor-worker service with build context
../juniper-cascor-worker, environment variables (CASCOR_SERVICE_URL, WORKER_ID, WORKER_LOG_LEVEL).
Attach to backend bridge network (same as cascor). Add depends_on: juniper-cascor: condition: service_healthy.
Define health check endpoint or process check. Add deploy.replicas for horizontal scaling (default 1).
Add WORKER_REPLICAS env var for override. Document scaling in README.

### JR-DEP-DEP-002 — Add juniper.target and per-service systemd unit files with dependency ordering.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 89-165)

**Detail**:

juniper.target groups all services. juniper-data.service runs first (MemoryMax=2G, CPUQuota=200%).
juniper-cascor.service depends on data (MemoryMax=8G, CPUQuota=400%). juniper-canopy.service
wants cascor softly (falls back to demo mode). All use ExecStartPost wait_for_health.sh gate.
Security hardening: NoNewPrivileges=true, ProtectSystem=strict, ProtectHome=read-only.

### JR-DEP-SEC-001 — Add reverse proxy (Traefik or Caddy) with TLS termination to production profile.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 135-152)

**Detail**:

Phase 2. Proxy service in production profile terminates TLS; services communicate
over plaintext on internal networks. Support both self-signed certificates (dev)
and Let's Encrypt (production). Expose only ports 443 (HTTPS) and optionally 80
(redirect) on host.

### JR-DEP-OBS-008 — Bridge juniper_cascor_pending_tasks gauge from worker coordinator queue depth to Prometheus.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 510-532)

**Detail**:

R4.4 worker heartbeat SLO (§4.1) is resolved via WorkerRegistryCollector. But §4.2
(pending-task queue depth) still requires a juniper_cascor_pending_tasks gauge from the
worker coordinator. Small cascor sub-track to add to existing WorkerRegistryCollector,
populated from coordinator's pending-task queue depth.

### JR-DEP-SEC-002 — Complete SOPS secrets management with .env.secrets example and make targets.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 143-152)

**Detail**:

Phase 2. Create .env.secrets.example documenting all secret variables (API keys,
Grafana admin password, Sentry DSNs). Add make secrets-encrypt / make secrets-decrypt
targets wrapping sops commands. Document workflow in docs/SECRETS_GUIDE.md. Ensure CI
does not require decrypted secrets (use ${VAR:-} defaults).

### JR-DEP-OBS-009 — Consolidate health check timings and Prometheus scrape intervals into .env variables.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 9-145)

**Detail**:

110+ hardcoded values across docker-compose.yml, Prometheus configs, alert rules, scripts.
~24 are env-configurable, ~85 remain hardcoded. Priority HIGH: health check timings (28 values)
and Prometheus config (7 values). Approach A (RECOMMENDED): Docker Compose extension fields
(x-healthcheck-defaults) + .env expansion. Create scripts/config.sh for shell script defaults.
Add ~20 new variables to .env.example: HEALTHCHECK_INTERVAL, TIMEOUT, START_PERIOD, RETRIES;
PROMETHEUS_SCRAPE_INTERVAL, EVAL_INTERVAL, SCRAPE_TIMEOUT; per-service intervals.

### JR-DEP-TOOL-001 — Create juniper-ctl CLI wrapper for systemd management (start/stop/restart/logs/health/resources).

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 256-274)

**Detail**:

Management CLI wrapping systemctl --user commands with 10+ subcommands:
start/stop/restart (single or all), status (all services), logs/follow, health (latest checks),
resources (CPU/memory/IO usage), install (symlink units + daemon-reload), enable/disable (auto-start).

### JR-DEP-OBS-010 — Decide on per-service vs. shared library approach for MetricsAuthMiddleware.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (lines 1-60)

**Detail**:

juniper-data ships MetricsAuthMiddleware (IP allowlist on /metrics). Cascor and canopy
expose /metrics without in-process auth. Question: lift to juniper-observability shared lib
or keep per-service? Decision (locked 2026-05-02): keep per-service. Cascor/canopy are
network-isolated (ClusterIP, no ingress routing); data is exposed beyond cluster boundary.
Asymmetry is deliberate. Re-open if: cascor/canopy exposed beyond boundary, third service
needs middleware, compliance audit mandates uniform posture, or NetworkPolicy isolation breaks.

### JR-DEP-OBS-011 — Define and document alert rule thresholds as environment-configurable constants.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 55-66)

**Detail**:

Prometheus alert_rules.yml contains 10+ hardcoded thresholds (error rate 0.05, data P95
latency 2.0s, cascor P95 5.0s, dataset gen 30.0s, correlation 0.01, restart count 3, windows
1m/5m/10m/15m/30m). Document all values clearly in YAML comments. Consider envsubst preprocessing
for full configurability across deployment targets. Medium priority per analysis.

### JR-DEP-DEP-003 — Define production Docker Compose profile with resource limits, restart policies, log rotation.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 121-152)

**Detail**:

Phase 2 (v0.3.0) production readiness. Add --profile production to docker-compose.yml
or docker-compose.production.yml override. Per-service resource limits (deploy.resources.limits
for CPU and memory), restart policies (restart: always with deploy.restart_policy),
log rotation (Docker logging driver options max-size, max-file).

### JR-DEP-OBS-012 — Emit X-Juniper-Readiness response header on all /v1/health/ready endpoints.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 89-94)

**Detail**:

All four services (cascor, data, canopy, cascor-worker) must emit
X-Juniper-Readiness: ready | degraded | not_ready response header on /v1/health/ready.
Header mirrors body status field byte-for-byte. Constant single-sourced in
juniper-observability (READINESS_HEADER). Cascor-worker uses same literal without import.

### JR-DEP-SEC-003 — Fix shell injection vulnerability in wait_for_services.sh and related scripts.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 264-314)

**Detail**:

check_service() interpolates environment-derived URLs directly into inline Python code.
Malicious JUNIPER_DATA_PORT value can break out and execute arbitrary code. Same pattern found
in health_check.sh (line 59-79) and test_health_enhanced.sh (line 66). Affects wait_for_services.sh,
health_check.sh, test_health_enhanced.sh. Remediation: pass URLs via sys.argv[1] instead of
interpolating into code string. Add PORT numeric validation as defense-in-depth.

### JR-DEP-SEC-004 — Add container image security scanning (Trivy or Grype) to CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 197-203)

**Detail**:

Phase 4. Add security-scan job to CI using Trivy or Grype. Scan all locally-built
images after build step. Fail on critical/high CVEs; warn on medium. Cache
vulnerability database to reduce CI time.

### JR-DEP-TEST-001 — Add scheduled weekly integration tests to detect upstream breakage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 184-195)

**Detail**:

Phase 4 (v0.5.0) CI enhancement. Add schedule: cron: '0 6 * * 1' trigger to
.github/workflows/ci.yml or dedicated workflow. Run full Docker integration suite
weekly against main to detect upstream breakage. Notify on failure via GitHub Actions.

### JR-DEP-SEC-005 — Close secret-leak detection bypass via Gitleaks path-based allowlisting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 29-91)

**Detail**:

Gitleaks .gitleaks.toml blanket-allows files matching *.env.enc and *.env.secrets.enc,
creating bypass path for plaintext secrets. Root causes: (1) path-based allowlisting exempts
matching files from all rules, (2) pre-commit hook skipped in CI, (3) weak SOPS metadata validation
(only grep "^sops_" check). Remediation: replace path allowlist with content-based ciphertext regex,
remove CI skip, strengthen to multi-field SOPS validation + ciphertext line check.

### JR-DEP-TOOL-002 — Consolidate demo dataset parameters and shell script timeouts into config.sh.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 93-117)

**Detail**:

Shell scripts have 8 hardcoded timeouts (90s service wait, 3s poll, 3s curl, 5s health,
120s demo test, 3s demo poll, 5s training start, 90s enhanced test). Demo has 7 hardcoded
parameters (n_spirals=2, n_points=200, noise=0.15, seed=42, learning_rate=0.01, 500 epochs).
Source all from scripts/config.sh. Lower priority (LOW) per analysis.

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-DEP-DEP-005 — Docker Python 3.14 migration plan for juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/history/DOCKER_PYTHON_314_MIGRATION_PLAN.md` (lines 1-50)

### JR-DEP-TEST-002 — Extend compose validation to cover observability and production profiles.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 205-211)

**Detail**:

Phase 4. validate-compose job in ci.yml already validates full, demo, dev profiles.
Extend to validate observability and production profiles as added. Add JSON schema
validation for Grafana dashboard files (Phase 1 output).

### JR-DEP-DEP-006 — Implement native systemd user-unit deployment mode alongside Docker Compose.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 1-30)

**Detail**:

Phase 2 systemd implementation provides zero containerization overhead, direct GPU/CUDA access,
dependency ordering via systemd After=/Requires=, health monitoring via timer-triggered one-shot
services, per-service resource accounting via cgroups v2, and security hardening.
Coexists with Docker Compose deployment. Both methods manage the same 3 core services
(juniper-data, juniper-cascor, juniper-canopy) with independent conda environments.

**Design**:

File layout: systemd/user/*.service (10 unit files), systemd/install.sh, scripts/wait_for_health.sh,
scripts/health_check_systemd.sh, conf/juniper.env.example, scripts/juniper-ctl CLI wrapper.
Tasks 2.1–2.14 define complete implementation with resource limits, health checks, and lifecycle validation.

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
