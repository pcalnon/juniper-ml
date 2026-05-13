# Requirements — SEC

**Area**: security — authn, authz, secrets, CVEs, hardening

**Total entries**: 54

**By status**: proposed=46 | shipped=7 | deferred=1

**By priority**: P0=13 | P1=32 | P2=8 | P3=1

**By owner**: ml=32 | can=8 | dep=5 | dat=3 | cwk=3 | ccl=2 | dcl=1

---

### JR-DAT-SEC-001 — API security includes APIKeyAuth authentication and RateLimiter middleware as default behaviors.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-017 complete. security.py confirmed.

### JR-DCL-SEC-001 — Enable PyPI build attestations and add scheduled security scanning (Bandit + pip-audit).

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 1-33)

**Detail**:

Supply chain security improvements: enabled build attestations in publish workflow, added
.github/workflows/security-scan.yml for weekly Bandit and pip-audit scanning. Version bump: 0.3.1 → 0.3.2.
All tests passing (88 unit tests, 0 failures).

**Notes**:

Status inferred from PR marked READY_FOR_MERGE with test results. SemVer impact: PATCH (0.3.1 → 0.3.2).
No breaking changes. Medium security/privacy impact (supply chain verification via attestations).

### JR-CWK-SEC-001 — v0.2.0 breaking change: remove hardcoded default auth key ("juniper"), make WORKER_AUTH_KEY environment variable required at worker startup with clear error message if not set.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 27-50)

**Detail**:

Breaking change for 0.1.0→0.2.0 (SemVer minor allowed pre-1.0). Rationale: hardcoded default allowed any network-accessible actor to register workers. Removed the 'juniper' default. WORKER_AUTH_KEY now REQUIRED with validation at startup (clear error if not set). Migration: set WORKER_AUTH_KEY environment variable explicitly before worker startup. For production: source from secret store (Docker secrets, K8s secrets, Vault, SOPS-encrypted env file) rather than plaintext export.

**Notes**:

Related: v0.3.0 renamed WORKER_AUTH_KEY to CASCOR_AUTH_TOKEN and the CLI flag from --api-key to --auth-token. Operators upgrading directly from v0.1.x to v0.3.0 should consult v0.3.0 release notes for mapping.

### JR-ML-SEC-001 — All WebSocket endpoints must enforce per-frame size limits: training 4 KB inbound, control 64 KB.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 145-180)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 681-703)

**Detail**:

Cascor training_stream.py: max_size=4096 on receive.
Cascor control_stream.py: maintain 64 KB cap (regression test).
Canopy /ws/training and /ws/control: audit every receive_*() call; add max_size parameter per control table.

**Notes**:

M-SEC-03 (P0). Must precede Phase B per R1-03. Phase B-pre-a (Day 5 of runbook).

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-ML-SEC-002 — Canopy and Cascor must validate WebSocket Origin header against configurable allowlist; reject null origins and wildcards.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 100-145)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 489-550)

**Detail**:

