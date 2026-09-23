# Juniper-Canopy — Selection Reachability: Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-02
- **Status**: Design of record for the remediation — §10 answered and dispositioned (2026-09-02); scope extended to iteration 2 (§12); **implemented**: all five PRs of §7 have shipped on juniper-canopy `main`, and the parallel packaging workstream is merged in juniper-data but not yet released (§7)
- **Last Updated**: 2026-09-23 — reconciled against the ship map, `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`, with each claim re-verified in canopy source at `main` `3a6dea95`. Added: a status line under each §4.x heading, shipped statuses in §5 and §7, and dated corrections wherever `main` contradicts the text. Superseded text is kept and annotated, not rewritten.
- **Amends**: [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
- **Evaluation of record**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md)

Guardrail identifiers **G1–G6** and defect identifiers **X1–X6 / Y1–Y9** are defined in the
evaluation document (its §8 and §6) and are used here with the same meaning. **G7–G11** and
decisions **N10–N13** are introduced here, when the §10 open questions were answered.

---

## 1. Scope

Restore reachability of every compatible-and-available `(model, dataset)` pair in canopy's
selection UI, and land the companions that the restoration **activates**. The defect, its
measurement, the sixteen proposals and the two adversarial rounds that selected among them are in
the evaluation document; this document specifies what to build.

**Scope revision (2026-09-02, §11).** The ten unseeded juniper-data generators are **in scope for
this arc**, as iteration 2 — specified in §12. The stated goal is a platform without gaps in
required functionality, and a research platform that exposes 6 of its 16 datasets has a capability
gap of the same standing as a workflow defect.

One refinement to that framing, which changes sequencing rather than scope: the missing generators
are a **capability gap**, while X1 is a **correctness defect**. A missing dataset is visible and
safe; a misreported model is invisible and unsafe, because it silently corrupts the provenance of
a benchmark result. Both ship in this arc; correctness-of-reporting leads (§7).

Out of scope, deliberately: relocating the capability model to the producing services (family F5
of the evaluation), which remains follow-on work.

---

## 2. The invariant this establishes

From §2.1 of the evaluation document, the shipped code enforces `I-safe` (every visited state is
compatible) and never stated `I-cover` (every compatible state is reachable). The remediation adds
`I-cover` **without weakening `I-safe`**:

> **I-safe** — no sequence of admitted transitions leaves the UI on a *committed* pair for which
> `compatible()` is False.
> **I-cover** — every pair that is both `compatible()` **and available** is reachable from the
> mount state.

**`I-cover` is conditioned on availability, and that condition is load-bearing.** A dataset whose
generator is unavailable is legitimately unreachable; §6.3 of the evaluation shows this is the
container's normal state, where the LMU has zero available datasets. An unconditioned `I-cover`
would be unsatisfiable by any UI change.

The rejected alternative (family F2) established `I-cover` **by breaking `I-safe`**: measured, it
created five reachable-but-invalid states while still failing to reach the target pair (evaluation
§5.1). That is the trade this design refuses.

The mechanism satisfying both is a **universal cut vertex**: a null dataset value `⊥`, compatible
with every model, joining every connected component of the compatibility graph.

**`⊥` is an incomplete state, not a valid one, and the distinction must be enforced rather than
assumed.** An earlier draft asserted `⊥` was "not trainable"; that is **false** as shipped —
`_update_button_appearance_handler` (`:7187`) takes `(self, button_states, model_key)` with no
dataset argument, and `:7206` gates Start solely on `model_is_trainable`. At `⊥` today,
`(recurrence, ⊥)` fails closed with a 409, but **`(cascor, ⊥)` sends the bare start POST and
trains on the last-staged dataset while the sidebar shows no dataset.** X5 (§4.8) closes this and
is a prerequisite of `⊥`, not an enhancement.

