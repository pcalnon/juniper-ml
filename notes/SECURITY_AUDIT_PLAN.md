# Juniper Ecosystem Security Audit

**Date**: 2026-03-03
**Author**: Paul Calnon (with Claude Code)
**Scope**: All 8 Juniper repositories
**Branch**: `feature/security-hardening` (per repo)

---

## Executive Summary

A comprehensive security audit of the Juniper microservice ecosystem identified 24 findings across 7 severity tiers. All HIGH and CRITICAL findings have been addressed. The audit hardened API security defaults, Docker deployment, WebSocket authentication, supply chain integrity, and error handling across the entire ecosystem.

**Key outcomes**:
- CORS wildcard defaults replaced with empty allow-lists
- Rate limiting enabled by default across all 3 services
- Security headers (HSTS, CSP, X-Frame-Options, etc.) added to all HTTP responses
- WebSocket endpoints now require API key authentication
- Docker Compose hardened with network isolation, capability dropping, and localhost port bindings
- PyPI build attestations enabled on all published packages
- Scheduled weekly security scanning (Bandit + pip-audit) added to 6 repos
- Error responses sanitized to prevent information leakage

---

## Findings Summary

| # | Finding | Severity | Status | Phase |
|---|---------|----------|--------|-------|
| 1 | No security headers on HTTP responses | HIGH | RESOLVED | 1 |
| 2 | Error details (stack traces, internal messages) exposed to clients | HIGH | RESOLVED | 1 |
| 3 | Rate limiting disabled by default | HIGH | RESOLVED | 1 |
| 4 | CORS wildcard `["*"]` default in all 3 services | HIGH | RESOLVED | 1 |
| 5 | Docker ports bound to 0.0.0.0 (all interfaces) | HIGH | RESOLVED | 2 |
| 6 | No Docker network isolation between services | HIGH | RESOLVED | 2 |
| 7 | No TLS for inter-service communication | MEDIUM | DOCUMENTED | — |
| 8 | SSH public keys with PII in canopy repo | MEDIUM | NOT APPLICABLE | 5 |
| 9 | WebSocket endpoints accept oversized messages | MEDIUM | RESOLVED | 3 |
| 10 | WebSocket messages lack schema validation | MEDIUM | RESOLVED | 3 |
| 11 | WebSocket connections have no idle timeout | MEDIUM | RESOLVED | 3 |
| 12 | WebSocket endpoints bypass all authentication | CRITICAL | RESOLVED | 3 |
| 13 | Loose input validation (`dict[str, Any]` params) | MEDIUM | DOCUMENTED | — |
| 14 | Pickle deserialization in snapshot loader | MEDIUM | DOCUMENTED | 5 |
| 15 | No request body size limits | MEDIUM | RESOLVED | 4 |
| 16 | Worker auth key hardcoded default `"juniper"` | MEDIUM | RESOLVED | 5 |
| 17 | `/metrics` endpoint unauthenticated | MEDIUM | RESOLVED | 4 |
| 18 | API docs (Swagger/Redoc) exposed in production | LOW | RESOLVED | 4 |
| 19 | Build attestations disabled on 3 packages | MEDIUM | RESOLVED | 6 |
| 20 | No container security hardening (cap_drop, no-new-privileges) | MEDIUM | RESOLVED | 2 |
| 21 | Unpinned third-party Docker images (prometheus, grafana) | LOW | RESOLVED | 2 |
| 22 | Default Grafana admin password `"admin"` | LOW | RESOLVED | 2 |
| 23 | No scheduled dependency vulnerability scanning | LOW | RESOLVED | 6 |
| 24 | Bandit CI uses `|| true`, masking security failures | LOW | RESOLVED | 6 |

**Resolution stats**: 20 RESOLVED, 3 DOCUMENTED (deferred/accepted risk), 1 NOT APPLICABLE

---

## Phase-by-Phase Implementation

### Phase 1: Critical Quick Wins

**1.1 Security Headers Middleware**

