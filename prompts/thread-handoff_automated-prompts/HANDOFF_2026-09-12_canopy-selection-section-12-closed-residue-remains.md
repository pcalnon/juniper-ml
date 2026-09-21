# Thread Handoff — §12 is closed; what remains is the arc's residue, and one of it is a decision

- **Date**: 2026-09-12
- **Arc**: juniper-canopy model/dataset selection reachability (the "Recurrence cannot be selected" defect)
- **Session**: `resilient-strolling-bachman`
- **Predecessor**: [`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`](HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md) — its item 1 is **closed** here; items 2–8 are carried forward, each **re-verified against `main` today** rather than inherited
- **Design of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) — **§12 now closes at §12.8**; §12.6 and §12.7 carry this arc's corrections
- **Status addendum**: [§ Status as of 2026-09-21](#status-as-of-2026-09-21) — read that FIRST. Three of the eleven items below are closed, two are materially misstated, and the residue is larger than this document records. The body below is preserved unedited as the 09-12 record.

---

## Status as of 2026-09-21

Session `velvety-pondering-frost`. Every item re-probed against `main` in both repos, then put through three independent adversarial
agents (factual re-probe / conclusion attack / omission hunt) per
`feedback_multi_agent_adversarial_validation_sop`. **Four of my own claims were refuted and are
corrected here**; the agents' findings were themselves re-derived in source before being recorded.
This document is still this arc's live handoff — nothing after 2026-09-12 supersedes it.

### Disposition of the eleven items below

| # | Item | Status |
|---|---|---|
| 1 | §4.10 hydration + G7 | **OPEN.** `_init_params_from_backend_handler` has moved to `src/frontend/dashboard_manager.py:8715` (was `:8679`); `NUM_OUTPUTS = 29`, still zero dataset-axis outputs. |
| 2 | `⊥`-at-mount (OQ-N2) | **OPEN**, unchanged. `value=DEFAULT_DATASET_TYPE` at `:1400` and `:5991`; `params-init-interval` ×11. |
| 3 | X10 / X11 | **OPEN and WIDER** — see new item **N3**. |
| 4 | Y1 / Y2 | **Y1 CLOSED** (canopy#633; `recurrence_backend.py:408`). **Y2 OPEN**, and four *more* methods are missing — see **N1**. |
| 5 | ∥ packaging | **OPEN, mechanism corrected.** `yfinance` is absent from `juniper-data/requirements.lock` because the lock is compiled `--extra api --extra observability --extra mnist` (its header line 2) and `yfinance` lives in the `equities` extra (`juniper-data/pyproject.toml:51`). Not a forgotten pin — a lock-scope decision. |
| 6 | §4.3 residue | **CORRECTED 2026-09-21 — half of this is already done, and my first pass repeated the predecessor's error.** The accessibility half is **SHIPPED**: `dashboard_manager.py:1418` renders the gate notice as `html.Div(id="dataset-gate-notice", role="status", **{"aria-live": "polite"})`, and `:1413-1417` records why that mechanism and not `aria-describedby` — Y7 measured zero aria-* attributes, dash 4.2.0's dropdown emits no `aria-disabled`, so a greyed option's gate is invisible to assistive technology and a detached toast would have been worse than rendering inline. **"`aria-describedby` 0 occurrences" is a true count and a false conclusion**; I verified the number without checking the claim, which is `reference_partial_read_generalisation` committed inside a document warning about it. What remains of item 6 is the D5 label only — see item 7, which is the same knot. |
| 7 | Record OQ-6 answered | **OPEN — and items 6 and 7 are ONE item.** `dashboard_manager.py:2909` asserts the snap is "(dataset-primary conflict policy, D5)". D5 does not say that. `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md:55` defines D5 as *"Conflict rule is a swappable policy… The default policy (dataset-primary vs model-primary) is **chosen after the A1 spike / first real use**"*, and `:305` files that choice as **OQ-6**. So the code cites D5 for a decision D5 explicitly defers, the implementation has since made that choice in fact (dataset-primary), and both design records still say it is open. Ratifying dataset-primary is an owner call; recording that the implementation already took it is not. Either way the code's citation should point at OQ-6's resolution rather than at D5. |
| 8 | `arc_agi` is a DECISION | **CLOSED.** §12.9 of the design doc adjudicated VR-1…VR-8 (juniper-ml#1923); canopy#623 → **canopy#625** shipped it. The registry expresses a single rank; a rank-flipping knob is withheld, not described. |
| 9 | "the signed-commit helper has FOUR copies" | **MISSTATED — do not action as written.** A canonical helper *is* already promoted: `util/open_signed_pr.py:117` `create_signed_commit`, with a hermetic test at `tests/test_open_signed_pr.py`. All four ad-hoc files **reuse** it (`import open_signed_pr as osp`, or an `importlib` path-load) rather than duplicating it, and one self-declares as a promotion candidate. The fourth path is `util/ad-hoc/push_signed_commit.py`, **not** `util/push_signed_commit.py`. What remains is consolidating four thin *drivers* — a much smaller job than "promote one, retire three". |
| 10 | canopy timing flakes | **SUPERSEDED.** The real defect was not flakiness — see **N0**, fixed in **canopy#641**. |
| 11 | upstream question to juniper-data | **HALF CLOSED.** The `arc_agi` `task_type` half was filed as **juniper-data#401** and fixed by **juniper-data#402** (merged 2026-09-15): `arc_agi` now declares a *third* task-type value, `TASK_TYPE_STRUCTURED`. The **equities-defaults half remains unfiled** — juniper-data has exactly one open issue (#179, June). |

### Corrections to my own first pass (kept, because each is a trap)

- **"60/60 failures since 2026-07-24" was an instrument artifact** — I read my own `--limit 60` as the
  retention horizon. Retention holds **145 runs back to 2026-05-01, with 58 successes**. The true
  shape is better evidence: last green **2026-07-20**, unbroken failure streak of **63** from
  2026-07-21 — and canopy#459 added the offending import at 17:57 on 2026-07-20.
- **"ci.yml documented this hazard and it was never propagated"** is right about the *integration*
  lane (its N3 comment names `.constants`) and wrong about the *unit* lane: that comment describes a
  silent `importorskip`, and landed 2h48m **before** the `.constants` import existed.
- **My own regression guard passed vacuously on first draft** — it searched the run-step text for
  `[juniper-cascor]`, which the explanatory comment I had just written satisfies. Mutation-checking
  caught it; the check now strips comments and matches a real `pip install`.

### New items, highest-value first

- **N0 — `Scheduled Tests` red for 63 consecutive runs. FIXED, PR open: canopy#641.**
  `scheduled-tests.yml` installed `pip install -e .` with no extra, so `src/tests/conftest.py`'s
  stub (top-level + `.exceptions` + `.client` only) could not satisfy
  `cascor_service_adapter.py:45`'s `from juniper_cascor_client.constants import …`. Four modules
  died at **collection**. Also fixed: `src/tests/contract/` and `src/tests/performance/` were named
  by **no lane at all** — 3 and 4 live tests that had never run in CI.
- **N1 — four more `RecurrenceBackend` methods are missing and called unguarded.** Y1 was one of
  five. `swap_dataset_live`, `cancel_swap_dataset_live`, `get_dataset_swap_events` and
  `get_snapshot_dataset_swaps` exist on `demo_backend.py` and `service_backend.py`, and are **0** in
  `recurrence_backend.py`; called with no `hasattr` guard at `main.py:4429`, `:4455`, `:4492`,
  `:4521`, inside a bare `except Exception` that returns a 500 + `error_id`. **`get_dataset_swap_events`
  is worse than Y1 ever was**: `_setup_dataset_swap_observers_callbacks` polls
  `/api/history/dataset_swaps` on every `slow-update-interval` tick —
  `SLOW_UPDATE_INTERVAL_MS = 5000` (`canopy_constants.py:371`) — so under recurrence that is a fresh
  500 every five seconds for the life of the page, invisible to the client.
- **N2 — §12.4's own acceptance criterion was never met.** §12.4 requires generate → **stage** →
  train → **render**, per seed. §12.6/§12.7 record direct library calls only (`LMURegressor.fit`
  in-process; generate → NPZ → `CascadeCorrelationNetwork.fit`). **No seed has ever travelled
  canopy's `_apply_dataset_handler` → `/api/stage_dataset` → Start path, and none has been rendered.**
  The 09-08 predecessor carried this caveat ("No training run has ever been started"); this document
  dropped it while declaring §12 closed.
- **N3 — X10/N6's other half.** Beyond `initialize()` returning `True` unconditionally
  (`recurrence_backend.py:422-425`) and `selection_is_live` being health-blind
  (`model_registry.py:491`), a recurrence run's `completion_reason` never reaches the operator.
  **Corrected 2026-09-21 — this is TWO mechanisms, not one, and the first is not a mapping
  miss.** `completion_reason` has exactly one consumer, `dashboard_manager.py:7118-7121`, and it
  is gated on `status == "Completed"`; there is **no `status == "Failed"` branch anywhere in the
  file**. So:
  - **A failed run's reason is never read at all.** `recurrence_backend.py:274` writes the raw
    error into `completion_reason` on `state == "failed"`, and the consumer block does not run.
    The gate matches cascor's semantics — its five reasons are all *completion* outcomes — so
    this is an overload: the same field carries a completion outcome in cascor and a **failure
    error** in recurrence, and only the cascor reading is implemented.
  - **A successful run's reason is dropped by the mapper.** `_completion_reason_label`
    (`:6921-6936`) maps five cascor tokens and `.get()` returns `None` for anything else, so
    recurrence's `stopped_reason` (`:277-279`) renders nothing. That reason is an **open
    vocabulary** — `recurrence_service_adapter.py:161` types it `Optional[str]`, passed straight
    through from the service's JSON — so the fix needs a rendering rule for unmapped values, not
    a bigger table.

  The earlier wording here attributed both halves to the mapper. It is right that the reason is
  discarded and right that §12.9's rejection of VR-5 rests on this being broken; it is wrong
  about why the failure case is lost, which matters because the fix is a missing branch rather
  than a missing table entry.
- **N4 — the equities seed's recorded evidence is stale against two breaking bumps.**
  `model_registry.py:201` records `(15799, 16)`, measured 2026-09-11 at generator `3.0.0`. The
  generator is now **`5.0.0`** (`juniper-data/.../equities/generator.py:58`), and 4.0.0 made the
  default feature matrix **15 columns, not 16**. #404 exists because #395 shipped values wrong by
  400–1000×. Nothing has re-validated the seed.
- **N5 — `_fetch_generators` fails OPEN, and §12 made that eight times worse.**
  `dashboard_manager.py:3006-3013`: any error yields an empty list, and the availability helpers then
  treat **every** generator as available. Three seeds are now availability-gated, and
  `_gate_dataset_options_handler` snaps to the first compatible-and-available entry — so with
  juniper-data down the operator is landed on a dataset that cannot generate, Apply returns 200, and
  Start fails. Carried by the 09-07 and 09-08 handoffs; dropped here without closure.
- **N6 — canopy#625 shipped the render half, not the forward half.** `dataset_schema.py:134-136`
  states the contract as "neither render **nor forward**". Only rendering is filtered
  (`dashboard_manager.py:3073`); `_collect_generator_params` still drops only `None`/`""` and the
  form overrides the seed. And `test_a_seeded_generator_with_a_withheld_knob_cannot_be_overridden_by_the_form`
  never constructs a control id — **its name over-claims a guarantee its body does not test**.
- **N7 — no drift test against juniper-data (Y6), and its stated justification is false.**
  `test_dataset_generator_contract.py:227-231` says upstream *adding* a generator is not caught;
  `:285-288` justifies being hermetic by claiming the env has juniper-data `0.6.0`. It has
  **`0.14.0`**. N4 is precisely the drift this would have caught.
- **N8 — canopy's `juniper-data-client` floor predates decision 11.** `pyproject.toml:148` pins
  `>=0.4.1,<0.6.0`; the env runs **0.4.1**, with **no `validate_npz_contract`**. The three-partition
  contract every §12 seed depends on arrived in 0.5.0, so it is never exercised locally. This is the
  unchanged local half of canopy#559.
- **N9 — canopy documents a two-value `task_type` vocabulary that is now three.**
  `model_registry.py:36-38` and `:91` both say `"classification" | "regression"`; juniper-data#402
  added `structured`. Nothing breaks today (`task_type` is an unconstrained `str` and `arc_agi` is
  unseeded), but no `ModelSpec.supported_task_types` contains it, so a future `structured` generator
  is silently compatible with nothing.
- **N10 — canopy#368 is this arc's parent issue and has never been updated.** Open since
  2026-06-17 while most of its A0/A1 shipped. Two clauses are outstanding: the mandatory `nn_model`
  backend mirror on `SetParamsRequest` and `StageDatasetRequest`, and the accessibility clause
  (= Y7, item 6 above, tracked there without its issue). **canopy#371**'s stated promotion trigger
  ("promote when A1 lands") has also fired, untouched.

### Recommended order

**N1 before N0's remainder.** A permanently-red CI lane is loud, bounded and costs attention; a
backend that reports healthy while its service is down, 500s every five seconds, and writes
snapshots that report success while persisting zero model state is silent and corrupts results.
N0 was done first only because it was cheap and already proven — not because it ranks highest.

### Progress, later on 2026-09-21

| item | state |
|---|---|
| **N0** | **MERGED — canopy#641.** Verified on `main` by a `workflow_dispatch` run rather than assumed: all three legs green, the first success after the 63-run streak. **The recovery was ~4× the estimate** — measured `413 → 506 passed`, `4 → 0 errors`, `103 → 81 skipped`. The PR predicted ~25 tests; other modules were `importorskip`-ing on the same missing client *without erroring*, including the 510-line stream-liveness suite `ci.yml:169-172` already warned about for its own lane. A skip is not a failure, so nothing counted them — the loud defect was masking a quiet one four times its size. |
| **N1** | **MERGED — canopy#643.** All four methods, plus `cancel_pending_dataset` (unguarded at `main.py:4324`, undeclared, implemented everywhere today — latent, not live). Verified on merged `main`: protocol declares **27**, all three backends implement all 27, `get_dataset_swap_events()` returns `{'ok': True, 'events': []}` and `swap_dataset_live()` returns `ok=False`. The five-second 500 is closed. Guard reads the requirement from the **caller**: a plain conformance test passes vacuously, because on `main` the protocol declared 22 methods and all three backends implemented all 22 while the four broken ones sat undeclared. |
| **N6** | **PR open — canopy#644.** Confirmed a **live** defect, not merely an untested claim: the mutation check shows a fabricated/stale `flatten: False` control genuinely overrides the seed and stages mnist rank-3. Needed an `Allow-Symbol-Loss:` trailer — the test split is a same-file rename, which the sequence-safety screen reads as deletion, correctly. |
| **N8** | **PR open — canopy#647.** The floor admitted `juniper-data-client>=0.4.1` while decision 11's contract shipped in 0.5.0; the lock already sat at 0.5.0, so the gap was between what the lock tests and what published metadata lets a consumer install. Verified from the published wheel. Also retires a comment in `demo_mode.py` whose justification ("absent from the pinned / published client (0.4.x)") is now false in both halves — canopy#559's first half. |
| **N4 / N9** | **PR open — canopy#648.** Both are stale claims the registry makes about juniper-data, not functional defects. The equities evidence was measured at generator `3.0.0`; it is now `5.0.0` and the default matrix is **15 columns, not 16**. The `task_type` vocabulary has been three values since juniper-data#402 added `structured`. |
| **11** | **CLOSED as asked — juniper-data#409.** The equities-defaults question is filed upstream with the defaults read from source today (`fundamentals_fill="nan"`, `normalize_features=False`, `regression_target="next_close"`, the last non-stationary by its own field description) and the two consumer measurements cited to their origin rather than re-measured. Awaiting an owner ruling; no change proposed, because a silent default change is the class that produced the 4.0.0 → 5.0.0 bump. |
| **N3** | Diagnosis corrected above. Not started — its fix needs a rendering rule for an open vocabulary, which is a UI judgement rather than a mechanical repair. |
| **N7** | Deliberately not built. canopy's CI does not install the juniper-data service package, so a registry-vs-upstream drift test would either skip in CI — vacuous exactly where it is needed — or require a new install in that lane. A design question, not a comment fix. |

Still unstarted: **N2** (needs the real stack — a different kind of work from the rest), **N5**,
**N10**, and original items 1, 2, 3, 5, 9, plus the single remaining half of 6/7.

### Verification commands (2026-09-21 — supersede the block below)

```bash
# Both repos are current as of this writing; canopy main = 034925ae, juniper-ml main = d721fc78.
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git pull --ff-only origin main

# §12 still closed: 14 seeds / cascor 8 / recurrence 6 / unseeded arc_agi + csv_import
cd src && conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from model_registry import DATASET_TYPES, MODELS, compatible_datasets, UNSEEDED_GENERATORS
print(len(DATASET_TYPES), sorted(UNSEEDED_GENERATORS))"

# N1: four methods present on demo/service, absent on recurrence
for m in swap_dataset_live cancel_swap_dataset_live get_dataset_swap_events get_snapshot_dataset_swaps; do
  echo "$m recurrence=$(grep -c "def $m" backend/recurrence_backend.py) service=$(grep -c "def $m" backend/service_backend.py)"
done   # expect 0 / 1 each

# N0 reproduced without a clean venv (juniper-ml worktree)
python util/ad-hoc/2026-09-21_canopy_scheduled_lane_repro.py   # expect 4 collection errors
```

**Changed this session**: `.github/workflows/ci.yml`, `.github/workflows/scheduled-tests.yml`,
`src/tests/regression/test_ci_lane_wiring.py` (all juniper-canopy, in **canopy#641**);
`util/ad-hoc/2026-09-21_canopy_scheduled_lane_repro.py` and this file,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md`
(both juniper-ml).

**Git status**: juniper-canopy `main` at `034925ae`, clean; branch `fix/scheduled-lane-cascor-extra`
pushed, **canopy#641 open, NOT merged** — the 09-12 merge approval covered that arc's PRs and does
not extend here. juniper-ml worktree `velvety-pondering-frost` on
`docs/canopy-selection-handoff-status-2026-09-21`.

---

## Goal statement

Continue the juniper-canopy selection-reachability arc. **§12 — the generator gap, the owner's
stated primary goal — is closed.** Eight of §12.1's ten generators are seeded; the two that are
not each have a settled reason, and one of those is a **design decision, not effort**. What
remains is the arc's residue: hydration, the `⊥`-at-mount contradiction, backend-identity
honesty, and two recurrence-path holes that 500 or silently lie.

**Completed this session — six PRs across two repos:**

- **canopy#609** — **Y5**. `/api/dataset/generators` was the one canopy→juniper-data caller using
  raw `httpx` with no `X-API-Key`; `/v1/generators` is not in juniper-data's `EXEMPT_PATHS`, so a
  keyed deployment 401'd, the route ignored any non-200, and the schema-less fallback made every
  dataset's params panel read *"No adjustable parameters"*.
- **canopy#610** — **the `equities_seq` seed could neither generate nor fit**, which is why the
  pair canopy#601 and canopy#607 exist for had never trained. `max_symbols` is a cap juniper-data
  *refuses* against (503 names over a cap of 14), and `fundamentals_fill` defaults to `"nan"`,
  leaving `X_train` 9.1% non-finite **while `X_val`/`X_test` are entirely clean**.
- **canopy#612** — §12's five rank-3 synthetics, each §12.4-validated (generate **and** fit).
  `multi_sine` r² 1.000, `mackey_glass` 0.9999, `irregular_sine` 0.9918, `ar_p` 0.043,
  `delay_product` 0.004 — all ~0.1s end to end. Seeded **before** `equities_seq` because the gate
  snaps to the first compatible+available entry. Plus G10 (`UNSEEDED_GENERATORS`).
- **canopy#616** — the rank-2 slice: `gaussian` (top-1 **1.000**) and `checkerboard` seeded,
  validated against **cascor** through the real NPZ artifact contract.
- **canopy#621** — **the `equities` unblock**. The blocker was never `equities`: it was the
  **defaults channel**, which reached one of two model tiers. Fixed at the cause, then seeded.
- **canopy#622** — `GeneratorInfo.install_hint` has been on the wire since juniper-data **W-4**;
  canopy was re-wording it for two generators behind a comment asserting it did not exist.

Record: **ml#1871**, **ml#1872**, **ml#1889**, **ml#1918** (§12.6–§12.8 + seven validation probes
under `util/ad-hoc/`), and **ml#1893** (the memory-index compaction helpers).

**Remaining work — the predecessor's items 2–8, all re-verified open today, plus four new:**

1. **§4.10 dataset-axis hydration + G7** — unshipped, and now the oldest blocker in the arc.
   `dashboard_manager.py:8679` `_init_params_from_backend_handler` is the natural host and
   hydrates hyperparameters and the spiral/element knobs from `/api/state` — but **not the
   dataset axis**. G7 has no test. **N10: hydration lands before `⊥`-at-mount.**
2. **`⊥`-at-mount (OQ-N2)** — owner-accepted, still undeliverable as specified. Do not
   re-litigate: the `params-init-interval` snap, the seed line at `dashboard_manager.py`
   `value=DEFAULT_DATASET_TYPE`, and the prospective two-writer problem are unchanged.
3. **X10 / X11** — `recurrence_backend.py:392` `initialize()` returns `True` unconditionally, so a
   dead service still reports `backend="recurrence"`; first paint always reads "Active: CasCor".
   **N5's gate is exactly as health-blind**: `selection_is_live` compares provider to
   `backend_type`, so a recurrence backend whose service is down still counts as live.
4. **Y1 / Y2** — `RecurrenceBackend` has **no** `get_experimental_functions`, and `main.py:4363`
   calls it unguarded; the `except Exception` turns that into a **500 with an error_id on every
   page mount under recurrence**. And it implements no snapshot save/restore, so that path writes
   cascor meta and zero LMU state **while reporting success**.
5. **∥ packaging** — `yfinance` is still absent from `juniper-data/requirements.lock` (verified).
   This is now more load-bearing, not less: `equities` is seeded, so it and `equities_seq` are
   both greyed in the container. canopy#622 at least makes that greying say what to install.
6. **§4.3 residue** — `dashboard_manager.py` still labels the model-driven snap *"(dataset-primary
   conflict policy, D5)"*; `aria-describedby` (Y7) has never shipped (0 occurrences).
7. **Record that OQ-6 is answered** — the design still says *"OQ-6 remains open"* (N7, line 81)
   while the dataset-primary policy is asserted in a docstring.
8. **NEW — `arc_agi` is a DECISION, not a task.** It has no fixed rank: `flatten_pairs` (a
   rendered boolean) flips it between rank-2 `(n, pad_to²)` and rank-3 `(n, pad_to, pad_to)`, and
   `DatasetTypeSpec.ndim` is static. A rank-3 `arc_agi` is compatible with nothing. Someone must
   decide how the registry expresses a variable-rank generator before it can be seeded.
9. **NEW — the signed-commit helper has FOUR copies**, not the two the predecessor recorded:
   `util/push_signed_commit.py`, `util/ad-hoc/2026-09-08_push_signed_commit.py`,
   `util/ad-hoc/2026-09-08_append_signed_commit.py`,
   `util/ad-hoc/2026-09-10_soak_stopping_rule/append_signed_commit.py`. Promote one, retire three.
10. **NEW — canopy's timing tests flake and cost reruns on every PR.** Not confined to the X7
    modules: `test_main_import_and_lifespan.py::test_keepalive_loop_survives_broadcast_error`
    joined them. `1 failed, 6355 passed` on the slowest matrix leg is the shape.
11. **NEW — an upstream question worth putting to juniper-data.** Both equities generators produce
    data their own consumers cannot use at bare defaults: `equities_seq` needs two keys, `equities`
    three. That may be a deliberate "the caller must choose", but nothing says so.

---

## Key context

### §12's real lesson: the blocker was the channel, not the dataset

canopy#616 recorded that `equities` needed three params canopy "cannot deliver on the cascor
path". That was true and one step short. `dataset_default_params` had **two** production
consumers — `_resolve_oneshot_start_body_handler` (gated on `model_class == "one_shot"`) and
`dataset_ref_from_staged` — **both recurrence**, while its docstring called the registry "the
single source of truth". Any rank-2 seed needing any parameter would have hit it.

**Fixing it needed BOTH halves**, and this generalises: `_apply_dataset_handler` seeds the payload
from the registry (so an unrendered key like the `symbols` **array** can travel), *and*
`apply_seeded_defaults` seeds the **rendered controls** — because otherwise a key that is both
seeded and rendered is posted back at its **schema** default on the next Apply, silently undoing
the seed while the operator is shown one value and a different one is sent. **Fixing only the
payload passes a unit test of the payload and still breaks in the browser on the second Apply.**

### Three measurement traps this arc paid for

- **A defect can live in `X_train` ONLY.** `equities_seq` was 9.1% non-finite in train and
  **entirely clean** in val and test, so any check sampling the held-out splits saw a healthy
  dataset. Check every partition by name.
- **Accuracy can be blind to the defect.** `equities` unnormalised gives a first-pass loss of
  **5.83e+21** vs **0.2511** — but train top-1 is ~0.52 either way. Only the loss magnitude shows it.
- **Check the instrument before the claim.** My first census contradicted §12.1's Δt table; the
  census was wrong (`dt[:, 0]` is a 0.0 no-previous-step sentinel). My first CasCor fit reported
  `equities` as a fit failure that was really `input_size` defaulting to 2, and starved
  `checkerboard` with `max_iterations=2`.

### Do not re-litigate

`swapped is False` is the wrong "is this model active" predicate; `None` is unknown, not
disagreement; cascor refuses 3-D artifacts **by design** (never widen that `Literal`); the
recurrence service is one-shot and needs no staging endpoint; a staged config wins over the
one-shot Start body.

---

## Verification commands

> **Bring the shared canopy checkout forward FIRST, or every check below lies to you.** At the
> time of writing `/home/pcalnon/Development/python/Juniper/juniper-canopy` sat **2 commits behind
> `origin/main`** — missing exactly #621 and #622 — with a clean tree. Running step 2 against it
> reports 13 seeds, 7 cascor datasets and `equities` still unseeded, which is the state *before*
> this session's last two PRs. I hit this writing this document. It is
> `reference_a_checkout_is_not_a_deployment` in miniature, and it is why step 1 is a `pull`
> rather than a `fetch`. (Left un-pulled deliberately: the shared checkout may be open in another
> session, and moving it is that session's call, not a handoff's.)

```bash
# 1. Both repos current — PULL, not just fetch; the shared checkout lags behind origin/main
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy status --porcelain   # must be clean first
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy pull --ff-only origin main
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy log --oneline -4
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin && git log origin/main --oneline -3

# 2. §12 is closed — eight seeds, and cascor/recurrence still form two components
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from model_registry import DATASET_TYPES, MODELS, compatible_datasets, UNSEEDED_GENERATORS
print('seeds      :', len(DATASET_TYPES))
print('cascor     :', [d.value for d in compatible_datasets(next(m for m in MODELS if m.key=='cascor'))])
print('recurrence :', [d.value for d in compatible_datasets(next(m for m in MODELS if m.key=='recurrence'))])
print('unseeded   :', sorted(UNSEEDED_GENERATORS))"
# expect 14 seeds; cascor 8; recurrence 6; unseeded ['arc_agi', 'csv_import']
# 13 / 7 / equities-still-unseeded means the checkout is stale, NOT that §12 regressed

# 3. The equities seed carries all three load-bearing keys
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from model_registry import dataset_default_params; print(dataset_default_params('equities'))"

# 4. The arc's guardrails
conda run -n JuniperCanopy1 python -m pytest \
  tests/regression/test_selection_reachability_guardrails.py \
  tests/regression/test_dataset_generator_contract.py \
  tests/regression/test_recurrence_staging.py \
  tests/unit/test_model_registry.py tests/unit/test_dataset_schema.py -q -p no:cacheprovider

# 5. Item 4 (Y1), reproduced: RecurrenceBackend has no get_experimental_functions
grep -c 'def get_experimental_functions' backend/recurrence_backend.py   # expect 0
```

**Judge a pytest run by the absence of `FAILED`/`ERROR` and the trailing `[100%]`** — this repo's
config prints no `N passed` line under `-q`. And **do not read only the last progress line**: a
`grep` for `100%` hides the earlier lines of a multi-line progress block and makes a 6,000-test
run look like 28.

---

## Git status at handoff

- **juniper-canopy**: `origin/main` at `1597c67` carries #609, #610, #612, #616, #621, #622. This
  session's worktrees are all removed and their branches deleted. **`#620` (release v0.8.0
  proposal) is open** — release-proposal commits dirty every open PR touching `CHANGELOG`/`AGENTS`,
  so expect to rebase around it.
- **juniper-ml**: this session worked from `.claude/worktrees/resilient-strolling-bachman` on
  `main`, now converged to `origin/main` and clean. ml#1871/#1872/#1889/#1893/#1918 are merged.
- **MEMORY.md was compacted** (23.8KB/162 lines → ~20KB/94 lines after a peer session folded it
  further). Verified lossless against a snapshot with
  `util/ad-hoc/2026-09-11_memory_index_verify_lossless.py`; 33 topic files carry an "Index digest".
- **Merge approval** was granted by the owner for this arc's PRs. It does **not** extend to a new
  arc, and never extended to deploys or PyPI gates.
