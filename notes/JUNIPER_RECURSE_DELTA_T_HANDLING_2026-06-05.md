# Juniper-Recurse — Irregular-Δt Datasets & Time/Δt Handling

**Project**: Juniper ML Research Platform — recurrent-model (juniper-recurse) data/Δt analysis
**Repository**: pcalnon/juniper-ml (analysis note; touches juniper-data, juniper-recurse, juniper-model-core)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (DRAFT — analysis & reference-design input; no code shipped on this basis until ratified)
**Last Updated**: 2026-06-05

---

> **Status:** DRAFT analysis note. **Planning/analysis only** — nothing here is implemented until the relevant workstream (WS-1 / WS-3 / WS-4) is opened and ratified.
> **Provenance:** Produced from a working session on irregular-Δt datasets. Grounded against the equities generator on disk (`juniper-data/juniper_data/generators/equities/generator.py` v1.0.0) and both halves of the recurse design:
> [`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md) (model) and
> [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) (refactor/contract).
> **Scope:** This note is effectively an addendum to the recurse model open questions on irregular-Δt handling (tracked there as **[OQ-7]**, model-owned; the separate NPZ-3-D-contract question is **[OQ-6]**, refactor-owned — see §4.4). It proposes concrete, C1-compliant answers and is intended as input to WS-1 (data contract), WS-3 (`juniper-model-core` interfaces), and WS-4 (the recurse model).

---

## 0. Purpose

Three deliverables, in increasing depth:

1. Define irregular-Δt datasets and their significance (§1).
2. Establish, from the code/docs as they actually are, (a) what the equities NPZ looks like today and how it must change to carry an explicit time/Δt channel (§2–§3), and (b) where the recurse design currently stands on Δt (§4).
3. Drive out the hand-waviness in three areas the working session left as sketches:
   - the `dt` / `observed_mask` NPZ-contract additions, with generator- and consumer-side reference code (§6);
   - the windowing-leakage property issue, with a runnable property test (§7);
   - Approach C — solver-free continuous-time integration at variable Δt via eigendecomposition, with the worked math and a reference implementation (§8).

---

## 1. Background: irregular-Δt datasets

### 1.1 Definition

**Δt** is the elapsed time between consecutive observations. A series is **regular** (uniformly/evenly sampled) when Δt is constant; **irregular-Δt** (a.k.a. *irregularly sampled*, *unevenly spaced*, *non-uniformly sampled*) when the gap varies step to step. Three related-but-distinct notions:

| Concept | What varies | Example |
|---|---|---|
| **Irregular sampling** | Time *between* observations | Lab drawn whenever a clinician orders it |
| **Asynchronous multivariate** | Different *channels* sampled at different times | Heart rate per minute, potassium per 12 h |
| **Missing data** | Values absent on an otherwise regular grid | Sensor dropout in a 1 Hz stream |

The general representation that subsumes all three is a **set of tuples** `(tᵢ, channelᵢ, valueᵢ)`, or per channel the pair `(tᵢ, xᵢ)` plus a per-channel time-since-last-observation.

**Causes:** event-driven processes (trades, clicks, spikes), human/operational cadence (EHR labs), **calendar effects** (markets skip weekends/holidays), sensor dropout/satellite revisit, deliberate adaptive sampling.

### 1.2 Why it is hard

Standard sequence models assume *a step is a step*: RNN/LSTM/GRU advance once per observation regardless of elapsed time; 1-D CNNs convolve evenly spaced taps; ARIMA/spectral methods are defined on a fixed grid. Feeding irregular data as-if-regular asserts that a 3-day weekend gap equals a 1-day gap, discarding timing that is frequently the signal. Two amplifiers:

- **The gap is informative.** A lab is ordered *because* a patient is deteriorating; the presence/timing of an observation carries information ("informative sampling/missingness"). Gridding destroys it.
- **Naive fixes inject bias.** Bin-to-grid + impute fabricates structure, blurs timing, and the grid resolution is itself a bias/variance knob.

### 1.3 The landscape of principled approaches

| Approach | Core idea | Tradeoff |
|---|---|---|
| Resample + impute | Snap to a grid, fill gaps | Simplest; biased, timing-lossy |
| Δt as a feature | Append gap / time-since-last / Time2Vec encodings | Cheap, strong; model must *learn* to use it |
| Time-gated RNNs (Phased-LSTM, **GRU-D**) | Decay state toward baseline as f(Δt) | Clinical workhorse; still discrete-event |
| Continuous-time / Neural-ODE (ODE-RNN, **Latent-ODE**, LTC, CfC) | Hidden state is a dynamical system; integrate forward by Δt | Principled; solver cost / transparency hit |
| Continuous-time attention (**mTAN**, **SeFT**) | Attention over `(t, value)` with continuous-time encodings; series-as-set | Scales to very irregular/async; no recurrence |
| Temporal point processes (Neural Hawkes) | Model the intensity λ(t) — timing *is* the target | Right when "when is the next event" is the question |
| Gaussian processes / path signatures | Native arbitrary time points / sampling-invariance | Strong priors; cost at scale |

Canonical references: GRU-D (Che et al. 2018), Latent-ODE (Rubanova/Chen/Duvenaud 2019), mTAN (Shukla & Marlin 2021), SeFT (Horn et al. 2020), Neural Hawkes (Mei & Eisner 2017).

### 1.4 Significance

- It is a **correctness** issue, not polish: ignoring Δt biases toward the over-sampled regime and conflates fast/slow dynamics.
- It is a **data-representation** decision made at the dataset layer: committing to time-awareness forces a representation (explicit Δt channel, `(t, value, mask)` triples) that then constrains every model and loader downstream.
- It is the origin of **continuous-time deep learning** (Neural ODEs, continuous-time attention) — choosing how to handle Δt places the platform on a mapped frontier rather than in ad-hoc territory.

### 1.5 Applications

Healthcare/clinical EHR (the motivating domain; MIMIC, PhysioNet); finance (ticks, market-closure daily bars, mixed-frequency); astronomy (telescope light curves); climate/remote-sensing/IoT; user behavior (clickstreams, churn); neuroscience/geophysics (spike/seismic point processes).

### 1.6 Why this lands on Juniper now

- **equities** (juniper-data #164): S&P 500 *daily* OHLCV has the textbook market-closure irregularity (Fri→Mon = 3 calendar days; holidays more) plus SEC-EDGAR fundamentals at irregular quarterly filing dates → an asynchronous multi-rate panel. The synthetic WS-1 generators (multi-sine, Mackey-Glass, AR(p)) are *regular* by construction, so **equities is the platform's natural first irregular-Δt benchmark**.
- **juniper-recurse**: the new recurrent model has to take a position on Δt; the "3-D NPZ + `task_type` + `temporal_split`" plan is exactly the representation question (§4).
- **CasCor angle**: Recurrent Cascade-Correlation has no native Δt notion and separately carries the star-free representational ceiling under research in [OQ-4]. Those are *two distinct* limits (can't express *when*; can't express certain *whats*) — see §4.5.

---

## 2. The equities NPZ today (grounded)

Source: `juniper-data/juniper_data/generators/equities/generator.py` (v1.0.0); feature list in `…/equities/defaults.py`; params in `…/equities/params.py`.

- **Not a sequence dataset.** Every `X_*` is **2-D `(n_samples, 10)`** — one row per ticker-day. Features (in order): `open, high, low, close, volume, week52_high, week52_low, total_shares, market_cap, cost_basis` (`defaults.py` `EQUITIES_FEATURE_COLUMNS`). No timesteps axis.
- **Targets are per-row.** `y_*` `(N, 2)` one-hot `[down, up]` next-day direction (`generator.py:428–436`); `y_reg_*` `(N, 1)` next-day close (`generator.py:198`, `next_close = close.shift(-1)` at `:310`).
- **Dates already exist, carried beside the features.** `date_*` `(N,)` `int32` as `YYYYMMDD` (`generator.py:439–443`, `frame.index.strftime("%Y%m%d")`). The pandas `DatetimeIndex` that knows weekends/holidays is used during conditioning and then dropped. **The Friday→Monday gap is implicit** — recoverable only by diffing `date_*`.
- **Split is per-ticker chronological `iloc`** (`generator.py:173–184`): for each ticker, first `round(n·train_ratio)` rows → train, next `round(n·test_ratio)` → test, concatenated across tickers. Default 80/20. Invariant tested: per ticker `max(date_train) ≤ min(date_test)`.
- **16 keys total**: `X_/y_/y_reg_/ticker_code_/date_` × `{train,test,full}` + `ticker_vocab`. Sidecar `…​.meta.json` holds params/dims/checksums.

**Takeaway:** today's artifact is a *flat tabular* dataset that retains a date column. The Δt signal is present in `date_*` but unused, and there is no per-step axis to attach it to.

---

## 3. Evolving the equities NPZ to carry time/Δt

### 3.1 The change is two steps

1. **Window the flat rows into 3-D sequences** — `X_{split}: (N,10) → (W, L, 10)` for lookback `L`, sliding *within each ticker only* (a window spanning a ticker boundary is a Frankenstein sequence — the bug §7 guards).
2. **Derive Δt from the existing `date_*` arrays** — decode `YYYYMMDD → ordinal → diff`; weekend/holiday gaps fall out for free.

### 3.2 Schema delta

| Key | Today | Proposed 3-D sequence variant |
|---|---|---|
| `X_{split}` | `(N, 10)` f32 | `(W, L, 10)` f32 |
| `y_{split}` | `(N, 2)` f32 one-hot | `(W, 2)` f32 — aligned to the step *after* the window's last day |
| `y_reg_{split}` | `(N, 1)` f32 | `(W, 1)` f32 — `next_close` after window end |
| `date_{split}` | `(N,)` i32 YYYYMMDD | `(W, L)` i32 — per-step dates retained |
| `ticker_code_{split}` | `(N,)` i32 | `(W,)` i32 — one per window (invariant: no cross-ticker window) |
| `ticker_vocab` | `(T,)` str | unchanged |
| **`dt_{split}`** *(new)* | — | `(W, L)` f32 — per-step elapsed **calendar days** since previous step; `dt[:,0]=0` |
| **`target_dt_{split}`** *(new)* | — | `(W,)` f32 — gap from the window's last day to the predicted day |
| **`window_end_date_{split}`** *(new)* | — | `(W,)` i32 — target alignment anchor |
| **`observed_mask_{split}`** *(new, optional)* | — | `(W, L)` u8 — 1=real, 0=imputed (all-ones in trading-day-native mode) |
| **`padding_mask_{split}` / `seq_lengths_{split}`** *(new, optional)* | — | ragged early-history windows (first `L-1` days/ticker) |

`meta.json` additions: `lookback=L`, `sequence=true`, `time_unit="calendar_days"`, Δt normalization stats, target (next_close) denormalization params, `generator_version` bump.

### 3.3 Three subtleties

1. **The target horizon is also irregular.** "Next trading day" from a Friday is a 3-day-ahead prediction; from a Tuesday, 1-day. Hence `target_dt_{split}` is first-class — a Δt-aware model and its metrics should know the prediction reaches different distances on different rows.
2. **Trading-day-native vs. resample.** Default to **trading-day-native + Δt** (`observed_mask` all-ones; `dt` carries the irregularity). Resampling to calendar-daily fabricates ~2/7 of the series; if used, mark fabricated steps in `observed_mask`.
3. **Back-compat posture (honors [OQ-6] additive-only).** The `X` shape changes 2-D→3-D, so this is a **new variant** (a `lookback`/`sequence=True` param or a sibling `equities_seq` dataset id), not an in-place mutation. The existing 2-D artifact stays byte-identical; new keys are optional; consumers dispatch on `X.ndim`.

---

## 4. juniper-recurse's current stance on Δt

**Verdict: Δt-aware at the *survey* level, Δt-deferring at the *decision* level.**

### 4.1 The survey knows the right tools and rejects them on C1 grounds

- Candidate table (model §1.2, row 7) flags Neural ODE / Latent ODE / ODE-RNN as *"Best for irregular Δt; low transparency."*
- §1.4 defers them: *"LTC / Neural ODE / Latent ODE — deferred. Best-in-class for irregularly-sampled series (Rubanova et al. 2019), but the **ODE-solver dependency undercuts C1 transparency** and there is no clean cascor structural mapping. Revisit if irregular-Δt datasets become central."*

C1 (model §0.3 / refactor §0.3): *first-principles implementation, no library black box.* The deferral premise — *handling Δt requires a solver black box* — is what §5/§8 challenge.

### 4.2 The planned contract is implicitly regular-Δt

Refactor §2.4 specifies the 3-D NPZ as `(samples, timesteps, features)` with optional `seq_lengths`, `padding_mask`, `scaling` — **but no time or Δt key.** It represents *sequence position*, never *elapsed time*.

### 4.3 All three short-listed models assume regular Δt — with one latent exception

- **RCC** (§1.3.1): discrete one-step self-delay; no elapsed-time notion.
- **Growing ESN** (§1.3.2): doc caveats *"classic ESN assumes regular Δt"* (§1.2, R4 note).
- **LMU** (§1.3.3): the only hook — *"Continuous-time formulation adapts to step size (window θ, Δt)"* and a guardrail to expose *"θ/Δt as inspectable, validated hyperparameters."* But θ/Δt is treated as a **fixed scalar**, not a **per-observation input**. The machinery is present; the dots to variable Δt are unconnected (closed in §8).

### 4.4 Open-question tracking

The irregular-Δt question is **model-owned**, tracked as **[OQ-7]** (model §1.4 and §1.6: *"When do irregular-Δt datasets … become relevant? Lean: defer; §1.4"*). The distinct **NPZ-3-D-contract** question (§6) is **refactor-owned** as **[OQ-6]** (refactor §2.4/§2.9). Two separate questions, two identifiers — consistent across both halves: the model half intentionally omits [OQ-6] (the refactor half owns it; the consolidated table lives in refactor Part 5).

> **Working-copy caveat (2026-06-06):** a concurrent, *uncommitted* edit to the main-repo checkout was mid-rewrite of model §1.6 (adding `Answer-N` blocks and renumbering this question `[OQ-7]→[OQ-6]`), which **would** collide with the refactor's [OQ-6]. That divergence is not on `origin/main`; if it lands, re-assert [OQ-7] for the irregular-Δt question.

### 4.5 Orthogonality to [OQ-4]

Δt handling is **orthogonal** to RCC's star-free ceiling: adding Δt awareness does not fix the no-count limitation, and fixing the ceiling (group-implementing units / NEAT / ESN-first) does not address Δt. But the two are **coupled at the model-pick level**: an [OQ-4] resolution toward **ESN** makes Δt *harder* (ESN assumes regular Δt); toward **LMU** makes it *easier* (§8 is native). State this so the two reviews do not collide.

---

## 5. Design approaches A–D (summary)

The crux: the design boxed itself in — *best Δt tool needs a solver → solver breaks C1 → defer Δt.* The missing observation: **continuous-time Δt handling does not require an ODE solver** (§8). Four approaches, cheapest→most principled:

| | A — Δt as input channel | B — Δt-gated decay | C — solver-free continuous-time (LMU) | D — resample+impute |
|---|---|---|---|---|
| **Mechanism** | Feed `dt` as an extra input dim | `h ← h·exp(−Δt/τ)`, learnable per-unit τ | Discretize LMU linear memory at the actual per-step Δt (§8) | Grid + impute in juniper-data, mark `observed_mask` |
| **Models** | RCC/ESN/LMU unchanged | RCC + ESN + LMU | **LMU only** | all (unchanged) |
| **C1** | cleanest (Δt is data) | clean (exp is elementary) | clean (matrix-exp of a fixed closed-form matrix) | clean (no model change) |
| **Bias strength** | weak (must learn) | strong (real-time forgetting) | strongest (true continuous memory) | n/a (lossy) |
| **Key weakness** | presentation, not mechanism | perturbs ESP (ESN) / freeze (RCC) | advantages 3rd-priority unit; matrix-exp cost | fabricates data; informative-sampling lost |
| **Primary guardrail** | shuffle-`dt` degradation test | variable-Δt ESP/delay tests | grid-invariance delay test (§8.6) | mask must be consumed |

Detailed strengths/weaknesses/limitations/risks/guardrails for each are in the working analysis; the deep dives below make A/C/the-leakage-test concrete.

---

## 6. DEEP DIVE — the `dt` / `observed_mask` data contract

This is the connective tissue: a single additive contract change serves approaches A–D and is populated for free by equities' existing `date_*`.

### 6.1 Canonical key specification (3-D sequence artifacts)

All keys are per split `{train,test,full}`. `W` = #windows, `L` = lookback, `F` = features.

| Key | Shape | Dtype | Required? | Semantics |
|---|---|---|---|---|
| `X_{split}` | `(W, L, F)` | f32 | yes (3-D) | feature sequence |
| `y_{split}` / `y_reg_{split}` | `(W, C)` / `(W, R)` | f32 | yes | target at the step after window end |
| `t_{split}` | `(W, L)` | f64 | one of {`t`,`dt`} | **absolute** time per step, in `time_unit` |
| `dt_{split}` | `(W, L)` | f32 | one of {`t`,`dt`} | **relative** elapsed time, `dt[:,0]=0`, `dt[:,k]=t[:,k]−t[:,k−1]` |
| `target_dt_{split}` | `(W,)` | f32 | recommended | elapsed time from last step to the predicted step |
| `observed_mask_{split}` | `(W, L)` | u8 | optional | 1=real observation, 0=imputed/synthetic |
| `padding_mask_{split}` | `(W, L)` | u8 | optional | 1=valid step, 0=structural padding (ragged length) |
| `seq_lengths_{split}` | `(W,)` | i32 | optional | count of valid (non-padded) steps |

Contract rules:
- **`X.ndim` dispatch:** `ndim==2` → legacy tabular path (byte-identical, no new keys required); `ndim==3` → sequence path.
- **At least one of `{t, dt}`** must be present for a 3-D artifact. If both, they must be consistent to tolerance (validator §6.4).
- **`dt ≥ 0`** everywhere; `dt[:,0] == 0` by convention (no predecessor).
- `time_unit` is declared **once** in `meta.json` (e.g. `"calendar_days"`); all `t`/`dt` are in that unit.

### 6.2 `padding_mask` vs `observed_mask` — distinct, do not conflate

The refactor doc lists only `padding_mask`. Two different ideas are needed:

- **`padding_mask`** answers *"does this step exist?"* — used when ragged sequences are padded to a common `L`. A padded step has no data at all.
- **`observed_mask`** answers *"is this existing step real or fabricated?"* — used when an irregular series is resampled onto a grid (Approach D). The step exists (padding=1) but was imputed (observed=0).

`observed_mask` is only meaningful where `padding_mask==1`. In **trading-day-native** mode `observed_mask` is all-ones (nothing imputed) and `dt` alone carries the irregularity.

### 6.3 Generator-side reference: equities windowing → all keys

Self-contained reference for one ticker. The real generator calls this per ticker (frames already sorted ascending by date) and concatenates; `cut_ordinal` is the ticker's test-boundary date from the existing `iloc` split.

```python
# juniper_data/generators/_sequence.py  (REFERENCE — not yet shipped)
from __future__ import annotations
import datetime as _dt
import numpy as np


def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    """(N,) int32 YYYYMMDD -> (N,) int64 proleptic-Gregorian ordinals."""
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64,
        count=len(dates),
    )


