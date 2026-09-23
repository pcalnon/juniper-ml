# Handoff: canopy selection arc — six PRs queued, the live-swap / restart mirror staged

**Date**: 2026-09-23 · **Predecessor**: `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md`
(same directory; items 1–23 below are its numbering) · **Merge approval**: granted by the owner for this arc.

## Goal

Continue the canopy selection-reachability arc: drain the merge queue, open the staged live-swap / restart
mirror PR, fix the comments #667 leaves stale, reconcile the design document from the archived ship map,
and run item 18.

### Completed so far

| PR | merged (UTC) | what |
|---|---|---|
| juniper-cascor#676 | 09-23 | the status payload carries `current_dataset`: `None` / `{"dataset_type": None}` / the config it was loaded from |
| juniper-canopy#662 (`2f973ca2`) | 02:18 | design PR 2: mount hydration on **both** axes, `GET /api/selection`, G7 + Y3 |
| juniper-ml#2037 (`91da4b0e`) | 05:47 | design docs; the **item-22 owner ruling**: the restart modal keeps its `enabled[0]` swap as a recorded OQ-6 exception (§5.6.1 point 4 of `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`) |
| juniper-canopy#665 (`7950bf9e`) | 06:17 | registry repairs, items 7, 10, 11, 12, 14 (G11 over every seed; equities re-measured at 5.0.0) |
| juniper-ml#2036 (`afcd9e2d`) | 06:21 | `util/push_signed_commit.py`: a pinned signed commit onto an existing branch |
| juniper-canopy#664 (`39ee09f8`) | 06:54 | WS connect-ordering test; three loop tests poll instead of timing the runner |

**Item 19** (owner ruled "add the equities extra"): juniper-data#421 merged 00:56Z (`68c3cd7c`). **No release
contains it**: v0.15.0 lacks yfinance, and juniper-ml#2033 floors the meta-package at `>=0.15.0`. A juniper-data
release is the owner's call (deploys are owner-approved).

### Remaining work, in order

1. **Drain the queue.** canopy strict checks; native auto-merge is **armed on all of these**. Sync ONE at a time with
   `gh api -X PUT repos/pcalnon/juniper-canopy/pulls/N/update-branch` after each merge. Order and state at 13:05Z:
   **#668** (restart re-stage seed; synced, CI running) → **#669** (FR9 `nn_model` mirror) → **#667** (item 2,
   ⊥-at-mount; three `Allow-Symbol-Loss:` trailers in its commit body) → **#671** (Y4 / Y8 / the model-table half
   of Y7) → **#672** (e2e contract helper, test-only) → **#673** (fixed-sleep follow-up, test-only). All six were
   `merge-tree`-clean against `cc3588a8`. juniper-ml **#2039** (the script-retention bundle) is armed and synced;
   that lane is contended, so re-sync when it goes BEHIND. After each merge, verify `git diff <pr-head> <squash>`
   is empty.
