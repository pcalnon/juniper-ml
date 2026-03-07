# Juniper Ecosystem — Comprehensive Security Audit Plan

**Project**: Juniper Microservice Ecosystem
**Author**: Paul Calnon (audit conducted by Claude Code)
**Date**: 2026-03-03
**Status**: Complete — All 7 phases implemented and verified
**Scope**: All 8 active Juniper repositories

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Audit Methodology](#audit-methodology)
- [Security Posture Summary](#security-posture-summary)
- [Consolidated Findings](#consolidated-findings)
- [Phase 1: Critical Quick Wins](#phase-1-critical-quick-wins-high-severity-low-difficulty)
- [Phase 2: Docker & Network Hardening](#phase-2-docker--network-hardening-high-severity-medium-difficulty)
- [Phase 3: WebSocket Security](#phase-3-websocket-security-critical-finding-medium-difficulty)
- [Phase 4: API Security Improvements](#phase-4-api-security-improvements-medium-severity)
- [Phase 5: Secrets & Data Integrity](#phase-5-secrets--data-integrity-medium-severity)
- [Phase 6: Supply Chain Security](#phase-6-supply-chain-security-medium-low-severity)
- [Phase 7: Final Audit & Documentation](#phase-7-final-audit--documentation)
- [Findings-to-Phase Mapping](#findings-to-phase-mapping)
- [Critical Files Reference](#critical-files-reference)
- [Cross-Repo Implementation Strategy](#cross-repo-implementation-strategy)
- [Existing Security Strengths](#existing-security-strengths)
- [Appendix A: Microservice Security Best Practices](#appendix-a-microservice-security-best-practices-applied)
- [Appendix B: Automated Scanning Commands](#appendix-b-automated-scanning-commands)

---

## Executive Summary

A comprehensive security audit was performed across all 8 active Juniper repositories:

| Repository | Type | Primary Concern |
|------------|------|-----------------|
| juniper-data | FastAPI REST service | API security, input validation |
| juniper-cascor | FastAPI + WebSocket ML backend | WebSocket auth, pickle deserialization |
| juniper-canopy | Dash/FastAPI monitoring dashboard | WebSocket auth, CORS, CSP |
| juniper-data-client | Python HTTP client library | Credential handling |
| juniper-cascor-client | HTTP/WebSocket client library | WS auth, message validation |
| juniper-cascor-worker | Distributed training worker | Auth key defaults |
| juniper-deploy | Docker Compose orchestration | Network isolation, port binding |
| juniper-ml | PyPI meta-package | Supply chain, attestations |

### Key Findings

- **24 security findings** identified across all repos
- **1 CRITICAL**: WebSocket endpoints completely bypass authentication middleware
- **4 HIGH**: Missing security headers, CORS wildcard defaults, rate limiting disabled, error detail exposure
- **12 MEDIUM**: Docker networking, message validation, pickle risks, /metrics exposure
- **7 LOW**: Grafana password, unpinned images, API docs in production

### Existing Strengths (Preserved)

The ecosystem has a strong security foundation including API key authentication, Bandit SAST scanning, pip-audit dependency scanning, Gitleaks secret detection, SOPS hooks, SHA-pinned GitHub Actions, OIDC trusted publishing, multi-stage Docker builds with non-root users, Pydantic validation, and Sentry integration with PII disabled.

---

## Audit Methodology

### Scope

- Static analysis of all source code, configuration files, Docker configurations, CI/CD workflows
- Dependency version analysis across all `pyproject.toml` files
- Network architecture review of inter-service communication
- Authentication and authorization flow tracing
- Input validation boundary analysis

### Standards Applied

- **OWASP API Security Top 10** (2023)
- **CIS Docker Benchmark** v1.6
- **SLSA Framework** (Supply-chain Levels for Software Artifacts)
- **Zero Trust Architecture** principles (NIST SP 800-207)
- **Defense in Depth** layering strategy

### Tools Used

- Manual code review (primary)
- Bandit (Python SAST) — already integrated in CI
- pip-audit (dependency vulnerability scanning) — already integrated in CI
- Gitleaks (secret detection) — already integrated in CI
- Docker Compose config validation

---

## Security Posture Summary

### Authentication & Authorization

| Service | API Key Auth | Rate Limiting | WebSocket Auth | Metrics Auth |
|---------|-------------|---------------|----------------|-------------|
| juniper-data | Implemented (disabled by default) | Implemented (disabled by default) | N/A | No |
| juniper-cascor | Implemented (disabled by default) | Implemented (disabled by default) | **MISSING** | No |
| juniper-canopy | Implemented (disabled by default) | Implemented (disabled by default) | **MISSING** | No |

### Network Security

| Aspect | Status |
|--------|--------|
| TLS/HTTPS | Not configured (all HTTP) |
| CORS | Wildcard `["*"]` default |
| Security Headers | None present |
| Docker Network Isolation | None (default bridge) |
| Port Binding | All interfaces (`0.0.0.0`) |
| Inter-service Auth | Optional API key headers |

### Supply Chain

| Aspect | Status |
|--------|--------|
| GitHub Actions | SHA-pinned (excellent) |
| PyPI Publishing | OIDC trusted publishing (excellent) |
| Build Attestations | Disabled (`attestations: false`) |
| Dependency Scanning | pip-audit in CI (good), no scheduled scans |
| Docker Images | Unpinned (`latest` tag) |

---

## Consolidated Findings

| # | Finding | Severity | Phase | Impact |
|---|---------|----------|-------|--------|
| F-01 | WebSocket endpoints bypass authentication entirely | CRITICAL | 3.1 | Unauthenticated access to training control and data streams |
| F-02 | No security headers middleware | HIGH | 1.1 | Clickjacking, MIME sniffing, XSS vectors |
| F-03 | ValueError details exposed in API responses | HIGH | 1.2 | Information disclosure of internal state |
| F-04 | Rate limiting disabled by default | HIGH | 1.3 | DoS vulnerability |
| F-05 | CORS defaults to wildcard `["*"]` | HIGH | 1.4 | Cross-origin request forgery vectors |
| F-06 | Docker ports exposed to all interfaces | HIGH | 2.2 | Services accessible from external networks |
| F-07 | No Docker network isolation | HIGH | 2.1 | Lateral movement between containers |
| F-08 | No TLS for inter-service communication | MEDIUM | — | Man-in-the-middle between services |
| F-09 | SSH public keys with PII in repository | MEDIUM | 5.1 | Email/IP exposure for social engineering |
| F-10 | No WebSocket message size limits | MEDIUM | 3.2 | Memory exhaustion via large messages |
| F-11 | No WebSocket message schema validation | MEDIUM | 3.3 | Malformed message injection |
| F-12 | No WebSocket idle connection timeout | MEDIUM | 3.4 | Resource exhaustion via stale connections |
| F-13 | Generic `dict[str, Any]` for generator params | MEDIUM | — | Arbitrary nested object injection |
| F-14 | Pickle deserialization in snapshot serializer | MEDIUM | 5.2 | Arbitrary code execution on untrusted snapshots |
| F-15 | No request body size limits | MEDIUM | 4.3 | OOM via large payloads |
| F-16 | Worker auth key defaults to `"juniper"` | MEDIUM | 5.3 | Trivially guessable multiprocessing auth |
| F-17 | /metrics endpoint unauthenticated | MEDIUM | 4.1 | Information disclosure of service internals |
| F-18 | No container security hardening (cap_drop) | MEDIUM | 2.3 | Unnecessary container privileges |
| F-19 | Build attestations disabled in publish workflows | MEDIUM | 6.1 | No supply chain provenance |
| F-20 | API docs exposed in production | LOW | 4.2 | API schema disclosure |
| F-21 | Unpinned third-party Docker images | LOW | 2.4 | Non-reproducible builds, supply chain risk |
| F-22 | Default Grafana admin password | LOW | 2.5 | Unauthorized dashboard access |
| F-23 | No scheduled dependency scanning | LOW | 6.2 | Delayed vulnerability detection |
| F-24 | Bandit CI uses `\|\| true` fallback | LOW | 6.3 | Security scan failures masked |

---

## Phase 1: Critical Quick Wins (High Severity, Low Difficulty)

**Objective**: Address the highest-severity findings with minimal code changes and lowest regression risk. These are "secure defaults" changes.

**Estimated effort**: 2-3 sessions
**Repos affected**: juniper-data, juniper-cascor, juniper-canopy

### Task 1.1: Add Security Headers Middleware (F-02)

**Severity**: HIGH | **Difficulty**: Low | **Files affected**: 6

**Problem**: No service sets standard security headers. This leaves the ecosystem vulnerable to clickjacking (no X-Frame-Options), MIME type sniffing attacks (no X-Content-Type-Options), and lacks basic browser-side security protections.

**Files to modify**:

| File | Change |
|------|--------|
| `juniper-data/juniper_data/api/middleware.py` | Add `SecurityHeadersMiddleware` class |
| `juniper-data/juniper_data/api/app.py` | Register middleware in `create_app()` |
| `juniper-cascor/src/api/middleware.py` | Add `SecurityHeadersMiddleware` class |
| `juniper-cascor/src/api/app.py` | Register middleware in `create_app()` |
| `juniper-canopy/src/middleware.py` | Add `SecurityHeadersMiddleware` class |
| `juniper-canopy/src/main.py` | Register middleware |

**Implementation**:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

**CSP notes**: juniper-data and juniper-cascor can use `Content-Security-Policy: default-src 'self'`. juniper-canopy needs `script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'` due to Dash's rendering requirements.

**Verification**:
```bash
curl -I http://localhost:8100/v1/health | grep -i "x-content-type\|x-frame\|referrer"
# Expected: All three headers present
```

---

### Task 1.2: Sanitize Error Responses (F-03)

**Severity**: HIGH | **Difficulty**: Low | **Files affected**: 5+

**Problem**: Exception handlers pass `str(exc)` directly to API consumers, potentially leaking internal file paths, stack traces, and implementation details.

**Files to modify**:

| File | Line(s) | Current | Fix |
|------|---------|---------|-----|
| `juniper-data/juniper_data/api/app.py` | 110-115 | `content={"detail": str(exc)}` | Generic "Invalid request parameters" |
| `juniper-cascor/src/api/app.py` | 203-208 | `error_response("VALIDATION_ERROR", str(exc))` | Generic message |
| `juniper-cascor/src/api/routes/training.py` | 61, 80, 91 | `HTTPException(detail=str(e))` | Generic per-route messages |
| `juniper-cascor/src/api/routes/network.py` | 26, 46 | `HTTPException(detail=str(e))` | Generic per-route messages |
| `juniper-cascor/src/api/websocket/control_stream.py` | 69 | `error=str(e)` | Generic "Command execution failed" |

**Implementation approach**:
- Return generic user-facing messages in responses
- Log full `str(exc)` at DEBUG level for internal diagnostics
- Consider a debug mode env var that re-enables detailed errors for development

**Verification**:
```bash
# Trigger a ValueError and verify response doesn't leak internals
curl -X POST http://localhost:8100/v1/datasets -H "Content-Type: application/json" -d '{"generator":"invalid"}'
# Expected: {"detail": "Invalid request parameters"}, NOT internal paths
```

---

### Task 1.3: Enable Rate Limiting by Default (F-04)

**Severity**: HIGH | **Difficulty**: Low | **Files affected**: 4

**Problem**: Rate limiting code exists in all 3 services but defaults to disabled. Without it, services are vulnerable to abuse and DoS.

**Files to modify**:

| File | Change |
|------|--------|
| `juniper-data/juniper_data/api/settings.py:48` | Change `_JUNIPER_DATA_API_RATELIMIT_ACTIVE_DEFAULT` to `_JUNIPER_DATA_API_RATELIMIT_ENABLED` |
| `juniper-cascor/src/api/settings.py:81` | Change default from `_JUNIPER_CASCOR_API_RATELIMIT_DISABLED` to `True` |
| `juniper-canopy/src/security.py` | Ensure rate limiting default is enabled |
| `juniper-deploy/docker-compose.yml:81,189` | Change `RATE_LIMIT_ENABLED` defaults from `false` to `true` |

**Verification**:
```bash
# Rapid-fire requests
for i in $(seq 1 65); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8100/v1/health; done
# Expected: Last responses return 429 Too Many Requests
```

---

### Task 1.4: Restrict CORS Defaults (F-05)

**Severity**: HIGH | **Difficulty**: Low | **Files affected**: 4

**Problem**: All 3 services default `allow_origins=["*"]`, permitting any origin to make cross-origin requests.

**Files to modify**:

| File | Change |
|------|--------|
| `juniper-data/juniper_data/api/settings.py:55-57` | Change `_JUNIPER_DATA_API_CORS_ORIGINS_DEFAULT` from `["*"]` to `[]` |
| `juniper-cascor/src/api/settings.py:19-20` | Change `_JUNIPER_CASCOR_API_CORS_ORIGINS_DEFAULT` from `["*"]` to `[]` |
| `juniper-canopy/src/main.py` | Ensure CORS reads from settings, not hardcoded |
| `juniper-deploy/docker-compose.yml` | Add CORS_ORIGINS env vars for Docker networking |

**Design decision**: Default to empty `[]` (no CORS) rather than `["*"]`. Services that need CORS can configure it via env vars. Docker Compose sets appropriate origins for inter-service communication.

**Verification**:
```bash
curl -H "Origin: http://evil.example.com" -I http://localhost:8100/v1/health
# Expected: No Access-Control-Allow-Origin header in response
```

---

## Phase 2: Docker & Network Hardening (High Severity, Medium Difficulty)

**Objective**: Harden Docker Compose deployment with network isolation, restricted port binding, and container security options.

**Estimated effort**: 1-2 sessions
**Repos affected**: juniper-deploy

### Task 2.1: Add Docker Network Isolation (F-07)

**Severity**: HIGH | **Difficulty**: Medium | **File**: `juniper-deploy/docker-compose.yml`

**Problem**: All containers share the default Docker bridge network with no segmentation. A compromised container can communicate with any other container.

**Implementation**:

```yaml
networks:
  frontend:
    driver: bridge
    name: juniper-frontend
  backend:
    driver: bridge
    internal: true
    name: juniper-backend
  data:
    driver: bridge
    internal: true
    name: juniper-data-net
```

**Service assignments**:

| Service | Networks | Rationale |
|---------|----------|-----------|
| juniper-data | `[data]` | Only needs to be reachable by cascor/canopy |
| juniper-cascor | `[backend, data]` | Needs data network for juniper-data, backend for canopy |
| juniper-canopy | `[frontend, backend, data]` | User-facing + needs both backend services |
| prometheus | `[backend, data, frontend]` | Needs all networks for scraping |
| grafana | `[frontend]` | User-facing only |

**Verification**:
```bash
docker compose --profile full config | grep -A5 "networks:"
docker compose --profile full up -d
# Verify data cannot reach canopy directly (internal network)
docker exec juniper-data python -c "import urllib.request; urllib.request.urlopen('http://juniper-canopy:8050')" 2>&1 | grep -i "error"
```

---

### Task 2.2: Restrict Port Bindings to Localhost (F-06)

**Severity**: HIGH | **Difficulty**: Low | **File**: `juniper-deploy/docker-compose.yml`

**Problem**: All services bind to `0.0.0.0`, making them accessible from any network interface on the host.

**Changes**:

| Service | Current | New |
|---------|---------|-----|
| juniper-data | `"${PORT}:${PORT}"` | `"127.0.0.1:${PORT}:${PORT}"` |
| juniper-cascor | `"${PORT}:${PORT}"` | `"127.0.0.1:${PORT}:${PORT}"` |
| juniper-canopy | `"${PORT}:${PORT}"` | `"${CANOPY_BIND_ADDRESS:-127.0.0.1}:${PORT}:${PORT}"` |
| prometheus | `"9090:9090"` | `"127.0.0.1:9090:9090"` |
| grafana | `"3000:3000"` | `"127.0.0.1:3000:3000"` |

Canopy is configurable via `CANOPY_BIND_ADDRESS` for scenarios where external access is needed (e.g., remote dashboard access).

---

### Task 2.3: Add Container Security Options (F-18)

**Severity**: MEDIUM | **Difficulty**: Low | **File**: `juniper-deploy/docker-compose.yml`

Add to each Juniper service definition:

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

**Note**: `read_only: true` was considered but requires writable volumes for data storage (juniper-data), logs, and tmp directories. Deferred to a future hardening pass.

---

### Task 2.4: Pin Third-Party Docker Images (F-21)

**Severity**: LOW | **Difficulty**: Low | **File**: `juniper-deploy/docker-compose.yml:271,284`

**Current**:
```yaml
image: prom/prometheus:latest
image: grafana/grafana:latest
```

**Fix**: Pin to specific versions (resolve current latest versions at implementation time):
```yaml
image: prom/prometheus:v3.2.0
image: grafana/grafana:11.5.1
```

---

### Task 2.5: Remove Default Grafana Password (F-22)

**Severity**: LOW | **Difficulty**: Trivial | **File**: `juniper-deploy/docker-compose.yml:290`

**Current**: `GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_ADMIN_PASSWORD:-admin}"`

**Fix**: `GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_ADMIN_PASSWORD:?GRAFANA_ADMIN_PASSWORD must be set}"` — forces explicit configuration, fails with clear error if unset.

---

## Phase 3: WebSocket Security (Critical Finding, Medium Difficulty)

**Objective**: Add authentication, message validation, and resource limits to all WebSocket endpoints.

**Estimated effort**: 2-3 sessions
**Repos affected**: juniper-cascor, juniper-canopy

### Task 3.1: Add WebSocket Authentication (F-01)

**Severity**: CRITICAL | **Difficulty**: Medium | **Files affected**: 4+

**Problem**: `BaseHTTPMiddleware` does **NOT** intercept WebSocket upgrade requests (documented in middleware docstrings: "WebSocket upgrade requests are not intercepted by BaseHTTPMiddleware, so /ws/* paths are inherently exempt"). This means ALL WebSocket endpoints have zero authentication regardless of API key configuration.

**Affected endpoints**:
- `juniper-cascor`: `/ws/training`, `/ws/control`
- `juniper-canopy`: `/ws/training`, `/ws/control`, `/ws`

**Files to modify**:

| File | Change |
|------|--------|
| `juniper-cascor/src/api/websocket/training_stream.py` | Add auth check before `websocket.accept()` |
| `juniper-cascor/src/api/websocket/control_stream.py` | Add auth check before `websocket.accept()` |
| `juniper-canopy/src/main.py` (WS handlers) | Add auth check before `websocket.accept()` |

**Implementation pattern**:

```python
async def websocket_handler(websocket: WebSocket):
    api_key_auth = websocket.app.state.api_key_auth
    if api_key_auth.enabled:
        api_key = websocket.headers.get("X-API-Key")
        if not api_key_auth.validate(api_key):
            await websocket.close(code=4001, reason="Authentication required")
            return
    await websocket.accept()
    # ... handler logic
```

**Verification**:
```bash
# With API keys configured, unauthenticated WS should be rejected
python -c "
import asyncio, websockets
async def test():
    try:
        async with websockets.connect('ws://localhost:8200/ws/training') as ws:
            msg = await ws.recv()
    except websockets.exceptions.ConnectionClosed as e:
        print(f'Closed: code={e.code} reason={e.reason}')
asyncio.run(test())
"
# Expected: Closed: code=4001 reason=Authentication required
```

---

### Task 3.2: Add WebSocket Message Size Limits (F-10)

**Severity**: MEDIUM | **Difficulty**: Low | **Files affected**: 4+

**Problem**: No max message size on WebSocket connections. A malicious client can send arbitrarily large messages, exhausting server memory.

**Implementation**: Add size check before JSON parsing in each handler:

```python
MAX_CONTROL_MESSAGE_SIZE = 65_536   # 64 KB for control messages
MAX_DATA_MESSAGE_SIZE = 1_048_576   # 1 MB for data messages

data = await websocket.receive_text()
if len(data) > MAX_CONTROL_MESSAGE_SIZE:
    await websocket.close(code=1009, reason="Message too large")
    return
```

---

### Task 3.3: Add WebSocket Message Schema Validation (F-11)

**Severity**: MEDIUM | **Difficulty**: Medium | **Files affected**: 2+

**Problem**: WebSocket control commands validated with basic string checks. No structured schema validation for incoming messages.

**Implementation**: Add Pydantic model for control messages:

```python
class WebSocketControlMessage(BaseModel):
    command: str
    params: dict[str, Any] = {}

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        if v not in VALID_COMMANDS:
            raise ValueError(f"Unknown command: {v}")
        return v
```

---

### Task 3.4: Add WebSocket Idle Connection Timeout (F-12)

**Severity**: MEDIUM | **Difficulty**: Low | **Files affected**: 2

**Problem**: No idle connection timeout. Stale connections consume server resources indefinitely.

**Implementation**:
- Track `last_activity_at` per connection in WebSocket manager metadata
- Periodic cleanup task (runs every 60s) closes connections idle for >5 minutes
- Configurable via `ws_idle_timeout_sec` settingh

---

## Phase 4: API Security Improvements (Medium Severity)

**Objective**: Address metrics exposure, API documentation access, and request size limits.

**Estimated effort**: 1-2 sessions
**Repos affected**: juniper-data, juniper-cascor, juniper-canopy, juniper-deploy

### Task 4.1: Protect /metrics Endpoint (F-17)

**Severity**: MEDIUM | **Difficulty**: Low | **Files affected**: 4

**Problem**: `/metrics` is in `EXEMPT_PATHS` in all three services' middleware, exposing Prometheus metrics without authentication. Metrics can reveal service internals, request patterns, and error rates.

**Files to modify**:
- `juniper-data/juniper_data/api/middleware.py:17` — Remove `/metrics` from `EXEMPT_PATHS`
- `juniper-cascor/src/api/middleware.py:17` — Remove `/metrics` from `EXEMPT_PATHS`
- `juniper-canopy/src/middleware.py:27` — Remove `/metrics` from `EXEMPT_PATHS`
- `juniper-deploy/prometheus/prometheus.yml` — Add API key in scrape headers

---

### Task 4.2: Disable API Docs in Production (F-20)

**Severity**: LOW | **Difficulty**: Low | **Files affected**: 3

**Problem**: `/docs`, `/openapi.json`, and `/redoc` are always available, exposing full API schema.

**Implementation**: Add conditional docs based on settings:

```python
docs_enabled = settings.docs_enabled if hasattr(settings, 'docs_enabled') else (settings.api_keys is None)
app = FastAPI(
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    ...
)
```

When API keys are configured (production), docs are disabled by default. Override via `JUNIPER_DATA_DOCS_ENABLED=true`.

---

### Task 4.3: Add Request Body Size Limits (F-15)

**Severity**: MEDIUM | **Difficulty**: Low | **Files affected**: 3

**Problem**: No maximum request body size. Large payloads can cause OOM.

**Implementation**: Add middleware or configure uvicorn's `--limit-max-request-size` (default: 10MB).

---

## Phase 5: Secrets & Data Integrity (Medium Severity)

**Objective**: Address PII in repository, pickle deserialization risks, and worker authentication.

**Estimated effort**: 1-2 sessions
**Repos affected**: juniper-canopy, juniper-cascor, juniper-cascor-worker

### Task 5.1: Remove PII from Repository (F-09)

**Severity**: MEDIUM | **Difficulty**: Low

**File**: `juniper-canopy/resources/pi_cluster_keys.md`

**Problem**: Contains SSH public keys with email addresses (`paul.calnon@gmail.com`) and internal IP addresses. While SSH public keys are not credentials, the associated PII enables targeted social engineering.

**Fix**:
1. `git rm juniper-canopy/resources/pi_cluster_keys.md`
2. Add `resources/pi_cluster_keys.md` to `juniper-canopy/.gitignore`
3. Move content to a private location outside the repository
4. Consider `git filter-repo` to remove from history if deemed necessary

---

### Task 5.2: Mitigate Pickle Deserialization Risk (F-14)

**Severity**: MEDIUM | **Difficulty**: High (full migration) / Low (mitigation)

**File**: `juniper-cascor/src/snapshots/snapshot_serializer.py`

**Problem**: Uses `pickle.dumps()` and `pickle.loads()` for snapshot serialization. Pickle deserialization of untrusted data enables arbitrary code execution. The file already has `# trunk-ignore(bandit/B403)` comments acknowledging the risk.

**Short-term mitigation** (recommended):
- Add HMAC signature verification before any `pickle.loads()` call
- Only deserialize snapshots signed with a project-specific secret key
- Document that snapshots are trusted-origin-only artifacts

```python
import hmac, hashlib

def verified_pickle_loads(data: bytes, signature: bytes, key: bytes) -> Any:
    expected = hmac.new(key, data, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Snapshot integrity check failed — refusing to deserialize")
    return pickle.loads(data)  # nosec B301
```

**Long-term**: Evaluate migration to HDF5-only serialization (already partially done for network state).

---

### Task 5.3: Strengthen Worker Auth Key (F-16)

**Severity**: MEDIUM | **Difficulty**: Low

**Problem**: `juniper-cascor-worker` defaults `CASCOR_AUTHKEY` to the string `"juniper"`, making it trivially guessable for multiprocessing authentication.

**Fix**:
- Remove hardcoded default
- Require explicit `CASCOR_AUTHKEY` environment variable
- Fail startup with clear error if not set
- Document in `.env.example`

---

## Phase 6: Supply Chain Security (Medium-Low Severity)

**Objective**: Strengthen build provenance, dependency scanning, and CI security.

**Estimated effort**: 1-2 sessions
**Repos affected**: All

### Task 6.1: Enable PyPI Build Attestations (F-19)

**Severity**: MEDIUM | **Difficulty**: Low

**Problem**: `attestations: false` in publish workflows for juniper-ml, juniper-data-client, juniper-canopy. Other repos omit the setting (defaults to false).

**Files to modify**: `publish.yml` in all repos — change to `attestations: true`. Ensure `id-token: write` permission.

---

### Task 6.2: Add Scheduled Dependency Scanning (F-23)

**Severity**: LOW | **Difficulty**: Low

Create `.github/workflows/security-scan.yml` in each repo:

```yaml
name: Security Scan
on:
  schedule:
    - cron: '0 8 * * 1'  # Weekly Monday 8am UTC
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.14' }
      - run: pip install pip-audit bandit
      - run: pip-audit --strict --desc on
      - run: bandit -r <source-dir> -f sarif -o bandit-report.sarif || true
```

---

### Task 6.3: Fix Bandit CI Fallback (F-24)

**Severity**: LOW | **Difficulty**: Trivial

**Problem**: Some CI workflows use `|| true` for bandit, masking security scan failures.

**Fix**: Remove `|| true` so bandit failures cause build failures. Use SARIF upload separately for non-blocking insights.

---

## Phase 7: Final Audit & Documentation

**Objective**: Comprehensive verification, cross-repo consistency check, and documentation.

**Estimated effort**: 1-2 sessions

### Task 7.1: Run Automated Security Scans

```bash
# Bandit across all services
for repo in juniper-cascor juniper-data juniper-canopy; do
    echo "=== $repo ==="
    bandit -r "$repo" -f json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
results = d.get('results', [])
print(f'Issues: {len(results)}')
for r in results:
    print(f'  [{r[\"issue_severity\"]}] {r[\"issue_text\"]} ({r[\"filename\"]}:{r[\"line_number\"]})')
"
done

# pip-audit in each conda environment
for env in JuniperCascor JuniperData JuniperPython; do
    echo "=== $env ==="
    conda run -n "$env" pip-audit --strict 2>&1 | tail -5
done

# Docker image scanning (if trivy installed)
for img in juniper-data juniper-cascor juniper-canopy; do
    echo "=== $img ==="
    trivy image "$img:latest" --severity HIGH,CRITICAL 2>/dev/null || echo "trivy not available"
done
```

### Task 7.2: Cross-Repo Consistency Audit

Verify identical implementations across all three services:

- [ ] `SecurityHeadersMiddleware` present and identically configured
- [ ] CORS defaults are restrictive (empty list)
- [ ] Rate limiting enabled by default
- [ ] Error handlers sanitized (no `str(exc)` in responses)
- [ ] `/metrics` removed from `EXEMPT_PATHS`
- [ ] WebSocket authentication present (cascor + canopy)
- [ ] All `publish.yml` have `attestations: true`
- [ ] Docker Compose has network isolation, port binding, security options

### Task 7.3: Run Full Test Suites

```bash
# juniper-data
cd /home/pcalnon/Development/python/Juniper/juniper-data && conda run -n JuniperData pytest juniper_data/tests/ -v

# juniper-cascor
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src/tests && conda run -n JuniperCascor bash scripts/run_tests.bash

# juniper-canopy
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src && conda run -n JuniperPython pytest tests/ -v

# juniper-deploy
cd /home/pcalnon/Development/python/Juniper/juniper-deploy && docker compose --profile full config
```

### Task 7.4: Update This Document

Mark each finding as RESOLVED with implementation date and commit reference.

### Verification Results (2026-03-03)

All test suites pass after security hardening changes:

| Repository | Tests | Result | Test Fixes Applied |
|---|---|---|---|
| juniper-data | 766 passed | PASS | Updated CORS, settings, error message assertions |
| juniper-cascor | 264 API tests passed | PASS | Updated CORS, settings, error message assertions |
| juniper-cascor-worker | 46 passed | PASS | Updated worker auth assertions |
| juniper-data-client | 88 passed | PASS | No changes needed |
| juniper-canopy | 3373 passed, 19 skipped | PASS | Disabled rate limiting in test conftest, updated error message assertion |
| juniper-deploy | Config validation | PASS | No changes needed |
| juniper-ml | N/A (meta-package) | N/A | No tests |

**Worktrees** (all on `feature/security-hardening` branches, changes uncommitted):

| Repo | Worktree Path |
|---|---|
| juniper-data | `worktrees/juniper-data--feature--security-hardening--20260303-1535--f06c00c8/` |
| juniper-cascor | `worktrees/juniper-cascor--feature--security-hardening--20260303-1535--046e6000/` |
| juniper-canopy | `worktrees/juniper-canopy--feature--security-hardening--20260303-1535--3c324970/` |
| juniper-deploy | `worktrees/juniper-deploy--feature--security-hardening--20260303-1535--a83130fa/` |
| juniper-cascor-worker | `worktrees/juniper-cascor-worker--feature--security-hardening--20260303-1551--42dce04e/` |
| juniper-data-client | `worktrees/juniper-data-client--feature--security-hardening--20260303-1553--64d8fad0/` |
| juniper-ml | `worktrees/juniper-ml--feature--security-hardening--20260303-1553--6fa971f6/` |

---

## Findings-to-Phase Mapping

| # | Finding | Severity | Phase.Task | Status |
|---|---------|----------|------------|--------|
| F-01 | WebSocket bypasses auth | CRITICAL | 3.1 | **RESOLVED** — WS auth added to cascor + canopy |
| F-02 | No security headers | HIGH | 1.1 | **RESOLVED** — SecurityHeadersMiddleware in all 3 services |
| F-03 | Error details exposed | HIGH | 1.2 | **RESOLVED** — Generic error messages in all handlers |
| F-04 | Rate limiting disabled | HIGH | 1.3 | **RESOLVED** — Enabled by default in all 3 services |
| F-05 | CORS wildcard default | HIGH | 1.4 | **RESOLVED** — Empty origins default in all 3 services |
| F-06 | Docker ports on 0.0.0.0 | HIGH | 2.2 | **RESOLVED** — 127.0.0.1 binding for internal services |
| F-07 | No Docker network isolation | HIGH | 2.1 | **RESOLVED** — frontend/backend/data networks added |
| F-08 | No TLS (inter-service) | MEDIUM | Documented | DEFERRED (requires reverse proxy/cert infra) |
| F-09 | PII in repository | MEDIUM | 5.1 | **RESOLVED** — File removed, .gitignore updated |
| F-10 | No WS message size limits | MEDIUM | 3.2 | **RESOLVED** — 64KB control, 1MB data limits |
| F-11 | No WS message validation | MEDIUM | 3.3 | **RESOLVED** — Pydantic model validation added |
| F-12 | No WS idle timeout | MEDIUM | 3.4 | **RESOLVED** — Configurable idle timeout added |
| F-13 | Loose input validation | MEDIUM | Documented | DEFERRED (low exploit risk with Pydantic validation at route level) |
| F-14 | Pickle deserialization | MEDIUM | 5.2 | **RESOLVED** — HMAC verification before pickle.loads |
| F-15 | No request body size limits | MEDIUM | 4.3 | **RESOLVED** — RequestBodyLimitMiddleware (10MB default) |
| F-16 | Worker auth hardcoded | MEDIUM | 5.3 | **RESOLVED** — Required env var, fails if not set |
| F-17 | /metrics unauthenticated | MEDIUM | 4.1 | **RESOLVED** — Removed from EXEMPT_PATHS |
| F-18 | No container hardening | MEDIUM | 2.3 | **RESOLVED** — no-new-privileges + cap_drop ALL |
| F-19 | Attestations disabled | MEDIUM | 6.1 | **RESOLVED** — attestations: true in all publish.yml |
| F-20 | API docs in production | LOW | 4.2 | **RESOLVED** — Conditional docs based on settings |
| F-21 | Unpinned Docker images | LOW | 2.4 | **RESOLVED** — SHA-pinned Prometheus + Grafana |
| F-22 | Default Grafana password | LOW | 2.5 | **RESOLVED** — Required env var with ?error syntax |
| F-23 | No scheduled dep scanning | LOW | 6.2 | **RESOLVED** — Weekly security-scan.yml workflow |
| F-24 | Bandit CI fallback | LOW | 6.3 | **RESOLVED** — Removed \|\| true from CI |

---

## Critical Files Reference

| File | Phases | Changes |
|------|--------|---------|
| `juniper-data/juniper_data/api/middleware.py` | 1, 4 | Add SecurityHeadersMiddleware, remove /metrics from EXEMPT_PATHS |
| `juniper-data/juniper_data/api/app.py` | 1, 4 | Register middleware, sanitize errors, conditional docs |
| `juniper-data/juniper_data/api/settings.py` | 1 | Rate limiting default, CORS default |
| `juniper-cascor/src/api/middleware.py` | 1, 4 | Mirror juniper-data middleware changes |
| `juniper-cascor/src/api/app.py` | 1, 4 | Mirror juniper-data app changes |
| `juniper-cascor/src/api/settings.py` | 1 | Mirror juniper-data settings changes |
| `juniper-cascor/src/api/websocket/training_stream.py` | 3 | Add WS auth |
| `juniper-cascor/src/api/websocket/control_stream.py` | 3 | Add WS auth, message validation, size limits |
| `juniper-canopy/src/middleware.py` | 1, 4 | Mirror middleware changes |
| `juniper-canopy/src/main.py` | 1, 3, 4 | Mirror app changes, WS auth |
| `juniper-canopy/src/security.py` | 1 | Rate limiting default |
| `juniper-deploy/docker-compose.yml` | 2 | Networks, ports, security_opt, image pins, Grafana pw |
| `juniper-deploy/prometheus/prometheus.yml` | 4 | Add API key to scrape config |
| `juniper-cascor/src/snapshots/snapshot_serializer.py` | 5 | HMAC verification for pickle |
| All repos `publish.yml` | 6 | Attestations |
| All repos `.github/workflows/` | 6 | Scheduled security scan |

---

## Cross-Repo Implementation Strategy

Because `security.py`, `middleware.py`, and `app.py` follow near-identical patterns across all three services, changes are implemented upstream-first:

1. **Implement in juniper-data first** (simplest service, no WebSocket concerns)
2. **Run juniper-data tests** to verify no regressions
3. **Port changes to juniper-cascor** (adds WebSocket auth complexity)
4. **Run juniper-cascor tests** to verify
5. **Port changes to juniper-canopy** (adds Dash/CSP complexity, multiple WS endpoints)
6. **Run juniper-canopy tests** to verify
7. **Update juniper-deploy** with Docker, env var, and Prometheus changes
8. **Run integration tests** via juniper-deploy

Each repo gets a `feature/security-hardening` branch in its own worktree per the [Worktree Procedures](../CLAUDE.md#worktree-procedures-mandatory--task-isolation).

---

## Existing Security Strengths

These practices are already in place and should be preserved:

| Practice | Where | Details |
|----------|-------|---------|
| API key authentication | All 3 services | `X-API-Key` header, `APIKeyAuth` class, thread-safe set validation |
| Rate limiting code | All 3 services | Fixed-window, per-key/per-IP, proper headers (429 + Retry-After) |
| Bandit SAST | CI + pre-commit | Configured with appropriate skips for ML code (B301, B403) |
| pip-audit | CI | `--strict` mode, fails on vulnerabilities |
| Gitleaks | CI | Secret detection in commits |
| SOPS hooks | Pre-commit | Blocks unencrypted `.env` files from commit |
| SHA-pinned Actions | All CI workflows | Full SHA pinning with version comments |
| OIDC trusted publishing | PyPI workflows | No API tokens stored |
| Multi-stage Docker builds | All Dockerfiles | Separate build/runtime stages |
| Non-root containers | All Dockerfiles | `groupadd`/`useradd` with UID 1000 |
| Pydantic validation | All services | Settings, request models, field constraints |
| Custom exception hierarchy | All services | Stack traces logged internally, not exposed |
| `detect-private-key` | Pre-commit | Prevents credential commits |
| Request ID tracing | All services | `RequestIdMiddleware` for audit correlation |
| Sentry integration | All services | Optional, PII disabled by default |
| Health checks | Docker + services | `/v1/health`, `/v1/health/live`, `/v1/health/ready` |
| `.env` in .gitignore | All repos | Standard .env exclusion patterns |

---

## Appendix A: Microservice Security Best Practices Applied

### OWASP API Security Top 10 (2023) Coverage

| # | Risk | Juniper Status | Action |
|---|------|---------------|--------|
| API1 | Broken Object Level Authorization | N/A (no multi-tenant) | — |
| API2 | Broken Authentication | Partial (WS bypass) | Phase 3.1 |
| API3 | Broken Object Property Level Authorization | N/A | — |
| API4 | Unrestricted Resource Consumption | Missing (rate limit off, no size limits) | Phase 1.3, 3.2, 4.3 |
| API5 | Broken Function Level Authorization | N/A (flat auth model) | — |
| API6 | Unrestricted Access to Sensitive Business Flows | Partial (/metrics exposed) | Phase 4.1 |
| API7 | Server Side Request Forgery | Low risk (controlled URLs) | — |
| API8 | Security Misconfiguration | Yes (CORS, headers, defaults) | Phase 1 |
| API9 | Improper Inventory Management | Good (versioned APIs, health endpoints) | — |
| API10 | Unsafe Consumption of APIs | Low risk (trusted internal services) | — |

### Zero Trust Principles Applied

- **Verify explicitly**: API key authentication on all endpoints including WebSocket (Phase 3)
- **Least privilege access**: Container `cap_drop: ALL` + `no-new-privileges` (Phase 2.3)
- **Assume breach**: Network segmentation via Docker networks (Phase 2.1)

### Defense in Depth Layers

1. **Network**: Docker network isolation, localhost port binding
2. **Transport**: TLS (deferred, requires reverse proxy infrastructure)
3. **Application**: Security headers, CORS, rate limiting, input validation
4. **Authentication**: API key validation on REST + WebSocket
5. **Container**: Non-root user, dropped capabilities, read-only (future)
6. **Supply Chain**: SHA-pinned actions, OIDC publishing, build attestations

---

## Appendix B: Automated Scanning Commands

### Pre-Implementation Baseline

Run before making changes to establish security baseline:

```bash
cd /home/pcalnon/Development/python/Juniper

# Bandit SAST scan across all services
for repo in juniper-cascor/src juniper-data/juniper_data juniper-canopy/src; do
    echo "=== $repo ==="
    bandit -r "$repo" -ll -q 2>/dev/null | head -20
done

# Dependency audit
for env in JuniperCascor JuniperData JuniperPython; do
    echo "=== $env ==="
    conda run -n "$env" pip-audit 2>&1
done

# Secret scanning
for repo in juniper-cascor juniper-data juniper-canopy juniper-deploy; do
    echo "=== $repo ==="
    cd "$repo" && git log --all --diff-filter=A -- "*.env" "*.key" "*.pem" "*secret*" "*password*" 2>/dev/null | head -5
    cd ..
done
```

### Post-Implementation Verification

Run after each phase to verify improvements:

```bash
# Verify security headers
for port in 8100 8200 8050; do
    echo "=== Port $port ==="
    curl -sI "http://localhost:$port/v1/health" | grep -iE "x-content-type|x-frame|referrer|permissions"
done

# Verify CORS restriction
for port in 8100 8200 8050; do
    echo "=== Port $port ==="
    curl -sI -H "Origin: http://evil.example.com" "http://localhost:$port/v1/health" | grep -i "access-control"
done

# Verify rate limiting
for port in 8100 8200 8050; do
    echo "=== Port $port ==="
    for i in $(seq 1 65); do curl -s -o /dev/null -w "%{http_code} " "http://localhost:$port/v1/health"; done
    echo ""
done

# Verify Docker port binding
ss -tlnp | grep -E "8100|8200|8050|9090|3000" | grep -v "127.0.0.1"
# Expected: Only canopy (8050) if configured for external access

# Verify Docker networks
docker network ls | grep juniper
docker inspect juniper-data --format '{{json .NetworkSettings.Networks}}' | python -m json.tool
```
