# Juniper-Recurrence WS-4b — FastAPI / CLI Application: App-Build Implementation Plan

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; build lands in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (RATIFIED build plan — decisions D-WS4b-1…2 concurred by Paul 2026-06-15)
**Last Updated**: 2026-06-15

---

> **What this is.** The concrete build plan for **WS-4b — the application build**: a FastAPI +
> CLI service that wraps the already-shipped `LMURegressor` (WS-4a) on the already-extracted
> `juniper-service-core` framework (WS-2), fed 3-D NPZ windows via `juniper-data-client`
> (`equities_seq`, WS-1). It is the application-side complement to the
> [`JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md)
> (the model only) and the canonical
> [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
> (§6.3/§6.4/§6.8). It **does not restate** their theory; it pins the app's file layout, its usage
> of the *as-built* `juniper-service-core` (not the aspirational §2.3 description), the endpoint
> surface, settings, the data path, the test matrix, the publish ordering, and PR sequencing.

---

## 0. Status & provenance (verified on PyPI + `main`, 2026-06-15)

| Prerequisite | State |
|---|---|
| WS-0 model pick (P3-C / LMU + Approach-C) | **RATIFIED** 2026-06-14 (#411) |
| WS-1 data foundation (3-D NPZ + Δt + temporal split + `equities_seq`) | **SHIPPED** (data #169/#170/#171 + data-client #87) |
| WS-3 `juniper-model-core` (interfaces + conformance kit) | **SHIPPED — PyPI `0.1.0`** (200); in juniper-ml `[tools]`/`[all]` (#416/#418) |
| WS-2 `juniper-service-core` (generic app framework) | **MERGED to juniper-ml `main`** at `juniper-service-core/` (#417/#419/#420/#422); dist `juniper-service-core 0.1.0`. **NOT on PyPI (404), NOT in extras.** Publish workflow `publish-service-core.yml` exists (tag `juniper-service-core-v*`). |
| WS-4a model (`LMURegressor`) | **SHIPPED to `juniper-recurrence` `main` @ `18815b7`** (PRs #1/#2/#3). Dist `juniper-recurrence-model 0.1.0a0` (alpha). **NOT on PyPI (404).** Publish workflow `publish-recurrence-model.yml` exists (tag `juniper-recurrence-model-v*`). |
| `juniper-recurrence` app dist | **404 / greenfield.** Repo holds only `juniper-recurrence-model/`; no `juniper_recurrence/` app package, no app CI/publish workflow yet. |

**Critical-path gates ahead of the docker pin (not blockers for app *code*):** publish-first requires
`juniper-service-core` and `juniper-recurrence-model` to reach PyPI before the app pins them in a
docker build. Both need a **PyPI pending-publisher (Paul)** + a release tag; `juniper-recurrence-model`
additionally needs a **`0.1.0a0` → `0.1.0` bump** (a pre-release does not satisfy `>=0.1.0`). App code
is developed against **editable sibling installs** until then (§10).

---

## 1. The gap WS-4b closes

`juniper-recurrence` today ships the **model** (`LMURegressor` + serializer + conformance) and nothing
else: no service, no HTTP surface, no CLI, no data ingestion at the application level. WS-4b adds the
**app layer** — the first real consumer of `juniper-service-core`'s `create_app` + `TrainingLifecycle`
(RK-4: the 2nd-implementer proof for the *service* contract, mirroring how WS-4a proved the *model*
contract). It exposes train / predict / status / model routes over the LMU, loading 3-D windowed
sequences (`equities_seq`) through `juniper-data-client`.

---

## 2. As-built reconciliation (the service-core we build on is *simpler* than refactor-doc §2.3)

Verified against `juniper-service-core/juniper_service_core/*` on `main`. The build plan targets the
**as-built** API, not the design doc's aspiration — three deltas that *shrink* WS-4b:

- **`create_app(*, title, version, routers=())` wires only the health router.** No middleware, CORS,
  security, or lifespan is auto-attached. ⇒ **the app owns its security/middleware stack and its own
  uvicorn entrypoint.** (`app.py:19-39`; health endpoints `/v1/health`, `/v1/health/ready`.)
- **`TrainingLifecycle(model, on_event=None).run(X, y, **kw) -> TrainResult` is concrete and
  synchronous.** There is **no `TrainingLifecycleBase`, no FSM, no threading, no status enum** (the
  §2.3 "threading + FSM + monitoring wrapper" was not built). ⇒ **WS-4b needs no lifecycle subclass** —
  it instantiates `TrainingLifecycle` directly and reads status from the event sink it injects.
  (`lifecycle.py:49-81`.)
- **No dual-mode CLI / launcher helper exists in service-core** (`launcher.py` only manages auxiliary
  subprocesses). ⇒ **the app writes its own `main()`** (`serve` / `train`).

This reconciliation, plus the one-shot `lstsq` fit, is exactly why **D-WS4b-2 (synchronous training)**
is the right v1 shape.

---

## 3. Ratified decisions (Paul, 2026-06-15)

- **D-WS4b-1 — Published dist `juniper-recurrence`.** The app ships as a **second PyPI package** in the
  repo (import package `juniper_recurrence/`), with its own `publish-recurrence-app.yml`
  (tag `juniper-recurrence-v*`) and an eventual `juniper-ml [servers]` extra entry in **WS-7**. Mirrors
  how `juniper-cascor` / `juniper-canopy` / `juniper-data` are published servers. Name `juniper-recurrence`
  is currently 404 / reserved.
- **D-WS4b-2 — Synchronous in-request training.** `POST /v1/train` runs `TrainingLifecycle.run()`
  **inline** and returns the `TrainResult` in the response body. No background task, no WebSocket event
  stream, no distributed worker. Correct for the microsecond one-shot `lstsq`; WS streaming + async +
  distributed are **deferred to WS-8** (OQ-11, unbuilt in service-core today).

---

## 4. Architecture (synchronous; numpy-only model; service-core framework)

```
 CLI: juniper-recurrence serve            uvicorn juniper_recurrence.app:app
        │  (or `train` → headless)                │  (single worker; in-process state)
        ▼                                          ▼
   juniper_service_core.create_app(routers=[training, predict, model, dataset])
        │   + SecurityHeadersMiddleware + RequestBodyLimitMiddleware
        │   + SecurityMiddleware(APIKeyAuth(keys), RateLimiter(rpm))   ← app attaches (§2)
        ▼
   POST /v1/train ──► data.py: juniper-data-client → equities_seq 3-D NPZ
        │              (X (n,T,F), y, dt (n,T), target_dt (n,), readout_mask/seq_lengths)
        ▼
   TrainingLifecycle(LMURegressor(d, theta, ridge), on_event=sink).run(X, y, dt=…, target_dt=…, …)
        │   emits training_start → epoch_end(0, metrics) → training_end   (n_epochs=1, "converged")
        ▼   sink → state.py (current model + last TrainResult + event log)
   TrainResult JSON  ◄──────────────────────────────────────────────────────┘
   POST /v1/predict ──► state.model.predict(X, dt=…, target_dt=…) → ŷ   (regression; never argmax)
```

- **State** (`state.py`): module-level holder `{model, last_result, events}` behind a `threading.Lock`;
  uvicorn `workers=1` for v1 (in-process; persistence/scale-out deferred). A second concurrent `/v1/train`
  takes the lock or returns `409` (contention is negligible given the µs solve, but the guard prevents
  torn state). `predict` before any `train` → `409` ("no model trained").

---

## 5. File layout (the substantial new surface)

```
juniper-recurrence/
├── juniper-recurrence-model/                # existing (WS-4a) — unchanged
└── juniper-recurrence/                      # NEW app dist (D-WS4b-1)
    ├── pyproject.toml                       # name="juniper-recurrence"; [project.scripts]; deps §10
    ├── README.md  CHANGELOG.md
    ├── juniper_recurrence/
    │   ├── __init__.py   _version.py        # __version__ = "0.1.0"
    │   ├── settings.py                       # Settings(SettingsBase), env_prefix JUNIPER_RECURRENCE_
    │   ├── app.py                            # build_app() → create_app(...) + middleware; module `app`
    │   ├── main.py                           # CLI: `serve` | `train` (C2 dual-mode)
    │   ├── state.py                          # in-process model/result/event holder + Lock
    │   ├── data.py                           # juniper-data-client adapter → 3-D NPZ → fit/predict kwargs
    │   ├── events.py                         # in-memory TrainingEvent sink (ring buffer → /status)
    │   └── routers/
    │       ├── training.py                   # POST /v1/train (sync), GET /v1/training/status
    │       ├── predict.py                    # POST /v1/predict
    │       ├── model.py                      # GET /v1/model (topology + metrics)
    │       └── dataset.py                    # GET /v1/dataset (descriptor)  [thin in v1]
    │   └── schemas.py                        # pydantic request/response models
    └── tests/                               # §12
.github/workflows/
    ├── ci-recurrence-app.yml                 # NEW (or extend ci-recurrence-model.yml matrix)
    └── publish-recurrence-app.yml            # NEW (tag juniper-recurrence-v*; TestPyPI→PyPI OIDC)
```

---

## 6. Endpoint surface (regression-generic — RK-6: no `argmax`, no `accuracy`)

| Route | Method | Auth | Behavior |
|---|---|---|---|
| `/v1/health`, `/v1/health/ready` | GET | exempt | from service-core `health_router()` (auto via `create_app`) |
| `/v1/train` | POST | key | body: dataset ref + hyperparams `{d, theta, ridge, target_dt?}`; loads NPZ via `data.py`; `TrainingLifecycle(LMURegressor(...)).run(X, y, dt=…, target_dt=…, readout_mask=…, seq_lengths=…)`; stores model+result+events; returns `TrainResult` (`final_metrics`, `n_epochs=1`, `stopped_reason="converged"`). **Synchronous.** |
| `/v1/training/status` | GET | key | last status + `final_metrics` + ordered events from the in-memory sink (instant — sync). `{state: "idle"|"trained", …}` |
| `/v1/predict` | POST | key | body: `X` (+ `dt`, `target_dt`) **or** dataset ref; `state.model.predict(X, dt=…, …)`; returns continuous `ŷ`. `409` if no trained model. |
| `/v1/model` | GET | key | `describe_topology()` + `metrics()` of current model; `404`/`409` if none. |
| `/v1/dataset` | GET | key | dataset descriptor (name, shapes) — thin in v1. |

Deferred to fast-follow / WS-8: `/v1/metrics` (Prometheus via `juniper-observability` + `MetricsAuthMiddleware`),
any WebSocket stream, async job submission.

---

## 7. Settings & secrets (`Settings(SettingsBase)`, env prefix `JUNIPER_RECURRENCE_`)

Subclass `juniper_service_core.SettingsBase` (inherits `service_name`, `host`, `port`, `log_level`),
override `model_config = SettingsConfigDict(env_prefix="JUNIPER_RECURRENCE_", extra="ignore")`, and add:

| Field | Default | Notes |
|---|---|---|
| `port` | `8210` | container port; **host 8211 → ctr 8210** at deploy (detailed-design §6.8) |
| `host` | `0.0.0.0` (container) | `127.0.0.1` for local `serve` |
| `api_keys` | `[]` | via `get_secret("JUNIPER_RECURRENCE_API_KEYS", file_env_var=…_FILE)` — **honor `_FILE` indirection** (worker-secret incident precedent) |
| `juniper_data_url` | `http://localhost:8100` | `http://juniper-data:8100` in docker |
| `juniper_data_api_key` | `None` | outbound `X-API-Key` to juniper-data (canopy #329 precedent) |
| `default_d`, `default_theta`, `default_ridge` | `16`, `None`, `0.0` | LMU hyperparameter defaults |

**Test hygiene:** do **not** set `env_file=` on `Settings` (the pydantic-settings `.env`-leak class —
cascor #309 / canopy #325 / data #153); rely on `env_prefix` + `extra="ignore"` only.

---

## 8. Data path (3-D NPZ via `juniper-data-client`, `equities_seq`)

`data.py` fetches the WS-1 additive 3-D contract (`equities_seq`) and maps it to the model kwargs:

- `X (n, T, F)` windowed sequences · `y` per-window target · `dt (n, T)` per-step ZOH gaps
  (`dt[:,0]` unused) · `target_dt (n,)` irregular horizon · `readout_mask (n, T)` / `seq_lengths (n,)`
  many-to-one (final valid step).
- The app passes `dt`/`target_dt`/`readout_mask`/`seq_lengths` **explicitly** into `fit`/`predict`
  (engaging the Δt path; the bare-`predict(X)` uniform-grid fallback is conformance-only).
- Outbound `X-API-Key` for juniper-data when `juniper_data_api_key` is set.

---

## 9. Lifecycle wiring (one-shot solve → synchronous, no subclass)

`/v1/train` constructs an in-memory sink (`events.py`), calls
`TrainingLifecycle(LMURegressor(**hp), on_event=sink).run(X, y, **kw)`. The model emits
`training_start → epoch_end(epoch 0, final metrics) → training_end` with monotonic `seq`; the sink
captures them into `state` for `/v1/training/status`. `TrainResult` (`n_epochs=1`,
`stopped_reason="converged"`) returns inline. **No background thread, no FSM** — the as-built lifecycle
already does exactly this. The **D3 `predict(**kw)` gap** is invisible here: `LMURegressor.predict` is
already widened (LSP-safe); the model-core `0.2.0` change merely documents `**kw` on the ABC (separate,
low-risk — out of WS-4b scope, §14).

---

## 10. Packaging & dependency ordering (PUBLISH-FIRST — binding)

App `pyproject.toml` dependencies:

```
fastapi>=0.110, uvicorn[standard]>=0.30,
juniper-service-core>=0.1.0, juniper-model-core>=0.1.0,
juniper-recurrence-model>=0.1.0, juniper-data-client>=0.4.1
# optional extra [observability]: juniper-observability>=0.3.1
[project.scripts]  juniper-recurrence = "juniper_recurrence.main:main"
```

**Publish order (each must be on PyPI before the next pins it in docker):**
`juniper-model-core` ✅ (200) → **`juniper-service-core` 0.1.0** (gate: Paul pending-publisher + tag
`juniper-service-core-v0.1.0`) → **`juniper-recurrence-model` 0.1.0** (gate: bump `0.1.0a0`→`0.1.0`,
pending-publisher, tag `juniper-recurrence-model-v0.1.0`) → **`juniper-recurrence` app**
(gate: pending-publisher, tag `juniper-recurrence-v0.1.0`).

- **App code is built against editable sibling installs** (`pip install -e ../juniper-service-core`
  etc., the `docs-full-check.yml` cross-repo-clone pattern) until the pins exist. The **`pyproject`
  pin-bump and `requirements.lock` regen land in the SAME PR** once each upstream is published (else
  build-green / runtime-red; RK-11). New shared packages take a **TestPyPI soak** before any docker
  lock pins them.
- **`publish-recurrence-app.yml`**: TestPyPI→PyPI OIDC, tag `juniper-recurrence-v*`. The app has real
  runtime deps, so the TestPyPI verify should follow the **hardened `--no-deps` import-check** pattern
  used by `publish-service-core.yml` (NOT `--extra-index-url https://pypi.org/simple/`); confirm the
  import smoke can run with deps preinstalled on the runner. **Align `publish-recurrence-model.yml` to
  the same no-fallback policy** while here (it currently uses `--extra-index-url`; see §15).
- `pypi` environment keeps the **dual gate** (wait_timer + reviewer approval) — Paul approves.

---

## 11. CLI dual-mode (C2) — `juniper_recurrence/main.py`

`juniper-recurrence serve` → `uvicorn.run("juniper_recurrence.app:app", host=Settings.host, port=Settings.port)`.
`juniper-recurrence train --dataset … [--d --theta --ridge --out model.npz]` → headless: load NPZ via
`data.py`, fit `LMURegressor`, print `metrics()`, persist via `LMUSerializer`. Mirrors cascor's
dual-mode entrypoint; `serve`/`train` share the same `data.py` + model construction.

---

## 12. Test matrix

| Test | Asserts |
|---|---|
| `build_app` smoke | returns `FastAPI`; `/v1/health` → 200; middleware attached; routers mounted |
| `/v1/train` happy path | synthetic 3-D NPZ fixture → 200, `TrainResult` with regression metrics, `n_epochs=1`; `/status` reflects `trained` |
| `/v1/predict` | shape `(n, output_dim)`; **engages `dt`** (passes explicit `dt`); `409` before train |
| security | protected route `401` without `X-API-Key`; health/docs **exempt**; rate-limit `429` path |
| settings | `JUNIPER_RECURRENCE_PORT` etc. honored; `_FILE` secret indirection resolves; **no `.env` leak** |
| RK-6 guard | no `accuracy` key in any response; `grep`-level assert no `argmax` in routers |
| `data.py` adapter | mocked data-client NPZ → correct `(X, y, dt, target_dt, mask, lengths)` mapping |
| CLI | `train` subcommand runs end-to-end on fixture (metrics printed, artifact written); `serve` wiring constructed without binding |
| RK-10 | `gh workflow run` the new `ci-recurrence-app.yml` + `publish-recurrence-app.yml` immediately after first push |

---

## 13. PR sequencing (worktree off `juniper-recurrence` `main`, per worktree procedures)

1. **PR-1 — app skeleton.** `pyproject` (editable sibling deps), `settings.py`, `build_app()` +
   middleware, `health` smoke, `main.py serve`, `ci-recurrence-app.yml`. Verify CI with `gh workflow run`.
2. **PR-2 — training + predict + model routes.** `state.py`, `events.py`, `data.py`, the four routers,
   `schemas.py`, synchronous lifecycle wiring, `main.py train`, full §12 test matrix.
3. **PR-3 — publish + docs.** `publish-recurrence-app.yml`, `README`/`CHANGELOG`; aligns
   `publish-recurrence-model.yml` no-fallback (§15). Publish/pin steps execute **only after** the
   upstream PyPI gates clear.
4. **(juniper-ml, separate PR, WS-7)** — add `juniper-recurrence` to `[servers]`/`[all]` + update
   `test_pyproject_extras.py` in the same PR. **After** the app is on PyPI.

**Standing rule:** no merge without Paul's explicit per-PR signal + `gh pr view <N>` MERGED confirmation;
`gh pr list` + `gh run list --branch main` (green) before assuming a red PR is ours (concurrent sessions).

---

## 14. Explicitly out of scope (deferred / trigger-gated)

WebSocket event stream + async/background training + distributed worker (WS-8, OQ-11) · canopy
generalization (WS-5) · cascor adoption onto shared packages (WS-6) · Prometheus `/v1/metrics` +
`MetricsAuthMiddleware` (fast-follow) · `multi_sine`/`mackey_glass`/`ar_p` synthetic generators +
walk-forward split (WS-4 data follow-ups) · trained projection / nonlinear readout (model increment
1(b), torch) · `juniper-model-core 0.2.0` `predict(**kw)` ABC documentation (item 6 — low-risk, separate).

---

## 15. Risks touched

- **publish-first ordering** (binding) — service-core + recurrence-model on PyPI before the app's docker
  pin; pin-and-lock in the same PR (§10).
- **`juniper-recurrence-model 0.1.0a0` alpha trap** — a pre-release won't satisfy `>=0.1.0`; bump to
  `0.1.0` before publishing (§10).
- **publish-verify `--extra-index-url` policy** — `publish-recurrence-model.yml` adds
  `--extra-index-url https://pypi.org/simple/` (target-squatting vector); align to the hardened
  `--no-deps` no-fallback pattern (`publish-service-core.yml`), and apply the same to the new app
  workflow.
- **RK-6** classification leak — regression-generic routes; conformance-style asserts (no `accuracy`,
  no `argmax`).
- **RK-10** new CI workflow first-run — `gh workflow run` each immediately.
- **RK-11** concurrent-session races on shared extras/CI — dedicated PRs; update extras lint in the same PR.
- **`_FILE` secret indirection** — `get_secret` must honor `*_FILE` (worker incident precedent).
- **pydantic-settings `.env` leak** — no `env_file=` on `Settings` (§7).

---

## 16. Cross-references

- Model build plan: [`JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md).
- Canonical model design (§6.3 model-core, §6.4 service-core lifecycle, §6.8 deploy/ports/env/publish-first):
  [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md).
- Refactor + workstream plan (§2.3 architecture, §2.7 phasing, Part 4 risk register):
  [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md).
- Model-core contract (Decision D3 `**kw` on fit/predict):
  [`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md).
- As-built service-core: `juniper-service-core/juniper_service_core/{app,lifecycle,settings,security,middleware,health,secrets,launcher}.py`.
- As-built model: `juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/model.py` (`LMURegressor`).
- Data foundation: juniper-data #169/#170/#171 + data-client #87 (`equities_seq`, 3-D NPZ).
