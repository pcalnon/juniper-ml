# HANDOFF 2026-10-03 — logging redesign arc, cascor#573 (CONSOLIDATED): P0.4 and P1.4 merged, round-2 reconciliation still 0 % applied on main, P2.1 unstarted

- **Consolidated sources** (both in `prompts/thread-handoff_automated-prompts/`):
  - `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`. It self-declares **UNVALIDATED** ("without validation lanes"). It is the primary source.
  - `HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md` is its predecessor. Round 1 VALIDATED it with five lanes (§8 there). Round 2 found 20 defects in that fix pass, which nobody has reconciled. This file carries only the items the 09-24 source cites by reference: §8.1 rows, §8.2, §0.3, §0.4, §4 traps and §5.
- **Supersedes**: `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, which now has a banner. The 09-22 file is NOT bannered. It is itself a document that round 2 corrects, so it stays live as an edit target.
- **Live probe**: 2026-10-03 08:35–08:50 UTC. Probed: `gh` on cascor PRs, issues, branches and `main`; `git fetch` and `git log origin/main` in this worktree; plain `diff` against the `temporal-snacking-zebra` worktree; `ls` of `worktrees/`.
- **Documents of record** (abbreviated below as shown):
  - `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` (`…ROADMAP.md`);
  - `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md` (`…RECONCILIATION.md`);
  - round-2 evidence: `reports/2026-09-23_logging-arc-handoff-consensus/round2_lane_reports.md` (`round2_lane_reports.md`);
  - round-1 evidence: `reports/2026-09-23_logging-arc-handoff-consensus/round1_lane_reports.md` (`round1_lane_reports.md`);
  - the predecessor handoff above (`HANDOFF_2026-09-22_…`);
  - the P4 design: `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`;
  - the consensus procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

## Goal statement (paste as the new thread's first prompt)

Continue the juniper-cascor logging redesign
([cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573), OPEN). Read
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_logging-arc-consolidated.md` in full first.

**Completed so far**
[VERIFIED 2026-10-03: `gh pr view` / `gh api`, except where tagged]:

- **P0.4, the envelope and marker harness**: cascor#680 MERGED as `6276c459`. `src/tests/unit/test_log_record_envelope_contract.py` is on cascor `main`.
- **P1.4's fix half (`src/profiling/logging_utils.py`)**: cascor#681 MERGED as `f6ee8de3`.
- **Earlier P1 and P6.4 work**: #667 (07:24Z), #670 (08:00Z) and #675 (23:37Z) all merged on 2026-09-22.
- **Round 1 of validating `HANDOFF_2026-09-22_…`**: 23 corrections, merged as ml#2038 (`7e952534`).
- **Round-2 lane reports**: archived verbatim and merged with the 09-24 handoff as ml#2093 (2026-09-25).
- **cascor#679**: filed (`LogConfig` custom-level binding loses VERBOSE/TRACE records). Still OPEN.

**Remaining work, in order**:

