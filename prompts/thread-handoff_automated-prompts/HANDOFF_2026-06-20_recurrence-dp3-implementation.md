# Thread Handoff — juniper-recurrence DP-3 readout-spectrum implementation

**Date**: 2026-06-20
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread)
**Origin**: Completion of the 2026-06-19 plan's **step 2** (equities data-conditioning re-bench) and
**step 3 design** (DP-3 readout-spectrum, ratified). This hands off the **DP-3 implementation**.
**Supersedes**: `HANDOFF_2026-06-19_recurrence-data-conditioning-and-dp3.md` (steps 2-3) — step 2 and
the step-3 *design* are now done; this prompt is the *build*.

---

## Continue

Implement **DP-3** — the **ratified readout-spectrum design** for `LMURegressor` — in
`juniper-recurrence/juniper-recurrence-model/`, phased **P1 → P2 → P3**. The design-of-record (read it
first) is juniper-ml `notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` (PR #491,
**v0.2.0**, ratified §8a). Its **Appendix A** (four independent sub-agent reviews) and §3/§6/§7 carry
the binding constraints — do not relitigate them.

## Completed this session (all verified)

- **juniper-data 0.8.0** — `regression_target: "next_close" | "return" | "log_return"` on
  `EquitiesParams` (inherited by `EquitiesSeqParams`); default `next_close` byte-identical. **PR #195
  MERGED**; **`v0.8.0` GitHub Release CUT** → `publish.yml` running → **PyPI dual-gate is Paul's to
  approve** (he is handling it before this thread starts). Release notes archive: juniper-data #198.
- **juniper-recurrence #29 (MERGED)** — bench `equities_seq` → stationary `log_return` target + a
  `lmu_var/fixed_d16_ridge1.0` variant; `[bench]` pin → `juniper-data>=0.8.0`; results regenerated
  (ratified ridge=0 synthetic primary bands byte-identical). **#28 (issue)** — readout-regularization
  follow-up.
- **juniper-ml #487 (MERGED)** — findings doc **v1.2** §3.2: the equities r²≈−50 was **dominantly an
  unregularized-readout artifact** (the bench's `ridge=0` default), not target non-stationarity; on a
  stationary target a *regularized* LMU reaches the efficient-market ceiling (r²≈0) and beats linear
  ridge. DP-3 refined to "build-for-insight, not strictly indicated".
- **juniper-ml #491** — the DP-3 readout-spectrum **design, ratified** (Paul accepted §8 Q1-Q4 +
  YES on the capacity dataset). May be MERGED by the time you read this; if still open, treat §8a as
  authoritative.

## Remaining work — DP-3 implementation (per #491 §9)

- **P1 — readout-spec refactor + Rung 1 (GCV).** Extract a `Readout` protocol +
  `LinearReadoutSpec(ridge=…)`; `LMURegressor` delegates. **Byte-identical backcompat** is the hard
  part (the app imports `LMURegressor`/`LMUSerializer` directly — 4 sites): keep the constructor
  signature, `ridge=0.0` default (a *hard invariant*), `_coef` as a forwarding property,
  `topology["meta"]["d"]` = memory order (asserted `==4` in recurrence `test_routes.py`),
  `model_type=="lmu"`, and an **old-format `LMUSerializer.load` fallback** (no `meta["readout"]` →
  `LinearReadout(ridge=meta["ridge"])`+`coef`). Add GCV ridge selection (`ridge="gcv"`: one SVD + a
  1-D search; persist the selected λ); widen `ridge: float|Literal["gcv"]` **cross-repo** into the app
  `schemas.py`/CLI/`settings`. **Resolves juniper-recurrence#28.** (numpy)
