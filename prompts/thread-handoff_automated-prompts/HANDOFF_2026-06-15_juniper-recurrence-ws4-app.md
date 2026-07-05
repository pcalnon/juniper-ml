# Handoff — juniper-recurrence WS-4: build the app on the proven template

**Date**: 2026-06-15
**Author**: Paul Calnon

> Paste the section below ("Continue …") as the initial prompt of a fresh thread.

---

Continue **WS-4 of the Juniper model/middleware refactor**: build out the `juniper-recurrence`
application now that the model template is proven. The arc — model-core interfaces + conformance
(published 0.1.0) → service-core scaffolding + lifecycle → the fixed-order LMU model passing the
conformance kit — is complete. Next is the runnable service, **starting with the recurrence app**.

## Verify starting state first

```bash
# All MERGED on juniper-ml main (4326dfd or later):
for n in 411 417 419 420 422; do gh pr view $n --repo pcalnon/juniper-ml --json title,state -q '.state+" "+.title'; done
# WS-4 LMU model — OPEN as of this handoff (merge before stacking the app on it):
gh pr view 1 --repo pcalnon/juniper-recurrence --json state,title
# Published deps:
curl -s https://pypi.org/pypi/juniper-model-core/json | python3 -c 'import sys,json;print("model-core",json.load(sys.stdin)["info"]["version"])'   # 0.1.0
curl -s -o /dev/null -w "service-core PyPI: %{http_code}\n" https://pypi.org/pypi/juniper-service-core/json                                       # 404 = NOT published yet
# Model passes the conformance kit (17 = 10 conformance + 7 grid-invariance):
cd /home/pcalnon/Development/python/Juniper/juniper-recurrence && pytest juniper-recurrence-model/tests/ -q
```

Read first: the WS-4 model-build plan (`juniper-ml/notes/`, merged as ml#424) and the design of
record `juniper-ml/notes/JUNIPER_2026-06-14_JUNIPER-RECURRENCE_MODEL-DETAILED-DESIGN.md`
(§6 integration; §0.5 C2 dual-mode; §6.8 deploy/ports/env). Refactor plan + WS register:
`juniper-ml/notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`.

## Completed (the session that produced this handoff)

WS-0 ratified (ml#411). `juniper-service-core` built: scaffold (ml#417), T1 security infra
(ml#419), service launcher (ml#420), and the **synchronous `TrainingLifecycleBase` body**
(ml#422) that drives any model-core `TrainableModel`. The stale juniper-ml `juniper-cascor-core`
home was retired (ml#410). `juniper-model-core` published to PyPI 0.1.0. **WS-4 model:
`FixedOrderLMURegressor(TrainableModel)` passes model-core's conformance kit 10/10**
(juniper-recurrence PR #1, OPEN) — a fixed LMU memory (C1-clean; A/B not learned) + a closed-form
least-squares readout (no BPTT, deterministic). This PROVES the template (RK-4): a Δt-native
sequence regressor satisfies the same interface as cascor's 2-D classifier.

## Next steps (in order — start with the app)

1. **Recurrence app.** Build at the `juniper-recurrence` repo (alongside `juniper-recurrence-model/`,
   mirroring cascor's `src/` app + model subdir). A FastAPI service via service-core's `create_app`
   + a lifecycle (the synchronous `TrainingLifecycle`, or a `RecurrentLifecycle` subclass) driving
   `FixedOrderLMURegressor`; generic `/v1/health`; security middleware. A standalone CLI `main.py`
   (dual-mode **C2**). `Settings(SettingsBase)` with env prefix `JUNIPER_RECURRENCE_`. Ports: host
   **8211** → container **8210** (OQ-15/18).
2. **Publish prerequisite (gates the app's CI/deploy).** The app depends on `juniper-service-core`,
   which is **not on PyPI yet**. Publish it (Paul's admin: trusted-publisher pending-publisher +
   tag `juniper-service-core-v0.1.0` + approve the dual gate), or cross-repo editable-install for
   dev. Note service-core itself depends on the now-published `juniper-model-core` (publish-first
   order already satisfied).
3. **`juniper-recurrence-client`** — the HTTP client library.
4. **Wire the 3-D NPZ data** — consume `equities_seq` via `juniper-data-client` into model training
   (the 3-D `(W, L, F)` + `dt`/`target_dt` contract is shipped).
5. **Canopy generalization (WS-5)** — model-agnostic UI via `describe_topology()` + regression metrics.
6. **Optional model-core 0.2.0 refinement (RK-4 finding):** model-core's `predict(self, X)` lacks the
   `**kw` that `fit` has (D3), so a Δt-native model can't receive `dt` at predict through the bare
   contract. The model works around it with an optional `predict(X, dt=)`; a 0.2.0 could mirror
   `fit`'s `**kw` on `predict` so it is contractual.

## Key context

- **Do not touch `juniper-cascor`** — cascor adoption of the shared packages is **WS-6**,
  trigger-gated. Build recurrence greenfield; the template is proven without touching production.
- **Patterns to reuse:** keep each package's top-level `__init__` **dependency-free** (lazy PEP 562
  `__getattr__`) so the `--no-deps` TestPyPI publish-verify works; a publish workflow must **not**
  combine `--no-deps` with `--extra-index-url` (lint: juniper-ml `tests/test_workflow_script_paths.py`);
  when porting cascor code, de-cascor by replacing `get_settings()`-based singletons with
  config-injected factories and `cascor_constants.*` with local module constants; for an
  in-monorepo sibling dependency, CI installs the sibling **editable first**.
- **Conventions:** end commit messages with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`;
  end PR bodies with the Claude Code attribution; commit/push/PR **only when asked**; verify a merge
  via `gh pr view <N>` (state=MERGED), not just a "merged" message; new `util/` scripts go under
  `util/ad-hoc/` (never `/tmp/`); use git worktrees for task isolation.

## Git / PR status

- juniper-ml `main` @ `4326dfd` (clean). All session PRs merged.
- juniper-recurrence: branch `feat/lmu-trainable-model` pushed; **PR #1 OPEN**; `main` @ `d2b5588`
  (PR #1 not yet merged — merge it, then base the app branch on the updated main).
- Active worktree: `juniper-ml/.claude/worktrees/validated-herding-pretzel`.