Cascor: new src/api/websocket/origin.py with validate_origin(ws, allowlist) → bool.
Rules: case-insensitive scheme+host, exact port, strip trailing slash, reject null origin, no wildcard support.
Canopy: mirror implementation in src/backend/ws_security.py (do not cross-import).
Cascor default: [http://localhost:8201, https://localhost:8201, http://127.0.0.1:8201, https://127.0.0.1:8201]
Canopy default: [http://localhost:8050, https://localhost:8050, http://127.0.0.1:8050, https://127.0.0.1:8050]

**Notes**:

M-SEC-01 (canopy), M-SEC-01b (cascor). RISK-15 CSWSH mitigation. Env var JUNIPER_WS_ALLOWED_ORIGINS. Phase B-pre (Day 4).

### JR-ML-SEC-003 — Canopy must implement cookie-session + CSRF first-frame validation before accepting WebSocket connections.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 145-230)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 604-705)

**Detail**:

Canopy src/main.py: add SessionMiddleware with secret_key from env JUNIPER_CANOPY_SESSION_SECRET.
New /api/csrf endpoint returns {"csrf_token": ...}, mints on first request, rotates hourly.
/ws/training and /ws/control: after accept, receive_json(timeout=5.0) for first frame.
First frame must be type="auth" with csrf_token matching session token (hmac.compare_digest).
On failure: close code 4001 "Authentication failed".
Frontend: inject window.__canopy_csrf in layout, send auth frame immediately in websocket_client.js onopen.

**Notes**:

M-SEC-02 (P0). CSWSH second-line defense. Env var JUNIPER_CANOPY_SESSION_SECRET. Phase B-pre (Day 5).

### JR-ML-SEC-004 — CSWSH (Cross-Site WebSocket Hijacking) attack must be closed by Origin allowlist + CSRF first-frame.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 450-520)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 489-550)

**Detail**:

First line: M-SEC-01 (Origin allowlist) lands Day 4.
Second line: M-SEC-02 (CSRF first-frame) lands Day 5.
Combined mitigation closes RISK-15 per R0-02 §10.1.
M-SEC-01 alone blocks third-party page from initiating; M-SEC-02 blocks cross-site session hijacking.
Origin validation must happen pre-accept (fail-closed).

**Notes**:

RISK-15 (High). Mandatory close per R1-03 as page-on-call alert, not ticket. Phase B-pre (Days 4-5).

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-CAN-SEC-004 — Phase 0 Addendum—Add threading.Lock to TrainingStateMachine.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 258-260)

**Detail**:

HIGH-015: Thread-safe locking required in backend training state machine.
File: src/backend/training_state_machine.py

### JR-CAN-SEC-005 — Phase 0 Pre-Release Security Blockers (6 vulnerabilities).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 30-61)

**Detail**:

0.1.1: Fix path traversal in snapshot endpoints via regex + resolve() check.
0.1.2: Fix timing attack in API key validation via hmac.compare_digest().
0.1.3: Suppress internal exception details; log server-side, return generic message.
0.1.4: Fix rate limiter memory leak with periodic eviction + size cap (10k entries).
0.2.1: Fix thread-unsafe CallbackContextAdapter via contextvars.ContextVar.
0.2.2: Fix threading.Event replacement race with clear() instead of reassign.

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-CCL-SEC-001 — Implement SOPS configuration (.sops.yaml) and .env.example for secrets management.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-DAT-SEC-002 — Security hardening includes SecurityHeadersMiddleware, RequestBodyLimitMiddleware, CORS, rate limiting, metrics auth, API docs hiding.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 80-85)

**Notes**:

v0.5.0 released as security hardening. Requires explicit CORS_ORIGINS env var for existing deployments.

### JR-CWK-SEC-002 — v0.2.0 security infrastructure: add .github/workflows/security-scan.yml for weekly scheduled Bandit and pip-audit scanning, Dependabot configuration, SOPS config, and SHA-pinned GitHub Actions.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 51-77)

**Detail**:

Added .github/workflows/security-scan.yml for weekly Bandit (static security) and pip-audit (dependency CVE scanning). Added SOPS configuration (.sops.yaml) and .env.example for secrets management. Updated .gitignore to cover all .env variants. SHA-pinned all GitHub Actions to immutable commit hashes. Added cross-repo CI dispatch to juniper-cascor on push to main. Added Dependabot configuration for weekly automated dependency updates. Added CODEOWNERS file for PR review routing.

### JR-CWK-SEC-003 — v0.3.0 CVE fix: bump setuptools minimum version to >=82.0 in pyproject.toml build-system requirements to remediate source distribution CVE.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 95-109)

**Detail**:

setuptools CVE affecting source distribution handling; bumped to >=82.0. Bandit pre-commit hook tuned to avoid false positives on known-safe test fixtures (B105: hardcoded_password_string suppressed for test auth_token fields). pip-audit dependency scanning runs in CI; torch +cpu local version handling fixed to enable reliable scanning of worker dependency tree.

### JR-DEP-SEC-001 — Add reverse proxy (Traefik or Caddy) with TLS termination to production profile.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 135-152)

**Detail**:

