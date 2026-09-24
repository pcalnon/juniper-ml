# Handoff: canopy selection arc — the four rulings shipped; cleanup and carry-forwards remain

**Date**: 2026-09-24 · **Predecessor**:
`HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md` (same directory; its work
items are cited here as W1–W6) · **Merge approval**: granted by the owner for this arc in this session (2026-09-24).

## Goal

The four owner rulings of 2026-09-24 are implemented and merged. What remains:
1. Clean up this arc's worktrees, but only on an explicit merge signal for each PR (W5).
2. Carry the open items forward (W6).

### Completed this session

| item | PR | merged (UTC) | what |
|---|---|---|---|
| X11 (W1) | canopy#680 (`5907713b`) | 09:08 | Unknown liveness reads "Selected: … · backend status unknown", never "Active". The failed mount read writes that text, and so does the first-paint seed. |
| F2 (W2) | cascor#685 (`d9220103`) | 09:10 | A start-fresh captures the discarded network's applied params and re-applies them to the rebuilt network. |
| X8 (W4) | juniper-data#437 (`1afc3484`) | 09:14 | `equities_seq` is declared `regression` at generator **6.0.0**. Flat `equities` stays `classification` at 5.0.0. |
| F1 (W3) | cascor#687 (`ec8b5bdb`) | 09:46 | A Start that continues the network refuses a wider staged dataset **before binding**, with the marker `[start_fresh_required]`. |
| F1 + F2, canopy half | canopy#681 (`f0401830`) | 09:53 | The refusal alert names "Stop & Restart with new dataset" and "Start fresh". The modal says the parameters carry over. |
| X8, canopy half | canopy#682 (`14a0e4c7`) | 10:09 | `TestX8TaskTypeDivergenceIsDeliberate` became `TestX8TaskTypeAgreesWithJuniperData`. Five `Allow-Symbol-Loss:` waivers reached main: the post-merge screen reports `WAIVED: 5`. |

- **Evidence for every PR:**
  - the **full** unit lane of its repo, run locally before opening;
  - pre-commit;
  - a **mutation check** with no survivors: `util/ad-hoc/2026-09-24_{x11,f2_start_fresh,f1_wider_dataset,x8_task_type}_mutation_check.py`.
- **Squash tree equals PR head** for canopy#680, #681 and #682, cascor#685 and #687, and juniper-data#437
  (`util/ad-hoc/2026-09-23_verify_squash_equals_pr_head.py`).
- **Two merges needed a second pass:**
  - cascor#687 went BLOCKED with 24/24 checks green, because CodeQL left a review thread on an unused `import torch`
    in the new test. A follow-up signed commit removed it, and the thread auto-resolved.
  - canopy#682 hit the known X7 wall-clock flake (`test_initialize_sync_does_not_block_the_loop`, 6,900 passed,
    1 failed), so its failed jobs were re-run. It then went BEHIND under `strict` when #681 merged, and was
    `update-branch`ed with its net armed.
