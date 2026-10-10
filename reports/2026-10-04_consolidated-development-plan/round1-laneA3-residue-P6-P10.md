# Round 1 — Lane A3 (residue, P6–P10)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-1 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round1-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- **Instrument**: I read the five 2026-10-03 consolidated handoffs for P6–P10 in full, then the documents they cite as carrying open work. Those were:
  - the logging roadmap §2–§3 and §12–§13.1;
  - the harness design §10–§13;
  - the CI-budget walkthrough §7;
  - the 09-09 handoff's banner, its first §1 block and :970–:1063;
  - the 09-11 banner :1–:389 and :525–:572;
  - the perf rulings note §5.4–§6 and the PF-3 suite header;
  - the CLI-tail re-probe §0.1 and the 09-07 perf handoff §8;
  - the work lists of the 09-24 perf and logging primaries.

  I built my own item list **before** opening the plan or the extraction reports. Then I checked each item against the four P6–P10 extraction reports and against the plan (§2–§11, Appendices A–B). Live checks were read-only: `ls`, `stat` and `find` on worktrees, `~/.local/state` and transcript dirs; `git ls-tree` and `git log` in this worktree; three `gh api` REST calls. No scripts, tests or experiments were run.
- **Entry point**: source handoffs and their references.
- **Sample**: 67 source items (P6 18, P7 14, P8 14, P9 11, P10 10), and all 67 were checked.
  - 1 is absent from every report and from the plan (F9).
  - 12 are in the reports but were dropped, mis-stated or left un-gated by the plan (F1–F8, F10–F13).
  - Appendix A places all 135 extraction rows for P6–P10.

**File keys.** Handoffs live in `prompts/thread-handoff_automated-prompts/`; the 09-07, 09-09 and 09-11 ones are under `HANDOFF_2026-09/`. **EX6**, **EX8**, **EX9** = `extraction-P6-perf.md`, `extraction-P8-harness.md`, `extraction-P9-ci-budget-P10-ci-tools.md`. **EX4** = `extraction-P4-release-P11-k8s.md`; **EX5** = `extraction-P5-partition.md`; **EX12** = `extraction-P12-equities.md`. The "In plan?" column refers to `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`.

## Findings

