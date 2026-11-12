# Handoff: flood-4 — record merged (juniper-ml#2530); every fix and round-2 carrier built, validated and corrected; landing next

**Date**: 2026-11-09 (UTC; written ~11:00Z)

**Arc**: the Cursor flood-4 disposition, session 3. It started as `binary-seeking-frog` and ran in `humming-stargazing-papert` via EnterWorktree. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md` (session 2's handoff, which the owner edited mid-session to add ruling 12).

**Host**: the Linux host.

**Git status**:

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert` at `4bae7520`.
  - The record PR (#2530, squash `734aab58`) put its 172 files on `main`. The worktree still holds them: `CHANGELOG.md` modified and the rest untracked. They are byte-identical to `main`'s, except where they are this handoff.
  - Before you fast-forward, `cmp` each file against `git show origin/main:<path>`, then remove the identical untracked copies and run `git checkout -- CHANGELOG.md`. Keep this handoff, `util/ad-hoc/2026-11-08_flood4r2_*.py` (untracked, round 2's helpers) and `tmp/`.
  - `tmp/flood4/STATE.txt` is the running log; read its session-3 section (from "== SESSION 3") first.
- **Round 2 and fix work, all uncommitted.** Each item's latest deliverables are listed under Goal step 2. Validators' scratch worktrees (`*--val--flood4r2-*`, `juniper-cascor--validate--*`, `juniper-ml--val--flood4r2-ml-propose-*`) are under `/home/pcalnon/Development/python/Juniper/worktrees/`.
- **The primary checkout** is on the owner's branch. Do not touch it.

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md (in the humming-stargazing-papert worktree,
uncommitted). EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert).
Run the Verification block first; if an invariant fails, stop, re-derive it from GitHub, and report.

FIRST ask the owner for THIS session's merge approval, "Merge, update, close" (auto-memory
feedback_headless_merge_approval_policy.md: a handoff cannot carry it). Rulings 1-17 below stand.

1. Fast-forward the orchestrator worktree to origin/main (see Git status for how).

