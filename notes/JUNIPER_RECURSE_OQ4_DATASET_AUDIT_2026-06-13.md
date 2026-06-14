# Juniper Dataset Operational-Demand Audit — OQ-4 Requirement Validation

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 dataset audit
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-13

---

> **Provenance.** Produced 2026-06-13 by a maximal multi-agent audit workflow (123 sub-agents, ~6.5 M tokens, ~21 min, clean run): a 4-agent reality-brief → 13 per-dataset classifiers read against the live generators → 3-vote refutation of every counting + ceiling-required verdict (**all 13 fully survived**) → a 6-angle counting-requirement panel → synthesis → two critics (completeness 0.88, anti-hallucination 0.82). The critics caught one material error — **`equities_seq` was built *during* the run** and was initially mis-tagged planned; it is reclassified BUILT/VERIFIED throughout (see §2.1), which *strengthens* the verdict. The load-bearing conclusion — no dataset requires the ceiling-break, exception list EMPTY — is critic-confirmed.

---

## 1. Executive Summary

**The load-bearing verdict, stated first:**

> **No Juniper dataset — none of the 11 built generators (the 10 classic + the new `equities_seq`), none of the 3 planned synthetics — requires the star-free ceiling-break, and none requires genuine unbounded-exact-state recurrence.** Not one dataset scores **MODULAR-UNBOUNDED** on the counting axis. The exception list is **EMPTY**.

This **CONFIRMS** the OQ-4 architecture re-evaluation's load-bearing claim. The re-eval (`JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md` §1(B), §9, §12) rested its entire recommendation on a single deferred empirical premise: *the star-free ceiling matters only if the workload requires a genuine modulo/period/parity-counting function over arbitrary-length sequences, and forecasting a real-valued series is not such a function.* The re-eval explicitly deferred the proof to "the DATASET AUDIT" and predicted the outcome as "expected." **This audit is that validator, and the prediction holds.**

Reading every shipped generator's actual target construction (not the name) yields:

- **9 of 10 shipped generators** (spiral, xor, checkerboard, circles, moon, gaussian, mnist, arc_agi, csv_import) fail the **TEMPORAL gate**: each label is a per-row or per-grid function, and every one calls `shuffle_and_split`, making row order irrelevant. STATIC/SPATIAL ⇒ COUNTING = NONE, RECURRENCE = NONE, automatically.
- **The shipped SEQUENTIAL generators** (`equities`, and now `equities_seq`) have a **memoryless-in-length** target — `next_close = close.shift(-1)` (a 1-step real-valued forecast) and `direction_up = (next_close > close)` (sign of a 1-step return). COUNTING = NONE. Their hard axis is **irregular Δt**, which is *orthogonal* to the ceiling.
- **`equities_seq` — the 3-D windowed form the re-eval recommended — was built *during* this audit (2026-06-13).** Same memoryless-in-length targets (`y_reg = next_close`, `y_dir = direction_onehot`, `equities_seq/generator.py:129-130`) ⇒ COUNTING = NONE; it adds explicit per-step `dt` (`_sequence.py:113-116`), i.e. it *realizes* the irregular-Δt front — still without any counting.
- **The 3 planned synthetics** (multi_sine, mackey_glass, ar_p) are real-valued **regression** with fading or bounded-window memory, and **regular-Δt by construction**. None is modular. (INFERRED from their mathematics — they are NOT yet built.)

**Consequence for the model pick:** The ceiling-break strands — **P2** (group-units) and **P6** (NARX-MLP) — solve a problem the data does not pose, and are correctly **de-prioritized**. The OQ-4 decision correctly collapses to the only cross-cutting demand the data *actually* exhibits — **irregular Δt + fading memory** — selecting the lowest-risk genuinely-recurrent, Δt-capable, C1-clean, cascor-faithful option → **P3-C / LMU (Approach-C)**, with **P1** as a cheap genuine-hidden-recurrence increment.

**Single watch-item:** `arc_agi`. Its underlying *research* task could conceptually involve object-counting or symmetry-recursion, but its **shipped target** is a static, spatial, row-shuffled input-grid → output-grid map with no sequence axis. As built, it is ceiling-irrelevant. Re-audit only if a future generator exposes ARC reasoning as an ordered sequence with a sequence-length-dependent modular/group label.

---

## 2. Method, Provenance & Demand Taxonomy

### 2.1 Method

Every claim about a **shipped** dataset is **VERIFIED**: I opened and read each `<name>/generator.py`, traced the target construction (the line that assigns `y`), the feature assembly (the line that builds `X`), and the temporal handling (the presence/absence of a sequence axis, `shift`-based target, or `shuffle_and_split`). I cross-checked the `GENERATOR_REGISTRY` in `juniper_data/api/routes/generators.py`. I did **not** classify any dataset from its name.

