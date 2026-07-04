# Juniper-Canopy — Regression Audit, Model-Selection Design & UI Regression Harness — WORKING PLAN

**Project**: juniper-canopy (subject of audit) / juniper-ml (doc home)
**Author**: Paul Calnon
**License**: MIT License
**Status**: Approved execution plan — implementation in progress
**Last Updated**: 2026-06-15
**Plan file (ephemeral)**: `/home/pcalnon/.claude/plans/atomic-painting-phoenix.md`

> **⚠️ STATUS UPDATE (2026-06-17): SUPERSEDED execution framing.** This plan's "in
> progress" state is stale — the entire iteration merged 2026-06-16 (canopy `#364`
> harness, `#366` wired **all three** orphan controls, juniper-ml `#430` docs/papers).
> Current state + go-forward roadmap:
> [`JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md).
>
> This is the durable, version-controlled copy of the **approved execution plan**.
> It guides the build of the automated UI-regression harness, the trivially-scoped
> dead-control fixes, and the model-selection design. It is **distinct from — and
> will be superseded by — the richer, evidence-backed deliverable** produced after
> the empirical phase, `JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`
> (created during execution).

---

## Context — why this work

`juniper-canopy` (the Dash/FastAPI research dashboard, v0.5.0) is the web front-end for the Juniper platform. Two pressures converge:

1. **Enhancement (forward-looking):** a new `juniper-recurrence` model (LMU, time-series / irregular-Δt) is being built and must be integrable from canopy. Today canopy lets you pick a **dataset** but has **no user-facing way to pick a model**, and has **zero `task_type` awareness** (verified by grep). Some dataset×model combinations are intrinsically incompatible (a time-series dataset cannot train CasCor; a 2-D classification dataset cannot train the recurrence model). We need model selection with **bidirectional compatibility gating** (greyed-out options + tooltips + toasts, both directions).

2. **Regressions (highest-priority blocker):** canopy has persistent, fix-resistant, user-facing dead-control regressions clustered around dataset configuration / modification / selection / application. These defeat the app's research purpose. Reconnaissance already **empirically confirmed** one: `restart-with-new-dataset-button` (`dashboard_manager.py:1409`) has **no** callback `Input`/`State`/`Output` binding anywhere in `src/` — clicking "Stop & Restart with new dataset" does nothing. The team already calls this the **"dead button" class** (`notes/CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md`). There is no automated net that catches it — so it keeps recurring.

**Intended outcome:** one authoritative audit/design/planning document (empirically validated, anti-hallucination), **plus** a real automated harness that exercises every canopy control and auto-extends to future controls, **plus** opportunistic fixes for trivially-scoped dead controls.

## Decisions (confirmed with user)

- **Deliverable doc → `juniper-ml/notes/`** (ecosystem hub, beside the `JUNIPER_RECURRENCE_*` corpus). Harness code + fixes → `juniper-canopy`.
- **Scope this iteration → doc + automated harness + fix only trivially-scoped proven dead controls.** Substantial regression fixes and the **model-selection feature implementation** each become their own follow-up PRs. The harness/infrastructure is built now.
- **Validation:** multiple independent sub-agents + empirical POCs; every internal claim carries `file:line`; every external citation retrieved into `juniper-ml/papers/` with a specific URL.

## Key verified facts (grounding)

- App entry `src/main.py:305-394` (FastAPI + Dash at `/dashboard`). Orchestrator `src/frontend/dashboard_manager.py`; callbacks in `_setup_callbacks()` (`:1896-1907`) + per-component `register_callbacks(app)`.
- Dataset-type options are **hardcoded inline** at `dashboard_manager.py:1114-1120` (Spirals/XOR/MNIST/Circles/Moons) — not from a constant.
- Endpoint contract (handlers in `src/main.py`): `POST /api/set_params` (`:2878`), `/api/train/{start,stop,pause,resume,reset}` (`:2748-2807`), `/api/stage_dataset` (`:3041`, body `StageDatasetRequest` `:3025-3038`), `/api/cancel_pending_dataset` (`:3064`), `/api/live_dataset_swap` (`:3154` POST / `:3185` DELETE); `GET /api/state` (`:916`), `/api/status`. WS `/ws/control` needs CSRF first-frame.
- **Test infra:** Playwright suite `src/tests/ui/` (~9 tests) runs isolated via `make test-ui` (event-loop-leak → `--ignore=src/tests/ui` in default addopts); CI job `ui-tests` `.github/workflows/ci.yml:293-355`. **Known wall:** Playwright can't drive `dbc.Input(type=number)` (React `onChange` never fires → `State=null`); `test_apply_button_flow.py` is `xfail(strict=True)`. Numeric inputs debounce 350 ms (`DashboardConstants.NUMERIC_INPUT_DEBOUNCE_MS`). 56 in-process `TestClient` integration tests already POST endpoints + assert `/api/state`.
- **Versions:** dash 4.1.0 (installed) / 4.2.0 (lock — **stale**), dbc 2.0.4, plotly 6.7.0/6.8.0. `dcc.Dropdown` supports per-option `disabled` but **not** `title`; `dbc.Select` supports both. selenium/playwright present in env **`JuniperCanopy1`** (the live env; legacy `JuniperCanopy` is now `JuniperCanopy-DEPRECATED`).
- `juniper-ml/papers/` exists (external-literature home). Canopy has none.
- Running `canopy:8050`/`cascor:8201` are almost certainly the **juniper-deploy Docker stack** (possibly stale image) — reproduce against **local `./demo`** for determinism, cross-check the live stack.

---

## Approach

### Part 1 — Empirical regression audit (evidence base for the doc)

1. Run canopy locally: `JuniperCanopy1` env, `./demo` on a free port (don't trust the Docker `:8050`).
2. **Static sweep (deterministic):** build the L1 control-graph lint (Part 3 L1) and run it across the whole app to enumerate **every** orphan/unbound actionable control — not just the one already found. This is the empirical discovery engine for the dead-button class.
3. **Live repro:** drive the real dashboard with the browser MCP (chrome-devtools / playwright MCP) — click each suspect control, capture screenshot + console + `/api/*` network traffic — to demonstrate (not assert) each regression. Artifacts saved under canopy `util/ad-hoc/` and `images/` (**never `/tmp/`** — script-placement rule).
4. Triage every confirmed regression into **trivial-fix-now** vs **defer-to-own-PR**, with root cause at `file:line`.
5. Align taxonomy with the existing `notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (Issues #1–#6) and the `CANOPY_TRAINING_CONTROL_ERROR_SURFACING` doc — the new audit **supersedes/extends**, does not duplicate.

### Part 2 — Model selection + bidirectional compat-gating (DESIGN ONLY this iteration; impl = follow-up PR)

Full design captured in the doc; implementation deferred per scope.

- **Registry** `src/model_registry.py`: `ModelSpec{key,label,supported_task_types,input_ndim,is_live,gated_reason}` + `DatasetTypeSpec{value,label,task_type,ndim}` + `models_for_dataset()` / `dataset_values_for_model()`. Seed: `cascor` (live, ndim={2}, {classification,regression}); `recurrence` (gated, ndim={3}, {time_series,irregular_dt}, "coming soon"). Registry also becomes the single source for the dataset-type options currently hardcoded at `dashboard_manager.py:1114-1120`. Ties into the juniper-data `task_type` + 3-D NPZ contract (WS-1).
- **Selector:** `dcc.Dropdown id="nn-model-dropdown"` inserted at `dashboard_manager.py:1111` (above the dataset-type dropdown, same idiom), wrapped in `html.Div(id="nn-model-wrapper")`.
- **Bidirectional gating:** two callbacks recompute `options` (flip per-option `disabled`): model→dataset and dataset→model, intersecting with `is_live`. Violation → toast via `dbc.Alert(duration, dismissable=True)` in a fixed Div (`top:13rem` to clear the existing outcome surfaces at 5rem/9rem). Also `Output(..., "value")` to snap to the first compatible option when the current one gets gated.
- **Accessibility (cited):** disabled controls fire neither hover nor focus, so a tooltip on a disabled option never shows → **wrapper-targeted `dbc.Tooltip`** (recomputed text); for the "coming-soon" recurrence model use **soft-gate** (selectable + toast + revert value) so users discover it; hard-disable only genuine task-type incompatibilities.
- **Backend mirror (mandatory):** add `nn_model` to `StageDatasetRequest`/`SetParamsRequest`, thread through `demo_mode.py` + `demo_backend.py`, reject `recurrence` with a clean error until the service exists.

### Part 3 — Automated UI regression-detection harness (BUILT this iteration)

Three complementary layers. **L1+L2 are the deterministic, zero-browser, auto-extending core (≈90% of value); L3 is a thin real-browser click-proof set.**

- **L1 — Static control-graph lint (no browser, default test suite).**
  - `util/ui_control_graph.py`: instantiate `DashboardManager({}).app` (cheap in demo mode), walk the realized layout tree (`.children`) to enumerate control ids+types, and walk `app.callback_map` for Input/State/Output ids (same private surface the existing `test_apply_blur_clientside.py` already uses).
  - Rule: every **actionable** control id appears in ≥1 callback **Input or State**, bifurcated — buttons/uploads/switches/radios require an **Input** (a button read only as State can never fire); value-carriers (Dropdown/Select/Input-number) allow Input **or** State (e.g. `nn-dataset-type-dropdown` is State-only by design, `:3514`). Handle pattern-matching dict ids by `type`-key normalization.
  - Gate: `src/tests/unit/test_control_graph_lint.py` (`@pytest.mark.unit`, default suite, no deps) asserts `lint(app) == []` with a deterministic orphan-control message. **This would have caught `restart-with-new-dataset-button` instantly.**
  - Self-validation meta-test: every `actionable=True` manifest control is found by the enumerator and vice-versa (or explicitly `xfail`-listed with a reason).
- **L2 — API/callback behavioral coverage (in-process `TestClient`, default suite).**
  - `src/tests/ui_contract/control_manifest.py`: list of `ControlContract{control_id,kind,endpoint,request_builder,expected_state_key,expected_state_value,http_ok,browser_proof,selector,actionable,binding}`.
  - `src/tests/integration/test_control_manifest_behavioral.py` parametrizes over manifest entries with an `endpoint`, calls it via `TestClient(app)`, polls `/api/state`/`/api/status`, asserts expectations. Reuses the dominant existing integration pattern.
  - **Future-proofing:** adding a `ControlContract` row auto-enrolls a control into L1 (binding check), L2 (behavioral), and optionally L3 (`browser_proof=True`).
- **L3 — Real-browser interaction proof (thin, isolated).** Resolve the Playwright wall via POC, **time-boxed, in this order**:
  - **POC #2 first (cheap):** corrected Playwright native-value-setter — `HTMLInputElement.prototype` value setter + **bubbling** `input`+`change` events + `blur`, waiting out the 350 ms debounce. Un-xfail `test_apply_button_flow.py`; gate = set `nn-learning-rate-input`, wait 500 ms, click Apply, `GET /api/state` shows the value within 10 s. **PASS → keep Playwright**, generalize into a `set_dash_number(page,id,value)` conftest fixture. **FAIL → POC #1.**
  - **POC #1 (fallback):** `dash.testing`/`dash_duo` (Selenium ≤4.2.0 + chromedriver) for numeric-input proofs only, in its own `make test-ui-dash` invocation; keep the 9 existing Playwright tests.
  - L3 scope = `browser_proof=True` subset (one numeric roundtrip, one dropdown, one button→DOM, the model-gating proof) — **not** a full per-control sweep.
- **CI wiring:** L1+L2 ride the existing `unit-tests`/`integration` jobs (no new deps, gate every PR). L3 stays in the existing `ui-tests` job; selenium/Chrome added only on the POC-#2-FAIL branch.

### Part 4 — Fix trivially-scoped dead controls (scope-approved)

- Run the L1 sweep, triage. Fix **only** small, self-contained, proven cases; each gets a regression test (and is then permanently guarded by L1/L2).
- Lead candidate: **wire `restart-with-new-dataset-button`** to the cold-swap restart path (confirm exact semantics first — likely stop/reset → start consuming the staged `pending_dataset`; FRONTEND_ISSUES_PLAN §3 designed the cold-swap but left this button unwired). **If it proves non-trivial, it defers** to its own PR per scope.

### Part 5 — Validation engine (anti-hallucination; independent sub-agents + POCs)

A dedicated validation phase before finalizing the doc:
- **Source-ref verifiers** — independent agents re-open every `file:line` cited and confirm the symbol/line still matches.
- **Empirical/POC verifiers** — every regression claim must have a runnable artifact (a failing L1/L2 test, or a repro script in canopy `util/ad-hoc/`) that an independent agent executes and confirms.
- **External-ref verifiers** — every external citation retrieved into `juniper-ml/papers/` (PDF/HTML snapshot where licensing permits, else URL + accessed-date) and the specific URL/section re-resolved by an independent agent.
- **Completeness critic** — an agent that hunts for unverified/contradicted claims; its findings become a fix list.
- Default engine = Agent-tool sub-agents (satisfies "multiple independent sub-agents"). Can escalate to a formal multi-agent **Workflow** (fan-out → adversarial multi-vote verify → synthesize) on request.

### Part 6 — External literature (into `juniper-ml/papers/`, with URLs)

Targeted, validated retrieval: NN/g on disabled buttons; WAI-ARIA Authoring Practices (tooltips + `aria-disabled` vs `disabled`); Dash testing docs (`dash.testing`/`dash_duo`) + the React controlled-input `onChange` behavior. Cross-link (don't re-retrieve) the recurrence/LMU + `task_type`/WS-1 corpus already in `juniper-ml/notes/`.

---

## Deliverable document

`juniper-ml/notes/JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`, sections:
1. Context & motivation (recurrence integration + blocker regressions)
2. Current-state audit (architecture, control-surface inventory w/ `file:line`, dead-button taxonomy, Docker-image caveat)
3. Empirically-validated regression catalog (per item: repro artifact, root cause `file:line`, severity, fix-now vs defer)
4. Enhancement design — model selection + bidirectional compat-gating (registry, `task_type` matrix, Dash mechanics, accessibility, backend mirror)
5. Automated regression-detection harness (L1/L2/L3 architecture, manifest, CI, future-proofing)
6. Validation methodology + evidence appendix (how every claim was verified)
7. Execution plan / PR breakdown (now vs deferred)
8. References (external lit in `papers/` + URLs; cross-links to recurrence corpus)

## Critical files

**Canopy — add:** `util/ui_control_graph.py`; `src/tests/unit/test_control_graph_lint.py`; `src/tests/ui_contract/control_manifest.py`; `src/tests/integration/test_control_manifest_behavioral.py`; `src/tests/ui/test_model_gating.py`; (design-only, follow-up PR) `src/model_registry.py`.
**Canopy — modify:** `src/tests/ui/conftest.py` (+`set_dash_number` fixture), `src/tests/ui/test_apply_button_flow.py` (un-xfail on POC-#2 pass), `.github/workflows/ci.yml` (only on dash[testing] fallback), `requirements.lock` (reconcile stale dash/plotly/starlette); for the fix: `dashboard_manager.py` (wire orphan button + its test). Feature (deferred): `dashboard_manager.py:1111/1114-1120/1896-1907`, `src/main.py:2831/3025-3038`, `src/demo_mode.py`, `src/backend/demo_backend.py`.
**juniper-ml — add:** the deliverable doc; retrieved papers under `papers/`.

## Worktrees (cross-repo, centralized per convention)

- `juniper-canopy` worktree, branch `test/ui-regression-harness` (harness) + a separate `fix/orphan-dataset-restart-button` for the fix (keep defect PR separate).
- `juniper-ml` worktree, branch `docs/canopy-audit-recurrence-integration` (doc + papers).

## Verification (end-to-end)

- **L1:** `cd src && pytest tests/unit/test_control_graph_lint.py -v` → fails on `main` listing `restart-with-new-dataset-button`; passes after the fix.
- **L2:** `cd src && pytest tests/integration/test_control_manifest_behavioral.py -v` (in-process, demo mode).
- **L3 POC #2:** `make test-ui` with un-xfail'd `test_apply_button_flow.py`; PASS ⇒ Playwright stays primary.
- **Live repro:** `./demo`, then browser MCP click-through of dataset controls capturing console/network/screenshot; confirm the orphan button does nothing pre-fix and works post-fix.
- **Default suite green:** `cd src && pytest -m "unit or integration" -q` (L1+L2 included, UI ignored).
- **Doc validation:** independent agents re-confirm every `file:line` + run every POC + re-resolve every external URL; completeness critic finds residual unverified claims.

## POCs / open items to resolve in execution

1. **POC #2** corrected Playwright native-value-setter (do first; cheap; un-xfail gate).
2. **POC #1** `dash.testing`/`dash_duo` numeric-input drive (only if #2 fails; needs selenium+chromedriver).
3. Confirm `app.callback_map` / layout `.children` traversal shape on dash 4.1.0 (likely stable — existing tests already depend on it).
4. Confirm cold-swap restart semantics before wiring the orphan button (else defer).
5. Reconcile `requirements.lock` (dash 4.2.0→4.1.0, plotly, starlette) so CI pins what it runs.
6. Active canopy env confirmed: **`JuniperCanopy1`** (AGENTS.md still says `JuniperCanopy`; that env is now `-DEPRECATED`).

## Risks

- L3 browser flake / Playwright wall — mitigated by leaning on deterministic L1+L2 and time-boxing the POC.
- Orphan-button fix may prove non-trivial (cold-swap semantics) — then it defers, per scope.
- `requirements.lock` drift could mask a CI-vs-local capability gap — reconcile early.
- Cross-repo PR ordering (canopy harness lands independently; ml doc references it) — sequence so the doc cites merged or in-flight PRs honestly.
