# Thread Handoff — §12 is closed; what remains is the arc's residue, and one of it is a decision

- **Date**: 2026-09-12
- **Arc**: juniper-canopy model/dataset selection reachability (the "Recurrence cannot be selected" defect)
- **Session**: `resilient-strolling-bachman`
- **Predecessor**: [`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`](HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md) — its item 1 is **closed** here; items 2–8 are carried forward, each **re-verified against `main` today** rather than inherited
- **Design of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) — **§12 now closes at §12.8**; §12.6 and §12.7 carry this arc's corrections

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