Every claim about a **planned** synthetic (multi_sine, mackey_glass, ar_p) is **INFERRED**: there is no generator file to read. Build-absence is VERIFIED (`ls` of the generators directory + strict word-boundary grep over `juniper_data/`); the demand characterization is derived from the standard mathematical definition of each process plus the WS-4 plan intent (model doc OQ-5).

**VERIFIED** = generator opened, target construction read at the cited line.
**INFERRED** = planned synthetic, classified from standard mathematics + OQ-5 plan intent, not yet built.

> **Mid-audit reclassification (2026-06-13).** `equities_seq` was **built during this audit run** (directory mtime 19:39; `generator.py` + `params.py` + `__init__.py`, registered at `api/routes/generators.py:100`, with a test suite). The early reality-brief saw only the forward-reference in `_sequence.py`; the late critics caught the live generator (target re-read this session at `generator.py:129-130`). It is reclassified **BUILT/VERIFIED** throughout — which *strengthens* the verdict (another real sequential dataset, still COUNTING = NONE) and confirms the re-eval's recommended data-side follow-on is now shipped. The 3 synthetics (`multi_sine`/`mackey_glass`/`ar_p`) remain genuinely unbuilt (strict grep: zero hits).

### 2.2 The Operational-Demand Taxonomy

Each dataset is classified on five orthogonal axes. The definitions are load-bearing.

- **TASK TYPE** — classification | regression | mixed | other.
- **TEMPORAL STRUCTURE** — STATIC (i.i.d., row order irrelevant) | SEQUENTIAL (ordered, prediction depends on earlier steps) | SPATIAL (structure in space, not time). *Only SEQUENTIAL data is recurrence/ceiling-relevant.*
- **COUNTING DEMAND** (the ceiling-relevant axis) — NONE | THRESHOLD (count to a bound then saturate; counter-free / star-free-sufficient) | MODULAR-BOUNDED (mod-k over a bounded window; still star-free-sufficient in deployment) | **MODULAR-UNBOUNDED** (mod-k / parity over arbitrary-length sequences — the *only* bucket the star-free ceiling blocks; requires P2/P6).
- **RECURRENCE / MEMORY DEMAND** — NONE | BOUNDED-WINDOW (FIR, last ≤W steps) | FADING-MEMORY (IIR/ESN/LMU, decaying-but-unbounded; genuine recurrence but **not** counting) | UNBOUNDED-EXACT-STATE (must hold an exact unbounded quantity; co-occurs with MODULAR-UNBOUNDED and only there). Plus the effective HORIZON.
- **IRREGULAR Δt** — non-uniform time spacing (the P3-C / LMU front).

### 2.3 The Ceiling Theory in One Paragraph

Recurrent cascades (RCC, and by Sarrof-Veitsman-Hahn the whole SSM/LMU family) capture **exactly the star-free = aperiodic = counter-free = group-free regular languages** (re-eval §6; Knorozova-Ronca 2024; McNaughton-Papert 1971). The ceiling is a **group/cycle** boundary, not a memory-length boundary. What lives *above* it is precisely the ability to traverse a non-trivial group orbit over an **arbitrary-length** input — canonically a **mod-k counter / parity** that must stay correct as the sequence grows without bound (minimal break: C2 = mod-2 = parity). Two corollaries are decisive here: (a) counter-free automata **can** still count *to a threshold* ("≥N" then saturate) — star-free-sufficient, **no** group needed; (b) **fading memory ≠ counting** — an unbounded-but-decaying linear state (ESN/LMU/Mamba) sits *at* the ceiling by theorem and does **not** break it. The single discriminating question: *does the label require tracking a quantity modulo k (or any non-trivial group orbit) over an unbounded number of ordered steps?*

### 2.4 The Critical Disambiguations (the #1 audit-failure modes)

1. **XOR ≠ temporal parity.** `xor` is a STATIC 2-input logical op (a single-step function of two features of one point) — it is NOT a mod-2 count over a sequence. Never score `xor` as MODULAR-UNBOUNDED.
2. **Spatial periodicity ≠ temporal counting.** `checkerboard`'s `% 2` is a *spatial* parity of one static point's grid-cell indices — a periodic classification boundary in **space**, not a counter advanced over ordered time.
3. **Periodicity of a signal ≠ MODULAR-UNBOUNDED counting.** Predicting a periodic signal (multi_sine) needs memory of ≈one period = FADING/BOUNDED, not a counter of unbounded period. Trigonometry that parameterizes a *spatial* curve (spiral/moon/circles) is not a temporal cycle.
4. **Chaos ≠ counting.** mackey_glass needs long FADING memory of a delayed state on a bounded attractor, not exact unbounded counting.
5. **Autoregression ≠ counting.** ar_p needs the last p lags = BOUNDED-WINDOW memory.
6. **Static benchmarks** (spiral, moon, circles, gaussian, mnist) have NO temporal/recurrence/counting demand — geometric/visual i.i.d. tasks.
7. **Regression/forecasting a real-valued series is never a mod-k task** absent an explicit, demonstrated counting argument.