def window_one_ticker(
    feats: np.ndarray,        # (N, F) float32, ascending by date
    dates_yyyymmdd: np.ndarray,  # (N,)  int32  YYYYMMDD, ascending, strictly increasing
    y_dir: np.ndarray,        # (N, C) float32  target-for-next-step (row i predicts day i+1)
    y_reg: np.ndarray,        # (N, R) float32
    ticker_code: int,
    *,
    lookback: int,
    cut_ordinal: int,         # first test-period date (ordinal); train iff target_time < cut
    embargo: bool = False,    # drop test windows whose lookback reaches before cut
) -> dict[str, dict[str, np.ndarray]]:
    """Build fixed-length windows for one ticker, split into train/test by target time.

    Window ending at row i (L<=i+1<=N) uses steps [i-L+1 .. i] and predicts day i+1,
    so valid i in [lookback-1, N-2].  No window ever crosses a ticker boundary because
    this function only ever sees ONE ticker (that is the whole point — see notes §7).
    """
    n, f = feats.shape
    ords = _yyyymmdd_to_ordinal(dates_yyyymmdd)
    if not np.all(np.diff(ords) > 0):
        raise ValueError("dates must be strictly increasing within a ticker")

    cols = {k: {"train": [], "test": []} for k in
            ("X", "y", "y_reg", "date", "dt", "target_dt", "window_end_date", "ticker_code")}

    for i in range(lookback - 1, n - 1):           # window end; target at i+1
        lo = i - lookback + 1
        target_time = int(ords[i + 1])
        split = "train" if target_time < cut_ordinal else "test"
        if split == "test" and embargo and int(ords[lo]) < cut_ordinal:
            continue                                # purge windows straddling the cut

        win_dates = dates_yyyymmdd[lo : i + 1]      # (L,)
        win_ords = ords[lo : i + 1].astype(np.float32)
        dt = np.empty(lookback, dtype=np.float32)
        dt[0] = 0.0
        dt[1:] = np.diff(win_ords)                  # calendar-day gaps (weekends => 3, etc.)

        cols["X"][split].append(feats[lo : i + 1])
        cols["y"][split].append(y_dir[i])           # target for day i+1
        cols["y_reg"][split].append(y_reg[i])
        cols["date"][split].append(win_dates)
        cols["dt"][split].append(dt)
        cols["target_dt"][split].append(np.float32(ords[i + 1] - ords[i]))
        cols["window_end_date"][split].append(dates_yyyymmdd[i])
        cols["ticker_code"][split].append(np.int32(ticker_code))

    def _stack(key, split, dtype):
        items = cols[key][split]
        if not items:
            # preserve rank so np.concatenate across tickers is well-defined
            shape = {"X": (0, lookback, f), "y": (0, y_dir.shape[1]),
                     "y_reg": (0, y_reg.shape[1]), "date": (0, lookback),
                     "dt": (0, lookback), "target_dt": (0,),
                     "window_end_date": (0,), "ticker_code": (0,)}[key]
            return np.empty(shape, dtype=dtype)
        return np.asarray(items, dtype=dtype)

    out = {}
    for split in ("train", "test"):
        out[split] = {
            "X": _stack("X", split, np.float32),
            "y": _stack("y", split, np.float32),
            "y_reg": _stack("y_reg", split, np.float32),
            "date": _stack("date", split, np.int32),
            "dt": _stack("dt", split, np.float32),
            "target_dt": _stack("target_dt", split, np.float32),
            "window_end_date": _stack("window_end_date", split, np.int32),
            "ticker_code": _stack("ticker_code", split, np.int32),
            # trading-day-native: nothing imputed, no padding (fixed L)
            "observed_mask": np.ones((_stack("X", split, np.float32).shape[0], lookback), np.uint8),
        }
    return out