- **P2 — Rung 2a (RFF) + the capacity dataset.** `RFFReadoutSpec` = **standardize(M, train-fold-only)
  → RFF `√(2/D)cos(Wm+b)` → GCV-ridge**, design `[φ(standardize(M)) | target_dt | 1]` (target_dt/bias
  stay **linear**); γ via median heuristic on standardized M (ridge can't pick γ); `D` capped to the
  smallest walk-forward fold; persist `W,b` (float64) + stats + γ + λ. **Add the
  capacity-demonstrating nonlinear dataset** (§8a: `y = x(t−τ₁)·x(t−τ₂)`, a second-order
  multiplicative target a linear readout provably can't fit — expect a clear nonlinear≫linear r²
  gap; home = juniper-data generator *or* bench-local, your call at P2). RFF conformance subclass
  (the bit-exact round-trip is the gate; assert finite predictions). Bench rows + findings update +
  the HTTP `readout` enum. (numpy)
- **P3 — Rung 2b (torch MLP), GATED.** Behind a `[torch]` extra; **build only if P2's measured 2a lift
  is non-trivial.** CPU-only + single fixed dtype + `set_num_threads(1)` + `eval()` +
  `use_deterministic_algorithms(True)`; state persisted as **named npz arrays** (NOT `torch.save` —
  serializer is `allow_pickle=False`); pin **`torch>=2.9`** (cp314 wheels ship since 2.9.0 — do NOT add
  a Python-version ceiling); separate optional CI job + exclude the torch module from the base job's
  `--cov-fail-under=90`. (torch)

## Key context / constraints (validated — see #491 Appendix A)

- **Conformance has NO fit-quality gate.** The one sharp constraint is **bit-exact
  `np.array_equal` lossless serialization**. RFF (`cos` of a recomputed-from-d/θ memory matmul) is
  *not* "trivially lossless" — gate it with a conformance subclass; a NaN fails `array_equal`.
- **RFF MUST per-column-standardize M** (Legendre memory columns span ~25× RMS — measured).
- **Immutable readout *spec*, not a live object** — a shared readout instance in a crossval factory
  closure leaks fitted `W,b`/coef across folds. Sample `W,b` in `fit()` from `random_seed`.
- **D-WS4-2 preserved**: the readout receives `M` only; `LMURegressor` owns `target_dt` (linear
  side-channel, appended *after* any nonlinearity) + bias. The fixed LMU memory is untouched.
- **Honest expectation**: the existing datasets are at the linear ceiling (r²=0.9999 mackey_glass,
  0.988 irregular_sine) → 2a *ties* there; the **capacity dataset** is what shows the upside.
- Memories: `project_dp3_readout_spectrum_design_2026-06-20`,
  `project_recurrence_equities_readout_finding_2026-06-19`, `project_ws4_recurrence_model`.

## Fresh-thread prompt (copy-paste)

```text
Implement DP-3 — the ratified readout-spectrum for the juniper-recurrence LMU regressor — phased P1→P2→P3.

Read first: juniper-ml notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md (the ratified
design-of-record, v0.2.0; §8a = ratification, Appendix A = the 4 sub-agent reviews with the binding
constraints). The model lives in juniper-recurrence/juniper-recurrence-model/.

P1: extract a Readout protocol + LinearReadoutSpec(ridge=); LMURegressor delegates. Keep byte-identical
backcompat (the app imports LMURegressor/LMUSerializer directly): constructor signature, ridge=0.0
default (HARD invariant), _coef forwarding property, topology meta["d"]=memory order (recurrence
test_routes asserts ==4), model_type=="lmu", old-format LMUSerializer.load fallback. Add GCV ridge
(ridge="gcv": one SVD + 1-D search; persist selected λ); widen ridge: float|Literal["gcv"] into the app
schemas/CLI/settings. Resolves juniper-recurrence#28.

P2: RFFReadoutSpec = standardize(M, train-fold-only) → RFF √(2/D)cos(Wm+b) → GCV-ridge; design
[φ(standardize(M)) | target_dt | 1]; γ via median heuristic; D capped to smallest fold; persist W,b
(float64)+stats+γ+λ. Add the capacity dataset (y=x(t-τ1)·x(t-τ2)); RFF conformance subclass (bit-exact
round-trip gate + finite assertion); bench rows + findings update + HTTP readout enum.

P3 (GATED on a measured 2a lift): torch MLP behind a [torch] extra; CPU-only+single-dtype+
set_num_threads(1)+eval()+deterministic; state as named npz arrays (no torch.save; allow_pickle=False);
pin torch>=2.9 (cp314 ships; no Python ceiling); separate CI job + coverage exclusion.

Constraints (do not relitigate — design Appendix A): conformance has no fit-quality gate, the one sharp
constraint is bit-exact np.array_equal lossless serialization; RFF must per-column-standardize M (~25×
RMS disparity); use an immutable readout spec (crossval cross-fold safety); D-WS4-2 = readout takes M
only, target_dt stays linear. Existing datasets are at the linear ceiling → 2a ties there; the capacity
dataset shows the upside.

Conventions: feature/** branches (chore/docs miss push CI; squash to one clean commit if an
agents-md-touch-up [skip ci] ancestor appears); centralized worktrees in Juniper/worktrees/; Paul
merges all PRs + approves PyPI/deploy gates; juniper-data/juniper-ml main use rulesets (BLOCKED shows
for non-admins even when green — Paul admin-merges). Publishing = cut a GitHub Release (templated notes
to notes/releases/), never a bare tag push.

Verify start state (commands below).
```

## Verification of start state

```bash
# juniper-data 0.8.0 must be live on PyPI (Paul approves the pypi gate before this thread starts).
# If this prints 0.8.0, the bench reproduces from PyPI; if it 404s/lags, the gate is still pending —
# check the publish run or ask Paul before relying on the published wheel.
curl -fsS https://pypi.org/pypi/juniper-data/0.8.0/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
gh run list --repo pcalnon/juniper-data --workflow publish.yml --limit 1   # v0.8.0 run state (success ⇒ on PyPI)

# DP-3 design ratified + merged?
gh pr view 491 --repo pcalnon/juniper-ml --json state,title --jq '.state + " — " + .title'
gh pr view 198 --repo pcalnon/juniper-data --json state --jq .state      # v0.8.0 release-notes archive

# Bench env (for P2 capacity-dataset measurement). /tmp may be reaped — rebuild as needed:
python3 -m venv /tmp/benchenv
/tmp/benchenv/bin/pip install -e "<recurrence>/juniper-recurrence-model[test]" "juniper-data[equities]>=0.8.0" pytest
# Run the bench from the recurrence repo/worktree root: cd <recurrence> && /tmp/benchenv/bin/python -m bench.run_benchmark

# Open recurrence items
gh pr list --repo pcalnon/juniper-recurrence --state open
gh issue view 28 --repo pcalnon/juniper-recurrence --json state --jq .state   # readout-regularization follow-up (DP-3 P1 closes it)
```

## Conventions / gates (carry forward)

- **feature/** branches** (not chore/docs — they miss the push-CI trigger; an agents-md-touch-up
  `[skip ci]` ancestor can suppress runs → squash to one clean commit). Centralized worktrees in
  `/home/pcalnon/Development/python/Juniper/worktrees/`.
- **Paul merges all PRs and approves every PyPI / deploy gate.** juniper-data & juniper-ml `main` use
  rulesets — `mergeStateStatus` shows BLOCKED for non-admins even when green; Paul admin-merges.
- **Publishing = cut a GitHub Release** (templated notes archived to `notes/releases/`), never a bare
  `git push <tag>`. For juniper-data the Release's `published` event triggers `publish.yml`.
- **Pydantic gotcha** (why the bench pins `>=0.8.0`): `EquitiesParams` is `extra='ignore'`, so an
  older pin would silently drop `regression_target`.

## Git status at handoff

All repos clean on their default branches (fast-forwarded). Open PRs at handoff: juniper-data #198
(v0.8.0 notes archive); juniper-ml #491 (DP-3 design — ratified, likely merged) + this handoff PR.
juniper-data `v0.8.0` Release cut; `publish.yml` in progress / waiting at the PyPI gate (Paul's).
No in-progress edits. Session feature worktrees were cleaned up after their PRs merged.