**The mandatory MODULAR-UNBOUNDED test:** a dataset may be scored MODULAR-UNBOUNDED *only* if one can exhibit two prefixes that (a) are arbitrarily long, (b) differ only in a count's residue mod k, and (c) demand different outputs — *and* show no bounded suffix distinguishes them. A name association is never sufficient.

---

## 3. The Demand Matrix

| Dataset          | Built?                         | Task              | Temporal         | Counting | Recurrence                  | Horizon                                       | Irreg-Δt              | Ceiling-break? |
|------------------|--------------------------------|-------------------|------------------|----------|-----------------------------|-----------------------------------------------|-----------------------|----------------|
| **spiral**       | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **xor**          | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **checkerboard** | ✅ VERIFIED                    | classification    | STATIC (spatial) | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **circles**      | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **moon**         | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **gaussian**     | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **mnist**        | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **arc_agi**      | ✅ VERIFIED                    | other (grid map)  | SPATIAL          | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **csv_import**   | ✅ VERIFIED                    | classification    | STATIC           | **NONE** | NONE                        | none                                          | no                    | **no**         |
| **equities**     | ✅ VERIFIED                    | mixed (dir + reg) | SEQUENTIAL       | **NONE** | FADING (bounded as shipped) | 1-step                                        | **YES**               | **no**         |
| **equities_seq** | ✅ VERIFIED (built 2026-06-13) | mixed (dir + reg) | SEQUENTIAL       | **NONE** | FADING/BOUNDED              | L (lookback default 64; ≤30 under cascor cap) | **YES (explicit dt)** | **no**         |
| **multi_sine**   | ❌ INFERRED                    | regression        | SEQUENTIAL       | **NONE** | FADING (~one period)        | ~one period                                   | no                    | **no**         |
| **mackey_glass** | ❌ INFERRED                    | regression        | SEQUENTIAL       | **NONE** | FADING (~τ delay)           | Lyapunov-capped                               | no                    | **no**         |
| **ar_p**         | ❌ INFERRED                    | regression        | SEQUENTIAL       | **NONE** | BOUNDED-WINDOW (p lags)     | ~p steps                                      | no                    | **no**         |

**Ceiling-break-required column is uniformly `no`. Counting column is uniformly `NONE`.**

---

## 4. Per-Dataset Notes

### Shipped (VERIFIED — generator read this session)

**spiral** — Classic two-spirals (n_spirals default 2, `spiral/defaults.py:8`). `_create_one_hot_labels` (`spiral/generator.py:177-195`) builds `y` as one-hot `(total_points, n_spirals)`; class = which contiguous spiral-arm block a point belongs to (`y[start_idx:end_idx, i] = 1.0`, :193). `X` is `(total_points, 2)` 2-D coords (`column_stack`, :146). The `np.sin/np.cos` at :135-141 parameterize a **spatial** curve, not a temporal cycle (disambiguation 3). `shuffle_and_split` (:46-53) permutes all rows → i.i.d. STATIC gate ⇒ COUNTING = NONE. The canonical cascor classification benchmark; sub-star-free, ceiling-irrelevant.

**xor** — STATIC 2-input logical op, **not** temporal parity (disambiguation 1). `X` is `(4n, 2)`, one 2-D point per row (`_generate_quadrant` :151-153; `vstack` :114). `y` is one-hot assigned **per quadrant** (:121-125): Q1/Q3 (x·y>0) → class 0, Q2/Q4 (x·y<0) → class 1 — i.e. `sign(x) XOR sign(y)` of two features of *one* point. `shuffle_and_split` (:48-55) → i.i.d. Shares only a *name* with the mod-2 parity language; no sequence axis exists to take a residue over. The #1 name-trap, refuted at source.

**checkerboard** — STATIC/SPATIAL, **not** a temporal modular counter (disambiguation 2). `X` is `(n_samples, 2)` uniform 2-D points (:80-83). Label is `labels = (x_idx + y_idx) % 2` (:99) where `x_idx, y_idx` are the **spatial grid-cell indices** of that single point (:90-97). The `% 2` operates on a spatial coordinate index — a periodic classification boundary in space — not on a count advanced over ordered time. `shuffle_and_split` (:46) → i.i.d. The literal `% 2` in source is the deliberate trap; it scores COUNTING = NONE.

**circles** — STATIC concentric-circles classification. `X` is `(n_samples, 2)` 2-D coords on two circles (outer/inner radius, :80-90). `y` is one-hot by which circle the point lies on (`y[:n_outer, 0]=1.0`, `y[n_outer:, 1]=1.0`, :99-101) — a function of one point's radius. `cos/sin` parameterize a spatial circle (disambiguation 3). `shuffle_and_split` (:46-53) → STATIC. COUNTING = NONE.

