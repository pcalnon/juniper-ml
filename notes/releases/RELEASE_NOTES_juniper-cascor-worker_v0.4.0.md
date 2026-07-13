# juniper-cascor-worker v0.4.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.4.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> The GitHub Release [`v0.4.0`](https://github.com/pcalnon/juniper-cascor-worker/releases/tag/v0.4.0) exists.

---

# juniper-cascor-worker v0.4.0 Release Notes

**Release Date:** 2026-05-23
**Version:** 0.4.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-cascor-worker
**Git tag:** `v0.4.0`
**PyPI:** <https://pypi.org/project/juniper-cascor-worker/0.4.0/>

---

## Overview

A minor release centered on env-var canonicalization, an HTTP health-probe surface for the worker, and
single-sourcing the worker's wire-protocol constants from the shared `juniper-cascor-protocol` package. No
public API changes — `WorkerConfig`, `CascorWorkerAgent`, `CandidateTrainingWorker`, the CLI flags, and the
exception hierarchy are all unchanged; all 130 existing tests pass without modification.

---

## Changed

- **CFG-06** (v7 roadmap §20): all 15 worker env vars renamed from bare `CASCOR_*` (or partial-scope
  `CASCOR_WORKER_*`) to the ecosystem-canonical `JUNIPER_CASCOR_WORKER_*` prefix. Legacy names continue to
  work via the shared `juniper-config-tools>=0.1.0,<0.2.0` alias-with-deprecation helper (added as a new
  stdlib-only runtime dep — does not regress the `test_no_pydantic_at_runtime.py` invariant). Each legacy use
  emits one `DeprecationWarning` per process naming both old and new env-var names. The dual-legacy
  `auth_token` chain (`CASCOR_AUTH_TOKEN` + `CASCOR_API_KEY` → `JUNIPER_CASCOR_WORKER_AUTH_TOKEN`) is
  preserved. **Version bumped 0.3.0 → 0.4.0** (additive runtime dep + behaviour-change-with-warning warrants
  a minor). New 85-test regression suite `tests/test_cfg_06_env_prefix_aliases.py`.
- **CFG-06 test-injection contract**: `WorkerConfig.from_env(env: Mapping[str, str] | None = None)` now
  accepts an explicit env mapping (defaults to `os.environ` via `juniper_config_tools.env_with_legacy_alias`).
- **CFG-06 docs sweep**: operator-facing env-var docs (`AGENTS.md`, `README.md`, `Dockerfile` baked `ENV`
  defaults) updated to the canonical `JUNIPER_CASCOR_WORKER_*` names with a preserved legacy → canonical
  mapping.
- **METRICS-MON R2.2.6 / seed-05**: the worker now consumes `juniper-cascor-protocol>=0.1.0` as a runtime
  dependency to single-source the `/ws/v1/workers` wire protocol. `MSG_TYPE_*` literals are derived from
  `juniper_cascor_protocol.worker.WorkerMessageType` (byte-identical values); `_encode_binary_frame`
  delegates to the shared `BinaryFrame.encode`; `_decode_binary_frame` is **kept local intentionally** to
  preserve the worker's stricter SEC-18 bounds. Importing any worker module still places no `pydantic` in
  `sys.modules` (pinned by `tests/test_no_pydantic_at_runtime.py`).

## Added

- **METRICS-MON R1.3 / seed-04 — HTTP health-probe surface** for the worker. New
  `juniper_cascor_worker/http_health.py` (`HealthServer` hand-rolled on `asyncio.start_server`, no new deps)
  hosts three localhost GET endpoints on a configurable port (default `8210`): `GET /v1/health` (no-op OK),
  `GET /v1/health/live` (in-process liveness tick within a 250 ms budget; 503 on failure), and
  `GET /v1/health/ready` (WS connected AND registration complete; 503 + `X-Juniper-Readiness` otherwise). The
  hand-rolled HTTP/1.1 handler accepts `GET` only, caps request bytes at 4096, applies a 2 s read timeout,
  and survives malformed requests. **Enriched heartbeat payload** now carries `in_flight_tasks`,
  `last_task_completed_at`, `rss_mb`, `tasks_completed`, `tasks_failed`; **task accounting** is wired around
  `_handle_task_assign` via `try/finally`. New `health_port` / `health_bind` config fields; cross-platform
  `rss_mb` sampling with no `psutil` dependency.
- New `juniper_cascor_worker/constants.py` module centralizing the wire-protocol message-type discriminators
  (`MSG_TYPE_*`), binary-frame header format (`BINARY_FRAME_*`), auth header / env-var names, and worker
  tuning defaults previously embedded as inline literals across five modules (~70 replacements).
- **`util/test_agents_md_version_drift.py`** — portable port of juniper-ml's lint pinning `AGENTS.md`'s
  `**Version**:` header to `pyproject.toml`'s `[project].version` (preventive; already in sync at 0.4.0).
- **METRICS-MON R3.7**: the `macos-latest` (Python 3.12) leg was added to the unit-tests CI matrix and, after
  a clean soak, flipped from `experimental: true` → `false`, making it required.

## Notes

- No public API changes; `WorkerConfig`, `CascorWorkerAgent`, `CandidateTrainingWorker`, CLI flags, and the
  exception hierarchy are all unchanged. All 130 existing tests pass without modification; pre-commit (22
  hooks) is clean.

---

## Links

- Package CHANGELOG (`[0.4.0]` section): <https://github.com/pcalnon/juniper-cascor-worker/blob/main/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-cascor-worker/0.4.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-cascor-worker/releases/tag/v0.4.0>
