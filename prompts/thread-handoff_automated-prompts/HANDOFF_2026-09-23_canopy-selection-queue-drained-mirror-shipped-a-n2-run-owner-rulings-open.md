# Handoff: canopy selection arc — queue drained, the mirror shipped, A-N2 run; four owner rulings open

**Date**: 2026-09-23 · **Predecessor**: `HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md`
(same directory; its remaining-work items are cited here as P1–P7) · **Merge approval**: granted by the owner for this
arc on 2026-09-23.

## Goal

Continue the canopy selection-reachability arc:
1. Get the four owner rulings below and act on them.
2. Triage the A-N2 findings F1 and F2.
3. Clean up this arc's worktrees, but only on an explicit merge signal.

### Completed this session

| PR | merged (UTC) | what |
|---|---|---|
| canopy#668, #669, #667, #672, #671, #673 | 13:19–16:06 | P1, the predecessor's queue. Every squash tree equals its PR head (`util/ad-hoc/2026-09-23_verify_squash_equals_pr_head.py`). #667's three `Allow-Symbol-Loss:` waivers reached main. |
| canopy#674 (`894a2cc7`) | 19:47 | P2. The live swap sent the spiral fields for every generator and dropped a seeded generator's params. It now shares Apply Dataset's builder, `_dataset_stage_payload`. The FR9 `nn_model` mirror is on the live swap and on the restart modal's re-stage and parameter apply. |
| canopy#675 (`0254a7ec`) | 20:06 | P3. `TestX2RestartModalIsGatedAgainstTheSelectedModel`, plus the three comments #662 and #667 made false. |
| canopy#677 | open, armed | Four older stale comments. The LMU's empty dataset set is no longer the container's normal state; yfinance is only on juniper-data main; six cascor seeds carry `{}`, not seven. |

- **Before #674 opened**, one test failed in the **full** CI unit lane:
  `test_dashboard_manager.py::TestDatasetApplyNumericCommit::test_apply_dataset_always_sends_dataset_type`, a
  source-window test. The predecessor's 7-module run had missed it. It was fixed inside #674.
- **§4.5 had no test.** The ship map's M6 regates the modal against the default model; with it applied, canopy's whole
  CI unit lane passed with 0 failures. #675's class fails twice under it. **M1** was reproduced as well: reverting the
  ✕ fails only `test_g2_either_clear_alone_opens_the_graph[withheld1]`.
