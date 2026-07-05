# Juniper-Canopy — Regression Remediation: Current-State Reconciliation & Go-Forward Roadmap

**Project**: juniper-canopy (subject) / juniper-ml (doc home)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-17
**Status**: Active planning deliverable — supersedes the *status framing* of the two 2026-06-15 canopy audit docs

> **What this is.** A source-validated reconciliation of where the juniper-canopy
> regression-remediation effort *actually stands today* (canopy `main` @ `d13649f`,
> origin `#367`; juniper-ml `main` @ `99a1fc0`) versus what the two 2026-06-15
> planning/deliverable docs describe, followed by a prioritized design/development/
> testing roadmap for the outstanding work. Every internal claim carries a
> `file:line` reference verified against actual source; the headline corrections
> below were each confirmed by multiple independent sub-agents **and** by direct
> re-reads (see §9).
>
> **Predecessor docs** (both landed via juniper-ml `#430`, 2026-06-16):
>
> - [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md) — the approved working plan.
> - [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md) — the empirical deliverable.
>
> This document does **not** replace their design content (which remains the design
> of record for model selection). It corrects their *execution-state* framing, which
> is now stale, and defines what happens next.

---

## 1. Purpose & method

The two predecessor docs were written mid-execution (2026-06-15/16). The work has
since fully merged, so their "in-flight / stacked / deferred" language no longer
describes reality. The user asked to (a) evaluate the current state of the process
and validate it against actual source, then (b) plan the design/development/testing
roadmap for outstanding work with prioritization, ordering, grouping, and multiple
approach options analyzed for strengths, weaknesses, risks, and guardrails.

**Method.** Five independent sub-agents each audited a non-overlapping slice
(harness reality, orphan-fix reality, model-selection + upstream readiness, citation/
paper/lockfile fidelity, cross-repo PR/issue state) against actual source on the
default branches — not against the docs' assertions. Their findings were
cross-corroborated and the two most decision-critical facts (`KNOWN_ORPHANS`
contents and L2 manifest coverage) were re-read directly. §9 records the methodology;
a second, independent validation pass over *this* document is described there and is
part of the deliverable.

**Grounding base.** canopy `main` local HEAD `d13649f` (origin/main is one commit
ahead at `#367`, a layout-snapshot regen that touches no logic in scope). juniper-ml
`main` @ `99a1fc0`. juniper-data `main` (v0.6.0). All `file:line` references are
against these unless noted.

---

## 2. Executive summary (TL;DR)

1. **The entire 2026-06-15/16 iteration is merged.** The UI-regression harness
   (canopy `#364`), all three orphan-control fixes (`#365` → recovered via `#366`),
   a snapshot restore (`#367`), and both deliverable docs (juniper-ml `#430`) all
   landed 2026-06-16. Nothing from this effort is open in either repo.

2. **The "dead-button" regression class is closed and gated.** `KNOWN_ORPHANS == {}`
   (`src/tests/unit/test_control_graph_lint.py:29`); the live L1 lint reports zero
   orphans (`python util/ui_control_graph.py` → exit 0); L1 + L2 run as required CI
   checks on every PR. The class that motivated this effort can no longer regress
   silently.

3. **Both predecessor docs are stale in their execution framing, not their design.**
   The deliverable doc's §3 ("1 orphan fixed, 2 deferred") and §7 ("in-flight /
   stacked") are superseded: `#366` wired **all three** orphans, including the two it
   marked *deferred* (`nn-init-output-weights-dropdown`, `dataset-plotter-dataset-selector`).
   Their model-selection design (§4) and accessibility analysis remain valid and
   un-implemented — they are still the design of record.

4. **Genuinely outstanding work is small, unstarted, and untracked** (no issues exist
   for any of it):
   - **Model-selection feature** (the dominant remaining piece; design-only today).
   - **L3 real-browser proof** via `dash_duo` (deferred; redundant with L2 today).
   - **`requirements.lock` reconcile** (lock still pins dash 4.2.0 vs installed 4.1.0).
   - **Harness-coverage extension** (the 3 newly-wired controls are L1-guarded but not
     in the L2 behavioral manifest — *new finding*, §5.4).
   - **Doc/comment hygiene** + a **latent squash-merge process risk** (§8.4).

5. **Center of gravity has shifted from firefighting to hardening + enhancement.**
   The regression backlog the docs targeted is drained; the forward work is the
   model-selection *enhancement* and making the harness's behavioral coverage match
   its wiring coverage. There is no evidence of an open, unaddressed regression class.

---

## 3. Current-state reconciliation (claim → ground truth)

Each row is a claim from a predecessor doc (or its implied execution state) versus
what is true in source today. Verdicts: **CONFIRMED** (still true), **STALE** (was
true, now superseded), **OPEN** (claim accurate, work still pending).