2. **Open the staged mirror PR once #668 AND #669 are on main** (details under Key context).
3. **After #667 merges**, one small canopy comments PR:
   - `src/tests/regression/test_selection_reachability_guardrails.py::_explore`: its comment says
     `params-init-interval` fires the gate at mount (false since #662, which moved that Input to `select_model`);
     its default start `(DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)` no longer matches a ⊥/hydrated mount; and the
     ship map flags the G1a helper docstring (~:186).
   - `src/frontend/dashboard_manager.py`, the `resolve_oneshot_start_body` wiring comment: "…tracks model swaps
     and dataset **snaps**". No open PR fixes it.
4. **Reconcile** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` from
   `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`:
   - §7: SHIPPED on PR 1/3/4/5, and ∥ as merged-not-released;
   - a status line per §4.x;
   - the ~30 contradicted lines in its §2;
   - the queue PRs as they merge.

   Re-derive line numbers, which drift. Confirm M6 ("§4.5 has no test") before stating it.
5. **Item 18 (A-N2)**: generate → stage → train → render, through canopy, once per §12-seeded generator. It has
   never been run; see the traps for the stack.
6. **Ask the owner: item 15 (X8)**, and A-N9 with it. juniper-data's `equities_seq` emits **both** `y`
   (one-hot next-day direction) and `y_reg` (the regression target), and declares `task_type="classification"`
   (`juniper_data/api/routes/generators.py`). canopy labels it `regression`. Relabelling leaves the LMU **zero**
   datasets (pinned by `TestX8TaskTypeDivergenceIsDeliberate`). Options:
   - keep the recorded divergence;
   - a dual-target vocabulary (a set of task types);
   - change juniper-data's declaration.

   A-N9: `structured` matches no model.
7. **Clean up** worktrees only on an explicit merge signal: agents' E/S/UI worktrees, mine for
   662/664–673, the detached `…verify--main-ui-baseline--20260923-0045--2f973ca2`, and cascor's #676 one.
   Follow `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`, and **never** `util/remove_stale_worktrees.bash`.

### Key context

- **The staged mirror PR.**
  - Worktree: `worktrees/juniper-canopy--feat--nn-model-mirror-restart-and-live-swap--20260923-0125--7950bf9e`.
  - Its base is the LOCAL merge commit `d16a26ae` (#668 + #669 branches onto `7950bf9e`). **Never push it.** The
    change is `git diff d16a26ae` (`dashboard_manager.py` +63/−36, `test_dashboard_manager_gate_coverage_inner2.py`)
    plus the untracked `src/tests/regression/test_staging_paths_send_one_payload.py`.
  - **The finding.** The live swap sent the four typed SPIRAL fields for every generator and never
    `nn_dataset_params`, so `equities` lost `symbols` and `mnist` lost `flatten`. That is #668's defect on a third
    staging path, probed with the real handlers (`util/ad-hoc/2026-09-23_live_swap_payload_probe.py`).
  - **The fix.**
    - One static builder, `_dataset_stage_payload`, used by Apply Dataset and the live swap.
    - The live-swap callback reads the gen-param States and `model-selection-store`.
    - `execute_restart` reads the store; `_restage_dataset` and the restart's `_apply_params_via_backend` send
      `nn_model`.
  - **Verified.**
    - 391 passed across the 7 affected modules.
    - Mutation check (`util/ad-hoc/2026-09-23_mutation_check_staging_paths.py`): **6/6 killed**, including N2, the
      builder losing the seed on BOTH paths, which parity alone cannot see.
  - **To open.**
    - Re-apply onto fresh main.
    - Re-test.
    - A CHANGELOG entry, and **amend #669's sub-bullet** ("The restart modal and the live-swap … do not yet"),
      which this makes false.
    - `open_signed_pr.py`, then arm.
    - State the limitation: `/api/train/restart` carries no model identity.
- **Canopy test-only PRs carry no CHANGELOG entry** (#641 / #649 / #654 precedent).
- **The peer session `canopy`** holds wave 3 (canopy's snapshot sites) and X10 under § B lapse terms. Its
  re-probe at `2f973ca2`:
  - Y2 is unchanged.
  - Under `RecurrenceBackend`, save answers 201 with an **empty `training_state`** group, restore 404, and
    replay/resume/retrain 501.
  - X11 is still OPEN (`_initial_model_summary` passes no backend); re-derive it under item 3 after #667.
  - A hydration check that inspects only `init_params_from_backend` reads OPEN after #662 shipped it. Include
    `GET /api/selection` and `select_model`'s `params-init-interval` Input.

## Corrections to the predecessor (R6 round, peer `canopy`; the squash messages cannot be amended)

- **MJ1.** Item 6's signed-commit taxonomy was stale at its own base; **re-derive at current origin/main**.
  - Classify driver vs opener by where `expectedHeadOid` comes from (the target branch vs the base sha).
  - There were five own-mutation existing-branch drivers, including the hybrid
    `util/ad-hoc/2026-09-22_push_signed_commit.py`, plus `util/push_signed_commit.py` since #2036.
- **MJ2.** "Never inherited" is false. "Items 1–3 are one PR-sequence…" is verbatim in `a2e63d1d` (#2014). The
  lesson is: **re-read every scoping statement the change relies on, changed OR inherited.**
- **MJ3.** There are **six** service-only snapshot predicates:
  - `_backend_snapshot_inventory`;
  - `_backend_snapshot_detail`;
  - `create_snapshot`;
  - `restore_snapshot` ×2;
  - `_require_service_adapter`.

  **Five are in scope.** `_require_service_adapter` keeps its 501 under PERSISTENCE-DESIGN §9.
  `SNAPSHOT_EXTENSIONS = (".h5", ".hdf5")` also means a recurrence `.npz` can never be listed.
- **Peer figures.**
  - The insertion in the 09-08 addendum is **~130 lines**, not 91.
  - "cascor-shaped meta" overstates the save result: it is an **empty `training_state` group** with no
    parameters.
- **M1–M9, in short.**
  - M1: the "why 3b" citations omit items 18, 20 and 23.
  - M2: N5(a) survives in item 20.
  - M3: the order note's reason was wrong (the PR plan, `…REACHABILITY-DESIGN.md` OQ-N2 "(PR 2)"); that line
    is OQ-N2, not D-N10.
  - M4: § A's heading still says "one sequence".
  - M5: the document was pinned to canopy `9bffaba1`, with drifted line numbers.
  - M6: the G7 and Y3 finders have false negatives (the grep is case-sensitive, and it misses hyphenated Dash ids).
  - M8: "never a widened predicate" contradicts PERSISTENCE-DESIGN §8.3 / §11.4.
  - M9: "expect 2 references" returns 1.

## Traps

- **Stack.** An isolated stack is **already running** on 8101/8202/8051 (pids 2856834 / 2857489 / 2858037,
  launched from the PRIMARY cascor and canopy checkouts). It is not ours: do not touch it, and do not move the
  primaries while it imports them.
  - For item 18, set `JUNIPER_E2E_{DATA,CASCOR,CANOPY,RECURRENCE}_PORT`, `JUNIPER_E2E_RUN_DIR`, and
    `JUNIPER_E2E_PROJECT_DIR` pointing at worktrees.
  - Then run `util/isolated_stack.bash --up --with-recurrence`.
- **Canopy tests.**
  - Run `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python -m pytest …` from `src/`.
  - CI's unit scope is `tests/unit/ tests/regression/ -m "not requires_cascor and not requires_server and not slow"`.
  - `JuniperCanopy1` has an editable install of the PRIMARY canopy checkout, so probes must put the worktree
    first on `sys.path` and print `__file__`.
- **Signed commits.**
  - `python3 util/open_signed_pr.py` uploads whole files. Run `git log <base>..origin/main -- <paths>` first.
  - Existing branch: `util/push_signed_commit.py --expected-head <sha>`.
  - Symbol-loss screen, in the canopy primary (fetch only):
    `/opt/miniforge3/envs/JuniperCascor1/bin/juniper-symbol-loss-check --scope 'src/**/*.py' --base origin/main --head origin/<branch>`.
- **Queue watcher.** `util/ad-hoc/2026-09-23_watch_pr_states.bash <repo>:<pr> …` as a `Monitor` source. It is
  report-only; `unknown` after a merge is a transient recompute.
- **markdownlint auto-fix** turns a line starting `#671` into an H1. Never start a markdown line with `#NNN`.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git fetch origin --quiet && git log --oneline -8 origin/main
gh pr list --repo pcalnon/juniper-canopy --state all --limit 14 --json number,state,mergeStateStatus,autoMergeRequest --jq '.[] | select(.number>=664) | "\(.number) \(.state) \(.mergeStateStatus) auto=\(.autoMergeRequest != null)"'
gh pr view 2039 --repo pcalnon/juniper-ml --json state,mergeStateStatus
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--feat--nn-model-mirror-restart-and-live-swap--20260923-0125--7950bf9e status --short   # expect 2 M + 1 ??
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--feat--nn-model-mirror-restart-and-live-swap--20260923-0125--7950bf9e diff --stat d16a26ae
```

## Git state at handoff

- juniper-ml worktree `.claude/worktrees/jazzy-soaring-minsky`, branch `worktree-jazzy-soaring-minsky`, at `91da4b0e`.
- Its untracked files are the #2039 bundle, plus the files this handoff's own PR carries:
  - this handoff and `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`;
  - four scripts: `util/ad-hoc/2026-09-23_{demo_first_unit_latency,fixed_sleep_followup_checks,live_swap_payload_probe,mutation_check_staging_paths}.py`.
- The staged canopy change is uncommitted in the mirror worktree, as above.

## Documents

- **Referenced:**
  - the predecessor handoff (named above);
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`;
  - `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.
- **Created this session:**
  - this file;
  - `SHIP_MAP.md`;
  - `util/ad-hoc/2026-09-22_canopy-selection-arc/` (27 files, in #2039);
  - `util/ad-hoc/2026-09-23_watch_pr_states.bash` and `…_mutation_check_e2e_contract_helper.py` (in #2039);
  - the four scripts listed under Git state.