1. **Round-2 reconciliation PR** (juniper-ml, cut from current `main`). Agent-doable; merging it is owner-gated (item 9).
   [VERIFIED 2026-10-03: none of it is on `main`. No commit has touched `…ROADMAP.md`, `…RECONCILIATION.md`, `HANDOFF_2026-09-22_…` or the census since `7e952534`. The census `EXCLUDED_FILES` lacks the three tools. `…ROADMAP.md:179` still says "BUILT". `:725` still says 28.25 %.] Line numbers in `round2_lane_reports.md` are at ml `f93c347f`, and these files have the same content on `main`.
   - **1a. Lane A's four fixes.** They exist uncommitted in worktree `juniper-ml/.claude/worktrees/temporal-snacking-zebra` [VERIFIED 2026-10-03: plain `diff` against `main` shows exactly these hunks]. Salvage them by copying the hunks, then soften the two "Phase 1 IS complete" phrasings per B5 (1c):
     - census `util/ad-hoc/2026-09-22_p04_log_marker_census.py`: add `EXCLUDED_FILES` entries, each with a reason, for `2026-09-22_p04_harness_mutation_check.py`, `2026-09-22_p04_reference_capture_excerpt.py` and `2026-09-23_logconfig_custom_level_binding_repro.py`.
       - The three are tracked on `main` and not excluded [VERIFIED].
       - **[CHANGED SINCE HANDOFF: zebra's three exclusions no longer get the census to exit 0.]** ml#2058 (merged 2026-09-23 21:53Z) added `util/ad-hoc/2026-09-23_a_n2_drive.py`, which brings 4 more UNCLASSIFIED anchors (`:134`, `:172`, `:566`, `:677`).
         [VERIFIED 2026-10-03: census on `afb02801`, `--rev e052ef8`: rc=1; 38 files name a log, 7 excluded, 22 carry anchors, 154 anchors; UNCLASSIFIED=8 (4 in `2026-09-22_p04_reference_capture_excerpt.py`, 4 in `2026-09-23_a_n2_drive.py`); MESSAGE LIVE=77, GONE=29.]
         The 09-24 source's "exits 0 with the exclusions (18 files, 104 anchors, LIVE=54, GONE=10)" described ml#2038's head.
       - **New step**: classify `a_n2_drive.py`'s four anchors in `CURATED`, or exclude the file with a reason. Then re-run until rc=0 and record the resulting counts.
     - The **N-4 hunk's counts** (33/34 files, 18 carrying anchors, 104 anchors) and **B4's** "35 markers from 14 scripts" were taken at ml#2038's head. Re-derive them on the PR's base before writing them; #680's checked-in `marker_inventory.json` is pinned at cascor `e052ef8` and does not move.
     - `…ROADMAP.md` decision 10: an UPDATE recording that #681 merged as `f6ee8de`. Zebra's text says "Phase 1 is complete"; soften it.
     - `HANDOFF_2026-09-22_…` §8.1 rows 12–13: record the merge. Zebra's row 13 says "Phase 1 IS complete now"; soften it.
     - `…RECONCILIATION.md` N-4: 33 files when the inventory was generated, 34 at ml#2038's head; the extra file carries no anchor.
   - **1b. Record one rejected finding as resolved dissent.** Lane A row 24 says "5/15 should be 1/5". At cascor `e052ef8`, `src/profiling/logging_utils.py:88-94` passes a literal `5`/`15`; the lane read post-#681 `main`. [UNVERIFIED — from the 09-24 source]
   - **1c. Re-derive each of Lane B's 20 single-lane findings, then apply it.** The table in "Context" below gives each one's substance; `round2_lane_reports.md` §Findings has the evidence and the fix text. B1, B2/B3 and B6 change a number or an action. **Resolve B16 first.**
     - **Open leads**, unverified by Lane B (from the "Not checked" section of `round2_lane_reports.md`, :231 and :229):
       - stale "~17 glob consumers" copies at `…ROADMAP.md:116`, `:409`, `:456`, `:646` and `…RECONCILIATION.md:441`. The census counts are what supersede them (re-derive per 1a);
       - B2's 1,238 "lines" against 1,218 "records" in the P0.1 run's shape survey is unreconciled.
   - **1d.** Write §8.3 in `HANDOFF_2026-09-22_…`: the lanes, what was accepted, what was rejected, and the author's two pre-round fixes (the restored P2.1(c) paragraph and the restored B1 forward hazard, which B2 corrects) [UNVERIFIED — from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, not validated]. Then run **round 3**, briefed only on the round-2 fixes. The consensus procedure's §4 requires it because B1, B2 and B6 change a number or an action. Agent-doable.
2. **Post the cascor#573 status comment.** Agent-doable. [VERIFIED 2026-10-03: #573 still has exactly one comment, from 2026-09-22 08:03Z.] The draft was lost with an ephemeral scratchpad, so rebuild it to say:
   - "Phase 1 is complete" was premature (B5);
   - "`logging_utils.py` fixed-but-unwired" was wrong, and #681 is what fixed it;
   - P6.4 is ruled hot-files-only and shipped as #675; widening to the other 236 sites needs a new ruling;
   - P0.2 is done: the gate read 16.70 %, and the instrument re-derives it to 29.2 % (per B1); P2 is measured unprofiled [UNVERIFIED — figures from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, not validated; 29.2 % is single-lane B1];
   - new: P0.4 is #680, and #679 is filed.
   Post it after 1c's numbers are settled. **P0.7** (keep #573 current) is only partly discharged by this comment: it still needs P0.3's numbers, so post a further comment once P0.3 runs (`HANDOFF_2026-09-22_…` §0.4) [NOT RE-PROBED — `HANDOFF_2026-09-22_…` §0.4, validated round 1].
3. **P2.1** (cascor). Agent-doable. Its blocker, item 1, is self-imposed.
   - **The change**: capture `frame`/`tsp` inside `_log_at_level`, after the filter. Pass `cls._frm().f_back` and leave `_frame_info` alone.
   - **The detector**: `test_log_record_envelope_contract.py::TestRealEmitPath::test_path_a_resolves_the_real_caller`. Not `test_logger_frame_resolution.py`, which passes a P2.1 that forgets `.f_back`.
   - **The measurement**: an unprofiled wall-clock A/B against the parent commit. cProfile inflates the discarded path 3.17× (B1, round 1), so no profiled number counts.
   - **Scope of the detector**: #680 checks Path A's eight emit methods, not every path to `_frame_info` (`HANDOFF_2026-09-22_…` §8.2). It supports "the harness would catch a frame-depth error on the emit methods", not "P2.1 is safe".
   - [VERIFIED 2026-10-03: on cascor `main` (`b2921712`) all eight emit methods still pass `cls._frm()` and `cls._tsp()` eagerly (`logger.py:612-668`), and the filter is at `:575`. The last commit to touch `logger.py` is #667.]
4. **P2.2** (cascor). Agent-doable after P2.1 and after B16 is resolved.
   - Hoist **six** closures: `logger.py:579`, `:580`, `:332`, `:333`, `:350` and `:351`.
   - Deleting `_get_log_level` / `_get_log_level_check` is symbol loss, so the commit body needs an enumerated `Allow-Symbol-Loss:` trailer.
   - [NOT RE-PROBED — line numbers from round 2, at cascor `e052ef8`. `logger.py` is unchanged since #667, so they should still hold on `main`.]
5. **cascor#679**: fix the `LogConfig.__init__` custom-level binding. It also has a second defect: the record never reaches the file sink (B20). [VERIFIED OPEN, 0 comments.] Agent-doable. It bears on the Phase-1 ruling in item 9.
6. **Ruled and unblocked**, agent-doable in any order [UNVERIFIED — list from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md` §6, not validated, as amended by round 2's B11; only P6.1's tracked-files fact was re-probed]:
   - decision 4: converge `src/log_config/logger/logger.py` into `juniper-cascor-model`, retire `_INTENTIONAL_DIVERGENCE` (`test_drift.py:31`), and delete `test_intentional_divergences_actually_differ` in the same PR;
   - decision 7: the swallowed-pytest investigation (§7.1 of `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md`, `:363`; the roadmap has no §7.1);
   - P0.3, the volume census. Paths B and C are separable by timestamp precision (B7);
   - P0.5. The candidate mechanism is `conftest.py`'s session-scoped `_log_at_level` no-op, and B1 says the stub's rationale is obsolete since #563;
   - P4.1–P4.3, with the B2/B3 obligation;
   - P5.1;
   - P6.1: `src/cascade_correlation/backups/` is still tracked, 5 files [VERIFIED 2026-10-03: `gh api contents`].
   - **P6.2 and P6.3 stay gated on P2** (B11).
7. **Cascor worktree cleanup** (section 5 of the 09-24 source). Agent-doable after verification, except the two owner-gated decisions in item 9. **Never run `util/remove_stale_worktrees.bash`.** All nine still exist [VERIFIED 2026-10-03: `ls`]. The table in "Context" lists them.
8. **juniper-ml worktree cleanup**: remove `temporal-snacking-zebra` once 1a has landed. `cached-greeting-mochi`, the 09-22 session's worktree at `a7568f78`, still exists. Agent-doable.
9. **Owner-gated**:
   - (a) re-confirm merge approval, which expires per session;
   - (b) a ruling on whether Phase 1 is "complete", given #670's per-level test gap and #679 (B5);
   - (c) any widening of P6.4 beyond the hot files. Residue for the ruling [NOT RE-PROBED — `HANDOFF_2026-09-22_…` §0.3, validated round 1; the roadmap's decision-6 UPDATE carries the same figures at cascor `e052ef8`]:
     - **236** mechanical sites outside the two hot files;
     - **51** mechanical sites inside them that were refused: 40 by the hazard-5 0-dim-tensor screen, 11 for other reasons (6 implicit string concatenation, 3 `!r`, 2 an `if`/`and` field). 0 remain convertible there;
     - re-derive with `util/ad-hoc/2026-09-22_p64_hot_file_convert.py --report` (hot files) and `util/ad-hoc/2026-09-09_p64_fstring_classify.py` (whole population). Both read `origin/main` and print the revision;
   - (d) the `…p01--logging-corpus…` worktree. It holds 5 ignored `cascor-snapshots/*.h5` files that `git worktree remove` would delete;
   - (e) whether to keep the cascor branch `wip/logging-p14-adopt-logging-utils` (`1b918e61`, still on the remote [VERIFIED]). #681 carries its fix, but it is the `--old` baseline for reproducing #667's timing (see `HANDOFF_2026-09-22_…` §7).

**Key context**: work from the verbatim archives (`round1_lane_reports.md`, `round2_lane_reports.md`), never from §8's summary in `HANDOFF_2026-09-22_…`. Round 1's reconciler dropped findings (B12–B15 are that residue). The traps are in "Context" below.

## Dependencies on other paths

- **No hard dependency found.** Neither `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (P3) nor `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_perf-lane-helper-binds-axis3-run-d6-control-micro-cut.md` (P6) mentions cascor#573, #679 or the logging arc [VERIFIED 2026-10-03: grep].
- **Soft, P6 (perf lane)**: P2.1's unprofiled wall-clock A/B runs on the same dev box as the perf lane's experiment suites. Run it when no perf stack is loading the host, and measure against the change's **parent commit**. That keeps cascor#683's BLAS-thread cap (perf lane D1, merged 2026-09-23) constant on both arms.
- **Soft, P6 (perf lane)**: per memory `reference_cascor_primary_frozen_while_any_stack_imports_it`, do P2.1 and P2.2 in a cascor worktree, never the primary checkout.
- **Naming hazard**: this arc's own "P6" (roadmap phase 6, call-site migration: P6.1–P6.4) is unrelated to path P6 (the perf lane).

## Context the remaining work needs

**Lane B's round-2 findings** [UNVERIFIED — from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, which was not validated, and `round2_lane_reports.md`; each finding is single-lane]:

| # | Finding | Fix target |
| --- | --- | --- |
| B1 | 28.25 % is a weighting defect. `util/ad-hoc/2026-09-23_p02_matcher_adequacy_check.py` weights builtins by pstats caller-edge CALL counts, which are degenerate in some profiles: `worker-1443178-df56f058.prof` has an edge sum of 1. Edge self-time gives **29.2 %** (≈10.80 s), which is A3's STRICT bound, not a looser one. The gate's decision is unchanged. | `…ROADMAP.md` decision-1 CORRECTION (:718, :723–725); `HANDOFF_2026-09-22_…` row 8; close §8.2's dissent in A3's favour |
| B2 + B3 | Under decision 5's A2-bind, `Logger.<level>` IS the default `BoundLogger`'s bound method (`util/ad-hoc/2026-09-10_p41_a2bind_prototype.py:128`), so #680's `test_path_a_resolves_the_real_caller` WOULD catch an extra hop. New obligation: **P4.1 keeps that test green without editing its expectations**, whether or not P2.1 ships first. Optional extra below. | `…ROADMAP.md` §5 P2.1(c) CORRECTION (:351–354), P4.1 ADDED block (:498, :502–504); `HANDOFF_2026-09-22_…` §8.2 (:461–464) |
| B4 | The 35 live markers come from **14** consumer scripts; 18 is the number of files with any anchor | `…ROADMAP.md:197`; `…RECONCILIATION.md:465`; row 21 |
| B5 | "Phase 1 complete" overstates it: #670's per-level test gap and #679 remain | row 13; zebra's decision-10 UPDATE |
| B6 | P2 Acceptance says "delta against P0.1's corpus". It should be an unprofiled wall-clock A/B against the parent commit. | `…ROADMAP.md:372–373` |
| B7 | P0.3(a) says B and C need instrumentation; they are separable by timestamp precision | `…ROADMAP.md:147` |
| B8 | The verdict at :270 becomes **RIGHT** (three scripts parse `func:LINE`); :634 and :638 become FALSIFIED 2026-09-23 | `…RECONCILIATION.md` |
| B9 | The banner scope and "next step" (:47–58) are uncorrected. Widen the banner and add row 24: the order survives only because #680 added caller identity beyond the spec. | `HANDOFF_2026-09-22_…` |
| B10 | §3.1 says "BUILT". Change it to MERGED `6276c459` [CHANGED SINCE HANDOFF: the lane's "#680 open" premise is moot; only the relabel remains] | `…ROADMAP.md:179`, `:207` |
| B11 | Row 19 is wrong: P6.2 and P6.3 depend on P2; only P6.1 is unblocked | row 19 |
| B12 | P6.4 shipped ahead of its gates (P6.2, P0.4, P2). Record the owner's hot-files ruling as the waiver. | `…ROADMAP.md` decision-6 UPDATE (:792–799) |
| B13 | Decision 5's "55–77 ns" describes stubs, not cascor; the correction was never applied | `…ROADMAP.md:771–773` |
| B14 | B1's gate critique was dropped. ~1.03 s of 6.18 s (`_filter_by_level` + `_resolve_level_number`) is beyond P2's reach, so report P2's addressable ceiling. B1's A/B measured V0 at 2,371 ns/call against V1 at 1,162 (0.669 s wall per corpus-equivalent, ≈21 ms per candidate training). | decision-1 CORRECTION |
| B15 | Row 17 omits part of B2's findings: "EXIT 0" has no test-count check under the conftest stub; an empty `$CASCOR` makes `git -C ""` run in the cwd; the byte-gate check covers 1 of 4 gated trees; local `--timeout=900` vs CI's 60 s | row 17 |
| B16 | P4.2 (:486) and P2.4 (:368–370) still have P4.2 subsuming `_get_log_level_check` (the roadmap cites `logger.py:394`/`:516`, which are stale; on cascor `main` `_get_log_level` is at `:427` and `_get_log_level_check` at `:435` [VERIFIED 2026-10-03: `gh api contents` + grep]; both are now dead), while the P2.2 correction gives its deletion to P2.2. **Resolve ownership first.** Plus eight stale copies: see the list below this table | `…ROADMAP.md` |
| B17 | "Path A and Path B/C emit different timestamp formats" should read: A and B emit seconds; C emits `,mmm`; 3 of 6 parsers cannot read C | `…RECONCILIATION.md:477–478` |
| B18 | "6/6 pass in both variants" and row 3's "convergent" overstate it: only B1 probed one-hop-too-many, and B1's V4 (two-hop `_frame_info`) gave correct callers, so the suite rejects a correct implementation | `…ROADMAP.md:329–330`; row 3 |
| B19 | The "at or above the level" rule is not universal: `stop_requested` (`src/api/lifecycle/manager.py`) has `required_level: null` | `…ROADMAP.md:199–201` |
| B20 | §6 (:322) still says "0.13 s over 2,912 calls", which is cumulative time. The #679 note omits "the record never reaches the file sink". Both notes say `Last Updated: 2026-09-02`. `…ROADMAP.md` §14 (:942–943) says "Round 3 is not warranted". Unrecorded rejections: see the list below this table | `HANDOFF_2026-09-22_…`; both notes |

**B2's optional extra**: add a `Logger.for_name(...)` case to #680's emitter. `test_logger_frame_resolution.py` still cannot see the extra hop.

**B16's stale copies in `…ROADMAP.md`**:

- the P2.2 row (:314) says "most frequent of the seven";
- the SWOT (:382) says "only detector";
- the scope table (:34) says "seven";
- `conftest.py:870-927` (:54, :149) should be 891–892 (fixture) and 948 (patch);
- `logger.py:1026` (:493, :769) should be `:1085`;
- `:521-526` (:380) should be `:579-580`;
- bare "§7.1" (:149, :700) points at a section the roadmap lacks;
- decision 8 (:822–824) still puts the fix half on the WIP branch.

**B20's unrecorded rejections**:

- B1's P0.5 point: the stub's rationale is obsolete since #563;
- B2's dropped traps 5.4, 5.5 and 5.9 (next block);
- B1's proposed juniper-ml-side consumer-drift test. The census's `--check-inventory` is not wired into any CI.

**B2's dropped traps** (from `round1_lane_reports.md:1141-1146`; carry them, or record their rejection):

- 5.4: a staging tree without `__init__.py`, and `sys.path` loop order;
- 5.5: a probe must not reconstruct the code under test. P0.4(d)(i) was exactly such a constants check;
- 5.9: `git grep -E '(?:…)'` returns empty silently.

**Owner rulings in force** (`…ROADMAP.md` §13.1) [UNVERIFIED — summarised from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, not validated; only decision 6's text was re-read]:

- decision 1: P2 runs, because the gate cleared 10 %;
- decision 4: converge the mirror;
- decision 5: A2-bind;
- decision 6 UPDATE, quoted from `…ROADMAP.md:793–797`: "**P6.4 RULED, hot files ONLY.** The owner authorised `%`-args conversion in `candidate_unit.py` and `cascade_correlation.py`; shipped as cascor#675, 220 sites. … **widening needs a fresh ruling.**" [VERIFIED 2026-10-03: `sed -n 790,800p`];
- decision 7;
- decision 10: P1.4 → hoisted guard + `%`-args, not `log_if_enabled`.
- Merge approval was granted for the 2026-09-23 session only, so **treat it as expired**.

**Traps from the validated predecessor** [NOT RE-PROBED — `HANDOFF_2026-09-22_…` §4, §8.1 rows 3 and 20, §8.2; validated round 1]:

- **P2.1(c)**: never make `_frame_info` walk two hops. Never "fix" a failing `test_path_a_resolves_the_real_caller` expectation.
- **Hazard 5**: `%`-args render 0-dim tensors differently (`'tensor(1.5000)'` vs `'1.5'`), and a template-level render check cannot see it.
- **`JUNIPER_CASCOR_LOG_DIR`**: if set, 6 unrelated tests fail. Run cascor tests with `env -u JUNIPER_CASCOR_LOG_DIR`.
- **cascor test modules**: each needs `pytestmark = pytest.mark.unit`, or CI deselects it.
- **Byte-gated mirror**: `candidate_unit.py` is byte-gated against `juniper-cascor-model`. Re-sync the mirror after the final lint, because Black covers `src/` only. The byte-gate vs `_INTENTIONAL_DIVERGENCE` ordering interacts with decision 4.
- **Formatter**: use `/opt/miniforge3/bin/pre-commit`, because the local black (26.5.1) differs from cascor's pin (25.1.0).
- **Signed commits**: a local `git commit` hangs.
  - `util/open_signed_pr.py` creates a new branch.
  - `util/ad-hoc/2026-09-08_push_signed_commit.py` appends to an existing branch.
- **PR bodies**: edit them with `gh api -X PATCH`, because gh 2.46 breaks `gh pr edit`.
- **Merging** (§4.7):
  - `util/safe_merge.py --execute` exits 0 without merging, so read its `MERGED` line;
  - in a contended lane, use native auto-merge (`gh pr merge --auto`) only **after** `safe_merge` refuses;
  - an unresolved CodeQL review thread blocks a merge even when every check is green;
  - `pre-commit run --files` reads the **index**, so stage first, and re-stage after a hook rewrites a file.
- **A cell is not a suite**: never put a cell YAML in `util/experiments/suites/`.
- **P0.1 is a re-baseline, not a repeat** (§4.4). juniper-data rejects ratios that sum to 1.1. `val_ratio: 0.0` emits an **empty** `X_val`, which cascor refuses at `cascade_correlation.py:1671`: the CLI tolerates a *missing* val, not an *empty* one. The cell used `0.8 / 0.1 / 0.1`, and `dataset_id` differs from August's.
- **P0.1 corpus** (§4.5): a zero-`.prof` run exits 0, so check the count. The raw 32 `.prof` blobs live only at `~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof/` and are not backed up; `reports/p01-logging-corpus-2026-09-22/prof_manifest.txt` is what survives in git.
- **A stale checkout returns a plausible number** (§4.6). The shared `juniper-cascor` checkout sits on whatever branch another session left. Instruments now default to `origin/main` and print the revision; **check that printed revision** before trusting a count.

**Traps from the unvalidated 09-24 source** [UNVERIFIED — from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, not validated]:

- **Real-emit tests** need a child process, because `conftest.py` no-ops `_log_at_level`.
- **`util/open_signed_pr.py`** uploads WHOLE files, so check that `origin/main` has not changed them first.
- **A BEHIND PR**: `gh api -X PUT repos/pcalnon/<repo>/pulls/N/update-branch -f expected_head_sha=<full sha>`. Look the SHA up; never guess it.
- **Squash trailers**: GitHub's squash lifts `Co-Authored-By` out of the trailer block, but the ci-tools waiver readers are line regexes, so `Allow-Symbol-Loss:` still applies.
- **Worktree-isolated sessions**: use one plain command per call. The Bash classifier refuses `for` loops, `${PIPESTATUS}`, a heredoc inside `&&`, `xargs -a`, `python -c` containing "git", and `git -C` aimed at another repo or at juniper-ml's primary checkout.

**Cascor worktrees** (all under `Juniper/worktrees/`; all exist [VERIFIED 2026-10-03: `ls`]; dirt states [UNVERIFIED — from the 09-24 source]):

| worktree | action |
| --- | --- |
| `…--feat--logging-p04-envelope-harness--20260922-2036--0d2d826b` | remove once `git -C <wt> diff --cached origin/main -- <its files>` is empty |
| `…--fix--logging-p14-logging-utils-levels--20260923-0032--e052ef80` | same |
| `…--fix--logging-isenabledfor-memo--20260921-0400--c6c848f2` | dirt reported byte-identical to its merged PR: verify, then remove |
| `…--fix--logging-p14-guard-display-progress--20260922-0530--0c14e92d` | same |
| `…--fix--logging-p64-hot-files--20260922-1815--05c13d55` | same |
| `…--measure--p14-plus-memo--20260921-0500--1b918e61` | its `logger.py` dirt DIFFERS: inspect it |
| `…--p01--logging-corpus--20260922-0630--8065ca0f` | 5 ignored `.h5` files: owner decides (item 9d) |
| `…--wip--logging-p14--20260921-0340--1b918e61` | clean; its fix is on `main`: removable (but see item 9e) |
| `…--perf--logging-hot-path--20260830-0145--6f3b09a7` | an older arc: leave it |

## Verification commands

```bash
gh pr view 680 -R pcalnon/juniper-cascor --json state,mergeCommit        # MERGED 6276c459…
gh pr view 681 -R pcalnon/juniper-cascor --json state,mergeCommit        # MERGED f6ee8de3…
gh issue view 573 -R pcalnon/juniper-cascor --json comments --jq '.comments | length'   # 1 until item 2 lands
gh issue view 679 -R pcalnon/juniper-cascor --json state                 # OPEN until item 5
gh api "repos/pcalnon/juniper-cascor/contents/src/log_config/logger/logger.py?ref=main" --jq .content | base64 -d | grep -c 'frame=cls._frm(), tsp=cls._tsp()'   # 8 until P2.1 lands
git log --oneline origin/main -2 -- notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md   # top = 7e952534 until item 1 lands
grep -c 'p04_harness_mutation_check' util/ad-hoc/2026-09-22_p04_log_marker_census.py   # 0 until 1a lands
diff util/ad-hoc/2026-09-22_p04_log_marker_census.py ../temporal-snacking-zebra/util/ad-hoc/2026-09-22_p04_log_marker_census.py   # zebra's 1a hunk (run from a juniper-ml worktree under .claude/worktrees/)
python3 util/ad-hoc/2026-09-22_p04_log_marker_census.py --cascor /home/pcalnon/Development/python/Juniper/juniper-cascor --rev e052ef8   # on afb02801: rc=1, 154 anchors, UNCLASSIFIED=8, LIVE=77 GONE=29; rc=0 only after zebra's 3 exclusions AND a_n2_drive.py's 4 anchors are handled
grep -c 'a_n2_drive' util/ad-hoc/2026-09-22_p04_log_marker_census.py   # 0 until 1a's new step lands
```

## Dispositioned / closed items

| item | source | disposition | evidence |
| --- | --- | --- | --- |
| P0.4 harness (`HANDOFF_2026-09-22_…` §0.1) | 09-22 | DONE | cascor#680 MERGED `6276c459` [VERIFIED] |
| P1.4 fix half / "`logging_utils` fixed-but-unwired" (§3 item 1, row 12) | 09-22 | DONE | cascor#681 MERGED `f6ee8de3` [VERIFIED] |
| Round 1 (23 corrections) | 09-24 | DONE | ml#2038 MERGED `7e952534` [VERIFIED] |
| Archiving the round-2 reports, and the 09-24 handoff PR (`docs/handoff-2026-09-24-logging-arc`) | 09-24 | DONE [CHANGED SINCE HANDOFF: the source called it unmerged] | ml#2093 MERGED 2026-09-25 [VERIFIED] |
| `MEMORY.md` compaction (26,903 → 24,808 characters) | 09-24 | DONE [UNVERIFIED — from `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`, not validated] | stated in the source; not re-probed |
| "The next step is P0.4, not P2.1" (§0, :47–58) | 09-22 | MOOT, because P0.4 merged. The text correction survives as B9 | — |
| P2.1's "only detector is `test_logger_frame_resolution.py`" | 09-22 | SUPERSEDED: the detector is #680's test (row 3) | carried in item 3 |
| P2.2 "seven closures" | 09-22 | SUPERSEDED: six (row 6) | carried in item 4 |
| The 09-22 §1 verification block | 09-22 | SUPERSEDED: not executable (row 17, B15) | replaced by this file's block |
| "Decide whether to close the WIP branch" (§5) | 09-22 | REVISED: closing it is no longer destructive, but it is the `--old` baseline for #667's timing | item 9e |
| `JuniperCascor1` broken env / private `/tmp` venv (§5.1 of `HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`) | 09-22 | MOOT: the env works | `HANDOFF_2026-09-22_…` §1 |
| The ~17 vs 18-scripts count (§0.1(c)) | 09-22 | SUPERSEDED by the census (row 21), then by B4 (14 consumers) | item 1c |
| Lane A row 24 ("5/15 → 1/5") | 09-24 | REJECTED, to be recorded (1b) | item 1b |
| B10 "#680 is still open" | round 2 | MOOT; only the "BUILT" relabel remains | item 1c |
| The cascor#573 comment draft | 09-24 | LOST (ephemeral scratchpad) | rebuilt from item 2 |

## Git state

- **juniper-ml `main`** is at `afb02801`. Nothing in the logging arc has merged since ml#2093 [VERIFIED: `git log origin/main`].
- **Remote branches** `docs/handoff-2026-09-24-logging-arc` and `feat/logging-p04-marker-census` are **already deleted on GitHub** [VERIFIED 2026-10-03: `gh api …/branches/<name>` returns 404]. Only stale local tracking refs remain (clear them with `git fetch --prune`), plus the local branch `feat/logging-p04-marker-census` (`25b78f55`) that zebra has checked out.
- **juniper-ml worktree** `.claude/worktrees/temporal-snacking-zebra` is on local `feat/logging-p04-marker-census` (`25b78f55`). It holds the four uncommitted 1a fixes [VERIFIED: `git worktree list` and `diff`].
- **juniper-ml worktree** `.claude/worktrees/cached-greeting-mochi` is at `a7568f78` (the 09-22 session's).
- **juniper-cascor `main`** is at `b2921712`. No logging PR has opened since #681; the post-#681 PRs are dependabot bumps plus #682–#690 (other arcs) [VERIFIED: `gh pr list`]. Branch `wip/logging-p14-adopt-logging-utils` is at `1b918e61` [VERIFIED]. The nine logging-arc worktrees are listed above.
- **This consolidation** lives on juniper-ml branch `docs/handoff-consolidation-2026-10-03` (uncommitted when written). It changes only this file, plus the banner on `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`.