Phase 2. Proxy service in production profile terminates TLS; services communicate
over plaintext on internal networks. Support both self-signed certificates (dev)
and Let's Encrypt (production). Expose only ports 443 (HTTPS) and optionally 80
(redirect) on host.

### JR-ML-SEC-005 — Add security hardening to check_doc_links.py including universal bounds checking, input validation, and traversal depth limits.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 813-920)

**Detail**:

Existing vulnerability: filesystem existence oracle via crafted links like ../../../../etc/passwd.

Required fixes:
1. Universal bounds check - constrain resolved paths to repo/ecosystem root using Path.is_relative_to()
2. Input validation - reject null bytes and absolute paths before path construction
3. Traversal depth limit - reject links with >5 ../ segments
4. Structural validation in skip mode - ensure cross-repo links don't escape target repo

### JR-ML-SEC-006 — Canopy WebSocket handlers must enforce 120s idle timeout; close with code 1000 on expiry.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 320-360)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 813-821)

**Detail**:

Wrap receive_text() main loop in asyncio.wait_for(..., timeout=120) on both /ws/training and /ws/control.
On asyncio.TimeoutError, close with 1000 "Normal Closure".
Heartbeat from Phase F will reset timer (safe because it ships later but idle timeout defensible alone).
IMPL-SEC-30 checkpoint.

**Notes**:

IMPL-SEC-30. Idle timeout does not force disconnect during long polling; only closes on true inactivity. Phase B-pre (Day 6).

### JR-ML-SEC-007 — Cascor /ws/control must enforce per-connection command rate limit (leaky bucket, 10/sec).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 210-250)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 786-810)

**Detail**:

New src/api/websocket/rate_limit.py: per-connection leaky bucket, capacity 10, refill 10/sec.
control_stream_handler consumes 1 token per command frame.
On empty bucket: reply {"type": "command_response", "data": {"status": "rate_limited", "retry_after": 0.3}}.
Do NOT close on rate limit; allow client to retry.
One-resume-per-connection micro-control: in training_stream resume handler, record connection-scoped resumed_once.
Second resume frame closes with 1003.

**Notes**:

M-SEC-05 (P1), IMPL-SEC-29. Phase B-pre (Day 6).

### JR-ML-SEC-008 — Cascor must enforce per-IP WebSocket connection limit (default 5) to mitigate connection exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 180-210)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 774-798)

**Detail**:

WebSocketManager.__init__: self._per_ip_counts: Dict[str, int] = {}, reuse self._lock.
In connect(): before accept(), under async with self._lock: increment and check against ws_max_connections_per_ip.
Increment must happen before accept() (fail-closed).
In disconnect(): decrement in finally block to handle exceptions.
Default 5; configurable via JUNIPER_WS_MAX_CONNECTIONS_PER_IP.
Rejection: code 1013 (Try Again Later).

**Notes**:

M-SEC-04 (P1), IMPL-SEC-05..09. RISK-07 mitigation. Phase B-pre (Day 6).

### JR-DEP-SEC-002 — Complete SOPS secrets management with .env.secrets example and make targets.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 143-152)

**Detail**:

Phase 2. Create .env.secrets.example documenting all secret variables (API keys,
Grafana admin password, Sentry DSNs). Add make secrets-encrypt / make secrets-decrypt
targets wrapping sops commands. Document workflow in docs/SECRETS_GUIDE.md. Ensure CI
does not require decrypted secrets (use ${VAR:-} defaults).

### JR-CAN-SEC-007 — CORS must be restricted to used methods and headers only.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 79-79)

**Detail**:

Issue 1.1.7: Currently allows all methods and headers. Restrict to
actual API usage (GET, POST, OPTIONS; only necessary headers). File: src/main.py

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

### JR-ML-SEC-009 — Phase B-pre-a: Origin allowlist, per-IP cap, frame-size cap, audit logger skeleton on `/ws/training`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 334-430)

**Detail**:

Cascor side: Origin validation (M-SEC-01), empty list = fail-closed, case-insensitive host, null origin rejected.
Per-IP connection cap = 5 default, configurable. `_per_ip_counts` dict under lock.
Frame size limit: `max_size=4096` on receive_* calls. Canopy side: duplicate Origin helper (copy, not import).
`Settings.allowed_origins` with localhost/127.0.0.1 defaults. `max_size=4096` on canopy's `/ws/training`.
Audit logger skeleton: `canopy.audit` logger (new module), JSON formatter, TimedRotatingFileHandler daily rotation,
30-day retention, scrub allowlist (no raw payloads). No Prometheus counters yet (land in Phase B).
"One resume per connection" rule: `resume_consumed: bool` per connection, second resume closes 1003.
GAP-WS-19 regression test: `test_close_all_holds_lock`.
Tests: frame size limit 1009, per-IP 6th rejected 1013, origin allowlist matrix, audit log format + rotation, empty allowlist rejects all, second resume closes 1003.
Observability: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` (hashed),
`canopy_ws_oversized_frame_rejected_total{endpoint}`, `canopy_ws_per_ip_cap_rejected_total{endpoint}`,
`canopy_audit_events_total{event_type}`.

**Design**:

Two-PR sequence, cascor→canopy. M-SEC-03 (frame size) + M-SEC-04 (per-IP cap) + M-SEC-07 (audit skeleton).
Origin allowlist on `/ws/training` specifically (read-path). Gates Phase B only.

**Notes**:

Parallel with Phase 0-cascor and A-SDK. Exit gate: empty allowlist = fail-closed (HALT if fail-open).
Rollback: env flags (`JUNIPER_WS_ALLOWED_ORIGINS='*'` ignored by parser; instead use high cap `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=1000`).

### JR-ML-SEC-010 — Phase B-pre-a: Origin on /ws/training, size caps, per-IP cap, idle timeout, audit-logger skeleton.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-93)

**Notes**:

Phase B-pre-a major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-011 — Phase B-pre-b: Origin on /ws/control, cookie session + CSRF first-frame, rate limit, idle timeout, adapter HMAC, audit Prom counters.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-95)

**Notes**:

Phase B-pre-b major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-012 — Phase B-pre-b: Origin on `/ws/control`, cookie+CSRF first-frame, rate limit, idle timeout, adapter HMAC, log injection escaping.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 597-699)

**Detail**:

Cookie session + CSRF (canopy): SessionMiddleware added (or reused if present).
`/api/csrf` endpoint returns CSRF token bound to session (constant-time comparable via `hmac.compare_digest`).
Dash template injects CSRF token via data attribute. `/ws/control` first frame must be `{type: "auth", csrf_token: "..."}` within 5 s;
invalid/absent/expired → close 1008. Cookie: `SameSite=Lax`, `HttpOnly`, `Secure` (prod).
M-SEC-06 opaque close: numeric codes only, no human-readable reasons.
Origin + rate limit (cascor): `/ws/control` validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`).
M-SEC-05 single-bucket rate limit: 10 cmd/s leaky bucket per-connection, 11th → close 1013.
M-SEC-10 idle timeout: >120 s idle → close 1008. Settings: `ws_idle_timeout_seconds = 120`.
Adapter auth: canopy computes `csrf_token = hmac(api_key.encode(), b"adapter-ws", sha256).hexdigest()` on connect.
First frame sent: `{type: "auth", csrf_token: <hmac>}`. Cascor derives same + compares with `hmac.compare_digest`.
Uniform code path (no `X-Juniper-Role` header special case).
M-SEC-11 adapter inbound validation: `cascor_service_adapter.py` wraps inbound with Pydantic `CascorServerFrame` (`extra="allow"`).
Malformed → log + increment `canopy_adapter_inbound_invalid_total` + continue.
M-SEC-07 extended log injection: audit logger escapes CRLF + tab in all logged strings (prevents log forgery).
Tests: CSRF required, binds to session constant-time, kill-switch works, Origin rejected, rate limit 11th cmd closes 1013,
idle timeout closes 1008, adapter sends HMAC on connect, inbound malformed logged+counted, CRLF injection escaped,
opaque close codes, session middleware exists, cascor rejects unknown params via extra="forbid".
Observability: `canopy_csrf_validation_failures_total`, `canopy_audit_events_total{event_type="csrf_failure"}`,
`cascor_ws_control_rate_limit_rejected_total`, `cascor_ws_control_idle_timeout_total`, `canopy_adapter_inbound_invalid_total`.

