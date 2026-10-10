# Extraction — P7 logging redesign

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04 20:54–21:05 UTC (juniper-ml `main` = `cf711cf4`; cascor `main` = `95cdc562`)

Short names used below: **consolidated** = `HANDOFF_2026-10-03_logging-arc-consolidated.md`; **09-24** = `HANDOFF_2026-09-24_logging-arc-p04-merged-finish-round-2-then-p21.md`; **09-22** = `HANDOFF_2026-09/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`; **ROADMAP** = `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`; **RECON** = `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`; **P4-design** = `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`; **R2** = `reports/2026-09-23_logging-arc-handoff-consensus/round2_lane_reports.md`; **census** = `util/ad-hoc/2026-09-22_p04_log_marker_census.py`. All handoffs live in `prompts/thread-handoff_automated-prompts/`.

## 0. Sources read

| file | read |
| --- | --- |
| consolidated | in full (:1–250) |
| `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` | in full |
| 09-24 | in full |
| 09-22 (now under `HANDOFF_2026-09/`) | in full (:1–466) |
| `HANDOFF_2026-09/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md` | headings, §0.2, §5.2, §5.6 only |
| R2 | in full |
| `reports/2026-09-23_logging-arc-handoff-consensus/round1_lane_reports.md` | **NOT READ** (1,338 lines); used only through R2's citations |
| ROADMAP | in full (:1–953) |
| RECON | §4 (:249–288), §6 N-3b–N-8 (:425–560), §7–§9 (:600–699), headings |
| P4-design | §4.1–§8 (:148–282), §11–§12 (:357–474) |
| `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md` | §7.1 only |
| `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` | §4 only |
| `HANDOFF_2026-10-03_perf-lane-consolidated.md`, `…release-and-distribution-consolidated.md`, other 10-03/10-04 handoffs | grep for P7 / quiet window / cascor release; `…defect-register-round-42-consolidated.md` :60–72 |
| census; `util/ad-hoc/2026-10-04_replay_redrive.py` | discovery/classify code and anchors, **read, not run** |
| `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` | not read (cited only for hazards) |