**moon** — Standard two-moons binary classification (NumPy-only). `X` is `(n_samples, 2)`: upper moon = `(cos θ, sin θ)`, lower moon offset by `(1.0, 0.5)` for θ in `linspace(0, π)` (:81-89). `y` one-hot by moon membership (:98-100). `cos/sin` parameterize a spatial half-circle, not a temporal oscillator. `shuffle_and_split` (:48-55) → STATIC. COUNTING = NONE.

**gaussian** — Static mixture-of-Gaussians. `samples = rng.standard_normal((n_per_class, n_features))` scaled by `class_std`, shifted by `centers[i]` (:89-90); class centers placed on a circle in **space** via `center_radius·cos/sin` (:122-124). `y` one-hot per-class block (:92). `shuffle_and_split` (:46-53) destroys the generation-time block ordering → STATIC. No `%`, no shift, no time axis. COUNTING = NONE.

**mnist** — Static handwritten-digit / fashion-item image classification (`Literal["mnist","fashion_mnist"]`, `params.py:24`). `X` reshaped to flat `(N, 784)` (flatten default True, `defaults.py:12`; :103-104); the 28×28 is a **spatial** image grid (`defaults.py:21-22`), not time. `y` digit one-hot `(N, 10)` (:106-111). Sourced from HuggingFace, `ds.shuffle`'d (:94), then `shuffle_and_split` (:59-66) → doubly i.i.d. COUNTING = NONE (disambiguation 6).

**arc_agi** — Spatial grid-pair reasoning. `_convert_tasks_to_arrays` (:188-208) pools demonstration pairs from all tasks: `pair["input"]` → `X`, `pair["output"]` → `y`, both `(N, 900)` flat (flatten default True) or `(N, 30, 30)` spatial; integer colors 0-9, `-1` pad (`_pad_grid` :229-237). The two 30×30 axes are **spatial** image dims, not time. `shuffle_and_split` (:71-78) pools and shuffles all pairs, collapsing per-task grouping (task_ids retained only as a side label) → no sequence axis in the NPZ. Recorded as task `other` (the target is a 900-value structured grid, not a scalar class), but COUNTING = NONE either way — **the watch-item**, adjudicated in §5/§8.

**csv_import** — Generic user-data import with a fixed STATIC contract *independent of file contents*. Output forced through `shuffle_and_split` (:53-60), default shuffle True (`params.py:59`) → any latent row order in a user's file is destroyed, so no sequence axis is ever exposed. `y` is per-row from a single `label_column` cell, unique labels sorted + index-mapped (:159-181). `X` is per-row numeric columns `(N, n_features)` (:149-162), no window axis, no `dt`. Even a CSV whose label encodes parity-of-something would be a precomputed memoryless per-row lookup. COUNTING = NONE by the contract.

**equities** — The only shipped generator with a real temporal axis; **mixed** task. **Dual targets:** regression `next_close = close.shift(-1)` (`equities/generator.py:310`) → `y_reg_*` `(N, 1)` (:198), and classification `direction_up = (next_close > close).astype(float32)` (:315) → one-hot `[down, up]` `(N, 2)` (`_direction_onehot` :428-436). **Features are flat `(N, 10)`** (`_raw_features` :414 over `EQUITIES_FEATURE_COLUMNS`, `defaults.py:50-61`) — **no lookback window axis** as shipped. **SEQUENTIAL** via per-ticker temporal split (train = earlier dates, test = later; `sort_index` :175, `iloc` :182-183) and `shift`-based target. **Irregular Δt from two sources:** (a) daily OHLCV over a trade-date `DatetimeIndex` skips weekends/holidays (Fri→Mon = 3 calendar days), dates carried `YYYYMMDD` int32 (`_dates_yyyymmdd` :443) but **no `dt_*` key emitted**; (b) async SEC-EDGAR quarterly fundamentals (latest-per-period-end :379-388) forward-filled onto the daily index (`reindex(...).ffill()` :290). The richest multi-step feature is `week52_high/low = rolling(252).max()/.min()` (:279-280) — a **bounded** FIR window, **not** `.expanding()`. **COUNTING = NONE**: the label is a 1-step function (real next-close; sign of a 1-step return), independent of sequence length. The registry's `task_type="classification"` (`generators.py:95`) is route-level argmax bookkeeping; the generator ships both targets, hence *mixed*. The distinguishing demand is **irregular Δt** (§6), orthogonal to the ceiling.

**equities_seq** — **BUILT 2026-06-13, during this audit (VERIFIED).** The 3-D windowed form of equities the re-eval recommended; now shipped on the data side. `EquitiesSeqGenerator.generate()` (`equities_seq/generator.py:65-149`) windows each ticker via `window_one_ticker` with `y_reg = next_close` and `y_dir = _direction_onehot` (`:129-130`) — the **same 1-step, memoryless-in-length targets** as equities ⇒ **COUNTING = NONE**. It adds the genuine sequential apparatus: per-step `dt = np.diff(win_ords)` calendar gaps + `target_dt` (`_sequence.py:113-123`), `observed_mask`, and a leakage-safe target-time split. Registered at `api/routes/generators.py:100` (`time_unit="calendar_days"`, unique in the registry); `lookback` default **64** (range 2–512, `params.py`). Recurrence **FADING/BOUNDED**; horizon = the lookback `L` (default 64), which cascor's stateless window would currently clip to ≤30. Ceiling-break **no** — it realizes the *irregular-Δt* front (§6), not counting.

