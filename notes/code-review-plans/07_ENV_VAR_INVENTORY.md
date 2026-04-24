# Ecosystem env-var inventory — observability surface

**Companion to**: `00_ECOSYSTEM_ROADMAP.md` §5.3
**Created**: 2026-04-24 (Phase D extraction)
**Status**: Reference table — verify against `main` HEAD before relying on
specific values.

---

## 1. Purpose

A single-source table of every environment variable across all six
in-scope applications that affects observability behavior — metrics,
logging, tracing, error reporting, healthchecks, rate limits, auth,
WebSocket framing, audit logging, and CSRF gating (because all of
those are part of "what the operator can see and what the operator can
shut off").

Per the original prompt's directive, this catalog is required by the
roadmap's cross-app validation gates (§6.2) and feeds the
normalization decision (§5.3).

---

## 2. Conventions

- `★` = env var **not** listed in the originating per-app plan's §2.2
  table — surfaced during Phase D extraction.
- `(alias)` = secondary env-var name supported via Pydantic `AliasChoices`.
- `(legacy)` = legacy fallback name; current code emits a deprecation
  warning when the legacy name is used.
- "Effect" is one phrase. Default and type are as written in
  `settings.py` / `constants.py`.

---

## 3. Prefix-convention summary

| App | Canonical prefix | Alias / legacy | Notes |
|-----|------------------|----------------|-------|
| juniper-data | `JUNIPER_DATA_*` | — | Clean |
| juniper-cascor | `JUNIPER_CASCOR_*` | `JUNIPER_WS_*` (alias for WS-only fields) | Two valid prefixes for the same fields |
| juniper-canopy | `JUNIPER_CANOPY_*` | `CASCOR_*` / `CANOPY_*` (legacy, validators warn) | Most legacy paths emit deprecation warning |
| juniper-cascor-worker | `CASCOR_*` (bare) | — | **Violates ecosystem convention** — needs `JUNIPER_CASCOR_*` migration |
| juniper-cascor-client | `JUNIPER_CASCOR_*` (single env var only) | — | Clean (only `_API_KEY`) |
| juniper-data-client | `JUNIPER_DATA_*` (single env var only) | — | Clean (only `_API_KEY`) |

**Decision required (roadmap §5.3)**: normalize all worker env vars
to `JUNIPER_CASCOR_*` over a deprecation cycle; pick a single prefix
for cascor WS-related fields and deprecate the alias.

---

## 4. juniper-data — 9 env vars

| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_DATA_LOG_LEVEL` | `INFO` | str | Root logger verbosity | settings.py:115 |
| `JUNIPER_DATA_LOG_FORMAT` | `text` | str | `json` switches to JSON formatter | settings.py:146 |
| `JUNIPER_DATA_SENTRY_DSN` | `None` | str? | Sentry init | settings.py:147 |
| `JUNIPER_DATA_SENTRY_SEND_PII` ★ | `False` | bool | Controls PII transmission to Sentry | settings.py:148 |
| `JUNIPER_DATA_SENTRY_TRACES_SAMPLE_RATE` | `0.1` | float | Sentry transaction sampling | settings.py:149 |
| `JUNIPER_DATA_METRICS_ENABLED` | `False` | bool | Mounts `/metrics` + `PrometheusMiddleware` | settings.py:150 |
| `JUNIPER_DATA_RATE_LIMIT_ENABLED` ★ | `True` | bool | Gates request rate limiting | settings.py:143 |
| `JUNIPER_DATA_RATE_LIMIT_REQUESTS_PER_MINUTE` ★ | `60` | int | Per-client RPM | settings.py:144 |
| `JUNIPER_DATA_API_KEYS` ★ | `None` | list[str]? | Auth credentials gating `/metrics` | settings.py:120 |

**New surface**: rate-limit + API-keys + Sentry-PII not previously
in plan 01 §2.2. Update plan 01.

---

## 5. juniper-cascor — 18 env vars

| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CASCOR_LOG_LEVEL` | `INFO` | str | Root logger verbosity | settings.py:125 |
| `JUNIPER_CASCOR_LOG_FORMAT` | `text` | str | `json` switches formatter | settings.py:188 |
| `JUNIPER_CASCOR_METRICS_ENABLED` | `false` | bool | Gates `/metrics` + middleware | settings.py:190 |
| `JUNIPER_CASCOR_SENTRY_DSN` | `None` | str? | Sentry init | settings.py:189 |
| `JUNIPER_CASCOR_WS_MAX_CONNECTIONS` | `50` | int | WS connection pool size | settings.py:128 |
| `JUNIPER_CASCOR_WS_HEARTBEAT_INTERVAL_SEC` | `30` | int | WS heartbeat cadence | settings.py:129 |
| `JUNIPER_CASCOR_WS_HEARTBEAT_PONG_TIMEOUT_SEC` | `10` | int | PONG response deadline | settings.py:130 |
| `JUNIPER_CASCOR_WS_REPLAY_BUFFER_SIZE` | `1024` | int | Replay buffer depth | settings.py:134–139 |
| `JUNIPER_WS_REPLAY_BUFFER_SIZE` (alias) | `1024` | int | Same field — alt prefix | settings.py:134–139 |
| `JUNIPER_CASCOR_WS_SEND_TIMEOUT_SECONDS` | `0.5` | float | Per-message send timeout | settings.py:140–145 |
| `JUNIPER_WS_SEND_TIMEOUT_SECONDS` (alias) | `0.5` | float | Same field — alt prefix | settings.py:140–145 |
| `JUNIPER_CASCOR_WS_RESUME_HANDSHAKE_TIMEOUT_S` | `5.0` | float | Resume window for `/ws/training` | settings.py:146–150 |
| `JUNIPER_CASCOR_WS_STATE_THROTTLE_COALESCE_MS` | `1000` | int | State broadcast coalesce window | settings.py:151–155 |
| `JUNIPER_CASCOR_WS_PENDING_MAX_DURATION_S` ★ | `10.0` | float | Max pending-state duration | settings.py:156–160 |
| `JUNIPER_CASCOR_RATE_LIMIT_ENABLED` ★ | `false` | bool | Request rate limiting | settings.py:185 |
| `JUNIPER_CASCOR_RATE_LIMIT_REQUESTS_PER_MINUTE` ★ | `60` | int | Per-client RPM | settings.py:186 |
| `JUNIPER_CASCOR_WORKER_AUDIT_LOGGING_ENABLED` ★ | `false` | bool | Worker request/response audit log | settings.py:215 |
| `JUNIPER_CASCOR_WORKER_METRICS_ENABLED` ★ | `false` | bool | Per-worker Prometheus metrics | settings.py:216 |

**New surface**: WS pending-max-duration + rate-limit pair + worker
audit/metrics gates not in plan 03 §2.2. Update plan 03 — these
materially affect what the review must cover.

---

## 6. juniper-canopy — 28 env vars (largest surface)

Grouped by category for readability.

### 6.1 Logging / error tracking
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_LOG_LEVEL` (legacy: `CASCOR_LOG_LEVEL`) | `INFO` | str | Root logger | settings.py:152 |
| `JUNIPER_CANOPY_LOG_FORMAT` (legacy: `CANOPY_LOG_FORMAT`) | `text` | str | JSON vs text | settings.py:153 |
| `JUNIPER_CANOPY_SENTRY_DSN` (legacy: `CANOPY_SENTRY_DSN`) | `None` | str? | Sentry init | settings.py:154 |
| `JUNIPER_CANOPY_SENTRY_TRACES_SAMPLE_RATE` | `0.1` | float | Sentry sampling | settings.py:155 |

### 6.2 Metrics
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_METRICS_ENABLED` | `False` | bool | Mounts `/metrics` + middleware | settings.py:158 |
| `JUNIPER_CANOPY_METRICS_SMOOTHING_WINDOW` ★ | `10` | int | Exponential-smoothing window | settings.py:168 |

### 6.3 Rate limiting
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_RATE_LIMIT_ENABLED` | `False` | bool | Per-min limit on REST endpoints | settings.py:164 |
| `JUNIPER_CANOPY_RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | int | Threshold | settings.py:165 |

### 6.4 Audit log (M-SEC-07)
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_AUDIT_LOG_ENABLED` ★ | `True` | bool | Audit log writes | settings.py:171 |
| `JUNIPER_CANOPY_AUDIT_LOG_PATH` ★ | `/var/log/canopy/audit.log` | str | File path | settings.py:172 |
| `JUNIPER_CANOPY_AUDIT_LOG_RETENTION_DAYS` ★ | `90` | int | Retention | settings.py:173 |

### 6.5 WebSocket framing (`websocket.*` nested settings)
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_WEBSOCKET__MAX_CONNECTIONS` ★ | `50` | int | Concurrent conn cap | settings.py:87 |
| `JUNIPER_CANOPY_WEBSOCKET__MAX_CONNECTIONS_PER_IP` ★ | `5` | int | Per-IP cap (M-SEC-01b) | settings.py:99 |
| `JUNIPER_CANOPY_WEBSOCKET__HEARTBEAT_INTERVAL` ★ | `30` | int | Ping cadence (sec) | settings.py:88 |
| `JUNIPER_CANOPY_WEBSOCKET__IDLE_TIMEOUT_SECONDS` ★ | `120` | int | Idle close (M-SEC-03) | settings.py:100 |
| `JUNIPER_CANOPY_WEBSOCKET__MAX_MESSAGE_SIZE_TRAINING` ★ | `4096` | int | `/ws/train` cap (bytes) | settings.py:101 |
| `JUNIPER_CANOPY_WEBSOCKET__MAX_MESSAGE_SIZE_CONTROL` ★ | `65536` | int | `/ws/control` cap (bytes) | settings.py:102 |

### 6.6 WebSocket control (`/ws/control`)
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_WS_SET_PARAMS_TIMEOUT` ★ | `1.0` | float | Per-request timeout (C-03) | settings.py:183 |
| `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS` | `True` | bool | D-49 flag-flip | settings.py:186 |
| `JUNIPER_CANOPY_WS_CONTROL_START_TIMEOUT` ★ | `10.0` | float | start-cmd timeout | settings.py:187 |
| `JUNIPER_CANOPY_WS_CONTROL_STOP_TIMEOUT` ★ | `2.0` | float | stop/pause/resume/reset timeout | settings.py:188 |
| `JUNIPER_CANOPY_WS_CONTROL_SET_PARAMS_TIMEOUT` ★ | `1.0` | float | set_params via `/ws/control` | settings.py:189 |
| `JUNIPER_CANOPY_ENABLE_BROWSER_WS_BRIDGE` ★ | `True` | bool | D-17 flag-flip | settings.py:176 |
| `JUNIPER_CANOPY_DISABLE_WS_BRIDGE` ★ | `False` | bool | D-18 kill switch | settings.py:177 |

### 6.7 CSRF (M-SEC-02)
| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CANOPY_CSRF_ENABLED` ★ | `True` | bool | CSRF token validation on `/ws/control` | settings.py:192 |
| `JUNIPER_CANOPY_CSRF_TOKEN_TTL_SECONDS` ★ | `3600` | int | Token sliding TTL | settings.py:193 |
| `JUNIPER_CANOPY_WS_CONTROL_AUTH_TIMEOUT` ★ | `5.0` | float | Wait for CSRF first frame | settings.py:195 |

**Material finding**: The original survey + plan 06 §2.2 captured 5
env vars; extraction found **28**. The security-related set
(CSRF, audit log, per-IP caps, message-size limits) is entirely
missing from the plan and must be folded in. **Plan 06 must be
expanded.** Recommend creating a security-focused subsection in
plan 06 §2 to absorb the new set.

---

## 7. juniper-cascor-worker — 13 env vars (all bare `CASCOR_*`)

| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `CASCOR_SERVER_URL` | (required) | str | Orchestrator WS URL | constants.py:126 |
| `CASCOR_AUTH_TOKEN` | `""` | str | `X-API-Key` header | constants.py:127 |
| `CASCOR_API_KEY` | `""` | str | Deprecated alias for `_AUTH_TOKEN` | constants.py:128 |
| `CASCOR_HEARTBEAT_INTERVAL` | `10.0` | float | Heartbeat cadence | constants.py:129 |
| `CASCOR_TASK_TIMEOUT` | `3600.0` | float | Max task duration | constants.py:130 |
| `CASCOR_TLS_CERT` | `None` | str? | mTLS client cert path | constants.py:131 |
| `CASCOR_TLS_KEY` | `None` | str? | mTLS client key | constants.py:132 |
| `CASCOR_TLS_CA` | `None` | str? | mTLS CA bundle | constants.py:133 |
| `CASCOR_MANAGER_HOST` ★ | `127.0.0.1` | str | Legacy manager host | constants.py:134 |
| `CASCOR_MANAGER_PORT` ★ | `50000` | int | Legacy manager port | constants.py:135 |
| `CASCOR_AUTHKEY` ★ | `""` | str | Legacy manager auth key | constants.py:136 |
| `CASCOR_NUM_WORKERS` ★ | `1` | int | Legacy worker pool size | constants.py:137 |
| `CASCOR_MP_CONTEXT` ★ | `forkserver` | str | mp start method | constants.py:138 |

**Cross-cutting**: every entry violates the `JUNIPER_*` ecosystem
convention. Plan 04 H9 captures the headline; the extraction shows the
full breadth. Migration plan must support both prefixes through one
deprecation cycle.

---

## 8. juniper-data-client — 1 env var

| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_DATA_API_KEY` | `None` | str? | `X-API-Key` header | constants.py:47 |

All other configuration is constructor-arg only. **Notable absence**:
no env-var override for `base_url`, timeout, retries, pool — every
caller wires the constructor. Plan 02 H7 captures this.

---

## 9. juniper-cascor-client — 1 env var

| Env var | Default | Type | Effect | File:line |
|---------|---------|------|--------|-----------|
| `JUNIPER_CASCOR_API_KEY` | `None` | str? | `X-API-Key` header | constants.py:43 |

All other config is constructor-arg. Same caveat as data-client.

---

## 10. Cross-cutting observations

1. **Prefix sprawl**: 4 distinct conventions in active use
   (`JUNIPER_*`, `JUNIPER_WS_*` alias, `CASCOR_*` legacy, bare
   `CASCOR_*` in worker). One ecosystem decision, one migration plan.
2. **Default-disabled metrics**: All three FastAPI services have
   `*_METRICS_ENABLED=false`. Reaffirms roadmap §5.4 question.
3. **Rate-limit defaults differ**: `juniper-data` defaults `True`;
   `juniper-cascor` and `juniper-canopy` default `False`. Pick a
   posture; document.
4. **Surprise: canopy security surface**: 11 of canopy's 28 env vars
   govern security/CSRF/audit/per-IP — **none** appeared in the
   original survey. Plan 06 must absorb these; the metrics-and-
   monitoring scope spills into security boundary by design.
5. **Worker has no observability env vars at all** beyond auth /
   transport. No log-format toggle, no metrics gate, no
   sample-rate. Suggests the worker review must propose adding
   `CASCOR_LOG_FORMAT` and (if Prometheus is added) a
   `CASCOR_METRICS_ENABLED` gate aligned with the rest of the
   ecosystem.

---

## 11. Recommended next actions

| # | Action | Plan to update |
|---|--------|----------------|
| 1 | Add 3 new env vars to plan 01 §2.2 | 01_juniper-data |
| 2 | Add 6 new env vars to plan 03 §2.2 | 03_juniper-cascor |
| 3 | Add 23 new env vars + dedicated security subsection to plan 06 | 06_juniper-canopy |
| 4 | Add 5 legacy env vars to plan 04 §2.2 | 04_juniper-cascor-worker |
| 5 | Decide ecosystem prefix normalization plan | 00_ECOSYSTEM_ROADMAP §5.3 |
| 6 | Decide metrics-default-flip policy | 00_ECOSYSTEM_ROADMAP §5.4 |
| 7 | Decide rate-limit-default policy | 00_ECOSYSTEM_ROADMAP §5.4 (extend) |
