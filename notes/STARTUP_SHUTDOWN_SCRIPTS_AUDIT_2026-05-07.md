# Startup / Shutdown Scripts Audit — 2026-05-07

**Author:** Paul Calnon
**Subject:** Audit and refresh of `util/juniper_plant_all.bash` and `util/juniper_chop_all.bash`
**Status:** Pass 1 — implemented (validation + tests pending). Pass 2 — pending.
**Branches:**

- Pass 1: `fix/startup-scripts-pass1` (BROKEN + DEGRADED items)
- Pass 2: `fix/startup-scripts-pass2` (NIT items)

---

## Scope

The two host-level orchestration scripts in `juniper-ml/util/` start and stop the four
juniper application services on a single host (no Docker, no Kubernetes):

- `juniper-data` (FastAPI dataset service, port 8100)
- `juniper-cascor` (FastAPI CasCor training service, port 8201)
- `juniper-canopy` (Dash + FastAPI dashboard, port 8050)
- `juniper-cascor-worker` (WebSocket worker that connects to cascor)

Substantial drift has accumulated between what the scripts assume and the current state
of each repo. This audit cross-checks every documented assumption against the source of
truth in each downstream repo and the live conda environments.

## Method

For each service:

1. Re-read the launch invocation in `util/juniper_plant_all.bash`.
2. Confirm the entrypoint module path against the current repo source.
3. Confirm port and health-endpoint defaults against the current settings module.
4. Enumerate required env vars from each repo's settings/config module.
5. Cross-check against `/opt/miniforge3/envs/<EnvName>` for binary presence and
   activate.d hook coverage.
6. Confirm the chop script's pid-file consumption pattern matches what plant writes.

Findings are graded by severity:

- 🔴 **BROKEN** — service either fails to start or starts in a state where the script
  reports success but the service is dead/unusable.
- 🟡 **DEGRADED** — service comes up but with stale, deprecated, or incomplete
  configuration; user-visible warnings or partial functionality.
- 🟢 **NIT** — cosmetic, documentation, or edge-case-only issue.

---

## Findings

### 🔴 #1 — Worker missing required `CASCOR_SERVER_URL` env var (BROKEN)

`util/juniper_plant_all.bash:404–405` runs the worker console-script with **no env vars
set**. The worker's config validation (`juniper-cascor-worker/juniper_cascor_worker/config.py:153–156`)
raises `WorkerConfigError("server_url is required — set CASCOR_SERVER_URL or pass --server-url")`
during startup. The launcher's 2-second `kill -0` check (`juniper_plant_all.bash:411–416`)
catches this but only emits a `WARNING` and continues, so users see "all started
successfully" while the worker is dead.

**Fix:** export `CASCOR_SERVER_URL="ws://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}/ws/v1/workers"`
(and pass through optional `CASCOR_AUTH_TOKEN`) before the `nohup`. Convert the
post-launch process check into a hard failure that trips the `cleanup_on_failure` trap.

**Source-of-truth references:**

- `juniper-cascor-worker/juniper_cascor_worker/constants.py:151` (`ENV_SERVER_URL`)
- `juniper-cascor-worker/juniper_cascor_worker/config.py:120,153–156` (validation)
- `juniper-cascor-worker/juniper_cascor_worker/cli.py:71–114` (websocket dispatch)

### 🔴 #2 — Canopy uses wrong conda env (BROKEN under common shell config)

`util/juniper_plant_all.bash:118` pins `JUNIPER_CANOPY_CONDA="JuniperCanopy"`, but only
`/opt/miniforge3/envs/JuniperCanopy1/etc/conda/activate.d/00_isolate_from_tch_rs.sh`
strips the inherited `LIBTORCH` / `LD_LIBRARY_PATH` from the shell. Without that hook
the rust_mudgeon `LIBTORCH` from the user's `~/.bashrc` preempts the env's torch and
breaks ~770 canopy tests at import time. On a shell where `LIBTORCH` is exported,
canopy fails to import torch → fails health probe → trips the cleanup trap → entire
plant_all aborts.

**Fix:** flip the default to `JuniperCanopy1`. Document the override.

**Source-of-truth references:**

- Memory: `project_canopy_libtorch_python_collision_2026-05-07.md`
- Filesystem: `/opt/miniforge3/envs/JuniperCanopy1/etc/conda/activate.d/00_isolate_from_tch_rs.sh`
  (present), `/opt/miniforge3/envs/JuniperCanopy/etc/conda/activate.d/` (no LIBTORCH hook)

### 🟡 #3 — Canopy uses deprecated `CASCOR_SERVICE_URL` env var (DEGRADED)

`util/juniper_plant_all.bash:388` sets `CASCOR_SERVICE_URL`. The canonical name is
`JUNIPER_CANOPY_CASCOR_SERVICE_URL` (auto-derived from canopy's
`Settings.model_config.env_prefix="JUNIPER_CANOPY_"` at
`juniper-canopy/src/settings.py:123`). Legacy name still works via fallback at
`juniper-canopy/src/settings.py:236–249` but logs a deprecation warning each boot.

