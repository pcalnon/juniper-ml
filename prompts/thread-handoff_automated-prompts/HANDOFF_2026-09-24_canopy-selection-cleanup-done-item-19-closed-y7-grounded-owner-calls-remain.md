# Handoff: canopy selection arc — cleanup done, item 19 closed, Y7 grounded; the owner's calls remain

**Date**: 2026-09-24 · **Predecessor**:
`HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md` (same directory; its
work items are cited here as W5 and W6) · **Merge approval**: granted by the owner for this arc in this session
(2026-09-24).

## Goal

Nothing in this arc is left for an agent to implement. What remains:

- owner decisions;
- three worktree removals that only the owner can run;
- a date, 2026-09-29.

Start a successor thread only when one of the items under "Remaining" moves.

### Completed this session

- **W5, the cleanup, in canopy, cascor and data.**
  - **Result:** 26 worktrees removed and 20 local branches deleted. No remote branch existed to delete.
  - **Tool:** `util/ad-hoc/2026-09-24_canopy_arc_worktree_cleanup.py` (new). It re-checks every gate immediately
    before each removal:
    - **Standing.** A PR on the head reads MERGED on GitHub, live, or a detached tree's HEAD is on `origin/main` or
      on a PR. For a superseded tree, the superseding PR is merged: #666 → #667, and the mirror v1 → #674.
    - **Not in use.** No process has its cwd or an open file inside the tree.
    - **Content.** Every path the tree changed, whether committed, dirty or untracked, is identical to the squash's
      copy or `origin/main`'s, or is contained in one of them. "Contained" means a `git merge-file` of the tree's
      delta into that copy changes nothing.
  - **Most PR trees were dirty by construction.** A session that ships through signed API commits never commits
    locally, so the PR's content sits uncommitted in its tree. "Clean" was unreachable, and the content gate
    decided instead. A dirty tree was removed with `--force`, after its full diff was saved.
  - **Three trees needed a human read.** All three hold superseded drafts:
    - `selection-ui-y4-y7-y8` holds the pre-CodeQL versions of three files;
    - the mirror v1 holds two CHANGELOG lines that #674 made false, plus the draft #674 simplified to `dict(sent)`;
    - `selection-bottom-at-mount`'s 49 CHANGELOG lines are all on `main`; only their position differs.
  - **The harvest is 174 MB, in 25 directories**, under
    `/home/pcalnon/Development/python/Juniper/backups/worktree-harvest-2026-09-24-canopy-selection-arc/`. It holds
    the ignored `logs/` and `snapshots/` payload (148.5 MB of it is the cascor A-N2 tree's logs) and each dirty
    tree's `_uncommitted/` diff.
- **Phase 7 is deferred: no primary was fast-forwarded.** The peer's isolated stack holds all three primaries:
  - canopy: `:8051`, pid 2858037, cwd `juniper-canopy/src`;
  - cascor: `:8202`, pid 2857489, cwd `juniper-cascor/src`. `util/ad-hoc/cascor_freeze_tell.py` reports FREEZE IN
    FORCE;
  - data: a live cwd holder.
- **juniper-ml's three worktrees are verified; removing them is the owner's job.**
  - An isolated session may not run git against another worktree of its own repo. So
    `util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py` (new) reads their files and compares them with this
    worktree's object store instead.
  - `tender-wibbling-flask` holds nothing that is not on `main`.
  - The other two hold only superseded drafts:
    - `jazzy-soaring-minsky`: one SHIP_MAP line, "Nothing here has been applied to the design yet";
    - `bright-crunching-alpaca`: the design doc before #2069's and #2082's notes (every added line is on `main`, and
      every deleted line is gone from it), and `a_n2_drive.py` before its implicit-concat fix.
  - `util/ad-hoc/2026-09-02_worktree_inuse_probe.py` reported all three free.
  - No `worktree-*` branch exists on origin.
- **Item 19 is closed.** juniper-data 0.16.0 contains #421: `68c3cd7c` is an ancestor of `v0.16.0`. It is published:
  - GitHub Release, 08:52:14Z;
  - GHCR;
  - PyPI: the wheel at 18:35:40Z, the sdist at 18:35:42Z.
- **X8's CHANGELOG entry** reached juniper-data main's `[Unreleased]` through juniper-data#438 (`0f0f7e0e`,
  18:51:59Z).
  - That is the containers session's correction. Its own #439 was closed unmerged.
  - `main`'s `[0.16.0]` is byte-identical to the tag's.
  - `Juniper/CLAUDE.md` is the containers session's to edit.
