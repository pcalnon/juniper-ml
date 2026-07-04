# juniper-cascor v0.5.0 — Release Notes (archived)

> Archived verbatim from the GitHub Release [`v0.5.0`](https://github.com/pcalnon/juniper-cascor/releases/tag/v0.5.0) (pcalnon/juniper-cascor), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)).

---

First PyPI release since v0.3.17 — rolls up the pending 0.4.0 work (CHANGELOG `[0.4.0] - 2026-03-03` section, never cut to PyPI) plus 469 commits and ~2.5 months of subsequent changes into a single 0.5.0 release.

See [CHANGELOG.md `[0.5.0] - 2026-05-22`](https://github.com/pcalnon/juniper-cascor/blob/main/CHANGELOG.md) and the preserved [`[0.4.0] - 2026-03-03`](https://github.com/pcalnon/juniper-cascor/blob/main/CHANGELOG.md) section for the full history.

## Highlights

**Security & API hardening** (originally targeted for 0.4.0):
- `SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware`, error sanitization
- Restrictive CORS / rate limiting defaults
- WebSocket auth + message validation + HMAC pickle verification

**Observability / METRICS-MON track** (post-2026-03-03):
- R1.2 readiness/liveness probes with 503 on dep failure + `X-Juniper-Readiness` header
- R1.3 worker heartbeat enrichment (`in_flight_tasks`, `rss_mb`, `last_task_completed_at`)
- R2.1 shared `juniper-observability` adoption (runtime dependency)
- R2.2 shared `juniper-cascor-protocol` package adoption (WS frame schema)
- R3.7 macOS unit-test matrix promoted to required

**Config consolidation** (CFG-03 / CFG-04 / CFG-05):
- `SENTRY_SDK_DSN` → `JUNIPER_CASCOR_SENTRY_DSN`
- `JUNIPER_DATA_URL` consolidated onto `Settings.juniper_data_url`
- `CASCOR_LOG_LEVEL` → `JUNIPER_CASCOR_LOG_LEVEL`

**API envelope migration** (API-09, 3-PR series):
- All `HTTPException` responses normalized to `ResponseEnvelope` shape
- Top-level `"detail"` deprecation alias added and then removed end-to-end

**Hardcoded-values refactor** (Waves 1-3):
- ~60 inline literals moved to `cascor_constants/constants_api/`

**CI infrastructure**:
- juniper-ci-tools v0.2.0 / v0.3.0 / v0.4.0 adoption (workflow-paths, agents-md-version, agents-md-header)
- AGENTS.md auto-bump workflow

🤖 Generated with [Claude Code](https://claude.com/claude-code)
