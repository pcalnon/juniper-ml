# Handoff: canopy selection arc — the four owner rulings are made; implement X11, F2, F1, then X8

**Date**: 2026-09-24 · **Predecessor**:
`HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md` (same directory;
merged in juniper-ml#2058) · **Merge approval**: granted by the owner for this arc on 2026-09-23.

## Goal

Implement the four rulings the owner made on 2026-09-24, one PR stream each, in the order below. The order runs from
smallest and single-repo to the multi-repo change that needs a census first.

### The rulings (owner, 2026-09-24, answering the predecessor's four questions)

| item | ruling |
|---|---|
| **X11** | **Fix the wording.** When liveness is unknown, the summary says "Selected: CasCor · backend status unknown", never "Active". |
| **F2** | **Apply the edits after the fresh rebuild**, so that parameters edited in the restart modal survive Start fresh. |
| **F1** | **Fix the Start path.** Detect the width mismatch before Start and refuse with a message pointing at Start fresh. Stop serving the previous run's results under the new label. Cover `mnist`. The `equities` seed stays enabled. |
| **X8** | **Change juniper-data's label.** juniper-data relabels `equities_seq`; the owner's option read "regression, or both". |

F1 and F2 are recorded in §12.4 of `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`, in the
A-N2 note, by this handoff's own PR. X8 and X11 are not in that design; their record is this handoff chain.

### Completed before this handoff

- The predecessor's arc shipped. canopy #674 (`894a2cc7`), #675 (`0254a7ec`) and #677 (`9cdfcad4`) are merged, and
  so is juniper-ml #2058 (`95a6469c`, 2026-09-23T21:53Z, after four re-syncs by
  `util/ad-hoc/2026-09-22_shepherd_automerge.bash`). Every squash tree equals its PR head
  (`util/ad-hoc/2026-09-23_verify_squash_equals_pr_head.py`).
- The owner was told about the A-N2 agent's privacy slips. It printed `HF_TOKEN` and two PyPI tokens into its
  transcript, and sent the owner's email to sec.gov in a User-Agent header. Token rotation is the owner's call.

### Work, in order

1. **X11 (canopy only).**
   - `_model_summary_text` renders "Active" whenever `_selection_is_live` returns `None`. It should say "Active" only
     on `True`, and use the ruled wording on `None`.
   - `_hydrate_selection_handler`'s failure path returns `dash.no_update` for the summary. It should write the
     unknown-state text.
   - `_initial_model_summary` seeds "Active: CasCor" at first paint, before any read. That is the same unknown state.
   - Tests to update: `test_a_failed_read_falls_back_and_still_runs_the_first_paint_gate` asserts
     `summary is dash.no_update`. Grep `src/tests` for every test that pins "Active: CasCor".
   - It needs a CHANGELOG entry (a behaviour change) and a mutation check. Run the **full** CI unit lane before opening.
2. **F2 (canopy and probably cascor).**
   - canopy's `/api/train/restart` runs stop, then `start(start_fresh)` (`api_train_restart` in `src/main.py`). The
     run therefore starts immediately, and parameters applied after the restart land mid-run.
   - The fix is likely cascor-side: build the fresh network from the parameters currently applied, not from
     `create_simple_config`'s defaults (`_start_fresh_reset_locked`, then create-on-start). The alternative is that the
     restart carries the edits in.
   - Evidence: F2 in `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`. `/api/state` read
     8/60/40/32 before and 1e6/10000/400/10 after.
   - Merge cascor before canopy.
3. **F1 (cascor, then canopy).**
   - On a refused Start, cascor reloads the staged dataset ("Reloaded dataset 'equities'") **before**
     `_pad_dataset_for_network` refuses it (409). The label has already moved while the network and metrics are still
     the previous run's.
   - The capacity check has to happen before the reload is committed. Canopy then surfaces the 409 with a pointer to
     Start fresh.
   - Tests should cover `equities` (15 features) and `mnist` (784). Evidence: F1 in the same README.
4. **X8 (juniper-data first, then its consumers). Census before any edit.**
   - `juniper_data/core/meta.py` dispatches on `task_type`: only classification populates the class distribution. So
     relabelling changes `equities_seq`'s emitted meta.
   - Per the data contract, changed output needs a **`generator_version` bump** (the equities pair is at 5.0.0). The
     allow-list in `juniper_data/tests/unit/test_val_emission_guards.py` names the pair.
   - juniper-recurrence reads `task_type` in `juniper-recurrence-model/.../model.py`, `routers/crossval.py`,
     `schemas.py` and `bench/baselines.py`, so a relabel can change its behaviour.
   - Census every repo, juniper-recurrence included. The decision-11 lesson: a repo missing from the ecosystem map is
     missing from every sweep.
   - Then choose `regression` or a dual form, and ask the owner if the census makes "both" cheap.
   - Canopy then flips `TestX8TaskTypeDivergenceIsDeliberate` (`src/tests/regression/test_dataset_generator_contract.py`)
     to assert agreement.
   - A juniper-data release is owner-gated.
5. **Cleanup**, only on an explicit per-PR merge signal. The list is in the predecessor, § Remaining work item 3. Add
   #677's worktree and `…--verify--m1-m6-mutations--…` to it.
6. **Carry forward:**
   - the peer claims on Y2 and X10 lapse 2026-09-29T00:00Z;
   - item 19, a juniper-data release that contains #421;
   - Y7's dropdown half;
   - the A-N2 observations O2–O5 (predecessor, item 4).

### Traps

- **The peer's isolated stack is on 8101/8202/8051.** `util/isolated_stack.bash` defaults to those ports, so use a
  wrapper that refuses them (`util/ad-hoc/2026-09-23_a_n2_stack.bash`).
- **Refactors can break source-window tests** anywhere in canopy, so run the full lane: repo root,
  `src/tests/{unit,regression,contract,performance}/`, `--timeout=60`, `LIBTORCH= LD_LIBRARY_PATH=`.
- **Agent briefs** must forbid printing env/secrets and sending the owner's email anywhere.
- **Signed API commits upload bytes.** An `*.png` is committed as its LFS pointer
  (`util/ad-hoc/2026-09-23_lfs_pointers_for_api_commit.py`).
- **`gh run watch` returns at once on a re-run attempt.** Use `util/wait_for_checks.py`.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git fetch origin --quiet && git log --oneline -4 origin/main
gh pr list --repo pcalnon/juniper-canopy --state open --json number,title --jq '.[] | "\(.number) \(.title[0:70])"'
git -C /home/pcalnon/Development/python/Juniper/juniper-data grep -n '"equities_seq"' -A6 origin/main -- juniper_data/api/routes/generators.py | grep task_type
ss -ltnp | grep -E ':(8101|8202|8051) '   # the peer's stack; do not touch
```

## Git state at handoff

- juniper-ml worktree `.claude/worktrees/bright-crunching-alpaca`, branch `worktree-bright-crunching-alpaca` at
  `51993b37`. Its untracked files are byte-identical to what #2058 merged. This handoff's PR carries this file and
  the design doc's two ruling notes.
- canopy: no open PRs from this arc.

## Documents

- **Referenced:**
  - the predecessor handoff (named above);
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.
- **Changed:** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (§12.4, the F1 and F2
  rulings).
- **Created:** this file.