| # | Predecessor claim | Ground truth on `main` | Verdict | Evidence |
|---|---|---|---|---|
| 1 | L1 control-graph lint built | `util/ui_control_graph.py` present; runs exit 0, 0 orphans | CONFIRMED | `ui_control_graph.py` `lint:140`, `enumerate_controls:107`, `enumerate_bindings:128`, `ACTIONABLE:55`, `TRIGGER_REQUIRES_INPUT:75` |
| 2 | L1 gate test built | Both tests present; `KNOWN_ORPHANS == {}` | CONFIRMED | `test_control_graph_lint.py` `KNOWN_ORPHANS:29`, `test_no_new_orphan_controls:42`, `test_known_orphans_not_stale:50` |
| 3 | L2 behavioral manifest built | Present, **8 `ControlContract` rows** | CONFIRMED | `control_manifest.py` `MANIFEST:50`; driver `test_control_manifest_behavioral.py::test_control_backend_contract:29` |
| 4 | L3 POC #2 (Playwright) run & failed; xfail canaries | Both strict-xfail in source | CONFIRMED | `test_l3_native_setter_poc.py:46`, `test_apply_button_flow.py:62` |
| 5 | L1 + L2 gate every PR | Both in `required-checks` needs | CONFIRMED | `.github/workflows/ci.yml` unit-tests + integration in required-checks |
| 6 | `restart-with-new-dataset-button` fixed (§3.1) | Wired + demo parity | CONFIRMED | `dashboard_manager.py:3629` Input → `restart_with_new_dataset:3632`; demo clear `demo_mode.py:1475` |
| 7 | `nn-init-output-weights-dropdown` **deferred** (§3.2) | **Both halves wired** | STALE | `State` `dashboard_manager.py:3436`; field `SetParamsRequest.nn_init_output_weights` `main.py:2875`; demo `demo_mode.py:2060` |
| 8 | `dataset-plotter-dataset-selector` **deferred** (§3.3) | Value now consumed | STALE | `State` `dashboard_manager.py:2806` → `load_selected_dataset:2809` via `Input load-selected-btn:2805` |
| 9 | Harness/fix "in-flight / stacked" (§7) | All merged 2026-06-16 | STALE | canopy `#364`/`#365`/`#366`/`#367`; ml `#430` |
| 10 | Model selection design-only | No code anywhere | CONFIRMED (still design-only) | no `src/model_registry.py`; no `nn-model-dropdown`/`nn_model`/`task_type` in canopy `src/`; options hardcoded `dashboard_manager.py:1115-1119` |
| 11 | 4 a11y papers retrieved | All 4 present, real URLs, dated | CONFIRMED | `juniper-ml/papers/{nngroup-disabled-buttons,w3c-aria-tooltip-and-disabled,dash-testing-dash-duo,react-controlled-input-onchange}.md` |
| 12 | `requirements.lock` reconcile pending | Lock still pins dash 4.2.0 | OPEN | `requirements.lock` dash 4.2.0 (`:30`), plotly 6.8.0 (`:94`), starlette 1.3.1 (`:137`); installed 4.1.0 / 6.7.0 / 1.0.0 |
| 13 | All cited `file:line` accurate | ~100% resolvable, ~74% exact | CONFIRMED (with drift) | `main.py` callback-body cites drift +18..+23 (main ahead of doc's `c07dab8`); zero wrong/absent |

**Net:** 7 CONFIRMED, 4 STALE, 1 OPEN, 1 CONFIRMED-with-drift. The STALE rows are all
execution-state, not design. The single OPEN substantive item (lockfile) is small.

---

## 4. What is DONE and gated (do not re-litigate)

- **Dead-button regression net (L1).** Walks the realized Dash layout for every
  actionable control and every callback `Input`/`State` binding; reports any
  actionable control unreachable by all callbacks. Buttons/uploads require an
  `Input`; value-carriers require `Input`-or-`State`. Empty `KNOWN_ORPHANS` baseline
  that may only shrink, with an anti-rot test that forces an entry out once its
  control is wired. This is the durable guarantee that the orphan class cannot
  silently return.
- **Backend-contract coverage (L2).** 8 declarative `ControlContract` rows exercised
  in-process via `TestClient` in demo mode: the 5 training buttons, `apply-params`
  (the only `/api/state` roundtrip, probing `nn_learning_rate=0.0123`),
  `apply-dataset`, `cancel-pending-dataset`. Adding a row auto-enrolls a control.
- **L3 wall, documented.** The `dbc.Input` native-value-setter wall is a settled
  negative result, pinned by two strict-xfail canaries that flip red (XPASS) if a
  future Dash release fixes the synthetic-event path.
- **All three orphan controls wired** (rows 6–8 above), each with the backend field
  and demo mirror needed to actually take effect.
- **Audit corpus + a11y papers** landed in juniper-ml (`#430`).

---

## 5. Outstanding work inventory

Each item: scope, evidence it is real, and dependencies. All are now tracked (filed
2026-06-17): canopy [#368](https://github.com/pcalnon/juniper-canopy/issues/368) (§5.1),
[#369](https://github.com/pcalnon/juniper-canopy/issues/369) (§5.4),
[#370](https://github.com/pcalnon/juniper-canopy/issues/370) (§5.3),
[#371](https://github.com/pcalnon/juniper-canopy/issues/371) (§5.2); juniper-ml
[#434](https://github.com/pcalnon/juniper-ml/issues/434) (§8.4 sweep).

### 5.1 Model-selection feature (dominant remaining piece)

Design-only. Build: `src/model_registry.py` (`ModelSpec` / `DatasetTypeSpec` +
`models_for_dataset` / `dataset_values_for_model`), the `nn-model-dropdown` selector,
bidirectional `task_type × input_ndim` compatibility gating, accessibility
(soft-gate vs `aria-disabled` hard-disable + wrapper tooltip), and the **mandatory
backend mirror** (`nn_model` on `SetParamsRequest` + `StageDatasetRequest`, threaded
through `demo_mode.py` / `demo_backend.py`). Design of record: deliverable doc §4.
Phasing (§7.1): the registry + de-duplication (A0) is a small Wave-1 refactor; the
dropdown + gate + a11y + backend mirror (A1) defers to early Wave 2.
**Evidence it is unbuilt:** no `src/model_registry.py`; zero hits for
`model_registry` / `ModelSpec` / `nn-model-dropdown` / `nn_model` / `task_type` in
canopy `src/`; dataset options still hardcoded (`dashboard_manager.py:1115-1119`).

**Upstream readiness (drives priority — see §8.2):**

| Upstream | Status | Effect on the feature |
|---|---|---|
| juniper-data `task_type` + 3-D/Δt NPZ (WS-1) | **DONE** (v0.6.0): `task_type` in `GENERATOR_REGISTRY` (`generators.py:42-165`), 3-D meta (`core/meta.py:103-120`), `equities_seq` + `irregular_sine` emit `(W,L,F)`+`dt` | Ready — but emits `classification`/`regression`, **not** the design's `time_series`/`irregular_dt` labels (vocabulary mismatch, §8.3) |
| `juniper-recurrence` model | Published (`juniper-recurrence-model 0.1.0`) | The model exists |
| `juniper-recurrence` **service/app** (WS-4b) | **Built but not on `main`**: PR `#6` (skeleton) merged to `main`; `#7` (routes) + `#8` (publish workflow) merged into *stacked branches* and never reached `origin/main` (the §8.4 footgun) — app not on PyPI, not deployed | No endpoint to route `recurrence` to → must stay soft-gated "coming soon" |
| cascor 3-D ingestion (OQ-4) | **BLOCKED**: hard rejects ndim>2 (`SharedTrainingMemory` raise; 2-D-only descriptor + tensor validation); discards `dt`/`mask` | The real long pole; until lifted, only cascor (2-D) is trainable |

### 5.2 L3 real-browser proof (dash_duo)

Deferred follow-up: `dash.testing`/`dash_duo` + Selenium `send_keys` (real keystrokes
fire React `onChange` natively), in a dedicated `make test-ui-dash` job. Needs
`selenium` + `multiprocess` + `chromedriver` (absent in `JuniperCanopy1`). **Today it
is redundancy, not a coverage gap:** the Apply→`/api/set_params`→`/api/state` contract
it targets is already proven deterministically by the L2 `apply-params` row.

### 5.3 `requirements.lock` reconcile

Lock pins dash 4.2.0 / plotly 6.8.0 / starlette 1.3.1; installed (and CI-green) is
4.1.0 / 6.7.0 / 1.0.0. The lock is *ahead* of reality, risking a CI-vs-local
capability gap. `dash-bootstrap-components` matches (2.0.4). No reconcile commit in
the last 15 lock touches.

### 5.4 Harness-coverage extension (new finding)

L1 guarantees *wiring* for all controls; L2 *behaviorally proves* only 8. The three
controls `#366` just wired — `restart-with-new-dataset-button`,
`nn-init-output-weights-dropdown` (its value rides the apply path, but the L2 apply
row probes only `nn_learning_rate`), and `dataset-plotter-dataset-selector` (via
`dataset-plotter-load-selected-btn`) — are **not** in the manifest. The manifest's own
docstring advertises "add one row per control"; these three are the obvious next
rows. Closing this makes behavioral coverage match wiring coverage.

### 5.5 Doc / comment hygiene

- Add a 2026-06-17 status banner to both predecessor docs pointing here (their
  §3/§7 execution framing is stale).
- Optional wording polish (not a correctness issue): the L1 lint docstring
  (`test_control_graph_lint.py:4-5`) names the three controls as "the regression class
  that shipped" — a past-tense historical reference a hurried reader could misread as
  current orphans; a one-line reword removes the ambiguity.
- Refresh the L2 manifest's drifted `# main.py:NNNN` inline comments and its
  "Verified against `c07dab8`" note to current `main` (citations drifted +18..+23).
- Resolve the `task_type` vocabulary mismatch (§8.3) before the registry hardcodes
  labels.

---

## 6. Roadmap — prioritization, ordering, grouping

Three waves by dependency, not calendar. Wave 0/1 have no upstream blocker; Wave 2 is
gated on the cascor 3-D long pole and the recurrence service; Wave 3 is triggered, not
scheduled.

### Wave 0 — Accuracy & tracking (now; hours; near-zero risk)

| Item | Why first | Output |
|---|---|---|
| File tracking issues for §5.1–§5.4 | None existed; roadmap items must be addressable | **DONE 2026-06-17** — canopy #368/#369/#370/#371 + ml #434, linked to this doc + PR #433 |
| Doc/comment hygiene (§5.5) | Stops the stale docs misleading the next reader | Banners on 2 docs; docstring + manifest-comment fixes |
| Squash-merge risk sweep (§8.4) | `#365`'s diff was lost to a stacked-squash footgun | Audit recent stacked merges; adopt rebase-merge policy |

### Wave 1 — Decoupled hardening + the model-selection registry/de-dup (now; no upstream blocker)

| Item | Approach (see §7) | Effort | Risk |
|---|---|---|---|
| `requirements.lock` reconcile (§5.3) | **C1** (pin lock to installed) | XS | Low |
| Harness-coverage extension (§5.4) | **D1** (enroll 3 controls in L2) | S | Low |
| `task_type`/gating-axis decision (§8.3) | Design spike | S | Low (design risk if skipped) |
| Model-selection **registry + de-dup** (§5.1) | **A0** (registry only; no dropdown/gate/mirror) | S | Low |

Order within Wave 1: lockfile + harness-coverage are quick and independent. The
`task_type`/gating-axis decision (§8.3) must precede A0 so the registry shape is frozen
correctly. A0 itself is a small, behavior-preserving refactor; the substantial gate
layer (A1) is deferred to early Wave 2 (§7.1).

### Wave 2 — Real model selection (upstream-gated; program-scale)

Wave 2 has **two triggers, not one barrier** (see the §6 fork and §8.2):

- **A1 gate layer** becomes worth building as soon as **either** upstream de-degenerates
  the gate: cascor 3-D ingestion (a 3-D dataset then correctly gates *out* cascor)
  **or** the recurrence service reaching `main` + PyPI + deploy (so `recurrence` goes
  live). Either alone makes the gate exercise a real incompatibility.
- **Full capability** (select `recurrence` AND train a cascor-incompatible 3-D dataset)
  needs **both**: (a) cascor 3-D + Δt ingestion (OQ-4 P3-C/LMU recurrent path —
  research-grade, "no cheap path"); and (b) the recurrence service — today only PR `#6`
  (skeleton) reached `main`; `#7` (routes) + `#8` (publish workflow) merged into stacked
  branches and never landed (§8.4), so the app is unpublished/undeployed; release is
  Paul-gated (PyPI pending-publishers + tag).

When the first trigger fires: build A1, flip `recurrence.is_live` as appropriate, and add
the model-gating browser proof (triggers Wave 3).

### Wave 3 — L3 dash_duo (triggered)

Take the dash_duo leg (**B2**) only if/when the model-gating UI lands and needs a
browser-level proof L2 cannot express (e.g., the soft-gate toast + value-revert
interaction). Until then, **B1** (status quo strict-xfail) stands.

### Dependency view

```text
Wave 0 (issues, hygiene, squash-sweep) ─┐
                                        ├─ independent, do now
Wave 1: lockfile(C1) ── harness(D1) ────┘
        task_type/gating-axis decision ── model-selection registry + de-dup (A0)
                                   │
                                   ▼
        A1 gate layer triggers on the FIRST de-degenerating upstream:
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                              ▼
  cascor 3-D ingestion (OQ-4)            recurrence service on main + PyPI
  "no cheap path"                        (today: only #6 landed; #7/#8 stranded — §8.4)
            │      either ONE alone de-degenerates the gate     │
            └──────────────────────┬──────────────────────┘
                                   ▼
        Wave 2: build A1 (dropdown + gate + a11y + backend mirror)
                                   │
        BOTH required for the FULL capability
   (select recurrence AND train 3-D cascor-incompatible data)
                                   │
                                   ▼
Wave 3: model-gating browser proof (B2)  ◄─ triggered, not scheduled
```

---

## 7. Approach options per workstream

Each workstream lists the viable options with strengths / weaknesses / risks /
guardrails, then a recommendation. Recommended option is first.

### 7.1 Model-selection feature (workstream A)

Options are split by how much of the feature ships before there is a *real*
dataset×model incompatibility to gate against. Validation insight: the bidirectional
gate is **degenerate today** (every shipped dataset is 2-D classification → all
cascor-compatible), so gate UX is value that cannot be exercised against reality until
an upstream lands (§8.2). That argues for shipping the *certain* value (de-duplication +
single-source registry) now and **deferring the gate**.

**A0 — Registry + de-duplication only; no dropdown, gate, or mirror yet (RECOMMENDED, Wave 1).**
Collapse the hardcoded dataset options (`dashboard_manager.py:1115-1119`) into a single
`model_registry` data structure (the `DatasetTypeSpec` half + a `ModelSpec` seed for
`cascor`). No user-facing `nn-model-dropdown`, no bidirectional gate, no backend mirror.

- *Strengths:* banks the **only currently-realizable value** — kills the
  hardcoded-options duplication and establishes the single source of truth — at XS–S
  effort and near-zero risk. No `task_type`-vocabulary commitment in the UI, no a11y
  surface, no speculative gate. A forward-compatible substrate for A1.
- *Weaknesses:* the published recurrence model stays invisible in the UI a while longer;
  no selector yet.
- *Risks:* low — a pure refactor behind an unchanged UI.
- *Guardrails:* the registry shape must accommodate the future `ModelSpec` fields
  (`supported_task_types`, `input_ndim`, `is_live`, `gated_reason`) without a rewrite;
  snapshot-test the rendered options to prove the refactor is behavior-preserving.

**A1 — Full scaffold: dropdown + bidirectional gate + a11y + backend mirror (early Wave 2).**
On top of A0: add the `nn-model-dropdown`, the bidirectional `task_type × input_ndim`
gate, the accessibility layer (soft-gate vs `aria-disabled` + wrapper tooltip + revert
toast), and the mandatory `nn_model` backend mirror on **both** request models.

- *Strengths:* the actual feature — a model selector with real compatibility gating and
  a discoverable, soft-gated `recurrence`. This is what design §4 scopes.
- *Weaknesses / why deferred:* until an upstream de-degenerates the gate (§8.2), it ships
  gate UX exercised only by a *synthetic* fixture that maps to no user-selectable
  dataset. Effort is **L (arguably XL)**, not the "M" it first looks: a new module, a
  control, gate logic, subtle a11y, a two-model backend mirror threaded through
  `demo_mode.py` **and** `demo_backend.py`, plus L1/L2 enrollment — a multi-PR tail.
- *Risks:* (1) `task_type` vocabulary mismatch — juniper-data emits
  `classification`/`regression`, the design assumes `time_series`/`irregular_dt`; commit
  the wrong gating axis and forward-compat breaks (§8.3); (2) **UX-rework risk** — the
  soft-gate toast + value-revert interaction is the riskiest UI and, built against a
  fixture-only gate, may need rework once real user flows exist (the 4 papers mitigate
  *implementation* correctness, not *UX-design* rework); (3) the deliverable-doc §3.2
  lesson — a field absent from a request model is silently dropped, so a half-built
  mirror is worse than none.
- *Guardrails:* resolve the vocabulary/gating-axis decision first (§8.3); derive
  `task_type` from juniper-data's actual contract; exercise the gate against a
  **synthetic 3-D incompatibility fixture** *and* a pure-function contract test
  (workstream B0); enroll the dropdown in L1 + add L2 rows in the same PR; the mirror
  must add `nn_model` to both request models with a clean `recurrence` rejection until
  the service exists.

**A2 — Wait for upstream.** Defer *all* canopy model-selection work (including A0) until
cascor 3-D + the recurrence service land.

- *Strengths:* the feature ships once, immediately meaningful; no throwaway scaffolding
  against a moving contract.
- *Weaknesses:* leaves the duplication + missing registry in place indefinitely; the
  published recurrence model stays invisible in the UI; the long pole (cascor 3-D) is
  not even started, so this is an open-ended idle.
- *Risks:* upstream slips → the canopy debt compounds (more hardcoded-options drift).
- *Guardrails:* file the tracking issue now with §4 linked; gate the start on a concrete
  upstream signal.

**A3 — Full vertical.** One coordinated cross-repo program: canopy gate + cascor 3-D
ingestion + recurrence service, delivered together end-to-end.

- *Strengths:* delivers the actual capability (select recurrence, train a 3-D
  irregular-Δt dataset). Maximal value.
- *Weaknesses:* enormous scope — the cascor feedforward↔recurrent boundary is
  research-grade (OQ-4); the recurrence service is stranded off `main` (§8.4); high
  coordination across 4 repos; long lead time.
- *Risks:* cascor 3-D has "no cheap path"; schedule + blast radius.
- *Guardrails:* only after the cascor 3-D design is ratified; strict upstream-first
  sequencing (data ✓ → cascor 3-D → recurrence service → canopy); run as a program, not
  a PR.

**Recommendation:** **A0 now** (Wave 1) — it converts a speculative L/XL into a certain S
and ships the only model-selection value that is real today. Take **A1** in early Wave 2,
triggered by the *first* upstream that de-degenerates the gate (cascor 3-D **or** the
recurrence service — either suffices; see §8.2 and the §6 fork). Reject **A2**
(needlessly leaves the duplication and an invisible model). Treat **A3** as a separate
later program, not an "evolution" of A0/A1 — A0/A1 are deliberately *decoupled,
canopy-first*, the opposite of A3's coordinated-delivery stance. The A0→A1 forward-compat
("flip `recurrence.is_live`") holds **only if** the §8.3 gating-axis decision modeled the
registry on the dimension that actually distinguishes the models (`input_ndim`), not on a
`task_type` vocabulary upstream may not emit — so make that decision before A0 freezes the
registry shape.

### 7.2 L3 real-browser proof (workstream B)

**B1 — Keep strict-xfail status quo (RECOMMENDED for now).**

- *Strengths:* zero new deps/flake; L2 already proves the Apply contract
  deterministically; the xfails auto-flip red if Dash fixes the event path (free
  canary); the 9 existing Playwright tests stay.
- *Weaknesses:* no real-browser keystroke coverage; clientside-callback / DOM-event
  regressions aren't exercised end-to-end.
- *Risks:* a browser-only regression (e.g., clientside `buttonMap` break) slips L1+L2.
- *Guardrails:* document the wall in-code (done); revisit when B2's trigger fires.

**B0 — No-browser gate-logic contract test (RECOMMENDED companion to B1, ships with A1).**
Extract the gate decision (`models_for_dataset` / `dataset_values_for_model` and the
clientside `buttonMap`/gate mapping) into pure functions and unit-test them directly in
Python (and a small JS unit test for the clientside half). No browser.

- *Strengths:* directly attacks the risk B1 leaves open — a `buttonMap`/gate *logic*
  regression — with zero Selenium flake and default-suite speed; proves A1's gate
  decision table deterministically.
- *Weaknesses:* does not prove the DOM *rendering* of the gate (disabled styling,
  tooltip visibility) — only the decision logic.
- *Risks:* requires the gate logic to be authored as testable pure functions (a mild,
  beneficial design constraint).
- *Guardrails:* land B0 *with* A1's gate (same PR) so the decision table never ships
  untested; keep it in the default suite.

**B2 — Add the dash_duo/Selenium leg.** The design's POC #1.

- *Strengths:* real `send_keys` fires React `onChange` natively (Dash-official path);
  un-xfails the numeric proof; closes the browser-leg gap.
- *Weaknesses:* adds CI weight + a new flake surface for a deliberately thin layer;
  proves a contract L2 already covers (redundancy, not coverage gain).
- *Risks:* browser/driver flake; CI time; maintenance.
- *Guardrails:* isolate in its own non-blocking `make test-ui-dash` job initially;
  time-box; scope to the `browser_proof` subset (one numeric roundtrip, one dropdown,
  one button→DOM, the model-gating proof).

**B3 — Playwright-via-renderer-shim.** Drive inputs through Dash clientside
`setProps`/renderer rather than raw DOM events.

- *Strengths:* stays on Playwright (already in env); no Selenium.
- *Weaknesses:* couples tests to Dash renderer internals; version-fragile; POC #2
  already proved the raw-event path fails.
- *Risks:* high maintenance, breaks across Dash upgrades.
- *Guardrails:* spike-only; abandon if it reaches into private renderer internals.

**Recommendation:** **B1 + B0** — keep the strict-xfail status quo *and* add the
pure-function gate-logic contract test (B0) when A1's gate lands; B0 kills the
`buttonMap`-regression risk without a browser. Escalate to **B2** (scoped to the gate
interaction) only if the *rendered* gate UX needs browser-level proof L2/B0 cannot
express. **B3** is a fallback spike only.

### 7.3 `requirements.lock` reconcile (workstream C)

**C1 — Regenerate the lock to the installed/green set (constraint-mode re-resolve) (RECOMMENDED).**

- *Strengths:* lock reflects reality; removes the CI-vs-local gap; smallest change.
- *Weaknesses:* moves pins backward; may re-drift on the next dependabot bump.
- *Risks:* downgrade breaks a 4.2.0-only dependency (unlikely — 4.1.0 is the green
  installed baseline).
- *Guardrails:* regenerate via the repo's constraint-mode lockfile flow (compile to a
  scratch path then `mv` to avoid the uv self-pin trap); run the full suite + L1/L2
  post-regen; confirm no code path requires dash 4.2.0.

**C2 — Upgrade installed up to the lock (adopt dash 4.2.0).**

- *Strengths:* moves forward; the lock becomes the single source of truth.
- *Weaknesses:* dash 4.1.0→4.2.0 may alter Dash behavior — and the L1 lint depends on
  `app.callback_map` / layout `.children` traversal, exactly the surface most exposed
  to a Dash change. Touches the live env + Docker image.
- *Risks:* behavior change in the traversal the harness relies on; larger blast radius.
- *Guardrails:* re-run L1+L2+UI on 4.2.0 *before* adopting; read the 4.2.0 changelog for
  callback/layout changes; stage in env first, then rebuild the Docker image.

**C3 — Make CI install from the lock (structural).**

- *Strengths:* closes the "CI pins what it runs" gap regardless of which versions.
- *Weaknesses:* orthogonal to the dev-env drift; if the lock keeps 4.2.0 it inherits
  C2's re-verify need.
- *Guardrails:* combine with C1 (pin down, then have CI install the lock).

**Recommendation:** **C1** now (pin to green, verify the harness traversal holds);
defer the forward upgrade (C2) to the normal dependabot cadence behind a harness
re-verify gate. C3 is a good structural follow-up after C1.

### 7.4 Harness-coverage extension (workstream D)

**D1 — Enroll the 3 newly-wired controls into L2 (RECOMMENDED).**

- *Strengths:* behaviorally proves the `#366` fixes (today only L1-wired); follows the
  manifest's own "one row per control" contract; cheap; closes the wired-vs-proven gap.
- *Weaknesses:* `restart-with-new-dataset-button` has a side effect (start-with-reset)
  needing a careful demo-mode assertion; modest effort.
- *Risks:* low; demo-mode is deterministic.
- *Guardrails:* demo-mode only; assert via `/api/state` or `/api/status` roundtrip; keep
  rows declarative; fold into the doc-hygiene PR.

**D2 — Leave L2 at 8 rows; rely on per-fix regression tests + L1.**

- *Strengths:* no new work; `#366` shipped dedicated regression tests.
- *Weaknesses:* the manifest is the future-proofing surface — leaving fixes out breaks
  the "one row per control" contract; future refactors of those controls escape the
  manifest.
- *Guardrails:* verify each newly-wired control has at least a dedicated regression
  test before accepting this.

**Recommendation:** **D1** — small, high-leverage, and exactly what the manifest is for.

---

## 8. Cross-cutting risks & guardrails

### 8.1 Regression-class coverage map (what the harness does and does not catch)

The user's framing is "multiple classes of regressions." The harness closes one class
hard and partially covers two more:

| Regression class | Caught by | Status |
|---|---|---|
| Dead control (actionable but unreachable by any callback) | L1 lint | **Fully gated** |
| Backend-contract break (wired control's endpoint/state contract) | L2 manifest (8 controls) | **Partial** — only enrolled controls; extend via D1 |
| Wrong *behavior* of a wired control / state desync | per-fix regression tests | **Ad-hoc**, not systematic |
| Browser/clientside-event regression (DOM, clientside callbacks) | L3 (xfail) + 9 Playwright tests | **Thin** — B-workstream gap |

*Guardrail:* treat D1 (and, later, B2) as the path to systematic coverage of the lower
two rows. Do not claim the harness covers "all regressions" — it covers reachability
fully and contract/behavior selectively.

### 8.2 Upstream sequencing — cascor 3-D is the long pole for *full* capability

The gate stays degenerate ("cascor + coming-soon") only until the **first** upstream
de-degenerates it — and *either* suffices: cascor 3-D ingestion (a 3-D dataset then
correctly gates cascor *out*) **or** the recurrence service going live (`recurrence`
becomes a real selectable target). The **full** capability (select `recurrence` AND
train cascor-incompatible 3-D data) needs both, and cascor 3-D is the long pole there —
a research-grade change (OQ-4: hard ndim>2 rejections, 2-D-only memory, `dt`/`mask`
discarded even if a 3-D array slipped in). *Guardrails:* do not couple Wave-1 (A0)
delivery to either upstream; and do not assume A1 is a mere flag-flip away — the A0→A1
forward-compat holds **only if** the §8.3 gating-axis decision modeled the registry on
the dimension that actually distinguishes the models (`input_ndim`), not on a `task_type`
vocabulary upstream may not emit.

### 8.3 `task_type` vocabulary / gating-axis decision (must resolve before A0 — it freezes the registry shape)

juniper-data emits `classification` / `regression`; the design assumes `time_series` /
`irregular_dt`. If the registry hardcodes either side, it diverges. *Guardrail:* make
the registry's `DatasetTypeSpec.task_type` derive from / map to juniper-data's actual
emitted values, with an explicit mapping table for the future time-series labels;
decide this in the Wave-1 design spike before writing the registry.

### 8.4 Squash-merge process risk (latent, ecosystem-wide — and already recurring)

This footgun has bitten **at least twice**: (1) canopy `#365`'s diff never reached
`main` (squash-merged into a stacked intermediate branch; recovered by `#366`); and
(2) juniper-recurrence `#7` (WS-4b routes) + `#8` (publish workflow) show **MERGED** but
targeted stacked branches (`feature/ws4b-app-skeleton`, `feature/ws4b-app-routes`) — only
`#6` (skeleton) targeted `main`, so the routes + publish workflow never landed and the
recurrence app is unpublished. Both match the known pattern "GitHub Squash-and-Merge
ships first commit only." *Guardrail (with teeth):* (a) **scope** — every stacked PR
merged since 2026-06-01 across the 8 repos; (b) **detection** — for each,
`gh pr view <n> --json baseRefName` (flag any `baseRefName` not `main`/`develop`) and
confirm the head diff is reachable from `origin/main`
(`git merge-base --is-ancestor <pr-head-sha> origin/main`); (c) **acceptance** — a
checklist of `(PR, baseRef, landed-on-main? y/n, remediation)`; (d) **policy** — for
future stacked PRs prefer rebase-merge or retarget-to-`main`-then-merge, and verify the
diff is on `main` post-merge. Start with juniper-recurrence `#7`/`#8` (known-stranded).

### 8.5 Doc-staleness risk

Two now-merged docs still read as in-flight. *Guardrail:* the Wave-0 banners; and going
forward, prefer a single living roadmap (this doc) over snapshot-dated deliverables that
silently age.

---

## 9. Validation methodology + evidence appendix

**Phase 1 — current-state validation (complete).** Five independent sub-agents each
owned a non-overlapping slice and reported per-claim verdicts with `file:line` evidence
against actual default branches:

| Agent | Slice | Headline finding |
|---|---|---|
| A | Harness reality (L1/L2/L3 + CI) | All present on `main`; `KNOWN_ORPHANS == {}`; lint exit 0 |
| B | Orphan-fix reality | All 3 orphans wired (`#366`); doc §3 stale |
| C | Model-selection + upstream | Feature 0% built (design accurate); data ✓, recurrence service ✗, cascor 3-D blocked |
| D | Citations / papers / lockfile | Cites ~100% resolvable; 4 papers good; lock still pins dash 4.2.0 |
| E | Cross-repo PR/issue state | Entire iteration merged 2026-06-16; nothing open; 3 follow-ups untracked |

Cross-corroboration: B and D independently found the same orphan wiring and the
docstring ambiguity; A and B independently found `KNOWN_ORPHANS` empty. The two most
decision-critical facts (`KNOWN_ORPHANS` contents; L2 manifest = 8 rows) were re-read
directly by the orchestrator — confirming both, and *softening* one agent claim: the
lint docstring's three-control mention is an ambiguous historical reference, not a live
contradiction (recorded as a low-priority wording nit, §5.5).

**Reproduction commands** (env `JuniperCanopy1`;
`source /opt/miniforge3/etc/profile.d/conda.sh && conda activate JuniperCanopy1`):

| Claim | Command | Observed |
|---|---|---|
| Zero orphans on `main` | `cd /…/juniper-canopy && python util/ui_control_graph.py; echo $?` | "No orphan controls"; exit 0 |
| `KNOWN_ORPHANS` empty | read `src/tests/unit/test_control_graph_lint.py:29` | `KNOWN_ORPHANS: dict[str, str] = {}` |
| L2 = 8 rows | read `src/tests/ui_contract/control_manifest.py:50` | 8 `ControlContract` entries |
| Lock drift | read `requirements.lock` vs `pip show dash` | lock 4.2.0 / installed 4.1.0 |
| Iteration merged | `gh pr view 364 366 --repo pcalnon/juniper-canopy` | merged 2026-06-16 |

**Phase 2 — validation of this document (complete).** Four independent sub-agents
validated this document — source-fidelity (re-opened every `file:line`),
internal-consistency + completeness, roadmap/decision soundness, and markdown/structure
lint. Material findings folded into this revision:

1. The `juniper-recurrence` service PR state was corrected — `#6`/`#7`/`#8` are all
   *merged*, but `#7`/`#8` targeted stacked branches and never reached `main` (the §8.4
   footgun recurring), not "open" as first drafted (verified by orchestrator via
   `gh pr list --repo pcalnon/juniper-recurrence`).
2. The model-selection workstream was split into **A0** (registry + de-dup, Wave 1) and
   **A1** (gate layer, early Wave 2) after the decision review showed A1's gate is
   upstream-blocked value and an L/XL — not M–L — build.
3. The §6 dependency graph was corrected from an AND-barrier to a fork (either upstream
   de-degenerates the gate); the "flip a flag" forward-compat claim was made conditional
   on the §8.3 gating-axis decision.
4. A no-browser gate-logic contract test (**B0**) was added to workstream B.
5. The FRONTEND_ISSUES_PLAN cross-link was corrected to "#1–#6 all resolved".
6. The squash-merge guardrail (§8.4) was given concrete detection teeth.
7. One markdown line-wrap lint nit was fixed; the `generators.py` span was corrected to
   the literal dict bounds (42-165).

Source-fidelity result: zero wrong source anchors; ~40 `file:line` claims confirmed
byte-exact; the only correction class was temporal drift the doc already anticipated.
The validators' raw findings are retained in the session record.

---

## 10. References & cross-links

**Predecessor docs (juniper-ml `notes/`, superseded framing):**

- [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md)
- [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-REGRESSIONS-AND-MODEL-SELECTION.md)

**Related juniper-ml `notes/`:**

- [`JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md`](JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md) — FRONTEND_ISSUES_PLAN Issues #1–#6 (the prior frontend backlog, all resolved)
- [`JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md`](JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md) — dataset readiness for the recurrence path
- the `JUNIPER_RECURRENCE_*` / WS-1 / WS-4 corpus — model-selection upstream

**External literature (juniper-ml `papers/`, retrieved 2026-06-16):**

- `nngroup-disabled-buttons.md`, `w3c-aria-tooltip-and-disabled.md`,
  `dash-testing-dash-duo.md`, `react-controlled-input-onchange.md`

**Key canopy source anchors (`main` @ `d13649f`):**

- L1: `util/ui_control_graph.py`; gate `src/tests/unit/test_control_graph_lint.py`
- L2: `src/tests/ui_contract/control_manifest.py`; driver
  `src/tests/integration/test_control_manifest_behavioral.py`
- Orphan fixes: `src/frontend/dashboard_manager.py:2806,3436,3629`;
  `src/main.py:2875`; `src/demo_mode.py:1475,2060`
- Hardcoded options to de-duplicate: `src/frontend/dashboard_manager.py:1115-1119`
