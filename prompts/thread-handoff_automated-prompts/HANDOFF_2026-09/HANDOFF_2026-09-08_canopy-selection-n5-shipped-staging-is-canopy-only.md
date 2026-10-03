# Thread Handoff — N5 shipped, the pair is stageable, and both "cross-repo" premises were wrong

- **Date**: 2026-09-08
- **Arc**: juniper-canopy model/dataset selection reachability (the "Recurrence cannot be selected" defect)
- **Session**: `glistening-bouncing-biscuit`
- **Predecessor**: [`HANDOFF_2026-09-07_canopy-selection-deadlock-fixed-generator-gap-open.md`](HANDOFF_2026-09-07_canopy-selection-deadlock-fixed-generator-gap-open.md) — its items 1 and 2 are closed here; items 3–10 are carried forward unchanged below
- **Design of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) — §4.9 now carries a dated correction; **§12 is unchanged and is the next phase**
- **Consensus validation**: [`notes/JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md`](../../notes/JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md) — §7 item 2 now carries the same correction

---

## Goal statement

Continue the juniper-canopy selection-reachability arc. `(recurrence, equities_seq)` is now
**selectable, honestly gated, and stageable**. It has still **never been trained end to end**. The
next phase is §12 of the design (the generator gap), which the owner ruled equally critical; its
prerequisites are unchanged from the predecessor handoff and are restated below.

**Completed this session — three PRs, plus the record:**

- **canopy#601** (merged) — predecessor item 1, decision **N5**. Start was gated on the registry's
  lifecycle status plus both axes being set, never on whether the live backend serves the selected
  model, so with `recurrence_service_url` unset a "Recurrence" run executed on cascor/demo. Now one
  shared predicate, `model_registry.selection_is_live` (provider agreement, deliberately not
  `swapped`), is read by the sidebar summary, the Start gate and the server. A new
  `model-state-store` carries the `/api/model/select` payload, written by the **same callback** as
  `model-selection-store` (one writer). `POST /api/train/start`, the `/ws/control` start dispatch
  and `POST /api/train/restart` refuse an inactive selection with 409 and the reason; restart refuses
  **before** stopping the current run. conftest resets `main.current_nn_model` between tests.
- **canopy#607** (merged) — predecessor item 2, X6 / §4.9. `RecurrenceBackend`
  stages **in-process** (`stage_dataset` / `cancel_pending_dataset` / `get_pending_dataset`,
  `pending_dataset` on `get_status` for the banner) and `start_training` fits the staged config,
  translated by `dataset_ref_from_staged` (registry `default_params` seed the params; typed fields
  override; `nn_dataset_params` override both; the alias map is applied here, never on the
  cascor-bound payload). **A staged config takes precedence over the one-shot Start body**, which
  carries only registry defaults. `POST /api/stage_dataset` refuses an inactive selection with 409;
  Apply Dataset is disabled there alongside Start; the train-gate notice names both controls.
- **ml#1830** (merged) — `util/ad-hoc/push_signed_commit.py`, a signed follow-up commit on an
  **existing** PR branch (the thing `util/open_signed_pr.py` refuses by contract). It landed
  canopy#601's CI fix-up and its CHANGELOG re-seat. **A peer session shipped the same tool the
  same day** as `util/ad-hoc/append_signed_commit.py` (ml#1835; reads the head live instead of
  taking `--expected-head`). Two ad-hoc helpers now do one job; promote one into `util/` with a
  hermetic test and retire the other.
- The consensus doc's §7 item 2 and the design's §4.9 carry dated corrections (this PR).

**Remaining work, in the predecessor's order (its items 3–10, renumbered):**