### Planned synthetics (INFERRED — not built; classified from mathematics + OQ-5 intent)

*(`equities_seq` was reclassified BUILT and moved to the Shipped block above — it shipped during this audit.)*

**multi_sine** — `x(t) = Σᵢ Aᵢ sin(2π fᵢ t + φᵢ) + ε(t)`, a finite superposition of K sinusoids (model doc OQ-5 :347). Regression, SEQUENTIAL, regular Δt by construction (Δt-note :82). Memory is **FADING / O(K), constant in sequence length** — once the K frequencies/phases are resolved from a finite window (~longest beat period `1/min|fᵢ−fⱼ|`), prediction at any horizon is a closed-form evaluation. **COUNTING = NONE**: periodicity ≠ modular counting (disambiguation 3) — phase lives on a bounded torus and is *continuously tracked*, not counted; no two-arbitrarily-long-prefixes-differing-only-in-residue argument exists. A clean recurrent-regression smoke test, sub-ceiling.

**mackey_glass** — `ẋ(t) = β·x(t−τ)/(1 + x(t−τ)ⁿ) − γ·x(t)`, canonical chaotic regime β=0.2, γ=0.1, n=10, τ=17 (model doc OQ-5 :347). Regression, SEQUENTIAL, regular Δt. The delay τ makes the formal state space infinite-dimensional; a predictor needs a Takens delay-embedding window ~τ = **FADING memory**. Because the system is **chaotic** (positive Lyapunov exponent), the *useful* horizon is intrinsically capped by the Lyapunov time, not by counting depth. **COUNTING = NONE**: chaos is aperiodic on a **bounded attractor** with fading correlation (disambiguation 4) — the opposite of an unbounded modular counter. This synthetic stresses a *capability ceiling* along the **chaos/horizon** axis, **orthogonal** to the star-free counting ceiling.

**ar_p** — `xₜ = c + Σᵢ φᵢ xₜ₋ᵢ + εₜ`, εₜ ~ N(0, σ²) (model doc OQ-5 :347). Regression, SEQUENTIAL, regular Δt. The conditional mean depends on **exactly** the last p observations (textbook minimal sufficient statistic) = **BOUNDED-WINDOW** memory; influence of older values decays geometrically; the white-noise innovation caps the useful horizon at a few steps. **COUNTING = NONE — the clearest non-counting case** (disambiguation 5): a fixed-order linear recurrence is star-free-trivial (no group/cycle in any syntactic monoid); a width-p suffix is always sufficient.

---

## 5. The Counting-Requirement Verdict (Marquee Panel)

> **Does ANY Juniper dataset — shipped or planned — require MODULAR-UNBOUNDED counting (the only demand the star-free ceiling blocks)?**
>
> **NO. The exception list is EMPTY.**

**Why, axis by axis:**

- **9 shipped generators fail the TEMPORAL gate.** A non-sequential dataset is automatically COUNTING = NONE and RECURRENCE = NONE — there is no ordered token stream over which a residue mod k could be taken, so the mandatory MODULAR-UNBOUNDED argument is *unconstructable*. Verified by `shuffle_and_split` calls + single-row/single-grid labels in every generator.

- **The 1 shipped SEQUENTIAL generator (equities) is memoryless-in-length.** `next_close = close.shift(-1)` (:310) and `direction_up = (next_close > close)` (:315) are fixed 1-step functions; the label does not depend on sequence length. COUNTING = NONE.

- **The 3 planned synthetics are real-valued regression.** Forecasting a real-valued series is never a mod-k task (re-eval rule 7). multi_sine = periodicity ≠ counting; mackey_glass = chaos ≠ counting; ar_p = AR-lags ≠ counting. All INFERRED, all NONE.

- **The two name-traps are refuted at source.** xor is a static quadrant logical op (`xor/generator.py:121-125`); checkerboard's `% 2` is over **spatial** grid-cell indices of one static point (`checkerboard/generator.py:99`).

- **No UNBOUNDED-EXACT-STATE recurrence either.** An accumulator scan (`cumsum|cumprod|cummax|cummin|expanding|%|np.mod|parity|counter`) over every `*/generator.py` returned **exactly one** hit — checkerboard's spatial `(x_idx + y_idx) % 2` — and **zero** `cumsum/cumprod/expanding` anywhere. equities' richest multi-step feature is a *bounded* `rolling(252)` window, not `.expanding()`. UNBOUNDED-EXACT-STATE co-occurs with MODULAR-UNBOUNDED and only there; since no dataset scores the latter, none needs the former.

