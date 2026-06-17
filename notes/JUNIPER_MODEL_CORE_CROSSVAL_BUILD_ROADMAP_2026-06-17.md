# juniper-model-core — Cross-Validation / Fold-Executor Layer: State Evaluation & Build Roadmap

**Project**: juniper-ml — `juniper-model-core` shared model-contract package
**Repository**: pcalnon/juniper-ml (package subdir `juniper-model-core/`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (RATIFIED — §10 decisions D1–D5 concurred by Paul 2026-06-17; Phase 1 / PR-1 unblocked)
**Last Updated**: 2026-06-17

---

> **What this is.** A source-validated evaluation of where the cross-validation / fold-executor
> layer actually stands, followed by a prioritized design / development / testing roadmap. It
> consumes the ratified design ([`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md)),
> the contract spec ([`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md)),
> and the WS-4b deferral ([`JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md)),
> then checks every load-bearing claim against the **as-built** source in
> `juniper-model-core/`, `juniper-data/`, and `juniper-recurrence/`. Headline result: the
> crossval layer is **design-only (0% implemented)**, the design is **substantially accurate**,
> and the validation surfaced **one critical sequencing defect** in the ratified plan plus six
> lower-severity refinements that change how PR-1 should be built. Claims were cross-checked
> by four independent sub-agents this session — model-core source accuracy, the cross-repo facts
> plus the F-CRIT-1 lint contradiction, internal consistency vs. the ratified decisions, and
> markdown lint — with their findings folded into this revision (§Appendix B).

---

## 1. Method & scope

This evaluation was produced in the `worktree-keen-spinning-locket` worktree of `juniper-ml`
(branch clean at start). It reconciles the three design documents against source by reading,
in full or in relevant part:

- **model-core (as-built, 0.1.0):** `juniper_model_core/{__init__,_version,interfaces,events,topology,validation,serialization,lifecycle}.py`, the whole `conformance/` subpackage, all four `tests/*.py`, `pyproject.toml`, `CHANGELOG.md`.
- **juniper-ml packaging/lints:** `pyproject.toml` extras, `tests/test_pyproject_extras.py`, `tests/test_model_core_drift.py`, `.github/workflows/ci-model-core.yml`, `publish-model-core.yml`.
- **Cross-repo anchors:** `juniper-data/juniper_data/core/split.py`, `juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/model.py` + its `pyproject.toml`.

Evidence is cited as `file:line` throughout and consolidated in [Appendix A](#appendix-a--source-evidence-ledger). Severity tags: **CRIT** (changes the plan), **REFINE** (sharpens it), **CONFIRM** (design matches reality).

---

## 2. Current-state verification (design claim vs. as-built source)

| # | Design claim (source doc) | As-built evidence | Verdict |
|---|---|---|---|
| 1 | No CV / fold / walk-forward logic anywhere; every model single-fit | Ecosystem grep for `crossval` is clean; no `crossval/` submodule, no `[crossval]` extra | **CONFIRM** |
| 2 | `juniper-data` ships only a single chronological cut; walk-forward deferred | `split.py:116` `temporal_split_index(n_samples, train_ratio) -> int`; deferral note `split.py:136-139` ("WS-1 / juniper-data#168 scope C … intentionally not implemented yet") | **CONFIRM** |
| 3 | model-core 0.1.0 has the per-fold *step* + `validate_metrics` + `REGRESSION_METRIC_KEYS`, but **no executor, no `reset()`/`clone()`, no `score()`** | per-fold step `conformance/suite.py:51-52`; `validation.py:42,35`; `TrainableModel` surface `interfaces.py:78-142` has exactly `fit/predict/metrics/describe_topology/input_shape/output_shape` — no reset/clone/score | **CONFIRM** |
| 4 | recurrence `LMURegressor` **is** a `TrainableModel` (drivable now) | `model.py:51` `class LMURegressor(TrainableModel)`; widened `predict` `model.py:169`; deps `juniper-model-core>=0.1.0,<0.2.0` (recurrence-model `pyproject.toml:31-33`) | **CONFIRM** |
| 5 | cascor `network.fit()` not yet a `TrainableModel` (WS-6) | Out of scope for this layer; not re-verified here (no cascor checkout in worktree) | **UNCHECKED** |
| 6 | Current model-core version 0.1.0, dependency-free core import | `_version.py:3` `"0.1.0"`; `pyproject.toml:32` `dependencies = []`; guard `tests/test_dependency_free_import.py` | **CONFIRM** |

**Bottom line:** the crossval design is faithful to the as-built contract. The layer does not
exist in code — only the ratified design doc (#431) and this roadmap. Implementation is at
**0%**. The `CHANGELOG.md` `[Unreleased]` section is empty (`CHANGELOG.md:8`); no 0.2.0 work is staged.

---

## 3. Findings that change or sharpen the plan

### F-CRIT-1 — The 0.2.0 version bump breaks two juniper-ml lints unless the `[tools]` pin is widened in the *same* PR

The ratified design says the `[tools]` pin-widen is a **separate follow-up** and PR-1 is
"self-contained; no consumer changes" (crossval design §5, §7). **The as-built lints make that
impossible:**

- `test_model_core_drift.py:116-139` reads the in-development version from `_version.py` and asserts `current_version < [tools]_pin_upper`. With `_version.py = "0.2.0"` and the `[tools]` pin `juniper-model-core>=0.1.0,<0.2.0`, the assertion `(0,2,0) < (0,2,0)` is **False → test fails** (`test_model_core_drift.py:135-139`).
- `test_pyproject_extras.py:38-65` hardcodes the exact string `"juniper-model-core>=0.1.0,<0.2.0"` in `EXPECTED_EXTRAS["tools"]` (`:55`) and asserts exact member-set equality (`:89-96`). Widening the pin without editing this table **fails the lint**; not widening it leaves F-CRIT-1's drift failure.

Both lints run as a **required CI gate** — `ci.yml`'s `tests` job invokes both `test_model_core_drift.py` and `test_pyproject_extras.py`, and `required-checks` fails the PR when `tests` is not green (independently re-derived — Appendix B, Validator 2). The instant
`_version.py` becomes `0.2.0`, the only green state is: **bump `_version.py`, widen the `[tools]`
pin to `<0.3.0`, and update `EXPECTED_EXTRAS["tools"]` — all in PR-1.** This is exactly what RK-11
("never split shared-CI/extras edits") prescribes, so the fix aligns the plan with an existing
standing rule. `[all]` needs **no** edit (it is the recursive ref `juniper-ml[clients,worker,servers,tools]`, `test_pyproject_extras.py:62-64`).

**Asymmetry that matters:** the *external* recurrence-model pin (`<0.2.0`) is **not** lint-coupled
to model-core's `_version.py` and must be **left alone** — it correctly keeps resolving 0.1.x until
recurrence itself adopts crossval (crossval design §5 is right about external consumers, only wrong
about the juniper-ml `[tools]` pin). See [OPT-E](#opt-e--pr-sequencing--versionpin-handling-decision).

**Every in-repo reference to `juniper-model-core`, and what the in-development 0.2.0 does to each** (independently swept — Appendix B, Validator 2):

| Reference | Pin / form | Effect of in-dev 0.2.0 | Action in PR-1 |
|---|---|---|---|
| juniper-ml `[tools]` extra (`pyproject.toml:55`) | `>=0.1.0,<0.2.0` | **Breaks** both lints | Widen to `<0.3.0` + update `EXPECTED_EXTRAS["tools"]` |
| `juniper-service-core/pyproject.toml:32` (in-repo sibling consumer) | `>=0.1.0` (open ceiling) | Safe — no upper bound; the drift lint scans only `[tools]` | None |
| `publish-model-core.yml:105` verify install | `==${version}` (templated) | Safe — auto-tracks the release tag | None |
| recurrence-model `pyproject.toml:33` (external repo) | `>=0.1.0,<0.2.0` | Not lint-coupled here; keeps resolving 0.1.x | Leave alone (recurrence bumps it in Phase 3) |

**Edit-time foot-gun (Validator 2):** widen the `[tools]` pin **surgically**, never via a global
find-replace — `test_model_core_drift.py:190` is a negative-control unit test asserting the
*literal* `"juniper-model-core>=0.1.0,<0.2.0"` parses to `("0.1.0","0.2.0")`, so a blanket sed of
that string would silently break it. (The drift lint also asserts exactly one `[tools]` pin —
`test_model_core_drift.py:123-127`.)

### F-REFINE-2 — The proposed `crossval/metrics.py` duplicates an existing private implementation

`conformance/reference.py:37-44` already defines `_regression_metrics(y_true, y_pred)` returning
`{mse, rmse, mae, r2, loss}` with `loss == mse` — byte-for-byte the contract the design proposes
for `crossval/metrics.py:regression_metrics` (crossval design §4). Shipping a second copy invites
silent drift between the held-out scorer and the kit's reference scorer. See
[OPT-A](#opt-a--where-the-regression-metric-math-lives-decision).

### F-REFINE-3 — `crossval` must stay a numpy-gated submodule; the dep-free guard already enforces it

`test_dependency_free_import.py:14-40` evicts and blocks `numpy`, imports the top-level package in
a subprocess, and asserts `"numpy" not in sys.modules`. Because `crossval` needs numpy, it **must
not** be re-exported from `juniper_model_core/__init__.py` (which today re-exports only the
dep-free contract, `__init__.py:21-33`, and deliberately omits `conformance`). This is a *latent
guardrail, already wired*: any `from juniper_model_core.crossval import …` added to `__init__.py`
fails the existing test. The roadmap must respect it (consumers do `from juniper_model_core.crossval import cross_validate`), and the `build` job's bare-wheel smoke (`ci-model-core.yml:98-105`) is a second backstop.

### F-REFINE-4 — `aux` slicing is sound only if every aux array is per-sample (axis 0 == n)

The design slices `aux` axis-0 per fold exactly like `X`/`y` (crossval design §4). Verified safe
for the arrays in play: `dt (n, T)`, `readout_mask (n, T)` (`fixtures.py:66-68`), and WS-4b's
`target_dt (n,)`, `seq_lengths (n,)` — all sample-indexed on axis 0. A non-per-sample entry
(e.g. a scalar hyperparameter mistakenly routed through `aux`) would be **silently mis-sliced**.
Guardrail: `cross_validate` should assert `arr.shape[0] == n_samples` for every `aux` value and
raise otherwise. See [OPT-D](#opt-d--splitspy-and-the-aux-contract).

### F-REFINE-5 — Passing the eval fold as `X_val`/`y_val` is mild optimism for early-stopping models

The design diagram fits with `X_val=X[ev], y_val=y[ev]` then scores held-out on the *same* `X[ev]`
(crossval design §3). For the closed-form `ReferenceLinearModel` (`reference.py:60-79`) and the
closed-form LMU readout there is no early stopping, so this is harmless today. For any future model
that uses the validation set to early-stop, feeding it the eval fold leaks the eval signal into the
fit and inflates the held-out score. See [OPT-B](#opt-b--validation-set-handling-in-the-executor-decision).

### F-REFINE-6 — The 2nd-implementer test must use an in-repo stub, never import recurrence

recurrence-model depends on model-core (`pyproject.toml:31-33`). If model-core's own test imported
`juniper-recurrence-model`, it would create a dependency **cycle**, drag numpy/recurrence into the
test env, and force a `<0.2.0`-pinned consumer to need 0.2.0. The design already resolves this
(prefer an in-repo 3-D `TrainableModel` stub; the real `LMURegressor`-CV test lives on the
recurrence side — crossval design §6). Validation confirms that is the **only** correct choice. See
[OPT-C](#opt-c--the-2nd-implementer-model-agnostic-proof).

### F-CONFIRM-7 — Contract-gap reasoning, factory model, and external scoring are all correct

The two gaps the executor surfaces (no `reset()`/`clone()` → factory; no held-out `score()`
*method* → external scoring; the lone `score` token in the ABC file is the `GrowthOutcome.score`
dataclass field, not a method) are real and correctly reasoned against `interfaces.py:78-142`. Keeping scoring
external and the ABC lean is the right call (crossval design §1-2 = **CONFIRM**).

---

## 4. Outstanding-work inventory

| Item | State | Owner phase |
|---|---|---|
| `crossval/{__init__,metrics,splits,executor}.py` | **Not started** | [Phase 1](#phase-1--pr-1-model-core-020-the-crossval-submodule) |
| `[crossval]` extra (numpy) | Not started | Phase 1 |
| `_version.py` 0.1.0 → 0.2.0 + `CHANGELOG [0.2.0]` | Not started | Phase 1 |
| `[tools]` pin widen `<0.2.0` → `<0.3.0` + `test_pyproject_extras.py` + drift-lint green (F-CRIT-1) | Not started | Phase 1 (lockstep) |
| §6 test matrix (metrics / splits / executor dogfood / stub 2nd-impl / determinism / aggregate / events) | Not started | Phase 1 |
| model-core 0.2.0 → TestPyPI soak → PyPI (pending-publisher + tag) | Blocked on Phase 1 | [Phase 2](#phase-2--publish-model-core-020-gated) |
| recurrence app `/v1/crossval` endpoint + recurrence-side `LMURegressor`-CV test | Blocked on Phase 2 | [Phase 3](#phase-3--consumers-opt-in-gated-on-publish) |
| Deferred: parallel/distributed folds, classification metrics, multi-ticker embargo, server-side fold materialization, `score()` on ABC | Gated | [Phase 4+](#phase-4--deferred--trigger-gated) |

---

## 5. Design / development approach options

Each option set lists choices with strengths, weaknesses, the dominant risk, and a guardrail, then
a recommendation. Items marked *(decision)* feed §10.

### OPT-A — Where the regression-metric math lives *(decision)*

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **A1** — new `crossval/metrics.py`, independent copy + a parity test asserting it equals `reference._regression_metrics` on a fixture | Lowest coupling; crossval stays self-contained; conformance untouched | Two impls to keep in step (parity test only catches drift in CI, not at author time) | Parity test in Phase 1 matrix; comment in both pointing at each other |
| **A2** — extract a private `juniper_model_core/_metrics.py` (numpy) imported by **both** `conformance/reference.py` and `crossval/metrics.py` | Single source of truth; no drift possible | A new module both numpy-gated submodules import; must verify it is never pulled by the top-level `__init__` (F-REFINE-3) | `test_dependency_free_import.py` already guards top-level; add an explicit "not imported at top level" assertion |
| **A3** — `crossval` imports from `conformance.reference` | Reuses existing code with zero new files | **Wrong direction** — couples the runtime crossval layer to the *test kit*; forces `[crossval]` users to carry the conformance surface | — (rejected) |

**Recommendation:** **A2** (single source of truth; the dep-free invariant is already enforced and
cheaply extended). A1 is the acceptable fallback if Paul prefers zero new shared modules. A3 rejected.
**Ratified (Paul, 2026-06-17): A2** — a private `juniper_model_core/_metrics.py`; `conformance/reference.py` is refactored to call it.

### OPT-B — Validation-set handling in the executor *(decision)*

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **B1** — fit with `X_val=X[ev], y_val=y[ev]` (design as drawn) | Matches the design diagram and the conformance `_fit` shape; fine for non-early-stopping models | Eval-fold leakage for any future early-stopping model (F-REFINE-5) | Document the assumption loudly |
| **B2** — fit with `X_val=None, y_val=None`; score held-out separately | Clean held-out purity; no leakage regardless of model | Models that *require* a val set for their fit path get none | Document; revisit if a model needs it |
| **B3** — `pass_eval_as_val: bool = False` parameter on `cross_validate` | Purity by default, opt-in convenience; future-proof | One more knob (small RK-4 surface) | Keep it a single bool; no further val-policy knobs in v1 |

**Recommendation:** **B3 defaulting to B2 behavior** — held-out purity is the safe default for a
generic CV layer, and the bool keeps the design diagram reachable without code change.
**Ratified (Paul, 2026-06-17): B3 with `pass_eval_as_val=False` default** (held-out purity).

### OPT-C — The 2nd-implementer (model-agnostic) proof

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **C1** — tiny in-repo 3-D `TrainableModel` stub with `aux={dt,…}` | No new dependency; keeps model-core dep-clean; proves shape-/aux-agnosticism | Stub is not a "real" model | Stub lives in `tests/`, never in the shipped package |
| **C2** — import real `LMURegressor` in model-core's test | Exercises a production model | Dependency **cycle** + dep bloat + pin trap (F-REFINE-6) | — (rejected) |

**Recommendation:** **C1** in model-core; the real `LMURegressor`-over-CV test lands on the
recurrence side in Phase 3 (so both halves of the model-agnostic claim are proven, in the right repos).

### OPT-D — `splits.py` and the `aux` contract

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **D1** — self-contained `walk_forward_folds(...)` in crossval returning index `Fold`s (design as written) | Shape-agnostic (2-D & 3-D, indices only); no cross-repo dep; honors D-CV-4 (client-side from `_full`) | Reimplements ordering/clamp logic that `temporal_split_index` also encodes | Mirror `temporal_split_index` clamp semantics (`split.py:142-145`) for consistency; share no code (different shape) |
| **D2** — promote walk-forward into `juniper-data` and import it | One canonical split home | Cross-repo dep + server-side materialization is explicitly deferred (juniper-data#168 scope C); over-builds v1 | — (defer to Phase 4) |

**Recommendation:** **D1**, plus the F-REFINE-4 per-sample `aux` assertion baked into
`cross_validate`. Keep `walk_forward_folds` index-only so it serves tabular and sequence identically.

### OPT-E — PR sequencing & version/pin handling *(decision)*

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **E1** — one PR-1: crossval code + `[crossval]` extra + `_version` 0.2.0 + CHANGELOG + **`[tools]` pin `<0.3.0` + `test_pyproject_extras.py` update** + full test matrix | The only green state (F-CRIT-1); satisfies RK-11; one reviewable unit | Slightly larger PR than the design imagined | Pin/extras/lint edits are the *same commit* as the version bump |
| **E2** — design's original split (pin-widen as later follow-up) | Smaller PR-1 | **Red CI** the moment `_version.py` hits 0.2.0 (F-CRIT-1) | — (rejected) |

**Sub-decision (design §5, "Paul's call"):** whether to bundle the deferred `predict(**kw)` ABC
documentation into 0.2.0. It is doc-only and low-risk; bundling avoids a second minor bump, but it
is logically independent of crossval. **Recommendation:** keep it out of PR-1 to keep the diff
single-purpose; fold it into the 0.2.0 release notes only if it lands before the tag.

**Recommendation:** **E1.**

**Ratified (Paul, 2026-06-17): E1, and BUNDLE the `predict(**kw)` ABC change into 0.2.0** (this overrides
the sub-decision recommendation above). PR-1 therefore also widens the ABC
`TrainableModel.predict(self, X)` → `predict(self, X, **kw)` plus docstring — additive and LSP-safe:
existing bare `predict(X)` implementers (`ReferenceLinearModel`) and the conformance kit's bare calls
stay valid (`interfaces.py:111-118`). It remains a single 0.2.0 minor.

### OPT-F — Parallelism seam *(decision)*

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **F1** — strictly serial loop (D-CV-5 as written) | Simplest; folds are independent; correctness obvious | A later parallel/distributed mode (WS-8/OQ-11) needs an API change | — |
| **F2** — serial by default, but accept an optional `map_fn=map` (or `n_jobs`) seam | Future-proofs WS-8 at near-zero cost; default stays serial (honors D-CV-5) | A speculative seam = small RK-4 over-abstraction surface | Seam is a single `map`-shaped callable only; **no** distributed/threading semantics in v1; documented as "serial unless a caller injects a map" |

**Recommendation:** **F1 for v1** (matches D-CV-5 and minimizes RK-4 surface); note F2 as the
intended WS-8 extension point so the signature can be widened additively later. If Paul wants the
seam now, F2's guardrail keeps it safe.
**Ratified (Paul, 2026-06-17): F2** — build the seam now: `cross_validate(..., map_fn=map)` defaulting to
the builtin serial `map`, so WS-8 can inject a parallel/distributed map with no API change. Guardrail
holds: a single `map`-shaped callable only, **no** threading/distributed semantics in v1; a parity test
asserts an injected `map_fn` yields an identical `CrossValResult`.

### OPT-G — Classification scope

| Option | Strengths | Weaknesses / risk | Guardrail |
|---|---|---|---|
| **G1** — regression-only; `score(task_type, …)` raises `NotImplementedError` for classification | Matches every current `TrainableModel` consumer (all regression); smallest correct surface | Classification CV is a later add | `score` dispatches on `task_type` so classification is a pure additive drop-in |
| **G2** — implement classification metrics now | Complete | No consumer needs it; speculative; risks RK-6 leakage into the generic layer | — (defer) |

**Recommendation:** **G1** — ship the `score()` dispatch shape, implement the regression branch,
defer classification (consistent with D-CV-3 and YAGNI).

---

## 6. Recommended roadmap (prioritized, ordered, grouped)

```text
Phase 0  Evaluation + decisions          ── THIS DOC — §10 decisions RATIFIED 2026-06-17
                │
Phase 1  PR-1 model-core 0.2.0           ── crossval submodule + extra + version + LINTS (lockstep)
                │  (self-contained; in-repo stub; CI green incl. ci-model-core + main ci)
Phase 2  Publish 0.2.0                    ── TestPyPI soak → PyPI (Paul pending-publisher + tag)
                │  (RK-10: gh workflow run publish; dual-gate pypi env, Paul approves)
Phase 3  Consumers opt in                 ── recurrence /v1/crossval + recurrence-side LMU-CV test
                │  (each bumps ITS model-core pin to admit 0.2.0, in its own PR)
Phase 4+ Deferred / trigger-gated         ── parallel folds (WS-8) · classification · multi-ticker
                                              embargo · server-side materialization · score() on ABC
```

### Phase 1 — PR-1 (model-core 0.2.0): the crossval submodule

Single, self-contained juniper-ml PR (scope reflects the ratified §10 decisions). **Grouped contents (one reviewable unit):**

1. `juniper_model_core/_metrics.py` — **NEW** private numpy helper holding the canonical regression-metric math (`{mse,rmse,mae,r2,loss}`, `loss==mse`), imported by **both** `crossval/metrics.py` and `conformance/reference.py` (D1/A2 single source of truth); `reference.py:_regression_metrics` is refactored to delegate. Never imported by the package `__init__` (F-REFINE-3).
2. `crossval/__init__.py` — exports `Fold`, `walk_forward_folds`, `FoldResult`, `CrossValResult`, `cross_validate`, `regression_metrics`, `score`. **Not** re-exported from the package `__init__` (F-REFINE-3).
3. `crossval/metrics.py` — `regression_metrics` (delegates to `_metrics.py`) + `score(task_type, …)` dispatch (regression branch; classification → `NotImplementedError`, [OPT-G](#opt-g--classification-scope)).
4. `crossval/splits.py` — `Fold` (frozen) + `walk_forward_folds(...)` index-only, expanding/rolling, `embargo`, `order`; mirror `temporal_split_index` clamp semantics ([OPT-D](#opt-d--splitspy-and-the-aux-contract)).
5. `crossval/executor.py` — `cross_validate(...)`; per-sample `aux` assertion (F-REFINE-4); `pass_eval_as_val=False` default ([OPT-B](#opt-b--validation-set-handling-in-the-executor-decision) B3); **`map_fn=map` seam, serial default** ([OPT-F](#opt-f--parallelism-seam-decision) F2); `on_event(fold_idx, event)` forwarding.
6. `interfaces.py` — **D3 (bundled):** widen the ABC `TrainableModel.predict(self, X)` → `predict(self, X, **kw)` + docstring documenting the `dt`/`readout_mask`/`seq_lengths` keyword path symmetric to `fit` (additive/LSP-safe).
7. `pyproject.toml` — add `[crossval] = ["numpy>=1.24"]`; `_version.py` → `0.2.0`; `CHANGELOG [0.2.0]` (crossval + `predict(**kw)` ABC doc + `_metrics.py` extraction).
8. **Lockstep lint/pin (F-CRIT-1):** widen juniper-ml `[tools]` to `juniper-model-core>=0.1.0,<0.3.0`; update `EXPECTED_EXTRAS["tools"]` in `test_pyproject_extras.py` **surgically** (not via global sed — `test_model_core_drift.py:190` negative-control shares the literal). `test_model_core_drift.py` then passes unedited (reads the pin dynamically).
9. Full §7 test matrix.

**Exit gate:** `ci-model-core.yml` (3.12/3.13/3.14, ≥85% cov, bare-wheel dep-free smoke) green; juniper-ml main `ci.yml` `tests` job green (drift + extras lints pass); Paul's explicit per-PR merge signal + `gh pr view` MERGED.

### Phase 2 — Publish model-core 0.2.0 (gated)

Tag `juniper-model-core-v0.2.0` → `publish-model-core.yml` → TestPyPI (`--no-deps`, no-fallback
verify) → PyPI (OIDC). Pending-publisher = Paul. **RK-10:** `gh workflow run` immediately; confirm
PyPI shows 0.2.0 (allow CDN cache lag). Until 0.2.0 is on PyPI, no docker consumer may pin it.

### Phase 3 — Consumers opt in (gated on publish)

- **recurrence app `/v1/crossval`** (WS-4b's deferred dependency now satisfied): an endpoint that builds folds from a `_full` selection and runs `cross_validate` with a `LMURegressor` factory; plus a recurrence-side conformance-style test that runs CV over a real 3-D `equities_seq` fixture with `aux={dt,target_dt,readout_mask,seq_lengths}` — the **real** 2nd-implementer proof ([OPT-C](#opt-c--the-2nd-implementer-model-agnostic-proof)). recurrence bumps its own model-core pin to admit 0.2.0 in that PR.
- **(optional)** juniper-data#168 scope C server-side fold materialization (perf optimization, not a prerequisite — D-CV-4).
- **(optional)** canopy *direct* fold-aware control + per-fold aggregation UI (deferred in crossval design §8; surfaced here as an optional consumer once the layer ships — WS-5-adjacent; the regression audit landed in canopy #430).

### Phase 4+ — Deferred / trigger-gated

Parallel/distributed fold execution (WS-8 / OQ-11 worker) · classification held-out metrics ·
multi-ticker embargo-aware walk-forward via `ticker_code` · a `score()` method on the
`TrainableModel` ABC (only if a second need appears) · `splits` promotion into juniper-data
([OPT-D](#opt-d--splitspy-and-the-aux-contract) D2).

---

## 7. Test roadmap

Mirror the existing patterns: free-function known-answer tests in the `test_validation.py` style,
and a `cross_validate` dogfood in the `test_reference_conformance.py` subclass style
(`tests/test_reference_conformance.py:20-50`). Target ≥85% coverage (the gate); the package norm is
~97%.

| Test | Asserts | Mirrors |
|---|---|---|
| `regression_metrics` known-answer | mse/rmse/mae/r2 vs hand-computed; `loss == mse`; keys ⊆ `REGRESSION_METRIC_KEYS` | `test_validation.py` |
| `regression_metrics` ≡ reference (A2) | identical output to `reference._regression_metrics` (both delegate to `_metrics.py`); test asserts equality + that `_metrics.py` is not pulled by the top-level import | new |
| `walk_forward_folds` shape/order | expanding & rolling counts; monotonic train growth; no eval-before-train; `embargo` drops the right rows; `order` enforces chronology | new |
| leakage guard | every `eval_idx` strictly after its `train_idx` under `order`; embargo gap respected | new |
| `aux` mis-slice guard (F-REFINE-4) | non-per-sample `aux` raises | new |
| `cross_validate` dogfood | factory = `ReferenceLinearModel`; high mean `r2`; sane per-fold + aggregate shapes | `test_reference_conformance.py` |
| 2nd-implementer (stub) | in-repo 3-D `TrainableModel` stub + `aux={dt,readout_mask}` → folds run, Δt path engaged | `tiny_regression_3d` shape |
| determinism | same factory/seed/folds → identical `CrossValResult` | new |
| aggregate correctness | `eval_aggregate`/`eval_std` == numpy mean/std of per-fold metrics | new |
| event forwarding | `on_event(fold_idx, event)` fires per fold in legal order (`legal_event_order` per fold) | `validation.py:100` |
| `map_fn` seam parity (F2) | `cross_validate(..., map_fn=custom_map)` == serial result; default `map_fn` is the builtin serial `map` | new |
| `predict(**kw)` ABC (D3) | bare `predict(X)` implementers still conform; a `**kw`-reading model receives the sliced `aux` via `predict` | conformance kit |
| dep-free unchanged (F-REFINE-3) | top-level import still numpy-free after `crossval` + `_metrics.py` added | existing `test_dependency_free_import.py` |

---

## 8. Automation & hardening

- **CI already covers crossval:** `ci-model-core.yml:64` installs `.[test]` (numpy present) and runs `--cov=juniper_model_core --cov-fail-under=85` (`:66-71`); new `crossval/*` is coverage-gated automatically. Ensure tests actually import `crossval` so coverage counts it.
- **Dep-free smoke preserved:** the bare-wheel `import juniper_model_core` check (`ci-model-core.yml:98-105`) and `test_dependency_free_import.py` together keep `crossval` **and the new `_metrics.py`** out of the top-level import path (F-REFINE-3 / A2).
- **Lints in lockstep (RK-11 / F-CRIT-1):** `test_pyproject_extras.py` + `[tools]` pin edited in the same PR as the version bump; `test_model_core_drift.py` validates the pin/version relationship continuously.
- **Publish-first + dual gate:** `publish-model-core.yml` TestPyPI→PyPI OIDC; `pypi` environment keeps wait_timer + reviewer approval — **Paul approves deployment gates** (never auto-approved).
- **RK-10:** `gh workflow run` the publish workflow immediately after the tag; lint-passing ≠ runtime-passing.
- **Concurrency hygiene:** `gh pr list` + `gh run list --branch main` (green) before assuming a red PR is ours; no merge without Paul's explicit per-PR signal + `gh pr view` MERGED.

---

## 9. Risk register & guardrails

| Risk | Where it bites | Guardrail |
|---|---|---|
| **F-CRIT-1** version/pin desync | juniper-ml CI red on `_version` 0.2.0 | Pin-widen + extras-lint in PR-1 (E1); `test_model_core_drift` is the continuous check |
| **RK-4** over-abstraction | `map_fn` seam (OPT-F F2, now built), val knob (OPT-B) | serial-default `map_fn` (one `map`-shaped callable, no threading/distributed semantics in v1) + parity test; single `pass_eval_as_val` bool |
| **RK-6** classification leak | `score()` / metrics | regression-only branch; classification → `NotImplementedError`; no argmax/accuracy in crossval |
| **Dep-free invariant** | top-level import pulls numpy | crossval never in `__init__`; existing subprocess test + bare-wheel smoke |
| **aux mis-slicing** (F-REFINE-4) | silent wrong folds | per-sample `shape[0] == n` assertion in `cross_validate` |
| **Eval-fold leakage** (F-REFINE-5) | inflated held-out score for early-stopping models | OPT-B default = no val passthrough |
| **Reverse-dep cycle** (F-REFINE-6) | model-core test importing recurrence | in-repo stub only (OPT-C C1) |
| **Publish-first ordering** | docker consumer pins 0.2.0 pre-publish | no pin until PyPI 0.2.0; TestPyPI soak |
| **Metric drift** (F-REFINE-2) | two metric impls diverge | A2 ratified — one `_metrics.py` source; `reference.py` refactored to call it |

---

## 10. Decisions — ratified (Paul, 2026-06-17)

1. **OPT-A → A2.** Single source of truth: a private `juniper_model_core/_metrics.py` holds the canonical regression-metric math; both `crossval/metrics.py` and `conformance/reference.py` call it.
2. **OPT-B → B3, default `pass_eval_as_val=False`.** Held-out purity by default; the bool re-enables eval-as-val if a future model needs it.
3. **OPT-E sub-decision → BUNDLE.** The `predict(**kw)` ABC widening rides along in 0.2.0 (`interfaces.py` `predict(self, X)` → `predict(self, X, **kw)` + docstring; additive/LSP-safe). One 0.2.0 minor.
4. **OPT-F → F2.** Build the `map_fn=map` seam now (serial default); WS-8 injects a parallel map with no API change. Guardrail: one `map`-shaped callable, no distributed semantics in v1, parity-tested.
5. **E1 confirmed.** Single lockstep PR-1 (version + `[tools]` pin `<0.3.0` + extras-lint together). This **supersedes** crossval design §5/§7's "separate follow-up" (required by F-CRIT-1).

Already settled by the ratified design + this validation (no separate sign-off): D-CV-1…5, OPT-C (in-repo
stub), OPT-D (D1 index-only splits), OPT-G (G1 regression-only with `score()` dispatch). **Phase 1 / PR-1
is unblocked.**

---

## 11. Cross-references

- Ratified layer design (the spec this roadmap operationalizes): [`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md).
- Model contract + conformance kit (the `TrainableModel` surface, D1-D10): [`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md).
- WS-4b app build (where the executor is the deferred dependency): [`JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md).
- WS-4 model build (the `LMURegressor` 2nd implementer): [`JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md).
- Workstream / refactor context (WS-2/3/8, OQ-11): [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md).
- Placement convention (`-core` = juniper-ml subdir): [`JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md`](JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md).
- Implementation targets: `juniper-model-core/juniper_model_core/{interfaces,validation,conformance/reference}.py`; split semantics to mirror: `juniper-data/juniper_data/core/split.py`.

---

## Appendix A — Source evidence ledger

| Claim | Evidence |
|---|---|
| `TrainableModel` surface (no reset/clone/score) | `juniper-model-core/juniper_model_core/interfaces.py:78-142` |
| `GrowableModel` (n_units/grow_step/freeze) | `interfaces.py:145-171` |
| `REGRESSION_METRIC_KEYS = {mse,rmse,mae,r2,loss}` | `validation.py:35` |
| `validate_metrics` / `validate_topology` / `legal_event_order` | `validation.py:42,66,100` |
| Existing `_regression_metrics` (the dup, F-REFINE-2) | `conformance/reference.py:37-44` |
| Per-fold step (`_fit`) | `conformance/suite.py:51-52` |
| `ConformanceDataset.fit_kwargs` + 3-D `dt`/`mask` | `conformance/fixtures.py:32,66-68` |
| Top-level re-exports omit conformance/crossval | `juniper_model_core/__init__.py:21-33` |
| `dependencies = []`; `[conformance]`/`[test]` extras only | `pyproject.toml:32,34-45` |
| `_version.py = "0.1.0"` | `_version.py:3` |
| `CHANGELOG [Unreleased]` empty; stale "not published" note | `CHANGELOG.md:8,37-38` |
| Dep-free import guard | `tests/test_dependency_free_import.py:14-40` |
| Conformance subclass pattern | `tests/test_reference_conformance.py:20-50` |
| `temporal_split_index` + walk-forward deferral | `juniper-data/juniper_data/core/split.py:116-145` |
| `LMURegressor(TrainableModel)` + widened predict | `juniper-recurrence/.../model.py:51,169` |
| recurrence-model deps model-core `<0.2.0` | recurrence-model `pyproject.toml:31-33` |
| juniper-ml `[tools]` pin `<0.2.0` | `pyproject.toml:55` |
| Drift lint asserts `current < pin_upper` | `tests/test_model_core_drift.py:116-139` |
| Extras lint hardcodes the exact pin string | `tests/test_pyproject_extras.py:55,89-96` |
| CI installs `.[test]`, 85% cov gate, bare-wheel smoke | `.github/workflows/ci-model-core.yml:64,66-71,98-105` |

---

## Appendix B — Independent sub-agent validation record

Four sub-agents validated this document during the authoring session, each scoped to a distinct
aspect and working only from the source (not from each other's conclusions). Their findings were
folded into this revision; residual caveats are listed last.

- **Validator 1 — model-core source accuracy.** Re-derived every `juniper-model-core` `file:line` claim in §2 / §3 / §7 / §8 / Appendix A against the as-built package: **all PASS, zero failures**, no citation off by more than 0 lines. Re-confirmed the "crossval = 0% implemented" headline two ways (filesystem `find` + source `grep`, both empty). Contributed the `GrowthOutcome.score`-is-a-field precision nuance (folded into F-CONFIRM-7).
- **Validator 2 — cross-repo facts + the F-CRIT-1 lint contradiction.** Independently re-derived
  F-CRIT-1 from the lint code: **CONFIRMED** — with `_version.py = "0.2.0"` and the `[tools]` pin
  `<0.2.0`, `assertLess((0,2,0),(0,2,0))` is False → red; widening to `<0.3.0` fixes it; `[all]`
  needs no edit; the external recurrence pin is not lint-coupled. Confirmed the failure surfaces in
  **required CI** (`ci.yml` `tests` job runs both lints; `required-checks` gates on it). All three
  cross-repo facts PASS. Surfaced the in-repo `juniper-service-core` open-ceiling pin (safe) and the
  global-sed foot-gun against `test_model_core_drift.py:190` — folded into the F-CRIT-1 inventory.
- **Validator 3 — internal consistency & ratified-decision conformance.** Found **no genuine contradiction** with D-CV-1…5 or D1-D10; confirmed every OPT recommendation conforms and that the one deviation (E1 superseding crossval design §5/§7) is explicitly disclosed and RK-11-grounded. All six cross-reference link targets exist. Flagged the canopy-UI re-tiering (now annotated in Phase 3) and that this appendix previously over-stated completion (corrected here).
- **Validator 4 — markdown lint & header schema.** Header schema PASS (six fields in order; `Last Updated` = ISO `2026-06-17`); structure clean (single H1; fences languaged + spaced; tables spaced; longest line 506 ≤ 512). Found **7 MD051 broken in-doc anchors** (the four `*(decision)*`-suffixed OPT headings) — **fixed in this revision**. The 86 MD060 "table-column-style" hits are a newer-toolchain artifact the repo's pinned `markdownlint-cli` v0.42.0 does **not** raise.

**Residual caveats:** §2 row 5 (cascor is not yet a `TrainableModel`) stays **UNCHECKED** — no cascor checkout in this worktree; it is out of this layer's scope and flagged as such, not asserted. The §10 decisions were **ratified by Paul on 2026-06-17** (D1–D5); this plan is now ready for Phase 1 / PR-1.