- **P4.** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` is reconciled from
  `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`. It now has a status line under each §4.x, §5 and
  §7 marked shipped, a dated correction under each contradicted line with the original text kept, and an A-N2 record
  under §12.4. The ship map's archivist notes record the four places where the map itself was wrong or out of date.
- **P5 (item 18, A-N2)** was run. Evidence: `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`.
- **canopy#368** got a scoped status comment: the mirror clause is complete.
- **X11 was re-derived** (item 3 of the ruling list below).
- **The older item 6**, the signed-commit drivers, is closed as far as it can be. It was promoted in juniper-ml#2036,
  and retiring the ad-hoc copies needs an owner decision under the retention policy.

### Remaining work, in order

1. **Owner rulings.** Ask them first; they were put to the owner at the end of this session.
   1. **X8 + A-N9.**
      - juniper-data declares `equities_seq` `task_type="classification"`; canopy labels it `regression`.
        `TestX8TaskTypeDivergenceIsDeliberate` pins that relabelling leaves the LMU **zero** datasets.
      - The divergence is still inert: `GeneratorInfo` (juniper-data `core/models.py`) carries no `task_type`.
      - Options: keep the recorded divergence; a dual-target vocabulary (a set of task types); or change juniper-data's
        declaration.
      - A-N9: no `ModelSpec` accepts `structured`, and seeding such a generator now fails
        `test_every_seeded_dataset_has_a_compatible_model` rather than greying out. `arc_agi` stays unseeded.
   2. **X11, or whether to fix it.**
      - After a failed mount read, `_hydrate_selection_handler` leaves the summary at its seed, and
        `_model_summary_text` renders "Active: CasCor" whenever `_selection_is_live` is `None`.
      - That contradicts its own docstring ("only when the live backend actually serves the selection").
      - The proposed fix is to say "Selected: … · backend status unknown" when liveness is unknown. It changes UI
        wording, which is why it is asked first.
   3. **F1, `equities` Start.** Start returns 409 when the live CasCor network is narrower than the dataset, with the
      message `dataset (15, 2) exceeds network capacity (2, 2)`.
      - After the refusal, cascor has already switched its loaded dataset, and the routes serve the previous run's
        results under an `equities` label.
      - `mnist` (784 features) should hit the same refusal; it was not run.
      - §12.4's rule says "seed disabled with a reason". The alternatives are fixing Start or pointing the operator at
        Start fresh.
   4. **F2, Start fresh discards parameters applied just before it.**
      - The restart modal applies edited params and then restarts. With Start fresh, cascor rebuilds at its defaults.
      - The README records `/api/state` before and after: 8/60/40/32 became 1e6/10000/400/10.
      - Confirm it is a defect, and the fix's direction: apply after the fresh rebuild, or refuse the combination.
2. **Implement the rulings.** F1's misattribution — results served under the wrong dataset's label — is the class this
   arc exists to remove, whatever is decided about the seed.
3. **Clean up only on an explicit merge signal** for each PR. Follow
   `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`, and **never**
   `util/remove_stale_worktrees.bash`. Under `/home/pcalnon/Development/python/Juniper/worktrees/`:
   - canopy, merged-PR branches: `…--feat--selection-hydration-both-axes--…`, `…--feat--selection-bottom-at-mount--…`
     (#666, closed), `…--fix--registry-record-repairs--…`, `…--fix--test-timing-flakes--…`,
     `…--fix--selection-ui-y4-y7-y8--…`, `…--fix--restart-restage-seed--…`, `…--feat--request-nn-model-mirror--…`,
     `…--fix--e2e-test-three-partition-contract--…`, `…--fix--fixed-sleep-lower-bounds-followup--…`,
     `…--feat--nn-model-mirror-restart-and-live-swap-v2--…` (#674),
     `…--fix--selection-stale-comments-and-restart-regate-test--…` (#675), and
     `…--fix--stale-availability-and-seed-count-comments--…` (#677, once merged).
   - canopy, local-only and superseded: `…--feat--nn-model-mirror-restart-and-live-swap--20260923-0125--7950bf9e`. Its
     staged diff went out as #674, and its local base `d16a26ae` was never pushed.
   - Detached verify worktrees: canopy `…--verify--m1-m6-mutations--…`, `…--verify--main-ui-baseline--…` and
     `…--verify--pr671-codeql--…`; `…--verify--a-n2-loop--…` in canopy, cascor and data. The cascor one holds 142 MB of
     ignored logs.
   - cascor: `…--feat--status-current-dataset--…` (#676).
   - juniper-ml: `.claude/worktrees/jazzy-soaring-minsky`, the predecessor's.
4. **Optional: register the A-N2 observations** with the peer session that owns the canopy E2E findings register. O1,
   the status-bar lag, is F-CANOPY-055, already filed. O2 through O5 are unregistered:
   - O2: the Classification Metrics chart's x-axis mixes phase counters;
   - O3: the `applied` list from `/api/set_params` omits the keys sent over WebSocket;
   - O4: `/v1/health` `version` comes from stale install metadata;
   - O5: `/api/network/stats` returns 503 under the recurrence backend.
5. **Carry forward, unchanged:**
   - The peer `canopy` claims on Y2 waves 2/3 and X10 lapse 2026-09-29T00:00Z, on the predecessor's terms.
   - Item 19, a juniper-data release that contains #421, is the owner's call. v0.15.0 lacks it.
   - Y7's dropdown half is still open: no `aria-disabled` on greyed options, and the design never specified a fix.

### Key context

- **A-N2 results.**
  - Seven of the eight §12 seeds, plus both controls, complete generate → stage → train → render through canopy's
    Start. The exception is `equities` (F1).
  - The stack ran data, cascor and canopy from worktrees at `origin/main`, with each leg's `git_sha` and imports
    proven. The recurrence leg was the installed console script, with juniper-recurrence-model **0.1.5**, not the
    released 0.3.x line.
  - The subagent that ran it sent the owner's email address to sec.gov in a User-Agent header during a connectivity
    check, and printed `HF_TOKEN` plus two PyPI tokens into its own transcript. The owner was told. The committed
    evidence was scanned: it contains no tokens and no email address.
- **LFS through the signed API.** `*.png` in juniper-ml is LFS-tracked, and `createCommitOnBranch` commits the bytes it
  is given. So `util/ad-hoc/2026-09-23_lfs_pointers_for_api_commit.py` stores each image and writes its pointer, then
  `git lfs push --object-id origin <oids>` uploads the objects, and the commit carries the pointers.
- **canopy UI flake.** `test_ws_silent_poll_liveness.py::test_metrics_store_polls_on_long_lived_tab_with_ws_silent`
  failed once on #674: the demo run converged mid-window. It passed on a failed-jobs re-run. Main's UI job was green.

### Traps

- **Stack.** The peer's isolated stack still runs on 8101/8202/8051 (pids 2856834 / 2857489 / 2858037, confirmed at
  20:07Z). `util/isolated_stack.bash` defaults to exactly those ports, so a bare `--down` kills it. Use a wrapper that
  refuses the defaults, such as `util/ad-hoc/2026-09-23_a_n2_stack.bash`.
- **Command shapes.**
  - This session refused loops that contain `gh`/`git`.
  - `gh run watch` returned at once on a re-run attempt; use `util/wait_for_checks.py`.
  - gh 2.46.0's `gh pr checks` has no `--json`.
- **Refactor PRs need the full canopy unit lane**, not the modules you think are affected. Source-window tests read
  `dashboard_manager.py` text.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git fetch origin --quiet && git log --oneline -6 origin/main
gh pr view 677 --repo pcalnon/juniper-canopy --json state,mergedAt
gh pr list --repo pcalnon/juniper-ml --state all --limit 5 --search "canopy selection" --json number,state,title
ss -ltnp | grep -E ':(8101|8202|8051) '   # the peer's stack; do not touch
```

## Git state at handoff

- juniper-ml: worktree `.claude/worktrees/bright-crunching-alpaca` (branch `worktree-bright-crunching-alpaca`, at
  `51993b37`). This handoff's own PR carries every new file.
- canopy: nothing uncommitted that matters. The mirror v1 worktree still holds its staged diff, superseded by #674.

## Documents

- **Referenced:**
  - the predecessor handoff (named above);
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (§5.6.1 point 4);
  - `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`;
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.
- **Changed:**
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md`.
- **Created:**
  - this file;
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/` (409 files; 13 PNGs as LFS pointers);
  - `util/ad-hoc/2026-09-23_{verify_squash_equals_pr_head,explore_start_probe_test,mutation_check_m1_m6,count_seeds_by_default_params,lfs_pointers_for_api_commit}.py`;
  - `util/ad-hoc/2026-09-23_a_n2_{stack.bash,drive.py,screenshot.py,run_batch.bash}`.
