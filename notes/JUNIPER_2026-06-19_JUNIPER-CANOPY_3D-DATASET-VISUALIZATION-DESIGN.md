# Juniper-Canopy — 3-D (Time-Series) Dataset Visualization Design

**Project**: juniper-canopy (subject) / juniper-ml (doc home)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-19
**Status**: Design-of-record — ratified in the 2026-06-18/19 interactive design session

> The design-of-record for how canopy **displays** 3-D (sequence / irregular-Δt
> time-series) datasets. Resolves OQ-6 and elaborates **D2** of the A1-enabler scope
> ([`JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md`](JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md)),
> which established that *training delivery* is service-side but *dataset display* is
> canopy's job for 3-D too — gating the dataset load on `ndim==2` is wrong-direction
> debt. Decided over two rounds of plotly mockups (the canopy renderer); the images are
> the appendix (§8) under [`canopy_3d_viz_mockups/`](canopy_3d_viz_mockups/), generated
> by [`../util/ad-hoc/canopy_3d_viz_mockups.py`](../util/ad-hoc/canopy_3d_viz_mockups.py).

---

## 1. Context

Canopy's dataset-visualization panel was built 2-D-scatter-simple (color by class).
The incoming model class (recurrence/LMU + the time-series models after it) trains on
3-D sequence datasets — shape `(W` windows `× L` length `× F` features`)` with a per-step
**`dt` `(W,L)`** (sampling is **irregular**) and **regression** targets (`y_reg`). A
research dashboard must let users *load and understand* these datasets, so canopy needs a
genuine 3-D visualization, not an `ndim==2` reject.

The design was explored against **two complementary synthetic time-series types** (the
basis for every mockup):

- **`irregular_sine`** — univariate-leaning, smooth oscillation, clearly irregular Δt;
  best for the time-axis and single-signal questions.
- **`equities_seq`** — 5-feature OHLCV, weekend-gapped (irregular) trading days,
  mixed-scale (Volume ≫ prices); best for the multi-feature questions.

---

## 2. Resolved decisions

| # | Question | Decision |
|---|---|---|
| Q1 | Primary view | **sample-lines primary** + a **Δt-characterization companion** (Q1-C) |
| Q2 | Multiple features | **multi-select signals** + **small-multiple ⇄ overlay** toggle (overlay always normalized) |
| Q3 | Irregular Δt | **real-time axis** (cumulative Δt) + a **Δt strip** companion |
| Q4 | Sample windows | a **compare-windows mode**: one signal × **multi-select windows** + same arrangement toggle |
| Q5 | Target | optional **`y_reg` companion** via a toggle |
| Q6 | Scope | **phased build** (§5) |
| M1 | Mode control widget | **segmented toggle** `Compare: [Signals \| Windows]` (revisit if rough edges) |
| M2 | Characterization placement | **side companion, on by default, collapsible** via toggle |
| M3 | Phase-1 boundary | **simple** — all signals small-multiple, no controls; features added in later phases |
| M4 | Full-cross grid | **future advanced** tab/toggle; **cap 100** (not 9) with **zoom + scrolling**; not dropped |

---

## 3. The design — a two-mode configurable viewer

Lives on the **full-width dataset-visualization panel** (not the width-pinned sidebar).
Layout: a control bar, a main plot, an always-on Δt strip, a collapsible characterization
side companion, and an optional target companion.

### 3.1 Comparison modes (M1)

A segmented `Compare: [Signals | Windows]` toggle. You vary **one axis at a time** — this
is deliberate; freely crossing both signals and windows is the §4 trap.

- **Compare signals** (default): within one selected window, **multi-select signals** →
  **small-multiple ⇄ overlay** toggle. *(mockup R1a)*
- **Compare windows**: for one selected signal, **multi-select windows** → same toggle.
  *(mockup R1b)*

### 3.2 Always-on

- **Real-time axis** (Q3): plot against cumulative Δt time, not step index — step index
  hides the irregular sampling and distorts the apparent frequency (mockup Q3).
- **Δt strip** (Q3): a per-step Δt bar strip under the main plot, revealing the spacing
  (e.g. the weekend gaps in `equities_seq`).
- **Per-signal normalization on overlay** (R2): overlay min-max-normalizes each signal —
  raw overlay buries the OHLC prices flat under Volume; normalized makes all legible.
  Small-multiple stays the honest default for mixed-scale sets.

### 3.3 Companions

- **Characterization (Q1-C / M2):** a side companion — Δt histogram + dataset stats
  (`W/L/F`, target distribution). On by default, collapsible via a toggle.
- **Target (Q5):** an optional `y_reg` companion (toggle) — renders the regression target
  alongside the inputs (mockup Q5).

### 3.4 Advanced (M4, future)