- **The design doc** (`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §12.4) now carries a
  "Shipped, 2026-09-24" note under both the F1 ruling and the F2 ruling.

### Key context (decisions and discoveries)

- **X8: `regression` was chosen, not a dual form. The owner was not re-asked** (W4 said to ask only if "both" was
  cheap). A census of every repo, including juniper-slacker, which the ecosystem map omits, found no consumer that
  breaks under either option. "Both" would need:
  - a vocabulary constant;
  - a `meta.py` dispatch change, without which "dual" behaves exactly like regression;
  - a canopy predicate change;
  - possibly a Postgres column-type change.
- **W4's premise was wrong.** juniper-recurrence never reads juniper-data's `task_type`. Its model, crossval and bench
  use the model's own label, and targets are picked by NPZ key (`y_reg_*`).
- **Why 6.0.0:** the relabel nulls `n_classes` / `class_distribution` in the stored meta, the dataset ID hashes the
  version but not the meta, and a cache hit serves the stored meta as-is. That is the arc_agi #402 → #427 precedent.
- **X8 ships in juniper-data 0.16.0**, because the 0.16.0 Release (not yet cut) tags main HEAD. Its CHANGELOG entry is
  under `[0.16.0]`, following #435's precedent.
  - The ecosystem guide's data-contract paragraph (`Juniper/CLAUDE.md`, unversioned) was updated to say `equities_seq`
    is at 6.0.0 on main.
  - When 0.16.0 is published, update it again to "on PyPI since 0.16.0".
- **F2 was fixed in cascor alone.** Canopy's order (apply the edits, then restart) was already right. canopy's demo
  backend keeps its params across a reset, so it never had the defect. Mutation evidence: **no pre-existing test** in
  cascor `src/tests/unit/api/` covered what a start-fresh does to params.
- **F1 was also fixed in cascor**, via `_reload_dataset(refuse_wider_than=…)`.
  - Inline `X` is deliberately unchanged: it still binds and then refuses, under the 2026-09-23 "follow the loaded
    data" ruling.
  - The marker is named `*_MARKER`, because bandit B105 flags `*_TOKEN`.
- **F1's visible aftermath, for the owner.** After a refused Start, canopy's sidebar title still reads the staged
  dataset ("Current Dataset — Equities"), because it follows the *selection*, which hydrates `pending` first. The
  routes are now honest (`current_dataset: checkerboard`, `pending_dataset: equities`), and the pending banner is
  up. It is the same state an Apply Dataset leaves.
  - Recorded as **O9**: whether "Current Dataset" should distinguish staged from loaded is a pre-existing U-6 design
    question, not F1.
- **A-N9** (from the 2026-09-23 handoff, attached to X8) was never put as a question. It stands as recorded:
  - no `ModelSpec` accepts `structured`;
  - seeding such a generator fails `test_every_seeded_dataset_has_a_compatible_model`;
  - `arc_agi` stays unseeded.

### Remaining work

1. **Cleanup (W5), only on an explicit per-PR merge signal.** Follow
   `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`, and **never** run
   `util/remove_stale_worktrees.bash`. The list:
   - **From the predecessors:**
     - the 2026-09-23 handoff's § Remaining work item 3 in full;
     - canopy `…--fix--stale-availability-and-seed-count-comments--…` (#677);
     - canopy `…--verify--m1-m6-mutations--…`;
     - juniper-ml `.claude/worktrees/bright-crunching-alpaca` (#2069).
   - **This session**, under `/home/pcalnon/Development/python/Juniper/worktrees/`:
     - `juniper-canopy--fix--selection-summary-unknown-liveness--20260924-0259--e9053227` (#680)
     - `juniper-cascor--fix--start-fresh-keeps-applied-params--20260924-0310--0e016a7c` (#685)
     - `juniper-data--fix--equities-seq-task-type-regression--20260924-0355--39d1cab2` (#437)
     - `juniper-cascor--fix--start-refuses-wider-dataset-before-binding--20260924-0355--33c965b3` (#687)
     - `juniper-canopy--fix--start-refusal-points-at-start-fresh--20260924-0356--1463f29a` (#681)
     - `juniper-canopy--test--x8-task-type-agrees-with-juniper-data--20260924-0401--6c4ad9a9` (#682). Its local
       branch holds an **unsigned, never-pushed probe commit** (made to run the symbol-loss screen), so it diverges
       from the remote branch. Use `git branch -D`.
     - juniper-ml `.claude/worktrees/tender-wibbling-flask` (this handoff's PR).
2. **Carry forward:**
   - The peer claims on Y2 waves 2/3 and X10 lapse **2026-09-29T00:00Z**.
   - **Item 19 is the owner's call**: cutting the juniper-data **0.16.0** Release. The release commit (#433) is merged
     and contains #421 and now #437 (X8). No `v0.16.0` tag or Release exists, and PyPI serves 0.15.0.
   - Y7's dropdown half: no `aria-disabled` on greyed options.
   - A-N2 observations: O2–O5 (2026-09-23 handoff, item 4), plus **O9** above.

### Traps

- **Whole-file signed uploads versus a moving `CHANGELOG.md`.** In all three repos, a publish-image fan-out (#679,
  #684, #436) landed a CHANGELOG entry mid-arc. The repair is `git merge-file <yours> <base> <main>`. When both
  sides inserted at the same point, `util/ad-hoc/2026-09-24_resolve_changelog_conflict_theirs_then_ours.py`
  resolves it with main's entry verbatim and yours below.
- **Mutation scripts edit the worktree in place.** Never upload from a worktree while one runs. Snapshot first, and
  scan the snapshot for the mutants' strings.
- **The peer's isolated stack is on 8101/8202/8051.** Do not touch it.
- **Commands this session's classifier refused:** `python3 - <<EOF` heredocs; a `jq` string containing `#`; a
  `git -C` redirect through a glob. Put the logic in a script file instead.

## Verification (run first)

```bash
gh pr list --repo pcalnon/juniper-canopy --state open --json number,title --jq '.[] | "\(.number) \(.title[0:70])"'
gh pr list --repo pcalnon/juniper-cascor --state open --json number,title --jq '.[] | "\(.number) \(.title[0:70])"'
gh release list --repo pcalnon/juniper-data --limit 2        # is 0.16.0 cut yet? (item 19)
git -C /home/pcalnon/Development/python/Juniper/juniper-data grep -n -A4 '"equities_seq": {' origin/main -- juniper_data/api/routes/generators.py | grep version
ss -ltnp | grep -E ':(8101|8202|8051) '   # the peer's stack; do not touch
```

Do not verify a squash commit's waiver with `git log --format='%(trailers:key=Allow-Symbol-Loss)'`. GitHub's squash
re-wraps the trailer block, so git reads 0 on canopy#682's `14a0e4c7`. The post-merge screen, which is what enforces
it, read `WAIVED: 5`.

## Documents

- **Referenced:**
  - the predecessor (named above);
  - `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md` (same
    directory);
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.
- **Changed:** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (§12.4, two "Shipped"
  notes). Also `Juniper/CLAUDE.md`, the unversioned ecosystem guide, whose data-contract `generator_version` bullet
  now names `equities_seq` at 6.0.0.
- **Created:**
  - this file;
  - `util/ad-hoc/2026-09-24_x11_mutation_check.py`;
  - `util/ad-hoc/2026-09-24_f2_start_fresh_mutation_check.py`;
  - `util/ad-hoc/2026-09-24_f1_wider_dataset_mutation_check.py`;
  - `util/ad-hoc/2026-09-24_x8_task_type_mutation_check.py`;
  - `util/ad-hoc/2026-09-24_resolve_changelog_conflict_theirs_then_ours.py`.
