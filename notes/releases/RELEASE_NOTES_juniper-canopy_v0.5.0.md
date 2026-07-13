# juniper-canopy v0.5.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.5.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> The GitHub Release [`v0.5.0`](https://github.com/pcalnon/juniper-canopy/releases/tag/v0.5.0) exists.
>
> **Template note:** this file uses the standard release-notes template even though the CHANGELOG carries a
> `Security` section. Those items (SEC-05/06/12/13/14/15) are canopy's own first-party hardening landed within
> a feature MINOR release — not a transitive-dependency CVE patch — so the CVE-advisory-shaped
> `TEMPLATE_SECURITY_RELEASE_NOTES.md` (vulnerable-package / CWE / advisory-URL / fixed-version fields) does
> not apply and would require inventing advisory content. The security work is preserved faithfully in the
> **Security** section below.

---

# juniper-canopy v0.5.0 Release Notes

**Release Date:** 2026-05-23
**Version:** 0.5.0
**Release Type:** MINOR (large roll-up)
**Repository:** pcalnon/juniper-canopy
**Git tag:** `v0.5.0`
**PyPI:** <https://pypi.org/project/juniper-canopy/0.5.0/>

---

## Overview

A large roll-up release for the real-time monitoring dashboard. It adopts the shared observability and
wire-protocol packages, ships Phase D WebSocket training-control buttons (flag-flipped on by default), adds
the Candidate Metrics tab and contextual left menu, hardens the WebSocket / remote-connect / error surfaces
(SEC-05/06/12/13/14/15), and lands a Track-3 concurrency-safety sweep.

> **Version-history note (from the CHANGELOG):** `pyproject.toml` was bumped 0.3.0 → 0.4.0 on 2026-03-03 in
> preparation for a 0.4.0 release that was never cut to PyPI. This 0.5.0 release rolls up both that work and
> the subsequent ~2.5 months of changes (**983 commits since `v0.3.0`**) into a single PyPI release.

---

## Added

- **METRICS-MON R2.2.5** — `CascorServiceAdapter._relay_loop` now validates every inbound `/ws/training`
  frame against the canonical Pydantic envelope schemas in `juniper-cascor-protocol>=0.1.0` (added as an
  explicit runtime dependency). Validation is purely **observational** (never raises, never mutates the
  message dict). New Prometheus counter `juniper_canopy_unrecognized_ws_frames_total{type, endpoint}` and
  helper `inc_unrecognized_ws_frame(...)`, with the R1.1 cardinality discipline (first 16 distinct unknown
  types tracked verbatim, then collapsed to `"_unmatched"`). New chaos-coverage suite
  `src/tests/unit/test_inbound_frame_validation.py`.
- **Phase D WebSocket training controls (§S10).** Flag-gated **clientside** training-button routing
  (`PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS`) routing Start/Pause/Stop/Resume/Reset through
  `window.cascorControlWS.send({command, command_id})` with automatic `fetch('/api/train/<command>')` REST
  fallback; a canonical `command_response` envelope on `/ws/control`; per-command timeouts (`asyncio.wait_for`
  with a `_PHASE_D_CONTROL_TIMEOUTS` budget dict); `unknown_command` envelope code; `set_params` as a
  first-class `/ws/control` command; the `enable_ws_control_buttons` flag (+ timeout budgets); and
  `command_id`-correlated browser sends. New tests `test_phase_d_control_buttons.py` (15) and
  `test_phase_d_button_clientside.py` (11).
- **UI** — a new top-level **Candidate Metrics** tab (`CandidateMetricsPanel`, component count 11 → 12), a
  **Contextual Left Menu** whose sidebar sections show/hide per active tab (`TAB_SIDEBAR_CONFIG`), collapsible
  contextual section wrappers, and 15 addressable sidebar wrapper div IDs.
- **Hardcoded-values refactor (Wave 1 + Wave 2)** — new `SecurityConstants` and `BackendConstants` classes in
  `src/canopy_constants.py`; extended `DashboardConstants` / `ServerConstants`.
- **CI / docs** — `util/test_agents_md_version_drift.py` port wired into the CI tests job; the macOS unit-test
  matrix leg (METRICS-MON R3.7) added and, after a clean soak, flipped to **required**; Network Editor
  service-mode documentation and documentation-link validation workflow docs.

## Changed (potentially breaking)

