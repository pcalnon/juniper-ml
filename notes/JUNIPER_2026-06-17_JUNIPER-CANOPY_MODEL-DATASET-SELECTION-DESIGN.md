# Juniper-Canopy — Model + Dataset Selection: Compatibility, UX & Scale Design

**Project**: juniper-canopy (subject) / juniper-ml (doc home)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-17
**Status**: Design-of-record (forks resolved 2026-06-17; pending A0 implementation)

> Captures the design for canopy's model + dataset selection, refining
> [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md)
> §4 and [`JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md)
> §7.1/§8.2/§8.3/§8.4. Supersedes the roadmap §8.3 "gate on `ndim`" conclusion (§1). Decisions
> D1–D8 were ratified in discussion 2026-06-17 after a four-agent validation pass
> (§12). Tracked by canopy issue [#368](https://github.com/pcalnon/juniper-canopy/issues/368).

---

## 1. What changed, and why `ndim`-gating is insufficient

The roadmap §8.3 concluded the gate should key on `input_ndim` (2-D cascor vs 3-D
recurrence). New information (2026-06-17) breaks that as a *sole* discriminator:

- **The next model is another `ndim=3` time-series-regression NN** — `ndim` *and*
  `task_type` both match the existing LMU model; neither separates them.
- **Many more models are coming** (§6): category-ii (established time-series, 3–5
  near-term) and category-i (growth/cascor-like experimental, 10–20+ near-term, each
  spawning several-to-many benchmark variants), most sharing the 3-D input contract.

Consequences:

1. **Compatibility is a multi-axis predicate, not a single key** (§4). `ndim` is one
   necessary axis; the axis that actually separates same-shape models is temporal
   structure (regular vs irregular Δt / does the model consume per-step Δt).
2. **Gating narrows to a compatible *set*; it cannot auto-pick** — when several models
   accept a dataset, the user chooses among them.
3. **Organization, not gating, is the long pole.** Because most time-series models
   share the 3-D contract, the gate is *coarse*; the dominant problem is browsing and
   comparing a large, mostly-compatible model population. That reframes the primary UI
   from a dropdown to a **dedicated searchable surface** (§5, D7).

A0 (registry + de-dup) is independent of all UX choices and proceeds first (§10).

---

## 2. Decisions (ratified 2026-06-17)

| # | Decision |
|---|---|
| D1 | Compatibility is a **multi-axis capability/requirement predicate** (§4), not `ndim` alone. The fine discriminator is temporal structure; `task_type` is carried but currently inert across the seeded models. |
| D2 | **Reason at the locus, via label suffix.** Incompatible options are **disabled (greyed)** to prevent selection; the *reason* is rendered **on the option itself** — a label suffix in the dataset dropdown ("Spirals — needs 2-D model") and a reason cell in the model table. No reverse-mapped selected-side tooltip as the sole channel. |
| D3 | **Compatibility grid is a secondary, informational view** behind a "compatibility / help" affordance — not the primary selector. |
| D4 | **Clear/reset = conventional inline ✕** on each control (clearing one auto-widens the other via the gate). The original cross-placement is retained as a **spike alternative** (OQ-2), not the default. |
| D5 | **Conflict rule is a swappable policy** (§5.6). Correctness comes from the predicate + backend (applied symmetrically); greying/labelling is a best-effort affordance, **not** the correctness guarantee. The default policy (dataset-primary vs model-primary) is chosen after the A1 spike / first real use. |
| D6 | **Scale is first-class** (§6): near-term dozens-to-hundreds of model variants → categorization + faceting + search, backed by a registry carrying `category`/`family`/`variant`/`version`. |
| D7 | **Model selection lives on a dedicated full-width surface** (a Models tab or modal — §9 OQ-1) with a **searchable, facet-filtered table**. The **sidebar keeps the dataset dropdown + a compact "Model: X ▸ change" summary** that opens the surface. The dropdown is *not* the scale vehicle. |
| D8 | **Lifecycle status drives presentation** (§5.7). `status ∈ {live, coming_soon, experimental, deprecated, broken}`; non-`live` models are shown but Train-disabled with a distinct reason — separate from incompatibility greying. |

---

## 3. Requirements

Functional:

| # | Requirement |
|---|---|
| FR1 | Select an NN model; select a dataset. |
| FR2 | Bidirectional — selecting either constrains the other (across the two surfaces, §5.3). |
| FR3 | Multi-axis compatibility predicate: `ndim` (necessary) + temporal structure (the real fine discriminator) + `task_type` (carried, currently inert) + extensible. |
| FR4 | When >1 option remains compatible, the user chooses within the set (no silent auto-pick). |
| FR5 | Incompatible options stay **visible but disabled**; the *reason* sits on the option (label suffix / reason cell — D2). |
| FR6 | Clear/reset each selection (inline ✕ — D4) → restores the full active set on the other side. |
| FR7 | Extensible — a new model/dataset/variant is one registry entry, no UX change. |
| FR8a | Incompatibility reason is reachable by hover **and** keyboard (label suffix / focusable cell). |
| FR8b | Gating/lifecycle reason (`coming_soon`, etc.) is surfaced accessibly and distinctly from incompatibility (D8). |
| FR9 | Backend validates the chosen `nn_model` × dataset and **fails closed** on shape mismatch (§5.9). |
| FR10 | Deterministic conflict resolution via the swappable policy (D5). |
| FR11 | Sensible default / empty state; the default pair must be compatible or fall back (FR15). |
| FR12 | Model selector usable at **dozens-to-hundreds** — categorized + faceted + searchable (the surface, D7). |
| FR13 | Registry models a hierarchy `category → family → variant` with stable, **unique** `key` + benchmark identity (`version`, `benchmark_id`). |
| FR14 | Adding a model/variant for benchmarking is registry-only (FR7 at scale). |
| FR15 | Selection initializes from current backend state, is **re-validated against the registry** on load, and falls back to the first compatible pair (with notice) if stale/incompatible. |

---

## 4. Compatibility engine (capability/requirement predicate)

Single source of truth. Datasets declare **properties**; models declare
**requirements**; compatibility is a pure predicate.

```text
compatible(dataset, model) :=
      dataset.ndim ∈ model.input_ndim
  AND dataset.task_type ∈ model.supported_task_types
  AND temporal_ok(dataset, model)        # irregular-Δt dataset ⇒ model must consume Δt
  AND (… future axes, added as models land …)
```

- **Additive axes.** A new distinguishing property is one field on both specs + one
  clause; existing entries default it to "don't care".
- **Pure + browser-free.** The predicate and resolvers `compatible_models(dataset)` /
  `compatible_datasets(model)` are unit-tested with no browser (the roadmap "B0" gate).
  They — not the UI greying — are the correctness guarantee (D5).
- **`ndim` sufficiency is temporary.** For the two *seeded* models (`cascor` 2-D,
  `recurrence` 3-D) the predicate happens to reduce to `ndim`. It becomes insufficient
  the instant a second 3-D model lands (the §1 trigger) — which is why the predicate is
  multi-axis from day one even though `task_type`/`temporal` are inert against the
  current seeds. The `temporal_ok` clause does the category-i/ii separation.

---

## 5. Selection UX

Two surfaces, one compatibility engine: a compact **sidebar** (dataset + model
summary) and a **dedicated full-width model-selection surface** (D7).

### 5.1 Surfaces

- **Sidebar** keeps: the **Dataset Type** dropdown (with inline ✕, D4, and reason-suffix
  greying, D2) and a **compact model summary** — "Model: `LMU-growth-v3` ▸ change" — a
  button opening the surface. Fits the width-pinned rail; no scale pressure there.
- **Model-selection surface** (a new *Models* tab or a modal — OQ-1): a **searchable,
  facet-filtered table** of model variants. This is the browse-and-compare control the
  scale demands; it is *not* in the sidebar.

### 5.2 The model table

- Rows = model variants. Columns: family / variant / version / status / **compatibility
  (with reason when incompatible)** / (benchmark id, last-result — later).
- Facets: `category`, ndim-fit, task fit, `status`, `tags`. Search matches
  `label` + `family` + `category` + `tags` (not label-only — §8).
- Compatible rows are selectable; incompatible rows are greyed with the reason in the
  compatibility cell (D2). `status≠live` rows are Train-disabled with a status reason
  (D8), independent of compatibility.

### 5.3 Bidirectional gate across the two surfaces (FR2)

- Selecting a **dataset** (sidebar) marks/greys incompatible **models** in the table and
  annotates the sidebar summary ("3-D models only"); the table is pre-filtered on open.
- Selecting a **model** (surface) greys incompatible **datasets** in the sidebar dropdown
  (reason suffix). Recomputed on change and on surface-open.

### 5.4 Reason placement (D2 / Fork 2)

Reason lives **on the incompatible item**: a label suffix in the dataset dropdown
("Spirals — needs a 2-D model") and a reason cell in the model table ("needs 2-D"). This
sits at the locus of confusion, scales (one per item), and avoids the
per-option-disabled-tooltip limitation (§8) without reverse-mapping the reason onto the
opposite control.

### 5.5 Clear / reset (D4 / Fork 4)

Conventional **inline ✕** on the dataset dropdown (clears itself; the model table
re-activates fully via the gate as a side-effect) and a "clear model / show all" reset on
the surface. Cross-placement ("clear the constraint on *this* list") is kept as the
OQ-2 spike alternative, not the default.

### 5.6 Conflict resolution (D5 / Fork 3)

A newly *selected* option is never incompatible (greyed). A conflict can only arise by
**changing** an already-set value so the other side is stranded. Resolution is a **single
swappable policy** in the resolver:

- *dataset-primary:* keep dataset, clear model + notice.
- *model-primary:* keep model, clear dataset + notice. (Fits the model-centric
  benchmarking trajectory.)

Default chosen post-spike. The predicate + backend (§5.9) enforce correctness regardless
of which policy/UI affordance is active — greying is best-effort, **not** the guarantee
(so a coarse-greying gap cannot push an invalid pair through).

### 5.7 Lifecycle / gated models (D8)

`status` drives presentation, distinct from compatibility: `coming_soon` (e.g. the
`recurrence` service, stranded off main — roadmap §8.4) and `experimental` models are
**shown, selectable for inspection, but Train-disabled** with a status reason (FR8b);
`deprecated`/`broken` are de-emphasised or filtered by default. The flagship second
model (LMU) is `coming_soon` on day one, so this state is exercised immediately.

### 5.8 Degenerate & default states

- **Empty compatible set** (e.g. a 3-D dataset when the only 3-D model is `coming_soon`):
  show a clear message + recovery ("no trainable model for this dataset yet — clear the
  dataset, or see *coming soon* models").
- **Default / reload (FR15):** initialise from current backend state, re-validate against
  the registry, fall back to the first compatible pair with a notice if stale.
- **Registry/table load failure:** the sidebar summary shows the last-known model; the
  surface shows a retry; training is not blocked by a picker load error.

### 5.9 Backend validation (FR9)

canopy threads `nn_model` to the backend; the **target model service validates the input
shape it receives and fails closed** on mismatch (defence in depth — a UI desync cannot
train an invalid pair). canopy's registry is the *UX-side* predicate; a shared
capability source across services is a possible later unification (noted, not required).

---

## 6. Scale — the long-pole problem, and why the surface answers it

Near-term model population (per 2026-06-17):

| Category | Description | Near-term | Variants |
|---|---|---|---|
| feedforward | `cascor` (current) | 1 | — |
| ii — established TS | known-effective time-series/recurrence designs | 3–5 | some |
| i — growth/experimental | cascor-like growth on TS models; novel/hybrid/integrated | **10–20+** | **several-to-many each**, kept distinct for benchmarking |

The compatibility gate barely partitions this (most are 3-D-compatible), so **organization
is the load-bearing problem** — and a sidebar dropdown is the wrong control for browsing
100+ benchmark variants. Hence D7's dedicated surface:

- **Hierarchy:** `category → family → variant` (FR13); the table groups/sorts by these.
- **Faceting + search** (FR12): filter by category/status/tags/task-fit; search across
  label+family+category+tags; the table is virtualized for hundreds of rows.
- **Two-stage within the surface (OQ-3):** if any single family exceeds a threshold
  (e.g. 25 variants), present *family → variant* rather than a flat list.
- **Benchmark identity (FR13):** each variant carries a unique `key` + `version` +
  `benchmark_id` so result analysis references it unambiguously.

---

## 7. Registry shape (the A0 substrate)

`src/model_registry.py` (new; sibling of `canopy_constants.py`). A0 builds the data + the
dataset-options de-dup; the predicate/resolvers, surface, gate, and mirror are A1 (§10).
The shape is future-proofed so A1+ is additive (not a migration across a populated
registry).

```text
DatasetTypeSpec:
    value: str             # "spirals"
    label: str             # "Spirals"
    task_type: str         # juniper-data vocab: "classification" | "regression"
    ndim: int              # 2 | 3
    temporal: str = "none" # "none" | "regular" | "irregular"

ModelSpec:
    key: str                      # globally UNIQUE stable id (A0 test asserts uniqueness)
    label: str
    category: str                 # "feedforward" | "ts_established" | "ts_growth"
    family: str                   # grouping for variants, e.g. "lmu", "cascor"
    variant: str = ""             # variant discriminator within a family
    version: str = ""             # benchmark identity
    benchmark_id: str = ""        # stable ref for result analysis
    input_ndim: frozenset[int]    # {2} | {3}
    supported_task_types: frozenset[str]
    requires_dt: bool = False     # temporal axis seed
    status: str = "live"          # live|coming_soon|experimental|deprecated|broken
    tags: frozenset[str] = frozenset()
    description: str = ""
    aliases: tuple[str, ...] = ()
    provider: str = ""            # where it's served (in-proc cascor / recurrence svc / …)
```

Seeds: `cascor` (feedforward, ndim={2}, {classification, regression}, `live`,
provider=in-process); `recurrence`/LMU (ts_established, family `lmu`, ndim={3},
{regression}, `requires_dt`, **`status=coming_soon`** until its service is published —
roadmap §8.4). Dataset seeds: the 5 current types, all `(classification, 2, none)`.

`status` (enum) replaces the earlier `is_live`/`gated_reason` two-state (keep a `live`
convenience property). **`task_type` vocabulary** uses juniper-data's emitted values
(`classification`/`regression`); the design's earlier `time_series`/`irregular_dt`
conflated *shape/temporal structure* (now `ndim` + `temporal`/`requires_dt`) with
*objective* — do not invent task-type labels (resolves roadmap §8.3).

---

## 8. Technical feasibility (verified vs installed `JuniperCanopy1`: dash 4.1.0 / dbc 2.0.4)

- **`dcc.Dropdown` (new native, virtualized in Dash 4.1 — not react-select):** per-option
  `disabled` ✓, default search ✓, handles hundreds of options ✓; **no** per-option
  `title`/tooltip, **flat** (no native `<optgroup>`). → label-suffix reason (D2) and
  app-level group headers are the idiom; search is label-only by default (so the
  *table*, not the dropdown, carries multi-field search — §6).
- **`dbc.Select`:** per-option `disabled` **and** `title` ✓, but **no `<optgroup>` in dbc
  2.0.4** (the earlier draft's claim was wrong). Not the grouping/scale answer.
- **`dash-mantine-components`** (grouped Select): **not installed** — would add a
  dependency + version pin; do not assume in the spike.
- **Bidirectional callbacks:** drive both sides from a **single callback keyed on
  `ctx.triggered_id`** (or via a `dcc.Store`), with `allow_duplicate=True` +
  `prevent_initial_call`. Two callbacks mutually rewriting each other's `value` trip
  Dash's circular-dependency check.
- **Tooltip/keyboard (FR8):** a `dbc.Tooltip` target must be focusable to be
  keyboard-reachable (the control itself or `tabIndex=0`); disabled elements don't fire
  hover/focus — which is exactly why D2 puts the reason in the *label*/cell, not a tooltip
  on a disabled option.
- **Table component (OQ-4):** the surface table is `dash_table.DataTable` (built-in,
  filter/sort/paginate) vs a custom `dbc.Table`/`ListGroup` vs AG-Grid — pick in the
  spike against the facet/virtualization needs.

---

## 9. Open questions / to validate in the A1 spike

- **OQ-1:** surface as a **Models tab** (persistent, best for compare) vs a **modal**
  (focused, reuses the existing `live-switch-modal` pattern). Default lean: tab.
- **OQ-2:** inline ✕ (default) vs cross-placed clear — quick first-click usability check.
- **OQ-3:** flat grouped table vs two-stage `family → variant` above a per-family
  threshold (~25).
- **OQ-4:** table component (`DataTable` vs custom vs AG-Grid).
- **OQ-5:** the precise input-requirement axes separating category-i/ii models as they
  land (fills `temporal`/`requires_dt` + any new clause). Engine is robust to deferral.
- **OQ-6:** conflict-policy default (dataset- vs model-primary) — decide post-spike (D5).

---

## 10. Phasing

- **A0 (now — canopy #368, no upstream blocker):** `model_registry.py` with the §7 specs
  (future-proofed shape) + `cascor`/`recurrence` + 5 dataset seeds; `dataset_type_options()`;
  rewire the hardcoded options at `dashboard_manager.py:1114-1121` (the `options=[…]` block
  **and** the `value="spirals"` default) through the registry. Behavior-preserving;
  snapshot + shape + **key-uniqueness** tests. No surface/gate/mirror yet.
- **A1 (early Wave 2):** the predicate + resolvers (B0-tested); the dedicated surface +
  table (starts small, scales); the sidebar dataset gate + compact model summary;
  reason-suffix greying (D2); inline ✕ (D4); the swappable conflict policy (D5); lifecycle
  states (D8); the `nn_model` backend mirror (FR9); L1/L2 enrollment. *Likely splits*:
  A1a (sidebar dataset-gate + compact summary + minimal picker) → A1b (full facet table).
- **Later:** compatibility-grid help view (D3); two-stage variant selection (OQ-3) and
  facet richness as variants grow; per-model axis refinement (OQ-5).

---

## 11. Alternatives considered (recorded; generated in the 2026-06-17 evaluation)

These selector alternatives were generated and judged in this round (the predecessor docs
committed to a single in-sidebar dropdown; they did not enumerate these). The chosen
design is **E** below.

- **A — symmetric dual dropdowns in the sidebar, bidirectional greying.** The starting
  point; rejected as the *scale* vehicle (a sidebar dropdown can't browse 100+ benchmark
  variants) but its bidirectional-gate + clear concepts survive in E's sidebar half.
- **B — ordered lead-axis (model-first / dataset-first).** A legitimate *model-primary
  workflow*; folded into D5's swappable policy rather than a user-visible lead toggle.
- **C — compatibility matrix as primary selector.** Maximal transparency, no
  conflict-state, but doesn't scale as primary; retained as the secondary help view (D3).
- **D — indicator-only (no greying).** Lightest and fully accessible; rejected as the
  *sole* prevention mechanism, but its "reason as visible text" idea is exactly what D2
  adopts (label suffix) and FR9 backstops.
- **E — dedicated full-width searchable surface + compact sidebar summary (CHOSEN, D7).**
  Browse-and-compare fit for the §6 scale; reuses canopy's tab/modal patterns; keeps the
  sidebar uncluttered.

---

## 12. Validation & references

**Validation history:**

- **v1 (2026-06-17):** four independent sub-agents — Dash feasibility (corrected the
  `dbc.Select` optgroup claim; confirmed the new native virtualized `dcc.Dropdown` and the
  single-driver-callback requirement), requirements/consistency (FR10 not airtight → D5
  now policy + predicate-as-guarantee; default/gated gaps → FR15/D8), design-soundness
  (reason mislocation → D2 label-suffix; sidebar-scale → D7 surface; registry
  under-shaped → §7 future-proofing; conflict primacy → D5 swappable), and markdown lint.
- **Forks resolved (2026-06-17):** scale vehicle → dedicated surface (D7); reason → label
  suffix (D2); conflict → swappable policy (D5); clear → inline ✕ (D4).
- **v2:** consistency + lint re-check of this revision (record appended on completion).

**References:**

- [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md) §4 — original design + a11y citations (`papers/`).
- [`JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md) §5.1/§7.1/§8.2/§8.3/§8.4 — supersedes the §8.3 `ndim`-gate conclusion; §8.4 = the stranded `recurrence` service.
- Canopy anchors: hardcoded options + default `src/frontend/dashboard_manager.py:1114-1121`; value reads `:3558`, `:3839`, `:3896`; `src/canopy_constants.py` dataset params; existing full-width `dbc.Tabs` panel + `live-switch-modal` pattern (surface reuse).
- Tracking: canopy issue [#368](https://github.com/pcalnon/juniper-canopy/issues/368).