While here, also pass `JUNIPER_CANOPY_JUNIPER_DATA_URL` so canopy's
`/v1/health/ready` probe resolves both upstream dependencies; the script currently
relies on canopy's hard-coded `http://localhost:8100` default which obscures any
operator override of `JUNIPER_DATA_PORT`.

**Fix:** rename and add the data URL. Both via canonical pydantic-prefixed names.

**Source-of-truth references:**

- `juniper-canopy/src/settings.py:114,123` (Settings + env_prefix)
- `juniper-canopy/src/settings.py:226–249` (legacy aliases with deprecation paths)

### 🟡 #4 — `JUNIPER_CASCOR_HOST` is not exported to cascor server (DEGRADED) — Pass 2

`util/juniper_plant_all.bash:370` only exports `JUNIPER_CASCOR_PORT` to the cascor
server; cascor's settings default `host=127.0.0.1`
(`juniper-cascor/src/api/settings.py:14,123`). For localhost-only deployments this is
fine — the launcher's health probe at `localhost:8201` works because both ends resolve
to 127.0.0.1 — but the script's documented `JUNIPER_CASCOR_HOST` override is silently a
no-op for binding; it only changes the URL the launcher polls.

**Fix:** also export `JUNIPER_CASCOR_HOST="${JUNIPER_CASCOR_HOST}"` to the cascor
process.

### 🟡 #5 — Worker process check is too weak (DEGRADED)

