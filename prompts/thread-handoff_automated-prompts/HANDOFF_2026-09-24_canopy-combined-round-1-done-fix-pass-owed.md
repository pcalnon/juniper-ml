# Handoff: canopy combined — one draft from three canopy handoffs; round 1 done, fix pass and round 2 owed

**Date**: 2026-09-24, ~21:20Z.
**Session**: "canopy combined", worktree `.claude/worktrees/bubbly-meandering-pie`.
**This handoff is NOT validated**: the owner asked for none.
**Merge approval**: none.

## Goal statement (paste as the first prompt)

Finish the owner's request, quoted verbatim: "combine these prompts into a single, unified prompt that integrates
the outstanding tasks included in each handoff. the new handoff document should contain all of the context needed
for the outstanding tasks to be completed. the combined handoff should be validated by consensus."

The three predecessors, all in `prompts/thread-handoff_automated-prompts/`:

- **A**: `HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`. On branch
  `docs/canopy-e2e-handoff-2026-09-24` (`dd4413e5`, no PR).
- **B**: `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md`. Untracked, and ONLY in
  `.claude/worktrees/idempotent-jumping-sparkle`.
- **C**: `HANDOFF_2026-09-24_canopy-selection-cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md`. On
  `main` (#2087).

Frozen copies of all three are in `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/`. `R` below
means `reports/2026-09-24_canopy-combined-handoff-consensus/`.

### Done

- **The draft.** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`
  is untracked in this worktree and deliberately NOT in this PR, because a sweeper merge would publish a draft known
  to be defective.
  - Its byte-identical frozen copy is `R/r1/DRAFT_r1.md` (sha256 `8c2fa290…`). If the worktree copy is gone, start
    from that.
  - Layout: Lane A (the E2E arc), Lane B (Y2 wave 2), Lane C (the selection arc's owner calls), cross-lane items
    X1–X5, traps, verification, git state, and a `VALIDATION_RECORD_PENDING` slot.
- **Round 1.** Five independent lanes, with reports archived verbatim at `R/r1/reports/R1{A..E}.md`. The lanes were
  facts, omission, executability, adversarial, and the `prompt-validator` rubric.
  - Verdicts: four SAFE AFTER FIXES; R1-E FAIL.
  - I re-derived every load-bearing finding in source. All of them hold.
- **A peer handed over a fourth canopy item.** Session "defect reg" sent the stale "Nothing was loaded…" copies
  (cascor#690). It is verified and in the draft's A2(a). I acknowledged it by SendMessage and assigned no id.
- **The reachability tool was upgraded.** `util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py` now reports
  reflog holders. It reports 33 commits: BRANCH 29, REFLOG-ONLY 4. The upgrade itself is unvalidated.

### Remaining

1. **Apply F1–F22 below to the prompts/ draft**, not to `DRAFT_r1.md`.
2. **Re-probe the state below** and update the draft.
3. **Round 2.**
   - Freeze to `R/r2/`.
   - Brief at least two lanes on the corrections only, and add one full-read, artifact-first lens.
   - Include the tool upgrade in scope.
   - Iterate until a round changes no number, disposition or action (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4).
4. **Fill `VALIDATION_RECORD_PENDING`** per §7 of that procedure.
5. **Ask the owner** whether to open a PR with the combined handoff, and whether to archive predecessors A and B in
   it. Never merge.

### Fix list

Every item was re-derived in source; the lanes that found it are in brackets.

**Critical or major:**

- **F1 [A,B,C,D,E]: A6 and A9 misread what holds the cited commits.**
  - **The facts.** canopy `78c057e2` sits in the reflogs of `perf/idle-dispatch-cuts-v2` and its worktree's HEAD.
    `26bf27b3`, `96e7b105` and `b07943d6` sit in the reflogs of `fix/idle-cuts-round3-wording` and its worktree's
    HEAD. No branch holds any of the four.
  - **Why it matters.** `gc` config is at its defaults. Removing a worktree deletes its HEAD reflog, and
    `branch -d/-D` deletes the branch reflog. So the threat is the cleanup, not `gc`.
  - **Rewrite A6:**
    - say "reflog-only", not "unreachable";
    - offer a local ref as the third option;
    - add a `fix/idle-cuts-round3-wording` row to its table.
  - **A9:** hold `…idle-cuts-round3-wording…` until A6 is answered. Only `…control--main--…` (detached, clean) is
    eligible now.
  - **Goal statement:** "four held only by reflogs a cleanup would delete".
- **F2 [B]: the ledger cites more local-only commits than the draft lists.**
  - It also cites the ten Phase 9 frozen commits (`e624c281` … `b0eb4ac1`), `5a0e4ea9` and `800c20bb`.
  - All of them live only on local `docs/canopy-e2e-phase9` (tip `808b74df`) and `worktree-squishy-dancing-moth`
    (tip `b54e3b3f`). `f6861234` is OLDER than the ten.
  - Provenance refs must point at the branch TIPS. The tool's output is the table.
- **F3 [B,C,D,E]: neither prescribed session can reach the draft or the tool.**
  - Lane B's tree is at `5ea8e273`, and a fresh `main` worktree lacks both files.
  - Give the absolute path. Lane B reads the draft by path. Until the draft merges, run the tool from this worktree.
- **F4 [C,E]: C6 is stale.**
  - The canopy and cascor primaries were fast-forwarded at 19:39:45–46Z with `pull --tags`, by an unknown actor,
    while the freeze was in force. Data is at `1afc3484`, one commit behind `0f0f7e0e` (#438).
  - So the trio now runs mixed-version code.
  - Two more holders: bash 2963582 holds the canopy primary and bash 2966837 the data primary, both from 09-19. The
    data leg, 2856834 (`/tmp/juniper-e2e`), holds no primary.
  - Fix the goal statement, C6, X4 and A4.
- **F5 [C]: A2 has no way to create a branch without opening a PR.**
  - `push_signed_commit.py` needs an existing branch. `open_signed_pr.py` refuses one, and opens a PR.
  - Use Phase 9's route:
    1. `gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/<b> -f sha=<main sha>`
    2. `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py --base <sha> --branch <b>`, which pushes the ledger
       alone and last.
    3. Open the PR only after that.
- **F6 [B]: restore two rules from B's predecessor (line 5)** to the binding rules: "Never merge other sessions' PRs"
  and "The juniper-recurrence release is owner-gated".
- **F7 [D]: X1's "make the preflight warn" option cannot remove the stake.**
  - 2b's mount is long form with `create_host_path: false`, so Docker refuses a missing source on every path
    (`S/r15/pr_wave2b_deploy.md`). `JUNIPER_SNAPSHOT_ROOT_OK=1` bypasses only the preflight.
  - **The real options:** exclude the four PRs from the sweeper, or fix forward. Under fix-forward, the owner could
    choose to pre-create `juniper-recurrence/recurrence-snapshots/` in the shared checkout.
  - **Add R15D's other consequences:** 2b's comment and CHANGELOG, and 2a's CHANGELOG, are false until 2c merges;
    and the merge-time checks never run.
  - **If X1 is unanswered,** the default is fix-forward, with `gh pr view` of all four before each merge and a
    blob-compare after any out-of-order merge.
  - R15D says "until 2a is released", not "ships".
- **F8 [D]: X2's "a pushed branch keeps the claim" collides with Lane B's own plan.**
  - `PLAN.md` says "nothing is opened or pushed from an unvalidated state", and the opener refuses an existing
    branch because it hard-codes the names.
  - Never pre-push a planned PR branch name.
  - Wave 3 and X10 are unstarted, so no branch can carry them. Their claims lapse on the date.

**Minor:**

- **F9: sources.**
  - O9's source is `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md:76-81`.
    The README's observations section (lines 188–223) holds O1–O8 only.
  - F-060–062 come from `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`
    (Remaining 4) and `reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md:21`.
- **F10: canopy#685 exists now.** It is OPEN, created 21:07:38Z, head `4a8af2a0`, not armed at 21:18Z. It comes from
  `fix/secret-leaks-683-validation` and fixes LOW 3 (F-061), LOW 4 (F-062) and a HIGH (padded outbound keys
  leaking). Record FIXED-BY #685. It is another session's PR.
- **F11: add to the owner batch:**
  - ledger items 3, 9 and 10;
  - making recurrence's `Settings` case-sensitive (`S/main/handoff_v4.md:54`);
  - token rotation: `HF_TOKEN` (`…four-rulings-made…md:30-31`) and `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI`;
  - whether to retain the ad-hoc driver copies (`…queue-drained…md:36`);
  - this handoff's PR, and archiving predecessors A and B;
  - who may stop the trio, and who is pulling the primaries under the freeze.
- **F12: numbering collisions.**
  - Rename X1–X5 to K1–K5.
  - Qualify each borrowed label:
    - "Lane B's handshake pacer" is the E2E review's Lane B (ledger `:8996`);
    - "Lanes C5/R4-A/A1/B2" are review lanes;
    - R15B's "X10, X18–X21" are mutation rows;
    - "Phase 7" in C6 is the cleanup procedure's, not the ledger's;
    - A7 item 12's "F1" is Phase 8's.
- **F13: line numbers at the current heads.**
  - cascor `7f4a7213` `manager.py`: start_replay's load `:6351`, `self.model` `:6108`, `_auto_snap_best` `:1526`.
  - canopy `7ab994e5`: `main.py:2998`; `dashboard_manager.py:4736`; `replay_player_panel.py` readout `:534`.
  - Add the rule: locate every line by its quoted text before editing.
- **F14: the verification block.**
  - Wrap Lane B's `cd …/r15 && sha256sum …` in a subshell.
  - Split "(any lane)". In Lane B's tree the triage prints 63/42/1/2/18, and two of the tools are missing.
  - Add `df -i /tmp` and `du -sh <harvest>` (174M).
- **F15: `.env.secrets.enc`.** Delete it only from a lane's scratch rebuild, never from the deploy primary or the
  2b worktree (`R15B.md:5`).
- **F16: the pinned re-probe now prints 45/46.** The local tag `v0.16.0` contains `68c3cd7c`. Update `handoff_v4`
  and the addendum rows.
- **F17: which handoff the addendum points at.** R15C's listing step greps for `canopy-selection`, which the combined
  file's name lacks, so name the file explicitly. R15C M1's own fix names only #2058, plus "reads every canopy
  merge since the pin"; the #674/#675 bullets come from B's predecessor.
- **F18: Lane B residue to carry.**
  - `tests/process_cleanup.py` is untracked (main's copy, in no upload set).
  - The tripwire and the four `2026-09-22_*` tools are intent-to-add.
  - The old tmpfs `…/798c2868-…/scratchpad/r15` still exists, and `S/main/lane_common_r15.md:8` points there.
    Re-point it to `S`.
  - The known limitations in `handoff_v4.md:50-54` (`JUNIPER_ROOT` and `JUNIPER_E2E_PROJECT_DIR`).
  - Round 15's tally: 3 MAJOR, 10 MINOR, ~20 NIT.
  - Deploy's new compose and helm tests must run in 2b's delta route.
- **F19: the two CHANGELOG conflicts differ.** #186 lands 3 lines clear of 2a's edit, so it should pass `--merged`
  (not executed). 2b's `### Fixed` is adjacent to #231/#232's, so R15D MINOR 1 is on 2b's path.
- **F20: sub-fixes the verbatim fix list omits,** so say the R15 reports are authoritative:
  - R15A `:59` "Also missed";
  - R15A m2 "writes or deletes";
  - R15B n3 "drop DOCKER_CONTEXT";
  - R15C `:130` `--fetch`;
  - R15D NIT 3, a deleted version heading.
- **F21: restore these traps:**
  - snapshot, then scan the mutants' strings;
  - review quoted literals by known-literal and length; `key_material()` refuses key material whatever
    `--allow-shape` allows;
  - agent briefs forbid printing secrets and sending the owner's email anywhere (A-N2 sent it to sec.gov);
  - PNGs go through the signed API as LFS pointers;
  - canopy's full test lane: `src/tests/{unit,regression,contract,performance}/`, `--timeout=60`,
    `LIBTORCH= LD_LIBRARY_PATH=` (`…four-rulings-made…md:84-86`);
  - the trio cascor fixture is "2/68/2".
- **F22: small corrections.**
  - A8's "ACTIVE lines" is the memory note's term; the word is not in MEMORY.md.
  - The linkset tool takes a file argument: `snapshot <f>` / `compare <f>`.
  - C2: drop "or accepts the gap", which is option 4.
  - C1: `enumerated-marinating-puddle` had 0 untracked files.
  - C3: the data 0.16.0 run `35977786108` failed its consumer-notify job after PyPI succeeded.
  - A fourth hard-coding tool: `2026-09-23_freeze_round14.py:38`.
  - "4–8 s".
  - Use mergedAt times: #683 19:10:20Z, #2069 07:54:41Z.
  - "Two branches hold `723ee812`".
  - "items 4 (§ B) and 20 (§ F)".
  - B3's pull precondition: the checkout must be clean and on `main`.
  - B2: spell out `S`; `addendum_v14.md` goes in `S/main/`; the logs directory must exist.
  - Choose lanes before running the verification.
  - The guard's refusals vary by session.
  - Name every document by filename (`…queue-drained.md`, the consensus procedure, the 09-23 E2E handoff) and
    complete the Documents list (R1A #5).
  - Record #684's main-verify as passed.
  - Only the recurrence and deploy trees were re-probed.

### State at 21:18Z (re-probe before round 2)

| repo | head or state |
|---|---|
| juniper-ml | `main` at `c061a99f` (#2086). No Y2 upload path has moved since `f9c81d80`. |
| juniper-recurrence | `db41e77e` |
| juniper-deploy | `7ff6ff32` |
| juniper-canopy | `7ab994e5` |
| juniper-cascor | #690 OPEN at `78e99414` |
| juniper-data | latest release v0.16.0 |

### Key context

- **Lane briefs** must say: read-only; never print secrets, environment values or the owner's email; no git in
  other juniper-ml worktrees; stay off ports 8101, 8202 and 8051. Default to REFUTE.
- **The session guard** refuses git against sibling juniper-ml worktrees and arguments computed at runtime.
- **The round-1 lanes disclosed local-only rule breaches.** These were scratch writes, email lines in their tool
  output, and one encrypted body fetched with only its size printed. Nothing was sent. See each report's
  Housekeeping.
- **The owner's sweeper may arm this PR.** Its merges are intended.

## Verify

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bubbly-meandering-pie
sha256sum reports/2026-09-24_canopy-combined-handoff-consensus/r1/DRAFT_r1.md   # 8c2fa290…
python3 util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py | tail -1   # BRANCH 29, REFLOG-ONLY 4
gh pr view 685 --repo pcalnon/juniper-canopy --json state,autoMergeRequest
```

## Git state

- **Worktree:** branch `worktree-bubbly-meandering-pie` at `6c23fdde`.
- **This PR** (branch `docs/canopy-combined-handoff-2026-09-24`) carries:
  - this file;
  - `R/r1/` (the draft copy, the predecessors, the five reports);
  - the reachability tool.
- **Left untracked:** the prompts/ draft.
- **Changed:** none.
