# Juniper-Canopy — Model-Selection A1 Enabler: Cross-Repo Integration Scope

**Project**: juniper-canopy (subject) / juniper-ml (doc home)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-18
**Status**: Scoping / program plan (design-first; pre-implementation)

> Scopes the cross-repo work to make canopy's model selection **meaningful** —
> i.e. to make the `recurrence` (LMU) model genuinely *selectable and trainable*
> from the dashboard, not just a soft-gated "coming soon" entry. Follows the A0
> registry (canopy #372) and the selection design-of-record
> [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md).
> Grounded by a three-slice investigation (recurrence API, canopy backend/dataset
> flow, juniper-deploy) on 2026-06-18; key `file:line` in §3/§9.

---

## 1. Goal & current state

**Goal:** a canopy user can select `recurrence`, pick a compatible 3-D dataset, train
it, and see results — the A1 feature operating against a *real* second model.

**Already done (no work):**

| Piece | State |
|---|---|
| juniper-data 3-D / irregular-Δt generators (WS-1) | **DONE** — `equities_seq`, `irregular_sine` ship the 3-D `(W,L,F)`+`dt` contract |
| juniper-data-client 3-D support | **DONE** — `validate_npz_contract` is `ndim`-dispatched (`tabular`/`sequence`); `download_artifact_npz` returns all keys |
| recurrence **model** (`juniper-recurrence-model`) | **DONE** — on PyPI |
| recurrence **app/service** (`juniper-recurrence`) | **DONE (code)** — app package on `origin/main` (`juniper-recurrence/juniper_recurrence/`) + PyPI **0.1.1**; FastAPI on port 8210; **Dockerfile + docker smoke-test CI shipped** (recurrence #21, `76ad27a`, 2026-06-18) |
| canopy A0 registry | **DONE** — `model_registry.py` seeds `cascor`/`recurrence`; `recurrence.status="coming_soon"`, `provider="juniper-recurrence"` |

**Not done (the A1 enabler):**

| Piece | Repo | State |
|---|---|---|
| recurrence service in the deploy stack | juniper-deploy | **missing** (no compose service yet; the recurrence **Dockerfile is now DONE** — recurrence #21) |
| canopy → recurrence backend adapter | juniper-canopy | **missing** (no client, no adapter) |
| model → backend routing | juniper-canopy | **missing** (`create_backend` keys on demo-vs-service, never on model) |
| **execution-paradigm bridge** (live-monitor ↔ one-shot fit) | juniper-canopy | **missing — the dominant gap (§2)** |
| 3-D dataset **load + display** | juniper-canopy | **missing** — canopy must gain `ndim`-aware load + a sequence plotter (the `ndim==2` reject is wrong-direction debt) |
| the A1 selection UI itself | juniper-canopy | **missing** (design-of-record only) |

---

## 2. The dominant finding — execution-paradigm mismatch

The selection UI (dropdown + compatibility gate) is the *easy* part. The hard part the
design-of-record under-weighted:

- **Canopy is a live-training monitor.** Its `BackendProtocol` and entire dashboard are
  built around an **asynchronous, pollable** training contract: `start_training` returns
  immediately, then canopy polls `get_status` / `get_metrics` / `get_metrics_history` on
  a timer and charts per-epoch progress, network-topology *growth*, and a 2-D decision
  boundary (`src/backend/protocol.py:214-285`).
- **The recurrence service is a synchronous one-shot fit.** `POST /v1/train` **blocks
  until done** (drives `TrainingLifecycle.run()` inline), returns final metrics; status
  is terminal (`idle`/`trained`); there is **no background job, no WebSocket, no
  per-epoch metrics endpoint** (LMU is a fixed-order model fit by a single ridge/lstsq —
  there are no meaningful epochs to stream). Streaming was explicitly deferred (the
  app's own "WS-8").

So canopy's poll-and-chart machinery has **nothing to poll** on the recurrence side.
Bridging this is a genuine design decision (D1, §4), not adapter wiring — and it means
**A1 requires canopy to grow a second model-execution paradigm (one-shot fit) alongside
its live-training paradigm.** The other genuinely-substantial canopy lift is **3-D
dataset display** (D2, §3.4) — canopy must load and *visualize* 3-D sequence datasets, not
gate them out; it is independent of this execution question and independently valuable.
The remainder (adapter, Dockerfile, routing) is comparatively mechanical.

---

## 3. Work breakdown by repo

### 3.1 juniper-recurrence

- **Dockerfile — DONE** (recurrence #21, `76ad27a`, 2026-06-18): multi-stage
  `python:3.13-slim`, provenance labels, `EXPOSE 8210`, `/v1/health` `HEALTHCHECK`,
  `ENTRYPOINT juniper-recurrence serve`, + a docker smoke-test CI. The app is in the repo
  *subdirectory* `juniper-recurrence/`, handled in the Dockerfile header (deploy
  `build.context: ../juniper-recurrence/juniper-recurrence`). No further recurrence-side
  image work. *(A concurrent WS-7/OUT-4 effort is actively shipping recurrence
  deploy-readiness — the deploy compose service in §3.2 may land from there.)*
- *(Optional, only if D1-B is chosen)* grow an async/streaming training surface.
- Already satisfies the deploy contract otherwise: `serve` CLI
  (`juniper-recurrence = juniper_recurrence.main:main`), `/v1/health` + `/v1/health/ready`
  (service-core), `JUNIPER_RECURRENCE_` env prefix, `*_FILE` secrets, `/metrics`.

### 3.2 juniper-deploy

Standard service addition (the recurrence Dockerfile now exists — §3.1, so deploy can
`build:` directly). Clone the `juniper-cascor` compose block
(`docker-compose.yml:167-469`) with: `build.context: ../juniper-recurrence/juniper-recurrence`
(the app subdirectory); `*resources-light`; ports `8211:8210`; `JUNIPER_RECURRENCE_*` env;
outbound
`JUNIPER_DATA_URL`; new secret `juniper_recurrence_api_keys` (+ `./secrets/` +
`./secrets.example/`); `/v1/health` healthcheck; `networks: [backend, data, frontend]`;
`profiles: ["full",…]`; `depends_on: juniper-data`. Add a prometheus scrape job
(`juniper-recurrence:8210`), `.env.example` vars (`RECURRENCE_PORT`/`RECURRENCE_HOST_PORT`/
`RECURRENCE_SERVICE_URL`), and provenance build-args. **Deploy-gated** (Paul approves).
This can land **independently** and bring the service up healthy before canopy consumes it.

### 3.3 juniper-canopy (the core)

1. **`RecurrenceServiceAdapter`** (D3) — a new backend adapter speaking the recurrence
   REST contract via `httpx` (~150–250 LOC; no WebSocket). Far simpler than
   `CascorServiceAdapter`. **Must send `X-API-Key`** — the recurrence service runs
   `SecurityMiddleware`, so add a canopy `Settings.recurrence_service_url` +
   `recurrence_api_key` (+ a deploy `_FILE` secret), mirroring the canopy→data /
   canopy→cascor outbound-key pattern; without it the adapter 401s. **Generous
   read-timeout** — `/v1/train` blocks through a juniper-data fetch + lstsq, so the httpx
   call needs a long timeout and the UI one-shot path (D1-A) must handle `409`
   (train-in-progress) + timeout/connection errors.
2. **Model → backend routing** (D5) — extend `create_backend()`
   (`src/backend/__init__.py:32`) into an `nn_model`/`provider`-keyed factory (the
   registry already carries `ModelSpec.provider`). Thread `nn_model` through; the target
   service validates + fails closed (design §5.9/FR9).
3. **One-shot execution path + panel suppression** (D1-A, D6) — a model-class-aware
   rendering mode: for a one-shot model, submit `POST /v1/train`, show progress, render
   the single `TrainResponse`/`/v1/model` result; **suppress** the cascade-specific
   panels (network-topology growth, decision boundary, candidate metrics) that don't map
   to LMU.
4. **3-D dataset load + display** (D2) — add 3-D `DatasetTypeSpec` rows, make canopy's
   dataset load `ndim`-aware (not `ndim==2`-gated), and add a sequence/Δt plotter mode so
   canopy can **display** 3-D datasets. *Training delivery* stays service-side (the model
   service fetches from juniper-data). Independently valuable; not gated on the recurrence
   service (§3.4).
5. **The A1 selection UI** — the surface + gate + `nn_model` mirror from the design note.

### 3.4 The canopy 2-D assumptions — what 3-D *display* must make `ndim`-aware

Canopy's local data + plot path hard-assumes 2-D classification. Per D2 these become
`ndim`-aware (dispatch), **not** reject-3-D:

- `demo_mode.py:833` — `if inputs.ndim != 2: raise ValueError("X_full must be 2D …")`,
  reading the `X_full` key 3-D sequence artifacts lack → dispatch on
  `validate_npz_contract` (`tabular`/`sequence`); handle the split-suffixed sequence keys
  (`X_train`/`dt_train`/…).
- `dataset_plotter.py` — 2-D scatter (`X[mask,0]`/`X[mask,1]`) → add a sequence/Δt mode
  (sample sequences as Δt-spaced time-series; show the irregular spacing).
- normalization — feature-axis stats over `(N,F)` → sequence-aware.
- decision boundary — genuinely 2-D-classification-only → **suppress** for 3-D (D6).

*Training delivery* still doesn't make canopy hold the array (cascor/recurrence pull from
juniper-data); only *display* needs this 3-D-aware path.

---

## 4. Key design decisions

### D1 — Bridge the execution-paradigm mismatch (DOMINANT)

**D1-A — canopy grows a one-shot "fit" path (RECOMMENDED).** A model-class-aware mode:
recurrence is rendered as submit → block/spinner → result view (final metrics + model
info), bypassing the live poll-and-chart machinery and suppressing cascade panels.

- *Strengths:* **honest** — LMU *is* a one-shot fit; faking epochs would be a lie. Keeps
  the recurrence service simple (as built). Matches the design's model-class direction.
- *Weaknesses:* canopy grows a second rendering mode; the dashboard's "live monitor"
  identity gains a distinct result-view experience.
- *Risks:* scope creep into the result view; panel-suppression must be model-aware
  everywhere.
- *Guardrails:* a `ModelSpec.execution = "live" | "one_shot"` field drives the path; build
  the minimal result view first (metrics table), enrich later.

**D1-B — recurrence service grows async/streaming (WS-8).** Add background training +
polling/WebSocket so canopy reuses its existing machinery.

- *Strengths:* uniform UX; less *canopy* work.
- *Weaknesses:* **dishonest + wasteful** — fabricating per-epoch progress for a
  synchronous lstsq; larger *recurrence* work; fights the model's nature.
- *Risks:* fake progress misleads researchers; maintenance of a streaming layer with no
  real signal.
- *Guardrails:* only if a *future* recurrence variant genuinely trains iteratively.

**Recommendation: D1-A.** Reject D1-B as fabricating progress a one-shot fit doesn't
have. This is the crux the design-of-record should absorb: **A1 = selection UI + a
one-shot execution paradigm**, not selection UI alone.

### D2 — 3-D datasets: separate *training delivery* from *display* (revised 2026-06-18)

The first draft conflated two things. **Training delivery is service-side** — the model
service fetches the dataset from juniper-data; canopy doesn't pipe the array to the model
(already how the real cascor path works; recurrence is the same). **But dataset *display*
is canopy's job, and must work for 3-D too.** A research dashboard has to let the user load
and visualize *any* processed dataset, including 3-D sequence / irregular-Δt data; gating
canopy's dataset load on `ndim==2` is the wrong direction.

So **canopy gains genuine 3-D dataset load + display** (not service-only-avoid): make the
load path `ndim`-aware (dispatch on `validate_npz_contract`'s `tabular`/`sequence` result
instead of raising on `ndim!=2`) and add a sequence/Δt visualization mode to the
dataset-plotter. A larger canopy lift, but it removes the `ndim==2` debt and restores the
dashboard's core value (dataset understanding) for the whole new model class. It is
**independently valuable** (load + view an `equities_seq` dataset before recurrence
training exists) and **not gated on the recurrence service** — so it can land *earlier*
than the training integration (§6).

### D3 — Integration: generic canopy adapter (RECOMMENDED) vs new client package

A `RecurrenceServiceAdapter` inside canopy (httpx, sync REST) is small and sufficient. A
published `juniper-recurrence-client` (mirroring `juniper-cascor-client`) is optional —
defer unless another consumer needs it.

### D4 — Recurrence image — DONE (settled + implemented)

Recurrence #21 (`76ad27a`, 2026-06-18) shipped a multi-stage `python:3.13-slim` Dockerfile
with provenance labels + a docker smoke-test CI — i.e. the build-from-local-Dockerfile
convention, with the subdirectory build context handled. No decision remains; deploy uses
`build.context: ../juniper-recurrence/juniper-recurrence`.

### D5 — Model→backend routing

Extend `create_backend()` keyed on `nn_model`/`ModelSpec.provider`. Medium, low-risk; no
multiplexing backend needed for two models. `BackendProtocol` survives structurally (its
`TypedDict`s are `total=False`, so a recurrence backend can stub
topology/decision-boundary to `None`).

### D6 — UI panel suppression (model-aware)

Cascade-specific panels (topology growth, decision boundary, candidate metrics) are
meaningless for LMU. Drive visibility from the model class (D1-A's `execution`/registry
metadata), not per-panel hacks.

---

## 5. Dependencies, ordering & gates

```text
juniper-data 3-D ✓ ─────────────────────────────┐
recurrence model+app on PyPI ✓ ──────────────────┤
                                                 ▼
[D4 Dockerfile ✓ #21] ──────► [§3.2] deploy: recurrence service (Paul-gated)
                                                 │  (service up, healthy, independent)
                                                 ▼
[D1 decision] one-shot paradigm ──► [§3.3] canopy: adapter + routing + one-shot
                                     path + panel suppression
                                                 │
                                                 ▼
                                     A1 selection UI goes from soft-gate → live

[independent, no upstream gate]
canopy 3-D dataset load + display (D2) ──► ndim-aware load + sequence plotter
   (Phase 1 — valuable on its own; prerequisite for meaningful 3-D selection)
```

**Gates:** (a) the **D1 architectural decision** (one-shot path) — settle before canopy
build; (b) **deploy approval** (Paul) for the stack change. (The recurrence Dockerfile
gate is already cleared — #21.)

**Independence:** §3.1+§3.2 (recurrence Dockerfile + deploy service) can land first and
stand alone; the canopy core (§3.3) is the larger, separable lift.

---

## 6. Phased plan

- **Phase 0 — stand up the service (deploy-gated, no canopy dependency):** the recurrence
  Dockerfile is already done (§3.1) → juniper-deploy recurrence service + secrets +
  prometheus + env. Outcome: `recurrence:8210` healthy in the stack. (May land from the
  concurrent WS-7 effort.)
- **Phase 1 — canopy 3-D dataset load + display (independent, no upstream gate):**
  `ndim`-aware load + a sequence/Δt plotter mode + 3-D `DatasetTypeSpec` rows (D2).
  Delivers dataset-understanding for the new model class early and removes the `ndim==2`
  debt — valuable even before recurrence training exists.
- **Phase 2 — canopy recurrence training integration:** `RecurrenceServiceAdapter` (D3) +
  model→backend routing (D5) + one-shot execution path & panel suppression (D1-A/D6) + the
  A1 selection UI. Flip `recurrence.status` `coming_soon → live`.
- **Phase 3 — polish (optional):** published `juniper-recurrence-client`; recurrence async
  surface only if a genuinely-iterative variant arrives.

---

## 7. Risks & guardrails

- **Paradigm creep (D1).** The one-shot result view could balloon. *Guardrail:* minimal
  metrics-table result first; registry-driven `execution` flag; no fake epochs.
- **Cascade-panel leakage.** A panel reading cascade fields renders empty/garbage for
  LMU. *Guardrail:* model-aware visibility from one source (D6); a test that asserts
  suppressed panels for a one-shot model.
- **3-D display correctness.** Canopy's 3-D load/plot path must handle sequence artifacts
  (split-suffixed keys, `(W,L,F)` shapes, per-step Δt, regression targets) — the inverse of
  the old `ndim==2` reject. *Guardrail:* dispatch on `validate_npz_contract`; tests for 3-D
  load + sequence-plot; suppress the 2-D-only decision-boundary panel for 3-D (D6).
  *Training delivery* stays service-side, so a model never receives a canopy-mangled array.
- **Deploy/provenance.** *Guardrail:* Dockerfile mirrors the provenance-stamp pattern;
  Paul drives the deploy gate.
- **Dataset compatibility at runtime.** A 2-D dataset sent to recurrence (or 3-D to
  cascor) must fail closed. *Guardrail:* the A1 gate (design) + the service's own
  `validate_npz_contract`.
- **Blocking `/v1/train`.** The synchronous fit (juniper-data fetch + lstsq) can run long.
  *Guardrail:* generous adapter read-timeout + UI handling of `409`/timeout/connection
  errors; revisit a server-side async job only if fits exceed a tolerable blocking window.
- **Outbound auth.** The recurrence service is API-key-secured; a missing canopy-side key
  yields 401s. *Guardrail:* `recurrence_api_key` setting + deploy `_FILE` secret (§3.3),
  same pattern as canopy→data / canopy→cascor.

---

## 8. Open questions

- **OQ-1:** ratify D1-A (one-shot paradigm) — does canopy own a "fit result" view, or is
  recurrence's first cut just "submit + show final metrics"?
- **OQ-2:** is `/v1/predict` (inference-after-fit) and/or `/v1/crossval` in A1 scope, or
  train-and-render-metrics only? (LMU's value is forecasting, so predict-from-dashboard is
  a plausible early ask.)
- **OQ-3:** does Phase 0 (service up) proceed before the canopy decision, or wait?
- **OQ-4:** which 3-D dataset(s) seed canopy's registry first (`equities_seq` vs
  `irregular_sine`), and do they need canopy-side metadata beyond a juniper-data ref?
- **OQ-5:** is a published `juniper-recurrence-client` wanted now (other consumers?) or
  deferred (D3)?
- **OQ-6:** the 3-D dataset **visualization** design (D2) — how to plot a `(W,L,F)`
  irregular-Δt sequence dataset (sample sequences as Δt-spaced time-series? a feature
  heatmap? the Δt distribution?). The plotter's sequence mode needs a viz spec.

---

## 9. Validation & references

**Investigation (2026-06-18):** three independent sub-agents — recurrence API/readiness,
canopy backend/dataset flow, juniper-deploy integration — plus an orchestrator
reconciliation that corrected a stale-local-clone read (the recurrence **app is** on
`origin/main` + PyPI 0.1.1; the "unmerged app" finding was stale). **Validation (2026-06-18):** a consistency/fidelity pass confirmed the central thesis
(D1 — recurrence `/v1/train` is a synchronous one-shot fit) against current source, and
corrected: the recurrence **Dockerfile is DONE** (#21, which landed *during* the
investigation — a second stale-read caught here), the canopy→recurrence **outbound
API-key** + **blocking-`/v1/train` timeout** gaps (now §3.3/§7), and the compose/protocol
line citations. markdownlint clean. **D2 revised 2026-06-18 (per Paul):** dataset
*display* is canopy's job for 3-D too — canopy gains `ndim`-aware load + a sequence plotter
rather than gating on `ndim==2`; only *training delivery* is service-side, and 3-D display
is now an independent earlier phase (§6 Phase 1).

**Key anchors:**

- recurrence app: `juniper-recurrence/juniper_recurrence/{app,main}.py`, `routers/`
  (`/v1/train` sync, `/v1/training/status`, `/v1/predict`, `/v1/model`, `/v1/dataset`,
  `/v1/crossval`, `/v1/health`); port 8210; **Dockerfile present** (recurrence #21).
- canopy: `src/backend/protocol.py:214-285` (`BackendProtocol`);
  `src/backend/__init__.py:32` (`create_backend`, demo-vs-service); `src/demo_mode.py:833`
  (`ndim==2` gate); `src/model_registry.py` (A0; `provider`).
- juniper-deploy: `docker-compose.yml:167-469` (cascor service template); build-from-local
  Dockerfile convention; ports 8100/8201/8050 (recurrence 8211→8210).
- juniper-data-client: `validate_npz_contract` (ndim-dispatched), `download_artifact_npz`.

**Cross-links:** [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
(A0/A1 design); [`JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md)
(§8.2 upstream gating). canopy #368 (model selection tracker).
