# HANDOFF 2026-09-24 — logging arc: P0.4 and P1.4 merged, round 2 half-reconciled; finish it, then P2.1

> **UNVALIDATED.** The owner asked for this handoff without validation lanes and with minimal
> tokens. Every claim cites its source; re-derive anything load-bearing before acting on it.
> Memory: `feedback_validate_handoff_prompts_independently`.

This is the successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`,
written `HANDOFF_2026-09-22_…` below.

- **Arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573).
- **Documents of record**:
  - `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, written `…ROADMAP.md` below;
  - `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`, written `…RECONCILIATION.md` below.
- **Line numbers** are at juniper-ml `f93c347f`, the round-2 freeze. For these three files it has
  the same content as the merge `7e952534`.
- **Dates** are UTC.

## Goal

Continue the juniper-cascor logging redesign (cascor#573), in this order:

1. finish the round-2 reconciliation of `HANDOFF_2026-09-22_…` in a new juniper-ml PR;
2. post the cascor#573 status comment;
3. start P2.1.

### Done (2026-09-23)

| item | state |
| --- | --- |
| P0.4 envelope and marker harness | cascor#680 **MERGED** `6276c459`. 31 tests; mutation check 14/14 plus 2/2 controls |
| P1.4 `logging_utils.py` level fix (it had never been on `main`) | cascor#681 **MERGED** `f6ee8de`. `Allow-Symbol-Loss` was waived on `main`, and Post-Merge Main Verification is green |
| cascor#679: `LogConfig` custom-level binding loses VERBOSE/TRACE records | filed, OPEN |
| Round 1: 5 lanes, 23 corrections in `HANDOFF_2026-09-22_…` §8 | juniper-ml#2038 **MERGED** `7e952534`, which also carries the at-source corrections, the P0.4 tooling and `reports/2026-09-23_logging-arc-handoff-consensus/round1_lane_reports.md` |
| Round 2: Lane A (sonnet) and Lane B (opus) against `f93c347f` | reports archived verbatim **in this PR**: `reports/2026-09-23_logging-arc-handoff-consensus/round2_lane_reports.md`. **Reconciliation NOT done** |
| `MEMORY.md` compaction | 26,903 → 24,808 characters; 0 losses and 0 dropped links. The load limit is about 25,000 **characters**, not bytes |

## 1. Round-2 reconciliation PR (juniper-ml, based on current `main`)

### 1a. Re-apply Lane A's four fixes

These were made locally and never pushed. If the session worktree still exists
(`juniper-ml/.claude/worktrees/temporal-snacking-zebra`), `git diff` there shows them.

- **`util/ad-hoc/2026-09-22_p04_log_marker_census.py`**: add these three to `EXCLUDED_FILES`, each
  with a reason. They are P0.4 tooling, not consumers.
  - `util/ad-hoc/2026-09-22_p04_harness_mutation_check.py`
  - `util/ad-hoc/2026-09-22_p04_reference_capture_excerpt.py`
  - `util/ad-hoc/2026-09-23_logconfig_custom_level_binding_repro.py`

  Why it matters:
  - they were untracked when the inventory was generated, and discovery reads TRACKED files only;
  - so **on `main` the census now exits 1** (4 UNCLASSIFIED anchors);
  - with the exclusions it exits 0: 18 files, 104 anchors, LIVE=54, GONE=10.
- **`…ROADMAP.md` decision 10**: add an UPDATE that cascor#681 merged as `f6ee8de`.
- **`HANDOFF_2026-09-22_…` §8.1 rows 12–13**: record that #681 merged. Soften row 13's "Phase 1 IS
  complete" per B5 below.
- **`…RECONCILIATION.md` N-4 CORRECTION**: "33 files" was the count when the inventory was
  generated. It is 34 at ml#2038's head, and the extra file carries no anchor.

### 1b. Record one rejected finding

Lane A's row 24 ("5/15 should be 1/5") is rejected. At `e052ef8`,
`src/profiling/logging_utils.py:88-94` passes a literal `5`/`15`; the lane read post-#681 `main`.
Record it as resolved dissent.

### 1c. Re-derive, then apply, Lane B's 20 findings

All of them are single-lane. The report in the round-2 archive has the evidence and the fix text.

**Changes a number or an action:**

- **B1: 28.25 % is a weighting defect.**
  - `util/ad-hoc/2026-09-23_p02_matcher_adequacy_check.py` shares builtins out by pstats
    caller-edge CALL counts, which are degenerate in some profiles. `worker-1443178-df56f058.prof`
    has an edge sum of 1.
  - Edge self-time gives **29.2 %**, which is Lane A3's STRICT bound.
  - Fix `…ROADMAP.md`'s decision-1 CORRECTION, `HANDOFF_2026-09-22_…` row 8, and §8.2's dissent
    (close it in A3's favour). The gate's decision is unchanged.
- **B2 and B3: the P4 forward hazard is mis-stated.**
  - Under decision 5's A2-bind, `Logger.<level>` IS the default `BoundLogger`'s bound method
    (`util/ad-hoc/2026-09-10_p41_a2bind_prototype.py:128`). So cascor#680's
    `test_path_a_resolves_the_real_caller` WOULD catch an extra hop.
  - The obligation becomes: **P4.1 keeps that test green without editing its expectations.**
  - It holds whether or not P2.1 ships first.
  - Fix `…ROADMAP.md`'s §5 P2.1(c) CORRECTION and its P4.1 ADDED block, and `HANDOFF_2026-09-22_…`
    §8.2.
- **B4**: the 35 markers come from **14** consumer scripts. The 18 is the number of files with any
  anchor.
- **B5**: "Phase 1 complete" overstates it, because #670's per-level test gap and #679 remain.
- **B6**: `…ROADMAP.md` P2 Acceptance (:372) says "delta against P0.1's corpus". Make it an
  unprofiled wall-clock A/B against the parent commit, as the decision-1 correction already says.
- **B7**: `…ROADMAP.md` P0.3(a) (:147) still says B and C need instrumentation. They are separable
  by timestamp precision.
- **B8**: in `…RECONCILIATION.md`, the verdict at :270 becomes RIGHT, and the claims at :634 and
  :638 are FALSIFIED.
- **B9**: `HANDOFF_2026-09-22_…`'s banner scope and its "next step" section (:47–58) are
  uncorrected. Widen the banner and add row 24.
- **B10**: `…ROADMAP.md` §3.1 says "BUILT". Change it to MERGED `6276c459`.
- **B11**: row 19 is wrong: P6.2 and P6.3 depend on P2. Only P6.1 is unblocked.

**Residue that round 1 dropped:**

- **B12**: P6.4 shipped ahead of its gates. Record the owner's hot-files ruling as the waiver.
- **B13**: decision 5's stub-benchmark correction was never applied (`…ROADMAP.md` :771).
- **B14**: B1's gate critique was dropped. The 1.03 s filter share is out of P2's reach, and B1's
  A/B measured V0 at 2,371 ns/call against V1 at 1,162.
- **B15**: row 17 carries only part of B2's §1 findings.

**Stale copies and citations: B16–B20.** These are listed in the report. B16's P2.2-versus-P4.2
ownership conflict over deleting `_get_log_level_check` needs resolving first.

### 1d. Record round 2, then decide on round 3

- Write §8.3 in `HANDOFF_2026-09-22_…` with the lanes, what was accepted and what was rejected.
- Also record the author's two pre-round fixes: the restored P2.1(c) paragraph, and the restored B1
  forward hazard, which B2 has now itself corrected.
- B1, B2 and B6 change a number or an action. Under
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4, that
  means a round 3, briefed only on the round-2 fixes.

## 2. The cascor#573 status comment

It corrects the 2026-09-22 comment:

- **"Phase 1 is complete"** was premature (see B5).
- **"`logging_utils.py` fixed-but-unwired"** was wrong; #681 is what fixed it.
- **P6.4 is ruled**: hot files only, shipped as #675. Widening to the other 236 sites needs a fresh
  ruling.
- **P0.2 is done**: the gate read 16.70 %, and the instrument re-derives to 29.2 %. Measure P2
  unprofiled.
- **New**: P0.4 is #680, and #679 is filed.

## 3. P2.1 (after section 1)

- **The change**: capture `frame`/`tsp` inside `_log_at_level`, after the filter. Pass
  `cls._frm().f_back` and leave `_frame_info` alone.
- **The detector**: cascor
  `src/tests/unit/test_log_record_envelope_contract.py::TestRealEmitPath::test_path_a_resolves_the_real_caller`.
  Not `test_logger_frame_resolution.py`, which passes a P2.1 that forgets `.f_back`.
- **The measurement**: an unprofiled wall-clock A/B against the parent commit. cProfile inflates the
  discarded path 3.17×.

## 4. P2.2

- **Scope**: six closures, at `logger.py:579`, `:580`, `:332`, `:333`, `:350` and `:351` at
  `e052ef8`.
- **Symbol loss**: deleting `_get_log_level` / `_get_log_level_check` needs an enumerated
  `Allow-Symbol-Loss:` trailer (see B16 first).

## 5. Cascor worktree cleanup (never run `util/remove_stale_worktrees.bash`)

**Mine: the P0.4 and P1.4 worktrees.**

- `worktrees/juniper-cascor--feat--logging-p04-envelope-harness--20260922-2036--0d2d826b`
- `worktrees/juniper-cascor--fix--logging-p14-logging-utils-levels--20260923-0032--e052ef80`

Their staged content is the merged PRs. Remove them once
`git -C <wt> diff --cached origin/main -- <its files>` comes back empty.

**Earlier sessions' worktrees:**

| worktree | state | action |
| --- | --- | --- |
| `…isenabledfor-memo…` | dirt reported byte-identical to its merged PR | verify, then remove |
| `…p14-guard-display-progress…` | dirt reported byte-identical to its merged PR | verify, then remove |
| `…p64-hot-files…` | dirt reported byte-identical to its merged PR | verify, then remove |
| `…measure--p14-plus-memo…` | its `logger.py` dirt DIFFERS | inspect it |
| `…p01--logging-corpus…` | holds 5 ignored `cascor-snapshots/*.h5`, which `worktree remove` deletes | decide first |
| `…wip--logging-p14…` | clean; its fix is on `main` | removable |
| `…perf--logging-hot-path…` | an older arc | leave it |

## 6. Ruled and unblocked

- decision 4: converge `src/log_config/logger/logger.py` into cascor-model and retire
  `_INTENTIONAL_DIVERGENCE`;
- decision 7;
- P0.3 and P0.5;
- P4.1–P4.3;
- P5.1;
- P6.1 (`src/cascade_correlation/backups/` is still tracked).

P6.4 widening needs an owner ruling.

## Traps

- **Merge approval** was granted for the 2026-09-23 session only. Re-confirm it.
- **Signed commits**:
  - `util/open_signed_pr.py` opens a new branch. It uploads WHOLE files, so check that `origin/main`
    has not changed them first.
  - `util/ad-hoc/2026-09-08_push_signed_commit.py` appends to an existing branch.
  - A local `git commit` hangs.
- **PR bodies**: edit them with `gh api -X PATCH`, because gh 2.46 breaks `gh pr edit`.
- **Merging**: use `util/safe_merge.py --execute`, and read its `MERGED` line.
- **A BEHIND PR**: `gh api -X PUT repos/pcalnon/<repo>/pulls/N/update-branch -f expected_head_sha=<full sha>`.
  Look the SHA up; never guess it.
- **Squash trailers**: GitHub's squash lifts `Co-Authored-By` out of the trailer block. The ci-tools
  waiver readers are line regexes, so the waivers still apply.
- **cascor tests**:
  - every test module needs `pytestmark = pytest.mark.unit`, or CI deselects it;
  - real-emit tests need a child process, because `conftest.py` no-ops `_log_at_level`.
- **The worktree-session Bash classifier**:
  - one plain command per call;
  - refused: `for` loops, `${PIPESTATUS}`, a heredoc inside `&&`, `xargs -a`, and `python -c`
    containing "git";
  - also refused: `git -C` aimed at juniper-ml's primary checkout.
- **pre-commit**: run `/opt/miniforge3/bin/pre-commit`.
- **Residue**: round 1's reconciler dropped findings. Work from the verbatim archives, never from
  §8's summary.

## Verification

```bash
gh pr view 680 -R pcalnon/juniper-cascor --json state,mergeCommit --jq '.state+" "+.mergeCommit.oid[:8]'   # MERGED 6276c459
gh pr view 681 -R pcalnon/juniper-cascor --json state --jq .state                                         # MERGED
gh pr view 2038 -R pcalnon/juniper-ml --json state --jq .state                                            # MERGED
python3 util/ad-hoc/2026-09-22_p04_log_marker_census.py --cascor /home/pcalnon/Development/python/Juniper/juniper-cascor --rev e052ef8   # exit 1 until 1a lands, then 0
```

## Git state (2026-09-24)

- **juniper-ml `main`** includes ml#2038.
- **This PR** is branch `docs/handoff-2026-09-24-logging-arc`: this handoff plus the round-2
  archive. It is unmerged.
- **The session worktree** `juniper-ml/.claude/worktrees/temporal-snacking-zebra` is on local branch
  `feat/logging-p04-marker-census`, whose remote was merged. It holds 1a's four fixes uncommitted.
- **The cascor#573 comment draft** sat in the session scratchpad, which is ephemeral. Rebuild it
  from section 2.