The 2-second `kill -0` in `util/juniper_plant_all.bash:411–416` misses the worker's
primary failure modes — config-validation crash (#1), WS reconnect wedge, registration
failure. The worker now ships an HTTP health listener at `127.0.0.1:8210` with
`/v1/health` / `/v1/health/live` / `/v1/health/ready` endpoints
(`juniper-cascor-worker/juniper_cascor_worker/http_health.py`,
`juniper-cascor-worker/juniper_cascor_worker/worker.py:124–142`).

**Fix:** call `wait_for_health "juniper-cascor-worker"
"http://127.0.0.1:${JUNIPER_WORKER_HEALTH_PORT}/v1/health/ready"` symmetric with the
other three services, and surface failure as a hard error.

### 🟡 #6 — No pre-flight check that worker binary exists (DEGRADED)

The script uses `JuniperCascor` for the worker but the worker requires
`websockets>=11.0`, which is not part of the cascor server's normal dependency
footprint. If the env was rebuilt without installing the worker package,
`${JUNIPER_WORKER_BIN}` won't exist and the launcher silently no-ops.

**Fix:** add `[[ -x "${JUNIPER_WORKER_BIN}" ]]` to the pre-flight block alongside the
existing `validate_conda_env` calls.

### 🟢 #7 — `juniper-data` host is hardcoded (NIT) — Pass 2

`util/juniper_plant_all.bash:87` defines `JUNIPER_DATA_HOST="0.0.0.0"` (ignores any
caller value), then the docstring at line 11 lists `JUNIPER_DATA_HOST` as an override
that doesn't exist. Also passes 0.0.0.0 hardcoded to uvicorn at line 352.

**Fix:** flip to `JUNIPER_DATA_HOST="${JUNIPER_DATA_HOST:-0.0.0.0}"` and reference the
variable in the uvicorn invocation.

### 🟢 #8 — Pre-flight `command -v uvicorn` runs before conda activation (NIT) — Pass 2

`util/juniper_plant_all.bash:283` requires uvicorn on the launcher's PATH, but uvicorn
lives inside each conda env. On a fresh shell with no env active, the check fails
before `JuniperData` is ever activated.

**Fix:** drop uvicorn from the global pre-flight set; the per-env binary check
already covers it.

### 🟢 #9 — `JUNIPER_DATA_HOST` shadowing (NIT) — Pass 2

Same line as #7: covered by the same fix.

### 🟢 #10 — Chop pid-file format is fragile (NIT) — Pass 2

Plant writes `name:    pid` (variable whitespace). Chop parses with `%%:*` / `#*:` /
`tr -d ' '`. Robust enough today, but a single typo in the format could silently break
all four shutdowns. Switch to `name=pid` (one per line) for both writer and reader.

**Fix:** swap to `=`-keyed format on both ends, keep the existing `validate_pid` call.

### 🟢 #11 — Chop's worker grep `cascor.*worker` is over-greedy (NIT) — Pass 2

`util/juniper_chop_all.bash:212` matches `juniper.cascor.worker\|juniper_cascor_worker\|cascor.*worker\|${WORKER_SEARCH_TERM}`.
The third alternative `cascor.*worker` can match unrelated dev shell processes
(e.g., `bash -lc "tail -f cascor.log; rerun-worker"`).

**Fix:** drop the third alternative; the underscore and dash variants are sufficient.

### 🟢 #12 — Duplicate `echo` traces (NIT) — KEEP per memory

`util/juniper_chop_all.bash:73–84` has duplicated `echo` lines for `SIGTERM_TIMEOUT` /
`KILL_WORKERS`. Per memory `feedback_chop_all_echo_debug.md` these are intentional
future-logging placeholders — **do not remove**.

---

## Pass 1 plan (BROKEN + DEGRADED)

In-scope items: **#1, #2, #3, #5, #6**.

Estimated diff: ~30 lines in `util/juniper_plant_all.bash` plus new test file.

### Pass 1 implementation status

| Item | Severity | Status |
| ---- | -------- | ------ |
| #1 worker URL | 🔴 BROKEN | implemented |
| #2 canopy env | 🔴 BROKEN | implemented |
| #3 canopy env-var rename | 🟡 DEGRADED | implemented |
| #5 worker health probe | 🟡 DEGRADED | implemented |
| #6 worker binary preflight | 🟡 DEGRADED | implemented |

**Pass 1 implementation summary:** ~60-line diff confined to `util/juniper_plant_all.bash`.
Header docstring updated. `JUNIPER_CANOPY_CONDA` now defaults to `JuniperCanopy1` and is
override-friendly. Worker block exports `CASCOR_SERVER_URL`, `CASCOR_AUTH_TOKEN`,
`CASCOR_WORKER_HEALTH_PORT`, `CASCOR_WORKER_HEALTH_BIND` to the worker process. Worker
health is now probed via `wait_for_health` against `/v1/health/ready` (both nohup and
systemd code paths). Pre-flight block validates the worker conda env and binary, and
checks the health-listener port is free. Canopy launch sets canonical pydantic-prefixed
env vars `JUNIPER_CANOPY_CASCOR_SERVICE_URL` and `JUNIPER_CANOPY_JUNIPER_DATA_URL`.
Bash syntax (`bash -n`) and shellcheck both clean.

### Pass 1 testing plan

1. `bash -n util/juniper_plant_all.bash util/juniper_chop_all.bash` (syntax)
2. `shellcheck` via the existing pre-commit hook
3. New `tests/test_juniper_plant_all.py` with isolated subprocess execution and
   stub-`/opt/miniforge3` fixtures to assert:
   - Pre-flight detects missing worker binary and aborts before launching anything.
   - Default canopy conda env is `JuniperCanopy1`.
   - Worker invocation receives `CASCOR_SERVER_URL` in its environment.
   - Canopy invocation receives `JUNIPER_CANOPY_CASCOR_SERVICE_URL` (NOT the legacy
     name).
   - Worker health URL is `http://127.0.0.1:8210/v1/health/ready` and is referenced by
     the wait_for_health call.
4. Run all existing unit tests (`tests/test_*.py`).

---

## Pass 2 plan (NIT)

In-scope items: **#4, #7, #8, #9, #10, #11**. (#12 stays as-is.)

### Pass 2 implementation status

| Item | Severity | Status |
| ---- | -------- | ------ |
| #4 cascor host export | 🟡 DEGRADED | pending |
| #7 data host honors override | 🟢 NIT | pending |
| #8 uvicorn preflight | 🟢 NIT | pending |
| #9 data-host shadowing | 🟢 NIT | pending |
| #10 pid file format | 🟢 NIT | pending |
| #11 worker grep tightening | 🟢 NIT | pending |

### Pass 2 testing plan

- Backward-compat test: chop_all reads both legacy `name: pid` AND new `name=pid`
  formats during the transition window.
- Test that JUNIPER_DATA_HOST override actually plumbs to uvicorn args.
- Test that the chop worker grep does not match a process containing
  `cascor` and `worker` separated by unrelated tokens.

---

## Out of scope

- systemd-mode codepath (`USE_SYSTEMD=1`). Both scripts have a parallel systemd block
  that this audit does not exercise. If/when juniper migrates to user-systemd as the
  default deployment, a separate audit pass should validate unit-file env-passing.
- Docker mode. `juniper-deploy` orchestrates the same services via Docker Compose and
  is unaffected by this script-level audit.
- Worker auth-token wiring. Worker accepts `CASCOR_AUTH_TOKEN` and `CASCOR_API_KEY`
  optionally; cascor server's auth requirements are deployment-specific and out of
  scope here.

---

## References

- Plant: `util/juniper_plant_all.bash`
- Chop: `util/juniper_chop_all.bash`
- Cascor settings: `juniper-cascor/src/api/settings.py:12,123–124`
- Canopy settings: `juniper-canopy/src/settings.py:114,123,226–249`
- Worker config: `juniper-cascor-worker/juniper_cascor_worker/config.py:120,153–156`
- Worker constants: `juniper-cascor-worker/juniper_cascor_worker/constants.py:107,151–157`
- Worker health: `juniper-cascor-worker/juniper_cascor_worker/http_health.py`
- Memory: `project_canopy_libtorch_python_collision_2026-05-07.md`,
  `feedback_chop_all_echo_debug.md`,
  `project_phase_d_control_buttons_shipped.md`