- **Registry corroboration.** `api/routes/generators.py` now has **11 entries** — it tags all 11 built generators (incl. `equities_seq` at `:100`, which uniquely carries `time_unit="calendar_days"`) `task_type="classification"`. There is **no `modular` / `counting` / `sequence-counting` task type anywhere in the codebase.**

**The watch-list (one item): `arc_agi`.** It is the sole dataset whose *underlying research problem* could conceptually involve counting/recursion (object-counting, symmetry-recursion). But the wildcard is **adjudicated REFUTED at the data-contract level**: the cascor target as constructed is a static, spatial, row-shuffled input-grid → output-grid map (`arc_agi/generator.py:188-226` + `split.py:109-113`) with no ordered token stream and no sequence-length-dependent modular/group quantity in `y`. Whatever latent abstraction a *solver* would need is not *exposed* as a temporal sequence in this NPZ. Per the mandatory TEMPORAL-first gate, the ceiling is simply not engaged.

---

## 6. The Irregular-Δt + Recurrence Demand — What the Data ACTUALLY Needs

The audit does not merely find an *absence* (no counting); it finds a *presence*. The one cross-cutting, genuinely-present demand in the Juniper corpus is **irregular Δt coupled with fading/bounded memory** — and it lives entirely in the equities line.

**equities (shipped) carries irregular Δt from two distinct sources, VERIFIED:**

1. **Market-closure irregularity.** Daily OHLCV over a trade-date `DatetimeIndex` skips weekends and holidays — Fri→Mon is a 3-calendar-day gap, holidays more. The gap is *informative* and is recoverable only by diffing `date_*` (`YYYYMMDD` int32, `:443`). No `dt_*` feature is emitted in the flat form.
2. **Asynchronous-fundamentals irregularity.** SEC-EDGAR shares-outstanding arrive at irregular quarterly filing dates (latest-per-period-end, `:378-388`), forward-filled onto the daily index (`reindex(...).ffill()`, `:290`) — an asynchronous multi-rate panel.