A **full-cross faceted grid** (signals × windows) behind an **advanced tab/toggle** — the
default two-mode viewer avoids it (a 3×3 grid is already cluttered, mockup R3), but as an
*opt-in* expert view it is retained, **capped at 100 panels** with **zoom + scrolling** to
stay navigable at scale.

---

## 4. Strengths / weaknesses / risks / guardrails

**Two-mode model (compare-signals | compare-windows).** *Strengths:* flexible
exploration; legible plots (one axis varies); one mental model per mode; scales to the
variable feature counts of future datasets. *Weakness:* a mode switch to learn; can't see
"2 signals × 3 windows" at once (rarely legible anyway). *Risk:* the second mode goes
undiscovered. *Guardrails:* default to compare-signals; an obvious segmented control;
remember the last selection across switches.

**Overlay arrangement.** *Risk:* a naive overlay is misleading (mixed scales collide —
Volume dominates, R2). *Guardrail:* per-signal normalization always; small-multiple is the
default for mixed-scale sets; optional secondary axis for a single outlier.

**Control-surface complexity.** *Risk:* dataset selector + Load + signal/window
multi-select + arrangement toggle + mode switch + target toggle + characterization toggle
is a lot. *Guardrails:* render in the full-width panel, not the sidebar; **progressive
disclosure** via the §5 phasing (controls arrive incrementally); good defaults.

**Advanced grid (M4).** *Risk:* combinatorial blow-up. *Guardrails:* opt-in only (never
default); hard cap of 100 panels; zoom + scroll for navigation.

---

## 5. Phasing (Q6 / M3)

- **Phase 1 — minimal, ships 3-D visibility** *(≈ mockup R4)*: **compare-signals only**,
  all signals **small-multiple**, **real-time axis + Δt strip**, **normalized**, single
  window via the **existing dataset selector + Load**. No signal/window multi-select, no
  arrangement toggle, no mode switch, no target toggle, no characterization companion.
- **Phase 2 — the control surface:** the segmented mode toggle (compare-windows),
  signal **and** window multi-select, **small-multiple ⇄ overlay** toggle, the `y_reg`
  target toggle, and the **characterization side companion** (on by default, collapsible).
- **Phase 3 — advanced:** the full-cross faceted grid (advanced tab/toggle, cap 100, with
  zoom and scroll).

This maps onto the A1-enabler scope's "canopy 3-D dataset load + display" track: the
`ndim`-aware **load foundation** (dispatch on the data-client's `validate_npz_contract`
instead of raising on `ndim!=2`; store the raw sequence arrays) underpins Phase 1, and is
independent of the recurrence *training* integration.

---

## 6. Implementation anchors

- **Load (foundation):** make `src/demo_mode.py` `ndim`-aware — `_validate_npz_arrays`
  (`:812`, the `ndim!=2` reject) and `regenerate_dataset_from_generator` (`:1764`, the
  `X_full` read + `argmax(y_full)`) dispatch on `validate_npz_contract`
  (`tabular`/`sequence`); a sequence dataset is stored **display-only** (not wired into the
  demo simulator's `network.train_x` — the cascor-like demo can't train 3-D).
- **Display:** `src/frontend/components/dataset_plotter.py` (today 2-D scatter at
  `:540-590`) gains the two-mode sequence renderer above.
- **Registry:** 3-D `DatasetTypeSpec` rows in `src/model_registry.py` (A0 shape) when the
  viewer can display them.

---

## 7. Open / deferred

- **OQ-A:** exact `y_reg` rendering when ON — overlaid on the signal, or a separate
  companion strip (likely the latter for scalar next-step targets).
- **OQ-B:** the advanced-grid (M4) interaction details (zoom/scroll mechanics, the 100-cap
  selection UX) — design when Phase 3 is taken.
- **OQ-C:** whether the characterization companion shows per-window or whole-dataset Δt
  stats (lean: whole-dataset summary + the selected window's strip inline).

---

## 8. Appendix — mockups

Plotly mockups (app-faithful), synthetic `irregular_sine` + `equities_seq`. PNG + an
interactive HTML each under [`canopy_3d_viz_mockups/`](canopy_3d_viz_mockups/);
regenerate via [`../util/ad-hoc/canopy_3d_viz_mockups.py`](../util/ad-hoc/canopy_3d_viz_mockups.py).

**Round 1 — the design questions:** `Q1_primary_view` · `Q2_multifeature` ·
`Q3_irregular_dt` · `Q4_sample_count` · `Q5_target` · `Q6_scope`.

**Round 2 — the converging design:** `R1a_viewer_compare_signals` ·
`R1b_viewer_compare_windows` · `R2_overlay_normalization` · `R3_full_cross_grid` ·
`R4_phase1_minimal`.

---

## 9. References

- [`JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md`](JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md) — D2 (3-D display) + OQ-6, which this resolves.
- [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md) — the model+dataset selection design-of-record.
- Tracks canopy [#368](https://github.com/pcalnon/juniper-canopy/issues/368) (model selection).