- **METRICS-MON R2.1.5** — canopy's observability surface now consumes the shared
  `juniper-observability>=0.1.1` package (added as a runtime dependency); `JuniperJsonFormatter`,
  `RequestIdMiddleware`, `PrometheusMiddleware`, `configure_logging`, `get_prometheus_app`, `set_build_info`,
  etc. move into the shared lib with `observability.py` / `health.py` kept as thin re-export shims.
  **Wire-format change:** `/v1/health/ready` `timestamp` now derives from `datetime.now(UTC).timestamp()`
  (was naive local time) — values stay unix-epoch-seconds. **Security improvement:** `configure_sentry` gains
  the SEC-15 `before_send` hook that scrubs `X-API-Key` / `Authorization` / `Cookie` from outbound Sentry
  events. `JuniperJsonFormatter()` default `service` is now `"juniper-service"` (all in-tree call sites pass
  the name explicitly).

## Changed

- **CFG-16** — `create_backend()` no longer re-reads `CASCOR_DEMO_MODE` / `CASCOR_SERVICE_URL` via raw
  `os.getenv` as a "legacy fallback"; both are handled by the Settings field validators (which emit
  `DeprecationWarning`). New regression `test_cfg_16_create_backend_no_raw_env.py`.
- **Phase D §S10.3 (D-49) flag-flip** — `enable_ws_control_buttons` default `False` → `True` after a
  production soak; the `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` kill switch reverts to pure REST.
- Namespaced Prometheus metrics under the `juniper_canopy_` prefix (`..._http_requests_total`,
  `..._websocket_connections_active`, `..._demo_mode_active`, `..._build_info`, etc.); ~55 inline literals
  replaced by `canopy_constants` imports (Wave 2); candidate pool display extracted to `CandidateMetricsPanel`;
  extensive backend / API / CI / testing documentation refreshes.

## Security

- **SEC-05 / SEC-12** — the `/ws` generic WebSocket endpoint now enforces the same `validate_origin` and
  `check_per_ip_limit` gates as `/ws/training` and `/ws/control`. Requests from unlisted origins or IPs over
  the per-IP cap are closed with standardized codes (4003 / 1013); origin rejections are audit-logged.
- **SEC-06** — opt-in bearer-token auth for all WebSocket endpoints, gated by
  `JUNIPER_CANOPY_WS_AUTH_ENABLED` (default `False`). When enabled, clients negotiate
  `Sec-WebSocket-Protocol: bearer, <token>` and the token is validated against `api_keys` with constant-time
  comparison.
- **SEC-13** — `POST /api/remote/connect` no longer accepts `authkey` as a query parameter. It now requires a
  JSON body modeled by `RemoteConnectRequest` with `SecretStr`, so the key is never written to URLs, access
  logs, browser history, or Referer headers. Callers still sending the query param receive 422.
- **SEC-14** — replaced the five `JSONResponse({"error": str(e)}, 500)` sites in `main.py` with opaque
  `{"error": "Internal server error", "error_id": <12-hex>}` responses; the full traceback is logged
  server-side under the same `error_id` so operators can correlate without leaking internals to clients.
- **SEC-15** (via R2.1.5) — the shared `configure_sentry` `before_send` hook scrubs `X-API-Key` /
  `Authorization` / `Cookie` from outbound Sentry events (canopy's previous local implementation lacked it).

## Fixed

- **Track-3 concurrency safety** — `DemoMode._perform_reset` now applies its three transitions atomically
  under a single lock (**BUG-CN-01**); a new `WebSocketManager._connections_lock` plus a `DemoMode.running`
  property close three companion races (`Set changed size during iteration`, non-atomic `message_count += 1`,
  and inconsistent `is_running` access) (**BUG-CN-09 / BUG-CN-10 / CONC-08**); `check_per_ip_limit` /
  `_decrement_ip_count` hold a new `_ip_lock` across the read-modify-write (**CONC-01**); and
  `regenerate_dataset` applies all reset state changes atomically (**CONC-07 / BUG-CN-11**). Each fix ships a
  dedicated regression suite.
- **DOCKER-001** — removed `README.md` from `.dockerignore` so the Dockerfile `COPY … README.md` step
  succeeds.
- **DOCKER-REGRESSION** — removed the forced `JUNIPER_CANOPY_DEMO_MODE=1` from `Dockerfile` / `conf/Dockerfile`
  so a deployment is not silently routed to the synthetic `DemoBackend`.

---

## Links

- Package CHANGELOG (`[0.5.0]` section): <https://github.com/pcalnon/juniper-canopy/blob/main/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-canopy/0.5.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-canopy/releases/tag/v0.5.0>