**The recurrence demand is FADING/BOUNDED, never unbounded-exact.** equities as shipped is flat `(N, 10)` with a bounded `rolling(252)` context; the genuine 3-D sequential form (`equities_seq`) is now **BUILT (2026-06-13)** and exposes explicit per-step `dt`/`target_dt` via `_sequence.py:106-125`, with state capped at the `lookback` (default 64; clipped to ≤30 under cascor's stateless window).

**Why this is the load-bearing axis and the ceiling is not:** irregular Δt is the "*can't express **when***" axis; the star-free ceiling is the "*can't express certain **whats***" (group/parity) axis. They are two distinct limits (re-eval §4.5, Δt-note §4.5). Adding Δt-awareness does not fix counting, and breaking the ceiling does not address Δt. **The data poses the former and not the latter** — which is exactly why the recommendation pivots to the Δt-capable option.

**The synthetics do NOT exercise this axis** — they are regular-Δt by construction (Δt-note :82). The platform's irregular-Δt benchmark is equities, full stop.

---

## 7. Validation of the OQ-4 Re-Evaluation Recommendation

**VERDICT: VALIDATED (confirm — does not overturn).**

The re-eval's load-bearing syllogism (`JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md` §1(B), §9, §12):

1. **Premise:** the star-free ceiling matters *only* if the target workload requires a genuine modulo/period/parity-counting function over arbitrary-length sequences (§9).
2. **Deferred empirical claim:** forecasting a real-valued series is NOT a mod-k task → the Juniper datasets pose no counting requirement. *Proof deferred to "the DATASET AUDIT"; outcome predicted "expected."*
3. **Conclusion:** the ceiling-break (P2/P6/hybrid) "solves a problem the data does not pose" and is de-prioritized; the decision collapses to *"which genuinely-recurrent, irregular-Δt-capable, C1-clean, cascor-faithful option is lowest risk?"* → **P3-C/LMU**, with **P1** as a cheap hidden-recurrence increment.

**This audit discharges step 2 by reading every generator's target construction.** Result: ZERO MODULAR-UNBOUNDED datasets among 10 shipped (VERIFIED) + 3 planned (INFERRED). The only actually-present cross-cutting demand is irregular-Δt + fading memory (equities, and now `equities_seq` — the 3-D `dt`/`target_dt` form, built on the data side during this audit). Therefore the ceiling-break addresses a capability **no current-or-planned dataset demands**.

**One-line consequence for the model pick:** *The OQ-4 decision correctly de-prioritizes P2/P6 and collapses to **P3-C / LMU (Approach-C)** — the only measured Δt win — with **P1** as the cheap genuine-hidden-recurrence increment.*

---

## 8. Watch-Items + What Dataset Class Would Change the Answer

**Watch-items (monitored, not currently triggering):**

- **`arc_agi`** — re-audit IF a future generator exposes ARC reasoning as an *ordered sequence* with a sequence-length-dependent modular/group label (e.g., a per-step state machine over a transformation trace). As shipped (spatial grid-pair map), it is ceiling-irrelevant.
- **`csv_import`** — a user *could* upload a real time series, but the generator emits no 3-D window, no `dt` key, and actively shuffles, so it cannot present an ordered-sequence (let alone counting) problem. Only a contract change (windowing + ordered split) would matter.
- **`equities_seq`** — now **built** on the data side (2026-06-13); it changes the *recurrence* exercise (FADING/BOUNDED + explicit Δt), **not** the counting verdict (still NONE). The remaining gate is the cascor `ndim>2` ingestion cap, not the generator's absence.

**What dataset class WOULD overturn the verdict (the trigger to re-open P2/P6):**

A dataset whose **target** is a function of a *count over the sequence* — concretely a label such as `(number of up-days so far) mod k`, parity of a sequence of events, `(ab)*` cyclic membership, or Dyck-1 depth-parity — i.e., a **sequence-length-dependent modular/group quantity** for which one *can* exhibit two arbitrarily-long prefixes differing only in a residue mod k that demand different outputs, with no bounded suffix sufficient. **No such target exists in the corpus today.** If one is added, the ceiling re-becomes load-bearing and the re-eval's §12 fallback (fund the P2 group-unit training recipe; P6 NARX-MLP as a representability reference) is the correct branch.

---

## 9. Claims Considered and NOT Supported

- **"`xor` is a parity/mod-2 counting task."** NOT SUPPORTED. `xor/generator.py:121-125` assigns one-hot per quadrant to a single static 2-D point; it is `sign(x) XOR sign(y)`, sharing only a name with the mod-2 parity language. STATIC, COUNTING = NONE.
- **"`checkerboard`'s `% 2` is a modular counter."** NOT SUPPORTED. The `% 2` (`checkerboard/generator.py:99`) operates on **spatial** grid-cell indices of one static point — spatial periodicity, not temporal counting.
- **"Predicting a periodic signal (multi_sine) requires an unbounded modular counter of the period."** NOT SUPPORTED (INFERRED). Periodicity needs frequency/phase resolution from a finite window (FADING, O(K)); phase is continuously tracked on a bounded torus, not counted.
- **"Chaotic forecasting (mackey_glass) needs exact unbounded state."** NOT SUPPORTED (INFERRED). Chaos is fading correlation on a bounded attractor; the limit is Lyapunov-time (horizon), not counting depth.
- **"Any forecasting target could secretly require mod-k counting."** NOT SUPPORTED. No generator computes any `cumsum/cumprod/expanding`/parity over the sequence; equities' richest feature is a *bounded* `rolling(252)` window. Re-eval rule 7 holds.
- **"ARC-AGI is a counting/recursion task, so the ceiling applies."** NOT SUPPORTED at the data-contract level. The *research problem* may involve counting; the *shipped target* is a static spatial grid map with no sequence axis (§5 adjudication). Scope caveat: this is a statement about the supervised target the cascade receives, not about the unsolved general ARC reasoning problem.
- **"The recurrent path is already exercisable end-to-end."** NOT SUPPORTED — but **out of scope** for this *data* audit. `equities_seq` is now **built + registered** on the data side (so the data half is done), but juniper-cascor's `SharedTrainingMemory` still caps `ndim > 2` (`juniper-cascor/src/cascade_correlation/cascade_correlation.py:272-273`). That cascor-side ingestion gate bounds how *soon* P3-C can be exercised; it neither confirms nor overturns the forecasting ≠ counting claim.

---

## 10. Recommendation + Open Questions

**Recommendation:**

1. **Adopt the audit verdict as the discharge of the re-eval's deferred validator.** Record in the OQ-4 thread that the dataset audit is complete and CONFIRMS forecasting ≠ counting across 10 shipped (VERIFIED) + 3 planned (INFERRED) datasets.
2. **De-prioritize P2/P6 as the re-eval directs** — they solve a problem the data does not pose. Keep them as the documented §12 fallback, gated on the trigger in §8 (a genuine sequence-counting target).
3. **Proceed with P3-C/LMU (Approach-C) + P1** as the model pick, on the strength of the irregular-Δt axis being the only actually-present cross-cutting demand.
4. **Treat the build-time gates as the real near-term blockers**, not the architecture choice: `equities_seq` is now built on the data side, so the remaining gate is wiring the 3-D contract into cascor (the `ndim>2` ingestion cap) so P3-C can actually be exercised end-to-end.

**Open questions (outside this data audit's scope):**

- **[OQ-4 still unratified]** WS-0 model pick (RCC-first vs ESN/NEAT) remains in review; this audit removes the *counting* objection but does not by itself settle the RCC star-free/no-count ceiling debate for *future* corpora.
- **P3-C fixed-Δt negative control** remains an *analytic assertion*, not a measurement (re-eval §5 honest-gap, R4). The audit does not supply that measurement.
- **3-D contract wiring** (`equities_seq` generator + cascor `ndim > 2` support, R5) is a build-time prerequisite before any recurrent path — including P3-C — can be measured.
- **If a counting target is ever added** (event-parity, mod-k label), re-run this audit and re-open the §12 fallback.

---

## 11. References

**Generators read this session (all under `/home/pcalnon/Development/python/Juniper/juniper-data/juniper_data/`), with load-bearing file:line:**

- `generators/spiral/generator.py` — labels :177-195; coords :102-146 (spatial sin/cos :135-141); shuffle :46-53. `generators/spiral/defaults.py:8` (n_spirals=2).
- `generators/xor/generator.py` — per-quadrant one-hot :121-125; vstack :114; shuffle :48-55.
- `generators/checkerboard/generator.py` — `(x_idx + y_idx) % 2` :99; spatial cell indices :90-97; coords :80-83; shuffle :46.
- `generators/circles/generator.py` — one-hot by circle :99-101; coords :80-90; shuffle :46-53.
- `generators/moon/generator.py` — one-hot by moon :98-100; coords :81-89; shuffle :48-55.
- `generators/gaussian/generator.py` — per-class one-hot :92; samples :89-90; centers (spatial cos/sin) :122-124; shuffle :46-53. `defaults.py:10` (n_features=2).
- `generators/mnist/generator.py` — digit one-hot :106-111; flat reshape :103-104; HF load + shuffle :91-94; shuffle_and_split :59-66. `defaults.py:12,21-23`; `params.py:24`.
- `generators/arc_agi/generator.py` — pair→array :188-208; flat/spatial emit :220-224; pad :229-237; shuffle :71-78. `core/split.py:109-113`.
- `generators/csv_import/generator.py` — per-row label :159-181; numeric features :149-162; shuffle :53-60. `params.py:59`.
- `generators/equities/generator.py` — `next_close = close.shift(-1)` :310; `direction_up` :315; targets emit :197-198; one-hot :428-436; flat features :414; temporal split :175,182-183; rolling 252 :279-280; SEC-EDGAR :378-388; ffill :290; dates :443. `generators/equities/defaults.py:50-61` (feature columns), `:35` (252 window).
- `generators/_sequence.py` — `window_one_ticker` :106-125; `dt = np.diff(...)` :113-116; `target_dt` :123.
- `generators/equities_seq/` — **BUILT 2026-06-13** (mtime 19:39): `generator.py:65-149` (`generate()`), targets `:129-130` (`y_reg=next_close`, `y_dir=direction_onehot`), `params.py` (`lookback` default 64, range 2-512), registered `api/routes/generators.py:100`, tests `tests/unit/test_equities_seq_generator.py`.
- `generators/__init__.py` — re-exports SpiralGenerator/SpiralParams only.
- `api/routes/generators.py` — `GENERATOR_REGISTRY` (**11 entries**); all tagged `task_type="classification"`; `equities_seq` at `:100` (uniquely `time_unit="calendar_days"`).
- `core/split.py` — `shuffle_data` / `rng.permutation` :31-32, :109-113.

**Build-absence checks (VERIFIED):** `ls` of `generators/` = **11 built dirs** (incl. `equities_seq`, built 2026-06-13) + `_sequence.py` + `__init__.py`; strict word-boundary grep over `juniper_data/` for `multi.?sine | mackey | sinusoid | autoregress | ar_p` returns **zero** hits — the 3 synthetics are genuinely unbuilt. Accumulator scan (`cumsum|cumprod|cummax|cummin|expanding|%|np.mod|parity|counter`) over every `*/generator.py` returned exactly one hit (checkerboard spatial `% 2`).

**Corpus documents (under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/validated-herding-pretzel/notes/`):**

- `JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md` — §1(B), §3, §3.2, §4, §4.1, §4.5, §5, §6, §9, §10, §12, §13 (ceiling theory, deferred dataset-audit validator, P3-C/LMU + P1 recommendation, P2/P6 §12 fallback).
- `JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md` — OQ-5 planned-synthetics list :341,347; WS-0/WS-4 status :33; R1/R2 rows :211-212; RCC smooth-signal guardrail §1.3.1.
- `JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md` — §1.6 / :82 (synthetics regular-by-construction), §2 (equities NPZ Δt), §3/§6 (3-D `dt`/`target_dt` contract, reference), §4.5 (Δt orthogonal to the ceiling).

**Ceiling-theory primary sources (as cited in the re-eval):** Knorozova & Ronca 2024 (recurrent cascades = star-free; Thm 7 / Prop 5/6); Sarrof, Veitsman & Hahn 2024 (SSM/LMU family = star-free); McNaughton & Papert 1971 (star-free = aperiodic); Schützenberger (counter-free = star-free; threshold-countable).

**cascor ingestion build-gate:** `juniper-cascor/src/cascade_correlation/cascade_correlation.py:272-273` — `SharedTrainingMemory` caps `ndim > 2` ("only supports tensors up to 2 dimensions … planned for a future release"), blocking 3-D windows. (In juniper-cascor, not the worker.)