Live probes: `gh api` on cascor issues #573, #679 (including #573's single comment and #679's body); cascor PRs #680 and #681, open/closed lists, `compare v0.11.0...main`, matching-refs and the latest release; cascor `main` copies of `logger.py`, `conftest.py`, `candidate_unit.py`, the envelope test, `marker_inventory.json` and `test_drift.py`, plus `logging_utils.py@e052ef8`; three code searches and three issue searches; ml PRs #2058, #2122, #2125 and the open list; PyPI for `juniper-cascor` and `juniper-cascor-model`; `git grep` replication of census discovery at HEAD and at `afb02801`; plain `diff` against the zebra worktree; `ls` of the worktrees and the corpus; `/proc/loadavg`; `ps` for clamscan.

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo | Eff | Crit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7-01 | Copy zebra's four Lane A hunks, hunk by hunk, onto a fresh branch from `main`. Soften both "Phase 1 IS complete" phrasings (B5). | consolidated item 1a; 09-24 §1a | [VERIFIED 2026-10-04: `diff` vs `temporal-snacking-zebra` → census +3 `EXCLUDED_FILES`, ROADMAP decision-10 UPDATE, 09-22 rows 12–13, RECON N-4 (:452–454); none of them on `main`] [CHANGED SINCE HANDOFF: ml#2117 (`8b6edddd`, 10-04 11:16Z) moved 09-22 into `HANDOFF_2026-09/` and fixed its links and ROADMAP :818. Zebra holds the OLD text of all three] | STARTABLE | — | ml | S | UNBLOCKER |
| P7-02 | Make the census exit 0 at the PR base. Classify or exclude `a_n2_drive.py`'s 4 anchors and the new `2026-10-04_replay_redrive.py`'s anchors. | consolidated 1a "new step" | [CHANGED SINCE HANDOFF: `git grep` replication of discovery → 38 files at `afb02801`, **39** at HEAD. The 39th, `util/ad-hoc/2026-10-04_replay_redrive.py`, came from ml#2120. An AST replication finds 5 anchors (:55, :227, :230, :253, :254). By `classify()`'s ≥3-character rule, `startswith("[")` (:227) is UNCLASSIFIED. Census not run] | STARTABLE | P7-01 | ml | S | UNBLOCKER |
| P7-03 | Re-derive N-4's file and anchor counts and B4's "35 markers / 14 scripts" at the PR base before writing them. | 1a | [VERIFIED 2026-10-04: cascor `marker_inventory.json` → rev `e052ef80`, 35 markers, 14 distinct consumer files (B4 holds)]; census-side counts [NOT RE-PROBED — census not run] | STARTABLE | P7-02 | ml | S | DATA-INTEGRITY |
| P7-04 | Record Lane A row 24 ("5/15 → 1/5") as rejected, resolved dissent. | 1b | [VERIFIED 2026-10-04: `logging_utils.py@e052ef8` :90 → `_log_with_sample(5,…)`, :94 → `(15,…)`. The rejection holds; consolidated tagged it UNVERIFIED] | STARTABLE | — | ml | S | HYGIENE |
| P7-05 | Resolve B16 first: assign the deletion of `_get_log_level`/`_get_log_level_check` to P2.2 or P4.2. Align ROADMAP :486 and :368–370. | 1c; B16 | [VERIFIED 2026-10-04: `logger.py:427`/`:435` on `main`; the only caller is `:436`. Code search: also in `juniper-cascor-model/log_config/logger/logger.py` and in both trees' `test_logger_coverage.py`] | STARTABLE | — | ml | S | UNBLOCKER |
| P7-06 | Re-derive, then apply, B1, B2+B3 and B6 (these change a number or an action), and B5, B7, B9, B10, B11. | 1c | [VERIFIED 2026-10-04: every target still uncorrected: ROADMAP :725 "28.25 %", :372–373, :147, :179 "BUILT", :498–504; 09-22 :7 banner, :427 row 13, :433 row 19]. B1's corpus [VERIFIED 2026-10-04: 32 `.prof` present]. The findings themselves [UNVERIFIED — single-lane, from R2] | STARTABLE | P7-05 | ml | M | DATA-INTEGRITY |
| P7-07 | Re-derive, then apply, B4, B8, B12–B15, B17–B20 and B16's eight stale copies. | 1c | [VERIFIED 2026-10-04: still uncorrected: ROADMAP :34, :54, :197, :771–773, :942–943; RECON :270, :465, :477–478; both notes say `Last Updated: 2026-09-02`. The corrected anchors hold on `main`: conftest :891–892/:948, `isEnabledFor` :1085, closures :579–580. B19: `stop_requested` has `required_level` null] | STARTABLE | P7-05 | ml | M | HYGIENE |
| P7-08 | Chase Lane B's open leads: the "~17 glob consumers" copies (ROADMAP :116/:409/:456/:646, RECON :441), and 1,238 lines vs 1,218 records. | 1c leads | [VERIFIED 2026-10-04: RECON :441 still reads "~17 scripts glob it"]; everything else [NOT RE-PROBED] | STARTABLE | P7-02 | ml | S | HYGIENE |
| P7-09 | Fix the stale copies that are NOT on Lane B's list: "#573 zero comments" (RECON :688, ROADMAP :820–821), and P4-design's §8 table (decisions 1 and 6) and Status line. | residue (§6) | [VERIFIED 2026-10-04: the texts are present; #573 has 1 comment] | STARTABLE | — | ml | S | HYGIENE |
| P7-10 | Write 09-22 §8.3 at its new path: the lanes, what was accepted, what was rejected, and the author's two pre-round fixes. | 1d | [VERIFIED 2026-10-04: no §8.3 exists] | STARTABLE | P7-06, P7-07 | ml | S | HYGIENE |
| P7-11 | Settle B1's consumer-drift check: wire up `--check-inventory`, or record the rejection. The inventory now lags new consumers. | B20 residue | [VERIFIED 2026-10-04: only the census itself references it (grep `.github/` `tests/` `util/`)] [CHANGED SINCE HANDOFF: `a_n2_drive.py` and `replay_redrive.py` both postdate the `e052ef8` inventory] | STARTABLE (to record it); wiring it = OWNER-DECISION | P7-02 | ml (+cascor) | S | DATA-INTEGRITY |
| P7-12 | Run consensus round 3, briefed only on the round-2 fixes. Include an independent re-run of P0.4's 14/14 mutation check. | 1d; procedure §4 | [NOT RE-PROBED — not started. Neither round-2 lane re-ran the mutation check (R2 :63, :228)] | STARTABLE | P7-01…P7-11; P8 (soft) | ml | M | DATA-INTEGRITY |
| P7-13 | Merge the reconciliation PR. | items 1, 9a | [VERIFIED 2026-10-04: no logging PR among ml's 8 open PRs] | OWNER-ACTION (merge) | P7-12, P7-37 | ml | S | UNBLOCKER |
| P7-14 | Post the cascor#573 status comment correcting the 09-22 one: Phase 1 premature; #681; P6.4 ruled (#675); P0.2 16.70 % → 29.2 %; #680; #679. | item 2 | [VERIFIED 2026-10-04: #573 OPEN with 1 comment (2026-09-22T08:03:26Z), whose "Open" list still says P6.4 is held and P0.1/P0.2 are untaken] | STARTABLE once B1's number settles | P7-06 (ideally P7-12) | cascor | S | HYGIENE |
| P7-15 | Post a further #573 comment with P0.3's numbers. That completes P0.7. | item 2; 09-22 §0.4 | [NOT RE-PROBED] | BLOCKED-ON P7-26 | P7-26 | cascor | S | HYGIENE |
| P7-16 | P2.1 in a cascor worktree: capture frame/tsp inside `_log_at_level` after the filter and pass `cls._frm().f_back`. Leave `_frame_info` alone. | item 3 | [VERIFIED 2026-10-04: on `main` `95cdc562` the 8 emit methods (:612–668) still pass `frame=cls._frm(), tsp=cls._tsp()`. Filter at :575. The last commit to `logger.py` is `c1de246a` (#667). The detector is at the envelope test :223–228, which has `pytestmark = unit` and no slow/skip. `main` CI is green. No logging branch or PR exists] [CHANGED SINCE HANDOFF: `main` moved `b2921712` → `95cdc562` (dependabot #697); `logger.py` untouched] | BLOCKED-ON P7-13 (self-imposed) | P7-13 | cascor | M | UNBLOCKER |
| P7-17 | Measure P2.1, then P2.2, as an unprofiled wall-clock A/B against the parent commit. Report a nil result honestly. | item 3; B6; P2-G3 | [VERIFIED 2026-10-04 21:0xZ: the window is NOT quiet. `clamscan` has run for 9h53m; load 4.49/3.80/3.15] | WAIT-QUIET-WINDOW | P7-16; P6 (PF-3) | cascor | S | RESEARCH |
| P7-18 | P2.2: hoist the six closures (`logger.py:579,:580,:332,:333,:350,:351`). Delete the dead helpers with an enumerated `Allow-Symbol-Loss:` trailer. | item 4 | [CHANGED SINCE HANDOFF: tagged NOT RE-PROBED there. VERIFIED 2026-10-04: all six lines unchanged on `main`] | BLOCKED-ON P7-16, P7-05 | P7-16, P7-05 | cascor | M | UNBLOCKER |
| P7-19 | P2.3: widen cache invalidation to every attribute the hoisted closures read. Add an invalidator and a firing test per cache (P2-G2). | ROADMAP §5 | [NOT RE-PROBED — consolidated does not carry it] | BLOCKED-ON P7-18 | P7-18 | cascor | M | DATA-INTEGRITY |
| P7-20 | Fix cascor#679: the custom-level closures bound via `__get__`, plus the record never reaching the file sink. | item 5 | [VERIFIED 2026-10-04: OPEN, 0 comments. The body says "No fix is proposed here… a design choice for that work" (Phase 1 / P4)] | STARTABLE (its shape needs a design call; §2 D8) | coordinate with P7-24 | cascor | M | DATA-INTEGRITY |
| P7-21 | Decision 4: converge `log_config/logger/logger.py` into juniper-cascor-model. Retire `_INTENTIONAL_DIVERGENCE` and delete the reverse guard in the same PR. | item 6 | [VERIFIED 2026-10-04: `test_drift.py:31` and `:104` are present on `main`. PyPI `juniper-cascor-model` has only 0.1.0 (2026-06-14)] | STARTABLE; the model release is OWNER-ACTION | P7-42 | cascor | M | DATA-INTEGRITY |
| P7-22 | Decision 7: the swallowed-pytest investigation per the design's §7.1. Reproduce, distinguish the cause, and only then fix. | item 6 | [VERIFIED 2026-10-04: no tracked artifact (`git ls-files` grep)] | STARTABLE | overlaps P7-23 | cascor | M | RESEARCH |
| P7-23 | P0.5: characterise the session-scoped `_log_at_level` no-op phase by phase. Record B1's "rationale obsolete since #563". | item 6 | [VERIFIED 2026-10-04: on `main` the fixture is at `conftest.py:891–892`, the no-op at :945 and the patch at :948] | STARTABLE | — | cascor/ml | S | UNBLOCKER |
| P7-24 | P4.1–P4.3: A2-bind (nine attributes, `_default` setter, factory, 16 binds), the precedence chain, the env surface, and P4-design §11.6's five guard tests. Keep #680's detector green without editing it. | item 6; B2/B3 | [VERIFIED 2026-10-04: no P4 branch or PR (matching-refs, open list, compare)] | STARTABLE, but after P7-21 (hazard 3) | P7-21, P7-20 | cascor | L | USER-FACING |
| P7-25 | Optional: add a `Logger.for_name(...)` case to #680's emitter. | B2 extra | [VERIFIED 2026-10-04: there is no `for_name` in the envelope test] | BLOCKED-ON P7-24 | P7-24 | cascor | S | DATA-INTEGRITY |
| P7-26 | P0.3 volume census: bytes per record per path (B and C separate by timestamp precision), the 1.89× factor, and caps 4 and 16 extrapolated to 64. | item 6; ROADMAP §3 | [NOT RE-PROBED — no artifact found] | WAIT-QUIET-WINDOW (live-stack slot; distinct `JUNIPER_CASCOR_LOG_DIR`) | P6; P7-06 (B7) | ml+cascor | M | RESEARCH |
| P7-27 | P5.1 per decision 3: narrow the fork to the delta, keep the rotator and reuse `JuniperJsonFormatter`. Dispose `test_api_observability.py:89,:97,:114` (P5-G4). | item 6; ROADMAP §8 | [NOT RE-PROBED — no PR since v0.11.0] | STARTABLE | — (it blocks P3.1/P3.3) | cascor | M | UNBLOCKER |
| P7-28 | P6.1: delete `src/cascade_correlation/backups/` and the two dead test clauses, and decide the untracked `src/backups/check.py`. The trailer must be the final paragraph. | item 6; ROADMAP §9 | [VERIFIED 2026-10-04: 5 files still tracked on `main`; `check.py` exists only in the local checkout] | STARTABLE | — | cascor | S | HYGIENE |
| P7-29 | P6.2, then P6.3: a lint rule banning bare numeric levels (`--advisory` until P6.2 lands). | item 6; B11 | [VERIFIED 2026-10-04: all 10 `isEnabledFor` sites in `candidate_unit.py` on `main` are symbolic, so P6.2's stated 8-site surface looks discharged by #652. No source records this] | BLOCKED-ON P2 (P7-16/P7-18) | P7-18 | cascor | S | HYGIENE |
| P7-30 | P6.4 widening: 236 sites outside the hot files and 51 refused inside them. | item 9c | [NOT RE-PROBED — figures at `e052ef8`] | OWNER-DECISION | — | cascor | M | HYGIENE |
| P7-31 | Phase 3: P3.1 sinks (fix the shadowed `_file_name` first), P3.2 console switch (decision 2), P3.3 rotation owner, then P3.4 persistent handle. | ROADMAP §6 | [NOT RE-PROBED] | BLOCKED-ON P7-18, P7-26, P7-27 | — | cascor | L | USER-FACING |
| P7-32 | P4.4 fork propagation, P5.2 JSON sink and P5.3 worker import-surface screen. Phase 7 (ELK) stays deferred. | ROADMAP §7, §8, §11 | [NOT RE-PROBED] | BLOCKED-ON P7-31 | P7-24 | cascor | L | USER-FACING |
| P7-33 | Per §10: put a version token in each revertable log artifact's first record, and make every phase state its mirror and release obligation. | ROADMAP §10 | [NOT RE-PROBED] | STARTABLE (with P7-31) | P7-31 | cascor | S | DATA-INTEGRITY |
| P7-34 | Remove eight cascor logging worktrees after verifying each one. Leave `perf--logging-hot-path`. Never run `remove_stale_worktrees.bash`. | items 7, 9d, 9e | [VERIFIED 2026-10-04: all nine exist; p01 holds 5 `.h5`]. Dirt states [UNVERIFIED — no git run outside this worktree] | STARTABLE, except p01 and wip (owner) | P7-39, P7-40 | cascor (local) | S | HYGIENE |
| P7-35 | Remove the ml worktree `temporal-snacking-zebra` once P7-01 lands. Dispose of `cached-greeting-mochi`. | item 8 | [VERIFIED 2026-10-04: both exist] | BLOCKED-ON P7-01 | P7-01 | ml (local) | S | HYGIENE |
| P7-36 | File one issue each for ROADMAP §12's adjacent defects: canopy's dead env overrides, service-core's unread `JUNIPER_SERVICE_LOG_LEVEL`, and canopy's `CASCOR_*` names. | ROADMAP §12 | [VERIFIED 2026-10-04: 3 issue searches → 0 hits. The canopy `src/logger/logger.py:536` gate is unchanged on `main`. service-core `settings.py:36` declares `log_level`, and nothing in the package reads it] | STARTABLE | P2 (canopy) | canopy, ml | S | HYGIENE |
| P7-37 | Owner re-confirms merge approval for this arc. | item 9a | approval expired [NOT RE-PROBED] | OWNER-ACTION | — | all | S | UNBLOCKER |
| P7-38 | Owner rules whether Phase 1 is "complete". | item 9b; B5 | [VERIFIED 2026-10-04: code search → `_display_training_progress` appears in 2 coverage tests and 2 fixtures, NOT in `test_logger_per_level_exercise.py`; #679 OPEN] | OWNER-DECISION | P7-20 | — | S | HYGIENE |
| P7-39 | Owner decides the p01 worktree's 5 ignored `.h5` snapshots. | item 9d | [VERIFIED 2026-10-04: 5 present] | OWNER-DECISION | — | cascor | S | DATA-INTEGRITY |
| P7-40 | Owner decides whether to keep `wip/logging-p14-adopt-logging-utils` (#667's `--old` baseline). | item 9e | [VERIFIED 2026-10-04: remote ref at `1b918e61`] | OWNER-DECISION | — | cascor | S | HYGIENE |
| P7-41 | Owner confirms or corrects ROADMAP decision 8's provenance ("Owner: please confirm or correct this entry"). | ROADMAP :815–821 | [VERIFIED 2026-10-04: the request text is unchanged] | OWNER-DECISION | — | ml | S | HYGIENE |
| P7-42 | Cut a cascor release, and after P7-21 a juniper-cascor-model release. | INDEX; ROADMAP §10 | [VERIFIED 2026-10-04: `compare v0.11.0...main` → 57 commits ahead, including logging PRs #644, #648, #652, #653, #667, #670, #675, #680, #681. PyPI: cascor 0.11.0 (2026-09-10), model 0.1.0] | OWNER-ACTION (P4) | P4 | cascor | S | USER-FACING |

## 2. Owner decisions pending

| ID | Question | Options, and the source's recommendation | Blocks | Source |
| --- | --- | --- | --- | --- |
| D1 | Re-confirm merge approval | grant it for the session / approve per PR. Approval expires per session | P7-13 and every merge | consolidated 9a; ROADMAP decision 9 |
| D2 | Is Phase 1 "complete"? | yes now / after #679 plus a per-level test of the #670 sites. B5: keep "complete" open until the owner rules | wording in P7-01 and P7-14 | 9b |
| D3 | Widen P6.4 beyond the hot files? | widen (236 sites) / hot files only. No recommendation; "widening needs a fresh ruling" | P7-30 | 9c; decision-6 UPDATE |
| D4 | p01 worktree `.h5` files | keep / move / delete. None recommended | P7-34 | 9d |
| D5 | WIP branch | keep it as #667's timing baseline / delete it (its fix is on `main` via #681) | P7-34 | 9e |
| D6 | Decision 8's provenance | confirm / correct | record only | ROADMAP :821 |
| D7 | Release cuts | cascor now (57 commits); cascor-model after convergence | logging fixes on PyPI | INDEX; release handoff item 5 |
| D8 | #679's fix shape | route the closure through the logger it is installed on / drop the copy. The issue defers it to the P1/P4 design; owner only if it alters ruled decision 5 | P7-20 | #679 body |
| D9 | Consumer-drift CI check | wire `--check-inventory` / record a rejection. No recommendation recorded | P7-11 | B20 |

## 3. Cross-path dependencies

- **P7 → P6.** P7-17 (A/B) and P7-26 (P0.3) need the perf lane's quiet window: no `clamscan`, and a 1-minute load that stays under ~6. PF-3 needs ~7 h of the same window, so run them one after another, never together. P7-16 and P7-18 code goes in a cascor worktree, never the primary checkout.
- **P7 → P4.** P7-42: none of the nine logging PRs is on PyPI. P7-21 creates a juniper-cascor-model release obligation (the release handoff counts cascor 17 and cascor-model 7 unreleased SHIP changes).
- **P3 → P7 (soft).** An observability release bundles whatever P7 has put in observability's `[Unreleased]`. Today that is nothing, and decision 3's option (c) (P7-27) needs no shared-package pin move.
- **P2 → P7.** P2's `util/ad-hoc/2026-10-04_replay_redrive.py` (ml#2120) became a census consumer, which is why P7-02 is needed. P7-36 files issues in canopy.
- **P8 → P7 (soft).** Launch P7-12's round 3 when no other arc is mid-round.
- **P1 → P7 (hazard only).** Tier-1 backups are down, and the raw P0.1 corpus is not backed up (hazard 4).
- No other path waits on P7, apart from release bundling.

## 4. Hazards

1. **Salvage zebra hunk by hunk.** Zebra's ROADMAP :818 and its 09-22 relative links predate ml#2117, and its 09-22 copy sits at the OLD path. A whole-file copy, or `util/open_signed_pr.py` (which uploads whole files), would revert #2117 or re-create a duplicate file.
2. **P2.1(c).** Never make `_frame_info` walk two hops, and never edit `test_path_a_resolves_the_real_caller`'s expectations. This binds P4.1 too, whether or not P2.1 ships first (B2/B3).
3. **A mirrored caller with an unmirrored callee** (09-17 §5.2). `candidate_unit.py` is byte-gated but the model's `logger.py` is not. P4.1's binds calling `Logger.for_name` would raise `AttributeError` in the published package while `src/` stays green. Converge first (P7-21), or mirror the factory. P2.2's helper deletion also hits the model copy's tests.
4. **The raw P0.1 corpus** (32 `.prof` in `~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof/`) is the only input for re-deriving B1 and P0.2. It is not backed up.
5. **`git worktree remove` deletes p01's 5 ignored `.h5`.** Never run `util/remove_stale_worktrees.bash`.
6. **Measurement.** Use unprofiled measurements only (cProfile inflated the discarded path 3.17×), a distinct `JUNIPER_CASCOR_LOG_DIR` per live run, and `env -u JUNIPER_CASCOR_LOG_DIR` for cascor tests. Instruments print their revision; check it.
7. **Deletions** in P7-18 and P7-28 need the `Allow-Symbol-Loss:` trailer as the final paragraph; cascor's main-verify always runs. `safe_merge.py` can exit 0 without merging, so read its `MERGED` line.

## 5. Discrepancies

1. The consolidated file names 09-22 at `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_…`. It now lives under `HANDOFF_2026-09/` (ml#2117).
2. "No commit has touched …ROADMAP.md since `7e952534`" is no longer true: `8b6edddd` changed one link (:818). The verification line "top = 7e952534 until item 1 lands" now fires falsely.
3. "rc=0 only after zebra's 3 exclusions AND a_n2_drive.py's 4 anchors" is now incomplete: a 39th consumer, `replay_redrive.py`, adds at least one UNCLASSIFIED anchor (static replication).
4. cascor `main` is `95cdc562`, not `b2921712`. The change is a dependency bump only; `logger.py` is unchanged.
5. The consolidated file calls #679 "agent-doable". The issue says its fix shape is "a design choice for that work" (Phase 1 / P4).
6. B11 gates P6.2 on P2, but P6.2's stated 8-site surface appears already converted by #652.

## 6. Residue (open in references, not carried by the consolidated file)

- P2.3 and P2-G2 (P7-19).
- Phase 3, P4.4, P5.2, P5.3, the deferred Phase 7, and P5-G4's test disposition (P7-31, P7-32, P7-27).
- ROADMAP §10's version token and per-phase release obligation (P7-33, P7-42).
- ROADMAP §12's three adjacent issues (P7-36).
- Decision 8's request for owner confirmation (P7-41).
- The stale "zero comments" copies and P4-design's §8 table (P7-09).
- P6.1's sub-items: `check.py` and the two dead test clauses (P7-28).
- R2 Lane A's unchecked list: P0.2 figures other than 28.25 %, the P6.4 residue counts, the shape-survey counts, the conftest stub, and the "golden caught none of five breaks" claim. No lane re-derived these, and no round-2 lane re-ran the 14/14 mutation check (P7-12).
- #680's inventory lags consumers added after `e052ef8` (P7-11).
- The P6.2 discharge is unrecorded (P7-29).
- 09-17 trap 5.2 appears in the consolidated file only obliquely (hazard 3).

## 7. Path assessment

**Urgency: medium-low.** No item here is a safety item. One data-integrity defect is live on `main`: #679 loses VERBOSE/TRACE records, though only at non-default levels. The document drift compounds: the census target has moved twice (ml#2058, ml#2120) and 09-22 has moved once.

**Leverage.** The reconciliation PR (P7-01 to P7-13) is the self-imposed gate on P2.1, which heads the critical path P0.4 → P2 → P3 → P5.2, and that path carries #573's user-facing scopes. P7-27 (P5.1) and P7-26 (P0.3) are Phase 3's other gates.

**Cost.** One M-sized juniper-ml PR plus an M-sized round 3. P2.1 is S–M of code, but its measurement competes with PF-3 for quiet windows.

**Next actions, in order:**

1. Do P7-01 → P7-02 → P7-05 → P7-06, P7-07, P7-09 and P7-10 in one juniper-ml PR (hunk by hunk, census at rc=0 including `replay_redrive.py`), then run P7-12.
2. Ask the owner for D1 and D2 together (P7-37, P7-38). They gate P7-13 and the wording of P7-14.
3. In parallel, P7-27 or P7-28 can start, since neither touches the reconciled text. Then do P7-16 right after P7-13, deferring P7-17's A/B to a quiet window.

## 8. What this report cannot support

- The census exit code and counts at HEAD. Discovery and anchors were replicated statically; the census was not run.
- The correctness of most Lane B findings. Only B4, B19 and B16's anchors were re-derived; the rest were checked only for "target text still present".
- Any profiled share (16.70 %, 28.25 %, 29.2 %) or any P2 effect size.
- Whether cascor CI executed the envelope test itself. Only workflow conclusions were read.
- The dirt state of each cascor worktree.
- That no §12 issue exists under other wording, or that code search is complete. Code search found 0 hits for "Snapshot replay started" and did not list `cascade_correlation.py` for `isEnabledFor`.
- Quiet-window status after 21:05Z.
- Anything in `round1_lane_reports.md` beyond what R2 cites.