```

Notes:
- `cut_ordinal` is derived exactly as the current generator derives its row split (`round(n·train_ratio)`), then mapped to `ords[n_train]` — so the sequence variant reuses the existing, tested split boundary rather than inventing a new one.
- Ragged early history (first `L−1` days of a ticker) is simply *not emitted* here (windows start at `i=lookback−1`). If short series must be kept, pad to `L`, set `padding_mask`, and populate `seq_lengths` — left as an optional extension.

### 6.4 Consumer-side reference: `X.ndim`-dispatching validator

For `juniper-data-client` (and any shape-validating consumer). Keeps the 2-D path untouched; enforces the 3-D rules in §6.1.

```python
# juniper_data_client/contract.py  (REFERENCE — not yet shipped)
import numpy as np


def validate_npz_contract(z, *, time_unit: str | None = None, dt_atol: float = 1e-6) -> str:
    """Return 'tabular' or 'sequence'; raise ValueError on contract violation."""
    X = z["X_full"] if "X_full" in z else z["X_train"]
    if X.ndim == 2:
        return "tabular"                              # legacy path, byte-identical
    if X.ndim != 3:
        raise ValueError(f"X must be 2-D or 3-D, got {X.ndim}-D")

    for split in ("train", "test", "full"):
        xk = f"X_{split}"
        if xk not in z:
            continue
        x = z[xk]
        W, L, _F = x.shape
        has_t, has_dt = f"t_{split}" in z, f"dt_{split}" in z
        if not (has_t or has_dt):
            raise ValueError(f"{split}: 3-D artifact needs at least one of t_/dt_")

        if has_dt:
            dt = z[f"dt_{split}"]
            if dt.shape != (W, L):
                raise ValueError(f"dt_{split} shape {dt.shape} != {(W, L)}")
            if np.any(dt < 0):
                raise ValueError(f"dt_{split} has negative gaps")
            if W and np.any(dt[:, 0] != 0):
                raise ValueError(f"dt_{split}[:,0] must be 0 by convention")
        if has_t and has_dt:                          # consistency of the redundant pair
            t = z[f"t_{split}"]
            recon = np.zeros_like(t)
            recon[:, 1:] = np.diff(t, axis=1)
            if not np.allclose(recon, z[f"dt_{split}"], atol=dt_atol):
                raise ValueError(f"{split}: t_ and dt_ inconsistent")

        for mkey in (f"observed_mask_{split}", f"padding_mask_{split}"):
            if mkey in z:
                m = z[mkey]
                if m.shape != (W, L):
                    raise ValueError(f"{mkey} shape {m.shape} != {(W, L)}")
                if not np.isin(m, (0, 1)).all():
                    raise ValueError(f"{mkey} must be binary")
        if f"observed_mask_{split}" in z and f"padding_mask_{split}" in z:
            obs, pad = z[f"observed_mask_{split}"], z[f"padding_mask_{split}"]
            if np.any((pad == 0) & (obs == 1)):       # observed only meaningful where padding==1
                raise ValueError(f"{split}: observed_mask=1 on a padded step")
    return "sequence"