- **The canopy E2E arc accepted O2–O5 and O9 for triage.** They are item 2 of its next thread
  (`HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`, on branch
  `docs/canopy-e2e-handoff-2026-09-24`).
  - O4 relates to OBS-1 (canopy#526), and O5 to the network-stats poller.
  - O9 may come back to this arc as the U-6 design question. Its triage will say.
- **Y7's dropdown half is grounded.** A dated note in §4.3 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` records what the source shows:
  - dash 4.2.0 renders `<label role="option" aria-selected>` around `<input disabled>`, and puts no `aria-disabled`
    on the option;
  - an option is `{label, value, disabled, title, search}`, so no canopy prop reaches that element;
  - upstream `dev` is unchanged, and no issue or PR there mentions it;
  - the reason is already announced through the label suffix; the state is not.

  The note ends with four options for the owner.

### Remaining — every item is the owner's call or waits on a date

1. **Remove juniper-ml's three worktrees.** Re-run the in-use probe first. `--force` is needed because each tree
   is dirty with untracked copies of what merged. Beyond those copies it deletes caches, and jazzy's three
   empty-or-near-empty `logs/*.log` files.

   ```bash
   python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/{jazzy-soaring-minsky,bright-crunching-alpaca,tender-wibbling-flask}
   git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jazzy-soaring-minsky
   git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bright-crunching-alpaca
   git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/tender-wibbling-flask
   git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree prune
   git -C /home/pcalnon/Development/python/Juniper/juniper-ml branch -D worktree-jazzy-soaring-minsky worktree-bright-crunching-alpaca worktree-tender-wibbling-flask
   ```

2. **Y7:** pick one of the four options in the §4.3 note, or accept the gap.
3. **X8's release.** The next juniper-data release after 0.16.0 carries #437 and #438. Cutting it is the owner's call.
4. **O9 / U-6:** wait for the canopy E2E triage. If O9 comes back, it is a design question for the owner.
5. **2026-09-29T00:00Z:** the peer `canopy` session's claims on Y2 waves 2/3 and X10 lapse, on the terms in
   `HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md`.
6. **Phase 7:** fast-forward the canopy, cascor and data primaries once nothing holds them.
7. **This session's worktree**, `enumerated-marinating-puddle`, can go once this handoff's PR merges.
8. **A-N9 needs no action.** It was never put to the owner as a question and stands as the predecessor's Key
   context records it: no `ModelSpec` accepts `structured`, and `arc_agi` stays unseeded.

### Traps

- **An ignored path can still be committed.** The A-N2 report's 92 files under `**/logs/` were force-added past
  that rule. This session first classified them "ignored" before comparing them with `main`, and read the README's
  `logs/` citations as a defect. They are not one. Compare with `main` first.
- **A clean holder scan is not proof that nothing holds a primary.** An import through an editable finder leaves
  no trace in `/proc` once the file is closed. That is why the cleanup script has `--no-primary-ff`.
- **Refused shapes this session:** `git -C` into a sibling worktree of *this* repo, even inside `$(…)`, and a
  `for` loop.

## Verification (run first)

```bash
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -cE 'selection|nn-model-mirror|a-n2-loop|x8-task|start-fresh|wider-dataset|equities-seq-task-type|status-current-dataset'   # 0
git worktree list | grep -E 'jazzy-soaring-minsky|bright-crunching-alpaca|tender-wibbling-flask'   # present until the owner removes them
du -sh /home/pcalnon/Development/python/Juniper/backups/worktree-harvest-2026-09-24-canopy-selection-arc   # 174M
python3 util/ad-hoc/cascor_freeze_tell.py   # exit 1 while a live stack holds the cascor primary
gh release list --repo pcalnon/juniper-data --limit 2   # has a release after 0.16.0 carried X8?
ss -ltnp | grep -E ':(8101|8202|8051) '   # the peer's stack; do not touch
```

## Git state at handoff

- **juniper-ml:** worktree `.claude/worktrees/enumerated-marinating-puddle`, branch
  `worktree-enumerated-marinating-puddle` at `df21367d`. This handoff's PR carries every new and changed file.
- **canopy, cascor, data:** no worktree or local branch from this arc remains. The primaries are not pulled,
  because live processes hold them.

## Documents

- **Referenced:**
  - the predecessor (named above);
  - `HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md` (same directory);
  - `HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` (the canopy E2E arc's,
    on its branch);
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`;
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (grepped, not changed);
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`.
- **Changed:** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (§4.3, the Y7 note).
- **Created:**
  - this file;
  - `util/ad-hoc/2026-09-24_canopy_arc_worktree_cleanup.py`;
  - `util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py`.
