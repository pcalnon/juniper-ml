# Thread Handoff — WS-4 (juniper-recurrence) + the model/middleware refactor publish chain

**Date:** 2026-06-15
**Purpose:** Initial prompt for a fresh thread continuing the Juniper model/middleware refactor.
**Prior thread:** juniper-model-core (WS-3) scaffold → PyPI 0.1.0 → extras (#416/#418), then re-validated ecosystem state against PyPI + `main` after significant concurrent-session work (WS-2 + WS-4a + build-provenance).

---

Continue the Juniper model/middleware refactor — **WS-4 (juniper-recurrence)** + the publish/extras chain. Design-first; lead with a proposal, not a scaffold.

## Completed (verified on PyPI + `main`, 2026-06-15)

- **WS-0** ratified (#411); **WS-1** data foundation shipped (3-D NPZ + Δt + `equities_seq`).
- **WS-3 `juniper-model-core`:** COMPLETE, **PyPI 0.1.0**, wired into juniper-ml `[tools]`/`[all]` (#416/#418).
- **WS-2 `juniper-service-core`:** `settings`/`app` (`create_app`)/`health`/`security`/`secrets`/`middleware`/`launcher`/`lifecycle` (**`TrainingLifecycle` body**) merged to `main` (#417/#419/#420/#422); **v0.1.0 ready — NOT published, NOT in extras.**
- **WS-4a:** `FixedOrderLMURegressor(TrainableModel)` (readout-only `lstsq`, no BPTT, C1-clean) passes model-core conformance **10/10** → **juniper-recurrence PR #1** (`mergeStateStatus: CLEAN`, CI green, **NOT merged**). Proves RK-4 (the 2nd real implementer of the model-core contract).
- `cascor-core` relocated out of juniper-ml (#410). Parallel build-provenance effort: `juniper-observability 0.4.0` published.

## Remaining (critical path, re-prioritized)

1. **Merge juniper-recurrence PR #1** (WS-4a model) — `CLEAN`, ready.
2. **Publish `juniper-service-core` 0.1.0** (its `juniper-model-core>=0.1.0` dep is already on PyPI → publish-first satisfied) → follow-up PR adding it to juniper-ml `[tools]`/`[all]` + `test_pyproject_extras.py` (mirror model-core #418). *Gate: Paul sets the PyPI pending-publisher.*
3. **Publish `juniper-recurrence-model` 0.1.0** (after PR #1 merges; pending-publisher gate).
4. **WS-4b — the recurrence APP:** FastAPI via service-core `create_app` + `TrainingLifecycle` + CLI `main.py` (dual-mode, C2), `Settings(SettingsBase)` env prefix `JUNIPER_RECURRENCE_`, port host **8211** → ctr **8210**; wire the 3-D NPZ data path via `juniper-data-client` (`equities_seq`). **Write a WS-4 *app* build-plan first** — `notes/JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md` (#424) covers the *model* only.
5. **WS-4c — `juniper-recurrence-client`** (HTTP/WS, mirror `juniper-cascor-client`).
6. **`juniper-model-core` 0.2.0** — add `**kw` to `predict()` (D3 symmetry) so sequence models are Δt-native at inference *through the contract*; removes the LMU `predict(X, dt=)` workaround, then bump consumers.

**Deferred / gated:** WS-5 canopy generalization; WS-6 cascor adoption (trigger-gated; cascor untouched); WS-8 service-core websocket/worker subsystem (OQ-11).

## Key context

- **INTERFACE GAP (RK-4 finding):** model-core `predict(X)` lacks `fit`'s `**kw` (decision D3) — a Δt-native model can't receive `dt` at inference through the bare contract. WS-4a worked around it with an optional, LSP-safe `predict(X, dt=None, readout_mask=None)`. Item 6 (the 0.2.0 refinement) closes it properly. This is the canonical example of the 2nd implementer surfacing an interface gap — exactly why recurrence is built greenfield (RK-4).
- **PUBLISH-FIRST is binding:** no consumer pins `service-core`/`recurrence-model` until they are on PyPI (docker can't build from sibling source). The `pyproject` pin-bump and `requirements.lock` regen must land in the **same PR** (else build-green/runtime-red). New shared packages take a TestPyPI soak before any docker lock pins them.
- **Concurrent sessions are active** (WS-2, WS-4a, and the build-provenance arc were done by session `e97c90e2…`). Before touching shared CI/extras files or assuming a red PR is yours: `gh pr list` per repo, and confirm `gh run list --branch main` is green first.
- **Worktree procedure:** all task work in centralized worktrees off updated `main`; publish-first + same-PR pin-and-lock; verify each new CI workflow with `gh workflow run` immediately (RK-10).
- **Design of record:** `notes/JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`, `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`, `notes/JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`.

## Verify starting state

```bash
# WS-4a model PR — should be OPEN + CLEAN until merged
gh pr view 1 -R pcalnon/juniper-recurrence --json state,mergeStateStatus,statusCheckRollup

# PyPI availability — model-core 200; service-core + recurrence-model 404 until published
for p in juniper-model-core juniper-service-core juniper-recurrence-model; do
  curl -s -o /dev/null -w "%{http_code}  $p\n" https://pypi.org/pypi/$p/json
done

# juniper-ml main now has juniper-service-core/ + model-core in [tools]
cd <PATH>/juniper-ml && git checkout main && git pull origin main
git show HEAD:pyproject.toml | grep -E 'model-core|service-core'

# recurrence repo state
cd <PATH>/juniper-recurrence && git fetch && git log --oneline -3 origin/main && gh pr list
```

## Git status

- **juniper-ml:** `main` is current through **#424**. The prior session's worktree is on the stale merged branch `feature/juniper-model-core-extras` — **start fresh off updated `main`** per the worktree procedure (it does not contain `juniper-service-core/`).
- **juniper-recurrence:** `main` (commit `d2b5588`) + open **PR #1** (`feat/lmu-trainable-model`, WS-4a model). Nothing uncommitted that matters.

## Suggested first move

Start with the cheap, unblocking sequence (1 → 2 → 3): merge PR #1, then drive the `service-core` + `recurrence-model` publishes and the `service-core` extras follow-up. In parallel, propose the **WS-4b app** design (it is the next substantial build and the first real consumer of `service-core`'s `create_app` + `TrainingLifecycle`). Treat item 6 (model-core 0.2.0 `predict(**kw)`) as a low-risk cleanup to fold in when convenient.