```

### 6.5 `scaling` / `meta.json` extension

Add, alongside the existing params/dims/checksums:

```json
{
  "sequence": true,
  "lookback": 64,
  "time_unit": "calendar_days",
  "dt_scaling": {"method": "standardize", "mean": 1.42, "std": 0.93, "max": 4.0},
  "target_scaling": {"y_reg": {"method": "identity"}},
  "masks": {"observed": true, "padding": false}
}
```

`dt_scaling` exists because Approach A feeds `dt` as a model input — unnormalized calendar-day magnitudes (1–4, holidays larger) want standardizing; the denorm params let canopy and the metrics layer report in real units. `target_scaling` records the (de)normalization for the regression target so `metrics()` can report MSE/MAE/R² in price units.

---

## 7. DEEP DIVE — windowing leakage & the property test

### 7.1 What "leakage" means here (three cases)

Each sample is `(window of L past steps, target at the step after the window)`. Conventionally the sample's *time* is its **target time**. The split must guarantee a model never trains on information from the test period. Three cases:

1. **Train sample with a future-reaching target — CATASTROPHIC.** If you window the *concatenated* series and assign windows to splits by raw index, a train window's target can land at/after the test boundary → the model trains on the answer it will be tested on. This is the leak to prevent.
2. **Test sample whose lookback reaches into the train period — USUALLY FINE.** Using known history to forecast the future is legitimate (walk-forward). Only forbid it when *strict* row-disjointness is wanted (the **embargo/purge** option, López de Prado): drop test windows whose lookback starts before the cut.
3. **Window crossing a ticker boundary — A BUG, always.** The concat-across-tickers layout makes naive windowing splice the tail of ticker A onto the head of ticker B into one "sequence." Never valid.

### 7.2 Correct construction

**Window per ticker, before concatenating** (exactly §6.3): case 3 becomes structurally impossible (the windower only ever sees one ticker), and split-by-target-time vs the ticker's own `cut_ordinal` makes case 1 impossible (a train window has `target_time < cut`, so both its window and target are pre-cut). Case 2 is allowed by default and removable via `embargo=True`.

### 7.3 The invariants

For any inputs, the emitted windows must satisfy:

- **I1 (no cross-ticker):** every step in a window shares one `ticker_code`.
- **I2 (no future leak):** per ticker, `max(train target_time) < min(test target_time)` — the window-level upgrade of the current per-row `max(date_train) ≤ min(date_test)`.
- **I3 (monotone time):** within each window, step dates strictly increase; `dt[0]==0`, `dt[1:]>0`, and `dt[1:] == diff(step_ordinals)`.
- **I4 (embargo, when enabled):** no test window's first step predates the ticker's `cut`.
- **I5 (target alignment):** `target_dt == ord(predicted_day) − ord(window_end_day) > 0`.

### 7.4 The property test (runnable)

Hypothesis-based, per the refactor doc's stated intent (§3, "Property-based testing (hypothesis): … temporal-split properties"). It builds windows via the §6.3 reference and asserts I1–I5. Running the *same* assertions against a naive concat-then-slide implementation fails I1 at every ticker boundary and I2 wherever a window straddles the cut — which is the regression class this test prevents.

```python
# juniper_data/tests/test_sequence_windowing_leakage.py  (REFERENCE)
import datetime as _dt
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from juniper_data.generators._sequence import window_one_ticker, _yyyymmdd_to_ordinal