**Design**:

Two-PR sequence (cascor→canopy). M-SEC-01/01b (Origin) + M-SEC-02 (cookie+CSRF) + M-SEC-05 (rate limit) + M-SEC-10 (idle timeout) +
M-SEC-11 (adapter validation) + M-SEC-07 extended (log escaping). Gates Phase D (browser control buttons).
HMAC first-frame auth uniform with existing SDK auth pattern.

**Notes**:

Parallel with Phase B. Entry: Phase B in main. Merge order strict: P8→P9 (P8 must land first, P9's adapter path depends on P8's handler).
Exit: all tests green, manual Origin/CSRF/rate-limit probes work, SessionMiddleware detected, adapter handshake works, 48h soak.
Rollback: `JUNIPER_DISABLE_WS_AUTH=true` (existing flag, 2 min TTF). Dedup candidate with R3-03.

### JR-ML-SEC-013 — SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 169-184)

### JR-ML-SEC-014 — SEC-02: Rate Limiter Memory Unbounded — DoS Vector.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 187-209)

### JR-ML-SEC-015 — SEC-03: No Per-IP WebSocket Connection Limiting (cascor).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 212-226)

### JR-ML-SEC-016 — SEC-04: Sync Dataset Generation Blocks Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 229-244)

### JR-ML-SEC-017 — SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 247-261)

### JR-ML-SEC-018 — SEC-06: No Auth on Canopy WS Endpoints.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 264-278)

### JR-ML-SEC-019 — SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 281-295)

### JR-ML-SEC-020 — SEC-10: Sentry `send_default_pii=True` (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 298-312)

### JR-ML-SEC-021 — SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 315-337)

### JR-ML-SEC-022 — SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 340-354)

### JR-ML-SEC-023 — SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 357-379)

### JR-ML-SEC-024 — SEC-14: Internal Exception Messages Leaked to Clients.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 382-396)

### JR-ML-SEC-025 — SEC-15: Cascor Sentry `send_default_pii=True`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 399-413)

### JR-ML-SEC-026 — SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 416-430)

### JR-ML-SEC-027 — SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 433-447)

### JR-ML-SEC-028 — SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 450-464)

### JR-ML-SEC-029 — Per-command HMAC deferred indefinitely.

**Status**: deferred  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 70-70)

**Notes**:

Settled position C-33 from R3-03 table; cross-round consensus consolidation

### JR-DEP-SEC-004 — Add container image security scanning (Trivy or Grype) to CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 197-203)

**Detail**:

Phase 4. Add security-scan job to CI using Trivy or Grype. Scan all locally-built
images after build step. Fail on critical/high CVEs; warn on medium. Cache
vulnerability database to reduce CI time.

### JR-CCL-SEC-002 — Add Security section to AGENTS.md documenting SOPS encryption, Gitleaks, Bandit, pip-audit.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 75-76)

**Notes**:

Medium severity: documents security tooling

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

### JR-DAT-SEC-003 — GitHub Actions versions must be pinned to SHA, not floating refs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 62-63)

**Notes**:

SEC-004 MEDIUM (P2). ci.yml:70,73,84, etc.

### JR-ML-SEC-030 — JUNIPER_WS_ALLOWED_ORIGINS=* explicitly REFUSED by the parser.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 67-67)

**Notes**:

Settled position C-30 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-031 — Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 63-63)

**Notes**:

Settled position C-26 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-032 — ws_security_enabled=True (positive sense), NOT disable_ws_auth.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 64-64)

**Notes**:

Settled position C-27 from R3-03 table; cross-round consensus consolidation

### JR-CAN-SEC-008 — Exception handling in callback_context must narrow exception types.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 244-244)

**Detail**:

Issue 5.3.3: Bare except: clause catches SystemExit/KeyboardInterrupt.
Narrow to (ValueError, AttributeError, ...); let system signals propagate.