> **Superseded 2026-09-06 (canopy#593).** True when written. `_update_button_appearance_handler`
> now takes `dataset_value` (and, since canopy#601, `model_state`) and disables Start whenever
> either axis is unset (`selection_axis_unset`), so neither `(cascor, ⊥)` nor `(recurrence, ⊥)` is
> startable from the sidebar. The same callback disables Apply Dataset at `⊥`. See §4.8.

---

## 3. Decisions

| id     | decision                                                                                                                                                                                                                                                               |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **N1** | **Reachability is a stated invariant, not an emergent property.** `I-cover` and `I-safe` (§2) are written down, tested at handler level, and fail the build when violated. The design of record's silence on reachability is the root omission.                        |
| **N2** | **Restore the unset dataset state (implements ratified D4/FR6, in part).** `clearable=True` on the sidebar dataset dropdown. §5.5 of the design of record specifies **two** affordances; only the dropdown ✕ is in scope here (see OQ-N6). **Superseded the same day by N11**: the model clear came into scope too. The ✕ shipped in canopy#593, the model clear in canopy#594. |
| **N3** | **The gate stays symmetric and hard (upholds D2/FR5 unchanged).** No `disabled` predicate is relaxed. Family F2 would have amended this, and both adversarial rounds rejected that amendment (evaluation §5.1, §7).                                                    |
| **N4** | **Name the consequence at the locus, in rendered content.** Never via `title=`, which §8 of the design of record rules out and which Y7 shows is a dead accessibility channel here.                                                                                    |
| **N5** | **A model whose displayed identity differs from the live backend is a defect, not a display lag.** The UI reads `swapped` and `backend`. Silent misattribution is worse than a blocked control for a benchmarking platform (X1). **Shipped (canopy#592) reading `backend` against the model's provider, not `swapped`**, which is also False when the live model is re-selected (§4.4). |
| **N6** | **Fail closed and say so.** The `ok=True`-then-fail-in-thread pattern (`recurrence_backend.py:154-156`) is not acceptable on a newly-reachable path.                                                                                                                   |
| **N7** | ~~**OQ-6 remains open.**~~ **ANSWERED 2026-09-22: `model-primary`, resolved by clearing** (§5.6.1 of `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`; shipped in juniper-canopy#652). This design still does not *choose* the default — it made OQ-6 answerable, and that framing was exactly right: under `clearable=False` both policies in §5.6 were unimplementable, because both say *clear* and a null dataset was not expressible. The answer became available only once §4 made both axes clearable, and the handler's `enabled[0]` snap turns out to have been the workaround for that impossibility rather than a chosen policy — it was labelled "dataset-primary" while doing neither policy. |
| **N8** | **The empty compatible∩available set is an explicit state.** It renders a recovery affordance, never `no_update`.                                                                                                                                                      |
| **N9** | **A control that cannot be honoured is disabled at the control, not discovered at the backend.** Start requires a dataset (X5); Apply Dataset requires a dataset (X4).                                                                                                 |

Decisions **N10–N13** were added 2026-09-02 when the §10 open questions were answered. Each
records a prerequisite the answer needs in order not to reintroduce the defect class this design
exists to close.

| id | decision |
|-----|----------|
| **N10** | **`⊥` at mount requires backend hydration first.** The dataset axis becomes unset-by-default (OQ-N2) **only once canopy hydrates it from the backend**. Without that, `⊥`-at-mount converts a usually-correct default into a post-reload state where Start and Apply Dataset are both disabled over a staged, ready backend — the X1 class on the dataset axis (§4.10). |
| **N11** | **Both axes are clearable, and a cleared axis ungates its peer.** OQ-N6 ships the "clear model / show all" reset. A cleared model must render **ungated** dataset options; today the handler early-returns `no_update` and would freeze the dropdown at the previous model's gate (§4.11). |
| **N12** | **A transient notice and a blocking state are different channels.** A successful gate repair is a **toast**; an unresolvable empty compatible∩available set is a **persistent inline alert**. Neither replaces N4's rendered annotation at the locus, because a toast alone is invisible to assistive technology (§4.3). **Shipped (canopy#595) with no `Toast`**: the transient notice is an auto-dismissing inline alert at the locus, and since canopy#652 it reports a clear, not a repair (§4.3). |
| **N13** | **Demo mode dogfoods the platform, and degrades loudly.** It keeps auto-loading the default spiral dataset and continues to source it from juniper-data; the local generator survives only as a **visibly announced** degraded mode, never a silent parallel implementation (§4.12). |

---

## 4. Mechanism

### 4.1 The clear affordance (N2)

> **Status (2026-09-23): SHIPPED** — canopy#593 (`aa611561`, 2026-09-06). The traversal's third step
> changed with canopy#652 (2026-09-22): a conflict now clears the dataset and the operator picks
> (note below), and canopy#656 (2026-09-22) made a gate re-fire at `⊥` silent.

`dashboard_manager.py:1334` — `clearable=False` → `clearable=True`.

The destination state is **already built and already tested**. Verified by execution:
`_build_model_selection_table(None, 'cascor')` returns both Select buttons `disabled=False`;
`_dataset_model_hint_handler(None)` returns `''`; `_resolve_oneshot_start_body_handler('one_shot',
None)` returns `None`. It is pinned by a passing regression test whose comment already reads *"No
dataset selected (e.g. cleared)"* (`test_model_table.py:170-173`). All **ten** Python consumers of
`nn-dataset-type-dropdown.value` are null-safe; there are **zero** JS consumers.

Traversal to the previously-unreachable pair, where the dataset is available:

```text
(cascor, spirals)  --clear dataset-->       (cascor, ⊥)
                   --Select Recurrence-->   (recurrence, ⊥)
                   --gate re-fires, enabled == ["equities_seq"] -->  (recurrence, equities_seq)
```

The third step is the existing snap at `:2702-2706`. Note the mechanism precisely: the snap
behaves identically whether the current value is `None` or `'spirals'` — what differs is where its
`or not enabled` branch leaves you. From `⊥` that branch leaves an *incomplete* selection; from a
concrete dataset it leaves a *complete but invalid* one. Clearing is also not itself re-gated,
because `gate_dataset_options` reads the dataset as `State` (`:2609`), not `Input`.

> **The third step no longer happens by itself (2026-09-23).** juniper-canopy#652 deleted the
> snap. OQ-6 was ratified as model-primary, resolved by clearing: see §5.6.1 of
> `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`. From `(recurrence, ⊥)`,
> the re-fired gate now leaves the dataset at `⊥`, and **the operator picks** `equities_seq` from a
> list in which it is the enabled entry. `I-cover` is unaffected, because the pair is still reachable
> in one pick. What changed is who takes the last step: the operator, not the gate. The quoted
> line numbers above are those of 2026-09-02; locate by symbol.
>
> **Correction, 2026-09-23 (ship-map reconciliation).** The traversal's `enabled == ["equities_seq"]`
> was true when written and stopped being true with canopy#612 (2026-09-10). The note above, written
> 2026-09-23, was wrong to call `equities_seq` "the enabled entry". Recurrence's compatible set is
> six rank-3 seeds, offered in registry order `multi_sine`, `mackey_glass`, `irregular_sine`, `ar_p`,
> `delay_product`, `equities_seq` (pinned by `test_the_lmu_s_compatible_set_is_the_six_rank_3_seeds`),
> and `equities_seq` is greyed wherever juniper-data lacks the `equities` extra. The pair is still
> reachable in one pick. Since canopy#667 (OQ-N2) the dropdown also mounts at `⊥` (§4.10).

### 4.2 The null-dataset guard (X4)

> **Status (2026-09-23): SHIPPED** — canopy#593 (`aa611561`, 2026-09-06): Apply Dataset is disabled
> at `⊥`, and `_apply_dataset_handler`, `_restage_dataset` and the live swap each refuse `⊥` without
> posting (`TestCommitPathsAreGuarded`).

`_apply_dataset_handler:2845` must not POST `{"nn_dataset_type": None}` — `main.py:3994`'s
`model_dump(exclude_none=True)` strips it into a vacuous 200 plus a false pending-banner. Guard it
and disable **Apply Dataset** at `⊥` (N9). The correct idiom already exists at
`_restage_dataset:5629-5631`.

> **Correction, 2026-09-23.** Two statements here were wrong when written. The `⊥` POST is not
> vacuous but destructive: the stripped body is `{}`, and cascor's `StageDatasetRequest` documents
> an empty body as clearing any prior staging (the docstring is present at cascor's 2026-09-02
> tip). And `_restage_dataset` was not the correct idiom: skipping the key sends the same empty
> body. canopy#593 made both paths refuse `⊥` instead; its comments in `_apply_dataset_handler` and
> `_restage_dataset` record why.

### 4.3 Consequence naming (N4)

> **Status (2026-09-23): SHIPPED, with departures** — canopy#594 (Y9), canopy#595 (the notices and
> the `role="status"` region), canopy#652 (the docstring) and canopy#671 (Y7's `aria-describedby`,
> 2026-09-23). No `Toast` was built, and the transient notice now reports a clear rather than a move
> (notes below the list).

- **Fix the inverted docstring first.** `:2695` labels the snap "dataset-primary" when it is
  model-primary (evaluation §2.2). The notice is written from that description; correcting the
  artifact must precede writing UI copy from it.
- When the dataset is `⊥`, the model table's compatibility cell must **not** render "✓ compatible"
  for every model (Y9) — that is a positive falsehood. Render what the row *would* require.
- Render the §5.6 notice — the notice D5 always specified and the snap never shipped — when the
  gate moves the dataset, naming the old and new value.
- **Two events, two channels (N12).** OQ-N4 asked for "a toast when the gate fails and a persistent
  error until the situation is resolved". Those are two different events and the split is what
  makes the answer coherent:

  | event | nature | channel |
  |-------|--------|---------|
  | the gate **successfully** moved the dataset (D5's notice) | informational; nothing to resolve | **toast**, auto-dismissing |
  | compatible ∩ available is **empty** (§4.7) | blocking; resolvable | **persistent inline alert**, cleared only by resolution |

  "Persistent until resolved" only applies to the second — the first is not a situation to resolve.
  Two practicalities: canopy has **zero** `Toast` components today, so this is new surface carrying
  its own dismiss / stacking / timer state; and a toast without `role="status"` / `aria-live` is
  invisible to assistive technology (Y7 records zero `aria-*` attributes in `dashboard_manager.py`).
  The toast therefore **supplements** the rendered annotation at the locus; it must not be the only
  channel, or the notice is an accessibility regression against simply rendering it inline.
- Both in rendered DOM content (N4). Give the reason cell an `id` and point the row's control at
  it with `aria-describedby` (Y7).

> **Shipped as, and superseded, 2026-09-23.** Checked against canopy `main`:
>
> - **The docstring** (first bullet) was fixed by canopy#652 (2026-09-22), after the notices it was
>   meant to precede had shipped in canopy#595. `_gate_dataset_options_handler` no longer calls its
>   conflict rule "dataset-primary".
> - **D5's notice** (third bullet, and the table's first row) shipped in canopy#595 as
>   `_dataset_repaired_notice`, naming the old and new value. canopy#652 replaced it with
>   `_dataset_cleared_notice` ("Dataset cleared", naming what was dropped and why), because a
>   conflict now clears the dataset instead of moving it (OQ-6, N7).
> - **The toast is not a `Toast`.** canopy still has none. The transient notice is a dismissable
>   `dbc.Alert` that auto-dismisses (`duration=8000`), rendered into `dataset-gate-notice`, a
>   `role="status"`, `aria-live="polite"` region at the locus (canopy#595). It is therefore the
>   accessible channel at the locus rather than a supplement to one. That region, and canopy#671's
>   `aria-describedby`, retire the "zero `aria-*` attributes" statement above, which was true when
>   written. The persistent alert shipped as specified (`_empty_dataset_set_notice`, no `duration`).
> - **Y7's bullet** (last) shipped in canopy#671 (`7cd8a9d4`) for the model table, which is what it
>   specified: each Compatibility cell has an id (`_model_compat_cell_id`), every row's Select is an
>   `html.Button` carrying `aria-describedby` to it, and `title=` is dropped on disabled Selects.
> - **What remains of Y7** lies outside this section's specification. The evaluation's Y7 also
>   records that dash's dropdown emits no `aria-disabled`, and that is unchanged: canopy `src/` sets
>   `aria-disabled` nowhere, so a greyed dataset option's reason suffix (`gated_dataset_options`) is
>   still its only accessible signal. canopy#671 counts the dropdown half as shipped through the
>   `role="status"` notice, but that notice announces what the gate did, not which options are
>   greyed. The browser posture has not been re-measured since OQ-N5 (2026-09-02).

### 4.4 Model-state truth (N5 / X1)

> **Status (2026-09-23): SHIPPED, with a deliberate departure** — canopy#592 (`b5ad897b`, 2026-09-06),
> extended by canopy#601 (`5d7dd6aa`, 2026-09-09). The predicate is "does the live backend serve this
> model", not `swapped is False` (note below).

`_select_model_handler` currently mirrors only `nn_model` and `execution` (`:2893`; def at
`:2876`). It must also read `swapped` and `backend`, and when `swapped is False` render the model
summary as **not active**, with the reason. Canopy's own test already pins the response shape
(`test_d8_d11_phase4_truth_up.py:64-82`).

> **Superseded 2026-09-06 and 2026-09-09.** "Currently mirrors only `nn_model` and `execution`" was
> true when written. canopy#592 made the summary read provider agreement through
> `_selection_is_live`. canopy#601 moved that predicate to `model_registry.selection_is_live` and made
> `_select_model_handler` return the whole `/api/model/select` payload into `model-state-store`,
> which the Start gate and the train-gate notice read; the server refuses an inactive selection on
> its own (`main._selection_inactive_reason`). The prescribed `swapped is False` test was not built,
> on purpose: `swapped` is also False when the operator re-selects the model already live, so it
> would report a running CasCor as inactive.
> `TestG5ModelStateTruth.test_noop_reselect_of_the_live_model_still_reads_active` pins that case.

**This ships first.** Unblocking selection without it converts the deadlock into silent benchmark
misattribution.

### 4.5 The restart modal (X2)

> **Status (2026-09-23): SHIPPED, with an owner-ruled departure; tested since 2026-09-23** —
> canopy#593 (`aa611561`, 2026-09-06). The modal keeps an `enabled[0]` swap where the sidebar clears,
> and its regate had no test until canopy#675 (`0254a7ec`, 2026-09-23) (note below).

`restart-ds-type` has no writer for `.options` anywhere in the repo. Add
`Output("restart-ds-type", "options")` + `State("model-selection-store", "data")` to
`open_restart_confirm_modal` (`:5260-5293`), composing `apply_availability_gate` as the sidebar
does at `:2702`. Without this, the fix *activates* an inverted gate that `execute_restart`
forwards.

> **Superseded 2026-09-06 (canopy#593).** "No writer" was true when written. `open_restart_confirm_modal`
> now has exactly the `Output` and `State` asked for, and `_open_restart_confirm_modal_handler`
> composes `apply_availability_gate` over `gated_dataset_options` for the selected model on every
> open. It landed with the ✕ in canopy#593, so §7's quarantine fallback was never needed. Three
> things a reader should know:
>
> - **The fallback swap is deliberate.** Where the sidebar clears a conflicting dataset (OQ-6,
>   canopy#652), the modal replaces it with `enabled[0]`. The owner ruled on 2026-09-22 to keep that
>   swap, because the modal is a confirmation dialog that shows the swapped value before anything is
>   re-staged: §5.6.1 point 4 of `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`.
>   Registry order decides where it lands (§12.6). An unset sidebar dataset stays unset.
> - **It had no test.** Regating the list against `DEFAULT_MODEL_KEY` instead of the selected model
>   passed canopy's entire CI unit lane with zero failures at canopy `48074653` (the ship map's M6,
>   reproduced 2026-09-23 with `util/ad-hoc/2026-09-23_mutation_check_m1_m6.py`). canopy#675
>   (`0254a7ec`, 2026-09-23) added `TestX2RestartModalIsGatedAgainstTheSelectedModel`, which fails
>   twice under that mutant.
> - **Re-staging from the modal** refuses `⊥` (canopy#593) and sends the registry seed
>   (canopy#668, 2026-09-23), so a seeded generator such as `equities` no longer 422s from here.
>   Since canopy#674 (`894a2cc7`, 2026-09-23) the re-stage and the modal's parameter apply also send
>   FR9's `nn_model` mirror. `/api/train/restart` itself carries no model identity, so a restart
>   with nothing edited is not checked against the server's model.

### 4.6 The generator alias (X3)

> **Status (2026-09-23): SHIPPED** — canopy#599 (`de253e93`, 2026-09-07): the one-shot body names
> `generator_name_for_type(value)` and looks its params up under canopy's own value
> (`TestX3OneShotBodyUsesTheResolvedName`).

`_resolve_oneshot_start_body_handler` (`:2681`) must route its value through
`generator_name_for_type`, as both sibling handlers do (`:2769`, `:2846`).

> **Correction, 2026-09-23.** "As both sibling handlers do" was imprecise when written. The two
> cited siblings, `_render_dataset_params_handler` and `_apply_dataset_handler`, use the alias only
> for lookups (the generator's schema, and the spiral branch). Neither translates the value it
> sends, and the staging payload must not be translated: cascor's `dataset_type` `Literal` takes
> canopy's plural names. canopy#599 pins that asymmetry with
> `test_the_STAGING_payload_must_NOT_be_translated`.

### 4.7 The empty-set state (N8)

> **Status (2026-09-23): SHIPPED** — canopy#595 (`0096f567`, 2026-09-06); the conflict arm was changed
> by canopy#652 and a re-fire at `⊥` by canopy#656, both 2026-09-22 (note below).

`_gate_dataset_options_handler`'s `if current_value in enabled or not enabled: return options,
dash.no_update` (`:2702-2706`) must distinguish its two arms. `not enabled` — no dataset is both
compatible and available — is a **recovery state**: clear the dataset to `⊥`, render why, and gate
Start.

> **Superseded 2026-09-06 (canopy#595).** The quoted line is the code as it stood on 2026-09-02.
> `_gate_dataset_options_handler` now has four outcomes: `not enabled` clears to `⊥` and renders the
> persistent `_empty_dataset_set_notice` (Start and Apply are then disabled at `⊥`); `⊥` changes
> nothing and reports no conflict (canopy#656); `current_value in enabled` changes nothing; and a
> conflict clears to `⊥` with the transient `_dataset_cleared_notice` (canopy#652). The two
> no-change outcomes still show the availability-unknown caveat when juniper-data could not be read.

### 4.8 Start requires a dataset (X5 / N9)

> **Status (2026-09-23): SHIPPED** — canopy#593 (`aa611561`, 2026-09-06), in the same PR as §4.1:
> `_update_button_appearance_handler` takes `dataset_value` and disables Start when either axis is
> unset. canopy#601 (2026-09-09) added `model_state`, so Start is also disabled for a selection the
> live backend does not serve.

`_update_button_appearance_handler` (`:7187`, gate at `:7206`) must take the dataset value and
disable Start at `⊥`. This is a **callback-signature change** and is a prerequisite of §4.1, not an
enhancement — without it `(cascor, ⊥)` trains silently on a stale dataset (§2).

### 4.9 Staging the pair (X6)

> **Status (2026-09-23): SHIPPED, inside canopy** — canopy#599 (the 501 guard), canopy#601 (the
> Start refusal) and canopy#607 (`95284f37`, 2026-09-09: in-process `RecurrenceBackend.stage_dataset`
> and the staging refusal), as the 2026-09-08 correction below anticipated (note after it).

Apply Dataset fails on both branches today: default deployment reaches cascor, whose `Literal`
(`juniper-cascor/src/api/models/training.py:235`) has no `equities_seq` → **502**; a configured
deployment reaches `RecurrenceBackend`, which has no `stage_dataset`, called unguarded at
`main.py:3995` → **500**. One-shot Start bypasses staging and is unaffected. Minimum: guard the
call site and surface a real message; full fix is a `stage_dataset` implementation.

**Correction (2026-09-08).** Both branches above were attributed to other repos, and both
attributions were wrong. The cascor 502 is cascor refusing a rank-3 artifact **by design** (the W-2
tier boundary, `api/lifecycle/manager.py:3815`); the defect was canopy staging into a backend the
selection does not target — the inactive state N5 names — and the fix is to refuse that state
(canopy#601 for Start; the follow-on staging PR for `POST /api/stage_dataset` and Apply Dataset).
The recurrence 500 needed no service endpoint: the service is one-shot, so `RecurrenceBackend`
stages **in-process**, as `DemoMode` does, and the next fit consumes the staged config, which
takes precedence over the one-shot body. The "full fix" this section asked for is therefore
canopy-only. See the consensus validation's §7 item 2 correction and
`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`.

> **Shipped, 2026-09-23 reconciliation.** The correction's unnamed "follow-on staging PR" is
> canopy#607 (`95284f37`, 2026-09-09). It gave `RecurrenceBackend` an in-process `stage_dataset`
> and made `api_stage_dataset` answer 409 for a selection the live backend does not serve. The
> route's 501 for a backend without `stage_dataset` came earlier, in canopy#599
> (`TestX6StagingIsGuarded`). Since then, canopy#669 (`9262a866`, 2026-09-23) added FR9's `nn_model`
> mirror: `api_stage_dataset`, `api_live_dataset_swap` and `api_set_params` answer 409 for a stale
> tab and 422 for an unknown model, and the two dataset routes also 422 an incompatible dataset
> (`_request_model_refusal`). The sidebar's two Apply paths send it, and since canopy#674
> (`894a2cc7`, 2026-09-23) so do the live swap and the restart modal's re-stage and parameter apply.
> canopy#674 also fixed the live swap's body, which had sent the spiral fields for every generator
> and never a seeded generator's params: the swap and Apply Dataset now build one body, in
> `_dataset_stage_payload`.

### 4.10 Dataset-axis hydration — the prerequisite for `⊥` at mount (N10 / OQ-N2)

> **Status (2026-09-23): SHIPPED** — canopy#662 (`2f973ca2`) with juniper-cascor#676 (`e052ef80`),
> then `⊥` at mount in canopy#667 (`2c56e8a3`), all 2026-09-23 and in the order N10 requires.
> Departures: a sibling route rather than a `/api/train/status` field, and an `unknown` read mounts
> on `DEFAULT_DATASET_TYPE` rather than `⊥` (the two blocks at the end of this section).

**Measured**: canopy has *never* hydrated the dataset from the backend. There is no
dataset-hydration callback, and `GET /api/train/status` carries no dataset field —
`nn_dataset_type` (`main.py:3971`) is a *request* model. The mount value is purely the layout
default.

Today that divergence is masked, because `spirals` is also the backend's default: the UI is right
by coincidence. Setting mount to `⊥` does not remove the divergence, it **changes its failure
mode** — after any mid-session reload the UI shows no dataset and, by N9 (X4 + X5), *both* Start
and Apply Dataset are disabled, over a backend that is staged and ready. Recovering requires
re-selecting and re-applying, which re-stages and can reset training state.

That is X1's class on the dataset axis, so it gets X1's remedy: extend the model-state hydration of
§4.4 to the dataset axis (`GET /api/train/status`, or a sibling route, must report the staged
dataset; canopy seeds the dropdown from it at mount). With hydration in place, `⊥` appears **only
when the backend genuinely has nothing staged** — which is the honest reading of OQ-N2, strictly
better than today, and free of the reload regression.

**Ordering is not negotiable**: hydration lands *before* `⊥` becomes the mount state (§7).

**SHIPPED 2026-09-23: juniper-canopy#662 (design PR 2) and juniper-cascor#676.** What was
built, where it departs from the sketch above, and why:

- **A sibling route, not a `/api/train/status` field.** `GET /api/selection` returns both axes. The
  model half has exactly `POST /api/model/select`'s response shape, so `model-state-store` can hold
  either one and its existing readers need no change. That model half is **Y3**, the read side the
  model axis never had. The dataset half is new.
- **"The staged dataset" needed a producer-side change.** cascor tracked `_current_dataset_config`,
  but exposed it only as a live swap's `before_cfg`. cascor#676 adds an additive `current_dataset`
  field to `/v1/training/status` with three readings: `null` (nothing loaded),
  `{"dataset_type": null}` (loaded but unnamed), and the config it was loaded from. The recurrence
  backend records the dataset of its latest fit. The demo simulator reads its dataset's `source`
  stamp.
- **`source` is the field to branch on**, not `value`. A pending dataset wins, because Start
  consumes it. After that come `loaded`, `none` (the backend holds nothing) and `unknown` (it
  cannot say: a cascor without #676, or an unreadable status). The last two both carry a `null`
  value and must be kept apart. This is the whole difference between `⊥`-at-mount being honest and
  it re-creating the reload regression above.
- **The gate's own mount trigger was removed.** It scheduled a second first-paint pass against the
  *seed* model beside the hydrated pass. The first-paint pass now comes from the hydration's store
  write, which happens on every mount, including after a failed read.
- **G7** is asserted through the registered callbacks and end to end through the real route and
  backends. A **Y3** guardrail was added beside it, because §5's table had no row that a Y3 defect
  could fail.

**`⊥` at mount followed the same day: canopy#667 (`2c56e8a3`, 2026-09-23), OQ-N2.** The sidebar
dataset dropdown and the restart modal's both mount at `value=None`. The mount hydration then lands
on the backend's dataset for `pending` / `loaded`, stays at `⊥` for `none`, and falls back to
`DEFAULT_DATASET_TYPE` for `unknown` (`_hydrated_dataset_value`). That fallback is the one place a
seeded default survives, deliberately: `⊥` there would disable Start and Apply after every reload
over a backend that may be staged and ready, which is the regression N10 forbids. A backend holding
a dataset canopy does not offer mounts at `⊥` with an informational notice
(`_unnameable_dataset_notice`). Demo mode still lands on spirals because the simulator reports them,
not because of a seed.

### 4.11 Clearing the model must ungate the dataset (N11 / OQ-N6)

> **Status (2026-09-23): SHIPPED** — canopy#594 (`7bc53cca`, 2026-09-06): "Clear model — show all
> datasets" (`model-selection-clear`) writes `None` without posting, and the early return is gone.
> Measured since: the model clear and the ✕ are independent cut vertices, each of which opens the
> graph alone (§5 note 1, §8).

OQ-N6 ships §5.5's second affordance, the "clear model / show all" reset. The registry is already
correct — `gated_dataset_options(None)` returns all six datasets enabled (executed). The handler is
not:

```text
_gate_dataset_options_handler:
    if not model_key:
        return dash.no_update, dash.no_update     # <- options stay frozen at the OLD model's gate
```

So clearing the model to escape a constraint would leave that constraint in force: the dataset
dropdown keeps the previous model's disabled set. **That is the mutual-gate trap again, on the
model axis** — a defect this design exists to prevent, shipped by the affordance meant to relieve
it. The early return must instead render ungated options composed with `apply_availability_gate`.

> **Superseded 2026-09-06 (canopy#594).** The quoted early return is the 2026-09-02 code. It was
> removed: a falsy model key now flows through `gated_dataset_options`, which enables every dataset,
> composed with `apply_availability_gate` as asked (`TestG8ClearedModelUngatesTheDataset`).

Consequence worth recording: with **both** axes clearable, OQ-6 becomes fully answerable for the
first time. §5.6's *dataset-primary* policy ("keep dataset, clear model") is finally expressible,
where under `clearable=False` neither policy was.

### 4.12 Demo mode (N13 / OQ-N2)

> **Status (2026-09-23): SHIPPED, with a departure** — canopy#596 (`f8fb4a2c`, 2026-09-06). The signal
> is a red connection badge ("WS: Demo — LOCAL data, not juniper-data"), not a banner, and it covers
> all three fallback call sites (note below).

Demo mode keeps auto-loading the default spiral dataset — `⊥`-at-mount is for normal operation
only. Its dogfooding is largely already true: `demo_mode.py:551-554` calls juniper-data first
(`_generate_spiral_dataset`) and only falls back to `_generate_spiral_dataset_local` on exception.

The demo-only code to minimise is that fallback. It should **not** simply be deleted: its own
comment names its purpose ("Docker standalone, CI smoke test"), and removing it makes demo mode
hard-depend on juniper-data being reachable. Instead it must **degrade loudly** — a visible
degraded-mode banner whenever the local generator is used — so demo mode never *quietly* runs on
non-platform data. That satisfies the stated intent (no silent divergence from the platform) without
breaking standalone or CI.

> **Correction, 2026-09-23.** "The fallback" was three call sites when written, not one:
> `DemoMode.__init__`, `DemoMode.regenerate_dataset` and `DemoMode.apply_params` each catch a
> juniper-data failure and call `_generate_spiral_dataset_local` (all three are present in canopy as
> of 2026-09-02). Each also logged a warning, so the old behaviour was silent in the UI, not in the
> log. canopy#596 sets `local_dataset_fallback` inside `_generate_spiral_dataset_local`, so every
> site raises it; `main._demo_dataset_source` publishes it on `/api/stream_health`, and the
> connection badge turns red instead of the grey "WS: Demo".

---

## 5. Test plan

Specified to **fail on today's code**, which the guardrail everyone first proposed did not
(evaluation §5.2). Identifiers match the evaluation's §8.

| id      | test                                                                                                     | status before                              | status after                                                                |
|---------|----------------------------------------------------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| **G1a** | BFS the composed transition relation; assert `Reach ⊇ compatible ∩ available`                            | fails (5 of 6)                             | passes — **shipped** in canopy#593 (`TestG1Reachability`); stays green if one clear alone is reverted (note 1) |
| **G1b** | same BFS; assert `Reach ⊆ compatible ∪ {(m, ⊥)}`                                                         | passes                                     | passes — **fails under F2** — **shipped** in canopy#593; never reaches the gate's conflict branch (note 2) |
| **G1c** | G1a/G1b over a synthetic **≥3-component** registry                                                       | fails (2 unreachable)                      | passes — **shipped** in canopy#598 (`TestG1cThreeComponents`) |
| **G1d** | G1a/G1b with an **injected all-unavailable** generator list                                              | fails (parks)                              | passes **vacuously for `⊥`** — asserts the recovery state, not reachability — **shipped** in canopy#595 (`TestG1dNothingAvailable`) |
| **G2**  | no committed pair with `compatible()` False is reachable                                                 | passes                                     | passes — **shipped** as G1b's property; the tests named `test_g2_*` pin something else (note 3) |
| **G3**  | empty compatible∩available renders recovery, not `no_update`                                             | fails                                      | passes — **shipped** in canopy#595 (`TestG3EmptySetRecovery`) |
| **G4**  | canopy `DATASET_TYPES` maps onto juniper-data `GENERATOR_REGISTRY` **through `generator_name_for_type`** | **fails** (`spirals`/`moons` are not keys) — *wrong: as worded it passed (note 5)* | passes — **shipped, re-specified** in canopy#599 (`TestG4GeneratorNameResolution`) |
| **G5**  | model summary reflects `swapped is False`                                                                | fails                                      | passes — **shipped** in canopy#592 as provider agreement, not `swapped` (note 6) |
| **G6**  | Start disabled at `⊥`                                                                                    | fails                                      | passes — **shipped** in canopy#593 (`TestG6StartRequiresACompleteSelection`) |
| **G7**  | the mount dataset value equals the backend's staged dataset (§4.10)                                      | **fails** — no hydration exists at all     | passes — **shipped** in canopy#662 (`TestG7MountDatasetIsTheBackendsDataset`, `TestG7AcrossTheRealSeams`) |
| **G8**  | a **cleared model** renders ungated dataset options, not `no_update` (§4.11)                             | **fails** — options freeze at the old gate | passes — **shipped** in canopy#594 (`TestG8ClearedModelUngatesTheDataset`) |
| **G9**  | demo mode's local-generator fallback is visibly announced (§4.12)                                        | **fails** — degrades silently — *in the UI only; it logged a warning (note 7)* | passes — **shipped** in canopy#596 (`test_demo_mode_local_fallback.py`) |
| **G10** | every juniper-data generator is either seeded in `DATASET_TYPES` or on a named exclusion list (§12)       | **fails** — 10 unseeded, none excluded     | passes — **shipped** in canopy#612 (`TestG10EveryUpstreamGeneratorIsSeededOrNamed`), against a dated snapshot (note 8) |
| **G11** | every seeded generator has bounded `default_params` (§12)                                                | fails for any new seed without them        | passes — *vacuously until canopy#665*; **shipped, re-specified** in canopy#665 (`TestG11EverySeedIsBounded`) (note 9) |
| **Y3**  | a reload shows the model the server recorded, and gates Start on it (§4.10's model half) — added 2026-09-23; this table had no row a Y3 defect could fail | **fails** — the model axis had no read side | passes — **shipped** in canopy#662 (`TestY3TheModelAxisHasAReadSide`) |

> **Shipped status, 2026-09-23.** Every row has shipped; the classes named are in canopy's
> `src/tests/regression/`. The caveats below were checked against canopy source, and the two
> measurements are marked as such.
>
> 1. **G1a stays green if either clear alone is reverted.** The dataset ✕ and the model clear
>    (§4.11) are independent cut vertices, and each opens the graph by itself. Reverting
>    `clearable=True` fails only `test_g2_either_clear_alone_opens_the_graph[withheld1]` (measured
>    2026-09-23 with `util/ad-hoc/2026-09-23_mutation_check_m1_m6.py`). A removed model clear is caught
>    by `TestG8ClearedModelUngatesTheDataset.test_the_clear_control_exists_in_the_layout`. The G1a
>    helper's docstring (`_dataset_dropdown_is_clearable`) said the opposite until canopy#675
>    (`0254a7ec`, 2026-09-23) corrected it.
> 2. **G1b cannot see a gate that keeps an incompatible dataset.** Its search selects only models the
>    table enables, which are compatible with the current dataset, so it never takes the gate's
>    conflict branch. `TestDatasetRepairNotice` pins that branch directly, and G7's
>    `test_the_hydrated_dataset_is_gated_against_the_HYDRATED_model` pins it at mount.
> 3. **G2 shipped as a property, and its name was reused.** "No invalid committed pair is reachable"
>    is what G1b (and the G1c / G1d invalid-state tests) assert. The tests *named* `test_g2_*`
>    (canopy#593, rewritten in canopy#594) pin something else: the deadlock returns only when both
>    clears are withheld.
> 4. **G1's start state.** `_explore` still starts at the `unknown` fallback pair `(cascor, spirals)`,
>    not at the `⊥` mount of canopy#667. A 2026-09-23 probe
>    (`util/ad-hoc/2026-09-23_explore_start_probe_test.py`) measured every mount state (`⊥`, the
>    fallback pair, a hydrated pair) reaching the same 31 states, so G1a and G1b do not depend on it.
> 5. **G4's "status before" was wrong when written**, and canopy#599 re-specified the test. Through
>    `generator_name_for_type`, `spirals` and `moons` already resolved to registry keys, so G4 as
>    worded passed on the unfixed code (canopy's test module records this as refutation R3). It now
>    asserts that the resolution is total and the alias map has no dead entries. It does not compare
>    against juniper-data's registry; G10's `test_every_seeded_value_resolves_to_a_known_generator`
>    does, against a snapshot.
> 6. **G5** shipped as provider agreement (`selection_is_live`) rather than `swapped is False`;
>    `test_noop_reselect_of_the_live_model_still_reads_active` pins the case the literal wording gets
>    wrong (§4.4).
> 7. **G9's "degrades silently"** was true of the UI only: each of the three fallback sites logged a
>    warning (§4.12).
> 8. **G10** checks `KNOWN_UPSTREAM_GENERATORS`, a snapshot of juniper-data's registry taken
>    2026-09-09 and re-checked 2026-09-22. An upstream generator added later is caught at runtime by
>    `/api/dataset/generators`, not in CI.
> 9. **G11's "passes" was vacuous until canopy#665** (2026-09-23): no test iterated every seed, and
>    canopy#610's `TestEquitiesSeedIsGenerableAndFinite` covered the equities pair only.
>    `TestG11EverySeedIsBounded` iterates `DATASET_TYPES` and requires each seed's generator to be
>    classified in `SEEDED_GENERATOR_BOUNDS` (14 entries), binding `symbols` only for the two universe
>    importers. That is §12.6's restatement of G11; canopy's comment above `SEEDED_GENERATOR_BOUNDS`
>    records why the literal wording in this row overshoots.

Two specification notes that cost round 1 a defect each:

- **G1b needs `⊥` admitted explicitly.** `⊥` is not in `compatible()`, so a bare
  `Reach ⊆ compatible` fails on this design's own change. The `∪ {(m, ⊥)}` term is the whole
  difference between "incomplete" and "invalid" and must be in the assertion, not only the prose.
- **G1d cannot assert reachability.** With nothing available there is nothing to reach; it asserts
  the §4.7 recovery state instead. An earlier draft filed it under "must pass after", which is
  unsatisfiable.

**Enabling change**: **five** resolvers in `model_registry.py` lack an injectable parameter —
`gated_dataset_options` (`:408`), `get_model_spec` (`:264`), `get_dataset_spec` (`:276`),
`dataset_type_options` (`:200`) and `dataset_default_params` (`:209`) — while `compatible_models`,
`compatible_datasets` and `model_options` have one. G1c/G1d cannot be written without adding it,
and `dataset_default_params` is on G1's path via `:2682`. `_gate_dataset_options_handler` also
needs its generator list injectable, since it calls live HTTP and fails open under test.

> **Done, 2026-09-06/07.** True when written. All five resolvers take injectable registries
> (`models=` / `dataset_types=`) since canopy#598, and `_gate_dataset_options_handler` has taken
> `generators=` since canopy#594 and `models=` / `dataset_types=` since canopy#598.

**G1 must live at handler level.** Written over `model_registry` alone it goes green on the
deadlocked code — measured.

---

## 6. Sizing

B3's independent estimate, which corrected the proposal round's "~20 lines": **50–80 src +
150–250 test** for the narrow fix; **75–125 + 230–370** for the full arc. Single-source and not
re-derived (evaluation §9).

That estimate predates the §10 answers and the §11 scope revision, and it costed **three** PRs. It
does not include: §4.8's callback-signature change, §4.9 staging, §4.10 hydration (a new route or
route field plus a mount callback), §4.11, the §4.3 toast surface (new to canopy), §4.12, or any of
§12. The arc is now **five PRs plus a parallel packaging workstream** (§7), and the estimate should
be treated as a floor for PRs 3–4 only, not as a total. It is deliberately not re-estimated here —
inventing a precise number for work this under-specified would be false authority of the kind
round 2 was commissioned to catch.

Existing test sites to touch before a new test is written: 4 forced assertion inversions, 3
rendered vacuous, 1 premise destroyed, 4 callback-arity breaks — **12 sites across 2 files**.

**Coverage gate.** Measured twice, exit 0 both times; total 96.06%. The per-file 90% floor is
**not** binding (`dashboard_manager.py` is 95.46% branch-inclusive, the gate's own basis). The
binding constraint is the **`src/frontend` pooled 95% bar at 96.34% — 27 uncovered statements of
slack**. Note `src/backend/state_sync.py` sits at 87.38% below the file floor already; it is
untouched here but means the lane is not clean.

---

## 7. Phasing

Revised 2026-09-02 for the §10 answers and the §11 scope revision. Five PRs plus one parallel
workstream. The ordering principle is that **truth-telling precedes reach, and reach precedes
breadth** — a UI that misreports which model produced a result is a worse platform than one with
fewer datasets, because its output is wrong rather than absent.

| PR    | contents                                                                                            | rationale                                                                                                                                |
|-------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **1** | §4.4 (X1 model-state truth) + **G5** — **SHIPPED** canopy#592 (2026-09-06) | Correctness of reporting leads. Independently correct; shippable alone.                                                                  |
| **2** | §4.10 hydration, **both** axes (X1's dataset-side sibling, Y3) + **G7** — **SHIPPED** canopy#662 + cascor#676 (2026-09-23), with a Y3 guardrail; `⊥` at mount followed in canopy#667 | Prerequisite for `⊥`-at-mount. Landing it separately keeps the reload regression from ever existing (N10).                                |
| **3** | §4.1 ✕ + §4.11 model clear + §4.2 / §4.8 guards + §4.3 naming and channels + §4.7 empty-set + **G1a–G1d, G3, G6, G8** — **SHIPPED** canopy#593, canopy#594, canopy#595, canopy#598 (2026-09-06/07); §4.3's Y7 item in canopy#671 (2026-09-23) | The reachability fix proper, now with both axes clearable. **Land G1a red first**, then green it. §4.8 and §4.11 are prerequisites, not follow-ups. |
| **4** | §4.5 restart modal + §4.6 alias + §4.9 staging + **G2, G4** — **SHIPPED** canopy#593 (§4.5), canopy#599, canopy#601, canopy#607 (2026-09-06 to 09-09); §4.5 untested until canopy#675 (2026-09-23) | Activated by PR 3; smaller and independently reviewable.                                                                                 |
| **5** | §12 generator expansion — Y5 first, then the seeds + `default_params` + the `mackey_glass` seed flag + **G10, G11** — **SHIPPED** canopy#609 through canopy#665 (2026-09-10 to 09-23); the seed flag proved unnecessary | Iteration 2 (§11). Depends on PRs 1–2 for honest attribution and on Y5 for a usable params panel.                                          |
| **∥** | juniper-data packaging: the `equities` extra into `requirements.lock`, and any other extra a newly-seeded generator needs — **MERGED, NOT RELEASED**: juniper-data#421 (2026-09-23); no juniper-data release contains it | Parallel and non-blocking. Without it several datasets are correctly `available=false` in the container (§9).                              |

§4.12 (demo mode, **G9**) rides with PR 3, since `⊥`-at-mount is what makes demo mode's behaviour
a distinguishable case.

If PR 4 cannot land with PR 3, the restart modal must be **quarantined** (its dataset field
disabled) in PR 3 rather than left inverted.

> **Shipped record, 2026-09-23.** All juniper-canopy unless prefixed; merge dates UTC, from `gh`.
>
> - **PR 1**: canopy#592 (`b5ad897b`, 2026-09-06). canopy#601 (`5d7dd6aa`, 2026-09-09) completed N5:
>   the Start gate reads the same provider-agreement predicate as the label, and the server refuses
>   an inactive selection.
> - **PR 2**: canopy#662 (`2f973ca2`) with juniper-cascor#676 (`e052ef80`), both 2026-09-23. OQ-N2's
>   `⊥` at mount followed in canopy#667 (`2c56e8a3`, 2026-09-23), after the hydration, as N10
>   requires (§4.10).
> - **PR 3**: canopy#593 (`aa611561`: §4.1, §4.2, §4.8, G1a / G1b, G6, and PR 4's §4.5),
>   canopy#594 (`7bc53cca`: §4.11, Y9, G8), canopy#595 (`0096f567`: §4.3's notices, §4.7, G1d, G3)
>   and canopy#598 (`f56f46c2`: G1c), 2026-09-06/07, with §4.12 and G9 in canopy#596 (`f8fb4a2c`).
>   The one item left was §4.3's Y7 bullet, which canopy#671 (`7cd8a9d4`, 2026-09-23) shipped for the
>   model table as specified. Y7's dropdown half stays open outside this design's specification
>   (§4.3). OQ-N5's browser acceptance step ran twice (§10).
> - **PR 4**: §4.5 landed early, in canopy#593 with the ✕, so the quarantine above was never needed.
>   §4.6 and G4 in canopy#599 (`de253e93`, 2026-09-07); §4.9 in canopy#599, canopy#601 and
>   canopy#607 (`95284f37`, 2026-09-09). §4.5 had no test until canopy#675 (`0254a7ec`, 2026-09-23).
> - **PR 5**: Y5 in canopy#609 (`39998791`); the `equities_seq` seed repair in canopy#610 (`94ff71c9`);
>   the five rank-3 seeds and G10 in canopy#612 (`8cfb29ac`); `gaussian` and `checkerboard` in
>   canopy#616 (`b7883d5d`); `equities` in canopy#621 (`b01f33f7`) and canopy#622 (`1597c679`); G11
>   in canopy#665 (`7950bf9e`, 2026-09-23); the §12.9 follow-ons in canopy#625 (`f7bbc4ee`),
>   canopy#632 (`812f26c0`) and canopy#644 (`ba3b16ff`). The `mackey_glass` seed flag was never built
>   and is not needed: `seed` is in `INFRASTRUCTURE_FIELDS`, so the form neither renders nor forwards
>   it (§12.6, item 3).
> - **∥**: juniper-data#421 (`68c3cd7c`) merged 2026-09-23T00:56Z, and `requirements.lock` on
>   juniper-data `main` pins `yfinance==1.7.0`. Probed 2026-09-23: no juniper-data tag contains that
>   commit, and v0.15.0 (released 2026-09-22T18:55Z, the latest on GitHub and on PyPI) does not; its
>   lock has no `yfinance`. The container gains `equities` and `equities_seq` only once a release
>   carries it and the deployment picks that release up.

---

## 8. Rollback

Each PR is independently revertible. PR 2's functional change is one keyword plus guards; a revert
restores the deadlock without leaving an inconsistent state. The invariant tests are the thing not
to revert — if a rollback is needed, mark G1 `xfail` with a reason rather than deleting it, so the
gap stays visible.

> **Correction, 2026-09-23.** This paragraph was written for the original three-PR plan, in which PR 2
> was the reachability fix, and it went stale the same day. §7's 2026-09-02 revision renumbered the
> PRs (PR 2 is now hydration, canopy#662) and put the model clear (§4.11) in the same PR as the ✕.
> With both clears shipped, reverting the ✕'s keyword alone does **not** restore the deadlock: the
> model clear opens the graph by itself. Reverting `clearable=True` fails only
> `test_g2_either_clear_alone_opens_the_graph[withheld1]`, and G1a stays green (measured 2026-09-23,
> §5 note 1). Only withholding both clears restores it, which is what
> `test_g2_the_deadlock_returns_only_when_BOTH_clears_are_withheld` pins. The advice not to delete
> the invariant tests stands.

---

## 9. What this does not fix

- **The container has no equities generator at all** (evaluation §6.3): `yfinance` is absent from
  `juniper-data/requirements.lock`. In the deployed stack the LMU has zero *available* datasets
  regardless of this work. §4.7 makes that state legible rather than a silent park; it does not
  make the dataset available. Fixing it is a juniper-data packaging change.
  - **Superseded in two steps (2026-09-23 note).** True when written. canopy#612 (2026-09-10)
    seeded five numpy-only rank-3 synthetics, so the LMU has five available datasets in the
    container whatever the lockfile holds (§12.5). juniper-data#421 (`68c3cd7c`, merged 2026-09-23)
    put `yfinance` into `requirements.lock` on juniper-data `main`, but no juniper-data release
    contains it yet (§7, ∥), so an image built from the latest release (v0.15.0) still lacks it.
- ~~**Ten unseeded generators**~~ — **moved into scope** as iteration 2 by the §11 revision;
  specified in §12. The caveat stands and is carried there: whether the LMU can actually train on
  the five rank-3 generators end-to-end is **unvalidated**, and the evaluation grades the
  "5× larger" framing OVERSTATED. §12 therefore treats validation as part of the work, not an
  assumption.
- **Y1–Y9** (evaluation §6.4), including further missing `RecurrenceBackend` methods — a count the
  round could not agree on (0 / 9 / 11 depending on baseline) and which is recorded as a lead, not
  a fact — and the vacuous snapshot save/restore.
  - **Superseded in part (2026-09-23 note).** Fixed on canopy `main` since: Y1 (canopy#633 for the
    experimental-functions pair; canopy#643 for the four dataset-swap methods `RecurrenceBackend`
    lacked, plus `test_backend_protocol_conformance.py`, which requires every attribute `main.py`
    reads off `backend` to be declared or explicitly conditional), Y3 (canopy#662), Y4 and Y8
    (canopy#671), Y5 (canopy#609) and Y9 (canopy#594). Y7 in part: the `role="status"` notice region (canopy#595)
    and the model table's `aria-describedby` (canopy#671); the dropdown's missing `aria-disabled`
    remains (§4.3). No fix was found in canopy source or its CHANGELOG for Y2, the vacuous snapshot
    save/restore under recurrence, or for Y6 by name. The nearest Y6 coverage is G10, which checks
    canopy's registry against a dated snapshot of juniper-data's (`KNOWN_UPSTREAM_GENERATORS`), not
    the live one.

---

## 10. Open questions

- **OQ-N1** — *(closed by round 2; retained for the record)* whether the newly-reachable path
  invokes `RecurrenceBackend.stage_dataset`. **It does not** — the failure fires on **Apply
  Dataset**; one-shot Start bypasses staging. Round 1 recorded this as unresolved dissent, which
  was itself an error: two reviewers were describing different controls. Carried as work item §4.9.
  - Response: already resolved.

- **OQ-N2** — should `⊥` be the *mount* state rather than a transit state? It would make the first
  interaction an explicit choice and remove the seeded-default asymmetry, at the cost of an extra
  click for the common case and an FR15 interaction.
  - Response: it should be the mount state for normal canopy operations.
  demo mode should continue to auto-load the default spiral dataset.
  this apporoach honors the fundamental design philosophy of the juniper project: power and flexibility over simplicity for the research platform--as normally utilzed--and a simpler, works-out-of-the-box user experience for demo mode.
  Specifically, the demo mode design should enable processing of an actual, live dataset, defaulting to dog-fooding the platform code and infrastruture, and minimizing custom, demo-only code or local versions of functions that exist elsewhere in the platform.
  - **Disposition: ACCEPTED, with a prerequisite (N10).** `⊥` at mount is adopted for normal
    operation, and demo mode keeps auto-loading spirals. But canopy has never hydrated the dataset
    from the backend (measured, §4.10), so `⊥`-at-mount alone would disable Start *and* Apply after
    every reload over a staged, ready backend. §4.10 lands dataset-axis hydration **first** (PR 2),
    after which `⊥` appears only when the backend truly holds nothing — the honest reading of this
    answer, with no reload regression.
  - On demo mode: the dogfooding is largely already true (`demo_mode.py:551-554` calls juniper-data
    first). The demo-only code to minimise is the local fallback — which §4.12 makes **loud** rather
    than deleting, since its own comment names Docker-standalone and CI smoke tests as its purpose.
    That keeps the intent (never silently run on non-platform data) without breaking those lanes.
  - **Shipped 2026-09-23 (note)**, in the order this disposition requires: hydration in canopy#662
    (with juniper-cascor#676), then `⊥` at mount in canopy#667 (§4.10). The local fallback, three
    call sites rather than the one cited above, is announced by a red connection badge (canopy#596,
    §4.12).

- **OQ-N3** — *(narrowed)* §4.8 settles that Start must be gated at `⊥`. Remaining: should Apply
  Dataset be disabled at `⊥` (§4.2 assumes yes), or should `⊥` be non-committable by construction?
  - Response: yes, apply dataset should be disabled when no dataset has been selected or dataset selection has been cleared.
  - **Disposition: ACCEPTED as written.** No prerequisite; consistent with N9 and already specified
    at §4.2. Closed.

- **OQ-N4** — is the §5.6 notice a toast, an inline alert, or a persistent annotation? N4 fixes the
  *locus*, not the form.
  - Response: let's go with a toast when the gate fails and a persistent error message until the situation is resolved.
  - **Disposition: ACCEPTED, split across two events (N12).** The answer describes two distinct
    events, and the split is what makes it coherent: a **toast** for the gate's *successful* repair
    (informational — nothing to resolve), a **persistent inline alert** for the empty
    compatible∩available set (blocking, and the only one "until resolved" applies to). Detail and
    the two practicalities — canopy has zero `Toast` components today, and a toast without
    `aria-live` is invisible to assistive technology — are at §4.3.

- **OQ-N5** — the browser falsifier is still open (evaluation §9): no agent clicked the greyed
  option in a live DOM, because canopy accepts TCP on 8050 but never responds. Cheapest remaining
  check.
  - Response: in the interest of being thorough, and avoiding the introduction of subtle gaps, let's perform the check.
  - **Disposition: ACCEPTED — and DONE (2026-09-02). Both gates hold.** Executed on an isolated trio
    (data 8103 / cascor 8204 / canopy 8053) with trusted CDP clicks, leaving the operator's stack
    and a concurrent session's stack untouched. Clicking the greyed `Equities (sequence)` option
    left the dropdown on `Spirals`; clicking the disabled `Recurrence (LMU)` Select left the model
    on CasCor. Record: `reports/2026-09-02_canopy-selection-deadlock/oqn5_browser_falsifier.md`.
  - Three by-products, all carried into the evaluation document
    (`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`): **X7** (canopy blocks
    entirely, health included, whenever cascor is unreachable — the environmental blocker turns out
    to be a canopy defect); a **correction** that the "canopy never responds" condition is transient
    rather than standing; and a measured refinement of **Y7** — the dataset option carries no
    `aria-disabled` at all, so its gate is invisible to assistive technology, while the model Select
    is a correctly-exposed native disabled button.
  - **Still not observed**: the `⊥`-dataset and `⊥`-model states, because they do not exist until
    §4.1 and §4.11 ship. Re-run this falsifier as an acceptance step for PR 3 — the traversal in
    §4.1 is so far established only by executing handlers, never in a DOM.
  - **Observed since (2026-09-23 note).** The `⊥`-dataset state and the §4.1 traversal to
    `(recurrence, equities_seq)` were observed in a live browser at canopy `aa61156` on 2026-09-05
    (`reports/2026-09-05_canopy-deadlock-consensus/browser_acceptance.md`), and the `⊥`-model state
    at `f8fb4a2` on 2026-09-07 (`browser_acceptance_prb.md`, same directory). The second run also
    found that the D5 notice of the time could not be triggered from the model table; canopy#652
    later replaced that notice (§4.3).
  - **Method constraints for the PR-3 re-run** (carried forward from this run): the operator's
    canopy on 8050 must **not** be restarted or killed; bring up an isolated instance on spare
    ports, overriding `JUNIPER_E2E_RUN_DIR` as well as the ports so a concurrent session's pid
    files are not clobbered. Set `JUNIPER_E2E_PROJECT_DIR` explicitly — run from a worktree,
    `util/isolated_stack.bash` derives the ecosystem root from its own location and resolves to a
    path that does not exist. The instance needs a run-dir `*.pid` entry or a cmdline referencing a
    run root, or the orphan reaper will collect it (it treats reparenting to `systemd --user` as
    its orphan predicate, and the stack scripts launch under `nohup`).
  - **Driver note for whoever runs it**: canopy never reaches DOM stability (its polling keeps a
    callback in flight, so `document.title` sits at `"Updating..."`). Both chrome-devtools `click`
    and Playwright's default `locator.click()` time out on the stability wait, and untrusted
    synthetic events are ignored outright because the widgets are **Radix**. Use
    `locator.click({force: true})`; coordinate clicking is unreliable because the coordinates go
    stale as the page re-renders.

- **OQ-N6** — D4's **second** affordance, the "clear model / show all" reset on the model surface
  (§5.5 of the design of record), is NO ARTIFACT and out of scope here. Ship it, or descope it on
  the record — it should not remain silently unbuilt a second time, which is how this defect
  arose.
  - Response: we should ship the "clear model / show all" reset.
  - **Disposition: ACCEPTED, with a prerequisite (N11).** The registry already ungates correctly on
    a cleared model — `gated_dataset_options(None)` returns all six datasets enabled (executed).
    The *handler* does not: it early-returns `no_update`, so clearing the model would leave the
    dataset dropdown frozen at the previous model's gate — **the mutual-gate trap again, on the
    model axis**, shipped by the very affordance meant to relieve it. §4.11 changes that early
    return. Consequence worth having: with both axes clearable, OQ-6 becomes answerable for the
    first time, because §5.6's *dataset-primary* policy ("keep dataset, clear model") is finally
    expressible.
  - **Shipped 2026-09-06 (note)** in canopy#594 (§4.11). OQ-6 was then answered on 2026-09-22 (N7).

**Status**: all six answered and dispositioned. OQ-N1 and OQ-N3 are closed outright; OQ-N2, N4, N5
and N6 are accepted with the prerequisites recorded above and specified in §4. As of 2026-09-23 all
four have shipped, OQ-N4 with the departures recorded at §4.3 (the §4.x status lines and §7).

---

## 11. Notes

### Revaluation of scope-of-work, prioritization of fixes, and overarching goals for this development plan

the ten unseeded generators represent a substantial gap between the project requirements, along with their corresponding implementation of functionality, and the reality of the research platform as it currently exists.
the availability of all of the specified datasets is critical if the juniper research platform is to be actually useful.
while the missing generators might have been overshadowed by the work-flow deadlock initially, i would argue that they are, effectively, just as critical a defect in the juniper platform.
as such, i'd like to include the dataset defects in this work arc and design, even if added as a second iteration of work.
getting the platform to a usable state--without the current gaps in required functionality--is my primary goal for this development plan and this work arc.

---

## 12. Iteration 2 — closing the generator gap

Adopted from §11. This section makes that scope concrete and records what it depends on.

### 12.1 What is actually missing

`GENERATOR_REGISTRY` (`juniper-data/juniper_data/api/routes/generators.py:44`) registers **16**
generators; canopy's `DATASET_TYPES` seeds **6**. The ten unseeded ones split evenly by rank —
classified by executing the registry, not by reading prose:

| rank-2 classification (cascor-compatible) | rank-3 regression (LMU-compatible) |
|-------------------------------------------|-------------------------------------|
| `gaussian`, `checkerboard`, `equities`, `arc_agi`, `csv_import` | `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` |

Two of the rank-3 five (`irregular_sine`, `delay_product`) are explicitly non-uniform Δt, so they
satisfy the LMU through `requires_dt=True` rather than the regular-Δt path.

### 12.2 The reassuring part

**This expansion adds no deadlock surface.** Rank-2 generators join cascor's component and rank-3
join recurrence's, so the compatibility graph keeps exactly **two** connected components. The
Confinement Lemma's reach is unchanged, and G1c's ≥3-component case correctly remains synthetic.
Growth in dataset count is not, by itself, growth in trap risk.

### 12.3 Prerequisites — none of which are optional

1. **Y5 is a hard blocker.** The generators proxy sends no `X-API-Key` while `/v1/generators` is
   not auth-exempt, so canopy falls back to a schema-less 4-entry list. Seeding ten generators on
   top of that ships ten datasets whose params panel reads *"No adjustable parameters"*. Y5 lands
   first, inside PR 5.
2. **`default_params` is hand-maintained and load-bearing.** `equities_seq` needed
   `max_symbols=5` to keep the one-shot fit inside the 300 s train timeout. Every new seed needs a
   bounded default or the one-shot path times out — **G11** enforces it.
3. **`mackey_glass` accepts a `seed` and ignores it.** A known ecosystem finding: generator
   seeding has three states, and this one is *seed-accepted-but-inert*. Exposing it in a
   benchmarking UI without flagging that ships irreproducible runs. Fix upstream or label at the
   locus before seeding.
4. **`csv_import` is not a peer of the others.** It is an import path, and canopy already has
   `dataset_import.py`. It belongs on G10's named exclusion list, not in the dropdown.
5. **`arc_agi`'s shape is unverified.** Confirm its rank before seeding rather than assuming
   rank-2 from its `task_type`.

### 12.4 Validation is part of the work, not an assumption

The evaluation grades "five ready 3-D datasets" as a **count**, not a measured capability — B3
graded the "5× larger" framing OVERSTATED precisely because none of the five has been exercised
end-to-end. §12 therefore requires, per newly-seeded generator: generate → stage → train → render,
observed once. A generator that cannot complete that sequence is seeded **disabled with a reason**
(the existing availability-gate idiom), not seeded silently broken. That is the difference between
closing a capability gap and moving it somewhere less visible.

> **Observed, 2026-09-23 (A-N2).** The loop ran once per seed, through canopy's own HTTP routes (the
> ones the dashboard's buttons and callbacks use), on an isolated stack. That stack ran data, cascor
> and canopy from worktrees at `origin/main`, each leg's import proven, plus the recurrence service.
> Evidence: `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`, with one
> dashboard screenshot per run.
>
> - **Seven of the eight §12 seeds complete it through Start.** They are `gaussian`, `checkerboard`
>   and the five rank-3 seeds, and both controls (`spirals`, `equities_seq`) pass too. The LMU's R²
>   values match §12.6's direct fits.
> - **`equities` generates and stages, but Start refuses it (409)** whenever the live CasCor network
>   is narrower than its 15 features. The refusal reads "`dataset (15, 2) exceeds network capacity
>   (2, 2); resize the network first`". Start continues the current model, and cascor pads a
>   narrower dataset but refuses a wider one. The loop completes through the restart modal's
>   **Start fresh**.
>   - After the refusal, cascor has already switched its loaded dataset, and the routes serve the
>     previous run's results under an `equities` label.
>   - `mnist` (784 features) should hit the same refusal by the same code path. It was not run.
>
>   So the failing step is the Start path, not the generator. Whether that means disabling the seed
>   (this section's rule), fixing Start, or pointing the operator at Start fresh is an owner decision.
> - **Adjacent: Start fresh discards parameters applied just before it.** The restart modal applies
>   edited parameters (`set_params`) and then restarts. With Start fresh on, cascor rebuilds a
>   vanilla network at its own defaults, so the edits are silently lost. This was observed through
>   the two routes the modal calls, not by clicking the modal.
> - **Caveat on the LMU rows.** The recurrence leg was the installed `juniper-recurrence` console
>   script (0.5.0, an editable install of the primary checkout). It ran with
>   juniper-recurrence-model **0.1.5**, not the 0.3.x line `juniper-ml[recurrence]` installs.

### 12.5 Deployment reality

Several of these will legitimately be `available=false` in the container until the parallel
packaging workstream (§7) lands their extras — `equities` needs `yfinance`, which is absent from
`juniper-data/requirements.lock` today (§9). The availability gate already renders that honestly
with an install hint; §4.7 makes the fully-empty case legible. The UI work and the packaging work
proceed independently.

> **Correction, 2026-09-09** (session `resilient-strolling-bachman`). `yfinance` is still absent
> — verified, not assumed. But "several will legitimately be unavailable" understates what that
> meant while `equities_seq` was the LMU's **only** compatible dataset: in the container the LMU
> had **zero** available datasets, so §4.7's empty-set alert was not an edge case, it was the
> normal state of the deployed product. The five rank-3 synthetics seeded in **canopy#612** are
> numpy-only and declare no `is_available` hook, so they are available everywhere; that is the
> substantive fix, and the packaging workstream is no longer on the LMU's critical path.
>
> **Superseded on juniper-data `main`, 2026-09-23.** juniper-data#421 (`68c3cd7c`, merged 2026-09-23)
> put the `equities` extra into `requirements.lock` (`yfinance==1.7.0`). It is merged, not released:
> no juniper-data tag contains it, and v0.15.0, the latest release, has no `yfinance` in its lock
> (probed 2026-09-23). Until a release carries it, `equities` and `equities_seq` stay greyed, with
> the producer's install hint, in a container built from a release.

### 12.6 Execution record and corrections (2026-09-09)

Added by session `resilient-strolling-bachman`. Everything below was established by **executing**
juniper-data's registry and fitting `juniper_recurrence_model.LMURegressor`, not by reading
schemas — the probes are `util/ad-hoc/2026-09-09_generator_gap_census.py`,
`…_rank3_seed_validation.py`, `…_equities_seq_remedies.py`, `…_equities_seq_candidate_seeds.py`
and `…_dt_uniformity_and_equities_cap.py` in juniper-ml.

**Shipped:** Y5 as **canopy#609**, the `equities_seq` seed repair as **canopy#610**, the five
rank-3 synthetic seeds + G10 as **canopy#612**.

**§12.4's premise was truer than it looked, and it applied to the INCUMBENT.** The section warns
that a count is not a measured capability. It is: `equities_seq` — the seed already shipped, and
the entire subject of canopy#601 and canopy#607 — **could not generate at all**, and once that was
fixed, **could not fit**. Two independent defects, each fatal at a different stage:

1. `max_symbols` is a cap juniper-data **refuses** against, not a truncator. At
   `{"max_symbols": 5}` it compares against the requested 503-name universe and raises
   `InputTooLargeError` → 422. Every Start failed in 0.0s. The remedy is an explicit `symbols`
   list, which juniper-ml's own `tests/test_equities_symbol_cap_operator.py` already prescribes
   while warning off the `allow_truncation` escape.
2. `fundamentals_fill` defaults to `"nan"`, and `LMURegressor.fit` refuses non-finite input.
   `X_train` was **9.1% non-finite while `X_val` and `X_test` were entirely clean** — so any check
   sampling the held-out splits saw a healthy dataset. Columns were exactly
   `EQUITIES_FEATURE_COLUMNS[7]/[8]/[15]`. `incomplete_rows` does not touch it, and a later
   `start_date` is **not** a substitute: `2010-01-01` still yields 299,808 non-finite cells, so the
   schema's "pre-2009 missing" wording is incomplete.

**§12.3's prerequisites, resolved:**

| item | status |
|---|---|
| 1 — Y5 hard blocker | **Confirmed and shipped** (canopy#609). It was the one raw-`httpx` caller; every other canopy → juniper-data call already sent the key via juniper-data-client. |
| 2 — `default_params` load-bearing / G11 | **Restated.** As worded G11 fails the five incumbents *and* the five synthetics. The unbounded axis is an imported **universe**, not generator parameters — and narrower than "imports data" (`mnist` downloads a fixed corpus bounded by the sidebar's `n_samples`). It binds the equities pair; enforced by `TestEquitiesSeedIsGenerableAndFinite`. |
| 3 — `mackey_glass` seed inert | **Does not reach canopy.** `seed` is in `INFRASTRUCTURE_FIELDS`, so the schema-driven form neither renders nor forwards it, and juniper-data's synthetic base pins `seed: int = Field(default=0)`. Runs are reproducible. Latent, not absent: it would bite if `seed` were ever added to the form. |
| 4 — `csv_import` excluded | **Confirmed by execution** — calling it with defaults raises a `ValidationError` (`file_path` required). It is on G10's list. |
| 5 — `arc_agi` rank unverified | **Answered, and the answer is that it has no fixed rank.** Rank-2 at defaults (`(6, 900)`, 30×30 flattened), but `flatten_pairs` — a plain boolean the params panel **renders** — flips it to rank-3. `DatasetTypeSpec.ndim` is static and cannot express that; a rank-3 `arc_agi` is compatible with nothing (cascor is rank-2 only, recurrence is regression-only). **This is a new trap the design did not contain.** It stays unseeded until the registry can express a variable-rank generator. |

> **Superseded for items 2 and 5, 2026-09-23.** Item 2: G11 is now enforced over every seed by
> `TestG11EverySeedIsBounded` (canopy#665), which reads `SEEDED_GENERATOR_BOUNDS`: the restatement
> above, given a constant. `TestEquitiesSeedIsGenerableAndFinite` (canopy#610) still pins what the
> two equities seeds need in order to generate and fit. Item 5: the params panel no longer renders
> `flatten_pairs` (canopy#625), and `arc_agi`'s blocker proved to be its `y`, not its rank (§12.9.1,
> §12.9.2).

**§12.1's table is CORRECT** — and worth recording that the first census contradicted it and the
census was wrong. `dt[:, 0]` is a `0.0` no-previous-step sentinel; including it makes every
generator look non-uniform. Excluding it: `multi_sine` / `mackey_glass` / `ar_p` are regular
(a single Δt of 1.0), `irregular_sine` / `delay_product` genuinely irregular (36 distinct values).
A measurement that contradicts a considered design claim is a reason to re-examine the instrument
first — the probe was answering an adjacent question (what does the whole array look like?)
rather than the intended one (what is the per-step spacing?).

**§12.2 is now measured, not argued.** All five synthetics are rank-3 and cascor is
`input_ndim={2}`, so `compatible_datasets(cascor)` is unchanged and the graph keeps exactly two
components — asserted in `test_compatible_datasets_resolver_over_seeds`.

**What §12 did not say, and should have: order is load-bearing.**
`_gate_dataset_options_handler` snaps to the first compatible **and available** entry, so registry
order decides where an operator lands on selecting Recurrence. The synthetics are seeded *before*
`equities_seq` so that target is `multi_sine` (generate 0.00s, fit 0.10s, r² 1.000) rather than
`equities_seq` (40.5s, r² −0.004, unavailable in the container).

> **Superseded for the sidebar, 2026-09-23.** juniper-canopy#652 (OQ-6 ratified, §5.6.1 of
> `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`) deleted that snap: a
> conflict now CLEARS the dataset to `⊥`, and the operator picks from the gated list. On selecting
> Recurrence the sidebar lands on `⊥`, not on `enabled[0]`. **Registry order still decides two
> things:** the order the dropdown offers the options in, and the **restart modal's** fallback,
> which keeps its `enabled[0]` swap by owner ruling of 2026-09-22 (item 22 of the 09-22 handoff; a
> recorded exception to OQ-6, see §5.6.1 of the same document). So the seeding order above is still
> worth keeping, but for those two reasons, not for where the sidebar lands.

**Per-generator validation, as §12.4 requires** — generate then fit, observed once, at the
recurrence service's effective LMU defaults (`d=16`, data-driven `theta`, `ridge=0.0`):

| generator | X_train | Δt | generate | fit | r² |
|---|---|---|---|---|---|
| `multi_sine` | (1574, 32, 1) | regular | 0.00s | 0.10s | 1.000 |
| `mackey_glass` | (1574, 32, 1) | regular | 0.00s | 0.11s | 0.9999 |
| `irregular_sine` | (1574, 32, 1) | irregular | 0.00s | 0.11s | 0.9918 |
| `ar_p` | (1574, 32, 1) | regular | 0.01s | 0.10s | 0.043 |
| `delay_product` | (1574, 32, 1) | irregular | 0.00s | 0.10s | 0.004 |
| `equities_seq` (repaired) | (15476, 64, 16) | irregular | 0.90s | 39.6s | −0.004 |

Zero non-finite in any split for all six. The two low-r² synthetics are honest rather than broken
— a noisy AR process has a low ceiling, and `delay_product` has a multiplicative target against a
linear ridge readout — and are recorded inline in the registry so neither is mistaken for a good
default. **`equities_seq`'s r² ≈ 0 is likewise the honest outcome for next-day equity returns**,
which is the strongest argument for the synthetics: the pair now runs, but it demonstrates little,
whereas three of the five synthetics are signals the LMU visibly learns.

**Still unseeded after this phase** (G10 records the reason for each): `gaussian`, `checkerboard`,
`equities` — rank-2, deferred to a slice whose §12.4 validation runs against **cascor** rather
than the LMU, with `equities` additionally needing the canopy#610 treatment — plus `arc_agi`
(variable rank, above) and `csv_import` (excluded).

### 12.7 The rank-2 slice (2026-09-10) — and a correction to §12.6's own prescription

Added by session `resilient-strolling-bachman`. Shipped as **canopy#616**. Probes:
`util/ad-hoc/2026-09-10_rank2_generate_artifacts.py` and `…_rank2_cascor_fit.py` in juniper-ml.

Validation for a rank-2 seed runs against **cascor**, so it goes in two stages through the real
artifact contract — generate → NPZ → `CascadeCorrelationNetwork.fit` — rather than passing arrays
in memory: `juniper_data` and `juniper-cascor` live in different conda environments, and the split
exercises the six-key NPZ shape one emits and the other consumes instead of assuming the round-trip.

| dataset | X_train | units recruited | loss first → last | train top-1 | fit |
|---|---|---|---|---|---|
| `gaussian` | (100, 2) | 1 | 0.0231 → 0.0016 | **1.000** | 0.4s |
| `checkerboard` | (200, 2) | 1 | 0.2499 → 0.2498 | 0.515 | 3.0s |
| `checkerboard` @ `n_samples=2000` | (1400, 2) | **8** | 0.2496 → 0.2418 | 0.5425 | 2.2s |
| `equities` (3 params, below) | (15799, 16) | 3 | 0.2511 → 0.2491 | 0.524 | 1.2s |
| `equities` unnormalised | (15799, 16) | 8 | **5.83e+21** → 5.32e+21 | 0.509 | 2.3s |

**`gaussian` and `checkerboard` are seeded.** cascor needed no change: its
`StageDatasetRequest.dataset_type` `Literal` already admitted both and already carries a typed
`n_squares` knob for checkerboard (W-3). It was canopy that never offered them. Checkerboard's own
default — 200 samples over a 4×4 grid — is too thin for CasCor to recruit against (one unit, loss
flat to four decimals); at 2,000 it recruits eight and the loss moves. `n_samples` is a rendered
schema field, so that is an operator knob, not a code change.

**§12.6's prescription for `equities` was wrong, and measuring it is what showed why.** That entry
said to seed it "with the same treatment `equities_seq` received (canopy#610), not before". The
treatment transfers *and then some* — `equities` needs **three** params, not two:

1. an explicit `symbols` list (bare defaults are refused: 503 names over a deployment cap of 14);
2. `fundamentals_fill` away from its `"nan"` default;
3. **`normalize_features=True`** — new, and absent from the sequence sibling, because equities'
   columns are raw market quantities. Unnormalised the first output pass reports a loss of
   **5.8e+21** against **0.2511** normalised: twenty-two orders of magnitude.

**But the prescription cannot be carried out at all, for a structural reason neither §12 nor
canopy#612 had noticed.** `dataset_default_params` is a **recurrence-only** concept. Its only two
production consumers are `_resolve_oneshot_start_body_handler` (gated on
`model_class == "one_shot"`) and `dataset_ref_from_staged`. `_apply_dataset_handler` builds the
**cascor** staging payload from the rendered form alone — and `symbols` is an *array*, which
`_field_from_property` deliberately does not render. A seeded `equities` would therefore send bare
defaults and 422 on every Apply: the gap moved somewhere less visible, which is the outcome §12.4
exists to prevent.

So the registry's `default_params` channel, which §12 has been treating as the general mechanism
for seeding a generator's bounded parameters, **only reaches one of the two model tiers**. Closing
`equities` needs that decided first — either the cascor path learns to carry registry defaults, or
an array-valued param becomes settable — and it is recorded in G10 as such rather than as a
treatment with nowhere to travel.

**Still unseeded after the rank-2 slice**: `equities` (above), `arc_agi` (variable rank, §12.6) and
`csv_import` (excluded). **Seven of §12.1's ten are now seeded** — five rank-3, two rank-2 — and
nothing remains that is both validated and deliverable: each of the three that remain has a named,
measured blocker rather than a backlog entry.

### 12.8 `equities` unblocked, and §12 closes (2026-09-11)

Shipped as **canopy#621** (the unblock + the seed) and **canopy#622** (the availability message
that unblock made load-bearing). Together these close §12: **eight of §12.1's ten generators are
seeded**, and the two that are not each have a settled, recorded reason rather than a blocker.

**§12.7 named the blocker correctly and stopped one step short of the cause.** It recorded that
`dataset_default_params` was recurrence-only and that `symbols` is an unrenderable array. The
missing step was that this is not a property of `equities` at all — it is a property of the
**defaults channel**, which reached one of the two model tiers while its own docstring called the
registry "the single source of truth". Any future rank-2 seed needing any parameter would have hit
it. Fixing the channel was therefore both smaller and more general than working around it.

**Both halves were required, and that is the part worth carrying forward.**

1. `_apply_dataset_handler` seeds the cascor payload from the registry and lets the form override
   it — the same order the recurrence path already used. This is what lets an unrendered key travel.
2. `apply_seeded_defaults` seeds the **rendered controls** from the same place. Without it, a key
   that is both seeded and rendered is posted back at its *schema* default on the next Apply,
   silently undoing the seed — and the operator is shown one value while a different one is sent.

Doing only (1) passes a unit test of the payload and still breaks in the browser on the second
Apply. When a defaults channel gains a consumer, ask what else re-sends that value.

The change is a no-op for every cascor seed shipped today: all seven carry `default_params={}`,
asserted rather than assumed (`test_an_unseeded_dataset_is_unchanged`).

> **Superseded 2026-09-13 (canopy#625).** True when written, with one overstatement: the cited test
> asserts one of the seven (`xor`), not all of them. `mnist` has since seeded
> `default_params={"flatten": True}`, so canopy sends the value that makes its `ndim=2` declaration
> true (§12.9.1). Six of the seven now carry `{}`.

**`equities` needed a third key the rank-3 sibling never did.** Beyond `symbols` and
`fundamentals_fill`, it needs **`normalize_features=True`**: its columns are raw market
quantities, and unnormalised CasCor's first output pass reports a loss of **5.83e+21** against
**0.2511**. Train top-1 is ~0.52 either way, so **accuracy alone would not have caught it** — only
the loss magnitude shows it. As seeded: `(15799, 16)`, zero non-finite in any split, 3 units
recruited, 0.2511 → 0.2491 in 1.2s.

**A second defect surfaced because the seed made it common.** `equities` needs juniper-data's
`equities` extra, absent from that lockfile, so it is the dataset an operator will actually find
greyed — and canopy's greyed message said only "unavailable in this deployment". The producer had
been publishing the remedy all along: `GeneratorInfo.install_hint` has been on `/v1/generators`
since **W-4**, and its docstring says it exists because `available: false` otherwise "says a
generator cannot run and nothing at all about what would fix that". canopy was re-wording that
string for two generators and saying nothing useful for the rest, behind a comment asserting the
field did not exist. canopy#622 derives the label from the wire and renders the producer's hint
verbatim in the params panel — label and panel deliberately split, because a `pip install` command
does not fit in a dropdown option.

> **2026-09-23.** The `equities` extra has been in the lockfile on juniper-data `main` since
> juniper-data#421, but not yet in any juniper-data release (§12.5), so the greyed option and its
> install hint are still what a container built from a release shows.

**§12 final state**, against §12.1's ten:

| seeded (8) | not seeded (2) |
|---|---|
| `gaussian`, `checkerboard`, `equities` (rank-2) | `arc_agi` — no fixed rank; `flatten_pairs` flips it and `DatasetTypeSpec.ndim` is static |
| `multi_sine`, `mackey_glass`, `irregular_sine`, `ar_p`, `delay_product` (rank-3) | `csv_import` — an import path, not a peer generator; `file_path` is required |

Neither remaining entry is waiting on effort: `arc_agi` is waiting on a **design decision** about
how the registry should express a variable-rank generator, and `csv_import` is a settled exclusion.

### 12.9 The variable-rank proposal, adjudicated — and the twin `arc_agi` was excluded against (2026-09-12)

§12.8 closed §12 leaving `arc_agi` "waiting on a **design decision** about how the registry should
express a variable-rank generator". The owner put a proposal for that decision to adversarial
consensus. This section records the verdict, and the two findings that turned out to matter more
than the verdict did.

The proposal's eight points are numbered **VR-1…VR-8** here. They are deliberately *not* numbered
`P1`–`P8`: `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` already uses `P1`–`P4`
for its proposal lanes and `F1`–`F5` for its rejected families, and a note citing both documents
would be unreadable.

| | Proposal | Verdict |
|---|---|---|
| **VR-1** | A clear, useful label as variable rank | **Amend** — goal sound, mechanism unavailable |
| **VR-2** | Rank as a range, `N ≤ rank ≤ M` | **Amend** — a set, not a range |
| **VR-3** | The same interface retrieves the range as a single rank | **Reject** at the operator; survivable at the field |
| **VR-4** | Approve if the model handles every rank in the range | **Reject** — under both readings |
| **VR-5** | The user and the experimental framework own compatibility | **Reject** — reverses D5 and N9 |
| **VR-6** | The model must match the ranks *actually present* | **Confirm** as a fact; **reject** as an acceptance criterion |
| **VR-7** | Prefer adaptable models for variable-rank datasets | **Confirm**, but it is a no-op today |
| **VR-8** | Models determine actual rank and restructure to match | **Reject** as scoped |

**VR-4 decides most of the rest, and it fails for an arithmetic reason.** There are exactly two
`ModelSpec` entries: `cascor` with `input_ndim=frozenset({2})` (`src/model_registry.py:356`) and
`recurrence` with `frozenset({3})` (`:367`). No model in the registry accepts more than one rank.
So VR-4's literal reading — the model handles *every* rank in the range, i.e.
`dataset_ranks ⊆ model.input_ndim` — makes a `{2,3}` dataset compatible with **zero** models. That
is the same user-visible outcome as leaving `arc_agi` unseeded, bought with a new abstraction across
four call sites and three string builders. The only reading that changes behaviour is the
existential one (`∩ ≠ ∅`), and it reinstates exactly the hazard `UNSEEDED_GENERATORS["arc_agi"]`
was written to record. **The proposal does not say which reading it intends, and neither is
available.**

Rank is also one conjunct of three. `compatible()` (`:545`) is
`ndim ∧ task_type ∧ temporal_ok`, so a rank-only approval rule scores the easiest third.

**VR-5 reverses a ratified allocation of correctness.**
`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md:55` (D5) places correctness in
{predicate, backend} and calls the greying "a best-effort affordance, **not** the correctness
guarantee"; `src/model_registry.py:517-520` restates it in the code. VR-5 swaps the two halves.
§2 of this document requires that the remediation add `I-cover` *without weakening* `I-safe`, and
N9 states the rule directly: **a control that cannot be honoured is disabled at the control, not
discovered at the backend.** `I-safe` is written over `compatible()` and machine-checked by
`test_g1b_no_reachable_state_is_invalid`; "user responsibility" is not a term any transition
relation can carry, so under VR-5 `I-safe` becomes unfalsifiable rather than satisfied.

Compounding it: the backend refusal VR-5 delegates to is **itself unshipped on the newly-reachable
path**. `src/backend/recurrence_backend.py:205-206` returns `ok=True` immediately after
`thread.start()`, and `_completion_reason_label` (`src/frontend/dashboard_manager.py:6923-6929`)
maps five cascor reasons only — which is item X10/N6 of this arc, still open. The operator would
not see the refusal VR-5 relies on.

> **Half of this paragraph is stale as of juniper-canopy#651 (2026-09-22).** `_completion_reason_label`
> now maps recurrence's three completion tokens and has the `Failed` branch it lacked, so the
> operator DOES see why a recurrence fit ended. The other half stands: `RecurrenceBackend.start_training`
> still returns `ok=True` once the fit thread starts, so a refusal still arrives asynchronously, as a
> failed status rather than at the control. **VR-5's primary rejection is unaffected**: under VR-5
> `I-safe` becomes unfalsifiable, as argued above. Only this compounding argument has weakened.
>
> **Precision, 2026-09-23.** canopy#651 shipped both halves of the reporting defect, in two places:
> `_completion_reason_label` maps recurrence's three tokens (`max_epochs`, `early_stopping`,
> `converged`), and the missing `Failed` branch is in `_build_unified_status_bar_content`, which
> renders the error through `_failure_reason_label`. Re-checked on canopy `main`:
> `RecurrenceBackend.start_training` still returns `ok=True` right after `thread.start()`, so the
> note's "other half" stands.

**VR-2: a range misdescribes the domain; a set does not.** Rank is an integer and 2 and 3 are
adjacent, so "strictly between" is uninhabitable — a range promises a density that cannot exist.
`frozenset[int]` is the honest type and is **already** what the model side uses
(`src/model_registry.py:109`), which yields VR-3's symmetry for free. This matters prospectively
rather than now: `src/tests/regression/test_selection_reachability_guardrails.py:604` already
exercises `input_ndim=frozenset({4})`, and a future generator reachable at `{2,4}` would be
actively misdescribed by `2 ≤ rank ≤ 4`.

> **Line drift, 2026-09-23.** The `frozenset({4})` case is the `m_vol` entry of `SYNTH_MODELS`,
> G1c's synthetic registry in `test_selection_reachability_guardrails.py`; the `:604` above has
> moved. The argument is unchanged.

**VR-3 fails because the operator is asymmetric and fails silently.** `:545` is `scalar in set`.
`frozenset`, `tuple` and `range` all evaluate `False`; only `list` raises. A container `ndim` would
therefore grey **every** variable-rank dataset against **every** model, with no exception and no CI
red. The attribute *name* can survive a widening; the operator cannot. Two of the three
human-facing builders share the defect — `dataset_reason` (`:572-573`) and `dataset_model_hint`
(`:627`, `:649-650`, via a scalar-keyed `_RANK_NOUNS`) would emit literal `frozenset({2, 3})` text.
Only `model_reason` (`:592`) already has a range-safe `" or ".join` builder. VR-1's goal is sound;
its assumption that existing strings carry it is not.

**VR-8 is out of scope by §1, and has a costed precedent.** No rank exists to read: `GeneratorInfo`
(`juniper-data/juniper_data/core/models.py:143-162`) publishes `name / version / description /
available / install_hint / params_schema` and no shape at all, and `TrainableModel` exposes
`input_shape` only as a read-only *post-fit* report. The sole structural-adaptation mechanism,
`_resize_network_for_dataset` (`juniper-cascor/src/cascade_correlation/cascade_correlation.py:880`),
adapts feature **count**: scalar-typed, grow-only, and not on the `fit` path. §1 of this document
already puts capability relocation out of scope as family F5. And silent self-restructuring is the
failure class that left `config_json` stale against `arch` and made **239 of 27,908 snapshots
unloadable** (juniper-ml#1254, repaired by cascor#560); rank has no `_sync_config_dimensions`
equivalent. VR-7 is separately a no-op: `input_ndim` is already a set, so an adaptable model is
declarable **today** with no design change, and none is declared.

#### 12.9.1 `mnist` is `arc_agi`'s twin, and it was seeded anyway

The consensus found the premise of the whole question to be false. **`arc_agi` is not the only
generator with parameter-dependent rank — `mnist` is the second, and it is already seeded.**

`juniper-data/juniper_data/generators/mnist/generator.py:125-126` is the identical two-branch
reshape: `if params.flatten: X = X.reshape(len(X), -1)`, so `flatten=False` yields rank-3
`(N, 28, 28)`. canopy seeds `DatasetTypeSpec(value="mnist", …, ndim=2)` at
`src/model_registry.py:156`. `flatten` is absent from `FORM_EXCLUDED_FIELDS`
(`src/dataset_schema.py:107`), so the schema-driven panel renders it as a checkbox, and the form
overrides the seed (`src/frontend/dashboard_manager.py:3191-3192`). `mnist` is available in a
correctly-installed deployment: `datasets==5.0.1` is in `juniper-data/requirements.lock` and
`MnistGenerator.is_available()` returns `True`.

So the hazard `UNSEEDED_GENERATORS["arc_agi"]` records — *"an operator could flip a dataset canopy
statically declares `ndim=2` into rank-3 output"* — describes a generator that **already ships**.
The exclusion was applied to one member of a two-member class.

**Round 2 materially shrank the harm, and the first reading was wrong.** Round 1 reported a silent
train-on-the-previous-dataset via `src/demo_mode.py:2185-2186`. That is **false**:
`regenerate_dataset_from_generator` hardcodes `params={"seed": 42}` (`src/demo_mode.py:1964`), so
`flatten` never reaches the sequence-install branch, and its only caller is gated on
`backend_type == "demo"` while Apply posts to `/api/stage_dataset` instead. cascor also **fails
closed**, at `juniper-cascor/src/api/lifecycle/manager.py:4034-4035`, on both fetch paths.

What survives is a real but smaller defect, and its shape is the point:

| | |
|---|---|
| **Harm class** | A blocked stage, deferred — not a 500, and not a silent mistrain |
| **At Apply** | HTTP **200**, green "staged" banner. Nothing in canopy checks rank (`grep ndim src/main.py` → zero hits); `gated_dataset_options` gates on the *declared* `ndim` only |
| **At Start** | HTTP **409**, or **502** with rollback on a live swap |
| **Message** | *"3-D sequence artifacts belong to the juniper-recurrence tier"* — to an operator who selected MNIST |
| **Recovery** | The staged config is retained (`manager.py:2344-2350`), so every retry fails identically until the box is re-ticked |
| **Waste** | juniper-data generates and persists a full rank-3 MNIST under its own `dataset_id`, and cascor downloads it, before the refusal |

**Success is reported at the moment of the mistake and failure at an unrelated one** — the same
shape as the `ok=True`-then-fail-in-thread pattern N6 rejects, arrived at from the opposite
direction. Existing tests ratify the behaviour rather than pin the hazard:
`src/tests/unit/test_dataset_schema.py:100-101` asserts `flatten` renders as a checkbox, and
`src/tests/integration/test_apply_dataset_flow.py:182-187` asserts `flatten: True` reaches the
backend. Nothing exercises `False`.

Filed as **canopy#623**. **This is the item §12 should have produced, and the variable-rank
question is what surfaced it.**

> **Fixed 2026-09-13 and 2026-09-21; true when written.** canopy#625 (`f7bbc4ee`) closed canopy#623:
> `SHAPE_DETERMINING_FIELDS` withholds `flatten` for `mnist` and `flatten_pairs` for `arc_agi` from
> the rendered form, keyed per generator as §12.9.3 asked, and `mnist` now seeds `flatten: True`.
> canopy#644 (`ba3b16ff`) enforced the forward half: `_apply_dataset_handler` filters the form's
> params through the same `form_excluded_fields`, so a control left over in a stale tab cannot send
> `flatten: False`, and `test_a_fabricated_control_id_cannot_override_the_withheld_knob` exercises
> exactly that. The two tests cited above are still present and test other layers: the schema
> parser still maps a boolean to a checkbox, and the stage route still forwards `flatten: True`.

#### 12.9.2 `arc_agi`'s blocker is its `y`, not its rank

The second finding retires the question rather than answering it. **Solving rank would not make
`arc_agi` seedable**, for two independent reasons that sit upstream of the registry.

1. **Its rank-3 form is refused on the task axis regardless of rank.** `arc_agi` is registered
   `task_type="classification"` (`juniper-data/juniper_data/api/routes/generators.py:172`), and the
   only rank-3 model is `supported_task_types=frozenset({"regression"})`
   (`src/model_registry.py:367`). Rank-3 classification has **zero** models in this registry, so
   `compatible()` is `False` at any rank type.
2. **Its `y` is not a class vector.** `y_stacked` is built from the padded `output_grid`
   (`juniper-data/juniper_data/generators/arc_agi/generator.py:265-273`) — the same shape as `X`.
   Flattened it is `(n, 900)`: 900 cells valued in `[-1..9]`, not a 10-way one-hot. It is a
   grid-to-grid map declared as classification. canopy's rank-2 install path takes
   `np.argmax(y, axis=1)` (`src/demo_mode.py:1993`), which yields a "class label" in `[0, 900)`.

The `task_type` declaration is wrong **at the producer**, and no model in canopy's registry consumes
a grid-to-grid map. §12.8's table gives `arc_agi`'s reason as "no fixed rank; `flatten_pairs` flips
it and `DatasetTypeSpec.ndim` is static". That is true but is **not the blocker**, and it is the
same class of error §12.8 itself recorded against §12.7: naming the obstacle correctly and stopping
one step short of the cause. The entry should name the `y`-shape and `task_type` mislabel, and the
`task_type` question belongs upstream alongside the other `arc_agi` corrections in
`JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`.

> **Done upstream, 2026-09-15; true when written.** juniper-data#402 (`f3797634`, released in
> v0.15.0) registers `arc_agi` with `task_type` `TASK_TYPE_STRUCTURED` ("structured"), its comment
> naming the grid `y`. canopy's `UNSEEDED_GENERATORS["arc_agi"]` gives the `y`-shape as the reason
> (since canopy#625) and records the upstream move. No model's `supported_task_types` contains
> "structured", so the incompatibility is now explicit, and `arc_agi` stays unseeded.

#### 12.9.3 What to ship

**Not a registry change.** `compatible()` is untouched.

1. **Exclude the shape-determining knobs from the rendered form** — `flatten` and `flatten_pairs` —
   joining `INFRASTRUCTURE_FIELDS` and `PARTIAL_DATA_POLICY_FIELDS` in the `FORM_EXCLUDED_FIELDS`
   union (`src/dataset_schema.py:107`). Same union, same shape, same reason class: *a field whose
   value contradicts a declaration the registry makes elsewhere.* Key it **per generator** rather
   than globally — this schema space already has cross-generator name collisions
   (`normalize_features` appears in three generators, `one_hot_labels` in two), and the call site at
   `src/frontend/dashboard_manager.py:3068` already has the generator name in hand.
   Excluded-but-seeded keys still travel to the backend (`:3191`), so nothing is dropped.
2. **Keep `arc_agi` unseeded, and correct its recorded reason** per §12.9.2.
3. **Leave the registry's rank type alone.** If a grid-native model is ever added, the two-entry
   split — `arc_agi_flat` / `arc_agi_grid`, each pinning `flatten_pairs` in `default_params` —
   becomes correct, costs two seeds and two aliases, introduces **zero** new concepts, and uses the
   defaults channel canopy#621 shipped. It is cheap *then* and premature *now*.

> **Shipped, 2026-09-23 note.** Item 1 in canopy#625 (render) and canopy#644 (forward), keyed per
> generator through `form_excluded_fields`; item 2 in canopy#625; item 3 needed no change, and
> `compatible()` is untouched (§12.9.1).

**Two unrelated defects surfaced in passing**, both in the same "the panel renders every scalar the
schema declares" class, and neither belongs to §12:

- `sizing_mode`, `val_percent`, `test_percent` and `val_ratio` render as generator *content*
  parameters on **all 16** generators. Three-partition split plumbing is leaking into the form;
  `INFRASTRUCTURE_FIELDS` (`src/dataset_schema.py:83`) predates those four fields.
- `sizing_mode` renders as a **free text box** — the schema emits `type: string` with no enum — so a
  typo becomes a 422 from juniper-data.

> **Fixed 2026-09-16; true when written.** canopy#632 (`812f26c0`, closing canopy#630) added
> `sizing_mode`, `val_percent`, `test_percent` and `val_ratio` to `INFRASTRUCTURE_FIELDS`, so none of
> the four renders or is forwarded, which also removes the free-text `sizing_mode` box.

**Corrected §12 final state**, superseding §12.8's table on the `arc_agi` row only:

| seeded (8) | not seeded (2) |
|---|---|
| `gaussian`, `checkerboard`, `equities` (rank-2) | `arc_agi` — its `y` is a 900-cell grid declared `task_type="classification"`; rank-3 classification has no model, and the variable rank is a secondary UI hazard shared with the seeded `mnist` |
| `multi_sine`, `mackey_glass`, `irregular_sine`, `ar_p`, `delay_product` (rank-3) | `csv_import` — an import path, not a peer generator; `file_path` is required |

`arc_agi` is no longer waiting on a design decision. The decision was taken here: **the registry
expresses a single rank, and a generator whose rank the operator can flip has that knob withheld
rather than described.**

> **2026-09-23.** The table's `arc_agi` row describes juniper-data before juniper-data#402
> (2026-09-15), which re-registered `arc_agi` as "structured" (§12.9.2). The row's conclusion is
> unchanged: no model accepts it, and it stays unseeded.