| ID | Severity | Item (from source) | Source (file §/line) | In extraction report? | In plan? (where) | Evidence | Proposed correction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | MAJOR | PF-3 ruling: one ~7 h pass, only with no `clamscan` and a 1-min load that STAYS under ~6, sampled throughout; loaded-host round-robin DECLINED | `pf3-cascor-pool-scaling.yaml:59-64`; `…SIX-OWNER-DECISIONS-RULED.md` §6; `perf-lane-consolidated.md:33,49` | Yes (P6-03); EX6 §7 cost says "three round-robin passes" | §7.2 :424 "three passes"; :435 only "check … and quote both" | header :61 "Declined…", :64 "One pass is ~7 h" | One pass; launch only on the ruled condition; sampler beside it |
| F2 | MAJOR | Single-copy state missing from XC-PRESERVE: P6 baselines, micro stores, suite dirs, retained worktrees and symlink; P9 biscuit lane scratch; P10 `luminous-inventing-crystal` untracked files | `perf-lane-consolidated.md:115-124`; `ci-budget-arc-consolidated.md:121-123,184-187`; 09-09 :976-978; 09-11 :200-202 | Partly: EX6 §4 omits the current PF-1 tag and micro stores; EX9 has biscuit as cleanup only (P9-16) | §3 rows a–j: none | note 1 | Add rows; harvest before XC-CLEAN |
| F3 | MAJOR | Cleanup keep-conditions: p01's 5 ignored `.h5` and the WIP branch wait for owner D4/D5; six local-only evidence branches stay until round 2; biscuit until after round 6 | `logging-arc-consolidated.md:90-91`; `dynamic-workflow-harness-consolidated.md:118`; EX9 P9-16 | Yes (P7-34; EX8 §4; P9-16) | XC-CLEAN :211 gated only on XC-PRESERVE and P2 O2; D4/D5 in Group C; branches unnamed; App. B row 16 bundles P3-29's branch cleanup | note 2 | Also gate on D4/D5, P8-02, P9-01; add a KEEP list |
| F4 | MAJOR | From any worktree the experiment stack mis-derives PROJECT_DIR; targets "fail silently (inverting results)". Export `JUNIPER_EXP_PROJECT_DIR`; pin `JUNIPER_EXP_CASCOR_SRC_DIR` | `perf-lane-consolidated.md:83` | EX6 §4 only; EX5, EX12: 0 hits | §7.2 queues P5-12/13, P12-08/09, P7-26; §11 omits it | `experiment_stack.bash:98` unchanged; `run_suite.py:289` "degrades rather than hard-failing"; P5 handoff, P12 plan: 0 hits | Add §11 H-14 and a §7.2 launch line |
| F5 | MINOR | Launch a round only when no other arc is mid-round. The 5-hour window killed all 5 of P8's round-1/2 validators | `dynamic-workflow-harness-consolidated.md:86`; `…INDEX_consolidated-development-paths.md:60` | Yes (EX8 §3; EX9 §3) | §7.1 :404 allows "two arcs mid-round at once", with no evidence | — | Restore one arc at a time, or record why two is safe |
| F6 | MINOR | Verify the "verbatim" records before their transcripts expire | `dynamic-workflow-harness-consolidated.md:36,49` | P8-10 covers R1 only | XC-PRESERVE j and Wave 2 "P8-10 (by about 10-22)" cover R1 only | note 3 | Extend P8-10 to `…GROUNDING-INVENTORIES-RECORD.md` and do that one first |
| F7 | MINOR | Before compacting `MEMORY.md`, fix the gates that "do not read hook TEXT" | `perf-lane-consolidated.md:243` | Yes (P6-34) | XC-MEM :182-184 rules, then compacts; the gate fix is dropped | — | Insert the gate fix before compaction |
| F8 | MINOR | P2.1 is the next code step; "Its blocker, item 1, is self-imposed"; it heads the critical path | `logging-arc-consolidated.md:61`; `…LOGGING-REDESIGN-ROADMAP.md:127` | Yes (P7-16, "right after P7-13") | Tier T5, Wave 4 "long arcs" :307; the Wave 2 lane :287 stops at P7-14 | — | Continue the lane: P7-13 → P7-16 → P7-17 (T4) → P7-18 |
| F9 | MINOR | Latent defect, unfiled: cascor-client's lockfile regen writes an untracked file that `git diff --quiet` cannot see | 09-11 Corrections 2 (:260-262) | No | No | cascor-client `main` `lockfile-update.yml:115-116` documents it; check at :131 (REST). Register: 0 rows | Route to P3 for a row, or record acceptance |
| F10 | MINOR | Roadmap P0 is exempt from the round-2 gate; D-10 needs ≥3 weekly windows of P0 data | `…DYNAMIC-WORKFLOW-HARNESS-DESIGN.md:571,585` | Yes (P8-14/15; EX8 §7 item 3 asks the owner) | P8-14 is T5; §6 never asks to authorise the user-level `statusLine` install; Group B :382 asks for D-10 "after round 2" | — | Group B: "start P0 now?"; mark D-10 as needing P0 data |
| F11 | MINOR | Serialize all T4 rows; each live-stack step needs a distinct `JUNIPER_CASCOR_LOG_DIR` | plan §1.1 T4; `…LOGGING-REDESIGN-ROADMAP.md:103` | Yes (P6-15, P6-18, P6-29; P7-26) | §7.2 omits P6-15, P6-18 (PF-5/6/7) and P6-29, and does not carry the LOG_DIR rule for concurrent load runs | — | List them; add the rule |
| F12 | MINOR | APD-ML-002: 4 of its 6 names exist nowhere; "a one-level unwrap harvests 2/6 and looks like a fix"; ship it with the first registry-`metrics` tests | `perf-lane-consolidated.md:56,133-136` | Yes (P6-08, OD-3) | XC-P12 :206 routes only the ruling to the in-flight W0.4 session | `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md:349` maps recurrence names only | Send P6-08's trap, test rule and OD-3 along with the ruling |
| F13 | MINOR | A conditional Wave 4 shape first needs the throwaway-repo test | `ci-tools-reevaluation-consolidated.md:155`; 09-11 :303-305 | Yes (P10-10) | Group C; §9 has no link from P10-10 to P4-10 | EX4 P4-10 (shape pick) names no such test | Add a §9 row: P4-10 (conditional) → P10-10 |
| F14 | NIT | Tier consistency | — | — | P9-13 is in Wave 0 (T0) but Appendix A says T1; merged row P6-33 is T6 but P3-33 is T2; the Wave 2 P7 lane omits T2 rows P7-04, P7-08 and P7-11 | — | Align |

