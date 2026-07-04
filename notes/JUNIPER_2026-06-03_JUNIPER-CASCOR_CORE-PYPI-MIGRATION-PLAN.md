# juniper-cascor-core — PyPI Extraction & Worker-Adoption Plan (CW-05)

**Project**: Juniper ML Research Platform
**Component**: juniper-cascor-core (new shared package) · juniper-cascor-worker · juniper-cascor
**Author**: Paul Calnon
**Date**: 2026-06-03
**Status**: **EXECUTED (2026-06-17)** — Wave 0 + Wave 1 shipped; the package is published as **`juniper-cascor-model` 0.1.0** on PyPI (renamed per the platform naming convention; home corrected to the **cascor family** per the [strategy doc](JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md), so the §3 "Home = `juniper-ml` subdirectory" row is **superseded**). Wave 2 (cascor self-adoption, retiring the drift-guard) is still deferred. See [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md).

---

## 1. Context

Issue [juniper-cascor#319](https://github.com/pcalnon/juniper-cascor/issues/319) ("dual-path remote candidate training stalls") was investigated across two sessions. The cascor-side defects are fixed:

- #1/#2 (remote-dispatch crashes) — [cascor#321](https://github.com/pcalnon/juniper-cascor/pull/321).
- #3/#4/#5 (collection budget, round-id isolation, idle-worker heartbeat dispatch) — [cascor#322](https://github.com/pcalnon/juniper-cascor/pull/322), verified end-to-end (`Collected 2/2 results from remote workers`).

**But the dual-path still does not work end-to-end**, because the true blocker is worker-side, filed as [juniper-cascor-worker#97 (CW-05)](https://github.com/pcalnon/juniper-cascor-worker/issues/97): **the `juniper-cascor-worker` container cannot execute a CasCor candidate** — it has no cascor codebase, no candidate-training deps, and several env mismatches.

A live **stopgap** (mount cascor `src/` + `--cascor-path`, `docker cp` PyYAML, `mkdir /logs`) proved two things:

1. **The cascor side is correct** — once the worker can load cascor code, tasks are delivered (#5) and collected (#3) within budget.
2. **The worker is fundamentally unprovisioned** — a *cascade* of gaps, each surfacing after the previous was patched (see §4). The worker's own error message already names the fix: *"CW-05 Approach A (juniper-cascor-core package) is the canonical long-term fix."*

This document plans that package.

## 2. Goal & scope

**Goal:** a working dual-path where remote workers actually train candidates and contribute to cascade growth.

**Ratified scope — Wave 0 + Wave 1:**

- **Wave 0** — create the `juniper-cascor-core` package (extract the candidate-training core from cascor src; make logging deployment-agnostic; publish workflow + drift-guard).
- **Wave 1** — the worker depends on `juniper-cascor-core`, drops the `--cascor-path` indirection, uses the shared activation registry, and the remote param-typing bug is fixed. **This unblocks #319 end-to-end.**
- **Wave 2 (deferred)** — cascor *itself* adopts the package (delete inline copies → single source of truth). Held behind a **drift-guard test** until scheduled (see §7).

## 3. The package

| Attribute | Decision |
|---|---|
| **Name (PyPI)** | `juniper-cascor-core` |
| **Home** | **SUPERSEDED 2026-06-09** — see [`JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md`](JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md) (D1/D2 ratified). The package relocates to the **cascor family** as a subdirectory of `juniper-cascor`, and is **renamed `juniper-cascor-model`**, before first publish. The interim `juniper-ml/juniper-cascor-core/` home and the `juniper-cascor-core` name are retired; every other mechanic in this plan still applies — only the home and distribution name change. |
| **Python** | `>=3.11` (worker floor) — note worker runs 3.14 in-container |
| **Runtime deps** | `torch`, `numpy`, `PyYAML` (+ optional `dill`, `columnar` behind an extra) |
| **Build** | setuptools, MIT, mirrors the other shared-package `pyproject.toml` |

**Extraction boundary (verified — ZERO coupling to server/training stack):**

| Module group | Files |
|---|---|
| candidate core | `candidate_unit/` |
| utils + activation | `utils/utils.py`, `utils/activation.py` |
| logging | `log_config/` (logger + log_config) |
| constants (candidate subset) | `cascor_constants/` — `constants_activation`, `constants_candidates`, `constants_logging`, candidate-relevant parts of `constants`, `constants_model`, `constants_hdf5` |

A full-tree trace from `candidate_unit/candidate_unit.py` found **no imports** of `cascade_correlation`, `api/`, `spiral_problem`, `snapshots`, `parallelism`, or FastAPI/uvicorn/websockets. The only cross-reference is a *comment* in `utils/activation.py:16`. Extraction risk is **LOW**.

### 3.1 Open sub-decision — import namespace

The extracted modules currently use **top-level** imports (`from candidate_unit.candidate_unit import ...`, `from cascor_constants.constants import ...`, `from utils...`, `from log_config...`).

- **Option (i) — ship top-level names as-is** (`candidate_unit`, `cascor_constants`, `utils`, `log_config`). Zero internal-import rewrites; the worker's existing `from candidate_unit.candidate_unit import CandidateUnit` resolves from the package with **no worker code change** beyond adding the dep. Cost: pollutes the global import namespace (unconventional vs `juniper_observability`-style packages); collision risk is low for these domain names.
- **Option (ii) — namespace under `juniper_cascor_core.*`**. Conventional/clean; requires rewriting every internal import in the extracted tree **and** the worker/cascor call sites. More work; better aligned with the eventual Wave-2 cascor adoption.

**Recommendation:** **(i) for Wave 0** (extract verbatim, lowest risk, fastest unblock); revisit (ii) when Wave 2 is scheduled. Flagged for ratification.

## 4. Gaps the package closes (each proven by the stopgap)

| # | Stopgap symptom | Root cause | Fix (wave) |
|---|---|---|---|
| 1 | `ModuleNotFoundError: candidate_unit` | worker has no cascor code | `pip install juniper-cascor-core` (W1) |
| 2 | `ModuleNotFoundError: yaml` | cascor logger needs PyYAML; worker image lacks it (no PyPI egress) | declared dep, installed transitively (W0/W1) |
| 3 | `/logs/juniper_cascor.log` ENOENT | log path hard-derived from `__file__` → `/logs`; **not env-overridable** | **add `JUNIPER_CASCOR_LOG_DIR` override + stderr/no-op fallback** in `log_config` (W0) |
| 4 | `Unknown activation 'Tanh' → sigmoid` | worker's `task_executor._get_activation_function` has its **own partial** map; cascor's `utils/activation.py:ACTIVATION_MAP` already supports `Tanh` | worker uses core's `ACTIVATION_MAP` (W1) |
| 5 | `'float' object cannot be interpreted as an integer` | `_dispatch_to_remote_workers` `float()`-coerces `random_max_value`/`sequence_max_value` (`cascade_correlation.py:~1193-94`); `candidate_unit` uses them in `random.randint`/`range` (`:345/:372`). Int locally → works; floated over the wire → worker fails | **stop coercing to float (keep int) in dispatch, or `int()` at the worker boundary** (W1) |

Gaps 3–5 are real bugs that the package/Wave-1 work fixes properly (vs the stopgap's container hacks).

## 5. Wave 0 — scaffold `juniper-cascor-core`

1. **Create `juniper-ml/juniper-cascor-core/`** mirroring `juniper-ci-tools/` layout: `pyproject.toml`, `README.md`, `CHANGELOG.md`, `LICENSE`, `tests/`, the extracted package tree, `_version.py`.
2. **Copy the §3 module set verbatim** from `juniper-cascor/src` (top-level names per §3.1(i)).
3. **Deployment-agnostic logging (gap #3):** add a `JUNIPER_CASCOR_LOG_DIR` env override to the log-path constant; when the dir is unset/unwritable, fall back to stderr-only (no file handler) instead of raising. Keep `JUNIPER_CASCOR_LOG_LEVEL` behavior.
4. **`pyproject.toml`:** deps `torch`, `numpy`, `PyYAML`; `[optional] full = [dill, columnar]`; classifiers 3.11–3.14; no console scripts (library).
5. **Publish workflow** `publish-cascor-core.yml` (tag `juniper-cascor-core-v*`, TestPyPI→PyPI OIDC) — clone of `publish-observability.yml`.
6. **Drift-guard test** (in juniper-ml `tests/`, dogfooded like `test_doc_tools_drift.py`): assert the extracted module set is byte-identical to `juniper-cascor/src` counterparts when the sibling repo is on disk (skips in CI when absent). Protects against Wave-2-deferral drift.
7. **Smoke test:** `from candidate_unit.candidate_unit import CandidateUnit; CandidateUnit(...).train_detailed(...)` on a tiny tensor — the exact path the worker exercises.

**Verify before first cron:** `gh workflow run publish-cascor-core.yml` (dry/TestPyPI) immediately after creation (per the "verify new CI workflows" rule).

## 6. Wave 1 — worker adopts `juniper-cascor-core`

1. **Add `juniper-cascor-core>=0.1.0` to `juniper-cascor-worker`** (`pyproject.toml` + lockfile).
2. **Delete the `--cascor-path` indirection** in `task_executor._get_candidate_unit_class()` — import `candidate_unit` directly (it's now a dep). Keep a clear error if the import fails.
3. **Activation (gap #4):** replace the worker's partial activation resolver with core's `ActivationWithDerivative.ACTIVATION_MAP`.
4. **Param typing (gap #5):** fix the float/int coercion — preferred: stop `float()`-coercing `random_max_value`/`sequence_max_value` in `cascade_correlation._dispatch_to_remote_workers` (they're int-valued); add `int()` defensively at the worker boundary. (This is a small cascor change — likely a follow-up to #322, or folded into the worker PR with an `int()` guard.)
5. **Logging:** set `JUNIPER_CASCOR_LOG_DIR` in the worker (compose) to a writable path, or rely on the stderr fallback.
6. **Rebuild the worker image** (no more cascor-src mount needed) and re-deploy.

**End-to-end verification (the #319 acceptance test):** on the juniper-deploy full stack (2 workers), run the repro — spiral, `max_hidden_units=3`, `candidate_pool_size=40`, `candidate_epochs=30`. **Success =** workers show `tasks_completed > 0`, cascor logs `TaskDistributor: All N remote tasks completed successfully` (not `Remote returned 0/2`), and the network grows past the local-only result. Read the **worker** logs, not just cascor (the #319 lesson).

## 7. Wave 2 — cascor adopts (DEFERRED)

cascor migrates its server/training code to import the candidate core from `juniper-cascor-core` and **deletes its inline copies** (single source of truth). This is the large, higher-risk step (many import sites across `cascade_correlation`, `api`, etc.) and is intentionally deferred.

**Until Wave 2:** the Wave-0 **drift-guard test** keeps the package and `juniper-cascor/src` byte-identical so the worker (package) and cascor server (src) never diverge — the only correctness risk of deferral. Trigger to schedule Wave 2: drift-guard friction, or a candidate_unit change that must land in both.

## 8. Risks & open decisions

- **Import namespace** (§3.1) — ratify (i) vs (ii). Recommend (i) for Wave 0.
- **`torch` dependency weight** — `juniper-cascor-core` pulls torch (multi-GB). Acceptable: the worker already has torch. Pin CPU wheel index in the worker image as today.
- **Param-typing fix location** (gap #5) — cascor dispatch (cleaner) vs worker boundary (`int()` guard). Recommend both: stop floating in dispatch *and* `int()` defensively in the worker.
- **Python floor** — worker runs 3.14; core declares `>=3.11`. Confirm torch/numpy wheels for 3.14 (already used in-container).
- **Drift-guard scope** — byte-identical vs AST-equivalent. Start byte-identical (simplest, like doc-tools/ci-tools).

## 9. Definition of done (Wave 0+1)

- `juniper-cascor-core` published to PyPI (TestPyPI-verified), drift-guard green.
- `juniper-cascor-worker` depends on it; no `--cascor-path`/mount; activation + param-typing + logging fixed.
- Live dual-path: network grows 0→3 with `All N remote tasks completed successfully` and `worker tasks_completed > 0`.
- juniper-cascor-worker#97 (CW-05) closed; juniper-cascor#319 closed.

## 10. Appendix — stopgap evidence (2026-06-03 deploy stack)

```text
# cascor side proven (#3 + #5):
22:14:17  Dispatching 2 tasks to remote workers (round 2d822113)
22:14:20  Collected 2/2 results from remote workers          # was 0/2 pre-#322

# worker-side gap cascade (each fix revealed the next):
ModuleNotFoundError: candidate_unit     -> mount src + --cascor-path
ModuleNotFoundError: yaml               -> docker cp PyYAML
[Errno 2] '/logs/juniper_cascor.log'    -> mkdir /logs
Unknown activation 'Tanh' -> sigmoid    -> (use core ACTIVATION_MAP)
'float' object ... integer              -> (stop float()-coercing int params)
```

Stopgap override (temporary, remove after Wave 1): `juniper-deploy/docker-compose.cw05-stopgap.yml`.