Added `SecurityHeadersMiddleware` to all 3 services:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (conditional on HTTPS)
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` (APIs) / relaxed for Canopy (Dash needs `unsafe-inline`)

Files modified:
- `juniper-data/juniper_data/api/middleware.py`
- `juniper-cascor/src/api/middleware.py`
- `juniper-canopy/src/middleware.py`

**1.2 Error Response Sanitization**

Replaced `str(exc)` in error handlers with generic messages. Internal details logged at DEBUG/ERROR level only.

Files modified:
- `juniper-data/juniper_data/api/app.py` (ValueError + general exception handlers)
- `juniper-cascor/src/api/app.py` (ValueError + general exception handlers)
- `juniper-cascor/src/api/routes/training.py` (HTTPException handlers)
- `juniper-cascor/src/api/routes/network.py` (HTTPException handlers)
- `juniper-cascor/src/api/websocket/control_stream.py` (WS error messages)

**1.3 Rate Limiting Enabled by Default**

Changed rate limiting default from `False`/disabled to `True`/enabled in all 3 services. Existing environment variable overrides still work for operators who need to disable it.

Files modified:
- `juniper-data/juniper_data/api/settings.py`
- `juniper-cascor/src/api/settings.py`
- `juniper-canopy/src/settings.py`

**1.4 CORS Restrictive Defaults**

Changed CORS `allow_origins` default from `["*"]` to `[]` (empty list). Operators must explicitly configure allowed origins via environment variables.

Files modified:
- `juniper-data/juniper_data/api/settings.py`
- `juniper-cascor/src/api/settings.py`
- `juniper-canopy/src/settings.py`
- `juniper-deploy/docker-compose.yml` (added explicit CORS_ORIGINS for Docker networking)

---

### Phase 2: Docker & Network Hardening

**2.1 Docker Network Isolation**

Added 3 isolated networks to `docker-compose.yml`:
- `frontend` (bridge) — canopy exposed to host
- `backend` (bridge, internal) — cascor accessible from canopy only
- `data` (bridge, internal) — data accessible from cascor and canopy

**2.2 Localhost Port Bindings**

Changed port mappings from `"${PORT}:${PORT}"` to `"127.0.0.1:${PORT}:${PORT}"` for internal services.

**2.3 Container Security Options**

Added to all Juniper service containers:
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

**2.4 Pinned Docker Images**

Changed `prom/prometheus:latest` → `prom/prometheus:v3.2.1` and `grafana/grafana:latest` → `grafana/grafana:12.3.0`.

**2.5 Grafana Password Requirement**

Removed default `"admin"` fallback: `GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_ADMIN_PASSWORD}"` (requires explicit env var).

File modified: `juniper-deploy/docker-compose.yml`

---

### Phase 3: WebSocket Security

**3.1 WebSocket Authentication**

Added API key validation at WebSocket connection accept in both cascor and canopy. Unauthenticated connections are closed with code 4001.

**3.2 WebSocket Message Size Limits**

Added message length validation before JSON parsing. Default limits: 64KB for control messages, 1MB for data streams.

**3.3 WebSocket Message Schema Validation**

Added Pydantic model validation for control messages with `command` and `params` fields.

**3.4 WebSocket Idle Connection Timeout**

Added idle connection tracking and cleanup for connections idle > 5 minutes.

Files modified:
- `juniper-cascor/src/api/websocket/control_stream.py`
- `juniper-cascor/src/api/websocket/training_stream.py`
- `juniper-canopy/src/main.py` (WS handlers)

---

### Phase 4: API Security Improvements

**4.1 Protect /metrics Endpoint**

Removed `/metrics` from the authentication-exempt paths list in all 3 service middleware files. Prometheus scrape config updated with API key header.

**4.2 Disable API Docs in Production**

Added conditional `docs_url`/`redoc_url`/`openapi_url` based on whether API keys are configured. When API keys are set (production), interactive docs are disabled.

Files modified:
- `juniper-data/juniper_data/api/app.py`
- `juniper-cascor/src/api/app.py`
- `juniper-canopy/src/main.py`

**4.3 Request Body Size Limits**

Added `RequestBodyLimitMiddleware` (10MB default) to all 3 services. Returns HTTP 413 for oversized requests.

Files modified:
- `juniper-data/juniper_data/api/middleware.py` + `app.py`
- `juniper-cascor/src/api/middleware.py` + `app.py`
- `juniper-canopy/src/middleware.py` + `main.py`

---

### Phase 5: Secrets & Data Integrity

**5.1 PII File**

`juniper-canopy/resources/pi_cluster_keys.md` is NOT git-tracked and is already excluded by `.gitignore` (`**/resources/*`). No action needed.

**5.2 Pickle Deserialization**

Added security documentation comment to `juniper-cascor/src/snapshots/snapshot_serializer.py` explaining that `pickle.loads` is used for trusted-origin-only HDF5 snapshots. Short-term mitigation; long-term migration to HDF5-only serialization recommended.

**5.3 Worker Auth Key**

Removed hardcoded `"juniper"` default from `juniper-cascor-worker`. The `authkey` field now defaults to empty string and `config.validate()` raises `WorkerConfigError` if not explicitly set via `CASCOR_AUTHKEY` env var or `--authkey` CLI flag.

Files modified:
- `juniper-cascor-worker/juniper_cascor_worker/config.py`
- `juniper-cascor-worker/juniper_cascor_worker/cli.py`

---

### Phase 6: Supply Chain Security

**6.1 Build Attestations**

Enabled `attestations: true` in `publish.yml` for all 3 repos that had it disabled:
- `juniper-canopy/.github/workflows/publish.yml`
- `juniper-data-client/.github/workflows/publish.yml`
- `juniper-ml/.github/workflows/publish.yml`

**6.2 Scheduled Dependency Scanning**

Created `.github/workflows/security-scan.yml` in 6 repos with weekly Monday 06:00 UTC cron schedule:
- `juniper-data` (bandit + pip-audit)
- `juniper-cascor` (bandit + pip-audit)
- `juniper-canopy` (bandit + pip-audit with .bandit.yml config)
- `juniper-data-client` (bandit + pip-audit)
- `juniper-cascor-worker` (bandit + pip-audit)
- `juniper-ml` (pip-audit only — meta-package, no source code)

**6.3 Bandit CI Fallback Fix**