**Notes.**

1. **F2.** `ls` on 2026-10-04 found:
   - `~/.local/state/juniper-experiments/baselines/{pf1-2026-09-04,pf1-2026-09-04b,pf1-2026-09-23-blas2,cascor-micro}`. `pf1-2026-09-23-blas2` is the current PF-1 tag, and `cascor-micro/` holds the 3.13 and 3.14 stores;
   - the pin worktree (`…perf-pf1-baseline-pin…0d2d826b`) and the cap64 worktree (`…e-c-cap64…67d7ea35`);
   - the `shadow-ec-cap64/juniper-cascor` symlink.

   Backups have been down since 09-18 (plan §Overview), so none of this has a second copy. In `ancient-yawning-biscuit`, `find` counts 109 `.py` files in the lane dir; `git ls-tree origin/main` tracks 8. 09-09 :976-978 says "the 857 and 733 readings rest on lane scratch output … not committed".
2. **F3.** `find` lists 5 `cascor-snapshots/*.h5` in `…p01--logging-corpus…8065ca0f`, and `git worktree remove` deletes ignored files (plan §11 H-6). The local `analysis/soak-stratum-predictors-main` is at `f9e5390a`, but #1854's head is `2ee8cc86` (REST). So `refs/pull/<N>/head` may not restore the branch as it was measured. The sources also ask to KEEP the P6 pin and cap64 worktrees and `…perf--logging-hot-path…` ("leave it").
3. **F6.** `stat` of `bb39e9fe…/subagents/` shows:
   - the 5 inventory agents (I1–I5): 2026-09-22 20:40–20:53 CDT;
   - R1's five lanes: 09-23 00:32–01:12 CDT.

   `~/.claude/settings.json` sets no `cleanupPeriodDays`, so the default 30 days applies. The oldest surviving top-level transcript is from 09-04 17:29 CDT, which fits a 30-day cutoff by mtime. The first deletion therefore falls around **2026-10-22 20:40 CDT**. The plan's date is right, but its scope is too narrow.

## Checked and holds (short)

- Appendix A places every row: P6 39, P7 42, P8 27, P9 17, P10 10. §5 or §6 places every P6–P10 owner decision: P6 OD-1..14, P7 D1–D9, P8 D-1..D-12, RS-1/2, V3 and B-1, P9/P10 OD-1..10.
- Three closures hold when re-checked:
  - ml#1811: `tests/test_experiment_config_schemas.py:144` is `= {}`;
  - F-P1-2 and Q-7: `…PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md:272`;
  - G-17's marker half: `…PERF-LANE-P2-PLAN.md:346`.
- "Title-repair gate first" binds title repairs only (`HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md:391-397`), so P6-23 belongs in Wave 2.
- These are all placed:
  - the roadmap's downstream phases and its §12 issues (P7-31..P7-33, P7-36);
  - the required round 3 (P7-12);
  - V3 ratification and RS-1/2 (P8-25, P8-12);
  - the archiver path fix ahead of round 6 (P9-02);
  - NON-OWNER 2's no-re-pin rule (S0.9 says "read-only");
  - 6f's floor first (P10-04).
- The P8-10 deadline is correct (note 3).

## Could not check

- Host load and `clamscan`: not probed.
- What is untracked in `luminous-inventing-crystal`, `harmonic-swimming-planet` and `structured-inventing-fairy`. Cross-worktree git is refused, so I could only `ls`.
- Whether cleanup deletes subagent files one by one or a whole session at a time. If by session, the parent's mtime (09-24 20:02 CDT) puts the cutoff around 10-24.
- Whether `f9e5390a` is an ancestor of `2ee8cc86`. That object is not fetched.
- MD013 on `reports/`, which `.pre-commit-config.yaml` does not exclude. awk byte counts flag 19 lines over 512 across the nine extraction reports. I did not run markdownlint, and multi-byte characters may inflate the counts.

## What this report cannot support

- That P6–P10 carry no further residue. I did not read `round1_lane_reports.md`, the reconciliation note, V3 or the P2 plan in full.
- Anything about P1–P5, P11 or P12 beyond where they meet P6–P10.
- What the untracked scratch or the `.h5` files are worth. I measured only that they exist, and how many there are.
- That two concurrent rounds are unsafe. I can show only that the sources say one at a time and the plan gives no evidence for two.