1. **§12, iteration 2 — the generator gap.** The owner's stated primary goal. **Read §12 in full.**
   Prerequisites (summary only; §12.3 and §12.4 are the authority): **Y5 first** (the generators
   proxy sends no `X-API-Key` while `/v1/generators` is not auth-exempt, so every new seed renders
   "No adjustable parameters"); `csv_import` is **excluded**, not seeded (G10's exclusion list);
   `arc_agi`'s rank is unverified and its extra unlocked; **`mackey_glass` accepts a `seed` and
   ignores it** (`juniper_data/generators/mackey_glass/params.py:37`, consumed only inside
   `if init_noise_std > 0`, default `0.0`); every seed needs bounded `default_params` and **G11 as
   designed fails on the incumbents** (`spirals/xor/mnist/circles/moons` have `default_params={}`);
   G10 and G11 do not exist; the seedable delta is ≤ 9. **X8 must be settled before any seed
   sources `task_type` upstream** — see "Key context".
   **What this session changes for §12.4:** rank-3 seeds never touch cascor. A rank-3 dataset is
   compatible only with recurrence, and recurrence now stages in-process, so the "none of
   `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` is in cascor's `Literal`"
   concern in the predecessor is **moot** — and adding them to that `Literal` would be wrong for the
   same reason `equities_seq` was (below). The generate → stage → train → render loop for a rank-3
   seed is: select Recurrence, pick the seed, Apply Dataset (stages in-process), Start (fits the
   staged config).
2. **§4.10 dataset-axis hydration + G7** — unshipped. `dashboard_manager.py`'s `_selection_is_live`
   docstring still names it as the seed's honest source. The `pending_dataset` channel exists on
   all three backends now (recurrence included, this session) and `_init_params_from_backend_handler`
   is the natural host. G7 has **no test**. N10: hydration lands *before* `⊥`-at-mount.
3. **`⊥`-at-mount (OQ-N2)** — owner-accepted, still undeliverable as specified; see the predecessor's
   "Do not re-litigate" (unchanged: the `params-init-interval` snap, the seed line at
   `dashboard_manager.py` `value=DEFAULT_DATASET_TYPE`, the prospective two-writer problem).
4. **X10 / X11** — `RecurrenceBackend.initialize()` returns `True` unconditionally (a dead service
   still reports `backend="recurrence"`); first paint always reads "Active: CasCor". Note that N5's
   gate is exactly as health-blind as the label: `selection_is_live` compares provider to
   `backend_type`, and a recurrence backend whose service is down still counts as live.
5. **Y1 / Y2** — `main.py` calls `backend.get_experimental_functions` unguarded and
   `RecurrenceBackend` lacks it (500 on every page mount under recurrence); snapshot save/restore
   writes cascor meta and zero LMU state while reporting success.
6. **∥ packaging** — `equities` and any other extra a new seed needs into
   `juniper-data/requirements.lock`; `arc-agi` is also unlocked.
7. **§4.3 residue** — `dashboard_manager.py` still labels the model-driven snap
   *"(dataset-primary conflict policy, D5)"*; `aria-describedby` (Y7) never shipped.
8. **Record that OQ-6 is answered** — the dataset-primary policy is asserted in a docstring; the
   design still lists it as deferred.

---

## Key context

### Both of item 2's "cross-repo" fixes were wrong, and the correction is now in the record

- **cascor refuses 3-D artifacts by design.** `juniper-cascor/src/api/lifecycle/manager.py:3815`
  and `:3852`: *"3-D sequence artifacts belong to the juniper-recurrence tier, not
  cascade-correlation (W-2 tier boundary)"*. The `Literal` at `api/models/training.py:235` is the
  first of three bars, not a gap. Widening it moves the refusal from the request boundary to
  artifact load. **Never add a rank-3 generator to that `Literal`.** The only way canopy sent one
  there was the inactive-selection state; that state is now refused at Start and at staging.
- **The recurrence service has no staging concept because it does not need one.** It is one-shot;
  the dataset reference rides in `POST /v1/train` (`DatasetRef`: `dataset_id` / `name` /
  `generator` + `params`). "Staged for the next start" is a canopy-side fact, and `DemoMode`
  already held it in-process (`_pending_dataset_config`). Do not file a juniper-recurrence endpoint.
- **A staged config wins over the one-shot Start body.** The body is resolved from the dropdown
  value with `dataset_default_params` and knows nothing of what the operator edited and applied.
  Preferring it would silently discard an applied change while reporting success. Start consumes
  the staged config so the banner closes, mirroring cascor.

### X8 is still the trap it was

canopy labels `equities_seq` `task_type="regression"` (`src/model_registry.py`); juniper-data labels
it `"classification"`. `compatible()` tests `task_type in supported_task_types` and recurrence
declares `frozenset({"regression"})`, so **aligning canopy to upstream gives the LMU zero datasets**.
Inert today only because `GeneratorInfo` omits `task_type` from the wire.
`src/tests/regression/test_dataset_generator_contract.py` pins it. Settle before any §12 seed
sources `task_type` upstream.

### Do not re-litigate

- **`swapped is False` is the wrong "is this model active" predicate** (also False on the healthy
  re-select). Provider agreement, via `model_registry.selection_is_live`, is the one predicate now;
  do not add a second.
- **`None` is unknown, not disagreement**: first paint and a cleared model are not gated. Seeding the
  payload honestly is §4.10 hydration.
- The two independent cut vertices, the unreachable §4.3 repair notice, the asymmetric alias fix and
  the `⊥`-at-mount contradiction are all unchanged from the predecessor.

### Not established (carry forward)

**No training run has ever been started.** Nothing in this arc says the LMU can train on
`equities_seq` end to end; §12.4's "5× larger" framing stays OVERSTATED. The two fail-open layers
(a down juniper-data reports `equities_seq` available) are unchanged.

### Environment and traps (new this session; the predecessor's still apply)

- **This session could not sign commits.** The signing subkey is on a YubiKey that needs a touch
  (`gpg: signing failed: Timeout`). PRs went through `util/open_signed_pr.py` (whole-file upload,
  base main) and the CI fix-up through `util/ad-hoc/push_signed_commit.py` (`--expected-head`
  pinned). Re-check base freshness immediately before every upload
  (`git log HEAD..origin/main -- <paths>` must be empty). A peer session hit the same wall the same
  day: memory `reference_headless_commit_signing_hangs_use_api_commits.md`.
- **`tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py` pins callback Input ORDER
  and Output COUNT positionally** through `callback_map`. It is not found by grepping handler names,
  and it failed only in CI (3 of 6248) on #601. Run `tests/unit/frontend` whole before pushing any
  callback-shape change.
- `conda run -n JuniperCanopy1 python -m pytest …` (the unsuffixed env is deprecated). The
  repo's pytest config prints no `N passed` summary line under `-q`; judge a run by the absence of
  `FAILED`/`ERROR` and the trailing `[100%]`.
- The isolated stack (`util/isolated_stack.bash`) serves the **shared** `juniper-canopy/src`; pull
  it first and grep the served source for your symbol. `--with-recurrence` sets the service URL and
  therefore masks the inactive-selection state; a bare local canopy reproduces it.

---

## Verification commands

```bash
# 1. Both repos current
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy fetch origin && git -C /home/pcalnon/Development/python/Juniper/juniper-canopy log origin/main --oneline -4
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin && git log origin/main --oneline -3

# 2. The arc's guardrails, now including N5 and staging
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperCanopy1 python -m pytest \
  tests/regression/test_selection_reachability_guardrails.py \
  tests/regression/test_recurrence_staging.py \
  tests/regression/test_demo_mode_local_fallback.py \
  tests/regression/test_dataset_generator_contract.py \
  tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py -q -p no:cacheprovider

# 3. N5 — an inactive selection disables Start AND Apply (must print True True)
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from frontend.dashboard_manager import DashboardManager
st={'start':{'disabled':False,'loading':False,'timestamp':0}}
x1={'nn_model':'recurrence','backend':'demo','execution':'continuous','status':'live','swapped':False}
out=DashboardManager({})._update_button_appearance_handler(button_states=st, model_key='recurrence', dataset_value='equities_seq', model_state=x1)
print(out[0], out[-1])"

# 4. Staging — the next fit consumes the staged config (must print equities_seq {'max_symbols': 2, 'regression_target': 'return'})
conda run -n JuniperCanopy1 python -c "
import sys, time; sys.path.insert(0,'.')
from backend.recurrence_backend import RecurrenceBackend
from backend.recurrence_service_adapter import RecurrenceTrainResult
class A:
    service_url='x'; calls=[]
    def train(self, **k): self.calls.append(k); return RecurrenceTrainResult(final_metrics={'mse':0.1}, n_epochs=1, stopped_reason='ok', dataset={})
b=RecurrenceBackend(A()); b.stage_dataset(nn_dataset_type='equities_seq', nn_dataset_params={'max_symbols':2}); b.start_training(reset=True)
time.sleep(0.2); c=b._adapter.calls[0]; print(c['generator'], c['params'])"

# 5. X8 still inert (must print 'regression')
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from model_registry import get_dataset_spec; print(get_dataset_spec('equities_seq').task_type)"
```

---

## Git status at handoff

- **juniper-canopy**: `origin/main` carries #601 and #607. This session's worktrees
  `worktrees/juniper-canopy--fix--n5-start-gate-backend-agreement--20260908-0648--eb05021d` and
  `worktrees/juniper-canopy--feature--recurrence-in-process-staging--20260908-0711--7939b48e` are
  removed once both PRs are confirmed MERGED. The `…--drop-full-family--…` and
  `…--val-split-gate--…` worktrees belong to **another session** — leave them.
- **juniper-ml**: this session worked from `.claude/worktrees/glistening-bouncing-biscuit` on
  `main`; ml#1830 carries the ad-hoc helper, and the PR carrying this handoff plus the two
  document corrections is named in the session's final report.
- **Merge approval** was granted by the owner for the PRs of this session and arc; it does **not**
  extend to a new arc, and it never extended to deploys or PyPI gates.