def _ordinal_to_yyyymmdd(o: int) -> int:
    d = _dt.date.fromordinal(int(o))
    return d.year * 10000 + d.month * 100 + d.day


@st.composite
def _ticker_series(draw, min_len=4, max_len=40):
    """A single ticker: strictly-increasing IRREGULAR dates + random features/targets."""
    n = draw(st.integers(min_len, max_len))
    start = _dt.date(2000, 1, 3).toordinal()
    gaps = draw(st.lists(st.integers(1, 5), min_size=n - 1, max_size=n - 1))  # 1..5 day gaps
    ords = np.concatenate([[start], start + np.cumsum(gaps)]).astype(np.int64)
    dates = np.array([_ordinal_to_yyyymmdd(o) for o in ords], dtype=np.int32)
    feats = draw(st.lists(st.floats(-5, 5, allow_nan=False, allow_infinity=False),
                          min_size=n * 3, max_size=n * 3)).__iter__()
    X = np.fromiter(feats, dtype=np.float32, count=n * 3).reshape(n, 3)
    y_dir = np.eye(2, dtype=np.float32)[np.arange(n) % 2]            # deterministic stand-in
    y_reg = X[:, :1].copy()
    return X, dates, y_dir, y_reg


@settings(max_examples=200, deadline=None)
@given(
    series=st.lists(_ticker_series(), min_size=1, max_size=4),
    lookback=st.integers(2, 6),
    train_ratio=st.floats(0.5, 0.9),
    embargo=st.booleans(),
)
def test_windowing_invariants(series, lookback, train_ratio, embargo):
    per_ticker = []
    for code, (X, dates, y_dir, y_reg) in enumerate(series):
        n = len(dates)
        if n <= lookback + 1:
            continue
        ords = _yyyymmdd_to_ordinal(dates)
        cut_idx = min(round(n * train_ratio), n - 1)   # clamp: always leave >=1 test row
        cut = int(ords[cut_idx])                       # ticker's own test-boundary date
        out = window_one_ticker(X, dates, y_dir, y_reg, code,
                                lookback=lookback, cut_ordinal=cut, embargo=embargo)
        per_ticker.append((code, cut, out))

    for code, cut, out in per_ticker:
        tr, te = out["train"], out["test"]

        # I1 — no cross-ticker window (codes are per-window scalars here, but assert step-consistency)
        assert np.all(tr["ticker_code"] == code) and np.all(te["ticker_code"] == code)

        # I3 — monotone time inside each window
        for blk in (tr, te):
            if blk["X"].shape[0] == 0:
                continue
            d = blk["date"]
            step_ords = np.vectorize(lambda v: _dt.date(v // 10000, (v // 100) % 100, v % 100).toordinal())(d)
            assert np.all(np.diff(step_ords, axis=1) > 0)          # strictly increasing
            assert np.all(blk["dt"][:, 0] == 0)
            assert np.all(blk["dt"][:, 1:] > 0)
            assert np.allclose(blk["dt"][:, 1:], np.diff(step_ords, axis=1))

        # I2 — no future leak: every train target strictly precedes every test target
        def _target_ords(blk):
            we = blk["window_end_date"]
            we_ord = np.vectorize(lambda v: _dt.date(v // 10000, (v // 100) % 100, v % 100).toordinal())(we)
            return we_ord + blk["target_dt"].astype(np.int64)      # I5: target = end + target_dt
        if tr["X"].shape[0] and te["X"].shape[0]:
            assert _target_ords(tr).max() < _target_ords(te).min()

        # I5 — target strictly after window end
        for blk in (tr, te):
            if blk["X"].shape[0]:
                assert np.all(blk["target_dt"] > 0)

        # I4 — embargo purges straddling test windows
        if embargo and te["X"].shape[0]:
            first_step_ord = np.vectorize(
                lambda v: _dt.date(v // 10000, (v // 100) % 100, v % 100).toordinal()
            )(te["date"][:, 0])
            assert np.all(first_step_ord >= cut)


def test_concat_then_slide_would_leak():
    """Documents the bug the per-ticker construction prevents (illustrative, not shipped)."""
    # Two tickers concatenated; a naive global slide of length 3 over rows [A0 A1 | B0 B1 B2]
    # produces a window (A1, B0, B1) that splices two tickers -> violates I1.
    codes = np.array([0, 0, 1, 1, 1])
    L = 3
    bad = [tuple(codes[i - L + 1 : i + 1]) for i in range(L - 1, len(codes) - 1)]
    assert any(len(set(w)) > 1 for w in bad)           # at least one cross-ticker window exists
```

The two requirements that matter most in review: **I2** (no future leak) and **I1** (no cross-ticker splice). Both are *structural* once windowing is per-ticker and split-by-target-time — the test pins them so a future refactor toward a faster vectorized/concat implementation cannot silently reintroduce either.

---

## 8. DEEP DIVE — Approach C: solver-free continuous-time at variable Δt

This is the path that handles genuinely irregular Δt with a real continuous-time inductive bias **while satisfying C1** — no ODE solver, no autodiff through a solver, only a matrix exponential of a *fixed, closed-form* matrix. It turns the LMU from a fixed-Δt cell into an irregular-Δt-native one, and it is exactly the mechanism the SSM family (S4/S5/Mamba) uses for variable step size — cashing in the doc's own "LMU is the bridge to SSMs" framing (model §1.3.3).

### 8.1 The LMU continuous system

The LMU memory `m ∈ ℝ^d` (Legendre coefficients of the input history over a window of length `θ`) obeys

```
θ · ṁ(t) = A · m(t) + B · u(t)
```

with **fixed, closed-form** matrices (Voelker, Kajić & Eliasmith 2019; HiPPO-LegT, Gu et al. 2020):

```
A[i, j] = (2i + 1) · ( −1            if i < j
                       (−1)^(i−j+1)  if i ≥ j )
B[i]    = (2i + 1) · (−1)^i                              i, j ∈ {0, …, d−1}
```

`A`, `B` depend only on order `d` — **not learned, not data-dependent.** `θ` sets the memory window in real-time units (same unit as `dt`).

### 8.2 Zero-order-hold discretization at the actual per-step Δt

Write the continuous system as `ṁ = M m + N u` with `M = A/θ`, `N = B/θ`. Holding `u` constant across an interval of real duration `Δt` (zero-order hold) gives the *exact* discrete update

```
m_{k+1} = Ā(Δt) · m_k + B̄(Δt) · u_k
Ā(Δt) = exp(M · Δt) = exp((A/θ) · Δt)
B̄(Δt) = M⁻¹ (Ā(Δt) − I) N        (= A⁻¹(Ā − I) B, since M⁻¹N = A⁻¹B and θ cancels)
```

Standard LMU implementations bake `Ā`, `B̄` as **constants** for one fixed Δt. The only change for irregular sampling is to **evaluate `Ā`, `B̄` at the actual gap `Δt_k`** — i.e., the `dt` channel from §6 *is* the discretization step. (This is precisely the role of the per-step `Δ` parameter in S4/Mamba.)

### 8.3 The eigendecomposition closed form

`A` is a fixed `d×d` matrix; diagonalize it **once**: `A = V Λ V⁻¹`, `Λ = diag(λ_0, …, λ_{d−1})` (eigenvalues in conjugate pairs, all with negative real part → stable). Then per step, only **scalar** exponentials of the eigenvalues are needed:

```
z_i(Δt) = λ_i · Δt / θ
Ā(Δt) = V · diag( e^{z_i} )            · V⁻¹
B̄(Δt) = V · diag( expm1(z_i) / λ_i )  · (V⁻¹ B)
```

Derivation of the `B̄` factor: `M⁻¹(Ā−I)N = V diag(θ/λ_i) V⁻¹ · V(diag(e^{z_i})−I)V⁻¹ · (B/θ) = V diag( (e^{z_i}−1)/λ_i ) V⁻¹ B`; the `θ` cancels, and `(e^{z}−1)/λ = expm1(z)/λ`, with the removable singularity `→ Δt/θ` as `λ→0` (LMU's `A` has no zero eigenvalue, but handle it for hygiene).

**Cost:** `V`, `V⁻¹`, `Λ`, `V⁻¹B` are precomputed once (depend only on `d`, `θ`). Per step: `d` scalar `exp`/`expm1` + two `d×d` mat-vecs — or, if `dt` is quantized into buckets, cache `Ā`,`B̄` per bucket. No solver, no per-step matrix exponential from scratch.

### 8.4 Reference implementation (numpy, transparent)

```python
# juniper_recurse/units/lmu_varstep.py  (REFERENCE — not yet shipped)
import numpy as np


def lmu_matrices(d: int) -> tuple[np.ndarray, np.ndarray]:
    """Canonical LMU / HiPPO-LegT A, B (theta-free form: theta*m_dot = A m + B u)."""
    A = np.zeros((d, d))
    B = np.zeros((d, 1))
    for i in range(d):
        B[i, 0] = (2 * i + 1) * ((-1) ** i)
        for j in range(d):
            A[i, j] = (2 * i + 1) * (-1.0 if i < j else (-1.0) ** (i - j + 1))
    return A, B


class VariableStepLMUMemory:
    """Solver-free continuous-time LMU memory; discretizes at the per-observation Δt.

    C1: no ODE solver, no autodiff-through-solver — only scalar exponentials of the
    eigenvalues of a FIXED, closed-form matrix.  Fully inspectable.
    """

    def __init__(self, d: int, theta: float):
        if d < 1:
            raise ValueError("d >= 1")
        self.d, self.theta = d, float(theta)
        A, B = lmu_matrices(d)
        lam, V = np.linalg.eig(A)                 # one-time: A = V diag(lam) V^{-1}
        self.lam = lam
        self.V = V
        self.Vinv = np.linalg.inv(V)
        self.VinvB = self.Vinv @ B                # (d,1), precomputed

    def step_matrices(self, dt: float) -> tuple[np.ndarray, np.ndarray]:
        """Closed-form Ā(dt), B̄(dt) — real (d,d) and (d,1)."""
        z = self.lam * (dt / self.theta)          # (d,) complex
        Abar = (self.V * np.exp(z)) @ self.Vinv   # column-scale then recombine
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = np.expm1(z) / self.lam          # (e^z - 1)/lam, accurate via expm1
        fac = np.where(np.abs(self.lam) < 1e-12, dt / self.theta, fac)  # removable singularity
        Bbar = (self.V * fac) @ self.VinvB        # (d,1)
        return Abar.real, Bbar.real

    def rollout(self, u: np.ndarray, dt: np.ndarray) -> np.ndarray:
        """u:(T,) scalar input per step; dt:(T,) with dt[k]=t[k]-t[k-1], dt[0]=0 (unused).

        ZOH convention: u[k-1] is held across the interval (t[k-1], t[k]] of length dt[k],
        so the memory state out[k] summarizes history up to t[k].  out[0]=0 (empty window).
        """
        m = np.zeros((self.d, 1))
        out = np.zeros((len(u), self.d))
        for k in range(1, len(u)):
            if dt[k] <= 0:
                raise ValueError("dt[k]>0 required for k>=1 (strictly increasing time)")
            Abar, Bbar = self.step_matrices(float(dt[k]))
            m = Abar @ m + Bbar * u[k - 1]
            out[k] = m[:, 0]
        return out                                 # (T, d) — Legendre memory trajectory

    def decode_weights(self, rho: float) -> np.ndarray:
        """Linear readout reconstructing u(t - rho*theta), rho in [0,1], via shifted Legendre.

        d(rho)[i] = P_i(2*rho - 1).  Used by the grid-invariance test (§8.6); exact
        normalization is irrelevant there because the test compares two grids with the
        SAME readout, so any constant factor cancels.
        """
        from numpy.polynomial.legendre import Legendre
        x = 2.0 * rho - 1.0
        return np.array([Legendre.basis(i)(x) for i in range(self.d)])
```

### 8.5 Numerical guardrails

- **Eigenvector conditioning.** The LegT `A` becomes ill-conditioned in `V` for large `d` (Vandermonde-like). Keep `d` modest (LMU operates at `d ≈ 4…64`). For larger `d`, replace eigendecomposition with **Padé scaling-and-squaring** of `M·Δt` (`scipy.linalg.expm`-style) plus the integral form of `B̄`, with a documented error bound — slower but robust.
- **Stability is automatic for `Δt>0`:** `Re(λ_i)<0 ⇒ |e^{z_i}|<1`, so `Ā` is a contraction; no blow-up. Large `Δt/θ` simply drives memory toward zero (the window has fully turned over) — expected, not an error.
- **Use `expm1`** for `(e^{z}−1)/λ` to avoid catastrophic cancellation at small `z` (short gaps).
- **Caching.** If `dt` is quantized (e.g. calendar-day integers 1–7 for equities), there are only a handful of distinct gaps — precompute `Ā`,`B̄` per distinct `Δt` once and look them up. This removes the per-step eigen-recombination entirely.

### 8.6 The analytic delay-line, grid-invariance known-answer test

The whole point of variable-step discretization is that the memory represents the *continuous* history, so the reconstructed delayed signal should be (nearly) **invariant to the sampling grid**. Test:

1. Pick a smooth signal `u(t)=sin(ωt)` and a window `θ`.
2. Sample it on a **regular** grid `t^reg` and an **irregular** grid `t^irr` (random positive gaps) over the same span, with comparable mean spacing.
3. Roll out `VariableStepLMUMemory` on each; reconstruct `û(t_k − ρθ) = decode_weights(ρ) · m_k` for some `ρ∈(0,1]`.
4. Assert the irregular-grid reconstruction error is **within a small factor of** the regular-grid error (both small), i.e. the method does not degrade on the irregular grid:

```python
def test_lmu_grid_invariance():
    import numpy as np
    from juniper_recurse.units.lmu_varstep import VariableStepLMUMemory

    d, theta, omega, rho = 16, 1.0, 2.0, 1.0
    mem = VariableStepLMUMemory(d, theta)
    w = mem.decode_weights(rho)

    def err_on(times):
        times = np.asarray(times, float)
        dt = np.empty_like(times); dt[0] = 0.0; dt[1:] = np.diff(times)
        u = np.sin(omega * times)
        m = mem.rollout(u, dt)
        warm = times >= (times[0] + theta)                 # only score once the window is full
        recon = m @ w
        truth = np.sin(omega * (times - rho * theta))
        return np.sqrt(np.mean((recon[warm] - truth[warm]) ** 2))

    t_reg = np.linspace(0, 12, 240)
    rng_gaps = np.r_[0.02, np.random.default_rng(0).uniform(0.02, 0.08, 239)]
    t_irr = np.cumsum(rng_gaps)

    e_reg, e_irr = err_on(t_reg), err_on(t_irr)
    assert e_reg < 0.05                                    # the method works at all
    assert e_irr < 3.0 * e_reg + 0.02                      # irregular grid does not degrade it
```

This is the variable-Δt extension of the "analytic delay-line unit test" the model doc already calls for as the LMU known-answer anchor (§1.3.3 guardrail). A *fixed*-Δt discretization fails the `e_irr` bound on `t_irr`; the variable-step discretization passes — which is the proof Approach C delivers.

### 8.7 Verification status (empirical, 2026-06-05)

The §6.3 windowing, §8.4 LMU implementation, and §8.6 test were executed (numpy 2.4.4, Python 3.13) via `util/ad-hoc/verify_delta_t_reference_code.py`. Measured:

| Check | Result |
|---|---|
| LMU `A` (d=16) max eigenvalue real part | **−6.49** (< 0 → stable; no sign error) |
| Reconstruction RMSE `e_reg` (d∈{16,24}, ρ∈{0.5,0.8,1.0}) | **0.035** (under the 0.05 bound; ZOH-limited, ~flat in d/ρ) |
| Grid-invariance `e_irr` | **0.039–0.043** (≈1.15× `e_reg`; within `3·e_reg + 0.02`) |
| Windowing invariants I1–I5 (2-ticker irregular example) | **all hold** |

So the Approach-C math is correct as written, the stated tolerances hold with margin, and the windowing construction satisfies the leakage invariants. (`e_reg` is ZOH-floor-limited, not order-limited — increasing `d` past ~16 barely moves it at this step size; to drop it, shrink the mean step or use a higher-order hold.)

---

## 9. Consolidated risks, guardrails, open questions

| # | Risk | Guardrail |
|---|---|---|
| R-Δt-1 | Windowing future-leak (train target ≥ test cut) | Per-ticker windowing + split-by-target-time; property test I2 (§7.4) |
| R-Δt-2 | Cross-ticker Frankenstein windows | Window per ticker only; property test I1 |
| R-Δt-3 | "Δt presented ≠ Δt used" (Approach A false confidence) | Shuffle-`dt` degradation conformance test on a Δt-sensitive synthetic |
| R-Δt-4 | ESP no longer guaranteed under Δt-decay (Approach B, ESN) | Re-derive/empirically validate ESP washout at variable Δt |
| R-Δt-5 | Matrix-exp instability / V ill-conditioning (Approach C, large d) | Keep d≤~64; scaling-and-squaring fallback with error bound; `expm1` |
| R-Δt-6 | Resample fabricates data accepted as real (Approach D) | Always emit `observed_mask`; conformance test that ignoring it fails |
| R-Δt-7 | NPZ contract change ripples ecosystem | Additive-only; `X.ndim` dispatch; 2-D path byte-identical; version artifact |
| R-Δt-8 | C1 pushback on Approach C | "Transparent ≠ trivial": matrix-exp of a fixed closed-form matrix is fully inspectable, the opposite of an ODE-solver black box (cf. OQ-2 resolution) |

Open questions surfaced/clarified here:

- **[OQ-7] (irregular-Δt relevance):** reframed — supporting irregular Δt does **not** require the deferred Neural-ODE solver; Approaches A (free) and C (LMU-native, C1-clean) exist. The "lean: defer" should be revisited on *cost* grounds, independent of whether irregular-Δt datasets become "central."
- **[OQ-6] (NPZ 3-D extension):** §6 proposes the concrete optional-key set including `dt`/`t`/`observed_mask`/`target_dt`; confirm which land in WS-1 vs deferred.
- **New:** does `target_dt` (irregular prediction horizon) need to flow into the loss/metrics layer (weight or condition on horizon), or is it metadata only? (Recommend: expose to metrics; optional to the loss.)

---

## 10. Mapping onto existing workstreams

- **WS-1 (juniper-data, critical path):** §3 schema delta + §6 contract + §7 windowing/property test. Pure additive, populated for free by equities `date_*`. Lands the `dt`/`observed_mask`/`target_dt` keys and the sequence variant of equities.
- **WS-3 (`juniper-model-core` interfaces):** `TrainableModel.input_shape` already admits `(timesteps, features)`; add an optional capability flag for "consumes per-step Δt" so canopy/metrics can condition on it. Conformance kit gains the shuffle-`dt` test (R-Δt-3) and the masked-step test (R-Δt-6).
- **WS-4 (juniper-recurse):** Approach A needs no model change (just plumb `dt` as an input channel). Approach C (§8) is the LMU unit's variable-step discretization, gated behind [OQ-7] and the LMU unit type. Approach B is the RCC/ESN-compatible middle path if those remain priority units after [OQ-4].

---

## 11. Recommendation

1. **Land the contract first (WS-1):** §6 keys + §7 per-ticker windowing & property test, with the equities sequence variant as the first real consumer. Cheap, additive, independently useful, zero model risk.
2. **Default model handling = Approach A** (`dt` as an input channel) — works across RCC/ESN/LMU unchanged, maximally C1-clean.
3. **Principled target = Approach C** when irregular-Δt becomes a priority: it is the *only* option delivering true continuous-time semantics without violating C1, and it is essentially already designed — the LMU's own closed-form math, discretized at the per-step `dt`. This resolves the deferral's own bind (the doc deferred Δt believing the solution required an ODE solver; its third unit type already contains a solver-free one).

---

## Sources / cross-references

- Recurse model design: [`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md) §1.2–1.6, §3.2.
- Refactor/contract design: [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) §0.3 (C1–C5), §2.3–2.4, §2.8–2.9, §3.
- Equities generator: `juniper-data/juniper_data/generators/equities/{generator.py,defaults.py,params.py}` (v1.0.0).
- Δt / continuous-time literature: Che et al. 2018 (GRU-D); Rubanova, Chen & Duvenaud 2019 (Latent-ODE); Shukla & Marlin 2021 (mTAN); Horn et al. 2020 (SeFT); Voelker, Kajić & Eliasmith 2019 (LMU); Gu et al. 2020 (HiPPO); Mei & Eisner 2017 (Neural Hawkes); López de Prado 2018 (purged/embargoed CV).
```