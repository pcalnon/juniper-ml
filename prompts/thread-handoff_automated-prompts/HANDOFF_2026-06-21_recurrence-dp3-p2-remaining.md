# Thread Handoff — juniper-recurrence DP-3 P2 (remaining: data → bench → HTTP enum)

**Date**: 2026-06-21
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread)
**Origin**: Completion of DP-3 **P1** (readout-spec + GCV) and **P2a** (RFF nonlinear readout), both
shipped to PyPI. This hands off the **remaining P2** work.
**Supersedes**: `HANDOFF_2026-06-20_recurrence-dp3-implementation.md` (#493) — P1 and P2a are now done.

---

## Continue

Implement the **remaining DP-3 P2** for `juniper-recurrence`, in order: **(1) the capacity dataset**
(juniper-data generator), **(2) the bench RFF row + findings update**, **(3) the HTTP `readout` enum**
(app + client). The design-of-record (read first; binding constraints in §3/§6/§7 + Appendix A — do
not relitigate) is juniper-ml
`notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` (ratified §8a, v0.2.0).

## Completed this session (all shipped + verified)

- **DP-3 P1 — `juniper-recurrence-model 0.1.3` LIVE on PyPI.** Readout-spec refactor
  (`Readout`/`ReadoutSpec` protocols, `LinearReadout`/`LinearReadoutSpec`), `ridge="gcv"` GCV
  selection (one SVD + 1-D grid), serializer schema 2 (`readout__*` arrays + nested `meta["readout"]`
  + registry + pre-DP-3 `.npz` fallback), `_coef` forwarding property, **byte-identical backcompat**.
  PRs (all MERGED): recurrence **#30** (model), **#31** (app+client `ridge="gcv"`), **#32** (notes).
  Closes recurrence#28.
- **DP-3 P2a — `juniper-recurrence-model 0.1.4` LIVE on PyPI.** `RFFReadout`/`RFFReadoutSpec` (Rung 2a):
  `standardize(M) → RFF √(2/D)cos(M·W+b) → GCV-ridge`, `W,b` sampled in `fit` from `random_seed`
  (cross-fold-safe via the immutable spec), median-`γ`, `D` capped to fold `n`, design
  `[φ(standardize(M)) | target_dt | 1]` (D-WS4-2 preserved), registered `"rff"`, float64
  `readout__{W,b,mean,std,beta}`, bit-exact round-trip **gated by an RFF conformance subclass**,
  `model._coef` None. **`model.py` unchanged** (the P1 refactor is readout-agnostic). 96 tests, cov
  99.6%. PRs (MERGED): recurrence **#39** (model), **#41** (notes).

## Remaining work

- **P2-data — NEW juniper-data generator `delay_product`** (`y = x(t−τ₁)·x(t−τ₂)`, irregular-Δt
  synthetic). Mirror `juniper_data/generators/irregular_sine/`: `params.py` (subclass
  `SyntheticSequenceParams`), `generator.py` (`VERSION` + Generator class + `get_schema`), `__init__.py`;
  window via `juniper_data.generators._sequence.window_timed_series`; register in
  `juniper_data/generators/__init__.py`; add unit tests (mirror the irregular_sine tests + a windowing
  leakage/contract test). Bump juniper-data **0.8.0 → 0.9.0**. **KEY INSIGHT:** keep τ₁,τ₂ inside the
  lookback; the target is then a **quadratic form `MᵀQM`** in the LMU memory state (each delayed value
  is ≈ a linear functional of the Legendre memory, so their product is bilinear) → a **linear** readout
  provably can't fit it (r² bounded < 1), an **RFF** readout can approximate → expect a clear
  **nonlinear ≫ linear** r² gap. Publish-gated: Paul cuts the GH Release + approves the PyPI gate.
- **P2-bench + findings** — `bench/datasets.py`: add a `delay_product` factory delegating to
  `juniper_data.generators.delay_product` + bump the `[bench]` pin to `juniper-data>=0.9.0`.
  `bench/run_benchmark.py`: add the **RFF readout row** (`LMURegressor(readout=RFFReadoutSpec(...))`) —
  expect a *tie* on the existing near-linear datasets (mackey_glass r²≈0.9999, irregular_sine r²≈0.988)
  and the *gap* on `delay_product`. Update the juniper-ml findings doc
  (`JUNIPER_RECURRENCE_EVALUATION_FINDINGS_*`). NOTE: a concurrent session added a **bench CI lane**
  (recurrence #36/#38) — bench changes now have CI; check it.
- **P2c — HTTP `readout` enum** (app + client). App `schemas.py`/`routers`/`main.py` CLI: a
  `readout: Literal["linear","rff"]` tagged enum + per-readout param fields (e.g. `rff_features`,
  `gamma`); pass a constructed `RFFReadoutSpec`/`LinearReadoutSpec` through to `LMURegressor`. Client
  passthrough. **Floor-bump the app model pin to `juniper-recurrence-model>=0.1.4`.** Publish-gated like
  P1's PR-B (the app CI installs the model from PyPI; 0.1.4 is already live, so this is unblocked).
- **P3 (later)** — Rung 2b torch MLP behind a `[torch]` extra (`torch>=2.9`, CPU-only, single dtype,
  `set_num_threads(1)`, `eval()`, deterministic; state as named npz arrays — NOT `torch.save`; separate
  optional CI job + coverage exclusion). **Build only if P2's measured 2a lift is non-trivial.**

## Key context / constraints (validated — design Appendix A; do not relitigate)

- **Conformance has NO fit-quality gate.** The one sharp constraint is **bit-exact `np.array_equal`
  lossless serialization** (RFF gates it with a conformance subclass; predictions must be finite).
- **RFF per-column-standardizes `M`** (Legendre columns ≈25× RMS); γ via median heuristic (ridge can't
  pick γ); immutable readout **spec** (cross-fold safety); **D-WS4-2** = readout takes `M` only,
  `target_dt` stays a linear side-channel.
- **Honest expectation:** existing datasets are at the linear ceiling → RFF *ties* there; the capacity
  dataset is what shows the upside. P2-data is the instrument that demonstrates capacity.
- Memories: `project_dp3_readout_spectrum_design_2026-06-20`,
  `project_recurrence_equities_readout_finding_2026-06-19`, `project_ws4_recurrence_model`.

## Fresh-thread prompt (copy-paste)

```text
Continue DP-3 P2 for juniper-recurrence (remaining), in order: P2-data → P2-bench → P2c.

Read first: juniper-ml notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md (ratified
design-of-record; binding constraints §3/§6/§7 + Appendix A — do not relitigate). P1 + P2a are SHIPPED:
juniper-recurrence-model 0.1.4 is LIVE on PyPI (RFFReadout/RFFReadoutSpec, registered "rff").

P2-data: NEW juniper-data generator `delay_product` (y = x(t−τ₁)·x(t−τ₂), irregular-Δt synthetic).
Mirror juniper_data/generators/irregular_sine/ (params.py over SyntheticSequenceParams; generator.py
with VERSION/Generator/get_schema; __init__.py); window via _sequence.window_timed_series; register in
generators/__init__.py; add unit + windowing-leakage tests; bump juniper-data 0.8.0→0.9.0. Keep τ₁,τ₂
inside the lookback so the target is a QUADRATIC form in the LMU memory → linear readout provably can't
fit it, RFF can → expect a clear nonlinear≫linear r² gap. Publish-gated (Paul).

P2-bench: bench/datasets.py add a delay_product factory delegating to juniper_data.generators + bump
[bench] pin to juniper-data>=0.9.0; bench/run_benchmark.py add the RFF readout row (tie on existing
datasets, gap on delay_product); update the juniper-ml findings doc. A bench CI lane now exists.

P2c: app schemas/routers/CLI readout: Literal["linear","rff"] tagged enum + per-readout params + client
passthrough; floor-bump the app model pin >=0.1.4 (already live on PyPI).

Then P3 (torch MLP behind [torch], gated on a measured 2a lift).

CONVENTIONS: verify repo state before each step (concurrent sessions are active); feature/** branches;
centralized worktrees in Juniper/worktrees/; Paul merges all PRs + approves every PyPI gate; publishing
= cut a GitHub Release (templated notes from juniper-ml notes/templates/TEMPLATE_RELEASE_NOTES.md,
archived to <repo>/notes/releases/), never a bare tag; recurrence has local-only pre-commit
(ruff/ruff-format/bandit) + per-package CI (ruff check + pytest --cov-fail-under=90 + build); a bench
CI lane + required-checks were added by a concurrent session (#36/#38/#40). Verify start state below.
```

## Verification of start state

```bash
# Model 0.1.4 live (RFF readout) + juniper-data 0.8.0 base:
curl -fsS https://pypi.org/pypi/juniper-recurrence-model/0.1.4/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
curl -fsS https://pypi.org/pypi/juniper-data/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
# Concurrent state (verify before each PR):
gh pr list --repo pcalnon/juniper-data --state open
gh pr list --repo pcalnon/juniper-recurrence --state open
# juniper-data generator template + sequence windowing helper:
ls juniper-data/juniper_data/generators/irregular_sine/
sed -n '1,80p' juniper-data/juniper_data/generators/_sequence.py   # window_timed_series
```

## Conventions / gates (carry forward)

- **feature/** branches**; centralized worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/`.
- **Paul merges all PRs and approves every PyPI gate.** juniper-data & juniper-recurrence `main` use
  rulesets / required checks — `mergeStateStatus` may show BLOCKED for non-admins even when green; Paul
  admin-merges.
- **Publishing = cut a GitHub Release** (templated notes archived to `<repo>/notes/releases/`), never a
  bare tag. For juniper-data the Release `published` event triggers `publish.yml`; for
  juniper-recurrence-model the `juniper-recurrence-model-v*` tag (created by the Release) triggers
  `publish-recurrence-model.yml` (build → TestPyPI verify → PyPI env gate).
- **Pydantic gotcha** (juniper-data generators): params subclass `SyntheticSequenceParams`; an
  `extra="ignore"` model silently drops unknown kwargs — pin the consumer to the version that adds new
  params.

## Git status at handoff

All session branches MERGED (recurrence #30/#31/#32/#39/#41). juniper-recurrence `main` at the #41
merge; `juniper-recurrence-model 0.1.3` + `0.1.4` LIVE on PyPI. No in-progress edits at handoff.
**Stale worktrees to remove on the next cleanup signal** (Paul deferred #31/#32 cleanup): the P1 + P2a
feature/docs worktrees under `Juniper/worktrees/juniper-recurrence--*`, plus scratch venvs
`worktrees/dp3-venv`, `worktrees/dp3-p2-venv`, and `/tmp/dp3-wheelhouse`.