2. Land in this order. Strict rulesets apply, and CHANGELOG.md, docs/REFERENCE.md and the doc stamps are shared.
   For EACH item:
   - apply its last check's text fixes;
   - rebuild the shared files three-way on the current main, re-bumping each touched doc stamp from main's value;
   - freeze and scan with gitleaks `dir`, with a planted-token control;
   - push signed, in ONE commit where possible;
   - CHECK the run count on the FINAL head;
   - run util/safe_merge.py --execute and read its MERGED line;
   - close the drafts that item carried, each with a comment naming its carrier.

   juniper-ml:
   a. M-3, the paused-fit wedge. Tree .claude/worktrees/agent-a046a9b4b79c0d922, deliverables tmp/flood4-fix/m3-r3/.
      Apply check/findings.json F1-F3: drop "per-run stop token" from ruling-11 citations; the failure-path pause
      release wakes a stale fit; the refused-start exception.
   b. M-4/M-7, the resume losses. Tree .claude/worktrees/agent-aba7a82eb8f1730ca, deliverables tmp/flood4-fix/m4m7-r3/.
      Apply check/findings.json C1-C6. After M-3 merges, re-derive stamps from stamps.json, and merge both
      CHANGELOGs three-way. This is service-core's next MINOR, 0.8.0: raise the [tools] cap when it ships.
   c. N-2 (stop-then-start race) and N-4 (broadcast drops a failed socket without closing it), in service-core.
      Build each after a and b land; validate with two lenses; land.
   d. ml-code. Tree .claude/worktrees/agent-a675564a3fa0194a8, deliverables tmp/flood4r2/ml-code/r2/.
      Ruling 15 is in. The guard's brace expansion now follows bash 5.3's own code: it matches real bash 5.3.9 on 173
      fixed and 2,000 generated words, and it refuses brace-in-sequence, backslash/backtick letter ranges and numbers
      above 2^61. The proposed 3-line patch disagreed with bash on 41 of 173 words.
      - CI: 232 of 237 (the five known host failures). Mutants: 36 of 36.
      - This is BIGGER than ruled. Its two-lens validation must attack the port itself.
      - New bypass still open on main and in the carrier: `cat ~/.ss{h,b\}c}/config` (the guard cannot see escapes).
        ASK THE OWNER whether to carry an escape fix here or in its own PR.
      Tell the owner to reinstall the guard (1.3.0) after it merges.
   e. ml-tests: build it (it carries #2507's tests and rewords #2507's "propose.py does not edit" docstring), validate,
      land.
   f. ml-propose. Tree .claude/worktrees/agent-a89a45162cee4b2e8, deliverables tmp/flood4r2/ml-propose/r2/. Lands after
      ml-tests.
   g. ml-docs: build it after d (post-ml-code behaviour: ruling 15, strict fail-closed per ruling 16 with a quote-aware
      follow-up planned, the effort ruling, #2470 and #2490 rewritten), validate, land.

   juniper-data:
   h. M-1. Worktree juniper-data--fix--gitleaks-pr-commit-pagination--20261108-0340--4f04fc8d.
      Round 4 first: R3-01 octopus guard plus a test (proven on the validator's copy), R3-02, and R3-03..06, all
      from tmp/flood4r2-val/m1-r3/findings.json. Then a quick check, then land.
      Then ruling 10: port it to the seven other repos once data's scan has run green LIVE. A port is not a copy;
      see the record's ruling 10.
   i. data-tests, then data-docs, then data-code. Deliverables tmp/flood4r2-fix/<carrier>/. When data-code is rebuilt
      on the main that holds data-docs, apply data-code/apply_after_data_docs.json.

   juniper-canopy:
   j. canopy-tests, then canopy-docs (tmp/flood4r2-fix/<carrier>/).

   juniper-cascor:
   k. N-1. Worktree juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c, deliverables tmp/flood4-fix/n1-r2/.
      Re-validate first: round 2 added a lock inside the state machine, beyond the validated fix.
   l. N-3. Worktree juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c. Fix-up first, applying:
      - tmp/flood4r2-val/n3-code-lens: a two-lock-section test and an eviction-every-pass test;
      - tmp/flood4r2-val/n3-claims-lens: C01-C15, among them ruling 11's citation, a CHANGELOG entry placed BELOW N-1's,
        stamps, the 0.14.0 note, and JR-ML-WS-001/-003/-006.
      Then validate and land after N-1.

3. Ruling 17: build, validate and land four fixes, each its own PR:
   - juniper-data: 44 tests in test_security.py lack the `unit` mark;
   - juniper-cascor's own stop-then-start race (repro util/ad-hoc/2026-11-08_stop_then_start_race_repro.py in the N-1
     worktree);
   - canopy: 20 unit-lane tests connect to 127.0.0.1:8050, so add a conftest guard;
   - canopy: lockfile-update.yml:224-227's failure print is unreachable.
4. Round 3: #2404 and #2406, individually.
5. Ruling 7 cleanup.
   - FIRST archive, out of tmp/, the evidence the record cites (its §8 "The evidence in tmp/"), plus this session's
     tmp/flood4/val-record/v5, v6, round2-fixes/, push/ml-record-r2/, tmp/flood4r2-val/ and tmp/flood4r2-fix/.
   - Commit round 2's util/ad-hoc/2026-11-0[89]_flood4r2_*.py helpers as provenance, after fixing G-PATH and G-TMP in
     the five jd-gitleaks ones.
   - Then remove the merged items' worktrees. Never use util/remove_stale_worktrees.bash. curious-plotting-hummingbird
     is DO NOT SWEEP.
6. The record-update PR: rulings 15-17, round 2's table and outcome, the fix PRs, and the new findings (Traps and
   STATE.txt "NEW FINDINGS").
7. Archive the next handoff.
```

---

## The owner's rulings (AskUserQuestion; option labels verbatim)

Rulings 1-12 are in session 2's handoff and in the record's §8. Session 3 added these:

| # | Question | Answer |
|---|---|---|
| — | the owner's message | "merge approval granted for this work arc" |
| 13 | Approval scope, session 3 | "Merge, update, close (Recommended)" |
| 14 | #2507 | "Carry + extend propose.py (Recommended)" |
| 15 | Guard bypass `cat ~/.{r..t..1}sh/config` | "Carry in ml-code (Recommended)" |
| 16 | Brace-cap false refusals (21 of 44,660 recent commands) | "Ship strict, fix later (Recommended)" |
| 17 | New defects (multiSelect) | all four: "data: 44 unrun tests", "cascor: stop-then-start", "canopy: tests hit :8050", "canopy: dead error path" |

The record (#2530) covers rulings 1-14 only. Rulings 15-17 go in the record-update PR.

## Traps (new this session)

- **A batched API push can leave the final head with no Actions runs.** On #2530, ten `createCommitOnBranch` commits got runs only on intermediate heads, and those runs were cancelled. Fix: re-upload one file byte-identical with `util/push_signed_commit.py`. Check `actions/runs?head_sha=<final>` before arming a merge gate. See auto-memory `reference_github_pr_ci_trigger_traps.md` trap 5.
- **CodeQL raises alerts the prescreen does not model:** a constant in a conditional, an unused global, and a module imported both ways. Each opens a review thread that blocks the merge until the code is fixed; the threads then auto-resolve.
- **`TMPDIR` at 80 characters or more makes CPython multiprocessing silently use `/tmp`.** An N-1 builder pointed `TMPDIR` at its worktree and wrote to `/tmp/pymp-*`; it disclosed and cleaned up. Tell agents never to set `TMPDIR` to a worktree. The auto-memory `feedback_never_write_to_tmp_use_repo_tmp.md` already records this.
- **Agents without isolation write helpers into the orchestrator's `util/ad-hoc/`.** Name them `2026-11-08_flood4r2_*`: the `flood4_` glob would ship them. M-1's five had to be renamed.
- **`tests/test_release_train_registry.py` scans `tmp/`,** so stray pytest files there fail it.
- **Validators sharing one scratch dir overwrote each other once.** Give each lens its own directory.
- **`git merge-file` (pristine entry + base + current main) is the CHANGELOG rebuild that works.** A hand-inserted entry nearly reverted #2522.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert
git fetch -q origin; git log -1 --format=%h origin/main          # 734aab58 or later
gh pr view 2530 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state,.mergeCommit.oid[0:8]'   # MERGED 734aab58
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json number,isDraft --jq '[length, ([.[]|select(.isDraft)]|length)]'   # [42,40] at 11:00Z: 38 round-2 drafts + #2404/#2406, plus #2360 and #2529 (another session's; not this arc's)
git show origin/main:notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md | grep -c '^14\. \*\*juniper-ml#2507'   # 1
ls util/ad-hoc/2026-11-0[78]_flood4_*.py | wc -l                  # 160
tail -40 tmp/flood4/STATE.txt
```

## Documents created or modified in session 3

- **Merged in juniper-ml#2530 (`734aab58`):**
  - `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`;
  - `CHANGELOG.md`;
  - `reports/2026-11-08_flood4-disposition/README.md`;
  - two handoffs;
  - `util/ad-hoc/2026-11-08_flood4_record_round2_fixes.py` (new);
  - `…_record_freeze.py` (FIXED list);
  - three probes fixed for CodeQL: `…_val_data_tests_mutants.py`, `…_val_canopy_docs_screens.py` and `…_val_claimsB_registry_replay_probe.py`.
- **Uncommitted:** this handoff, `tmp/flood4/STATE.txt`, `tmp/flood4/BRIEF_COMMON_R2.txt` and `BRIEF_VALIDATE_R2.txt`, plus every fix and carrier worktree listed in Goal step 2.
- **Outside any repo:** auto-memory `reference_github_pr_ci_trigger_traps.md` (trap 5 added).
- **GitHub:** opened and merged juniper-ml#2530 (three commits on its branch, then a squash). No other PR was opened, merged or closed.