Fixed `juniper-cascor/.github/workflows/ci.yml` line 472: replaced `bandit ... || true` with two-stage approach (SARIF with `--exit-zero` + blocking check with `--confidence-level medium --severity-level medium`). Also upgraded `bandit` to `bandit[sarif]` for proper SARIF output support.

---

## Documented / Deferred Findings

### Finding 7: No TLS for Inter-Service Communication

**Risk**: Medium. Inter-service HTTP traffic is unencrypted within Docker network.
**Mitigation**: Docker internal networks are isolated. For production, deploy behind a reverse proxy (Traefik, nginx) with TLS termination.
**Status**: Documented — requires infrastructure-level change beyond application code.

### Finding 13: Loose Input Validation

**Risk**: Medium. Some API parameters use `dict[str, Any]` without strict schema validation.
**Mitigation**: Existing Pydantic models validate most inputs. Tighter schemas recommended for future development.
**Status**: Documented — incremental improvement, not a blocking security issue.

### Finding 14: Pickle Deserialization

**Risk**: Medium. `pickle.loads` in snapshot serializer could execute arbitrary code if loading untrusted files.
**Mitigation**: Security documentation added. Snapshots are trusted-origin-only artifacts created by the application itself. Long-term: migrate to HDF5-only serialization.
**Status**: Documented with mitigation comment in code.

---

## Cross-Repo Consistency Verification

All checks passed across applicable repos:

| Check | juniper-data | juniper-cascor | juniper-canopy | juniper-deploy |
|-------|:---:|:---:|:---:|:---:|
| SecurityHeadersMiddleware | PASS | PASS | PASS | N/A |
| CORS restrictive defaults | PASS | PASS | PASS | N/A |
| Rate limiting enabled | PASS | PASS | PASS | N/A |
| Error sanitization | PASS | PASS | PASS | N/A |
| RequestBodyLimitMiddleware | PASS | PASS | PASS | N/A |
| Conditional API docs | PASS | PASS | PASS | N/A |
| WebSocket auth | N/A | PASS | PASS | N/A |
| Build attestations | N/A | N/A | PASS | N/A |
| Security-scan.yml | PASS | PASS | PASS | N/A |
| Docker hardening | N/A | N/A | N/A | PASS |

---

## Remaining Recommendations

1. **TLS termination**: Deploy reverse proxy for production inter-service TLS
2. **Pickle migration**: Plan HDF5-only serialization for snapshot system
3. **Input validation tightening**: Add strict Pydantic schemas for remaining `dict[str, Any]` parameters
4. **juniper-cascor-client**: Not included in this audit (no worktree created). Should receive security-scan.yml and attestation review in a follow-up
5. **Dependency pinning**: Consider adding `pip-compile` / lockfile workflow to cascor-worker and ml repos
6. **SBOM generation**: Add CycloneDX or SPDX SBOM generation to publish workflows for supply chain transparency

---

## Changed Files by Repository

### juniper-data (3 modified, 1 new)
- `juniper_data/api/app.py` — Security headers registration, error sanitization, conditional docs, body limit middleware
- `juniper_data/api/middleware.py` — SecurityHeadersMiddleware, RequestBodyLimitMiddleware
- `juniper_data/api/settings.py` — CORS default `[]`, rate limiting default `True`
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning

### juniper-cascor (8 modified, 1 new)
- `.github/workflows/ci.yml` — Bandit `|| true` fix, `bandit[sarif]` install
- `src/api/app.py` — Security headers registration, error sanitization, conditional docs, body limit middleware
- `src/api/middleware.py` — SecurityHeadersMiddleware, RequestBodyLimitMiddleware
- `src/api/routes/network.py` — Error response sanitization
- `src/api/routes/training.py` — Error response sanitization
- `src/api/settings.py` — CORS default `[]`, rate limiting default `True`
- `src/api/websocket/control_stream.py` — WS auth, message validation, error sanitization
- `src/snapshots/snapshot_serializer.py` — Pickle security documentation
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning

### juniper-canopy (5 modified, 1 new)
- `.github/workflows/publish.yml` — Build attestations enabled
- `src/main.py` — Security headers registration, WS auth, conditional docs, body limit middleware
- `src/middleware.py` — SecurityHeadersMiddleware, RequestBodyLimitMiddleware
- `src/security.py` — Rate limiting default enabled
- `src/settings.py` — CORS default `[]`, rate limiting default `True`
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning

### juniper-deploy (1 modified)
- `docker-compose.yml` — Network isolation, localhost ports, security_opt, cap_drop, pinned images, Grafana password

### juniper-cascor-worker (2 modified, 1 new)
- `juniper_cascor_worker/cli.py` — Auth key resolution from env/CLI, validation
- `juniper_cascor_worker/config.py` — Auth key default removed, validation added
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning

### juniper-data-client (1 modified, 1 new)
- `.github/workflows/publish.yml` — Build attestations enabled
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning

### juniper-ml (1 modified, 1 new)
- `.github/workflows/publish.yml` — Build attestations enabled
- `.github/workflows/security-scan.yml` — NEW: weekly security scanning (pip-audit only)
